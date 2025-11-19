# Java 설치 및 tabula-py 설정 가이드

## Windows에서 Java 설치

### 1. Java 설치
```bash
# Option 1: Oracle JDK (추천)
# https://www.oracle.com/java/technologies/downloads/ 에서 다운로드

# Option 2: OpenJDK via Chocolatey
choco install openjdk

# Option 3: OpenJDK via winget
winget install Microsoft.OpenJDK.17
```

### 2. 환경변수 설정
```bash
# 시스템 환경변수에 추가
JAVA_HOME=C:\Program Files\Java\jdk-17
PATH=%JAVA_HOME%\bin;%PATH%
```

### 3. 설치 확인
```bash
java -version
javac -version
```

### 4. tabula-py 재설치
```bash
pip uninstall tabula-py
pip install tabula-py
```

## 대안: Java 없이 강화된 표 추출

### pdfplumber 기반 표 추출 강화
- pdfplumber의 고급 기능 활용
- 표 영역 수동 지정
- 컨텍스트 기반 표 탐지


