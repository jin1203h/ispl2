"""
LangFuse 모니터링 서비스
Multi-Agent 워크플로우 추적 및 성능 메트릭 수집
"""
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

try:
    from langfuse import Langfuse
    # LangFuse 3.x에서는 decorators 모듈 구조가 변경됨
    try:
        # from langfuse.decorators import observe  # LangFuse 3.5.1에서 사용하지 않음
        observe = None  # 현재 사용하지 않음
    except ImportError:
        # 3.x 버전에서는 observe가 다른 위치에 있을 수 있음
        observe = None
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logging.warning("LangFuse SDK not available. Install with: pip install langfuse")

logger = logging.getLogger(__name__)


class LangFuseMonitor:
    """LangFuse 기반 워크플로우 모니터링 서비스"""
    
    def __init__(self):
        self.langfuse = None
        self.enabled = False
        
        # 워크플로우 로거 초기화 (로컬 DB 백업용)
        self.workflow_logger = None
        self._initialize_workflow_logger()
        
        self._initialize_client()
    
    def _initialize_workflow_logger(self):
        """워크플로우 로거 초기화 (로컬 DB 백업용)"""
        try:
            from services.workflow_logger import get_workflow_logger
            self.workflow_logger = get_workflow_logger()
            logger.debug("LangFuse 모니터에서 워크플로우 로거 초기화 완료")
        except Exception as e:
            logger.warning(f"워크플로우 로거 초기화 실패: {e}")
            self.workflow_logger = None
    
    def _initialize_client(self):
        """LangFuse 클라이언트 초기화"""
        if not LANGFUSE_AVAILABLE:
            logger.warning("LangFuse SDK가 설치되지 않았습니다.")
            return
            
        try:
            secret_key = os.getenv('LANGFUSE_SECRET_KEY')
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
            
            if not secret_key or not public_key:
                logger.warning("LangFuse 인증 키가 설정되지 않았습니다. 모니터링이 비활성화됩니다.")
                return
            
            # SSL 인증서 설정 (certifi 활용)
            self._setup_ssl_certificates()
            
            # Self-hosted LangFuse 지원
            if host == "http://localhost:3001":
                logger.info("Self-hosted LangFuse 모드로 연결 시도")
            
            self.langfuse = Langfuse(
                secret_key=secret_key,
                public_key=public_key,
                host=host
            )
            
            # 연결 테스트
            self._test_connection()
            self.enabled = True
            logger.info(f"LangFuse 모니터링이 활성화되었습니다. Host: {host}")
            
        except Exception as e:
            logger.error(f"LangFuse 클라이언트 초기화 실패: {e}")
            self.enabled = False
    
    def _setup_ssl_certificates(self):
        """SSL 인증서 설정 (certifi 활용)"""
        try:
            import certifi
            import urllib3
            
            # certifi 번들 경로 설정
            ca_bundle_path = certifi.where()
            
            # 환경 변수 설정
            os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle_path
            os.environ['SSL_CERT_FILE'] = ca_bundle_path
            os.environ['CURL_CA_BUNDLE'] = ca_bundle_path
            
            # urllib3 경고 비활성화 (개발 환경용)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            logger.info(f"SSL 인증서 설정 완료: {ca_bundle_path}")
            
        except Exception as e:
            logger.warning(f"SSL 인증서 설정 실패: {e}")
            logger.info("기본 SSL 설정을 사용합니다.")
    
    def _test_connection(self):
        """LangFuse 연결 테스트"""
        if not self.langfuse:
            return False
            
        try:
            # LangFuse 3.5.1에서는 간단한 이벤트 생성으로 연결 테스트
            self.langfuse.create_event(
                name="connection_test",
                metadata={"test": True, "timestamp": datetime.now().isoformat()}
            )
            logger.info("LangFuse 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"LangFuse 연결 테스트 실패: {e}")
            raise
    
    @asynccontextmanager
    async def trace_workflow(self, workflow_name: str, metadata: Optional[Dict[str, Any]] = None):
        """워크플로우 전체를 추적하는 컨텍스트 매니저"""
        if not self.enabled:
            # LangFuse가 비활성화된 경우 더미 컨텍스트 반환
            yield DummyTrace()
            return
            
        try:
            trace_metadata = {
                "workflow_name": workflow_name,
                "start_time": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # LangFuse 3.5.1에서는 간단한 이벤트 기반 추적
            trace = WorkflowTrace(self.langfuse, workflow_name, trace_metadata)
            
            logger.info(f"워크플로우 추적 시작: {workflow_name}")
            yield trace
            
            # 워크플로우 완료 시 메타데이터 업데이트
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
            yield DummyTrace()
    
    async def trace_agent_execution(
        self, 
        agent_name: str, 
        input_data: Dict[str, Any],
        parent_trace=None
    ):
        """개별 에이전트 실행을 추적"""
        if not self.enabled:
            return DummySpan()
            
        try:
            span_data = {
                "name": f"{agent_name}_execution",
                "input": self._sanitize_data(input_data),
                "metadata": {
                    "agent": agent_name,
                    "start_time": datetime.now().isoformat()
                }
            }
            
            # LangFuse 3.5.1에서는 이벤트로 에이전트 실행 추적
            event_name = f"agent_{agent_name}_start"
            self.langfuse.create_event(
                name=event_name,
                metadata=span_data.get('metadata', {})
            )
            
            # 더미 스팬 반환 (실제로는 이벤트 기반)
            span = AgentSpan(self.langfuse, agent_name, span_data)
            
            logger.debug(f"에이전트 실행 추적 시작: {agent_name}")
            return span
            
        except Exception as e:
            logger.error(f"에이전트 추적 생성 실패: {e}")
            return DummySpan()
    
    async def update_agent_result(
        self, 
        span, 
        output_data: Dict[str, Any], 
        execution_time: float,
        status: str = "completed"
    ):
        """에이전트 실행 결과 업데이트"""
        if not self.enabled or isinstance(span, DummySpan):
            return
            
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
        """성능 메트릭 로깅 (LangFuse + 로컬 DB 백업)"""
        if not self.enabled:
            return
            
        try:
            # LangFuse 3.5.1에서는 create_event 사용
            self.langfuse.create_event(
                name="performance_metrics",
                metadata=metrics
            )
            logger.debug("성능 메트릭 로깅 완료")
            
        except Exception as e:
            logger.error(f"메트릭 로깅 실패: {e}")
        
        # 로컬 DB에도 백업 (LangFuse 실패와 무관하게 실행)
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
            return {"data": str(data)[:1000]}  # 문자열 길이 제한
            
        sanitized = {}
        for key, value in data.items():
            # 민감한 키워드 마스킹
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                sanitized[key] = "***MASKED***"
            elif isinstance(value, str) and len(value) > 1000:
                # 긴 문자열 자르기
                sanitized[key] = value[:1000] + "...[truncated]"
            elif isinstance(value, (list, dict)) and len(str(value)) > 2000:
                # 큰 객체 요약
                sanitized[key] = f"[Large object: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else 'unknown'} items]"
            else:
                sanitized[key] = value
                
        return sanitized
    
    async def get_workflow_stats(self, workflow_name: Optional[str] = None) -> Dict[str, Any]:
        """워크플로우 통계 조회 (LangFuse API 사용)"""
        if not self.enabled:
            return {"error": "LangFuse가 비활성화되어 있습니다."}
            
        try:
            # TODO: LangFuse API를 통한 통계 조회 구현
            # 현재는 기본 응답 반환
            return {
                "workflow_name": workflow_name,
                "total_executions": 0,
                "avg_execution_time": 0,
                "success_rate": 0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"워크플로우 통계 조회 실패: {e}")
            return {"error": str(e)}
    
    async def get_workflow_executions(self) -> List[Dict[str, Any]]:
        """워크플로우 실행 목록 조회 (LangFuse API 사용)"""
        if not self.enabled:
            return []
            
        try:
            # TODO: LangFuse API를 통한 워크플로우 실행 목록 조회 구현
            # 현재는 빈 리스트 반환
            return []
            
        except Exception as e:
            logger.error(f"워크플로우 실행 목록 조회 실패: {e}")
            return []
    
    def flush(self):
        """버퍼된 데이터를 LangFuse로 전송"""
        if self.enabled and self.langfuse:
            try:
                self.langfuse.flush()
                logger.debug("LangFuse 데이터 플러시 완료")
            except Exception as e:
                logger.error(f"LangFuse 플러시 실패: {e}")


class WorkflowTrace:
    """LangFuse 3.5.1 워크플로우 트레이스 래퍼"""
    
    def __init__(self, langfuse_client, name, metadata):
        self.langfuse = langfuse_client
        self.trace_id = self.langfuse.create_trace_id()
        self.name = name
        self.metadata = metadata
        
        # 워크플로우 시작 이벤트 생성
        self.langfuse.create_event(
            name=f"workflow_start_{name}",
            metadata=metadata
        )
        
    def create_span(self, **kwargs):
        # 스팬 대신 이벤트로 처리
        event_name = kwargs.get('name', 'span_event')
        self.langfuse.create_event(
            name=event_name,
            metadata=kwargs.get('metadata', {})
        )
        return DummySpan()
    
    def update(self, **kwargs):
        # 워크플로우 완료 이벤트 생성
        self.langfuse.create_event(
            name=f"workflow_end_{self.name}",
            metadata=kwargs.get('metadata', {})
        )


class DummyTrace:
    """LangFuse가 비활성화된 경우 사용하는 더미 트레이스"""
    
    def __init__(self):
        self.trace_id = "dummy_trace_id"
    
    def create_span(self, **kwargs):
        return DummySpan()
    
    def span(self, **kwargs):
        return DummySpan()
    
    def update(self, **kwargs):
        pass


class AgentSpan:
    """LangFuse 3.5.1 에이전트 스팬 래퍼"""
    
    def __init__(self, langfuse_client, agent_name, span_data):
        self.langfuse = langfuse_client
        self.agent_name = agent_name
        self.span_data = span_data
    
    def update(self, **kwargs):
        # 에이전트 완료 이벤트 생성
        event_name = f"agent_{self.agent_name}_end"
        self.langfuse.create_event(
            name=event_name,
            metadata={
                **kwargs,
                "status": kwargs.get("status", "completed")
            }
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class DummySpan:
    """LangFuse가 비활성화된 경우 사용하는 더미 스팬"""
    
    def update(self, **kwargs):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# 전역 모니터 인스턴스
langfuse_monitor = LangFuseMonitor()

# LangFuse 실패 시 로컬 모니터 사용
def get_monitor():
    """사용 가능한 모니터 반환 (LangFuse 우선, 실패 시 로컬)"""
    if langfuse_monitor.enabled:
        return langfuse_monitor
    else:
        from services.local_monitor import local_monitor
        logger.info("LangFuse 비활성화로 인해 로컬 모니터 사용")
        return local_monitor


# 데코레이터 함수들
def trace_workflow(workflow_name: str, metadata: Optional[Dict[str, Any]] = None):
    """워크플로우 추적 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with langfuse_monitor.trace_workflow(workflow_name, metadata) as trace:
                kwargs['_trace'] = trace
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def trace_agent(agent_name: str):
    """에이전트 실행 추적 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            # 부모 트레이스가 있는지 확인
            parent_trace = kwargs.get('_trace')
            input_data = kwargs.copy()
            input_data.pop('_trace', None)
            
            span = await langfuse_monitor.trace_agent_execution(
                agent_name, input_data, parent_trace
            )
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                await langfuse_monitor.update_agent_result(
                    span, result, execution_time, "completed"
                )
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                await langfuse_monitor.update_agent_result(
                    span, {"error": str(e)}, execution_time, "error"
                )
                raise
                
        return wrapper
    return decorator
