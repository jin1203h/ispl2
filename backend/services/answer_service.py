"""
LLM 기반 답변 생성 서비스
GPT-4o, Claude 등과 통합된 RAG 답변 생성 시스템
"""
import asyncio
import logging
import time
import os
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import re

from agents.query_processor import ProcessedQuery
from services.result_service import ProcessedResult

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """LLM 공급자"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"

@dataclass
class AnswerConfig:
    """답변 생성 설정"""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 2000
    max_context_length: int = 8000
    min_quality_score: float = 0.7
    citation_format: str = "standard"

@dataclass
class GeneratedAnswer:
    """생성된 답변"""
    content: str
    sources: List[Dict[str, Any]]
    quality_score: float
    confidence: float
    generation_time: float
    token_usage: Dict[str, int]
    citations: List[str]
    model_used: str

class RAGAnswerService:
    """RAG 기반 답변 생성 서비스"""
    
    def __init__(self, config: Optional[AnswerConfig] = None):
        self.config = config or AnswerConfig()
        self.client = None
        self.system_prompt = self._load_system_prompt()
        self._init_llm_client()
        
    def _load_system_prompt(self) -> str:
        """시스템 프롬프트 로드"""
        try:
            prompt_path = os.path.join(
                os.path.dirname(__file__), "..", "prompts", "insurance_rag_prompt.txt"
            )
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning("보험 프롬프트 파일 없음, 기본 프롬프트 사용")
                return self._get_default_prompt()
        except Exception as e:
            logger.error(f"프롬프트 로드 실패: {e}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """기본 시스템 프롬프트"""
        return """당신은 전문 보험 상담사입니다. 제공된 보험약관 정보를 바탕으로 정확하고 도움이 되는 답변을 제공하세요.

답변 시 다음을 준수하세요:
1. 제공된 정보에만 기반하여 답변
2. 보험 전문용어는 쉽게 설명
3. 출처를 명시하여 신뢰성 확보
4. 친근하고 이해하기 쉬운 어조 사용
5. 불확실한 경우 보험회사 문의 안내"""
    
    def _init_llm_client(self):
        """LLM 클라이언트 초기화"""
        try:
            if self.config.provider == LLMProvider.OPENAI:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info("OpenAI 클라이언트 초기화 성공")
            elif self.config.provider == LLMProvider.ANTHROPIC:
                # Anthropic 클라이언트 초기화 (향후 구현)
                logger.warning("Anthropic 클라이언트는 아직 구현되지 않음")
                self.client = None
            else:
                logger.warning(f"지원하지 않는 LLM 공급자: {self.config.provider}")
                self.client = None
        except ImportError as e:
            logger.warning(f"LLM 클라이언트 라이브러리 없음: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"LLM 클라이언트 초기화 실패: {e}")
            self.client = None
    
    async def generate_answer(
        self,
        query: ProcessedQuery,
        search_results: List[ProcessedResult],
        config: Optional[AnswerConfig] = None
    ) -> GeneratedAnswer:
        """RAG 답변 생성"""
        generation_config = config or self.config
        start_time = time.time()
        
        try:
            # 1. 컨텍스트 구성
            context = self._build_context(search_results, generation_config)
            
            # 2. 프롬프트 구성
            user_prompt = self._build_rag_prompt(query, context)
            
            # 3. LLM 답변 생성
            if self.client:
                llm_response = await self._call_llm(user_prompt, generation_config)
                answer_content = llm_response["content"]
                token_usage = llm_response["usage"]
            else:
                # Fallback 답변
                answer_content = self._generate_fallback_answer(query, search_results)
                token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
            # 4. 출처 정보 추출
            sources = self._extract_sources(search_results)
            
            # 5. 인용 구문 생성
            citations = self._generate_citations(search_results, generation_config)
            
            # 6. 답변 품질 검증
            quality_score = await self._validate_answer_quality(
                answer_content, query, search_results
            )
            
            # 7. 신뢰도 계산
            confidence = self._calculate_confidence(search_results, quality_score)
            
            generation_time = time.time() - start_time
            
            result = GeneratedAnswer(
                content=answer_content,
                sources=sources,
                quality_score=quality_score,
                confidence=confidence,
                generation_time=generation_time,
                token_usage=token_usage,
                citations=citations,
                model_used=generation_config.model
            )
            
            logger.info(f"답변 생성 완료: {generation_time:.2f}초, 품질: {quality_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"답변 생성 실패: {e}")
            return self._create_error_response(query, str(e), time.time() - start_time)
    
    def _build_context(
        self,
        search_results: List[ProcessedResult],
        config: AnswerConfig
    ) -> str:
        """검색 결과로부터 컨텍스트 구성"""
        context_parts = []
        total_length = 0
        
        for i, result in enumerate(search_results):
            # 결과 정보 구성
            source_info = f"[출처 {i+1}] {result.original_result.product_name} - {result.original_result.company}"
            content = result.original_result.chunk_text
            
            # 확장된 컨텍스트가 있으면 사용
            if result.extended_context:
                content = result.extended_context
            
            context_part = f"{source_info}\n{content}\n"
            
            # 길이 제한 확인
            if total_length + len(context_part) > config.max_context_length:
                break
            
            context_parts.append(context_part)
            total_length += len(context_part)
        
        return "\n".join(context_parts)
    
    def _build_rag_prompt(self, query: ProcessedQuery, context: str) -> str:
        """RAG 프롬프트 구성"""
        intent_description = {
            "search": "정보를 찾고 있습니다",
            "compare": "상품들을 비교하고 있습니다", 
            "calculate": "금액이나 수치를 계산하고 있습니다",
            "explain": "절차나 방법을 설명해달라고 합니다",
            "apply": "가입이나 신청을 원합니다",
            "modify": "변경이나 수정을 원합니다"
        }.get(query.intent.value, "질문하고 있습니다")
        
        prompt = f"""다음은 고객의 질문과 관련된 보험약관 정보입니다:

<보험약관 정보>
{context}
</보험약관 정보>

<고객 질문>
질문: {query.original}
의도: 고객이 {intent_description}
키워드: {', '.join(query.keywords)}
보험용어: {', '.join(query.insurance_terms)}
</고객 질문>

위 보험약관 정보를 바탕으로 고객의 질문에 대해 정확하고 도움이 되는 답변을 작성해주세요.

답변 시 다음을 포함해주세요:
1. 질문에 대한 명확한 답변
2. 관련 조건이나 절차
3. 주의사항이나 예외사항
4. 출처 정보 (상품명, 회사명 포함)

답변 형식:
## 답변

[질문에 대한 핵심 답변]

## 상세 설명

[구체적인 조건, 절차, 주의사항]

## 관련 정보

[추가로 알아두면 좋은 정보]

## 출처

[참고한 약관이나 상품 정보]"""

        return prompt
    
    async def _call_llm(self, prompt: str, config: AnswerConfig) -> Dict[str, Any]:
        """LLM API 호출"""
        try:
            if config.provider == LLMProvider.OPENAI:
                response = await self.client.chat.completions.create(
                    model=config.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
                
                return {
                    "content": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            else:
                raise ValueError(f"지원하지 않는 LLM 공급자: {config.provider}")
                
        except Exception as e:
            logger.error(f"LLM API 호출 실패: {e}")
            raise
    
    def _generate_fallback_answer(
        self,
        query: ProcessedQuery,
        search_results: List[ProcessedResult]
    ) -> str:
        """Fallback 답변 생성 (LLM 없을 때)"""
        if not search_results:
            return f"죄송합니다. '{query.original}' 질문에 대한 관련 정보를 찾을 수 없습니다. 자세한 내용은 보험회사에 직접 문의해주시기 바랍니다."
        
        # 검색 결과 기반 간단한 답변 구성
        answer_parts = ["질문하신 내용과 관련된 정보입니다:\n"]
        
        for i, result in enumerate(search_results[:3]):
            answer_parts.append(f"{i+1}. {result.original_result.product_name} ({result.original_result.company})")
            answer_parts.append(f"   {result.original_result.chunk_text[:200]}...")
            answer_parts.append("")
        
        answer_parts.append("더 자세한 정보는 해당 보험회사에 직접 문의하시기 바랍니다.")
        
        return "\n".join(answer_parts)
    
    def _extract_sources(self, search_results: List[ProcessedResult]) -> List[Dict[str, Any]]:
        """출처 정보 추출"""
        sources = []
        
        for result in search_results:
            source = {
                "product_name": result.original_result.product_name,
                "company": result.original_result.company,
                "category": result.original_result.category,
                "chunk_index": result.original_result.chunk_index,
                "relevance_score": result.final_score,
                "text_preview": result.original_result.chunk_text[:100] + "..."
            }
            sources.append(source)
        
        return sources
    
    def _generate_citations(
        self,
        search_results: List[ProcessedResult],
        config: AnswerConfig
    ) -> List[str]:
        """인용 구문 생성"""
        citations = []
        
        for i, result in enumerate(search_results):
            if config.citation_format == "standard":
                citation = f"[{i+1}] {result.original_result.product_name}, {result.original_result.company}"
            elif config.citation_format == "detailed":
                citation = f"[{i+1}] {result.original_result.product_name}, {result.original_result.company}, 청크 {result.original_result.chunk_index}"
            else:
                citation = f"[{i+1}] {result.original_result.product_name}"
            
            citations.append(citation)
        
        return citations
    
    async def _validate_answer_quality(
        self,
        answer: str,
        query: ProcessedQuery,
        search_results: List[ProcessedResult]
    ) -> float:
        """답변 품질 검증"""
        try:
            quality_score = 0.0
            
            # 1. 길이 검증 (너무 짧거나 길지 않은지)
            if 50 <= len(answer) <= 3000:
                quality_score += 0.2
            
            # 2. 키워드 포함 검증
            query_keywords = set(query.keywords + query.insurance_terms)
            answer_lower = answer.lower()
            
            matched_keywords = sum(1 for keyword in query_keywords if keyword.lower() in answer_lower)
            if query_keywords:
                keyword_score = matched_keywords / len(query_keywords)
                quality_score += keyword_score * 0.3
            
            # 3. 구조 검증 (제목, 섹션 등이 있는지)
            structure_indicators = ["##", "**", "답변", "설명", "정보", "출처"]
            structure_score = sum(1 for indicator in structure_indicators if indicator in answer)
            quality_score += min(structure_score / len(structure_indicators), 1.0) * 0.2
            
            # 4. 출처 언급 검증
            source_mentioned = any(
                result.original_result.product_name in answer or 
                result.original_result.company in answer
                for result in search_results
            )
            if source_mentioned:
                quality_score += 0.3
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.warning(f"답변 품질 검증 실패: {e}")
            return 0.5  # 기본값
    
    def _calculate_confidence(
        self,
        search_results: List[ProcessedResult],
        quality_score: float
    ) -> float:
        """신뢰도 계산"""
        if not search_results:
            return 0.0
        
        # 검색 결과 점수 평균
        avg_relevance = sum(r.final_score for r in search_results) / len(search_results)
        
        # 결과 개수 고려 (더 많은 결과 = 더 높은 신뢰도)
        result_count_factor = min(len(search_results) / 5, 1.0)
        
        # 품질 점수와 결합
        confidence = (avg_relevance * 0.4 + quality_score * 0.4 + result_count_factor * 0.2)
        
        return min(confidence, 1.0)
    
    def _create_error_response(
        self,
        query: ProcessedQuery,
        error_message: str,
        generation_time: float
    ) -> GeneratedAnswer:
        """오류 응답 생성"""
        return GeneratedAnswer(
            content=f"죄송합니다. 답변 생성 중 오류가 발생했습니다. 다시 시도해주시거나 고객센터에 문의해주세요.\n\n오류: {error_message}",
            sources=[],
            quality_score=0.0,
            confidence=0.0,
            generation_time=generation_time,
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            citations=[],
            model_used=self.config.model
        )
    
    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계 반환"""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "client_available": self.client is not None,
            "system_prompt_loaded": len(self.system_prompt) > 0,
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "max_context_length": self.config.max_context_length
            }
        }

# 전역 인스턴스
_answer_service = None

def get_answer_service() -> RAGAnswerService:
    """싱글톤 패턴으로 RAGAnswerService 인스턴스 반환"""
    global _answer_service
    if _answer_service is None:
        _answer_service = RAGAnswerService()
    return _answer_service

