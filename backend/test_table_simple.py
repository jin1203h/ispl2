"""
간단한 표 추출 테스트 도구
"""
import asyncio
import os
import sys
from agents.table_processor import TableProcessorAgent

async def quick_table_test():
    """빠른 표 추출 테스트"""
    
    file_path = "uploads/pdf/test_policy.pdf"

    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    print(f"📄 파일: {os.path.basename(file_path)}")
    print(f"📊 표 추출 테스트 시작...\n")
    
    # PDF 기본 정보
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"📖 총 페이지: {total_pages}페이지")
    except Exception as e:
        print(f"⚠️ PDF 정보 읽기 실패: {e}")
        total_pages = 1
    
    # 표 추출 실행
    agent = TableProcessorAgent(quality_threshold=30.0)
    
    state = {
        "file_path": file_path,
        "policy_id": 999,
        "file_name": os.path.basename(file_path),
        "current_step": "quick_table_test",
        "status": "pending",
        "error_message": None,
        "total_pages": total_pages,
        "processed_chunks": []
    }
    
    try:
        result_state = await agent.process(state)
        
        status = result_state.get("status")
        error_msg = result_state.get("error_message")
        
        if status == "completed" and not error_msg:
            tables = result_state.get("extracted_tables", [])
            stats = result_state.get("table_extraction_stats", {})
            
            print(f"✅ 성공!")
            print(f"📊 결과 요약:")
            print(f"   • 총 추출 표: {len(tables)}개")
            print(f"   • 고품질 표: {stats.get('high_quality_tables', 0)}개")
            print(f"   • 평균 신뢰도: {stats.get('average_confidence', 0):.1f}%")
            print(f"   • 처리 시간: {stats.get('processing_time', 0):.2f}초")
            print(f"   • 사용 방법: {', '.join(stats.get('extraction_methods', []))}")
            
            if tables:
                print(f"\n📋 페이지별 표 분포:")
                page_counts = {}
                for table in tables:
                    page_num = table.get('page_number', 'Unknown')
                    page_counts[page_num] = page_counts.get(page_num, 0) + 1
                
                for page_num in sorted(page_counts.keys()):
                    count = page_counts[page_num]
                    print(f"   • 페이지 {page_num}: {count}개")
                
                print(f"\n📝 표 상세 정보:")
                for i, table in enumerate(tables[:5]):  # 최대 5개만
                    shape = table.get('shape', (0, 0))
                    confidence = table.get('confidence', 0)
                    method = table.get('extraction_method', 'unknown')
                    page = table.get('page_number', 'N/A')
                    
                    print(f"   {i+1}. 페이지 {page}: {shape[0]}행×{shape[1]}열, "
                          f"{confidence:.0f}% ({method})")
                
                if len(tables) > 5:
                    print(f"   ... (총 {len(tables)}개 중 5개만 표시)")
            else:
                print(f"\n❌ 추출된 표가 없습니다")
                
                # 원인 추정
                print(f"\n🔍 가능한 원인:")
                if stats.get('extraction_methods') == ['none']:
                    print(f"   • PDF에 표가 없거나 텍스트만 구성")
                else:
                    print(f"   • 표 형태가 복잡하거나 비표준적")
                    print(f"   • Java 의존성 문제 (tabula-py)")
                    print(f"   • 스캔된 이미지 형태의 표")
        else:
            print(f"❌ 실패: {error_msg or '알 수 없는 오류'}")
    
    except Exception as e:
        print(f"💥 예외 발생: {e}")

def main():
    """메인 함수"""
    # if len(sys.argv) != 2:
    #     print("사용법: python test_table_simple.py <PDF파일경로>")
    #     print("예시: python test_table_simple.py sample_policy.pdf")
    #     return
    
    # file_path = sys.argv[1]
    asyncio.run(quick_table_test())

if __name__ == "__main__":
    main()


