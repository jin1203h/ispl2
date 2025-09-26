#!/usr/bin/env python3
"""
간단한 DB 연결 테스트
"""
import asyncio
import sys
import os

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_db_connection():
    """DB 연결 및 테이블 확인 테스트"""
    try:
        from services.database import create_tables
        print("🚀 DB 연결 및 테이블 확인 시작...")
        
        await create_tables()
        print("✅ DB 연결 및 테이블 확인/생성 성공!")
        return True
        
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("PostgreSQL 연결 테스트")
    print("=" * 50)
    
    success = asyncio.run(test_db_connection())
    
    if success:
        print("\n🎉 DB 연결 성공! 백엔드 서버를 시작할 수 있습니다.")
        sys.exit(0)
    else:
        print("\n🚨 DB 연결 실패! PostgreSQL 서버 상태를 확인하세요.")
        print("- PostgreSQL이 실행 중인지 확인")
        print("- 사용자명/비밀번호 확인 (admin/admin)")
        print("- 데이터베이스 존재 확인 (ispldb)")
        sys.exit(1)
