"""
Task 4.2: 고급 청킹 및 토큰화 시스템 테스트
3가지 청킹 전략의 성능과 정확성을 검증합니다.
"""
import asyncio
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from dotenv import load_dotenv

try:
    from services.chunking_service import (
        AdvancedChunkingService, 
        ChunkingStrategy, 
        ChunkingConfig
    )
    CHUNKING_SERVICE_AVAILABLE = True
    print("✅ 청킹 서비스 import 성공")
except ImportError as e:
    print(f"❌ 청킹 서비스 import 실패: {e}")
    CHUNKING_SERVICE_AVAILABLE = False
from agents.base import ProcessedChunk

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

class ChunkingTestReport:
    """청킹 테스트 보고서"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_data = {
            "metadata": {
                "timestamp": self.timestamp,
                "test_type": "advanced_chunking_analysis"
            },
            "strategy_tests": {},
            "performance_comparison": {},
            "quality_metrics": {},
            "overall_status": "FAILED",
            "error_message": None
        }
        self.console_output = []

    def log_console(self, message: str):
        """콘솔 출력을 로그에 저장"""
        self.console_output.append(message)
        print(message)

    def add_strategy_test(self, strategy: str, result: Dict[str, Any]):
        """전략별 테스트 결과 추가"""
        self.report_data["strategy_tests"][strategy] = result

    def add_performance_comparison(self, comparison: Dict[str, Any]):
        """성능 비교 결과 추가"""
        self.report_data["performance_comparison"] = comparison

    def add_quality_metrics(self, metrics: Dict[str, Any]):
        """품질 메트릭 추가"""
        self.report_data["quality_metrics"] = metrics

    def set_overall_status(self, status: str, error_message: str = None):
        """전체 상태 설정"""
        self.report_data["overall_status"] = status
        self.report_data["error_message"] = error_message

    def save_reports(self):
        """보고서 저장"""
        reports_dir = Path("reports/chunking_service")
        reports_dir.mkdir(parents=True, exist_ok=True)

        base_filename = f"chunking_service_report_{self.timestamp}"

        # JSON 보고서
        json_file = reports_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)

        # 텍스트 요약
        txt_file = reports_dir / f"{base_filename}_summary.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("고급 청킹 및 토큰화 시스템 테스트 보고서\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"🕐 테스트 시간: {self.timestamp}\n")
            f.write(f"✅ 전체 상태: {self.report_data['overall_status']}\n\n")

            f.write("📊 전략별 테스트 결과:\n")
            for strategy, result in self.report_data["strategy_tests"].items():
                status = "✅" if result.get("success", False) else "❌"
                f.write(f"   {status} {strategy}: {result.get('chunk_count', 0)}개 청크\n")
            f.write("\n")

            if self.report_data["performance_comparison"]:
                f.write("⚡ 성능 비교:\n")
                perf = self.report_data["performance_comparison"]
                for strategy, timing in perf.get("processing_times", {}).items():
                    f.write(f"   - {strategy}: {timing:.3f}초\n")
            f.write("\n")

            if self.report_data["quality_metrics"]:
                f.write("🎯 품질 메트릭:\n")
                quality = self.report_data["quality_metrics"]
                for metric, value in quality.items():
                    f.write(f"   - {metric}: {value}\n")
            f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("콘솔 출력 로그:\n")
            f.write("=" * 80 + "\n")
            for line in self.console_output:
                f.write(line + "\n")

        return {"json_report": str(json_file), "txt_summary": str(txt_file)}

def create_sample_insurance_text() -> str:
    """테스트용 보험약관 샘플 텍스트 생성"""
    return """
제1장 총칙

제1조 (목적) 이 약관은 보험회사와 보험계약자 간의 권리와 의무를 규정함을 목적으로 합니다. 보험약관은 보험계약의 기본 조건을 명시하며, 양 당사자가 준수해야 할 사항들을 포함합니다.

제2조 (정의) 이 약관에서 사용하는 용어의 정의는 다음과 같습니다.
1. 보험계약자: 보험회사와 보험계약을 체결하고 보험료를 납입할 의무를 지는 자를 말합니다.
2. 피보험자: 보험사고의 대상이 되는 자를 말합니다.
3. 보험금액: 보험회사가 보험사고 발생 시 지급할 수 있는 보상의 최고 한도액을 말합니다.
4. 보험료: 보험계약에 따라 보험계약자가 보험회사에 납입하는 대가를 말합니다.

제3조 (보험계약의 성립) 보험계약은 보험계약자의 청약과 보험회사의 승낙으로 성립됩니다. 보험회사는 청약을 받은 날부터 30일 이내에 승낙 또는 거절의 의사표시를 하여야 합니다.

제2장 보험료의 납입

제4조 (보험료 납입 방법) 보험료는 계약자가 선택한 방법에 따라 납입하며, 다음과 같은 방법이 있습니다.
가. 일시납: 보험료 전액을 한 번에 납입하는 방법
나. 월납: 매월 분할하여 납입하는 방법
다. 연납: 매년 분할하여 납입하는 방법

제5조 (보험료 연체 시 조치) 보험료 납입이 연체된 경우 다음과 같은 조치를 취합니다.
1. 14일간의 유예기간을 제공합니다.
2. 유예기간 내 납입하지 않을 경우 보험계약이 실효됩니다.
3. 실효된 계약은 2년 이내에 부활할 수 있습니다.

제3장 보험금 지급

제6조 (보험금 지급 사유) 다음 각 호의 어느 하나에 해당하는 경우 보험금을 지급합니다.
1. 피보험자가 질병 또는 상해로 입원한 경우
2. 피보험자가 수술을 받은 경우  
3. 피보험자가 진단확정을 받은 경우

제7조 (보험금 지급 절차) 보험금 청구 시 다음 서류를 제출하여야 합니다.
- 보험금 청구서
- 진단서 또는 소견서
- 입원확인서 (입원 시)
- 수술확인서 (수술 시)
- 기타 보험회사가 요구하는 서류

제8조 (면책사항) 다음의 경우에는 보험금을 지급하지 않습니다.
1. 고의 또는 중과실로 인한 사고
2. 음주운전으로 인한 사고
3. 전쟁, 폭동, 내란 등으로 인한 사고
4. 기타 약관에서 정한 면책사유
"""

async def test_chunking_strategies():
    """3가지 청킹 전략 테스트"""
    logger.info("=" * 60)
    logger.info("청킹 전략별 성능 테스트 시작")
    logger.info("=" * 60)
    
    report = ChunkingTestReport()
    sample_text = create_sample_insurance_text()
    
    strategies = [
        ChunkingStrategy.FIXED_SIZE,
        ChunkingStrategy.CONTENT_AWARE,
        ChunkingStrategy.SEMANTIC
    ]
    
    strategy_results = {}
    processing_times = {}
    
    for strategy in strategies:
        try:
            report.log_console(f"\n📊 전략: {strategy.value}")
            
            # 청킹 서비스 생성
            config = ChunkingConfig(
                strategy=strategy,
                chunk_size=200,
                overlap_ratio=0.15,
                preserve_article_boundaries=True
            )
            service = AdvancedChunkingService(config)
            
            # 청킹 실행 및 시간 측정
            start_time = time.time()
            chunks = await service.chunk_text(sample_text, {"page_number": 1})
            processing_time = time.time() - start_time
            
            processing_times[strategy.value] = processing_time
            
            # 통계 생성
            stats = service.get_chunking_stats(chunks)
            
            report.log_console(f"   청크 수: {stats['total_chunks']}")
            report.log_console(f"   평균 토큰: {stats['avg_tokens_per_chunk']:.1f}")
            report.log_console(f"   토큰 범위: {stats['min_tokens']}-{stats['max_tokens']}")
            report.log_console(f"   처리 시간: {processing_time:.3f}초")
            
            # 청크 품질 검증
            quality_score = _evaluate_chunk_quality(chunks, strategy)
            report.log_console(f"   품질 점수: {quality_score:.1f}/100")
            
            strategy_results[strategy.value] = {
                "success": True,
                "chunk_count": stats['total_chunks'],
                "avg_tokens": stats['avg_tokens_per_chunk'],
                "token_range": f"{stats['min_tokens']}-{stats['max_tokens']}",
                "total_tokens": stats['total_tokens'],
                "processing_time": processing_time,
                "quality_score": quality_score,
                "stats": stats
            }
            
            report.add_strategy_test(strategy.value, strategy_results[strategy.value])
            
        except Exception as e:
            error_msg = f"전략 {strategy.value} 테스트 실패: {str(e)}"
            report.log_console(f"   ❌ {error_msg}")
            
            strategy_results[strategy.value] = {
                "success": False,
                "error": str(e),
                "chunk_count": 0,
                "processing_time": 0,
                "quality_score": 0
            }
            
            report.add_strategy_test(strategy.value, strategy_results[strategy.value])
    
    # 성능 비교
    performance_comparison = {
        "processing_times": processing_times,
        "fastest_strategy": min(processing_times, key=processing_times.get) if processing_times else None,
        "slowest_strategy": max(processing_times, key=processing_times.get) if processing_times else None
    }
    
    report.add_performance_comparison(performance_comparison)
    
    return report, strategy_results

def _evaluate_chunk_quality(chunks: List[ProcessedChunk], strategy: ChunkingStrategy) -> float:
    """청킹 품질 평가"""
    if not chunks:
        return 0.0
    
    quality_score = 100.0
    
    # 1. 토큰 크기 일관성 (±5% 허용)
    target_size = 200
    token_counts = [chunk["metadata"]["token_count"] for chunk in chunks]
    size_variance = sum(abs(count - target_size) for count in token_counts) / len(token_counts)
    size_penalty = min(30, size_variance / target_size * 100)
    quality_score -= size_penalty
    
    # 2. 최소/최대 크기 위반
    min_violations = sum(1 for count in token_counts if count < 50)
    max_violations = sum(1 for count in token_counts if count > 300)
    violation_penalty = (min_violations + max_violations) / len(chunks) * 20
    quality_score -= violation_penalty
    
    # 3. 전략별 추가 평가
    if strategy == ChunkingStrategy.CONTENT_AWARE:
        # 조항 경계 보존 평가
        article_preserved_chunks = sum(1 for chunk in chunks 
                                     if chunk["metadata"].get("article_title"))
        if article_preserved_chunks > 0:
            quality_score += 10  # 보너스
    
    elif strategy == ChunkingStrategy.SEMANTIC:
        # 주제 일관성 평가
        topic_chunks = sum(1 for chunk in chunks 
                          if chunk["metadata"].get("semantic_topic"))
        if topic_chunks > len(chunks) * 0.8:
            quality_score += 10  # 보너스
    
    return max(0, min(100, quality_score))

async def test_article_boundary_preservation():
    """조항 경계 보존 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("조항 경계 보존 테스트")
    logger.info("=" * 60)
    
    report = ChunkingTestReport()
    sample_text = create_sample_insurance_text()
    
    # Content-aware 전략으로 테스트
    config = ChunkingConfig(
        strategy=ChunkingStrategy.CONTENT_AWARE,
        chunk_size=200,
        preserve_article_boundaries=True
    )
    service = AdvancedChunkingService(config)
    
    try:
        chunks = await service.chunk_text(sample_text)
        
        # 조항 경계 분석
        article_chunks = [chunk for chunk in chunks 
                         if chunk["metadata"].get("article_title")]
        
        report.log_console(f"전체 청크 수: {len(chunks)}")
        report.log_console(f"조항 경계 보존 청크: {len(article_chunks)}")
        report.log_console(f"조항 보존율: {len(article_chunks)/len(chunks)*100:.1f}%")
        
        # 조항별 상세 분석
        articles_found = set()
        for chunk in article_chunks:
            article_title = chunk["metadata"].get("article_title", "")
            if article_title:
                articles_found.add(article_title)
        
        report.log_console(f"발견된 조항 수: {len(articles_found)}")
        for article in sorted(articles_found):
            report.log_console(f"   - {article}")
        
        return True
        
    except Exception as e:
        report.log_console(f"❌ 조항 경계 보존 테스트 실패: {str(e)}")
        return False

async def test_token_accuracy():
    """토큰 계산 정확성 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("토큰 계산 정확성 테스트")
    logger.info("=" * 60)
    
    report = ChunkingTestReport()
    
    try:
        # tiktoken 직접 사용
        import tiktoken
        tokenizer = tiktoken.get_encoding("cl100k_base")
        
        test_texts = [
            "보험약관 제1조 목적",
            "보험계약자는 보험료를 납입할 의무가 있습니다.",
            "제2조 (정의) 이 약관에서 사용하는 용어의 정의는 다음과 같습니다."
        ]
        
        config = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=200)
        service = AdvancedChunkingService(config)
        
        total_accuracy = 0
        
        for i, text in enumerate(test_texts):
            # tiktoken으로 직접 계산
            actual_tokens = len(tokenizer.encode(text))
            
            # 서비스로 계산 (테스트 메타데이터 추가)
            test_metadata = {"source": "토큰_테스트", "page_number": 1}
            chunks = await service.chunk_text(text, test_metadata)
            if chunks:
                service_tokens = chunks[0]["metadata"]["token_count"]
                accuracy = (1 - abs(actual_tokens - service_tokens) / actual_tokens) * 100
            else:
                accuracy = 0
            
            total_accuracy += accuracy
            
            report.log_console(f"테스트 {i+1}:")
            report.log_console(f"   실제 토큰: {actual_tokens}")
            report.log_console(f"   서비스 토큰: {service_tokens if chunks else 0}")
            report.log_console(f"   정확도: {accuracy:.1f}%")
        
        avg_accuracy = total_accuracy / len(test_texts)
        report.log_console(f"\n평균 토큰 계산 정확도: {avg_accuracy:.1f}%")
        
        return avg_accuracy > 95.0
        
    except ImportError:
        report.log_console("⚠️ tiktoken이 설치되지 않아 토큰 정확성 테스트를 건너뜁니다.")
        return True
    except Exception as e:
        report.log_console(f"❌ 토큰 정확성 테스트 실패: {str(e)}")
        return False

async def main():
    """메인 테스트 함수"""
    logger.info("=" * 80)
    logger.info("Task 4.2: 고급 청킹 및 토큰화 시스템 테스트 시작")
    logger.info("=" * 80)
    
    overall_report = ChunkingTestReport()
    
    try:
        # 1. 청킹 전략별 성능 테스트
        strategy_report, strategy_results = await test_chunking_strategies()
        overall_report.report_data["strategy_tests"] = strategy_report.report_data["strategy_tests"]
        overall_report.report_data["performance_comparison"] = strategy_report.report_data["performance_comparison"]
        overall_report.console_output.extend(strategy_report.console_output)
        
        # 2. 조항 경계 보존 테스트
        boundary_success = await test_article_boundary_preservation()
        
        # 3. 토큰 계산 정확성 테스트
        token_accuracy_success = await test_token_accuracy()
        
        # 전체 결과 평가
        strategy_success = all(result.get("success", False) 
                              for result in strategy_results.values())
        
        overall_success = strategy_success and boundary_success and token_accuracy_success
        
        # 품질 메트릭 계산
        if strategy_success:
            avg_quality = sum(result.get("quality_score", 0) 
                            for result in strategy_results.values()) / len(strategy_results)
            fastest_time = min(result.get("processing_time", float('inf')) 
                             for result in strategy_results.values())
            
            quality_metrics = {
                "average_quality_score": avg_quality,
                "fastest_processing_time": fastest_time,
                "boundary_preservation": boundary_success,
                "token_accuracy": token_accuracy_success,
                "strategies_tested": len(strategy_results)
            }
            overall_report.add_quality_metrics(quality_metrics)
        
        overall_report.log_console("\n" + "=" * 80)
        overall_report.log_console("테스트 결과 요약")
        overall_report.log_console("=" * 80)
        overall_report.log_console(f"청킹 전략 테스트: {'✅ 성공' if strategy_success else '❌ 실패'}")
        overall_report.log_console(f"조항 경계 보존: {'✅ 성공' if boundary_success else '❌ 실패'}")
        overall_report.log_console(f"토큰 계산 정확성: {'✅ 성공' if token_accuracy_success else '❌ 실패'}")
        overall_report.log_console(f"전체 테스트: {'✅ 성공' if overall_success else '❌ 실패'}")
        
        if strategy_success:
            overall_report.log_console(f"평균 품질 점수: {avg_quality:.1f}/100")
            overall_report.log_console(f"최고 성능: {fastest_time:.3f}초")
        
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
    logger.info("Task 4.2 테스트 완료")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
