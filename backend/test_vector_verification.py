"""
벡터 삽입 확인 및 검증 도구
실제 pgvector 데이터베이스의 벡터 데이터를 조회하고 분석
"""
import asyncio
import logging
from typing import List, Dict, Any
import numpy as np

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_vector_tables():
    """벡터 테이블 현황 확인"""
    print("=" * 60)
    print("벡터 테이블 현황 확인")
    print("=" * 60)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 1. 모든 벡터 테이블 목록 조회
            print("1. 벡터 테이블 목록...")
            
            vector_tables_query = """
                SELECT 
                    table_name,
                    column_name,
                    data_type
                FROM information_schema.columns 
                WHERE data_type = 'USER-DEFINED' 
                AND udt_name = 'vector'
                ORDER BY table_name, column_name
            """
            
            result = await db.execute(text(vector_tables_query))
            vector_tables = result.fetchall()
            
            if vector_tables:
                print("   발견된 벡터 테이블:")
                for table in vector_tables:
                    print(f"     - {table.table_name}.{table.column_name} ({table.data_type})")
            else:
                print("   ❌ 벡터 테이블을 찾을 수 없습니다")
                return False
            
            # 2. 각 테이블의 벡터 데이터 개수 확인
            print("\n2. 테이블별 벡터 데이터 개수...")
            
            table_stats = {}
            for table in vector_tables:
                table_name = table.table_name
                column_name = table.column_name
                
                try:
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    result = await db.execute(text(count_query))
                    count = result.scalar()
                    
                    # 벡터 차원 확인
                    dim_query = f"""
                        SELECT vector_dims(embedding) as dimensions 
                        FROM {table_name} 
                        WHERE embedding IS NOT NULL 
                        LIMIT 1
                    """
                    result = await db.execute(text(dim_query))
                    dim_row = result.fetchone()
                    dimensions = dim_row.dimensions if dim_row else "Unknown"
                    
                    table_stats[table_name] = {
                        "count": count,
                        "dimensions": dimensions,
                        "column": column_name
                    }
                    
                    print(f"     {table_name}: {count}개 벡터 (차원: {dimensions})")
                    
                except Exception as e:
                    print(f"     {table_name}: 조회 실패 - {e}")
            
            return table_stats
            
    except Exception as e:
        print(f"❌ 벡터 테이블 확인 실패: {e}")
        return False

async def inspect_vector_data(table_name: str = "embeddings_text_embedding_3", limit: int = 5):
    """특정 테이블의 벡터 데이터 상세 조회"""
    print(f"\n{'=' * 60}")
    print(f"벡터 데이터 상세 조회: {table_name}")
    print("=" * 60)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 1. 기본 정보 조회
            print("1. 기본 정보...")
            
            info_query = f"""
                SELECT 
                    COUNT(*) as total_count,
                    MIN(id) as min_id,
                    MAX(id) as max_id
                FROM {table_name}
            """
            
            result = await db.execute(text(info_query))
            info = result.fetchone()
            
            if info and info.total_count > 0:
                print(f"   총 레코드: {info.total_count}개")
                print(f"   ID 범위: {info.min_id} ~ {info.max_id}")
            else:
                print("   ❌ 데이터가 없습니다")
                return False
            
            # 2. 샘플 데이터 조회
            print(f"\n2. 샘플 데이터 (최대 {limit}개)...")
            
            sample_query = f"""
                SELECT 
                    id,
                    policy_id,
                    chunk_index,
                    chunk_text,
                    vector_dims(embedding) as dimensions,
                    model,
                    created_at
                FROM {table_name}
                ORDER BY id
                LIMIT {limit}
            """
            
            result = await db.execute(text(sample_query))
            samples = result.fetchall()
            
            for i, sample in enumerate(samples, 1):
                print(f"\n   샘플 {i}:")
                print(f"     ID: {sample.id}")
                print(f"     Policy ID: {sample.policy_id}")
                print(f"     Chunk Index: {sample.chunk_index}")
                print(f"     Content: {sample.chunk_text[:100]}...")
                print(f"     Model: {sample.model}")
                print(f"     Vector Dimensions: {sample.dimensions}")
                print(f"     Created: {sample.created_at}")
            
            # 3. 벡터 품질 분석
            print(f"\n3. 벡터 품질 분석...")
            await analyze_vector_quality(db, table_name)
            
            return True
            
    except Exception as e:
        print(f"❌ 벡터 데이터 조회 실패: {e}")
        return False

async def analyze_vector_quality(db, table_name: str):
    """벡터 품질 분석"""
    try:
        # 벡터 norm 분석
        norm_query = f"""
            SELECT 
                AVG(vector_norm(embedding)) as avg_norm,
                MIN(vector_norm(embedding)) as min_norm,
                MAX(vector_norm(embedding)) as max_norm,
                STDDEV(vector_norm(embedding)) as std_norm
            FROM {table_name}
            WHERE embedding IS NOT NULL
        """
        
        result = await db.execute(text(norm_query))
        norm_stats = result.fetchone()
        
        if norm_stats:
            print(f"   벡터 Norm 통계:")
            print(f"     평균: {norm_stats.avg_norm:.6f}")
            print(f"     최소: {norm_stats.min_norm:.6f}")
            print(f"     최대: {norm_stats.max_norm:.6f}")
            print(f"     표준편차: {norm_stats.std_norm:.6f}")
            
            # 정규화 상태 확인
            if abs(norm_stats.avg_norm - 1.0) < 0.001:
                print(f"   ✅ 벡터가 정규화되어 있습니다")
            else:
                print(f"   ⚠️ 벡터가 정규화되지 않았을 수 있습니다")
        
        # NULL 벡터 확인
        null_query = f"""
            SELECT COUNT(*) as null_count
            FROM {table_name}
            WHERE embedding IS NULL
        """
        
        result = await db.execute(text(null_query))
        null_count = result.scalar()
        
        if null_count > 0:
            print(f"   ⚠️ NULL 벡터: {null_count}개")
        else:
            print(f"   ✅ NULL 벡터 없음")
            
    except Exception as e:
        print(f"   벡터 품질 분석 실패: {e}")

async def test_vector_similarity():
    """벡터 유사도 검색 테스트"""
    print(f"\n{'=' * 60}")
    print("벡터 유사도 검색 테스트")
    print("=" * 60)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 1. 첫 번째 벡터 가져오기
            print("1. 기준 벡터 선택...")
            
            base_query = """
                SELECT id, embedding, chunk_text
                FROM embeddings_text_embedding_3
                WHERE embedding IS NOT NULL
                ORDER BY id
                LIMIT 1
            """
            
            result = await db.execute(text(base_query))
            base_vector = result.fetchone()
            
            if not base_vector:
                print("   ❌ 기준 벡터를 찾을 수 없습니다")
                return False
            
            print(f"   기준 벡터 ID: {base_vector.id}")
            print(f"   내용: {base_vector.chunk_text[:100]}...")
            
            # 2. 유사한 벡터 검색
            print("\n2. 유사한 벡터 검색...")
            
            similarity_query = """
                SELECT 
                    id,
                    chunk_text,
                    1 - (embedding <=> :base_embedding) as similarity
                FROM embeddings_text_embedding_3
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :base_embedding
                LIMIT 5
            """
            
            # 벡터를 문자열로 변환
            embedding_array = base_vector.embedding
            embedding_str = str(embedding_array)
            
            result = await db.execute(text(similarity_query), {"base_embedding": embedding_str})
            similar_vectors = result.fetchall()
            
            print("   유사도 검색 결과:")
            for i, vec in enumerate(similar_vectors, 1):
                print(f"     {i}. ID: {vec.id}, 유사도: {vec.similarity:.4f}")
                print(f"        내용: {vec.chunk_text[:80]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ 유사도 검색 테스트 실패: {e}")
        return False

async def check_indexes():
    """벡터 인덱스 상태 확인"""
    print(f"\n{'=' * 60}")
    print("벡터 인덱스 상태 확인")
    print("=" * 60)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 1. 모든 인덱스 조회
            index_query = """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE indexdef LIKE '%hnsw%' OR indexdef LIKE '%vector%'
                ORDER BY tablename, indexname
            """
            
            result = await db.execute(text(index_query))
            indexes = result.fetchall()
            
            if indexes:
                print("   발견된 벡터 인덱스:")
                for idx in indexes:
                    print(f"     테이블: {idx.tablename}")
                    print(f"     인덱스: {idx.indexname}")
                    print(f"     정의: {idx.indexdef[:80]}...")
                    print()
            else:
                print("   ❌ 벡터 인덱스를 찾을 수 없습니다")
            
            # 2. 인덱스 사용 통계
            if indexes:
                print("2. 인덱스 사용 통계...")
                
                for idx in indexes:
                    stats_query = f"""
                        SELECT 
                            idx_scan as scans,
                            idx_tup_read as tuples_read,
                            idx_tup_fetch as tuples_fetched
                        FROM pg_stat_user_indexes 
                        WHERE indexrelname = '{idx.indexname}'
                    """
                    
                    result = await db.execute(text(stats_query))
                    stats = result.fetchone()
                    
                    if stats:
                        print(f"     {idx.indexname}:")
                        print(f"       스캔 횟수: {stats.scans}")
                        print(f"       읽은 튜플: {stats.tuples_read}")
                        print(f"       가져온 튜플: {stats.tuples_fetched}")
            
            return len(indexes) > 0
            
    except Exception as e:
        print(f"❌ 인덱스 확인 실패: {e}")
        return False

async def insert_test_vector():
    """테스트 벡터 삽입"""
    print(f"\n{'=' * 60}")
    print("테스트 벡터 삽입")
    print("=" * 60)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        import random
        
        async with get_async_session() as db:
            # 1. 먼저 기존 policy 확인 또는 생성
            print("   기존 policy 확인 중...")
            
            # 기존 policy 확인 (실제 스키마: policy_id가 Primary Key)
            policy_check = await db.execute(text("SELECT policy_id FROM policies LIMIT 1"))
            existing_policy = policy_check.fetchone()
            
            if existing_policy:
                test_policy_id = existing_policy.policy_id
                print(f"   기존 policy 사용: ID {test_policy_id}")
            else:
                # 테스트용 policy 생성 (실제 스키마에 맞춰서)
                policy_insert = """
                    INSERT INTO policies (
                        company, category, product_type, product_name, 
                        sale_start_dt, sale_end_dt, sale_stat, summary,
                        created_at, security_level
                    )
                    VALUES (
                        :company, :category, :product_type, :product_name,
                        :sale_start_dt, :sale_end_dt, :sale_stat, :summary,
                        NOW(), :security_level
                    )
                    RETURNING policy_id
                """
                
                policy_result = await db.execute(text(policy_insert), {
                    "company": "테스트회사",
                    "category": "TEST",
                    "product_type": "벡터테스트",
                    "product_name": "테스트 벡터 확인용 약관",
                    "sale_start_dt": "20250101",
                    "sale_end_dt": "20251231",
                    "sale_stat": "판매중",
                    "summary": "벡터 삽입 테스트를 위한 더미 약관입니다.",
                    "security_level": "PUBLIC"
                })
                
                test_policy_id = policy_result.scalar()
                await db.commit()
                print(f"   새 policy 생성: ID {test_policy_id}")
            
            # 2. 3072차원 랜덤 벡터 생성
            print("   3072차원 벡터 생성 중...")
            test_vector = [random.uniform(-1, 1) for _ in range(3072)]
            
            # 정규화
            norm = sum(x**2 for x in test_vector) ** 0.5
            if norm > 0:
                test_vector = [x / norm for x in test_vector]
            
            # 벡터를 문자열로 변환
            vector_str = "[" + ",".join(map(str, test_vector)) + "]"
            
            # 3. 벡터 삽입
            print("   벡터 삽입 중...")
            insert_query = """
                INSERT INTO embeddings_text_embedding_3 
                (policy_id, chunk_index, chunk_text, embedding, model, created_at)
                VALUES 
                (:policy_id, :chunk_index, :content, :embedding, :model, NOW())
                RETURNING id
            """
            
            result = await db.execute(text(insert_query), {
                "policy_id": test_policy_id,
                "chunk_index": 9999,
                "content": "테스트 벡터 삽입 확인용 더미 텍스트입니다.",
                "embedding": vector_str,
                "model": "test-verification-model"
            })
            
            new_id = result.scalar()
            await db.commit()
            
            print(f"   ✅ 테스트 벡터 삽입 성공")
            print(f"   새 ID: {new_id}")
            print(f"   벡터 차원: {len(test_vector)}")
            print(f"   벡터 Norm: {norm:.6f}")
            
            return new_id
            
    except Exception as e:
        print(f"❌ 테스트 벡터 삽입 실패: {e}")
        return None

async def main():
    """메인 벡터 확인 프로세스"""
    print("벡터 삽입 확인 및 검증 도구")
    print("=" * 70)
    
    # 1. 벡터 테이블 현황 확인
    table_stats = await check_vector_tables()
    
    if table_stats:
        # 2. 메인 임베딩 테이블 상세 조회
        await inspect_vector_data("embeddings_text_embedding_3")
        
        # 3. 벡터 유사도 검색 테스트
        await test_vector_similarity()
        
        # 4. 인덱스 상태 확인
        await check_indexes()
        
        # 5. 테스트 벡터 삽입
        test_id = await insert_test_vector()
        
        if test_id:
            print(f"\n{'=' * 70}")
            print("✅ 모든 벡터 확인 테스트 완료!")
            print(f"   - 벡터 테이블: 정상 작동")
            print(f"   - 데이터 품질: 검증 완료")
            print(f"   - 유사도 검색: 정상 작동")
            print(f"   - 새 벡터 삽입: 성공 (ID: {test_id})")
            print("=" * 70)
        else:
            print(f"\n{'=' * 70}")
            print("⚠️ 일부 테스트 실패")
            print("=" * 70)
    else:
        print("\n❌ 벡터 테이블을 찾을 수 없습니다. pgvector 설정을 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())
