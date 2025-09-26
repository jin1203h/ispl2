"""
벡터 테이블 차원 확인
"""
import asyncio
from services.database import get_async_session
from sqlalchemy import text

async def check_dimensions():
    async with get_async_session() as db:
        # pg_attribute에서 벡터 차원 확인
        query = """
            SELECT 
                c.relname as table_name,
                a.attname as column_name,
                CASE 
                    WHEN a.atttypmod = -1 THEN 'variable'
                    ELSE (a.atttypmod - 4)::text
                END as dimensions
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_type t ON a.atttypid = t.oid
            WHERE t.typname = 'vector'
            AND c.relkind = 'r'
            ORDER BY c.relname, a.attname
        """
        
        result = await db.execute(text(query))
        tables = result.fetchall()
        
        print("벡터 테이블 차원 정보:")
        for table in tables:
            print(f"  {table.table_name}.{table.column_name}: {table.dimensions} 차원")
        
        return tables

if __name__ == "__main__":
    asyncio.run(check_dimensions())

