"""
최적화된 벡터 저장소 서비스
HNSW 인덱스, 대량 삽입 최적화, 성능 모니터링 포함
"""
import asyncio
import logging
import time
import json
import io
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
from sqlalchemy import select, text, MetaData, inspect
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.engine import Row

# pgvector import
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    print("⚠️ pgvector가 설치되지 않았습니다. 벡터 검색이 제한됩니다.")
    PGVECTOR_AVAILABLE = False

from models.database import EmbeddingTextEmbedding3, EmbeddingQwen, Policy
from agents.base import ProcessedChunk
from services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

@dataclass
class IndexConfig:
    """HNSW 인덱스 설정"""
    m: int = 16              # 각 레이어에서 연결할 최대 노드 수 (16이 기본값)
    ef_construction: int = 64 # 인덱스 생성 시 탐색 깊이 (높을수록 정확하지만 느림)
    ef_search: int = 40      # 검색 시 탐색 깊이
    distance_function: str = "vector_cosine_ops"  # 거리 함수

@dataclass
class BulkInsertConfig:
    """대량 삽입 설정"""
    batch_size: int = 1000
    use_copy: bool = True
    chunk_size: int = 5000

@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    operation: str
    duration: float
    records_processed: int
    timestamp: datetime
    additional_info: Dict[str, Any] = None

class OptimizedVectorStoreService(VectorStoreService):
    """최적화된 벡터 저장소 서비스"""
    
    def __init__(self, 
                 embedding_model: str = "text-embedding-3-large",
                 index_config: Optional[IndexConfig] = None,
                 bulk_config: Optional[BulkInsertConfig] = None):
        super().__init__(embedding_model)
        
        self.index_config = index_config or IndexConfig()
        self.bulk_config = bulk_config or BulkInsertConfig()
        self.performance_metrics: List[PerformanceMetrics] = []
        
        # 지원되는 테이블과 차원 매핑
        self.supported_tables = {
            "embeddings_text_embedding_3": {
                "model_class": EmbeddingTextEmbedding3,
                "dimensions": 3072,
                "index_name": "embeddings_text_embedding_3_embedding_idx"
            },
            "embeddings_qwen": {
                "model_class": EmbeddingQwen,
                "dimensions": 4096,
                "index_name": "embeddings_qwen_embedding_idx"
            }
        }
        
        logger.info(f"OptimizedVectorStoreService 초기화: 모델={embedding_model}")
    
    async def initialize_indexes(self, db: AsyncSession) -> Dict[str, bool]:
        """모든 지원되는 테이블에 HNSW 인덱스 생성"""
        results = {}
        
        for table_name, table_info in self.supported_tables.items():
            try:
                success = await self.create_hnsw_index(db, table_name)
                results[table_name] = success
                
                if success:
                    logger.info(f"✅ {table_name} HNSW 인덱스 생성/확인 완료")
                else:
                    logger.warning(f"⚠️ {table_name} HNSW 인덱스 생성 실패")
                    
            except Exception as e:
                logger.error(f"❌ {table_name} 인덱스 초기화 실패: {e}")
                results[table_name] = False
        
        return results
    
    async def create_hnsw_index(self, db: AsyncSession, table_name: str) -> bool:
        """특정 테이블에 HNSW 인덱스 생성"""
        try:
            if table_name not in self.supported_tables:
                raise ValueError(f"지원되지 않는 테이블: {table_name}")
            
            table_info = self.supported_tables[table_name]
            index_name = table_info["index_name"]
            
            # 기존 인덱스 확인
            check_index_sql = f"""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = '{table_name}' AND indexname = '{index_name}'
            """
            
            result = await db.execute(text(check_index_sql))
            existing_index = result.fetchone()
            
            if existing_index:
                logger.info(f"HNSW 인덱스 '{index_name}'가 이미 존재합니다")
                return True
            
            # HNSW 인덱스 생성 (안전한 방식)
            try:
                create_index_sql = f"""
                    CREATE INDEX {index_name}
                    ON {table_name} USING hnsw (embedding {self.index_config.distance_function})
                    WITH (m = {self.index_config.m}, ef_construction = {self.index_config.ef_construction})
                """
                
                start_time = time.time()
                await db.execute(text(create_index_sql))
                await db.commit()
                duration = time.time() - start_time
                
            except Exception as create_error:
                # 인덱스가 이미 존재하거나 다른 오류 발생 시
                if "already exists" in str(create_error):
                    logger.info(f"HNSW 인덱스 '{index_name}'가 이미 존재합니다")
                    return True
                else:
                    # 다른 오류는 재발생
                    raise create_error
            
            # 성능 메트릭 기록
            self._record_performance_metric(
                operation=f"create_hnsw_index_{table_name}",
                duration=duration,
                records_processed=0,
                additional_info={"index_config": self.index_config.__dict__}
            )
            
            logger.info(f"HNSW 인덱스 '{index_name}' 생성 완료 ({duration:.2f}초)")
            return True
            
        except Exception as e:
            logger.error(f"HNSW 인덱스 생성 실패 ({table_name}): {e}")
            await db.rollback()
            return False
    
    async def bulk_store_embeddings_optimized(
        self, 
        db: AsyncSession, 
        policy_id: int, 
        chunks: List[ProcessedChunk],
        table_name: str = "embeddings_text_embedding_3"
    ) -> Dict[str, Any]:
        """최적화된 대량 임베딩 저장"""
        
        start_time = time.time()
        
        try:
            # 임베딩이 있는 청크들만 필터링
            chunks_with_embeddings = [
                chunk for chunk in chunks 
                if chunk.get("embedding") and len(chunk["embedding"]) > 0
            ]
            
            if not chunks_with_embeddings:
                return {
                    "success": False,
                    "message": "저장할 임베딩이 없음",
                    "stored_count": 0
                }
            
            logger.info(f"Policy {policy_id}: {len(chunks_with_embeddings)}개 임베딩 최적화 저장 시작")
            
            # 기존 임베딩 삭제
            await self._delete_existing_embeddings_optimized(db, policy_id, table_name)
            
            # 대량 삽입 수행
            if self.bulk_config.use_copy and len(chunks_with_embeddings) > 100:
                stored_count = await self._bulk_insert_using_copy(
                    db, policy_id, chunks_with_embeddings, table_name
                )
            else:
                stored_count = await self._bulk_insert_using_batch(
                    db, policy_id, chunks_with_embeddings, table_name
                )
            
            await db.commit()
            duration = time.time() - start_time
            
            # 성능 메트릭 기록
            self._record_performance_metric(
                operation="bulk_store_embeddings",
                duration=duration,
                records_processed=stored_count,
                additional_info={
                    "policy_id": policy_id,
                    "table_name": table_name,
                    "method": "copy" if self.bulk_config.use_copy else "batch",
                    "throughput": stored_count / duration if duration > 0 else 0
                }
            )
            
            logger.info(
                f"Policy {policy_id}: {stored_count}개 임베딩 저장 완료 "
                f"({duration:.2f}초, {stored_count/duration:.1f} 벡터/초)"
            )
            
            return {
                "success": True,
                "stored_count": stored_count,
                "duration": duration,
                "throughput": stored_count / duration if duration > 0 else 0,
                "table_name": table_name
            }
            
        except Exception as e:
            await db.rollback()
            duration = time.time() - start_time
            
            error_msg = f"Policy {policy_id} 최적화 저장 실패: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "message": error_msg,
                "stored_count": 0,
                "duration": duration
            }
    
    async def _delete_existing_embeddings_optimized(
        self, 
        db: AsyncSession, 
        policy_id: int, 
        table_name: str
    ):
        """최적화된 기존 임베딩 삭제"""
        try:
            delete_sql = f"DELETE FROM {table_name} WHERE policy_id = :policy_id"
            result = await db.execute(text(delete_sql), {"policy_id": policy_id})
            
            deleted_count = result.rowcount
            logger.debug(f"Policy {policy_id}: {table_name}에서 {deleted_count}개 기존 임베딩 삭제")
            
        except Exception as e:
            logger.warning(f"Policy {policy_id} 기존 임베딩 삭제 실패 ({table_name}): {e}")
    
    async def _bulk_insert_using_copy(
        self, 
        db: AsyncSession, 
        policy_id: int, 
        chunks: List[ProcessedChunk], 
        table_name: str
    ) -> int:
        """COPY 명령어를 활용한 고속 대량 삽입"""
        
        try:
            # CSV 데이터 준비
            csv_data = io.StringIO()
            
            for chunk in chunks:
                embedding_str = "[" + ",".join(map(str, chunk["embedding"])) + "]"
                
                # CSV 행 작성 (PostgreSQL COPY 형식)
                csv_data.write(f"{policy_id}\t{chunk['text'].replace(chr(9), ' ').replace(chr(10), ' ').replace(chr(13), ' ')}\t{chunk['metadata']['chunk_index']}\t{embedding_str}\t{self.embedding_model}\t{datetime.now().isoformat()}\n")
            
            csv_data.seek(0)
            
            # 원시 연결 가져오기
            raw_connection = await db.connection()
            
            # PostgreSQL psycopg3 AsyncConnection 사용
            async with raw_connection.begin():
                copy_sql = f"""
                    COPY {table_name} (policy_id, chunk_text, chunk_index, embedding, model, created_at)
                    FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')
                """
                
                # COPY 실행 (psycopg3의 copy 메서드 사용)
                cursor = await raw_connection.execute(copy_sql)
                await cursor.copy_from(csv_data)
            
            logger.info(f"COPY를 통한 대량 삽입 완료: {len(chunks)}개 레코드")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"COPY 대량 삽입 실패: {e}")
            # 실패 시 배치 삽입으로 폴백
            return await self._bulk_insert_using_batch(db, policy_id, chunks, table_name)
    
    async def _bulk_insert_using_batch(
        self, 
        db: AsyncSession, 
        policy_id: int, 
        chunks: List[ProcessedChunk], 
        table_name: str
    ) -> int:
        """배치 삽입 (COPY 실패 시 폴백)"""
        
        try:
            table_info = self.supported_tables[table_name]
            model_class = table_info["model_class"]
            
            batch_size = self.bulk_config.batch_size
            stored_count = 0
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # 배치 레코드 생성
                batch_records = []
                for chunk in batch:
                    record = model_class(
                        policy_id=policy_id,
                        chunk_text=chunk["text"],
                        chunk_index=chunk["metadata"]["chunk_index"],
                        embedding=chunk["embedding"],
                        model=self.embedding_model
                    )
                    batch_records.append(record)
                
                # 배치 삽입
                db.add_all(batch_records)
                await db.flush()
                
                stored_count += len(batch_records)
                
                if i % (batch_size * 5) == 0:  # 진행률 로그
                    progress = min(100, (i + batch_size) / len(chunks) * 100)
                    logger.debug(f"배치 삽입 진행률: {progress:.1f}%")
            
            logger.info(f"배치 삽입 완료: {stored_count}개 레코드")
            return stored_count
            
        except Exception as e:
            logger.error(f"배치 삽입 실패: {e}")
            return 0
    
    async def search_similar_optimized(
        self, 
        db: AsyncSession, 
        query_embedding: List[float], 
        limit: int = 10,
        similarity_threshold: float = 0.7,
        policy_ids: Optional[List[int]] = None,
        table_name: str = "embeddings_text_embedding_3"
    ) -> Dict[str, Any]:
        """최적화된 유사도 검색"""
        
        start_time = time.time()
        
        try:
            # 벡터를 문자열로 변환
            vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # 검색 시 HNSW 파라미터 설정
            await db.execute(text(f"SET hnsw.ef_search = {self.index_config.ef_search}"))
            
            # 최적화된 검색 쿼리
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
                FROM {table_name} e
                JOIN policies p ON e.policy_id = p.policy_id
                WHERE 1 - (e.embedding <=> '{vector_str}'::vector) > :threshold
            """
            
            # 정책 ID 필터링
            if policy_ids:
                policy_ids_str = ",".join(str(pid) for pid in policy_ids)
                similarity_query += f" AND e.policy_id IN ({policy_ids_str})"
            
            similarity_query += """
                ORDER BY e.embedding <=> '{vector_str}'::vector
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
            
            duration = time.time() - start_time
            
            # 성능 메트릭 기록
            self._record_performance_metric(
                operation="search_similar",
                duration=duration,
                records_processed=len(search_results),
                additional_info={
                    "table_name": table_name,
                    "similarity_threshold": similarity_threshold,
                    "limit": limit,
                    "policy_filters": len(policy_ids) if policy_ids else 0
                }
            )
            
            logger.info(f"최적화 유사도 검색 완료: {len(search_results)}개 결과 ({duration*1000:.1f}ms)")
            
            return {
                "results": search_results,
                "duration": duration,
                "result_count": len(search_results),
                "table_name": table_name
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"최적화 유사도 검색 실패: {e} ({duration*1000:.1f}ms)")
            
            return {
                "results": [],
                "duration": duration,
                "result_count": 0,
                "error": str(e)
            }
    
    async def analyze_index_performance(self, db: AsyncSession) -> Dict[str, Any]:
        """인덱스 성능 분석"""
        
        try:
            performance_stats = {}
            
            for table_name, table_info in self.supported_tables.items():
                index_name = table_info["index_name"]
                
                # 인덱스 크기 조회
                index_size_query = f"""
                    SELECT pg_size_pretty(pg_relation_size('{index_name}')) as index_size,
                           pg_relation_size('{index_name}') as index_size_bytes
                """
                
                try:
                    result = await db.execute(text(index_size_query))
                    size_info = result.fetchone()
                    
                    # 테이블 통계
                    table_stats_query = f"""
                        SELECT 
                            COUNT(*) as row_count,
                            pg_size_pretty(pg_relation_size('{table_name}')) as table_size
                        FROM {table_name}
                    """
                    
                    stats_result = await db.execute(text(table_stats_query))
                    table_stats = stats_result.fetchone()
                    
                    performance_stats[table_name] = {
                        "index_name": index_name,
                        "index_size": size_info.index_size if size_info else "N/A",
                        "index_size_bytes": size_info.index_size_bytes if size_info else 0,
                        "table_size": table_stats.table_size if table_stats else "N/A",
                        "row_count": table_stats.row_count if table_stats else 0,
                        "index_exists": size_info is not None
                    }
                    
                except Exception as e:
                    performance_stats[table_name] = {
                        "error": str(e),
                        "index_exists": False
                    }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "index_config": self.index_config.__dict__,
                "table_performance": performance_stats,
                "recent_metrics": self._get_recent_performance_metrics()
            }
            
        except Exception as e:
            logger.error(f"인덱스 성능 분석 실패: {e}")
            return {"error": str(e)}
    
    def _record_performance_metric(self, 
                                 operation: str, 
                                 duration: float, 
                                 records_processed: int,
                                 additional_info: Optional[Dict[str, Any]] = None):
        """성능 메트릭 기록"""
        
        metric = PerformanceMetrics(
            operation=operation,
            duration=duration,
            records_processed=records_processed,
            timestamp=datetime.now(),
            additional_info=additional_info or {}
        )
        
        self.performance_metrics.append(metric)
        
        # 메트릭 개수 제한 (최근 1000개)
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]
    
    def _get_recent_performance_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """최근 성능 메트릭 조회"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            {
                "operation": metric.operation,
                "duration": metric.duration,
                "records_processed": metric.records_processed,
                "timestamp": metric.timestamp.isoformat(),
                "throughput": metric.records_processed / metric.duration if metric.duration > 0 else 0,
                **metric.additional_info
            }
            for metric in self.performance_metrics
            if metric.timestamp > cutoff_time
        ]
        
        return recent_metrics
    
    async def optimize_table_statistics(self, db: AsyncSession) -> Dict[str, bool]:
        """테이블 통계 최적화 (ANALYZE 실행)"""
        
        results = {}
        
        for table_name in self.supported_tables.keys():
            try:
                analyze_sql = f"ANALYZE {table_name}"
                await db.execute(text(analyze_sql))
                await db.commit()
                
                results[table_name] = True
                logger.info(f"✅ {table_name} 통계 최적화 완료")
                
            except Exception as e:
                logger.error(f"❌ {table_name} 통계 최적화 실패: {e}")
                results[table_name] = False
        
        return results
    
    def get_optimization_recommendations(self) -> List[str]:
        """최적화 권장사항 생성"""
        
        recommendations = []
        
        # 성능 메트릭 분석
        if self.performance_metrics:
            search_metrics = [m for m in self.performance_metrics if m.operation == "search_similar"]
            if search_metrics:
                avg_search_time = sum(m.duration for m in search_metrics) / len(search_metrics)
                
                if avg_search_time > 0.1:  # 100ms 초과
                    recommendations.append(f"검색 시간이 평균 {avg_search_time*1000:.1f}ms로 느립니다. HNSW 파라미터 조정을 고려하세요.")
                
                if avg_search_time < 0.01:  # 10ms 미만
                    recommendations.append("검색 성능이 우수합니다. ef_search 값을 높여 정확도를 개선할 수 있습니다.")
            
            bulk_metrics = [m for m in self.performance_metrics if m.operation == "bulk_store_embeddings"]
            if bulk_metrics:
                avg_throughput = sum(m.additional_info.get("throughput", 0) for m in bulk_metrics) / len(bulk_metrics)
                
                if avg_throughput < 500:  # 500 벡터/초 미만
                    recommendations.append(f"대량 삽입 속도가 {avg_throughput:.1f} 벡터/초로 느립니다. 배치 크기 증가나 COPY 방식 사용을 고려하세요.")
        else:
            recommendations.append("성능 메트릭이 없습니다. 실제 작업을 수행한 후 분석해주세요.")
        
        # 일반적인 권장사항
        recommendations.extend([
            "정기적으로 ANALYZE를 실행하여 테이블 통계를 최신 상태로 유지하세요.",
            "대량 데이터 삽입 전에는 인덱스를 일시적으로 제거하는 것을 고려하세요.",
            "메모리 사용량을 모니터링하고 shared_buffers 설정을 최적화하세요."
        ])
        
        return recommendations
