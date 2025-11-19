#!/usr/bin/env python3
"""
워크플로우 모니터링 통합 테스트
LangFuse 실패 시 로컬 모니터로 자동 전환 테스트
"""
import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_monitoring_system():
    """모니터링 시스템 통합 테스트"""
    print("=" * 60)
    print("🔍 워크플로우 모니터링 시스템 테스트")
    print("=" * 60)
    
    try:
        from services.langfuse_monitor import get_monitor
        
        # 활성 모니터 확인
        monitor = get_monitor()
        monitor_type = "LangFuse" if hasattr(monitor, 'langfuse') else "로컬"
        print(f"✅ 활성 모니터: {monitor_type}")
        print(f"✅ 모니터 활성화 상태: {getattr(monitor, 'enabled', True)}")
        
        # 워크플로우 추적 테스트
        print("\n📊 워크플로우 추적 테스트 시작...")
        
        async with monitor.trace_workflow(
            "test_pdf_processing",
            {"test": True, "document": "sample.pdf"}
        ) as trace:
            print("✅ 워크플로우 트레이스 생성 성공")
            
            # 에이전트 실행 시뮬레이션
            agents = ["pdf_analyzer", "text_extractor", "embedding_generator"]
            
            for agent_name in agents:
                print(f"  🤖 {agent_name} 실행 중...")
                
                span = await monitor.trace_agent_execution(
                    agent_name,
                    {"input": f"test_data_for_{agent_name}"},
                    trace
                )
                
                # 처리 시간 시뮬레이션
                await asyncio.sleep(0.1)
                
                await monitor.update_agent_result(
                    span,
                    {"output": f"processed_by_{agent_name}", "success": True},
                    0.1,
                    "completed"
                )
                
                print(f"  ✅ {agent_name} 완료")
        
        print("✅ 워크플로우 추적 테스트 완료")
        
        # 메트릭 로깅 테스트
        print("\n📈 메트릭 로깅 테스트...")
        
        test_metrics = {
            "total_documents": 1,
            "processing_time": 0.3,
            "memory_usage": 256,
            "success_rate": 100.0
        }
        
        await monitor.log_metrics(test_metrics)
        print("✅ 메트릭 로깅 완료")
        
        # 통계 조회 테스트
        print("\n📊 통계 조회 테스트...")
        
        stats = await monitor.get_workflow_stats("test_pdf_processing")
        print(f"✅ 통계 조회 완료: {stats}")
        
        # 데이터 플러시
        print("\n💾 데이터 플러시...")
        monitor.flush()
        print("✅ 데이터 플러시 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 모니터링 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_integration():
    """API 통합 테스트"""
    print("\n" + "=" * 60)
    print("🌐 API 통합 테스트")
    print("=" * 60)
    
    try:
        # 임시 사용자 생성 (테스트용)
        test_user = {"email": "test@example.com", "user_id": 1}
        
        # 워크플로우 요약 API 테스트
        from routers.workflow import get_workflow_summary
        
        print("📊 워크플로우 요약 API 테스트...")
        summary = await get_workflow_summary(current_user=test_user)
        
        print(f"✅ API 응답 성공:")
        print(f"  - 모니터 타입: {summary.get('monitor_type', 'unknown')}")
        print(f"  - 모니터 활성화: {summary.get('monitor_enabled', False)}")
        print(f"  - 총 워크플로우: {summary.get('total_workflows', 0)}")
        print(f"  - 성공률: {summary.get('success_rate', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ API 통합 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("🚀 워크플로우 모니터링 통합 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().isoformat()}")
    
    results = {}
    
    # 1. 모니터링 시스템 테스트
    results['monitoring'] = await test_monitoring_system()
    
    # 2. API 통합 테스트
    results['api'] = await test_api_integration()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과")
    print(f"⏰ 완료 시간: {datetime.now().isoformat()}")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ Task 6.1 LangFuse SDK 통합 및 기본 설정 완료")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)





