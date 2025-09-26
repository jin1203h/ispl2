"""
약관 관리 API 라우터
기존 프론트엔드 policyAPI와 완전 호환
Multi-Agent 시스템과 연계하여 자동 처리
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import re
import logging
import os
import time
import asyncio
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

def secure_filename(filename: str) -> str:
    """
    파일명을 안전하게 만드는 함수
    특수문자를 제거하고 안전한 파일명으로 변환
    """
    # 파일명에서 확장자 분리
    name, ext = os.path.splitext(filename)
    
    # 특수문자 제거 및 공백을 언더스코어로 변경
    safe_name = re.sub(r'[^\w\s-]', '', name)  # 영문, 숫자, 공백, 하이픈만 허용
    safe_name = re.sub(r'[-\s]+', '_', safe_name)  # 공백과 하이픈을 언더스코어로 변경
    safe_name = safe_name.strip('_')  # 앞뒤 언더스코어 제거
    
    # 빈 문자열인 경우 기본 이름 사용
    if not safe_name:
        safe_name = "unnamed"
    
    return safe_name + ext

async def copy_outputs_markdown_to_uploads(policy_id: int):
    """
    outputs/markdown/ 폴더의 MD 파일을 uploads/ 폴더로 복사
    """
    try:
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        import shutil
        
        async with get_async_session() as db:
            # DB에서 약관 정보 조회
            stmt = select(Policy).where(Policy.policy_id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if not policy:
                logger.error(f"약관 {policy_id}: DB에서 약관을 찾을 수 없음")
                return False
            
            # outputs/markdown/ 폴더에서 MD 파일 찾기
            outputs_markdown_dir = Path("outputs/markdown")
            if not outputs_markdown_dir.exists():
                logger.warning(f"약관 {policy_id}: outputs/markdown 폴더가 없습니다")
                return False
            
            # 가장 최근 생성된 MD 파일 찾기 (policy_id 또는 product_name으로)
            md_files = list(outputs_markdown_dir.glob("*.md"))
            if not md_files:
                logger.warning(f"약관 {policy_id}: outputs/markdown에 MD 파일이 없습니다")
                return False
            
            # 가장 최근 파일 선택
            latest_md_file = max(md_files, key=lambda x: x.stat().st_mtime)
            
            # uploads 폴더로 복사
            if policy.md_path:
                target_path = Path(policy.md_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(latest_md_file, target_path)
                
                logger.info(f"✅ 약관 {policy_id}: MD 파일 복사 완료")
                logger.info(f"   원본: {latest_md_file}")
                logger.info(f"   대상: {target_path}")
                return True
            else:
                logger.error(f"약관 {policy_id}: MD 경로가 DB에 설정되지 않음")
                return False
                
    except Exception as e:
        logger.error(f"약관 {policy_id}: MD 파일 복사 실패 - {e}")
        return False

# Multi-Agent 시스템 초기화 (조건부)
try:
    from agents.supervisor import SupervisorAgent
    from services.vector_store import VectorStoreService
    from services.database import get_async_session
    from sqlalchemy.ext.asyncio import AsyncSession
    from models.database import Policy
    
    MULTI_AGENT_AVAILABLE = True
    supervisor_agent = SupervisorAgent()
    vector_store = VectorStoreService()
    logger.info("Multi-Agent 시스템 초기화 완료")
    
except ImportError as e:
    MULTI_AGENT_AVAILABLE = False
    supervisor_agent = None
    vector_store = None
    logger.warning(f"Multi-Agent 시스템을 사용할 수 없습니다: {e}")

# 파일 저장 디렉토리
UPLOAD_DIR = Path("uploads")
PDF_DIR = UPLOAD_DIR  # uploads 폴더에 직접 저장

# 디렉토리 생성
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic 모델 - 기존 프론트엔드 API 호환
class PolicyResponse(BaseModel):
    policy_id: int
    company: str
    category: str
    product_type: str
    product_name: str
    summary: Optional[str] = None
    created_at: str
    security_level: str

class UploadResponse(BaseModel):
    message: str
    policy_id: int
    summary: Optional[str] = None

# DB 전용 모드 - 메모리 캐시 제거

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """토큰 검증 (인증이 필요한 엔드포인트용)"""
    from routers.auth import get_current_user
    return await get_current_user(credentials)

async def process_policy_document(
    file_path: str, 
    policy_id: int, 
    file_name: str
):
    """백그라운드에서 문서 처리 (Multi-Agent 워크플로우)"""
    
    if not MULTI_AGENT_AVAILABLE or not supervisor_agent:
        logger.warning(f"약관 {policy_id}: Multi-Agent 시스템 없음")
        return
    
    try:
        logger.info(f"Policy {policy_id}: 백그라운드 문서 처리 시작 - {file_name}")
        
        # Supervisor Agent로 문서 처리
        result = await supervisor_agent.process_document(
            file_path=file_path,
            policy_id=policy_id,
            file_name=file_name
        )
        
        # 처리 결과 확인
        if result["status"] == "completed":
            # 1. outputs/markdown/ 폴더의 MD 파일을 uploads/ 폴더로 복사
            copy_success = await copy_outputs_markdown_to_uploads(policy_id)
            if copy_success:
                logger.info(f"✅ 약관 {policy_id}: outputs/markdown → uploads 복사 완료")
            else:
                logger.warning(f"약관 {policy_id}: MD 파일 복사 실패")
            
            # 2. 벡터 저장소에 임베딩 저장
            if result.get("processed_chunks") and vector_store:
                async with get_async_session() as db:
                    success = await vector_store.store_embeddings(
                        db=db,
                        policy_id=policy_id,
                        chunks=result["processed_chunks"]
                    )
                    
                    if success:
                        logger.info(f"약관 {policy_id}: 벡터 저장소 저장 완료")
                    else:
                        logger.error(f"약관 {policy_id}: 벡터 저장소 저장 실패")
            
            logger.info(
                f"Policy {policy_id}: 문서 처리 완료 - "
                f"{result.get('total_chunks', 0)}개 청크, "
                f"처리시간: {result.get('processing_time', 0):.2f}초"
            )
        else:
            logger.error(
                f"약관 {policy_id}: 문서 처리 실패 - {result.get('error_message', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"약관 {policy_id}: 백그라운드 처리 중 예외 발생: {str(e)}")

@router.post("/upload", response_model=UploadResponse)
async def upload_policy(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company: str = Form(default="미분류"),
    category: str = Form(default="미분류"),
    product_type: str = Form(default="일반형"),
    product_name: str = Form(default=""),
    security_level: str = Form("public")
    # current_user: dict = Depends(verify_token)  # 임시로 인증 제거
):
    """
    약관 파일 업로드
    기존 프론트엔드 policyAPI.upload()와 호환
    """
    try:
        logger.info(f"약관 업로드 시작: {product_name} ({file.filename})")
        
        # 파일 형식 검증
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF 파일만 업로드 가능합니다."
            )
        
        # 파일 크기 검증 (100MB 제한)
        file_content = await file.read()
        if len(file_content) > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="파일 크기는 100MB를 초과할 수 없습니다."
            )
        
        # 약관명 기반 파일명 생성
        safe_product_name = secure_filename(product_name) if product_name.strip() else secure_filename(file.filename.replace('.pdf', ''))
        timestamp = int(time.time())
        pdf_filename = f"{timestamp}_{safe_product_name}.pdf"
        pdf_file_path = PDF_DIR / pdf_filename
        
        # PDF 파일 저장
        with open(pdf_file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"✅ 약관 PDF 저장 완료: {pdf_file_path}")
        
        # MD 파일 경로 설정 (같은 uploads 폴더에)
        md_filename = f"{timestamp}_{safe_product_name}.md"
        md_file_path = PDF_DIR / md_filename  # uploads 폴더에 직접 저장
        
        # 주의: MD 파일은 아직 생성되지 않음 - Multi-Agent 처리 완료 후 생성됨
        
        # 파일명에서 제품명 추출 (제품명이 비어있는 경우)
        if not product_name.strip():
            product_name = file.filename.replace('.pdf', '').replace('_', ' ')
        
        # 실제 DB에 정책 저장
        try:
            from services.database import get_async_session
            from models.database import Policy
            from sqlalchemy import select
            
            async with get_async_session() as db:
                # 새 약관 생성 (파일 경로 포함)
                current_date = datetime.now()
                new_policy_obj = Policy(
                    company=company,
                    category=category,
                    product_type=product_type,
                    product_name=product_name,
                    summary=f"{company}에서 제공하는 {product_name} 상품입니다.",
                    created_at=current_date,
                    security_level=security_level,
                    sale_start_dt=current_date.strftime('%Y%m%d'),
                    sale_end_dt=current_date.strftime('%Y%m%d'),
                    sale_stat="Y",
                    pdf_path=str(pdf_file_path),  # PDF 파일 경로 저장
                    md_path=str(md_file_path),    # MD 파일 경로 저장 (처리 후 생성 예정)
                    original_path=str(pdf_file_path)  # 원본 파일 경로
                )
                
                db.add(new_policy_obj)
                await db.commit()
                await db.refresh(new_policy_obj)
                
                new_policy_id = new_policy_obj.policy_id
                logger.info(f"✅ 약관 {new_policy_id}: DB에 약관 저장 완료 (PDF: {pdf_filename})")
                
        except Exception as db_error:
            logger.error(f"❌ DB 약관 저장 실패: {db_error}")
            # DB 저장 실패 시 오류 반환 (DB 필수)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"데이터베이스 저장 실패: {str(db_error)}"
            )
        
        # 백그라운드에서 Multi-Agent 약관 처리 시작 (DB 연결 보장됨)
        background_tasks.add_task(
            process_policy_document,
            file_path=str(pdf_file_path),  # 수정된 파일 경로 사용
            policy_id=new_policy_id,
            file_name=pdf_filename
        )
        logger.info(f"약관 {new_policy_id}: PDF 백그라운드 처리 시작됨")
        
        logger.info(f"약관 {new_policy_id}: 백그라운드 처리 작업 등록 완료")
        
        return UploadResponse(
            message="약관 업로드가 완료되었습니다. 백그라운드에서 문서 처리가 진행됩니다.",
            policy_id=new_policy_id,
            summary=f"{product_name}에 대한 약관이 성공적으로 업로드되어 처리 중입니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"업로드 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 업로드 중 오류가 발생했습니다."
        )

@router.get("", response_model=List[PolicyResponse])
async def get_policies(skip: int = 0, limit: int = 100):
    """
    약관 목록 조회 - 실제 DB에서 조회
    기존 프론트엔드 policyAPI.getPolicies()와 호환
    """
    try:
        logger.info(f"약관 목록 조회: skip={skip}, limit={limit}")
        
        # 실제 DB에서 조회
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        
        async with get_async_session() as db:
            # DB에서 정책 조회
            stmt = select(Policy).offset(skip).limit(limit).order_by(Policy.created_at.desc())
            result = await db.execute(stmt)
            policies = result.scalars().all()
            
            # 응답 형식으로 변환
            policy_responses = []
            for policy in policies:
                policy_responses.append({
                    "policy_id": policy.policy_id,
                    "company": policy.company,
                    "category": policy.category,
                    "product_type": policy.product_type,
                    "product_name": policy.product_name,
                    "summary": policy.summary,
                    "created_at": policy.created_at.isoformat(),
                    "security_level": policy.security_level
                })
            
            logger.info(f"✅ DB에서 {len(policy_responses)}개 정책 조회 완료")
            return policy_responses
        
    except Exception as e:
        logger.error(f"❌ 약관 목록 조회 오류: {e}")
        # DB 조회 실패 시 오류 반환 (DB 필수)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터베이스 조회 실패: {str(e)}"
        )

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: int):
    """
    특정 약관 조회
    기존 프론트엔드 policyAPI.getPolicy()와 호환
    """
    try:
        logger.info(f"약관 조회: policy_id={policy_id}")
        
        # 실제 DB에서 정책 조회
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        
        async with get_async_session() as db:
            # DB에서 정책 조회
            stmt = select(Policy).where(Policy.policy_id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="약관을 찾을 수 없습니다."
                )
            
            # 응답 형식으로 변환
            return {
                "policy_id": policy.policy_id,
                "company": policy.company,
                "category": policy.category,
                "product_type": policy.product_type,
                "product_name": policy.product_name,
                "summary": policy.summary,
                "created_at": policy.created_at.isoformat(),
                "security_level": policy.security_level
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"약관 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="약관 조회 중 오류가 발생했습니다."
        )

@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: int
    # current_user: dict = Depends(verify_token)  # 임시로 인증 제거
):
    """
    약관 삭제
    기존 프론트엔드 policyAPI.deletePolicy()와 호환
    """
    try:
        logger.info(f"약관 삭제: policy_id={policy_id}")
        
        # 실제 DB에서 정책 삭제
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select, delete
        
        async with get_async_session() as db:
            # 삭제할 정책 존재 확인
            stmt = select(Policy).where(Policy.policy_id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="약관을 찾을 수 없습니다."
                )
            
            # 정책 삭제 (CASCADE로 관련 임베딩도 자동 삭제)
            delete_stmt = delete(Policy).where(Policy.policy_id == policy_id)
            await db.execute(delete_stmt)
            await db.commit()
            
            logger.info(f"✅ Policy {policy_id} 삭제 완료: {policy.product_name}")
        
        return {"message": "약관이 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"약관 삭제 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="약관 삭제 중 오류가 발생했습니다."
        )

@router.get("/{policy_id}/download")
async def download_policy(policy_id: int):
    """
    약관 PDF 파일 다운로드
    """
    try:
        logger.info(f"PDF 다운로드: policy_id={policy_id}")
        
        # DB에서 정책 찾기
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        
        async with get_async_session() as db:
            stmt = select(Policy).where(Policy.policy_id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="약관을 찾을 수 없습니다."
                )
            
            # DB에서 저장된 PDF 경로 사용
            if policy.pdf_path and os.path.exists(policy.pdf_path):
                return FileResponse(
                    path=policy.pdf_path,
                    filename=f"{policy.product_name}.pdf",
                    media_type='application/pdf'
                )
            
            # 파일이 없는 경우
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{policy.product_name} 약관 파일을 찾을 수 없습니다."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 다운로드 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF 다운로드 중 오류가 발생했습니다."
        )

@router.get("/{policy_id}/view")
async def view_policy(policy_id: int):
    """
    약관 PDF 파일 보기 (브라우저에서 직접 열기)
    """
    try:
        logger.info(f"PDF 보기: policy_id={policy_id}")
        
        # DB에서 정책 찾기
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        
        async with get_async_session() as db:
            stmt = select(Policy).where(Policy.policy_id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="약관을 찾을 수 없습니다."
                )
            
            # DB에서 저장된 PDF 경로 사용하여 인라인 반환
            if policy.pdf_path and os.path.exists(policy.pdf_path):
                return FileResponse(
                    path=policy.pdf_path,
                    filename=f"{policy.product_name}.pdf",
                    media_type='application/pdf',
                    headers={"Content-Disposition": "inline"}
                )
        
            # 파일이 없는 경우 HTML 페이지로 안내
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{policy.product_name} - 약관 보기</title>
                <meta charset="utf-8">
            </head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>{policy.product_name}</h1>
                <p><strong>보험사:</strong> {policy.company}</p>
                <p><strong>분류:</strong> {policy.category}</p>
                <p><strong>요약:</strong> {policy.summary}</p>
                <p style="color: #666;">PDF 파일이 아직 처리되지 않았습니다.</p>
            </body>
            </html>
            """
            
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 보기 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF 보기 중 오류가 발생했습니다."
        )

@router.get("/{policy_id}/md")
async def get_policy_md(policy_id: int):
    """
    약관 Markdown 파일 조회
    기존 프론트엔드 policyAPI.getPolicyMd()와 호환
    """
    try:
        logger.info(f"MD 조회: policy_id={policy_id}")
        
        # DB에서 정책 찾기
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        
        async with get_async_session() as db:
            stmt = select(Policy).where(Policy.policy_id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="약관을 찾을 수 없습니다."
                )
            
            # DB에서 저장된 MD 파일 경로 확인
            if policy.md_path and os.path.exists(policy.md_path):
                # 실제 처리된 Markdown 파일 반환
                with open(policy.md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
            else:
                # 파일이 없으면 기본 정보로 Markdown 생성
                md_content = f"""# {policy.product_name}

## 보험사
{policy.company}

## 상품 정보
- **분류**: {policy.category}
- **상품유형**: {policy.product_type}
- **보안등급**: {policy.security_level}

## 요약
{policy.summary}

## 상세 약관
*상세 약관 내용은 PDF 처리 파이프라인 구현 후 제공됩니다.*
"""
        
            return {"content": md_content}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MD 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MD 조회 중 오류가 발생했습니다."
        )

# Frontend 호환성을 위한 추가 엔드포인트들
@router.get("/{policy_id}/view/pdf")
async def view_policy_pdf(policy_id: int):
    """PDF 보기 - Frontend 호환"""
    return await view_policy(policy_id)

@router.get("/{policy_id}/download/pdf")
async def download_policy_pdf(policy_id: int):
    """PDF 다운로드 - Frontend 호환"""
    return await download_policy(policy_id)

@router.get("/{policy_id}/view/markdown")
async def view_policy_markdown(policy_id: int):
    """Markdown 보기 - Frontend 호환"""
    return await get_policy_md(policy_id)

@router.get("/{policy_id}/download/markdown")
async def download_policy_markdown(policy_id: int):
    """Markdown 다운로드 - Frontend 호환"""
    try:
        # MD 내용 가져오기
        md_response = await get_policy_md(policy_id)
        md_content = md_response["content"]
        
        # DB에서 정책 이름 가져오기
        from services.database import get_async_session
        from models.database import Policy
        from sqlalchemy import select
        
        async with get_async_session() as db:
            stmt = select(Policy).where(Policy.policy_id == policy_id)
            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="약관을 찾을 수 없습니다."
                )
        
        # 임시 파일 생성 후 반환
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(md_content)
            tmp_file_path = tmp_file.name
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=tmp_file_path,
            filename=f"{policy.product_name}.md",
            media_type='text/markdown'
        )
    
    except Exception as e:
        logger.error(f"MD 다운로드 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MD 다운로드 중 오류가 발생했습니다."
        )
