#!/usr/bin/env python3
"""
Task 3.3: 표 데이터 처리 및 구조화 고도화 테스트 스크립트
"""

# .env 파일 로드 (가장 먼저 실행)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from agents.table_processor import TableProcessorAgent
from agents.base import DocumentProcessingState, ProcessingStatus

def get_pdf_info(file_path: str) -> tuple:
    """PDF 기본 정보 반환 (총 페이지 수, 파일 크기)"""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
    except Exception:
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
        except Exception:
            total_pages = 1
    
    # 파일 크기
    try:
        size_bytes = os.path.getsize(file_path)
        if size_bytes < 1024:
            file_size = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            file_size = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            file_size = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    except Exception:
        file_size = "알 수 없음"
    
    return total_pages, file_size

def analyze_pages_detailed(file_path: str, total_pages: int) -> list:
    """전체 페이지별 상세 분석"""
    page_analysis = []
    
    try:
        from services.pdfplumber_table_extractor import PDFPlumberTableExtractor
        extractor = PDFPlumberTableExtractor()
        
        for page_num in range(1, min(total_pages + 1, 6)):  # 최대 5페이지
            debug_info = extractor.debug_table_detection(file_path, page_num=page_num)
            
            if "error" not in debug_info:
                page_info = debug_info.get("page_info", {})
                text_info = debug_info.get("text_info", {})
                line_info = debug_info.get("line_info", {})
                table_info = debug_info.get("table_detection", {})
                
                page_summary = {
                    'page_num': page_num,
                    'width': page_info.get('width', 0),
                    'height': page_info.get('height', 0),
                    'chars': text_info.get('total_chars', 0),
                    'lines': line_info.get('total_lines', 0),
                    'h_lines': line_info.get('horizontal_lines', 0),
                    'v_lines': line_info.get('vertical_lines', 0),
                    'tables_detected': table_info.get('tables_found', 0),
                    'table_details': table_info.get('table_details', [])
                }
                page_analysis.append(page_summary)
            else:
                # 오류가 있는 경우 기본값으로
                page_analysis.append({
                    'page_num': page_num,
                    'width': 0, 'height': 0,
                    'chars': 0, 'lines': 0,
                    'h_lines': 0, 'v_lines': 0,
                    'tables_detected': 0,
                    'table_details': []
                })
    except Exception as e:
        print(f"⚠️ 페이지 분석 실패: {e}")
        # 기본값으로 초기화
        for page_num in range(1, min(total_pages + 1, 6)):
            page_analysis.append({
                'page_num': page_num,
                'width': 0, 'height': 0,
                'chars': 0, 'lines': 0,
                'h_lines': 0, 'v_lines': 0,
                'tables_detected': 0,
                'table_details': []
            })
    
    return page_analysis

class TableProcessingReport:
    """표 처리 결과 보고서 생성 및 저장"""
    
    def __init__(self, test_pdf_path: str):
        self.test_pdf_path = test_pdf_path
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_data = {
            "metadata": {
                "test_file": test_pdf_path,
                "timestamp": self.timestamp,
                "test_type": "table_processing_analysis"
            },
            "pdf_info": {},
            "page_analysis": [],
            "agent_settings": {},
            "processing_stats": {},
            "extraction_results": {},
            "quality_report": {},
            "failure_analysis": {}
        }
        self.console_output = []
    
    def log_console(self, message: str):
        """콘솔 출력을 로그에 저장"""
        self.console_output.append(message)
        print(message)
    
    def set_pdf_info(self, total_pages: int, file_size: str):
        """PDF 기본 정보 설정"""
        self.report_data["pdf_info"] = {
            "total_pages": total_pages,
            "file_size": file_size,
            "file_exists": os.path.exists(self.test_pdf_path)
        }
    
    def set_page_analysis(self, page_analysis: list):
        """페이지별 분석 결과 설정"""
        self.report_data["page_analysis"] = page_analysis
    
    def set_agent_settings(self, agent):
        """에이전트 설정 정보 저장"""
        self.report_data["agent_settings"] = {
            "quality_threshold": agent.quality_threshold,
            "advanced_service_active": bool(agent.table_service),
            "pdfplumber_extractor_active": bool(hasattr(agent, 'pdfplumber_extractor') and agent.pdfplumber_extractor),
            "camelot_available": hasattr(agent, '_extract_with_camelot_lattice'),
            "tabula_available": hasattr(agent, '_extract_with_tabula')
        }
    
    def set_processing_stats(self, processing_time: float, extracted_tables: list, table_chunks: list, stats: dict):
        """전체 처리 통계 설정"""
        self.report_data["processing_stats"] = {
            "processing_time_seconds": processing_time,
            "total_tables_extracted": len(extracted_tables),
            "high_quality_tables": stats.get('high_quality_tables', 0),
            "table_chunks_generated": len(table_chunks),
            "average_confidence": stats.get('average_confidence', 0),
            "extraction_methods_used": stats.get('extraction_methods', [])
        }
    
    def set_extraction_results(self, extracted_tables: list):
        """페이지별 표 추출 결과 설정"""
        page_table_count = {}
        detailed_results = []
        
        for i, table in enumerate(extracted_tables):
            page_num = table.get('page_number', 'Unknown')
            if page_num not in page_table_count:
                page_table_count[page_num] = 0
            page_table_count[page_num] += 1
            
            # 표 상세 정보
            table_detail = {
                "table_index": i,
                "table_id": table.get('table_id', f'table_{i}'),
                "page_number": page_num,
                "shape": table.get('shape', (0, 0)),
                "confidence": table.get('confidence', 0),
                "extraction_method": table.get('extraction_method', 'unknown'),
                "has_preview_data": False
            }
            
            # 표 내용 미리보기
            df = table.get('dataframe')
            if df is not None and not df.empty:
                table_detail["has_preview_data"] = True
                table_detail["preview_rows"] = []
                for row_idx in range(min(3, len(df))):  # 최대 3행
                    row_data = df.iloc[row_idx].tolist()[:5]  # 최대 5열
                    table_detail["preview_rows"].append(row_data)
            
            detailed_results.append(table_detail)
        
        self.report_data["extraction_results"] = {
            "page_table_counts": page_table_count,
            "detailed_table_info": detailed_results,
            "total_pages_with_tables": len(page_table_count)
        }
    
    def set_quality_report(self, quality_report: dict):
        """품질 보고서 설정"""
        self.report_data["quality_report"] = quality_report
    
    def set_failure_analysis(self, page_analysis: list, has_tables: bool):
        """실패 원인 분석 설정"""
        if not has_tables:
            total_lines = sum(p.get('lines', 0) for p in page_analysis)
            total_h_lines = sum(p.get('h_lines', 0) for p in page_analysis)
            total_v_lines = sum(p.get('v_lines', 0) for p in page_analysis)
            
            # 원인 추정
            estimated_cause = "unknown"
            if total_h_lines < 5 and total_v_lines < 5:
                estimated_cause = "text_only_document"
            elif total_lines > 100:
                estimated_cause = "complex_layout"
            else:
                estimated_cause = "non_standard_tables_or_scanned"
            
            self.report_data["failure_analysis"] = {
                "has_extraction_failure": True,
                "total_lines": total_lines,
                "horizontal_lines": total_h_lines,
                "vertical_lines": total_v_lines,
                "estimated_cause": estimated_cause,
                "recommended_solutions": [
                    "pdfplumber 고급 설정 조정",
                    "OCR 기반 표 추출 시도",
                    "수동 표 영역 지정"
                ]
            }
        else:
            self.report_data["failure_analysis"] = {
                "has_extraction_failure": False
            }
    
    def save_reports(self):
        """보고서들을 파일로 저장"""
        # 보고서 디렉토리 생성
        reports_dir = Path("reports/table_processing")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        base_filename = f"table_processing_report_{self.timestamp}"
        
        # 1. JSON 상세 보고서 저장
        json_file = reports_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            # JSON 직렬화 가능한 데이터로 변환
            def json_serializable(obj):
                """JSON 직렬화 가능한 형태로 변환"""
                if isinstance(obj, dict):
                    return {k: json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [json_serializable(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    return json_serializable(obj.__dict__)
                elif str(type(obj)) in ['<class \'pandas._libs.missing.NAType\'>', '<class \'numpy.float64\'>', '<class \'numpy.int64\'>']:
                    return None if str(obj) in ['<NA>', 'nan', 'NaN'] else str(obj)
                elif obj is None or (hasattr(obj, '__ne__') and obj != obj):  # NaN 체크
                    return None
                else:
                    try:
                        json.dumps(obj)  # 직렬화 가능한지 테스트
                        return obj
                    except (TypeError, ValueError):
                        return str(obj)
            
            serializable_data = json_serializable(self.report_data)
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        # 2. 텍스트 요약 보고서 저장
        txt_file = reports_dir / f"{base_filename}_summary.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("표 처리 및 구조화 고도화 테스트 보고서\n")
            f.write("=" * 80 + "\n\n")
            
            # 기본 정보
            f.write(f"📄 테스트 파일: {self.test_pdf_path}\n")
            f.write(f"🕐 테스트 시간: {self.timestamp}\n\n")
            
            # PDF 정보
            pdf_info = self.report_data["pdf_info"]
            f.write(f"📖 PDF 기본 정보:\n")
            f.write(f"   - 총 페이지: {pdf_info.get('total_pages', 'N/A')}페이지\n")
            f.write(f"   - 파일 크기: {pdf_info.get('file_size', 'N/A')}\n\n")
            
            # 에이전트 설정
            agent_settings = self.report_data["agent_settings"]
            f.write(f"🔧 에이전트 설정:\n")
            f.write(f"   - 품질 임계값: {agent_settings.get('quality_threshold', 'N/A')}%\n")
            f.write(f"   - 고급 표 서비스: {'활성화' if agent_settings.get('advanced_service_active') else '비활성화'}\n")
            f.write(f"   - pdfplumber 추출기: {'활성화' if agent_settings.get('pdfplumber_extractor_active') else '비활성화'}\n")
            f.write(f"   - Camelot: {'사용 가능' if agent_settings.get('camelot_available') else '사용 불가'}\n")
            f.write(f"   - Tabula: {'사용 가능' if agent_settings.get('tabula_available') else '사용 불가'}\n\n")
            
            # 처리 통계
            processing_stats = self.report_data["processing_stats"]
            f.write(f"📊 전체 처리 통계:\n")
            f.write(f"   - 처리 시간: {processing_stats.get('processing_time_seconds', 0):.2f}초\n")
            f.write(f"   - 총 추출 표: {processing_stats.get('total_tables_extracted', 0)}개\n")
            f.write(f"   - 고품질 표: {processing_stats.get('high_quality_tables', 0)}개\n")
            f.write(f"   - 표 청크 생성: {processing_stats.get('table_chunks_generated', 0)}개\n")
            f.write(f"   - 평균 신뢰도: {processing_stats.get('average_confidence', 0):.1f}%\n")
            f.write(f"   - 사용된 방법: {', '.join(processing_stats.get('extraction_methods_used', []))}\n\n")
            
            # 추출 결과
            extraction_results = self.report_data["extraction_results"]
            if extraction_results.get('total_pages_with_tables', 0) > 0:
                f.write(f"📋 페이지별 표 추출 결과:\n")
                page_counts = extraction_results.get('page_table_counts', {})
                for page_num in sorted(page_counts.keys()):
                    count = page_counts[page_num]
                    f.write(f"   페이지 {page_num}: {count}개 표 추출\n")
                
                f.write(f"\n📝 표 상세 정보:\n")
                for table_detail in extraction_results.get('detailed_table_info', [])[:10]:  # 최대 10개
                    shape = table_detail.get('shape', (0, 0))
                    f.write(f"   표 {table_detail.get('table_index', 0)+1}: "
                           f"페이지 {table_detail.get('page_number', 'N/A')}, "
                           f"{shape[0]}행×{shape[1]}열, "
                           f"{table_detail.get('confidence', 0):.1f}% "
                           f"({table_detail.get('extraction_method', 'unknown')})\n")
            else:
                f.write(f"❌ 추출된 표가 없습니다\n")
                
                # 실패 분석
                failure_analysis = self.report_data["failure_analysis"]
                if failure_analysis.get('has_extraction_failure'):
                    f.write(f"\n🔍 실패 원인 분석:\n")
                    f.write(f"   - 전체 라인 수: {failure_analysis.get('total_lines', 0)}개\n")
                    f.write(f"   - 수평 라인: {failure_analysis.get('horizontal_lines', 0)}개\n")
                    f.write(f"   - 수직 라인: {failure_analysis.get('vertical_lines', 0)}개\n")
                    f.write(f"   - 추정 원인: {failure_analysis.get('estimated_cause', 'unknown')}\n")
                    f.write(f"   - 권장 해결책:\n")
                    for solution in failure_analysis.get('recommended_solutions', []):
                        f.write(f"     * {solution}\n")
            
            f.write(f"\n")
        
        # 3. 콘솔 출력 로그 저장
        console_file = reports_dir / f"{base_filename}_console.log"
        with open(console_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.console_output))
        
        return {
            "json_report": str(json_file),
            "summary_report": str(txt_file),
            "console_log": str(console_file)
        }

async def test_table_processing():
    """표 처리 및 구조화 고도화 테스트"""
    # 테스트용 PDF 파일 경로 설정
    test_pdf_path = "uploads/pdf/test_policy.pdf"
    
    # 보고서 생성기 초기화
    report = TableProcessingReport(test_pdf_path)
    
    report.log_console("=" * 60)
    report.log_console("Task 3.3: 표 데이터 처리 및 구조화 고도화 테스트")
    report.log_console("=" * 60)
    
    # TableProcessorAgent 초기화
    agent = TableProcessorAgent(quality_threshold=30.0)
    
    # 실제 PDF 파일이 없으면 기본 기능만 테스트
    if not os.path.exists(test_pdf_path):
        report.log_console(f"⚠️ 테스트 PDF 파일이 없습니다: {test_pdf_path}")
        report.log_console("💡 기본 기능 테스트로 진행합니다.")
        
        # 기본 기능 테스트
        await test_table_service_features_only()
        return
    
    report.log_console(f"📄 테스트 파일: {test_pdf_path}")
    
    # PDF 기본 정보 분석
    total_pages, file_size = get_pdf_info(test_pdf_path)
    report.set_pdf_info(total_pages, file_size)
    
    report.log_console(f"📖 PDF 기본 정보:")
    report.log_console(f"   - 총 페이지: {total_pages}페이지")
    report.log_console(f"   - 파일 크기: {file_size}")
    report.log_console("")
    
    # 페이지별 상세 분석
    report.log_console(f"📊 페이지별 상세 분석:")
    page_analysis = analyze_pages_detailed(test_pdf_path, total_pages)
    report.set_page_analysis(page_analysis)
    
    for page_info in page_analysis[:5]:  # 최대 5페이지만
        page_num = page_info['page_num']
        report.log_console(f"   페이지 {page_num}: "
              f"{page_info['chars']:,}자, "
              f"{page_info['lines']}라인 "
              f"(H:{page_info['h_lines']}/V:{page_info['v_lines']}), "
              f"표 {page_info['tables_detected']}개")
        
        # 표 상세 정보
        for i, table_detail in enumerate(page_info['table_details']):
            rows = table_detail.get('rows', 0)
            cols = table_detail.get('cols', 0)
            bbox = table_detail.get('bbox', [])
            if bbox and len(bbox) == 4:
                report.log_console(f"      표 {i+1}: {rows}행×{cols}열, 위치({bbox[0]:.0f},{bbox[1]:.0f})")
            else:
                report.log_console(f"      표 {i+1}: {rows}행×{cols}열")
    
    if total_pages > 5:
        report.log_console(f"   ... (나머지 {total_pages - 5}페이지 생략)")
    report.log_console("")
    
    # 에이전트 설정 저장
    report.set_agent_settings(agent)
    
    report.log_console(f"🔧 에이전트 설정:")
    report.log_console(f"   - 품질 임계값: {agent.quality_threshold}%")
    report.log_console(f"   - 고급 표 서비스: {'활성화' if agent.table_service else '비활성화'}")
    report.log_console(f"   - pdfplumber 추출기: {'활성화' if hasattr(agent, 'pdfplumber_extractor') and agent.pdfplumber_extractor else '비활성화'}")
    report.log_console(f"   - Camelot: {'사용 가능' if hasattr(agent, '_extract_with_camelot_lattice') else '사용 불가'}")
    report.log_console(f"   - Tabula: {'사용 가능' if hasattr(agent, '_extract_with_tabula') else '사용 불가'}")
    report.log_console("")
    
    # 초기 상태 설정 (이전 단계들의 결과 모방)
    state: DocumentProcessingState = {
        "file_path": test_pdf_path,
        "policy_id": "test_policy_001",
        "current_step": "table_extraction",
        "processed_pages": 0,
        "total_pages": total_pages,  # 실제 페이지 수
        "extracted_text": [
            {
                "page_number": 1,
                "original_text": "다음 표는 보험료율을 나타냅니다. 표 1을 참조하십시오.",
                "cleaned_text": "다음 표는 보험료율을 나타냅니다. 표 1을 참조하십시오."
            },
            {
                "page_number": 2,
                "original_text": "위 표에서 확인할 수 있듯이, 보상한도는 가입금액에 따라 결정됩니다.",
                "cleaned_text": "위 표에서 확인할 수 있듯이, 보상한도는 가입금액에 따라 결정됩니다."
            }
        ],
        "processed_chunks": [],
        "workflow_logs": []
    }
    
    # 표 추출 및 구조화 실행
    report.log_console("🚀 표 데이터 처리 및 구조화 시작...")
    start_time = time.time()
    
    try:
        # 에이전트 실행
        result_state = await agent.process(state)
        
        processing_time = time.time() - start_time
        
        # 결과 분석 (상태와 오류 메시지 모두 확인)
        status = result_state.get("status")
        has_error = result_state.get("error_message") is not None
        
        if status == ProcessingStatus.COMPLETED.value and not has_error:
            report.log_console("✅ 표 처리 및 구조화 성공!")
            
            # 추출 결과 통계
            extracted_tables = result_state.get("extracted_tables", [])
            table_chunks = [chunk for chunk in result_state.get("processed_chunks", []) 
                          if chunk['metadata']['chunk_type'].startswith('table')]
            stats = result_state.get("table_extraction_stats", {})
            
            # 처리 통계 저장
            report.set_processing_stats(processing_time, extracted_tables, table_chunks, stats)
            
            report.log_console(f"📊 전체 처리 통계:")
            report.log_console(f"   - 처리 시간: {processing_time:.2f}초")
            report.log_console(f"   - 총 추출 표: {len(extracted_tables)}개")
            report.log_console(f"   - 고품질 표: {stats.get('high_quality_tables', 0)}개")
            report.log_console(f"   - 표 청크 생성: {len(table_chunks)}개")
            report.log_console(f"   - 평균 신뢰도: {stats.get('average_confidence', 0):.1f}%")
            report.log_console(f"   - 사용된 방법: {', '.join(stats.get('extraction_methods', []))}")
            report.log_console("")
            
            # 추출 결과 저장
            report.set_extraction_results(extracted_tables)
            
            if extracted_tables:
                # 페이지별 표 추출 결과 상세 분석
                report.log_console(f"📋 페이지별 표 추출 결과:")
                page_table_count = {}
                
                for i, table in enumerate(extracted_tables):
                    page_num = table.get('page_number', 'Unknown')
                    if page_num not in page_table_count:
                        page_table_count[page_num] = []
                    page_table_count[page_num].append(table)
                
                for page_num in sorted(page_table_count.keys()):
                    page_tables = page_table_count[page_num]
                    print(f"   페이지 {page_num}: {len(page_tables)}개 표 추출")
                    
                    for j, table in enumerate(page_tables):
                        shape = table.get('shape', (0, 0))
                        confidence = table.get('confidence', 0)
                        method = table.get('extraction_method', 'unknown')
                        table_id = table.get('table_id', f'table_{j}')
                        
                        print(f"      표 {j+1} ({table_id}): "
                              f"{shape[0]}행×{shape[1]}열, "
                              f"신뢰도 {confidence:.1f}%, "
                              f"방법: {method}")
                        
                        # 표 내용 미리보기 (첫 2행)
                        df = table.get('dataframe')
                        if df is not None and not df.empty:
                            preview_row1 = df.iloc[0].tolist()[:3] if len(df) > 0 else ['N/A']
                            print(f"         미리보기: {preview_row1}")
                            if len(df) > 1:
                                preview_row2 = df.iloc[1].tolist()[:3]
                                print(f"                   {preview_row2}")
                print()
            else:
                print("❌ 추출된 표가 없습니다")
                
                # 표가 없는 이유 분석
                print(f"\n🔍 표 추출 실패 원인 분석:")
                total_lines = sum(p['lines'] for p in page_analysis)
                total_h_lines = sum(p['h_lines'] for p in page_analysis)
                total_v_lines = sum(p['v_lines'] for p in page_analysis)
                
                print(f"   - 전체 라인 수: {total_lines}개 (H:{total_h_lines}, V:{total_v_lines})")
                
                if total_h_lines < 5 and total_v_lines < 5:
                    print(f"   💡 추정 원인: 라인 기반 표가 거의 없음 (텍스트만 구성)")
                elif total_lines > 100:
                    print(f"   💡 추정 원인: 복잡한 레이아웃으로 표 인식 어려움")
                else:
                    print(f"   💡 추정 원인: 표 형태가 일반적이지 않거나 스캔 문서")
                
                print(f"   🔧 권장 해결책:")
                print(f"      - pdfplumber 고급 설정 조정")
                print(f"      - OCR 기반 표 추출 시도")
                print(f"      - 수동 표 영역 지정")
                print()
            
            # 품질 보고서 생성
            print("📈 품질 분석 중...")
            quality_report = agent.get_table_extraction_quality_report(result_state)
            
            if "error" not in quality_report:
                print("📋 품질 보고서:")
                summary = quality_report['extraction_summary']
                print(f"   - 총 표 개수: {summary['total_tables']}개")
                
                # 표가 있는 경우에만 상세 품질 정보 출력
                if summary['total_tables'] > 0:
                    print(f"   - 고품질 비율: {summary['quality_ratio']:.1%}")
                    print(f"   - 평균 신뢰도: {summary['average_confidence']:.1f}%")
                    
                    performance = quality_report['processing_performance']
                    print(f"   - 처리 속도: {performance['tables_per_second']:.1f} 표/초")
                    
                    features = quality_report['advanced_features']
                    print(f"   - 컨텍스트 분석: {'✅' if features.get('context_analysis') else '❌'}")
                    print(f"   - 병합셀 탐지: {'✅' if features.get('merged_cell_detection') else '❌'}")
                    print(f"   - 표 타입 분류: {'✅' if features.get('table_type_classification') else '❌'}")
                else:
                    # 표가 없는 경우 메시지 출력
                    if 'message' in summary:
                        print(f"   - 상태: {summary['message']}")
                
                features = quality_report['advanced_features']
                print(f"   - 고급 서비스: {'✅' if features['advanced_service_used'] else '❌'}")
                print(f"   - Java 의존성: {'❌ 문제 있음' if features.get('java_dependency_issue') else '✅ 정상'}")
                print()
            
            # 샘플 표 출력
            if extracted_tables:
                print("📄 샘플 표 (처음 2개):")
                for i, table in enumerate(extracted_tables[:2]):
                    print(f"   표 {i+1}:")
                    print(f"     - ID: {table.get('table_id', 'Unknown')}")
                    print(f"     - 페이지: {table.get('page_number', 'Unknown')}")
                    print(f"     - 추출방법: {table.get('extraction_method', 'Unknown')}")
                    print(f"     - 신뢰도: {table.get('confidence', 0):.1f}%")
                    print(f"     - 크기: {table.get('shape', (0, 0))}")
                    print(f"     - 타입: {table.get('table_type', 'unknown')}")
                    
                    # DataFrame 샘플 출력
                    df = table.get('dataframe')
                    if df is not None and not df.empty:
                        print(f"     - 헤더: {list(df.columns)}")
                        print(f"     - 샘플 데이터: {df.head(2).to_dict('records')}")
                    print()
            
            # 샘플 청크 출력
            if table_chunks:
                print("📄 샘플 표 청크 (처음 2개):")
                for i, chunk in enumerate(table_chunks[:2]):
                    print(f"   청크 {i+1}:")
                    print(f"     - 타입: {chunk['metadata']['chunk_type']}")
                    print(f"     - 페이지: {chunk['metadata']['page_number']}")
                    print(f"     - 표 ID: {chunk['metadata'].get('table_id', 'Unknown')}")
                    print(f"     - 길이: {len(chunk['text'])}자")
                    print(f"     - 내용: {chunk['text'][:200]}...")
                    print()
            
            # 결과를 파일로 저장
            result_file = "test_table_extraction_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                # 결과 직렬화 가능하도록 처리
                serializable_result = {
                    "processing_time": processing_time,
                    "stats": stats,
                    "quality_report": quality_report,
                    "sample_tables": [
                        {
                            "table_id": table.get("table_id"),
                            "page_number": table.get("page_number"),
                            "extraction_method": table.get("extraction_method"),
                            "confidence": table.get("confidence"),
                            "shape": table.get("shape"),
                            "table_type": table.get("table_type"),
                            "headers": list(table["dataframe"].columns) if "dataframe" in table else [],
                            "sample_data": table["dataframe"].head(3).to_dict('records') if "dataframe" in table else []
                        }
                        for table in extracted_tables[:3]  # 처음 3개만
                    ],
                    "sample_chunks": [
                        {
                            "text": chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                            "metadata": chunk["metadata"]
                        }
                        for chunk in table_chunks[:3]  # 처음 3개만
                    ]
                }
                json.dump(serializable_result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 상세 결과가 저장되었습니다: {result_file}")
            
        else:
            print("❌ 표 처리 및 구조화 실패!")
            print(f"   상태: {result_state.get('status', 'Unknown')}")
            
            # 상세 오류 정보 추출
            error_info = result_state.get('error_message', result_state.get('error', '알 수 없는 오류'))
            workflow_logs = result_state.get('workflow_logs', [])
            
            print(f"   오류: {error_info}")
            
            # 워크플로우 로그에서 오류 정보 찾기
            if workflow_logs:
                error_logs = [log for log in workflow_logs if log.get('level') == 'error']
                if error_logs:
                    print("   상세 오류 로그:")
                    for log in error_logs[-3:]:  # 최근 3개만
                        print(f"     - {log.get('message', 'No message')}")
            
            # 현재 단계 정보
            current_step = result_state.get('current_step', 'Unknown')
            print(f"   실패 단계: {current_step}")
    
        # 보고서 저장
        report.log_console("\n💾 보고서 저장 중...")
        try:
            saved_files = report.save_reports()
            report.log_console("✅ 보고서 저장 완료!")
            report.log_console(f"   📄 JSON 상세 보고서: {saved_files['json_report']}")
            report.log_console(f"   📋 텍스트 요약 보고서: {saved_files['summary_report']}")
            report.log_console(f"   📝 콘솔 로그: {saved_files['console_log']}")
        except Exception as save_error:
            report.log_console(f"⚠️ 보고서 저장 실패: {save_error}")
    
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시에도 보고서 저장 시도
        try:
            saved_files = report.save_reports()
            print(f"📄 오류 보고서 저장: {saved_files['json_report']}")
        except:
            pass

async def test_table_service_features_only():
    """PDF 없이 표 서비스 기능만 테스트"""
    print("=" * 60)
    print("고급 표 서비스 기능 기본 테스트 (PDF 없음)")
    print("=" * 60)
    
    # TableProcessorAgent 초기화
    agent = TableProcessorAgent()
    
    print(f"🤖 고급 표 서비스: {'활성화' if agent.table_service else '비활성화'}")
    print(f"📊 Camelot: {'설치됨' if hasattr(agent, '_extract_with_camelot_lattice') else '미설치'}")
    print(f"📋 Tabula: {'설치됨' if hasattr(agent, '_extract_with_tabula') else '미설치'}")
    print(f"🐼 Pandas: {'설치됨' if 'pandas' in sys.modules else '미설치'}")
    
    if not agent.table_service:
        print("❌ 고급 표 서비스를 사용할 수 없습니다.")
        print("   기본 라이브러리만으로 테스트 진행")
        return
    
    # 기본 기능만 테스트
    await test_table_service_features()

async def test_table_service_features():
    """표 서비스 기능 개별 테스트"""
    print("\n" + "=" * 60)
    print("고급 표 서비스 기능 개별 테스트")
    print("=" * 60)
    
    # TableProcessorAgent 초기화
    agent = TableProcessorAgent()
    
    if not agent.table_service:
        print("❌ 고급 표 서비스를 사용할 수 없습니다.")
        return
    
    # 테스트용 샘플 표 데이터
    import pandas as pd
    
    sample_df = pd.DataFrame({
        '구분': ['A타입', 'B타입', 'C타입'],
        '보험료율(%)': [1.5, 2.0, 2.5],
        '보상한도(만원)': [1000, 2000, 3000],
        '면책금액(만원)': [10, 20, 30]
    })
    
    sample_table = {
        'table_id': 'sample_001',
        'page_number': 1,
        'extraction_method': 'sample',
        'confidence': 85.0,
        'dataframe': sample_df,
        'shape': sample_df.shape
    }
    
    print("📝 샘플 표:")
    print(sample_df)
    print()
    
    # 표 구조 개선 테스트
    print("🔧 표 구조 개선 테스트...")
    try:
        enhanced_table = agent.table_service._enhance_table_structure(sample_table)
        
        print(f"✅ 개선된 표 정보:")
        print(f"   - 표 타입: {enhanced_table.get('table_type', 'unknown')}")
        print(f"   - 캡션: {enhanced_table.get('caption', 'N/A')}")
        print(f"   - 품질 점수: {enhanced_table.get('quality_score', 0):.1f}")
        print(f"   - 컬럼명: {enhanced_table.get('column_names', [])}")
        print()
        
        # 구조화된 텍스트 변환 테스트
        print("📄 구조화된 텍스트 변환 테스트...")
        structured_text = agent.table_service.convert_table_to_structured_text(enhanced_table)
        
        print("✅ 변환된 텍스트:")
        print(structured_text)
        
    except Exception as e:
        print(f"❌ 표 서비스 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """메인 테스트 함수"""
    await test_table_processing()
    await test_table_service_features()
    
    print("\n" + "=" * 60)
    print("Task 3.3 테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
