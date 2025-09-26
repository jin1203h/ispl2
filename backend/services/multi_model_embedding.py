"""
다중 모델 임베딩 서비스
보안 등급별 임베딩 모델 관리 및 자동 선택
"""
import os
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Type
from dataclasses import dataclass
from dotenv import load_dotenv

# 기존 임베딩 에이전트 확장
from agents.embedding_agent import EmbeddingAgent
from agents.base import ProcessedChunk

load_dotenv()
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """보안 등급"""
    PUBLIC = "public"           # 공개망 - OpenAI API
    RESTRICTED = "restricted"   # 조건부 폐쇄망 - Azure OpenAI
    CLOSED = "closed"          # 완전 폐쇄망 - 로컬 모델

class EmbeddingModelType(Enum):
    """임베딩 모델 타입"""
    OPENAI_TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    OPENAI_TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    AZURE_TEXT_EMBEDDING = "azure-text-embedding"
    QWEN_8B_EMBED = "qwen3-8b-embed"
    MULTILINGUAL_E5_LARGE = "multilingual-e5-large"

@dataclass
class ModelConfig:
    """모델 설정"""
    model_name: str
    dimensions: int
    table_name: str
    api_type: str  # "openai", "azure", "local"
    cost_per_1k_tokens: float
    max_tokens: int
    supports_batch: bool = True

class EmbeddingModelRegistry:
    """임베딩 모델 레지스트리"""
    
    MODELS = {
        EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_LARGE: ModelConfig(
            model_name="text-embedding-3-large",
            dimensions=3072,
            table_name="embeddings_text_embedding_3",
            api_type="openai",
            cost_per_1k_tokens=0.00013,
            max_tokens=8192,
            supports_batch=True
        ),
        EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_SMALL: ModelConfig(
            model_name="text-embedding-3-small", 
            dimensions=1536,
            table_name="embeddings_text_embedding_small",
            api_type="openai",
            cost_per_1k_tokens=0.00002,
            max_tokens=8192,
            supports_batch=True
        ),
        EmbeddingModelType.AZURE_TEXT_EMBEDDING: ModelConfig(
            model_name="text-embedding-ada-002",
            dimensions=1536,
            table_name="embeddings_azure_ada",
            api_type="azure",
            cost_per_1k_tokens=0.00010,
            max_tokens=8192,
            supports_batch=True
        ),
        EmbeddingModelType.QWEN_8B_EMBED: ModelConfig(
            model_name="qwen3-8b-embed",
            dimensions=4096,
            table_name="embeddings_qwen",
            api_type="local",
            cost_per_1k_tokens=0.0,  # 로컬 모델은 무료
            max_tokens=32768,
            supports_batch=False
        ),
        EmbeddingModelType.MULTILINGUAL_E5_LARGE: ModelConfig(
            model_name="multilingual-e5-large",
            dimensions=1024,
            table_name="embeddings_multilingual_e5",
            api_type="local", 
            cost_per_1k_tokens=0.0,
            max_tokens=512,
            supports_batch=True
        )
    }
    
    SECURITY_LEVEL_MODELS = {
        SecurityLevel.PUBLIC: [
            EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_LARGE,
            EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_SMALL
        ],
        SecurityLevel.RESTRICTED: [
            EmbeddingModelType.AZURE_TEXT_EMBEDDING,
            EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_LARGE  # fallback
        ],
        SecurityLevel.CLOSED: [
            EmbeddingModelType.QWEN_8B_EMBED,
            EmbeddingModelType.MULTILINGUAL_E5_LARGE
        ]
    }
    
    @classmethod
    def get_model_config(cls, model_type: EmbeddingModelType) -> ModelConfig:
        """모델 설정 조회"""
        return cls.MODELS[model_type]
    
    @classmethod
    def get_models_for_security_level(cls, security_level: SecurityLevel) -> List[EmbeddingModelType]:
        """보안 등급별 사용 가능한 모델 목록"""
        return cls.SECURITY_LEVEL_MODELS[security_level]
    
    @classmethod
    def get_default_model(cls, security_level: SecurityLevel) -> EmbeddingModelType:
        """보안 등급별 기본 모델"""
        models = cls.get_models_for_security_level(security_level)
        return models[0] if models else EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_LARGE

class MultiModelEmbeddingAgent(EmbeddingAgent):
    """다중 모델 지원 임베딩 에이전트"""
    
    def __init__(self, 
                 security_level: Optional[Union[str, SecurityLevel]] = None,
                 model_type: Optional[Union[str, EmbeddingModelType]] = None,
                 **kwargs):
        
        # 보안 등급 설정
        if isinstance(security_level, str):
            self.security_level = SecurityLevel(security_level)
        elif isinstance(security_level, SecurityLevel):
            self.security_level = security_level
        else:
            # 환경 변수에서 읽기
            env_security_level = os.getenv("SECURITY_LEVEL", "public").lower()
            self.security_level = SecurityLevel(env_security_level)
        
        # 모델 타입 설정
        if isinstance(model_type, str):
            # 문자열로 전달된 경우 enum으로 변환
            try:
                self.model_type = EmbeddingModelType(model_type)
            except ValueError:
                # 기본 모델 사용
                self.model_type = EmbeddingModelRegistry.get_default_model(self.security_level)
                logger.warning(f"알 수 없는 모델 타입: {model_type}, 기본 모델 사용: {self.model_type.value}")
        elif isinstance(model_type, EmbeddingModelType):
            self.model_type = model_type
        else:
            # 보안 등급에 따른 기본 모델 선택
            self.model_type = EmbeddingModelRegistry.get_default_model(self.security_level)
        
        # 모델 설정 로드
        self.model_config = EmbeddingModelRegistry.get_model_config(self.model_type)
        
        # 부모 클래스 초기화 (model 파라미터 전달)
        super().__init__(
            model=self.model_config.model_name,
            batch_size=kwargs.get("batch_size", 100),
        )
        
        # 추가 설정
        self._initialize_model_specific_client()
        
        logger.info(
            f"MultiModelEmbeddingAgent 초기화: "
            f"보안등급={self.security_level.value}, "
            f"모델={self.model_type.value}, "
            f"차원={self.model_config.dimensions}"
        )
    
    def _initialize_model_specific_client(self):
        """모델별 클라이언트 초기화"""
        if self.model_config.api_type == "azure":
            self._initialize_azure_client()
        elif self.model_config.api_type == "local":
            self._initialize_local_client()
        # openai는 부모 클래스에서 이미 처리됨
    
    def _initialize_azure_client(self):
        """Azure OpenAI 클라이언트 초기화"""
        try:
            from openai import AsyncAzureOpenAI
            
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
            
            if api_key and endpoint:
                self.client = AsyncAzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version=api_version
                )
                logger.info("Azure OpenAI 클라이언트 초기화 완료")
            else:
                logger.warning("Azure OpenAI 설정이 불완전합니다. OpenAI 클라이언트로 fallback")
                
        except ImportError:
            logger.warning("Azure OpenAI 라이브러리를 찾을 수 없습니다. OpenAI 클라이언트로 fallback")
    
    def _initialize_local_client(self):
        """로컬 모델 클라이언트 초기화"""
        # 로컬 모델 구현은 추후 Task 4.2에서 처리
        logger.warning(f"로컬 모델 {self.model_type.value}는 아직 구현되지 않았습니다.")
        self.client = None
    
    def get_embedding_dimension(self) -> int:
        """현재 모델의 임베딩 차원 반환"""
        return self.model_config.dimensions
    
    def get_table_name(self) -> str:
        """현재 모델에 대응하는 데이터베이스 테이블명 반환"""
        return self.model_config.table_name
    
    def estimate_cost(self, total_tokens: int) -> float:
        """현재 모델의 예상 비용 계산 (USD)"""
        return (total_tokens / 1000) * self.model_config.cost_per_1k_tokens
    
    def get_model_info(self) -> Dict[str, Any]:
        """현재 모델 정보 반환"""
        return {
            "security_level": self.security_level.value,
            "model_type": self.model_type.value,
            "model_name": self.model_config.model_name,
            "dimensions": self.model_config.dimensions,
            "table_name": self.model_config.table_name,
            "api_type": self.model_config.api_type,
            "cost_per_1k_tokens": self.model_config.cost_per_1k_tokens,
            "max_tokens": self.model_config.max_tokens,
            "supports_batch": self.model_config.supports_batch
        }
    
    @classmethod
    def create_from_security_level(cls, 
                                  security_level: Union[str, SecurityLevel],
                                  preferred_model: Optional[str] = None) -> "MultiModelEmbeddingAgent":
        """보안 등급에 따른 자동 모델 선택"""
        if isinstance(security_level, str):
            security_level = SecurityLevel(security_level)
        
        available_models = EmbeddingModelRegistry.get_models_for_security_level(security_level)
        
        if preferred_model:
            # 선호 모델이 사용 가능한지 확인
            try:
                preferred_model_type = EmbeddingModelType(preferred_model)
                if preferred_model_type in available_models:
                    model_type = preferred_model_type
                else:
                    logger.warning(f"선호 모델 {preferred_model}은 보안등급 {security_level.value}에서 사용할 수 없습니다.")
                    model_type = available_models[0]
            except ValueError:
                logger.warning(f"알 수 없는 모델: {preferred_model}")
                model_type = available_models[0]
        else:
            model_type = available_models[0]
        
        return cls(security_level=security_level, model_type=model_type)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 리스트에 대한 임베딩 생성"""
        try:
            if not self.client:
                raise ValueError("임베딩 클라이언트가 초기화되지 않았습니다")
            
            if not texts:
                return []
            
            # OpenAI 스타일 API 호출
            response = await self.client.embeddings.create(
                input=texts,
                model=self.model_config.model_name
            )
            
            embeddings = [data.embedding for data in response.data]
            
            logger.info(f"{len(texts)}개 텍스트에 대한 임베딩 생성 완료")
            return embeddings
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]):
        """기존 EmbeddingAgent와의 호환성을 위한 메서드"""
        try:
            embeddings = await self.generate_embeddings(texts)
            
            # EmbeddingAgent와 동일한 형식의 응답 객체 생성
            class EmbeddingData:
                def __init__(self, embedding: List[float], index: int):
                    self.embedding = embedding
                    self.index = index
            
            class EmbeddingResponse:
                def __init__(self, embeddings: List[List[float]]):
                    self.data = [EmbeddingData(emb, i) for i, emb in enumerate(embeddings)]
            
            return EmbeddingResponse(embeddings)
            
        except Exception as e:
            logger.error(f"호환성 임베딩 생성 실패: {e}")
            raise
    
    @classmethod
    def get_available_models(cls, security_level: Optional[Union[str, SecurityLevel]] = None) -> List[Dict[str, Any]]:
        """사용 가능한 모델 목록 조회"""
        if security_level is None:
            # 모든 모델 반환
            models = list(EmbeddingModelRegistry.MODELS.keys())
        else:
            if isinstance(security_level, str):
                security_level = SecurityLevel(security_level)
            models = EmbeddingModelRegistry.get_models_for_security_level(security_level)
        
        return [
            {
                "model_type": model.value,
                "config": EmbeddingModelRegistry.get_model_config(model).__dict__
            }
            for model in models
        ]

class MultiModelVectorStoreService:
    """다중 모델 벡터 저장소 서비스"""
    
    def __init__(self, embedding_agent: MultiModelEmbeddingAgent):
        self.embedding_agent = embedding_agent
        self.table_name = embedding_agent.get_table_name()
        self.model_config = embedding_agent.model_config
    
    async def get_table_model_class(self):
        """현재 모델에 해당하는 SQLAlchemy 모델 클래스 반환"""
        from models.database import EmbeddingTextEmbedding3, EmbeddingQwen
        
        table_model_map = {
            "embeddings_text_embedding_3": EmbeddingTextEmbedding3,
            "embeddings_qwen": EmbeddingQwen,
            # 필요시 추가 모델 매핑
        }
        
        return table_model_map.get(self.table_name, EmbeddingTextEmbedding3)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """저장소 정보 반환"""
        return {
            "table_name": self.table_name,
            "model_name": self.model_config.model_name,
            "dimensions": self.model_config.dimensions,
            "api_type": self.model_config.api_type
        }

# 전역 인스턴스
_multi_model_agent = None

def get_multi_model_agent() -> MultiModelEmbeddingAgent:
    """싱글톤 패턴으로 MultiModelEmbeddingAgent 인스턴스 반환"""
    global _multi_model_agent
    if _multi_model_agent is None:
        _multi_model_agent = MultiModelEmbeddingAgent()
    return _multi_model_agent

def get_multi_model_embedding_agent() -> MultiModelEmbeddingAgent:
    """get_multi_model_agent의 별칭 함수 (호환성을 위해)"""
    return get_multi_model_agent()
