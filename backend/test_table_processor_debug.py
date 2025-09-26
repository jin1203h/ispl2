"""
표 처리 디버깅 버전 - 실행 중 멈춤 문제 해결용
"""
import asyncio
import os
import sys
import time
import signal
from datetime import datetime

# 타임아웃 핸들러
def timeout_handler(signum, frame):
    print(f"\n⏰ 타임아웃 발생! 프로그램이 {TIMEOUT_SECONDS}초 이상 응답하지 않습니다.")
    print(f"현재 위치: {frame.f_code.co_filename}:{frame.f_lineno}")
    raise TimeoutError("프로그램 실행 타임아웃")

TIMEOUT_SECONDS = 60  # 60초 타임아웃

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

class DebugLogger:
    """디버깅을 위한 상세 로거"""
    
    def __init__(self):
        self.start_time = time.time()
        self.step_count = 0
    
    def log_step(self, message: str, detail: str = ""):
        self.step_count += 1
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:6.2f}s] Step {self.step_count:2d}: {message}")
        if detail:
            print(f"          {detail}")
        
        # 플러시로 즉시 출력
        sys.stdout.flush()

async def test_table_processing_debug():
    """디버깅 버전 표 처리 테스트"""
    logger = DebugLogger()
    
    try:
        # 시그널 핸들러 설정 (Linux/Mac에서만 작동)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(TIMEOUT_SECONDS)
        
        logger.log_step("테스트 시작", "디버깅 모드로 실행")
        
        # PDF 파일 경로
        test_pdf_path = "uploads/pdf/test_policy.pdf"
        logger.log_step(f"PDF 파일 확인", f"경로: {test_pdf_path}")
        
        if not os.path.exists(test_pdf_path):
            logger.log_step("PDF 파일 없음", "기본 기능 테스트로 전환")
            await test_basic_functionality()
            return
        
        # PDF 기본 정보 확인
        logger.log_step("PDF 정보 읽기 시작")
        try:
            import pdfplumber
            logger.log_step("pdfplumber import 성공")
            
            with pdfplumber.open(test_pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.log_step(f"PDF 열기 성공", f"총 {total_pages}페이지")
        except Exception as e:
            logger.log_step(f"PDF 열기 실패", f"오류: {e}")
            return
        
        # Agent 초기화
        logger.log_step("TableProcessorAgent 로드 시작")
        try:
            from agents.table_processor import TableProcessorAgent
            logger.log_step("TableProcessorAgent import 성공")
            
            agent = TableProcessorAgent(quality_threshold=30.0)
            logger.log_step("TableProcessorAgent 초기화 성공")
        except Exception as e:
            logger.log_step(f"Agent 초기화 실패", f"오류: {e}")
            return
        
        # 라이브러리 상태 확인
        logger.log_step("라이브러리 상태 확인")
        try:
            import camelot
            logger.log_step("Camelot 사용 가능")
        except ImportError:
            logger.log_step("Camelot 사용 불가")
        
        try:
            import tabula
            logger.log_step("Tabula 사용 가능")
        except ImportError:
            logger.log_step("Tabula 사용 불가")
        
        try:
            import pandas as pd
            logger.log_step("Pandas 사용 가능")
        except ImportError:
            logger.log_step("Pandas 사용 불가")
            return
        
        # State 생성
        logger.log_step("State 객체 생성")
        from agents.base import DocumentProcessingState
        
        state: DocumentProcessingState = {
            "file_path": test_pdf_path,
            "policy_id": "debug_test",
            "current_step": "debug_table_extraction",
            "processed_pages": 0,
            "total_pages": total_pages,
            "extracted_text": [],
            "processed_chunks": [],
            "workflow_logs": []
        }
        logger.log_step("State 객체 생성 완료")
        
        # 표 추출 실행
        logger.log_step("표 추출 시작")
        start_time = time.time()
        
        try:
            result_state = await agent.process(state)
            processing_time = time.time() - start_time
            logger.log_step(f"표 추출 완료", f"처리 시간: {processing_time:.2f}초")
            
            # 결과 분석
            status = result_state.get("status")
            error_msg = result_state.get("error_message")
            extracted_tables = result_state.get("extracted_tables", [])
            
            logger.log_step(f"결과 분석", f"상태: {status}, 표: {len(extracted_tables)}개")
            
            if error_msg:
                logger.log_step(f"오류 메시지", f"{error_msg}")
            
            # 간단한 결과 요약
            print(f"\n📊 최종 결과:")
            print(f"   - 상태: {status}")
            print(f"   - 처리 시간: {processing_time:.2f}초")
            print(f"   - 추출된 표: {len(extracted_tables)}개")
            
            if extracted_tables:
                print(f"   - 표 상세:")
                for i, table in enumerate(extracted_tables[:3]):  # 최대 3개만
                    shape = table.get('shape', (0, 0))
                    confidence = table.get('confidence', 0)
                    method = table.get('extraction_method', 'unknown')
                    print(f"     {i+1}. {shape[0]}행×{shape[1]}열, {confidence:.1f}% ({method})")
        
        except Exception as e:
            processing_time = time.time() - start_time
            logger.log_step(f"표 추출 중 오류", f"오류: {e}, 경과시간: {processing_time:.2f}초")
            import traceback
            traceback.print_exc()
        
        logger.log_step("테스트 완료")
        
    except TimeoutError:
        print(f"\n❌ 프로그램이 {TIMEOUT_SECONDS}초 타임아웃으로 중단되었습니다.")
        print(f"마지막 실행 단계: Step {logger.step_count}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 사용자에 의해 중단되었습니다 (Ctrl+C)")
        print(f"실행된 단계: {logger.step_count}")
        
    except Exception as e:
        logger.log_step(f"예상치 못한 오류", f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 타임아웃 해제
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        
        total_time = time.time() - logger.start_time
        print(f"\n🕐 총 실행 시간: {total_time:.2f}초")

async def test_basic_functionality():
    """기본 기능만 테스트 (PDF 없이)"""
    logger = DebugLogger()
    
    logger.log_step("기본 기능 테스트 시작")
    
    try:
        from agents.table_processor import TableProcessorAgent
        logger.log_step("Agent import 성공")
        
        agent = TableProcessorAgent()
        logger.log_step("Agent 초기화 성공")
        
        # 기본 설정 확인
        print(f"✅ TableProcessorAgent 기본 테스트 통과")
        print(f"   - 품질 임계값: {agent.quality_threshold}")
        print(f"   - 고급 서비스: {'활성화' if agent.table_service else '비활성화'}")
        
    except Exception as e:
        logger.log_step(f"기본 기능 테스트 실패", f"{e}")

def diagnose_system():
    """시스템 진단"""
    print("🔍 시스템 진단 시작...")
    
    # Python 버전
    print(f"Python 버전: {sys.version}")
    
    # 메모리 사용량 (가능한 경우)
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"메모리 사용량: {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)")
    except ImportError:
        print("메모리 정보 확인 불가 (psutil 필요)")
    
    # 필수 라이브러리 확인
    libraries = ['pandas', 'pdfplumber', 'camelot', 'tabula', 'asyncio']
    for lib in libraries:
        try:
            __import__(lib)
            print(f"✅ {lib}: 사용 가능")
        except ImportError:
            print(f"❌ {lib}: 사용 불가")
    
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("표 처리 디버깅 테스트")
    print("=" * 60)
    
    diagnose_system()
    
    try:
        asyncio.run(test_table_processing_debug())
    except Exception as e:
        print(f"❌ 최상위 레벨 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n디버깅 테스트 완료")


