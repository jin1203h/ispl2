"""
Pydantic 스키마 모델
API 요청/응답 모델 정의
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime

# 사용자 관련 스키마
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "USER"

class UserResponse(BaseModel):
    user_id: int
    email: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# 약관 관련 스키마
class PolicyCreate(BaseModel):
    company: str
    category: str
    product_type: str
    product_name: str
    sale_start_dt: Optional[str] = None
    sale_end_dt: Optional[str] = None
    sale_stat: Optional[str] = None
    summary: Optional[str] = None
    security_level: str = "public"

class PolicyResponse(BaseModel):
    policy_id: int
    company: Optional[str]
    category: Optional[str]
    product_type: Optional[str]
    product_name: str
    summary: Optional[str]
    created_at: datetime
    security_level: Optional[str]
    
    class Config:
        from_attributes = True

class PolicyUploadResponse(BaseModel):
    message: str
    policy_id: int
    summary: Optional[str] = None

# 검색 관련 스키마
class SearchRequest(BaseModel):
    query: str = Field(..., description="검색 질의")
    policy_ids: Optional[List[int]] = Field(None, description="검색 대상 약관 ID 목록")
    limit: int = Field(10, ge=1, le=50, description="검색 결과 최대 개수")
    security_level: str = Field("public", description="보안 등급")

class SearchResult(BaseModel):
    policy_id: int
    policy_name: str
    company: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    matched_text: str
    page_number: Optional[int] = None

class SearchResponse(BaseModel):
    answer: str
    results: List[SearchResult]

# 워크플로우 관련 스키마
class WorkflowLogResponse(BaseModel):
    log_id: int
    workflow_id: str
    step_name: str
    status: str
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorkflowSummary(BaseModel):
    total_workflows: int
    total_steps: int
    completed_steps: int
    error_steps: int
    running_steps: int
    success_rate: float
    avg_execution_time: float
    last_updated: datetime

# 임베딩 관련 스키마
class EmbeddingCreate(BaseModel):
    policy_id: int
    chunk_text: str
    chunk_index: int
    model: str
    embedding: List[float]

class EmbeddingResponse(BaseModel):
    id: int
    policy_id: int
    chunk_text: str
    chunk_index: int
    model: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 공통 응답 스키마
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

# 파일 업로드 관련 스키마
class FileUploadRequest(BaseModel):
    company: str
    category: str
    product_type: str
    product_name: str
    security_level: str = "public"

# 페이지네이션 스키마
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

# 헬스체크 스키마
class HealthCheckResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.now)


