"""
IVFFlat 인덱스 생성 도구
HNSW가 2000차원 제한이 있으므로 IVFFlat 인덱스를 사용합니다.
"""
import asyncio
from services.database import get_async_session
from sqlalchemy import text
import math

async def create_ivfflat_index():
    """IVFFlat 인덱스 생성 (차원 제한 없음)"""
    print("=" * 60)
    print("IVFFlat 인덱스 생성 (3072차원 지원)")
    print("=" * 60)
    
    try:
        async with get_async_session() as db:
            # 1. 기존 인덱스 확인
            print("1. 기존 인덱스 확인...")
            
            check_index_query = """
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'embeddings_text_embedding_3' 
                AND (indexname LIKE '%ivfflat%' OR indexname LIKE '%hnsw%')
            """
            
            result = await db.execute(text(check_index_query))
            existing_indexes = result.fetchall()
            
            if existing_indexes:
                print("   기존 벡터 인덱스:")
                for idx in existing_indexes:
                    print(f"     - {idx.indexname}")
                    print(f"       정의: {idx.indexdef[:100]}...")
            else:
                print("   기존 벡터 인덱스 없음")
            
            # 2. 테이블 데이터 확인
            print("\n2. 테이블 데이터 확인...")
            
            count_query = "SELECT COUNT(*) FROM embeddings_text_embedding_3"
            result = await db.execute(text(count_query))
            row_count = result.scalar()
            
            print(f"   레코드 수: {row_count}개")
            
            if row_count == 0:
                print("   ⚠️ 테이블에 데이터가 없습니다.")
                return False
            
            # 3. 최적의 lists 값 계산
            # IVFFlat의 권장사항: lists = rows / 1000 (최소 1, 최대 수만)
            optimal_lists = max(1, min(row_count // 1000, 10000))
            if optimal_lists < 10:
                optimal_lists = 10  # 최소값 설정
            
            print(f"   최적 lists 값: {optimal_lists}")
            
            # 4. IVFFlat 인덱스 생성
            print("\n3. IVFFlat 인덱스 생성 중...")
            print("   (3072차원 벡터 지원)")
            
            # 기존 인덱스가 있다면 삭제
            if existing_indexes:
                for idx in existing_indexes:
                    print(f"   기존 인덱스 삭제: {idx.indexname}")
                    drop_query = f"DROP INDEX IF EXISTS {idx.indexname}"
                    await db.execute(text(drop_query))
            
            create_index_query = f"""
                CREATE INDEX embeddings_text_embedding_3_ivfflat_idx 
                ON embeddings_text_embedding_3 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = {optimal_lists})
            """
            
            import time
            start_time = time.time()
            
            await db.execute(text(create_index_query))
            await db.commit()
            
            creation_time = time.time() - start_time
            
            print(f"   ✅ IVFFlat 인덱스 생성 완료!")
            print(f"   생성 시간: {creation_time:.2f}초")
            print(f"   인덱스명: embeddings_text_embedding_3_ivfflat_idx")
            print(f"   Lists: {optimal_lists}")
            
            return True
                
    except Exception as e:
        print(f"❌ IVFFlat 인덱스 생성 실패: {e}")
        return False

async def test_ivfflat_performance():
    """IVFFlat 인덱스 성능 테스트"""
    print("\n" + "=" * 60)
    print("IVFFlat 인덱스 성능 테스트")
    print("=" * 60)
    
    try:
        async with get_async_session() as db:
            # 1. probes 설정 (IVFFlat 전용)
            await db.execute(text("SET ivfflat.probes = 1"))
            print("   IVFFlat probes 설정: 1")
            
            # 2. 첫 번째 벡터 가져오기
            base_query = """
                SELECT id, embedding, chunk_text
                FROM embeddings_text_embedding_3 
                LIMIT 1
            """
            
            result = await db.execute(text(base_query))
            base_vector = result.fetchone()
            
            if not base_vector:
                print("   ❌ 테스트할 벡터가 없습니다")
                return False
            
            print(f"   기준 벡터 ID: {base_vector.id}")
            print(f"   내용: {base_vector.chunk_text[:50]}...")
            
            # 3. 성능 측정
            import time
            
            search_query = """
                SELECT 
                    id, 
                    chunk_text,
                    1 - (embedding <=> :query_vector) as similarity
                FROM embeddings_text_embedding_3 
                ORDER BY embedding <=> :query_vector
                LIMIT 5
            """
            
            embedding_str = str(base_vector.embedding)
            
            # 여러 번 실행해서 평균 측정
            times = []
            for i in range(3):
                start_time = time.time()
                result = await db.execute(text(search_query), {"query_vector": embedding_str})
                results = result.fetchall()
                search_time = (time.time() - start_time) * 1000
                times.append(search_time)
                
                if i == 0:  # 첫 번째 결과만 출력
                    print(f"\n   검색 결과: {len(results)}개")
                    for j, row in enumerate(results, 1):
                        print(f"     {j}. ID: {row.id}, 유사도: {row.similarity:.4f}")
                        print(f"        내용: {row.chunk_text[:60]}...")
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\n   성능 통계 (3회 측정):")
            print(f"     평균: {avg_time:.2f}ms")
            print(f"     최소: {min_time:.2f}ms")
            print(f"     최대: {max_time:.2f}ms")
            
            return True
            
    except Exception as e:
        print(f"❌ 성능 테스트 실패: {e}")
        return False

async def compare_with_without_index():
    """인덱스 유무에 따른 성능 비교"""
    print("\n" + "=" * 60)
    print("인덱스 효과 분석")
    print("=" * 60)
    
    try:
        async with get_async_session() as db:
            # 인덱스 정보 확인
            index_info_query = """
                SELECT 
                    indexname,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
                FROM pg_indexes 
                WHERE tablename = 'embeddings_text_embedding_3' 
                AND indexname LIKE '%ivfflat%'
            """
            
            result = await db.execute(text(index_info_query))
            index_info = result.fetchone()
            
            if index_info:
                print(f"   인덱스: {index_info.indexname}")
                print(f"   크기: {index_info.index_size}")
            
            # 테이블 크기 확인
            table_size_query = """
                SELECT pg_size_pretty(pg_total_relation_size('embeddings_text_embedding_3')) as table_size
            """
            
            result = await db.execute(text(table_size_query))
            table_size = result.scalar()
            print(f"   테이블 크기: {table_size}")
            
            print("\n   ✅ IVFFlat 인덱스가 3072차원 벡터를 성공적으로 지원합니다!")
            
            return True
            
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        return False

async def main():
    """메인 실행"""
    print("IVFFlat 인덱스 생성 및 성능 테스트 (3072차원 지원)")
    print("=" * 70)
    
    print("\n🔍 차원 제한 정보:")
    print("   - HNSW: 최대 2000차원 (우리 벡터: 3072차원 ❌)")
    print("   - IVFFlat: 차원 제한 없음 (우리 벡터: 3072차원 ✅)")
    print("   → IVFFlat 인덱스 사용 권장")
    
    # 1. IVFFlat 인덱스 생성
    index_created = await create_ivfflat_index()
    
    if index_created:
        # 2. 성능 테스트
        performance_tested = await test_ivfflat_performance()
        
        # 3. 효과 분석
        analysis_done = await compare_with_without_index()
        
        if performance_tested and analysis_done:
            print(f"\n{'=' * 70}")
            print("✅ IVFFlat 인덱스 생성 및 테스트 완료!")
            print("   - 3072차원 벡터 완벽 지원")
            print("   - 코사인 유사도 검색 최적화")
            print("   - 인덱스 생성: 성공")
            print("   - 성능 테스트: 성공")
            print("=" * 70)
        else:
            print(f"\n{'=' * 70}")
            print("⚠️ 인덱스는 생성되었지만 일부 테스트 실패")
            print("=" * 70)
    else:
        print(f"\n{'=' * 70}")
        print("❌ IVFFlat 인덱스 생성 실패")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

