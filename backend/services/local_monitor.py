"""
로컬 워크플로우 모니터링 시스템
LangFuse 대안으로 자체 구현한 모니터링 시스템
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalWorkflowMonitor:
    """로컬 파일 기반 워크플로우 모니터링"""
    
    def __init__(self):
        self.enabled = True
        self.log_dir = Path("logs/workflow")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.workflow_cache = {}  # 워크플로우 상태 캐시
        
        # 워크플로우 로거 초기화 (DB 백업용)
        self.workflow_logger = None
        self._initialize_workflow_logger()
        
        logger.info(f"로컬 워크플로우 모니터링 활성화: {self.log_dir}")
    
    def _initialize_workflow_logger(self):
        """워크플로우 로거 초기화 (DB 백업용)"""
        try:
            from services.workflow_logger import get_workflow_logger
            self.workflow_logger = get_workflow_logger()
            logger.debug("로컬 모니터에서 워크플로우 로거 초기화 완료")
        except Exception as e:
            logger.warning(f"워크플로우 로거 초기화 실패: {e}")
            self.workflow_logger = None
    
    @asynccontextmanager
    async def trace_workflow(self, workflow_name: str, metadata: Optional[Dict[str, Any]] = None):
        """워크플로우 전체를 추적하는 컨텍스트 매니저"""
        workflow_id = f"{workflow_name}_{self.current_session}_{datetime.now().strftime('%H%M%S')}"
        
        try:
            trace_metadata = {
                "workflow_name": workflow_name,
                "workflow_id": workflow_id,
                "start_time": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            trace = LocalWorkflowTrace(self, workflow_id, workflow_name, trace_metadata)
            
            logger.info(f"워크플로우 추적 시작: {workflow_name} (ID: {workflow_id})")
            yield trace
            
            # 워크플로우 완료 로그
            trace.update(
                metadata={
                    **trace_metadata,
                    "end_time": datetime.now().isoformat(),
                    "status": "completed"
                }
            )
            logger.info(f"워크플로우 추적 완료: {workflow_name}")
            
        except Exception as e:
            logger.error(f"워크플로우 추적 중 오류: {e}")
            if 'trace' in locals():
                trace.update(
                    metadata={
                        **trace_metadata,
                        "end_time": datetime.now().isoformat(),
                        "status": "error",
                        "error": str(e)
                    }
                )
            yield LocalWorkflowTrace(self, workflow_id, workflow_name, {"error": str(e)})
    
    async def trace_agent_execution(
        self, 
        agent_name: str, 
        input_data: Dict[str, Any],
        parent_trace=None
    ):
        """개별 에이전트 실행을 추적"""
        try:
            span_data = {
                "name": f"{agent_name}_execution",
                "input": self._sanitize_data(input_data),
                "metadata": {
                    "agent": agent_name,
                    "start_time": datetime.now().isoformat(),
                    "parent_workflow": parent_trace.workflow_id if parent_trace else None
                }
            }
            
            span = LocalAgentSpan(self, agent_name, span_data)
            logger.debug(f"에이전트 실행 추적 시작: {agent_name}")
            return span
            
        except Exception as e:
            logger.error(f"에이전트 추적 생성 실패: {e}")
            return LocalAgentSpan(self, agent_name, {"error": str(e)})
    
    async def update_agent_result(
        self, 
        span, 
        output_data: Dict[str, Any], 
        execution_time: float,
        status: str = "completed"
    ):
        """에이전트 실행 결과 업데이트"""
        try:
            span.update(
                output=self._sanitize_data(output_data),
                metadata={
                    "end_time": datetime.now().isoformat(),
                    "execution_time": execution_time,
                    "status": status
                }
            )
            logger.debug(f"에이전트 실행 결과 업데이트 완료: {status}")
            
        except Exception as e:
            logger.error(f"에이전트 결과 업데이트 실패: {e}")
    
    async def log_metrics(self, metrics: Dict[str, Any]):
        """성능 메트릭 로깅 (파일 + DB 백업)"""
        try:
            # 파일에 로깅
            metrics_file = self.log_dir / f"metrics_{self.current_session}.jsonl"
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "metrics",
                **metrics
            }
            
            with open(metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            logger.debug("성능 메트릭 로깅 완료")
            
        except Exception as e:
            logger.error(f"메트릭 로깅 실패: {e}")
        
        # DB에도 백업 (파일 로깅 실패와 무관하게 실행)
        if self.workflow_logger and metrics.get("workflow_id"):
            try:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=metrics.get("workflow_id", "unknown"),
                    step_name=metrics.get("step_name", "metrics"),
                    status=metrics.get("status", "completed"),
                    input_data={"metrics": metrics},
                    execution_time=int(metrics.get("execution_time", 0) * 1000) if metrics.get("execution_time") else None
                )
            except Exception as e:
                logger.warning(f"로컬 DB 메트릭 백업 실패: {e}")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """민감한 정보 마스킹 및 데이터 크기 제한"""
        if not isinstance(data, dict):
            return {"data": str(data)[:1000]}
            
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                sanitized[key] = "***MASKED***"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[truncated]"
            elif isinstance(value, (list, dict)) and len(str(value)) > 2000:
                sanitized[key] = f"[Large object: {type(value).__name__}]"
            else:
                sanitized[key] = value
                
        return sanitized
    
    async def get_workflow_stats(self, workflow_name: Optional[str] = None) -> Dict[str, Any]:
        """워크플로우 통계 조회"""
        try:
            stats = {
                "workflow_name": workflow_name,
                "total_executions": 0,
                "avg_execution_time": 0,
                "success_rate": 100,
                "last_updated": datetime.now().isoformat(),
                "log_directory": str(self.log_dir)
            }
            
            # 로그 파일에서 통계 계산
            log_files = list(self.log_dir.glob("workflow_*.jsonl"))
            if log_files:
                stats["total_executions"] = len(log_files)
            
            return stats
            
        except Exception as e:
            logger.error(f"워크플로우 통계 조회 실패: {e}")
            return {"error": str(e)}
    
    async def get_workflow_executions(self) -> List[Dict[str, Any]]:
        """워크플로우 실행 목록 조회"""
        try:
            # 로컬 캐시에서 워크플로우 실행 데이터 반환
            executions = []
            for workflow_id, workflow_data in self.workflow_cache.items():
                execution = {
                    "workflow_id": workflow_id,
                    "document_name": workflow_data.get("document_name", f"문서-{workflow_id}"),
                    "status": workflow_data.get("status", "pending"),
                    "start_time": workflow_data.get("start_time", ""),
                    "end_time": workflow_data.get("end_time"),
                    "total_duration": workflow_data.get("total_duration", 0),
                    "agents": workflow_data.get("agents", [])
                }
                executions.append(execution)
            
            return executions
        except Exception as e:
            logger.error(f"로컬 워크플로우 실행 목록 조회 실패: {e}")
            return []
    
    def flush(self):
        """버퍼된 데이터 플러시 (로컬에서는 즉시 저장되므로 no-op)"""
        logger.debug("로컬 모니터 데이터 플러시 완료")


class LocalWorkflowTrace:
    """로컬 워크플로우 트레이스"""
    
    def __init__(self, monitor, workflow_id, name, metadata):
        self.monitor = monitor
        self.workflow_id = workflow_id
        self.name = name
        self.metadata = metadata
        self.log_file = monitor.log_dir / f"workflow_{workflow_id}.jsonl"
        
        # 워크플로우 시작 로그
        self._log_event("workflow_start", metadata)
    
    def create_span(self, **kwargs):
        """스팬 생성 (에이전트 실행)"""
        event_name = kwargs.get('name', 'span_event')
        self._log_event(event_name, kwargs.get('metadata', {}))
        return LocalAgentSpan(self.monitor, event_name, kwargs)
    
    def update(self, **kwargs):
        """워크플로우 업데이트"""
        self._log_event("workflow_update", kwargs.get('metadata', {}))
    
    def _log_event(self, event_type, data):
        """이벤트 로그 기록"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "workflow_id": self.workflow_id,
                "event_type": event_type,
                "data": data
            }
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"이벤트 로그 기록 실패: {e}")


class LocalAgentSpan:
    """로컬 에이전트 스팬"""
    
    def __init__(self, monitor, agent_name, span_data):
        self.monitor = monitor
        self.agent_name = agent_name
        self.span_data = span_data
        self.span_id = f"{agent_name}_{datetime.now().strftime('%H%M%S_%f')}"
        self.log_file = monitor.log_dir / f"agent_{self.span_id}.jsonl"
        
        # 에이전트 시작 로그
        self._log_event("agent_start", span_data)
    
    def update(self, **kwargs):
        """에이전트 결과 업데이트"""
        self._log_event("agent_end", kwargs)
    
    def _log_event(self, event_type, data):
        """이벤트 로그 기록"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "span_id": self.span_id,
                "agent_name": self.agent_name,
                "event_type": event_type,
                "data": data
            }
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"에이전트 로그 기록 실패: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.update(error=str(exc_val), status="error")


# 전역 로컬 모니터 인스턴스
local_monitor = LocalWorkflowMonitor()

