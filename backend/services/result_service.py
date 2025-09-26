"""
검색 결과 후처리 및 재랭킹 서비스
Cross-encoder 재랭킹, 중복 제거, 컨텍스트 병합, 다양성 확보
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import numpy as np
from collections import defaultdict
import re

from services.advanced_search_engine import SearchResult
from agents.query_processor import ProcessedQuery

logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """후처리 설정"""
    diversity_threshold: float = 0.8
    similarity_threshold: float = 0.85
    context_merge_threshold: float = 0.9
    max_context_length: int = 2000
    min_result_score: float = 0.3
    max_results: int = 10

@dataclass
class ProcessedResult:
    """후처리된 검색 결과"""
    original_result: SearchResult
    rerank_score: float
    diversity_score: float
    context_quality: float
    final_score: float
    extended_context: Optional[str] = None
    adjacent_chunks: List[SearchResult] = None
    deduplication_group: Optional[str] = None

class SearchResultService:
    """검색 결과 후처리 서비스"""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self.cross_encoder = None
        self._init_cross_encoder()
        
    def _init_cross_encoder(self):
        """Cross-encoder 초기화 (조건부)"""
        try:
            # sentence-transformers 사용 시도
            from sentence_transformers import CrossEncoder
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
            logger.info("Cross-encoder 모델 로드 성공")
        except ImportError:
            logger.warning("sentence-transformers 없음 - 재랭킹 기능 제한")
        except Exception as e:
            logger.warning(f"Cross-encoder 로드 실패: {e}")
    
    async def process_results(
        self,
        query: ProcessedQuery,
        raw_results: List[SearchResult],
        config: Optional[ProcessingConfig] = None
    ) -> List[ProcessedResult]:
        """검색 결과 후처리 메인 파이프라인"""
        processing_config = config or self.config
        
        try:
            start_time = time.time()
            
            # 1. 입력 검증 및 필터링
            filtered_results = self._filter_low_quality_results(raw_results, processing_config)
            
            # 2. Cross-encoder 재랭킹
            reranked_results = await self._cross_encoder_rerank(query, filtered_results)
            
            # 3. 의미적 중복 제거
            deduplicated_results = self._remove_semantic_duplicates(reranked_results, processing_config)
            
            # 4. 컨텍스트 병합
            context_merged_results = await self._merge_context(deduplicated_results, processing_config)
            
            # 5. 다양성 확보
            diversified_results = self._ensure_diversity(context_merged_results, processing_config)
            
            # 6. 최종 정렬 및 제한
            final_results = self._final_ranking(diversified_results, processing_config)
            
            processing_time = time.time() - start_time
            logger.info(f"결과 후처리 완료: {len(raw_results)} -> {len(final_results)} ({processing_time*1000:.1f}ms)")
            
            return final_results
            
        except Exception as e:
            logger.error(f"검색 결과 후처리 실패: {e}")
            # Fallback: 원본 결과를 ProcessedResult로 변환
            return [self._create_fallback_result(result) for result in raw_results[:processing_config.max_results]]
    
    def _filter_low_quality_results(
        self,
        results: List[SearchResult],
        config: ProcessingConfig
    ) -> List[SearchResult]:
        """저품질 결과 필터링"""
        filtered = []
        for result in results:
            # 최소 점수 기준
            if result.final_score < config.min_result_score:
                continue
            
            # 텍스트 길이 검증
            if len(result.chunk_text.strip()) < 10:
                continue
            
            # 중복 패턴 검증 (같은 텍스트 반복)
            if self._is_repetitive_text(result.chunk_text):
                continue
            
            filtered.append(result)
        
        logger.info(f"품질 필터링: {len(results)} -> {len(filtered)}")
        return filtered
    
    def _is_repetitive_text(self, text: str) -> bool:
        """반복적인 텍스트 패턴 감지"""
        # 같은 문장이 3번 이상 반복
        sentences = text.split('.')
        if len(sentences) >= 3:
            for i in range(len(sentences) - 2):
                if sentences[i] == sentences[i+1] == sentences[i+2] and sentences[i].strip():
                    return True
        return False
    
    async def _cross_encoder_rerank(
        self,
        query: ProcessedQuery,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Cross-encoder를 사용한 재랭킹"""
        if not self.cross_encoder or not results:
            return results
        
        try:
            # 질의-문서 쌍 생성
            query_text = query.original
            pairs = [(query_text, result.chunk_text) for result in results]
            
            # Cross-encoder 점수 계산
            scores = self.cross_encoder.predict(pairs)
            
            # 기존 점수와 결합 (가중 평균)
            for i, result in enumerate(results):
                cross_encoder_score = float(scores[i])
                # 70% cross-encoder + 30% 기존 점수
                result.final_score = 0.7 * cross_encoder_score + 0.3 * result.final_score
            
            # 재정렬
            results.sort(key=lambda x: x.final_score, reverse=True)
            
            logger.info(f"Cross-encoder 재랭킹 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.warning(f"Cross-encoder 재랭킹 실패: {e}")
            return results
    
    def _remove_semantic_duplicates(
        self,
        results: List[SearchResult],
        config: ProcessingConfig
    ) -> List[SearchResult]:
        """의미적 중복 제거"""
        if not results:
            return results
        
        # 간단한 텍스트 유사도 기반 중복 제거
        unique_results = []
        processed_texts = set()
        
        for result in results:
            # 텍스트 정규화
            normalized_text = self._normalize_for_dedup(result.chunk_text)
            
            # 유사한 텍스트가 이미 있는지 확인
            is_duplicate = False
            for existing_text in processed_texts:
                if self._calculate_text_similarity(normalized_text, existing_text) > config.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
                processed_texts.add(normalized_text)
        
        logger.info(f"중복 제거: {len(results)} -> {len(unique_results)}")
        return unique_results
    
    def _normalize_for_dedup(self, text: str) -> str:
        """중복 제거를 위한 텍스트 정규화"""
        # 소문자 변환, 특수문자 제거, 공백 정리
        normalized = re.sub(r'[^\w\s가-힣]', ' ', text.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """간단한 텍스트 유사도 계산 (Jaccard 유사도)"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _merge_context(
        self,
        results: List[SearchResult],
        config: ProcessingConfig
    ) -> List[SearchResult]:
        """연관된 청크들의 컨텍스트 병합"""
        if not results:
            return results
        
        # 정책별, 청크 인덱스별로 그룹화
        policy_chunks = defaultdict(list)
        for result in results:
            policy_chunks[result.policy_id].append(result)
        
        enhanced_results = []
        
        for policy_id, chunks in policy_chunks.items():
            # 청크 인덱스 순으로 정렬
            chunks.sort(key=lambda x: x.chunk_index)
            
            for chunk in chunks:
                # 인접 청크 찾기
                adjacent_chunks = self._find_adjacent_chunks(chunk, chunks)
                
                if adjacent_chunks:
                    # 확장된 컨텍스트 생성
                    extended_context = self._combine_chunks([chunk] + adjacent_chunks, config)
                    chunk.relevance_reason += " (확장된 컨텍스트)"
                    
                    # 새로운 결과로 래핑 (향후 ProcessedResult 사용 예정)
                    enhanced_results.append(chunk)
                else:
                    enhanced_results.append(chunk)
        
        logger.info(f"컨텍스트 병합 완료: {len(enhanced_results)}개 결과")
        return enhanced_results
    
    def _find_adjacent_chunks(
        self,
        target_chunk: SearchResult,
        all_chunks: List[SearchResult]
    ) -> List[SearchResult]:
        """인접한 청크들 찾기"""
        adjacent = []
        target_index = target_chunk.chunk_index
        
        for chunk in all_chunks:
            if chunk.chunk_index == target_index:
                continue
            
            # 인접한 청크 (±1, ±2 범위)
            if abs(chunk.chunk_index - target_index) <= 2:
                adjacent.append(chunk)
        
        return adjacent
    
    def _combine_chunks(
        self,
        chunks: List[SearchResult],
        config: ProcessingConfig
    ) -> str:
        """청크들을 결합하여 확장된 컨텍스트 생성"""
        # 청크 인덱스 순으로 정렬
        sorted_chunks = sorted(chunks, key=lambda x: x.chunk_index)
        
        combined_text = ""
        for chunk in sorted_chunks:
            if len(combined_text + chunk.chunk_text) > config.max_context_length:
                break
            combined_text += chunk.chunk_text + " "
        
        return combined_text.strip()
    
    def _ensure_diversity(
        self,
        results: List[SearchResult],
        config: ProcessingConfig
    ) -> List[SearchResult]:
        """검색 결과 다양성 확보 (회사 우선 고려)"""
        if len(results) <= 3:
            return results
        
        diverse_results = [results[0]]  # 최상위 결과는 항상 포함
        used_companies = {results[0].company}
        
        # 1단계: 서로 다른 회사 우선 선택
        for candidate in results[1:]:
            if candidate.company not in used_companies:
                diverse_results.append(candidate)
                used_companies.add(candidate.company)
                
                if len(diverse_results) >= config.max_results:
                    break
        
        # 2단계: 남은 자리가 있으면 기존 로직으로 채움
        if len(diverse_results) < config.max_results:
            for candidate in results[1:]:
                if candidate in diverse_results:
                    continue
                    
                # 기존 결과들과 다양성 확인
                is_diverse = True
                for existing in diverse_results:
                    similarity = self._calculate_diversity_score(candidate, existing)
                    if similarity > config.diversity_threshold:
                        is_diverse = False
                        break
                
                if is_diverse:
                    diverse_results.append(candidate)
                
                # 최대 결과 수 제한
                if len(diverse_results) >= config.max_results:
                    break
        
        logger.info(f"다양성 확보: {len(results)} -> {len(diverse_results)}, 회사 수: {len(used_companies)}")
        return diverse_results
    
    def _calculate_diversity_score(
        self,
        result1: SearchResult,
        result2: SearchResult
    ) -> float:
        """두 결과 간 다양성 점수 계산"""
        # 회사가 다르면 다양성 증가
        if result1.company != result2.company:
            company_diversity = 0.3
        else:
            company_diversity = 0.0
        
        # 상품이 다르면 다양성 증가
        if result1.product_name != result2.product_name:
            product_diversity = 0.3
        else:
            product_diversity = 0.0
        
        # 텍스트 유사도 (낮을수록 다양성 증가)
        text_similarity = self._calculate_text_similarity(
            result1.chunk_text, result2.chunk_text
        )
        
        # 종합 다양성 점수 (0: 매우 유사, 1: 매우 다양)
        diversity = company_diversity + product_diversity + (1 - text_similarity) * 0.4
        return min(diversity, 1.0)
    
    def _final_ranking(
        self,
        results: List[SearchResult],
        config: ProcessingConfig
    ) -> List[ProcessedResult]:
        """최종 순위 결정 및 ProcessedResult 변환"""
        processed_results = []
        
        for i, result in enumerate(results):
            # 순위 보정 (상위권일수록 보너스)
            rank_bonus = max(0, (len(results) - i) / len(results) * 0.1)
            
            processed_result = ProcessedResult(
                original_result=result,
                rerank_score=result.final_score,
                diversity_score=1.0,  # 다양성 필터링을 통과했으므로
                context_quality=0.8,  # 기본값
                final_score=result.final_score + rank_bonus,
                extended_context=None,
                adjacent_chunks=None,
                deduplication_group=None
            )
            
            processed_results.append(processed_result)
        
        # 최종 정렬
        processed_results.sort(key=lambda x: x.final_score, reverse=True)
        
        # 최대 개수 제한
        return processed_results[:config.max_results]
    
    def _create_fallback_result(self, result: SearchResult) -> ProcessedResult:
        """Fallback용 ProcessedResult 생성"""
        return ProcessedResult(
            original_result=result,
            rerank_score=result.final_score,
            diversity_score=1.0,
            context_quality=0.5,
            final_score=result.final_score,
            extended_context=None,
            adjacent_chunks=None,
            deduplication_group=None
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """후처리 통계 반환"""
        return {
            "cross_encoder_available": self.cross_encoder is not None,
            "config": {
                "diversity_threshold": self.config.diversity_threshold,
                "similarity_threshold": self.config.similarity_threshold,
                "max_results": self.config.max_results
            }
        }

# 전역 인스턴스
_result_service = None

def get_result_service() -> SearchResultService:
    """싱글톤 패턴으로 SearchResultService 인스턴스 반환"""
    global _result_service
    if _result_service is None:
        _result_service = SearchResultService()
    return _result_service

