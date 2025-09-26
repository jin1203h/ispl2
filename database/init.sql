-- ISPL2 보험약관 AI 시스템 데이터베이스 초기화 스크립트
-- shrimp-rules.md 규칙에 따른 테이블 구조

-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id             SERIAL PRIMARY KEY,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    role                VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'USER')),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 약관 테이블
CREATE TABLE IF NOT EXISTS policies (
    policy_id           SERIAL PRIMARY KEY,
    company             VARCHAR(100),
    category            VARCHAR(100),
    product_type        VARCHAR(100),
    product_name        VARCHAR(255) NOT NULL,
    sale_start_dt       VARCHAR(8),
    sale_end_dt         VARCHAR(8),
    sale_stat           VARCHAR(10),
    summary             TEXT,
    original_path       VARCHAR(500),
    md_path             VARCHAR(500),
    pdf_path            VARCHAR(500),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    security_level      VARCHAR(20)
);

-- text-embedding-3 임베딩 테이블 (3072차원) - 공개망/조건부 폐쇄망 환경용
CREATE TABLE IF NOT EXISTS embeddings_text_embedding_3 (
    id                  SERIAL PRIMARY KEY,
    policy_id           INTEGER NOT NULL REFERENCES policies(policy_id) ON DELETE CASCADE,
    chunk_text          TEXT NOT NULL,
    chunk_index         INTEGER NOT NULL,
    embedding           VECTOR(3072) NOT NULL,
    model               VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Qwen 임베딩 테이블 (4096차원) - 완전 폐쇄망 환경용 (향후 확장)
CREATE TABLE IF NOT EXISTS embeddings_qwen (
    id                  SERIAL PRIMARY KEY,
    policy_id           INTEGER NOT NULL REFERENCES policies(policy_id) ON DELETE CASCADE,
    chunk_text          TEXT NOT NULL,
    chunk_index         INTEGER NOT NULL,
    embedding           VECTOR(4096) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 벡터 인덱스는 2000차원 제한으로 인해 생략
-- 3072차원과 4096차원은 pgvector 인덱스 제한을 초과
-- 성능 최적화는 나중에 차원 축소 또는 다른 방법으로 해결
-- TODO: 벡터 검색 성능 최적화 방안 검토 필요

-- 기본 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_policies_company ON policies(company);
CREATE INDEX IF NOT EXISTS idx_policies_category ON policies(category);
CREATE INDEX IF NOT EXISTS idx_policies_created_at ON policies(created_at);
CREATE INDEX IF NOT EXISTS idx_embeddings_policy_id ON embeddings_text_embedding_3(policy_id);

-- 기본 관리자 사용자 생성 (개발용)
INSERT INTO users (email, password_hash, role) 
VALUES ('admin@ispl2.com', 'admin', 'ADMIN')
ON CONFLICT (email) DO NOTHING;

-- 기본 사용자 생성 (개발용)
INSERT INTO users (email, password_hash, role) 
VALUES ('user@ispl2.com', 'user', 'USER')
ON CONFLICT (email) DO NOTHING;

-- 데이터베이스 설정 확인 쿼리
SELECT 'Database initialized successfully' as status;
SELECT version() as postgresql_version;
SELECT * FROM pg_extension WHERE extname = 'vector';

