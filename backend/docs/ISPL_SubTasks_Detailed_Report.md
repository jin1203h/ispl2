# ISPL Insurance Policy AI - 서브 타스크 분할 상세 보고서

**생성일**: 2025년 9월 23일  
**프로젝트**: ISPL Insurance Policy AI 시스템  
**목적**: 전체 메인 타스크들을 체계적인 서브 타스크로 분할하여 효율적인 프로젝트 관리 구현

---

## 📋 **전체 서브 타스크 현황**

### **✅ 완료된 타스크** (5개)
- **Task 1**: FastAPI 백엔드 기본 구조 및 API 엔드포인트 구현
- **Task 2**: LangGraph Multi-Agent 아키텍처 설계 및 구현  
- **Task 3.1**: PDF 품질 분석 및 구조 파악
- **Task 3.2**: 텍스트 추출 및 정제 강화
- **Task 3.3**: 표 데이터 처리 및 구조화 고도화

### **⏳ 대기 중인 타스크** (27개)
- **Task 3 남은 서브 타스크**: 3.4, 3.5, 3.6 (3개)
- **Task 4 서브 타스크**: 4.1, 4.2, 4.3, 4.4 (4개)
- **Task 5 서브 타스크**: 5.1, 5.2, 5.3, 5.4 (4개)
- **Task 6 서브 타스크**: 6.1, 6.2, 6.3, 6.4 (4개)
- **Task 7 서브 타스크**: 7.1, 7.2, 7.3 (3개)
- **Task 8 서브 타스크**: 8.1, 8.2, 8.3 (3개)
- **기타 메인 타스크**: 6개

---

## 🎯 **Task 1: FastAPI 백엔드 기본 구조** ✅ **완료**

### **ID**: `8063f2ff-5c5b-4600-b7f1-e2bc70654a2a`
### **상태**: 완료 (2025/9/22 17:45:59)

#### **📝 설명**
기존 프론트엔드 API 서비스와 완전 호환되는 FastAPI 백엔드 서버를 구현합니다. 인증, 약관 관리, 검색, 워크플로우 모니터링 API를 포함하여 기존 React 앱이 즉시 연동 가능하도록 구성합니다.

#### **🔧 구현 가이드**
```python
# FastAPI 프로젝트 구조 생성
- backend/main.py: FastAPI 앱 초기화, CORS 설정
- backend/routers/: auth.py, policies.py, search.py, workflow.py
- backend/models/: SQLAlchemy 모델, Pydantic 스키마
- backend/services/: database.py, auth_service.py

# 기존 API 인터페이스 구현
- POST /auth/login, /auth/register, GET /auth/verify
- POST /policies/upload, GET /policies, DELETE /policies/{id}
- GET /policies/{id}/pdf, /policies/{id}/md
- POST /search (RAG 검색)
- GET /workflow/logs

# 데이터베이스 연결
- SQLAlchemy ORM 설정
- PostgreSQL + pgvector 연결
- 기존 테이블 스키마 활용

# JWT 인증 시스템
- 토큰 생성/검증
- 미들웨어 설정
- 사용자 권한 관리
```

#### **✓ 검증 기준**
1. 모든 기존 API 엔드포인트가 정상 동작하여 프론트엔드와 연동 성공
2. JWT 인증이 정상 작동하여 로그인/로그아웃 기능 완료
3. 데이터베이스 CRUD 작업이 모두 정상 동작
4. API 응답 형식이 프론트엔드 기대값과 일치
5. 에러 처리가 적절하게 구현되어 사용자 친화적 메시지 제공

#### **📁 관련 파일**
- `backend/main.py` (생성됨): FastAPI 메인 애플리케이션
- `backend/routers/auth.py` (생성됨): 인증 관련 API 엔드포인트
- `backend/routers/policies.py` (생성됨): 약관 관리 API 엔드포인트
- `backend/routers/search.py` (생성됨): 검색 API 엔드포인트
- `backend/routers/workflow.py` (생성됨): 워크플로우 모니터링 API

#### **🎉 완료 요약**
FastAPI 백엔드 기본 구조가 성공적으로 구현되었습니다. 모든 주요 API 엔드포인트(/auth, /policies, /search, /workflow)가 생성되었고, 데이터베이스 연결 및 JWT 인증 시스템이 구현되었습니다. 프론트엔드 API 호환성을 위한 CORS 설정과 응답 형식도 맞춰졌습니다.

---

## 🤖 **Task 2: LangGraph Multi-Agent 아키텍처** ✅ **완료**

### **ID**: `5de82c67-559e-4c19-8874-1142fd613552`
### **상태**: 완료 (2025/9/22 17:53:44)

#### **📝 설명**
PDF 문서 처리를 위한 LangGraph 기반 multi-agent 시스템을 구현합니다. 텍스트, 표, 이미지 처리 에이전트와 이들을 조율하는 supervisor 에이전트로 구성된 워크플로우를 구축합니다.

#### **🎉 완료 요약**
LangGraph Multi-Agent 아키텍처가 성공적으로 구현되었습니다. SupervisorAgent를 중심으로 PDFProcessor, TextProcessor, TableProcessor, ImageProcessor, EmbeddingAgent로 구성된 워크플로우가 완성되었습니다.

---

## 📄 **Task 3: PDF 처리 파이프라인 서브 타스크**

### **Task 3.1: PDF 품질 분석 및 구조 파악** ✅ **완료**

#### **ID**: `a34b2447-d926-4d08-8bc7-d0fdf94ff925`
#### **상태**: 완료 (2025/9/23 14:04:23)

**설명**: PyMuPDF를 사용하여 PDF 문서의 기본 구조를 분석하고 텍스트 계층 존재 여부, 스캔 PDF 여부, 표 및 이미지 영역을 탐지합니다.

### **Task 3.2: 텍스트 추출 및 정제 강화** ✅ **완료**

#### **ID**: `b640b8b3-136b-457f-8f4d-6a356165dc3a`
#### **상태**: 완료 (2025/9/23 14:11:47)

**설명**: pdfplumber와 Tesseract OCR을 활용하여 다양한 형태의 PDF에서 텍스트를 추출하고, 정규식과 NLP 기법으로 텍스트를 정제합니다.

### **Task 3.3: 표 데이터 처리 및 구조화 고도화** ✅ **완료**

#### **ID**: `ab2182fb-0bf9-4a00-ba50-f270fe455953`
#### **상태**: 완료 (2025/9/23 14:38:23)

**설명**: camelot-py와 tabula-py를 조합하여 복잡한 표 구조를 정확히 추출하고, pandas DataFrame으로 구조화합니다.

### **Task 3.4: 이미지 처리 및 OCR 통합** ⏳ **대기**

#### **ID**: `d80f0186-2aa9-422b-ae97-99b9fef8b090`
#### **의존성**: Task 3.1

**설명**: PyMuPDF로 이미지를 추출하고 OpenCV로 전처리한 후 Tesseract OCR을 적용합니다. 이미지 내 텍스트와 메타데이터를 보존하여 문서 맥락을 유지합니다.

### **Task 3.5: Markdown 변환 및 구조 보존** ⏳ **대기**

#### **ID**: `4d351247-c665-4f98-98bf-6ca75dfd4878`
#### **의존성**: Task 3.2, 3.3, 3.4

**설명**: 추출된 텍스트, 표, 이미지 데이터를 구조화된 Markdown 형식으로 변환합니다. 원본 PDF의 레이아웃과 논리적 구조를 최대한 보존하여 가독성을 확보합니다.

### **Task 3.6: PDF 처리 파이프라인 통합 및 최적화** ⏳ **대기**

#### **ID**: `dc668152-05f4-4f23-b171-78578e50bce7`
#### **의존성**: Task 3.5

**설명**: 개별 구현된 기능들을 통합하여 완전한 PDF 처리 파이프라인을 구성합니다. 성능 최적화와 에러 처리, 진행률 모니터링을 포함한 안정적인 시스템을 완성합니다.

---

## 🔮 **Task 4: 임베딩 생성 및 pgvector 저장 시스템**

### **Task 4.1: 보안 등급별 임베딩 모델 관리 시스템** ⏳ **대기**

#### **ID**: `3f3d74b5-e1e6-4057-bfc6-4e50ea5f8cd2`
#### **의존성**: 없음

#### **📝 설명**
공개망(text-embedding-3-large), 조건부 폐쇄망(Azure OpenAI), 완전 폐쇄망(Qwen3 8B, multilingual-e5) 환경별 자동 임베딩 모델 선택 및 설정 시스템을 구현합니다. 모델별 차원 수와 테이블 매핑을 지원합니다.

#### **🔧 구현 가이드**
```python
# 기존 EmbeddingAgent 클래스를 확장하여 다중 모델 지원:

class MultiModelEmbeddingAgent(EmbeddingAgent):
    def __init__(self, security_level: str):
        model_config = {
            'public': 'text-embedding-3-large',
            'restricted': 'azure-text-embedding',
            'closed': 'qwen3-8b-embed'
        }
        super().__init__(model=model_config[security_level])
        self.security_level = security_level

    async def get_embedding_table(self) -> str:
        table_map = {
            'text-embedding-3-large': 'embeddings_text_embedding_3',
            'qwen3-8b-embed': 'embeddings_qwen'
        }
        return table_map[self.model]
```

#### **💡 노트**
기존 EmbeddingAgent의 model 파라미터를 확장하여 하위 호환성 유지. 환경별 설정은 .env 파일의 SECURITY_LEVEL 변수로 제어

#### **✓ 검증 기준**
1. 3가지 보안 등급별 모델 자동 선택 테스트
2. 모델별 차원 수 정확성 검증
3. 환경별 비용 계산 정확성
4. 기존 EmbeddingAgent 호환성 유지

#### **📁 관련 파일**
- `backend/agents/embedding_agent.py` (수정): 다중 모델 지원을 위한 클래스 확장
- `backend/models/database.py` (참조): 임베딩 테이블 모델 확인
- `backend/env.example` (수정): 보안 등급 설정 변수 추가

### **Task 4.2: 고급 청킹 및 토큰화 시스템** ⏳ **대기**

#### **ID**: `c4a6cb8a-bf73-4299-9f8b-848de09ec291`
#### **의존성**: 없음

#### **📝 설명**
Fixed-size, Content-aware, Semantic chunking 3가지 전략을 지원하는 고급 청킹 시스템을 구현합니다. 200토큰 기준, 10-20% overlap, 한국어 보험 용어 특화 처리를 포함합니다.

#### **🔧 구현 가이드**
```python
# 새로운 ChunkingService 클래스 구현:

class AdvancedChunkingService:
    def __init__(self, strategy: str = 'content_aware'):
        self.strategy = strategy
        self.chunk_size = 200  # tokens
        self.overlap = 0.15  # 15%
        self.tokenizer = tiktoken.get_encoding('cl100k_base')

    async def chunk_text(self, text: str, metadata: dict) -> List[ProcessedChunk]:
        if self.strategy == 'fixed_size':
            return self._fixed_size_chunking(text, metadata)
        elif self.strategy == 'content_aware':
            return self._content_aware_chunking(text, metadata)
        elif self.strategy == 'semantic':
            return self._semantic_chunking(text, metadata)
```

#### **💡 노트**
tiktoken 라이브러리로 정확한 토큰 계산. 보험 약관의 조항 구조(제1조, 제2조 등)를 고려한 논리적 분할

#### **✓ 검증 기준**
1. 3가지 청킹 전략별 성능 비교 테스트
2. 200토큰 ±5% 정확도
3. 조항 경계 보존 검증
4. 중복 텍스트 최소화 확인

#### **📁 관련 파일**
- `backend/services/chunking_service.py` (생성): 고급 청킹 서비스 새로 생성
- `backend/agents/text_processor.py` (수정): ChunkingService 통합
- `backend/utils/text_cleaner.py` (참조): 기존 텍스트 정제 로직 활용
- `backend/requirements.txt` (수정): tiktoken, spacy 의존성 추가

### **Task 4.3: 임베딩 품질 검증 및 배치 최적화** ⏳ **대기**

#### **ID**: `0b7777f7-a11c-4e40-84a1-e394e5568365`
#### **의존성**: Task 4.1

#### **📝 설명**
임베딩 생성 품질을 검증하고 배치 크기 동적 조정, API 호출 최적화, 비용 추정을 포함하는 고급 임베딩 처리 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# 기존 EmbeddingAgent에 품질 검증 기능 추가:

class QualityEmbeddingAgent(EmbeddingAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quality_threshold = 0.1  # 최소 벡터 norm
        self.adaptive_batch_size = True

    async def _validate_embedding_quality(self, embeddings: List[List[float]]) -> List[bool]:
        quality_scores = []
        for emb in embeddings:
            norm = np.linalg.norm(emb)
            is_valid = norm > self.quality_threshold and not np.isnan(emb).any()
            quality_scores.append(is_valid)
        return quality_scores

    async def _adjust_batch_size(self, success_rate: float):
        if success_rate < 0.9 and self.batch_size > 10:
            self.batch_size = max(10, self.batch_size // 2)
```

#### **💡 노트**
numpy를 활용한 벡터 품질 검증. OpenAI API 제한(RPM, TPM)을 고려한 동적 배치 크기 조정

#### **✓ 검증 기준**
1. 벡터 norm 임계값 검증
2. 배치 크기 동적 조정 테스트
3. API 호출 성공률 95% 이상
4. 비용 추정 정확도 ±10%

#### **📁 관련 파일**
- `backend/agents/embedding_agent.py` (수정): 품질 검증 및 배치 최적화 기능 추가
- `backend/services/quality_monitor.py` (생성): 임베딩 품질 모니터링 서비스

### **Task 4.4: pgvector 저장 최적화 및 인덱싱** ⏳ **대기**

#### **ID**: `c88bb957-4294-4521-87ca-4dd0bacd1521`
#### **의존성**: Task 4.3

#### **📝 설명**
HNSW 인덱스 구성, 차원별 테이블 관리, 벡터 검색 성능 최적화를 포함하는 고성능 벡터 데이터베이스 시스템을 완성합니다.

#### **🔧 구현 가이드**
```python
# 기존 VectorStoreService 최적화:

class OptimizedVectorStoreService(VectorStoreService):
    async def create_hnsw_index(self, db: AsyncSession, table_name: str):
        index_sql = f"""
            CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx 
            ON {table_name} USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """
        await db.execute(text(index_sql))

    async def bulk_insert_optimized(self, chunks: List[ProcessedChunk]):
        # COPY 명령어를 활용한 대량 삽입 최적화
        conn = await db.get_raw_connection()
        await conn.copy_from_query(...)
```

#### **💡 노트**
PostgreSQL HNSW 인덱스 파라미터 튜닝. 대량 데이터 삽입 시 COPY 명령어 활용으로 성능 개선

#### **✓ 검증 기준**
1. HNSW 인덱스 생성 확인
2. 1만개 벡터 기준 검색 시간 100ms 이하
3. 대량 삽입 성능 1000 벡터/초 이상
4. 메모리 사용량 모니터링

#### **📁 관련 파일**
- `backend/services/vector_store.py` (수정): HNSW 인덱스 및 성능 최적화
- `backend/models/database.py` (수정): 인덱스 생성 마이그레이션 추가
- `database/init.sql` (수정): HNSW 인덱스 초기 설정

---

## 🔍 **Task 5: RAG 기반 자연어 질의 검색 시스템**

### **Task 5.1: 자연어 질의 전처리 및 의도 분석** ⏳ **대기**

#### **ID**: `22e19074-40c7-44de-a616-29fea6a04c03`
#### **의존성**: Task 4.4

#### **📝 설명**
KoNLPy, spaCy를 활용한 한국어 질의 전처리, 보험 도메인 특화 용어 처리, 질의 의도 분석(정보 검색, 비교, 계산 등)을 수행하는 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# 새로운 QueryProcessor 클래스 구현:

class InsuranceQueryProcessor:
    def __init__(self):
        self.nlp = spacy.load('ko_core_news_sm')
        self.mecab = MeCab()
        self.insurance_terms = self._load_insurance_terms()

    async def preprocess_query(self, query: str) -> Dict[str, Any]:
        # 1. 텍스트 정규화
        normalized = self._normalize_text(query)
        
        # 2. 형태소 분석 및 보험 용어 보존
        tokens = self._tokenize_with_terms(normalized)
        
        # 3. 의도 분석
        intent = self._analyze_intent(tokens)
        
        return {
            'original': query,
            'normalized': normalized,
            'tokens': tokens,
            'intent': intent,
            'keywords': self._extract_keywords(tokens)
        }
```

#### **💡 노트**
보험 전문 용어 사전 구축 필요. '골절', '입원', '수술' 등 핵심 키워드의 동의어/유사어 처리

#### **✓ 검증 기준**
1. 한국어 질의 전처리 정확도 95%
2. 보험 용어 인식률 90% 이상
3. 의도 분류 정확도 85%
4. 처리 시간 질의당 100ms 이하

#### **📁 관련 파일**
- `backend/services/query_processor.py` (생성): 자연어 질의 전처리 서비스
- `backend/routers/search.py` (수정): QueryProcessor 통합
- `backend/data/insurance_terms.json` (생성): 보험 전문 용어 사전
- `backend/utils/text_cleaner.py` (참조): 기존 텍스트 정제 로직 재사용

### **Task 5.2: 벡터 유사도 검색 엔진 최적화** ⏳ **대기**

#### **ID**: `a0cd5edb-129e-47bf-97be-6d76931b7fae`
#### **의존성**: Task 5.1

#### **📝 설명**
코사인 유사도 기반 고성능 벡터 검색, 동적 임계값 조정, 하이브리드 검색(벡터+키워드), Top-N 추출 최적화를 구현합니다.

#### **🔧 구현 가이드**
```python
# 기존 VectorStoreService 검색 기능 확장:

class AdvancedSearchEngine(VectorStoreService):
    def __init__(self):
        super().__init__()
        self.similarity_threshold = 0.7
        self.hybrid_weight = {'vector': 0.7, 'keyword': 0.3}

    async def hybrid_search(self, query_data: Dict, limit: int = 10):
        # 1. 벡터 검색
        vector_results = await self.search_similar(
            query_data['embedding'], limit=limit*2
        )
        
        # 2. 키워드 검색
        keyword_results = await self._keyword_search(
            query_data['keywords'], limit=limit*2
        )
        
        # 3. 하이브리드 스코어링
        combined_results = self._combine_scores(vector_results, keyword_results)
        
        return combined_results[:limit]
```

#### **💡 노트**
PostgreSQL Full-Text Search와 pgvector 코사인 유사도를 결합한 하이브리드 검색. 검색 품질에 따른 가중치 자동 조정

#### **✓ 검증 기준**
1. 벡터 검색 응답시간 50ms 이하
2. 하이브리드 검색 정확도 향상 15%
3. 동적 임계값 조정 효과 검증
4. 관련성 스코어 신뢰도 90%

#### **📁 관련 파일**
- `backend/services/vector_store.py` (수정): 하이브리드 검색 엔진 확장
- `backend/services/search_engine.py` (생성): 고급 검색 엔진 서비스
- `backend/models/database.py` (수정): Full-Text Search 인덱스 추가

### **Task 5.3: 검색 결과 후처리 및 재랭킹** ⏳ **대기**

#### **ID**: `90a421fb-ab16-45fb-94e5-586ae70a4f14`
#### **의존성**: Task 5.2

#### **📝 설명**
Cross-encoder 재랭킹, 중복 제거, 컨텍스트 병합, 결과 다양성 확보를 통한 고품질 검색 결과 후처리 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# 검색 후처리 파이프라인 구현:

class SearchResultProcessor:
    def __init__(self):
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
        self.diversity_threshold = 0.8

    async def process_results(self, query: str, raw_results: List[Dict]) -> List[Dict]:
        # 1. Cross-encoder 재랭킹
        reranked = await self._cross_encoder_rerank(query, raw_results)
        
        # 2. 중복 제거
        deduplicated = self._remove_duplicates(reranked)
        
        # 3. 컨텍스트 병합
        merged = self._merge_context(deduplicated)
        
        # 4. 다양성 확보
        diversified = self._ensure_diversity(merged)
        
        return diversified

    def _merge_context(self, results: List[Dict]) -> List[Dict]:
        # 연속된 청크를 병합하여 더 큰 컨텍스트 제공
        merged_results = []
        for result in results:
            adjacent_chunks = self._find_adjacent_chunks(result)
            if adjacent_chunks:
                result['extended_context'] = self._combine_chunks(adjacent_chunks)
```

#### **💡 노트**
Cross-encoder 모델은 한국어 지원 모델로 교체 고려. 컨텍스트 병합 시 원본 페이지 번호와 위치 정보 보존

#### **✓ 검증 기준**
1. Cross-encoder 재랭킹 정확도 향상 20%
2. 중복 제거율 95% 이상
3. 컨텍스트 병합 관련성 유지
4. 검색 결과 다양성 지수 0.8 이상

#### **📁 관련 파일**
- `backend/services/result_processor.py` (생성): 검색 결과 후처리 서비스
- `backend/routers/search.py` (수정): 결과 후처리 파이프라인 통합
- `backend/requirements.txt` (수정): sentence-transformers, cross-encoder 의존성 추가

### **Task 5.4: LLM 기반 답변 생성 파이프라인** ⏳ **대기**

#### **ID**: `f6b40c5d-a878-49f8-b8ae-2dd1aac62c7e`
#### **의존성**: Task 5.3

#### **📝 설명**
GPT-4o, Claude와 통합된 RAG 답변 생성, 보험 도메인 특화 프롬프트, 답변 품질 검증, 출처 인용을 포함하는 완전한 답변 생성 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# LLM 답변 생성 서비스 구현:

class RAGAnswerGenerator:
    def __init__(self, model: str = 'gpt-4o'):
        self.model = model
        self.client = AsyncOpenAI()
        self.system_prompt = self._load_insurance_prompt()

    async def generate_answer(self, query: str, search_results: List[Dict]) -> Dict[str, Any]:
        # 1. 컨텍스트 구성
        context = self._build_context(search_results)
        
        # 2. 프롬프트 구성
        prompt = self._build_rag_prompt(query, context)
        
        # 3. LLM 답변 생성
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.1
        )
        
        # 4. 답변 품질 검증
        answer = response.choices[0].message.content
        quality_score = await self._validate_answer_quality(answer, query)
        
        return {
            'answer': answer,
            'sources': self._extract_sources(search_results),
            'quality_score': quality_score,
            'confidence': self._calculate_confidence(search_results)
        }
```

#### **💡 노트**
보험 도메인 전문성을 위한 Few-shot 예제 포함. 답변에 반드시 관련 약관 조항과 페이지 번호 인용

#### **✓ 검증 기준**
1. 답변 관련성 점수 90% 이상
2. 출처 인용 정확도 95%
3. 답변 생성 시간 3초 이하
4. 보험 용어 사용 적절성 검증

#### **📁 관련 파일**
- `backend/services/answer_generator.py` (생성): LLM 기반 답변 생성 서비스
- `backend/routers/search.py` (수정): 답변 생성 파이프라인 통합
- `backend/prompts/insurance_rag_prompt.txt` (생성): 보험 도메인 특화 RAG 프롬프트
- `backend/agents/embedding_agent.py` (참조): OpenAI 클라이언트 설정 참고

---

## 📈 **Task 6: LangFuse 워크플로우 모니터링 시스템**

### **Task 6.1: LangFuse SDK 통합 및 기본 설정** ⏳ **대기**

#### **ID**: `9230f7f3-04dd-4d80-9e73-608681acdeb5`
#### **의존성**: 없음

#### **📝 설명**
LangFuse 모니터링 시스템과의 연동을 위한 SDK 설치, 인증 설정, 기본 로깅 구성을 구현합니다.

#### **🔧 구현 가이드**
```python
# LangFuse 클라이언트 설정:

from langfuse import Langfuse
from langfuse.decorators import observe

class LangFuseMonitor:
    def __init__(self):
        self.langfuse = Langfuse(
            secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
            host=os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
        )
        
    @observe()
    async def trace_agent_execution(self, agent_name: str, input_data: dict):
        with self.langfuse.trace(name=f'{agent_name}_execution') as trace:
            trace.update(
                input=input_data,
                metadata={'agent': agent_name, 'timestamp': datetime.now()}
            )
            return trace
```

#### **💡 노트**
LangFuse 클라우드 또는 Self-hosted 옵션 지원. 개발/운영 환경별 설정 분리

#### **✓ 검증 기준**
1. LangFuse 연결 성공 확인
2. 기본 트레이스 생성 테스트
3. 환경별 설정 동작 확인
4. 에러 처리 검증

#### **📁 관련 파일**
- `backend/services/langfuse_monitor.py` (생성): LangFuse 모니터링 서비스
- `backend/env.example` (수정): LangFuse 환경 변수 추가
- `backend/requirements.txt` (수정): langfuse 의존성 추가

### **Task 6.2: Multi-Agent 워크플로우 추적 구현** ⏳ **대기**

#### **ID**: `11b095ab-6eea-4d4f-b443-0995a62a226a`
#### **의존성**: Task 6.1

#### **📝 설명**
LangGraph 기반 Multi-Agent 워크플로우의 실행 상태, 에이전트 간 데이터 흐름, 처리 시간을 실시간으로 추적하는 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# 기존 SupervisorAgent에 LangFuse 추적 통합:

class TrackedSupervisorAgent(SupervisorAgent):
    def __init__(self):
        super().__init__()
        self.monitor = LangFuseMonitor()
        
    @observe()
    async def execute_workflow(self, state: DocumentProcessingState):
        with self.monitor.trace_workflow('pdf_processing_workflow') as workflow_trace:
            # 각 에이전트 실행 추적
            for agent_name, agent in self.agents.items():
                with workflow_trace.span(name=f'{agent_name}_execution') as span:
                    start_time = time.time()
                    result = await agent.process(state)
                    
                    span.update(
                        input=self._serialize_state(state),
                        output=self._serialize_state(result),
                        metadata={
                            'agent': agent_name,
                            'duration': time.time() - start_time,
                            'status': result.get('status')
                        }
                    )
            return result
```

#### **💡 노트**
State 객체의 민감한 정보는 마스킹 처리. 대용량 파일 경로만 기록하고 내용은 제외

#### **✓ 검증 기준**
1. 전체 워크플로우 트레이스 생성
2. 에이전트별 실행 시간 측정
3. 오류 발생 시 상세 로깅
4. 데이터 플로우 시각화 확인

#### **📁 관련 파일**
- `backend/agents/supervisor.py` (수정): LangFuse 추적 기능 통합
- `backend/agents/base.py` (수정): BaseAgent에 추적 데코레이터 추가
- `backend/services/langfuse_monitor.py` (수정): 워크플로우 추적 메서드 추가

### **Task 6.3: 성능 메트릭 수집 및 분석 대시보드** ⏳ **대기**

#### **ID**: `29b17e2a-b21d-4b54-807f-a7b283b9913f`
#### **의존성**: Task 6.2

#### **📝 설명**
에이전트별 처리 성능, 메모리 사용량, 처리 성공률, 평균 응답 시간을 수집하고 분석하는 메트릭 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# 성능 메트릭 수집기 구현:

class PerformanceMetricsCollector:
    def __init__(self):
        self.langfuse = LangFuseMonitor()
        self.metrics_cache = {}
        
    async def collect_agent_metrics(self, agent_name: str, execution_data: dict):
        metrics = {
            'agent_name': agent_name,
            'execution_time': execution_data['duration'],
            'memory_usage': psutil.Process().memory_info().rss,
            'success_rate': execution_data['status'] == 'completed',
            'error_count': 1 if execution_data['status'] == 'failed' else 0,
            'throughput': execution_data.get('processed_items', 0) / execution_data['duration']
        }
        
        await self.langfuse.log_metrics(metrics)
        self._update_cache(agent_name, metrics)
        
    def generate_performance_report(self) -> dict:
        return {
            'summary': self._calculate_summary_stats(),
            'agent_performance': self._get_agent_performance(),
            'trends': self._analyze_trends(),
            'bottlenecks': self._identify_bottlenecks()
        }
```

#### **💡 노트**
psutil로 시스템 리소스 모니터링. 24시간 rolling window로 성능 트렌드 분석

#### **✓ 검증 기준**
1. 실시간 메트릭 수집 확인
2. 성능 보고서 생성 테스트
3. 대시보드 API 응답 시간 100ms 이하
4. 메트릭 정확도 검증

#### **📁 관련 파일**
- `backend/services/metrics_collector.py` (생성): 성능 메트릭 수집 서비스
- `backend/routers/workflow.py` (수정): 메트릭 조회 API 추가
- `frontend/src/components/WorkflowMonitor.tsx` (수정): 성능 대시보드 UI 확장
- `backend/requirements.txt` (수정): psutil 의존성 추가

### **Task 6.4: WorkflowMonitor 컴포넌트 연동 및 시각화** ⏳ **대기**

#### **ID**: `f0bc3f7f-0116-4e97-a04d-71968dfb9013`
#### **의존성**: Task 6.3

#### **📝 설명**
기존 React WorkflowMonitor 컴포넌트와 LangFuse 데이터를 연동하여 실시간 워크플로우 모니터링 UI를 완성합니다.

#### **🔧 구현 가이드**
```typescript
# WorkflowMonitor 컴포넌트 확장:

interface WorkflowMetrics {
  agentPerformance: AgentMetric[];
  workflowStatus: WorkflowStatus;
  realTimeMetrics: RealTimeMetric[];
}

const WorkflowMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<WorkflowMetrics>();
  const [selectedAgent, setSelectedAgent] = useState<string>();
  
  useEffect(() => {
    const fetchMetrics = async () => {
      const response = await api.get('/workflow/metrics');
      setMetrics(response.data);
    };
    
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // 5초마다 업데이트
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="workflow-monitor">
      <AgentPerformanceChart data={metrics?.agentPerformance} />
      <WorkflowFlowDiagram workflow={metrics?.workflowStatus} />
      <RealTimeMetrics metrics={metrics?.realTimeMetrics} />
    </div>
  );
};
```

#### **💡 노트**
기존 WorkflowMonitor.tsx의 구조를 유지하면서 LangFuse 데이터 추가. WebSocket 연결 고려

#### **✓ 검증 기준**
1. 실시간 워크플로우 상태 표시
2. 에이전트별 성능 차트 렌더링
3. 5초 간격 자동 업데이트
4. 반응형 UI 동작 확인

#### **📁 관련 파일**
- `frontend/src/components/WorkflowMonitor.tsx` (수정): LangFuse 데이터 연동 및 시각화 확장
- `backend/routers/workflow.py` (수정): 실시간 메트릭 API 엔드포인트 추가
- `frontend/src/services/api.ts` (수정): 워크플로우 메트릭 API 호출 추가
- `frontend/package.json` (수정): chart.js, recharts 의존성 추가

---

## 🤖 **Task 7: MCP 연동 및 자동 Tool 호출 시스템**

### **Task 7.1: MCP 프로토콜 클라이언트 구현** ⏳ **대기**

#### **ID**: `5880d47d-967b-4d95-89ed-62170f76e9e2`
#### **의존성**: Task 6.4

#### **📝 설명**
Model Context Protocol 표준을 준수하는 클라이언트를 구현하여 자동 Tool 호출 기반을 마련합니다.

#### **🔧 구현 가이드**
```python
# MCP 클라이언트 기본 구현:

class MCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session = aiohttp.ClientSession()
        self.tools = {}
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        response = await self.session.post(
            f'{self.server_url}/mcp/tools/list',
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
        )
        result = await response.json()
        self.tools = {tool['name']: tool for tool in result['result']['tools']}
        return result['result']['tools']
        
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self.tools:
            raise ValueError(f'Tool {name} not found')
            
        response = await self.session.post(
            f'{self.server_url}/mcp/tools/call',
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': name, 'arguments': arguments}
            }
        )
        return await response.json()
```

#### **💡 노트**
MCP 표준 사양 준수. Tool 등록, 호출, 결과 처리의 전체 라이프사이클 지원

#### **✓ 검증 기준**
1. MCP 서버 연결 성공
2. Tool 목록 조회 확인
3. Tool 호출 및 결과 수신
4. 에러 처리 검증

#### **📁 관련 파일**
- `backend/services/mcp_client.py` (생성): MCP 프로토콜 클라이언트
- `backend/requirements.txt` (수정): aiohttp, jsonrpc 의존성 추가
- `backend/env.example` (수정): MCP 서버 URL 설정 추가

### **Task 7.2: 자연어 의도 분석 및 Tool 라우팅 시스템** ⏳ **대기**

#### **ID**: `c49da8a8-8d4d-4945-892d-a4aaf4a17106`
#### **의존성**: Task 7.1

#### **📝 설명**
사용자의 자연어 입력을 분석하여 적절한 Tool을 자동으로 선택하고 호출하는 지능형 라우팅 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# 의도 분석 및 Tool 라우팅 엔진:

class IntentAnalyzer:
    def __init__(self):
        self.intent_patterns = {
            'search_policy': [r'.*찾.*', r'.*검색.*', r'.*약관.*'],
            'upload_document': [r'.*업로드.*', r'.*올리.*', r'.*추가.*'],
            'compare_policies': [r'.*비교.*', r'.*차이.*'],
            'calculate_premium': [r'.*보험료.*', r'.*계산.*']
        }
        self.tool_mapping = {
            'search_policy': 'search_policies',
            'upload_document': 'upload_policy_document',
            'compare_policies': 'compare_policy_terms',
            'calculate_premium': 'calculate_insurance_premium'
        }
        
    async def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        # 1. 패턴 매칭
        matched_intent = self._pattern_matching(user_input)
        
        # 2. LLM 의도 분석
        llm_intent = await self._llm_intent_analysis(user_input)
        
        # 3. 신뢰도 기반 최종 의도 결정
        final_intent = self._resolve_intent(matched_intent, llm_intent)
        
        return {
            'intent': final_intent,
            'confidence': self._calculate_confidence(matched_intent, llm_intent),
            'suggested_tool': self.tool_mapping.get(final_intent),
            'extracted_parameters': self._extract_parameters(user_input, final_intent)
        }
```

#### **💡 노트**
보험 도메인 특화 의도 패턴 구축. 신뢰도가 낮을 경우 사용자 확인 요청

#### **✓ 검증 기준**
1. 의도 분석 정확도 85% 이상
2. Tool 라우팅 성공률 90%
3. 파라미터 추출 정확도 80%
4. 응답 시간 500ms 이하

#### **📁 관련 파일**
- `backend/services/intent_analyzer.py` (생성): 자연어 의도 분석 서비스
- `backend/services/tool_router.py` (생성): Tool 라우팅 엔진
- `backend/data/intent_patterns.json` (생성): 의도 분석 패턴 정의
- `backend/routers/mcp.py` (생성): MCP 기반 자동 Tool 호출 API

### **Task 7.3: ChatInterface 통합 자동화** ⏳ **대기**

#### **ID**: `90aadc0d-de73-4561-a770-3231da12498b`
#### **의존성**: Task 7.2

#### **📝 설명**
기존 ChatInterface.tsx 컴포넌트와 MCP 시스템을 연동하여 대화형 AI 어시스턴트 기능을 완성합니다.

#### **🔧 구현 가이드**
```typescript
# ChatInterface에 MCP 통합:

interface MCPResponse {
  intent: string;
  confidence: number;
  toolCall?: ToolCall;
  result?: any;
  requiresConfirmation?: boolean;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const handleUserMessage = async (input: string) => {
    setIsProcessing(true);
    
    try {
      // 1. 의도 분석
      const intentResponse = await api.post('/mcp/analyze-intent', { input });
      
      // 2. 신뢰도 확인
      if (intentResponse.data.confidence < 0.8) {
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: '의도를 정확히 파악하지 못했습니다. 다시 말씀해 주세요.',
          suggestions: intentResponse.data.suggestions
        }]);
        return;
      }
      
      // 3. Tool 자동 호출
      const toolResponse = await api.post('/mcp/execute-tool', {
        tool: intentResponse.data.suggested_tool,
        parameters: intentResponse.data.extracted_parameters
      });
      
      // 4. 결과 표시
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: toolResponse.data.result,
        metadata: { toolUsed: intentResponse.data.suggested_tool }
      }]);
      
    } finally {
      setIsProcessing(false);
    }
  };
}
```

#### **💡 노트**
기존 ChatInterface 디자인 유지하면서 MCP 기능 추가. Tool 호출 과정을 사용자에게 투명하게 표시

#### **✓ 검증 기준**
1. 자연어 입력 → Tool 자동 호출 플로우
2. Tool 실행 과정 시각화
3. 에러 상황 적절한 처리
4. 기존 ChatInterface 기능 호환성

#### **📁 관련 파일**
- `frontend/src/components/ChatInterface.tsx` (수정): MCP 통합 대화형 AI 인터페이스
- `backend/routers/mcp.py` (수정): ChatInterface용 MCP API 엔드포인트
- `frontend/src/services/api.ts` (수정): MCP API 호출 메서드 추가
- `frontend/src/types/mcp.ts` (생성): MCP 관련 TypeScript 타입 정의

---

## 🐳 **Task 8: Docker 컨테이너 환경 구성**

### **Task 8.1: Backend Docker 환경 구성** ⏳ **대기**

#### **ID**: `862e2b02-75e0-4060-8c5f-a6ca68c41b19`
#### **의존성**: 없음

#### **📝 설명**
FastAPI 백엔드를 위한 최적화된 Docker 환경을 구성하고 개발/운영 환경별 설정을 분리합니다.

#### **🔧 구현 가이드**
```dockerfile
# Backend Dockerfile 작성:

# Multi-stage build
FROM python:3.11-slim as base

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc g++ \
    libpq-dev \
    tesseract-ocr tesseract-ocr-kor \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 개발 환경
FROM base as development
ENV ENVIRONMENT=development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 운영 환경
FROM base as production
ENV ENVIRONMENT=production
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### **💡 노트**
OCR 및 PDF 처리를 위한 시스템 패키지 포함. Multi-stage build로 이미지 크기 최적화

#### **✓ 검증 기준**
1. Docker 이미지 빌드 성공
2. 컨테이너 정상 시작 확인
3. API 엔드포인트 접근 가능
4. 파일 업로드 기능 동작

#### **📁 관련 파일**
- `backend/Dockerfile` (생성): Backend Docker 설정
- `backend/.dockerignore` (생성): Docker 빌드 제외 파일
- `backend/docker-entrypoint.sh` (생성): 컨테이너 시작 스크립트
- `backend/requirements-docker.txt` (생성): Docker용 최적화된 의존성

### **Task 8.2: Multi-container docker-compose 통합** ⏳ **대기**

#### **ID**: `35a53c2c-9792-4c4e-9198-5fd68a8e28f4`
#### **의존성**: Task 8.1

#### **📝 설명**
Backend, Frontend, Database를 통합하는 docker-compose 환경을 구성하고 컨테이너 간 네트워킹을 설정합니다.

#### **🔧 구현 가이드**
```yaml
# 통합 docker-compose.yml 작성:

version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: ispl_insurance
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: 
      context: ./backend
      target: development
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@postgres:5432/ispl_insurance
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

#### **💡 노트**
Health check를 통한 서비스 간 의존성 관리. 볼륨 마운트로 개발 시 코드 변경 실시간 반영

#### **✓ 검증 기준**
1. 모든 서비스 정상 시작
2. 서비스 간 통신 확인
3. 데이터베이스 초기화 성공
4. 볼륨 마운트 동작 확인

#### **📁 관련 파일**
- `docker-compose.yml` (생성): 개발 환경 통합 Docker Compose
- `docker-compose.prod.yml` (생성): 운영 환경 Docker Compose override
- `database/Dockerfile` (참조): 기존 데이터베이스 Dockerfile 활용
- `frontend/Dockerfile` (참조): 기존 프론트엔드 Dockerfile 활용

### **Task 8.3: 개발/운영 환경 분리 설정** ⏳ **대기**

#### **ID**: `b410e677-dd53-41d8-81dc-6bc529a7571d`
#### **의존성**: Task 8.2

#### **📝 설명**
환경별 설정 파일, 시크릿 관리, 로깅 레벨, 성능 최적화를 포함하는 환경 분리 시스템을 구현합니다.

#### **🔧 구현 가이드**
```python
# 환경별 설정 관리:

# config/settings.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = True
    database_url: str
    openai_api_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    
    # 환경별 설정
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
        
    @property
    def log_level(self) -> str:
        return "DEBUG" if self.is_development else "INFO"
        
    @property
    def cors_origins(self) -> list:
        if self.is_development:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return ["https://your-domain.com"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

#### **💡 노트**
민감한 정보는 Docker Secrets 또는 환경 변수로 관리. 개발 환경에서는 .env 파일 사용

#### **✓ 검증 기준**
1. 환경별 설정 자동 로드
2. 시크릿 정보 보안 처리
3. 로깅 레벨 환경별 적용
4. CORS 설정 환경별 분리

#### **📁 관련 파일**
- `backend/config/settings.py` (생성): 환경별 설정 관리
- `backend/config/logging.py` (생성): 환경별 로깅 설정
- `.env.development` (생성): 개발 환경 설정
- `.env.production` (생성): 운영 환경 설정 템플릿
- `backend/main.py` (수정): 환경별 설정 적용

---

## 📊 **Dependencies 및 Critical Path**

### **🔗 의존성 관계**
```
Task 1 (완료) → Task 2 (완료) → Task 3.1-3.3 (완료)
                ↓
Task 4.1 → Task 4.2 → Task 4.3 → Task 4.4
                                    ↓
                        Task 5.1 → Task 5.2 → Task 5.3 → Task 5.4
                                                          ↓
Task 6.1 → Task 6.2 → Task 6.3 → Task 6.4 → Task 7.1 → Task 7.2 → Task 7.3

Task 8.1 → Task 8.2 → Task 8.3 (독립 실행 가능)

Task 3.4 → Task 3.5 → Task 3.6 (독립 실행 가능)
```

### **🚀 권장 진행 순서**

#### **Phase 1: Core System (높은 우선순위)**
1. **Task 4.1**: 보안 등급별 임베딩 모델 관리 ← **다음 시작 권장**
2. **Task 4.2**: 고급 청킹 및 토큰화 시스템  
3. **Task 4.3**: 임베딩 품질 검증 및 배치 최적화
4. **Task 4.4**: pgvector 저장 최적화 및 인덱싱

#### **Phase 2: Search System (중간 우선순위)**
5. **Task 5.1**: 자연어 질의 전처리 및 의도 분석
6. **Task 5.2**: 벡터 유사도 검색 엔진 최적화  
7. **Task 5.3**: 검색 결과 후처리 및 재랭킹
8. **Task 5.4**: LLM 기반 답변 생성 파이프라인

#### **Phase 3: Monitoring & Advanced Features (낮은 우선순위)**
9. **Task 6.1-6.4**: LangFuse 모니터링 시스템
10. **Task 7.1-7.3**: MCP 연동 및 자동 Tool 호출
11. **Task 8.1-8.3**: Docker 컨테이너 환경 구성
12. **Task 3.4-3.6**: PDF 처리 파이프라인 완성

---

## 🎯 **결론**

**ISPL Insurance Policy AI 프로젝트**의 서브 타스크 분할이 완료되었습니다:

- **총 32개 타스크** (완료 5개 + 대기 27개)
- **체계적인 의존성 관리** (선형적 진행 가능)
- **1-2일 완료 단위** (실용적 개발 범위)
- **기존 코드 재사용 극대화** (효율적 개발)

다음 단계로 **Task 4.1 (보안 등급별 임베딩 모델 관리 시스템)**부터 시작하여 체계적으로 진행할 수 있습니다.

---

**문서 생성일**: 2025년 9월 23일  
**마지막 업데이트**: 2025년 9월 23일 19:35  
**버전**: 1.0

