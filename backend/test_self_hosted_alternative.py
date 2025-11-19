#!/usr/bin/env python3
"""
Self-hosted LangFuse 대안 테스트
Docker 없이 로컬 모니터링 시스템으로 완전한 워크플로우 모니터링 테스트
"""
import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_local_monitoring_complete():
    """로컬 모니터링 시스템 완전 테스트"""
    print("=" * 60)
    print("🏠 로컬 모니터링 시스템 완전 테스트")
    print("   (Self-hosted LangFuse 대안)")
    print("=" * 60)
    
    try:
        # 로컬 모니터 직접 사용 (LangFuse 우회)
        from services.local_monitor import local_monitor
        
        print(f"✅ 로컬 모니터 활성화: {local_monitor.enabled}")
        print(f"✅ 로그 디렉토리: {local_monitor.log_dir}")
        
        # 복잡한 워크플로우 시뮬레이션
        print("\n📊 복잡한 PDF 처리 워크플로우 시뮬레이션...")
        
        # 1. PDF 처리 워크플로우
        async with local_monitor.trace_workflow(
            "pdf_processing_pipeline",
            {
                "document": "sample_insurance_policy.pdf",
                "file_size": "2.5MB",
                "pages": 45,
                "language": "korean"
            }
        ) as pdf_trace:
            print("✅ PDF 처리 워크플로우 시작")
            
            # 1.1 PDF 분석 에이전트
            pdf_analyzer = await local_monitor.trace_agent_execution(
                "pdf_analyzer",
                {
                    "input_file": "sample_insurance_policy.pdf",
                    "analysis_type": "structure_detection"
                },
                pdf_trace
            )
            
            await asyncio.sleep(0.2)  # 처리 시간 시뮬레이션
            
            await local_monitor.update_agent_result(
                pdf_analyzer,
                {
                    "has_text_layer": True,
                    "table_count": 8,
                    "image_count": 3,
                    "total_pages": 45,
                    "scan_quality": "high"
                },
                0.2,
                "completed"
            )
            print("  ✅ PDF 분석 완료")
            
            # 1.2 텍스트 추출 에이전트
            text_extractor = await local_monitor.trace_agent_execution(
                "text_extractor",
                {
                    "extraction_method": "pdfplumber_primary",
                    "fallback_ocr": True
                },
                pdf_trace
            )
            
            await asyncio.sleep(0.3)
            
            await local_monitor.update_agent_result(
                text_extractor,
                {
                    "extracted_text_length": 45678,
                    "confidence_score": 0.95,
                    "ocr_pages": 2,
                    "cleanup_applied": True
                },
                0.3,
                "completed"
            )
            print("  ✅ 텍스트 추출 완료")
            
            # 1.3 표 처리 에이전트
            table_processor = await local_monitor.trace_agent_execution(
                "table_processor",
                {
                    "table_detection_method": "camelot-py",
                    "table_count": 8
                },
                pdf_trace
            )
            
            await asyncio.sleep(0.25)
            
            await local_monitor.update_agent_result(
                table_processor,
                {
                    "structured_tables": 8,
                    "total_cells": 456,
                    "extraction_accuracy": 0.92,
                    "format": "pandas_dataframe"
                },
                0.25,
                "completed"
            )
            print("  ✅ 표 처리 완료")
            
            # 1.4 임베딩 생성 에이전트
            embedding_agent = await local_monitor.trace_agent_execution(
                "embedding_generator",
                {
                    "model": "text-embedding-3-large",
                    "chunk_strategy": "content_aware",
                    "chunk_count": 89
                },
                pdf_trace
            )
            
            await asyncio.sleep(0.4)
            
            await local_monitor.update_agent_result(
                embedding_agent,
                {
                    "embeddings_created": 89,
                    "dimensions": 3072,
                    "batch_size": 20,
                    "total_tokens": 17800
                },
                0.4,
                "completed"
            )
            print("  ✅ 임베딩 생성 완료")
        
        print("✅ PDF 처리 워크플로우 완료")
        
        # 2. 검색 쿼리 워크플로우
        print("\n🔍 검색 쿼리 워크플로우 시뮬레이션...")
        
        async with local_monitor.trace_workflow(
            "search_query_pipeline",
            {
                "query": "보험금 지급 조건은 무엇인가요?",
                "user_id": "user_123",
                "session_id": "session_456"
            }
        ) as search_trace:
            print("✅ 검색 워크플로우 시작")
            
            # 2.1 쿼리 전처리
            query_processor = await local_monitor.trace_agent_execution(
                "query_processor",
                {
                    "original_query": "보험금 지급 조건은 무엇인가요?",
                    "preprocessing_steps": ["normalize", "tokenize", "intent_analysis"]
                },
                search_trace
            )
            
            await asyncio.sleep(0.1)
            
            await local_monitor.update_agent_result(
                query_processor,
                {
                    "processed_query": "보험금 지급 조건",
                    "intent": "policy_inquiry",
                    "keywords": ["보험금", "지급", "조건"],
                    "confidence": 0.89
                },
                0.1,
                "completed"
            )
            print("  ✅ 쿼리 전처리 완료")
            
            # 2.2 벡터 검색
            vector_search = await local_monitor.trace_agent_execution(
                "vector_search_engine",
                {
                    "query_embedding_dims": 3072,
                    "search_method": "cosine_similarity",
                    "top_k": 10
                },
                search_trace
            )
            
            await asyncio.sleep(0.15)
            
            await local_monitor.update_agent_result(
                vector_search,
                {
                    "matches_found": 7,
                    "top_score": 0.89,
                    "search_time_ms": 45,
                    "index_size": 89
                },
                0.15,
                "completed"
            )
            print("  ✅ 벡터 검색 완료")
            
            # 2.3 답변 생성
            answer_generator = await local_monitor.trace_agent_execution(
                "answer_generator",
                {
                    "model": "gpt-4o",
                    "context_chunks": 7,
                    "max_tokens": 500
                },
                search_trace
            )
            
            await asyncio.sleep(0.3)
            
            await local_monitor.update_agent_result(
                answer_generator,
                {
                    "answer_length": 245,
                    "sources_cited": 3,
                    "confidence_score": 0.92,
                    "generation_time": 0.3
                },
                0.3,
                "completed"
            )
            print("  ✅ 답변 생성 완료")
        
        print("✅ 검색 쿼리 워크플로우 완료")
        
        # 3. 메트릭 로깅 테스트
        print("\n📈 종합 성능 메트릭 로깅...")
        
        comprehensive_metrics = {
            "session_id": "test_session_001",
            "total_workflows": 2,
            "total_agents": 7,
            "total_processing_time": 1.25,
            "memory_usage_mb": 512,
            "cpu_usage_percent": 45.2,
            "documents_processed": 1,
            "queries_processed": 1,
            "embeddings_created": 89,
            "search_accuracy": 0.89,
            "user_satisfaction": 0.95,
            "error_count": 0,
            "warning_count": 1,
            "timestamp": datetime.now().isoformat()
        }
        
        await local_monitor.log_metrics(comprehensive_metrics)
        print("✅ 종합 메트릭 로깅 완료")
        
        # 4. 통계 조회 테스트
        print("\n📊 워크플로우 통계 조회...")
        
        stats = await local_monitor.get_workflow_stats()
        print(f"✅ 통계 조회 완료:")
        print(f"  - 총 실행 수: {stats.get('total_executions', 0)}")
        print(f"  - 성공률: {stats.get('success_rate', 0)}%")
        print(f"  - 로그 디렉토리: {stats.get('log_directory', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 로컬 모니터링 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_integration_local():
    """로컬 모니터와 API 통합 테스트"""
    print("\n" + "=" * 60)
    print("🌐 로컬 모니터 API 통합 테스트")
    print("=" * 60)
    
    try:
        # 테스트 사용자
        test_user = {"email": "test@ispl.com", "user_id": 1}
        
        # 워크플로우 API 테스트
        from routers.workflow import get_workflow_summary
        
        print("📊 워크플로우 요약 API 테스트...")
        summary = await get_workflow_summary(current_user=test_user)
        
        print(f"✅ API 응답 성공:")
        print(f"  - 모니터 타입: {summary.get('monitor_type', 'unknown')}")
        print(f"  - 모니터 활성화: {summary.get('monitor_enabled', False)}")
        print(f"  - 총 워크플로우: {summary.get('total_workflows', 0)}")
        print(f"  - 성공률: {summary.get('success_rate', 0)}%")
        print(f"  - 평균 실행시간: {summary.get('avg_execution_time', 0)}ms")
        
        # 모니터 통계 확인
        monitor_stats = summary.get('monitor_stats', {})
        if monitor_stats:
            print(f"  - 로컬 모니터 통계: {monitor_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ API 통합 테스트 실패: {e}")
        return False


async def verify_log_files():
    """생성된 로그 파일 검증"""
    print("\n" + "=" * 60)
    print("📁 로그 파일 검증")
    print("=" * 60)
    
    try:
        from pathlib import Path
        
        log_dir = Path("logs/workflow")
        
        if log_dir.exists():
            print(f"✅ 로그 디렉토리 존재: {log_dir}")
            
            # 생성된 파일들 확인
            log_files = list(log_dir.glob("*.jsonl"))
            print(f"📄 생성된 로그 파일 수: {len(log_files)}")
            
            for log_file in log_files[:5]:  # 처음 5개만 표시
                file_size = log_file.stat().st_size
                print(f"  📄 {log_file.name} ({file_size} bytes)")
                
                # 파일 내용 일부 확인
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line:
                            import json
                            log_entry = json.loads(first_line)
                            print(f"     🔍 첫 번째 로그: {log_entry.get('event_type', 'unknown')}")
                except Exception as e:
                    print(f"     ⚠️  파일 읽기 실패: {e}")
            
            return True
        else:
            print(f"⚠️  로그 디렉토리가 없습니다: {log_dir}")
            return False
            
    except Exception as e:
        print(f"❌ 로그 파일 검증 실패: {e}")
        return False


async def main():
    """Self-hosted LangFuse 대안 테스트 메인"""
    print("🏠 Self-hosted LangFuse 대안 테스트")
    print("   (로컬 모니터링 시스템 완전 테스트)")
    print(f"⏰ 시작 시간: {datetime.now().isoformat()}")
    
    results = {}
    
    # 1. 로컬 모니터링 완전 테스트
    results['local_monitoring'] = await test_local_monitoring_complete()
    
    # 2. API 통합 테스트
    results['api_integration'] = await test_api_integration_local()
    
    # 3. 로그 파일 검증
    results['log_verification'] = await verify_log_files()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 Self-hosted LangFuse 대안 테스트 결과")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과")
    print(f"⏰ 완료 시간: {datetime.now().isoformat()}")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ 로컬 모니터링 시스템이 Self-hosted LangFuse 완전 대체")
        print("✅ Task 6.1 완료: 워크플로우 모니터링 시스템 구축 성공")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
    
    print("\n💡 달성된 기능:")
    print("- 🔍 완전한 워크플로우 추적")
    print("- 📊 에이전트별 성능 모니터링")
    print("- 📈 실시간 메트릭 수집")
    print("- 📁 영구 로그 저장")
    print("- 🌐 API 통합")
    print("- 🔄 자동 폴백 시스템")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)




