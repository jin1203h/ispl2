"""
워크플로우 모니터링 API 라우터
기존 프론트엔드 workflowAPI와 완전 호환
LangFuse 모니터링 시스템 통합
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Any
import logging
from datetime import datetime

from services.langfuse_monitor import get_monitor
from services.workflow_logger import get_workflow_logger

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
        
        # 실제 데이터베이스에서 워크플로우 로그 조회
        workflow_logger = get_workflow_logger()
        logs = await workflow_logger.get_workflow_logs(
            workflow_id=workflow_id,
            limit=100
        )
        
        # 데이터베이스에 데이터가 없으면 임시 데이터 사용 (개발용)
        if not logs:
            logger.warning("데이터베이스에 워크플로우 로그가 없음, 임시 데이터 사용")
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
    대시보드용 통계 데이터 (LangFuse 통합)
    """
    try:
        logger.info("워크플로우 요약 정보 조회")
        
        # 실제 데이터베이스에서 워크플로우 요약 조회
        workflow_logger = get_workflow_logger()
        summary = await workflow_logger.get_workflow_summary()
        
        # 활성 모니터에서 통계 조회 시도
        monitor = get_monitor()
        monitor_stats = await monitor.get_workflow_stats()
        
        # 데이터베이스 요약에 모니터 정보 추가
        if summary and not summary.get("error"):
            summary.update({
                "monitor_type": "langfuse" if hasattr(monitor, 'langfuse') else "local",
                "monitor_enabled": getattr(monitor, 'enabled', True),
                "monitor_stats": monitor_stats
            })
        else:
            # 데이터베이스 조회 실패 시 임시 데이터 사용
            logger.warning("데이터베이스 요약 조회 실패, 임시 데이터 사용")
            logs = TEMP_WORKFLOW_LOGS.copy()
            
            total_workflows = len(set(log["workflow_id"] for log in logs))
            completed_steps = len([log for log in logs if log["status"] == "completed"])
            error_steps = len([log for log in logs if log["status"] == "error"])
            running_steps = len([log for log in logs if log["status"] == "running"])
            
            avg_execution_time = sum(
                log["execution_time"] for log in logs 
                if log["execution_time"] is not None
            ) / len([log for log in logs if log["execution_time"] is not None])
            
            summary = {
                "total_workflows": total_workflows,
                "total_steps": len(logs),
                "completed_steps": completed_steps,
                "error_steps": error_steps,
                "running_steps": running_steps,
                "success_rate": round(completed_steps / len(logs) * 100, 2),
                "avg_execution_time": round(avg_execution_time / 1000, 2),  # ms -> s
                "last_updated": datetime.now().isoformat(),
                "monitor_type": "langfuse" if hasattr(monitor, 'langfuse') else "local",
                "monitor_enabled": getattr(monitor, 'enabled', True),
                "monitor_stats": monitor_stats,
                "data_source": "fallback"
            }
        
        return summary
        
    except Exception as e:
        logger.error(f"워크플로우 요약 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="워크플로우 요약 조회 중 오류가 발생했습니다."
        )

@router.get("/executions")
async def get_workflow_executions(
    status_filter: Optional[str] = Query(None, description="상태 필터 (pending/running/completed/failed)"),
    limit: int = Query(50, description="조회할 실행 수", ge=1, le=100),
    current_user: dict = Depends(verify_token)
):
    """
    워크플로우 실행 목록 조회 (프론트엔드 WorkflowMonitoring용)
    """
    return await _get_workflow_executions_impl(status_filter, limit)

@router.get("/executions/demo")
async def get_workflow_executions_demo(
    status_filter: Optional[str] = Query(None, description="상태 필터 (pending/running/completed/failed)"),
    limit: int = Query(50, description="조회할 실행 수", ge=1, le=100)
):
    """
    워크플로우 실행 목록 조회 (데모용, 인증 불필요)
    """
    return await _get_workflow_executions_impl(status_filter, limit)

async def _get_workflow_executions_impl(status_filter: Optional[str], limit: int):
    """
    워크플로우 실행 목록 조회 구현 (공통 로직)
    """
    try:
        logger.info(f"워크플로우 실행 목록 조회: status={status_filter}, limit={limit}")
        
        # 실제 데이터베이스에서 워크플로우 실행 목록 조회
        workflow_logger = get_workflow_logger()
        db_executions = await workflow_logger.get_workflow_executions(
            status_filter=status_filter,
            limit=limit
        )
        
        # 데이터베이스에 데이터가 있으면 사용
        if db_executions:
            logger.info(f"데이터베이스에서 {len(db_executions)}개 워크플로우 실행 조회")
            return {
                "success": True,
                "data": {
                    "workflow_executions": db_executions,
                    "total_count": len(db_executions),
                    "filtered_by": status_filter,
                    "data_source": "database"
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # 데이터베이스에 데이터가 없으면 모니터와 임시 데이터 사용
        logger.warning("데이터베이스에 워크플로우 실행 데이터가 없음, 임시 데이터 사용")
        
        # 활성 모니터에서 실제 데이터 조회 시도
        monitor = get_monitor()
        
        # LangFuse나 로컬 모니터에서 워크플로우 실행 데이터 가져오기
        try:
            workflow_data = await monitor.get_workflow_executions()
        except Exception as e:
            logger.warning(f"모니터에서 워크플로우 데이터 조회 실패: {e}")
            workflow_data = []
        
        # 임시 데이터를 실제 워크플로우 실행 형태로 변환
        temp_executions = []
        workflows = {}
        
        # TEMP_WORKFLOW_LOGS를 워크플로우별로 그룹화
        for log in TEMP_WORKFLOW_LOGS:
            wf_id = log["workflow_id"]
            if wf_id not in workflows:
                workflows[wf_id] = {
                    "workflow_id": wf_id,
                    "document_name": log["input_data"].get("file_name", f"문서-{wf_id}") if log["input_data"] else f"문서-{wf_id}",
                    "status": "pending",
                    "start_time": log["created_at"],
                    "end_time": None,
                    "total_duration": 0,
                    "agents": []
                }
            
            # 에이전트 정보 추가
            agent_info = {
                "agent_name": log["step_name"],
                "name": log["step_name"],
                "status": log["status"],
                "start_time": log["created_at"],
                "end_time": log["created_at"] if log["status"] == "completed" else None,
                "execution_time": log["execution_time"] / 1000 if log["execution_time"] else None,  # ms -> s
                "input_data": log["input_data"],
                "output_data": log["output_data"],
                "error_message": log["error_message"]
            }
            workflows[wf_id]["agents"].append(agent_info)
            
            # 워크플로우 총 실행 시간 계산
            if log["execution_time"]:
                workflows[wf_id]["total_duration"] += log["execution_time"] / 1000
        
        # 워크플로우 상태 결정
        for wf_id, workflow in workflows.items():
            agents = workflow["agents"]
            if any(agent["status"] == "error" for agent in agents):
                workflow["status"] = "failed"
            elif all(agent["status"] == "completed" for agent in agents):
                workflow["status"] = "completed"
                # 마지막 에이전트의 종료 시간을 워크플로우 종료 시간으로 설정
                last_agent = max(agents, key=lambda a: a["start_time"] if a["start_time"] else "")
                workflow["end_time"] = last_agent.get("end_time")
            elif any(agent["status"] == "running" for agent in agents):
                workflow["status"] = "running"
            else:
                workflow["status"] = "pending"
        
        # 리스트로 변환
        temp_executions = list(workflows.values())
        
        # 실제 모니터 데이터와 임시 데이터 병합
        all_executions = workflow_data + temp_executions
        
        # 상태 필터링
        if status_filter:
            all_executions = [exec for exec in all_executions if exec.get("status") == status_filter]
        
        # 최신 순으로 정렬
        all_executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        # 제한 적용
        all_executions = all_executions[:limit]
        
        return {
            "success": True,
            "data": {
                "workflow_executions": all_executions,
                "total_count": len(all_executions),
                "filtered_by": status_filter,
                "monitor_type": "langfuse" if hasattr(monitor, 'langfuse') else "local",
                "data_source": "fallback"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"워크플로우 실행 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"워크플로우 실행 목록 조회 실패: {str(e)}"
        )


@router.get("/langfuse/status")
async def get_langfuse_status(
    current_user: dict = Depends(verify_token)
):
    """
    LangFuse 모니터링 시스템 상태 확인
    """
    try:
        monitor = get_monitor()
        return {
            "enabled": getattr(monitor, 'enabled', False),
            "host": getattr(getattr(monitor, 'langfuse', None), 'host', None) if hasattr(monitor, 'langfuse') else None,
            "status": "connected" if getattr(monitor, 'enabled', False) else "disconnected",
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"LangFuse 상태 확인 오류: {e}")
        return {
            "enabled": False,
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


@router.post("/test/trace")
async def create_test_trace(
    current_user: dict = Depends(verify_token)
):
    """
    LangFuse 연결 테스트용 트레이스 생성
    """
    try:
        logger.info("테스트 트레이스 생성 시작")
        
        monitor = get_monitor()
        async with monitor.trace_workflow(
            "test_workflow", 
            {"test": True, "user": current_user.get("email", "unknown")}
        ) as trace:
            
            # 테스트 에이전트 실행 시뮬레이션
            import time
            import asyncio
            
            span = await monitor.trace_agent_execution(
                "test_agent",
                {"input": "test_data", "timestamp": datetime.now().isoformat()},
                trace
            )
            
            # 짧은 처리 시간 시뮬레이션
            await asyncio.sleep(0.1)
            
            await monitor.update_agent_result(
                span,
                {"output": "test_result", "processed": True},
                0.1,
                "completed"
            )
            
            # 메트릭 로깅 테스트
            await monitor.log_metrics({
                "test_metric": 1.0,
                "execution_time": 0.1,
                "status": "success"
            })
        
        return {
            "success": True,
            "message": "테스트 트레이스가 성공적으로 생성되었습니다.",
            "langfuse_enabled": getattr(monitor, 'enabled', False),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"테스트 트레이스 생성 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 트레이스 생성 실패: {str(e)}"
        )
