"""
임베딩 품질 검증 및 배치 최적화 서비스
벡터 품질 검증, 동적 배치 크기 조정, API 호출 최적화, 비용 모니터링 기능
"""
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

# 수치 계산 라이브러리
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    print("⚠️ numpy가 설치되지 않았습니다. 기본 벡터 검증을 사용합니다.")
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    """품질 등급"""
    EXCELLENT = "excellent"  # 95% 이상
    GOOD = "good"           # 85-95%
    FAIR = "fair"           # 70-85%
    POOR = "poor"           # 70% 미만

@dataclass
class EmbeddingQualityMetrics:
    """임베딩 품질 메트릭"""
    vector_norm: float
    dimension_consistency: bool
    has_nan_values: bool
    has_inf_values: bool
    zero_variance: bool
    quality_score: float
    quality_level: QualityLevel

@dataclass
class BatchOptimizationMetrics:
    """배치 최적화 메트릭"""
    current_batch_size: int
    success_rate: float
    avg_response_time: float
    api_errors: int
    cost_per_batch: float
    total_tokens_processed: int
    optimization_suggestion: str

@dataclass
class APIUsageStats:
    """API 사용량 통계"""
    requests_per_minute: float = 0.0
    tokens_per_minute: float = 0.0
    daily_cost: float = 0.0
    monthly_cost_estimate: float = 0.0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    recent_requests: List[datetime] = field(default_factory=list)
    recent_tokens: List[int] = field(default_factory=list)

class EmbeddingQualityValidator:
    """임베딩 품질 검증기"""
    
    def __init__(self, 
                 min_norm_threshold: float = 0.1,
                 max_norm_threshold: float = 10.0,
                 variance_threshold: float = 1e-6):
        self.min_norm_threshold = min_norm_threshold
        self.max_norm_threshold = max_norm_threshold
        self.variance_threshold = variance_threshold
        
    def validate_embedding_batch(self, embeddings: List[List[float]], 
                                expected_dimension: int) -> List[EmbeddingQualityMetrics]:
        """임베딩 배치의 품질을 검증"""
        metrics = []
        
        for i, embedding in enumerate(embeddings):
            try:
                metric = self._validate_single_embedding(embedding, expected_dimension)
                metrics.append(metric)
                
            except Exception as e:
                logger.warning(f"임베딩 {i} 검증 실패: {e}")
                # 실패한 경우 기본 메트릭 생성
                metrics.append(EmbeddingQualityMetrics(
                    vector_norm=0.0,
                    dimension_consistency=False,
                    has_nan_values=True,
                    has_inf_values=False,
                    zero_variance=True,
                    quality_score=0.0,
                    quality_level=QualityLevel.POOR
                ))
        
        return metrics
    
    def _validate_single_embedding(self, embedding: List[float], 
                                 expected_dimension: int) -> EmbeddingQualityMetrics:
        """단일 임베딩의 품질을 검증"""
        
        # 차원 일관성 검사
        dimension_consistency = len(embedding) == expected_dimension
        
        if NUMPY_AVAILABLE:
            vec = np.array(embedding, dtype=np.float32)
            
            # 벡터 norm 계산
            vector_norm = float(np.linalg.norm(vec))
            
            # NaN/Inf 값 검사
            has_nan_values = bool(np.isnan(vec).any())
            has_inf_values = bool(np.isinf(vec).any())
            
            # 분산 검사 (모든 값이 동일한지)
            variance = float(np.var(vec))
            zero_variance = variance < self.variance_threshold
            
        else:
            # numpy 없이 기본 계산
            vector_norm = sum(x**2 for x in embedding) ** 0.5
            has_nan_values = any(x != x for x in embedding)  # NaN 체크
            has_inf_values = any(abs(x) == float('inf') for x in embedding)
            
            # 간단한 분산 계산
            mean_val = sum(embedding) / len(embedding)
            variance = sum((x - mean_val)**2 for x in embedding) / len(embedding)
            zero_variance = variance < self.variance_threshold
        
        # 품질 점수 계산
        quality_score = self._calculate_quality_score(
            vector_norm, dimension_consistency, has_nan_values, 
            has_inf_values, zero_variance
        )
        
        # 품질 등급 결정
        quality_level = self._determine_quality_level(quality_score)
        
        return EmbeddingQualityMetrics(
            vector_norm=vector_norm,
            dimension_consistency=dimension_consistency,
            has_nan_values=has_nan_values,
            has_inf_values=has_inf_values,
            zero_variance=zero_variance,
            quality_score=quality_score,
            quality_level=quality_level
        )
    
    def _calculate_quality_score(self, vector_norm: float, dimension_consistency: bool,
                               has_nan_values: bool, has_inf_values: bool, 
                               zero_variance: bool) -> float:
        """품질 점수 계산 (0-100)"""
        score = 100.0
        
        # 차원 일관성 (필수)
        if not dimension_consistency:
            score -= 50
        
        # NaN/Inf 값 (치명적)
        if has_nan_values or has_inf_values:
            score -= 40
        
        # 벡터 norm 검사
        if vector_norm < self.min_norm_threshold:
            score -= 30  # 너무 작은 norm
        elif vector_norm > self.max_norm_threshold:
            score -= 20  # 너무 큰 norm
        
        # 분산 검사 (모든 값이 동일)
        if zero_variance:
            score -= 25
        
        return max(0.0, score)
    
    def _determine_quality_level(self, quality_score: float) -> QualityLevel:
        """품질 점수를 기반으로 등급 결정"""
        if quality_score >= 95:
            return QualityLevel.EXCELLENT
        elif quality_score >= 85:
            return QualityLevel.GOOD
        elif quality_score >= 70:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR

class AdaptiveBatchOptimizer:
    """적응형 배치 크기 최적화기"""
    
    def __init__(self, 
                 initial_batch_size: int = 100,
                 min_batch_size: int = 10,
                 max_batch_size: int = 2000,
                 target_success_rate: float = 0.95,
                 target_response_time: float = 10.0):
        self.initial_batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_success_rate = target_success_rate
        self.target_response_time = target_response_time
        
        self.current_batch_size = initial_batch_size
        self.success_history: List[bool] = []
        self.response_time_history: List[float] = []
        self.error_history: List[str] = []
        
    def record_batch_result(self, success: bool, response_time: float, 
                           error_message: Optional[str] = None):
        """배치 처리 결과 기록"""
        self.success_history.append(success)
        self.response_time_history.append(response_time)
        
        if error_message:
            self.error_history.append(error_message)
        
        # 히스토리 크기 제한 (최근 100개)
        if len(self.success_history) > 100:
            self.success_history = self.success_history[-100:]
            self.response_time_history = self.response_time_history[-100:]
        
        if len(self.error_history) > 50:
            self.error_history = self.error_history[-50:]
    
    def get_optimization_metrics(self) -> BatchOptimizationMetrics:
        """현재 최적화 메트릭 반환"""
        if not self.success_history:
            return BatchOptimizationMetrics(
                current_batch_size=self.current_batch_size,
                success_rate=0.0,
                avg_response_time=0.0,
                api_errors=0,
                cost_per_batch=0.0,
                total_tokens_processed=0,
                optimization_suggestion="데이터 부족"
            )
        
        success_rate = sum(self.success_history) / len(self.success_history)
        avg_response_time = sum(self.response_time_history) / len(self.response_time_history)
        
        suggestion = self._generate_optimization_suggestion(success_rate, avg_response_time)
        
        return BatchOptimizationMetrics(
            current_batch_size=self.current_batch_size,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            api_errors=len(self.error_history),
            cost_per_batch=0.0,  # 별도 계산 필요
            total_tokens_processed=0,  # 별도 계산 필요
            optimization_suggestion=suggestion
        )
    
    def adjust_batch_size(self) -> int:
        """배치 크기 동적 조정"""
        if len(self.success_history) < 5:
            return self.current_batch_size  # 충분한 데이터가 없으면 유지
        
        # 최근 성능 분석
        recent_success_rate = sum(self.success_history[-10:]) / min(10, len(self.success_history))
        recent_avg_response_time = sum(self.response_time_history[-10:]) / min(10, len(self.response_time_history))
        
        old_batch_size = self.current_batch_size
        
        # 성공률이 낮으면 배치 크기 감소
        if recent_success_rate < self.target_success_rate:
            self.current_batch_size = max(
                self.min_batch_size, 
                int(self.current_batch_size * 0.7)
            )
            logger.info(f"낮은 성공률로 인한 배치 크기 감소: {old_batch_size} → {self.current_batch_size}")
            
        # 응답 시간이 너무 길면 배치 크기 감소
        elif recent_avg_response_time > self.target_response_time:
            self.current_batch_size = max(
                self.min_batch_size,
                int(self.current_batch_size * 0.8)
            )
            logger.info(f"긴 응답 시간으로 인한 배치 크기 감소: {old_batch_size} → {self.current_batch_size}")
            
        # 성능이 좋으면 배치 크기 증가
        elif (recent_success_rate >= self.target_success_rate and 
              recent_avg_response_time < self.target_response_time * 0.7):
            self.current_batch_size = min(
                self.max_batch_size,
                int(self.current_batch_size * 1.2)
            )
            logger.info(f"좋은 성능으로 인한 배치 크기 증가: {old_batch_size} → {self.current_batch_size}")
        
        return self.current_batch_size
    
    def _generate_optimization_suggestion(self, success_rate: float, 
                                        avg_response_time: float) -> str:
        """최적화 제안 생성"""
        suggestions = []
        
        if success_rate < 0.9:
            suggestions.append("API 호출 성공률이 낮습니다. 배치 크기를 줄이거나 재시도 로직을 강화하세요.")
        
        if avg_response_time > self.target_response_time:
            suggestions.append("응답 시간이 깁니다. 배치 크기를 줄이거나 병렬 처리를 고려하세요.")
        
        if len(self.error_history) > 10:
            suggestions.append("API 오류가 빈번합니다. API 키와 네트워크 상태를 확인하세요.")
        
        if success_rate >= 0.95 and avg_response_time < self.target_response_time * 0.5:
            suggestions.append("성능이 우수합니다. 배치 크기를 늘려 처리량을 향상시킬 수 있습니다.")
        
        if not suggestions:
            suggestions.append("현재 설정이 최적입니다.")
        
        return " ".join(suggestions)

class APIUsageMonitor:
    """API 사용량 모니터링"""
    
    def __init__(self, cost_per_1k_tokens: float = 0.00013):
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.stats = APIUsageStats()
        
    def record_api_call(self, tokens: int, response_time: float, success: bool):
        """API 호출 기록"""
        now = datetime.now()
        
        self.stats.recent_requests.append(now)
        self.stats.recent_tokens.append(tokens)
        
        # 1시간 이내 데이터만 유지
        cutoff_time = now - timedelta(hours=1)
        self.stats.recent_requests = [
            req_time for req_time in self.stats.recent_requests 
            if req_time > cutoff_time
        ]
        
        self.stats.recent_tokens = self.stats.recent_tokens[-len(self.stats.recent_requests):]
        
        # 통계 업데이트
        self._update_stats()
    
    def _update_stats(self):
        """통계 업데이트"""
        if not self.stats.recent_requests:
            return
        
        now = datetime.now()
        
        # 분당 요청 수
        minute_ago = now - timedelta(minutes=1)
        recent_minute_requests = [
            req_time for req_time in self.stats.recent_requests 
            if req_time > minute_ago
        ]
        self.stats.requests_per_minute = len(recent_minute_requests)
        
        # 분당 토큰 수
        if len(self.stats.recent_tokens) >= len(recent_minute_requests):
            recent_minute_tokens = self.stats.recent_tokens[-len(recent_minute_requests):]
            self.stats.tokens_per_minute = sum(recent_minute_tokens)
        
        # 일일/월간 비용 추정
        hourly_tokens = sum(self.stats.recent_tokens)
        self.stats.daily_cost = (hourly_tokens * 24 / 1000) * self.cost_per_1k_tokens
        self.stats.monthly_cost_estimate = self.stats.daily_cost * 30
    
    def get_usage_stats(self) -> APIUsageStats:
        """현재 사용량 통계 반환"""
        return self.stats
    
    def is_approaching_rate_limit(self, rpm_limit: int = 3000, 
                                tpm_limit: int = 200000) -> Tuple[bool, str]:
        """Rate limit 접근 여부 확인"""
        warnings = []
        
        if self.stats.requests_per_minute > rpm_limit * 0.8:
            warnings.append(f"분당 요청 수가 한계의 80%에 근접: {self.stats.requests_per_minute}/{rpm_limit}")
        
        if self.stats.tokens_per_minute > tpm_limit * 0.8:
            warnings.append(f"분당 토큰 수가 한계의 80%에 근접: {self.stats.tokens_per_minute}/{tpm_limit}")
        
        return len(warnings) > 0, "; ".join(warnings)

class EmbeddingQualityService:
    """임베딩 품질 검증 및 최적화 통합 서비스"""
    
    def __init__(self, 
                 model_config: Dict[str, Any],
                 initial_batch_size: int = 100):
        self.model_config = model_config
        
        # 컴포넌트 초기화
        self.quality_validator = EmbeddingQualityValidator()
        self.batch_optimizer = AdaptiveBatchOptimizer(initial_batch_size=initial_batch_size)
        self.usage_monitor = APIUsageMonitor(
            cost_per_1k_tokens=model_config.get("cost_per_1k_tokens", 0.00013)
        )
        
        logger.info(f"EmbeddingQualityService 초기화: 모델={model_config.get('model_name', 'unknown')}")
    
    async def validate_and_optimize_batch(self, 
                                        embeddings: List[List[float]], 
                                        processing_time: float,
                                        total_tokens: int,
                                        success: bool,
                                        error_message: Optional[str] = None) -> Dict[str, Any]:
        """배치 검증 및 최적화"""
        
        # 1. 임베딩 품질 검증
        expected_dimension = self.model_config.get("dimensions", 1536)
        quality_metrics = self.quality_validator.validate_embedding_batch(
            embeddings, expected_dimension
        )
        
        # 2. 배치 최적화 메트릭 기록
        self.batch_optimizer.record_batch_result(success, processing_time, error_message)
        
        # 3. API 사용량 기록
        self.usage_monitor.record_api_call(total_tokens, processing_time, success)
        
        # 4. 다음 배치 크기 조정
        new_batch_size = self.batch_optimizer.adjust_batch_size()
        
        # 5. 종합 분석 결과
        analysis_result = {
            "quality_analysis": self._analyze_quality_metrics(quality_metrics),
            "batch_optimization": self.batch_optimizer.get_optimization_metrics(),
            "usage_stats": self.usage_monitor.get_usage_stats(),
            "recommendations": self._generate_recommendations(quality_metrics, new_batch_size),
            "next_batch_size": new_batch_size
        }
        
        return analysis_result
    
    def _analyze_quality_metrics(self, metrics: List[EmbeddingQualityMetrics]) -> Dict[str, Any]:
        """품질 메트릭 분석"""
        if not metrics:
            return {"error": "분석할 메트릭이 없습니다"}
        
        # 통계 계산
        quality_scores = [m.quality_score for m in metrics]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        quality_levels = [m.quality_level for m in metrics]
        level_counts = {level: quality_levels.count(level) for level in QualityLevel}
        
        # 문제 유형 분석
        issues = {
            "nan_vectors": sum(1 for m in metrics if m.has_nan_values),
            "inf_vectors": sum(1 for m in metrics if m.has_inf_values),
            "zero_variance": sum(1 for m in metrics if m.zero_variance),
            "dimension_mismatch": sum(1 for m in metrics if not m.dimension_consistency),
            "abnormal_norm": sum(1 for m in metrics if m.vector_norm < 0.1 or m.vector_norm > 10.0)
        }
        
        return {
            "total_vectors": len(metrics),
            "average_quality_score": avg_quality,
            "quality_distribution": {level.value: count for level, count in level_counts.items()},
            "issues_detected": issues,
            "pass_rate": sum(1 for m in metrics if m.quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD]) / len(metrics) * 100
        }
    
    def _generate_recommendations(self, 
                                quality_metrics: List[EmbeddingQualityMetrics],
                                new_batch_size: int) -> List[str]:
        """종합 권장사항 생성"""
        recommendations = []
        
        if not quality_metrics:
            return ["품질 메트릭 분석 불가"]
        
        # 품질 기반 권장사항
        avg_quality = sum(m.quality_score for m in quality_metrics) / len(quality_metrics)
        
        if avg_quality < 70:
            recommendations.append("임베딩 품질이 낮습니다. 입력 텍스트 전처리를 강화하거나 다른 모델을 고려하세요.")
        
        # 문제 유형별 권장사항
        nan_count = sum(1 for m in quality_metrics if m.has_nan_values)
        if nan_count > 0:
            recommendations.append(f"{nan_count}개 벡터에 NaN 값이 있습니다. API 호출을 재시도하세요.")
        
        zero_var_count = sum(1 for m in quality_metrics if m.zero_variance)
        if zero_var_count > len(quality_metrics) * 0.1:
            recommendations.append("동일한 값으로 구성된 벡터가 많습니다. 입력 텍스트의 다양성을 확인하세요.")
        
        # 배치 크기 권장사항
        batch_metrics = self.batch_optimizer.get_optimization_metrics()
        if batch_metrics.success_rate < 0.9:
            recommendations.append("배치 처리 성공률이 낮습니다. 배치 크기를 줄이거나 재시도 로직을 강화하세요.")
        
        # Rate limit 경고
        approaching_limit, warning_msg = self.usage_monitor.is_approaching_rate_limit()
        if approaching_limit:
            recommendations.append(f"API 한계 접근: {warning_msg}")
        
        if not recommendations:
            recommendations.append("현재 상태가 양호합니다.")
        
        return recommendations
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """종합 품질 보고서 생성"""
        return {
            "timestamp": datetime.now().isoformat(),
            "model_config": self.model_config,
            "batch_optimization": self.batch_optimizer.get_optimization_metrics(),
            "usage_stats": self.usage_monitor.get_usage_stats(),
            "current_settings": {
                "batch_size": self.batch_optimizer.current_batch_size,
                "quality_thresholds": {
                    "min_norm": self.quality_validator.min_norm_threshold,
                    "max_norm": self.quality_validator.max_norm_threshold,
                    "variance": self.quality_validator.variance_threshold
                }
            }
        }

