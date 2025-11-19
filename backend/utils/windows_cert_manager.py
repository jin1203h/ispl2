"""
Windows 환경에서 SSL 인증서 관리
certificates.command 대신 Windows용 인증서 관리 도구들 활용
"""
import os
import ssl
import sys
import subprocess
import tempfile
import certifi
from pathlib import Path


class WindowsCertificateManager:
    """Windows 환경 SSL 인증서 관리자"""
    
    def __init__(self):
        self.certifi_path = certifi.where()
        self.system_cert_store = None
        
    def get_windows_cert_store(self):
        """Windows 시스템 인증서 저장소에서 인증서 추출"""
        print("🔒 Windows 시스템 인증서 저장소 접근...")
        
        try:
            # PowerShell을 사용하여 시스템 인증서 추출
            powershell_script = '''
            Get-ChildItem -Path Cert:\\LocalMachine\\Root | 
            Where-Object { $_.HasPrivateKey -eq $false } |
            Export-Certificate -FilePath "temp_certs.cer" -Type CERT
            '''
            
            # PowerShell 명령 실행
            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                print("✅ Windows 인증서 저장소 접근 성공")
                return True
            else:
                print(f"⚠️  Windows 인증서 저장소 접근 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Windows 인증서 저장소 접근 오류: {e}")
            return False
    
    def export_certificates_certlm(self):
        """certlm.msc (인증서 관리자) 명령어 사용"""
        print("🔒 Windows certlm.msc 활용...")
        
        try:
            # 인증서 관리자 열기 (사용자 확인용)
            print("📋 인증서 관리자를 여는 중...")
            print("   1. certlm.msc가 열리면 '신뢰할 수 있는 루트 인증 기관' 확인")
            print("   2. 회사 인증서가 있는지 확인")
            
            # 비관리자 모드로 실행
            subprocess.Popen(["certlm.msc"], shell=True)
            
            return True
            
        except Exception as e:
            print(f"❌ certlm.msc 실행 실패: {e}")
            return False
    
    def use_certmgr_command(self):
        """certmgr 명령어 사용 (관리자 권한 필요)"""
        print("🔒 certmgr 명령어 활용...")
        
        try:
            # 현재 사용자 인증서 저장소 목록
            result = subprocess.run(
                ["certmgr.exe", "-c", "-s", "Root", "-v"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if result.returncode == 0:
                print("✅ certmgr 명령어 실행 성공")
                print("📋 루트 인증서 목록:")
                # 출력 내용 일부만 표시
                lines = result.stdout.split('\n')[:10]
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                return True
            else:
                print(f"⚠️  certmgr 명령어 실패: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("⚠️  certmgr.exe를 찾을 수 없습니다.")
            return False
        except Exception as e:
            print(f"❌ certmgr 명령어 오류: {e}")
            return False
    
    def create_enhanced_ca_bundle(self):
        """Windows 시스템 인증서를 포함한 향상된 CA 번들 생성"""
        print("🔒 향상된 CA 번들 생성...")
        
        try:
            # 기본 certifi 번들 읽기
            with open(self.certifi_path, 'r', encoding='utf-8') as f:
                certifi_content = f.read()
            
            # Windows 시스템 인증서 추가 시도
            enhanced_bundle_path = Path(__file__).parent / 'enhanced_ca_bundle.pem'
            
            with open(enhanced_bundle_path, 'w', encoding='utf-8') as f:
                f.write(certifi_content)
                f.write('\n# Windows System Certificates\n')
                
                # Windows 시스템 인증서를 추가하는 로직
                # (실제 구현에서는 wincertstore 패키지 사용 권장)
                try:
                    import wincertstore
                    print("   📦 wincertstore 패키지 사용")
                    
                    # Windows 인증서 저장소에서 인증서 추출
                    for cert in wincertstore.CertSystemStore("ROOT"):
                        cert_pem = ssl.DER_cert_to_PEM_cert(cert.get_encoded())
                        f.write(cert_pem)
                        f.write('\n')
                    
                    print("✅ Windows 시스템 인증서 추가 완료")
                    
                except ImportError:
                    print("⚠️  wincertstore 패키지가 없습니다.")
                    print("   pip install wincertstore 로 설치하세요.")
            
            # 환경 변수 설정
            os.environ['REQUESTS_CA_BUNDLE'] = str(enhanced_bundle_path)
            os.environ['SSL_CERT_FILE'] = str(enhanced_bundle_path)
            
            print(f"✅ 향상된 CA 번들 생성: {enhanced_bundle_path}")
            return str(enhanced_bundle_path)
            
        except Exception as e:
            print(f"❌ 향상된 CA 번들 생성 실패: {e}")
            return None
    
    def use_windows_ssl_context(self):
        """Windows 시스템 SSL 컨텍스트 사용"""
        print("🔒 Windows 시스템 SSL 컨텍스트 설정...")
        
        try:
            # Windows 기본 SSL 컨텍스트 생성
            ssl_context = ssl.create_default_context()
            
            # Windows 시스템 인증서 저장소 사용
            ssl_context.load_default_certs()
            
            # 추가 보안 설정
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            print("✅ Windows SSL 컨텍스트 설정 완료")
            return ssl_context
            
        except Exception as e:
            print(f"❌ Windows SSL 컨텍스트 설정 실패: {e}")
            return None
    
    def check_corporate_proxy(self):
        """회사 프록시 설정 확인"""
        print("🔍 회사 프록시 설정 확인...")
        
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        proxy_found = False
        
        for var in proxy_vars:
            value = os.environ.get(var)
            if value:
                print(f"   {var}: {value}")
                proxy_found = True
        
        if not proxy_found:
            print("   프록시 설정이 감지되지 않았습니다.")
        
        # Windows 시스템 프록시 설정 확인
        try:
            import winreg
            
            # Internet Explorer 프록시 설정 확인
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            )
            
            try:
                proxy_enable = winreg.QueryValueEx(key, "ProxyEnable")[0]
                if proxy_enable:
                    proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                    print(f"   시스템 프록시: {proxy_server}")
                    proxy_found = True
            except FileNotFoundError:
                pass
            
            winreg.CloseKey(key)
            
        except ImportError:
            print("   Windows 레지스트리 접근 불가")
        except Exception as e:
            print(f"   프록시 확인 오류: {e}")
        
        return proxy_found
    
    def apply_windows_ssl_fix(self):
        """Windows 환경에 맞는 SSL 수정 적용"""
        print("🔧 Windows SSL 인증서 문제 수정 시도...")
        
        # 1. 프록시 설정 확인
        self.check_corporate_proxy()
        
        # 2. 향상된 CA 번들 생성 시도
        enhanced_bundle = self.create_enhanced_ca_bundle()
        
        # 3. Windows SSL 컨텍스트 설정
        ssl_context = self.use_windows_ssl_context()
        
        # 4. 인증서 관리자 정보 제공
        print("\n📋 수동 해결 방법:")
        print("1. Windows 키 + R → certlm.msc")
        print("2. '신뢰할 수 있는 루트 인증 기관' 확인")
        print("3. 회사 인증서가 있다면 PEM 형식으로 내보내기")
        print("4. certifi 번들에 추가")
        
        return enhanced_bundle is not None


def windows_certificate_setup():
    """Windows 환경 인증서 설정 메인 함수"""
    print("🪟 Windows 환경 SSL 인증서 설정")
    print("=" * 50)
    
    manager = WindowsCertificateManager()
    
    # Windows SSL 수정 적용
    success = manager.apply_windows_ssl_fix()
    
    if success:
        print("✅ Windows SSL 설정 완료")
    else:
        print("⚠️  일부 설정이 실패했지만 계속 진행합니다.")
    
    return success


if __name__ == "__main__":
    windows_certificate_setup()




