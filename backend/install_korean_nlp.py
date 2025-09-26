"""
한국어 NLP 라이브러리 설치 및 확인 스크립트
"""
import subprocess
import sys
import os

def install_package(package):
    """패키지 설치"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 설치 성공")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 설치 실패: {e}")
        return False

def download_spacy_model():
    """spaCy 한국어 모델 다운로드"""
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "ko_core_news_sm"])
        print("✅ spaCy 한국어 모델 다운로드 성공")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ spaCy 한국어 모델 다운로드 실패: {e}")
        return False

def test_installations():
    """설치된 라이브러리 테스트"""
    print("\n🔍 설치 확인 테스트")
    print("=" * 40)
    
    # KoNLPy 테스트
    try:
        from konlpy.tag import MeCab
        mecab = MeCab()
        result = mecab.morphs("안녕하세요")
        print(f"✅ KoNLPy (MeCab): {result}")
    except Exception as e:
        print(f"❌ KoNLPy 테스트 실패: {e}")
    
    # spaCy 테스트
    try:
        import spacy
        nlp = spacy.load("ko_core_news_sm")
        doc = nlp("보험료 계산")
        tokens = [token.text for token in doc]
        print(f"✅ spaCy: {tokens}")
    except Exception as e:
        print(f"❌ spaCy 테스트 실패: {e}")

def check_java():
    """Java 설치 확인"""
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java 설치 확인됨")
            return True
        else:
            print("❌ Java가 설치되지 않았거나 PATH에 없습니다")
            return False
    except FileNotFoundError:
        print("❌ Java가 설치되지 않았습니다")
        return False

def main():
    """메인 설치 프로세스"""
    print("🚀 한국어 NLP 라이브러리 설치 시작")
    print("=" * 50)
    
    # Java 확인 (KoNLPy에 필요)
    java_ok = check_java()
    if not java_ok:
        print("\n⚠️ Java 설치가 필요합니다:")
        print("1. OpenJDK 다운로드: https://adoptium.net/")
        print("2. 설치 후 환경변수 JAVA_HOME 설정")
        print("3. 시스템 재시작")
        print("4. 다시 이 스크립트 실행")
        return
    
    # 패키지 설치
    packages_to_install = [
        "konlpy",
        "spacy"
    ]
    
    for package in packages_to_install:
        install_package(package)
    
    # spaCy 한국어 모델 다운로드
    download_spacy_model()
    
    # 설치 확인
    test_installations()
    
    print("\n🎉 설치 완료!")
    print("이제 query_processor에서 고급 한국어 처리가 가능합니다.")

if __name__ == "__main__":
    main()

