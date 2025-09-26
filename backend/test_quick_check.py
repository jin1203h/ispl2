"""
빠른 상태 점검 - 어디서 멈추는지 확인
"""
import os
import time
import asyncio

async def quick_check():
    """빠른 점검"""
    print("🔍 빠른 상태 점검 시작...")
    
    # 1. PDF 파일 존재 확인
    test_pdf = "uploads/pdf/test_policy.pdf"
    if os.path.exists(test_pdf):
        print(f"✅ PDF 파일 존재: {test_pdf}")
        
        # 파일 크기 확인
        size = os.path.getsize(test_pdf)
        print(f"   파일 크기: {size:,} bytes ({size/1024/1024:.1f} MB)")
        
        # PDF 기본 정보만 빠르게 확인
        try:
            import pdfplumber
            with pdfplumber.open(test_pdf) as pdf:
                pages = len(pdf.pages)
                print(f"   총 페이지: {pages}")
                
                # 첫 페이지만 빠르게 분석
                if pages > 0:
                    page = pdf.pages[0]
                    chars = len(page.chars)
                    lines = len(page.lines)
                    print(f"   첫 페이지: {chars}문자, {lines}라인")
        except Exception as e:
            print(f"❌ PDF 분석 실패: {e}")
    else:
        print(f"❌ PDF 파일 없음: {test_pdf}")
    
    # 2. 라이브러리 로드 테스트
    print("\n📚 라이브러리 로드 테스트:")
    
    libs = {
        'camelot': '표 추출 (라인 기반)',
        'tabula': '표 추출 (Java 기반)', 
        'pdfplumber': '표 추출 (Python 기반)',
        'pandas': '데이터 처리'
    }
    
    for lib, desc in libs.items():
        try:
            start = time.time()
            if lib == 'camelot':
                import camelot
            elif lib == 'tabula':
                import tabula
            elif lib == 'pdfplumber':
                import pdfplumber
            elif lib == 'pandas':
                import pandas
            
            load_time = time.time() - start
            print(f"✅ {lib:12} ({desc}): {load_time:.3f}초")
        except Exception as e:
            print(f"❌ {lib:12}: {e}")
    
    # 3. Agent 로드 테스트
    print("\n🤖 Agent 로드 테스트:")
    try:
        start = time.time()
        from agents.table_processor import TableProcessorAgent
        load_time = time.time() - start
        print(f"✅ TableProcessorAgent 로드: {load_time:.3f}초")
        
        # Agent 초기화 테스트
        start = time.time()
        agent = TableProcessorAgent(quality_threshold=50.0)
        init_time = time.time() - start
        print(f"✅ Agent 초기화: {init_time:.3f}초")
        
        # Agent 설정 확인
        print(f"   품질 임계값: {agent.quality_threshold}")
        print(f"   고급 서비스: {'활성화' if agent.table_service else '비활성화'}")
        print(f"   pdfplumber: {'활성화' if hasattr(agent, 'pdfplumber_extractor') and agent.pdfplumber_extractor else '비활성화'}")
        
    except Exception as e:
        print(f"❌ Agent 로드 실패: {e}")
    
    print("\n✅ 빠른 점검 완료")

if __name__ == "__main__":
    asyncio.run(quick_check())


