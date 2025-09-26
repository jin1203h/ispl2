"""
Task 3.5 Markdown 변환 및 구조 보존 테스트
"""
import asyncio
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

from agents.markdown_processor import MarkdownProcessorAgent
from agents.base import DocumentProcessingState, ProcessingStatus

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

class MarkdownProcessingReport:
    """Markdown 변환 처리 결과 보고서"""

    def __init__(self, test_pdf_path: str):
        self.test_pdf_path = test_pdf_path
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_data = {
            "metadata": {
                "test_file": test_pdf_path,
                "timestamp": self.timestamp,
                "test_type": "markdown_conversion_analysis"
            },
            "pdf_info": {},
            "conversion_stats": {},
            "quality_validation": {},
            "output_files": {},
            "overall_status": "FAILED",
            "error_message": None
        }
        self.console_output = []

    def log_console(self, message: str):
        """콘솔 출력을 로그에 저장"""
        self.console_output.append(message)
        print(message)

    def set_pdf_info(self, total_pages: int, file_size: str):
        """PDF 기본 정보 설정"""
        self.report_data["pdf_info"] = {
            "total_pages": total_pages,
            "file_size": file_size,
            "file_exists": os.path.exists(self.test_pdf_path)
        }

    def set_conversion_stats(self, stats: Dict[str, Any]):
        """변환 통계 설정"""
        self.report_data["conversion_stats"] = stats

    def set_quality_validation(self, validation: Dict[str, Any]):
        """품질 검증 결과 설정"""
        self.report_data["quality_validation"] = validation

    def set_output_files(self, output_info: Dict[str, Any]):
        """출력 파일 정보 설정"""
        self.report_data["output_files"] = output_info

    def set_overall_status(self, status: ProcessingStatus, error_message: str = None):
        """전체 처리 상태 설정"""
        self.report_data["overall_status"] = status.value
        self.report_data["error_message"] = error_message

    def save_reports(self):
        """보고서들을 파일로 저장"""
        reports_dir = Path("reports/markdown_conversion")
        reports_dir.mkdir(parents=True, exist_ok=True)

        base_filename = f"markdown_conversion_report_{self.timestamp}"

        # 1. JSON 상세 보고서 저장
        json_file = reports_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            def json_serializable(obj):
                """JSON 직렬화 가능한 형태로 변환"""
                if hasattr(obj, 'value'):  # Enum 객체
                    return obj.value
                if isinstance(obj, dict):
                    return {k: json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [json_serializable(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    return json_serializable(obj.__dict__)
                elif obj is None or (hasattr(obj, '__ne__') and obj != obj):  # NaN 체크
                    return None
                else:
                    try:
                        json.dumps(obj)  # 직렬화 가능한지 테스트
                        return obj
                    except (TypeError, ValueError):
                        return str(obj)

            serializable_data = json_serializable(self.report_data)
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

        # 2. 텍스트 요약 보고서 저장
        txt_file = reports_dir / f"{base_filename}_summary.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("Markdown 변환 및 구조 보존 테스트 보고서\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"📄 테스트 파일: {self.test_pdf_path}\n")
            f.write(f"🕐 테스트 시간: {self.timestamp}\n")
            f.write(f"✅ 전체 상태: {self.report_data['overall_status']}\n")
            if self.report_data['error_message']:
                f.write(f"❌ 오류 메시지: {self.report_data['error_message']}\n")
            f.write("\n")

            f.write("📖 PDF 기본 정보:\n")
            for k, v in self.report_data["pdf_info"].items():
                f.write(f"   - {k}: {v}\n")
            f.write("\n")

            f.write("📊 변환 통계:\n")
            for k, v in self.report_data["conversion_stats"].items():
                f.write(f"   - {k}: {v}\n")
            f.write("\n")

            f.write("🔍 품질 검증 결과:\n")
            quality = self.report_data["quality_validation"]
            if quality:
                f.write(f"   - 전체 통과: {quality.get('overall_passed', False)}\n")
                f.write(f"   - 점수: {quality.get('score', 0):.1f}점\n")
                if quality.get('issues'):
                    f.write("   - 문제점:\n")
                    for issue in quality['issues']:
                        f.write(f"     * {issue}\n")
                
                f.write("   - 세부 결과:\n")
                for test_name, result in quality.get('detailed_results', {}).items():
                    status = "✅" if result['passed'] else "❌"
                    f.write(f"     {status} {result['description']}: {result['score']}\n")
            f.write("\n")

            f.write("📁 출력 파일:\n")
            for k, v in self.report_data["output_files"].items():
                f.write(f"   - {k}: {v}\n")
            f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("콘솔 출력 로그:\n")
            f.write("=" * 80 + "\n")
            for line in self.console_output:
                f.write(line + "\n")

        # 3. 콘솔 로그 파일 저장
        log_file = reports_dir / f"{base_filename}_console.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            for line in self.console_output:
                f.write(line + "\n")

        return {"json_report": str(json_file), "txt_summary": str(txt_file), "console_log": str(log_file)}

def create_sample_processed_chunks() -> List[Dict[str, Any]]:
    """테스트용 샘플 처리된 청크 생성"""
    return [
        {
            "text": "보험약관 제1장 총칙",
            "metadata": {
                "chunk_index": 0,
                "page_number": 1,
                "chunk_type": "text",
                "source": "text_extraction",
                "font_size": 16,
                "bbox": [100, 700, 400, 720]
            }
        },
        {
            "text": "제1조 (목적) 이 약관은 보험회사와 보험계약자 간의 권리와 의무를 규정함을 목적으로 합니다.",
            "metadata": {
                "chunk_index": 1,
                "page_number": 1,
                "chunk_type": "text",
                "source": "text_extraction",
                "font_size": 12,
                "bbox": [100, 650, 500, 680]
            }
        },
        {
            "text": "제2조 (정의) 이 약관에서 사용하는 용어의 정의는 다음과 같습니다.\n1. 보험계약자: 보험회사와 보험계약을 체결하는 자\n2. 피보험자: 보험사고의 대상이 되는 자",
            "metadata": {
                "chunk_index": 2,
                "page_number": 1,
                "chunk_type": "text",
                "source": "text_extraction",
                "font_size": 12,
                "bbox": [100, 580, 500, 640]
            }
        },
        {
            "text": "",
            "metadata": {
                "chunk_index": 3,
                "page_number": 2,
                "chunk_type": "table",
                "source": "table_extraction",
                "table_data": [
                    ["구분", "보장내용", "보험금액"],
                    ["상해사망", "상해로 인한 사망 시", "1억원"],
                    ["상해후유장해", "상해로 인한 후유장해 시", "장해정도에 따라"],
                    ["질병사망", "질병으로 인한 사망 시", "5천만원"]
                ]
            }
        },
        {
            "text": "보험 가입 절차 안내 이미지",
            "metadata": {
                "chunk_index": 4,
                "page_number": 3,
                "chunk_type": "image",
                "source": "image_extraction",
                "image_index": 0,
                "image_analysis": {
                    "quality": "good",
                    "image_type": "diagram",
                    "confidence": 0.85
                },
                "image_data": b"dummy_image_data"
            }
        },
        {
            "text": "* 주의사항: 보험료 납입이 연체될 경우 보험계약이 해지될 수 있습니다.",
            "metadata": {
                "chunk_index": 5,
                "page_number": 3,
                "chunk_type": "text",
                "source": "text_extraction",
                "font_size": 10,
                "bbox": [100, 200, 450, 220]
            }
        }
    ]

async def test_markdown_conversion():
    """Task 3.5 Markdown 변환 및 구조 보존 테스트"""
    logger.info("=" * 60)
    logger.info("Task 3.5: Markdown 변환 및 구조 보존 테스트 시작")
    logger.info("=" * 60)

    test_pdf_path = "uploads/pdf/test_policy.pdf"
    report = MarkdownProcessingReport(test_pdf_path)
    report.log_console("📄 테스트 대상: " + test_pdf_path)

    # PDF 정보 설정 (실제 파일이 없어도 테스트 진행)
    if os.path.exists(test_pdf_path):
        file_size_mb = os.path.getsize(test_pdf_path) / (1024 * 1024)
        report.set_pdf_info(10, f"{file_size_mb:.2f} MB")
        report.log_console(f"📖 파일 크기: {file_size_mb:.2f} MB")
    else:
        report.set_pdf_info(10, "샘플 데이터")
        report.log_console("📖 샘플 데이터로 테스트 진행")

    # 테스트용 샘플 데이터 생성
    sample_chunks = create_sample_processed_chunks()
    report.log_console(f"📦 테스트 청크 생성: {len(sample_chunks)}개")

    initial_state: DocumentProcessingState = {
        "file_path": test_pdf_path,
        "policy_id": 1,
        "file_name": os.path.basename(test_pdf_path),
        "current_step": "markdown_conversion",
        "status": ProcessingStatus.PENDING.value,
        "error_message": None,
        "processed_chunks": sample_chunks,
        "total_chunks": len(sample_chunks),
        "pdf_analysis": {
            "total_pages": 3,
            "document_type": "insurance_policy",
            "quality_score": 85.5,
            "processing_strategy": "standard"
        },
        "text_processing_stats": {
            "total_words": 150,
            "total_articles": 2
        }
    }

    agent = MarkdownProcessorAgent()

    try:
        report.log_console("\n🔄 Markdown 변환 에이전트 실행 중...")
        final_state = await agent.process(initial_state)

        # 결과 분석
        status = ProcessingStatus(final_state["status"])
        report.set_overall_status(status, final_state.get("error_message"))

        if "markdown_processing_stats" in final_state:
            report.set_conversion_stats(final_state["markdown_processing_stats"])

        if "quality_validation" in final_state:
            report.set_quality_validation(final_state["quality_validation"])

        # 출력 파일 정보
        output_info = {
            "markdown_file": final_state.get("markdown_file_path"),
            "markdown_length": len(final_state.get("markdown_content", "")),
            "extracted_images": len(final_state.get("extracted_images", []))
        }
        report.set_output_files(output_info)

        # 결과 요약 출력
        summary = agent.get_conversion_summary(final_state)
        
        report.log_console("\n" + "=" * 60)
        report.log_console("테스트 결과 요약")
        report.log_console("=" * 60)
        report.log_console(f"변환 상태: {summary.get('conversion_status')}")
        report.log_console(f"변환된 청크 수: {summary.get('total_chunks_converted')}")
        report.log_console(f"Markdown 길이: {summary.get('markdown_length')} 문자")
        report.log_console(f"추출된 이미지: {summary.get('extracted_images_count')}개")
        report.log_console(f"처리 시간: {summary.get('processing_time')}")

        report.log_console("\n📊 품질 메트릭:")
        quality_metrics = summary.get('quality_metrics', {})
        for metric, value in quality_metrics.items():
            report.log_console(f"   - {metric}: {value}")

        report.log_console("\n🔍 품질 검증:")
        quality_validation = summary.get('quality_validation', {})
        report.log_console(f"   - 전체 통과: {quality_validation.get('전체 통과')}")
        report.log_console(f"   - 점수: {quality_validation.get('점수')}")
        
        issues = quality_validation.get('문제점', [])
        if issues:
            report.log_console("   - 문제점:")
            for issue in issues:
                report.log_console(f"     * {issue}")

        # Markdown 내용 미리보기
        if final_state.get("markdown_content"):
            markdown_preview = final_state["markdown_content"][:500]
            report.log_console(f"\n📝 Markdown 미리보기 (처음 500자):")
            report.log_console("-" * 40)
            report.log_console(markdown_preview)
            if len(final_state["markdown_content"]) > 500:
                report.log_console("...")
            report.log_console("-" * 40)

        # 보고서 저장
        report.log_console("\n💾 보고서 저장 중...")
        saved_files = report.save_reports()
        report.log_console("✅ 보고서 저장 완료!")
        report.log_console(f"   - JSON 상세 보고서: {saved_files['json_report']}")
        report.log_console(f"   - TXT 요약 보고서: {saved_files['txt_summary']}")
        report.log_console(f"   - 콘솔 로그: {saved_files['console_log']}")

    except Exception as e:
        error_msg = f"테스트 실행 중 예외 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)
        report.log_console(f"❌ {error_msg}")
        report.set_overall_status(ProcessingStatus.FAILED, error_msg)
        report.save_reports()

    logger.info("\n" + "=" * 60)
    logger.info("Task 3.5 테스트 완료")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_markdown_conversion())

