"""
Markdown 변환 처리 에이전트
PDF 처리 결과를 구조화된 Markdown 형식으로 변환
"""
import time
import logging
from typing import Dict, Any, List, Optional

from agents.base import BaseAgent, DocumentProcessingState, ProcessingStatus
from services.markdown_service import MarkdownConverter

logger = logging.getLogger(__name__)

class MarkdownProcessorAgent(BaseAgent):
    """Markdown 변환 처리 에이전트"""

    def __init__(self):
        super().__init__(
            name="markdown_processor",
            description="PDF에서 추출된 데이터를 구조화된 Markdown 형식으로 변환하고 원본 구조를 보존합니다"
        )
        
        # Markdown 변환기 초기화
        self.markdown_converter = MarkdownConverter()
        
        # 변환 옵션
        self.conversion_options = {
            "include_toc": True,
            "include_metadata": True,
            "extract_images": True,
            "preserve_structure": True
        }

    async def process(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Markdown 변환 처리"""
        self.log_step(state, "Markdown 변환 및 구조 보존 시작")

        try:
            start_time = time.time()
            
            # 1. 필수 데이터 확인
            processed_chunks = state.get("processed_chunks", [])
            if not processed_chunks:
                error_msg = "변환할 처리된 청크가 없습니다"
                self.log_step(state, error_msg, "error")
                return self.update_status(state, ProcessingStatus.FAILED, "markdown_conversion", error_msg)
            
            # 2. 문서 메타데이터 준비
            document_metadata = self._prepare_document_metadata(state)
            
            # 3. Markdown 변환 수행
            self.log_step(state, f"{len(processed_chunks)}개 청크를 Markdown으로 변환 중...")
            
            markdown_content = self.markdown_converter.convert_to_markdown(
                processed_chunks=processed_chunks,
                document_metadata=document_metadata,
                include_toc=self.conversion_options["include_toc"],
                include_metadata=self.conversion_options["include_metadata"]
            )
            
            # 4. 변환 결과 저장
            output_path = self._generate_output_path(state)
            save_result = self.markdown_converter.save_markdown_to_file(
                markdown_content=markdown_content,
                output_path=output_path,
                extract_images=self.conversion_options["extract_images"],
                processed_chunks=processed_chunks
            )
            
            # 5. 변환 보고서 생성
            structure = self.markdown_converter.structure_analyzer.analyze_document_structure(processed_chunks)
            conversion_report = self.markdown_converter.generate_conversion_report(structure, save_result)
            
            # 6. 품질 검증
            quality_results = self._validate_conversion_quality(conversion_report)
            
            # 7. 상태 업데이트
            processing_time = time.time() - start_time
            
            state["markdown_content"] = markdown_content
            state["markdown_file_path"] = save_result["markdown_file"]
            state["extracted_images"] = save_result["extracted_images"]
            state["conversion_report"] = conversion_report
            state["quality_validation"] = quality_results
            state["markdown_processing_stats"] = {
                "total_chunks_converted": len(processed_chunks),
                "markdown_length": len(markdown_content),
                "extracted_images_count": len(save_result["extracted_images"]),
                "processing_time": processing_time,
                "structure_preservation_rate": conversion_report["quality_metrics"]["structure_preservation_rate"],
                "readability_score": conversion_report["quality_metrics"]["readability_score"],
                "metadata_completeness": conversion_report["quality_metrics"]["metadata_completeness"]
            }

            self.log_step(
                state,
                f"Markdown 변환 완료: {len(markdown_content)}자, "
                f"{len(save_result['extracted_images'])}개 이미지 추출, "
                f"구조 보존율: {conversion_report['quality_metrics']['structure_preservation_rate']:.1f}%, "
                f"처리시간: {processing_time:.2f}초"
            )

            return self.update_status(state, ProcessingStatus.COMPLETED, "markdown_conversion")

        except Exception as e:
            error_msg = f"Markdown 변환 중 오류 발생: {str(e)}"
            self.log_step(state, error_msg, "error")
            logger.error(error_msg, exc_info=True)
            return self.update_status(
                state,
                ProcessingStatus.FAILED,
                "markdown_conversion",
                error_msg
            )

    def _prepare_document_metadata(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """문서 메타데이터 준비"""
        file_name = state.get("file_name", "unknown.pdf")
        file_path = state.get("file_path", "")
        
        # 기본 메타데이터
        metadata = {
            "title": file_name.replace(".pdf", "").replace("_", " ").title(),
            "source_file": file_name,
            "source_path": file_path,
            "language": "ko"
        }
        
        # PDF 분석 결과에서 추가 메타데이터 추출
        if "pdf_analysis" in state:
            pdf_analysis = state["pdf_analysis"]
            metadata.update({
                "total_pages": pdf_analysis.get("total_pages"),
                "document_type": pdf_analysis.get("document_type"),
                "quality_score": pdf_analysis.get("quality_score"),
                "processing_strategy": pdf_analysis.get("processing_strategy")
            })
        
        # 통계 정보 추가
        if "text_processing_stats" in state:
            text_stats = state["text_processing_stats"]
            metadata.update({
                "word_count": text_stats.get("total_words"),
                "article_count": text_stats.get("total_articles")
            })
        
        return metadata

    def _generate_output_path(self, state: DocumentProcessingState) -> str:
        """출력 파일 경로 생성"""
        file_name = state.get("file_name", "unknown.pdf")
        base_name = file_name.replace(".pdf", "")
        
        # 출력 디렉토리 생성
        output_dir = "outputs/markdown"
        output_filename = f"{base_name}_converted.md"
        
        return f"{output_dir}/{output_filename}"

    def _validate_conversion_quality(self, conversion_report: Dict[str, Any]) -> Dict[str, Any]:
        """변환 품질 검증"""
        quality_metrics = conversion_report.get("quality_metrics", {})
        
        validation_results = {
            "overall_passed": True,
            "detailed_results": {},
            "score": 0,
            "issues": []
        }
        
        # 1. 구조 보존 정확도 검증 (90% 이상)
        structure_rate = quality_metrics.get("structure_preservation_rate", 0)
        structure_passed = structure_rate >= 90.0
        validation_results["detailed_results"]["structure_preservation"] = {
            "score": structure_rate,
            "passed": structure_passed,
            "threshold": 90.0,
            "description": "문서 구조 보존 정확도"
        }
        if not structure_passed:
            validation_results["issues"].append(f"구조 보존율이 기준({90.0}%) 미달: {structure_rate:.1f}%")

        # 2. Markdown 문법 준수 (100%)
        syntax_compliance = quality_metrics.get("markdown_syntax_compliance", True)
        validation_results["detailed_results"]["syntax_compliance"] = {
            "score": 100 if syntax_compliance else 0,
            "passed": syntax_compliance,
            "threshold": 100,
            "description": "Markdown 문법 준수"
        }
        if not syntax_compliance:
            validation_results["issues"].append("Markdown 문법 준수 실패")

        # 3. 가독성 평가 (우수 등급)
        readability_score = quality_metrics.get("readability_score", "불량")
        readability_passed = readability_score in ["우수", "양호"]
        validation_results["detailed_results"]["readability"] = {
            "score": readability_score,
            "passed": readability_passed,
            "threshold": "양호 이상",
            "description": "가독성 평가"
        }
        if not readability_passed:
            validation_results["issues"].append(f"가독성 평가 기준 미달: {readability_score}")

        # 4. 메타데이터 완성도 (95% 이상)
        metadata_completeness = quality_metrics.get("metadata_completeness", 0)
        metadata_passed = metadata_completeness >= 95.0
        validation_results["detailed_results"]["metadata_completeness"] = {
            "score": metadata_completeness,
            "passed": metadata_passed,
            "threshold": 95.0,
            "description": "메타데이터 완성도"
        }
        if not metadata_passed:
            validation_results["issues"].append(f"메타데이터 완성도가 기준({95.0}%) 미달: {metadata_completeness:.1f}%")

        # 전체 점수 계산
        passed_count = sum(1 for result in validation_results["detailed_results"].values() if result["passed"])
        total_count = len(validation_results["detailed_results"])
        validation_results["score"] = (passed_count / total_count * 100) if total_count > 0 else 0
        
        # 전체 통과 여부 (모든 기준 통과)
        validation_results["overall_passed"] = len(validation_results["issues"]) == 0

        return validation_results

    def get_conversion_summary(self, state: DocumentProcessingState) -> Dict[str, Any]:
        """변환 요약 정보 제공"""
        if "markdown_processing_stats" not in state:
            return {"error": "Markdown 변환이 완료되지 않았습니다"}
        
        stats = state["markdown_processing_stats"]
        quality_validation = state.get("quality_validation", {})
        
        return {
            "conversion_status": "완료" if state.get("status") == ProcessingStatus.COMPLETED.value else "실패",
            "total_chunks_converted": stats.get("total_chunks_converted", 0),
            "markdown_length": stats.get("markdown_length", 0),
            "extracted_images_count": stats.get("extracted_images_count", 0),
            "processing_time": f"{stats.get('processing_time', 0):.2f}초",
            "quality_metrics": {
                "구조 보존율": f"{stats.get('structure_preservation_rate', 0):.1f}%",
                "가독성 점수": stats.get('readability_score', '알 수 없음'),
                "메타데이터 완성도": f"{stats.get('metadata_completeness', 0):.1f}%"
            },
            "quality_validation": {
                "전체 통과": quality_validation.get("overall_passed", False),
                "점수": f"{quality_validation.get('score', 0):.1f}점",
                "문제점": quality_validation.get("issues", [])
            },
            "output_files": {
                "markdown_file": state.get("markdown_file_path"),
                "extracted_images": len(state.get("extracted_images", []))
            }
        }

