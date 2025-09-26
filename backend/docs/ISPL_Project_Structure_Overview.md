# ISPL2 보험약관 AI 시스템 - 프로젝트 구조 개요

**프로젝트명**: ISPL2 Insurance Policy AI System  
**생성일**: 2025년 9월 26일  
**버전**: 1.0.0  
**담당**: ISPL AI Team

---

## 📋 **프로젝트 개요**

ISPL2는 **보험약관 기반 Multi-Agent AI 시스템**으로, PDF 문서 처리부터 자연어 질의응답까지 전체 파이프라인을 제공하는 통합 플랫폼입니다.

### **핵심 기능**
- 🤖 **Multi-Agent AI**: LangGraph 기반 에이전트 워크플로우
- 📄 **PDF 처리**: OCR, 표 추출, 구조 분석 자동화
- 🔍 **RAG 검색**: pgvector 기반 시맨틱 검색
- 💬 **채팅 UI**: GPT 스타일 대화형 인터페이스
- 📊 **모니터링**: LangFuse 기반 워크플로우 추적
- 🔗 **MCP 연동**: 자동 Tool 호출 시스템

---

## 🏗️ **전체 아키텍처**

```
┌─────────────────────────────────────────────────────────────────┐
│                        ISPL2 시스템                             │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Frontend      │    Backend      │       Database             │
│   (React/Next)  │   (FastAPI)     │    (PostgreSQL+pgvector)  │
│                 │                 │                            │
│ • ChatInterface │ • Multi-Agent   │ • 정책 메타데이터           │
│ • PolicyMgmt    │ • PDF Pipeline  │ • 벡터 임베딩               │
│ • Monitoring    │ • RAG Search    │ • 사용자 인증               │
│                 │ • Auth System   │ • 워크플로우 로그           │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

---

## 📁 **루트 디렉토리 구조**

```
d:\APP\ispl2\
├── 📊 archi.svg                      # 시스템 아키텍처 다이어그램
├── 📊 archi2.svg                     # 상세 아키텍처 다이어그램
├── 📋 Insurance Policy_prd.md        # 프로젝트 요구사항 문서 (PRD)
├── 🖥️ backend/                       # FastAPI 백엔드 서버
├── 🌐 frontend/                      # React/Next.js 프론트엔드
└── 🗄️ database/                      # PostgreSQL 도커 설정
```

---

## 🖥️ **Backend 구조 상세**

### **📂 핵심 디렉토리**

```
backend/
├── 🚀 main.py                        # FastAPI 메인 애플리케이션
├── 🎯 start.py                       # 서버 시작 스크립트 (의존성 자동설치)
├── 📋 requirements.txt               # Python 패키지 목록 (68개)
├── 📋 requirements_minimal.txt       # 최소 패키지 목록 (9개)
├── 🔧 env.example                    # 환경변수 템플릿
│
├── 🤖 agents/                        # Multi-Agent 시스템
│   ├── base.py                       # 기본 에이전트 클래스
│   ├── supervisor.py                 # 워크플로우 총괄 에이전트
│   ├── pdf_processor.py              # PDF 문서 처리 에이전트
│   ├── text_processor.py             # 텍스트 추출/정제 에이전트
│   ├── table_processor.py            # 표 데이터 처리 에이전트
│   ├── image_processor.py            # 이미지/OCR 처리 에이전트
│   ├── markdown_processor.py         # Markdown 변환 에이전트
│   ├── embedding_agent.py            # 임베딩 생성 에이전트
│   ├── quality_embedding_agent.py    # 임베딩 품질 관리 에이전트
│   └── query_processor.py            # 자연어 질의 처리 에이전트
│
├── 🌐 routers/                       # API 엔드포인트
│   ├── auth.py                       # 인증 API (JWT)
│   ├── auth_simple.py                # 간단한 인증 API
│   ├── policies.py                   # 약관 관리 API
│   ├── search.py                     # RAG 검색 API
│   └── workflow.py                   # 워크플로우 모니터링 API
│
├── 🔧 services/                      # 비즈니스 로직 서비스
│   ├── database.py                   # 데이터베이스 연결 관리
│   ├── auth.py                       # 인증 서비스 (JWT, 패스워드)
│   ├── pdf_pipeline.py               # PDF 처리 메인 파이프라인
│   ├── pdf_analysis.py               # PDF 구조 분석
│   ├── chunking_service.py           # 텍스트 청킹 서비스
│   ├── chunking_service_v2.py        # 고급 청킹 서비스
│   ├── table_service.py              # 표 추출/처리 서비스
│   ├── ocr_service.py                # OCR 처리 서비스
│   ├── advanced_image_service.py     # 고급 이미지 처리
│   ├── markdown_service.py           # Markdown 변환 서비스
│   ├── multi_model_embedding.py      # 다중 모델 임베딩 생성
│   ├── embedding_quality_service.py  # 임베딩 품질 검증
│   ├── optimized_vector_store.py     # 최적화된 벡터 저장소
│   ├── vector_store.py               # 기본 벡터 저장소
│   ├── advanced_search_engine.py     # 고급 검색 엔진
│   ├── answer_service.py             # LLM 답변 생성 서비스
│   └── result_service.py             # 검색 결과 후처리
│
├── 💾 models/                        # 데이터 모델
│   ├── database.py                   # SQLAlchemy ORM 모델
│   └── schemas.py                    # Pydantic 스키마 (API)
│
├── 🔧 utils/                         # 유틸리티 함수
│   ├── environment_config.py         # 환경 설정 관리
│   ├── performance_monitor.py        # 성능 모니터링
│   ├── structure_analyzer.py         # 문서 구조 분석
│   └── text_cleaner.py               # 텍스트 정제
│
├── 📊 docs/                          # 프로젝트 문서
│   ├── ISPL_SubTasks_Summary_Table.md    # 서브 태스크 요약 (32개 태스크)
│   ├── ISPL_SubTasks_Detailed_Report.md  # 상세 구현 보고서 (1204줄)
│   └── ISPL_Project_Structure_Overview.md # 프로젝트 구조 개요 (현재 문서)
│
├── 📁 data/                          # 정적 데이터
│   └── insurance_terms.json          # 보험 용어 사전
│
├── 💡 prompts/                       # AI 프롬프트 템플릿
│   └── insurance_rag_prompt.txt       # RAG 답변 생성 프롬프트
│
├── 📤 uploads/                       # 업로드된 파일 저장소
│   ├── *_sample_policy999.pdf         # 샘플 보험약관 PDF
│   ├── *_sample_policy999.md          # 변환된 Markdown
│   ├── *_무배당_AXA초간편건강보험*.pdf  # 실제 보험약관
│   └── *_무배당_AXA초간편건강보험*.md   # 변환된 Markdown
│
├── 📊 outputs/markdown/              # PDF→Markdown 변환 결과 (35개 파일)
│   ├── *.md                          # 변환된 마크다운 파일들
│   └── *.png                         # 추출된 이미지들 (27개)
│
├── 📈 reports/                       # 시스템 성능 리포트
│   ├── chunking_service/             # 청킹 서비스 테스트 결과 (14개 파일)
│   ├── image_processing/             # 이미지 처리 테스트 결과 (8개 파일)
│   ├── markdown_conversion/          # 마크다운 변환 테스트 (6개 파일)
│   ├── table_processing/             # 표 처리 테스트 결과 (4개 파일)
│   ├── quality_embedding/            # 임베딩 품질 테스트 (8개 파일)
│   ├── optimized_vector_store/       # 벡터 저장소 성능 (12개 파일)
│   ├── multi_model_embedding/        # 다중 모델 테스트 (2개 파일)
│   └── integrated_pipeline/          # 통합 파이프라인 테스트 (2개 파일)
│
├── 🗄️ database/                      # 데이터베이스 설정
│   └── init_pgvector_indexes.sql     # pgvector 인덱스 초기화 스크립트
│
└── 🧪 test_*.py                      # 테스트 스크립트 (25개 파일)
    ├── test_api.py                   # 통합 API 테스트
    ├── test_*_processor.py           # 각 에이전트별 테스트
    ├── test_*_service.py             # 각 서비스별 테스트
    └── test_*.py                     # 기타 단위 테스트들
```

### **🛠️ 설정 및 유틸리티 파일**

```
backend/
├── 📋 setup_java.md                  # Java 환경 설정 가이드
├── 📋 install_tesseract_guide.md     # Tesseract OCR 설치 가이드
├── 📋 KOREAN_NLP_SETUP.md            # 한국어 NLP 환경 설정
├── 🐍 install_korean_nlp.py          # 한국어 NLP 패키지 자동 설치
├── 🔧 init_admin_user.py             # 관리자 계정 초기화
├── 🔧 fix_existing_policies.py       # 기존 정책 데이터 수정
├── 🔍 check_dimensions.py            # 벡터 차원 확인
├── 🔍 check_table_schema.py          # 테이블 스키마 확인
├── 🗂️ create_hnsw_index.py           # HNSW 인덱스 생성
├── 🗂️ create_ivfflat_index.py        # IVFFlat 인덱스 생성
└── 🔧 vector_dimension_solutions.py  # 벡터 차원 문제 해결
```

---

## 🌐 **Frontend 구조 상세**

### **📂 핵심 디렉토리**

```
frontend/
├── 📋 package.json                   # Node.js 패키지 관리
├── 🔧 next.config.js                 # Next.js 설정
├── 🎨 tailwind.config.js             # Tailwind CSS 설정
├── 📝 tsconfig.json                  # TypeScript 설정
├── 🔧 env.example                    # 환경변수 템플릿
├── 📋 INSTALL.md                     # 설치 가이드
│
├── 📱 src/                           # 소스 코드
│   ├── 🏠 app/                       # Next.js App Router
│   │   ├── layout.tsx                # 루트 레이아웃
│   │   ├── page.tsx                  # 메인 페이지 (홈)
│   │   └── globals.css               # 글로벌 스타일
│   │
│   ├── 🧩 components/                # React 컴포넌트
│   │   ├── 💬 chat/                  # 채팅 관련 컴포넌트
│   │   │   ├── ChatInterface.tsx     # 메인 채팅 인터페이스
│   │   │   ├── ChatMessage.tsx       # 개별 메시지 컴포넌트
│   │   │   ├── ChatInput.tsx         # 메시지 입력 컴포넌트
│   │   │   └── SearchResults.tsx     # 검색 결과 표시 컴포넌트
│   │   │
│   │   ├── 🔐 auth/                  # 인증 관련 컴포넌트
│   │   │   └── Login.tsx             # 로그인 모달 컴포넌트
│   │   │
│   │   ├── 🗂️ layout/                # 레이아웃 컴포넌트
│   │   │   └── Sidebar.tsx           # 사이드바 네비게이션
│   │   │
│   │   ├── 📄 policies/              # 약관 관리 컴포넌트
│   │   │   └── PolicyManagement.tsx  # 약관 업로드/관리 UI
│   │   │
│   │   └── 📊 workflow/              # 워크플로우 모니터링
│   │       └── WorkflowMonitoring.tsx # 에이전트 실행 상태 모니터링
│   │
│   ├── 🎯 hooks/                     # Custom React Hooks
│   │   └── useChat.ts                # 채팅 상태 관리 훅
│   │
│   ├── 🌐 services/                  # API 통신 서비스
│   │   └── api.ts                    # Backend API 통신 로직
│   │
│   ├── 📋 types/                     # TypeScript 타입 정의
│   │   └── api.ts                    # API 타입 정의 (218줄)
│   │
│   └── 🔧 contexts/                  # React Context
│       └── AuthContext.tsx           # 인증 상태 관리 Context
│
└── 📁 public/                        # 정적 파일 (아이콘, 이미지 등)
```

### **🎯 주요 기능별 컴포넌트**

#### **💬 채팅 시스템**
- `ChatInterface.tsx` - GPT 스타일 채팅 UI
- `ChatMessage.tsx` - 사용자/AI 메시지 렌더링
- `ChatInput.tsx` - 질문 입력 및 전송
- `SearchResults.tsx` - 검색 결과 사이드바

#### **🔐 인증 시스템**
- `Login.tsx` - 모달 방식 로그인 UI
- `AuthContext.tsx` - JWT 토큰 기반 상태 관리

#### **📄 약관 관리**
- `PolicyManagement.tsx` - 파일 업로드, 목록 조회, 삭제

#### **📊 모니터링**
- `WorkflowMonitoring.tsx` - Multi-Agent 실행 상태 추적

---

## 🗄️ **Database 구조**

### **PostgreSQL + pgvector 설정**

```
database/
├── 🐳 Dockerfile                     # PostgreSQL + pgvector 이미지
└── 🗄️ init.sql                       # 초기 데이터베이스 설정
```

### **주요 테이블 구조**

```sql
-- 사용자 관리
users (user_id, email, password_hash, role, created_at)

-- 보험약관 메타데이터
policies (policy_id, company, category, product_name, file_paths, created_at)

-- 벡터 임베딩 저장
embeddings (id, policy_id, chunk_text, embedding[1536], chunk_index, model)

-- 워크플로우 로그
workflow_logs (log_id, workflow_id, step_name, status, execution_time)
```

---

## 🚀 **핵심 기술 스택**

### **Backend (Python)**
- **FastAPI** - 고성능 웹 프레임워크
- **LangGraph** - Multi-Agent 워크플로우
- **LangChain** - LLM 체인 관리
- **pgvector** - PostgreSQL 벡터 확장
- **OpenAI** - GPT-4 모델 API
- **Tesseract** - OCR 엔진
- **OpenCV** - 이미지 처리
- **pdfplumber** - PDF 파싱

### **Frontend (TypeScript)**
- **Next.js 14** - React 프레임워크
- **Tailwind CSS** - 유틸리티 CSS
- **React Query** - 서버 상태 관리
- **React Markdown** - 마크다운 렌더링

### **Infrastructure**
- **PostgreSQL** - 관계형 데이터베이스
- **pgvector** - 벡터 유사도 검색
- **Docker** - 컨테이너화
- **LangFuse** - AI 워크플로우 모니터링

---

## 📊 **현재 구현 상태**

### **✅ 완료된 기능 (18개 - 진척률 56%)**

#### **🎯 Core Infrastructure (완료)**
1. **FastAPI 백엔드 기본 구조** - API 서버, 인증, 라우팅 완성
2. **LangGraph Multi-Agent 아키텍처** - SupervisorAgent 중심 멀티에이전트 시스템

#### **📄 PDF 처리 파이프라인 (완료 6개)**
3. **Task 3.1**: PDF 품질 분석 및 구조 파악 - 고급 구조 분석, 스캔 품질 평가
4. **Task 3.2**: 텍스트 추출 및 정제 강화 - pdfplumber + Tesseract OCR 통합
5. **Task 3.3**: 표 데이터 처리 및 구조화 - camelot-py, tabula-py 조합 처리
6. **Task 3.4**: 이미지 처리 및 OCR 통합 - AdvancedImageService 구현
7. **Task 3.5**: Markdown 변환 및 구조 보존 - 문서 구조 유지 변환
8. **Task 3.6**: PDF 처리 파이프라인 통합 - 성능 모니터링, 병렬 처리

#### **🔮 임베딩 및 벡터 저장 (완료 4개)**
9. **Task 4.1**: 보안 등급별 임베딩 모델 관리 - 공개망/폐쇄망별 모델 선택
10. **Task 4.2**: 고급 청킹 및 토큰화 시스템 - Fixed/Content-aware/Semantic 3가지 전략
11. **Task 4.3**: 임베딩 품질 검증 및 배치 최적화 - 품질 검증, 동적 배치 조정
12. **Task 4.4**: pgvector 저장 최적화 및 인덱싱 - HNSW 인덱스, 대량 삽입 최적화

#### **🔍 RAG 검색 시스템 (완료 4개)**
13. **Task 5.1**: 자연어 질의 전처리 및 의도 분석 - KoNLPy, 보험 용어 특화
14. **Task 5.2**: 벡터 유사도 검색 엔진 최적화 - 하이브리드 검색 (벡터+키워드)
15. **Task 5.3**: 검색 결과 후처리 및 재랭킹 - Cross-encoder 재랭킹, 중복 제거
16. **Task 5.4**: LLM 기반 답변 생성 파이프라인 - GPT-4o 통합, 보험 특화 프롬프트

#### **🌟 메인 태스크 (완료 2개)**
17. **RAG 기반 자연어 질의 검색 시스템** - 전체 검색 파이프라인 통합 완성
18. **PDF 처리 파이프라인** - 모든 PDF 처리 기능 통합 완성

### **⏳ 대기 중인 기능 (13개 - 41%)**

#### **📈 LangFuse 워크플로우 모니터링 (4개)**
- **Task 6.1**: LangFuse SDK 통합 및 기본 설정
- **Task 6.2**: Multi-Agent 워크플로우 추적 구현
- **Task 6.3**: 성능 메트릭 수집 및 분석 대시보드
- **Task 6.4**: WorkflowMonitor 컴포넌트 연동 및 시각화

#### **🤖 MCP 연동 및 자동 Tool 호출 (3개)**
- **Task 7.1**: MCP 프로토콜 클라이언트 구현
- **Task 7.2**: 자연어 의도 분석 및 Tool 라우팅 시스템
- **Task 7.3**: ChatInterface 통합 자동화

#### **🐳 Docker 컨테이너 환경 (3개)**
- **Task 8.1**: Backend Docker 환경 구성
- **Task 8.2**: Multi-container docker-compose 통합
- **Task 8.3**: 개발/운영 환경 분리 설정

#### **🔗 메인 태스크 (3개)**
- **LangFuse 워크플로우 모니터링 시스템 통합**
- **MCP 연동 및 자동 Tool 호출 시스템**
- **Docker 컨테이너 환경 구성 및 배포 시스템**

---

## 🔄 **개발 워크플로우**

### **1. 백엔드 개발 시작**
```bash
cd backend
python start.py          # 의존성 자동설치 + 서버 실행
python test_api.py       # API 테스트
```

### **2. 프론트엔드 개발 시작**
```bash
cd frontend
npm install              # 의존성 설치
npm run dev             # 개발 서버 실행 (localhost:3000)
```

### **3. 데이터베이스 설정**
```bash
cd database
docker build -t ispl-postgres .
docker run -d --name ispl-db -p 5432:5432 ispl-postgres
```

---

## 📈 **성능 최적화**

### **Backend 최적화**
- **비동기 처리**: FastAPI + asyncio
- **벡터 인덱싱**: HNSW, IVFFlat 인덱스
- **배치 처리**: 대용량 PDF 분할 처리
- **캐싱**: Redis 기반 결과 캐싱 (예정)

### **Frontend 최적화**
- **코드 분할**: Next.js dynamic imports
- **상태 관리**: React Query 캐싱
- **번들 최적화**: Tree shaking
- **이미지 최적화**: Next.js Image 컴포넌트

---

## 🔒 **보안 고려사항**

### **데이터 보안**
- **JWT 토큰** - 무상태 인증
- **패스워드 해싱** - bcrypt 암호화
- **보안 등급** - public/internal/confidential 분류
- **CORS 설정** - 허용된 도메인만 접근

### **API 보안**
- **Rate Limiting** - 요청 속도 제한
- **Input Validation** - Pydantic 스키마 검증
- **SQL Injection 방지** - SQLAlchemy ORM
- **XSS 방지** - Content Security Policy

---

## 📋 **다음 단계 액션 아이템**

### **🎯 다음 진행 권장 순서**
1. **Task 6.1** - LangFuse SDK 통합 및 기본 설정 (즉시 시작 가능)
2. **Task 8.1** - Backend Docker 환경 구성 (병렬 진행 가능)

### **📅 단계별 로드맵 (업데이트)**
- **✅ Week 1-4**: Core System + Search System + PDF Pipeline **완료** (18개 태스크)
- **🚧 Week 5**: LangFuse 모니터링 시스템 구현 (Task 6.1-6.4)
- **🚧 Week 6**: Docker 배포 환경 구성 (Task 8.1-8.3)
- **🚧 Week 7**: MCP 자동화 시스템 구현 (Task 7.1-7.3)
- **🎯 Week 8**: 통합 테스트 및 최종 검증

### **💪 현재 달성도**
- **전체 진척률**: **56% 완료** (18/32 태스크)
- **핵심 기능**: **RAG 검색 시스템 100% 완성** ✅
- **남은 작업**: **모니터링 및 배포 시스템** (13개 태스크)

---

## 📞 **연락처 및 지원**

**개발팀**: ISPL AI Team  
**문서 관리**: backend/docs/  
**이슈 트래킹**: GitHub Issues  
**API 문서**: http://localhost:8000/docs  

---

**마지막 업데이트**: 2025년 9월 26일 (태스크 시스템 동기화)  
**문서 버전**: 1.1.0  
**총 라인 수**: 현재 문서 (450+ 줄)  
**진척률**: **56% 완료** (18/32 태스크) - 핵심 RAG 시스템 완성

