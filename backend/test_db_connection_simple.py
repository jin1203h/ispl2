"""
간단한 데이터베이스 연결 테스트
실제 DB 연계를 위한 기본 상태 확인
"""
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_connection():
    """기본 연결 테스트"""
    print("=" * 50)
    print("기본 데이터베이스 연결 테스트")
    print("=" * 50)
    
    try:
        from services.database import check_database_connection, check_pgvector_extension
        
        # 1. 기본 연결 테스트
        print("1. 데이터베이스 연결 테스트...")
        result = await check_database_connection()
        print(f"   결과: {'✅ 성공' if result else '❌ 실패'}")
        
        if not result:
            print("   데이터베이스 연결 실패 - 추가 테스트 중단")
            return False
        
        # 2. pgvector 확장 테스트
        print("2. pgvector 확장 확인...")
        pgvector_result = await check_pgvector_extension()
        print(f"   결과: {'✅ 설치됨' if pgvector_result else '❌ 없음'}")
        
        return result and pgvector_result
        
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

async def test_basic_queries():
    """기본 쿼리 테스트"""
    print("\n" + "=" * 50)
    print("기본 SQL 쿼리 테스트")
    print("=" * 50)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 1. 간단한 SELECT 테스트
            print("1. 기본 SELECT 테스트...")
            result = await db.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            print(f"   결과: {row.test_value if row else 'None'}")
            
            # 2. 현재 시간 조회
            print("2. 현재 시간 조회...")
            result = await db.execute(text("SELECT NOW() as current_time"))
            row = result.fetchone()
            print(f"   결과: {row.current_time if row else 'None'}")
            
            # 3. 버전 정보 조회
            print("3. PostgreSQL 버전 확인...")
            result = await db.execute(text("SELECT version()"))
            row = result.fetchone()
            version = str(row[0])[:50] + "..." if row and len(str(row[0])) > 50 else str(row[0]) if row else "Unknown"
            print(f"   결과: {version}")
            
            return True
            
    except Exception as e:
        print(f"❌ 쿼리 테스트 실패: {e}")
        return False

async def test_table_exists():
    """테이블 존재 확인"""
    print("\n" + "=" * 50)
    print("테이블 존재 확인")
    print("=" * 50)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 임베딩 테이블 확인
            tables_to_check = [
                "policies",
                "embeddings_text_embedding_3", 
                "embeddings_qwen"
            ]
            
            for table_name in tables_to_check:
                print(f"테이블 '{table_name}' 확인...")
                
                # 테이블 존재 확인
                check_query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """
                result = await db.execute(text(check_query), {"table_name": table_name})
                exists = result.scalar()
                
                if exists:
                    # 레코드 수 확인
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    result = await db.execute(text(count_query))
                    count = result.scalar()
                    print(f"   ✅ 존재함 (레코드 수: {count})")
                else:
                    print(f"   ❌ 존재하지 않음")
            
            return True
            
    except Exception as e:
        print(f"❌ 테이블 확인 실패: {e}")
        return False

async def main():
    """메인 테스트 실행"""
    print("실제 데이터베이스 연계 테스트 시작")
    print("=" * 60)
    
    # 1. 기본 연결 테스트
    connection_ok = await test_basic_connection()
    
    if connection_ok:
        # 2. 기본 쿼리 테스트
        query_ok = await test_basic_queries()
        
        if query_ok:
            # 3. 테이블 존재 확인
            table_ok = await test_table_exists()
            
            if table_ok:
                print("\n" + "=" * 60)
                print("✅ 모든 기본 테스트 통과 - 실제 기능 테스트 준비 완료")
                print("=" * 60)
                return True
    
    print("\n" + "=" * 60)
    print("❌ 기본 테스트 실패 - 실제 기능 테스트 불가")
    print("=" * 60)
    return False

if __name__ == "__main__":
    asyncio.run(main())

