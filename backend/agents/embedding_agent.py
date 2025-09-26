"""
임베딩 생성 에이전트
OpenAI API를 활용한 임베딩 생성
"""
import os
import time
import asyncio
from typing import List, Dict, Any, Optional
from .base import BaseAgent, DocumentProcessingState, ProcessingStatus, ProcessedChunk

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("⚠️ OpenAI 라이브러리가 설치되지 않았습니다. 임베딩 생성이 제한됩니다.")
    OPENAI_AVAILABLE = False

class EmbeddingAgent(BaseAgent):
    """임베딩 생성 에이전트"""
    
    def __init__(self, model: str = "text-embedding-3-large", batch_size: int = 100):
        super().__init__(
            name="embedding_agent",
            description="텍스트 청크들에 대해 임베딩을 생성합니다"
        )
        self.model = model
        self.batch_size = batch_size
        
        # OpenAI 클라이언트 초기화
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
            else:
                self.client = None
                print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        else:
            self.client = None
    
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """임베딩 생성"""
        self.log_step(state, "임베딩 생성 시작")
        
        if not self.client:
            self.log_step(state, "OpenAI 클라이언트가 초기화되지 않음, 건너뛰기", "warning")
            return self.update_status(state, ProcessingStatus.SKIPPED, "embedding_generation")
        
        try:
            start_time = time.time()
            
            processed_chunks = state.get("processed_chunks", [])
            if not processed_chunks:
                self.log_step(state, "처리할 청크가 없음", "warning")
                return self.update_status(state, ProcessingStatus.SKIPPED, "embedding_generation")
            
            # 임베딩이 없는 청크들만 필터링
            chunks_need_embedding = [
                chunk for chunk in processed_chunks 
                if chunk.get("embedding") is None
            ]
            
            if not chunks_need_embedding:
                self.log_step(state, "모든 청크에 임베딩이 이미 있음")
                state["embeddings_created"] = True
                return self.update_status(state, ProcessingStatus.COMPLETED, "embedding_generation")
            
            self.log_step(state, f"{len(chunks_need_embedding)}개 청크에 대해 임베딩 생성")
            
            # 배치 단위로 임베딩 생성
            total_chunks = len(chunks_need_embedding)
            processed_count = 0
            
            for i in range(0, total_chunks, self.batch_size):
                batch_chunks = chunks_need_embedding[i:i + self.batch_size]
                
                # 배치 임베딩 생성
                embeddings = await self._create_embeddings_batch(batch_chunks)
                
                # 임베딩을 청크에 할당
                for chunk, embedding in zip(batch_chunks, embeddings):
                    chunk["embedding"] = embedding
                
                processed_count += len(batch_chunks)
                self.log_step(
                    state, 
                    f"임베딩 진행률: {processed_count}/{total_chunks} "
                    f"({processed_count/total_chunks*100:.1f}%)"
                )
                
                # API 호출 제한 방지
                if i + self.batch_size < total_chunks:
                    await asyncio.sleep(0.1)
            
            processing_time = time.time() - start_time
            state["embeddings_created"] = True
            
            self.log_step(
                state,
                f"임베딩 생성 완료: {total_chunks}개 청크, "
                f"모델: {self.model}, 처리시간: {processing_time:.2f}초"
            )
            
            return self.update_status(state, ProcessingStatus.COMPLETED, "embedding_generation")
            
        except Exception as e:
            error_msg = f"임베딩 생성 중 오류 발생: {str(e)}"
            self.log_step(state, error_msg, "error")
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "embedding_generation",
                error_msg
            )
    
    async def _create_embeddings_batch(self, chunks: List[ProcessedChunk]) -> List[List[float]]:
        """배치 단위로 임베딩 생성"""
        texts = [chunk["text"] for chunk in chunks]
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [embedding.embedding for embedding in response.data]
            return embeddings
            
        except Exception as e:
            self.log_step({}, f"배치 임베딩 생성 실패: {str(e)}", "error")
            # 실패 시 빈 임베딩 반환
            return [[] for _ in chunks]
    
    async def create_single_embedding(self, text: str) -> Optional[List[float]]:
        """단일 텍스트에 대한 임베딩 생성 (검색 시 사용)"""
        if not self.client:
            return None
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            return response.data[0].embedding
            
        except Exception as e:
            print(f"단일 임베딩 생성 실패: {e}")
            return None
    
    def get_embedding_dimension(self) -> int:
        """모델별 임베딩 차원 반환"""
        dimension_map = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536
        }
        return dimension_map.get(self.model, 1536)
    
    def estimate_cost(self, total_tokens: int) -> float:
        """예상 비용 계산 (USD)"""
        # OpenAI 임베딩 비용 (2024년 기준)
        cost_per_1k_tokens = {
            "text-embedding-3-large": 0.00013,
            "text-embedding-3-small": 0.00002,
            "text-embedding-ada-002": 0.00010
        }
        
        rate = cost_per_1k_tokens.get(self.model, 0.00013)
        return (total_tokens / 1000) * rate
