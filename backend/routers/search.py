"""
검색 API 라우터
기존 프론트엔드 searchAPI와 완전 호환
Multi-Agent 시스템과 연계된 RAG 검색
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging

# Multi-Agent 시스템 import (조건부)
try:
    from agents.embedding_agent import EmbeddingAgent
    from services.vector_store import VectorStoreService
    from services.database import get_async_session
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # 고급 RAG 파이프라인 import
    from agents.query_processor import InsuranceQueryProcessor
    from services.advanced_search_engine import AdvancedSearchEngine, SearchStrategy
    from services.result_service import SearchResultService
    from services.answer_service import get_answer_service
    
    RAG_AVAILABLE = True
    
    embedding_agent = EmbeddingAgent()
    vector_store = VectorStoreService()
    query_processor = InsuranceQueryProcessor()
    search_engine = AdvancedSearchEngine()
    result_service = SearchResultService()
    answer_service = get_answer_service()
    
except ImportError as e:
    RAG_AVAILABLE = False
    embedding_agent = None
    vector_store = None
    query_processor = None
    search_engine = None
    result_service = None
    answer_service = None
    print(f"⚠️ RAG 시스템을 사용할 수 없습니다: {e}")

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic 모델 - 기존 프론트엔드 API 호환
class SearchRequest(BaseModel):
    query: str
    policy_ids: Optional[List[int]] = None
    limit: int = 10
    security_level: str = "public"

class SearchResult(BaseModel):
    policy_id: int
    policy_name: str
    company: str
    relevance_score: float
    matched_text: str
    page_number: Optional[int] = None

class SearchResponse(BaseModel):
    answer: str
    results: List[SearchResult]

async def perform_rag_search(request: SearchRequest) -> SearchResponse:
    """고급 RAG 파이프라인 기반 검색 수행"""
    try:
        logger.info(f"고급 RAG 검색 시작: '{request.query}'")
        
        # 1. 질의 전처리 및 의도 분석
        processed_query = await query_processor.preprocess_query(request.query)
        logger.info(f"질의 의도: {processed_query.intent.value}, 키워드: {processed_query.keywords}")
        
        # 2. 고급 검색 엔진을 통한 하이브리드 검색
        async with get_async_session() as db:
            search_results = await search_engine.search(
                db=db,
                processed_query=processed_query,
                strategy=SearchStrategy.ADAPTIVE
            )
        
        if not search_results:
            logger.info("고급 검색 결과 없음")
            return SearchResponse(
                answer=f"'{request.query}'에 대한 정보를 찾을 수 없습니다. 다른 키워드로 검색해보세요.",
                results=[]
            )
        
        # 3. 검색 결과 후처리 및 재랭킹
        processed_results = await result_service.process_results(
            query=processed_query,
            raw_results=search_results
        )
        
        # 4. LLM 기반 고품질 답변 생성
        generated_answer = await answer_service.generate_answer(
            query=processed_query,
            search_results=processed_results
        )
        
        # 5. 검색 결과를 API 형태로 변환
        converted_results = []
        for processed_result in processed_results:
            result = processed_result.original_result
            search_result = SearchResult(
                policy_id=result.policy_id,
                policy_name=result.product_name,
                company=result.company,
                relevance_score=processed_result.final_score,
                matched_text=result.chunk_text[:200] + "..." if len(result.chunk_text) > 200 else result.chunk_text,
                page_number=None
            )
            converted_results.append(search_result)
        
        logger.info(f"고급 RAG 검색 완료: {len(converted_results)}개 결과, 품질점수: {generated_answer.quality_score:.2f}")
        
        return SearchResponse(
            answer=generated_answer.content,
            results=converted_results
        )
        
    except Exception as e:
        logger.error(f"고급 RAG 검색 중 오류: {str(e)}")
        return await fallback_search(request)

async def fallback_search(request: SearchRequest) -> SearchResponse:
    """RAG 검색 실패 시 fallback 검색"""
    query_lower = request.query.lower()
    
    # 기본 키워드 매칭 로직 (기존과 동일)
    temp_results = []
    
    if any(keyword in query_lower for keyword in ["건강", "의료", "병원", "수술", "입원"]):
        temp_results.append(SearchResult(
            policy_id=1,
            policy_name="삼성화재 건강보험 상품",
            company="삼성화재",
            relevance_score=0.95,
            matched_text="건강보험 상품으로 입원비와 수술비를 보장하며, 질병 및 상해로 인한 의료비를 지원합니다.",
            page_number=1
        ))
        
    if any(keyword in query_lower for keyword in ["자동차", "차량", "사고", "대인", "대물"]):
        temp_results.append(SearchResult(
            policy_id=2,
            policy_name="현대해상 자동차보험",
            company="현대해상",
            relevance_score=0.88,
            matched_text="자동차 사고로 인한 대인배상, 대물배상, 자차손해를 종합적으로 보장하는 상품입니다.",
            page_number=2
        ))
    
    # 결과가 없으면 기본 응답
    if not temp_results:
        temp_results.append(SearchResult(
            policy_id=1,
            policy_name="삼성화재 건강보험 상품",
            company="삼성화재",
            relevance_score=0.3,
            matched_text="요청하신 내용과 관련된 약관 정보를 찾지 못했습니다. 보다 구체적인 질문을 해주시기 바랍니다.",
            page_number=1
        ))
    
    # 답변 생성
    if temp_results and temp_results[0].relevance_score > 0.5:
        answer = f"'{request.query}'에 대한 검색 결과를 찾았습니다. "
        if len(temp_results) == 1:
            result = temp_results[0]
            answer += f"{result.company}의 {result.policy_name}에서 관련 내용을 확인할 수 있습니다."
        else:
            answer += f"총 {len(temp_results)}개의 관련 약관을 찾았습니다."
    else:
        answer = f"'{request.query}'에 대한 정확한 정보를 찾지 못했습니다. 보다 구체적인 질문을 해주시거나, 다른 키워드로 검색해 보시기 바랍니다."
    
    return SearchResponse(answer=answer, results=temp_results[:request.limit])

def generate_answer_from_context(query: str, context_chunks: List[str]) -> str:
    """컨텍스트를 기반으로 답변 생성 (간단한 버전)"""
    if not context_chunks:
        return f"'{query}'에 대한 정보를 찾을 수 없습니다."
    
    # 간단한 규칙 기반 답변 생성
    combined_context = " ".join(context_chunks)
    
    if len(combined_context) > 500:
        summary = combined_context[:500] + "..."
    else:
        summary = combined_context
    
    answer = f"'{query}'에 대한 정보를 찾았습니다.\\n\\n{summary}\\n\\n위 내용은 관련 약관에서 추출한 정보입니다. 더 자세한 내용은 해당 약관 문서를 참조해 주세요."
    
    return answer

@router.post("/search", response_model=SearchResponse)
async def search_policies(request: SearchRequest):
    """
    약관 검색 (RAG 기반 + Multi-Agent)
    기존 프론트엔드 searchAPI.search()와 호환
    """
    try:
        logger.info(f"검색 요청: '{request.query}' (limit: {request.limit})")
        
        # 고급 RAG 파이프라인이 사용 가능한 경우 실제 검색 수행
        if (RAG_AVAILABLE and embedding_agent and vector_store and 
            query_processor and search_engine and result_service and answer_service):
            return await perform_rag_search(request)
        
        # Fallback: 기존 키워드 매칭 로직
        return await fallback_search(request)
        
    except Exception as e:
        logger.error(f"검색 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="검색 처리 중 오류가 발생했습니다."
        )
