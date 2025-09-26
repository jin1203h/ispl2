# ISPL Insurance Policy AI Backend

보험약관 기반 Agentic AI 시스템의 FastAPI 백엔드 서버입니다.

## 🚀 빠른 시작

### 1. 필수 조건
- Python 3.8 이상
- PostgreSQL (선택사항 - 나중에 설정 가능)

### 2. 서버 실행
```bash
# 백엔드 디렉토리로 이동
cd backend

# 서버 시작 (패키지 자동 설치 포함)
python start.py
```

### 3. API 테스트
```bash
# 다른 터미널에서 실행
python test_api.py
```

## 📚 API 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 주요 엔드포인트

### 인증 (Authentication)
- `POST /auth/login` - 사용자 로그인
- `POST /auth/register` - 사용자 회원가입
- `GET /auth/verify` - 토큰 검증

### 약관 관리 (Policy Management)
- `GET /policies` - 약관 목록 조회
- `POST /policies/upload` - 약관 파일 업로드 (인증 필요)
- `GET /policies/{id}` - 특정 약관 조회
- `DELETE /policies/{id}` - 약관 삭제 (인증 필요)
- `GET /policies/{id}/pdf` - PDF 파일 다운로드
- `GET /policies/{id}/md` - Markdown 파일 조회

### 검색 (Search)
- `POST /search` - RAG 기반 자연어 검색

### 워크플로우 모니터링 (Workflow Monitoring)
- `GET /workflow/logs` - 워크플로우 로그 조회 (인증 필요)
- `GET /workflow/logs/summary` - 워크플로우 요약 정보 (인증 필요)

## 🧪 테스트 계정

개발용 테스트 계정:
- **관리자**: `admin@ispl2.com` / `admin`
- **사용자**: `user@ispl2.com` / `user`

## 🗄️ 데이터베이스 설정

### PostgreSQL + pgvector 설정
```bash
# Docker로 PostgreSQL 실행 (선택사항)
cd ../database
docker build -t ispl-postgres .
docker run -d --name ispl-db -p 5432:5432 ispl-postgres
```

### 환경 변수 설정
```bash
# env.example을 참고하여 .env 파일 생성
cp env.example .env
# DATABASE_URL 등 필요한 설정 수정
```

## 📁 프로젝트 구조

```
backend/
├── main.py              # FastAPI 메인 애플리케이션
├── requirements.txt     # Python 의존성
├── start.py            # 서버 시작 스크립트
├── test_api.py         # API 테스트 스크립트
├── env.example         # 환경 변수 템플릿
├── routers/            # API 라우터
│   ├── auth.py         # 인증 API
│   ├── policies.py     # 약관 관리 API
│   ├── search.py       # 검색 API
│   └── workflow.py     # 워크플로우 모니터링 API
├── models/             # 데이터 모델
│   ├── database.py     # SQLAlchemy 모델
│   └── schemas.py      # Pydantic 스키마
└── services/           # 서비스 레이어
    ├── database.py     # 데이터베이스 연결
    └── auth.py         # 인증 서비스
```

## 🔧 현재 구현 상태

### ✅ 완료된 기능
- [x] FastAPI 기본 구조
- [x] JWT 인증 시스템
- [x] PostgreSQL + pgvector 모델
- [x] 기본 API 엔드포인트
- [x] 프론트엔드 호환 API
- [x] CORS 설정

### 🚧 진행 중인 기능
- [ ] 실제 PDF 처리 파이프라인
- [ ] 임베딩 생성 및 벡터 검색
- [ ] LangGraph Multi-Agent 시스템
- [ ] LangFuse 모니터링 연동
- [ ] MCP 프로토콜 연동

## 🐛 문제 해결

### ImportError 발생 시
```bash
# 패키지 재설치
pip install -r requirements.txt
```

### 데이터베이스 연결 오류 시
```bash
# 환경 변수 확인
echo $DATABASE_URL

# PostgreSQL 상태 확인
docker ps | grep postgres
```

### 포트 충돌 시
```bash
# 다른 포트로 실행
uvicorn main:app --port 8001
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. `python test_api.py` 실행 결과
2. 서버 로그 메시지
3. API 문서 (http://localhost:8000/docs)


