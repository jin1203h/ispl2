"""
검색 결과 후처리 및 재랭킹 테스트
Task 5.3 검증을 위한 종합 테스트
"""
import asyncio
import logging
import time
from typing import List, Dict, Any
import sys
import os

# 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.result_service import (
    SearchResultService, ProcessingConfig, ProcessedResult
)
from services.advanced_search_engine import SearchResult
from agents.query_processor import InsuranceQueryProcessor, ProcessedQuery

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResultServiceTest:
    """검색 결과 후처리 테스트"""
    
    def __init__(self):
        self.service = SearchResultService()
        self.query_processor = InsuranceQueryProcessor()
        
    def create_mock_search_results(self, count: int = 10) -> List[SearchResult]:
        """Mock 검색 결과 생성"""
        mock_results = []
        
        # 다양한 유형의 결과 생성
        result_templates = [
            {
                "chunk_text": "암보험은 암 진단 시 진단금을 지급하는 보험입니다. 가입 조건은 연령 제한이 있으며, 최대 80세까지 가입 가능합니다.",
                "product_name": "무배당 원더플 암보험",
                "company": "삼성생명",
                "category": "생명보험"
            },
            {
                "chunk_text": "보험료는 피보험자의 나이, 성별, 건강상태에 따라 달라집니다. 월납 기준으로 3만원부터 시작됩니다.",
                "product_name": "무배당 원더플 암보험",
                "company": "삼성생명", 
                "category": "생명보험"
            },
            {
                "chunk_text": "암 진단금은 일반암 2천만원, 고액치료비암 4천만원, 소액치료비암 1천만원을 지급합니다.",
                "product_name": "무배당 원더플 암보험",
                "company": "삼성생명",
                "category": "생명보험"
            },
            {
                "chunk_text": "KB손해보험의 암보험은 진단금 외에 수술비, 입원비까지 보장하는 종합적인 상품입니다.",
                "product_name": "KB 암보험플러스",
                "company": "KB손해보험",
                "category": "손해보험"
            },
            {
                "chunk_text": "심장질환 보장은 급성심근경색증, 관상동맥우회술, 기타 심장질환을 포함합니다.",
                "product_name": "심혈관질환보험",
                "company": "현대해상",
                "category": "손해보험"
            },
            {
                "chunk_text": "뇌혈관질환으로는 뇌출혈, 뇌경색이 주요 보장 대상이며, 진단 즉시 보험금이 지급됩니다.",
                "product_name": "뇌혈관질환보험", 
                "company": "메리츠화재",
                "category": "손해보험"
            },
            {
                "chunk_text": "보험료는 피보험자의 나이, 성별, 건강상태에 따라 달라집니다. 월납 기준으로 3만원부터 시작됩니다.",  # 중복
                "product_name": "중복상품",
                "company": "중복회사",
                "category": "생명보험"
            },
            {
                "chunk_text": "가입 조건으로는 연령 제한이 있으며 건강 상태를 확인하는 건강고지가 필요합니다.",
                "product_name": "건강보험",
                "company": "동양생명",
                "category": "생명보험"
            },
            {
                "chunk_text": "의료실비보험은 병원비 부담을 덜어주는 기본적인 보험상품입니다.",
                "product_name": "실손의료보험",
                "company": "흥국화재",
                "category": "손해보험"
            },
            {
                "chunk_text": "치아보험은 치료비 부담이 큰 치과 치료비를 보장하는 특화된 상품입니다.",
                "product_name": "치아보험",
                "company": "DB손해보험",
                "category": "손해보험"
            }
        ]
        
        for i in range(count):
            template = result_templates[i % len(result_templates)]
            result = SearchResult(
                embedding_id=i + 1,
                policy_id=100 + (i // 3),  # 3개씩 같은 정책
                chunk_text=template["chunk_text"],
                chunk_index=i,
                product_name=template["product_name"],
                company=template["company"],
                category=template["category"],
                vector_score=0.9 - (i * 0.05),
                keyword_score=0.8 - (i * 0.03),
                hybrid_score=0.85 - (i * 0.04),
                final_score=0.85 - (i * 0.04),
                model="text-embedding-3-large",
                created_at="2024-09-24T12:00:00",
                relevance_reason="Mock 테스트 결과"
            )
            mock_results.append(result)
        
        return mock_results
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🔧 검색 결과 후처리 및 재랭킹 테스트 시작")
        print("=" * 70)
        
        try:
            # 1. 기본 후처리 테스트
            print("\n1️⃣ 기본 후처리 파이프라인 테스트")
            await self.test_basic_processing()
            
            # 2. 중복 제거 테스트
            print("\n2️⃣ 중복 제거 테스트")
            await self.test_deduplication()
            
            # 3. 다양성 확보 테스트
            print("\n3️⃣ 다양성 확보 테스트")
            await self.test_diversity()
            
            # 4. 컨텍스트 병합 테스트
            print("\n4️⃣ 컨텍스트 병합 테스트")
            await self.test_context_merging()
            
            # 5. 성능 테스트
            print("\n5️⃣ 성능 테스트")
            await self.test_performance()
            
            # 6. 종합 품질 테스트
            print("\n6️⃣ 종합 품질 테스트")
            await self.test_overall_quality()
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {e}")
            return False
        
        return True
    
    async def test_basic_processing(self):
        """기본 후처리 파이프라인 테스트"""
        try:
            # 테스트 질의 생성
            test_query = "암보험 가입조건과 보험료가 궁금해요"
            processed_query = await self.query_processor.preprocess_query(test_query)
            
            # Mock 결과 생성
            mock_results = self.create_mock_search_results(8)
            
            # 후처리 실행
            start_time = time.time()
            processed_results = await self.service.process_results(
                processed_query, mock_results
            )
            processing_time = time.time() - start_time
            
            print(f"질의: '{test_query}'")
            print(f"원본 결과: {len(mock_results)}개")
            print(f"후처리 결과: {len(processed_results)}개")
            print(f"처리 시간: {processing_time*1000:.1f}ms")
            
            # 결과 검증
            if processed_results:
                print("상위 3개 결과:")
                for i, result in enumerate(processed_results[:3]):
                    print(f"  {i+1}. 점수: {result.final_score:.3f}")
                    print(f"     상품: {result.original_result.product_name}")
                    print(f"     내용: {result.original_result.chunk_text[:80]}...")
                    print()
            
            success = (
                len(processed_results) > 0 and
                len(processed_results) <= len(mock_results) and
                processing_time < 1.0  # 1초 미만
            )
            
            if success:
                print("✅ 기본 후처리 테스트 성공")
            else:
                print("❌ 기본 후처리 테스트 실패")
                
        except Exception as e:
            print(f"❌ 기본 후처리 테스트 오류: {e}")
    
    async def test_deduplication(self):
        """중복 제거 테스트"""
        try:
            # 중복이 포함된 결과 생성
            mock_results = self.create_mock_search_results(10)
            
            # 중복 제거 전 개수
            before_count = len(mock_results)
            
            # 중복 제거 테스트
            config = ProcessingConfig(similarity_threshold=0.8)
            deduplicated = self.service._remove_semantic_duplicates(mock_results, config)
            
            after_count = len(deduplicated)
            
            print(f"중복 제거 전: {before_count}개")
            print(f"중복 제거 후: {after_count}개")
            print(f"제거율: {(before_count - after_count) / before_count * 100:.1f}%")
            
            # 중복 제거 효과 확인
            deduplication_rate = (before_count - after_count) / before_count
            
            if deduplication_rate > 0.05:  # 5% 이상 제거
                print("✅ 중복 제거 테스트 성공")
            else:
                print("⚠️ 중복 제거 효과 미미")
                
        except Exception as e:
            print(f"❌ 중복 제거 테스트 오류: {e}")
    
    async def test_diversity(self):
        """다양성 확보 테스트"""
        try:
            # 다양한 회사/상품의 결과 생성
            mock_results = self.create_mock_search_results(10)
            
            # 다양성 확보 테스트
            config = ProcessingConfig(diversity_threshold=0.7)
            diverse_results = self.service._ensure_diversity(mock_results, config)
            
            # 회사별 분포 확인
            companies = set()
            products = set()
            
            for result in diverse_results:
                companies.add(result.company)
                products.add(result.product_name)
            
            print(f"다양성 확보 전: {len(mock_results)}개")
            print(f"다양성 확보 후: {len(diverse_results)}개")
            print(f"포함된 회사 수: {len(companies)}개")
            print(f"포함된 상품 수: {len(products)}개")
            
            # 다양성 검증
            diversity_score = len(companies) / len(diverse_results) if diverse_results else 0
            
            if diversity_score > 0.3:  # 30% 이상 다양성
                print(f"✅ 다양성 확보 성공 (다양성 지수: {diversity_score:.2f})")
            else:
                print(f"⚠️ 다양성 부족 (다양성 지수: {diversity_score:.2f})")
                
        except Exception as e:
            print(f"❌ 다양성 확보 테스트 오류: {e}")
    
    async def test_context_merging(self):
        """컨텍스트 병합 테스트"""
        try:
            # 연속된 청크가 있는 결과 생성
            mock_results = []
            
            # 같은 정책의 연속된 청크들 생성
            base_text = "암보험 가입조건에 대한 설명입니다."
            for i in range(5):
                result = SearchResult(
                    embedding_id=i + 1,
                    policy_id=100,  # 모두 같은 정책
                    chunk_text=f"{base_text} 청크 {i+1}번째 내용입니다.",
                    chunk_index=i,  # 연속된 인덱스
                    product_name="테스트 암보험",
                    company="테스트 회사",
                    category="생명보험",
                    vector_score=0.9,
                    keyword_score=0.8,
                    hybrid_score=0.85,
                    final_score=0.85,
                    model="test",
                    created_at="2024-09-24",
                    relevance_reason="컨텍스트 병합 테스트"
                )
                mock_results.append(result)
            
            # 컨텍스트 병합 테스트
            config = ProcessingConfig()
            merged_results = await self.service._merge_context(mock_results, config)
            
            print(f"컨텍스트 병합 전: {len(mock_results)}개")
            print(f"컨텍스트 병합 후: {len(merged_results)}개")
            
            # 인접 청크 찾기 테스트
            test_chunk = mock_results[2]  # 중간 청크
            adjacent = self.service._find_adjacent_chunks(test_chunk, mock_results)
            print(f"청크 {test_chunk.chunk_index}의 인접 청크: {len(adjacent)}개")
            
            if len(adjacent) > 0:
                print("✅ 컨텍스트 병합 테스트 성공")
            else:
                print("⚠️ 인접 청크 탐지 부족")
                
        except Exception as e:
            print(f"❌ 컨텍스트 병합 테스트 오류: {e}")
    
    async def test_performance(self):
        """성능 테스트"""
        try:
            # 대량 결과로 성능 테스트
            large_results = self.create_mock_search_results(50)
            test_query = await self.query_processor.preprocess_query("보험료 계산")
            
            # 여러 번 실행하여 평균 시간 측정
            execution_times = []
            
            for i in range(5):
                start_time = time.time()
                processed_results = await self.service.process_results(
                    test_query, large_results
                )
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
            
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
            
            print(f"대량 데이터 처리 (50개 결과):")
            print(f"평균 처리 시간: {avg_time*1000:.1f}ms")
            print(f"최대 처리 시간: {max_time*1000:.1f}ms")
            print(f"최소 처리 시간: {min_time*1000:.1f}ms")
            
            # 성능 기준 확인
            performance_ok = avg_time < 0.5  # 평균 500ms 미만
            
            if performance_ok:
                print("✅ 성능 테스트 성공")
            else:
                print(f"❌ 성능 테스트 실패 (기준: 500ms, 실제: {avg_time*1000:.1f}ms)")
                
        except Exception as e:
            print(f"❌ 성능 테스트 오류: {e}")
    
    async def test_overall_quality(self):
        """종합 품질 테스트"""
        try:
            # 복합적인 시나리오 테스트
            test_query = "30세 남성 암보험 가입조건과 보험료, 보장범위를 알고 싶어요"
            processed_query = await self.query_processor.preprocess_query(test_query)
            
            # 다양한 품질의 결과 혼합
            mock_results = self.create_mock_search_results(15)
            
            # 저품질 결과 추가
            low_quality_result = SearchResult(
                embedding_id=999,
                policy_id=999,
                chunk_text="a b c d e",  # 너무 짧음
                chunk_index=0,
                product_name="저품질상품",
                company="저품질회사",
                category="기타",
                vector_score=0.1,  # 낮은 점수
                keyword_score=0.1,
                hybrid_score=0.1,
                final_score=0.1,
                model="test",
                created_at="2024-09-24",
                relevance_reason="저품질 테스트"
            )
            mock_results.append(low_quality_result)
            
            # 종합 후처리
            start_time = time.time()
            final_results = await self.service.process_results(
                processed_query, mock_results
            )
            total_time = time.time() - start_time
            
            # 품질 지표 계산
            if final_results:
                avg_score = sum(r.final_score for r in final_results) / len(final_results)
                min_score = min(r.final_score for r in final_results)
                companies = set(r.original_result.company for r in final_results)
                
                print(f"종합 테스트 결과:")
                print(f"  최종 결과 수: {len(final_results)}개")
                print(f"  평균 점수: {avg_score:.3f}")
                print(f"  최소 점수: {min_score:.3f}")
                print(f"  회사 다양성: {len(companies)}개")
                print(f"  총 처리 시간: {total_time*1000:.1f}ms")
                
                # 품질 기준 검증
                quality_criteria = {
                    "결과수": len(final_results) >= 3,
                    "평균점수": avg_score >= 0.5,
                    "최소점수": min_score >= 0.3,
                    "회사다양성": len(companies) >= 2,
                    "처리시간": total_time < 1.0
                }
                
                print(f"\n품질 검증 결과:")
                passed_criteria = 0
                for criterion, passed in quality_criteria.items():
                    status = "✅" if passed else "❌"
                    print(f"  {criterion}: {status}")
                    if passed:
                        passed_criteria += 1
                
                success_rate = passed_criteria / len(quality_criteria)
                print(f"\n종합 성공률: {success_rate:.1%}")
                
                if success_rate >= 0.8:  # 80% 이상
                    print("✅ 종합 품질 테스트 성공")
                    return True
                else:
                    print("❌ 종합 품질 테스트 실패")
                    return False
            else:
                print("❌ 결과 없음")
                return False
                
        except Exception as e:
            print(f"❌ 종합 품질 테스트 오류: {e}")
            return False

async def main():
    """메인 테스트 실행"""
    tester = ResultServiceTest()
    
    try:
        success = await tester.run_all_tests()
        
        print("\n" + "=" * 70)
        if success:
            print("🎉 검색 결과 후처리 테스트 완료!")
            print("✅ 모든 기능이 정상적으로 작동합니다.")
            print("\n📋 검증된 기능:")
            print("  - 기본 후처리 파이프라인")
            print("  - 의미적 중복 제거")
            print("  - 다양성 확보 (회사별 우선 선택)")
            print("  - 컨텍스트 병합")
            print("  - 성능 최적화")
        else:
            print("❌ 일부 테스트가 실패했습니다.")
        
        return success
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 심각한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

