"""
고급 PDF 구조 분석 서비스
PyMuPDF 기반 상세 품질 분석, 표/이미지 영역 탐지, 스캔 품질 평가
"""
import os
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("⚠️ PyMuPDF가 설치되지 않았습니다.")
    PYMUPDF_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    print("⚠️ OpenCV가 설치되지 않았습니다. 이미지 분석이 제한됩니다.")
    OPENCV_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFQualityAnalyzer:
    """PDF 품질 및 구조 분석기"""
    
    def __init__(self):
        self.min_text_ratio = 0.1  # 텍스트 비율 임계값
        self.min_image_size = 1000  # 최소 이미지 크기 (바이트)
        self.scan_quality_threshold = 0.7  # 스캔 품질 임계값
    
    def analyze_document_structure(self, file_path: str) -> Dict[str, Any]:
        """PDF 문서의 전체 구조를 분석"""
        if not PYMUPDF_AVAILABLE:
            return {"error": "PyMuPDF가 설치되지 않음"}
        
        try:
            doc = fitz.open(file_path)
            
            analysis_result = {}
            
            # 각 단계별로 try-catch 적용
            try:
                analysis_result["file_info"] = self._get_file_info(file_path, doc)
            except Exception as e:
                logger.error(f"파일 정보 분석 실패: {str(e)}")
                analysis_result["file_info"] = {"error": str(e)}
            
            try:
                analysis_result["document_type"] = self._classify_document_type(doc)
            except Exception as e:
                logger.error(f"문서 타입 분류 실패: {str(e)}")
                analysis_result["document_type"] = {"error": str(e)}
            
            try:
                analysis_result["pages_analysis"] = self._analyze_pages(doc)
            except Exception as e:
                logger.error(f"페이지 분석 실패: {str(e)}")
                analysis_result["pages_analysis"] = []
            
            try:
                analysis_result["table_regions"] = self._detect_table_regions(doc)
            except Exception as e:
                logger.error(f"표 영역 탐지 실패: {str(e)}")
                analysis_result["table_regions"] = []
            
            try:
                analysis_result["image_analysis"] = self._analyze_images(doc)
            except Exception as e:
                logger.error(f"이미지 분석 실패: {str(e)}")
                analysis_result["image_analysis"] = {}
            
            try:
                analysis_result["scan_quality"] = self._evaluate_scan_quality(doc)
            except Exception as e:
                logger.error(f"스캔 품질 평가 실패: {str(e)}")
                analysis_result["scan_quality"] = {}
            
            # 처리 전략 결정
            try:
                analysis_result["processing_strategy"] = self._determine_processing_strategy(analysis_result)
            except Exception as e:
                logger.error(f"처리 전략 결정 실패: {str(e)}")
                analysis_result["processing_strategy"] = {}
            
            doc.close()
            return analysis_result
            
        except Exception as e:
            logger.error(f"PDF 구조 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    def _get_file_info(self, file_path: str, doc: fitz.Document) -> Dict[str, Any]:
        """기본 파일 정보 수집"""
        file_size = os.path.getsize(file_path)
        
        return {
            "filename": os.path.basename(file_path),
            "file_size": file_size,
            "page_count": doc.page_count,
            "encrypted": doc.is_encrypted,
            "needs_password": doc.needs_pass,
            "metadata": dict(doc.metadata),
            "size_category": self._categorize_file_size(file_size)
        }
    
    def _categorize_file_size(self, size: int) -> str:
        """파일 크기 분류"""
        if size < 1024 * 1024:  # 1MB 미만
            return "small"
        elif size < 10 * 1024 * 1024:  # 10MB 미만
            return "medium"
        elif size < 50 * 1024 * 1024:  # 50MB 미만
            return "large"
        else:
            return "very_large"
    
    def _classify_document_type(self, doc: fitz.Document) -> Dict[str, Any]:
        """문서 타입 분류 (텍스트/스캔/혼합)"""
        text_pages = 0
        scan_pages = 0
        mixed_pages = 0
        
        for page_num in range(min(10, doc.page_count)):  # 최대 10페이지 샘플링
            page = doc[page_num]
            text_content = page.get_text().strip()
            images = page.get_images()
            
            has_text = len(text_content) > 50
            has_large_images = any(
                self._get_image_size(doc, img) > self.min_image_size 
                for img in images
            )
            
            if has_text and not has_large_images:
                text_pages += 1
            elif has_large_images and not has_text:
                scan_pages += 1
            elif has_text and has_large_images:
                mixed_pages += 1
        
        total_sampled = text_pages + scan_pages + mixed_pages
        
        if total_sampled == 0:
            doc_type = "empty"
        elif text_pages / total_sampled > 0.8:
            doc_type = "text_based"
        elif scan_pages / total_sampled > 0.8:
            doc_type = "scan_based"
        else:
            doc_type = "mixed"
        
        return {
            "type": doc_type,
            "text_pages": text_pages,
            "scan_pages": scan_pages,
            "mixed_pages": mixed_pages,
            "confidence": max(text_pages, scan_pages, mixed_pages) / total_sampled if total_sampled > 0 else 0
        }
    
    def _analyze_pages(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """페이지별 상세 분석"""
        pages_analysis = []
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # 텍스트 분석
            text = page.get_text()
            text_blocks = page.get_text_blocks()
            
            # 이미지 분석
            images = page.get_images()
            
            # 그래픽 요소 분석
            drawings = page.get_drawings()
            
            page_analysis = {
                "page_number": page_num + 1,
                "dimensions": {
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation
                },
                "text_analysis": {
                    "char_count": len(text),
                    "text_blocks": len(text_blocks),
                    "has_meaningful_text": len(text.strip()) > 20,
                    "text_density": len(text) / (page.rect.width * page.rect.height) if page.rect.width * page.rect.height > 0 else 0
                },
                "image_analysis": {
                    "image_count": len(images),
                    "large_images": sum(1 for img in images if self._get_image_size(doc, img) > self.min_image_size),
                    "total_image_area": self._calculate_total_image_area(page, images)
                },
                "graphics_analysis": {
                    "drawing_count": len(drawings),
                    "has_complex_graphics": len(drawings) > 10
                }
            }
            
            # 페이지 타입 결정
            page_analysis["page_type"] = self._classify_page_type(page_analysis)
            
            pages_analysis.append(page_analysis)
        
        return pages_analysis
    
    def _detect_table_regions(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """표 영역 탐지"""
        table_regions = []
        
        for page_num in range(min(20, doc.page_count)):  # 최대 20페이지 분석
            page = doc[page_num]
            
            # 텍스트 블록 기반 표 영역 탐지
            text_blocks = page.get_text_blocks()
            
            # 정렬된 텍스트 블록으로 표 패턴 탐지
            potential_tables = self._find_table_patterns(text_blocks)
            
            # 그래픽 라인 기반 표 탐지
            drawings = page.get_drawings()
            line_based_tables = self._detect_line_based_tables(drawings, page.rect)
            
            for table in potential_tables + line_based_tables:
                table_info = {
                    "page_number": page_num + 1,
                    "bbox": table["bbox"],
                    "detection_method": table["method"],
                    "confidence": table["confidence"],
                    "estimated_rows": table.get("rows", 0),
                    "estimated_cols": table.get("cols", 0)
                }
                table_regions.append(table_info)
        
        return table_regions
    
    def _find_table_patterns(self, text_blocks: List) -> List[Dict[str, Any]]:
        """텍스트 블록 패턴으로 표 탐지"""
        tables = []
        
        if len(text_blocks) < 4:  # 최소 4개 블록 필요
            return tables
        
        # Y좌표 기준으로 그룹화
        rows = {}
        for block in text_blocks:
            try:
                # PyMuPDF text_blocks는 다양한 형태로 반환될 수 있음
                if len(block) >= 7:
                    x0, y0, x1, y1, text, block_type, block_no = block[:7]
                elif len(block) >= 5:
                    x0, y0, x1, y1, text = block[:5]
                    block_type, block_no = 0, 0
                else:
                    continue  # 형식이 맞지 않으면 건너뛰기
                
                y_key = round(y0 / 5) * 5  # 5포인트 단위로 그룹화
                
                if y_key not in rows:
                    rows[y_key] = []
                rows[y_key].append({
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "text": str(text).strip(), "width": x1 - x0
                })
            except (ValueError, TypeError) as e:
                # 튜플 언패킹 오류 시 건너뛰기
                continue
        
        # 테이블 후보 찾기
        sorted_rows = sorted(rows.keys())
        for i, y_key in enumerate(sorted_rows[:-2]):  # 최소 3행 필요
            row_group = []
            for j in range(i, min(i + 10, len(sorted_rows))):  # 최대 10행 확인
                current_row = rows[sorted_rows[j]]
                if len(current_row) >= 2:  # 최소 2열 필요
                    row_group.append(current_row)
                else:
                    break
            
            if len(row_group) >= 3:  # 최소 3행 이상
                # 표 영역 계산
                all_blocks = [block for row in row_group for block in row]
                min_x = min(block["x0"] for block in all_blocks)
                min_y = min(block["y0"] for block in all_blocks)
                max_x = max(block["x1"] for block in all_blocks)
                max_y = max(block["y1"] for block in all_blocks)
                
                tables.append({
                    "bbox": (min_x, min_y, max_x, max_y),
                    "method": "text_alignment",
                    "confidence": min(0.8, len(row_group) / 5),
                    "rows": len(row_group),
                    "cols": max(len(row) for row in row_group)
                })
        
        return tables
    
    def _detect_line_based_tables(self, drawings: List, page_rect: fitz.Rect) -> List[Dict[str, Any]]:
        """라인 기반 표 탐지"""
        tables = []
        
        if not drawings:
            return tables
        
        # 수평/수직 라인 추출
        horizontal_lines = []
        vertical_lines = []
        
        for drawing in drawings:
            for item in drawing.get("items", []):
                try:
                    if len(item) > 0 and item[0] == "l":  # 라인
                        # PyMuPDF drawing items는 다양한 형태로 반환될 수 있음
                        if len(item) >= 5:
                            x1, y1, x2, y2 = item[1:5]
                        elif len(item) >= 3:
                            # 간단한 형태의 라인 정보
                            x1, y1 = item[1:3]
                            x2, y2 = x1, y1  # 점으로 처리
                        else:
                            continue  # 형식이 맞지 않으면 건너뛰기
                        
                        # 수평선 (y좌표가 거의 같음)
                        if abs(y1 - y2) < 2:
                            horizontal_lines.append({"x1": min(x1, x2), "x2": max(x1, x2), "y": y1})
                        
                        # 수직선 (x좌표가 거의 같음)
                        elif abs(x1 - x2) < 2:
                            vertical_lines.append({"y1": min(y1, y2), "y2": max(y1, y2), "x": x1})
                except (ValueError, TypeError, IndexError):
                    # 튜플 언패킹 오류 시 건너뛰기
                    continue
        
        # 교차점 기반 표 영역 탐지
        if len(horizontal_lines) >= 2 and len(vertical_lines) >= 2:
            # 라인들이 격자를 형성하는지 확인
            for h_line in horizontal_lines:
                for v_line in vertical_lines:
                    # 교차 영역 확인
                    if (h_line["x1"] <= v_line["x"] <= h_line["x2"] and
                        v_line["y1"] <= h_line["y"] <= v_line["y2"]):
                        
                        # 표 영역 추정
                        intersecting_h = [h for h in horizontal_lines 
                                        if h["x1"] <= v_line["x"] <= h["x2"]]
                        intersecting_v = [v for v in vertical_lines 
                                        if v["y1"] <= h_line["y"] <= v["y2"]]
                        
                        if len(intersecting_h) >= 2 and len(intersecting_v) >= 2:
                            min_x = min(h["x1"] for h in intersecting_h)
                            max_x = max(h["x2"] for h in intersecting_h)
                            min_y = min(v["y1"] for v in intersecting_v)
                            max_y = max(v["y2"] for v in intersecting_v)
                            
                            tables.append({
                                "bbox": (min_x, min_y, max_x, max_y),
                                "method": "line_detection",
                                "confidence": 0.9,
                                "rows": len(intersecting_h) - 1,
                                "cols": len(intersecting_v) - 1
                            })
                            break
        
        return tables
    
    def _analyze_images(self, doc: fitz.Document) -> Dict[str, Any]:
        """이미지 상세 분석"""
        total_images = 0
        large_images = 0
        total_size = 0
        image_types = {}
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            images = page.get_images()
            
            for img_index, img in enumerate(images):
                total_images += 1
                img_size = self._get_image_size(doc, img)
                total_size += img_size
                
                if img_size > self.min_image_size:
                    large_images += 1
                
                # 이미지 타입 분석
                try:
                    img_data = doc.extract_image(img[0])
                    img_ext = img_data["ext"]
                    image_types[img_ext] = image_types.get(img_ext, 0) + 1
                except:
                    pass
        
        return {
            "total_images": total_images,
            "large_images": large_images,
            "total_size_bytes": total_size,
            "average_size_bytes": total_size / total_images if total_images > 0 else 0,
            "image_types": image_types,
            "large_image_ratio": large_images / total_images if total_images > 0 else 0
        }
    
    def _evaluate_scan_quality(self, doc: fitz.Document) -> Dict[str, Any]:
        """스캔 품질 평가"""
        if not OPENCV_AVAILABLE:
            return {"error": "OpenCV가 설치되지 않음"}
        
        quality_scores = []
        scan_indicators = {
            "has_large_images": False,
            "low_text_density": False,
            "irregular_text_layout": False
        }
        
        # 샘플 페이지 분석 (최대 5페이지)
        sample_pages = min(5, doc.page_count)
        
        for page_num in range(sample_pages):
            page = doc[page_num]
            
            # 텍스트 밀도 체크
            text = page.get_text()
            page_area = page.rect.width * page.rect.height
            text_density = len(text) / page_area if page_area > 0 else 0
            
            if text_density < 0.001:  # 매우 낮은 텍스트 밀도
                scan_indicators["low_text_density"] = True
            
            # 큰 이미지 존재 여부
            images = page.get_images()
            for img in images:
                if self._get_image_size(doc, img) > 100000:  # 100KB 이상
                    scan_indicators["has_large_images"] = True
                    break
            
            # 이미지 품질 분석 (가능한 경우)
            try:
                if images:
                    img = images[0]  # 첫 번째 이미지 분석
                    img_data = doc.extract_image(img[0])
                    img_bytes = img_data["image"]
                    
                    # OpenCV로 이미지 품질 분석
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    cv_image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                    
                    if cv_image is not None:
                        # 샤프니스 계산 (Laplacian variance)
                        laplacian_var = cv2.Laplacian(cv_image, cv2.CV_64F).var()
                        quality_scores.append(laplacian_var)
            except:
                pass
        
        # 전체 품질 점수 계산
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        
        # 스캔 여부 판단
        is_scan = (scan_indicators["has_large_images"] or 
                  scan_indicators["low_text_density"] or
                  avg_quality < 100)  # 낮은 이미지 품질
        
        return {
            "is_likely_scan": is_scan,
            "quality_score": float(avg_quality),
            "scan_indicators": scan_indicators,
            "quality_samples": len(quality_scores),
            "ocr_recommended": is_scan and avg_quality < 200
        }
    
    def _determine_processing_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과를 바탕으로 처리 전략 결정"""
        strategy = {
            "text_extraction": "pdfplumber",
            "ocr_required": False,
            "table_extraction": [],
            "image_processing": "basic",
            "optimization_level": "standard"
        }
        
        doc_type = analysis.get("document_type", {}).get("type", "unknown")
        scan_quality = analysis.get("scan_quality", {})
        table_regions = analysis.get("table_regions", [])
        image_analysis = analysis.get("image_analysis", {})
        
        # 텍스트 추출 전략
        if doc_type == "scan_based" or scan_quality.get("is_likely_scan", False):
            strategy["ocr_required"] = True
            strategy["text_extraction"] = "tesseract_ocr"
        
        # 표 추출 전략
        if table_regions:
            high_confidence_tables = [t for t in table_regions if t["confidence"] > 0.7]
            if high_confidence_tables:
                if any(t["detection_method"] == "line_detection" for t in high_confidence_tables):
                    strategy["table_extraction"].append("camelot_lattice")
                else:
                    strategy["table_extraction"].append("camelot_stream")
                strategy["table_extraction"].append("tabula")
        
        # 이미지 처리 전략
        if image_analysis.get("large_image_ratio", 0) > 0.5:
            strategy["image_processing"] = "advanced"
            if scan_quality.get("ocr_recommended", False):
                strategy["image_processing"] = "ocr_focused"
        
        # 최적화 레벨
        file_info = analysis.get("file_info", {})
        if file_info.get("size_category") in ["large", "very_large"]:
            strategy["optimization_level"] = "high"
        elif file_info.get("page_count", 0) > 100:
            strategy["optimization_level"] = "high"
        
        return strategy
    
    def _get_image_size(self, doc: fitz.Document, img: tuple) -> int:
        """이미지 크기 계산"""
        try:
            img_data = doc.extract_image(img[0])
            return len(img_data["image"])
        except:
            return 0
    
    def _calculate_total_image_area(self, page: fitz.Page, images: List) -> float:
        """페이지 내 이미지 총 면적 계산"""
        total_area = 0
        for img in images:
            try:
                img_rect = page.get_image_rects(img[0])
                if img_rect:
                    rect = img_rect[0]
                    total_area += rect.width * rect.height
            except:
                pass
        return total_area
    
    def _classify_page_type(self, page_analysis: Dict[str, Any]) -> str:
        """페이지 타입 분류"""
        text_density = page_analysis["text_analysis"]["text_density"]
        image_count = page_analysis["image_analysis"]["image_count"]
        has_text = page_analysis["text_analysis"]["has_meaningful_text"]
        
        if text_density > 0.001 and not image_count:
            return "text_only"
        elif image_count > 0 and not has_text:
            return "image_only"
        elif text_density > 0.001 and image_count > 0:
            return "mixed_content"
        else:
            return "minimal_content"
