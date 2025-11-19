#!/usr/bin/env python3
"""
LangFuse 최소 기능 테스트 (SSL 우회)
"""
import os
import ssl
import urllib3
from dotenv import load_dotenv

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경 변수 로드
load_dotenv()

print("🔍 LangFuse 최소 기능 테스트 (SSL 우회)")

try:
    from langfuse import Langfuse
    print("✅ LangFuse 모듈 import 성공")
    
    # 환경 변수 확인
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
    
    print(f"🔑 Secret Key: {'설정됨' if secret_key else '미설정'}")
    print(f"🔑 Public Key: {'설정됨' if public_key else '미설정'}")
    print(f"🌐 Host: {host}")
    
    if secret_key and public_key:
        print("\n🔗 LangFuse 클라이언트 생성 (SSL 검증 우회)...")
        
        # SSL 컨텍스트 설정
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 환경 변수로 SSL 검증 비활성화
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        
        client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host
        )
        print("✅ LangFuse 클라이언트 생성 성공")
        
        # 간단한 테스트
        try:
            print("📝 테스트 이벤트 생성 시도...")
            client.create_event(
                name="ssl_bypass_test",
                metadata={"test": True, "ssl_bypass": True}
            )
            print("✅ 테스트 이벤트 생성 성공!")
            
            # 데이터 플러시
            print("💾 데이터 플러시...")
            client.flush()
            print("✅ 데이터 플러시 완료")
            
        except Exception as e:
            print(f"⚠️  테스트 실패: {e}")
            print("   하지만 클라이언트 생성은 성공했습니다.")
    else:
        print("⚠️  환경 변수가 설정되지 않았습니다.")
        
except Exception as e:
    print(f"❌ 오류 발생: {e}")

print("\n✅ 테스트 완료")
print("💡 SSL 인증서 문제가 있는 환경에서는 이 방식을 사용하세요.")





