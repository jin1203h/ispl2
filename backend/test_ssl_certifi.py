#!/usr/bin/env python3
"""
certifi를 활용한 SSL 인증서 문제 해결 테스트
"""
import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# SSL 설정 먼저 적용
from utils.ssl_fixer import setup_ssl_for_langfuse

print("🔒 SSL 인증서 설정 테스트")
print("=" * 50)

# SSL 설정 적용
ssl_success = setup_ssl_for_langfuse()

if ssl_success:
    print("\n🚀 LangFuse 클라이언트 테스트")
    print("=" * 50)
    
    try:
        from langfuse import Langfuse
        print("✅ LangFuse 모듈 import 성공")
        
        # 환경 변수 확인
        secret_key = os.getenv('LANGFUSE_SECRET_KEY')
        public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
        host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
        
        if secret_key and public_key:
            print("🔗 LangFuse 클라이언트 생성 (SSL 수정 적용)...")
            
            client = Langfuse(
                secret_key=secret_key,
                public_key=public_key,
                host=host
            )
            print("✅ LangFuse 클라이언트 생성 성공")
            
            # 간단한 테스트
            try:
                print("📝 테스트 이벤트 생성...")
                client.create_event(
                    name="ssl_certifi_test",
                    metadata={"test": True, "ssl_method": "certifi"}
                )
                print("✅ 테스트 이벤트 생성 성공!")
                
                # 데이터 플러시
                print("💾 데이터 플러시...")
                client.flush()
                print("✅ 모든 테스트 성공!")
                
            except Exception as e:
                print(f"⚠️  이벤트 생성 실패: {e}")
                print("   하지만 클라이언트 생성은 성공했습니다.")
        else:
            print("⚠️  환경 변수가 설정되지 않았습니다.")
            
    except Exception as e:
        print(f"❌ LangFuse 테스트 실패: {e}")
        
else:
    print("❌ SSL 설정 실패로 인해 LangFuse 테스트를 건너뜁니다.")

print("\n📋 SSL 인증서 해결 방법 요약:")
print("1. certifi 번들 사용 - 표준 인증서 번들")
print("2. 환경 변수 설정 - REQUESTS_CA_BUNDLE, SSL_CERT_FILE")
print("3. 회사 인증서 추가 - 필요시 사용자 정의 번들 생성")
print("4. requests 세션 설정 - 세션별 인증서 지정")




