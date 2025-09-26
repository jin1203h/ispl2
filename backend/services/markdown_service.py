"""
Markdown 변환 전용 서비스
PDF에서 추출된 구조화된 데이터를 Markdown 형식으로 변환
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import yaml
import pandas as pd

from utils.structure_analyzer import (
    DocumentStructureAnalyzer, 
    StructureElement, 
    ContentType, 
    StructureLevel
)

logger = logging.getLogger(__name__)

class MarkdownConverter:
    """Markdown 변환기"""
    
    def __init__(self):
        self.structure_analyzer = DocumentStructureAnalyzer()
        
        # Markdown 헤더 레벨 매핑
        self.header_level_mapping = {
            StructureLevel.CHAPTER.value: 1,
            StructureLevel.SECTION.value: 2,
            StructureLevel.SUBSECTION.value: 3,
            StructureLevel.PARAGRAPH.value: 4
        }
        
        # 이미지 저장 디렉토리
        self.image_dir = "images"
        
        # 지원되는 이미지 확장자
        self.supported_image_formats = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}

    def convert_to_markdown(self, 
                          processed_chunks: List[Dict[str, Any]], 
                          document_metadata: Optional[Dict[str, Any]] = None,
                          include_toc: bool = True,
                          include_metadata: bool = True) -> str:
        """PDF 처리 결과를 Markdown으로 변환"""
        
        logger.info("Markdown 변환 시작")
        
        # 1. 문서 구조 분석
        structure = self.structure_analyzer.analyze_document_structure(processed_chunks)
        
        # 2. Markdown 문서 생성
        markdown_content = []
        
        # 3. 메타데이터 (YAML 프론트매터) 추가
        if include_metadata:
            frontmatter = self._generate_frontmatter(document_metadata, structure)
            markdown_content.append(frontmatter)
        
        # 4. 목차 생성
        if include_toc:
            toc = self._generate_table_of_contents(structure)
            if toc:
                markdown_content.append(toc)
        
        # 5. 본문 변환
        body = self._convert_structure_to_markdown(structure)
        markdown_content.append(body)
        
        # 6. 각주 및 참조 추가
        footnotes = self._extract_and_format_footnotes(structure)
        if footnotes:
            markdown_content.append(footnotes)
        
        final_markdown = "\n\n".join(markdown_content)
        
        logger.info(f"Markdown 변환 완료: {len(final_markdown)} 문자")
        return final_markdown

    def _generate_frontmatter(self, 
                            document_metadata: Optional[Dict[str, Any]], 
                            structure: List[StructureElement]) -> str:
        """YAML 프론트매터 생성"""
        
        # 문서 통계
        stats = self.structure_analyzer.analyze_document_statistics(structure)
        
        # 기본 메타데이터
        frontmatter_data = {
            "title": document_metadata.get("title", "Untitled Document") if document_metadata else "Untitled Document",
            "generated_at": datetime.now().isoformat(),
            "generator": "ISPL PDF Processor",
            "source_format": "PDF",
            "document_statistics": {
                "total_pages": stats.get("total_pages", 0),
                "total_elements": stats.get("total_elements", 0),
                "content_types": stats.get("content_types", {}),
                "average_text_length": round(stats.get("average_text_length", 0), 2)
            }
        }
        
        # 추가 메타데이터 병합
        if document_metadata:
            frontmatter_data.update({
                "author": document_metadata.get("author"),
                "subject": document_metadata.get("subject"),
                "keywords": document_metadata.get("keywords"),
                "creation_date": document_metadata.get("creation_date"),
                "modification_date": document_metadata.get("modification_date"),
                "file_size": document_metadata.get("file_size"),
                "language": document_metadata.get("language", "ko")
            })
        
        # None 값 제거
        frontmatter_data = {k: v for k, v in frontmatter_data.items() if v is not None}
        
        yaml_content = yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_content}---"

    def _generate_table_of_contents(self, structure: List[StructureElement]) -> str:
        """목차 생성"""
        toc_items = self.structure_analyzer.get_table_of_contents(structure)
        
        if not toc_items:
            return ""
        
        toc_lines = ["## 목차", ""]
        
        for item in toc_items:
            # 들여쓰기 계산
            indent = "  " * item["depth"]
            
            # 제목에서 특수 문자 제거하여 앵커 생성
            anchor = self._create_anchor(item["title"])
            
            # 목차 항목 생성
            toc_line = f"{indent}- [{item['title']}](#{anchor}) (페이지 {item['page']})"
            toc_lines.append(toc_line)
        
        return "\n".join(toc_lines)

    def _create_anchor(self, title: str) -> str:
        """제목에서 Markdown 앵커 생성"""
        # 한글, 영문, 숫자만 남기고 소문자로 변환
        anchor = re.sub(r'[^\w\s가-힣]', '', title)
        anchor = re.sub(r'\s+', '-', anchor.strip())
        anchor = anchor.lower()
        return anchor

    def _convert_structure_to_markdown(self, structure: List[StructureElement]) -> str:
        """구조화된 요소들을 Markdown으로 변환"""
        markdown_lines = []
        
        for element in structure:
            converted = self._convert_element_to_markdown(element)
            if converted:
                markdown_lines.append(converted)
        
        return "\n\n".join(markdown_lines)

    def _convert_element_to_markdown(self, element: StructureElement) -> str:
        """개별 요소를 Markdown으로 변환"""
        
        if element.content_type == ContentType.TITLE:
            markdown = f"# {element.text}"
            
        elif element.content_type == ContentType.HEADER:
            level = self.header_level_mapping.get(element.level, 2)
            markdown = f"{'#' * level} {element.text}"
            
        elif element.content_type == ContentType.SUBHEADER:
            level = self.header_level_mapping.get(element.level, 3)
            markdown = f"{'#' * level} {element.text}"
            
        elif element.content_type == ContentType.PARAGRAPH:
            markdown = element.text
            
        elif element.content_type == ContentType.LIST_ITEM:
            # 리스트 아이템 형식 정리
            clean_text = re.sub(r'^\s*[-*•]\s+', '', element.text)
            clean_text = re.sub(r'^\s*\d+\)\s+', '', clean_text)
            clean_text = re.sub(r'^\s*[가-힣a-zA-Z]\)\s+', '', clean_text)
            markdown = f"- {clean_text}"
            
        elif element.content_type == ContentType.TABLE:
            markdown = self._convert_table_to_markdown(element)
            
        elif element.content_type == ContentType.IMAGE:
            markdown = self._convert_image_to_markdown(element)
            
        elif element.content_type == ContentType.QUOTE:
            # 인용문 처리
            quote_text = element.text.strip('"\'「」『』""''')
            markdown = f"> {quote_text}"
            
        elif element.content_type == ContentType.CODE:
            markdown = f"```\n{element.text}\n```"
            
        elif element.content_type == ContentType.FOOTNOTE:
            # 각주는 별도로 처리하므로 여기서는 빈 문자열 반환
            return ""
            
        else:
            markdown = element.text
        
        # 자식 요소들 처리
        if element.children:
            child_content = []
            for child in element.children:
                child_markdown = self._convert_element_to_markdown(child)
                if child_markdown:
                    child_content.append(child_markdown)
            
            if child_content:
                markdown += "\n\n" + "\n\n".join(child_content)
        
        return markdown

    def _convert_table_to_markdown(self, element: StructureElement) -> str:
        """표 요소를 Markdown 표 형식으로 변환"""
        
        # 메타데이터에서 표 데이터 추출
        table_data = element.metadata.get("table_data")
        
        if not table_data:
            return f"*[표 데이터를 로드할 수 없습니다: 페이지 {element.page_number}]*"
        
        try:
            # pandas DataFrame인 경우
            if hasattr(table_data, 'to_markdown'):
                return table_data.to_markdown(index=False)
            
            # 리스트 형태인 경우
            elif isinstance(table_data, list) and table_data:
                return self._list_to_markdown_table(table_data)
            
            # 딕셔너리 형태인 경우
            elif isinstance(table_data, dict):
                # 딕셔너리를 DataFrame으로 변환 시도
                try:
                    df = pd.DataFrame(table_data)
                    return df.to_markdown(index=False)
                except:
                    # 변환 실패 시 키-값 쌍으로 표시
                    rows = [["항목", "값"]]
                    rows.extend([[str(k), str(v)] for k, v in table_data.items()])
                    return self._list_to_markdown_table(rows)
            
            else:
                return f"*[지원되지 않는 표 형식: 페이지 {element.page_number}]*"
                
        except Exception as e:
            logger.warning(f"표 변환 실패: {e}")
            return f"*[표 변환 오류: 페이지 {element.page_number}]*"

    def _list_to_markdown_table(self, table_data: List[List[str]]) -> str:
        """2차원 리스트를 Markdown 표로 변환"""
        if not table_data or not table_data[0]:
            return "*[빈 표]*"
        
        # 헤더 행
        header = table_data[0]
        markdown_lines = []
        
        # 헤더 라인
        header_line = "| " + " | ".join(str(cell) for cell in header) + " |"
        markdown_lines.append(header_line)
        
        # 구분자 라인
        separator_line = "| " + " | ".join("---" for _ in header) + " |"
        markdown_lines.append(separator_line)
        
        # 데이터 행들
        for row in table_data[1:]:
            # 행의 열 수를 헤더와 맞춤
            padded_row = (list(row) + [""] * len(header))[:len(header)]
            row_line = "| " + " | ".join(str(cell) for cell in padded_row) + " |"
            markdown_lines.append(row_line)
        
        return "\n".join(markdown_lines)

    def _convert_image_to_markdown(self, element: StructureElement) -> str:
        """이미지 요소를 Markdown 이미지 링크로 변환"""
        
        # 이미지 메타데이터 추출
        image_metadata = element.metadata.get("image_analysis", {})
        page_number = element.page_number
        image_index = element.metadata.get("image_index", 0)
        
        # 이미지 파일명 생성
        image_filename = f"page_{page_number}_image_{image_index}.png"
        image_path = f"{self.image_dir}/{image_filename}"
        
        # 이미지 설명 생성
        alt_text = self._generate_image_alt_text(element, image_metadata)
        
        # Markdown 이미지 링크 생성
        markdown = f"![{alt_text}]({image_path})"
        
        # 이미지 캡션 추가 (OCR 텍스트가 있는 경우)
        ocr_text = element.text.strip()
        if ocr_text and not ocr_text.startswith("["):
            caption = f"\n\n*{ocr_text}*"
            markdown += caption
        
        # 이미지 메타데이터 정보 추가 (디버그용)
        if image_metadata:
            quality = image_metadata.get("quality", "알 수 없음")
            image_type = image_metadata.get("image_type", "알 수 없음")
            confidence = image_metadata.get("confidence", 0)
            
            metadata_comment = f"\n<!-- 이미지 정보: 품질={quality}, 타입={image_type}, OCR 신뢰도={confidence:.2f} -->"
            markdown += metadata_comment
        
        return markdown

    def _generate_image_alt_text(self, element: StructureElement, image_metadata: Dict[str, Any]) -> str:
        """이미지 대체 텍스트 생성"""
        
        page_number = element.page_number
        image_type = image_metadata.get("image_type", "이미지")
        
        # OCR 텍스트가 있으면 간단한 설명 생성
        ocr_text = element.text.strip()
        if ocr_text and not ocr_text.startswith("["):
            # 첫 몇 단어만 사용
            words = ocr_text.split()[:5]
            preview = " ".join(words)
            if len(words) == 5:
                preview += "..."
            return f"페이지 {page_number} {image_type}: {preview}"
        
        return f"페이지 {page_number} {image_type}"

    def _extract_and_format_footnotes(self, structure: List[StructureElement]) -> str:
        """각주 추출 및 형식화"""
        footnotes = []
        
        def collect_footnotes(elements: List[StructureElement]):
            for element in elements:
                if element.content_type == ContentType.FOOTNOTE:
                    footnotes.append(element)
                if element.children:
                    collect_footnotes(element.children)
        
        collect_footnotes(structure)
        
        if not footnotes:
            return ""
        
        footnote_lines = ["## 각주", ""]
        
        for i, footnote in enumerate(footnotes, 1):
            footnote_text = footnote.text.strip()
            # 기존 각주 번호 제거
            footnote_text = re.sub(r'^\*+\s*', '', footnote_text)
            footnote_text = re.sub(r'^\d+\)\s*', '', footnote_text)
            footnote_text = re.sub(r'^주\s*\d+\)\s*', '', footnote_text)
            
            footnote_lines.append(f"[^{i}]: {footnote_text}")
        
        return "\n".join(footnote_lines)

    def save_markdown_to_file(self, 
                            markdown_content: str, 
                            output_path: str,
                            extract_images: bool = True,
                            processed_chunks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Markdown 내용을 파일로 저장"""
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Markdown 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        result = {
            "markdown_file": str(output_path),
            "file_size": output_path.stat().st_size,
            "extracted_images": []
        }
        
        # 이미지 파일 추출 및 저장
        if extract_images and processed_chunks:
            image_dir = output_path.parent / self.image_dir
            image_dir.mkdir(exist_ok=True)
            
            extracted_images = self._extract_and_save_images(processed_chunks, image_dir)
            result["extracted_images"] = extracted_images
        
        logger.info(f"Markdown 파일 저장 완료: {output_path}")
        return result

    def _extract_and_save_images(self, 
                                processed_chunks: List[Dict[str, Any]], 
                                image_dir: Path) -> List[Dict[str, Any]]:
        """처리된 청크에서 이미지 추출 및 저장"""
        extracted_images = []
        
        for chunk in processed_chunks:
            metadata = chunk.get("metadata", {})
            chunk_type = metadata.get("chunk_type", "")
            
            if chunk_type == "image":
                try:
                    page_number = metadata.get("page_number", 1)
                    image_index = metadata.get("image_index", 0)
                    
                    # 이미지 데이터 추출
                    image_data = metadata.get("image_data")
                    
                    # 더미 데이터인 경우 실제 이미지 생성
                    if not image_data or image_data == b"dummy_image_data":
                        image_data = self._create_placeholder_image(chunk.get("text", "샘플 이미지"))
                    
                    if not image_data:
                        logger.warning(f"페이지 {page_number} 이미지 {image_index}: 이미지 데이터 없음")
                        continue
                    
                    # 파일명 생성
                    image_filename = f"page_{page_number}_image_{image_index}.png"
                    image_path = image_dir / image_filename
                    
                    # 이미지 저장
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    extracted_images.append({
                        "filename": image_filename,
                        "path": str(image_path),
                        "page_number": page_number,
                        "image_index": image_index,
                        "size_bytes": len(image_data),
                        "is_placeholder": image_data == self._create_placeholder_image(chunk.get("text", "샘플 이미지"))
                    })
                    
                    logger.info(f"이미지 저장 완료: {image_filename} ({len(image_data)} bytes)")
                    
                except Exception as e:
                    logger.warning(f"이미지 저장 실패: {e}")
        
        logger.info(f"이미지 {len(extracted_images)}개 추출 완료")
        return extracted_images

    def _create_placeholder_image(self, text: str = "샘플 이미지") -> bytes:
        """플레이스홀더 이미지 생성"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # 이미지 크기
            width, height = 400, 200
            
            # 이미지 생성
            img = Image.new('RGB', (width, height), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # 텍스트 추가
            try:
                # 기본 폰트 사용
                font = ImageFont.load_default()
            except:
                font = None
            
            # 텍스트 위치 계산
            text_lines = [
                "📄 ISPL Insurance Policy",
                text[:30] + ("..." if len(text) > 30 else ""),
                "Sample Image Placeholder"
            ]
            
            y_offset = 50
            for line in text_lines:
                if font:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                else:
                    text_width, text_height = len(line) * 8, 12
                
                x = (width - text_width) // 2
                draw.text((x, y_offset), line, fill='black', font=font)
                y_offset += text_height + 10
            
            # 테두리 그리기
            draw.rectangle([5, 5, width-5, height-5], outline='gray', width=2)
            
            # PNG 바이트로 변환
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            return img_buffer.getvalue()
            
        except ImportError:
            logger.warning("PIL 라이브러리가 없어 플레이스홀더 이미지를 생성할 수 없습니다")
            # 최소한의 PNG 헤더 (빈 이미지)
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```\x04\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        except Exception as e:
            logger.error(f"플레이스홀더 이미지 생성 실패: {e}")
            return b""

    def generate_conversion_report(self, 
                                 structure: List[StructureElement],
                                 conversion_result: Dict[str, Any]) -> Dict[str, Any]:
        """변환 보고서 생성"""
        
        stats = self.structure_analyzer.analyze_document_statistics(structure)
        toc = self.structure_analyzer.get_table_of_contents(structure)
        
        report = {
            "conversion_timestamp": datetime.now().isoformat(),
            "document_statistics": stats,
            "table_of_contents": toc,
            "conversion_results": conversion_result,
            "quality_metrics": {
                "structure_preservation_rate": self._calculate_structure_preservation_rate(structure),
                "markdown_syntax_compliance": True,  # 기본적으로 준수
                "readability_score": self._calculate_readability_score(structure),
                "metadata_completeness": self._calculate_metadata_completeness(structure)
            }
        }
        
        return report

    def _calculate_structure_preservation_rate(self, structure: List[StructureElement]) -> float:
        """구조 보존율 계산"""
        total_elements = 0
        preserved_elements = 0
        
        def count_preserved(elements: List[StructureElement]):
            nonlocal total_elements, preserved_elements
            
            for element in elements:
                total_elements += 1
                
                # 구조 정보가 보존된 요소 카운트
                if (element.content_type != ContentType.PARAGRAPH and 
                    element.level > 0 and 
                    element.text.strip()):
                    preserved_elements += 1
                elif element.content_type == ContentType.PARAGRAPH and element.text.strip():
                    preserved_elements += 1
                
                if element.children:
                    count_preserved(element.children)
        
        count_preserved(structure)
        
        return (preserved_elements / total_elements * 100) if total_elements > 0 else 0

    def _calculate_readability_score(self, structure: List[StructureElement]) -> str:
        """가독성 점수 계산"""
        # 간단한 휴리스틱 기반 가독성 평가
        
        total_text_length = 0
        header_count = 0
        paragraph_count = 0
        
        def analyze_readability(elements: List[StructureElement]):
            nonlocal total_text_length, header_count, paragraph_count
            
            for element in elements:
                total_text_length += len(element.text)
                
                if element.content_type in [ContentType.TITLE, ContentType.HEADER, ContentType.SUBHEADER]:
                    header_count += 1
                elif element.content_type == ContentType.PARAGRAPH:
                    paragraph_count += 1
                
                if element.children:
                    analyze_readability(element.children)
        
        analyze_readability(structure)
        
        # 가독성 점수 계산 (헤더와 문단의 비율 등 고려)
        if paragraph_count == 0:
            return "불량"
        
        header_to_paragraph_ratio = header_count / paragraph_count
        avg_paragraph_length = total_text_length / paragraph_count if paragraph_count > 0 else 0
        
        if header_to_paragraph_ratio > 0.3 and 50 <= avg_paragraph_length <= 500:
            return "우수"
        elif header_to_paragraph_ratio > 0.1 and 30 <= avg_paragraph_length <= 800:
            return "양호"
        else:
            return "보통"

    def _calculate_metadata_completeness(self, structure: List[StructureElement]) -> float:
        """메타데이터 완성도 계산"""
        total_elements = 0
        elements_with_metadata = 0
        
        def count_metadata(elements: List[StructureElement]):
            nonlocal total_elements, elements_with_metadata
            
            for element in elements:
                total_elements += 1
                
                # 메타데이터 항목 확인
                has_position = element.position and any(element.position.values())
                has_page_number = element.page_number > 0
                has_content_type = element.content_type is not None
                has_metadata = bool(element.metadata)
                
                metadata_score = sum([has_position, has_page_number, has_content_type, has_metadata])
                if metadata_score >= 3:  # 4개 중 3개 이상
                    elements_with_metadata += 1
                
                if element.children:
                    count_metadata(element.children)
        
        count_metadata(structure)
        
        return (elements_with_metadata / total_elements * 100) if total_elements > 0 else 0
