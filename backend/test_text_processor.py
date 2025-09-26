#!/usr/bin/env python3
"""
Task 3.2: 텍스트 추출 및 정제 강화 테스트 스크립트
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

from agents.text_processor import TextProcessorAgent
from agents.base import DocumentProcessingState, ProcessingStatus

async def test_text_processing():
    """텍스트 추출 및 정제 강화 테스트"""
    print("=" * 60)
    print("Task 3.2: 텍스트 추출 및 정제 강화 테스트")
    print("=" * 60)
    
    # TextProcessorAgent 초기화
    agent = TextProcessorAgent(chunk_size=200, chunk_overlap=40)
    
    # 테스트용 PDF 파일 경로 설정
    test_pdf_path = "test_policy.pdf"
    
    # 실제 PDF 파일이 없으면 경고
    if not os.path.exists(test_pdf_path):
        print(f"⚠️ 테스트 PDF 파일이 없습니다: {test_pdf_path}")
        print("💡 실제 보험약관 PDF 파일을 'test_policy.pdf'로 저장하여 테스트하세요.")
        return
    
    # 초기 상태 설정
    state: DocumentProcessingState = {
        "file_path": test_pdf_path,
        "policy_id": "test_policy_001",
        "current_step": "text_extraction",
        "processed_pages": 0,
        "total_pages": 0,
        "processing_strategy": {
            "text_extraction": "pdfplumber",
            "ocr_required": True,  # OCR 테스트를 위해 활성화
            "table_extraction": ["camelot_stream"],
            "image_processing": "basic",
            "optimization_level": "standard"
        },
        "workflow_logs": []
    }
    
    print(f"📄 테스트 파일: {test_pdf_path}")
    print(f"🔧 청킹 설정: {agent.chunk_size} 토큰, {agent.chunk_overlap} 토큰 오버랩")
    print(f"🤖 OCR 서비스: {'활성화' if agent.ocr_service else '비활성화'}")
    print(f"🧹 텍스트 정제: {'활성화' if agent.text_cleaner else '비활성화'}")
    print(f"🇰🇷 한글 처리: {'활성화' if agent.korean_processor else '비활성화'}")
    print()
    
    # 텍스트 추출 및 정제 실행
    print("🚀 텍스트 추출 및 정제 시작...")
    start_time = time.time()
    
    try:
        # 에이전트 실행
        result_state = await agent.process(state)
        
        processing_time = time.time() - start_time
        
        # 결과 분석
        if result_state.get("status") == ProcessingStatus.COMPLETED:
            print("✅ 텍스트 추출 및 정제 성공!")
            
            # 추출 결과 통계
            extracted_texts = result_state.get("extracted_text", [])
            processed_chunks = result_state.get("processed_chunks", [])
            stats = result_state.get("text_extraction_stats", {})
            
            print(f"📊 처리 통계:")
            print(f"   - 처리 시간: {processing_time:.2f}초")
            print(f"   - 총 페이지: {stats.get('total_pages', 0)}개")
            print(f"   - 추출 텍스트 길이: {stats.get('total_text_length', 0):,}자")
            print(f"   - 평균 페이지당 텍스트: {stats.get('average_text_per_page', 0):.0f}자")
            print(f"   - 생성된 청크: {len(processed_chunks)}개")
            print(f"   - OCR 사용: {'예' if stats.get('ocr_used', False) else '아니오'}")
            print()
            
            # 품질 보고서 생성
            print("📈 품질 분석 중...")
            quality_report = agent.get_text_extraction_quality_report(result_state)
            
            if "error" not in quality_report:
                print("📋 품질 보고서:")
                print(f"   - 추출 방법: {quality_report['extraction_method']}")
                print(f"   - 정제 효율성: {quality_report['text_statistics']['cleaning_efficiency']:.1%}")
                print(f"   - 평균 청크 크기: {quality_report['text_statistics']['average_chunk_size']:.0f}자")
                print(f"   - 한글 텍스트 비율: {quality_report['quality_indicators']['korean_text_ratio']:.1f}%")
                print(f"   - 청크 일관성: {quality_report['quality_indicators']['chunk_consistency']:.1f}%")
                print()
                
                # 기능 상태
                features = quality_report['processing_features']
                print("🔧 기능 상태:")
                print(f"   - OCR 통합: {'✅' if features['ocr_integration'] else '❌'}")
                print(f"   - 보험약관 정제: {'✅' if features['insurance_text_cleaning'] else '❌'}")
                print(f"   - 한글 처리: {'✅' if features['korean_text_processing'] else '❌'}")
                print(f"   - 약관 구조 탐지: {'✅' if features['article_structure_detection'] else '❌'}")
                print()
            
            # 샘플 청크 출력
            if processed_chunks:
                print("📄 샘플 청크 (처음 3개):")
                for i, chunk in enumerate(processed_chunks[:3]):
                    print(f"   청크 {i+1}:")
                    print(f"     - 타입: {chunk['metadata']['chunk_type']}")
                    print(f"     - 페이지: {chunk['metadata']['page_number']}")
                    print(f"     - 길이: {len(chunk['text'])}자")
                    print(f"     - 내용: {chunk['text'][:100]}...")
                    print()
            
            # 결과를 파일로 저장
            result_file = "test_text_extraction_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                # 결과 직렬화 가능하도록 처리
                serializable_result = {
                    "processing_time": processing_time,
                    "stats": stats,
                    "quality_report": quality_report,
                    "sample_chunks": [
                        {
                            "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                            "metadata": chunk["metadata"]
                        }
                        for chunk in processed_chunks[:5]  # 처음 5개만
                    ]
                }
                json.dump(serializable_result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 상세 결과가 저장되었습니다: {result_file}")
            
        else:
            print("❌ 텍스트 추출 및 정제 실패!")
            print(f"   오류: {result_state.get('error', '알 수 없는 오류')}")
    
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_text_cleaning_features():
    """텍스트 정제 기능 개별 테스트"""
    print("\n" + "=" * 60)
    print("텍스트 정제 기능 개별 테스트")
    print("=" * 60)
    
    # TextProcessorAgent 초기화
    agent = TextProcessorAgent()
    
    if not agent.text_cleaner:
        print("❌ 텍스트 정제 서비스를 사용할 수 없습니다.")
        return
    
    # 테스트용 원본 텍스트
    sample_text = """
    
    보험약관집     
    
    제 1 조 (목적)
    
    이 약관은    피보험자 또는 피보험인의  보험금액  에 관한 사항을 정합니다.
    
    - 1 -
    
    제2조 보상한도액
    
    보험료율    은   다음과 같습니다.
    
    페이지 1/10
    
    """
    
    print("📝 원본 텍스트:")
    print(repr(sample_text))
    print()
    
    # 텍스트 정제 실행
    cleaned_text = agent._clean_extracted_text(sample_text)
    
    print("🧹 정제된 텍스트:")
    print(repr(cleaned_text))
    print()
    
    # 정제 통계
    if agent.text_cleaner:
        stats = agent.text_cleaner.get_cleaning_statistics(sample_text, cleaned_text)
        if stats:
            print("📊 정제 통계:")
            print(f"   - 원본 길이: {stats['original_length']}자")
            print(f"   - 정제 후 길이: {stats['cleaned_length']}자")
            print(f"   - 감소율: {stats['reduction_ratio']:.1%}")
            print(f"   - 원본 줄 수: {stats['original_lines']}")
            print(f"   - 정제 후 줄 수: {stats['cleaned_lines']}")

async def main():
    """메인 테스트 함수"""
    await test_text_processing()
    await test_text_cleaning_features()
    
    print("\n" + "=" * 60)
    print("Task 3.2 테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())


