"""
Task 4.1: 보안 등급별 임베딩 모델 관리 시스템 테스트
다중 모델 임베딩 에이전트의 기능을 검증합니다.
"""
import asyncio
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

from services.multi_model_embedding import (
    MultiModelEmbeddingAgent, 
    SecurityLevel, 
    EmbeddingModelType,
    EmbeddingModelRegistry
)
from agents.base import DocumentProcessingState, ProcessingStatus

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

class MultiModelEmbeddingReport:
    """다중 모델 임베딩 테스트 보고서"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_data = {
            "metadata": {
                "timestamp": self.timestamp,
                "test_type": "multi_model_embedding_analysis"
            },
            "security_level_tests": {},
            "model_compatibility_tests": {},
            "cost_estimation_tests": {},
            "overall_status": "FAILED",
            "error_message": None
        }
        self.console_output = []

    def log_console(self, message: str):
        """콘솔 출력을 로그에 저장"""
        self.console_output.append(message)
        print(message)

    def add_security_level_test(self, security_level: str, result: Dict[str, Any]):
        """보안 등급별 테스트 결과 추가"""
        self.report_data["security_level_tests"][security_level] = result

    def add_model_compatibility_test(self, model_type: str, result: Dict[str, Any]):
        """모델 호환성 테스트 결과 추가"""
        self.report_data["model_compatibility_tests"][model_type] = result

    def add_cost_estimation_test(self, result: Dict[str, Any]):
        """비용 계산 테스트 결과 추가"""
        self.report_data["cost_estimation_tests"] = result

    def set_overall_status(self, status: str, error_message: str = None):
        """전체 상태 설정"""
        self.report_data["overall_status"] = status
        self.report_data["error_message"] = error_message

    def save_reports(self):
        """보고서 저장"""
        reports_dir = Path("reports/multi_model_embedding")
        reports_dir.mkdir(parents=True, exist_ok=True)

        base_filename = f"multi_model_embedding_report_{self.timestamp}"

        # JSON 보고서
        json_file = reports_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)

        # 텍스트 요약
        txt_file = reports_dir / f"{base_filename}_summary.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("다중 모델 임베딩 시스템 테스트 보고서\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"🕐 테스트 시간: {self.timestamp}\n")
            f.write(f"✅ 전체 상태: {self.report_data['overall_status']}\n\n")

            f.write("📊 보안 등급별 테스트 결과:\n")
            for level, result in self.report_data["security_level_tests"].items():
                status = "✅" if result.get("success", False) else "❌"
                f.write(f"   {status} {level}: {result.get('message', 'N/A')}\n")
            f.write("\n")

            f.write("🔧 모델 호환성 테스트 결과:\n")
            for model, result in self.report_data["model_compatibility_tests"].items():
                status = "✅" if result.get("success", False) else "❌"
                f.write(f"   {status} {model}: {result.get('message', 'N/A')}\n")
            f.write("\n")

            if self.report_data["cost_estimation_tests"]:
                f.write("💰 비용 계산 테스트:\n")
                cost_tests = self.report_data["cost_estimation_tests"]
                for model, cost_info in cost_tests.items():
                    f.write(f"   - {model}: ${cost_info:.6f}\n")
            f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("콘솔 출력 로그:\n")
            f.write("=" * 80 + "\n")
            for line in self.console_output:
                f.write(line + "\n")

        return {"json_report": str(json_file), "txt_summary": str(txt_file)}

def create_sample_chunks() -> List[Dict[str, Any]]:
    """테스트용 샘플 청크 생성"""
    return [
        {
            "text": "보험약관 제1조 (목적) 이 약관은 보험회사와 보험계약자 간의 권리와 의무를 규정함을 목적으로 합니다.",
            "metadata": {
                "chunk_index": 0,
                "page_number": 1,
                "source": "text_extraction"
            }
        },
        {
            "text": "제2조 (정의) 이 약관에서 사용하는 용어의 정의는 다음과 같습니다. 1. 보험계약자: 보험회사와 보험계약을 체결하는 자",
            "metadata": {
                "chunk_index": 1,
                "page_number": 1,
                "source": "text_extraction"
            }
        },
        {
            "text": "제3조 (보상 한도) 보험금 지급 한도는 보험가입금액을 한도로 하며, 보험사고 발생 시 약관에서 정한 기준에 따라 지급합니다.",
            "metadata": {
                "chunk_index": 2,
                "page_number": 2,
                "source": "text_extraction"
            }
        }
    ]

async def test_security_level_model_selection():
    """보안 등급별 모델 자동 선택 테스트"""
    logger.info("=" * 60)
    logger.info("보안 등급별 모델 자동 선택 테스트 시작")
    logger.info("=" * 60)
    
    report = MultiModelEmbeddingReport()
    
    # 각 보안 등급별 테스트
    security_levels = [SecurityLevel.PUBLIC, SecurityLevel.RESTRICTED, SecurityLevel.CLOSED]
    
    for security_level in security_levels:
        try:
            report.log_console(f"\n🔒 보안 등급: {security_level.value}")
            
            # 자동 모델 선택
            agent = MultiModelEmbeddingAgent.create_from_security_level(security_level)
            model_info = agent.get_model_info()
            
            report.log_console(f"   선택된 모델: {model_info['model_name']}")
            report.log_console(f"   임베딩 차원: {model_info['dimensions']}")
            report.log_console(f"   테이블명: {model_info['table_name']}")
            report.log_console(f"   API 타입: {model_info['api_type']}")
            
            # 사용 가능한 모델 목록 확인
            available_models = MultiModelEmbeddingAgent.get_available_models(security_level)
            report.log_console(f"   사용 가능한 모델 수: {len(available_models)}")
            
            # 성공 기록
            report.add_security_level_test(security_level.value, {
                "success": True,
                "selected_model": model_info['model_name'],
                "dimensions": model_info['dimensions'],
                "table_name": model_info['table_name'],
                "api_type": model_info['api_type'],
                "available_models_count": len(available_models),
                "message": f"모델 선택 성공: {model_info['model_name']}"
            })
            
        except Exception as e:
            error_msg = f"보안 등급 {security_level.value} 테스트 실패: {str(e)}"
            report.log_console(f"   ❌ {error_msg}")
            report.add_security_level_test(security_level.value, {
                "success": False,
                "error": str(e),
                "message": error_msg
            })
    
    return report

async def test_model_compatibility():
    """모델 호환성 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("모델 호환성 및 차원 수 검증 테스트")
    logger.info("=" * 60)
    
    report = MultiModelEmbeddingReport()
    
    # 각 모델 타입별 테스트
    model_types = [
        EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_LARGE,
        EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_SMALL,
        EmbeddingModelType.QWEN_8B_EMBED
    ]
    
    for model_type in model_types:
        try:
            report.log_console(f"\n🤖 모델: {model_type.value}")
            
            # 모델 설정 확인
            config = EmbeddingModelRegistry.get_model_config(model_type)
            report.log_console(f"   설정된 차원: {config.dimensions}")
            report.log_console(f"   테이블명: {config.table_name}")
            report.log_console(f"   비용 (1K 토큰): ${config.cost_per_1k_tokens}")
            report.log_console(f"   최대 토큰: {config.max_tokens}")
            
            # 에이전트 생성 테스트
            agent = MultiModelEmbeddingAgent(model_type=model_type)
            
            # 차원 수 검증
            expected_dimensions = config.dimensions
            actual_dimensions = agent.get_embedding_dimension()
            dimensions_match = expected_dimensions == actual_dimensions
            
            # 테이블명 검증
            expected_table = config.table_name
            actual_table = agent.get_table_name()
            table_match = expected_table == actual_table
            
            report.log_console(f"   차원 수 일치: {dimensions_match} (기대: {expected_dimensions}, 실제: {actual_dimensions})")
            report.log_console(f"   테이블명 일치: {table_match} (기대: {expected_table}, 실제: {actual_table})")
            
            # 성공 기록
            success = dimensions_match and table_match
            report.add_model_compatibility_test(model_type.value, {
                "success": success,
                "expected_dimensions": expected_dimensions,
                "actual_dimensions": actual_dimensions,
                "dimensions_match": dimensions_match,
                "expected_table": expected_table,
                "actual_table": actual_table,
                "table_match": table_match,
                "message": "호환성 검증 완료" if success else "호환성 검증 실패"
            })
            
        except Exception as e:
            error_msg = f"모델 {model_type.value} 호환성 테스트 실패: {str(e)}"
            report.log_console(f"   ❌ {error_msg}")
            report.add_model_compatibility_test(model_type.value, {
                "success": False,
                "error": str(e),
                "message": error_msg
            })
    
    return report

async def test_cost_estimation():
    """비용 계산 정확성 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("모델별 비용 계산 정확성 테스트")
    logger.info("=" * 60)
    
    report = MultiModelEmbeddingReport()
    
    # 테스트 데이터
    test_tokens = 10000  # 10K 토큰
    
    cost_results = {}
    
    # 각 모델별 비용 계산
    model_types = [
        EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_LARGE,
        EmbeddingModelType.OPENAI_TEXT_EMBEDDING_3_SMALL,
        EmbeddingModelType.QWEN_8B_EMBED
    ]
    
    for model_type in model_types:
        try:
            agent = MultiModelEmbeddingAgent(model_type=model_type)
            
            # 비용 계산
            estimated_cost = agent.estimate_cost(test_tokens)
            config = EmbeddingModelRegistry.get_model_config(model_type)
            expected_cost = (test_tokens / 1000) * config.cost_per_1k_tokens
            
            cost_results[model_type.value] = estimated_cost
            
            report.log_console(f"📊 {model_type.value}:")
            report.log_console(f"   예상 비용: ${estimated_cost:.6f}")
            report.log_console(f"   기대 비용: ${expected_cost:.6f}")
            report.log_console(f"   일치 여부: {abs(estimated_cost - expected_cost) < 0.000001}")
            
        except Exception as e:
            report.log_console(f"❌ {model_type.value} 비용 계산 실패: {str(e)}")
            cost_results[model_type.value] = f"ERROR: {str(e)}"
    
    report.add_cost_estimation_test(cost_results)
    return report

async def test_embedding_creation():
    """실제 임베딩 생성 테스트 (OpenAI 모델만)"""
    logger.info("\n" + "=" * 60)
    logger.info("실제 임베딩 생성 테스트 (OpenAI 모델)")
    logger.info("=" * 60)
    
    report = MultiModelEmbeddingReport()
    
    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        report.log_console("⚠️ OPENAI_API_KEY가 설정되지 않음, 임베딩 생성 테스트 건너뛰기")
        return report
    
    try:
        # PublicLlevel 에이전트 생성
        agent = MultiModelEmbeddingAgent.create_from_security_level(SecurityLevel.PUBLIC)
        
        # 테스트용 상태 생성
        initial_state: DocumentProcessingState = {
            "file_path": "test_policy.pdf",
            "policy_id": 999,
            "file_name": "test_policy.pdf",
            "current_step": "embedding_test",
            "status": ProcessingStatus.PENDING.value,
            "error_message": None,
            "processed_chunks": create_sample_chunks(),
            "total_chunks": 3,
            "extracted_images": [],
            "document_structure": [],
            "markdown_content": "",
            "converted_markdown_path": "",
            "extracted_images_for_markdown": []
        }
        
        report.log_console(f"🚀 임베딩 생성 시작: {len(initial_state['processed_chunks'])}개 청크")
        report.log_console(f"   모델: {agent.get_model_info()['model_name']}")
        
        # 임베딩 생성 실행
        final_state = await agent.process(initial_state)
        
        # 결과 검증
        success = final_state["status"] == ProcessingStatus.COMPLETED.value
        embeddings_created = final_state.get("embeddings_created", False)
        
        if success and embeddings_created:
            # 임베딩 검증
            embedded_chunks = [
                chunk for chunk in final_state["processed_chunks"]
                if chunk.get("embedding") and len(chunk["embedding"]) > 0
            ]
            
            expected_dimension = agent.get_embedding_dimension()
            actual_dimensions = [len(chunk["embedding"]) for chunk in embedded_chunks]
            dimensions_correct = all(dim == expected_dimension for dim in actual_dimensions)
            
            report.log_console(f"✅ 임베딩 생성 성공!")
            report.log_console(f"   임베딩된 청크 수: {len(embedded_chunks)}")
            report.log_console(f"   예상 차원: {expected_dimension}")
            report.log_console(f"   실제 차원: {actual_dimensions}")
            report.log_console(f"   차원 일치: {dimensions_correct}")
            
        else:
            report.log_console(f"❌ 임베딩 생성 실패: {final_state.get('error_message', '알 수 없는 오류')}")
            
    except Exception as e:
        error_msg = f"임베딩 생성 테스트 중 오류: {str(e)}"
        report.log_console(f"❌ {error_msg}")
    
    return report

async def main():
    """메인 테스트 함수"""
    logger.info("=" * 80)
    logger.info("Task 4.1: 보안 등급별 임베딩 모델 관리 시스템 테스트 시작")
    logger.info("=" * 80)
    
    # 전체 보고서 생성
    overall_report = MultiModelEmbeddingReport()
    
    try:
        # 1. 보안 등급별 모델 선택 테스트
        security_report = await test_security_level_model_selection()
        overall_report.report_data["security_level_tests"] = security_report.report_data["security_level_tests"]
        overall_report.console_output.extend(security_report.console_output)
        
        # 2. 모델 호환성 테스트
        compatibility_report = await test_model_compatibility()
        overall_report.report_data["model_compatibility_tests"] = compatibility_report.report_data["model_compatibility_tests"]
        overall_report.console_output.extend(compatibility_report.console_output)
        
        # 3. 비용 계산 테스트
        cost_report = await test_cost_estimation()
        overall_report.report_data["cost_estimation_tests"] = cost_report.report_data["cost_estimation_tests"]
        overall_report.console_output.extend(cost_report.console_output)
        
        # 4. 실제 임베딩 생성 테스트 (선택적)
        embedding_report = await test_embedding_creation()
        overall_report.console_output.extend(embedding_report.console_output)
        
        # 전체 결과 평가
        security_success = all(
            test.get("success", False) 
            for test in overall_report.report_data["security_level_tests"].values()
        )
        compatibility_success = all(
            test.get("success", False) 
            for test in overall_report.report_data["model_compatibility_tests"].values()
        )
        
        overall_success = security_success and compatibility_success
        
        overall_report.log_console("\n" + "=" * 80)
        overall_report.log_console("테스트 결과 요약")
        overall_report.log_console("=" * 80)
        overall_report.log_console(f"보안 등급별 테스트: {'✅ 성공' if security_success else '❌ 실패'}")
        overall_report.log_console(f"모델 호환성 테스트: {'✅ 성공' if compatibility_success else '❌ 실패'}")
        overall_report.log_console(f"전체 테스트: {'✅ 성공' if overall_success else '❌ 실패'}")
        
        overall_report.set_overall_status("SUCCESS" if overall_success else "FAILED")
        
        # 보고서 저장
        overall_report.log_console("\n💾 보고서 저장 중...")
        saved_files = overall_report.save_reports()
        overall_report.log_console("✅ 보고서 저장 완료!")
        overall_report.log_console(f"   - JSON 보고서: {saved_files['json_report']}")
        overall_report.log_console(f"   - TXT 요약: {saved_files['txt_summary']}")
        
    except Exception as e:
        error_msg = f"테스트 실행 중 예외 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)
        overall_report.log_console(f"❌ {error_msg}")
        overall_report.set_overall_status("FAILED", error_msg)
        overall_report.save_reports()

    logger.info("\n" + "=" * 80)
    logger.info("Task 4.1 테스트 완료")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())

