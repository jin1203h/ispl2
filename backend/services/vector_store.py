"""
벡터 저장소 서비스
pgvector를 활용한 임베딩 저장 및 검색
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from models.database import EmbeddingTextEmbedding3, Policy
from agents.base import ProcessedChunk

logger = logging.getLogger(__name__)

class VectorStoreService:
    """벡터 저장소 서비스"""
    
    def __init__(self, embedding_model: str = "text-embedding-3-large"):
        self.embedding_model = embedding_model
        self.batch_size = 100
    
    async def store_embeddings(
        self, 
        db: AsyncSession, 
        policy_id: int, 
        chunks: List[ProcessedChunk]
    ) -> bool:
        """청크들의 임베딩을 데이터베이스에 저장 (연결 안정성 강화)"""
        max_retries = 3
        retry_delay = 1  # 초
        
        for attempt in range(max_retries):
            try:
                # 임베딩이 있는 청크들만 필터링
                chunks_with_embeddings = [
                    chunk for chunk in chunks 
                    if chunk.get("embedding") and len(chunk["embedding"]) > 0
                ]
                
                if not chunks_with_embeddings:
                    logger.warning(f"Policy {policy_id}: 저장할 임베딩이 없음")
                    return False
                
                logger.info(f"Policy {policy_id}: {len(chunks_with_embeddings)}개 임베딩 저장 시작 (시도 {attempt + 1}/{max_retries})")
                
                # 연결 상태 확인
                await db.execute(text("SELECT 1"))
                
                # 기존 임베딩 삭제 (재처리 시) - 안전한 방식
                await self._delete_existing_embeddings(db, policy_id)
                
                # 더 작은 배치 크기로 저장 (연결 안정성 향상)
                small_batch_size = min(self.batch_size // 2, 20)  # 배치 크기 축소
                stored_count = 0
                
                for i in range(0, len(chunks_with_embeddings), small_batch_size):
                    batch = chunks_with_embeddings[i:i + small_batch_size]
                    
                    # 각 배치마다 연결 상태 확인
                    await db.execute(text("SELECT 1"))
                    batch_stored = await self._store_embedding_batch(db, policy_id, batch)
                    stored_count += batch_stored
                    
                    # 배치 간 짧은 대기 (연결 안정성)
                    if i + small_batch_size < len(chunks_with_embeddings):
                        await asyncio.sleep(0.1)
            
                await db.commit()
                
                logger.info(f"Policy {policy_id}: {stored_count}개 임베딩 저장 완료")
                return stored_count > 0
                
            except Exception as e:
                logger.error(f"Policy {policy_id} 임베딩 저장 실패 (시도 {attempt + 1}): {str(e)}")
                await db.rollback()
                
                if attempt < max_retries - 1:
                    logger.info(f"Policy {policy_id}: {retry_delay}초 후 재시도...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                else:
                    logger.error(f"Policy {policy_id}: 최대 재시도 횟수 초과")
                    return False
    
    async def _delete_existing_embeddings(self, db: AsyncSession, policy_id: int):
        """기존 임베딩 삭제"""
        try:
            # text-embedding-3-large 테이블에서 삭제
            stmt = text(
                "DELETE FROM embeddings_text_embedding_3 WHERE policy_id = :policy_id"
            )
            await db.execute(stmt, {"policy_id": policy_id})
            
            logger.debug(f"Policy {policy_id}: 기존 임베딩 삭제 완료")
            
        except Exception as e:
            logger.warning(f"Policy {policy_id} 기존 임베딩 삭제 실패: {str(e)}")
    
    async def _store_embedding_batch(
        self, 
        db: AsyncSession, 
        policy_id: int, 
        batch: List[ProcessedChunk]
    ) -> int:
        """임베딩 배치 저장"""
        stored_count = 0
        
        for chunk in batch:
            try:
                embedding_record = EmbeddingTextEmbedding3(
                    policy_id=policy_id,
                    chunk_text=chunk["text"],
                    chunk_index=chunk["metadata"]["chunk_index"],
                    embedding=chunk["embedding"],
                    model=self.embedding_model
                )
                
                db.add(embedding_record)
                stored_count += 1
                
            except Exception as e:
                logger.warning(f"청크 {chunk['metadata']['chunk_index']} 저장 실패: {str(e)}")
        
        return stored_count
    
    async def search_similar(
        self, 
        db: AsyncSession, 
        query_embedding: List[float], 
        limit: int = 10,
        similarity_threshold: float = 0.7,
        policy_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """유사도 검색"""
        try:
            # 벡터를 문자열로 변환
            vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # pgvector 코사인 유사도 검색 쿼리 (안전한 방식)
            similarity_query = f"""
                SELECT 
                    e.id,
                    e.policy_id,
                    e.chunk_text,
                    e.chunk_index,
                    e.model,
                    e.created_at,
                    p.product_name,
                    p.company,
                    p.category,
                    1 - (e.embedding <=> '{vector_str}'::vector) AS similarity_score
                FROM embeddings_text_embedding_3 e
                JOIN policies p ON e.policy_id = p.policy_id
                WHERE 1 - (e.embedding <=> '{vector_str}'::vector) > :threshold
            """
            
            # 정책 ID 필터링
            if policy_ids:
                policy_ids_str = ",".join(str(pid) for pid in policy_ids)
                similarity_query += f" AND e.policy_id IN ({policy_ids_str})"
            
            similarity_query += """
                ORDER BY similarity_score DESC
                LIMIT :limit
            """
            
            # 쿼리 실행 (벡터는 이미 문자열로 삽입됨)
            result = await db.execute(
                text(similarity_query),
                {
                    "threshold": similarity_threshold,
                    "limit": limit
                }
            )
            
            # 결과 처리
            search_results = []
            for row in result:
                search_results.append({
                    "embedding_id": row.id,
                    "policy_id": row.policy_id,
                    "chunk_text": row.chunk_text,
                    "chunk_index": row.chunk_index,
                    "similarity_score": float(row.similarity_score),
                    "product_name": row.product_name,
                    "company": row.company,
                    "category": row.category,
                    "model": row.model,
                    "created_at": row.created_at
                })
            
            logger.info(f"유사도 검색 완료: {len(search_results)}개 결과")
            return search_results
            
        except Exception as e:
            logger.error(f"유사도 검색 실패: {str(e)}")
            return []
    
    async def get_policy_embeddings_count(self, db: AsyncSession, policy_id: int) -> int:
        """정책별 임베딩 개수 조회"""
        try:
            stmt = select(EmbeddingTextEmbedding3).where(
                EmbeddingTextEmbedding3.policy_id == policy_id
            )
            result = await db.execute(stmt)
            embeddings = result.scalars().all()
            return len(embeddings)
            
        except Exception as e:
            logger.error(f"Policy {policy_id} 임베딩 개수 조회 실패: {str(e)}")
            return 0
    
    async def delete_policy_embeddings(self, db: AsyncSession, policy_id: int) -> bool:
        """정책의 모든 임베딩 삭제"""
        try:
            stmt = text(
                "DELETE FROM embeddings_text_embedding_3 WHERE policy_id = :policy_id"
            )
            result = await db.execute(stmt, {"policy_id": policy_id})
            await db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Policy {policy_id}: {deleted_count}개 임베딩 삭제 완료")
            return True
            
        except Exception as e:
            logger.error(f"Policy {policy_id} 임베딩 삭제 실패: {str(e)}")
            await db.rollback()
            return False
    
    async def get_vector_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """벡터 저장소 통계"""
        try:
            # 전체 임베딩 개수
            count_query = "SELECT COUNT(*) FROM embeddings_text_embedding_3"
            count_result = await db.execute(text(count_query))
            total_embeddings = count_result.scalar()
            
            # 정책별 임베딩 개수
            policy_stats_query = """
                SELECT 
                    p.policy_id,
                    p.product_name,
                    p.company,
                    COUNT(e.id) as embedding_count
                FROM policies p
                LEFT JOIN embeddings_text_embedding_3 e ON p.policy_id = e.policy_id
                GROUP BY p.policy_id, p.product_name, p.company
                ORDER BY embedding_count DESC
            """
            policy_result = await db.execute(text(policy_stats_query))
            policy_stats = []
            
            for row in policy_result:
                policy_stats.append({
                    "policy_id": row.policy_id,
                    "product_name": row.product_name,
                    "company": row.company,
                    "embedding_count": row.embedding_count
                })
            
            return {
                "total_embeddings": total_embeddings,
                "total_policies": len(policy_stats),
                "policies_with_embeddings": len([p for p in policy_stats if p["embedding_count"] > 0]),
                "embedding_model": self.embedding_model,
                "policy_stats": policy_stats
            }
            
        except Exception as e:
            logger.error(f"벡터 저장소 통계 조회 실패: {str(e)}")
            return {
                "total_embeddings": 0,
                "total_policies": 0,
                "policies_with_embeddings": 0,
                "embedding_model": self.embedding_model,
                "policy_stats": []
            }

