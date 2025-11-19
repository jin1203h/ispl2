"""
인증 관련 API 라우터
기존 프론트엔드 authAPI와 완전 호환
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.database import get_db_session
from services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Pydantic 모델 - 기존 프론트엔드 API 호환
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "USER"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserInfo(BaseModel):
    user_id: int
    email: str
    role: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    """
    사용자 로그인
    기존 프론트엔드 authAPI.login()과 호환
    """
    try:
        logger.info(f"🔐 로그인 API 호출 받음: {request.email}")
        logger.debug(f"로그인 API 호출: {request.email}")
        logger.info(f"로그인 시도: {request.email}")
        
        # 사용자 인증
        logger.debug("사용자 인증 서비스 호출")
        user = await AuthService.authenticate_user(db, request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다."
            )
        
        # JWT 토큰 생성
        logger.debug(f"사용자 인증 성공: {user.email}, 역할: {user.role}")
        token_data = {
            "sub": user.email,
            "user_id": user.user_id,
            "role": user.role
        }
        logger.debug("JWT 토큰 생성 중")
        access_token = AuthService.create_access_token(token_data)
        logger.debug(f"JWT 토큰 생성 완료: {access_token[:20]}...")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role
            }
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    """
    사용자 회원가입
    기존 프론트엔드 authAPI.register()와 호환
    """
    try:
        logger.info(f"회원가입 시도: {request.email}")
        
        # 사용자 생성
        user = await AuthService.create_user(db, request.email, request.password, request.role)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 이메일이거나 회원가입에 실패했습니다."
            )
        
        return {
            "message": "회원가입이 완료되었습니다.",
            "user": {
                "email": user.email,
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회원가입 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다."
        )

@router.get("/verify", response_model=UserInfo)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    토큰 검증
    기존 프론트엔드 authAPI.verifyToken()과 호환
    """
    try:
        token = credentials.credentials
        logger.info(f"토큰 검증 요청: {token[:20]}...")
        
        # JWT 토큰 검증
        payload = AuthService.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        
        return UserInfo(
            user_id=payload.get("user_id"),
            email=payload.get("sub"),
            role=payload.get("role")
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 검증 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 검증 중 오류가 발생했습니다."
        )

# 토큰 검증을 위한 의존성 함수
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """현재 사용자 정보 반환 (의존성 함수)"""
    try:
        token = credentials.credentials
        payload = AuthService.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        return payload
    except Exception as e:
        logger.error(f"사용자 인증 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다."
        )
