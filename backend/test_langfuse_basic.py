#!/usr/bin/env python3
"""
LangFuse 기본 연결 테스트 (간단한 버전)
"""
import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

print("🔍 LangFuse 환경 변수 확인:")
print(f"LANGFUSE_SECRET_KEY: {'설정됨' if os.getenv('LANGFUSE_SECRET_KEY') else '미설정'}")
print(f"LANGFUSE_PUBLIC_KEY: {'설정됨' if os.getenv('LANGFUSE_PUBLIC_KEY') else '미설정'}")
print(f"LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', '기본값')}")

try:
    # SSL 경고 비활성화 (개발 환경용)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    from langfuse import Langfuse
    print("✅ LangFuse 모듈 import 성공")
    
    # 클라이언트 생성 테스트
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
    
    if secret_key and public_key:
        print("🔗 LangFuse 클라이언트 생성 시도...")
        client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host
        )
        print("✅ LangFuse 클라이언트 생성 성공")
        
        # 간단한 이벤트 테스트
        try:
            client.create_event(name="test_event", metadata={"test": True})
            print("✅ 테스트 이벤트 생성 성공")
        except Exception as e:
            print(f"⚠️  이벤트 생성 실패: {e}")
    else:
        print("⚠️  키 미설정으로 실제 연결 테스트 건너뜀")
        
except ImportError as e:
    print(f"❌ LangFuse 모듈 import 실패: {e}")
except Exception as e:
    print(f"❌ LangFuse 테스트 실패: {e}")

print("\n📋 LangFuse 설정 가이드:")
print("1. https://langfuse.com 에서 계정 생성")
print("2. 새 프로젝트 생성")
print("3. Settings > API Keys에서 키 복사")
print("4. .env 파일에 실제 키 설정:")
print("   LANGFUSE_SECRET_KEY=sk-lf-실제키")
print("   LANGFUSE_PUBLIC_KEY=pk-lf-실제키")
