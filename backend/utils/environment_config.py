"""
환경 설정 유틸리티
보안 등급별 환경 변수 관리 및 설정 검증
"""
import os
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """보안 등급 (multi_model_embedding.py와 동일)"""
    PUBLIC = "public"
    RESTRICTED = "restricted" 
    CLOSED = "closed"

class EnvironmentConfig:
    """환경 설정 관리자"""
    
    def __init__(self):
        # .env 파일 로드
        load_dotenv()
        self.security_level = self._get_security_level()
        logger.info(f"환경 설정 초기화: 보안등급={self.security_level.value}")
    
    def _get_security_level(self) -> SecurityLevel:
        """환경 변수에서 보안 등급 읽기"""
        level_str = os.getenv("SECURITY_LEVEL", "public").lower()
        try:
            return SecurityLevel(level_str)
        except ValueError:
            logger.warning(f"알 수 없는 보안 등급: {level_str}, 기본값 'public' 사용")
            return SecurityLevel.PUBLIC
    
    def get_openai_config(self) -> Dict[str, Optional[str]]:
        """OpenAI 설정 반환"""
        return {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "organization": os.getenv("OPENAI_ORGANIZATION"),
            "base_url": os.getenv("OPENAI_BASE_URL")
        }
    
    def get_azure_openai_config(self) -> Dict[str, Optional[str]]:
        """Azure OpenAI 설정 반환"""
        return {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        }
    
    def get_local_model_config(self) -> Dict[str, Optional[str]]:
        """로컬 모델 설정 반환"""
        return {
            "embedding_model_path": os.getenv("LOCAL_EMBEDDING_MODEL_PATH"),
            "qwen_model_path": os.getenv("QWEN_MODEL_PATH"),
            "device": os.getenv("LOCAL_MODEL_DEVICE", "cpu")
        }
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """임베딩 관련 설정 반환"""
        return {
            "batch_size": int(os.getenv("EMBEDDING_BATCH_SIZE", "100")),
            "max_tokens": int(os.getenv("EMBEDDING_MAX_TOKENS", "8192")),
            "overlap_ratio": float(os.getenv("EMBEDDING_OVERLAP_RATIO", "0.15"))
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """현재 보안 등급에 필요한 설정 검증"""
        validation_result = {
            "security_level": self.security_level.value,
            "valid": True,
            "missing_configs": [],
            "warnings": [],
            "recommendations": []
        }
        
        if self.security_level == SecurityLevel.PUBLIC:
            # 공개망: OpenAI API 키 필요
            openai_config = self.get_openai_config()
            if not openai_config["api_key"]:
                validation_result["valid"] = False
                validation_result["missing_configs"].append("OPENAI_API_KEY")
                validation_result["recommendations"].append("OpenAI API 키를 설정하세요")
        
        elif self.security_level == SecurityLevel.RESTRICTED:
            # 조건부 폐쇄망: Azure OpenAI 설정 필요
            azure_config = self.get_azure_openai_config()
            if not azure_config["api_key"] or not azure_config["endpoint"]:
                validation_result["warnings"].append("Azure OpenAI 설정이 불완전합니다. OpenAI로 fallback됩니다")
                
                # OpenAI fallback 검증
                openai_config = self.get_openai_config()
                if not openai_config["api_key"]:
                    validation_result["valid"] = False
                    validation_result["missing_configs"].append("AZURE_OPENAI_API_KEY 또는 OPENAI_API_KEY")
                    validation_result["recommendations"].append("Azure OpenAI 또는 OpenAI API 키를 설정하세요")
        
        elif self.security_level == SecurityLevel.CLOSED:
            # 완전 폐쇄망: 로컬 모델 경로 필요
            local_config = self.get_local_model_config()
            if not local_config["embedding_model_path"]:
                validation_result["warnings"].append("로컬 임베딩 모델 경로가 설정되지 않았습니다")
                validation_result["recommendations"].append("LOCAL_EMBEDDING_MODEL_PATH를 설정하거나 Qwen 모델을 사용하세요")
            
            if not local_config["qwen_model_path"]:
                validation_result["warnings"].append("Qwen 모델 경로가 설정되지 않았습니다")
        
        # 데이터베이스 설정 검증
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            validation_result["valid"] = False
            validation_result["missing_configs"].append("DATABASE_URL")
            validation_result["recommendations"].append("PostgreSQL 데이터베이스 URL을 설정하세요")
        
        return validation_result
    
    def get_recommended_model(self) -> str:
        """현재 보안 등급에 대한 추천 모델"""
        recommendations = {
            SecurityLevel.PUBLIC: "text-embedding-3-large",
            SecurityLevel.RESTRICTED: "azure-text-embedding", 
            SecurityLevel.CLOSED: "qwen3-8b-embed"
        }
        return recommendations[self.security_level]
    
    def print_configuration_summary(self):
        """설정 요약 출력"""
        print("\n" + "=" * 60)
        print("🔧 환경 설정 요약")
        print("=" * 60)
        print(f"보안 등급: {self.security_level.value}")
        print(f"추천 모델: {self.get_recommended_model()}")
        
        validation = self.validate_configuration()
        if validation["valid"]:
            print("✅ 설정 상태: 유효")
        else:
            print("❌ 설정 상태: 불완전")
            if validation["missing_configs"]:
                print("누락된 설정:")
                for config in validation["missing_configs"]:
                    print(f"   - {config}")
        
        if validation["warnings"]:
            print("⚠️ 경고:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
        
        if validation["recommendations"]:
            print("💡 권장사항:")
            for rec in validation["recommendations"]:
                print(f"   - {rec}")
        
        print("=" * 60)

# 전역 설정 인스턴스
config = EnvironmentConfig()

def get_environment_config() -> EnvironmentConfig:
    """전역 설정 인스턴스 반환"""
    return config

def validate_environment() -> bool:
    """환경 설정 유효성 검증"""
    validation = config.validate_configuration()
    return validation["valid"]

def print_environment_summary():
    """환경 설정 요약 출력"""
    config.print_configuration_summary()

