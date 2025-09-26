"""
고급 표 처리 및 구조화 서비스
복잡한 표 구조 분석, 병합셀 처리, 표-본문 연결 관계 분석
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    print("⚠️ camelot-py가 설치되지 않았습니다.")
    CAMELOT_AVAILABLE = False

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    print("⚠️ tabula-py가 설치되지 않았습니다.")
    TABULA_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedTableService:
    """고급 표 처리 서비스"""
    
    def __init__(self):
        self.table_detection_params = {
            'camelot_lattice': {
                'line_scale': 40,
                'copy_text': ['v', 'h'],
                'process_background': True,
                'lattice_strategy': 'exact'
            },
            'camelot_stream': {
                'edge_tol': 50,
                'row_tol': 2,
                'column_tol': 0,
                'table_areas': None
            },
            'tabula': {
                'lattice': True,
                'stream': False,
                'guess': True,
                'pandas_options': {'header': 'infer'}
            }
        }
    
    def extract_tables_comprehensive(
        self, 
        file_path: str, 
        page_range: str = 'all',
        quality_threshold: float = 30.0
    ) -> List[Dict[str, Any]]:
        """종합적인 표 추출"""
        all_tables = []
        
        # 1. Camelot lattice 모드로 우선 추출
        camelot_lattice_tables = self._extract_camelot_lattice(
            file_path, page_range, quality_threshold
        )
        all_tables.extend(camelot_lattice_tables)
        
        # 2. Camelot stream 모드로 보완
        camelot_stream_tables = self._extract_camelot_stream(
            file_path, page_range, quality_threshold
        )
        all_tables.extend(camelot_stream_tables)
        
        # 3. Tabula로 추가 보완
        tabula_tables = self._extract_tabula(file_path, page_range)
        all_tables.extend(tabula_tables)
        
        # 4. 중복 제거 및 병합
        unique_tables = self._deduplicate_and_merge_tables(all_tables)
        
        # 5. 품질 평가 및 후처리
        processed_tables = []
        for table in unique_tables:
            quality_score = self._evaluate_table_quality(table)
            if quality_score >= quality_threshold:
                enhanced_table = self._enhance_table_structure(table)
                processed_tables.append(enhanced_table)
        
        logger.info(f"종합 표 추출 완료: {len(processed_tables)}개 (원본: {len(all_tables)}개)")
        return processed_tables
    
    def _extract_camelot_lattice(
        self, 
        file_path: str, 
        page_range: str, 
        quality_threshold: float
    ) -> List[Dict[str, Any]]:
        """Camelot lattice 모드 추출"""
        if not CAMELOT_AVAILABLE:
            return []
        
        tables = []
        try:
            params = self.table_detection_params['camelot_lattice']
            
            # 배경 라인 처리를 위한 두 번의 시도
            for process_bg in [False, True]:
                camelot_tables = camelot.read_pdf(
                    file_path,
                    pages=page_range,
                    flavor='lattice',
                    line_scale=params['line_scale'],
                    copy_text=params['copy_text'],
                    process_background=process_bg
                )
                
                for i, table in enumerate(camelot_tables):
                    if table.accuracy >= quality_threshold:
                        table_data = {
                            'table_id': f"camelot_lattice_{i}_{int(table.page)}_{process_bg}",
                            'page_number': int(table.page),
                            'extraction_method': f"camelot_lattice_bg_{process_bg}",
                            'confidence': table.accuracy,
                            'dataframe': table.df.copy(),
                            'bbox': getattr(table, '_bbox', None),
                            'parsing_report': table.parsing_report,
                            'shape': table.df.shape,
                            'raw_data': table.df.to_dict('records')
                        }
                        tables.append(table_data)
                
                # 첫 번째 시도에서 충분한 표를 찾았으면 두 번째 시도 생략
                if len(tables) >= 3:
                    break
        
        except Exception as e:
            logger.warning(f"Camelot lattice 추출 실패: {e}")
        
        logger.debug(f"Camelot lattice: {len(tables)}개 표 추출")
        return tables
    
    def _extract_camelot_stream(
        self, 
        file_path: str, 
        page_range: str, 
        quality_threshold: float
    ) -> List[Dict[str, Any]]:
        """Camelot stream 모드 추출"""
        if not CAMELOT_AVAILABLE:
            return []
        
        tables = []
        try:
            params = self.table_detection_params['camelot_stream']
            
            camelot_tables = camelot.read_pdf(
                file_path,
                pages=page_range,
                flavor='stream',
                edge_tol=params['edge_tol'],
                row_tol=params['row_tol'],
                column_tol=params['column_tol']
            )
            
            for i, table in enumerate(camelot_tables):
                # stream 모드는 accuracy가 없으므로 다른 기준 사용
                if len(table.df) > 1 and len(table.df.columns) > 1:
                    table_data = {
                        'table_id': f"camelot_stream_{i}_{int(table.page)}",
                        'page_number': int(table.page),
                        'extraction_method': "camelot_stream",
                        'confidence': getattr(table, 'accuracy', 70.0),  # 기본값
                        'dataframe': table.df.copy(),
                        'bbox': getattr(table, '_bbox', None),
                        'parsing_report': getattr(table, 'parsing_report', {}),
                        'shape': table.df.shape,
                        'raw_data': table.df.to_dict('records')
                    }
                    tables.append(table_data)
        
        except Exception as e:
            logger.warning(f"Camelot stream 추출 실패: {e}")
        
        logger.debug(f"Camelot stream: {len(tables)}개 표 추출")
        return tables
    
    def _extract_tabula(self, file_path: str, page_range: str) -> List[Dict[str, Any]]:
        """Tabula 추출 (Java 의존성 강화 처리)"""
        if not TABULA_AVAILABLE:
            logger.debug("Tabula 라이브러리를 사용할 수 없습니다")
            return []
        
        tables = []
        try:
            # lattice 모드 시도
            tabula_dfs = tabula.read_pdf(
                file_path,
                pages=page_range,
                multiple_tables=True,
                lattice=True,
                pandas_options={'header': 'infer'}
            )
            
            for i, df in enumerate(tabula_dfs):
                if len(df) > 1 and len(df.columns) > 1:
                    table_data = {
                        'table_id': f"tabula_lattice_{i}",
                        'page_number': None,  # tabula는 페이지 정보 제공 안 함
                        'extraction_method': "tabula_lattice",
                        'confidence': 60.0,  # 추정값
                        'dataframe': df.copy(),
                        'bbox': None,
                        'parsing_report': {},
                        'shape': df.shape,
                        'raw_data': df.to_dict('records')
                    }
                    tables.append(table_data)
            
            # stream 모드 추가 시도 (lattice가 실패하거나 부족한 경우)
            if len(tables) < 2:
                try:
                    tabula_dfs_stream = tabula.read_pdf(
                        file_path,
                        pages=page_range,
                        multiple_tables=True,
                        stream=True,
                        pandas_options={'header': 'infer'}
                    )
                    
                    for i, df in enumerate(tabula_dfs_stream):
                        if len(df) > 1 and len(df.columns) > 1:
                            table_data = {
                                'table_id': f"tabula_stream_{i}",
                                'page_number': None,
                                'extraction_method': "tabula_stream", 
                                'confidence': 50.0,
                                'dataframe': df.copy(),
                                'bbox': None,
                                'parsing_report': {},
                                'shape': df.shape,
                                'raw_data': df.to_dict('records')
                            }
                            tables.append(table_data)
                
                except Exception as stream_e:
                    if "java" in str(stream_e).lower() or "jpype" in str(stream_e).lower():
                        logger.debug(f"Tabula stream Java 의존성 오류 (무시): {stream_e}")
                    else:
                        logger.debug(f"Tabula stream 모드 실패: {stream_e}")
        
        except Exception as e:
            # Java 관련 오류는 DEBUG 레벨로 처리하여 사용자에게 노출하지 않음
            if "java" in str(e).lower() or "jpype" in str(e).lower():
                logger.debug(f"Tabula Java 의존성 오류 (무시하고 계속): {e}")
            else:
                logger.warning(f"Tabula 추출 실패: {e}")
        
        logger.debug(f"Tabula: {len(tables)}개 표 추출")
        return tables
    
    def _deduplicate_and_merge_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 제거 및 유사 표 병합"""
        if not tables:
            return []
        
        unique_tables = []
        seen_signatures = set()
        
        for table in tables:
            # 표 시그니처 생성 (크기, 첫 번째 행, 마지막 행 기반)
            signature = self._generate_table_signature(table)
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_tables.append(table)
            else:
                # 중복된 표 중 품질이 더 좋은 것 선택
                existing_idx = None
                for i, existing_table in enumerate(unique_tables):
                    if self._generate_table_signature(existing_table) == signature:
                        existing_idx = i
                        break
                
                if existing_idx is not None:
                    existing_confidence = unique_tables[existing_idx]['confidence']
                    new_confidence = table['confidence']
                    
                    if new_confidence > existing_confidence:
                        unique_tables[existing_idx] = table
        
        logger.debug(f"중복 제거: {len(tables)} → {len(unique_tables)}개")
        return unique_tables
    
    def _generate_table_signature(self, table: Dict[str, Any]) -> str:
        """표의 고유 시그니처 생성"""
        try:
            df = table['dataframe']
            shape = df.shape
            
            # 첫 번째와 마지막 행의 일부 데이터
            first_row = str(df.iloc[0].head(3).tolist()) if len(df) > 0 else ""
            last_row = str(df.iloc[-1].head(3).tolist()) if len(df) > 0 else ""
            
            # 페이지 번호 (있는 경우)
            page = table.get('page_number', 0)
            
            signature = f"{shape}_{page}_{hash(first_row + last_row) % 10000}"
            return signature
        
        except Exception:
            return f"fallback_{hash(str(table.get('table_id', 'unknown'))) % 10000}"
    
    def _evaluate_table_quality(self, table: Dict[str, Any]) -> float:
        """표 품질 평가"""
        try:
            df = table['dataframe']
            base_confidence = table.get('confidence', 50.0)
            
            # 품질 요소들
            factors = []
            
            # 1. 기본 신뢰도
            factors.append(('base_confidence', base_confidence, 0.4))
            
            # 2. 크기 적절성 (너무 작거나 크지 않음)
            rows, cols = df.shape
            size_score = min(100, max(20, (rows * cols) * 5))  # 2x2 = 20점, 10x10 = 500점 → 100점
            if size_score > 100:
                size_score = 100 - (size_score - 100) * 0.1  # 너무 크면 감점
            factors.append(('size_score', size_score, 0.2))
            
            # 3. 데이터 완성도 (빈 셀 비율)
            total_cells = rows * cols
            empty_cells = df.isnull().sum().sum() + (df == '').sum().sum()
            completeness_score = max(0, (1 - empty_cells / total_cells) * 100) if total_cells > 0 else 0
            factors.append(('completeness', completeness_score, 0.2))
            
            # 4. 구조 일관성 (각 행의 열 개수 일치)
            structure_score = 100.0  # pandas DataFrame은 이미 구조적으로 일치
            factors.append(('structure', structure_score, 0.1))
            
            # 5. 내용 다양성 (각 셀이 서로 다른 내용)
            unique_values = len(set(df.values.flatten().astype(str)))
            diversity_score = min(100, (unique_values / total_cells) * 100) if total_cells > 0 else 0
            factors.append(('diversity', diversity_score, 0.1))
            
            # 가중 평균 계산
            weighted_score = sum(score * weight for _, score, weight in factors)
            
            return min(100.0, max(0.0, weighted_score))
        
        except Exception as e:
            logger.warning(f"표 품질 평가 실패: {e}")
            return table.get('confidence', 50.0)
    
    def _enhance_table_structure(self, table: Dict[str, Any]) -> Dict[str, Any]:
        """표 구조 개선 및 메타데이터 보강"""
        try:
            df = table['dataframe'].copy()
            
            # 1. 컬럼명 정리
            df.columns = self._clean_column_names(df.columns)
            
            # 2. 셀 내용 정리
            df = self._clean_cell_contents(df)
            
            # 3. 병합셀 패턴 탐지
            merged_cell_info = self._detect_merged_cells(df)
            
            # 4. 표 유형 분류
            table_type = self._classify_table_type(df)
            
            # 5. 표 캡션/제목 추정
            caption = self._estimate_table_caption(table, df)
            
            # 개선된 표 정보 업데이트
            enhanced_table = table.copy()
            enhanced_table.update({
                'dataframe': df,
                'cleaned_data': df.to_dict('records'),
                'column_names': df.columns.tolist(),
                'table_type': table_type,
                'caption': caption,
                'merged_cells': merged_cell_info,
                'quality_score': self._evaluate_table_quality(table),
                'processing_notes': []
            })
            
            return enhanced_table
        
        except Exception as e:
            logger.warning(f"표 구조 개선 실패: {e}")
            return table
    
    def _clean_column_names(self, columns) -> List[str]:
        """컬럼명 정리"""
        cleaned_columns = []
        for i, col in enumerate(columns):
            col_str = str(col).strip()
            
            # 빈 컬럼명 처리
            if not col_str or col_str.lower() in ['unnamed', 'nan', 'none']:
                col_str = f"Column_{i+1}"
            
            # 특수문자 정리
            col_str = re.sub(r'[^\w\s가-힣]', '_', col_str)
            col_str = re.sub(r'\s+', '_', col_str)
            
            cleaned_columns.append(col_str)
        
        return cleaned_columns
    
    def _clean_cell_contents(self, df: pd.DataFrame) -> pd.DataFrame:
        """셀 내용 정리"""
        df_cleaned = df.copy()
        
        for col in df_cleaned.columns:
            # 문자열 컬럼 정리
            if df_cleaned[col].dtype == 'object':
                df_cleaned[col] = df_cleaned[col].astype(str)
                df_cleaned[col] = df_cleaned[col].str.strip()
                
                # 빈 문자열을 NaN으로
                df_cleaned[col] = df_cleaned[col].replace(['', 'nan', 'None'], pd.NA)
                
                # 줄바꿈 정리
                df_cleaned[col] = df_cleaned[col].str.replace(r'\n+', ' ', regex=True)
                df_cleaned[col] = df_cleaned[col].str.replace(r'\s+', ' ', regex=True)
        
        return df_cleaned
    
    def _detect_merged_cells(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """병합셀 패턴 탐지"""
        merged_patterns = []
        
        try:
            # 같은 값이 연속으로 나타나는 패턴 찾기
            for col_idx, col in enumerate(df.columns):
                current_value = None
                start_row = 0
                
                for row_idx in range(len(df)):
                    cell_value = df.iloc[row_idx, col_idx]
                    
                    if pd.isna(cell_value) or str(cell_value).strip() == '':
                        continue
                    
                    if current_value == cell_value and row_idx > start_row:
                        # 연속된 같은 값 발견
                        continue
                    else:
                        # 새로운 값 시작
                        if current_value is not None and row_idx - start_row > 1:
                            merged_patterns.append({
                                'column': col,
                                'start_row': start_row,
                                'end_row': row_idx - 1,
                                'value': current_value,
                                'span_size': row_idx - start_row
                            })
                        
                        current_value = cell_value
                        start_row = row_idx
        
        except Exception as e:
            logger.debug(f"병합셀 탐지 실패: {e}")
        
        return merged_patterns
    
    def _classify_table_type(self, df: pd.DataFrame) -> str:
        """표 유형 분류"""
        try:
            rows, cols = df.shape
            
            # 크기 기반 분류
            if rows <= 2 or cols <= 2:
                return "simple_list"
            elif rows > 20 and cols > 5:
                return "large_data_table"
            
            # 내용 기반 분류
            numeric_cols = len([col for col in df.columns if df[col].dtype in ['int64', 'float64']])
            
            if numeric_cols / cols > 0.7:
                return "numerical_table"
            elif any(keyword in str(df.columns).lower() for keyword in ['금액', '비용', '요금', '보험료']):
                return "financial_table"
            elif any(keyword in str(df.columns).lower() for keyword in ['조건', '대상', '범위', '한도']):
                return "condition_table"
            else:
                return "general_table"
        
        except Exception:
            return "unknown_table"
    
    def _estimate_table_caption(self, table: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
        """표 캡션/제목 추정"""
        try:
            # 표 주변 텍스트에서 캡션 추정 (향후 구현)
            # 현재는 기본 정보로 캡션 생성
            page_num = table.get('page_number', 'Unknown')
            table_type = self._classify_table_type(df)
            shape = df.shape
            
            caption = f"Page {page_num} - {table_type} ({shape[0]}×{shape[1]})"
            return caption
        
        except Exception:
            return None
    
    def extract_table_context_relationship(
        self, 
        tables: List[Dict[str, Any]], 
        text_content: str
    ) -> List[Dict[str, Any]]:
        """표와 본문의 연결 관계 분석"""
        enriched_tables = []
        
        for table in tables:
            try:
                # 표 주변 텍스트 분석
                context_info = self._analyze_table_context(table, text_content)
                
                # 표 참조 관계 분석
                reference_info = self._find_table_references(table, text_content)
                
                # 정보 추가
                enriched_table = table.copy()
                enriched_table.update({
                    'context_analysis': context_info,
                    'reference_analysis': reference_info
                })
                
                enriched_tables.append(enriched_table)
            
            except Exception as e:
                logger.warning(f"표 {table.get('table_id', 'unknown')} 컨텍스트 분석 실패: {e}")
                enriched_tables.append(table)
        
        return enriched_tables
    
    def _analyze_table_context(self, table: Dict[str, Any], text_content: str) -> Dict[str, Any]:
        """표 컨텍스트 분석"""
        context_info = {
            'preceding_text': '',
            'following_text': '',
            'related_keywords': [],
            'context_confidence': 0.0
        }
        
        try:
            page_num = table.get('page_number')
            if page_num and text_content:
                # 페이지별 텍스트에서 표 위치 추정
                # 실제 구현에서는 PDF의 좌표 정보를 활용
                pass
        
        except Exception as e:
            logger.debug(f"표 컨텍스트 분석 실패: {e}")
        
        return context_info
    
    def _find_table_references(self, table: Dict[str, Any], text_content: str) -> Dict[str, Any]:
        """표 참조 관계 찾기"""
        reference_info = {
            'reference_patterns': [],
            'mentioned_locations': [],
            'reference_count': 0
        }
        
        try:
            # "표 1", "다음 표", "위 표" 등의 패턴 찾기
            table_patterns = [
                r'표\s*\d+',
                r'다음\s*표',
                r'위\s*표',
                r'아래\s*표',
                r'상기\s*표',
                r'하기\s*표'
            ]
            
            for pattern in table_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                reference_info['reference_patterns'].extend([
                    {'pattern': pattern, 'match': match.group(), 'position': match.start()}
                    for match in matches
                ])
            
            reference_info['reference_count'] = len(reference_info['reference_patterns'])
        
        except Exception as e:
            logger.debug(f"표 참조 분석 실패: {e}")
        
        return reference_info
    
    def convert_table_to_structured_text(self, table: Dict[str, Any]) -> str:
        """표를 구조화된 텍스트로 변환"""
        try:
            df = table['dataframe']
            table_type = table.get('table_type', 'general_table')
            caption = table.get('caption', '')
            
            text_parts = []
            
            # 캡션 추가
            if caption:
                text_parts.append(f"[표 제목] {caption}")
            
            # 메타정보
            page_num = table.get('page_number', 'Unknown')
            method = table.get('extraction_method', 'unknown')
            confidence = table.get('confidence', 0)
            
            text_parts.append(
                f"[표 정보] 페이지: {page_num}, 추출방법: {method}, "
                f"신뢰도: {confidence:.1f}%, 크기: {df.shape[0]}행 × {df.shape[1]}열"
            )
            
            # 표 유형별 특화 변환
            if table_type == 'financial_table':
                structured_text = self._convert_financial_table(df)
            elif table_type == 'condition_table':
                structured_text = self._convert_condition_table(df)
            else:
                structured_text = self._convert_general_table(df)
            
            text_parts.append(structured_text)
            
            return '\n'.join(text_parts)
        
        except Exception as e:
            logger.error(f"표 텍스트 변환 실패: {e}")
            return f"[표 변환 실패: {str(e)}]"
    
    def _convert_financial_table(self, df: pd.DataFrame) -> str:
        """금융/보험료 표 전용 변환"""
        try:
            text_parts = ["[금융 표 데이터]"]
            
            for idx, row in df.iterrows():
                row_items = []
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        # 금액 관련 컬럼 강조
                        if any(keyword in str(col).lower() for keyword in ['금액', '비용', '요금', '보험료']):
                            row_items.append(f"**{col}: {value}**")
                        else:
                            row_items.append(f"{col}: {value}")
                
                if row_items:
                    text_parts.append(f"  • {' | '.join(row_items)}")
            
            return '\n'.join(text_parts)
        
        except Exception:
            return self._convert_general_table(df)
    
    def _convert_condition_table(self, df: pd.DataFrame) -> str:
        """조건/범위 표 전용 변환"""
        try:
            text_parts = ["[조건 표 데이터]"]
            
            for idx, row in df.iterrows():
                condition_parts = []
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        condition_parts.append(f"{col}: {value}")
                
                if condition_parts:
                    text_parts.append(f"  조건 {idx+1}: {' → '.join(condition_parts)}")
            
            return '\n'.join(text_parts)
        
        except Exception:
            return self._convert_general_table(df)
    
    def _convert_general_table(self, df: pd.DataFrame) -> str:
        """일반 표 변환"""
        try:
            text_parts = ["[표 데이터]"]
            
            # 헤더 정보
            text_parts.append(f"헤더: {' | '.join(df.columns)}")
            
            # 데이터 행들 (최대 15행)
            for idx, row in df.head(15).iterrows():
                row_text = " | ".join(
                    f"{col}: {value}" for col, value in row.items() 
                    if pd.notna(value) and str(value).strip()
                )
                if row_text:
                    text_parts.append(f"  행 {idx+1}: {row_text}")
            
            # 행이 많으면 생략 표시
            if len(df) > 15:
                text_parts.append(f"  ... (총 {len(df)}행 중 15행만 표시)")
            
            return '\n'.join(text_parts)
        
        except Exception as e:
            return f"[일반 표 변환 실패: {str(e)}]"
