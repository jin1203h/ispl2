"""
테이블 스키마 확인 도구
"""
import asyncio
from services.database import get_async_session
from sqlalchemy import text

async def check_schema():
    async with get_async_session() as db:
        # 1. 모든 테이블 목록
        print("1. 모든 테이블 목록:")
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        result = await db.execute(text(tables_query))
        tables = result.fetchall()
        
        for table in tables:
            print(f"   - {table.table_name}")
        
        # 2. embeddings_text_embedding_3 스키마
        print("\n2. embeddings_text_embedding_3 스키마:")
        schema_query = """
            SELECT column_name, data_type, udt_name, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'embeddings_text_embedding_3'
            ORDER BY ordinal_position
        """
        result = await db.execute(text(schema_query))
        columns = result.fetchall()
        
        if columns:
            for col in columns:
                print(f"   {col.column_name}: {col.data_type} ({col.udt_name}) - NULL: {col.is_nullable}")
        else:
            print("   테이블을 찾을 수 없습니다")
        
        # 3. 샘플 데이터 조회 (있다면)
        print("\n3. 샘플 데이터:")
        try:
            sample_query = "SELECT * FROM embeddings_text_embedding_3 LIMIT 1"
            result = await db.execute(text(sample_query))
            sample = result.fetchone()
            
            if sample:
                print(f"   샘플 레코드 발견: {sample}")
            else:
                print("   데이터 없음")
        except Exception as e:
            print(f"   조회 실패: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())

