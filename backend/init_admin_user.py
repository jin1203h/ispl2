#!/usr/bin/env python3
"""
기본 관리자 계정 생성 스크립트
데이터베이스에 admin@ispl2.com 계정을 생성합니다.
"""
import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def create_admin_user():
    """기본 관리자 계정 생성"""
    try:
        from services.database import get_async_session
        from models.database import User
        from services.auth import AuthService
        from sqlalchemy import select
        
        async with get_async_session() as db:
            # 기존 관리자 계정 확인
            stmt = select(User).where(User.email == "admin@ispl2.com")
            result = await db.execute(stmt)
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print(f"✅ 관리자 계정이 이미 존재합니다: {existing_admin.email}")
                return True
            
            # 새 관리자 계정 생성
            hashed_password = AuthService.hash_password("admin")
            
            admin_user = User(
                email="admin@ispl2.com",
                password=hashed_password,
                role="ADMIN",
                created_at=datetime.now()
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            print(f"🎉 관리자 계정 생성 완료!")
            print(f"   이메일: admin@ispl2.com")
            print(f"   비밀번호: admin")
            print(f"   역할: ADMIN")
            print(f"   사용자 ID: {admin_user.user_id}")
            
            # 일반 사용자 계정도 생성
            stmt = select(User).where(User.email == "user@ispl2.com")
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                user_password = AuthService.hash_password("user")
                regular_user = User(
                    email="user@ispl2.com",
                    password=user_password,
                    role="USER",
                    created_at=datetime.now()
                )
                
                db.add(regular_user)
                await db.commit()
                await db.refresh(regular_user)
                
                print(f"🎉 일반 사용자 계정 생성 완료!")
                print(f"   이메일: user@ispl2.com")
                print(f"   비밀번호: user")
                print(f"   역할: USER")
                print(f"   사용자 ID: {regular_user.user_id}")
            
        
        return True
        
    except Exception as e:
        print(f"❌ 사용자 계정 생성 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("기본 사용자 계정 생성")
    print("=" * 60)
    
    success = asyncio.run(create_admin_user())
    
    if success:
        print("\n🎉 모든 기본 계정이 생성되었습니다!")
        print("이제 데이터베이스 기반 인증을 사용할 수 있습니다.")
    else:
        print("\n🚨 계정 생성 실패!")
