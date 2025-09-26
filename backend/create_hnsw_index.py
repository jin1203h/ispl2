"""
실제 HNSW 인덱스 생성 도구
embeddings_text_embedding_3 테이블에 HNSW 인덱스를 생성합니다.
"""
import asyncio
from services.database import get_async_session
from sqlalchemy import text

async def create_hnsw_index():
    """실제 HNSW 인덱스 생성"""
    print("=" * 60)
    print("HNSW 인덱스 생성")
    print("=" * 60)
    
    try:
        async with get_async_session() as db:
            # 1. 기존 인덱스 확인
            print("1. 기존 인덱스 확인...")
            
            check_index_query = """
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'embeddings_text_embedding_3' 
                AND indexname LIKE '%hnsw%'
            """
            
            result = await db.execute(text(check_index_query))
            existing_indexes = result.fetchall()
            
            if existing_indexes:
                print("   기존 HNSW 인덱스:")
                for idx in existing_indexes:
                    print(f"     - {idx.indexname}")
                return True
            else:
                print("   기존 HNSW 인덱스 없음")
            
            # 2. 테이블 데이터 확인
            print("\n2. 테이블 데이터 확인...")
            
            count_query = "SELECT COUNT(*) FROM embeddings_text_embedding_3"
            result = await db.execute(text(count_query))
            row_count = result.scalar()
            
            print(f"   레코드 수: {row_count}개")
            
            if row_count == 0:
                print("   ⚠️ 테이블에 데이터가 없습니다. 먼저 벡터 데이터를 삽입해주세요.")
                return False
            
            # 3. HNSW 인덱스 생성
            print("\n3. HNSW 인덱스 생성 중...")
            print("   (대량 데이터의 경우 시간이 오래 걸릴 수 있습니다)")
            
            create_index_query = """
                CREATE INDEX embeddings_text_embedding_3_hnsw_idx 
                ON embeddings_text_embedding_3 
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """
            
            import time
            start_time = time.time()
            
            await db.execute(text(create_index_query))
            await db.commit()
            
            creation_time = time.time() - start_time
            
            print(f"   ✅ HNSW 인덱스 생성 완료!")
            print(f"   생성 시간: {creation_time:.2f}초")
            print(f"   인덱스명: embeddings_text_embedding_3_hnsw_idx")
            
            # 4. 인덱스 확인
            print("\n4. 생성된 인덱스 확인...")
            
            verify_query = """
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename = 'embeddings_text_embedding_3' 
                AND indexname = 'embeddings_text_embedding_3_hnsw_idx'
            """
            
            result = await db.execute(text(verify_query))
            index_info = result.fetchone()
            
            if index_info:
                print(f"   인덱스명: {index_info.indexname}")
                print(f"   정의: {index_info.indexdef}")
                return True
            else:
                print("   ❌ 인덱스 생성 실패")
                return False
                
    except Exception as e:
        print(f"❌ HNSW 인덱스 생성 실패: {e}")
        return False

async def test_index_performance():
    """인덱스 성능 테스트"""
    print("\n" + "=" * 60)
    print("인덱스 성능 테스트")
    print("=" * 60)
    
    try:
        async with get_async_session() as db:
            # 1. ef_search 설정
            await db.execute(text("SET hnsw.ef_search = 40"))
            
            # 2. 첫 번째 벡터 가져오기
            base_query = """
                SELECT embedding 
                FROM embeddings_text_embedding_3 
                LIMIT 1
            """
            
            result = await db.execute(text(base_query))
            base_vector = result.fetchone()
            
            if not base_vector:
                print("   ❌ 테스트할 벡터가 없습니다")
                return False
            
            # 3. 성능 측정
            import time
            
            search_query = """
                SELECT id, 1 - (embedding <=> :query_vector) as similarity
                FROM embeddings_text_embedding_3 
                ORDER BY embedding <=> :query_vector
                LIMIT 10
            """
            
            embedding_str = str(base_vector.embedding)
            
            # 여러 번 실행해서 평균 측정
            times = []
            for i in range(5):
                start_time = time.time()
                result = await db.execute(text(search_query), {"query_vector": embedding_str})
                results = result.fetchall()
                search_time = (time.time() - start_time) * 1000
                times.append(search_time)
                
                if i == 0:  # 첫 번째 결과만 출력
                    print(f"   검색 결과: {len(results)}개")
                    for j, row in enumerate(results[:3], 1):
                        print(f"     {j}. ID: {row.id}, 유사도: {row.similarity:.4f}")
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\n   성능 통계 (5회 측정):")
            print(f"     평균: {avg_time:.2f}ms")
            print(f"     최소: {min_time:.2f}ms")
            print(f"     최대: {max_time:.2f}ms")
            
            return True
            
    except Exception as e:
        print(f"❌ 성능 테스트 실패: {e}")
        return False

async def main():
    """메인 실행"""
    print("실제 HNSW 인덱스 생성 및 성능 테스트")
    print("=" * 70)
    
    # 1. HNSW 인덱스 생성
    index_created = await create_hnsw_index()
    
    if index_created:
        # 2. 성능 테스트
        performance_tested = await test_index_performance()
        
        if performance_tested:
            print(f"\n{'=' * 70}")
            print("✅ HNSW 인덱스 생성 및 성능 테스트 완료!")
            print("   - 인덱스 생성: 성공")
            print("   - 성능 테스트: 성공")
            print("   이제 벡터 검색이 최적화되었습니다!")
            print("=" * 70)
        else:
            print(f"\n{'=' * 70}")
            print("⚠️ 인덱스는 생성되었지만 성능 테스트 실패")
            print("=" * 70)
    else:
        print(f"\n{'=' * 70}")
        print("❌ HNSW 인덱스 생성 실패")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())

