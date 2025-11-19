"""
ISPL Insurance Policy AI - FastAPI Backend
보험약관 기반 Agentic AI 시스템 메인 애플리케이션

기존 프론트엔드 API 서비스와 완전 호환되는 FastAPI 백엔드 서버
"""

# .env 파일 로드 (가장 먼저 실행)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
from contextlib import asynccontextmanager

from routers import auth, policies, search, workflow, dashboard
from services.database import engine, create_tables
from models.database import Base

# 로깅 설정 - 환경 변수에서 레벨 가져오기
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

logging.basicConfig(
    level=log_level_mapping.get(log_level, logging.DEBUG),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 추가 로거 설정 (더 상세한 디버깅)
uvicorn_level = log_level_mapping.get(log_level, logging.DEBUG)
logging.getLogger("uvicorn").setLevel(uvicorn_level)
logging.getLogger("uvicorn.access").setLevel(uvicorn_level)
logging.getLogger("fastapi").setLevel(uvicorn_level)

# SQLAlchemy는 너무 많은 로그를 출력하므로 한 단계 높게 설정
sql_level = logging.INFO if log_level == "DEBUG" else uvicorn_level
logging.getLogger("sqlalchemy").setLevel(sql_level)

# PDF 처리 관련 로거들의 로그 레벨 조정 (매우 많은 DEBUG 로그 방지)
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfminer.pdfinterp").setLevel(logging.ERROR)
logging.getLogger("pdfminer.psparser").setLevel(logging.ERROR)
logging.getLogger("pdfminer.pdfpage").setLevel(logging.ERROR)
logging.getLogger("pdfminer.converter").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)
logging.getLogger("fitz").setLevel(logging.WARNING)  # PyMuPDF
logging.getLogger("PIL").setLevel(logging.WARNING)  # Pillow
logging.getLogger("camelot").setLevel(logging.WARNING)
logging.getLogger("tabula").setLevel(logging.WARNING)

logger.debug(f"로그 레벨 설정: {log_level}")
logger.debug(f"디버그 모드: {os.getenv('DEBUG', 'True')}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시 실행
    logger.info("ISPL Insurance Policy AI Backend 시작")
    
    # 데이터베이스 테이블 생성 (필수)
    try:
        await create_tables()
        logger.info("✅ 데이터베이스 연결 및 테이블 생성 성공!")
    except Exception as e:
        logger.error(f"🚨 데이터베이스 연결 실패: {e}")
        logger.error("프로그램을 종료합니다. PostgreSQL이 실행 중인지 확인하세요.")
        raise e  # 앱 시작 실패
    
    yield
    
    # 종료 시 실행
    logger.info("ISPL Insurance Policy AI Backend 종료")

# FastAPI 앱 초기화
app = FastAPI(
    title="ISPL Insurance Policy AI",
    description="보험약관 기반 Agentic AI 시스템 Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 설정 - 프론트엔드 호환성
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 글로벌 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리기 - 프론트엔드 기대 형식으로 에러 반환"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "내부 서버 오류가 발생했습니다."}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리기 - 프론트엔드 호환 에러 형식"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# 라우터 등록 - 기존 프론트엔드 API 인터페이스 호환
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(policies.router, prefix="/policies", tags=["Policy Management"])
app.include_router(search.router, prefix="", tags=["Search"])  # /search 엔드포인트
app.include_router(workflow.router, prefix="/workflow", tags=["Workflow Monitoring"])
app.include_router(dashboard.router, prefix="", tags=["Performance Dashboard"])  # /dashboard 엔드포인트

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "service": "ISPL Insurance Policy AI Backend"}

# .well-known 경로 처리 (Chrome DevTools 오류 방지)
@app.get("/.well-known/{path:path}")
async def well_known_handler(path: str):
    """Chrome DevTools 관련 요청 처리"""
    logger.debug(f"Chrome DevTools 요청 무시: /.well-known/{path}")
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 정보"""
    return {
        "message": "ISPL Insurance Policy AI Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

if __name__ == "__main__":
    # 환경 변수에서 로그 레벨 가져오기
    uvicorn_log_level = os.getenv("LOG_LEVEL", "DEBUG").lower()
    
    # Windows에서 multiprocessing 문제 방지
    import multiprocessing
    multiprocessing.freeze_support()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Windows에서 reload 비활성화
        log_level=uvicorn_log_level
    )
