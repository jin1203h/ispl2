"""
LangGraph Supervisor Agent
멀티 에이전트 워크플로우를 조율하는 중앙 관리 에이전트
"""
import time
import asyncio
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from .base import BaseAgent, DocumentProcessingState, ProcessingStatus

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    print("⚠️ LangGraph가 설치되지 않았습니다. Multi-Agent 워크플로우가 제한됩니다.")
    LANGGRAPH_AVAILABLE = False

from .pdf_processor import PDFProcessorAgent
from .text_processor import TextProcessorAgent
from .table_processor import TableProcessorAgent
from .image_processor import ImageProcessorAgent
from .embedding_agent import EmbeddingAgent
from .markdown_processor import MarkdownProcessorAgent

class SupervisorAgent(BaseAgent):
    """멀티 에이전트 워크플로우 관리자"""
    
    def __init__(self):
        super().__init__(
            name="supervisor",
            description="PDF 문서 처리를 위한 멀티 에이전트 워크플로우를 조율합니다"
        )
        
        # 에이전트들 초기화
        self.pdf_processor = PDFProcessorAgent()
        self.text_processor = TextProcessorAgent()
        self.table_processor = TableProcessorAgent()
        self.image_processor = ImageProcessorAgent()
        self.markdown_processor = MarkdownProcessorAgent()
        self.embedding_agent = EmbeddingAgent()
        
        # 에이전트 딕셔너리 생성 (추적용)
        self.agents = {
            "pdf_processor": self.pdf_processor,
            "text_processor": self.text_processor,
            "table_processor": self.table_processor,
            "image_processor": self.image_processor,
            "markdown_processor": self.markdown_processor,
            "embedding_agent": self.embedding_agent
        }
        
        # 성능 메트릭 수집기 초기화
        self.performance_collector = None
        self._initialize_performance_collector()
        
        # 통합 파이프라인은 lazy loading으로 처리
        self.pipeline = None
        
        # LangGraph 워크플로우 구성
        if LANGGRAPH_AVAILABLE:
            self.workflow = self._create_workflow()
        else:
            self.workflow = None
    
    def _initialize_performance_collector(self):
        """성능 메트릭 수집기 초기화"""
        try:
            from services.performance_metrics_collector import get_performance_collector
            self.performance_collector = get_performance_collector()
            self.logger.debug("성능 메트릭 수집기 초기화 완료")
        except Exception as e:
            self.logger.warning(f"성능 메트릭 수집기 초기화 실패: {e}")
            self.performance_collector = None
    
    def _create_workflow(self) -> Optional[StateGraph]:
        """LangGraph 워크플로우 생성"""
        try:
            # StateGraph 정의
            workflow = StateGraph(DocumentProcessingState)
            
            # 노드들 추가
            workflow.add_node("pdf_analysis", self._pdf_analysis_node)
            workflow.add_node("text_extraction", self._text_extraction_node)
            workflow.add_node("table_extraction", self._table_extraction_node)
            workflow.add_node("image_ocr", self._image_ocr_node)
            workflow.add_node("markdown_conversion", self._markdown_conversion_node)
            workflow.add_node("embedding_generation", self._embedding_generation_node)
            workflow.add_node("finalize", self._finalize_node)
            
            # 워크플로우 연결
            workflow.set_entry_point("pdf_analysis")
            
            # PDF 분석 → 병렬 처리 (텍스트, 표, 이미지)
            workflow.add_edge("pdf_analysis", "text_extraction")
            workflow.add_edge("text_extraction", "table_extraction")
            workflow.add_edge("table_extraction", "image_ocr")
            
            # 모든 추출 완료 → Markdown 변환
            workflow.add_edge("image_ocr", "markdown_conversion")
            
            # Markdown 변환 → 임베딩 생성
            workflow.add_edge("markdown_conversion", "embedding_generation")
            
            # 임베딩 생성 → 완료
            workflow.add_edge("embedding_generation", "finalize")
            workflow.add_edge("finalize", END)
            
            return workflow.compile()
            
        except Exception as e:
            self.log_step({}, f"LangGraph 워크플로우 생성 실패: {str(e)}", "error")
            return None
    
    async def process_document(
        self, 
        file_path: str, 
        policy_id: int, 
        file_name: str
    ) -> DocumentProcessingState:
        """문서 처리 메인 진입점"""
        
        # 초기 상태 생성
        initial_state: DocumentProcessingState = {
            "file_path": file_path,
            "policy_id": policy_id,
            "file_name": file_name,
            "current_step": "initialized",
            "status": ProcessingStatus.PENDING.value,
            "error_message": None,
            "raw_content": None,
            "pdf_metadata": None,
            "extracted_text": None,
            "extracted_tables": None,
            "extracted_images": None,
            "processed_chunks": [],
            "embeddings_created": False,
            "stored_in_vector_db": False,
            "total_pages": None,
            "processed_pages": 0,
            "total_chunks": 0,
            "processing_time": None
        }
        
        self.log_step(initial_state, f"문서 처리 시작: {file_name}")
        
        if self.workflow and LANGGRAPH_AVAILABLE:
            # LangGraph 워크플로우 실행
            return await self._run_langgraph_workflow(initial_state)
        else:
            # Fallback: 순차 실행
            return await self._run_sequential_workflow(initial_state)
    
    async def _run_langgraph_workflow(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """LangGraph 워크플로우 실행 (추적 기능 통합)"""
        
        if not self.monitor:
            # 모니터링 비활성화 시 기본 실행
            return await self._run_langgraph_workflow_basic(state)
        
        # 워크플로우 ID 생성 및 설정
        workflow_id = f"langgraph_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{state.get('policy_id', 'unknown')}"
        state["workflow_id"] = workflow_id
        
        # 워크플로우 추적 시작
        async with self.monitor.trace_workflow(
            "pdf_processing_workflow",
            {
                "workflow_id": workflow_id,
                "file_name": state.get("file_name"),
                "policy_id": state.get("policy_id"),
                "workflow_type": "langgraph",
                "start_time": datetime.now().isoformat()
            }
        ) as workflow_trace:
            
            try:
                start_time = time.time()
                
                # LangGraph 워크플로우 실행 (내부적으로 각 노드가 추적됨)
                result = await self.workflow.ainvoke(state)
                
                processing_time = time.time() - start_time
                result["processing_time"] = processing_time
                
                # 워크플로우 완료 메트릭 로깅
                await self.monitor.log_metrics({
                    "workflow_type": "langgraph",
                    "total_processing_time": processing_time,
                    "total_pages": result.get("total_pages", 0),
                    "total_chunks": result.get("total_chunks", 0),
                    "agents_executed": len(self.agents),
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
                
                # 성능 메트릭 수집기에도 워크플로우 메트릭 전송
                if self.performance_collector:
                    await self._collect_workflow_performance_metrics(
                        workflow_id=f"langgraph_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        workflow_type="langgraph",
                        result=result,
                        processing_time=processing_time
                    )
                
                self.log_step(
                    result,
                    f"LangGraph 워크플로우 완료 (추적됨): 처리시간 {processing_time:.2f}초"
                )
                
                return result
                
            except Exception as e:
                error_msg = f"LangGraph 워크플로우 실행 실패: {str(e)}"
                
                # 오류 메트릭 로깅
                await self.monitor.log_metrics({
                    "workflow_type": "langgraph",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                })
                
                self.log_step(state, error_msg, "error")
                return self.update_status(
                    state,
                    ProcessingStatus.FAILED,
                    "workflow_execution",
                    error_msg
                )
    
    async def _run_langgraph_workflow_basic(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """기본 LangGraph 워크플로우 실행 (추적 없음)"""
        try:
            start_time = time.time()
            
            # LangGraph 워크플로우 실행
            result = await self.workflow.ainvoke(state)
            
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            
            self.log_step(
                result,
                f"LangGraph 워크플로우 완료: 처리시간 {processing_time:.2f}초"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"LangGraph 워크플로우 실행 실패: {str(e)}"
            self.log_step(state, error_msg, "error")
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "workflow_execution",
                error_msg
            )
    
    async def _run_sequential_workflow(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """순차적 워크플로우 실행 (LangGraph 없을 때) - 추적 기능 통합"""
        
        if not self.monitor:
            # 모니터링 비활성화 시 기본 실행
            return await self._run_sequential_workflow_basic(state)
        
        # 워크플로우 ID 생성 및 설정
        workflow_id = f"sequential_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{state.get('policy_id', 'unknown')}"
        state["workflow_id"] = workflow_id
        
        # 워크플로우 추적 시작
        async with self.monitor.trace_workflow(
            "pdf_processing_workflow_sequential",
            {
                "workflow_id": workflow_id,
                "file_name": state.get("file_name"),
                "policy_id": state.get("policy_id"),
                "workflow_type": "sequential",
                "start_time": datetime.now().isoformat()
            }
        ) as workflow_trace:
            
            try:
                start_time = time.time()
                
                # 각 에이전트를 순차적으로 실행하면서 추적
                agents_to_execute = [
                    ("pdf_processor", self.pdf_processor),
                    ("text_processor", self.text_processor),
                    ("table_processor", self.table_processor),
                    ("image_processor", self.image_processor),
                    ("markdown_processor", self.markdown_processor),
                    ("embedding_agent", self.embedding_agent)
                ]
                
                for agent_name, agent in agents_to_execute:
                    # PDF 분석이 실패하면 중단
                    if agent_name == "pdf_processor" and state["status"] == ProcessingStatus.FAILED.value:
                        return state
                    
                    # 각 에이전트 실행을 추적
                    state = await agent.process_with_tracing(state, workflow_trace)
                    
                    # 중요한 단계에서 실패 시 중단 (선택적)
                    if agent_name in ["pdf_processor", "text_processor"] and state["status"] == ProcessingStatus.FAILED.value:
                        return state
                
                # 완료 처리
                state = await self._finalize_processing(state)
                
                processing_time = time.time() - start_time
                state["processing_time"] = processing_time
                
                # 워크플로우 완료 메트릭 로깅
                await self.monitor.log_metrics({
                    "workflow_type": "sequential",
                    "total_processing_time": processing_time,
                    "total_pages": state.get("total_pages", 0),
                    "total_chunks": state.get("total_chunks", 0),
                    "agents_executed": len(agents_to_execute),
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
                
                # 성능 메트릭 수집기에도 워크플로우 메트릭 전송
                if self.performance_collector:
                    await self._collect_workflow_performance_metrics(
                        workflow_id=f"sequential_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        workflow_type="sequential",
                        result=state,
                        processing_time=processing_time
                    )
                
                self.log_step(
                    state,
                    f"순차 워크플로우 완료 (추적됨): 처리시간 {processing_time:.2f}초"
                )
                
                return state
                
            except Exception as e:
                error_msg = f"순차 워크플로우 실행 실패: {str(e)}"
                
                # 오류 메트릭 로깅
                await self.monitor.log_metrics({
                    "workflow_type": "sequential",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                })
                
                self.log_step(state, error_msg, "error")
                return self.update_status(
                    state,
                    ProcessingStatus.FAILED,
                    "workflow_execution",
                    error_msg
                )
    
    async def _run_sequential_workflow_basic(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """기본 순차적 워크플로우 실행 (추적 없음)"""
        try:
            start_time = time.time()
            
            # 1. PDF 분석
            state = await self.pdf_processor.process(state)
            if state["status"] == ProcessingStatus.FAILED.value:
                return state
            
            # 2. 텍스트 추출
            state = await self.text_processor.process(state)
            
            # 3. 표 추출 (실패해도 계속)
            state = await self.table_processor.process(state)
            
            # 4. 이미지 OCR (실패해도 계속)
            state = await self.image_processor.process(state)
            
            # 5. Markdown 변환
            state = await self.markdown_processor.process(state)
            
            # 6. 임베딩 생성
            state = await self.embedding_agent.process(state)
            
            # 6. 완료 처리
            state = await self._finalize_processing(state)
            
            processing_time = time.time() - start_time
            state["processing_time"] = processing_time
            
            self.log_step(
                state,
                f"순차 워크플로우 완료: 처리시간 {processing_time:.2f}초"
            )
            
            return state
            
        except Exception as e:
            error_msg = f"순차 워크플로우 실행 실패: {str(e)}"
            self.log_step(state, error_msg, "error")
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "workflow_execution",
                error_msg
            )
    
    async def process_document_with_pipeline(self, 
                                           file_path: str, 
                                           policy_id: int = 1,
                                           pipeline_mode: str = "STANDARD") -> Dict[str, Any]:
        """통합 파이프라인을 사용한 문서 처리"""
        
        # Lazy import to avoid circular dependency
        from services.pdf_pipeline import PDFProcessingPipeline, PipelineConfig, PipelineMode
        
        # 문자열을 enum으로 변환
        mode_enum = getattr(PipelineMode, pipeline_mode, PipelineMode.STANDARD)
        
        # 파이프라인 설정
        config = PipelineConfig(
            mode=mode_enum,
            enable_ocr=True,
            enable_table_extraction=True,
            enable_image_extraction=True,
            enable_markdown_conversion=True,
            parallel_processing=True
        )
        
        # 새 파이프라인 인스턴스 생성
        pipeline = PDFProcessingPipeline(config)
        
        # 진행률 콜백 설정
        def progress_callback(message: str, progress: float):
            self.log_step({}, f"파이프라인 진행률: {progress:.1f}% - {message}")
        
        pipeline.set_progress_callback(progress_callback)
        
        try:
            # 파이프라인 실행
            result = await pipeline.process_document(file_path, policy_id)
            
            # 결과를 DocumentProcessingState 형식으로 변환
            if result.success:
                state = result.final_state
                state["pipeline_result"] = {
                    "processing_time": result.processing_time,
                    "stages_completed": result.stages_completed,
                    "performance_metrics": result.performance_metrics
                }
                return state
            else:
                # 실패한 경우 에러 상태 반환
                error_state = self._create_error_state(file_path, policy_id, result.error_message)
                return error_state
                
        except Exception as e:
            error_msg = f"통합 파이프라인 실행 실패: {str(e)}"
            self.log_step({}, error_msg, "error")
            return self._create_error_state(file_path, policy_id, error_msg)
    
    def _create_error_state(self, file_path: str, policy_id: int, error_message: str) -> DocumentProcessingState:
        """에러 상태 생성"""
        from pathlib import Path
        return {
            "file_path": file_path,
            "policy_id": policy_id,
            "file_name": Path(file_path).name,
            "current_step": "error",
            "status": ProcessingStatus.FAILED.value,
            "error_message": error_message,
            "processed_chunks": [],
            "total_chunks": 0
        }
    
    # LangGraph 노드 함수들 (추적 기능 통합)
    async def _pdf_analysis_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """PDF 분석 노드"""
        if self.monitor:
            return await self.pdf_processor.process_with_tracing(state)
        return await self.pdf_processor.process(state)
    
    async def _text_extraction_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """텍스트 추출 노드"""
        if self.monitor:
            return await self.text_processor.process_with_tracing(state)
        return await self.text_processor.process(state)
    
    async def _table_extraction_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """표 추출 노드"""
        if self.monitor:
            return await self.table_processor.process_with_tracing(state)
        return await self.table_processor.process(state)
    
    async def _image_ocr_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """이미지 OCR 노드"""
        if self.monitor:
            return await self.image_processor.process_with_tracing(state)
        return await self.image_processor.process(state)
    
    async def _markdown_conversion_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Markdown 변환 노드"""
        if self.monitor:
            return await self.markdown_processor.process_with_tracing(state)
        return await self.markdown_processor.process(state)
    
    async def _embedding_generation_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """임베딩 생성 노드"""
        if self.monitor:
            return await self.embedding_agent.process_with_tracing(state)
        return await self.embedding_agent.process(state)
    
    async def _finalize_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """완료 처리 노드"""
        return await self._finalize_processing(state)
    
    async def _finalize_processing(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """처리 완료 및 통계 생성"""
        try:
            # 통계 계산
            processed_chunks = state.get("processed_chunks", [])
            text_chunks = [c for c in processed_chunks if c["metadata"]["chunk_type"] == "text"]
            table_chunks = [c for c in processed_chunks if c["metadata"]["chunk_type"] == "table"]
            image_chunks = [c for c in processed_chunks if c["metadata"]["chunk_type"] == "image"]
            
            # 임베딩 생성 확인
            chunks_with_embeddings = [c for c in processed_chunks if c.get("embedding")]
            
            self.log_step(
                state,
                f"처리 완료 통계: "
                f"총 {len(processed_chunks)}청크 "
                f"(텍스트: {len(text_chunks)}, 표: {len(table_chunks)}, 이미지: {len(image_chunks)}), "
                f"임베딩: {len(chunks_with_embeddings)}개"
            )
            
            # 최종 상태 업데이트
            state["total_chunks"] = len(processed_chunks)
            state["embeddings_created"] = len(chunks_with_embeddings) > 0
            
            return self.update_status(state, ProcessingStatus.COMPLETED, "completed")
            
        except Exception as e:
            error_msg = f"완료 처리 중 오류: {str(e)}"
            self.log_step(state, error_msg, "error")
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "finalization",
                error_msg
            )
    
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """BaseAgent 인터페이스 구현"""
        return await self.process_document(
            state["file_path"],
            state["policy_id"],
            state["file_name"]
        )
    
    async def _collect_workflow_performance_metrics(self, 
                                               workflow_id: str,
                                               workflow_type: str, 
                                               result: Dict[str, Any],
                                               processing_time: float):
        """워크플로우 성능 메트릭 수집"""
        try:
            # 성공/실패 에이전트 수 계산
            successful_agents = 0
            failed_agents = 0
            
            if result.get("status") == "completed":
                successful_agents = len(self.agents)
            else:
                failed_agents = 1  # 최소 1개 에이전트 실패
            
            # 파일 크기 추정
            file_size = 0
            if result.get("raw_content"):
                file_size = len(result["raw_content"])
            
            workflow_data = {
                "total_processing_time": processing_time,
                "agents_executed": len(self.agents),
                "successful_agents": successful_agents,
                "failed_agents": failed_agents,
                "memory_peak": 0,  # 추후 구현
                "avg_cpu_usage": 0.0,  # 추후 구현
                "file_size": file_size,
                "total_chunks": result.get("total_chunks", 0)
            }
            
            await self.performance_collector.collect_workflow_metrics(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                workflow_data=workflow_data
            )
            
            self.log_step(result, f"워크플로우 성능 메트릭 수집 완료: {workflow_id}")
            
        except Exception as e:
            self.log_step(result, f"워크플로우 성능 메트릭 수집 실패: {e}", "error")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """워크플로우 상태 정보 반환"""
        return {
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "workflow_initialized": self.workflow is not None,
            "performance_collector_enabled": self.performance_collector is not None,
            "agents": {
                "pdf_processor": self.pdf_processor.name,
                "text_processor": self.text_processor.name,
                "table_processor": self.table_processor.name,
                "image_processor": self.image_processor.name,
                "markdown_processor": self.markdown_processor.name,
                "embedding_agent": self.embedding_agent.name
            }
        }
