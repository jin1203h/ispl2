#!/usr/bin/env python3
"""
ISPL Insurance Policy AI Backend 시작 스크립트
개발환경에서 빠른 테스트를 위한 스크립트
"""
import sys
import os
import subprocess
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 이상이 필요합니다. 현재 버전: %s", sys.version)
        return False
    logger.info("Python 버전: %s", sys.version.split()[0])
    return True

def install_requirements():
    """필수 패키지 설치"""
    try:
        logger.info("필수 패키지 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("패키지 설치 실패: %s", e)
        return False

def check_database_connection():
    """데이터베이스 연결 확인 (선택사항)"""
    try:
        # 환경변수에서 데이터베이스 URL 확인
        db_url = os.getenv('DATABASE_URL', 'postgresql://admin@localhost:5432/ispldb')
        logger.info("데이터베이스 URL: %s", db_url)
        
        # 실제 연결 테스트는 PostgreSQL이 실행 중일 때만 가능
        logger.info("데이터베이스 연결 테스트는 PostgreSQL 서버 실행 후 가능합니다.")
        return True
    except Exception as e:
        logger.warning("데이터베이스 연결 확인 실패: %s", e)
        return True  # 데이터베이스 없어도 서버 시작은 가능

def start_server():
    """FastAPI 서버 시작"""
    try:
        logger.info("FastAPI 서버 시작 중...")
        logger.info("서버 주소: http://localhost:8000")
        logger.info("API 문서: http://localhost:8000/docs")
        logger.info("종료하려면 Ctrl+C를 누르세요")
        
        # uvicorn으로 서버 시작
        subprocess.call([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        logger.info("서버가 종료되었습니다.")
    except Exception as e:
        logger.error("서버 시작 실패: %s", e)

def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("ISPL Insurance Policy AI Backend 시작")
    logger.info("=" * 60)
    
    # Python 버전 확인
    if not check_python_version():
        sys.exit(1)
    
    # 패키지 설치
    if not install_requirements():
        logger.error("패키지 설치에 실패했습니다. 수동으로 설치해주세요:")
        logger.error("pip install -r requirements.txt")
        sys.exit(1)
    
    # 데이터베이스 연결 확인
    check_database_connection()
    
    # 서버 시작
    start_server()

if __name__ == "__main__":
    main()


