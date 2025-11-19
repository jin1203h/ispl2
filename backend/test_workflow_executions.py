#!/usr/bin/env python3
"""
워크플로우 실행 목록 API 테스트
Task 6.4: WorkflowMonitor 컴포넌트 연동 테스트
"""
import asyncio
import requests
import json
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

def test_workflow_executions_api():
    """워크플로우 실행 목록 API 테스트"""
    print("\n🔍 워크플로우 실행 목록 API 테스트 시작")
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    test_cases = [
        {
            "name": "전체 워크플로우 실행 목록 조회 (데모)",
            "url": f"{BASE_URL}/workflow/executions/demo",
            "params": {},
            "auth_required": False
        },
        {
            "name": "완료된 워크플로우만 필터링 (데모)",
            "url": f"{BASE_URL}/workflow/executions/demo",
            "params": {"status_filter": "completed"},
            "auth_required": False
        },
        {
            "name": "실패한 워크플로우만 필터링 (데모)",
            "url": f"{BASE_URL}/workflow/executions/demo",
            "params": {"status_filter": "failed"},
            "auth_required": False
        },
        {
            "name": "제한된 수량 조회 (limit=2, 데모)",
            "url": f"{BASE_URL}/workflow/executions/demo",
            "params": {"limit": 2},
            "auth_required": False
        },
        {
            "name": "인증 필요 엔드포인트 테스트",
            "url": f"{BASE_URL}/workflow/executions",
            "params": {},
            "auth_required": True
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n📋 테스트: {test_case['name']}")
            
            # 인증이 필요한 경우에만 헤더 포함
            request_headers = headers if test_case.get("auth_required", True) else {"Content-Type": "application/json"}
            
            response = requests.get(
                test_case["url"],
                headers=request_headers,
                params=test_case["params"],
                timeout=10
            )
            
            print(f"   상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    executions = data.get("data", {}).get("workflow_executions", [])
                    total_count = data.get("data", {}).get("total_count", 0)
                    
                    print(f"   ✅ 성공: {total_count}개 워크플로우 실행 조회")
                    
                    # 첫 번째 실행 정보 출력
                    if executions:
                        first_exec = executions[0]
                        print(f"   📄 첫 번째 실행:")
                        print(f"      - ID: {first_exec.get('workflow_id')}")
                        print(f"      - 문서: {first_exec.get('document_name')}")
                        print(f"      - 상태: {first_exec.get('status')}")
                        print(f"      - 에이전트 수: {len(first_exec.get('agents', []))}")
                        
                        # 에이전트 정보 출력
                        agents = first_exec.get('agents', [])
                        if agents:
                            print(f"      - 에이전트:")
                            for agent in agents[:3]:  # 처음 3개만
                                print(f"        * {agent.get('agent_name', agent.get('name'))}: {agent.get('status')}")
                    
                    results.append({
                        "test": test_case['name'],
                        "status": "PASS",
                        "count": total_count,
                        "details": f"{total_count}개 실행 조회 성공"
                    })
                else:
                    print(f"   ❌ API 응답 실패: {data}")
                    results.append({
                        "test": test_case['name'],
                        "status": "FAIL",
                        "error": "API success=false"
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

def test_workflow_summary_api():
    """워크플로우 요약 API 테스트"""
    print("\n📊 워크플로우 요약 API 테스트")
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/workflow/logs/summary",
            headers=headers,
            timeout=10
        )
        
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 워크플로우 요약 조회 성공")
            print(f"   - 총 워크플로우: {data.get('total_workflows')}")
            print(f"   - 총 단계: {data.get('total_steps')}")
            print(f"   - 완료된 단계: {data.get('completed_steps')}")
            print(f"   - 성공률: {data.get('success_rate')}%")
            print(f"   - 평균 실행 시간: {data.get('avg_execution_time')}초")
            print(f"   - 모니터 타입: {data.get('monitor_type')}")
            
            return {"status": "PASS", "data": data}
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"응답: {response.text}")
            return {"status": "FAIL", "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return {"status": "FAIL", "error": str(e)}

def main():
    """메인 테스트 실행"""
    print("🚀 워크플로우 실행 목록 API 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 워크플로우 실행 목록 API 테스트
    execution_results = test_workflow_executions_api()
    
    # 2. 워크플로우 요약 API 테스트
    summary_result = test_workflow_summary_api()
    
    # 결과 요약
    print("\n" + "="*60)
    print("📋 테스트 결과 요약")
    print("="*60)
    
    total_tests = len(execution_results) + 1
    passed_tests = len([r for r in execution_results if r["status"] == "PASS"])
    if summary_result["status"] == "PASS":
        passed_tests += 1
    
    print(f"총 테스트: {total_tests}")
    print(f"통과: {passed_tests}")
    print(f"실패: {total_tests - passed_tests}")
    
    print("\n📊 워크플로우 실행 목록 테스트:")
    for result in execution_results:
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"  {status_icon} {result['test']}")
        if result["status"] == "PASS":
            print(f"     {result.get('details', '')}")
        else:
            print(f"     오류: {result.get('error', '')}")
    
    print(f"\n📈 워크플로우 요약 테스트:")
    status_icon = "✅" if summary_result["status"] == "PASS" else "❌"
    print(f"  {status_icon} 워크플로우 요약 API")
    
    print(f"\n⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ Task 6.4: 워크플로우 실행 목록 API 연동 성공")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
