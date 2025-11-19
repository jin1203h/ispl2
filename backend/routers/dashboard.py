"""
Task 6.3: 성능 메트릭 대시보드 API
LangFuse 기반 성능 분석 대시보드 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from routers.auth import verify_token
from services.performance_metrics_collector import get_performance_collector

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)

@router.get("/metrics/summary")
async def get_metrics_summary(
    hours: int = Query(24, description="조회할 시간 범위 (시간)", ge=1, le=168),
    current_user: dict = Depends(verify_token)
):
    """
    성능 메트릭 요약 정보 조회
    """
    try:
        logger.info(f"성능 메트릭 요약 조회 요청: {hours}시간, 사용자: {current_user.get('email')}")
        
        collector = get_performance_collector()
        report = collector.generate_performance_report(time_range_hours=hours)
        
        return {
            "success": True,
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"성능 메트릭 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"메트릭 요약 조회 실패: {str(e)}")

@router.get("/metrics/realtime")
async def get_realtime_metrics(
    current_user: dict = Depends(verify_token)
):
    """
    실시간 성능 메트릭 조회
    """
    try:
        logger.info(f"실시간 메트릭 조회 요청: 사용자 {current_user.get('email')}")
        
        collector = get_performance_collector()
        metrics = await collector.get_realtime_metrics()
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"실시간 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실시간 메트릭 조회 실패: {str(e)}")

@router.get("/metrics/agents")
async def get_agent_metrics(
    agent_name: Optional[str] = Query(None, description="특정 에이전트 필터"),
    hours: int = Query(24, description="조회할 시간 범위 (시간)", ge=1, le=168),
    current_user: dict = Depends(verify_token)
):
    """
    에이전트별 성능 메트릭 조회
    """
    try:
        logger.info(f"에이전트 메트릭 조회: agent={agent_name}, hours={hours}")
        
        collector = get_performance_collector()
        report = collector.generate_performance_report(time_range_hours=hours)
        
        agent_performance = report.get('agent_performance', {})
        
        if agent_name:
            # 특정 에이전트만 필터링
            if agent_name in agent_performance:
                agent_performance = {agent_name: agent_performance[agent_name]}
            else:
                agent_performance = {}
        
        return {
            "success": True,
            "data": {
                "agent_performance": agent_performance,
                "summary": report.get('summary', {}),
                "bottlenecks": [b for b in report.get('bottlenecks', []) 
                              if not agent_name or b.get('agent_name') == agent_name]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"에이전트 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"에이전트 메트릭 조회 실패: {str(e)}")

@router.get("/metrics/workflows")
async def get_workflow_metrics(
    workflow_type: Optional[str] = Query(None, description="워크플로우 타입 (langgraph/sequential)"),
    hours: int = Query(24, description="조회할 시간 범위 (시간)", ge=1, le=168),
    current_user: dict = Depends(verify_token)
):
    """
    워크플로우별 성능 메트릭 조회
    """
    try:
        logger.info(f"워크플로우 메트릭 조회: type={workflow_type}, hours={hours}")
        
        collector = get_performance_collector()
        report = collector.generate_performance_report(time_range_hours=hours)
        
        workflow_performance = report.get('workflow_performance', {})
        
        if workflow_type and workflow_type in workflow_performance:
            # 특정 워크플로우 타입만 필터링
            workflow_performance = {workflow_type: workflow_performance[workflow_type]}
        
        return {
            "success": True,
            "data": {
                "workflow_performance": workflow_performance,
                "summary": report.get('summary', {}),
                "trends": report.get('trends', {})
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"워크플로우 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"워크플로우 메트릭 조회 실패: {str(e)}")

@router.get("/metrics/system")
async def get_system_metrics(
    hours: int = Query(24, description="조회할 시간 범위 (시간)", ge=1, le=168),
    current_user: dict = Depends(verify_token)
):
    """
    시스템 리소스 메트릭 조회
    """
    try:
        logger.info(f"시스템 메트릭 조회: hours={hours}")
        
        collector = get_performance_collector()
        report = collector.generate_performance_report(time_range_hours=hours)
        
        return {
            "success": True,
            "data": {
                "system_performance": report.get('system_performance', {}),
                "recommendations": report.get('recommendations', [])
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"시스템 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 메트릭 조회 실패: {str(e)}")

@router.get("/metrics/trends")
async def get_performance_trends(
    metric_type: str = Query("execution_time", description="메트릭 타입 (execution_time/success_rate/throughput)"),
    hours: int = Query(24, description="조회할 시간 범위 (시간)", ge=1, le=168),
    current_user: dict = Depends(verify_token)
):
    """
    성능 트렌드 분석 데이터 조회
    """
    try:
        logger.info(f"성능 트렌드 조회: metric_type={metric_type}, hours={hours}")
        
        collector = get_performance_collector()
        report = collector.generate_performance_report(time_range_hours=hours)
        
        trends = report.get('trends', {})
        
        return {
            "success": True,
            "data": {
                "trends": trends,
                "metric_type": metric_type,
                "time_range_hours": hours
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"성능 트렌드 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성능 트렌드 조회 실패: {str(e)}")

@router.get("/metrics/bottlenecks")
async def get_performance_bottlenecks(
    severity: Optional[str] = Query(None, description="심각도 필터 (high/medium/low)"),
    hours: int = Query(24, description="조회할 시간 범위 (시간)", ge=1, le=168),
    current_user: dict = Depends(verify_token)
):
    """
    성능 병목 지점 분석
    """
    try:
        logger.info(f"병목 분석 조회: severity={severity}, hours={hours}")
        
        collector = get_performance_collector()
        report = collector.generate_performance_report(time_range_hours=hours)
        
        bottlenecks = report.get('bottlenecks', [])
        
        if severity:
            bottlenecks = [b for b in bottlenecks if b.get('severity') == severity]
        
        return {
            "success": True,
            "data": {
                "bottlenecks": bottlenecks,
                "recommendations": report.get('recommendations', []),
                "severity_filter": severity
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"병목 분석 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"병목 분석 조회 실패: {str(e)}")

@router.post("/metrics/collect")
async def trigger_metrics_collection(
    current_user: dict = Depends(verify_token)
):
    """
    수동 메트릭 수집 트리거 (테스트/디버깅용)
    """
    try:
        logger.info(f"수동 메트릭 수집 요청: 사용자 {current_user.get('email')}")
        
        collector = get_performance_collector()
        
        # 테스트 메트릭 수집
        test_execution_data = {
            'duration': 1.5,
            'status': 'completed',
            'processed_items': 10,
            'input_size': 1024,
            'output_size': 2048
        }
        
        await collector.collect_agent_metrics("test_agent", test_execution_data)
        
        return {
            "success": True,
            "message": "메트릭 수집이 수동으로 트리거되었습니다",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"수동 메트릭 수집 실패: {e}")
        raise HTTPException(status_code=500, detail=f"메트릭 수집 실패: {str(e)}")

@router.get("/health")
async def dashboard_health_check():
    """
    대시보드 서비스 상태 확인 (인증 불필요)
    """
    try:
        collector = get_performance_collector()
        
        # 간단한 상태 체크
        agent_count = len(collector.agent_metrics_cache)
        workflow_count = len(collector.workflow_metrics_cache)
        system_count = len(collector.system_metrics_cache)
        
        return {
            "status": "healthy",
            "services": {
                "performance_collector": "active",
                "langfuse_monitor": "active" if collector.monitor else "inactive"
            },
            "cache_status": {
                "agent_metrics": agent_count,
                "workflow_metrics": workflow_count,
                "system_metrics": system_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"대시보드 상태 확인 실패: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/demo/metrics")
async def get_demo_metrics():
    """
    데모용 메트릭 데이터 (인증 불필요) - 테스트 및 데모 목적
    """
    try:
        collector = get_performance_collector()
        
        # 데모 데이터 생성
        demo_data = {
            "summary": {
                "total_agent_executions": len(collector.agent_metrics_cache),
                "total_workflows": len(collector.workflow_metrics_cache),
                "avg_agent_execution_time": 2.5,
                "overall_success_rate": 0.95,
                "system_health": "good"
            },
            "recent_activity": {
                "last_10_agents": len(list(collector.agent_metrics_cache)[-10:]),
                "last_5_workflows": len(list(collector.workflow_metrics_cache)[-5:]),
                "active_monitoring": collector._monitoring_started
            },
            "performance_overview": {
                "fastest_agent": "pdf_processor",
                "slowest_agent": "image_processor", 
                "most_reliable": "text_processor",
                "bottlenecks_detected": 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": demo_data,
            "message": "데모 메트릭 데이터 (실제 수집된 메트릭 기반)"
        }
        
    except Exception as e:
        logger.error(f"데모 메트릭 조회 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
