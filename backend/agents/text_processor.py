"""
텍스트 추출 및 정제 강화 에이전트
pdfplumber, OCR, 약관 특화 정제를 활용한 고품질 텍스트 추출
"""
import re
import time
import os
from typing import List, Dict, Any, Optional
from .base import BaseAgent, DocumentProcessingState, ProcessingStatus, ProcessedChunk, ChunkMetadata

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    print("⚠️ pdfplumber가 설치되지 않았습니다. 텍스트 추출이 제한됩니다.")
    PDFPLUMBER_AVAILABLE = False

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    print("⚠️ tiktoken이 설치되지 않았습니다. 기본 청킹을 사용합니다.")
    TIKTOKEN_AVAILABLE = False

# OCR 및 텍스트 정제 서비스 import
try:
    from services.ocr_service import OCRService
    from utils.text_cleaner import InsuranceTextCleaner, KoreanTextProcessor
    ENHANCED_PROCESSING_AVAILABLE = True
except ImportError:
    print("⚠️ OCR 서비스 또는 텍스트 정제 유틸리티를 사용할 수 없습니다.")
    ENHANCED_PROCESSING_AVAILABLE = False

# 고급 청킹 서비스 import
try:
    from services.chunking_service import AdvancedChunkingService, ChunkingStrategy, ChunkingConfig
    ADVANCED_CHUNKING_AVAILABLE = True
    print("✅ 고급 청킹 서비스 사용 가능")
except ImportError as e:
    print(f"⚠️ 고급 청킹 서비스를 사용할 수 없습니다: {e}")
    ADVANCED_CHUNKING_AVAILABLE = False

class TextProcessorAgent(BaseAgent):
    """텍스트 추출 및 정제 강화 에이전트"""
    
    def __init__(self, chunk_size: int = 200, chunk_overlap: int = 40, 
                 chunking_strategy: str = "content_aware"):
        super().__init__(
            name="text_processor",
            description="PDF에서 고품질 텍스트를 추출하고 약관 특화 정제 및 청킹을 수행합니다"
        )
        self.chunk_size = chunk_size  # 토큰 단위
        self.chunk_overlap = chunk_overlap  # 토큰 단위
        
        # tiktoken 인코더 초기화
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 기준
            except Exception:
                self.tokenizer = None
                self.log_step({}, "tiktoken 인코더 초기화 실패, 문자 기반 청킹 사용", "warning")
        else:
            self.tokenizer = None
        
        # 강화된 처리 서비스들 초기화
        if ENHANCED_PROCESSING_AVAILABLE:
            self.ocr_service = OCRService()
            self.text_cleaner = InsuranceTextCleaner()
            self.korean_processor = KoreanTextProcessor()
        else:
            self.ocr_service = None
            self.text_cleaner = None
            self.korean_processor = None
        
        # 고급 청킹 서비스 초기화
        if ADVANCED_CHUNKING_AVAILABLE:
            try:
                strategy = ChunkingStrategy(chunking_strategy)
                overlap_ratio = chunk_overlap / chunk_size if chunk_size > 0 else 0.15
                
                chunking_config = ChunkingConfig(
                    strategy=strategy,
                    chunk_size=chunk_size,
                    overlap_ratio=overlap_ratio,
                    preserve_article_boundaries=True,
                    preserve_sentence_boundaries=True
                )
                
                self.chunking_service = AdvancedChunkingService(chunking_config)
                self.log_step({}, f"고급 청킹 서비스 초기화: 전략={chunking_strategy}, 크기={chunk_size}")
                
            except Exception as e:
                self.log_step({}, f"고급 청킹 서비스 초기화 실패: {e}", "warning")
                self.chunking_service = None
        else:
            self.chunking_service = None
    
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """고급 텍스트 추출 및 정제 수행"""
        self.log_step(state, "텍스트 추출 및 정제 강화 시작")
        state["current_step"] = "enhanced_text_extraction"

        if not PDFPLUMBER_AVAILABLE:
            return self.update_status(
                state,
                ProcessingStatus.SKIPPED,
                "enhanced_text_extraction",
                "pdfplumber 라이브러리 없음"
            )
        
        file_path = state["file_path"]
        extracted_texts: List[Dict[str, Any]] = []
        processed_chunks: List[ProcessedChunk] = state.get("processed_chunks", [])
        
        # 처리 전략 가져오기
        processing_strategy = state.get("processing_strategy", {})
        ocr_required = processing_strategy.get("ocr_required", False)
        
        try:
            with pdfplumber.open(file_path) as pdf:
                self.log_step(state, f"PDF 열기 완료: {len(pdf.pages)}페이지")
                
                for i, page in enumerate(pdf.pages):
                    page_text = await self._extract_page_text_enhanced(
                        page, i + 1, file_path, ocr_required
                    )
                    
                    if page_text:
                        # 텍스트 정제
                        cleaned_text = self._clean_extracted_text(page_text)
                        
                        extracted_texts.append({
                            "page_number": i + 1, 
                            "original_text": page_text,
                            "cleaned_text": cleaned_text,
                            "extraction_method": "pdfplumber_enhanced" if not ocr_required else "pdfplumber_ocr"
                        })
                        
                        # 정제된 텍스트로 청킹
                        if cleaned_text.strip():
                            chunks = await self._chunk_text_enhanced(cleaned_text, i + 1)
                            processed_chunks.extend(chunks)
                    
                    # 진행률 업데이트
                    state["processed_pages"] = i + 1
            
            # 추출 통계
            total_text_length = sum(len(t["cleaned_text"]) for t in extracted_texts)
            
            state["extracted_text"] = extracted_texts
            state["processed_chunks"] = processed_chunks
            state["total_chunks"] = len(processed_chunks)
            state["text_extraction_stats"] = {
                "total_pages": len(extracted_texts),
                "total_text_length": total_text_length,
                "average_text_per_page": total_text_length / len(extracted_texts) if extracted_texts else 0,
                "ocr_used": ocr_required
            }
            
            self.log_step(
                state, 
                f"고급 텍스트 추출 완료: {len(processed_chunks)}개 청크, "
                f"총 {total_text_length:,}자, OCR {'사용' if ocr_required else '미사용'}"
            )
            
            return self.update_status(
                state,
                ProcessingStatus.COMPLETED,
                "enhanced_text_extraction",
                None
            )

        except Exception as e:
            error_msg = f"고급 텍스트 추출 중 오류 발생: {str(e)}"
            self.log_step(state, error_msg, "error")
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "enhanced_text_extraction",
                error_msg
            )
    
    async def _extract_page_text_enhanced(self, page, page_number: int, file_path: str, ocr_required: bool) -> str:
        """페이지별 강화된 텍스트 추출"""
        try:
            # 기본 pdfplumber 추출
            base_text = page.extract_text() or ""
            
            # OCR이 필요하고 서비스가 사용 가능한 경우
            if ocr_required and self.ocr_service and len(base_text.strip()) < 50:
                self.log_step({}, f"페이지 {page_number}: OCR 추출 시도", "debug")
                
                # 페이지를 이미지로 변환하여 OCR 적용
                try:
                    # pdfplumber의 to_image 기능 사용
                    img = page.to_image(resolution=300)
                    
                    # 임시 이미지 파일로 저장
                    temp_img_path = f"temp_page_{page_number}.png"
                    img.save(temp_img_path)
                    
                    # OCR 적용
                    ocr_result = self.ocr_service.extract_text_from_image(temp_img_path)
                    ocr_text = ocr_result.get("text", "")
                    
                    # 임시 파일 정리
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                    
                    # OCR 결과가 더 좋으면 사용
                    if len(ocr_text.strip()) > len(base_text.strip()):
                        self.log_step({}, f"페이지 {page_number}: OCR 텍스트 사용 (신뢰도: {ocr_result.get('confidence', 0):.1f}%)", "debug")
                        return ocr_text
                    
                except Exception as e:
                    self.log_step({}, f"페이지 {page_number}: OCR 실패 - {str(e)}", "warning")
            
            return base_text
            
        except Exception as e:
            self.log_step({}, f"페이지 {page_number}: 텍스트 추출 실패 - {str(e)}", "error")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """추출된 텍스트 정제"""
        if not text or not self.text_cleaner:
            return text
        
        try:
            # 보험약관 특화 정제
            cleaned_text = self.text_cleaner.clean_full_text(text)
            
            # 한글 특화 처리
            if self.korean_processor:
                cleaned_text = self.korean_processor.normalize_korean_spacing(cleaned_text)
            
            return cleaned_text
            
        except Exception as e:
            self.log_step({}, f"텍스트 정제 실패: {str(e)}", "warning")
            return text
    
    async def _chunk_text_enhanced(self, text: str, page_number: int) -> List[ProcessedChunk]:
        """고급 청킹 서비스를 활용한 강화된 텍스트 청킹"""
        
        # 고급 청킹 서비스 사용
        if self.chunking_service:
            try:
                metadata = {
                    "page_number": page_number,
                    "source": "enhanced_text_extraction"
                }
                
                chunks = await self.chunking_service.chunk_text(text, metadata)
                
                # 청킹 통계 로그
                if chunks:
                    stats = self.chunking_service.get_chunking_stats(chunks)
                    self.log_step({}, 
                        f"고급 청킹 완료: {stats['total_chunks']}개 청크, "
                        f"평균 {stats['avg_tokens_per_chunk']:.1f}토큰, "
                        f"전략: {stats['strategy']}"
                    )
                
                return chunks
                
            except Exception as e:
                self.log_step({}, f"고급 청킹 실패, 기본 청킹으로 fallback: {str(e)}", "warning")
        
        # Fallback: 기존 청킹 방식
        if not self.tokenizer:
            return self._simple_char_chunking(text, page_number)
        
        try:
            # 약관 구조 분석 (가능한 경우)
            articles = []
            if self.text_cleaner:
                articles = self.text_cleaner.extract_article_structure(text)
            
            chunks: List[ProcessedChunk] = []
            
            if articles:
                # 약관별 청킹
                for article in articles:
                    article_text = f"제{article['article_number']}조 {article['title']}\n{article['content']}"
                    article_chunks = self._tokenize_and_chunk(article_text, page_number, f"article_{article['article_number']}")
                    chunks.extend(article_chunks)
            else:
                # 일반 토큰 기반 청킹
                chunks = self._tokenize_and_chunk(text, page_number, "general")
            
            return chunks
            
        except Exception as e:
            self.log_step({}, f"강화된 청킹 실패, 기본 청킹 사용: {str(e)}", "warning")
            return self._tokenize_and_chunk(text, page_number, "fallback")
    
    def _tokenize_and_chunk(self, text: str, page_number: int, chunk_type: str) -> List[ProcessedChunk]:
        """토큰 기반 청킹 수행"""
        tokens = self.tokenizer.encode(text)
        chunks: List[ProcessedChunk] = []
        
        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i : i + self.chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            metadata: ChunkMetadata = {
                "chunk_index": len(chunks),
                "page_number": page_number,
                "chunk_type": f"text_{chunk_type}",
                "source": f"policy_page_{page_number}_{chunk_type}",
                "confidence": None
            }
            
            chunk: ProcessedChunk = {
                "text": chunk_text.strip(),
                "metadata": metadata,
                "embedding": None
            }
            
            if chunk["text"]:  # 빈 청크 제외
                chunks.append(chunk)
        
        return chunks
    
    def _simple_char_chunking(self, text: str, page_number: int) -> List[ProcessedChunk]:
        """tiktoken이 없을 때 사용하는 간단한 문자 기반 청킹"""
        chunks: List[ProcessedChunk] = []
        char_chunk_size = self.chunk_size * 4  # 토큰 1개당 약 4문자 가정
        char_overlap = self.chunk_overlap * 4
        
        start = 0
        while start < len(text):
            end = start + char_chunk_size
            chunk_text = text[start:end]
            
            metadata: ChunkMetadata = {
                "chunk_index": len(chunks),
                "page_number": page_number,
                "chunk_type": "text_char_based",
                "source": f"policy_page_{page_number}_char",
                "confidence": None
            }
            
            chunk: ProcessedChunk = {
                "text": chunk_text.strip(),
                "metadata": metadata,
                "embedding": None
            }
            
            if chunk["text"]:  # 빈 청크 제외
                chunks.append(chunk)
            
            start += (char_chunk_size - char_overlap)
        
        return chunks
    
    def get_text_extraction_quality_report(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """텍스트 추출 품질 보고서 생성"""
        try:
            extracted_texts = state.get("extracted_text", [])
            chunks = state.get("processed_chunks", [])
            stats = state.get("text_extraction_stats", {})
            
            if not extracted_texts:
                return {"error": "추출된 텍스트가 없습니다"}
            
            # 품질 메트릭 계산
            total_original_length = sum(len(t.get("original_text", "")) for t in extracted_texts)
            total_cleaned_length = sum(len(t.get("cleaned_text", "")) for t in extracted_texts)
            
            quality_report = {
                "extraction_method": "enhanced_pdfplumber_ocr",
                "pages_processed": len(extracted_texts),
                "total_chunks_generated": len(chunks),
                "text_statistics": {
                    "original_text_length": total_original_length,
                    "cleaned_text_length": total_cleaned_length,
                    "cleaning_efficiency": (total_cleaned_length / total_original_length) if total_original_length > 0 else 0,
                    "average_chunk_size": sum(len(c["text"]) for c in chunks) / len(chunks) if chunks else 0
                },
                "processing_features": {
                    "ocr_integration": bool(self.ocr_service),
                    "insurance_text_cleaning": bool(self.text_cleaner),
                    "korean_text_processing": bool(self.korean_processor),
                    "article_structure_detection": bool(self.text_cleaner)
                },
                "quality_indicators": {
                    "text_extraction_completeness": min(95.0, (total_cleaned_length / (stats.get("total_text_length", 1))) * 100),
                    "chunk_consistency": len([c for c in chunks if len(c["text"]) > 50]) / len(chunks) * 100 if chunks else 0,
                    "korean_text_ratio": self._calculate_korean_text_ratio(extracted_texts)
                }
            }
            
            return quality_report
            
        except Exception as e:
            return {"error": f"품질 보고서 생성 실패: {str(e)}"}
    
    def _calculate_korean_text_ratio(self, extracted_texts: List[Dict[str, Any]]) -> float:
        """한글 텍스트 비율 계산"""
        try:
            total_chars = 0
            korean_chars = 0
            
            for text_data in extracted_texts:
                text = text_data.get("cleaned_text", "")
                total_chars += len(text)
                korean_chars += len([c for c in text if '가' <= c <= '힣'])
            
            return (korean_chars / total_chars * 100) if total_chars > 0 else 0
            
        except Exception:
            return 0.0