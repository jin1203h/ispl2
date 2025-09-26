"""
pdfplumber 기반 강화된 표 추출기 (Java 의존성 없음)
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    print("⚠️ pdfplumber가 설치되지 않았습니다.")
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFPlumberTableExtractor:
    """pdfplumber만 사용하는 고급 표 추출기"""
    
    def __init__(self):
        self.table_settings = {
            # 기본 설정
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines", 
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 3,
            "min_words_horizontal": 1,
            "intersection_tolerance": 3,
            "text_tolerance": 3
        }
    
    def extract_tables_from_pdf(self, file_path: str, pages: str = "all") -> List[Dict[str, Any]]:
        """PDF에서 표 추출"""
        if not PDFPLUMBER_AVAILABLE:
            return []
        
        tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                page_range = self._parse_page_range(pages, len(pdf.pages))
                
                for page_num in page_range:
                    page = pdf.pages[page_num - 1]  # 0-based index
                    page_tables = self._extract_tables_from_page(page, page_num)
                    tables.extend(page_tables)
            
            logger.info(f"pdfplumber로 {len(tables)}개 표 추출 완료")
            return tables
        
        except Exception as e:
            logger.error(f"pdfplumber 표 추출 실패: {e}")
            return []
    
    def _parse_page_range(self, pages: str, total_pages: int) -> List[int]:
        """페이지 범위 파싱"""
        if pages == "all":
            return list(range(1, total_pages + 1))
        
        # 간단한 페이지 파싱 (예: "1,2,3" 또는 "1-3")
        page_list = []
        for part in pages.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                page_list.extend(range(start, end + 1))
            else:
                page_list.append(int(part))
        
        return [p for p in page_list if 1 <= p <= total_pages]
    
    def _extract_tables_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """페이지에서 표 추출 (다중 전략)"""
        tables = []
        
        # 전략 1: 기본 라인 기반 추출
        tables.extend(self._extract_with_lines_strategy(page, page_num))
        
        # 전략 2: 텍스트 기반 추출 (라인이 없는 경우)
        if len(tables) == 0:
            tables.extend(self._extract_with_text_strategy(page, page_num))
        
        # 전략 3: 수동 영역 지정 (다른 방법이 실패한 경우)
        if len(tables) == 0:
            tables.extend(self._extract_with_manual_areas(page, page_num))
        
        return tables
    
    def _extract_with_lines_strategy(self, page, page_num: int) -> List[Dict[str, Any]]:
        """라인 기반 표 추출"""
        tables = []
        
        try:
            # 기본 설정으로 시도
            found_tables = page.find_tables(self.table_settings)
            
            for i, table in enumerate(found_tables):
                df = pd.DataFrame(table.extract())
                
                if len(df) > 1 and len(df.columns) > 1:
                    table_data = {
                        'table_id': f"pdfplumber_lines_{page_num}_{i}",
                        'page_number': page_num,
                        'extraction_method': "pdfplumber_lines",
                        'confidence': 85.0,  # pdfplumber는 일반적으로 높은 정확도
                        'dataframe': df,
                        'bbox': table.bbox,
                        'shape': df.shape,
                        'table_settings': self.table_settings.copy()
                    }
                    tables.append(table_data)
        
        except Exception as e:
            logger.debug(f"페이지 {page_num} 라인 기반 추출 실패: {e}")
        
        return tables
    
    def _extract_with_text_strategy(self, page, page_num: int) -> List[Dict[str, Any]]:
        """텍스트 기반 표 추출"""
        tables = []
        
        try:
            # 텍스트 기반 설정
            text_settings = self.table_settings.copy()
            text_settings.update({
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "text_tolerance": 5,
                "text_x_tolerance": 5,
                "text_y_tolerance": 5
            })
            
            found_tables = page.find_tables(text_settings)
            
            for i, table in enumerate(found_tables):
                df = pd.DataFrame(table.extract())
                
                if len(df) > 1 and len(df.columns) > 1:
                    table_data = {
                        'table_id': f"pdfplumber_text_{page_num}_{i}",
                        'page_number': page_num,
                        'extraction_method': "pdfplumber_text",
                        'confidence': 75.0,
                        'dataframe': df,
                        'bbox': table.bbox,
                        'shape': df.shape,
                        'table_settings': text_settings
                    }
                    tables.append(table_data)
        
        except Exception as e:
            logger.debug(f"페이지 {page_num} 텍스트 기반 추출 실패: {e}")
        
        return tables
    
    def _extract_with_manual_areas(self, page, page_num: int) -> List[Dict[str, Any]]:
        """수동 영역 지정 표 추출"""
        tables = []
        
        try:
            # 페이지를 여러 영역으로 나누어 표 탐지
            width = page.width
            height = page.height
            
            # 페이지를 상하좌우로 나누어 검색
            areas = [
                [0, 0, width, height/2],          # 상단
                [0, height/2, width, height],     # 하단
                [0, 0, width/2, height],          # 좌측  
                [width/2, 0, width, height],      # 우측
                [width*0.1, height*0.1, width*0.9, height*0.9]  # 중앙 여백 제외
            ]
            
            for i, area in enumerate(areas):
                try:
                    cropped_page = page.within_bbox(area)
                    area_tables = cropped_page.find_tables()
                    
                    for j, table in enumerate(area_tables):
                        df = pd.DataFrame(table.extract())
                        
                        if len(df) > 1 and len(df.columns) > 1:
                            table_data = {
                                'table_id': f"pdfplumber_area_{page_num}_{i}_{j}",
                                'page_number': page_num,
                                'extraction_method': f"pdfplumber_area_{i}",
                                'confidence': 70.0,
                                'dataframe': df,
                                'bbox': table.bbox,
                                'shape': df.shape,
                                'search_area': area
                            }
                            tables.append(table_data)
                
                except Exception as area_e:
                    logger.debug(f"페이지 {page_num} 영역 {i} 추출 실패: {area_e}")
        
        except Exception as e:
            logger.debug(f"페이지 {page_num} 수동 영역 추출 실패: {e}")
        
        return tables
    
    def debug_table_detection(self, file_path: str, page_num: int = 1) -> Dict[str, Any]:
        """표 탐지 디버깅 정보"""
        if not PDFPLUMBER_AVAILABLE:
            return {"error": "pdfplumber 사용 불가"}
        
        debug_info = {}
        
        try:
            with pdfplumber.open(file_path) as pdf:
                if page_num > len(pdf.pages):
                    return {"error": f"페이지 {page_num}이 존재하지 않음 (총 {len(pdf.pages)}페이지)"}
                
                page = pdf.pages[page_num - 1]
                
                # 페이지 기본 정보
                debug_info["page_info"] = {
                    "width": page.width,
                    "height": page.height,
                    "rotation": getattr(page, 'rotation', 0)
                }
                
                # 텍스트 정보
                chars = page.chars
                debug_info["text_info"] = {
                    "total_chars": len(chars),
                    "unique_fonts": len(set(c.get('fontname', 'unknown') for c in chars)),
                    "unique_sizes": len(set(c.get('size', 0) for c in chars))
                }
                
                # 라인 정보
                lines = page.lines
                debug_info["line_info"] = {
                    "total_lines": len(lines),
                    "horizontal_lines": len([l for l in lines if abs(l.get('top', 0) - l.get('bottom', 0)) < 2]),
                    "vertical_lines": len([l for l in lines if abs(l.get('x0', 0) - l.get('x1', 0)) < 2])
                }
                
                # 표 탐지 시도
                tables = page.find_tables()
                debug_info["table_detection"] = {
                    "tables_found": len(tables),
                    "table_details": [
                        {
                            "bbox": t.bbox,
                            "rows": len(t.extract()) if t.extract() else 0,
                            "cols": len(t.extract()[0]) if t.extract() and t.extract()[0] else 0
                        }
                        for t in tables
                    ]
                }
                
        except Exception as e:
            debug_info["error"] = str(e)
        
        return debug_info


