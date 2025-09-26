"""
Task 3.6 통합 PDF 처리 파이프라인 테스트
전체 파이프라인의 통합 성능 및 안정성 검증
"""
import asyncio
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

from services.pdf_pipeline import (
    PDFProcessingPipeline, 
    PipelineConfig, 
    PipelineMode, 
    BatchProcessor
)
from agents.supervisor import SupervisorAgent
from utils.performance_monitor import ResourceOptimizer

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

class IntegratedPipelineReport:
    """통합 파이프라인 테스트 보고서"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_data = {
            "metadata": {
                "test_type": "integrated_pipeline_analysis",
                "timestamp": self.timestamp
            },
            "system_info": {},
            "pipeline_tests": {},
            "performance_analysis": {},
            "error_analysis": {},
            "recommendations": []
        }
        self.console_output = []

    def log_console(self, message: str):
        """콘솔 출력을 로그에 저장"""
        self.console_output.append(message)
        print(message)

    def set_system_info(self, system_status: Dict[str, Any]):
        """시스템 정보 설정"""
        self.report_data["system_info"] = system_status

    def add_pipeline_test(self, test_name: str, result: Dict[str, Any]):
        """파이프라인 테스트 결과 추가"""
        self.report_data["pipeline_tests"][test_name] = result

    def set_performance_analysis(self, analysis: Dict[str, Any]):
        """성능 분석 설정"""
        self.report_data["performance_analysis"] = analysis

    def set_error_analysis(self, analysis: Dict[str, Any]):
        """에러 분석 설정"""
        self.report_data["error_analysis"] = analysis

    def add_recommendation(self, recommendation: str):
        """권장사항 추가"""
        self.report_data["recommendations"].append(recommendation)

    def save_reports(self):
        """보고서들을 파일로 저장"""
        reports_dir = Path("reports/integrated_pipeline")
        reports_dir.mkdir(parents=True, exist_ok=True)

        base_filename = f"integrated_pipeline_report_{self.timestamp}"

        # 1. JSON 상세 보고서 저장
        json_file = reports_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            def json_serializable(obj):
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
                        json.dumps(obj)
                        return obj
                    except (TypeError, ValueError):
                        return str(obj)

            serializable_data = json_serializable(self.report_data)
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

        # 2. 텍스트 요약 보고서 저장
        txt_file = reports_dir / f"{base_filename}_summary.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("통합 PDF 처리 파이프라인 테스트 보고서\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"🕐 테스트 시간: {self.timestamp}\n")
            f.write("\n")

            f.write("💻 시스템 정보:\n")
            system_info = self.report_data["system_info"]
            if system_info:
                memory_info = system_info.get("memory", {})
                cpu_info = system_info.get("cpu", {})
                f.write(f"   - 총 메모리: {memory_info.get('total_mb', 0):.1f} MB\n")
                f.write(f"   - 사용 가능 메모리: {memory_info.get('available_mb', 0):.1f} MB\n")
                f.write(f"   - CPU 사용률: {cpu_info.get('usage_percent', 0):.1f}%\n")
                f.write(f"   - CPU 코어 수: {cpu_info.get('count', 0)}\n")
            f.write("\n")

            f.write("🧪 파이프라인 테스트 결과:\n")
            for test_name, result in self.report_data["pipeline_tests"].items():
                status = "✅ 성공" if result.get("success", False) else "❌ 실패"
                f.write(f"   {status} {test_name}:\n")
                f.write(f"     - 처리 시간: {result.get('processing_time', 0):.2f}초\n")
                if result.get("error_message"):
                    f.write(f"     - 오류: {result['error_message']}\n")
                f.write(f"     - 완료된 스테이지: {len(result.get('stages_completed', []))}\n")
            f.write("\n")

            f.write("📊 성능 분석:\n")
            perf_analysis = self.report_data["performance_analysis"]
            if perf_analysis:
                f.write(f"   - 평균 처리 시간: {perf_analysis.get('avg_processing_time', 0):.2f}초\n")
                f.write(f"   - 최대 메모리 사용량: {perf_analysis.get('peak_memory_mb', 0):.1f} MB\n")
                f.write(f"   - 전체 성공률: {perf_analysis.get('success_rate', 0):.1f}%\n")
                f.write(f"   - 성능 등급: {perf_analysis.get('performance_grade', 'N/A')}\n")
            f.write("\n")

            f.write("🔍 권장사항:\n")
            for rec in self.report_data["recommendations"]:
                f.write(f"   - {rec}\n")
            f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("콘솔 출력 로그:\n")
            f.write("=" * 80 + "\n")
            for line in self.console_output:
                f.write(line + "\n")

        return {"json_report": str(json_file), "txt_summary": str(txt_file)}

async def test_standard_pipeline():
    """표준 파이프라인 테스트"""
    logger.info("표준 파이프라인 테스트 시작")
    
    config = PipelineConfig(
        mode=PipelineMode.STANDARD,
        parallel_processing=False,
        timeout_seconds=120
    )
    
    pipeline = PDFProcessingPipeline(config)
    test_file = "uploads/pdf/test_policy.pdf"
    
    # 더미 파일이 없으면 생성
    if not os.path.exists(test_file):
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, 'w') as f:
            f.write("dummy pdf content for testing")
    
    start_time = time.time()
    try:
        result = await pipeline.process_document(test_file, policy_id=1)
        processing_time = time.time() - start_time
        
        return {
            "success": result.success,
            "processing_time": processing_time,
            "stages_completed": result.stages_completed,
            "error_message": result.error_message,
            "performance_metrics": result.performance_metrics
        }
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "success": False,
            "processing_time": processing_time,
            "stages_completed": [],
            "error_message": str(e),
            "performance_metrics": {}
        }

async def test_fast_pipeline():
    """고속 파이프라인 테스트"""
    logger.info("고속 파이프라인 테스트 시작")
    
    config = PipelineConfig(
        mode=PipelineMode.FAST,
        enable_table_extraction=False,
        enable_image_extraction=False,
        parallel_processing=False,
        timeout_seconds=60
    )
    
    pipeline = PDFProcessingPipeline(config)
    test_file = "uploads/pdf/test_policy.pdf"
    
    start_time = time.time()
    try:
        result = await pipeline.process_document(test_file, policy_id=2)
        processing_time = time.time() - start_time
        
        return {
            "success": result.success,
            "processing_time": processing_time,
            "stages_completed": result.stages_completed,
            "error_message": result.error_message,
            "performance_metrics": result.performance_metrics
        }
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "success": False,
            "processing_time": processing_time,
            "stages_completed": [],
            "error_message": str(e),
            "performance_metrics": {}
        }

async def test_parallel_pipeline():
    """병렬 처리 파이프라인 테스트"""
    logger.info("병렬 처리 파이프라인 테스트 시작")
    
    config = PipelineConfig(
        mode=PipelineMode.STANDARD,
        parallel_processing=True,
        timeout_seconds=180
    )
    
    pipeline = PDFProcessingPipeline(config)
    test_file = "uploads/pdf/test_policy.pdf"
    
    start_time = time.time()
    try:
        result = await pipeline.process_document(test_file, policy_id=3)
        processing_time = time.time() - start_time
        
        return {
            "success": result.success,
            "processing_time": processing_time,
            "stages_completed": result.stages_completed,
            "error_message": result.error_message,
            "performance_metrics": result.performance_metrics
        }
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "success": False,
            "processing_time": processing_time,
            "stages_completed": [],
            "error_message": str(e),
            "performance_metrics": {}
        }

async def test_supervisor_integration():
    """SupervisorAgent 통합 테스트"""
    logger.info("SupervisorAgent 통합 테스트 시작")
    
    supervisor = SupervisorAgent()
    test_file = "uploads/pdf/test_policy.pdf"
    
    start_time = time.time()
    try:
        result = await supervisor.process_document_with_pipeline(
            test_file, 
            policy_id=4, 
            pipeline_mode="STANDARD"
        )
        processing_time = time.time() - start_time
        
        return {
            "success": result.get("status") != "failed",
            "processing_time": processing_time,
            "stages_completed": result.get("pipeline_result", {}).get("stages_completed", []),
            "error_message": result.get("error_message"),
            "performance_metrics": result.get("pipeline_result", {}).get("performance_metrics", {})
        }
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "success": False,
            "processing_time": processing_time,
            "stages_completed": [],
            "error_message": str(e),
            "performance_metrics": {}
        }

def analyze_performance(test_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """성능 분석"""
    successful_tests = {k: v for k, v in test_results.items() if v["success"]}
    failed_tests = {k: v for k, v in test_results.items() if not v["success"]}
    
    if successful_tests:
        processing_times = [t["processing_time"] for t in successful_tests.values()]
        avg_processing_time = sum(processing_times) / len(processing_times)
        max_processing_time = max(processing_times)
        min_processing_time = min(processing_times)
    else:
        avg_processing_time = max_processing_time = min_processing_time = 0
    
    # 메모리 사용량 분석 (성능 메트릭에서 추출)
    peak_memory_mb = 0
    for test_result in successful_tests.values():
        metrics = test_result.get("performance_metrics", {})
        if isinstance(metrics, dict) and "peak_memory_mb" in metrics:
            peak_memory_mb = max(peak_memory_mb, metrics["peak_memory_mb"])
    
    success_rate = (len(successful_tests) / len(test_results)) * 100 if test_results else 0
    
    # 성능 등급 결정
    if success_rate >= 95 and avg_processing_time <= 30:
        performance_grade = "A (우수)"
    elif success_rate >= 90 and avg_processing_time <= 60:
        performance_grade = "B (양호)"
    elif success_rate >= 80 and avg_processing_time <= 120:
        performance_grade = "C (보통)"
    else:
        performance_grade = "D (개선 필요)"
    
    return {
        "total_tests": len(test_results),
        "successful_tests": len(successful_tests),
        "failed_tests": len(failed_tests),
        "success_rate": success_rate,
        "avg_processing_time": avg_processing_time,
        "max_processing_time": max_processing_time,
        "min_processing_time": min_processing_time,
        "peak_memory_mb": peak_memory_mb,
        "performance_grade": performance_grade
    }

def generate_recommendations(system_status: Dict[str, Any], 
                           performance_analysis: Dict[str, Any], 
                           test_results: Dict[str, Dict[str, Any]]) -> List[str]:
    """권장사항 생성"""
    recommendations = []
    
    # 메모리 사용량 권장사항
    memory_usage = system_status.get("memory", {}).get("used_percent", 0)
    if memory_usage > 80:
        recommendations.append("시스템 메모리 사용량이 높습니다. 메모리 증설을 고려하세요.")
    
    # 성능 권장사항
    success_rate = performance_analysis.get("success_rate", 0)
    if success_rate < 90:
        recommendations.append("파이프라인 성공률이 낮습니다. 에러 처리 로직을 강화하세요.")
    
    avg_time = performance_analysis.get("avg_processing_time", 0)
    if avg_time > 60:
        recommendations.append("평균 처리 시간이 깁니다. 병렬 처리 활성화를 고려하세요.")
    
    # 실패한 테스트 분석
    failed_tests = [k for k, v in test_results.items() if not v["success"]]
    if failed_tests:
        recommendations.append(f"실패한 테스트: {', '.join(failed_tests)}. 해당 기능들을 점검하세요.")
    
    # 일반적인 권장사항
    if not recommendations:
        recommendations.append("모든 테스트가 성공적으로 완료되었습니다. 현재 설정을 유지하세요.")
    
    return recommendations

async def run_integrated_pipeline_tests():
    """통합 파이프라인 테스트 실행"""
    logger.info("=" * 60)
    logger.info("Task 3.6: 통합 PDF 처리 파이프라인 테스트 시작")
    logger.info("=" * 60)

    report = IntegratedPipelineReport()
    
    # 시스템 상태 확인
    system_status = ResourceOptimizer.get_system_status()
    report.set_system_info(system_status)
    report.log_console(f"💻 시스템 상태: 메모리 {system_status['memory']['used_percent']:.1f}% 사용 중")

    # 테스트 실행
    test_functions = {
        "standard_pipeline": test_standard_pipeline,
        "fast_pipeline": test_fast_pipeline,
        "parallel_pipeline": test_parallel_pipeline,
        "supervisor_integration": test_supervisor_integration
    }

    test_results = {}
    
    for test_name, test_func in test_functions.items():
        report.log_console(f"\n🧪 {test_name} 테스트 실행 중...")
        try:
            result = await test_func()
            test_results[test_name] = result
            status = "✅ 성공" if result["success"] else "❌ 실패"
            report.log_console(f"{status} {test_name}: {result['processing_time']:.2f}초")
            if result.get("error_message"):
                report.log_console(f"   오류: {result['error_message']}")
        except Exception as e:
            test_results[test_name] = {
                "success": False,
                "processing_time": 0,
                "stages_completed": [],
                "error_message": str(e),
                "performance_metrics": {}
            }
            report.log_console(f"❌ {test_name} 테스트 실행 실패: {e}")

    # 결과를 보고서에 추가
    for test_name, result in test_results.items():
        report.add_pipeline_test(test_name, result)

    # 성능 분석
    performance_analysis = analyze_performance(test_results)
    report.set_performance_analysis(performance_analysis)

    # 권장사항 생성
    recommendations = generate_recommendations(system_status, performance_analysis, test_results)
    for rec in recommendations:
        report.add_recommendation(rec)

    # 결과 요약 출력
    report.log_console("\n" + "=" * 60)
    report.log_console("테스트 결과 요약")
    report.log_console("=" * 60)
    report.log_console(f"📊 전체 테스트: {performance_analysis['total_tests']}개")
    report.log_console(f"✅ 성공: {performance_analysis['successful_tests']}개")
    report.log_console(f"❌ 실패: {performance_analysis['failed_tests']}개")
    report.log_console(f"📈 성공률: {performance_analysis['success_rate']:.1f}%")
    report.log_console(f"⏱️ 평균 처리 시간: {performance_analysis['avg_processing_time']:.2f}초")
    report.log_console(f"🏆 성능 등급: {performance_analysis['performance_grade']}")

    # 보고서 저장
    report.log_console("\n💾 보고서 저장 중...")
    saved_files = report.save_reports()
    report.log_console("✅ 보고서 저장 완료!")
    report.log_console(f"   - JSON 상세 보고서: {saved_files['json_report']}")
    report.log_console(f"   - TXT 요약 보고서: {saved_files['txt_summary']}")

    logger.info("\n" + "=" * 60)
    logger.info("Task 3.6 통합 테스트 완료")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_integrated_pipeline_tests())
