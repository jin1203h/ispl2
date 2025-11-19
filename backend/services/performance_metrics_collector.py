"""
Task 6.3: 성능 메트릭 수집 및 분석 서비스
LangFuse 기반 Multi-Agent 워크플로우 성능 분석 시스템
"""
import time
import psutil
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
import statistics

from services.langfuse_monitor import get_monitor

logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """에이전트별 성능 메트릭"""
    agent_name: str
    execution_time: float
    memory_usage: int  # bytes
    success_rate: float
    error_count: int
    throughput: float  # items/second
    timestamp: datetime
    input_size: int = 0
    output_size: int = 0
    cpu_usage: float = 0.0

@dataclass
class WorkflowMetrics:
    """워크플로우 전체 성능 메트릭"""
    workflow_id: str
    workflow_type: str  # "langgraph", "sequential"
    total_execution_time: float
    total_agents: int
    successful_agents: int
    failed_agents: int
    total_memory_peak: int
    avg_cpu_usage: float
    timestamp: datetime
    file_size: int = 0
    chunks_processed: int = 0

@dataclass
class SystemMetrics:
    """시스템 리소스 메트릭"""
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_available: int
    disk_usage_percent: float
    timestamp: datetime

class PerformanceMetricsCollector:
    """성능 메트릭 수집 및 분석 클래스"""
    
    def __init__(self, cache_size: int = 1000):
        self.monitor = get_monitor()
        self.cache_size = cache_size
        
        # 메트릭 캐시 (rolling window)
        self.agent_metrics_cache: deque = deque(maxlen=cache_size)
        self.workflow_metrics_cache: deque = deque(maxlen=cache_size)
        self.system_metrics_cache: deque = deque(maxlen=cache_size)
        
        # 에이전트별 누적 통계
        self.agent_stats: Dict[str, Dict] = defaultdict(lambda: {
            'total_executions': 0,
            'total_execution_time': 0.0,
            'success_count': 0,
            'error_count': 0,
            'avg_memory': 0.0,
            'last_updated': datetime.now()
        })
        
        # 시스템 모니터링 태스크 (lazy initialization)
        self._system_monitoring_task = None
        self._monitoring_started = False
        
        logger.info("PerformanceMetricsCollector 초기화 완료")
    
    def _ensure_monitoring_started(self):
        """시스템 모니터링이 시작되었는지 확인하고 필요시 시작"""
        if self._monitoring_started:
            return
        
        try:
            # 현재 실행 중인 이벤트 루프가 있는지 확인
            loop = asyncio.get_running_loop()
            if loop and not self._monitoring_started:
                self._system_monitoring_task = loop.create_task(self._monitor_system())
                self._monitoring_started = True
                logger.info("시스템 모니터링 백그라운드 태스크 시작")
        except RuntimeError:
            # 실행 중인 이벤트 루프가 없으면 나중에 시작
            logger.debug("이벤트 루프가 아직 실행되지 않음 - 시스템 모니터링 지연 시작")
    
    async def _monitor_system(self):
        """시스템 메트릭 모니터링 백그라운드 태스크"""
        while True:
            try:
                metrics = SystemMetrics(
                    cpu_percent=psutil.cpu_percent(interval=1),
                    memory_percent=psutil.virtual_memory().percent,
                    memory_used=psutil.virtual_memory().used,
                    memory_available=psutil.virtual_memory().available,
                    disk_usage_percent=psutil.disk_usage('/').percent,
                    timestamp=datetime.now()
                )
                self.system_metrics_cache.append(metrics)
                await asyncio.sleep(30)  # 30초마다 수집
            except Exception as e:
                logger.error(f"시스템 메트릭 수집 오류: {e}")
                await asyncio.sleep(60)
    
    async def collect_agent_metrics(self, 
                                  agent_name: str, 
                                  execution_data: Dict[str, Any]) -> AgentMetrics:
        """에이전트 실행 메트릭 수집"""
        try:
            # 시스템 모니터링 시작 확인
            self._ensure_monitoring_started()
            
            # 현재 시스템 상태 수집
            process = psutil.Process()
            
            metrics = AgentMetrics(
                agent_name=agent_name,
                execution_time=execution_data.get('duration', 0.0),
                memory_usage=process.memory_info().rss,
                success_rate=1.0 if execution_data.get('status') == 'completed' else 0.0,
                error_count=1 if execution_data.get('status') == 'failed' else 0,
                throughput=self._calculate_throughput(execution_data),
                timestamp=datetime.now(),
                input_size=execution_data.get('input_size', 0),
                output_size=execution_data.get('output_size', 0),
                cpu_usage=psutil.cpu_percent()
            )
            
            # 캐시에 저장
            self.agent_metrics_cache.append(metrics)
            
            # 누적 통계 업데이트
            self._update_agent_stats(agent_name, metrics)
            
            # LangFuse에 메트릭 전송
            await self._send_metrics_to_langfuse(metrics)
            
            logger.debug(f"에이전트 메트릭 수집 완료: {agent_name}")
            return metrics
            
        except Exception as e:
            logger.error(f"에이전트 메트릭 수집 실패 [{agent_name}]: {e}")
            return None
    
    async def collect_workflow_metrics(self, 
                                     workflow_id: str,
                                     workflow_type: str,
                                     workflow_data: Dict[str, Any]) -> WorkflowMetrics:
        """워크플로우 전체 메트릭 수집"""
        try:
            # 시스템 모니터링 시작 확인
            self._ensure_monitoring_started()
            metrics = WorkflowMetrics(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                total_execution_time=workflow_data.get('total_processing_time', 0.0),
                total_agents=workflow_data.get('agents_executed', 0),
                successful_agents=workflow_data.get('successful_agents', 0),
                failed_agents=workflow_data.get('failed_agents', 0),
                total_memory_peak=workflow_data.get('memory_peak', 0),
                avg_cpu_usage=workflow_data.get('avg_cpu_usage', 0.0),
                timestamp=datetime.now(),
                file_size=workflow_data.get('file_size', 0),
                chunks_processed=workflow_data.get('total_chunks', 0)
            )
            
            # 캐시에 저장
            self.workflow_metrics_cache.append(metrics)
            
            # LangFuse에 워크플로우 메트릭 전송
            await self._send_workflow_metrics_to_langfuse(metrics)
            
            logger.info(f"워크플로우 메트릭 수집 완료: {workflow_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"워크플로우 메트릭 수집 실패 [{workflow_id}]: {e}")
            return None
    
    def _calculate_throughput(self, execution_data: Dict[str, Any]) -> float:
        """처리량 계산"""
        duration = execution_data.get('duration', 1.0)
        processed_items = execution_data.get('processed_items', 0)
        
        if duration > 0:
            return processed_items / duration
        return 0.0
    
    def _update_agent_stats(self, agent_name: str, metrics: AgentMetrics):
        """에이전트 누적 통계 업데이트"""
        stats = self.agent_stats[agent_name]
        
        stats['total_executions'] += 1
        stats['total_execution_time'] += metrics.execution_time
        
        if metrics.success_rate > 0:
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1
        
        # 이동 평균으로 메모리 사용량 계산
        if stats['avg_memory'] == 0:
            stats['avg_memory'] = metrics.memory_usage
        else:
            stats['avg_memory'] = (stats['avg_memory'] * 0.9) + (metrics.memory_usage * 0.1)
        
        stats['last_updated'] = datetime.now()
    
    async def _send_metrics_to_langfuse(self, metrics: AgentMetrics):
        """LangFuse에 에이전트 메트릭 전송"""
        if not self.monitor:
            return
        
        try:
            await self.monitor.log_metrics({
                'metric_type': 'agent_performance',
                'agent_name': metrics.agent_name,
                'execution_time': metrics.execution_time,
                'memory_usage_mb': metrics.memory_usage / (1024 * 1024),
                'success_rate': metrics.success_rate,
                'throughput': metrics.throughput,
                'cpu_usage': metrics.cpu_usage,
                'timestamp': metrics.timestamp.isoformat()
            })
        except Exception as e:
            logger.error(f"LangFuse 메트릭 전송 실패: {e}")
    
    async def _send_workflow_metrics_to_langfuse(self, metrics: WorkflowMetrics):
        """LangFuse에 워크플로우 메트릭 전송"""
        if not self.monitor:
            return
        
        try:
            await self.monitor.log_metrics({
                'metric_type': 'workflow_performance',
                'workflow_id': metrics.workflow_id,
                'workflow_type': metrics.workflow_type,
                'total_execution_time': metrics.total_execution_time,
                'total_agents': metrics.total_agents,
                'success_rate': metrics.successful_agents / max(metrics.total_agents, 1),
                'memory_peak_mb': metrics.total_memory_peak / (1024 * 1024),
                'chunks_processed': metrics.chunks_processed,
                'timestamp': metrics.timestamp.isoformat()
            })
        except Exception as e:
            logger.error(f"LangFuse 워크플로우 메트릭 전송 실패: {e}")
    
    def generate_performance_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """성능 분석 보고서 생성"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            
            # 시간 범위 내 메트릭 필터링
            recent_agent_metrics = [
                m for m in self.agent_metrics_cache 
                if m.timestamp >= cutoff_time
            ]
            recent_workflow_metrics = [
                m for m in self.workflow_metrics_cache 
                if m.timestamp >= cutoff_time
            ]
            recent_system_metrics = [
                m for m in self.system_metrics_cache 
                if m.timestamp >= cutoff_time
            ]
            
            report = {
                'summary': self._calculate_summary_stats(recent_agent_metrics, recent_workflow_metrics),
                'agent_performance': self._get_agent_performance(recent_agent_metrics),
                'workflow_performance': self._get_workflow_performance(recent_workflow_metrics),
                'system_performance': self._get_system_performance(recent_system_metrics),
                'trends': self._analyze_trends(recent_agent_metrics, recent_workflow_metrics),
                'bottlenecks': self._identify_bottlenecks(recent_agent_metrics),
                'recommendations': self._generate_recommendations(),
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'time_range_hours': time_range_hours,
                    'total_agent_executions': len(recent_agent_metrics),
                    'total_workflows': len(recent_workflow_metrics)
                }
            }
            
            logger.info(f"성능 보고서 생성 완료 (시간 범위: {time_range_hours}시간)")
            return report
            
        except Exception as e:
            logger.error(f"성능 보고서 생성 실패: {e}")
            return {'error': str(e)}
    
    def _calculate_summary_stats(self, agent_metrics: List[AgentMetrics], 
                               workflow_metrics: List[WorkflowMetrics]) -> Dict[str, Any]:
        """요약 통계 계산"""
        if not agent_metrics and not workflow_metrics:
            return {'message': '메트릭 데이터가 없습니다'}
        
        # 에이전트 통계
        agent_execution_times = [m.execution_time for m in agent_metrics]
        agent_success_rates = [m.success_rate for m in agent_metrics]
        agent_throughputs = [m.throughput for m in agent_metrics if m.throughput > 0]
        
        # 워크플로우 통계
        workflow_execution_times = [m.total_execution_time for m in workflow_metrics]
        workflow_success_rates = [
            m.successful_agents / max(m.total_agents, 1) 
            for m in workflow_metrics if m.total_agents > 0
        ]
        
        return {
            'total_agent_executions': len(agent_metrics),
            'total_workflows': len(workflow_metrics),
            'avg_agent_execution_time': statistics.mean(agent_execution_times) if agent_execution_times else 0,
            'avg_workflow_execution_time': statistics.mean(workflow_execution_times) if workflow_execution_times else 0,
            'overall_agent_success_rate': statistics.mean(agent_success_rates) if agent_success_rates else 0,
            'overall_workflow_success_rate': statistics.mean(workflow_success_rates) if workflow_success_rates else 0,
            'avg_throughput': statistics.mean(agent_throughputs) if agent_throughputs else 0,
            'p95_agent_execution_time': statistics.quantiles(agent_execution_times, n=20)[18] if len(agent_execution_times) > 20 else (max(agent_execution_times) if agent_execution_times else 0)
        }
    
    def _get_agent_performance(self, agent_metrics: List[AgentMetrics]) -> Dict[str, Any]:
        """에이전트별 성능 분석"""
        agent_groups = defaultdict(list)
        for metric in agent_metrics:
            agent_groups[metric.agent_name].append(metric)
        
        performance = {}
        for agent_name, metrics in agent_groups.items():
            execution_times = [m.execution_time for m in metrics]
            success_rates = [m.success_rate for m in metrics]
            memory_usages = [m.memory_usage for m in metrics]
            
            performance[agent_name] = {
                'execution_count': len(metrics),
                'avg_execution_time': statistics.mean(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'success_rate': statistics.mean(success_rates),
                'avg_memory_usage_mb': statistics.mean(memory_usages) / (1024 * 1024),
                'total_errors': sum(m.error_count for m in metrics)
            }
        
        return performance
    
    def _get_workflow_performance(self, workflow_metrics: List[WorkflowMetrics]) -> Dict[str, Any]:
        """워크플로우 성능 분석"""
        if not workflow_metrics:
            return {}
        
        langgraph_metrics = [m for m in workflow_metrics if m.workflow_type == 'langgraph']
        sequential_metrics = [m for m in workflow_metrics if m.workflow_type == 'sequential']
        
        def analyze_type(metrics, type_name):
            if not metrics:
                return None
            
            execution_times = [m.total_execution_time for m in metrics]
            success_rates = [m.successful_agents / max(m.total_agents, 1) for m in metrics]
            
            return {
                'count': len(metrics),
                'avg_execution_time': statistics.mean(execution_times),
                'avg_success_rate': statistics.mean(success_rates),
                'avg_agents_per_workflow': statistics.mean([m.total_agents for m in metrics]),
                'avg_chunks_processed': statistics.mean([m.chunks_processed for m in metrics])
            }
        
        return {
            'langgraph': analyze_type(langgraph_metrics, 'langgraph'),
            'sequential': analyze_type(sequential_metrics, 'sequential'),
            'total_workflows': len(workflow_metrics)
        }
    
    def _get_system_performance(self, system_metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """시스템 성능 분석"""
        if not system_metrics:
            return {}
        
        cpu_usages = [m.cpu_percent for m in system_metrics]
        memory_usages = [m.memory_percent for m in system_metrics]
        
        return {
            'avg_cpu_usage': statistics.mean(cpu_usages),
            'max_cpu_usage': max(cpu_usages),
            'avg_memory_usage': statistics.mean(memory_usages),
            'max_memory_usage': max(memory_usages),
            'samples_count': len(system_metrics)
        }
    
    def _analyze_trends(self, agent_metrics: List[AgentMetrics], 
                       workflow_metrics: List[WorkflowMetrics]) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        # 시간대별 성능 변화 분석
        hourly_performance = defaultdict(list)
        
        for metric in agent_metrics:
            hour = metric.timestamp.hour
            hourly_performance[hour].append(metric.execution_time)
        
        # 시간대별 평균 실행 시간
        hourly_avg = {
            hour: statistics.mean(times) 
            for hour, times in hourly_performance.items()
        }
        
        return {
            'hourly_performance': hourly_avg,
            'peak_hour': max(hourly_avg.keys(), key=lambda h: hourly_avg[h]) if hourly_avg else None,
            'best_hour': min(hourly_avg.keys(), key=lambda h: hourly_avg[h]) if hourly_avg else None
        }
    
    def _identify_bottlenecks(self, agent_metrics: List[AgentMetrics]) -> List[Dict[str, Any]]:
        """병목 지점 식별"""
        bottlenecks = []
        
        # 에이전트별 평균 실행 시간 계산
        agent_avg_times = defaultdict(list)
        for metric in agent_metrics:
            agent_avg_times[metric.agent_name].append(metric.execution_time)
        
        # 평균 실행 시간이 긴 에이전트 식별
        for agent_name, times in agent_avg_times.items():
            avg_time = statistics.mean(times)
            if avg_time > 5.0:  # 5초 이상
                bottlenecks.append({
                    'type': 'slow_agent',
                    'agent_name': agent_name,
                    'avg_execution_time': avg_time,
                    'severity': 'high' if avg_time > 10.0 else 'medium'
                })
        
        return bottlenecks
    
    def _generate_recommendations(self) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []
        
        # 에이전트별 통계 기반 권장사항
        for agent_name, stats in self.agent_stats.items():
            if stats['total_executions'] > 0:
                avg_time = stats['total_execution_time'] / stats['total_executions']
                success_rate = stats['success_count'] / stats['total_executions']
                
                if avg_time > 10.0:
                    recommendations.append(f"{agent_name} 에이전트의 실행 시간 최적화 검토 필요")
                
                if success_rate < 0.9:
                    recommendations.append(f"{agent_name} 에이전트의 오류율 개선 필요")
        
        return recommendations
    
    async def get_realtime_metrics(self) -> Dict[str, Any]:
        """실시간 메트릭 데이터 반환"""
        try:
            # 시스템 모니터링 시작 확인
            self._ensure_monitoring_started()
            # 최근 메트릭 가져오기
            latest_system = self.system_metrics_cache[-1] if self.system_metrics_cache else None
            recent_agents = list(self.agent_metrics_cache)[-10:] if self.agent_metrics_cache else []
            recent_workflows = list(self.workflow_metrics_cache)[-5:] if self.workflow_metrics_cache else []
            
            return {
                'current_system': asdict(latest_system) if latest_system else {},
                'recent_agent_executions': [asdict(m) for m in recent_agents],
                'recent_workflows': [asdict(m) for m in recent_workflows],
                'active_agents': len(set(m.agent_name for m in recent_agents)),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"실시간 메트릭 조회 실패: {e}")
            return {'error': str(e)}

# 전역 인스턴스
performance_collector = PerformanceMetricsCollector()

def get_performance_collector() -> PerformanceMetricsCollector:
    """PerformanceMetricsCollector 인스턴스 반환"""
    return performance_collector
