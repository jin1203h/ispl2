"""
통합 PDF 처리 파이프라인 서비스
Task 3.1~3.5에서 구현된 기능들을 통합하여 완전한 처리 파이프라인 제공
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from agents.base import DocumentProcessingState, ProcessingStatus
from agents.pdf_processor import PDFProcessorAgent
from agents.text_processor import TextProcessorAgent
from agents.table_processor import TableProcessorAgent
from agents.image_processor import ImageProcessorAgent
from agents.markdown_processor import MarkdownProcessorAgent
from utils.performance_monitor import PerformanceMonitor, PipelineProfiler, ResourceOptimizer

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """파이프라인 스테이지"""
    PDF_ANALYSIS = "pdf_analysis"
    TEXT_EXTRACTION = "text_extraction"
    TABLE_EXTRACTION = "table_extraction"
    IMAGE_EXTRACTION = "image_extraction"
    MARKDOWN_CONVERSION = "markdown_conversion"
    
class PipelineMode(Enum):
    """파이프라인 모드"""
    STANDARD = "standard"      # 표준 모드 (모든 기능)
    FAST = "fast"             # 고속 모드 (기본 기능만)
    THOROUGH = "thorough"     # 정밀 모드 (최고 품질)

@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    mode: PipelineMode = PipelineMode.STANDARD
    enable_ocr: bool = True
    enable_table_extraction: bool = True
    enable_image_extraction: bool = True
    enable_markdown_conversion: bool = True
    parallel_processing: bool = False
    max_memory_mb: float = 500.0
    timeout_seconds: int = 300
    enable_progress_callback: bool = True

@dataclass
class PipelineResult:
    """파이프라인 처리 결과"""
    success: bool
    file_path: str
    processing_time: float
    stages_completed: List[str]
    final_state: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class PDFProcessingPipeline:
    """통합 PDF 처리 파이프라인"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.profiler = PipelineProfiler()
        self.monitor = PerformanceMonitor()
        
        # 에이전트 초기화
        self.agents = {
            PipelineStage.PDF_ANALYSIS: PDFProcessorAgent(),
            PipelineStage.TEXT_EXTRACTION: TextProcessorAgent(),
            PipelineStage.TABLE_EXTRACTION: TableProcessorAgent(),
            PipelineStage.IMAGE_EXTRACTION: ImageProcessorAgent(),
            PipelineStage.MARKDOWN_CONVERSION: MarkdownProcessorAgent()
        }
        
        # 스테이지 의존성 정의
        self.stage_dependencies = {
            PipelineStage.PDF_ANALYSIS: [],
            PipelineStage.TEXT_EXTRACTION: [PipelineStage.PDF_ANALYSIS],
            PipelineStage.TABLE_EXTRACTION: [PipelineStage.PDF_ANALYSIS],
            PipelineStage.IMAGE_EXTRACTION: [PipelineStage.PDF_ANALYSIS],
            PipelineStage.MARKDOWN_CONVERSION: [
                PipelineStage.TEXT_EXTRACTION,
                PipelineStage.TABLE_EXTRACTION,
                PipelineStage.IMAGE_EXTRACTION
            ]
        }
        
        # 진행률 콜백
        self.progress_callback: Optional[Callable[[str, float], None]] = None
        
    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """진행률 콜백 설정"""
        self.progress_callback = callback
    
    async def process_document(self, 
                             file_path: str, 
                             policy_id: int = 1) -> PipelineResult:
        """문서 처리 메인 함수"""
        start_time = time.time()
        self.monitor.start_task("full_pipeline")
        
        try:
            # 초기 상태 생성
            initial_state = self._create_initial_state(file_path, policy_id)
            
            # 파이프라인 실행 계획 생성
            execution_plan = self._generate_execution_plan()
            
            # 병렬 처리 가능한 스테이지 그룹화
            stage_groups = self._group_parallel_stages(execution_plan)
            
            # 스테이지별 실행
            current_state = initial_state
            completed_stages = []
            
            for group_index, stage_group in enumerate(stage_groups):
                group_progress = (group_index / len(stage_groups)) * 100
                self._update_progress(f"스테이지 그룹 {group_index + 1} 실행 중", group_progress)
                
                # 리소스 상태 확인
                resource_status = ResourceOptimizer.should_pause_processing()
                if resource_status["should_pause"]:
                    logger.warning(f"리소스 부족으로 잠시 대기: {resource_status}")
                    await asyncio.sleep(2)
                
                if len(stage_group) == 1 or not self.config.parallel_processing:
                    # 순차 처리
                    for stage in stage_group:
                        current_state = await self._execute_stage(stage, current_state)
                        completed_stages.append(stage.value)
                else:
                    # 병렬 처리
                    current_state = await self._execute_parallel_stages(stage_group, current_state)
                    completed_stages.extend([stage.value for stage in stage_group])
            
            # 최종 처리 완료
            processing_time = time.time() - start_time
            performance_metrics = self.profiler.get_pipeline_summary()
            self.monitor.end_task("full_pipeline")
            
            self._update_progress("처리 완료", 100)
            
            return PipelineResult(
                success=True,
                file_path=file_path,
                processing_time=processing_time,
                stages_completed=completed_stages,
                final_state=current_state,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"파이프라인 처리 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            try:
                self.monitor.end_task("full_pipeline")
            except:
                pass
            
            return PipelineResult(
                success=False,
                file_path=file_path,
                processing_time=processing_time,
                stages_completed=completed_stages if 'completed_stages' in locals() else [],
                final_state=current_state if 'current_state' in locals() else {},
                performance_metrics={},
                error_message=error_msg
            )
    
    def _create_initial_state(self, file_path: str, policy_id: int) -> DocumentProcessingState:
        """초기 상태 생성"""
        return {
            "file_path": file_path,
            "policy_id": policy_id,
            "file_name": Path(file_path).name,
            "current_step": "initialization",
            "status": ProcessingStatus.PENDING.value,
            "error_message": None,
            "processed_chunks": [],
            "total_chunks": 0,
            "pipeline_config": {
                "mode": self.config.mode.value,
                "enable_ocr": self.config.enable_ocr,
                "enable_table_extraction": self.config.enable_table_extraction,
                "enable_image_extraction": self.config.enable_image_extraction,
                "enable_markdown_conversion": self.config.enable_markdown_conversion
            }
        }
    
    def _generate_execution_plan(self) -> List[PipelineStage]:
        """실행 계획 생성"""
        plan = [PipelineStage.PDF_ANALYSIS]
        
        if self.config.mode == PipelineMode.FAST:
            plan.append(PipelineStage.TEXT_EXTRACTION)
            if self.config.enable_markdown_conversion:
                plan.append(PipelineStage.MARKDOWN_CONVERSION)
        
        elif self.config.mode == PipelineMode.THOROUGH:
            plan.append(PipelineStage.TEXT_EXTRACTION)
            if self.config.enable_table_extraction:
                plan.append(PipelineStage.TABLE_EXTRACTION)
            if self.config.enable_image_extraction:
                plan.append(PipelineStage.IMAGE_EXTRACTION)
            if self.config.enable_markdown_conversion:
                plan.append(PipelineStage.MARKDOWN_CONVERSION)
        
        else:  # STANDARD
            plan.append(PipelineStage.TEXT_EXTRACTION)
            if self.config.enable_table_extraction:
                plan.append(PipelineStage.TABLE_EXTRACTION)
            if self.config.enable_image_extraction:
                plan.append(PipelineStage.IMAGE_EXTRACTION)
            if self.config.enable_markdown_conversion:
                plan.append(PipelineStage.MARKDOWN_CONVERSION)
        
        return plan
    
    def _group_parallel_stages(self, execution_plan: List[PipelineStage]) -> List[List[PipelineStage]]:
        """병렬 처리 가능한 스테이지 그룹화"""
        if not self.config.parallel_processing:
            return [[stage] for stage in execution_plan]
        
        groups = []
        remaining_stages = execution_plan.copy()
        
        while remaining_stages:
            current_group = []
            stages_to_remove = []
            
            for stage in remaining_stages:
                # 의존성 확인
                dependencies = self.stage_dependencies.get(stage, [])
                dependencies_satisfied = all(
                    dep not in remaining_stages for dep in dependencies
                )
                
                if dependencies_satisfied:
                    current_group.append(stage)
                    stages_to_remove.append(stage)
            
            if not current_group:
                # 무한 루프 방지
                current_group = [remaining_stages[0]]
                stages_to_remove = [remaining_stages[0]]
            
            for stage in stages_to_remove:
                remaining_stages.remove(stage)
            
            groups.append(current_group)
        
        return groups
    
    async def _execute_stage(self, 
                           stage: PipelineStage, 
                           state: DocumentProcessingState) -> DocumentProcessingState:
        """단일 스테이지 실행"""
        agent = self.agents[stage]
        stage_name = stage.value
        
        logger.info(f"스테이지 실행 시작: {stage_name}")
        
        # 성능 모니터링 시작
        monitor_decorator = self.profiler.profile_stage(stage_name)
        
        try:
            # 에이전트 실행
            decorated_process = monitor_decorator(agent.process)
            result_state = await decorated_process(state)
            
            logger.info(f"스테이지 실행 완료: {stage_name}")
            return result_state
            
        except Exception as e:
            logger.error(f"스테이지 실행 실패: {stage_name} - {e}")
            # 실패해도 상태는 유지하되 에러 정보 추가
            state["error_message"] = f"{stage_name} 실패: {str(e)}"
            state["status"] = ProcessingStatus.FAILED.value
            raise
    
    async def _execute_parallel_stages(self, 
                                     stages: List[PipelineStage], 
                                     state: DocumentProcessingState) -> DocumentProcessingState:
        """병렬 스테이지 실행"""
        logger.info(f"병렬 스테이지 실행: {[s.value for s in stages]}")
        
        # 상태 복사본 생성 (각 스테이지에서 독립적으로 사용)
        tasks = []
        for stage in stages:
            state_copy = state.copy()
            task = self._execute_stage(stage, state_copy)
            tasks.append(task)
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 병합
        merged_state = state.copy()
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"병렬 스테이지 실패: {stages[i].value} - {result}")
                continue
            
            # 성공한 결과 병합
            if isinstance(result, dict):
                merged_state = self._merge_states(merged_state, result, stages[i])
        
        return merged_state
    
    def _merge_states(self, 
                     base_state: DocumentProcessingState, 
                     new_state: DocumentProcessingState, 
                     stage: PipelineStage) -> DocumentProcessingState:
        """상태 병합"""
        # 기본적으로 새로운 상태의 내용을 기존 상태에 추가
        for key, value in new_state.items():
            if key == "processed_chunks":
                # 청크는 추가
                base_state.setdefault("processed_chunks", []).extend(value)
            elif key.startswith(stage.value):
                # 스테이지별 데이터는 덮어쓰기
                base_state[key] = value
            elif key not in base_state or base_state[key] is None:
                # 새로운 키나 None 값은 업데이트
                base_state[key] = value
        
        # 총 청크 수 업데이트
        base_state["total_chunks"] = len(base_state.get("processed_chunks", []))
        
        return base_state
    
    def _update_progress(self, message: str, progress: float) -> None:
        """진행률 업데이트"""
        if self.config.enable_progress_callback and self.progress_callback:
            self.progress_callback(message, progress)
        
        logger.info(f"진행률: {progress:.1f}% - {message}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 보고서 생성"""
        return {
            "pipeline_summary": self.profiler.get_pipeline_summary(),
            "system_status": ResourceOptimizer.get_system_status(),
            "configuration": {
                "mode": self.config.mode.value,
                "parallel_processing": self.config.parallel_processing,
                "max_memory_mb": self.config.max_memory_mb,
                "timeout_seconds": self.config.timeout_seconds
            }
        }
    
    def export_performance_metrics(self, output_path: str) -> None:
        """성능 메트릭 내보내기"""
        self.monitor.export_metrics(output_path)
    
    def clear_cache(self) -> None:
        """캐시 및 메트릭 초기화"""
        self.profiler = PipelineProfiler()
        self.monitor.clear_metrics()

class BatchProcessor:
    """배치 처리기"""
    
    def __init__(self, pipeline_config: Optional[PipelineConfig] = None):
        self.pipeline_config = pipeline_config or PipelineConfig()
        self.results: List[PipelineResult] = []
    
    async def process_multiple_files(self, 
                                   file_paths: List[str], 
                                   max_concurrent: int = 3) -> List[PipelineResult]:
        """다중 파일 배치 처리"""
        logger.info(f"배치 처리 시작: {len(file_paths)}개 파일")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_file(file_path: str) -> PipelineResult:
            async with semaphore:
                pipeline = PDFProcessingPipeline(self.pipeline_config)
                return await pipeline.process_document(file_path)
        
        tasks = [process_single_file(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 정리
        self.results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = PipelineResult(
                    success=False,
                    file_path=file_paths[i],
                    processing_time=0,
                    stages_completed=[],
                    final_state={},
                    performance_metrics={},
                    error_message=str(result)
                )
                self.results.append(error_result)
            else:
                self.results.append(result)
        
        logger.info(f"배치 처리 완료: {len(self.results)}개 결과")
        return self.results
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """배치 처리 요약"""
        if not self.results:
            return {"error": "처리된 결과가 없습니다"}
        
        success_count = sum(1 for r in self.results if r.success)
        total_time = sum(r.processing_time for r in self.results)
        avg_time = total_time / len(self.results)
        
        return {
            "total_files": len(self.results),
            "successful": success_count,
            "failed": len(self.results) - success_count,
            "success_rate": (success_count / len(self.results)) * 100,
            "total_processing_time": total_time,
            "average_processing_time": avg_time,
            "results": self.results
        }

