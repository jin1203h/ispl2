"""
PDF 분석 및 구조 파악 에이전트
PyMuPDF를 사용하여 PDF 메타데이터 및 고급 구조 분석
표/이미지 영역 탐지, 스캔 품질 평가, 처리 전략 결정 포함
"""
import os
import time
from typing import Dict, Any, Optional
from .base import BaseAgent, DocumentProcessingState, ProcessingStatus

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("⚠️ PyMuPDF가 설치되지 않았습니다. PDF 처리가 제한됩니다.")
    PYMUPDF_AVAILABLE = False

try:
    from services.pdf_analysis import PDFQualityAnalyzer
    PDF_ANALYZER_AVAILABLE = True
except ImportError:
    print("⚠️ PDF 품질 분석 서비스를 사용할 수 없습니다.")
    PDF_ANALYZER_AVAILABLE = False

class PDFProcessorAgent(BaseAgent):
    """PDF 문서 분석 에이전트 - 고급 구조 분석 포함"""
    
    def __init__(self):
        super().__init__(
            name="pdf_processor",
            description="PDF 문서의 메타데이터, 구조, 품질을 종합 분석합니다"
        )
        self.quality_analyzer = PDFQualityAnalyzer() if PDF_ANALYZER_AVAILABLE else None
    
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """PDF 파일 고급 분석 및 메타데이터 추출"""
        self.log_step(state, "PDF 고급 구조 분석 시작")
        
        if not PYMUPDF_AVAILABLE:
            return self.update_status(
                state, 
                ProcessingStatus.FAILED,
                "pdf_analysis",
                "PyMuPDF가 설치되지 않아 PDF 처리를 할 수 없습니다"
            )
        
        try:
            start_time = time.time()
            
            # 파일 존재 확인
            file_path = state["file_path"]
            if not os.path.exists(file_path):
                return self.update_status(
                    state,
                    ProcessingStatus.FAILED,
                    "pdf_analysis",
                    f"파일을 찾을 수 없습니다: {file_path}"
                )
            
            # 기본 PDF 분석
            basic_analysis = await self._perform_basic_analysis(file_path, state)
            if basic_analysis.get("error"):
                return self.update_status(
                    state,
                    ProcessingStatus.FAILED,
                    "pdf_analysis",
                    basic_analysis["error"]
                )
            
            # 고급 구조 분석 (품질 분석기 사용)
            advanced_analysis = {}
            if self.quality_analyzer:
                self.log_step(state, "고급 구조 분석 수행 중...")
                try:
                    advanced_analysis = self.quality_analyzer.analyze_document_structure(file_path)
                    if advanced_analysis.get("error"):
                        self.log_step(state, f"고급 분석 실패: {advanced_analysis['error']}", "warning")
                        advanced_analysis = {}
                except Exception as e:
                    self.log_step(state, f"고급 분석 중 오류: {str(e)}", "warning")
                    advanced_analysis = {}
            
            # 분석 결과 통합
            integrated_metadata = self._integrate_analysis_results(basic_analysis, advanced_analysis)
            
            # 상태 업데이트
            state["pdf_metadata"] = integrated_metadata
            state["total_pages"] = integrated_metadata["basic_info"]["total_pages"]
            state["processed_pages"] = 0
            
            # 고급 분석 결과 추가 저장
            if advanced_analysis:
                state["structure_analysis"] = advanced_analysis
                state["processing_strategy"] = advanced_analysis.get("processing_strategy", {})
            
            processing_time = time.time() - start_time
            state["processing_time"] = processing_time
            
            # 결과 로깅
            self._log_analysis_summary(state, integrated_metadata, processing_time)
            
            return self.update_status(state, ProcessingStatus.COMPLETED, "pdf_analysis")
            
        except Exception as e:
            error_msg = f"PDF 분석 중 오류 발생: {str(e)}"
            self.log_step(state, error_msg, "error")
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "pdf_analysis", 
                error_msg
            )
    
    async def _perform_basic_analysis(self, file_path: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """기본 PDF 분석 수행"""
        try:
            # PDF 파일 읽기
            with open(file_path, 'rb') as f:
                raw_content = f.read()
            
            state["raw_content"] = raw_content
            
            # PyMuPDF로 PDF 문서 열기
            pdf_document = fitz.open(file_path)
            
            # 메타데이터 추출
            basic_metadata = {
                "title": pdf_document.metadata.get("title", ""),
                "author": pdf_document.metadata.get("author", ""),
                "subject": pdf_document.metadata.get("subject", ""),
                "creator": pdf_document.metadata.get("creator", ""),
                "producer": pdf_document.metadata.get("producer", ""),
                "creation_date": pdf_document.metadata.get("creationDate", ""),
                "modification_date": pdf_document.metadata.get("modDate", ""),
                "total_pages": pdf_document.page_count,
                "file_size": len(raw_content),
                "encrypted": pdf_document.is_encrypted,
                "needs_pass": pdf_document.needs_pass
            }
            
            # 페이지별 구조 분석
            pages_info = []
            total_text_chars = 0
            total_images = 0
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                total_text_chars += len(page_text)
                page_images = page.get_images()
                total_images += len(page_images)
                
                page_info = {
                    "page_number": page_num + 1,
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation,
                    "has_text": bool(page_text.strip()),
                    "has_images": bool(page_images),
                    "has_drawings": bool(page.get_drawings()),
                    "text_blocks_count": len(page.get_text_blocks()),
                    "image_count": len(page_images),
                    "text_length": len(page_text)
                }
                pages_info.append(page_info)
            
            basic_metadata.update({
                "pages_info": pages_info,
                "total_text_chars": total_text_chars,
                "total_images": total_images,
                "avg_text_per_page": total_text_chars / pdf_document.page_count if pdf_document.page_count > 0 else 0
            })
            
            pdf_document.close()
            return basic_metadata
            
        except Exception as e:
            return {"error": f"기본 PDF 분석 실패: {str(e)}"}
    
    def _integrate_analysis_results(self, basic: Dict[str, Any], advanced: Dict[str, Any]) -> Dict[str, Any]:
        """기본 분석과 고급 분석 결과를 통합"""
        integrated = {
            "basic_info": basic,
            "analysis_timestamp": time.time(),
            "analysis_version": "3.1.0"
        }
        
        if advanced and not advanced.get("error"):
            integrated.update({
                "document_classification": advanced.get("document_type", {}),
                "quality_assessment": advanced.get("scan_quality", {}),
                "structure_elements": {
                    "table_regions": advanced.get("table_regions", []),
                    "image_analysis": advanced.get("image_analysis", {}),
                    "pages_analysis": advanced.get("pages_analysis", [])
                },
                "processing_recommendations": advanced.get("processing_strategy", {}),
                "advanced_analysis_available": True
            })
        else:
            integrated["advanced_analysis_available"] = False
            
            # 기본 분석으로부터 간단한 분류 수행
            integrated["document_classification"] = self._basic_document_classification(basic)
            integrated["processing_recommendations"] = self._basic_processing_strategy(basic)
        
        return integrated
    
    def _basic_document_classification(self, basic: Dict[str, Any]) -> Dict[str, Any]:
        """기본 분석 정보로 문서 분류"""
        pages_info = basic.get("pages_info", [])
        
        text_pages = sum(1 for p in pages_info if p.get("has_text", False))
        image_pages = sum(1 for p in pages_info if p.get("has_images", False))
        total_pages = len(pages_info)
        
        if total_pages == 0:
            doc_type = "empty"
        elif text_pages / total_pages > 0.8:
            doc_type = "text_based"
        elif image_pages / total_pages > 0.5:
            doc_type = "image_heavy"
        else:
            doc_type = "mixed"
        
        return {
            "type": doc_type,
            "confidence": 0.6,  # 기본 분석이므로 낮은 신뢰도
            "text_pages": text_pages,
            "image_pages": image_pages,
            "total_pages": total_pages
        }
    
    def _basic_processing_strategy(self, basic: Dict[str, Any]) -> Dict[str, Any]:
        """기본 분석 정보로 처리 전략 결정"""
        avg_text_per_page = basic.get("avg_text_per_page", 0)
        total_images = basic.get("total_images", 0)
        total_pages = basic.get("total_pages", 0)
        
        strategy = {
            "text_extraction": "pdfplumber",
            "ocr_required": avg_text_per_page < 100,  # 페이지당 평균 100자 미만이면 OCR 고려
            "table_extraction": ["camelot_stream"],  # 기본 전략
            "image_processing": "basic",
            "optimization_level": "standard"
        }
        
        # 이미지가 많으면 고급 이미지 처리
        if total_images > total_pages * 2:
            strategy["image_processing"] = "advanced"
        
        # 큰 문서면 최적화 레벨 상향
        if total_pages > 50:
            strategy["optimization_level"] = "high"
        
        return strategy
    
    def _log_analysis_summary(self, state: Dict[str, Any], metadata: Dict[str, Any], processing_time: float):
        """분석 결과 요약 로깅"""
        basic_info = metadata.get("basic_info", {})
        doc_classification = metadata.get("document_classification", {})
        
        summary_parts = [
            f"PDF 분석 완료: {basic_info.get('total_pages', 0)}페이지",
            f"크기: {basic_info.get('file_size', 0):,}바이트",
            f"문서타입: {doc_classification.get('type', 'unknown')}",
            f"처리시간: {processing_time:.2f}초"
        ]
        
        # 고급 분석 정보 추가
        if metadata.get("advanced_analysis_available", False):
            quality = metadata.get("quality_assessment", {})
            tables = metadata.get("structure_elements", {}).get("table_regions", [])
            
            summary_parts.extend([
                f"표 영역: {len(tables)}개",
                f"스캔 여부: {'예' if quality.get('is_likely_scan', False) else '아니오'}"
            ])
        
        self.log_step(state, " | ".join(summary_parts))
    
    def get_document_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """PDF 문서 기본 정보만 빠르게 조회"""
        if not PYMUPDF_AVAILABLE:
            return None
            
        try:
            doc = fitz.open(file_path)
            info = {
                "page_count": doc.page_count,
                "file_size": os.path.getsize(file_path),
                "title": doc.metadata.get("title", ""),
                "encrypted": doc.is_encrypted
            }
            doc.close()
            return info
        except Exception as e:
            print(f"PDF 정보 조회 실패: {e}")
            return None
