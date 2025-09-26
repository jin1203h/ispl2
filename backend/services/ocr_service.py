"""
OCR 처리 전용 서비스
Tesseract OCR을 활용한 이미지 텍스트 인식 및 전처리
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    TESSERACT_AVAILABLE = True
except ImportError:
    print("⚠️ pytesseract 또는 Pillow가 설치되지 않았습니다. OCR 기능이 제한됩니다.")
    TESSERACT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    print("⚠️ OpenCV가 설치되지 않았습니다. 고급 이미지 전처리가 제한됩니다.")
    OPENCV_AVAILABLE = False

logger = logging.getLogger(__name__)

class OCRService:
    """OCR 처리 서비스"""
    
    def __init__(self):
        self.tesseract_config = {
            # 한글 + 영문 언어 설정
            'lang': 'kor+eng',
            # PSM (Page Segmentation Mode) 설정
            'psm': 6,  # 단일 균일한 텍스트 블록
            # OEM (OCR Engine Mode) 설정  
            'oem': 3,  # Default, LSTM + Legacy 결합
            # 추가 설정
            'config': '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz가-힣ㄱ-ㅎㅏ-ㅣ.,()[]{}+-=*/%<>:;!?@#$%^&_|\\"\' '
        }
    
    def enhance_image_for_ocr(self, image_path: str) -> str:
        """OCR을 위한 이미지 품질 향상"""
        if not TESSERACT_AVAILABLE:
            return image_path
        
        try:
            # PIL로 이미지 로드
            image = Image.open(image_path)
            
            # 그레이스케일 변환
            if image.mode != 'L':
                image = image.convert('L')
            
            # 이미지 크기 조정 (너무 작으면 확대)
            width, height = image.size
            if width < 300 or height < 300:
                scale_factor = max(300 / width, 300 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 대비 향상
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # 선명도 향상
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # 노이즈 제거 (약간의 블러)
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # 향상된 이미지 저장
            enhanced_path = image_path.replace('.', '_enhanced.')
            image.save(enhanced_path)
            
            logger.debug(f"이미지 품질 향상 완료: {enhanced_path}")
            return enhanced_path
            
        except Exception as e:
            logger.warning(f"이미지 품질 향상 실패: {e}")
            return image_path
    
    def advanced_image_preprocessing(self, image_path: str) -> str:
        """OpenCV를 활용한 고급 이미지 전처리"""
        if not OPENCV_AVAILABLE:
            return self.enhance_image_for_ocr(image_path)
        
        try:
            # OpenCV로 이미지 로드
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            # 가우시안 블러로 노이즈 제거
            image = cv2.GaussianBlur(image, (3, 3), 0)
            
            # 히스토그램 평활화
            image = cv2.equalizeHist(image)
            
            # 모폴로지 연산으로 텍스트 선명화
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
            
            # 이진화 (Otsu 방법)
            _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 전처리된 이미지 저장
            processed_path = image_path.replace('.', '_processed.')
            cv2.imwrite(processed_path, image)
            
            logger.debug(f"고급 이미지 전처리 완료: {processed_path}")
            return processed_path
            
        except Exception as e:
            logger.warning(f"고급 이미지 전처리 실패: {e}")
            return self.enhance_image_for_ocr(image_path)
    
    def extract_text_from_image(
        self, 
        image_path: str, 
        enhance_image: bool = True,
        use_advanced_preprocessing: bool = True
    ) -> Dict[str, Any]:
        """이미지에서 텍스트 추출"""
        if not TESSERACT_AVAILABLE:
            return {
                "text": "",
                "confidence": 0.0,
                "error": "Tesseract가 설치되지 않음"
            }
        
        try:
            # 이미지 전처리
            processed_image_path = image_path
            if use_advanced_preprocessing and OPENCV_AVAILABLE:
                processed_image_path = self.advanced_image_preprocessing(image_path)
            elif enhance_image:
                processed_image_path = self.enhance_image_for_ocr(image_path)
            
            # Tesseract 설정 구성
            config = f"--oem {self.tesseract_config['oem']} --psm {self.tesseract_config['psm']}"
            if self.tesseract_config.get('config'):
                config += f" {self.tesseract_config['config']}"
            
            # 텍스트 추출
            image = Image.open(processed_image_path)
            text = pytesseract.image_to_string(
                image, 
                lang=self.tesseract_config['lang'],
                config=config
            )
            
            # 상세 정보 추출 (신뢰도 포함)
            data = pytesseract.image_to_data(
                image,
                lang=self.tesseract_config['lang'],
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # 평균 신뢰도 계산
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # 임시 파일 정리
            if processed_image_path != image_path:
                try:
                    os.remove(processed_image_path)
                except:
                    pass
            
            result = {
                "text": text.strip(),
                "confidence": avg_confidence,
                "word_count": len(text.split()),
                "processing_method": "advanced" if use_advanced_preprocessing and OPENCV_AVAILABLE else "enhanced" if enhance_image else "basic"
            }
            
            logger.debug(f"OCR 처리 완료: 신뢰도 {avg_confidence:.1f}%, 단어 수 {result['word_count']}")
            return result
            
        except Exception as e:
            logger.error(f"OCR 텍스트 추출 실패: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def extract_text_with_coordinates(self, image_path: str) -> List[Dict[str, Any]]:
        """좌표 정보와 함께 텍스트 추출"""
        if not TESSERACT_AVAILABLE:
            return []
        
        try:
            # 이미지 전처리
            processed_image_path = self.advanced_image_preprocessing(image_path)
            
            # Tesseract 설정
            config = f"--oem {self.tesseract_config['oem']} --psm {self.tesseract_config['psm']}"
            
            # 상세 데이터 추출
            image = Image.open(processed_image_path)
            data = pytesseract.image_to_data(
                image,
                lang=self.tesseract_config['lang'],
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # 단어별 정보 구성
            words = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text and int(data['conf'][i]) > 30:  # 신뢰도 30% 이상만
                    word_info = {
                        "text": text,
                        "confidence": int(data['conf'][i]),
                        "bbox": {
                            "left": int(data['left'][i]),
                            "top": int(data['top'][i]),
                            "width": int(data['width'][i]),
                            "height": int(data['height'][i])
                        },
                        "page_num": int(data['page_num'][i]),
                        "block_num": int(data['block_num'][i]),
                        "par_num": int(data['par_num'][i]),
                        "line_num": int(data['line_num'][i]),
                        "word_num": int(data['word_num'][i])
                    }
                    words.append(word_info)
            
            # 임시 파일 정리
            if processed_image_path != image_path:
                try:
                    os.remove(processed_image_path)
                except:
                    pass
            
            logger.debug(f"좌표 포함 OCR 완료: {len(words)}개 단어 추출")
            return words
            
        except Exception as e:
            logger.error(f"좌표 포함 OCR 실패: {e}")
            return []
    
    def detect_text_orientation(self, image_path: str) -> Dict[str, Any]:
        """텍스트 방향 및 스크립트 탐지"""
        if not TESSERACT_AVAILABLE:
            return {"error": "Tesseract가 설치되지 않음"}
        
        try:
            image = Image.open(image_path)
            osd = pytesseract.image_to_osd(image, lang=self.tesseract_config['lang'])
            
            # OSD 결과 파싱
            osd_dict = {}
            for line in osd.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    osd_dict[key.strip()] = value.strip()
            
            result = {
                "orientation": osd_dict.get("Orientation in degrees", "0"),
                "script": osd_dict.get("Script", "Unknown"),
                "confidence": osd_dict.get("Orientation confidence", "0")
            }
            
            logger.debug(f"텍스트 방향 탐지: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"텍스트 방향 탐지 실패: {e}")
            return {"error": str(e)}
    
    def is_text_region_valid(self, image_path: str, min_confidence: float = 50.0) -> bool:
        """텍스트 영역이 OCR에 적합한지 판단"""
        if not TESSERACT_AVAILABLE:
            return False
        
        try:
            result = self.extract_text_from_image(image_path, enhance_image=False)
            
            # 기본 조건들
            has_text = len(result["text"].strip()) > 0
            good_confidence = result["confidence"] >= min_confidence
            sufficient_words = result.get("word_count", 0) >= 2
            
            return has_text and good_confidence and sufficient_words
            
        except Exception as e:
            logger.warning(f"텍스트 영역 유효성 검사 실패: {e}")
            return False
    
    def get_supported_languages(self) -> List[str]:
        """지원되는 언어 목록 반환"""
        if not TESSERACT_AVAILABLE:
            return []
        
        try:
            languages = pytesseract.get_languages()
            return languages
        except Exception as e:
            logger.warning(f"지원 언어 목록 조회 실패: {e}")
            return ['eng', 'kor']  # 기본값
    
    def get_tesseract_version(self) -> str:
        """Tesseract 버전 정보 반환"""
        if not TESSERACT_AVAILABLE:
            return "Not installed"
        
        try:
            version = pytesseract.get_tesseract_version()
            return str(version)
        except Exception as e:
            logger.warning(f"Tesseract 버전 조회 실패: {e}")
            return "Unknown"


