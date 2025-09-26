#!/usr/bin/env python3
"""
기존 메모리 정책들을 실제 DB에 저장하는 스크립트
"""
import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def fix_existing_policies():
    """기존 메모리 정책들을 DB에 저장"""
    try:
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        
        # 임시 정책 데이터 (기존 TEMP_POLICIES와 동일)
        temp_policies = [
            {
                "policy_id": 1,
                "company": "삼성화재",
                "category": "건강보험",
                "product_type": "정액형",
                "product_name": "삼성화재 건강보험 상품",
                "summary": "기본적인 건강보험 상품으로 입원비와 수술비를 보장합니다.",
                "security_level": "public"
            },
            {
                "policy_id": 2,
                "company": "현대해상",
                "category": "자동차보험",
                "product_type": "종합형",
                "product_name": "현대해상 자동차보험",
                "summary": "종합적인 자동차보험으로 대인/대물/자차손해를 보장합니다.",
                "security_level": "public"
            },
            {
                "policy_id": 3,
                "company": "업로드된회사",
                "category": "업로드된카테고리",
                "product_type": "일반형",
                "product_name": "업로드된 PDF 파일",
                "summary": "최근 업로드된 정책입니다.",
                "security_level": "public"
            }
        ]
        
        async with get_async_session() as db:
            for temp_policy in temp_policies:
                # 기존 정책 확인
                stmt = select(Policy).where(Policy.policy_id == temp_policy["policy_id"])
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"✅ Policy {temp_policy['policy_id']} 이미 존재: {existing.product_name}")
                    continue
                
                # 새 정책 생성
                current_date = datetime.now()
                new_policy = Policy(
                    policy_id=temp_policy["policy_id"],  # 기존 ID 유지
                    company=temp_policy["company"],
                    category=temp_policy["category"],
                    product_type=temp_policy["product_type"],
                    product_name=temp_policy["product_name"],
                    summary=temp_policy["summary"],
                    created_at=current_date,
                    security_level=temp_policy["security_level"],
                    sale_start_dt=current_date.strftime('%Y%m%d'),
                    sale_end_dt=current_date.strftime('%Y%m%d'),
                    sale_stat="Y"
                )
                
                db.add(new_policy)
                print(f"📝 Policy {temp_policy['policy_id']} 추가: {temp_policy['product_name']}")
            
            await db.commit()
            print("✅ 모든 정책 DB 저장 완료!")
        
        return True
        
    except Exception as e:
        print(f"❌ 정책 저장 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("기존 메모리 정책들을 DB에 저장")
    print("=" * 60)
    
    success = asyncio.run(fix_existing_policies())
    
    if success:
        print("\n🎉 기존 정책들이 DB에 저장되었습니다!")
        print("이제 Foreign Key 오류가 해결됩니다.")
    else:
        print("\n🚨 정책 저장 실패!")
