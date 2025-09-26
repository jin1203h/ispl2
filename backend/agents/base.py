"""
Base Agent 클래스 및 공통 타입 정의
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict, Union
from enum import Enum
import logging

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
    
    @abstractmethod
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        상태를 받아서 처리하고 업데이트된 상태를 반환
        """
        pass
    
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


