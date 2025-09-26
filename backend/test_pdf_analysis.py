#!/usr/bin/env python3
"""
Task 3.1: PDF 품질 분석 및 구조 파악 테스트 스크립트
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

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from agents.pdf_processor import PDFProcessorAgent
from agents.base import DocumentProcessingState, ProcessingStatus

async def test_pdf_analysis():
    """PDF 분석 기능 테스트"""
    print("🔍 Task 3.1: PDF 품질 분석 및 구조 파악 테스트")
    print("=" * 60)
    
    # PDF 프로세서 에이전트 초기화
    pdf_processor = PDFProcessorAgent()
    
    # 테스트용 PDF 파일 경로 (실제 업로드된 파일이 있는 경우)
    test_files = [
        "uploads/pdf/test_policy.pdf",
        "uploads/pdf/sample.pdf",
        "../frontend/public/sample.pdf"
    ]
    
    # 실제 존재하는 PDF 파일 찾기
    test_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print("❌ 테스트용 PDF 파일을 찾을 수 없습니다.")
        print("다음 위치 중 하나에 PDF 파일을 배치해주세요:")
        for file_path in test_files:
            print(f"  - {file_path}")
        
        # 더미 PDF 파일 생성 시도
        print("\n📄 더미 PDF 파일 생성 시도...")
        dummy_pdf = await create_dummy_pdf()
        if dummy_pdf:
            test_file = dummy_pdf
        else:
            return False
    
    print(f"📄 테스트 파일: {test_file}")
    
    # 초기 상태 생성
    initial_state: DocumentProcessingState = {
        "file_path": test_file,
        "policy_id": 999,
        "file_name": os.path.basename(test_file),
        "current_step": "initialized",
        "status": ProcessingStatus.PENDING.value,
        "error_message": None,
        "raw_content": None,
        "pdf_metadata": None,
        "extracted_text": None,
        "extracted_tables": None,
        "extracted_images": None,
        "processed_chunks": [],
        "total_chunks": 0,
        "processing_time": 0.0,
        "start_time": time.time(),
        "end_time": None,
        "next_node": None
    }
    
    print("\n🚀 PDF 분석 시작...")
    start_time = time.time()
    
    # PDF 분석 실행
    result_state = await pdf_processor.process(initial_state)
    
    processing_time = time.time() - start_time
    
    # 결과 출력
    print(f"\n📊 분석 결과 (처리시간: {processing_time:.2f}초)")
    print("-" * 40)
    
    if result_state["status"] == ProcessingStatus.COMPLETED.value:
        print("✅ 분석 성공!")
        
        # 기본 정보 출력
        metadata = result_state.get("pdf_metadata", {})
        basic_info = metadata.get("basic_info", {})
        
        print(f"\n📋 기본 정보:")
        print(f"  - 파일명: {basic_info.get('title', '제목 없음')}")
        print(f"  - 페이지 수: {basic_info.get('total_pages', 0)}")
        print(f"  - 파일 크기: {basic_info.get('file_size', 0):,} bytes")
        print(f"  - 총 텍스트 길이: {basic_info.get('total_text_chars', 0):,} 문자")
        print(f"  - 총 이미지 수: {basic_info.get('total_images', 0)}")
        
        # 문서 분류 정보
        doc_classification = metadata.get("document_classification", {})
        print(f"\n📄 문서 분류:")
        print(f"  - 타입: {doc_classification.get('type', 'unknown')}")
        print(f"  - 신뢰도: {doc_classification.get('confidence', 0):.2f}")
        
        # 고급 분석 결과 (사용 가능한 경우)
        if metadata.get("advanced_analysis_available", False):
            print(f"\n🔬 고급 분석 결과:")
            
            quality = metadata.get("quality_assessment", {})
            print(f"  - 스캔 문서 여부: {'예' if quality.get('is_likely_scan', False) else '아니오'}")
            print(f"  - OCR 권장: {'예' if quality.get('ocr_recommended', False) else '아니오'}")
            
            structure = metadata.get("structure_elements", {})
            tables = structure.get("table_regions", [])
            images = structure.get("image_analysis", {})
            
            print(f"  - 탐지된 표 영역: {len(tables)}개")
            print(f"  - 이미지 분석: {images.get('total_images', 0)}개 (대형: {images.get('large_images', 0)}개)")
        
        # 처리 전략
        strategy = metadata.get("processing_recommendations", {})
        print(f"\n🎯 처리 전략:")
        print(f"  - 텍스트 추출: {strategy.get('text_extraction', 'unknown')}")
        print(f"  - OCR 필요: {'예' if strategy.get('ocr_required', False) else '아니오'}")
        print(f"  - 표 추출: {', '.join(strategy.get('table_extraction', []))}")
        print(f"  - 이미지 처리: {strategy.get('image_processing', 'basic')}")
        print(f"  - 최적화 레벨: {strategy.get('optimization_level', 'standard')}")
        
        # 페이지별 분석 (처음 3페이지만)
        pages_info = basic_info.get("pages_info", [])
        if pages_info:
            print(f"\n📄 페이지 분석 (처음 3페이지):")
            for page in pages_info[:3]:
                print(f"  페이지 {page['page_number']}: "
                      f"텍스트 {'✓' if page['has_text'] else '✗'} | "
                      f"이미지 {page['image_count']}개 | "
                      f"크기 {page['width']:.0f}x{page['height']:.0f}")
        
        # 구조 분석 결과 저장 (디버깅용)
        output_file = "test_analysis_result.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_state, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 상세 분석 결과가 {output_file}에 저장되었습니다.")
        except Exception as e:
            print(f"\n⚠️ 결과 저장 실패: {e}")
        
        return True
        
    else:
        print("❌ 분석 실패!")
        error_msg = result_state.get("error_message", "알 수 없는 오류")
        print(f"오류: {error_msg}")
        return False

async def create_dummy_pdf():
    """테스트용 더미 PDF 파일 생성"""
    try:
        # PyMuPDF로 간단한 PDF 생성
        import fitz
        
        doc = fitz.open()  # 새 PDF 문서 생성
        page = doc.new_page()
        
        # 텍스트 추가
        text = """
        테스트 보험약관 문서
        
        제1장 총칙
        제1조 (목적) 이 약관은 보험 계약에 관한 사항을 규정함을 목적으로 한다.
        
        제2조 (정의) 이 약관에서 사용하는 용어의 정의는 다음과 같다.
        1. 피보험자: 보험의 대상이 되는 사람
        2. 보험금: 보험사고 발생 시 지급하는 금액
        
        제2장 보험계약
        제3조 (계약의 체결) 보험계약은 계약자의 청약과 회사의 승낙으로 성립한다.
        """
        
        page.insert_text((50, 50), text, fontsize=12)
        
        # 저장
        os.makedirs("uploads/pdf", exist_ok=True)
        dummy_file = "uploads/pdf/test_dummy.pdf"
        doc.save(dummy_file)
        doc.close()
        
        print(f"✅ 더미 PDF 파일 생성: {dummy_file}")
        return dummy_file
        
    except ImportError:
        print("❌ PyMuPDF가 설치되지 않아 더미 PDF를 생성할 수 없습니다.")
        return None
    except Exception as e:
        print(f"❌ 더미 PDF 생성 실패: {e}")
        return None

async def main():
    """메인 테스트 함수"""
    success = await test_pdf_analysis()
    
    if success:
        print("\n🎉 Task 3.1: PDF 품질 분석 및 구조 파악 테스트 완료!")
        print("✅ 모든 기능이 정상적으로 동작합니다.")
    else:
        print("\n❌ 테스트 실패!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
