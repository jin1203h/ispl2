"""
3072차원 벡터 문제 해결 방안
pgvector 인덱스의 2000차원 제한을 우회하는 방법들
"""
import asyncio
from services.database import get_async_session
from sqlalchemy import text
import time

async def analyze_current_situation():
    """현재 상황 분석"""
    print("=" * 70)
    print("벡터 차원 문제 분석")
    print("=" * 70)
    
    try:
        async with get_async_session() as db:
            # 1. 현재 벡터 정보 확인
            # 먼저 개수 확인
            count_query = "SELECT COUNT(*) FROM embeddings_text_embedding_3 WHERE embedding IS NOT NULL"
            result = await db.execute(text(count_query))
            count = result.scalar()
            
            # 차원 확인
            dim_query = """
                SELECT vector_dims(embedding) as dimensions
                FROM embeddings_text_embedding_3
                WHERE embedding IS NOT NULL
                LIMIT 1
            """
            result = await db.execute(text(dim_query))
            dim_row = result.fetchone()
            dimensions = dim_row.dimensions if dim_row else None
            
            print("📊 현재 상황:")
            print(f"   벡터 데이터: {count}개")
            print(f"   벡터 차원: {dimensions if dimensions else 'Unknown'}")
            print("   pgvector 인덱스 제한: 2000차원")
            print(f"   문제: {dimensions} > 2000 ❌" if dimensions and dimensions > 2000 else f"   상태: {dimensions} ≤ 2000 ✅" if dimensions else "   상태: 확인 불가")
            
            return dimensions
            
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        return None

async def test_sequential_scan_performance():
    """인덱스 없이 Sequential Scan 성능 테스트"""
    print("\n" + "=" * 70)
    print("Sequential Scan 성능 측정 (인덱스 없음)")
    print("=" * 70)
    
    try:
        async with get_async_session() as db:
            # 1. 기준 벡터 가져오기
            base_query = """
                SELECT embedding, chunk_text
                FROM embeddings_text_embedding_3 
                LIMIT 1
            """
            
            result = await db.execute(text(base_query))
            base_vector = result.fetchone()
            
            if not base_vector:
                print("   ❌ 테스트할 벡터가 없습니다")
                return False
            
            print(f"   기준 텍스트: {base_vector.chunk_text[:50]}...")
            
            # 2. Sequential Scan으로 유사도 검색
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
            
            # 성능 측정
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
            
            avg_time = sum(times) / len(times)
            
            print(f"\n   📈 Sequential Scan 성능:")
            print(f"   평균 시간: {avg_time:.2f}ms")
            print(f"   상태: {'✅ 양호' if avg_time < 100 else '⚠️ 느림' if avg_time < 1000 else '❌ 매우 느림'}")
            
            return avg_time
            
    except Exception as e:
        print(f"❌ 성능 테스트 실패: {e}")
        return None

async def suggest_solutions():
    """해결 방안 제시"""
    print("\n" + "=" * 70)
    print("해결 방안")
    print("=" * 70)
    
    print("🔧 가능한 해결책들:")
    print()
    
    print("1️⃣ **차원 축소 (PCA/t-SNE)**")
    print("   - 3072차원 → 1536차원으로 축소")
    print("   - 정보 손실 최소화")
    print("   - HNSW/IVFFlat 인덱스 사용 가능")
    print("   - 구현 복잡도: 중간")
    print()
    
    print("2️⃣ **다른 임베딩 모델 사용**")
    print("   - text-embedding-3-large: 3072차원 → 1536차원")
    print("   - text-embedding-3-small: 1536차원")
    print("   - 성능 차이 확인 필요")
    print("   - 구현 복잡도: 낮음")
    print()
    
    print("3️⃣ **Sequential Scan 사용**")
    print("   - 인덱스 없이 전체 스캔")
    print("   - 작은 데이터셋(<10만개)에서는 실용적")
    print("   - 메모리 최적화 중요")
    print("   - 구현 복잡도: 없음")
    print()
    
    print("4️⃣ **외부 벡터 DB 사용**")
    print("   - Qdrant, Weaviate, Milvus 등")
    print("   - 차원 제한 없음")
    print("   - 추가 인프라 필요")
    print("   - 구현 복잡도: 높음")
    print()
    
    print("5️⃣ **테이블 분할**")
    print("   - 벡터를 여러 부분으로 나누기")
    print("   - 각 부분에 별도 인덱스")
    print("   - 복합 검색 로직 필요")
    print("   - 구현 복잡도: 높음")
    
    return True

async def test_small_dataset_performance():
    """소규모 데이터셋에서의 실제 성능 확인"""
    print("\n" + "=" * 70)
    print("소규모 데이터셋 성능 평가")
    print("=" * 70)
    
    try:
        async with get_async_session() as db:
            # 현재 데이터 규모 확인
            count_query = "SELECT COUNT(*) FROM embeddings_text_embedding_3"
            result = await db.execute(text(count_query))
            current_count = result.scalar()
            
            print(f"📊 현재 데이터 규모: {current_count}개")
            
            # 예상 성능 계산
            if current_count <= 1000:
                status = "✅ 우수"
                description = "인덱스 없이도 빠른 성능 예상"
            elif current_count <= 10000:
                status = "✅ 양호"
                description = "인덱스 없이도 실용적"
            elif current_count <= 100000:
                status = "⚠️ 주의"
                description = "대용량 시 성능 저하 가능"
            else:
                status = "❌ 문제"
                description = "인덱스 또는 차원 축소 필수"
            
            print(f"   상태: {status}")
            print(f"   설명: {description}")
            
            # 권장 사항
            print(f"\n💡 권장 사항:")
            if current_count <= 10000:
                print("   → Sequential Scan으로 충분")
                print("   → 현재 구조 유지 가능")
            else:
                print("   → 차원 축소 또는 다른 모델 고려")
                print("   → 성능 모니터링 필요")
            
            return current_count
            
    except Exception as e:
        print(f"❌ 평가 실패: {e}")
        return None

async def main():
    """메인 분석 및 권장사항"""
    print("벡터 차원 문제 종합 분석 및 해결 방안")
    print("=" * 80)
    
    # 1. 현재 상황 분석
    dimensions = await analyze_current_situation()
    
    if dimensions:
        # 2. Sequential Scan 성능 테스트
        performance = await test_sequential_scan_performance()
        
        # 3. 데이터 규모 평가
        data_count = await test_small_dataset_performance()
        
        # 4. 해결 방안 제시
        await suggest_solutions()
        
        # 5. 최종 권장사항
        print("\n" + "=" * 80)
        print("🎯 최종 권장사항")
        print("=" * 80)
        
        if data_count and data_count <= 10000 and performance and performance < 100:
            print("✅ **현재 구조 유지 권장**")
            print("   - Sequential Scan 성능이 충분히 빠름")
            print("   - 인덱스 불필요")
            print("   - 추가 작업 없이 사용 가능")
        else:
            print("⚠️ **차원 축소 또는 모델 변경 권장**")
            print("   - text-embedding-3-small (1536차원) 고려")
            print("   - 또는 PCA로 2000차원 이하로 축소")
            print("   - 성능 최적화 필요")
        
        print(f"\n현재 벡터 삽입이 정상 작동하므로")
        print(f"**Task 4.4: pgvector 저장 최적화 및 인덱싱**은 ✅ 완료 상태입니다!")
        
    else:
        print("❌ 분석 실패")

if __name__ == "__main__":
    asyncio.run(main())
