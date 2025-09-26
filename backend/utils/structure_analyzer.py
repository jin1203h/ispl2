"""
문서 구조 분석 유틸리티
PDF에서 추출된 데이터를 기반으로 논리적 문서 구조를 분석하고 생성
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """콘텐츠 타입 분류"""
    TITLE = "title"
    HEADER = "header"
    SUBHEADER = "subheader"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    IMAGE = "image"
    QUOTE = "quote"
    CODE = "code"
    FOOTNOTE = "footnote"

class StructureLevel(Enum):
    """구조 계층 레벨"""
    DOCUMENT = 0
    CHAPTER = 1
    SECTION = 2
    SUBSECTION = 3
    PARAGRAPH = 4

@dataclass
class StructureElement:
    """문서 구조 요소"""
    content_type: ContentType
    level: int
    text: str
    page_number: int
    position: Dict[str, float]  # x, y, width, height
    metadata: Dict[str, Any]
    children: List['StructureElement']
    
    def __post_init__(self):
        if self.children is None:
            self.children = []

class DocumentStructureAnalyzer:
    """문서 구조 분석기"""
    
    def __init__(self):
        # 헤더 패턴 (한국어 및 영어)
        self.header_patterns = [
            # 번호가 있는 헤더 (1., 1-1, 1.1, 가., 나.)
            r'^(\d+\.?\s*|\d+[\-\.]\d+\.?\s*|[가-힣]\.?\s*)',
            # 조항 패턴 (제1조, 제1장, 제1절)
            r'^제\s*\d+\s*[조장절항]\s*',
            # 영어 헤더 패턴
            r'^(Chapter|Section|Article)\s*\d+',
            # 로마 숫자
            r'^[IVX]+\.\s*',
        ]
        
        # 리스트 아이템 패턴
        self.list_patterns = [
            r'^\s*[-*•]\s+',  # 불릿 포인트
            r'^\s*\d+\)\s+',  # 숫자 리스트 (1)
            r'^\s*[가-힣]\)\s+',  # 한글 리스트 (가)
            r'^\s*[a-zA-Z]\)\s+',  # 영문 리스트 (a)
        ]
        
        # 폰트 크기 기반 헤더 임계값
        self.font_size_thresholds = {
            "title": 16,
            "header": 14,
            "subheader": 12,
            "normal": 10
        }

    def analyze_document_structure(self, processed_chunks: List[Dict[str, Any]]) -> List[StructureElement]:
        """전체 문서 구조 분석"""
        logger.info("문서 구조 분석 시작")
        
        elements = []
        
        for chunk in processed_chunks:
            element = self._analyze_chunk_structure(chunk)
            if element:
                elements.append(element)
        
        # 계층 구조 정리
        structured_elements = self._build_hierarchy(elements)
        
        logger.info(f"문서 구조 분석 완료: {len(structured_elements)}개 최상위 요소")
        return structured_elements

    def _analyze_chunk_structure(self, chunk: Dict[str, Any]) -> Optional[StructureElement]:
        """개별 청크의 구조 분석"""
        text = chunk.get("text", "").strip()
        if not text:
            return None
            
        metadata = chunk.get("metadata", {})
        chunk_type = metadata.get("chunk_type", "text")
        page_number = metadata.get("page_number", 1)
        
        # 위치 정보 추출
        position = self._extract_position_info(metadata)
        
        # 콘텐츠 타입 및 레벨 결정
        content_type, level = self._determine_content_type_and_level(text, metadata, chunk_type)
        
        return StructureElement(
            content_type=content_type,
            level=level,
            text=text,
            page_number=page_number,
            position=position,
            metadata=metadata,
            children=[]
        )

    def _extract_position_info(self, metadata: Dict[str, Any]) -> Dict[str, float]:
        """메타데이터에서 위치 정보 추출"""
        bbox = metadata.get("bbox", [0, 0, 0, 0])
        if len(bbox) >= 4:
            return {
                "x": float(bbox[0]),
                "y": float(bbox[1]),
                "width": float(bbox[2] - bbox[0]),
                "height": float(bbox[3] - bbox[1])
            }
        return {"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}

    def _determine_content_type_and_level(self, text: str, metadata: Dict[str, Any], 
                                        chunk_type: str) -> Tuple[ContentType, int]:
        """텍스트와 메타데이터를 기반으로 콘텐츠 타입과 레벨 결정"""
        
        # 청크 타입별 기본 분류
        if chunk_type == "table":
            return ContentType.TABLE, StructureLevel.PARAGRAPH.value
        elif chunk_type == "image":
            return ContentType.IMAGE, StructureLevel.PARAGRAPH.value
            
        # 폰트 크기 기반 분석
        font_size = metadata.get("font_size", 10)
        
        # 헤더 패턴 검사
        for pattern in self.header_patterns:
            if re.match(pattern, text.strip()):
                if font_size >= self.font_size_thresholds["title"]:
                    return ContentType.TITLE, StructureLevel.CHAPTER.value
                elif font_size >= self.font_size_thresholds["header"]:
                    return ContentType.HEADER, StructureLevel.SECTION.value
                else:
                    return ContentType.SUBHEADER, StructureLevel.SUBSECTION.value
        
        # 리스트 아이템 검사
        for pattern in self.list_patterns:
            if re.match(pattern, text.strip()):
                return ContentType.LIST_ITEM, StructureLevel.PARAGRAPH.value
        
        # 기타 특수 패턴
        if self._is_quote_text(text):
            return ContentType.QUOTE, StructureLevel.PARAGRAPH.value
        elif self._is_code_text(text):
            return ContentType.CODE, StructureLevel.PARAGRAPH.value
        elif self._is_footnote_text(text):
            return ContentType.FOOTNOTE, StructureLevel.PARAGRAPH.value
        
        # 기본값: 일반 문단
        return ContentType.PARAGRAPH, StructureLevel.PARAGRAPH.value

    def _is_quote_text(self, text: str) -> bool:
        """인용문 텍스트 판별"""
        quote_indicators = ['"', "'", '"', '"', '「', '」', '『', '』']
        text_stripped = text.strip()
        
        # 양쪽 끝에 인용 부호가 있는지 확인
        for indicator in quote_indicators:
            if text_stripped.startswith(indicator) and text_stripped.endswith(indicator):
                return True
        
        # 인용문을 나타내는 접두사
        quote_prefixes = ['인용:', 'Quote:', '출처:', 'Source:']
        for prefix in quote_prefixes:
            if text_stripped.lower().startswith(prefix.lower()):
                return True
                
        return False

    def _is_code_text(self, text: str) -> bool:
        """코드 텍스트 판별"""
        code_indicators = [
            # 프로그래밍 키워드
            'function', 'class', 'def ', 'var ', 'let ', 'const ',
            'import ', 'from ', 'public ', 'private ', 'protected ',
            # 특수 문자가 많은 경우
        ]
        
        text_lower = text.lower()
        
        # 코드 키워드 검사
        for indicator in code_indicators:
            if indicator in text_lower:
                return True
        
        # 특수 문자 비율 검사 (간단한 휴리스틱)
        special_chars = sum(1 for c in text if c in '{}[];(){}=<>+-*/%&|!@#$%^')
        if len(text) > 20 and special_chars / len(text) > 0.2:
            return True
            
        return False

    def _is_footnote_text(self, text: str) -> bool:
        """각주 텍스트 판별"""
        footnote_patterns = [
            r'^\*+\s',  # * 표시
            r'^\d+\)\s',  # 숫자)
            r'^주\s*\d+\)',  # 주1)
            r'^註\s*\d+\)',  # 註1)
            r'^\[\d+\]',  # [1]
        ]
        
        for pattern in footnote_patterns:
            if re.match(pattern, text.strip()):
                return True
                
        return False

    def _build_hierarchy(self, elements: List[StructureElement]) -> List[StructureElement]:
        """평면적인 요소들을 계층 구조로 변환"""
        if not elements:
            return []
        
        hierarchy = []
        stack = []  # 현재 계층 구조를 추적하기 위한 스택
        
        for element in elements:
            # 현재 요소보다 레벨이 높거나 같은 요소들을 스택에서 제거
            while stack and stack[-1].level >= element.level:
                stack.pop()
            
            if stack:
                # 부모 요소의 자식으로 추가
                stack[-1].children.append(element)
            else:
                # 최상위 요소로 추가
                hierarchy.append(element)
            
            # 현재 요소를 스택에 추가 (자식 요소들의 부모가 될 수 있음)
            if element.content_type in [ContentType.TITLE, ContentType.HEADER, ContentType.SUBHEADER]:
                stack.append(element)
        
        return hierarchy

    def get_table_of_contents(self, structure: List[StructureElement]) -> List[Dict[str, Any]]:
        """목차 생성"""
        toc = []
        
        def extract_headers(elements: List[StructureElement], depth: int = 0):
            for element in elements:
                if element.content_type in [ContentType.TITLE, ContentType.HEADER, ContentType.SUBHEADER]:
                    toc.append({
                        "title": element.text,
                        "level": element.level,
                        "depth": depth,
                        "page": element.page_number,
                        "content_type": element.content_type.value
                    })
                
                # 재귀적으로 자식 요소들 처리
                if element.children:
                    extract_headers(element.children, depth + 1)
        
        extract_headers(structure)
        return toc

    def analyze_document_statistics(self, structure: List[StructureElement]) -> Dict[str, Any]:
        """문서 통계 분석"""
        stats = {
            "total_elements": 0,
            "content_types": {},
            "structure_levels": {},
            "pages": set(),
            "average_text_length": 0,
            "total_text_length": 0
        }
        
        def count_elements(elements: List[StructureElement]):
            for element in elements:
                stats["total_elements"] += 1
                
                # 콘텐츠 타입별 카운트
                content_type = element.content_type.value
                stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1
                
                # 레벨별 카운트
                level = element.level
                stats["structure_levels"][level] = stats["structure_levels"].get(level, 0) + 1
                
                # 페이지 수집
                stats["pages"].add(element.page_number)
                
                # 텍스트 길이
                stats["total_text_length"] += len(element.text)
                
                # 재귀적으로 자식 요소들 처리
                if element.children:
                    count_elements(element.children)
        
        count_elements(structure)
        
        # 평균 계산
        if stats["total_elements"] > 0:
            stats["average_text_length"] = stats["total_text_length"] / stats["total_elements"]
        
        stats["total_pages"] = len(stats["pages"])
        stats["pages"] = sorted(list(stats["pages"]))
        
        return stats

