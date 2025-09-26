"""
고급 벡터 유사도 검색 엔진
하이브리드 검색(벡터+키워드), 동적 임계값 조정, Top-N 최적화
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import json

from services.vector_store import VectorStoreService
from services.multi_model_embedding import get_multi_model_embedding_agent
from agents.query_processor import ProcessedQuery, QueryIntent

logger = logging.getLogger(__name__)

class SearchStrategy(Enum):
    """검색 전략"""
    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"

@dataclass
class SearchConfig:
    """검색 설정"""
    similarity_threshold: float = 0.7
    keyword_threshold: float = 0.5
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    top_k: int = 10
    rerank_top_n: int = 50
    max_tokens: int = 4000
    adaptive_threshold: bool = True

@dataclass
class SearchResult:
    """검색 결과"""
    embedding_id: int
    policy_id: int
    chunk_text: str
    chunk_index: int
    product_name: str
    company: str
    category: str
    vector_score: float
    keyword_score: float
    hybrid_score: float
    final_score: float
    model: str
    created_at: str
    relevance_reason: str

class AdvancedSearchEngine(VectorStoreService):
    """고급 벡터 검색 엔진"""
    
    def __init__(self, embedding_model: str = "text-embedding-3-large"):
        super().__init__(embedding_model)
        self.config = SearchConfig()
        self.embedding_agent = None
        self._performance_stats = {
            "search_count": 0,
            "avg_response_time": 0.0,
            "cache_hits": 0,
            "search_quality_scores": []
        }
        self._query_cache = {}  # 간단한 캐시
        
    async def _get_embedding_agent(self):
        """임베딩 에이전트 지연 로딩"""
        if self.embedding_agent is None:
            self.embedding_agent = get_multi_model_embedding_agent()
        return self.embedding_agent
    
    async def search(
        self,
        db: AsyncSession,
        processed_query: ProcessedQuery,
        strategy: SearchStrategy = SearchStrategy.ADAPTIVE,
        config: Optional[SearchConfig] = None
    ) -> List[SearchResult]:
        """통합 검색 메인 함수"""
        start_time = time.time()
        
        try:
            # 설정 적용
            search_config = config or self.config
            
            # 캐시 확인
            cache_key = self._generate_cache_key(processed_query, strategy, search_config)
            if cache_key in self._query_cache:
                self._performance_stats["cache_hits"] += 1
                logger.info("캐시에서 검색 결과 반환")
                return self._query_cache[cache_key]
            
            # 질의 임베딩 생성
            query_embedding = await self._generate_query_embedding(processed_query)
            
            # 검색 전략에 따른 검색 수행
            if strategy == SearchStrategy.ADAPTIVE:
                results = await self._adaptive_search(db, processed_query, query_embedding, search_config)
            elif strategy == SearchStrategy.HYBRID:
                results = await self._hybrid_search(db, processed_query, query_embedding, search_config)
            elif strategy == SearchStrategy.VECTOR_ONLY:
                results = await self._vector_search(db, query_embedding, search_config)
            elif strategy == SearchStrategy.KEYWORD_ONLY:
                results = await self._keyword_search(db, processed_query, search_config)
            else:
                results = await self._hybrid_search(db, processed_query, query_embedding, search_config)
            
            # 후처리 및 재랭킹
            final_results = await self._post_process_results(results, processed_query, search_config)
            
            # 성능 통계 업데이트
            response_time = time.time() - start_time
            self._update_performance_stats(response_time, len(final_results))
            
            # 캐시에 저장
            self._query_cache[cache_key] = final_results
            
            logger.info(f"검색 완료: {len(final_results)}개 결과, {response_time*1000:.1f}ms")
            return final_results
            
        except Exception as e:
            logger.error(f"검색 실패: {e}")
            return []
    
    async def _generate_query_embedding(self, processed_query: ProcessedQuery) -> List[float]:
        """질의 임베딩 생성"""
        try:
            embedding_agent = await self._get_embedding_agent()
            
            # 키워드와 보험 용어를 결합한 검색 쿼리 생성
            search_text = processed_query.original
            if processed_query.insurance_terms:
                search_text += " " + " ".join(processed_query.insurance_terms)
            
            embeddings = await embedding_agent.generate_embeddings([search_text])
            return embeddings[0] if embeddings else []
            
        except Exception as e:
            logger.error(f"질의 임베딩 생성 실패: {e}")
            return []
    
    async def _vector_search(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        config: SearchConfig
    ) -> List[SearchResult]:
        """순수 벡터 검색"""
        try:
            # 기존 search_similar 메서드 활용
            raw_results = await self.search_similar(
                db=db,
                query_embedding=query_embedding,
                limit=config.rerank_top_n,
                similarity_threshold=config.similarity_threshold
            )
            
            # SearchResult 객체로 변환
            results = []
            for raw in raw_results:
                result = SearchResult(
                    embedding_id=raw["embedding_id"],
                    policy_id=raw["policy_id"],
                    chunk_text=raw["chunk_text"],
                    chunk_index=raw["chunk_index"],
                    product_name=raw["product_name"],
                    company=raw["company"],
                    category=raw["category"],
                    vector_score=raw["similarity_score"],
                    keyword_score=0.0,
                    hybrid_score=raw["similarity_score"],
                    final_score=raw["similarity_score"],
                    model=raw["model"],
                    created_at=str(raw["created_at"]),
                    relevance_reason="벡터 유사도 매칭"
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []
    
    async def _keyword_search(
        self,
        db: AsyncSession,
        processed_query: ProcessedQuery,
        config: SearchConfig
    ) -> List[SearchResult]:
        """키워드 기반 검색 (PostgreSQL Full-Text Search)"""
        try:
            # 검색 키워드 준비
            keywords = processed_query.keywords + processed_query.insurance_terms
            if not keywords:
                keywords = processed_query.tokens
            
            # PostgreSQL Full-Text Search 쿼리 (안전한 문자열 처리)
            safe_keywords = [keyword.replace("'", "''").replace("&", "").replace("|", "") for keyword in keywords[:10]]
            safe_keywords = [k.strip() for k in safe_keywords if k.strip()]
            
            if not safe_keywords:
                # 검색어가 없으면 빈 결과 반환
                return []
                
            # 안전한 검색어 조합 (OR 연산 사용)
            search_terms = " | ".join(safe_keywords)  # OR 연산으로 변경 (더 안전)
            
            # 한국어 친화적인 키워드 검색 쿼리
            keyword_conditions = []
            for i, keyword in enumerate(safe_keywords[:5]):  # 최대 5개 키워드만 사용
                keyword_conditions.append(f"e.chunk_text ILIKE '%' || :keyword_{i} || '%'")
            
            where_clause = " OR ".join(keyword_conditions)
            
            keyword_query = f"""
                SELECT 
                    e.id,
                    e.policy_id,
                    e.chunk_text,
                    e.chunk_index,
                    e.model,
                    e.created_at,
                    p.product_name,
                    p.company,
                    p.category,
                    -- 키워드 매칭 점수 계산 (한국어 특화)
                    (
                        {" + ".join([f"CASE WHEN e.chunk_text ILIKE '%' || :keyword_{i} || '%' THEN 1 ELSE 0 END" for i in range(len(safe_keywords[:5]))])}
                    ) AS keyword_score
                FROM embeddings_text_embedding_3 e
                JOIN policies p ON e.policy_id = p.policy_id
                WHERE {where_clause}
                ORDER BY keyword_score DESC, e.id
                LIMIT :limit
            """
            
            # 한국어 전문 검색이 안될 경우 LIKE 검색으로 대체
            fallback_query = f"""
                SELECT 
                    e.id,
                    e.policy_id,
                    e.chunk_text,
                    e.chunk_index,
                    e.model,
                    e.created_at,
                    p.product_name,
                    p.company,
                    p.category,
                    (CASE 
                        WHEN e.chunk_text ILIKE '%' || :first_keyword || '%' THEN 1.0
                        ELSE 0.5
                    END) AS keyword_score
                FROM embeddings_text_embedding_3 e
                JOIN policies p ON e.policy_id = p.policy_id
                WHERE e.chunk_text ILIKE '%' || :first_keyword || '%'
                ORDER BY keyword_score DESC
                LIMIT :limit
            """
            
            try:
                # 키워드별 파라미터 생성
                params = {"limit": config.rerank_top_n}
                for i, keyword in enumerate(safe_keywords[:5]):
                    params[f"keyword_{i}"] = keyword
                
                # 한국어 친화적인 키워드 검색 실행
                result = await db.execute(text(keyword_query), params)
                rows = result.fetchall()
                    
            except Exception as e:
                logger.warning(f"전문 검색 실패, fallback 사용: {e}")
                
                # 전문 검색 실패시 새로운 세션에서 fallback 시도
                if safe_keywords:
                    try:
                        # 새로운 세션 사용
                        from services.database import get_async_session
                        async with get_async_session() as new_db:
                            result = await new_db.execute(
                                text(fallback_query),
                                {"first_keyword": safe_keywords[0], "limit": config.rerank_top_n}
                            )
                            rows = result.fetchall()
                    except Exception as fallback_error:
                        logger.error(f"Fallback 검색도 실패: {fallback_error}")
                        rows = []
                else:
                    rows = []
            
            # SearchResult 객체로 변환
            results = []
            for row in rows:
                result = SearchResult(
                    embedding_id=row.id,
                    policy_id=row.policy_id,
                    chunk_text=row.chunk_text,
                    chunk_index=row.chunk_index,
                    product_name=row.product_name,
                    company=row.company,
                    category=row.category,
                    vector_score=0.0,
                    keyword_score=float(row.keyword_score),
                    hybrid_score=float(row.keyword_score),
                    final_score=float(row.keyword_score),
                    model=row.model,
                    created_at=str(row.created_at),
                    relevance_reason="키워드 매칭"
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {e}")
            return []
    
    async def _hybrid_search(
        self,
        db: AsyncSession,
        processed_query: ProcessedQuery,
        query_embedding: List[float],
        config: SearchConfig
    ) -> List[SearchResult]:
        """하이브리드 검색 (벡터 + 키워드)"""
        try:
            # 순차 실행으로 변경 (DB 연결 문제 방지)
            vector_results = await self._vector_search(db, query_embedding, config)
            keyword_results = await self._keyword_search(db, processed_query, config)
            
            # 결과 통합 및 스코어 계산
            combined_results = self._combine_search_results(
                vector_results, keyword_results, config
            )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            return []
    
    async def _adaptive_search(
        self,
        db: AsyncSession,
        processed_query: ProcessedQuery,
        query_embedding: List[float],
        config: SearchConfig
    ) -> List[SearchResult]:
        """적응형 검색 (질의 유형에 따른 전략 선택)"""
        try:
            # 질의 의도에 따른 전략 선택
            if processed_query.intent == QueryIntent.CALCULATE:
                # 계산 질의는 키워드 검색이 더 효과적
                weight_config = SearchConfig(
                    vector_weight=0.3,
                    keyword_weight=0.7,
                    similarity_threshold=0.6
                )
            elif processed_query.intent == QueryIntent.COMPARE:
                # 비교 질의는 균형잡힌 검색
                weight_config = SearchConfig(
                    vector_weight=0.5,
                    keyword_weight=0.5,
                    similarity_threshold=0.7
                )
            elif processed_query.intent == QueryIntent.SEARCH:
                # 정보 검색은 벡터 검색이 더 효과적
                weight_config = SearchConfig(
                    vector_weight=0.8,
                    keyword_weight=0.2,
                    similarity_threshold=0.75
                )
            else:
                # 기본 하이브리드
                weight_config = config
            
            # 복잡도에 따른 임계값 조정
            complexity = len(processed_query.keywords) + len(processed_query.insurance_terms)
            if complexity > 5:
                weight_config.similarity_threshold *= 0.9  # 복잡한 질의는 임계값 낮춤
            
            return await self._hybrid_search(db, processed_query, query_embedding, weight_config)
            
        except Exception as e:
            logger.error(f"적응형 검색 실패: {e}")
            return []
    
    def _combine_search_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        config: SearchConfig
    ) -> List[SearchResult]:
        """벡터 검색과 키워드 검색 결과 통합"""
        try:
            # 결과를 embedding_id로 그룹화
            combined_map = {}
            
            # 벡터 검색 결과 추가
            for result in vector_results:
                combined_map[result.embedding_id] = result
            
            # 키워드 검색 결과 통합
            for result in keyword_results:
                if result.embedding_id in combined_map:
                    # 기존 결과 업데이트
                    existing = combined_map[result.embedding_id]
                    existing.keyword_score = result.keyword_score
                    existing.relevance_reason = "벡터+키워드 매칭"
                else:
                    # 새 결과 추가
                    combined_map[result.embedding_id] = result
            
            # 하이브리드 스코어 계산
            combined_results = []
            for result in combined_map.values():
                # 정규화된 하이브리드 스코어
                hybrid_score = (
                    config.vector_weight * result.vector_score +
                    config.keyword_weight * result.keyword_score
                )
                
                result.hybrid_score = hybrid_score
                result.final_score = hybrid_score
                combined_results.append(result)
            
            # 스코어 순으로 정렬
            combined_results.sort(key=lambda x: x.final_score, reverse=True)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"검색 결과 통합 실패: {e}")
            return vector_results  # fallback
    
    async def _post_process_results(
        self,
        results: List[SearchResult],
        processed_query: ProcessedQuery,
        config: SearchConfig
    ) -> List[SearchResult]:
        """검색 결과 후처리"""
        try:
            # 중복 제거 (같은 policy_id, 비슷한 chunk_index)
            deduplicated = self._deduplicate_results(results)
            
            # 토큰 수 제한 고려한 결과 선택
            filtered = self._filter_by_token_limit(deduplicated, config.max_tokens)
            
            # 최종 Top-K 선택
            top_results = filtered[:config.top_k]
            
            # 관련성 이유 업데이트
            for result in top_results:
                result.relevance_reason = self._generate_relevance_reason(result, processed_query)
            
            return top_results
            
        except Exception as e:
            logger.error(f"검색 결과 후처리 실패: {e}")
            return results[:config.top_k]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """중복 결과 제거"""
        seen_combinations = set()
        deduplicated = []
        
        for result in results:
            # policy_id와 chunk_index 근처의 중복 체크
            key = (result.policy_id, result.chunk_index // 3)  # 3개 청크마다 그룹화
            
            if key not in seen_combinations:
                seen_combinations.add(key)
                deduplicated.append(result)
        
        return deduplicated
    
    def _filter_by_token_limit(self, results: List[SearchResult], max_tokens: int) -> List[SearchResult]:
        """토큰 수 제한에 따른 필터링"""
        filtered = []
        total_tokens = 0
        
        for result in results:
            # 간단한 토큰 수 추정 (한국어 기준)
            estimated_tokens = len(result.chunk_text) // 2
            
            if total_tokens + estimated_tokens <= max_tokens:
                filtered.append(result)
                total_tokens += estimated_tokens
            else:
                break
        
        return filtered
    
    def _generate_relevance_reason(self, result: SearchResult, processed_query: ProcessedQuery) -> str:
        """관련성 이유 생성"""
        reasons = []
        
        if result.vector_score > 0.8:
            reasons.append("높은 의미적 유사도")
        
        if result.keyword_score > 0.7:
            reasons.append("키워드 직접 매칭")
        
        # 보험 용어 매칭 확인
        for term in processed_query.insurance_terms:
            if term in result.chunk_text:
                reasons.append(f"'{term}' 용어 매칭")
        
        if not reasons:
            reasons.append("일반적 관련성")
        
        return ", ".join(reasons)
    
    def _generate_cache_key(self, processed_query: ProcessedQuery, strategy: SearchStrategy, config: SearchConfig) -> str:
        """캐시 키 생성"""
        key_data = {
            "query": processed_query.normalized,
            "intent": processed_query.intent.value,
            "strategy": strategy.value,
            "threshold": config.similarity_threshold,
            "top_k": config.top_k
        }
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    def _update_performance_stats(self, response_time: float, result_count: int):
        """성능 통계 업데이트"""
        self._performance_stats["search_count"] += 1
        
        # 이동 평균으로 응답 시간 업데이트
        current_avg = self._performance_stats["avg_response_time"]
        count = self._performance_stats["search_count"]
        self._performance_stats["avg_response_time"] = (current_avg * (count - 1) + response_time) / count
        
        # 검색 품질 점수 (임시)
        quality_score = min(result_count / 10, 1.0)  # 10개 결과를 최대로 가정
        self._performance_stats["search_quality_scores"].append(quality_score)
        
        # 최근 100개만 유지
        if len(self._performance_stats["search_quality_scores"]) > 100:
            self._performance_stats["search_quality_scores"] = self._performance_stats["search_quality_scores"][-100:]
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        quality_scores = self._performance_stats["search_quality_scores"]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "search_count": self._performance_stats["search_count"],
            "avg_response_time_ms": self._performance_stats["avg_response_time"] * 1000,
            "cache_hit_rate": (
                self._performance_stats["cache_hits"] / max(self._performance_stats["search_count"], 1)
            ),
            "avg_search_quality": avg_quality,
            "cache_size": len(self._query_cache)
        }
    
    def clear_cache(self):
        """캐시 초기화"""
        self._query_cache.clear()
        logger.info("검색 캐시 초기화 완료")

# 전역 인스턴스
_advanced_search_engine = None

def get_advanced_search_engine() -> AdvancedSearchEngine:
    """싱글톤 패턴으로 AdvancedSearchEngine 인스턴스 반환"""
    global _advanced_search_engine
    if _advanced_search_engine is None:
        _advanced_search_engine = AdvancedSearchEngine()
    return _advanced_search_engine
