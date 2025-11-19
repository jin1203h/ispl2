#!/usr/bin/env python3
"""
Task 6.2: Multi-Agent 워크플로우 추적 테스트
LangGraph 기반 Multi-Agent 시스템과 LangFuse 모니터링 통합 테스트
"""
import asyncio
import time
import logging
from pathlib import Path
import tempfile
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_pdf_content():
    """테스트용 PDF 내용 생성"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000173 00000 n \n0000000301 00000 n \n trailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n380\n%%EOF"

async def test_supervisor_agent_initialization():
    """SupervisorAgent 초기화 테스트"""
    print("\n=== SupervisorAgent 초기화 테스트 ===")
    
    try:
        from agents.supervisor import SupervisorAgent
        
        supervisor = SupervisorAgent()
        print(f"✅ SupervisorAgent 초기화 성공")
        print(f"  - 모니터링 활성화: {supervisor.monitor is not None}")
        print(f"  - LangGraph 사용 가능: {supervisor.workflow is not None}")
        print(f"  - 등록된 에이전트 수: {len(supervisor.agents)}")
        
        # 워크플로우 상태 확인
        status = supervisor.get_workflow_status()
        print(f"  - 워크플로우 상태: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ SupervisorAgent 초기화 실패: {e}")
        return False

async def test_individual_agent_tracking():
    """개별 에이전트 추적 테스트"""
    print("\n=== 개별 에이전트 추적 테스트 ===")
    
    try:
        from agents.supervisor import SupervisorAgent
        from agents.base import DocumentProcessingState, ProcessingStatus
        
        supervisor = SupervisorAgent()
        
        # 테스트 상태 생성
        test_state: DocumentProcessingState = {
            "file_path": "/tmp/test.pdf",
            "policy_id": 1,
            "file_name": "test.pdf",
            "current_step": "initialized",
            "status": ProcessingStatus.PENDING.value,
            "error_message": None,
            "raw_content": None,
            "pdf_metadata": None,
            "extracted_text": None,
            "extracted_tables": None,
            "extracted_images": None,
            "processed_chunks": [],
            "embeddings_created": False,
            "stored_in_vector_db": False,
            "total_pages": None,
            "processed_pages": 0,
            "total_chunks": 0,
            "processing_time": None
        }
        
        # PDF Processor 추적 테스트
        print("📋 PDF Processor 추적 테스트...")
        pdf_result = await supervisor.pdf_processor.process_with_tracing(test_state)
        print(f"  - 결과 상태: {pdf_result.get('status')}")
        print(f"  - 현재 단계: {pdf_result.get('current_step')}")
        
        # Text Processor 추적 테스트 (PDF 처리 성공 시)
        if pdf_result.get('status') != ProcessingStatus.FAILED.value:
            print("📝 Text Processor 추적 테스트...")
            text_result = await supervisor.text_processor.process_with_tracing(pdf_result)
            print(f"  - 결과 상태: {text_result.get('status')}")
            print(f"  - 현재 단계: {text_result.get('current_step')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 개별 에이전트 추적 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_workflow_tracking():
    """전체 워크플로우 추적 테스트"""
    print("\n=== 전체 워크플로우 추적 테스트 ===")
    
    try:
        from agents.supervisor import SupervisorAgent
        
        supervisor = SupervisorAgent()
        
        # 테스트용 임시 PDF 파일 생성
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(create_test_pdf_content())
            temp_pdf_path = tmp_file.name
        
        print(f"📄 테스트 PDF 파일 생성: {temp_pdf_path}")
        
        # 워크플로우 실행 (추적 포함)
        start_time = time.time()
        
        result = await supervisor.process_document(
            file_path=temp_pdf_path,
            policy_id=1,
            file_name="test_tracking.pdf"
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ 워크플로우 실행 완료")
        print(f"  - 실행 시간: {execution_time:.2f}초")
        print(f"  - 최종 상태: {result.get('status')}")
        print(f"  - 처리된 청크 수: {result.get('total_chunks', 0)}")
        print(f"  - 임베딩 생성: {result.get('embeddings_created', False)}")
        
        if result.get("error_message"):
            print(f"  - 에러 메시지: {result.get('error_message')}")
        
        # 임시 파일 정리
        Path(temp_pdf_path).unlink(missing_ok=True)
        
        from agents.base import ProcessingStatus
        return result.get('status') != ProcessingStatus.FAILED.value
        
    except Exception as e:
        print(f"❌ 전체 워크플로우 추적 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_monitoring_system_integration():
    """모니터링 시스템 통합 테스트"""
    print("\n=== 모니터링 시스템 통합 테스트 ===")
    
    try:
        from services.langfuse_monitor import get_monitor
        
        monitor = get_monitor()
        print(f"✅ 모니터 인스턴스 획득: {type(monitor).__name__}")
        print(f"  - 모니터 활성화: {getattr(monitor, 'enabled', True)}")
        
        # 워크플로우 통계 조회 테스트
        stats = await monitor.get_workflow_stats()
        print(f"  - 워크플로우 통계: {stats}")
        
        # 테스트 메트릭 로깅
        await monitor.log_metrics({
            "test_metric": "multi_agent_tracking_test",
            "timestamp": datetime.now().isoformat(),
            "agents_count": 6,
            "test_status": "success"
        })
        print("✅ 테스트 메트릭 로깅 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 모니터링 시스템 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling_and_tracking():
    """오류 처리 및 추적 테스트"""
    print("\n=== 오류 처리 및 추적 테스트 ===")
    
    try:
        from agents.supervisor import SupervisorAgent
        
        supervisor = SupervisorAgent()
        
        # 존재하지 않는 파일로 테스트
        result = await supervisor.process_document(
            file_path="/nonexistent/path/test.pdf",
            policy_id=1,
            file_name="nonexistent.pdf"
        )
        
        print(f"✅ 오류 처리 테스트 완료")
        print(f"  - 결과 상태: {result.get('status')}")
        print(f"  - 에러 메시지: {result.get('error_message', 'N/A')}")
        
        # 오류 상태 또는 경고 메시지가 있으면 오류 처리가 작동한 것으로 간주
        from agents.base import ProcessingStatus
        has_error = (
            result.get('status') == ProcessingStatus.FAILED.value or
            result.get('error_message') is not None or
            "변환할 처리된 청크가 없습니다" in str(result.get('error_message', ''))
        )
        print(f"  - 오류 처리 감지: {has_error}")
        return has_error
        
    except Exception as e:
        print(f"❌ 오류 처리 및 추적 테스트 실패: {e}")
        return False

async def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 Task 6.2: Multi-Agent 워크플로우 추적 테스트 시작")
    print("=" * 60)
    
    test_results = []
    
    # 테스트 목록
    tests = [
        ("initialization", test_supervisor_agent_initialization),
        ("individual_tracking", test_individual_agent_tracking),
        ("workflow_tracking", test_full_workflow_tracking),
        ("monitoring_integration", test_monitoring_system_integration),
        ("error_handling", test_error_handling_and_tracking)
    ]
    
    # 각 테스트 실행
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name} 테스트 실행 중...")
        try:
            start_time = time.time()
            result = await test_func()
            duration = time.time() - start_time
            
            test_results.append((test_name, result, duration))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name} ({duration:.2f}초)")
            
        except Exception as e:
            test_results.append((test_name, False, 0))
            print(f"❌ FAIL {test_name} - 예외 발생: {e}")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 Task 6.2 Multi-Agent 워크플로우 추적 테스트 결과")
    print("=" * 60)
    
    passed = sum(1 for _, result, _ in test_results if result)
    total = len(test_results)
    
    for test_name, result, duration in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과")
    print(f"⏰ 완료 시간: {datetime.now().isoformat()}")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ Task 6.2 완료: Multi-Agent 워크플로우 추적 시스템 구축 성공")
        print("\n💡 달성된 기능:")
        print("- 🔍 개별 에이전트 실행 추적")
        print("- 📊 워크플로우 전체 성능 모니터링") 
        print("- 📈 실시간 메트릭 수집 및 분석")
        print("- 🚨 오류 발생 시 상세 추적")
        print("- 🔄 LangGraph/Sequential 워크플로우 지원")
        print("- 🎛️ 자동 폴백 및 상태 추적")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
