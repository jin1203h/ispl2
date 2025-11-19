"""
SQLAlchemy 데이터베이스 모델
기존 데이터베이스 스키마와 호환
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

# pgvector import
from pgvector.sqlalchemy import Vector
PGVECTOR_AVAILABLE = True

Base = declarative_base()

class User(Base):
    """사용자 테이블 모델"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 제약 조건
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'USER')", name="check_user_role"),
    )

class Policy(Base):
    """약관 테이블 모델"""
    __tablename__ = "policies"
    
    policy_id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String(100))
    category = Column(String(100))
    product_type = Column(String(100))
    product_name = Column(String(255), nullable=False)
    sale_start_dt = Column(String(8))
    sale_end_dt = Column(String(8))
    sale_stat = Column(String(10))
    summary = Column(Text)
    original_path = Column(String(500))
    md_path = Column(String(500))
    pdf_path = Column(String(500))
    created_at = Column(DateTime, default=func.current_timestamp())
    security_level = Column(String(20))
    
    # 관계 설정
    embeddings_text = relationship("EmbeddingTextEmbedding3", back_populates="policy", cascade="all, delete-orphan")
    embeddings_qwen = relationship("EmbeddingQwen", back_populates="policy", cascade="all, delete-orphan")

class EmbeddingTextEmbedding3(Base):
    """text-embedding-3 임베딩 테이블 모델 (3072차원)"""
    __tablename__ = "embeddings_text_embedding_3"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(3072), nullable=False)
    model = Column(String(100), nullable=False, default="text-embedding-3-large")
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 관계 설정
    policy = relationship("Policy", back_populates="embeddings_text")

class EmbeddingQwen(Base):
    """Qwen 임베딩 테이블 모델 (4096차원)"""
    __tablename__ = "embeddings_qwen"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(Integer, ForeignKey("policies.policy_id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(4096), nullable=False)
    model = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 관계 설정
    policy = relationship("Policy", back_populates="embeddings_qwen")

class WorkflowLog(Base):
    """워크플로우 로그 테이블 모델 (LangFuse 연동용)"""
    __tablename__ = "workflow_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(255), nullable=False)
    step_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # completed, error, running, pending
    input_data = Column(Text)  # JSON 형태로 저장
    output_data = Column(Text)  # JSON 형태로 저장
    error_message = Column(Text)
    execution_time = Column(Integer)  # milliseconds
    start_time = Column(DateTime)  # 시작 시간
    end_time = Column(DateTime)    # 종료 시간
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 제약 조건
    __table_args__ = (
        CheckConstraint("status IN ('completed', 'error', 'running', 'pending')", name="check_workflow_status"),
    )
