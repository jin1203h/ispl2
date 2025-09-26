"""
고급 이미지 OCR 처리 에이전트
PyMuPDF, OpenCV, Tesseract를 활용한 향상된 이미지 분석 및 텍스트 추출
"""
import os
import time
import tempfile
import logging
from typing import List, Dict, Any, Optional
from .base import BaseAgent, DocumentProcessingState, ProcessingStatus, ProcessedChunk, create_chunk_metadata, create_processed_chunk
from services.advanced_image_service import AdvancedImageService, ImageQuality, ImageType

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF (이미지 추출용)
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("⚠️ PyMuPDF가 설치되지 않았습니다. 이미지 추출이 제한됩니다.")
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    import cv2
    import numpy as np
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    print("⚠️ OCR 라이브러리(pytesseract, opencv, PIL)가 설치되지 않았습니다. 이미지 텍스트 추출이 제한됩니다.")
    OCR_AVAILABLE = False

class ImageProcessorAgent(BaseAgent):
    """고급 이미지 OCR 처리 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="image_processor", 
            description="PDF 내 이미지에서 고급 분석과 OCR을 통해 텍스트를 추출하고 메타데이터를 보존합니다"
        )
        
        # 고급 이미지 서비스 초기화
        self.image_service = AdvancedImageService()
        
        # 처리 통계
        self.processing_stats = {
            "total_images": 0,
            "successful_ocr": 0,
            "high_quality_images": 0,
            "text_regions_found": 0
        }
    
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """고급 이미지 OCR 처리"""
        self.log_step(state, "고급 이미지 OCR 처리 시작")
        
        if not (PYMUPDF_AVAILABLE and OCR_AVAILABLE):
            self.log_step(state, "이미지 처리 라이브러리가 설치되지 않음, 건너뛰기", "warning")
            return self.update_status(state, ProcessingStatus.SKIPPED, "image_ocr")
        
        try:
            start_time = time.time()
            file_path = state["file_path"]
            
            # 1. 향상된 메타데이터와 함께 이미지 추출
            self.log_step(state, "이미지 메타데이터 추출 중...")
            image_metadata_list = self.image_service.extract_images_with_metadata(file_path)
            self.processing_stats["total_images"] = len(image_metadata_list)
            
            # 2. 각 이미지에 대해 종합적 분석 수행
            image_analysis_results = []
            successful_ocr_count = 0
            high_quality_count = 0
            total_text_regions = 0
            
            for metadata in image_metadata_list:
                self.log_step(state, f"이미지 분석 중: 페이지 {metadata.page_number}, 인덱스 {metadata.image_index}")
                
                # 종합적 이미지 분석
                analysis_result = self.image_service.analyze_image_comprehensive(metadata, file_path)
                image_analysis_results.append(analysis_result)
                
                # 통계 업데이트
                if analysis_result.ocr_text.strip():
                    successful_ocr_count += 1
                
                if analysis_result.quality in [ImageQuality.EXCELLENT, ImageQuality.GOOD]:
                    high_quality_count += 1
                
                total_text_regions += len(analysis_result.text_regions)
            
            # 3. 분석 결과를 청크로 변환
            image_chunks = self._convert_analysis_to_chunks(image_analysis_results)
            
            # 4. 상태 업데이트
            state["extracted_images"] = image_analysis_results
            state["image_processing_stats"] = {
                "total_images": len(image_metadata_list),
                "successful_ocr": successful_ocr_count,
                "high_quality_images": high_quality_count,
                "text_regions_found": total_text_regions,
                "ocr_success_rate": successful_ocr_count / len(image_metadata_list) if image_metadata_list else 0
            }
            
            # 기존 processed_chunks에 추가
            if "processed_chunks" not in state:
                state["processed_chunks"] = []
            state["processed_chunks"].extend(image_chunks)
            state["total_chunks"] = len(state["processed_chunks"])
            
            processing_time = time.time() - start_time
            
            self.log_step(
                state,
                f"고급 이미지 OCR 완료: {len(image_metadata_list)}개 이미지 분석, "
                f"{successful_ocr_count}개 OCR 성공, "
                f"{high_quality_count}개 고품질 이미지, "
                f"처리시간: {processing_time:.2f}초"
            )
            
            return self.update_status(state, ProcessingStatus.COMPLETED, "image_ocr")
            
        except Exception as e:
            error_msg = f"고급 이미지 OCR 중 오류 발생: {str(e)}"
            self.log_step(state, error_msg, "error")
            logger.error(error_msg, exc_info=True)
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "image_ocr",
                error_msg
            )
    
    def _convert_analysis_to_chunks(self, analysis_results: List) -> List[ProcessedChunk]:
        """이미지 분석 결과를 청크로 변환"""
        chunks = []
        
        for i, analysis in enumerate(analysis_results):
            try:
                if not analysis.ocr_text.strip():
                    continue  # OCR 텍스트가 없으면 건너뛰기
                
                # 청크 메타데이터 생성
                metadata = create_chunk_metadata(
                    chunk_index=len(chunks),
                    page_number=analysis.metadata.page_number,
                    chunk_type="image",
                    source=f"advanced_ocr_{analysis.processing_strategy}",
                    confidence=analysis.confidence
                )
                
                # 향상된 이미지 설명 생성
                image_description = self._create_enhanced_image_description(analysis)
                
                # 청크 생성
                chunk = create_processed_chunk(
                    text=image_description,
                    metadata=metadata
                )
                
                # 추가 메타데이터 저장
                chunk["image_analysis"] = {
                    "quality": analysis.quality.value,
                    "image_type": analysis.image_type.value,
                    "processing_strategy": analysis.processing_strategy,
                    "text_regions_count": len(analysis.text_regions),
                    "context_hints": analysis.context_hints,
                    "image_size": f"{analysis.metadata.width}x{analysis.metadata.height}",
                    "position": analysis.metadata.position
                }
                
                chunks.append(chunk)
                
            except Exception as e:
                logger.warning(f"이미지 {i} 청크 변환 실패: {e}")
        
        return chunks
    
    def _create_enhanced_image_description(self, analysis) -> str:
        """향상된 이미지 설명 생성"""
        metadata = analysis.metadata
        
        # 기본 이미지 정보
        description_parts = [
            f"[이미지 분석 결과]",
            f"페이지: {metadata.page_number}",
            f"위치: {metadata.position}",
            f"크기: {metadata.width}x{metadata.height} 픽셀",
            f"파일크기: {metadata.size_bytes:,} 바이트",
            f"이미지 타입: {analysis.image_type.value}",
            f"품질: {analysis.quality.value}",
            f"OCR 신뢰도: {analysis.confidence:.2f}"
        ]
        
        # 처리 전략 정보
        if analysis.processing_strategy != "general":
            description_parts.append(f"처리 전략: {analysis.processing_strategy}")
        
        # 텍스트 영역 정보
        if analysis.text_regions:
            description_parts.append(f"텍스트 영역: {len(analysis.text_regions)}개 발견")
        
        # 맥락 힌트
        if analysis.context_hints:
            description_parts.append(f"맥락: {', '.join(analysis.context_hints)}")
        
        # 구분선
        description_parts.append("=" * 50)
        
        # OCR 추출 텍스트
        description_parts.append("추출된 텍스트:")
        description_parts.append(analysis.ocr_text)
        
        return "\n".join(description_parts)
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """이미지 처리 통계 반환"""
        return {
            "agent_name": self.name,
            "processing_stats": self.processing_stats,
            "description": "고급 이미지 분석 및 OCR 처리 통계"
        }

