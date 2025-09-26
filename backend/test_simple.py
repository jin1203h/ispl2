#!/usr/bin/env python3
"""
간단한 FastAPI 서버 테스트
최소한의 의존성으로 서버 구동 테스트
"""
import sys
import os

# 데이터베이스 의존성 없이 동작하도록 임시 수정
def create_simple_app():
    """최소한의 FastAPI 앱 생성"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel, EmailStr
        
        app = FastAPI(
            title="ISPL Insurance Policy AI - Test",
            description="테스트용 간단한 API",
            version="1.0.0"
        )
        
        # CORS 설정
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 간단한 모델
        class LoginRequest(BaseModel):
            email: str
            password: str
        
        class LoginResponse(BaseModel):
            access_token: str
            token_type: str
            user: dict
        
        # 헬스체크
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "ISPL Insurance Policy AI Backend"}
        
        # 루트
        @app.get("/")
        async def root():
            return {
                "message": "ISPL Insurance Policy AI Backend",
                "version": "1.0.0",
                "docs": "/docs",
                "status": "running"
            }
        
        # 간단한 로그인 (데이터베이스 없이)
        @app.post("/auth/login", response_model=LoginResponse)
        async def login(request: LoginRequest):
            if request.email == "admin@ispl2.com" and request.password == "admin":
                return LoginResponse(
                    access_token="test_token_admin",
                    token_type="bearer",
                    user={
                        "user_id": 1,
                        "email": request.email,
                        "role": "ADMIN"
                    }
                )
            elif request.email == "user@ispl2.com" and request.password == "user":
                return LoginResponse(
                    access_token="test_token_user",
                    token_type="bearer",
                    user={
                        "user_id": 2,
                        "email": request.email,
                        "role": "USER"
                    }
                )
            else:
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        
        # 약관 목록 (임시)
        @app.get("/policies")
        async def get_policies():
            return [
                {
                    "policy_id": 1,
                    "company": "삼성화재",
                    "category": "건강보험",
                    "product_type": "정액형",
                    "product_name": "삼성화재 건강보험 상품",
                    "summary": "기본적인 건강보험 상품으로 입원비와 수술비를 보장합니다.",
                    "created_at": "2024-01-15T10:30:00",
                    "security_level": "public"
                },
                {
                    "policy_id": 2,
                    "company": "현대해상",
                    "category": "자동차보험",
                    "product_type": "종합형",
                    "product_name": "현대해상 자동차보험",
                    "summary": "종합적인 자동차보험으로 대인/대물/자차손해를 보장합니다.",
                    "created_at": "2024-01-20T14:20:00",
                    "security_level": "public"
                }
            ]
        
        # 간단한 검색
        @app.post("/search")
        async def search_policies(request: dict):
            query = request.get("query", "")
            return {
                "answer": f"'{query}'에 대한 검색 결과입니다. 현재 테스트 모드로 동작 중입니다.",
                "results": [
                    {
                        "policy_id": 1,
                        "policy_name": "삼성화재 건강보험 상품",
                        "company": "삼성화재",
                        "relevance_score": 0.95,
                        "matched_text": "검색어와 관련된 내용을 찾았습니다.",
                        "page_number": 1
                    }
                ]
            }
        
        return app
        
    except ImportError as e:
        print(f"필요한 패키지가 설치되지 않았습니다: {e}")
        print("다음 명령어로 설치해주세요:")
        print("pip install fastapi uvicorn pydantic")
        return None

def main():
    """서버 시작"""
    print("=" * 60)
    print("🚀 ISPL Insurance Policy AI - 간단 테스트 서버")
    print("=" * 60)
    
    app = create_simple_app()
    if not app:
        sys.exit(1)
    
    try:
        import uvicorn
        print("✅ 서버 시작 중...")
        print("📍 주소: http://localhost:8000")
        print("📚 API 문서: http://localhost:8000/docs")
        print("🛑 종료: Ctrl+C")
        print("-" * 60)
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="debug"
        )
        
    except ImportError:
        print("❌ uvicorn이 설치되지 않았습니다.")
        print("pip install uvicorn 명령어로 설치해주세요.")
    except KeyboardInterrupt:
        print("\n✅ 서버가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")

if __name__ == "__main__":
    main()
