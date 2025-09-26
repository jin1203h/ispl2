# ISPL Frontend 설치 가이드

## 🔧 의존성 충돌 해결

npm 설치 시 TypeScript ESLint 버전 충돌이 발생할 수 있습니다. 다음 방법으로 해결하세요:

### 방법 1: 권장 방법 (clean install)

```bash
# 1. 기존 node_modules와 lock 파일 삭제
rm -rf node_modules package-lock.json

# 2. npm 캐시 정리
npm cache clean --force

# 3. 의존성 재설치
npm install --legacy-peer-deps
```

### 방법 2: 대안 방법

```bash
# legacy peer deps 플래그 사용
npm install --legacy-peer-deps
```

### 방법 3: yarn 사용 (권장)

```bash
# yarn 설치 (없는 경우)
npm install -g yarn

# yarn으로 의존성 설치
yarn install
```

## 🚀 설치 및 실행 단계

### 1. 프로젝트 폴더로 이동
```bash
cd frontend
```

### 2. Node.js 버전 확인
```bash
node --version  # 18.0.0 이상 필요
npm --version   # 9.0.0 이상 권장
```

### 3. 의존성 설치
```bash
# 방법 1: npm (legacy peer deps)
npm install --legacy-peer-deps

# 방법 2: yarn (권장)
yarn install
```

### 4. 환경변수 설정
```bash
# .env.local 파일 생성
cp env.example .env.local

# 내용 편집
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME="ISPL 보험 정책 AI"
```

### 5. 개발 서버 실행
```bash
# npm 사용
npm run dev

# yarn 사용
yarn dev
```

### 6. 브라우저에서 확인
```
http://localhost:3000
```

## 🔍 문제 해결

### TypeScript 에러
```bash
# 타입 체크
npm run type-check

# TypeScript 캐시 삭제
rm -rf .next
```

### ESLint 에러
```bash
# ESLint 실행
npm run lint

# 자동 수정
npm run lint -- --fix
```

### 빌드 에러
```bash
# 개발 빌드
npm run build

# 프로덕션 실행
npm run start
```

## 📦 의존성 정보

### 핵심 라이브러리
- **Next.js 14**: React 프레임워크
- **React 18**: UI 라이브러리
- **TypeScript 5**: 타입 안전성
- **Tailwind CSS 3**: 스타일링

### API 및 상태 관리
- **Axios**: HTTP 클라이언트
- **React Query 3**: 서버 상태 관리
- **React Hot Toast**: 알림 시스템

### UI 컴포넌트
- **React Markdown**: 마크다운 렌더링
- **Lucide React**: 아이콘 라이브러리
- **clsx**: 조건부 클래스네임

## 🐛 알려진 이슈

### 1. ESLint 버전 충돌
**문제**: @typescript-eslint 버전 불일치
**해결**: `--legacy-peer-deps` 플래그 사용

### 2. React Query 타입 에러
**문제**: React Query v3와 React 18 타입 충돌
**해결**: 이미 package.json에서 호환 버전 지정됨

### 3. Tailwind CSS 인텔리센스
**문제**: VSCode에서 클래스 자동완성 안됨
**해결**: Tailwind CSS IntelliSense 확장 설치

## 💡 개발 팁

### VSCode 확장 프로그램 (권장)
```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense"
  ]
}
```

### 유용한 스크립트
```bash
# 타입 체크 (watch 모드)
npx tsc --noEmit --watch

# Tailwind CSS 클래스 정렬
npx prettier --write "src/**/*.{js,jsx,ts,tsx}"

# 번들 분석
npm run build && npx @next/bundle-analyzer
```

## 🔄 업데이트 가이드

### 의존성 업데이트
```bash
# 모든 패키지 최신 버전 확인
npm outdated

# 안전한 업데이트 (patch/minor)
npm update

# 메이저 버전 업데이트 (주의)
npx npm-check-updates -u
npm install --legacy-peer-deps
```

### Next.js 업데이트
```bash
# Next.js 및 관련 패키지 업데이트
npm install next@latest react@latest react-dom@latest
```

## 📞 지원

문제가 계속 발생하면:
1. `node_modules` 삭제 후 재설치
2. npm 캐시 정리 (`npm cache clean --force`)
3. Node.js 버전 확인 (18.0.0 이상)
4. yarn 사용 시도

---

**개발팀**: ISPL AI Team  
**업데이트**: 2024년 9월 24일

