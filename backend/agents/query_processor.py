"""
자연어 질의 전처리 및 의도 분석 에이전트
보험 도메인 특화 자연어 처리
"""
import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """질의 의도 분류"""
    SEARCH = "search"  # 정보 검색
    COMPARE = "compare"  # 비교 질의  
    CALCULATE = "calculate"  # 계산 질의
    EXPLAIN = "explain"  # 설명 요청
    APPLY = "apply"  # 신청/가입
    MODIFY = "modify"  # 변경/수정
    UNKNOWN = "unknown"  # 의도 불명

@dataclass
class ProcessedQuery:
    """전처리된 질의 데이터"""
    original: str
    normalized: str
    tokens: List[str]
    keywords: List[str]
    insurance_terms: List[str]
    intent: QueryIntent
    confidence: float
    entity_types: Dict[str, List[str]]
    query_type: str

class InsuranceQueryProcessor:
    """보험 도메인 특화 자연어 질의 전처리기"""
    
    def __init__(self):
        """초기화"""
        self.insurance_terms = self._load_insurance_terms()
        self.stop_words = self._load_stop_words()
        self._init_nlp_tools()
        
    def _load_insurance_terms(self) -> Dict[str, Dict[str, List[str]]]:
        """보험 전문 용어 사전 로드"""
        try:
            terms_path = os.path.join(os.path.dirname(__file__), "..", "data", "insurance_terms.json")
            if os.path.exists(terms_path):
                with open(terms_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"보험 용어 파일을 찾을 수 없음: {terms_path}")
                return self._get_default_insurance_terms()
        except Exception as e:
            logger.error(f"보험 용어 로드 실패: {e}")
            return self._get_default_insurance_terms()
    
    def _get_default_insurance_terms(self) -> Dict[str, Dict[str, List[str]]]:
        """기본 보험 용어 반환"""
        return {
            "medical_terms": {
                "질병": ["질병", "병", "아픔", "증상"],
                "수술": ["수술", "시술", "치료"],
                "입원": ["입원", "병원", "치료"]
            },
            "insurance_terms": {
                "보험료": ["보험료", "프리미엄", "납입금"],
                "보험금": ["보험금", "급여", "지급금"],
                "가입": ["가입", "신청", "계약"]
            },
            "coverage_terms": {
                "보장": ["보장", "커버", "담보"],
                "특약": ["특약", "옵션", "추가보장"]
            }
        }
    
    def _load_stop_words(self) -> List[str]:
        """불용어 목록 로드"""
        return [
            "은", "는", "이", "가", "을", "를", "에", "의", "와", "과", "로", "으로",
            "에서", "부터", "까지", "와", "과", "도", "만", "조차", "마저", "라도",
            "이라도", "라면", "이라면", "에게", "에서", "으로", "로써", "로서"
        ]
    
    def _init_nlp_tools(self):
        """NLP 도구 초기화 (조건부)"""
        self.spacy_nlp = None
        self.mecab = None
        
        # spaCy 초기화 시도
        try:
            import spacy
            self.spacy_nlp = spacy.load("ko_core_news_sm")
            logger.info("spaCy 한국어 모델 로드 성공")
        except Exception as e:
            logger.warning(f"spaCy 로드 실패: {e}")
        
        # MeCab 초기화 시도
        try:
            from konlpy.tag import MeCab
            self.mecab = MeCab()
            logger.info("MeCab 형태소 분석기 로드 성공")
        except Exception as e:
            logger.warning(f"MeCab 로드 실패: {e}")
    
    async def preprocess_query(self, query: str) -> ProcessedQuery:
        """질의 전처리 메인 함수"""
        try:
            # 1. 텍스트 정규화
            normalized = self._normalize_text(query)
            
            # 2. 토큰화
            tokens = self._tokenize_with_terms(normalized)
            
            # 3. 키워드 추출
            keywords = self._extract_keywords(tokens, normalized)
            
            # 4. 보험 용어 인식
            insurance_terms = self._extract_insurance_terms(normalized)
            
            # 5. 의도 분석
            intent, confidence = self._analyze_intent(normalized, tokens, keywords)
            
            # 6. 개체명 추출
            entities = self._extract_entities(tokens, normalized)
            
            # 7. 질의 타입 분석
            query_type = self._analyze_query_type(normalized)
            
            result = ProcessedQuery(
                original=query,
                normalized=normalized,
                tokens=tokens,
                keywords=keywords,
                insurance_terms=insurance_terms,
                intent=intent,
                confidence=confidence,
                entity_types=entities,
                query_type=query_type
            )
            
            logger.info(f"질의 전처리 완료: {intent.value} (신뢰도: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"질의 전처리 실패: {e}")
            # 기본값 반환
            return ProcessedQuery(
                original=query,
                normalized=query,
                tokens=[query],
                keywords=[query],
                insurance_terms=[],
                intent=QueryIntent.UNKNOWN,
                confidence=0.0,
                entity_types={},
                query_type="unknown"
            )
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        # 소문자 변환
        text = text.lower()
        
        # 특수문자 정리 (한국어는 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _tokenize_with_terms(self, text: str) -> List[str]:
        """보험 용어를 고려한 토큰화"""
        tokens = []
        
        # MeCab 사용 가능한 경우
        if self.mecab:
            try:
                morphs = self.mecab.morphs(text)
                tokens.extend(morphs)
            except Exception as e:
                logger.warning(f"MeCab 토큰화 실패: {e}")
        
        # spaCy 사용 가능한 경우
        if self.spacy_nlp:
            try:
                doc = self.spacy_nlp(text)
                spacy_tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
                tokens.extend(spacy_tokens)
            except Exception as e:
                logger.warning(f"spaCy 토큰화 실패: {e}")
        
        # Fallback: 개선된 한국어 토큰화
        if not tokens:
            tokens = self._enhanced_korean_tokenize(text)
        
        # 중복 제거 및 불용어 필터링
        filtered_tokens = []
        for token in tokens:
            if len(token) > 1 and token not in self.stop_words:
                filtered_tokens.append(token)
        
        return list(set(filtered_tokens))  # 중복 제거
    
    def _enhanced_korean_tokenize(self, text: str) -> List[str]:
        """개선된 한국어 토큰화 (spaCy/MeCab 없을 때 사용)"""
        tokens = []
        
        # 1. 기본 공백 분리
        words = text.split()
        
        # 2. 한국어 특성을 고려한 패턴 분리
        for word in words:
            # 숫자+단위 분리 (예: "10만원" -> ["10", "만원"])
            if re.search(r'\d+[가-힣]+', word):
                parts = re.findall(r'\d+|[가-힣]+', word)
                tokens.extend(parts)
            # 영어+한국어 혼합 분리 (예: "API서비스" -> ["API", "서비스"])
            elif re.search(r'[a-zA-Z]+[가-힣]+|[가-힣]+[a-zA-Z]+', word):
                parts = re.findall(r'[a-zA-Z]+|[가-힣]+', word)
                tokens.extend(parts)
            else:
                tokens.append(word)
        
        # 3. 보험 전문 용어 복합어 추출
        insurance_compounds = [
            "가입조건", "보험료", "보험금", "보장범위", "특약", "면책기간",
            "납입기간", "만기환급금", "해약환급금", "진단금", "수술비",
            "입원비", "통원비", "생명보험", "손해보험", "건강보험", "암보험",
            "심장질환", "뇌혈관질환", "교통사고", "산재보험"
        ]
        
        original_text = text
        for compound in insurance_compounds:
            if compound in original_text and compound not in tokens:
                tokens.append(compound)
        
        # 4. 중요 키워드 패턴 추출
        patterns = [
            r'\d+세',  # 나이
            r'\d+살',  # 나이
            r'\d+년',  # 기간
            r'\d+개월',  # 기간
            r'\d+만원',  # 금액
            r'\d+원'   # 금액
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, original_text)
            tokens.extend(matches)
        
        return tokens
    
    def _extract_keywords(self, tokens: List[str], text: str) -> List[str]:
        """키워드 추출"""
        keywords = []
        
        # 토큰에서 키워드 선별
        for token in tokens:
            if len(token) >= 2:  # 2글자 이상
                keywords.append(token)
        
        # 보험 관련 복합어 처리
        compound_terms = ["가입조건", "보험료", "보험금", "보장범위", "특약"]
        for term in compound_terms:
            if term in text:
                keywords.append(term)
        
        return keywords
    
    def _extract_insurance_terms(self, text: str) -> List[str]:
        """보험 전문 용어 추출"""
        found_terms = []
        
        for category, terms_dict in self.insurance_terms.items():
            for main_term, synonyms in terms_dict.items():
                # 주요 용어 확인
                if main_term in text:
                    found_terms.append(main_term)
                
                # 동의어 확인
                for synonym in synonyms:
                    if synonym in text and synonym not in found_terms:
                        found_terms.append(synonym)
        
        return found_terms
    
    def _analyze_intent(self, text: str, tokens: List[str], keywords: List[str]) -> Tuple[QueryIntent, float]:
        """의도 분석"""
        
        # 1. 변경/수정 (가장 우선)
        if any(word in text for word in ["변경", "수정", "바꾸", "해지", "취소"]):
            return QueryIntent.MODIFY, 0.9
        
        # 2. 신청/가입 (두 번째 우선, 단 설명 요청이 아닌 경우)
        if any(word in text for word in ["가입", "신청", "등록", "계약"]) and not any(word in text for word in ["어떻게", "방법", "절차"]):
            return QueryIntent.APPLY, 0.85
        
        # 3. 계산 관련 (금액이 포함되고 정보 요청이 아닌 경우)
        if any(word in text for word in ["얼마", "금액", "비용", "가격", "원", "계산"]) and not any(word in text for word in ["알려", "뭔가", "무엇"]):
            return QueryIntent.CALCULATE, 0.8
        
        # 4. 설명 요청 (높은 우선순위)
        if any(word in text for word in ["어떻게", "방법", "절차", "어떤 식"]):
            return QueryIntent.EXPLAIN, 0.9
        
        # 5. 정보 검색 (우선 처리)
        search_patterns = ["알려", "알고", "뭔가", "뭔지", "무엇", "어떤", "궁금", "문의", "조회", "확인", "정보", "소개"]
        if any(word in text for word in search_patterns):
            return QueryIntent.SEARCH, 0.85
        
        # 5. 보장/금액 관련 정보 요청
        if any(word in text for word in ["보장", "보험금"]) and any(word in text for word in ["알려", "얼마"]):
            return QueryIntent.SEARCH, 0.8  # 정보 검색으로 분류
        
        # 6. 기본 패턴 (기존 로직)
        priority_patterns = [
            (QueryIntent.MODIFY, ["변경", "수정", "바꾸", "해지"]),
            (QueryIntent.APPLY, ["가입", "신청", "등록"]),
            (QueryIntent.COMPARE, ["비교", "차이", "더"]),
            (QueryIntent.EXPLAIN, ["설명", "방법", "절차"]),
            (QueryIntent.CALCULATE, ["계산", "산출"]),
            (QueryIntent.SEARCH, ["찾", "검색", "조회", "알고", "정보", "소개", "설명해"])
        ]
        
        # 우선순위 순으로 패턴 매칭
        for intent, patterns in priority_patterns:
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                if pattern in text:
                    score += 2  # 전체 텍스트에서 매칭시 높은 점수
                    matched_patterns.append(pattern)
                else:
                    # 토큰에서 부분 매칭
                    for token in tokens:
                        if pattern in token:
                            score += 1
                            matched_patterns.append(pattern)
                            break
            
            # 충분한 점수가 있으면 해당 의도로 결정
            if score >= 1:
                confidence = min(score / 3.0, 1.0)
                
                # 특정 패턴에 대한 신뢰도 보정
                if intent == QueryIntent.MODIFY and any(p in text for p in ["변경", "수정", "해지"]):
                    confidence = max(confidence, 0.8)
                elif intent == QueryIntent.COMPARE and any(p in text for p in ["비교", "차이", "더"]):
                    confidence = max(confidence, 0.8)
                elif intent == QueryIntent.CALCULATE and any(p in text for p in ["얼마", "금액", "원"]):
                    confidence = max(confidence, 0.8)
                
                return intent, confidence
        
        # 아무 패턴도 매칭되지 않으면 UNKNOWN
        return QueryIntent.UNKNOWN, 0.0
    
    def _extract_entities(self, tokens: List[str], original_text: str) -> Dict[str, List[str]]:
        """개체명 추출"""
        entities = {
            "amounts": [],
            "periods": [],
            "age": [],
            "diseases": [],
            "body_parts": []
        }
        
        text = original_text
        
        # 금액 패턴
        amount_patterns = [
            r'(\d+(?:,\d{3})*)\s*원',
            r'(\d+)\s*만\s*원',
            r'(\d+)\s*천\s*원'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            entities["amounts"].extend(matches)
        
        # 기간 패턴
        period_patterns = [
            r'(\d+)\s*년',
            r'(\d+)\s*개월',
            r'(\d+)\s*일'
        ]
        
        for pattern in period_patterns:
            matches = re.findall(pattern, text)
            entities["periods"].extend(matches)
        
        # 나이 패턴
        age_patterns = [
            r'(\d+)\s*세',
            r'(\d+)\s*살'
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, text)
            entities["age"].extend(matches)
        
        # 질병명 (보험 용어에서)
        medical_terms = self.insurance_terms.get("medical_terms", {})
        for disease in medical_terms.keys():
            if disease in text:
                entities["diseases"].append(disease)
        
        return entities
    
    def _analyze_query_type(self, text: str) -> str:
        """질의 타입 분석"""
        question_patterns = {
            "what": ["무엇", "뭐", "뭔가"],
            "how": ["어떻게", "방법", "어떤"],
            "when": ["언제", "시기"],
            "where": ["어디", "곳"],
            "why": ["왜", "이유"],
            "how_much": ["얼마", "금액"]
        }
        
        for q_type, patterns in question_patterns.items():
            if any(pattern in text for pattern in patterns):
                return q_type
        
        return "statement"
    
    def analyze_query_complexity(self, processed_query: ProcessedQuery) -> Dict[str, Any]:
        """질의 복잡도 분석"""
        complexity_score = 0
        
        # 키워드 수
        complexity_score += len(processed_query.keywords) * 0.5
        
        # 보험 용어 수
        complexity_score += len(processed_query.insurance_terms) * 1.0
        
        # 개체명 수
        entity_count = sum(len(entities) for entities in processed_query.entity_types.values())
        complexity_score += entity_count * 0.8
        
        # 의도의 신뢰도 (낮을수록 복잡)
        complexity_score += (1 - processed_query.confidence) * 2.0
        
        if complexity_score < 2:
            level = "low"
        elif complexity_score < 5:
            level = "medium"
        else:
            level = "high"
        
        return {
            "level": level,
            "score": round(complexity_score, 2),
            "token_count": len(processed_query.tokens),
            "insurance_term_count": len(processed_query.insurance_terms),
            "entity_count": entity_count
        }
