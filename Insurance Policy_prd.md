# 보험약관 기반 Agentic AI PRD (Product Requirements Document)

## 1. 서비스 목적 및 개요
- 생성형 AI를 활용하여 약관을 전처리, 요약, 임베딩 후 벡터DB에 저장
- 사용자의 자연어 질의에 대해 관련 약관을 검색 및 답변 제공
- 파일 업로드 지원
- 약관의 통합 관리 및 활용 편의성 극대화
    - 약관 질의 즉시 응답(예: "골절 시 보장 여부?")
    - 타 보함사 약관 비교, 설계사 교육, 계약 특약 확인 지원


## 2. 주요 기능 요건

### 2.1 약관 업로드
- 지원 파일: PDF
- 파일 업로드 → 전처리 → Markdown 변환 → 요약 → 임베딩 → 벡터DB 저장
- 원본 파일은 로컬에 저장, md 원문/요약본은 벡터DB에 저장
- 요약 결과를 업로드 시점에 사용자에게 제공

#### 2.1.1 전처리

##### 2.1.1.1 PDF 품질 및 구조 확인
- PDF 내 텍스트, 표, 이미지 존재 여부 및 위치 파악
- 스캔 PDF 여부 확인, OCR 필요성 평가
- 도구: PyMuPDF (fitz), pdfminer.six

##### 2.1.1.2 텍스트 추출
- 텍스트 계층 존재 시: pdfplumber, PyPDF2 사용해 추출
- 텍스트 계층 없는 스캔 이미지 부분: Tesseract OCR 또는 Google Vision OCR 적용
- 표 영역: pdfplumber, camelot-py, tabula-py 등으로 셀 단위 구조 추출

##### 2.1.1.3 이미지 처리
- 도표, 아이콘 등 중요 이미지 분리 저장
- 이미지 내 텍스트 OCR 추출 보조
- 이미지 위치, 페이지 번호 등 메타데이터 기록
- 도구: PyMuPDF 이미지 추출, OpenCV 이미지 전처리, Tesseract OCR

##### 2.1.1.4 텍스트 정제
- 특수문자, 공백, 줄바꿈 통일 및 불필요 문구 필터링
- 페이지 머리말·바닥글, 광고 문구, 반복 내용 제거
- 약관 내 고유 번호와 조항 표기 통일
- 도구: Python re(정규식), pandas

##### 2.1.1.5 표 데이터 전처리
- 표 내 셀 텍스트 추출 후 리스트, 표 형태로 구조화
- 표와 본문 문장 간 매핑 및 연계 관계 분석
- 도구: pandas, camelot-py, tabula-py

##### 2.1.1.6 문서 구조화 및 청크 분할
- 챕터, 조항, 특약 단위 논리적 분할
- 표 및 텍스트 청크 간 관계 고려 청크 분할
- 토큰 수 기준 크기 조절 및 문맥 훼손 최소화
- 도구: spaCy (한국어 모델), KoNLPy, 커스텀 청크 분할 스크립트

##### 2.1.1.7 토크나이징 및 형태소 분석
- 한국어 토큰화 및 불용어 처리
- 조사 처리 시 보험 용어 보존
- 도구: KoNLPy, Mecab, spaCy 한글 모델

##### 2.1.1.8 개체명 인식 및 태깅 (선택 사항)
- 보험금, 계약자, 보장 내용 등 핵심 엔티티 태깅
- 도구: KoBERT NER, spaCy NER, Transformers 기반 커스텀 NER

#### 2.1.2 Markdown 변환
- 텍스트, 표, 이미지 포함 문서 전체를 Markdown 문법에 맞게 변환
- 표는 Markdown 표 형식(|와 - 사용)으로 처리
- 이미지 Markdown 삽입 구문(` 포함
- 챕터 및 조항 제목은 Markdown 헤더(#, ##)로 표시하여 문서 구조 확화
- 이미지 위치, 페이지 번호 등 메타데이터를 별도 주석 또는 섹션에 추가
- Markdown 파일(.md)로 저장, 별도 폴더에 이미지 파일 보관
- 도구: Marker, Aspose.Words (자동 변환), Python markdown2 라이브러리 (커스텀 변환)

#### 2.1.3 요약
- OpenAI GPT-4o 또는 Anthropic Claude API + LangChain 워크플로우 조합

#### 2.1.4 임베딩
- chunking (**Fixed-size Chunking**, Content-aware Chunking, Semantic Chunking)
- chunk size : 200 토큰
- overlap 10~20%
- 임베딩 모델 (nomic-ai/nomic-embed-text-v1, all-MiniLM-L6-v2)
- 차원수 : 500~1000 차원

#### 2.1.5 벡터DB 저장
- DB : **FAISS** (Facebook AI Similarity Search), ChromaDB, Weaviate
- 인덱싱 : Flat (Brute Force), HNSW (Hierarchical Navigable Small World)
- 유사도 측정 방식 : Cosine Similarity
- 차원수 : 500~1000 차원

### 2.2 약관 검색
- 통합검색 및 개별 약관 지정 검색
- 유사도 순으로 결과 반환
- 검색 결과 기반 답변 생성

#### 2.2.1 자연어 질의 입력
- 사용자가 질문을 입력하면 프론트엔드/챗봇 시스템에서 질의 수집.

#### 2.2.2 질의 전처리
- 불필요 문장·정제, 토크나이즈, 언어·문맥 태깅. (spaCy, KoNLPy)

#### 2.2.3 질의 임베딩(Embedding)
- 동일 임베딩 모델(OpenAI, ko-sbert, Sentence-BERT 등)로 질의 벡터화.

#### 2.2.4 벡터 DB 유사도 검색
- 벡터DB(pgvector, Pinecone, Qdrant 등)에서 쿼리 벡터와 유사도가 높은 약관 벡터 청크 검색.

#### 2.2.5 검색 결과 후처리 및 랭킹
- Top-N 청크/문단 추출, Cross-encoder 재랭킹(옵션), FAQ/챕터/원문 연결.

#### 2.2.6 답변 생성
- LLM(OpenAI GPT-4, koGPT, RAG 파이프라인)로 결과 요약 및 자연어 답변 생성.

#### 2.2.7 응답 반환
- 최종 FAQ/근거문서/핵심설명 등 사용자에게 제공.

### 2.3 약관 관리
- 저장된 약관의 제목/요약본 목록 제공
- 원본 파일 다운로드 및 삭제 기능
- PDF 파일 조회 기능
- Markdown 파일 조회 기능

### 2.4 보안조건별 모델 추천 및 자동 세팅
<!-- - 완전 폐쇄망: Qwen3 8B embedding, intfloat/multilingual-e5-large-instruct, dragonkue/snowflake-arctic-embed-l-v2.0
- 조건부 폐쇄망: Azure OpenAI(GPT-4o, GPT-4.1, text-embedding-3-large) -->
- 공개망: text-embedding-3-large
- 환경별 임베딩 차원에 맞는 테이블 설계 필요

## 3. 비기능 요건
- 웹 기반 UI(React, Open Web UI 스타일)
- 파일 및 데이터 보안
- 확장성 있는 DB 설계
- 빠른 검색 및 응답 속도

## 4. 시스템 아키텍처 및 MCP 연동
- 챗 UI 기반 메인 화면(GPT 스타일)
- 사용자의 자연어 입력 → 의도 파악 → 자동 Tool 호출(MCP 기반) → 결과 응답
- 좌측 탭(사이드바)에서 수동 기능 사용 가능
- React(프론트엔드) + FastAPI/Flask(백엔드) + PostgreSQL(pgvector) + MCP 연동 구조
- 서비스구조 : 
  - frontend : React (docker container) 
  - backend : FastAPI (docker container)
  - database : postgreSQL + pgvector (docker container - image: pgvector/pgvector:pg17)
- 로컬테스트 환경 및 docker 환경
- multi agent 구성
  - 텍스트 처리
  - 표 처리
  - 이미지 처리
  - 약관 관리를 위한 처리 중 (텍스트,표,이미지) 이외에도 별도 구성 가능한 것이 있다면 agent로 구성 
  - 약관 검색 (AI 채팅 메뉴가 약관 검색 기능임) 
  - 이미지 분석
- multi agent 구현을 위한 langgraph 활용
- langfuse 를 활용한 agent graph view 와 같은 내용이 워크플로우 메뉴에서 조회

## 5. 데이터베이스 테이블 설계(예시)

```sql
-- 사용자 테이블
CREATE TABLE USER (
    USER_ID             SERIAL PRIMARY KEY,                   -- 사용자 고유 ID
    EMAIL               VARCHAR(255) UNIQUE NOT NULL,         -- 사용자 이메일
    PASSWORD_HASH       VARCHAR(255) NOT NULL,                -- 암호화된 비밀번호
    ROLE                VARCHAR(20) NOT NULL CHECK (ROLE IN ('ADMIN', 'USER')), -- 사용자 권한
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 생성일시
);

-- 약관 테이블
CREATE TABLE POLICY (
    POLICY_ID           SERIAL PRIMARY KEY,                   -- 약관 ID
    COMPANY             VARCHAR(100),                         -- 보험사
    CATEGORY            VARCHAR(100),                         -- 보험분류(건강보험, 자동차보험)
    PRODUCT_TYPE        VARCHAR(100),                         -- 상품 유형(정액형, 실비형)
    PRODUCT_NAME        VARCHAR(255) NOT NULL,                -- 상품명
    SALE_START_DT       VARCHAR(8),                           -- 판매시작일자
    SALE_END_DT         VARCHAR(8),                           -- 판매종료일자
    SALE_STAT           VARCHAR(10),                          -- 판매상태 (판매중, 판매종료)
    SUMMARY             TEXT,                                 -- 상품 요약
    ORIGINAL_PATH       VARCHAR(500),                         -- 원본 파일 경로
    MD_PATH             VARCHAR(500),                         -- Markdown 파일 경로
    PDF_PATH            VARCHAR(500),                         -- PDF 파일 경로
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 생성일시
    SECURITY_LEVEL      VARCHAR(20)                           -- 보안 등급
);

-- text-embedding-3 임베딩 테이블 (3072차원)
CREATE TABLE EMBEDDINGS_TEXT_EMBEDDING_3 (
    ID                  SERIAL PRIMARY KEY,                   -- 임베딩 고유 ID
    POLICY_ID           INTEGER NOT NULL REFERENCES POLICY(POLICY_ID), -- 약관 ID
    EMBEDDING           VECTOR(3072) NOT NULL,                -- 3072차원 임베딩 벡터
    MODEL               VARCHAR(100) NOT NULL,                -- 사용된 모델명
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 생성일시
);

-- Qwen 임베딩 테이블 (4096차원)
CREATE TABLE EMBEDDINGS_QWEN (
    ID                  SERIAL PRIMARY KEY,                   -- 임베딩 고유 ID
    POLICY_ID           INTEGER NOT NULL REFERENCES POLICY(POLICY_ID), -- 약관 ID
    EMBEDDING           VECTOR(4096) NOT NULL,                -- 4096차원 임베딩 벡터
    MODEL               VARCHAR(100) NOT NULL,                -- 사용된 모델명
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 생성일시
);
```

## 6. 추가 참고사항
- PoC 단계이므로 동시 사용자 수, 대규모 트래픽 등은 우선 고려하지 않음
- UI/UX는 Open Web UI의 오픈소스 스타일을 참고하여 커스터마이징
- MCP 기반 자동 Tool 호출 및 수동 기능 병행 지원

---

*본 문서는 PoC(Proof of Concept) 단계의 요구사항 정의서로, 추후 상세 설계 및 구현 단계에서 변경될 수 있습니다.*
