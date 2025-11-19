# Tesseract OCR 설치 가이드

## Windows 설치

### 1. Tesseract OCR 설치
```bash
# Chocolatey를 통한 설치 (권장)
choco install tesseract

# 또는 직접 다운로드 설치
# https://github.com/UB-Mannheim/tesseract/wiki
# tesseract-ocr-w64-setup-5.3.3.20231005.exe 다운로드 후 설치
```

### 2. 한국어 언어팩 설치
Tesseract 설치 시 Korean 언어팩도 함께 선택하거나:
```bash
# 수동으로 kor.traineddata 파일 다운로드
# https://github.com/tesseract-ocr/tessdata
# C:\Program Files\Tesseract-OCR\tessdata\ 폴더에 복사
```

### 3. 환경 변수 설정 확인
```bash
# PATH에 Tesseract가 포함되어 있는지 확인
tesseract --version

# 환경 변수에 추가 (필요한 경우)
# C:\Program Files\Tesseract-OCR\
```

### 4. Python 패키지 설치
```bash
pip install pytesseract opencv-python pillow
```

## 설치 후 테스트
```python
import pytesseract
print(pytesseract.get_tesseract_version())
```

