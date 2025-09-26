"""
표 추출 상세 테스트 및 디버깅 도구
"""
import asyncio
import os
from agents.table_processor import TableProcessorAgent
from services.pdfplumber_table_extractor import PDFPlumberTableExtractor

def test_table_extraction_detailed():
    """상세한 표 추출 테스트"""
    
    # 테스트할 PDF 파일들
    test_files = [
        "sample_policy.pdf",
        "sample_simple_table.pdf", 
        "sample_complex_table.pdf"
    ]
    
    print("🔍 **표 추출 상세 테스트 및 디버깅**\n")
    
    # 1. 사용 가능한 라이브러리 확인
    print("📚 **라이브러리 상태 확인:**")
    try:
        import camelot
        print("✅ camelot-py 사용 가능")
    except ImportError:
        print("❌ camelot-py 사용 불가")
    
    try:
        import tabula
        print("✅ tabula-py 설치됨")
        try:
            # Java 테스트
            tabula.read_pdf("dummy", pages="1")
        except FileNotFoundError:
            print("   📄 더미 파일 오류 (정상)")
        except Exception as e:
            if "java" in str(e).lower():
                print("   ❌ Java 의존성 문제")
            else:
                print(f"   ⚠️ 알 수 없는 오류: {e}")
    except ImportError:
        print("❌ tabula-py 사용 불가")
    
    try:
        import pdfplumber
        print("✅ pdfplumber 사용 가능")
    except ImportError:
        print("❌ pdfplumber 사용 불가")
    
    print()
    
    # 2. 실제 PDF 파일로 테스트
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"📄 **{test_file} 테스트:**")
            asyncio.run(test_single_pdf(test_file))
            print()

async def test_single_pdf(file_path: str):
    """단일 PDF 파일 상세 테스트"""
    
    try:
        # 0. PDF 기본 정보 먼저 확인
        print(f"📄 **PDF 기본 정보:**")
        total_pages = get_pdf_total_pages(file_path)
        print(f"   - 총 페이지 수: {total_pages}페이지")
        print(f"   - 파일 크기: {get_file_size(file_path)}")
        print()
        
        # 1. 전체 페이지 개별 분석
        print(f"📊 **전체 페이지 분석:**")
        extractor = PDFPlumberTableExtractor()
        page_analysis_summary = []
        
        for page_num in range(1, min(total_pages + 1, 6)):  # 최대 5페이지까지만
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
                page_analysis_summary.append(page_summary)
                
                print(f"   페이지 {page_num}: "
                      f"{page_summary['chars']:,}자, "
                      f"{page_summary['lines']}라인 "
                      f"(H:{page_summary['h_lines']}/V:{page_summary['v_lines']}), "
                      f"표 {page_summary['tables_detected']}개")
                
                # 표 상세 정보
                for i, table_detail in enumerate(page_summary['table_details']):
                    rows = table_detail.get('rows', 0)
                    cols = table_detail.get('cols', 0)
                    bbox = table_detail.get('bbox', [])
                    if bbox and len(bbox) == 4:
                        print(f"      표 {i+1}: {rows}행x{cols}열, 위치({bbox[0]:.0f},{bbox[1]:.0f})")
                    else:
                        print(f"      표 {i+1}: {rows}행x{cols}열")
            else:
                print(f"   페이지 {page_num}: ❌ 분석 실패")
        
        if total_pages > 5:
            print(f"   ... (나머지 {total_pages - 5}페이지 생략)")
        print()
        
        # 2. TableProcessorAgent 전체 테스트
        print(f"🤖 **Agent 전체 문서 테스트:**")
        agent = TableProcessorAgent(quality_threshold=30.0)
        
        state = {
            "file_path": file_path,
            "policy_id": 999,
            "file_name": os.path.basename(file_path),
            "current_step": "table_extraction_test",
            "status": "pending",
            "error_message": None,
            "total_pages": total_pages,
            "processed_chunks": []
        }
        
        result_state = await agent.process(state)
        
        status = result_state.get("status")
        error_msg = result_state.get("error_message")
        
        if status == "completed" and not error_msg:
            tables = result_state.get("extracted_tables", [])
            stats = result_state.get("table_extraction_stats", {})
            
            print(f"   ✅ 전체 추출 성공: {len(tables)}개 표")
            print(f"   📈 품질 통계: 고품질 {stats.get('high_quality_tables', 0)}개, "
                  f"평균 신뢰도 {stats.get('average_confidence', 0):.1f}%")
            print(f"   🔧 사용된 방법: {', '.join(stats.get('extraction_methods', []))}")
            print(f"   ⏱️ 처리 시간: {stats.get('processing_time', 0):.2f}초")
            print()
            
            # 3. 페이지별 표 추출 결과 상세 분석
            print(f"📋 **페이지별 표 추출 결과:**")
            page_table_count = {}
            
            for i, table in enumerate(tables):
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
                        print(f"         미리보기: {df.iloc[0].tolist()[:3] if len(df) > 0 else 'N/A'}")
                        if len(df) > 1:
                            print(f"                   {df.iloc[1].tolist()[:3]}")
            
            if not page_table_count:
                print(f"   ❌ 추출된 표가 없습니다")
                
                # 표가 없는 이유 분석
                print(f"\n🔍 **표 추출 실패 원인 분석:**")
                total_lines = sum(p['lines'] for p in page_analysis_summary)
                total_h_lines = sum(p['h_lines'] for p in page_analysis_summary)
                total_v_lines = sum(p['v_lines'] for p in page_analysis_summary)
                
                print(f"   - 전체 라인 수: {total_lines}개 (H:{total_h_lines}, V:{total_v_lines})")
                
                if total_h_lines < 5 and total_v_lines < 5:
                    print(f"   💡 추정 원인: 라인 기반 표가 거의 없음 (텍스트만 구성)")
                elif total_lines > 100:
                    print(f"   💡 추정 원인: 복잡한 레이아웃으로 표 인식 어려움")
                else:
                    print(f"   💡 추정 원인: 표 형태가 일반적이지 않거나 스캔 문서")
        else:
            print(f"   ❌ 전체 추출 실패: {error_msg or '알 수 없는 오류'}")
    
    except Exception as e:
        print(f"   💥 예외 발생: {e}")

def get_pdf_total_pages(file_path: str) -> int:
    """PDF 총 페이지 수 반환"""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            return len(pdf.pages)
    except Exception:
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return len(reader.pages)
        except Exception:
            return 1  # 기본값

def get_file_size(file_path: str) -> str:
    """파일 크기를 읽기 쉬운 형태로 반환"""
    try:
        size_bytes = os.path.getsize(file_path)
        
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    except Exception:
        return "알 수 없음"

def suggest_solutions():
    """해결 방안 제시"""
    print("🛠️ **표 추출 개선 방안:**\n")
    
    print("**즉시 해결 방안:**")
    print("1. Java 설치 및 설정")
    print("   - Oracle JDK 또는 OpenJDK 설치")
    print("   - JAVA_HOME 환경변수 설정")
    print("   - PATH에 Java bin 디렉토리 추가")
    print("   - 터미널에서 'java -version' 확인")
    print()
    
    print("2. tabula-py 재설치")
    print("   - pip uninstall tabula-py")
    print("   - pip install tabula-py")
    print("   - Java 설치 후 재설치 권장")
    print()
    
    print("**대안 방법:**")
    print("3. pdfplumber 강화 사용")
    print("   - Java 없이 동작")
    print("   - 라인 기반, 텍스트 기반, 영역 기반 추출")
    print("   - 복잡한 표에서는 성능 제한")
    print()
    
    print("4. 수동 표 영역 지정")
    print("   - PDF 좌표를 직접 지정하여 추출")
    print("   - 정확도 높음, 수동 작업 필요")
    print()
    
    print("**고급 방법:**")
    print("5. OCR 기반 표 추출")
    print("   - 이미지로 변환 후 OCR 적용")
    print("   - 스캔 문서에 효과적")
    print("   - 처리 시간 증가")

if __name__ == "__main__":
    test_table_extraction_detailed()
    suggest_solutions()
