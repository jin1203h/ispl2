"""
데이터베이스 연결 및 설정
PostgreSQL + pgvector 연동
"""
import os
import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from models.database import Base

logger = logging.getLogger(__name__)

# 데이터베이스 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:admin@localhost:5432/ispldb"
)

# 비동기 URL로 변환 (asyncpg 사용)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# 동기 엔진 (초기화용)
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 비동기 엔진 (운영용) - 무조건 연결 성공 설정
async_engine = create_async_engine(
    ASYNC_DATABASE_URL, 
    echo=False,
    future=True,
    pool_size=1,          # 최소 연결 풀
    max_overflow=0,       # 오버플로우 없음
    pool_pre_ping=True,   # 연결 상태 사전 확인
    pool_recycle=-1,      # 연결 재활용 비활성화
    pool_timeout=60,      # 연결 대기 시간 증가
    connect_args={
        "server_settings": {
            "application_name": "ispl_backend",
        }
    }
)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    expire_on_commit=False
)

async def create_tables():
    """데이터베이스 연결 확인 및 필요시 테이블 생성"""
    max_retries = 3  # 연결 테스트용
    base_retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"데이터베이스 연결 시도 {attempt + 1}/{max_retries}")
            
            # 단계 1: 기본 연결 테스트
            logger.info("1단계: 기본 연결 테스트...")
            async with async_engine.connect() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                logger.info(f"✅ 기본 연결 성공: test={test_value}")
            
            # 단계 2: PostgreSQL 버전 확인
            logger.info("2단계: PostgreSQL 버전 확인...")
            async with async_engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"✅ PostgreSQL 버전: {version.split(',')[0]}")
            
            # 단계 3: 기존 테이블 확인
            logger.info("3단계: 기존 테이블 확인...")
            async with async_engine.connect() as conn:
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """))
                existing_tables = [row[0] for row in result.fetchall()]
                
                if existing_tables:
                    logger.info(f"✅ 기존 테이블 발견: {', '.join(existing_tables)}")
                    
                    # 필수 테이블들 확인
                    required_tables = ['policies', 'embeddings_text_embedding_3', 'workflow_logs']
                    missing_tables = [table for table in required_tables if table not in existing_tables]
                    
                    if missing_tables:
                        logger.warning(f"⚠️ 누락된 테이블: {', '.join(missing_tables)}")
                        need_create = True
                    else:
                        logger.info("✅ 모든 필수 테이블 존재 - 생성 건너뛰기")
                        need_create = False
                else:
                    logger.info("📝 기존 테이블 없음 - 새로 생성 필요")
                    need_create = True
            
            # 단계 4: 필요시 pgvector 확장 및 테이블 생성
            if need_create:
                logger.info("4단계: pgvector 확장 확인...")
                async with async_engine.begin() as conn:
                    try:
                        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                        logger.info("✅ pgvector 확장 설치/확인 완료")
                    except Exception as ext_error:
                        logger.warning(f"⚠️ pgvector 확장 설치 건너뛰기: {ext_error}")
                
                logger.info("5단계: 테이블 생성...")
                async with async_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("✅ 테이블 생성 완료")
                
                # 생성 후 재확인
                async with async_engine.connect() as conn:
                    result = await conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        ORDER BY table_name
                    """))
                    final_tables = [row[0] for row in result.fetchall()]
                    logger.info(f"✅ 최종 테이블 목록: {', '.join(final_tables)}")
            
            logger.info("🎉 데이터베이스 연결 및 테이블 확인/생성 완료!")
            return  # 성공시 함수 종료
            
        except Exception as e:
            retry_delay = base_retry_delay * (attempt + 1)
            logger.error(f"❌ 시도 {attempt + 1} 실패: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ {retry_delay}초 후 재시도 (남은 시도: {max_retries - attempt - 1})")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("🚨 모든 재시도 실패 - 프로그램을 종료합니다")
                raise Exception("데이터베이스 연결 필수 - 연결 실패로 프로그램 종료")

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """비동기 데이터베이스 세션 생성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """동기 데이터베이스 세션 생성 (초기화용)"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성용 데이터베이스 세션"""
    async with get_async_session() as session:
        yield session

async def check_database_connection():
    """데이터베이스 연결 확인"""
    try:
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()  # fetchone()은 async가 아님
        logger.info("데이터베이스 연결 성공")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return False

async def check_pgvector_extension():
    """pgvector 확장 설치 확인"""
    try:
        async with get_async_session() as session:
            result = await session.execute(
                text("SELECT * FROM pg_extension WHERE extname = 'vector'")
            )
            extension = result.fetchone()  # fetchone()은 async가 아님
            
        if extension:
            logger.info("pgvector 확장 설치 확인됨")
            return True
        else:
            logger.warning("pgvector 확장이 설치되지 않음")
            return False
            
    except Exception as e:
        logger.error(f"pgvector 확장 확인 실패: {e}")
        return False

# 데이터베이스 초기화 함수
async def initialize_database():
    """데이터베이스 전체 초기화"""
    try:
        logger.info("데이터베이스 초기화 시작")
        
        # 연결 확인
        if not await check_database_connection():
            raise Exception("데이터베이스 연결 실패")
        
        # 테이블 생성
        await create_tables()
        
        # pgvector 확장 확인
        await check_pgvector_extension()
        
        logger.info("데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise
