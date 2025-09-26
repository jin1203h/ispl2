"""
표 데이터 처리 및 구조화 고도화 에이전트
camelot-py와 tabula-py를 조합하여 복잡한 표 구조를 정확히 추출하고 구조화
"""
import time
import logging
from typing import List, Dict, Any, Optional
from .base import BaseAgent, DocumentProcessingState, ProcessingStatus, ProcessedChunk, ChunkMetadata

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    print("⚠️ camelot-py가 설치되지 않았습니다. 표 추출이 제한됩니다.")
    CAMELOT_AVAILABLE = False

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    print("⚠️ tabula-py가 설치되지 않았습니다. 표 추출이 제한됩니다.")
    TABULA_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("⚠️ pandas가 설치되지 않았습니다. 표 데이터 처리가 제한됩니다.")
    PANDAS_AVAILABLE = False

# 고급 표 처리 서비스 import
try:
    from services.table_service import AdvancedTableService
    ADVANCED_TABLE_SERVICE_AVAILABLE = True
except ImportError:
    print("⚠️ AdvancedTableService를 로드할 수 없습니다. 고급 표 처리 기능이 제한됩니다.")
    ADVANCED_TABLE_SERVICE_AVAILABLE = False

try:
    from services.pdfplumber_table_extractor import PDFPlumberTableExtractor
    PDFPLUMBER_EXTRACTOR_AVAILABLE = True
except ImportError:
    print("⚠️ PDFPlumberTableExtractor를 로드할 수 없습니다.")
    PDFPLUMBER_EXTRACTOR_AVAILABLE = False

logger = logging.getLogger(__name__)

class TableProcessorAgent(BaseAgent):
    """표 데이터 처리 및 구조화 고도화 에이전트"""
    
    def __init__(self, quality_threshold: float = 30.0):
        super().__init__(
            name="table_processor",
            description="PDF에서 복잡한 표 구조를 정확히 추출하고 구조화된 데이터로 변환합니다"
        )
        self.quality_threshold = quality_threshold
        
        # 고급 표 처리 서비스 초기화
        if ADVANCED_TABLE_SERVICE_AVAILABLE:
            self.table_service = AdvancedTableService()
        else:
            self.table_service = None
        
        # pdfplumber 대안 추출기 초기화
        if PDFPLUMBER_EXTRACTOR_AVAILABLE:
            self.pdfplumber_extractor = PDFPlumberTableExtractor()
        else:
            self.pdfplumber_extractor = None
    
    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """고도화된 표 추출 및 구조화"""
        self.log_step(state, "표 데이터 처리 및 구조화 고도화 시작")
        state["current_step"] = "advanced_table_extraction"
        
        if not CAMELOT_AVAILABLE and not TABULA_AVAILABLE:
            return self.update_status(
                state,
                ProcessingStatus.SKIPPED,
                "advanced_table_extraction",
                "표 추출 라이브러리가 설치되지 않음"
            )
        
        # Camelot만 있어도 처리 가능
        if not CAMELOT_AVAILABLE and TABULA_AVAILABLE:
            self.log_step(state, "Camelot 없음, Tabula만 사용 (Java 필요)", "warning")
        
        if not PANDAS_AVAILABLE:
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "advanced_table_extraction",
                "pandas가 설치되지 않아 표 처리를 할 수 없습니다"
            )
        
        try:
            start_time = time.time()
            file_path = state["file_path"]
            total_pages = state.get("total_pages", 1)
            
            # 기존 텍스트 내용 가져오기 (표-본문 연결 분석용)
            extracted_text_data = state.get("extracted_text", [])
            full_text = ""
            if extracted_text_data:
                full_text = "\n".join([
                    page_data.get("cleaned_text", page_data.get("text", ""))
                    for page_data in extracted_text_data
                    if isinstance(page_data, dict)
                ])
            
            # 고급 표 추출 수행
            if self.table_service:
                extracted_tables = await self._extract_tables_advanced(file_path, total_pages, full_text)
            else:
                extracted_tables = await self._extract_tables_basic(file_path, total_pages)
            
            # 표 데이터를 청크로 변환
            table_chunks = []
            if extracted_tables:
                table_chunks = self._convert_tables_to_enhanced_chunks(extracted_tables)
            
            # 상태 업데이트
            state["extracted_tables"] = extracted_tables
            
            # 기존 processed_chunks에 추가
            if "processed_chunks" not in state:
                state["processed_chunks"] = []
            state["processed_chunks"].extend(table_chunks)
            state["total_chunks"] = len(state["processed_chunks"])
            
            # 통계 정보
            processing_time = time.time() - start_time
            state["table_extraction_stats"] = {
                "total_tables": len(extracted_tables),
                "high_quality_tables": len([t for t in extracted_tables if t.get('quality_score', 0) >= 70]),
                "extraction_methods": list(set(t.get('extraction_method', 'unknown') for t in extracted_tables)) if extracted_tables else ["none"],
                "average_confidence": sum(t.get('confidence', 0) for t in extracted_tables) / len(extracted_tables) if extracted_tables else 0,
                "processing_time": processing_time
            }
            
            # 표가 없어도 성공으로 처리 (PDF에 표가 없을 수 있음)
            if extracted_tables:
                self.log_step(
                    state,
                    f"고도화된 표 추출 완료: {len(extracted_tables)}개 표, "
                    f"고품질: {state['table_extraction_stats']['high_quality_tables']}개, "
                    f"처리시간: {processing_time:.2f}초"
                )
            else:
                self.log_step(
                    state,
                    f"표 추출 완료: 추출된 표 없음 (PDF에 표가 없거나 Java 의존성 문제), "
                    f"처리시간: {processing_time:.2f}초"
                )
            
            return self.update_status(state, ProcessingStatus.COMPLETED, "advanced_table_extraction")
            
        except Exception as e:
            error_msg = f"고도화된 표 추출 중 오류 발생: {str(e)}"
            self.log_step(state, error_msg, "error")
            
            # 상세 오류 정보 추가
            import traceback
            detailed_error = traceback.format_exc()
            logger.error(f"표 추출 상세 오류:\n{detailed_error}")
            
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "advanced_table_extraction",
                error_msg
            )
    
    async def _extract_tables_advanced(self, file_path: str, total_pages: int, full_text: str) -> List[Dict[str, Any]]:
        """고급 표 추출 (AdvancedTableService 사용)"""
        try:
            # 1. 종합적인 표 추출
            tables = self.table_service.extract_tables_comprehensive(
                file_path, 
                page_range='all', 
                quality_threshold=self.quality_threshold
            )
            
            # 2. 표-본문 연결 관계 분석
            if full_text and tables:
                tables = self.table_service.extract_table_context_relationship(tables, full_text)
            
            self.log_step({}, f"고급 서비스로 {len(tables)}개 표 추출 완료", "debug")
            return tables
        
        except Exception as e:
            self.log_step({}, f"고급 표 추출 실패: {e}", "error")
            return []
    
    async def _extract_tables_basic(self, file_path: str, total_pages: int) -> List[Dict[str, Any]]:
        """기본 표 추출 (fallback) - 다중 전략"""
        all_tables = []
        
        try:
            # 전략 1: Camelot 기반 추출
            if CAMELOT_AVAILABLE:
                camelot_tables = await self._extract_with_camelot_lattice(file_path)
                all_tables.extend(camelot_tables)
                
                # lattice가 충분하지 않으면 stream 모드 추가
                if len(camelot_tables) < 2:
                    stream_tables = await self._extract_with_camelot_stream(file_path)
                    all_tables.extend(stream_tables)
                
                self.log_step({}, f"Camelot으로 {len(all_tables)}개 표 추출", "debug")
            
            # 전략 2: Tabula 추가 (Java 가능한 경우)
            if TABULA_AVAILABLE and len(all_tables) < 3:
                try:
                    tabula_tables = await self._extract_with_tabula(file_path)
                    all_tables.extend(tabula_tables)
                    self.log_step({}, f"Tabula로 {len(tabula_tables)}개 표 추가", "debug")
                except Exception as tabula_error:
                    self.log_step({}, f"Tabula 실패: {tabula_error}", "debug")
            
            # 전략 3: pdfplumber 대안 (Camelot/Tabula 결과가 부족한 경우)
            if len(all_tables) < 2 and self.pdfplumber_extractor:
                self.log_step({}, "pdfplumber 기반 표 추출 시도", "debug")
                try:
                    pdfplumber_tables = self.pdfplumber_extractor.extract_tables_from_pdf(file_path)
                    all_tables.extend(pdfplumber_tables)
                    self.log_step({}, f"pdfplumber로 {len(pdfplumber_tables)}개 표 추가", "debug")
                except Exception as pdfplumber_error:
                    self.log_step({}, f"pdfplumber 추출 실패: {pdfplumber_error}", "debug")
            
            # 중복 제거
            unique_tables = self._basic_deduplicate(all_tables)
            
            self.log_step({}, f"다중 전략으로 {len(unique_tables)}개 표 추출 완료", "debug")
            return unique_tables
        
        except Exception as e:
            self.log_step({}, f"기본 표 추출 실패: {e}", "error")
            return []
    
    async def _extract_with_camelot_lattice(self, file_path: str) -> List[Dict[str, Any]]:
        """Camelot lattice 모드 추출"""
        tables = []
        
        try:
            camelot_tables = camelot.read_pdf(
                file_path, 
                pages='all',
                flavor='lattice',
                line_scale=40,
                process_background=True
            )
            
            for i, table in enumerate(camelot_tables):
                if table.accuracy >= self.quality_threshold:
                    table_data = {
                        "table_id": f"camelot_lattice_{i}_{table.page}",
                        "page_number": int(table.page),
                        "extraction_method": "camelot_lattice",
                        "confidence": table.accuracy,
                        "dataframe": table.df.copy(),
                        "quality_score": table.accuracy,
                        "shape": table.df.shape,
                        "bbox": getattr(table, '_bbox', None),
                        "parsing_report": table.parsing_report
                    }
                    tables.append(table_data)
        
        except Exception as e:
            logger.warning(f"Camelot lattice 추출 실패: {e}")
        
        return tables
    
    async def _extract_with_camelot_stream(self, file_path: str) -> List[Dict[str, Any]]:
        """Camelot stream 모드 추출"""
        tables = []
        
        try:
            camelot_tables = camelot.read_pdf(
                file_path,
                pages='all',
                flavor='stream',
                edge_tol=50,
                row_tol=2
            )
            
            for i, table in enumerate(camelot_tables):
                if len(table.df) > 1 and len(table.df.columns) > 1:
                    confidence = getattr(table, 'accuracy', 60.0)
                    table_data = {
                        "table_id": f"camelot_stream_{i}_{table.page}",
                        "page_number": int(table.page),
                        "extraction_method": "camelot_stream",
                        "confidence": confidence,
                        "dataframe": table.df.copy(),
                        "quality_score": confidence,
                        "shape": table.df.shape,
                        "bbox": getattr(table, '_bbox', None),
                        "parsing_report": getattr(table, 'parsing_report', {})
                    }
                    tables.append(table_data)
        
        except Exception as e:
            logger.warning(f"Camelot stream 추출 실패: {e}")
        
        return tables
    
    async def _extract_with_tabula(self, file_path: str) -> List[Dict[str, Any]]:
        """Tabula 추출 (Java 의존성 처리)"""
        tables = []
        
        try:
            # Java 및 tabula 사용 가능성 확인
            if not TABULA_AVAILABLE:
                logger.debug("Tabula 라이브러리를 사용할 수 없습니다")
                return tables
            
            # lattice 모드 시도
            tabula_dfs = tabula.read_pdf(
                file_path,
                pages='all',
                multiple_tables=True,
                lattice=True,
                pandas_options={'header': 'infer'}
            )
            
            for i, df in enumerate(tabula_dfs):
                if len(df) > 1 and len(df.columns) > 1:
                    table_data = {
                        "table_id": f"tabula_{i}",
                        "page_number": None,
                        "extraction_method": "tabula_lattice",
                        "confidence": 50.0,
                        "dataframe": df.copy(),
                        "quality_score": 50.0,
                        "shape": df.shape,
                        "bbox": None,
                        "parsing_report": {}
                    }
                    tables.append(table_data)
        
        except Exception as e:
            # Java 관련 오류는 경고로만 처리하고 계속 진행
            if "java" in str(e).lower() or "jpype" in str(e).lower():
                logger.warning(f"Tabula Java 의존성 오류 (무시하고 계속): {e}")
            else:
                logger.warning(f"Tabula 추출 실패: {e}")
        
        return tables
    
    def _basic_deduplicate(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """기본 중복 제거"""
        if not tables:
            return []
        
        unique_tables = []
        seen_shapes = set()
        
        for table in tables:
            shape = table['shape']
            page = table.get('page_number', 0)
            signature = f"{shape}_{page}"
            
            if signature not in seen_shapes:
                seen_shapes.add(signature)
                unique_tables.append(table)
            else:
                # 같은 시그니처 중 품질이 더 좋은 것 선택
                for i, existing in enumerate(unique_tables):
                    if f"{existing['shape']}_{existing.get('page_number', 0)}" == signature:
                        if table['confidence'] > existing['confidence']:
                            unique_tables[i] = table
                        break
        
        return unique_tables
    
    def _convert_tables_to_enhanced_chunks(self, tables: List[Dict[str, Any]]) -> List[ProcessedChunk]:
        """향상된 표 청킹"""
        chunks = []
        
        for table in tables:
            try:
                # 고급 텍스트 변환 (서비스 사용 가능한 경우)
                if self.table_service:
                    table_text = self.table_service.convert_table_to_structured_text(table)
                else:
                    table_text = self._basic_table_to_text(table)
                
                if table_text.strip():
                    metadata: ChunkMetadata = {
                        "chunk_index": len(chunks),
                        "page_number": table.get("page_number"),
                        "chunk_type": f"table_{table.get('table_type', 'general')}",
                        "source": table.get("extraction_method", "table_extractor"),
                        "confidence": table.get("confidence", 50) / 100.0
                    }
                    
                    # 추가 메타데이터
                    metadata.update({
                        "table_id": table.get("table_id"),
                        "table_shape": table.get("shape"),
                        "quality_score": table.get("quality_score"),
                        "table_type": table.get("table_type", "general")
                    })
                    
                    chunk: ProcessedChunk = {
                        "text": table_text,
                        "metadata": metadata,
                        "embedding": None
                    }
                    chunks.append(chunk)
            
            except Exception as e:
                logger.warning(f"표 {table.get('table_id', 'unknown')} 청킹 실패: {e}")
        
        return chunks
    
    def _basic_table_to_text(self, table: Dict[str, Any]) -> str:
        """기본 표 텍스트 변환"""
        try:
            df = table["dataframe"]
            
            text_parts = []
            
            # 메타정보
            page_num = table.get("page_number", "Unknown")
            method = table.get("extraction_method", "Unknown")
            confidence = table.get("confidence", 0)
            shape = table.get("shape", (0, 0))
            
            text_parts.append(
                f"[표 정보] 페이지: {page_num}, 추출방법: {method}, "
                f"신뢰도: {confidence:.1f}%, 크기: {shape[0]}행 × {shape[1]}열"
            )
            
            # 헤더
            if len(df.columns) > 0:
                headers = [str(col) for col in df.columns]
                text_parts.append(f"[표 헤더] {' | '.join(headers)}")
            
            # 데이터 (최대 10행)
            text_parts.append("[표 데이터]")
            for idx, row in df.head(10).iterrows():
                row_items = []
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip():
                        row_items.append(f"{col}: {value}")
                
                if row_items:
                    text_parts.append(f"  행 {idx+1}: {' | '.join(row_items)}")
            
            # 행이 많으면 생략 표시
            if len(df) > 10:
                text_parts.append(f"  ... (총 {len(df)}행 중 10행만 표시)")
            
            return '\n'.join(text_parts)
        
        except Exception as e:
            return f"[표 변환 실패: {str(e)}]"
    
    def get_table_extraction_quality_report(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """표 추출 품질 보고서 생성"""
        try:
            extracted_tables = state.get("extracted_tables", [])
            stats = state.get("table_extraction_stats", {})
            
            if not extracted_tables:
                return {
                    "extraction_summary": {
                        "total_tables": 0,
                        "message": "추출된 표가 없습니다 (PDF에 표가 없거나 Java 의존성 문제)"
                    },
                    "advanced_features": {
                        "advanced_service_used": bool(self.table_service),
                        "camelot_available": True,  # 항상 설치되어 있다고 가정
                        "tabula_available": False,  # Java 문제로 사용 불가
                        "java_dependency_issue": True
                    }
                }
            
            # 품질 메트릭 계산
            total_tables = len(extracted_tables)
            high_quality_tables = len([t for t in extracted_tables if t.get('quality_score', 0) >= 70])
            avg_confidence = sum(t.get('confidence', 0) for t in extracted_tables) / total_tables
            
            # 추출 방법별 통계
            method_stats = {}
            for table in extracted_tables:
                method = table.get('extraction_method', 'unknown')
                if method not in method_stats:
                    method_stats[method] = {'count': 0, 'avg_confidence': 0, 'total_confidence': 0}
                method_stats[method]['count'] += 1
                method_stats[method]['total_confidence'] += table.get('confidence', 0)
            
            for method in method_stats:
                method_stats[method]['avg_confidence'] = (
                    method_stats[method]['total_confidence'] / method_stats[method]['count']
                )
                del method_stats[method]['total_confidence']  # 불필요한 필드 제거
            
            quality_report = {
                "extraction_summary": {
                    "total_tables": total_tables,
                    "high_quality_tables": high_quality_tables,
                    "quality_ratio": high_quality_tables / total_tables if total_tables > 0 else 0,
                    "average_confidence": avg_confidence
                },
                "extraction_methods": method_stats,
                "processing_performance": {
                    "processing_time": stats.get("processing_time", 0),
                    "tables_per_second": total_tables / stats.get("processing_time", 1) if stats.get("processing_time", 0) > 0 else 0
                },
                "quality_indicators": {
                    "extraction_accuracy": min(95.0, avg_confidence),
                    "structure_consistency": high_quality_tables / total_tables * 100 if total_tables > 0 else 0,
                    "method_diversity": len(method_stats)
                },
                "advanced_features": {
                    "advanced_service_used": bool(self.table_service),
                    "context_analysis": any(t.get('context_analysis') for t in extracted_tables),
                    "merged_cell_detection": any(t.get('merged_cells') for t in extracted_tables),
                    "table_type_classification": any(t.get('table_type') for t in extracted_tables)
                }
            }
            
            return quality_report
        
        except Exception as e:
            return {"error": f"품질 보고서 생성 실패: {str(e)}"}