-- pgvector 최적화 인덱스 및 설정 초기화 스크립트
-- Task 4.4: pgvector 저장 최적화 및 인덱싱

-- pgvector 확장 활성화 (이미 설치되어 있다고 가정)
CREATE EXTENSION IF NOT EXISTS vector;

-- HNSW 인덱스 생성 (text-embedding-3 테이블)
-- 3072차원 임베딩용 최적화 인덱스
CREATE INDEX CONCURRENTLY IF NOT EXISTS embeddings_text_embedding_3_embedding_idx
ON embeddings_text_embedding_3 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- HNSW 인덱스 생성 (qwen 테이블)
-- 4096차원 임베딩용 최적화 인덱스
CREATE INDEX CONCURRENTLY IF NOT EXISTS embeddings_qwen_embedding_idx
ON embeddings_qwen 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 성능 최적화를 위한 추가 인덱스
-- policy_id 기반 필터링 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_text_embedding_3_policy_id
ON embeddings_text_embedding_3(policy_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_qwen_policy_id
ON embeddings_qwen(policy_id);

-- chunk_index 기반 정렬 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_text_embedding_3_chunk_index
ON embeddings_text_embedding_3(policy_id, chunk_index);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_qwen_chunk_index
ON embeddings_qwen(policy_id, chunk_index);

-- 복합 인덱스 (정책별 검색 최적화)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_text_embedding_3_policy_model
ON embeddings_text_embedding_3(policy_id, model);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_qwen_policy_model
ON embeddings_qwen(policy_id, model);

-- PostgreSQL 설정 최적화 (운영 환경에서 적용)
-- 이 설정들은 데이터베이스 관리자가 postgresql.conf에서 설정해야 함

-- 메모리 설정 (예시 - 실제 환경에 맞게 조정 필요)
-- shared_buffers = 256MB (총 메모리의 25%)
-- effective_cache_size = 1GB (총 메모리의 75%)
-- work_mem = 4MB (동시 연결 수 고려)
-- maintenance_work_mem = 64MB

-- 벡터 검색 최적화 설정
-- hnsw.ef_search 기본값 설정 (검색 시 동적으로 조정 가능)
-- 높을수록 정확하지만 느림 (기본값: 40)
ALTER SYSTEM SET hnsw.ef_search = 40;

-- 통계 수집 최적화
-- 벡터 테이블의 통계를 정기적으로 업데이트
ANALYZE embeddings_text_embedding_3;
ANALYZE embeddings_qwen;
ANALYZE policies;

-- 테이블 클러스터링 (대량 데이터가 있을 때 효과적)
-- policy_id 순으로 물리적 저장 순서 최적화
-- CLUSTER embeddings_text_embedding_3 USING idx_embeddings_text_embedding_3_policy_id;
-- CLUSTER embeddings_qwen USING idx_embeddings_qwen_policy_id;

-- 인덱스 상태 확인 쿼리
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('embeddings_text_embedding_3', 'embeddings_qwen')
ORDER BY tablename, indexname;

-- 인덱스 크기 확인 쿼리
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
  AND tablename IN ('embeddings_text_embedding_3', 'embeddings_qwen')
ORDER BY pg_relation_size(indexrelid) DESC;

-- 벡터 검색 성능 테스트 쿼리 예시
-- (실제 임베딩 벡터로 교체하여 사용)
/*
-- 성능 테스트 쿼리
EXPLAIN (ANALYZE, BUFFERS) 
SELECT 
    e.id,
    e.policy_id,
    e.chunk_text,
    e.chunk_index,
    1 - (e.embedding <=> '[0.1,0.2,0.3,...]'::vector) AS similarity_score
FROM embeddings_text_embedding_3 e
JOIN policies p ON e.policy_id = p.policy_id
WHERE 1 - (e.embedding <=> '[0.1,0.2,0.3,...]'::vector) > 0.7
ORDER BY e.embedding <=> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;
*/

-- 대량 삽입 성능 최적화 설정
-- 대량 데이터 삽입 시 임시로 적용
/*
-- 대량 삽입 전
SET maintenance_work_mem = '1GB';
SET max_parallel_workers_per_gather = 4;

-- 인덱스 비활성화 (선택사항, 매우 큰 데이터셋의 경우)
-- DROP INDEX IF EXISTS embeddings_text_embedding_3_embedding_idx;

-- 대량 삽입 수행 (COPY 명령어 권장)
-- COPY embeddings_text_embedding_3 FROM '/path/to/data.csv' WITH CSV;

-- 인덱스 재생성
-- CREATE INDEX embeddings_text_embedding_3_embedding_idx ...

-- 설정 복원
RESET maintenance_work_mem;
RESET max_parallel_workers_per_gather;
*/

-- 정기 유지보수 쿼리
-- 매일 실행 권장
VACUUM ANALYZE embeddings_text_embedding_3;
VACUUM ANALYZE embeddings_qwen;
VACUUM ANALYZE policies;

-- 주간 실행 권장 (테이블 재구성)
-- VACUUM FULL embeddings_text_embedding_3; -- 주의: 테이블 잠금 발생
-- REINDEX TABLE embeddings_text_embedding_3; -- 주의: 인덱스 잠금 발생

COMMIT;

