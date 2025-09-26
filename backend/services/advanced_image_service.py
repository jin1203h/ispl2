"""
고급 이미지 처리 및 OCR 서비스
PyMuPDF, OpenCV, Tesseract를 활용한 향상된 이미지 분석
"""
import os
import tempfile
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image, ImageEnhance
    
    # Tesseract 실행 파일 경로 설정 (Windows)
    if os.name == 'nt':  # Windows
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
            r"C:\Tesseract-OCR\tesseract.exe"
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ Tesseract 경로 설정됨: {path}")
                break
        else:
            print("⚠️ Tesseract 실행 파일을 찾을 수 없습니다.")
    
    REQUIRED_LIBS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"이미지 처리 라이브러리 누락: {e}")
    REQUIRED_LIBS_AVAILABLE = False

class ImageQuality(Enum):
    """이미지 품질 등급"""
    EXCELLENT = "excellent"  # 95% 이상
    GOOD = "good"           # 80-95%
    FAIR = "fair"           # 60-80%
    POOR = "poor"           # 60% 미만
    UNREADABLE = "unreadable"

class ImageType(Enum):
    """이미지 타입"""
    TEXT_DOCUMENT = "text_document"  # 텍스트 문서 스캔
    TABLE = "table"                  # 표 이미지
    CHART_GRAPH = "chart_graph"      # 차트/그래프
    LOGO_ICON = "logo_icon"         # 로고/아이콘
    PHOTO = "photo"                 # 사진
    MIXED = "mixed"                 # 혼합 타입
    UNKNOWN = "unknown"

@dataclass
class ImageMetadata:
    """이미지 메타데이터"""
    page_number: int
    image_index: int
    xref: int
    position: Tuple[float, float, float, float]  # x0, y0, x1, y1
    width: int
    height: int
    size_bytes: int
    extension: str
    dpi: Optional[float] = None
    color_space: Optional[str] = None
    is_mask: bool = False

@dataclass
class ImageAnalysisResult:
    """이미지 분석 결과"""
    metadata: ImageMetadata
    quality: ImageQuality
    image_type: ImageType
    ocr_text: str
    confidence: float
    processing_strategy: str
    text_regions: List[Dict[str, Any]]
    context_hints: List[str]

class AdvancedImageService:
    """고급 이미지 처리 서비스"""
    
    def __init__(self):
        self.ocr_config_kor_eng = '--oem 3 --psm 6 -l kor+eng'
        self.ocr_config_eng = '--oem 3 --psm 6 -l eng'
        self.ocr_config_table = '--oem 3 --psm 4 -l kor+eng'  # 표 전용
        
    def extract_images_with_metadata(self, pdf_path: str) -> List[ImageMetadata]:
        """PDF에서 향상된 메타데이터와 함께 이미지 추출"""
        if not REQUIRED_LIBS_AVAILABLE:
            logger.warning("필수 라이브러리가 설치되지 않아 이미지 추출을 건너뜁니다.")
            return []
            
        images = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    try:
                        metadata = self._extract_image_metadata(
                            pdf_document, page, img, page_num, img_index
                        )
                        
                        # 최소 크기 조건 확인 (아이콘 등 제외)
                        if (metadata.width >= 50 and metadata.height >= 50 
                            and metadata.size_bytes >= 2000):
                            images.append(metadata)
                            
                    except Exception as e:
                        logger.warning(f"페이지 {page_num + 1}, 이미지 {img_index} 메타데이터 추출 실패: {e}")
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"PDF 이미지 추출 실패: {e}")
        
        logger.info(f"총 {len(images)}개 이미지 추출 완료")
        return images
    
    def _extract_image_metadata(self, pdf_doc, page, img, page_num: int, img_index: int) -> ImageMetadata:
        """이미지 메타데이터 상세 추출"""
        xref = img[0]
        base_image = pdf_doc.extract_image(xref)
        
        # 이미지 위치 정보 추출
        img_dict = pdf_doc.xref_get_key(xref, "Type")
        
        # 페이지에서 이미지 위치 찾기
        position = self._find_image_position(page, xref)
        
        return ImageMetadata(
            page_number=page_num + 1,
            image_index=img_index,
            xref=xref,
            position=position,
            width=base_image.get("width", 0),
            height=base_image.get("height", 0),
            size_bytes=len(base_image["image"]),
            extension=base_image["ext"],
            color_space=base_image.get("colorspace"),
            is_mask=img[7] == 1  # smask field
        )
    
    def _find_image_position(self, page, xref: int) -> Tuple[float, float, float, float]:
        """페이지에서 이미지 위치 찾기"""
        try:
            # 페이지 내 이미지 블록 검색
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block.get("type") == 1:  # 이미지 블록
                    if block.get("number") == xref:
                        bbox = block.get("bbox", (0, 0, 0, 0))
                        return bbox
            
            return (0, 0, 0, 0)  # 위치를 찾을 수 없는 경우
            
        except Exception:
            return (0, 0, 0, 0)
    
    def analyze_image_comprehensive(self, metadata: ImageMetadata, pdf_path: str) -> ImageAnalysisResult:
        """종합적인 이미지 분석"""
        try:
            # PDF에서 이미지 데이터 추출
            image_data = self._get_image_data(pdf_path, metadata.xref)
            
            # 이미지 품질 평가
            quality = self._assess_image_quality(image_data, metadata)
            
            # 이미지 타입 분류
            image_type = self._classify_image_type(image_data, metadata)
            
            # 처리 전략 결정
            strategy = self._determine_processing_strategy(quality, image_type)
            
            # OCR 수행
            ocr_result = self._perform_advanced_ocr(image_data, strategy, image_type)
            
            # 텍스트 영역 분석
            text_regions = self._analyze_text_regions(image_data)
            
            # 맥락 힌트 생성
            context_hints = self._generate_context_hints(metadata, image_type, quality)
            
            return ImageAnalysisResult(
                metadata=metadata,
                quality=quality,
                image_type=image_type,
                ocr_text=ocr_result["text"],
                confidence=ocr_result["confidence"],
                processing_strategy=strategy,
                text_regions=text_regions,
                context_hints=context_hints
            )
            
        except Exception as e:
            logger.error(f"이미지 분석 실패: {e}")
            return ImageAnalysisResult(
                metadata=metadata,
                quality=ImageQuality.UNREADABLE,
                image_type=ImageType.UNKNOWN,
                ocr_text="",
                confidence=0.0,
                processing_strategy="failed",
                text_regions=[],
                context_hints=["분석 실패"]
            )
    
    def _get_image_data(self, pdf_path: str, xref: int) -> np.ndarray:
        """PDF에서 이미지 데이터 추출"""
        pdf_doc = fitz.open(pdf_path)
        base_image = pdf_doc.extract_image(xref)
        image_bytes = base_image["image"]
        pdf_doc.close()
        
        # PIL Image로 변환 후 OpenCV 배열로
        pil_image = Image.open(io.BytesIO(image_bytes))
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def _assess_image_quality(self, image: np.ndarray, metadata: ImageMetadata) -> ImageQuality:
        """이미지 품질 평가"""
        try:
            # 1. 해상도 기반 평가
            total_pixels = metadata.width * metadata.height
            
            # 2. 명확도 평가 (Laplacian variance)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 3. 대비 평가
            contrast = gray.std()
            
            # 4. 종합 점수 계산
            resolution_score = min(100, (total_pixels / 10000) * 20)  # 해상도
            sharpness_score = min(100, laplacian_var / 10)             # 선명도
            contrast_score = min(100, contrast / 2)                    # 대비
            
            total_score = (resolution_score + sharpness_score + contrast_score) / 3
            
            if total_score >= 85:
                return ImageQuality.EXCELLENT
            elif total_score >= 70:
                return ImageQuality.GOOD
            elif total_score >= 50:
                return ImageQuality.FAIR
            elif total_score >= 25:
                return ImageQuality.POOR
            else:
                return ImageQuality.UNREADABLE
                
        except Exception as e:
            logger.warning(f"이미지 품질 평가 실패: {e}")
            return ImageQuality.FAIR
    
    def _classify_image_type(self, image: np.ndarray, metadata: ImageMetadata) -> ImageType:
        """이미지 타입 분류"""
        try:
            height, width = image.shape[:2]
            aspect_ratio = width / height
            
            # 1. 크기 기반 분류
            if width < 100 or height < 100:
                return ImageType.LOGO_ICON
            
            # 2. 종횡비 기반 분류
            if aspect_ratio > 3 or aspect_ratio < 0.3:
                return ImageType.CHART_GRAPH
            
            # 3. 색상 분포 분석
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            unique_colors = len(np.unique(gray))
            
            if unique_colors < 10:  # 흑백 이진 이미지
                return ImageType.TEXT_DOCUMENT
            elif unique_colors < 50:  # 제한된 색상
                return ImageType.TABLE
            else:
                return ImageType.MIXED
                
        except Exception:
            return ImageType.UNKNOWN
    
    def _determine_processing_strategy(self, quality: ImageQuality, image_type: ImageType) -> str:
        """처리 전략 결정"""
        if quality == ImageQuality.UNREADABLE:
            return "skip"
        
        if image_type == ImageType.LOGO_ICON:
            return "minimal"
        elif image_type == ImageType.TEXT_DOCUMENT:
            return "text_optimized"
        elif image_type == ImageType.TABLE:
            return "table_optimized"
        elif image_type == ImageType.CHART_GRAPH:
            return "chart_optimized"
        else:
            return "general"
    
    def _perform_advanced_ocr(self, image: np.ndarray, strategy: str, image_type: ImageType) -> Dict[str, Any]:
        """고급 OCR 수행"""
        if strategy == "skip":
            return {"text": "", "confidence": 0.0}
        
        # OCR 라이브러리 사용 가능 여부 확인
        if not REQUIRED_LIBS_AVAILABLE:
            logger.warning("OCR 라이브러리가 설치되지 않음, 메타데이터만 추출")
            return {"text": "[OCR 라이브러리 없음 - 메타데이터만 추출됨]", "confidence": 0.0}
        
        try:
            import pytesseract
            
            # 전략별 전처리
            processed_image = self._preprocess_by_strategy(image, strategy)
            
            # 타입별 OCR 설정
            config = self._get_ocr_config(image_type)
            
            # OCR 수행
            ocr_text = pytesseract.image_to_string(processed_image, config=config)
            
            # 신뢰도 계산
            confidence = self._calculate_ocr_confidence(ocr_text, processed_image)
            
            # 텍스트 정제
            cleaned_text = self._clean_ocr_text_advanced(ocr_text)
            
            return {
                "text": cleaned_text,
                "confidence": confidence
            }
            
        except ImportError:
            logger.warning("pytesseract 모듈을 찾을 수 없음")
            return {"text": "[pytesseract 설치 필요]", "confidence": 0.0}
        except Exception as e:
            if "tesseract" in str(e).lower():
                logger.warning(f"Tesseract OCR 설치 필요: {e}")
                return {"text": "[Tesseract OCR 설치 필요 - install_tesseract_guide.md 참조]", "confidence": 0.0}
            else:
                logger.warning(f"OCR 수행 실패: {e}")
                return {"text": "", "confidence": 0.0}
    
    def _preprocess_by_strategy(self, image: np.ndarray, strategy: str) -> np.ndarray:
        """전략별 이미지 전처리"""
        if strategy == "minimal":
            return image
        
        # 기본 전처리
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        if strategy == "text_optimized":
            # 텍스트 최적화: 고대비, 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(gray)
            enhanced = cv2.convertScaleAbs(denoised, alpha=1.2, beta=10)
            binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            return binary
            
        elif strategy == "table_optimized":
            # 표 최적화: 선 강화, 구조 보존
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 10)
            kernel = np.ones((1,3), np.uint8)
            enhanced = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            return enhanced
            
        elif strategy == "chart_optimized":
            # 차트 최적화: 대비 향상
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            return enhanced
            
        else:  # general
            # 일반적 전처리
            denoised = cv2.fastNlMeansDenoising(gray)
            enhanced = cv2.convertScaleAbs(denoised, alpha=1.1, beta=5)
            return enhanced
    
    def _get_ocr_config(self, image_type: ImageType) -> str:
        """이미지 타입별 OCR 설정"""
        if image_type == ImageType.TABLE:
            return self.ocr_config_table
        elif image_type == ImageType.CHART_GRAPH:
            return self.ocr_config_eng  # 차트는 주로 영어
        else:
            return self.ocr_config_kor_eng
    
    def _calculate_ocr_confidence(self, text: str, image: np.ndarray) -> float:
        """OCR 신뢰도 계산"""
        if not text.strip():
            return 0.0
        
        try:
            # 1. 텍스트 길이 기반 점수
            length_score = min(1.0, len(text.strip()) / 50)
            
            # 2. 문자 종류 다양성 점수
            import re
            korean_chars = len(re.findall(r'[가-힣]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            digit_chars = len(re.findall(r'[0-9]', text))
            
            variety_score = min(1.0, (korean_chars + english_chars + digit_chars) / len(text))
            
            # 3. 이미지 품질 점수
            quality_score = min(1.0, cv2.Laplacian(image, cv2.CV_64F).var() / 100)
            
            return (length_score + variety_score + quality_score) / 3
            
        except Exception:
            return 0.5
    
    def _analyze_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """텍스트 영역 분석"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # MSER를 사용한 텍스트 영역 검출
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            
            text_regions = []
            for i, region in enumerate(regions):
                if len(region) > 10:  # 최소 크기
                    x, y, w, h = cv2.boundingRect(region)
                    area = w * h
                    
                    if area > 100:  # 유의미한 크기
                        text_regions.append({
                            "region_id": i,
                            "bbox": (x, y, w, h),
                            "area": area,
                            "aspect_ratio": w / h
                        })
            
            return text_regions[:10]  # 최대 10개 영역
            
        except Exception as e:
            logger.warning(f"텍스트 영역 분석 실패: {e}")
            return []
    
    def _generate_context_hints(self, metadata: ImageMetadata, image_type: ImageType, quality: ImageQuality) -> List[str]:
        """맥락 힌트 생성"""
        hints = []
        
        # 페이지 위치 기반 힌트
        x0, y0, x1, y1 = metadata.position
        page_width = x1 - x0 if x1 > x0 else metadata.width
        page_height = y1 - y0 if y1 > y0 else metadata.height
        
        if y0 < page_height * 0.3:
            hints.append("페이지 상단 이미지")
        elif y0 > page_height * 0.7:
            hints.append("페이지 하단 이미지")
        else:
            hints.append("페이지 중앙 이미지")
        
        # 크기 기반 힌트
        if metadata.width * metadata.height > 100000:
            hints.append("대형 이미지")
        elif metadata.width * metadata.height < 10000:
            hints.append("소형 이미지")
        
        # 타입 기반 힌트
        if image_type == ImageType.TABLE:
            hints.append("표 형태의 데이터")
        elif image_type == ImageType.TEXT_DOCUMENT:
            hints.append("문서 텍스트")
        elif image_type == ImageType.CHART_GRAPH:
            hints.append("차트/그래프")
        
        # 품질 기반 힌트
        if quality == ImageQuality.POOR:
            hints.append("낮은 해상도, OCR 정확도 제한적")
        elif quality == ImageQuality.EXCELLENT:
            hints.append("고품질, 높은 OCR 정확도 기대")
        
        return hints
    
    def _clean_ocr_text_advanced(self, text: str) -> str:
        """고급 OCR 텍스트 정제"""
        if not text:
            return ""
        
        import re
        
        # 1. 기본 정제
        text = re.sub(r'\s+', ' ', text)  # 연속 공백 제거
        text = text.strip()
        
        # 2. 의미 없는 결과 필터링
        if len(text) < 5:
            return ""
        
        # 3. 특수문자만 있는 라인 제거
        lines = text.split('\n')
        meaningful_lines = []
        
        for line in lines:
            line = line.strip()
            # 한글, 영문, 숫자가 포함된 의미있는 라인만 유지
            if re.search(r'[가-힣a-zA-Z0-9]', line) and len(line) >= 2:
                meaningful_lines.append(line)
        
        # 4. 보험 약관 특화 정제
        result = '\n'.join(meaningful_lines)
        
        # 일반적인 OCR 오류 수정
        corrections = {
            '0': 'O',  # 숫자 0을 문자 O로 (맥락에 따라)
            '1': 'I',  # 숫자 1을 문자 I로 (맥락에 따라)
            '조건': '조건',
            '약관': '약관'
        }
        
        # 너무 짧은 결과는 제외
        if len(result.strip()) < 10:
            return ""
        
        return result

# 필요한 import 추가
try:
    import io
except ImportError:
    pass
