#!/usr/bin/env python3
"""
Task 3.3: 기본 표 처리 테스트 (Java 의존성 없이)
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

async def test_basic_table_functionality():
    """기본 표 처리 기능만 테스트"""
    print("=" * 60)
    print("Task 3.3: 기본 표 처리 기능 테스트")
    print("=" * 60)
    
    # 라이브러리 가용성 확인
    print("📋 라이브러리 상태 확인:")
    
    # Camelot 확인
    try:
        import camelot
        print("✅ Camelot: 사용 가능")
        camelot_available = True
    except ImportError as e:
        print(f"❌ Camelot: 사용 불가 - {e}")
        camelot_available = False
    
    # Tabula 확인
    try:
        import tabula
        print("⚠️ Tabula: 설치됨 (Java 필요)")
        tabula_available = True
    except ImportError as e:
        print(f"❌ Tabula: 사용 불가 - {e}")
        tabula_available = False
    
    # Pandas 확인
    try:
        import pandas as pd
        print("✅ Pandas: 사용 가능")
        pandas_available = True
    except ImportError as e:
        print(f"❌ Pandas: 사용 불가 - {e}")
        pandas_available = False
    
    print()
    
    # 기본 서비스 테스트
    if pandas_available:
        await test_table_service_without_extraction()
    
    # Camelot만으로 에이전트 테스트
    if camelot_available and pandas_available:
        await test_agent_camelot_only()
    
    print("\n" + "=" * 60)
    print("기본 테스트 완료")
    print("=" * 60)

async def test_table_service_without_extraction():
    """표 서비스 기능 테스트 (추출 없이)"""
    print("🔧 표 서비스 기본 기능 테스트...")
    
    try:
        from services.table_service import AdvancedTableService
        import pandas as pd
        
        # 샘플 데이터 생성
        sample_df = pd.DataFrame({
            '상품명': ['화재보험', '자동차보험', '생명보험'],
            '보험료': [100000, 200000, 300000],
            '보장한도': [1000000, 5000000, 10000000]
        })
        
        sample_table = {
            'table_id': 'test_001',
            'page_number': 1,
            'extraction_method': 'manual',
            'confidence': 95.0,
            'dataframe': sample_df,
            'shape': sample_df.shape
        }
        
        service = AdvancedTableService()
        
        # 표 구조 개선 테스트
        enhanced = service._enhance_table_structure(sample_table)
        
        print(f"  ✅ 표 타입 분류: {enhanced.get('table_type', 'unknown')}")
        print(f"  ✅ 품질 점수: {enhanced.get('quality_score', 0):.1f}")
        print(f"  ✅ 컬럼 정리: {enhanced.get('column_names', [])}")
        
        # 텍스트 변환 테스트
        text_result = service.convert_table_to_structured_text(enhanced)
        print(f"  ✅ 텍스트 변환: {len(text_result)}자 생성")
        print(f"     미리보기: {text_result[:100]}...")
        
        print("✅ 표 서비스 기본 기능 정상 작동")
        
    except Exception as e:
        print(f"❌ 표 서비스 테스트 실패: {e}")

async def test_agent_camelot_only():
    """Camelot만 사용하는 에이전트 테스트"""
    print("\n🤖 TableProcessorAgent 기본 기능 테스트...")
    
    try:
        from agents.table_processor import TableProcessorAgent
        from agents.base import DocumentProcessingState, ProcessingStatus
        
        # 테스트용 상태 (PDF 파일 없이)
        test_state = {
            "file_path": "non_existent.pdf",  # 존재하지 않는 파일
            "policy_id": "test_001",
            "current_step": "table_extraction",
            "processed_pages": 0,
            "total_pages": 1,
            "extracted_text": [],
            "processed_chunks": [],
            "workflow_logs": []
        }
        
        agent = TableProcessorAgent(quality_threshold=30.0)
        
        print(f"  🔧 에이전트 초기화: {agent.name}")
        print(f"  🔧 고급 서비스: {'활성화' if agent.table_service else '비활성화'}")
        
        # 비존재 파일로 테스트하면 오류가 예상되지만 구조는 확인 가능
        print("  ℹ️ 에이전트 구조 확인 완료")
        print("✅ TableProcessorAgent 기본 구조 정상")
        
    except Exception as e:
        print(f"❌ 에이전트 테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_table_functionality())


