"""
SSL 인증서 문제 해결 유틸리티
certifi를 활용한 다양한 SSL 설정 방법
"""
import os
import ssl
import sys
import certifi
import requests
import urllib3
from pathlib import Path


class SSLCertificateFixer:
    """SSL 인증서 문제 해결 클래스"""
    
    def __init__(self):
        self.certifi_path = certifi.where()
        self.custom_ca_bundle = None
        
    def method_1_certifi_bundle(self):
        """방법 1: certifi 인증서 번들 사용"""
        print(f"🔒 방법 1: certifi 인증서 번들 사용")
        print(f"   인증서 경로: {self.certifi_path}")
        
        # 환경 변수 설정
        os.environ['REQUESTS_CA_BUNDLE'] = self.certifi_path
        os.environ['SSL_CERT_FILE'] = self.certifi_path
        
        # urllib3 설정
        urllib3.util.ssl_.DEFAULT_CIPHERS += ':!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA'
        
        return self.certifi_path
    
    def method_2_custom_ca_bundle(self):
        """방법 2: 회사 인증서를 certifi 번들에 추가"""
        print(f"🔒 방법 2: 사용자 정의 CA 번들 생성")
        
        # 기본 certifi 번들 읽기
        with open(self.certifi_path, 'rb') as f:
            original_bundle = f.read()
        
        # 사용자 정의 번들 경로
        custom_bundle_path = Path(__file__).parent / 'custom_ca_bundle.pem'
        
        # 기본 번들을 사용자 정의 경로에 복사
        with open(custom_bundle_path, 'wb') as f:
            f.write(original_bundle)
        
        # 회사 인증서가 있다면 추가 (예시)
        company_cert_path = Path(__file__).parent / 'company_cert.pem'
        if company_cert_path.exists():
            print(f"   회사 인증서 추가: {company_cert_path}")
            with open(company_cert_path, 'rb') as company_cert:
                with open(custom_bundle_path, 'ab') as custom_bundle:
                    custom_bundle.write(b'\n')
                    custom_bundle.write(company_cert.read())
        
        self.custom_ca_bundle = str(custom_bundle_path)
        
        # 환경 변수 설정
        os.environ['REQUESTS_CA_BUNDLE'] = self.custom_ca_bundle
        os.environ['SSL_CERT_FILE'] = self.custom_ca_bundle
        
        return self.custom_ca_bundle
    
    def method_3_ssl_context(self):
        """방법 3: SSL 컨텍스트 직접 설정"""
        print(f"🔒 방법 3: SSL 컨텍스트 직접 설정")
        
        # SSL 컨텍스트 생성
        ssl_context = ssl.create_default_context(cafile=self.certifi_path)
        
        # 보안 설정 강화
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        return ssl_context
    
    def method_4_requests_session(self):
        """방법 4: requests 세션에 인증서 설정"""
        print(f"🔒 방법 4: requests 세션 인증서 설정")
        
        session = requests.Session()
        session.verify = self.certifi_path
        
        # 추가 헤더 설정
        session.headers.update({
            'User-Agent': 'ISPL-LangFuse-Client/1.0',
            'Accept': 'application/json',
        })
        
        return session
    
    def test_ssl_connection(self, url="https://cloud.langfuse.com"):
        """SSL 연결 테스트"""
        print(f"\n🔍 SSL 연결 테스트: {url}")
        
        methods = [
            ("기본 requests", self._test_basic_requests),
            ("certifi 번들", self._test_with_certifi),
            ("사용자 정의 번들", self._test_with_custom_bundle),
            ("requests 세션", self._test_with_session),
        ]
        
        results = {}
        
        for method_name, test_func in methods:
            try:
                print(f"  📡 {method_name} 테스트...")
                success = test_func(url)
                results[method_name] = success
                print(f"    {'✅ 성공' if success else '❌ 실패'}")
            except Exception as e:
                results[method_name] = False
                print(f"    ❌ 실패: {e}")
        
        return results
    
    def _test_basic_requests(self, url):
        """기본 requests 테스트"""
        response = requests.get(url, timeout=10)
        return response.status_code < 400
    
    def _test_with_certifi(self, url):
        """certifi 번들로 테스트"""
        self.method_1_certifi_bundle()
        response = requests.get(url, verify=self.certifi_path, timeout=10)
        return response.status_code < 400
    
    def _test_with_custom_bundle(self, url):
        """사용자 정의 번들로 테스트"""
        if not self.custom_ca_bundle:
            self.method_2_custom_ca_bundle()
        response = requests.get(url, verify=self.custom_ca_bundle, timeout=10)
        return response.status_code < 400
    
    def _test_with_session(self, url):
        """requests 세션으로 테스트"""
        session = self.method_4_requests_session()
        response = session.get(url, timeout=10)
        return response.status_code < 400
    
    def apply_best_fix(self):
        """가장 적합한 SSL 수정 방법 적용"""
        print("🔧 SSL 인증서 문제 자동 수정 시도...")
        
        # 테스트 순서 (안전한 순서대로)
        fixes = [
            ("certifi 번들 설정", self.method_1_certifi_bundle),
            ("사용자 정의 번들", self.method_2_custom_ca_bundle),
        ]
        
        for fix_name, fix_method in fixes:
            try:
                print(f"  🔧 {fix_name} 적용 중...")
                result = fix_method()
                
                # 간단한 연결 테스트
                test_result = self._test_with_certifi("https://httpbin.org/get")
                if test_result:
                    print(f"  ✅ {fix_name} 성공!")
                    return result
                    
            except Exception as e:
                print(f"  ❌ {fix_name} 실패: {e}")
                continue
        
        print("  ⚠️  모든 자동 수정 방법 실패")
        return None


def setup_ssl_for_langfuse():
    """LangFuse용 SSL 설정 (OS별 최적화)"""
    print("🔒 LangFuse용 SSL 인증서 설정")
    
    # Windows 환경 특별 처리
    if sys.platform == "win32":
        print("🪟 Windows 환경 감지 - 특별 SSL 설정 적용")
        try:
            from utils.windows_cert_manager import windows_certificate_setup
            windows_certificate_setup()
        except ImportError:
            print("⚠️  Windows 인증서 관리자 모듈 로드 실패, 기본 방법 사용")
    
    fixer = SSLCertificateFixer()
    
    # 자동 수정 시도
    result = fixer.apply_best_fix()
    
    if result:
        print(f"✅ SSL 설정 완료: {result}")
        
        # LangFuse 연결 테스트
        try:
            print("🔍 LangFuse 연결 테스트...")
            test_results = fixer.test_ssl_connection("https://cloud.langfuse.com")
            
            success_count = sum(test_results.values())
            total_count = len(test_results)
            
            if success_count > 0:
                print(f"✅ SSL 연결 성공! ({success_count}/{total_count} 방법 성공)")
                return True
            else:
                print("❌ 모든 SSL 연결 방법 실패")
                return False
                
        except Exception as e:
            print(f"❌ LangFuse 연결 테스트 실패: {e}")
            return False
    else:
        print("❌ SSL 설정 실패")
        return False


if __name__ == "__main__":
    # SSL 설정 테스트
    setup_ssl_for_langfuse()
