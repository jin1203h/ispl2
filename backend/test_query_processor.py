"""
자연어 질의 전처리 시스템 테스트
Task 5.1 검증을 위한 종합 테스트
"""
import asyncio
import logging
import time
from typing import List, Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_query_preprocessing():
    """질의 전처리 테스트"""
    print("=" * 60)
    print("Task 5.1: 자연어 질의 전처리 및 의도 분석 테스트")
    print("=" * 60)
    
    try:
        from agents.query_processor import InsuranceQueryProcessor, QueryIntent
        
        processor = InsuranceQueryProcessor()
        
        # 테스트 질의들
        test_queries = [
            # 정보 검색 질의
            "골절 수술비는 얼마나 보장되나요?",
            "암 보험에서 지급되는 보험금을 알려주세요",
            "입원비 특약이 무엇인지 설명해주세요",
            
            # 비교 질의
            "A 보험과 B 보험의 차이점이 뭔가요?",
            "암 보험과 종합 보험 중 어느 것이 좋을까요?",
            
            # 계산 질의
            "30세 남성의 월 보험료는 얼마인가요?",
            "100만원 수술비에서 자기부담금을 계산해주세요",
            
            # 설명 요청
            "보험금 청구 절차를 설명해주세요",
            "어떻게 보험에 가입할 수 있나요?",
            
            # 신청/가입
            "암 보험에 가입하고 싶습니다",
            "특약을 추가로 신청하려고 합니다",
            
            # 변경/수정
            "보험 계약을 변경하고 싶어요",
            "보험을 해지하려면 어떻게 해야 하나요?"
        ]
        
        print(f"1. 기본 전처리 테스트 ({len(test_queries)}개 질의)")
        print("-" * 40)
        
        results = []
        total_time = 0
        
        for i, query in enumerate(test_queries, 1):
            start_time = time.time()
            
            processed = await processor.preprocess_query(query)
            
            processing_time = (time.time() - start_time) * 1000  # ms
            total_time += processing_time
            
            results.append(processed)
            
            print(f"\n{i}. 원본: {query}")
            print(f"   정규화: {processed.normalized}")
            print(f"   토큰: {processed.tokens[:10]}{'...' if len(processed.tokens) > 10 else ''}")
            print(f"   키워드: {processed.keywords[:5]}{'...' if len(processed.keywords) > 5 else ''}")
            print(f"   보험용어: {processed.insurance_terms}")
            print(f"   의도: {processed.intent.value} (신뢰도: {processed.confidence:.2f})")
            print(f"   질의유형: {processed.query_type}")
            print(f"   처리시간: {processing_time:.1f}ms")
            
            # 개체명이 있으면 출력
            if any(processed.entity_types.values()):
                entities = {k: v for k, v in processed.entity_types.items() if v}
                print(f"   개체명: {entities}")
        
        avg_time = total_time / len(test_queries)
        
        print(f"\n{'=' * 40}")
        print(f"전처리 성능 요약:")
        print(f"  총 처리 시간: {total_time:.1f}ms")
        print(f"  평균 처리 시간: {avg_time:.1f}ms")
        print(f"  목표 (<100ms): {'✅ 달성' if avg_time < 100 else '❌ 미달성'}")
        
        return results
        
    except Exception as e:
        print(f"❌ 전처리 테스트 실패: {e}")
        return []

async def test_intent_classification():
    """의도 분류 정확도 테스트"""
    print(f"\n{'=' * 60}")
    print("2. 의도 분류 정확도 테스트")
    print("-" * 40)
    
    try:
        from agents.query_processor import InsuranceQueryProcessor, QueryIntent
        
        processor = InsuranceQueryProcessor()
        
        # 정답이 있는 테스트 데이터
        labeled_queries = [
            ("골절 수술비 보장 금액을 알려주세요", QueryIntent.SEARCH),
            ("A보험과 B보험을 비교해주세요", QueryIntent.COMPARE),
            ("30세 남성 보험료를 계산해주세요", QueryIntent.CALCULATE),
            ("보험금 청구 방법을 설명해주세요", QueryIntent.EXPLAIN),
            ("암보험에 가입하고 싶습니다", QueryIntent.APPLY),
            ("보험 계약을 변경하려고 합니다", QueryIntent.MODIFY),
            ("입원비 특약이 뭔가요?", QueryIntent.SEARCH),
            ("어느 보험이 더 좋을까요?", QueryIntent.COMPARE),
            ("얼마나 보장받을 수 있나요?", QueryIntent.CALCULATE),
            ("어떻게 신청하나요?", QueryIntent.EXPLAIN)
        ]
        
        correct = 0
        total = len(labeled_queries)
        
        for query, expected_intent in labeled_queries:
            processed = await processor.preprocess_query(query)
            predicted_intent = processed.intent
            
            is_correct = predicted_intent == expected_intent
            correct += is_correct
            
            status = "✅" if is_correct else "❌"
            print(f"{status} '{query}'")
            print(f"     예상: {expected_intent.value}, 예측: {predicted_intent.value} (신뢰도: {processed.confidence:.2f})")
        
        accuracy = correct / total * 100
        
        print(f"\n의도 분류 정확도:")
        print(f"  정확한 예측: {correct}/{total}")
        print(f"  정확도: {accuracy:.1f}%")
        print(f"  목표 (≥85%): {'✅ 달성' if accuracy >= 85 else '❌ 미달성'}")
        
        return accuracy
        
    except Exception as e:
        print(f"❌ 의도 분류 테스트 실패: {e}")
        return 0

async def test_insurance_term_recognition():
    """보험 용어 인식률 테스트"""
    print(f"\n{'=' * 60}")
    print("3. 보험 용어 인식률 테스트")
    print("-" * 40)
    
    try:
        from agents.query_processor import InsuranceQueryProcessor
        
        processor = InsuranceQueryProcessor()
        
        # 보험 용어가 포함된 테스트 문장들
        term_test_cases = [
            ("골절로 인한 수술비 보장", ["골절", "수술"]),
            ("입원치료와 약물치료 비용", ["입원", "약물"]),
            ("암진단 시 보험금 지급", ["암", "진단", "보험금"]),
            ("심근경색 수술 보장 범위", ["심장", "수술"]),
            ("재활치료 특약 가입", ["재활", "특약", "가입"]),
            ("자기부담금과 면책사유", ["자기부담금", "면책"]),
            ("보험료 계산과 만기환급", ["보험료", "만기"]),
            ("상해보장과 질병보장 차이", ["상해", "질병"])
        ]
        
        total_expected = 0
        total_found = 0
        
        for query, expected_terms in term_test_cases:
            processed = await processor.preprocess_query(query)
            found_terms = processed.insurance_terms
            
            # 기대되는 용어 중 실제로 찾은 용어 개수
            matched = len(set(expected_terms) & set(found_terms))
            
            total_expected += len(expected_terms)
            total_found += matched
            
            print(f"'{query}'")
            print(f"  기대 용어: {expected_terms}")
            print(f"  찾은 용어: {found_terms}")
            print(f"  매칭: {matched}/{len(expected_terms)}")
        
        recognition_rate = (total_found / total_expected * 100) if total_expected > 0 else 0
        
        print(f"\n보험 용어 인식률:")
        print(f"  매칭된 용어: {total_found}/{total_expected}")
        print(f"  인식률: {recognition_rate:.1f}%")
        print(f"  목표 (≥90%): {'✅ 달성' if recognition_rate >= 90 else '❌ 미달성'}")
        
        return recognition_rate
        
    except Exception as e:
        print(f"❌ 보험 용어 인식 테스트 실패: {e}")
        return 0

async def test_performance_benchmark():
    """성능 벤치마크 테스트"""
    print(f"\n{'=' * 60}")
    print("4. 성능 벤치마크 테스트")
    print("-" * 40)
    
    try:
        from agents.query_processor import InsuranceQueryProcessor
        
        processor = InsuranceQueryProcessor()
        
        # 다양한 길이의 질의로 성능 측정
        benchmark_queries = [
            "보험금",  # 짧은 질의
            "골절 수술비 보장 금액",  # 보통 질의
            "30세 남성이 암보험에 가입할 때 월 보험료와 보장 범위를 자세히 알려주세요",  # 긴 질의
            "A 보험 상품과 B 보험 상품을 비교해서 어떤 것이 더 유리한지 상세한 분석과 함께 설명해주세요"  # 매우 긴 질의
        ]
        
        print("질의 길이별 처리 시간:")
        
        for i, query in enumerate(benchmark_queries, 1):
            times = []
            
            # 여러 번 측정해서 평균 계산
            for _ in range(5):
                start_time = time.time()
                await processor.preprocess_query(query)
                processing_time = (time.time() - start_time) * 1000
                times.append(processing_time)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"  {i}. '{query[:30]}{'...' if len(query) > 30 else ''}'")
            print(f"     길이: {len(query)}자, 평균: {avg_time:.1f}ms, 범위: {min_time:.1f}-{max_time:.1f}ms")
        
        # 대량 처리 성능 테스트
        print(f"\n대량 처리 성능 테스트:")
        
        test_query = "골절로 인한 수술비 보장 금액을 알려주세요"
        batch_size = 100
        
        start_time = time.time()
        
        for _ in range(batch_size):
            await processor.preprocess_query(test_query)
        
        total_time = time.time() - start_time
        avg_time_per_query = (total_time * 1000) / batch_size
        
        print(f"  {batch_size}개 질의 처리: {total_time:.2f}초")
        print(f"  평균 처리 시간: {avg_time_per_query:.1f}ms")
        print(f"  목표 (<100ms): {'✅ 달성' if avg_time_per_query < 100 else '❌ 미달성'}")
        
        return avg_time_per_query
        
    except Exception as e:
        print(f"❌ 성능 테스트 실패: {e}")
        return float('inf')

async def test_complexity_analysis():
    """질의 복잡도 분석 테스트"""
    print(f"\n{'=' * 60}")
    print("5. 질의 복잡도 분석 테스트")
    print("-" * 40)
    
    try:
        from agents.query_processor import InsuranceQueryProcessor
        
        processor = InsuranceQueryProcessor()
        
        complexity_test_cases = [
            "보험금",  # 단순
            "골절 수술비 얼마?",  # 보통
            "30세 남성 암보험 월 10만원 보험료 계산",  # 복잡
            "뇌경색과 심근경색 보장 범위를 비교하여 50세 여성에게 적합한 보험 상품을 추천해주세요"  # 매우 복잡
        ]
        
        for query in complexity_test_cases:
            processed = await processor.preprocess_query(query)
            complexity = processor.analyze_query_complexity(processed)
            
            print(f"'{query}'")
            print(f"  복잡도: {complexity['level']} (점수: {complexity['score']})")
            print(f"  토큰 수: {complexity['token_count']}")
            print(f"  보험 용어: {complexity['insurance_term_count']}")
            print(f"  개체명: {complexity['entity_count']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 복잡도 분석 테스트 실패: {e}")
        return False

async def main():
    """메인 테스트 실행"""
    print("Task 5.1: 자연어 질의 전처리 및 의도 분석 종합 테스트")
    print("=" * 80)
    
    results = {}
    
    # 1. 기본 전처리 테스트
    query_results = await test_query_preprocessing()
    results['preprocessing'] = len(query_results) > 0
    
    # 2. 의도 분류 정확도
    intent_accuracy = await test_intent_classification()
    results['intent_accuracy'] = intent_accuracy
    
    # 3. 보험 용어 인식률
    term_recognition = await test_insurance_term_recognition()
    results['term_recognition'] = term_recognition
    
    # 4. 성능 벤치마크
    avg_performance = await test_performance_benchmark()
    results['performance'] = avg_performance
    
    # 5. 복잡도 분석
    complexity_ok = await test_complexity_analysis()
    results['complexity'] = complexity_ok
    
    # 최종 평가
    print(f"\n{'=' * 80}")
    print("Task 5.1 최종 평가")
    print("=" * 80)
    
    print("📊 성능 지표:")
    print(f"  한국어 질의 전처리: {'✅ 성공' if results['preprocessing'] else '❌ 실패'}")
    print(f"  의도 분류 정확도: {results['intent_accuracy']:.1f}% (목표: ≥85%)")
    print(f"  보험 용어 인식률: {results['term_recognition']:.1f}% (목표: ≥90%)")
    print(f"  평균 처리 시간: {results['performance']:.1f}ms (목표: <100ms)")
    print(f"  복잡도 분석: {'✅ 정상' if results['complexity'] else '❌ 오류'}")
    
    # 종합 평가
    success_criteria = [
        results['preprocessing'],
        results['intent_accuracy'] >= 85,
        results['term_recognition'] >= 90,
        results['performance'] < 100,
        results['complexity']
    ]
    
    success_count = sum(success_criteria)
    total_criteria = len(success_criteria)
    
    print(f"\n🎯 종합 결과:")
    print(f"  성공한 기준: {success_count}/{total_criteria}")
    print(f"  달성률: {success_count/total_criteria*100:.1f}%")
    
    if success_count >= 4:
        print(f"  ✅ Task 5.1 구현 성공!")
    elif success_count >= 3:
        print(f"  ⚠️ Task 5.1 부분 성공 (일부 개선 필요)")
    else:
        print(f"  ❌ Task 5.1 구현 실패 (대폭 수정 필요)")
    
    return success_count >= 4

if __name__ == "__main__":
    asyncio.run(main())
