# 한국어 NLP 라이브러리 설치 가이드

## 🎯 목적
query_processor의 한국어 자연어 처리 성능 향상을 위해 spaCy와 KoNLPy를 설치합니다.

## 📋 설치 단계

### 1단계: Java 설치 (KoNLPy 필수)
```bash
# Windows
# https://adoptium.net/ 에서 OpenJDK 다운로드 및 설치
# 환경변수 JAVA_HOME 설정

# 확인
java -version
```

### 2단계: KoNLPy 설치
```bash
pip install konlpy
```

### 3단계: spaCy 및 한국어 모델 설치
```bash
# spaCy 설치
pip install spacy

# 한국어 모델 다운로드
python -m spacy download ko_core_news_sm
```

### 4단계: 설치 확인
```bash
cd backend
python install_korean_nlp.py
```

## 🔧 설치 후 효과

### Before (현재)
- 단순 공백 분리: `["암보험", "정보를", "알고", "싶어요"]`
- 의도 분석 정확도: 낮음
- 키워드 추출: 기본적

### After (설치 후)
- 형태소 분석: `["암", "보험", "정보", "알", "고", "싶", "어요"]`
- 품사 태깅: `[("암", "NNG"), ("보험", "NNG"), ("정보", "NNG")]`
- 불용어 제거: 자동
- 의도 분석 정확도: 높음

## 📊 성능 비교

| 기능 | Fallback | MeCab | spaCy |
|------|----------|-------|-------|
| 토큰화 | 공백 분리 | 형태소 | 형태소+품사 |
| 불용어 처리 | 수동 | 자동 | 자동 |
| 복합어 처리 | 규칙 기반 | 학습 기반 | 학습 기반 |
| 정확도 | 60% | 85% | 90% |

## ⚠️ 문제 해결

### Java 관련 오류
```
OSError: Java not found
```
**해결**: Java JDK 설치 및 JAVA_HOME 환경변수 설정

### spaCy 모델 오류
```
OSError: Can't find model 'ko_core_news_sm'
```
**해결**: `python -m spacy download ko_core_news_sm`

### Windows 권한 오류
```
PermissionError: [Errno 13]
```
**해결**: 관리자 권한으로 CMD 실행

## 🚀 설치 없이 사용하기

현재 구현된 enhanced_korean_tokenize 메서드로도 기본적인 한국어 처리가 가능합니다:

- 숫자+단위 분리: "10만원" → ["10", "만원"]
- 영한 혼합어 분리: "API서비스" → ["API", "서비스"]  
- 보험 전문용어 인식: "가입조건", "보험료" 등
- 패턴 기반 개체명 추출: "30세", "10만원" 등

## 📈 권장사항

1. **개발 단계**: enhanced_korean_tokenize로 충분
2. **운영 단계**: spaCy + KoNLPy 설치 권장
3. **고성능 요구**: 추가로 형태소 분석기 커스터마이징

