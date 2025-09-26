"""
품질 검증 임베딩 에이전트
기존 EmbeddingAgent를 확장하여 품질 검증 및 배치 최적화 기능 추가
"""
import os
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from .base import BaseAgent, DocumentProcessingState, ProcessingStatus, ProcessedChunk
from .embedding_agent import EmbeddingAgent

# 품질 검증 서비스 import
try:
    from services.embedding_quality_service import (
        EmbeddingQualityService, 
        QualityLevel,
        EmbeddingQualityMetrics
    )
    QUALITY_SERVICE_AVAILABLE = True
except ImportError:
    print("⚠️ 임베딩 품질 검증 서비스를 사용할 수 없습니다.")
    QUALITY_SERVICE_AVAILABLE = False

# MultiModel 임베딩 서비스 import
try:
    from services.multi_model_embedding import (
        MultiModelEmbeddingAgent,
        SecurityLevel,
        EmbeddingModelRegistry
    )
    MULTI_MODEL_AVAILABLE = True
except ImportError:
    print("⚠️ 다중 모델 임베딩 서비스를 사용할 수 없습니다.")
    MULTI_MODEL_AVAILABLE = False

logger = logging.getLogger(__name__)

class QualityEmbeddingAgent(BaseAgent):
    """품질 검증 임베딩 에이전트"""
    
    def __init__(self, 
                 model: str = "text-embedding-3-large",
                 batch_size: int = 100,
                 security_level: str = "public",
                 enable_quality_validation: bool = True,
                 enable_adaptive_batching: bool = True):
        super().__init__(
            name="quality_embedding_agent",
            description="품질 검증 및 배치 최적화가 포함된 임베딩 생성 에이전트"
        )
        
        self.model = model
        self.initial_batch_size = batch_size
        self.security_level = security_level
        self.enable_quality_validation = enable_quality_validation
        self.enable_adaptive_batching = enable_adaptive_batching
        
        # 기본 임베딩 에이전트 초기화
        if MULTI_MODEL_AVAILABLE:
            self.embedding_agent = MultiModelEmbeddingAgent(
                security_level=SecurityLevel(security_level),
                default_model=model,
                batch_size=batch_size
            )
        else:
            self.embedding_agent = EmbeddingAgent(model=model, batch_size=batch_size)
        
        # 품질 검증 서비스 초기화
        self.quality_service = None
        if QUALITY_SERVICE_AVAILABLE and enable_quality_validation:
            try:
                model_config = self._get_model_config()
                self.quality_service = EmbeddingQualityService(
                    model_config=model_config,
                    initial_batch_size=batch_size
                )
                logger.info("품질 검증 서비스 활성화됨")
            except Exception as e:
                logger.warning(f"품질 검증 서비스 초기화 실패: {e}")
        
        # 통계 추적
        self.processing_stats = {
            "total_chunks_processed": 0,
            "total_embeddings_generated": 0,
            "quality_failures": 0,
            "batch_adjustments": 0,
            "total_processing_time": 0.0,
            "average_quality_score": 0.0
        }
    
    def _get_model_config(self) -> Dict[str, Any]:
        """모델 설정 가져오기"""
        if MULTI_MODEL_AVAILABLE:
            try:
                registry = EmbeddingModelRegistry()
                return registry.get_model_info(self.model)
            except:
                pass
        
        # 기본 설정
        return {
            "model_name": self.model,
            "dimensions": 3072 if "3-large" in self.model else 1536,
            "cost_per_1k_tokens": 0.00013,
            "max_tokens": 8191
        }
    
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """품질 검증을 포함한 임베딩 생성"""
        self.log_step(state, "품질 검증 임베딩 생성 시작")
        state["current_step"] = "quality_embedding_generation"
        
        try:
            # 청크 데이터 확인
            chunks = state.get("processed_chunks", [])
            if not chunks:
                return self.update_status(
                    state, ProcessingStatus.FAILED, 
                    "embedding_generation", "처리할 청크가 없습니다"
                )
            
            self.log_step(state, f"총 {len(chunks)}개 청크에 대한 임베딩 생성 시작")
            
            # 배치 단위로 처리
            all_embeddings = []
            all_quality_reports = []
            current_batch_size = self.initial_batch_size
            
            for i in range(0, len(chunks), current_batch_size):
                batch_chunks = chunks[i:i + current_batch_size]
                
                # 배치 처리
                batch_result = await self._process_batch(batch_chunks, len(all_embeddings))
                
                if batch_result["success"]:
                    all_embeddings.extend(batch_result["embeddings"])
                    
                    if batch_result.get("quality_report"):
                        all_quality_reports.append(batch_result["quality_report"])
                        
                        # 적응형 배치 크기 조정
                        if self.enable_adaptive_batching and batch_result["quality_report"].get("next_batch_size"):
                            new_batch_size = batch_result["quality_report"]["next_batch_size"]
                            if new_batch_size != current_batch_size:
                                current_batch_size = new_batch_size
                                self.processing_stats["batch_adjustments"] += 1
                                self.log_step(state, f"배치 크기 조정: {current_batch_size}로 변경")
                else:
                    # 배치 실패 처리
                    self.log_step(state, f"배치 {i//current_batch_size + 1} 처리 실패: {batch_result.get('error', 'Unknown error')}", "warning")
                    
                    # 실패한 청크들을 개별 처리 시도
                    for chunk in batch_chunks:
                        try:
                            individual_result = await self._process_individual_chunk(chunk)
                            if individual_result["success"]:
                                all_embeddings.append(individual_result["embedding"])
                        except Exception as e:
                            self.log_step(state, f"개별 청크 처리 실패: {e}", "error")
                            self.processing_stats["quality_failures"] += 1
                
                # 진행률 업데이트
                progress = min(100, (i + current_batch_size) / len(chunks) * 100)
                state["embedding_progress"] = progress
                self.log_step(state, f"임베딩 생성 진행률: {progress:.1f}%")
            
            # 결과 정리
            state["embeddings"] = all_embeddings
            state["embedding_quality_reports"] = all_quality_reports
            state["total_embeddings"] = len(all_embeddings)
            
            # 통계 업데이트
            self.processing_stats["total_chunks_processed"] += len(chunks)
            self.processing_stats["total_embeddings_generated"] += len(all_embeddings)
            
            # 품질 종합 보고서 생성
            if self.quality_service:
                comprehensive_report = self.quality_service.get_comprehensive_report()
                state["embedding_quality_summary"] = comprehensive_report
            
            # 처리 완료 로그
            success_rate = len(all_embeddings) / len(chunks) * 100
            self.log_step(
                state,
                f"임베딩 생성 완료: {len(all_embeddings)}/{len(chunks)}개 성공 "
                f"(성공률: {success_rate:.1f}%)"
            )
            
            if success_rate >= 95:
                return self.update_status(state, ProcessingStatus.COMPLETED, "embedding_generation")
            elif success_rate >= 80:
                return self.update_status(
                    state, ProcessingStatus.COMPLETED, "embedding_generation",
                    f"일부 임베딩 생성 실패 (성공률: {success_rate:.1f}%)"
                )
            else:
                return self.update_status(
                    state, ProcessingStatus.FAILED, "embedding_generation",
                    f"임베딩 생성 실패율이 높음 (성공률: {success_rate:.1f}%)"
                )
                
        except Exception as e:
            error_msg = f"품질 검증 임베딩 생성 중 오류 발생: {str(e)}"
            self.log_step(state, error_msg, "error")
            return self.update_status(
                state, ProcessingStatus.FAILED, "embedding_generation", error_msg
            )
    
    async def _process_batch(self, batch_chunks: List[ProcessedChunk], 
                           start_index: int) -> Dict[str, Any]:
        """배치 단위 임베딩 처리"""
        batch_start_time = time.time()
        
        try:
            # 텍스트 추출
            texts = [chunk["text"] for chunk in batch_chunks]
            
            # 임베딩 생성 (기존 에이전트 활용)
            if hasattr(self.embedding_agent, 'generate_embeddings'):
                embeddings = await self.embedding_agent.generate_embeddings(texts)
            else:
                # EmbeddingAgent의 내부 메서드 활용
                embeddings_response = await self.embedding_agent._generate_embeddings(texts)
                embeddings = [data.embedding for data in embeddings_response.data]
            
            processing_time = time.time() - batch_start_time
            total_tokens = sum(len(text.split()) * 1.3 for text in texts)  # 대략적인 토큰 계산
            
            result = {
                "success": True,
                "embeddings": embeddings,
                "processing_time": processing_time,
                "total_tokens": int(total_tokens)
            }
            
            # 품질 검증 (활성화된 경우)
            if self.quality_service:
                try:
                    quality_report = await self.quality_service.validate_and_optimize_batch(
                        embeddings=embeddings,
                        processing_time=processing_time,
                        total_tokens=int(total_tokens),
                        success=True
                    )
                    result["quality_report"] = quality_report
                    
                    # 평균 품질 점수 업데이트
                    if quality_report.get("quality_analysis", {}).get("average_quality_score"):
                        avg_quality = quality_report["quality_analysis"]["average_quality_score"]
                        self.processing_stats["average_quality_score"] = (
                            (self.processing_stats["average_quality_score"] * self.processing_stats["total_chunks_processed"] + 
                             avg_quality * len(batch_chunks)) / 
                            (self.processing_stats["total_chunks_processed"] + len(batch_chunks))
                        )
                    
                except Exception as e:
                    logger.warning(f"품질 검증 실패: {e}")
                    result["quality_validation_error"] = str(e)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - batch_start_time
            
            # 실패한 경우에도 품질 서비스에 기록
            if self.quality_service:
                try:
                    await self.quality_service.validate_and_optimize_batch(
                        embeddings=[],
                        processing_time=processing_time,
                        total_tokens=0,
                        success=False,
                        error_message=str(e)
                    )
                except:
                    pass
            
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    async def _process_individual_chunk(self, chunk: ProcessedChunk) -> Dict[str, Any]:
        """개별 청크 처리 (배치 실패 시 폴백)"""
        try:
            text = chunk["text"]
            
            if hasattr(self.embedding_agent, 'generate_embeddings'):
                embeddings = await self.embedding_agent.generate_embeddings([text])
                embedding = embeddings[0] if embeddings else None
            else:
                embeddings_response = await self.embedding_agent._generate_embeddings([text])
                embedding = embeddings_response.data[0].embedding if embeddings_response.data else None
            
            if embedding:
                return {"success": True, "embedding": embedding}
            else:
                return {"success": False, "error": "임베딩 생성 실패"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """처리 통계 반환"""
        return {
            **self.processing_stats,
            "quality_service_enabled": self.quality_service is not None,
            "adaptive_batching_enabled": self.enable_adaptive_batching,
            "current_model": self.model,
            "security_level": self.security_level
        }
    
    async def generate_quality_report(self) -> Dict[str, Any]:
        """품질 보고서 생성"""
        if not self.quality_service:
            return {"error": "품질 검증 서비스가 비활성화되어 있습니다"}
        
        try:
            return self.quality_service.get_comprehensive_report()
        except Exception as e:
            return {"error": f"품질 보고서 생성 실패: {str(e)}"}

