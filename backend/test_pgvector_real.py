"""
실제 pgvector 기능 테스트
HNSW 인덱스 생성, 벡터 삽입, 검색 성능 실제 측정
"""
import asyncio
import time
import logging
from typing import List
import random

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vector_operations():
    """실제 벡터 연산 테스트"""
    print("=" * 60)
    print("실제 pgvector 벡터 연산 테스트")
    print("=" * 60)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 1. 벡터 생성 및 삽입 테스트
            print("1. 벡터 생성 및 삽입 테스트...")
            
            # 간단한 3차원 벡터로 테스트 (빠른 실행을 위해)
            test_vectors = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0], 
                [0.0, 0.0, 1.0],
                [0.5, 0.5, 0.5],
                [0.8, 0.1, 0.1]
            ]
            
            # 테스트용 임시 테이블 생성
            create_table_sql = """
                CREATE TEMP TABLE test_vectors (
                    id SERIAL PRIMARY KEY,
                    embedding vector(3),
                    description TEXT
                )
            """
            await db.execute(text(create_table_sql))
            
            # 벡터 삽입
            for i, vec in enumerate(test_vectors):
                # 벡터를 문자열로 변환
                vec_str = "[" + ",".join(map(str, vec)) + "]"
                insert_sql = """
                    INSERT INTO test_vectors (embedding, description) 
                    VALUES (:embedding, :description)
                """
                await db.execute(text(insert_sql), {
                    "embedding": vec_str,
                    "description": f"테스트 벡터 {i+1}"
                })
            
            await db.commit()
            print(f"   ✅ {len(test_vectors)}개 벡터 삽입 완료")
            
            # 2. 벡터 유사도 검색 테스트
            print("2. 벡터 유사도 검색 테스트...")
            
            query_vector = [1.0, 0.0, 0.0]  # 첫 번째 벡터와 동일
            query_vector_str = "[" + ",".join(map(str, query_vector)) + "]"
            
            similarity_sql = """
                SELECT 
                    id,
                    description,
                    embedding,
                    1 - (embedding <=> :query_vector) as similarity
                FROM test_vectors 
                ORDER BY embedding <=> :query_vector
                LIMIT 3
            """
            
            start_time = time.time()
            result = await db.execute(text(similarity_sql), {"query_vector": query_vector_str})
            search_time = (time.time() - start_time) * 1000  # ms
            
            rows = result.fetchall()
            
            print(f"   쿼리 벡터: {query_vector}")
            print(f"   검색 시간: {search_time:.2f}ms")
            print("   검색 결과:")
            
            for row in rows:
                print(f"     ID: {row.id}, 설명: {row.description}, 유사도: {row.similarity:.4f}")
            
            return True
            
    except Exception as e:
        print(f"❌ 벡터 연산 테스트 실패: {e}")
        return False

async def test_index_creation():
    """실제 HNSW 인덱스 생성 테스트"""
    print("\n" + "=" * 60)
    print("실제 HNSW 인덱스 생성 테스트")
    print("=" * 60)
    
    try:
        from services.database import get_async_session
        from sqlalchemy import text
        
        async with get_async_session() as db:
            # 1. 기존 인덱스 확인
            print("1. 기존 인덱스 상태 확인...")
            
            index_check_sql = """
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'embeddings_text_embedding_3'
                AND indexname LIKE '%hnsw%'
            """
            
            result = await db.execute(text(index_check_sql))
            existing_indexes = result.fetchall()
            
            if existing_indexes:
                print("   기존 HNSW 인덱스:")
                for idx in existing_indexes:
                    print(f"     - {idx.indexname}")
            else:
                print("   기존 HNSW 인덱스 없음")
            
            # 2. 작은 테스트 인덱스 생성
            print("2. 테스트용 HNSW 인덱스 생성...")
            
            # 테스트용 작은 테이블 생성 (빠른 인덱스 생성을 위해)
            create_test_table_sql = """
                CREATE TEMP TABLE test_hnsw (
                    id SERIAL PRIMARY KEY,
                    embedding vector(128)  -- 작은 차원으로 테스트
                )
            """
            await db.execute(text(create_test_table_sql))
            
            # 테스트 데이터 삽입 (100개 정도)
            print("   테스트 데이터 삽입 중...")
            for i in range(100):
                # 랜덤 벡터 생성
                vec = [random.uniform(-1, 1) for _ in range(128)]
                # 정규화
                norm = sum(x**2 for x in vec) ** 0.5
                if norm > 0:
                    vec = [x / norm for x in vec]
                
                # 벡터를 문자열로 변환
                vec_str = "[" + ",".join(map(str, vec)) + "]"
                insert_sql = "INSERT INTO test_hnsw (embedding) VALUES (:embedding)"
                await db.execute(text(insert_sql), {"embedding": vec_str})
            
            await db.commit()
            print(f"   ✅ 100개 테스트 벡터 삽입 완료")
            
            # HNSW 인덱스 생성
            print("   HNSW 인덱스 생성 중...")
            start_time = time.time()
            
            create_index_sql = """
                CREATE INDEX test_hnsw_idx 
                ON test_hnsw 
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """
            
            await db.execute(text(create_index_sql))
            await db.commit()
            
            index_creation_time = time.time() - start_time
            print(f"   ✅ HNSW 인덱스 생성 완료 ({index_creation_time:.2f}초)")
            
            # 3. 인덱스를 사용한 검색 성능 테스트
            print("3. 인덱스 성능 테스트...")
            
            # ef_search 설정
            await db.execute(text("SET hnsw.ef_search = 40"))
            
            query_vec = [random.uniform(-1, 1) for _ in range(128)]
            norm = sum(x**2 for x in query_vec) ** 0.5
            if norm > 0:
                query_vec = [x / norm for x in query_vec]
            
            # 쿼리 벡터를 문자열로 변환
            query_vec_str = "[" + ",".join(map(str, query_vec)) + "]"
            
            # 여러 번 검색해서 평균 시간 측정
            search_times = []
            for _ in range(10):
                start_time = time.time()
                
                search_sql = """
                    SELECT id, 1 - (embedding <=> :query_vector) as similarity
                    FROM test_hnsw 
                    ORDER BY embedding <=> :query_vector
                    LIMIT 5
                """
                
                result = await db.execute(text(search_sql), {"query_vector": query_vec_str})
                rows = result.fetchall()
                
                search_time = (time.time() - start_time) * 1000
                search_times.append(search_time)
            
            avg_search_time = sum(search_times) / len(search_times)
            print(f"   평균 검색 시간: {avg_search_time:.2f}ms (10회 평균)")
            print(f"   검색된 결과 수: {len(rows)}")
            
            return {
                "index_creation_time": index_creation_time,
                "avg_search_time": avg_search_time,
                "data_count": 100
            }
            
    except Exception as e:
        print(f"❌ 인덱스 생성 테스트 실패: {e}")
        return None

async def test_optimized_service():
    """최적화된 벡터 저장소 서비스 실제 테스트"""
    print("\n" + "=" * 60)
    print("최적화된 벡터 저장소 서비스 실제 테스트")
    print("=" * 60)
    
    try:
        from services.optimized_vector_store import OptimizedVectorStoreService, IndexConfig
        from services.database import get_async_session
        
        # 서비스 초기화
        index_config = IndexConfig(m=16, ef_construction=64, ef_search=40)
        service = OptimizedVectorStoreService(
            embedding_model="test-real-embedding",
            index_config=index_config
        )
        
        async with get_async_session() as db:
            # 1. 인덱스 성능 분석 실제 실행
            print("1. 실제 인덱스 성능 분석...")
            
            analysis_result = await service.analyze_index_performance(db)
            
            if "error" not in analysis_result:
                print("   ✅ 인덱스 성능 분석 성공")
                
                table_perf = analysis_result.get("table_performance", {})
                for table_name, perf_data in table_perf.items():
                    if "error" not in perf_data:
                        print(f"     {table_name}:")
                        print(f"       - 테이블 크기: {perf_data.get('table_size', 'N/A')}")
                        print(f"       - 인덱스 크기: {perf_data.get('index_size', 'N/A')}")
                        print(f"       - 레코드 수: {perf_data.get('row_count', 'N/A')}")
                        print(f"       - 인덱스 존재: {perf_data.get('index_exists', 'N/A')}")
            else:
                print(f"   ❌ 인덱스 성능 분석 실패: {analysis_result['error']}")
            
            # 2. 최적화 권장사항 생성
            print("2. 최적화 권장사항 생성...")
            
            recommendations = service.get_optimization_recommendations()
            print(f"   생성된 권장사항: {len(recommendations)}개")
            
            for i, rec in enumerate(recommendations, 1):
                print(f"     {i}. {rec}")
            
            return True
            
    except Exception as e:
        print(f"❌ 최적화된 서비스 테스트 실패: {e}")
        return False

async def main():
    """메인 실제 테스트 실행"""
    print("실제 pgvector 기능 테스트 시작")
    print("=" * 70)
    
    test_results = {}
    
    # 1. 벡터 연산 테스트
    vector_result = await test_vector_operations()
    test_results["vector_operations"] = vector_result
    
    if vector_result:
        # 2. 인덱스 생성 테스트
        index_result = await test_index_creation()
        test_results["index_creation"] = index_result
        
        # 3. 최적화된 서비스 테스트
        service_result = await test_optimized_service()
        test_results["optimized_service"] = service_result
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("실제 테스트 결과 요약")
    print("=" * 70)
    
    for test_name, result in test_results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        
        if test_name == "index_creation" and isinstance(result, dict):
            print(f"  - 인덱스 생성 시간: {result['index_creation_time']:.2f}초")
            print(f"  - 평균 검색 시간: {result['avg_search_time']:.2f}ms")
            print(f"  - 테스트 데이터: {result['data_count']}개")
    
    # 전체 성공 여부
    overall_success = all(test_results.values())
    print(f"\n전체 실제 테스트: {'✅ 성공' if overall_success else '❌ 실패'}")
    
    if overall_success:
        print("\n🎉 모든 실제 pgvector 기능이 정상 작동합니다!")
    else:
        print("\n⚠️ 일부 기능에 문제가 있습니다. 로그를 확인해주세요.")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())
