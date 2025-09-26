# ISPL 보험 정책 AI - Frontend

React + Next.js 기반의 보험약관 AI 검색 웹 애플리케이션

## 🚀 주요 기능

### 📱 **GPT 스타일 채팅 UI**
- 자연어 질의로 보험 약관 검색
- 실시간 답변 생성 및 출처 표시
- 대화 세션 관리 (저장, 로드, 삭제)
- 메시지 히스토리 및 검색 결과 추적

### 🎯 **사이드바 기능**
- **AI 채팅**: 메인 검색 인터페이스
- **약관 관리**: 파일 업로드, 목록 조회, 다운로드
- **워크플로우**: Multi-Agent 처리 과정 모니터링
- **설정**: 앱 설정 및 환경 구성

### 🔍 **고급 검색 기능**
- 벡터 유사도 + 키워드 하이브리드 검색
- 검색 결과 실시간 표시 및 상세 정보
- 관련도 점수 및 출처 정보 제공
- 회사별, 카테고리별 결과 분류

### 💡 **사용자 경험**
- 반응형 디자인 (모바일, 태블릿, 데스크톱)
- 다크/라이트 테마 지원 (구현 예정)
- 키보드 단축키 지원
- 실시간 로딩 상태 및 에러 처리

## 🛠 기술 스택

### **프론트엔드**
- **Next.js 14** - React 프레임워크
- **TypeScript** - 타입 안전성
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **React Query** - 서버 상태 관리
- **React Markdown** - 마크다운 렌더링

### **상태 관리**
- **Custom Hooks** - 채팅, API 호출 로직
- **Local Storage** - 세션 영속성
- **React Query** - API 캐싱 및 동기화

### **UI 컴포넌트**
- **Lucide React** - 아이콘 라이브러리
- **React Hot Toast** - 알림 시스템
- **Framer Motion** - 애니메이션 (구현 예정)
- **React Dropzone** - 파일 업로드 (구현 예정)

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # 루트 레이아웃
│   │   ├── page.tsx           # 메인 페이지
│   │   └── globals.css        # 글로벌 스타일
│   ├── components/            # React 컴포넌트
│   │   ├── chat/              # 채팅 관련 컴포넌트
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── SearchResults.tsx
│   │   └── layout/            # 레이아웃 컴포넌트
│   │       └── Sidebar.tsx
│   ├── hooks/                 # Custom React Hooks
│   │   └── useChat.ts        # 채팅 상태 관리
│   ├── services/              # API 서비스
│   │   └── api.ts            # Backend API 통신
│   ├── types/                 # TypeScript 타입
│   │   └── api.ts            # API 타입 정의
│   └── utils/                 # 유틸리티 함수
├── public/                    # 정적 파일
├── package.json              # 의존성 및 스크립트
├── next.config.js            # Next.js 설정
├── tailwind.config.js        # Tailwind CSS 설정
├── tsconfig.json             # TypeScript 설정
└── env.example               # 환경변수 예시
```

## 🚀 시작하기

### **개발 환경 요구사항**
- Node.js 18.0.0 이상
- npm 또는 yarn

### **설치 및 실행**

1. **의존성 설치**
```bash
cd frontend
npm install
```

2. **환경변수 설정**
```bash
cp env.example .env.local
```

3. **개발 서버 실행**
```bash
npm run dev
```

4. **브라우저에서 확인**
```
http://localhost:3000
```

### **빌드 및 배포**
```bash
# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행
npm run start

# 타입 체크
npm run type-check

# 린터 실행
npm run lint
```

## 🔧 환경 설정

### **환경변수 (.env.local)**
```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# 앱 설정
NEXT_PUBLIC_APP_NAME="ISPL 보험 정책 AI"
NEXT_PUBLIC_APP_VERSION="1.0.0"

# 기능 활성화
NEXT_PUBLIC_ENABLE_WORKFLOW_MONITORING=true
NEXT_PUBLIC_ENABLE_MCP_INTEGRATION=false

# UI 설정
NEXT_PUBLIC_THEME_DEFAULT=light
NEXT_PUBLIC_CHAT_MAX_MESSAGES=100
NEXT_PUBLIC_SIDEBAR_WIDTH=280
```

## 📱 화면 구성

### **메인 레이아웃**
```
┌─────────────────────────────────────────────────────────┐
│ Header: ISPL 보험 정책 AI | 상태 | 사용자 메뉴         │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  Sidebar     │         Main Content                     │
│              │                                          │
│ ┌──────────┐ │  ┌────────────────────────────────────┐  │
│ │ 새 대화   │ │  │                                    │  │
│ └──────────┘ │  │          Chat Interface            │  │
│              │  │                                    │  │
│ Navigation:  │  │  ┌──────────────────────────────┐   │  │
│ • AI 채팅    │ │  │                              │   │  │
│ • 약관 관리   │ │  │        Chat Messages         │   │  │
│ • 워크플로우  │ │  │                              │   │  │
│ • 설정       │ │  └──────────────────────────────┘   │  │
│              │  │                                    │  │
│ Recent Chats │  │  ┌──────────────────────────────┐   │  │
│ • 대화 1     │ │  │        Chat Input            │   │  │
│ • 대화 2     │ │  └──────────────────────────────┘   │  │
│ • 대화 3     │ │                                    │  │
│              │  └────────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────────┘
```

### **채팅 인터페이스**
- **빈 상태**: 환영 메시지 + 예시 질문 버튼들
- **대화 중**: 메시지 목록 + 검색 결과 사이드바 (선택적)
- **입력 영역**: 텍스트 입력 + 예시 질문 + 전송 버튼

## 🎨 디자인 시스템

### **색상 팔레트**
- **Primary**: Blue (#3b82f6) - 브랜드 컬러
- **Secondary**: Gray (#6b7280) - 보조 컬러
- **Success**: Green (#10b981) - 성공/건강보험
- **Warning**: Amber (#f59e0b) - 경고/자동차보험
- **Error**: Red (#ef4444) - 오류/재산보험
- **Info**: Purple (#8b5cf6) - 정보/생명보험

### **타이포그래피**
- **Font Family**: Inter (Korean support)
- **Headings**: 16px-24px, 600-700 weight
- **Body**: 14px-16px, 400-500 weight
- **Small**: 12px-13px, 400 weight

### **컴포넌트 스타일**
- **Border Radius**: 0.5rem (8px) - 기본, 1rem (16px) - 카드
- **Shadows**: Subtle drop shadows
- **Transitions**: 200-300ms ease

## 🔄 API 연동

### **Backend API 엔드포인트**
```typescript
// 검색
POST /search
{
  query: string,
  policy_ids?: number[],
  limit?: number
}

// 약관 관리
GET    /policies           # 약관 목록
POST   /policies/upload    # 약관 업로드
GET    /policies/{id}      # 약관 상세
DELETE /policies/{id}      # 약관 삭제

// 워크플로우
GET /workflow/status/{id}     # 처리 상태
GET /workflow/executions      # 실행 기록

// 인증 (구현 예정)
POST /auth/login             # 로그인
POST /auth/logout            # 로그아웃
```

### **데이터 타입**
```typescript
interface SearchResponse {
  answer: string;
  results: SearchResult[];
}

interface SearchResult {
  policy_id: number;
  policy_name: string;
  company: string;
  relevance_score: number;
  matched_text: string;
  page_number?: number;
}
```

## 🧪 테스트 (구현 예정)

### **테스트 프레임워크**
- **Jest** - 단위 테스트
- **React Testing Library** - 컴포넌트 테스트
- **Cypress** - E2E 테스트

### **테스트 커버리지**
- 핵심 비즈니스 로직: 90% 이상
- React 컴포넌트: 80% 이상
- API 통신 로직: 95% 이상

## 📈 성능 최적화

### **코드 분할**
- **Dynamic imports** - 페이지별 코드 분할
- **Component lazy loading** - 조건부 컴포넌트 지연 로딩

### **번들 최적화**
- **Tree shaking** - 사용하지 않는 코드 제거
- **Code compression** - Gzip/Brotli 압축

### **캐싱 전략**
- **React Query** - API 응답 캐싱
- **Browser cache** - 정적 리소스 캐싱
- **Service Worker** - 오프라인 지원 (구현 예정)

## 🔒 보안

### **데이터 보호**
- **HTTPS only** - SSL/TLS 암호화
- **CSP headers** - XSS 공격 방지
- **Input validation** - 사용자 입력 검증

### **인증 및 권한**
- **JWT tokens** - 토큰 기반 인증
- **Role-based access** - 역할 기반 접근 제어
- **Secure storage** - 민감 정보 안전 저장

## 🔮 향후 계획

### **Phase 1 (현재)**
- ✅ 기본 채팅 인터페이스
- ✅ 검색 결과 표시
- ✅ 세션 관리

### **Phase 2 (구현 예정)**
- 📄 약관 업로드 UI
- 📊 워크플로우 모니터링 대시보드
- ⚙️ 설정 페이지

### **Phase 3 (향후)**
- 🌙 다크 모드
- 📱 PWA 지원
- 🔄 실시간 알림
- 📈 사용 통계 대시보드

## 🤝 기여하기

### **개발 가이드라인**
1. **코드 스타일**: Prettier + ESLint
2. **커밋 메시지**: Conventional Commits
3. **브랜치 전략**: Git Flow
4. **코드 리뷰**: Pull Request 필수

### **이슈 리포팅**
- 버그 리포트는 재현 단계와 함께
- 기능 요청은 사용 사례와 함께
- 성능 이슈는 프로파일링 데이터와 함께

## 📄 라이선스

이 프로젝트는 ISPL 팀의 소유입니다.

---

**개발팀**: ISPL AI Team  
**버전**: 1.0.0  
**마지막 업데이트**: 2024년 9월 24일

