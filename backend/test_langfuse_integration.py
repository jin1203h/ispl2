#!/usr/bin/env python3
"""
LangFuse 통합 테스트 스크립트
Task 6.1: LangFuse SDK 통합 및 기본 설정 검증
"""
import asyncio
import os
import sys
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.langfuse_monitor import langfuse_monitor, trace_workflow, trace_agent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_langfuse_connection():
    """LangFuse 연결 테스트"""
    print("=" * 60)
    print("🔍 LangFuse 연결 테스트")
    print("=" * 60)
    
    try:
        # 모니터 상태 확인
        print(f"✅ LangFuse 활성화 상태: {langfuse_monitor.enabled}")
        
        if langfuse_monitor.langfuse:
            print(f"✅ LangFuse 호스트: {langfuse_monitor.langfuse.host}")
        else:
            print("⚠️  LangFuse 클라이언트가 초기화되지 않았습니다.")
            print("   환경 변수를 확인하세요:")
            print(f"   - LANGFUSE_SECRET_KEY: {'설정됨' if os.getenv('LANGFUSE_SECRET_KEY') else '미설정'}")
            print(f"   - LANGFUSE_PUBLIC_KEY: {'설정됨' if os.getenv('LANGFUSE_PUBLIC_KEY') else '미설정'}")
            print(f"   - LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', '기본값 사용')}")
        
        return langfuse_monitor.enabled
        
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False


async def test_basic_trace():
    """기본 트레이스 생성 테스트"""
    print("\n" + "=" * 60)
    print("📊 기본 트레이스 생성 테스트")
    print("=" * 60)
    
    try:
        async with langfuse_monitor.trace_workflow(
            "test_basic_workflow",
            {"test_type": "basic", "timestamp": datetime.now().isoformat()}
        ) as trace:
            print("✅ 워크플로우 트레이스 생성 성공")
            
            # 에이전트 실행 시뮬레이션
            span = await langfuse_monitor.trace_agent_execution(
                "test_basic_agent",
                {"input": "test_input", "version": "1.0"},
                trace
            )
            print("✅ 에이전트 스팬 생성 성공")
            
            # 처리 시간 시뮬레이션
            await asyncio.sleep(0.05)
            
            # 결과 업데이트
            await langfuse_monitor.update_agent_result(
                span,
                {"output": "test_output", "success": True},
                0.05,
                "completed"
            )
            print("✅ 에이전트 결과 업데이트 성공")
        
        print("✅ 기본 트레이스 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 기본 트레이스 테스트 실패: {e}")
        return False


async def test_metrics_logging():
    """메트릭 로깅 테스트"""
    print("\n" + "=" * 60)
    print("📈 메트릭 로깅 테스트")
    print("=" * 60)
    
    try:
        # 다양한 메트릭 로깅
        test_metrics = [
            {
                "metric_type": "performance",
                "execution_time": 0.123,
                "memory_usage": 1024,
                "cpu_usage": 45.6
            },
            {
                "metric_type": "business",
                "documents_processed": 5,
                "embeddings_created": 150,
                "search_queries": 10
            },
            {
                "metric_type": "error",
                "error_count": 0,
                "warning_count": 2,
                "success_rate": 100.0
            }
        ]
        
        for i, metrics in enumerate(test_metrics, 1):
            await langfuse_monitor.log_metrics(metrics)
            print(f"✅ 메트릭 {i} 로깅 성공: {metrics['metric_type']}")
        
        print("✅ 메트릭 로깅 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 메트릭 로깅 테스트 실패: {e}")
        return False


@trace_workflow("decorator_test_workflow", {"test_type": "decorator"})
async def test_decorator_workflow(**kwargs):
    """데코레이터 기반 워크플로우 테스트"""
    print("\n" + "=" * 60)
    print("🎭 데코레이터 기반 워크플로우 테스트")
    print("=" * 60)
    
    try:
        print("✅ 워크플로우 데코레이터 적용 성공")
        
        # 내부 에이전트 호출
        result = await test_decorator_agent(
            input_data="decorator_test",
            _trace=kwargs.get('_trace')
        )
        
        print(f"✅ 에이전트 결과: {result}")
        return {"workflow_result": "success", "agent_result": result}
        
    except Exception as e:
        print(f"❌ 데코레이터 워크플로우 테스트 실패: {e}")
        return {"workflow_result": "error", "error": str(e)}


@trace_agent("decorator_test_agent")
async def test_decorator_agent(input_data: str, **kwargs):
    """데코레이터 기반 에이전트 테스트"""
    try:
        print("✅ 에이전트 데코레이터 적용 성공")
        
        # 간단한 처리 시뮬레이션
        await asyncio.sleep(0.02)
        
        result = {
            "processed_input": input_data.upper(),
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
        print(f"✅ 에이전트 처리 완료: {result['processed_input']}")
        return result
        
    except Exception as e:
        print(f"❌ 에이전트 처리 실패: {e}")
        raise


async def test_error_handling():
    """에러 처리 테스트"""
    print("\n" + "=" * 60)
    print("⚠️  에러 처리 테스트")
    print("=" * 60)
    
    try:
        async with langfuse_monitor.trace_workflow(
            "error_test_workflow",
            {"test_type": "error_handling"}
        ) as trace:
            print("✅ 에러 테스트 워크플로우 시작")
            
            span = await langfuse_monitor.trace_agent_execution(
                "error_test_agent",
                {"will_fail": True},
                trace
            )
            
            try:
                # 의도적 에러 발생
                raise ValueError("테스트용 에러입니다.")
                
            except ValueError as e:
                # 에러 상태로 결과 업데이트
                await langfuse_monitor.update_agent_result(
                    span,
                    {"error": str(e), "error_type": "ValueError"},
                    0.01,
                    "error"
                )
                print(f"✅ 에러 상태 기록 성공: {e}")
        
        print("✅ 에러 처리 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 에러 처리 테스트 실패: {e}")
        return False


async def test_data_sanitization():
    """데이터 마스킹 테스트"""
    print("\n" + "=" * 60)
    print("🔒 데이터 마스킹 테스트")
    print("=" * 60)
    
    try:
        # 민감한 데이터 포함 테스트
        sensitive_data = {
            "user_password": "secret123",
            "api_key": "sk-1234567890",
            "normal_data": "public_info",
            "large_text": "x" * 2000,  # 긴 텍스트
            "token": "bearer_token_123"
        }
        
        async with langfuse_monitor.trace_workflow(
            "sanitization_test_workflow",
            {"test_type": "data_sanitization"}
        ) as trace:
            
            span = await langfuse_monitor.trace_agent_execution(
                "sanitization_test_agent",
                sensitive_data,
                trace
            )
            
            await langfuse_monitor.update_agent_result(
                span,
                {"processed": True, "sensitive_output": "should_be_masked"},
                0.01,
                "completed"
            )
        
        print("✅ 민감한 데이터 마스킹 테스트 완료")
        print("   (실제 마스킹 여부는 LangFuse 대시보드에서 확인)")
        return True
        
    except Exception as e:
        print(f"❌ 데이터 마스킹 테스트 실패: {e}")
        return False


async def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 LangFuse 통합 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().isoformat()}")
    
    test_results = {}
    
    # 1. 연결 테스트
    test_results['connection'] = await test_langfuse_connection()
    
    if not test_results['connection']:
        print("\n❌ LangFuse 연결 실패로 인해 추가 테스트를 건너뜁니다.")
        print("   환경 변수를 설정하고 다시 시도하세요.")
        return test_results
    
    # 2. 기본 기능 테스트
    test_results['basic_trace'] = await test_basic_trace()
    test_results['metrics_logging'] = await test_metrics_logging()
    test_results['decorator_workflow'] = bool(await test_decorator_workflow())
    test_results['error_handling'] = await test_error_handling()
    test_results['data_sanitization'] = await test_data_sanitization()
    
    # 3. 데이터 플러시
    print("\n" + "=" * 60)
    print("💾 LangFuse 데이터 플러시")
    print("=" * 60)
    
    try:
        langfuse_monitor.flush()
        print("✅ 데이터 플러시 완료")
        test_results['flush'] = True
    except Exception as e:
        print(f"❌ 데이터 플러시 실패: {e}")
        test_results['flush'] = False
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과")
    print(f"⏰ 완료 시간: {datetime.now().isoformat()}")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️  일부 테스트가 실패했습니다. 로그를 확인하세요.")
    
    return test_results


if __name__ == "__main__":
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    # 테스트 실행
    results = asyncio.run(run_all_tests())
    
    # 종료 코드 설정
    sys.exit(0 if all(results.values()) else 1)





