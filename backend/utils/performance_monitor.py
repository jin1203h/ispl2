"""
성능 모니터링 유틸리티
PDF 처리 파이프라인의 성능 및 리소스 사용량 모니터링
"""
import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""
    start_time: float
    end_time: Optional[float] = None
    memory_start: float = 0.0
    memory_peak: float = 0.0
    memory_end: float = 0.0
    cpu_usage: List[float] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """처리 시간 (초)"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def memory_usage_mb(self) -> Dict[str, float]:
        """메모리 사용량 (MB)"""
        return {
            "start": self.memory_start / 1024 / 1024,
            "peak": self.memory_peak / 1024 / 1024,
            "end": self.memory_end / 1024 / 1024
        }
    
    @property
    def avg_cpu_usage(self) -> float:
        """평균 CPU 사용률"""
        return sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0.0

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self, monitor_interval: float = 1.0):
        self.monitor_interval = monitor_interval
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.current_task: Optional[str] = None
        
    def start_task(self, task_name: str) -> None:
        """태스크 모니터링 시작"""
        current_memory = psutil.virtual_memory().used
        
        self.metrics[task_name] = PerformanceMetrics(
            start_time=time.time(),
            memory_start=current_memory,
            memory_peak=current_memory
        )
        
        self.current_task = task_name
        self._start_monitoring()
        
        logger.info(f"성능 모니터링 시작: {task_name}")
    
    def end_task(self, task_name: str) -> PerformanceMetrics:
        """태스크 모니터링 종료"""
        if task_name not in self.metrics:
            raise ValueError(f"태스크 '{task_name}'이 모니터링되지 않음")
        
        metrics = self.metrics[task_name]
        metrics.end_time = time.time()
        metrics.memory_end = psutil.virtual_memory().used
        
        if self.current_task == task_name:
            self._stop_monitoring()
            self.current_task = None
        
        logger.info(f"성능 모니터링 완료: {task_name} - {metrics.duration:.2f}초")
        return metrics
    
    def _start_monitoring(self) -> None:
        """백그라운드 모니터링 시작"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
    
    def _stop_monitoring(self) -> None:
        """백그라운드 모니터링 종료"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self) -> None:
        """모니터링 루프"""
        while self.is_monitoring and self.current_task:
            try:
                # CPU 사용률 수집
                cpu_percent = psutil.cpu_percent()
                
                # 메모리 사용량 수집
                current_memory = psutil.virtual_memory().used
                
                if self.current_task in self.metrics:
                    metrics = self.metrics[self.current_task]
                    metrics.cpu_usage.append(cpu_percent)
                    
                    # 피크 메모리 업데이트
                    if current_memory > metrics.memory_peak:
                        metrics.memory_peak = current_memory
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.warning(f"모니터링 중 오류: {e}")
                break
    
    def get_task_metrics(self, task_name: str) -> Optional[PerformanceMetrics]:
        """특정 태스크의 메트릭 조회"""
        return self.metrics.get(task_name)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """모든 메트릭 조회"""
        return self.metrics.copy()
    
    def clear_metrics(self) -> None:
        """메트릭 초기화"""
        self.metrics.clear()
    
    def export_metrics(self, output_path: str) -> None:
        """메트릭을 파일로 내보내기"""
        export_data = {}
        
        for task_name, metrics in self.metrics.items():
            export_data[task_name] = {
                "duration": metrics.duration,
                "memory_usage_mb": metrics.memory_usage_mb,
                "avg_cpu_usage": metrics.avg_cpu_usage,
                "start_time": datetime.fromtimestamp(metrics.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(metrics.end_time).isoformat() if metrics.end_time else None
            }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"성능 메트릭 내보내기 완료: {output_path}")

class PipelineProfiler:
    """파이프라인 프로파일러"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.stage_metrics: Dict[str, Dict[str, Any]] = {}
        
    def profile_stage(self, stage_name: str):
        """스테이지 프로파일링 데코레이터"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.monitor.start_task(stage_name)
                try:
                    result = func(*args, **kwargs)
                    metrics = self.monitor.end_task(stage_name)
                    
                    self.stage_metrics[stage_name] = {
                        "success": True,
                        "duration": metrics.duration,
                        "memory_usage": metrics.memory_usage_mb,
                        "cpu_usage": metrics.avg_cpu_usage
                    }
                    
                    return result
                    
                except Exception as e:
                    metrics = self.monitor.end_task(stage_name)
                    
                    self.stage_metrics[stage_name] = {
                        "success": False,
                        "error": str(e),
                        "duration": metrics.duration,
                        "memory_usage": metrics.memory_usage_mb,
                        "cpu_usage": metrics.avg_cpu_usage
                    }
                    
                    raise
            return wrapper
        return decorator
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """파이프라인 전체 요약"""
        total_duration = sum(
            stage["duration"] for stage in self.stage_metrics.values()
        )
        
        peak_memory = max(
            stage["memory_usage"]["peak"] for stage in self.stage_metrics.values()
        ) if self.stage_metrics else 0
        
        avg_cpu = sum(
            stage["cpu_usage"] for stage in self.stage_metrics.values()
        ) / len(self.stage_metrics) if self.stage_metrics else 0
        
        success_rate = sum(
            1 for stage in self.stage_metrics.values() if stage["success"]
        ) / len(self.stage_metrics) * 100 if self.stage_metrics else 0
        
        return {
            "total_duration": total_duration,
            "peak_memory_mb": peak_memory,
            "avg_cpu_usage": avg_cpu,
            "success_rate": success_rate,
            "stages_completed": len(self.stage_metrics),
            "stage_details": self.stage_metrics
        }

class ResourceOptimizer:
    """리소스 최적화 유틸리티"""
    
    @staticmethod
    def get_optimal_batch_size(available_memory_mb: float, 
                             item_size_mb: float, 
                             safety_factor: float = 0.7) -> int:
        """최적 배치 크기 계산"""
        if item_size_mb <= 0:
            return 1
            
        max_batch = int((available_memory_mb * safety_factor) / item_size_mb)
        return max(1, min(max_batch, 10))  # 최소 1, 최대 10
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """시스템 상태 조회"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "memory": {
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "used_percent": memory.percent
            },
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "disk": {
                "usage_percent": psutil.disk_usage('/').percent
            }
        }
    
    @staticmethod
    def should_pause_processing(memory_threshold: float = 85.0, 
                              cpu_threshold: float = 90.0) -> Dict[str, Any]:
        """처리 일시정지 여부 판단"""
        status = ResourceOptimizer.get_system_status()
        
        memory_overload = status["memory"]["used_percent"] > memory_threshold
        cpu_overload = status["cpu"]["usage_percent"] > cpu_threshold
        
        return {
            "should_pause": memory_overload or cpu_overload,
            "memory_overload": memory_overload,
            "cpu_overload": cpu_overload,
            "current_memory": status["memory"]["used_percent"],
            "current_cpu": status["cpu"]["usage_percent"]
        }

