#!/usr/bin/env python3
"""
Windows 환경 SSL 인증서 문제 해결 테스트
certificates.command 대신 Windows 방법 사용
"""
import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

print("🪟 Windows 환경 SSL 인증서 테스트")
print("=" * 50)

# Windows 환경 확인
if sys.platform != "win32":
    print("⚠️  이 스크립트는 Windows 환경용입니다.")
    sys.exit(1)

print(f"✅ Windows 환경 확인: {sys.platform}")

# Windows 인증서 관리자 테스트
try:
    from utils.windows_cert_manager import WindowsCertificateManager
    
    manager = WindowsCertificateManager()
    
    print("\n🔍 Windows 인증서 저장소 테스트...")
    
    # 1. certlm.msc 정보 제공
    print("\n📋 Windows 인증서 관리 방법:")
    print("1. Windows + R 키를 누르고 'certlm.msc' 입력")
    print("2. '신뢰할 수 있는 루트 인증 기관' > '인증서' 확인")
    print("3. 회사 인증서가 있는지 확인")
    
    # 2. 프록시 설정 확인
    print("\n🔍 프록시 설정 확인...")
    proxy_found = manager.check_corporate_proxy()
    
    # 3. 향상된 CA 번들 생성
    print("\n🔧 향상된 CA 번들 생성...")
    enhanced_bundle = manager.create_enhanced_ca_bundle()
    
    # 4. LangFuse 테스트
    if enhanced_bundle:
        print("\n🚀 LangFuse 클라이언트 테스트 (Windows 최적화)...")
        
        try:
            from langfuse import Langfuse
            print("✅ LangFuse 모듈 import 성공")
            
            # 환경 변수 확인
            secret_key = os.getenv('LANGFUSE_SECRET_KEY')
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
            
            if secret_key and public_key:
                print("🔗 LangFuse 클라이언트 생성 (Windows 인증서 적용)...")
                
                client = Langfuse(
                    secret_key=secret_key,
                    public_key=public_key,
                    host=host
                )
                print("✅ LangFuse 클라이언트 생성 성공")
                
                # 테스트 이벤트 생성
                try:
                    print("📝 테스트 이벤트 생성...")
                    client.create_event(
                        name="windows_cert_test",
                        metadata={
                            "test": True,
                            "platform": "windows",
                            "cert_method": "enhanced_bundle"
                        }
                    )
                    print("✅ 테스트 이벤트 생성 성공!")
                    
                    # 데이터 플러시
                    print("💾 데이터 플러시...")
                    client.flush()
                    print("🎉 모든 Windows SSL 테스트 성공!")
                    
                except Exception as e:
                    print(f"⚠️  이벤트 생성 실패: {e}")
                    
            else:
                print("⚠️  환경 변수가 설정되지 않았습니다.")
                
        except Exception as e:
            print(f"❌ LangFuse 테스트 실패: {e}")
    
    print("\n📋 Windows SSL 문제 해결 단계:")
    print("1. ✅ certifi 패키지 기본 인증서 사용")
    print("2. ✅ Windows 시스템 인증서 저장소 접근")
    print("3. ✅ 향상된 CA 번들 생성")
    print("4. ⚠️  wincertstore 패키지 설치 권장: pip install wincertstore")
    print("5. 📋 수동: certlm.msc에서 회사 인증서 확인")
    
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
except Exception as e:
    print(f"❌ Windows 인증서 테스트 실패: {e}")

print("\n💡 추가 해결 방법:")
print("- 회사 네트워크: IT 부서에 SSL 인증서 문의")
print("- 방화벽: SSL 검사 기능 비활성화 요청")
print("- VPN: VPN 연결 해제 후 테스트")
print("- Self-hosted: docker-compose.langfuse.yml 사용")




