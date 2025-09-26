"""
고급 청킹 및 토큰화 서비스
Fixed-size, Content-aware, Semantic 3가지 전략을 지원하는 텍스트 분할 시스템
"""
import re
import logging
import time
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 순환 import 방지 - 간단한 딕셔너리 타입 사용
ProcessedChunk = Dict[str, Any]  # {"text": str, "metadata": dict}
ChunkMetadata = Dict[str, Any]   # 메타데이터 딕셔너리

# 토큰화 라이브러리 import
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    print("⚠️ tiktoken이 설치되지 않았습니다. 대략적인 토큰 계산을 사용합니다.")
    TIKTOKEN_AVAILABLE = False

# 한국어 처리 라이브러리 import
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("⚠️ spaCy가 설치되지 않았습니다. 기본 문장 분할을 사용합니다.")
    SPACY_AVAILABLE = False

try:
    from konlpy.tag import Kkma
    KONLPY_AVAILABLE = True
except ImportError:
    print("⚠️ KoNLPy가 설치되지 않았습니다. 기본 문장 분할을 사용합니다.")
    KONLPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class ChunkingStrategy(Enum):
    """청킹 전략"""
    FIXED_SIZE = "fixed_size"
    CONTENT_AWARE = "content_aware" 
    SEMANTIC = "semantic"

@dataclass
class ChunkingConfig:
    """청킹 설정"""
    strategy: ChunkingStrategy = ChunkingStrategy.CONTENT_AWARE
    chunk_size: int = 200  # 토큰 기준
    overlap_ratio: float = 0.15  # 15% 중복
    min_chunk_size: int = 50  # 최소 청크 크기
    max_chunk_size: int = 300  # 최대 청크 크기
    preserve_article_boundaries: bool = True  # 조항 경계 보존
    preserve_sentence_boundaries: bool = True  # 문장 경계 보존

class BaseChunker(ABC):
    """청킹 전략 기본 클래스"""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        
        # 토큰화 초기화
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                logger.warning(f"tiktoken 초기화 실패: {e}")
                self.tokenizer = None
        else:
            self.tokenizer = None
        
        # 보험 약관 특화 패턴
        self.article_patterns = [
            r'제\s*\d+\s*조(?:\s*\([^)]+\))?',  # 제1조 (목적)
            r'제\s*\d+\s*장(?:\s*[^0-9\n]+)?',  # 제1장 총칙
            r'제\s*\d+\s*절(?:\s*[^0-9\n]+)?',  # 제1절
            r'^\d+\.\s+[^\n]+',  # 1. 정의
            r'^[가-힣]\.\s+[^\n]+',  # 가. 보험계약자
        ]
    
    def count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 계산"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # 대략적 계산: 한국어 1글자 ≈ 1토큰, 영어 1단어 ≈ 1토큰
            korean_chars = len(re.findall(r'[가-힣]', text))
            english_words = len(re.findall(r'[a-zA-Z]+', text))
            other_chars = len(text) - korean_chars - english_words
            return korean_chars + english_words + (other_chars // 4)
    
    def find_article_boundaries(self, text: str) -> List[Tuple[int, int, str]]:
        """조항 경계 찾기 (시작위치, 끝위치, 조항명)"""
        boundaries = []
        
        for pattern in self.article_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = match.start()
                article_title = match.group().strip()
                boundaries.append((start, start + len(article_title), article_title))
        
        # 위치순으로 정렬
        boundaries.sort(key=lambda x: x[0])
        return boundaries
    
    def split_sentences(self, text: str) -> List[str]:
        """문장 분할 (한국어 특화)"""
        if KONLPY_AVAILABLE:
            try:
                kkma = Kkma()
                return kkma.sentences(text)
            except Exception as e:
                logger.warning(f"KoNLPy 문장 분할 실패: {e}")
        
        # 기본 문장 분할 (정규식 기반)
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """텍스트 청킹 (구현 필요)"""
        pass

class FixedSizeChunker(BaseChunker):
    """고정 크기 청킹 전략"""
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """고정 크기로 텍스트 분할"""
        chunks = []
        chunk_index = 0
        
        # 토큰 단위로 분할
        tokens = self.tokenizer.encode(text) if self.tokenizer else text
        chunk_size = self.config.chunk_size
        overlap_size = int(chunk_size * self.config.overlap_ratio)
        
        i = 0
        while i < len(tokens):
            # 청크 범위 계산
            end = min(i + chunk_size, len(tokens))
            chunk_tokens = tokens[i:end]
            
            # 토큰을 텍스트로 변환
            if self.tokenizer:
                chunk_text = self.tokenizer.decode(chunk_tokens)
            else:
                chunk_text = text[i:end]
            
            # 청크 생성
            chunk_metadata = {
                "chunk_index": chunk_index,
                "chunk_type": "text",
                "source": "fixed_size_chunking",
                "page_number": metadata.get("page_number", 1),
                "token_count": len(chunk_tokens) if isinstance(chunk_tokens, list) else self.count_tokens(chunk_text),
                "char_count": len(chunk_text),
                "strategy": "fixed_size"
            }
            
            chunk = {
                "text": chunk_text.strip(),
                "metadata": chunk_metadata
            }
            
            if chunk["text"]:  # 빈 청크 제외
                chunks.append(chunk)
                chunk_index += 1
            
            # 다음 시작 위치 (중복 고려)
            i += chunk_size - overlap_size
        
        logger.info(f"고정 크기 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks

class ContentAwareChunker(BaseChunker):
    """내용 인식 청킹 전략 (조항 경계 고려)"""
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """조항 구조를 고려한 텍스트 분할"""
        chunks = []
        chunk_index = 0
        
        if self.config.preserve_article_boundaries:
            # 조항 경계 찾기
            article_boundaries = self.find_article_boundaries(text)
            
            if article_boundaries:
                return self._chunk_by_articles(text, article_boundaries, metadata)
        
        # 조항이 없으면 문장 기반 청킹
        return self._chunk_by_sentences(text, metadata)
    
    def _chunk_by_articles(self, text: str, boundaries: List[Tuple[int, int, str]], 
                          metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """조항별 청킹"""
        chunks = []
        chunk_index = 0
        
        for i, (start, _, article_title) in enumerate(boundaries):
            # 다음 조항까지의 텍스트
            if i + 1 < len(boundaries):
                end = boundaries[i + 1][0]
            else:
                end = len(text)
            
            article_text = text[start:end].strip()
            
            if not article_text:
                continue
            
            # 조항이 너무 크면 문장 단위로 재분할
            token_count = self.count_tokens(article_text)
            
            if token_count <= self.config.max_chunk_size:
                # 단일 청크로 처리
                chunk_metadata = {
                    "chunk_index": chunk_index,
                    "chunk_type": "text",
                    "source": "content_aware_chunking",
                    "page_number": metadata.get("page_number", 1),
                    "token_count": token_count,
                    "char_count": len(article_text),
                    "strategy": "content_aware",
                    "article_title": article_title
                }
                
                chunk = {
                    "text":article_text,
                    "metadata":chunk_metadata
                }
                chunks.append(chunk)
                chunk_index += 1
                
            else:
                # 문장 단위로 재분할
                article_chunks = self._chunk_large_article(article_text, article_title, metadata, chunk_index)
                chunks.extend(article_chunks)
                chunk_index += len(article_chunks)
        
        logger.info(f"조항 기반 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks
    
    def _chunk_large_article(self, article_text: str, article_title: str, 
                            metadata: Dict[str, Any], start_index: int) -> List[ProcessedChunk]:
        """큰 조항을 문장 단위로 분할"""
        chunks = []
        sentences = self.split_sentences(article_text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_index = start_index
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # 현재 청크에 문장 추가 가능한지 확인
            if current_tokens + sentence_tokens <= self.config.chunk_size:
                current_chunk += (" " if current_chunk else "") + sentence
                current_tokens += sentence_tokens
            else:
                # 현재 청크 저장
                if current_chunk.strip():
                    chunk_metadata = {
                        "chunk_index": chunk_index,
                        "chunk_type": "text",
                        "source": "content_aware_chunking",
                        "page_number": metadata.get("page_number", 1),
                        "token_count": current_tokens,
                        "char_count": len(current_chunk),
                        "strategy": "content_aware",
                        "article_title": article_title
                    }
                    
                    chunk = {
                        "text":current_chunk.strip(),
                        "metadata":chunk_metadata
                    }
                    chunks.append(chunk)
                    chunk_index += 1
                
                # 새 청크 시작
                current_chunk = sentence
                current_tokens = sentence_tokens
        
        # 마지막 청크 저장
        if current_chunk.strip():
            chunk_metadata = {
                "chunk_index": chunk_index,
                "chunk_type": "text",
                "source": "content_aware_chunking",
                "page_number": metadata.get("page_number", 1),
                "token_count": current_tokens,
                "char_count": len(current_chunk),
                "strategy": "content_aware",
                "article_title": article_title
            }
            
            chunk = {
                "text":current_chunk.strip(),
                "metadata": chunk_metadata
            }
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """문장 기반 청킹"""
        chunks = []
        sentences = self.split_sentences(text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # 청크 크기 체크
            if current_tokens + sentence_tokens <= self.config.chunk_size:
                current_chunk += (" " if current_chunk else "") + sentence
                current_tokens += sentence_tokens
            else:
                # 현재 청크 저장
                if current_chunk.strip():
                    chunk_metadata = {
                        "chunk_index": chunk_index,
                        chunk_type="text",
                        source="content_aware_chunking",
                        page_number=metadata.get("page_number", 1),
                        token_count=current_tokens,
                        char_count=len(current_chunk),
                        strategy="content_aware"
                    }
                    
                    chunk = {
                        "text":current_chunk.strip(),
                        "metadata":chunk_metadata
                    }
                    chunks.append(chunk)
                    chunk_index += 1
                
                # 새 청크 시작
                current_chunk = sentence
                current_tokens = sentence_tokens
        
        # 마지막 청크 저장
        if current_chunk.strip():
            chunk_metadata = ChunkMetadata(
                chunk_index=chunk_index,
                chunk_type="text",
                source="content_aware_chunking",
                page_number=metadata.get("page_number", 1),
                token_count=current_tokens,
                char_count=len(current_chunk),
                strategy="content_aware"
            )
            
            chunk = {
                "text":current_chunk.strip(),
                "metadata": chunk_metadata
            }
            chunks.append(chunk)
        
        logger.info(f"문장 기반 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks

class SemanticChunker(BaseChunker):
    """의미적 청킹 전략 (주제별 분할)"""
    
    def __init__(self, config: ChunkingConfig):
        super().__init__(config)
        
        # 보험 용어 키워드 그룹
        self.semantic_keywords = {
            "보험계약": ["보험계약", "계약자", "피보험자", "보험가입", "계약조건"],
            "보험금": ["보험금", "보상", "지급", "청구", "지급기준"],
            "보험료": ["보험료", "납입", "납부", "연체", "할인", "할증"],
            "보험사고": ["보험사고", "사고", "손해", "위험", "재해"],
            "면책": ["면책", "제외", "부담하지", "적용되지"],
            "기타": []  # 기본 그룹
        }
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """주제별 의미적 텍스트 분할"""
        # 먼저 조항별로 분할
        article_boundaries = self.find_article_boundaries(text)
        
        if article_boundaries:
            return self._semantic_chunk_by_articles(text, article_boundaries, metadata)
        else:
            return self._semantic_chunk_by_topics(text, metadata)
    
    def _semantic_chunk_by_articles(self, text: str, boundaries: List[Tuple[int, int, str]], 
                                   metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """조항별 의미적 청킹"""
        chunks = []
        chunk_index = 0
        
        for i, (start, _, article_title) in enumerate(boundaries):
            # 조항 텍스트 추출
            if i + 1 < len(boundaries):
                end = boundaries[i + 1][0]
            else:
                end = len(text)
            
            article_text = text[start:end].strip()
            if not article_text:
                continue
            
            # 조항 내에서 주제별 분할
            topic = self._identify_topic(article_text)
            token_count = self.count_tokens(article_text)
            
            if token_count <= self.config.max_chunk_size:
                # 단일 청크
                chunk_metadata = {
                    chunk_index=chunk_index,
                    chunk_type="text",
                    source="semantic_chunking",
                    page_number=metadata.get("page_number", 1),
                    token_count=token_count,
                    char_count=len(article_text),
                    strategy="semantic",
                    article_title=article_title,
                    semantic_topic=topic
                }
                
                chunk = {
                    "text":article_text,
                    "metadata":chunk_metadata
                }
                chunks.append(chunk)
                chunk_index += 1
            else:
                # 큰 조항은 주제별로 세분화
                article_chunks = self._split_large_article_by_topic(
                    article_text, article_title, metadata, chunk_index
                )
                chunks.extend(article_chunks)
                chunk_index += len(article_chunks)
        
        logger.info(f"의미적 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks
    
    def _identify_topic(self, text: str) -> str:
        """텍스트의 주제 식별"""
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in self.semantic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        # 가장 높은 점수의 주제 반환
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        else:
            return "기타"
    
    def _split_large_article_by_topic(self, article_text: str, article_title: str,
                                     metadata: Dict[str, Any], start_index: int) -> List[ProcessedChunk]:
        """큰 조항을 주제별로 분할"""
        # 현재는 문장 기반으로 분할 (추후 개선 가능)
        sentences = self.split_sentences(article_text)
        chunks = []
        
        current_chunk = ""
        current_tokens = 0
        current_topic = None
        chunk_index = start_index
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            sentence_topic = self._identify_topic(sentence)
            
            # 주제가 바뀌거나 크기 초과 시 청크 분할
            if (current_topic and current_topic != sentence_topic) or \
               (current_tokens + sentence_tokens > self.config.chunk_size):
                
                # 현재 청크 저장
                if current_chunk.strip():
                    chunk_metadata = {
                        "chunk_index": chunk_index,
                        chunk_type="text",
                        source="semantic_chunking",
                        page_number=metadata.get("page_number", 1),
                        token_count=current_tokens,
                        char_count=len(current_chunk),
                        strategy="semantic",
                        article_title=article_title,
                        semantic_topic=current_topic
                    }
                    
                    chunk = {
                        "text":current_chunk.strip(),
                        "metadata":chunk_metadata
                    }
                    chunks.append(chunk)
                    chunk_index += 1
                
                # 새 청크 시작
                current_chunk = sentence
                current_tokens = sentence_tokens
                current_topic = sentence_topic
            else:
                # 현재 청크에 추가
                current_chunk += (" " if current_chunk else "") + sentence
                current_tokens += sentence_tokens
                if not current_topic:
                    current_topic = sentence_topic
        
        # 마지막 청크 저장
        if current_chunk.strip():
            chunk_metadata = ChunkMetadata(
                chunk_index=chunk_index,
                chunk_type="text",
                source="semantic_chunking",
                page_number=metadata.get("page_number", 1),
                token_count=current_tokens,
                char_count=len(current_chunk),
                strategy="semantic",
                article_title=article_title,
                semantic_topic=current_topic
            )
            
            chunk = {
                "text":current_chunk.strip(),
                "metadata": chunk_metadata
            }
            chunks.append(chunk)
        
        return chunks
    
    def _semantic_chunk_by_topics(self, text: str, metadata: Dict[str, Any]) -> List[ProcessedChunk]:
        """전체 텍스트를 주제별로 청킹"""
        # 기본적으로는 content-aware와 동일하게 처리
        content_chunker = ContentAwareChunker(self.config)
        base_chunks = content_chunker._chunk_by_sentences(text, metadata)
        
        # 각 청크에 주제 정보 추가
        for chunk in base_chunks:
            topic = self._identify_topic(chunk["text"])
            chunk["metadata"]["semantic_topic"] = topic
            chunk["metadata"]["strategy"] = "semantic"
            chunk["metadata"]["source"] = "semantic_chunking"
        
        return base_chunks

class AdvancedChunkingService:
    """고급 청킹 서비스 메인 클래스"""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        
        # 전략별 청킹 클래스 매핑
        self.chunkers = {
            ChunkingStrategy.FIXED_SIZE: FixedSizeChunker(self.config),
            ChunkingStrategy.CONTENT_AWARE: ContentAwareChunker(self.config),
            ChunkingStrategy.SEMANTIC: SemanticChunker(self.config)
        }
        
        logger.info(f"AdvancedChunkingService 초기화: 전략={self.config.strategy.value}")
    
    async def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[ProcessedChunk]:
        """텍스트 청킹 실행"""
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        start_time = time.time()
        
        # 선택된 전략으로 청킹
        chunker = self.chunkers[self.config.strategy]
        chunks = chunker.chunk_text(text, metadata)
        
        # 청킹 후 검증 및 최적화
        chunks = self._post_process_chunks(chunks)
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"청킹 완료: 전략={self.config.strategy.value}, "
            f"청크수={len(chunks)}, 처리시간={processing_time:.2f}초"
        )
        
        return chunks
    
    def _post_process_chunks(self, chunks: List[ProcessedChunk]) -> List[ProcessedChunk]:
        """청킹 후처리 (크기 검증, 중복 제거 등)"""
        processed_chunks = []
        
        for chunk in chunks:
            # 빈 텍스트 체크
            if not chunk["text"] or not chunk["text"].strip():
                continue
            
            # 최소 크기 체크 (테스트 모드에서는 완화)
            token_count = chunk["metadata"]["token_count"]
            if token_count < self.config.min_chunk_size:
                # 매우 작은 텍스트라도 의미가 있으면 보존
                if token_count >= 10 or "테스트" in chunk.get("metadata", {}).get("source", ""):
                    pass  # 보존
                else:
                    continue  # 필터링
            
            # 최대 크기 체크
            if token_count > self.config.max_chunk_size:
                # 큰 청크는 추가 분할 (간단한 고정 크기 분할)
                large_chunk_text = chunk["text"]
                chunker = self.chunkers[ChunkingStrategy.FIXED_SIZE]
                sub_chunks = chunker.chunk_text(large_chunk_text, chunk["metadata"])
                processed_chunks.extend(sub_chunks)
            else:
                processed_chunks.append(chunk)
        
        return processed_chunks
    
    def get_chunking_stats(self, chunks: List[ProcessedChunk]) -> Dict[str, Any]:
        """청킹 통계 생성"""
        if not chunks:
            return {}
        
        token_counts = [chunk["metadata"]["token_count"] for chunk in chunks]
        char_counts = [chunk["metadata"]["char_count"] for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_tokens_per_chunk": sum(token_counts) / len(token_counts),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "total_tokens": sum(token_counts),
            "avg_chars_per_chunk": sum(char_counts) / len(char_counts),
            "total_chars": sum(char_counts),
            "strategy": self.config.strategy.value,
            "chunk_size_target": self.config.chunk_size,
            "overlap_ratio": self.config.overlap_ratio
        }
    
    @classmethod
    def create_with_strategy(cls, strategy: Union[str, ChunkingStrategy], **config_kwargs) -> "AdvancedChunkingService":
        """전략별 청킹 서비스 생성"""
        if isinstance(strategy, str):
            strategy = ChunkingStrategy(strategy)
        
        config = ChunkingConfig(strategy=strategy, **config_kwargs)
        return cls(config)
