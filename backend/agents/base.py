"""
Base Agent 클래스 및 공통 타입 정의
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict, Union
from enum import Enum
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class DocumentType(Enum):
    """문서 타입"""
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    
class ChunkMetadata(TypedDict):
    """청크 메타데이터"""
    chunk_index: int
    page_number: Optional[int]
    chunk_type: str  # "text", "table", "image"
    source: str
    confidence: Optional[float]

class ProcessedChunk(TypedDict):
    """처리된 청크 데이터"""
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]]

class DocumentProcessingState(TypedDict):
    """문서 처리 상태 (LangGraph State)"""
    # 입력 데이터
    file_path: str
    policy_id: int
    file_name: str
    
    # 처리 상태
    current_step: str
    status: str
    error_message: Optional[str]
    
    # 중간 결과
    raw_content: Optional[bytes]
    pdf_metadata: Optional[Dict[str, Any]]
    extracted_text: Optional[str]
    extracted_tables: Optional[List[Dict[str, Any]]]
    extracted_images: Optional[List[Dict[str, Any]]]
    
    # 최종 결과
    processed_chunks: List[ProcessedChunk]
    embeddings_created: bool
    stored_in_vector_db: bool
    
    # 진행률 및 통계
    total_pages: Optional[int]
    processed_pages: int
    total_chunks: int
    processing_time: Optional[float]

class BaseAgent(ABC):
    """베이스 에이전트 클래스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agents.{name}")
        
        # LangFuse 모니터링 초기화 (선택적)
        self.monitor = None
        self._initialize_monitoring()
        
        # 성능 메트릭 수집기 초기화 (선택적)
        self.performance_collector = None
        self._initialize_performance_collector()
        
        # 워크플로우 로거 초기화 (선택적)
        self.workflow_logger = None
        self._initialize_workflow_logger()
    
    def _initialize_monitoring(self):
        """모니터링 시스템 초기화"""
        try:
            from services.langfuse_monitor import get_monitor
            self.monitor = get_monitor()
            self.logger.debug(f"[{self.name}] 모니터링 시스템 초기화 완료")
        except Exception as e:
            self.logger.warning(f"[{self.name}] 모니터링 시스템 초기화 실패: {e}")
            self.monitor = None
    
    def _initialize_performance_collector(self):
        """성능 메트릭 수집기 초기화"""
        try:
            from services.performance_metrics_collector import get_performance_collector
            self.performance_collector = get_performance_collector()
            self.logger.debug(f"[{self.name}] 성능 메트릭 수집기 초기화 완료")
        except Exception as e:
            self.logger.warning(f"[{self.name}] 성능 메트릭 수집기 초기화 실패: {e}")
            self.performance_collector = None
    
    def _initialize_workflow_logger(self):
        """워크플로우 로거 초기화"""
        try:
            from services.workflow_logger import get_workflow_logger
            self.workflow_logger = get_workflow_logger()
            self.logger.debug(f"[{self.name}] 워크플로우 로거 초기화 완료")
        except Exception as e:
            self.logger.warning(f"[{self.name}] 워크플로우 로거 초기화 실패: {e}")
            self.workflow_logger = None
    
    @abstractmethod
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        상태를 받아서 처리하고 업데이트된 상태를 반환
        """
        pass
    
    async def process_with_tracing(self, state: DocumentProcessingState, parent_trace=None) -> DocumentProcessingState:
        """
        추적 기능이 통합된 처리 메소드
        """
        if not self.monitor:
            # 모니터링 비활성화 시 기본 처리
            return await self.process(state)
        
        # 에이전트 실행 추적 시작
        span = await self.monitor.trace_agent_execution(
            self.name,
            self._serialize_state_for_input(state),
            parent_trace
        )
        
        start_time = time.time()
        start_datetime = datetime.now()
        error_occurred = False
        
        # 워크플로우 ID 추출 (Supervisor에서 설정된 것을 사용)
        workflow_id = state.get("workflow_id")
        if not workflow_id:
            # Supervisor가 설정하지 않은 경우에만 생성 (fallback)
            policy_id = state.get("policy_id", "unknown")
            workflow_id = f"fallback_workflow_{policy_id}"
            self.logger.warning(f"[{self.name}] Supervisor에서 workflow_id가 설정되지 않음. Fallback 사용: {workflow_id}")
            state["workflow_id"] = workflow_id
        
        # 워크플로우 로그: 시작 상태
        if self.workflow_logger:
            await self.workflow_logger.log_workflow_step(
                workflow_id=workflow_id,
                step_name=self.name,
                status="running",
                input_data=self._serialize_state_for_input(state),
                execution_time=None,
                start_time=start_datetime
            )
        
        try:
            # 실제 처리 실행
            result = await self.process(state)
            
            # 처리 시간 계산
            duration = (time.time() - start_time) * 1000  # ms
            
            # 성공 결과 업데이트
            await self.monitor.update_agent_result(
                span,
                self._serialize_state_for_output(result),
                duration,
                "completed"
            )
            
            # 워크플로우 로그: 완료 상태
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name=self.name,
                    status="completed",
                    input_data=self._serialize_state_for_input(state),
                    output_data=self._serialize_state_for_output(result),
                    execution_time=int(duration),
                    end_time=datetime.now()
                )
            
            # 성능 메트릭 수집
            if self.performance_collector:
                await self._collect_agent_performance_metrics(state, result, duration, "completed")
            
            return result
            
        except Exception as e:
            error_occurred = True
            duration = (time.time() - start_time) * 1000  # ms
            
            # 오류 결과 업데이트
            await self.monitor.update_agent_result(
                span,
                {"error": str(e), "error_type": type(e).__name__},
                duration,
                "failed"
            )
            
            # 워크플로우 로그: 오류 상태
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name=self.name,
                    status="error",
                    input_data=self._serialize_state_for_input(state),
                    error_message=str(e),
                    execution_time=int(duration),
                    end_time=datetime.now()
                )
            
            # 에러 상태로 상태 업데이트
            error_state = self.update_status(
                state,
                ProcessingStatus.FAILED,
                f"{self.name}_error",
                str(e)
            )
            
            # 성능 메트릭 수집 (오류 상황)
            if self.performance_collector:
                await self._collect_agent_performance_metrics(state, error_state, duration, "failed")
            
            self.log_step(error_state, f"처리 중 오류 발생: {str(e)}", "error")
            return error_state
    
    def _serialize_state_for_input(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """입력 상태를 추적용으로 직렬화 (민감한 데이터 마스킹)"""
        return {
            "file_name": state.get("file_name", "unknown"),
            "policy_id": state.get("policy_id", 0),
            "current_step": state.get("current_step", "unknown"),
            "status": state.get("status", "unknown"),
            "total_pages": state.get("total_pages"),
            "processed_pages": state.get("processed_pages", 0),
            "total_chunks": state.get("total_chunks", 0),
            # 대용량 데이터는 메타정보만
            "has_raw_content": state.get("raw_content") is not None,
            "has_extracted_text": state.get("extracted_text") is not None,
            "has_extracted_tables": bool(state.get("extracted_tables")),
            "has_extracted_images": bool(state.get("extracted_images")),
        }
    
    def _serialize_state_for_output(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """출력 상태를 추적용으로 직렬화"""
        serialized = self._serialize_state_for_input(state)
        serialized.update({
            "embeddings_created": state.get("embeddings_created", False),
            "stored_in_vector_db": state.get("stored_in_vector_db", False),
            "processing_time": state.get("processing_time"),
            "chunks_count": len(state.get("processed_chunks", [])),
        })
        
        # 오류 정보 포함
        if state.get("error_message"):
            serialized["error_message"] = state.get("error_message")
        
        return serialized
    
    async def _collect_agent_performance_metrics(self, 
                                               input_state: DocumentProcessingState,
                                               output_state: DocumentProcessingState, 
                                               duration_ms: float,
                                               status: str):
        """에이전트 성능 메트릭 수집"""
        try:
            # 처리된 아이템 수 계산
            processed_items = 0
            if output_state.get("processed_chunks"):
                processed_items = len(output_state["processed_chunks"])
            elif output_state.get("extracted_text"):
                processed_items = 1  # 텍스트 추출
            elif output_state.get("extracted_tables"):
                processed_items = len(output_state.get("extracted_tables", []))
            elif output_state.get("extracted_images"):
                processed_items = len(output_state.get("extracted_images", []))
            
            # 입출력 크기 계산
            input_size = 0
            output_size = 0
            
            if input_state.get("raw_content"):
                input_size = len(input_state["raw_content"])
            if output_state.get("extracted_text"):
                output_size = len(output_state["extracted_text"])
            
            execution_data = {
                "duration": duration_ms / 1000.0,  # 초 단위로 변환
                "status": status,
                "processed_items": processed_items,
                "input_size": input_size,
                "output_size": output_size
            }
            
            await self.performance_collector.collect_agent_metrics(
                agent_name=self.name,
                execution_data=execution_data
            )
            
            self.logger.debug(f"[{self.name}] 성능 메트릭 수집 완료")
            
        except Exception as e:
            self.logger.error(f"[{self.name}] 성능 메트릭 수집 실패: {e}")
    
    def log_step(self, state: DocumentProcessingState, message: str, level: str = "info"):
        """로깅 헬퍼"""
        log_message = f"[{self.name}] Policy {state.get('policy_id', 'Unknown')} - {message}"
        
        if level == "debug":
            self.logger.debug(log_message)
        elif level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
    
    def update_status(self, state: DocumentProcessingState, status: ProcessingStatus, 
                     current_step: str, error_message: Optional[str] = None) -> DocumentProcessingState:
        """상태 업데이트 헬퍼"""
        state["status"] = status.value
        state["current_step"] = current_step
        if error_message:
            state["error_message"] = error_message
        return state

def create_chunk_metadata(
    chunk_index: int,
    page_number: Optional[int] = None,
    chunk_type: str = "text",
    source: str = "pdf",
    confidence: Optional[float] = None
) -> ChunkMetadata:
    """청크 메타데이터 생성 헬퍼"""
    return ChunkMetadata(
        chunk_index=chunk_index,
        page_number=page_number,
        chunk_type=chunk_type,
        source=source,
        confidence=confidence
    )

def create_processed_chunk(
    text: str,
    metadata: ChunkMetadata,
    embedding: Optional[List[float]] = None
) -> ProcessedChunk:
    """처리된 청크 생성 헬퍼"""
    return ProcessedChunk(
        text=text,
        metadata=metadata,
        embedding=embedding
    )


