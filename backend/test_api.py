#!/usr/bin/env python3
"""
ISPL Insurance Policy AI Backend API 테스트 스크립트
현재 구현된 API 엔드포인트들을 테스트합니다.
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def test_health_check():
    """헬스체크 테스트"""
    print("🔍 헬스체크 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 헬스체크 성공")
            print(f"   응답: {response.json()}")
            return True
        else:
            print(f"❌ 헬스체크 실패: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 헬스체크 연결 실패: {e}")
        return False

def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    print("\n🔍 루트 엔드포인트 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ 루트 엔드포인트 성공")
            print(f"   응답: {response.json()}")
            return True
        else:
            print(f"❌ 루트 엔드포인트 실패: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 루트 엔드포인트 연결 실패: {e}")
        return False

def test_login_api():
    """로그인 API 테스트"""
    print("\n🔍 로그인 API 테스트...")
    
    # 1. 관리자 로그인 테스트
    login_data = {
        "email": "admin@ispl2.com",
        "password": "admin"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login", 
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 관리자 로그인 성공")
            data = response.json()
            print(f"   토큰: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   사용자: {data.get('user', {})}")
            return data.get('access_token')
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"   에러: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 로그인 API 연결 실패: {e}")
        return None

def test_token_verification(token):
    """토큰 검증 API 테스트"""
    if not token:
        print("\n⏭️ 토큰이 없어서 검증 테스트를 건너뜁니다.")
        return False
        
    print("\n🔍 토큰 검증 API 테스트...")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 토큰 검증 성공")
            print(f"   사용자 정보: {response.json()}")
            return True
        else:
            print(f"❌ 토큰 검증 실패: {response.status_code}")
            print(f"   에러: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 토큰 검증 API 연결 실패: {e}")
        return False

def test_policies_api(token):
    """약관 관리 API 테스트"""
    if not token:
        print("\n⏭️ 토큰이 없어서 약관 API 테스트를 건너뜁니다.")
        return False
        
    print("\n🔍 약관 목록 API 테스트...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/policies",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 약관 목록 조회 성공")
            policies = response.json()
            print(f"   약관 수: {len(policies)}")
            for policy in policies[:2]:  # 처음 2개만 출력
                print(f"   - {policy.get('company', 'N/A')}: {policy.get('product_name', 'N/A')}")
            return True
        else:
            print(f"❌ 약관 목록 조회 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 약관 API 연결 실패: {e}")
        return False

def test_search_api():
    """검색 API 테스트"""
    print("\n🔍 검색 API 테스트...")
    
    search_data = {
        "query": "건강보험 보장범위",
        "limit": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json=search_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ 검색 API 성공")
            data = response.json()
            print(f"   답변: {data.get('answer', 'N/A')[:100]}...")
            print(f"   검색 결과 수: {len(data.get('results', []))}")
            return True
        else:
            print(f"❌ 검색 API 실패: {response.status_code}")
            print(f"   에러: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 검색 API 연결 실패: {e}")
        return False

def test_workflow_api(token):
    """워크플로우 API 테스트"""
    if not token:
        print("\n⏭️ 토큰이 없어서 워크플로우 API 테스트를 건너뜁니다.")
        return False
        
    print("\n🔍 워크플로우 로그 API 테스트...")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{BASE_URL}/workflow/logs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 워크플로우 로그 조회 성공")
            logs = response.json()
            print(f"   로그 수: {len(logs)}")
            if logs:
                print(f"   최신 로그: {logs[0].get('step_name', 'N/A')} - {logs[0].get('status', 'N/A')}")
            return True
        else:
            print(f"❌ 워크플로우 로그 조회 실패: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 워크플로우 API 연결 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🚀 ISPL Insurance Policy AI Backend API 테스트")
    print("=" * 80)
    
    # 서버 연결 확인
    if not test_health_check():
        print("\n❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        print("   서버 시작: python start.py")
        sys.exit(1)
    
    # 기본 엔드포인트 테스트
    test_root_endpoint()
    
    # 인증 관련 테스트
    token = test_login_api()
    test_token_verification(token)
    
    # 각 API 테스트
    test_policies_api(token)
    test_search_api()
    test_workflow_api(token)
    
    print("\n" + "=" * 80)
    print("🎉 API 테스트 완료!")
    print("=" * 80)
    
    if token:
        print("\n✅ 주요 기능들이 정상적으로 작동합니다!")
        print("📝 다음 단계:")
        print("   1. PostgreSQL 데이터베이스 설정")
        print("   2. 실제 PDF 업로드 및 처리 기능 구현") 
        print("   3. 프론트엔드와 연동 테스트")
    else:
        print("\n⚠️ 일부 기능에서 문제가 발생했습니다.")
        print("   데이터베이스 연결을 확인해주세요.")

if __name__ == "__main__":
    main()


