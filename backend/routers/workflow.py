"""
워크플로우 모니터링 API 라우터
기존 프론트엔드 workflowAPI와 완전 호환
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Pydantic 모델 - 기존 프론트엔드 API 호환
class WorkflowLog(BaseModel):
    log_id: int
    workflow_id: str
    step_name: str
    status: str
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: Optional[int] = None  # milliseconds
    created_at: str

# 임시 워크플로우 로그 데이터 (개발용)
TEMP_WORKFLOW_LOGS = [
    {
        "log_id": 1,
        "workflow_id": "wf-001-pdf-processing",
        "step_name": "PDF Analysis",
        "status": "completed",
        "input_data": {"file_name": "삼성화재_건강보험.pdf", "file_size": 2048576},
        "output_data": {"pages": 25, "has_text": True, "has_tables": True, "has_images": False},
        "error_message": None,
        "execution_time": 1250,
        "created_at": "2024-01-15T10:30:15"
    },
    {
        "log_id": 2,
        "workflow_id": "wf-001-pdf-processing",
        "step_name": "Text Extraction",
        "status": "completed",
        "input_data": {"pages": 25, "extraction_method": "pdfplumber"},
        "output_data": {"extracted_chars": 45678, "cleaned_text_length": 42156},
        "error_message": None,
        "execution_time": 890,
        "created_at": "2024-01-15T10:30:17"
    },
    {
        "log_id": 3,
        "workflow_id": "wf-001-pdf-processing",
        "step_name": "Table Processing",
        "status": "completed",
        "input_data": {"table_count": 3, "method": "camelot-py"},
        "output_data": {"structured_tables": 3, "total_cells": 156},
        "error_message": None,
        "execution_time": 1580,
        "created_at": "2024-01-15T10:30:19"
    },
    {
        "log_id": 4,
        "workflow_id": "wf-001-pdf-processing",
        "step_name": "Embedding Generation",
        "status": "completed",
        "input_data": {"chunk_count": 89, "model": "text-embedding-3-large"},
        "output_data": {"embeddings_created": 89, "dimensions": 3072},
        "error_message": None,
        "execution_time": 3450,
        "created_at": "2024-01-15T10:30:23"
    },
    {
        "log_id": 5,
        "workflow_id": "wf-002-search-query",
        "step_name": "Query Processing",
        "status": "completed",
        "input_data": {"query": "건강보험 보장범위", "user_id": 1},
        "output_data": {"processed_query": "건강보험 보장범위", "intent": "policy_inquiry"},
        "error_message": None,
        "execution_time": 120,
        "created_at": "2024-01-15T14:25:10"
    },
    {
        "log_id": 6,
        "workflow_id": "wf-002-search-query",
        "step_name": "Vector Search",
        "status": "completed",
        "input_data": {"query_embedding": "vector(3072)", "search_limit": 10},
        "output_data": {"matches_found": 5, "top_score": 0.89},
        "error_message": None,
        "execution_time": 450,
        "created_at": "2024-01-15T14:25:11"
    },
    {
        "log_id": 7,
        "workflow_id": "wf-003-error-case",
        "step_name": "PDF Analysis",
        "status": "error",
        "input_data": {"file_name": "corrupted_file.pdf"},
        "output_data": None,
        "error_message": "PDF 파일이 손상되었거나 읽을 수 없습니다.",
        "execution_time": 500,
        "created_at": "2024-01-15T16:45:22"
    }
]

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """토큰 검증 (인증이 필요한 엔드포인트용)"""
    from routers.auth import get_current_user
    return await get_current_user(credentials)

@router.get("/logs", response_model=List[WorkflowLog])
async def get_workflow_logs(
    workflow_id: Optional[str] = Query(None, description="특정 워크플로우 ID로 필터링"),
    current_user: dict = Depends(verify_token)
):
    """
    워크플로우 로그 조회
    기존 프론트엔드 workflowAPI.getLogs()와 호환
    """
    try:
        logger.info(f"워크플로우 로그 조회: workflow_id={workflow_id}")
        
        # TODO: 실제 데이터베이스 조회 로직 구현 필요
        # - LangFuse 데이터 동기화
        # - 필터링 및 정렬
        # - 페이지네이션
        
        # 임시 응답 (개발용)
        logs = TEMP_WORKFLOW_LOGS.copy()
        
        # 워크플로우 ID 필터링
        if workflow_id:
            logs = [log for log in logs if log["workflow_id"] == workflow_id]
        
        # 최신 순으로 정렬
        logs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return logs
        
    except Exception as e:
        logger.error(f"워크플로우 로그 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="워크플로우 로그 조회 중 오류가 발생했습니다."
        )

@router.get("/logs/summary")
async def get_workflow_summary(
    current_user: dict = Depends(verify_token)
):
    """
    워크플로우 실행 요약 정보
    대시보드용 통계 데이터
    """
    try:
        logger.info("워크플로우 요약 정보 조회")
        
        # TODO: 실제 통계 계산 로직 구현 필요
        
        # 임시 요약 데이터 (개발용)
        logs = TEMP_WORKFLOW_LOGS.copy()
        
        total_workflows = len(set(log["workflow_id"] for log in logs))
        completed_steps = len([log for log in logs if log["status"] == "completed"])
        error_steps = len([log for log in logs if log["status"] == "error"])
        running_steps = len([log for log in logs if log["status"] == "running"])
        
        avg_execution_time = sum(
            log["execution_time"] for log in logs 
            if log["execution_time"] is not None
        ) / len([log for log in logs if log["execution_time"] is not None])
        
        return {
            "total_workflows": total_workflows,
            "total_steps": len(logs),
            "completed_steps": completed_steps,
            "error_steps": error_steps,
            "running_steps": running_steps,
            "success_rate": round(completed_steps / len(logs) * 100, 2),
            "avg_execution_time": round(avg_execution_time, 2),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"워크플로우 요약 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="워크플로우 요약 조회 중 오류가 발생했습니다."
        )
