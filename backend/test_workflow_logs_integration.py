#!/usr/bin/env python3
"""
워크플로우 로그 통합 테스트
workflow_logs 테이블 실제 사용 구현 검증
"""
import asyncio
import requests
import json
import time
from datetime import datetime
import os
import sys

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# JWT 토큰 생성 (테스트용)
try:
    from jose import jwt
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    
    # 테스트 사용자 토큰 생성
    test_payload = {
        "sub": "test@example.com",
        "email": "test@example.com", 
        "role": "admin",
        "exp": datetime.utcnow().timestamp() + 3600  # 1시간 후 만료
    }
    TEST_USER_TOKEN = jwt.encode(test_payload, JWT_SECRET_KEY, algorithm="HS256")
    print(f"✅ 테스트 토큰 생성 완료")
    
except ImportError:
    print("❌ python-jose 라이브러리가 필요합니다: pip install python-jose")
    sys.exit(1)

BASE_URL = "http://localhost:8000"

async def test_workflow_logger_service():
    """워크플로우 로거 서비스 직접 테스트"""
    print("\n🔧 워크플로우 로거 서비스 직접 테스트")
    
    try:
        from services.workflow_logger import get_workflow_logger
        
        workflow_logger = get_workflow_logger()
        
        # 테스트 워크플로우 ID
        test_workflow_id = f"test_workflow_{int(time.time())}"
        
        # 1. 워크플로우 단계 로그 저장 테스트
        print("📝 워크플로우 단계 로그 저장 테스트...")
        
        steps = [
            {
                "step_name": "PDF Analysis",
                "status": "running",
                "input_data": {"file_name": "test.pdf", "file_size": 1024},
                "execution_time": None
            },
            {
                "step_name": "PDF Analysis",
                "status": "completed",
                "input_data": {"file_name": "test.pdf", "file_size": 1024},
                "output_data": {"pages": 10, "has_text": True},
                "execution_time": 1500
            },
            {
                "step_name": "Text Extraction",
                "status": "running",
                "input_data": {"pages": 10},
                "execution_time": None
            },
            {
                "step_name": "Text Extraction",
                "status": "completed",
                "input_data": {"pages": 10},
                "output_data": {"text_length": 5000},
                "execution_time": 800
            },
            {
                "step_name": "Embedding Generation",
                "status": "error",
                "input_data": {"text_length": 5000},
                "error_message": "API 호출 실패",
                "execution_time": 200
            }
        ]
        
        log_ids = []
        for step in steps:
            log_id = await workflow_logger.log_workflow_step(
                workflow_id=test_workflow_id,
                **step
            )
            log_ids.append(log_id)
            print(f"   ✅ {step['step_name']} ({step['status']}) 로그 저장: ID {log_id}")
        
        # 2. 워크플로우 로그 조회 테스트
        print("\n📋 워크플로우 로그 조회 테스트...")
        logs = await workflow_logger.get_workflow_logs(workflow_id=test_workflow_id)
        print(f"   ✅ 조회된 로그 수: {len(logs)}")
        
        for log in logs:
            print(f"   - {log['step_name']}: {log['status']} ({log['execution_time']}ms)")
        
        # 3. 워크플로우 요약 테스트
        print("\n📊 워크플로우 요약 테스트...")
        summary = await workflow_logger.get_workflow_summary()
        print(f"   ✅ 총 워크플로우: {summary.get('total_workflows')}")
        print(f"   ✅ 총 단계: {summary.get('total_steps')}")
        print(f"   ✅ 성공률: {summary.get('success_rate')}%")
        print(f"   ✅ 평균 실행 시간: {summary.get('avg_execution_time')}초")
        
        # 4. 워크플로우 실행 목록 테스트
        print("\n📋 워크플로우 실행 목록 테스트...")
        executions = await workflow_logger.get_workflow_executions(limit=10)
        print(f"   ✅ 조회된 실행 수: {len(executions)}")
        
        for execution in executions:
            print(f"   - {execution['workflow_id']}: {execution['status']} ({len(execution['agents'])}개 에이전트)")
        
        return {
            "status": "PASS",
            "test_workflow_id": test_workflow_id,
            "logs_created": len(log_ids),
            "logs_retrieved": len(logs),
            "executions_found": len(executions)
        }
        
    except Exception as e:
        print(f"❌ 워크플로우 로거 서비스 테스트 실패: {e}")
        return {"status": "FAIL", "error": str(e)}

def test_workflow_api_endpoints():
    """워크플로우 API 엔드포인트 테스트"""
    print("\n🌐 워크플로우 API 엔드포인트 테스트")
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    test_cases = [
        {
            "name": "워크플로우 로그 조회 (인증)",
            "url": f"{BASE_URL}/workflow/logs",
            "auth_required": True
        },
        {
            "name": "워크플로우 요약 조회 (인증)",
            "url": f"{BASE_URL}/workflow/logs/summary",
            "auth_required": True
        },
        {
            "name": "워크플로우 실행 목록 조회 (데모)",
            "url": f"{BASE_URL}/workflow/executions/demo",
            "auth_required": False
        },
        {
            "name": "워크플로우 실행 목록 조회 (인증)",
            "url": f"{BASE_URL}/workflow/executions",
            "auth_required": True
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n📋 테스트: {test_case['name']}")
            
            request_headers = headers if test_case["auth_required"] else {"Content-Type": "application/json"}
            
            response = requests.get(
                test_case["url"],
                headers=request_headers,
                timeout=10
            )
            
            print(f"   상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 응답 데이터 분석
                if isinstance(data, list):
                    # 로그 리스트 응답
                    print(f"   ✅ 성공: {len(data)}개 로그 조회")
                    data_source = "database" if any("workflow_" in str(item.get("workflow_id", "")) for item in data) else "fallback"
                elif isinstance(data, dict):
                    if "success" in data:
                        # API 응답 형식
                        if data.get("success"):
                            workflow_data = data.get("data", {})
                            if "workflow_executions" in workflow_data:
                                executions = workflow_data["workflow_executions"]
                                print(f"   ✅ 성공: {len(executions)}개 워크플로우 실행 조회")
                                data_source = workflow_data.get("data_source", "unknown")
                            else:
                                print(f"   ✅ 성공: 요약 데이터 조회")
                                data_source = workflow_data.get("data_source", "unknown")
                        else:
                            print(f"   ❌ API 응답 실패: {data}")
                            data_source = "error"
                    else:
                        # 직접 데이터 응답
                        print(f"   ✅ 성공: 요약 데이터 조회")
                        data_source = data.get("data_source", "unknown")
                
                print(f"   📊 데이터 소스: {data_source}")
                
                results.append({
                    "test": test_case['name'],
                    "status": "PASS",
                    "data_source": data_source,
                    "response_size": len(str(data))
                })
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                print(f"   응답: {response.text}")
                results.append({
                    "test": test_case['name'],
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"   ❌ 예외 발생: {e}")
            results.append({
                "test": test_case['name'],
                "status": "FAIL",
                "error": str(e)
            })
    
    return results

async def test_agent_workflow_integration():
    """에이전트 워크플로우 통합 테스트 (시뮬레이션)"""
    print("\n🤖 에이전트 워크플로우 통합 테스트")
    
    try:
        from agents.base import BaseAgent, DocumentProcessingState, ProcessingStatus
        from services.workflow_logger import get_workflow_logger
        
        # 테스트용 에이전트 클래스
        class TestAgent(BaseAgent):
            async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
                # 간단한 처리 시뮬레이션
                await asyncio.sleep(0.1)  # 처리 시간 시뮬레이션
                
                state["processed_by"] = self.name
                state["processing_time"] = 0.1
                
                return self.update_status(
                    state,
                    ProcessingStatus.COMPLETED,
                    f"{self.name}_completed",
                    f"{self.name} 처리 완료"
                )
        
        # 테스트 에이전트 생성
        test_agent = TestAgent("test_agent", "테스트 에이전트")
        
        # 테스트 상태 생성
        test_state = {
            "workflow_id": f"integration_test_{int(time.time())}",
            "file_name": "test_integration.pdf",
            "policy_id": 999,
            "status": ProcessingStatus.PENDING,
            "messages": []
        }
        
        print(f"📝 테스트 워크플로우 ID: {test_state['workflow_id']}")
        
        # 에이전트 실행 (추적 기능 포함)
        print("🚀 에이전트 실행 중...")
        result_state = await test_agent.process_with_tracing(test_state)
        
        print(f"   ✅ 에이전트 실행 완료: {result_state.get('status')}")
        
        # 데이터베이스에서 로그 확인
        workflow_logger = get_workflow_logger()
        logs = await workflow_logger.get_workflow_logs(
            workflow_id=test_state["workflow_id"]
        )
        
        print(f"   ✅ 생성된 로그 수: {len(logs)}")
        for log in logs:
            print(f"      - {log['step_name']}: {log['status']} ({log['execution_time']}ms)")
        
        return {
            "status": "PASS",
            "workflow_id": test_state["workflow_id"],
            "agent_status": result_state.get("status"),
            "logs_created": len(logs)
        }
        
    except Exception as e:
        print(f"❌ 에이전트 워크플로우 통합 테스트 실패: {e}")
        return {"status": "FAIL", "error": str(e)}

async def main():
    """메인 테스트 실행"""
    print("🚀 워크플로우 로그 통합 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 워크플로우 로거 서비스 직접 테스트
    logger_result = await test_workflow_logger_service()
    
    # 2. 워크플로우 API 엔드포인트 테스트
    api_results = test_workflow_api_endpoints()
    
    # 3. 에이전트 워크플로우 통합 테스트
    integration_result = await test_agent_workflow_integration()
    
    # 결과 요약
    print("\n" + "="*60)
    print("📋 테스트 결과 요약")
    print("="*60)
    
    # 워크플로우 로거 서비스 결과
    print(f"\n🔧 워크플로우 로거 서비스:")
    if logger_result["status"] == "PASS":
        print(f"  ✅ 성공")
        print(f"     - 로그 생성: {logger_result.get('logs_created', 0)}개")
        print(f"     - 로그 조회: {logger_result.get('logs_retrieved', 0)}개")
        print(f"     - 실행 목록: {logger_result.get('executions_found', 0)}개")
    else:
        print(f"  ❌ 실패: {logger_result.get('error', '')}")
    
    # API 엔드포인트 결과
    print(f"\n🌐 워크플로우 API 엔드포인트:")
    api_passed = len([r for r in api_results if r["status"] == "PASS"])
    api_total = len(api_results)
    print(f"  통과: {api_passed}/{api_total}")
    
    for result in api_results:
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"  {status_icon} {result['test']}")
        if result["status"] == "PASS":
            print(f"     데이터 소스: {result.get('data_source', 'unknown')}")
        else:
            print(f"     오류: {result.get('error', '')}")
    
    # 에이전트 통합 결과
    print(f"\n🤖 에이전트 워크플로우 통합:")
    if integration_result["status"] == "PASS":
        print(f"  ✅ 성공")
        print(f"     - 워크플로우 ID: {integration_result.get('workflow_id', '')}")
        print(f"     - 에이전트 상태: {integration_result.get('agent_status', '')}")
        print(f"     - 생성된 로그: {integration_result.get('logs_created', 0)}개")
    else:
        print(f"  ❌ 실패: {integration_result.get('error', '')}")
    
    # 전체 결과
    total_tests = 1 + api_total + 1  # 로거 서비스 + API 엔드포인트들 + 통합 테스트
    passed_tests = (1 if logger_result["status"] == "PASS" else 0) + api_passed + (1 if integration_result["status"] == "PASS" else 0)
    
    print(f"\n📊 전체 결과: {passed_tests}/{total_tests} 테스트 통과")
    print(f"⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ workflow_logs 테이블 실제 사용 구현 완료")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)




