"""
약관 특화 텍스트 정제 유틸리티
보험약관 문서의 특성에 맞는 텍스트 전처리 및 정제 기능
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class InsuranceTextCleaner:
    """보험약관 텍스트 정제기"""
    
    def __init__(self):
        # 보험약관 특화 패턴들
        self.patterns = {
            # 약관 번호 패턴
            'article_numbers': [
                r'제\s*(\d+)\s*조',  # 제1조, 제 1 조
                r'제\s*(\d+)\s*장',  # 제1장
                r'제\s*(\d+)\s*절',  # 제1절
                r'(\d+)\s*\.',      # 1., 2.
                r'(\d+)\s*-\s*(\d+)',  # 1-1, 1-2
            ],
            
            # 불필요한 머리말/바닥글 패턴
            'headers_footers': [
                r'페이지\s*\d+\s*/\s*\d+',  # 페이지 1/10
                r'- \d+ -',                  # - 1 -
                r'^\s*\d+\s*$',             # 단독 페이지 번호
                r'.*보험약관.*',             # 보험약관 제목
                r'.*약관.*집.*',             # 약관집
                r'목\s*차',                  # 목차
                r'색\s*인',                  # 색인
            ],
            
            # 보험 용어 정규화 패턴
            'insurance_terms': {
                r'피보험자|피보험인': '피보험자',
                r'보험금액|보험가액': '보험금액',
                r'보험료|보험료율': '보험료',
                r'보상한도|보상한도액': '보상한도',
                r'면책금액|공제액': '면책금액',
                r'보험기간|보험계약기간': '보험기간',
            },
            
            # 특수 문자 정리
            'special_chars': [
                r'\u00a0',  # Non-breaking space
                r'\u2022',  # Bullet point
                r'\u2023',  # Triangular bullet
                r'\u25cf',  # Black circle
                r'\u25cb',  # White circle
            ],
            
            # 중복 공백 및 줄바꿈
            'whitespace': [
                r'\s{2,}',      # 2개 이상 연속 공백
                r'\n{3,}',      # 3개 이상 연속 줄바꿈
                r'^\s+',        # 줄 시작 공백
                r'\s+$',        # 줄 끝 공백
            ]
        }
        
        # 컴파일된 정규식 패턴들
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, Any]:
        """정규식 패턴들을 컴파일"""
        compiled = {}
        
        # 단순 패턴들 컴파일
        for category, patterns in self.patterns.items():
            if category in ['article_numbers', 'headers_footers', 'special_chars', 'whitespace']:
                compiled[category] = [re.compile(pattern, re.MULTILINE | re.IGNORECASE) for pattern in patterns]
            elif category == 'insurance_terms':
                compiled[category] = {re.compile(pattern): replacement for pattern, replacement in patterns.items()}
        
        return compiled
    
    def clean_article_numbers(self, text: str) -> str:
        """약관 번호 표기 통일"""
        try:
            # 제N조 형태로 통일
            for pattern in self.compiled_patterns['article_numbers']:
                matches = pattern.findall(text)
                for match in matches:
                    if isinstance(match, tuple):
                        # 1-1 형태의 경우
                        if len(match) == 2:
                            old_text = f"{match[0]}-{match[1]}"
                            new_text = f"제{match[0]}조 제{match[1]}항"
                            text = text.replace(old_text, new_text)
                    else:
                        # 단순 숫자의 경우
                        if match.isdigit():
                            # 이미 제N조 형태가 아닌 경우만 변환
                            old_pattern = rf'\b{match}\.\s*'
                            new_text = f"제{match}조 "
                            text = re.sub(old_pattern, new_text, text)
            
            logger.debug("약관 번호 표기 통일 완료")
            return text
            
        except Exception as e:
            logger.warning(f"약관 번호 정리 실패: {e}")
            return text
    
    def remove_headers_footers(self, text: str) -> str:
        """머리말, 바닥글 제거"""
        try:
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # 불필요한 패턴 확인
                is_unnecessary = False
                for pattern in self.compiled_patterns['headers_footers']:
                    if pattern.search(line.strip()):
                        is_unnecessary = True
                        break
                
                if not is_unnecessary and line.strip():
                    cleaned_lines.append(line)
            
            result = '\n'.join(cleaned_lines)
            logger.debug(f"머리말/바닥글 제거: {len(lines)} -> {len(cleaned_lines)} 줄")
            return result
            
        except Exception as e:
            logger.warning(f"머리말/바닥글 제거 실패: {e}")
            return text
    
    def normalize_insurance_terms(self, text: str) -> str:
        """보험 용어 정규화"""
        try:
            for pattern, replacement in self.compiled_patterns['insurance_terms'].items():
                text = pattern.sub(replacement, text)
            
            logger.debug("보험 용어 정규화 완료")
            return text
            
        except Exception as e:
            logger.warning(f"보험 용어 정규화 실패: {e}")
            return text
    
    def clean_special_characters(self, text: str) -> str:
        """특수 문자 정리"""
        try:
            # 특수 문자 제거
            for pattern in self.compiled_patterns['special_chars']:
                text = pattern.sub(' ', text)
            
            # 연속된 특수 문자들 정리
            text = re.sub(r'[^\w\s가-힣.,()[\]{}+-=*/%<>:;!?@#$%^&_|"\'~`]', ' ', text)
            
            logger.debug("특수 문자 정리 완료")
            return text
            
        except Exception as e:
            logger.warning(f"특수 문자 정리 실패: {e}")
            return text
    
    def normalize_whitespace(self, text: str) -> str:
        """공백 및 줄바꿈 정규화"""
        try:
            # 연속 공백을 단일 공백으로
            text = re.sub(r'\s{2,}', ' ', text)
            
            # 연속 줄바꿈을 최대 2개로 제한
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # 줄 시작/끝 공백 제거
            lines = text.split('\n')
            cleaned_lines = [line.strip() for line in lines]
            text = '\n'.join(cleaned_lines)
            
            # 전체 시작/끝 공백 제거
            text = text.strip()
            
            logger.debug("공백 정규화 완료")
            return text
            
        except Exception as e:
            logger.warning(f"공백 정규화 실패: {e}")
            return text
    
    def extract_article_structure(self, text: str) -> List[Dict[str, Any]]:
        """약관 구조 추출 (조, 항, 호)"""
        try:
            articles = []
            current_article = None
            current_paragraph = None
            
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # 제N조 패턴 확인
                article_match = re.search(r'제\s*(\d+)\s*조\s*(.*)', line)
                if article_match:
                    # 이전 조 저장
                    if current_article:
                        articles.append(current_article)
                    
                    current_article = {
                        'article_number': int(article_match.group(1)),
                        'title': article_match.group(2).strip(),
                        'line_number': line_num + 1,
                        'content': '',
                        'paragraphs': []
                    }
                    current_paragraph = None
                    continue
                
                # 제N항 패턴 확인
                paragraph_match = re.search(r'제\s*(\d+)\s*항\s*(.*)', line)
                if paragraph_match and current_article:
                    current_paragraph = {
                        'paragraph_number': int(paragraph_match.group(1)),
                        'content': paragraph_match.group(2).strip(),
                        'line_number': line_num + 1
                    }
                    current_article['paragraphs'].append(current_paragraph)
                    continue
                
                # 일반 내용
                if current_article:
                    if current_paragraph:
                        current_paragraph['content'] += ' ' + line
                    else:
                        current_article['content'] += ' ' + line
            
            # 마지막 조 저장
            if current_article:
                articles.append(current_article)
            
            logger.debug(f"약관 구조 추출 완료: {len(articles)}개 조")
            return articles
            
        except Exception as e:
            logger.warning(f"약관 구조 추출 실패: {e}")
            return []
    
    def detect_table_text(self, text: str) -> List[Dict[str, Any]]:
        """표 형태 텍스트 탐지"""
        try:
            tables = []
            lines = text.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 탭이나 다수의 공백으로 구분된 데이터 확인
                if re.search(r'\t|\s{3,}', line) and len(line.split()) >= 3:
                    # 연속된 표 형태 라인들 수집
                    table_lines = [line]
                    j = i + 1
                    
                    while j < len(lines) and j < i + 20:  # 최대 20줄까지
                        next_line = lines[j].strip()
                        if re.search(r'\t|\s{3,}', next_line) and len(next_line.split()) >= 3:
                            table_lines.append(next_line)
                            j += 1
                        else:
                            break
                    
                    if len(table_lines) >= 2:  # 최소 2줄 이상
                        table_info = {
                            'start_line': i + 1,
                            'end_line': j,
                            'line_count': len(table_lines),
                            'content': '\n'.join(table_lines),
                            'columns': self._estimate_column_count(table_lines)
                        }
                        tables.append(table_info)
                        i = j
                    else:
                        i += 1
                else:
                    i += 1
            
            logger.debug(f"표 형태 텍스트 탐지: {len(tables)}개")
            return tables
            
        except Exception as e:
            logger.warning(f"표 텍스트 탐지 실패: {e}")
            return []
    
    def _estimate_column_count(self, table_lines: List[str]) -> int:
        """표의 열 개수 추정"""
        try:
            column_counts = []
            for line in table_lines[:5]:  # 처음 5줄만 분석
                # 탭 구분
                if '\t' in line:
                    column_counts.append(len(line.split('\t')))
                else:
                    # 3개 이상 연속 공백으로 구분
                    parts = re.split(r'\s{3,}', line)
                    column_counts.append(len(parts))
            
            # 최빈값 반환
            return max(set(column_counts), key=column_counts.count) if column_counts else 1
            
        except Exception:
            return 1
    
    def clean_full_text(self, text: str) -> str:
        """전체 텍스트 정제 파이프라인"""
        try:
            logger.info("보험약관 텍스트 정제 시작")
            
            # 1. 특수 문자 정리
            text = self.clean_special_characters(text)
            
            # 2. 머리말/바닥글 제거
            text = self.remove_headers_footers(text)
            
            # 3. 약관 번호 표기 통일
            text = self.clean_article_numbers(text)
            
            # 4. 보험 용어 정규화
            text = self.normalize_insurance_terms(text)
            
            # 5. 공백 정규화
            text = self.normalize_whitespace(text)
            
            logger.info("보험약관 텍스트 정제 완료")
            return text
            
        except Exception as e:
            logger.error(f"텍스트 정제 실패: {e}")
            return text
    
    def get_cleaning_statistics(self, original_text: str, cleaned_text: str) -> Dict[str, Any]:
        """정제 통계 정보 반환"""
        try:
            stats = {
                'original_length': len(original_text),
                'cleaned_length': len(cleaned_text),
                'reduction_ratio': (len(original_text) - len(cleaned_text)) / len(original_text) if original_text else 0,
                'original_lines': len(original_text.split('\n')),
                'cleaned_lines': len(cleaned_text.split('\n')),
                'original_words': len(original_text.split()),
                'cleaned_words': len(cleaned_text.split())
            }
            
            return stats
            
        except Exception as e:
            logger.warning(f"정제 통계 계산 실패: {e}")
            return {}

class KoreanTextProcessor:
    """한글 텍스트 특화 처리기"""
    
    def __init__(self):
        # 한글 특화 패턴들
        self.korean_patterns = {
            'incomplete_syllables': r'[ㄱ-ㅎㅏ-ㅣ]',  # 불완전한 한글 자모
            'mixed_numbers': r'(\d+)([가-힣])',        # 숫자와 한글 혼재
            'spacing_issues': r'([가-힣])([A-Za-z])',  # 한글과 영문 사이 공백
        }
    
    def normalize_korean_spacing(self, text: str) -> str:
        """한글 띄어쓰기 정규화"""
        try:
            # 한글과 영문/숫자 사이에 공백 추가
            text = re.sub(r'([가-힣])([A-Za-z0-9])', r'\1 \2', text)
            text = re.sub(r'([A-Za-z0-9])([가-힣])', r'\1 \2', text)
            
            # 불완전한 한글 자모 제거
            text = re.sub(self.korean_patterns['incomplete_syllables'], '', text)
            
            return text
            
        except Exception as e:
            logger.warning(f"한글 띄어쓰기 정규화 실패: {e}")
            return text


