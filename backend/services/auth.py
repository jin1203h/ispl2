"""
인증 관련 서비스
JWT 토큰 생성, 검증, 비밀번호 해싱
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 실제 패키지들 import
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import User

logger = logging.getLogger(__name__)

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

class AuthService:
    """인증 서비스 클래스"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        # 개발용: 평문 비밀번호 비교 (init.sql의 'admin', 'user')
        if plain_password == hashed_password:
            return True
        
        # 실제 해싱된 비밀번호 검증
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"JWT 토큰 검증 실패: {e}")
            return None
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """사용자 인증"""
        try:
            # 사용자 조회
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"사용자를 찾을 수 없음: {email}")
                return None
            
            # 비밀번호 검증
            if not AuthService.verify_password(password, user.password_hash):
                logger.warning(f"비밀번호 불일치: {email}")
                return None
            
            logger.info(f"사용자 인증 성공: {email}")
            return user
            
        except Exception as e:
            logger.error(f"사용자 인증 오류: {e}")
            return None
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        try:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"사용자 조회 오류: {e}")
            return None
    
    @staticmethod
    async def create_user(db: AsyncSession, email: str, password: str, role: str = "USER") -> Optional[User]:
        """새 사용자 생성"""
        try:
            # 중복 이메일 확인
            existing_user = await AuthService.get_user_by_email(db, email)
            if existing_user:
                logger.warning(f"이미 존재하는 이메일: {email}")
                return None
            
            # 비밀번호 해싱
            hashed_password = AuthService.hash_password(password)
            
            # 새 사용자 생성
            new_user = User(
                email=email,
                password_hash=hashed_password,
                role=role
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            logger.info(f"새 사용자 생성 완료: {email}")
            return new_user
            
        except Exception as e:
            logger.error(f"사용자 생성 오류: {e}")
            await db.rollback()
            return None
