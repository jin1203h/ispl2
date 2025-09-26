"""
간단한 인증 라우터 (데이터베이스 연결 문제 해결용)
임시로 하드코딩된 사용자로 테스트
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import logging

from services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Pydantic 모델
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "USER"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# 임시 하드코딩된 사용자 (테스트용)
TEMP_USERS = {
    "admin@ispl2.com": {
        "user_id": 1,
        "email": "admin@ispl2.com",
        "password": "admin",
        "role": "ADMIN"
    },
    "user@ispl2.com": {
        "user_id": 2,
        "email": "user@ispl2.com", 
        "password": "user",
        "role": "USER"
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """간단한 로그인 (하드코딩된 사용자)"""
    try:
        logger.info(f"간단 로그인 시도: {request.email}")
        
        # 하드코딩된 사용자 확인
        if request.email not in TEMP_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다."
            )
        
        user_data = TEMP_USERS[request.email]
        
        # 비밀번호 확인
        if request.password != user_data["password"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호가 올바르지 않습니다."
            )
        
        # JWT 토큰 생성
        token_data = {
            "sub": user_data["email"],
            "user_id": user_data["user_id"],
            "role": user_data["role"]
        }
        
        access_token = AuthService.create_access_token(token_data)
        
        logger.info(f"간단 로그인 성공: {user_data['email']}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"간단 로그인 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """간단한 회원가입 (메모리에만 저장)"""
    try:
        logger.info(f"간단 회원가입 시도: {request.email}")
        
        # 이미 존재하는 사용자 확인
        if request.email in TEMP_USERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 이메일입니다."
            )
        
        # 새 사용자 추가 (메모리에만)
        new_user_id = max([u["user_id"] for u in TEMP_USERS.values()]) + 1
        TEMP_USERS[request.email] = {
            "user_id": new_user_id,
            "email": request.email,
            "password": request.password,
            "role": request.role
        }
        
        # JWT 토큰 생성
        token_data = {
            "sub": request.email,
            "user_id": new_user_id,
            "role": request.role
        }
        
        access_token = AuthService.create_access_token(token_data)
        
        logger.info(f"간단 회원가입 성공: {request.email}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "user_id": new_user_id,
                "email": request.email,
                "role": request.role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"간단 회원가입 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다."
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 사용자 정보 조회 (JWT 토큰 기반)"""
    try:
        token = credentials.credentials
        payload = AuthService.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰에서 사용자 정보를 찾을 수 없습니다."
            )
        
        # 하드코딩된 사용자에서 확인
        if email not in TEMP_USERS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다."
            )
        
        return TEMP_USERS[email]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 인증 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증에 실패했습니다."
        )

@router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """토큰 검증"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"]
    }
