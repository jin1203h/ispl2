"""
안전한 표 추출 테스트 - 타임아웃과 안전장치 포함
"""
import asyncio
import os
import time
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import threading

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

class SafeTableTest:
    """안전한 표 추출 테스트"""
    
    def __init__(self):
        self.timeout = 30  # 30초 타임아웃
        self.results = {}
    
    def run_with_timeout(self, func, *args, **kwargs):
        """함수를 타임아웃과 함께 실행"""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=self.timeout)
            except FutureTimeoutError:
                print(f"⏰ 타임아웃 ({self.timeout}초) 발생")
                return None
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                return None
    
    async def test_camelot_only(self, file_path: str):
        """Camelot만 테스트"""
        print("🐪 Camelot 단독 테스트...")
        
        def camelot_test():
            try:
                import camelot
                print("   Camelot 라이브러리 로드 완료")
                
                # lattice 모드 테스트
                print("   Lattice 모드 시도...")
                tables = camelot.read_pdf(file_path, pages='1', flavor='lattice')
                print(f"   Lattice 결과: {len(tables)}개 표")
                
                # stream 모드 테스트
                print("   Stream 모드 시도...")
                tables = camelot.read_pdf(file_path, pages='1', flavor='stream')
                print(f"   Stream 결과: {len(tables)}개 표")
                
                return {"camelot_success": True, "tables_found": len(tables)}
            except Exception as e:
                print(f"   Camelot 오류: {e}")
                return {"camelot_success": False, "error": str(e)}
        
        result = self.run_with_timeout(camelot_test)
        self.results["camelot"] = result
        return result
    
    async def test_pdfplumber_only(self, file_path: str):
        """pdfplumber만 테스트"""
        print("📄 pdfplumber 단독 테스트...")
        
        def pdfplumber_test():
            try:
                import pdfplumber
                print("   pdfplumber 라이브러리 로드 완료")
                
                with pdfplumber.open(file_path) as pdf:
                    page = pdf.pages[0]
                    print("   첫 페이지 로드 완료")
                    
                    # 표 찾기
                    tables = page.find_tables()
                    print(f"   표 탐지 결과: {len(tables)}개")
                    
                    if tables:
                        for i, table in enumerate(tables):
                            data = table.extract()
                            print(f"   표 {i+1}: {len(data)}행")
                    
                    return {"pdfplumber_success": True, "tables_found": len(tables)}
            except Exception as e:
                print(f"   pdfplumber 오류: {e}")
                return {"pdfplumber_success": False, "error": str(e)}
        
        result = self.run_with_timeout(pdfplumber_test)
        self.results["pdfplumber"] = result
        return result
    
    async def test_agent_minimal(self, file_path: str):
        """Agent 최소 테스트"""
        print("🤖 Agent 최소 테스트...")
        
        def agent_test():
            try:
                from agents.table_processor import TableProcessorAgent
                from agents.base import DocumentProcessingState
                
                print("   Agent import 완료")
                
                # 매우 높은 임계값으로 빠른 실행
                agent = TableProcessorAgent(quality_threshold=90.0)
                print("   Agent 초기화 완료")
                
                # 최소 State
                state: DocumentProcessingState = {
                    "file_path": file_path,
                    "policy_id": "safe_test",
                    "current_step": "safe_table_test",
                    "processed_pages": 0,
                    "total_pages": 1,  # 첫 페이지만
                    "extracted_text": [],
                    "processed_chunks": [],
                    "workflow_logs": []
                }
                
                print("   State 생성 완료, 처리 시작...")
                start_time = time.time()
                
                # 비동기 실행을 동기로 변환
                import asyncio
                result = asyncio.run(agent.process(state))
                
                processing_time = time.time() - start_time
                print(f"   처리 완료: {processing_time:.2f}초")
                
                status = result.get("status", "unknown")
                tables = result.get("extracted_tables", [])
                
                return {
                    "agent_success": True,
                    "status": status,
                    "tables_found": len(tables),
                    "processing_time": processing_time
                }
            except Exception as e:
                print(f"   Agent 오류: {e}")
                return {"agent_success": False, "error": str(e)}
        
        result = self.run_with_timeout(agent_test)
        self.results["agent"] = result
        return result

async def main():
    """메인 테스트"""
    print("🛡️ 안전한 표 추출 테스트 시작")
    print("=" * 50)
    
    file_path = "uploads/pdf/test_policy.pdf"
    
    if not os.path.exists(file_path):
        print(f"❌ PDF 파일이 없습니다: {file_path}")
        return
    
    tester = SafeTableTest()
    
    # 1. Camelot 단독 테스트
    await tester.test_camelot_only(file_path)
    
    # 2. pdfplumber 단독 테스트  
    await tester.test_pdfplumber_only(file_path)
    
    # 3. Agent 최소 테스트
    await tester.test_agent_minimal(file_path)
    
    # 결과 요약
    print("\n📊 테스트 결과 요약:")
    print("-" * 30)
    
    for test_name, result in tester.results.items():
        if result:
            if result.get(f"{test_name}_success"):
                tables = result.get("tables_found", 0)
                time_taken = result.get("processing_time", "N/A")
                print(f"✅ {test_name:12}: {tables}개 표, 시간: {time_taken}")
            else:
                error = result.get("error", "Unknown")
                print(f"❌ {test_name:12}: 실패 - {error}")
        else:
            print(f"⏰ {test_name:12}: 타임아웃")
    
    print("\n안전한 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())


