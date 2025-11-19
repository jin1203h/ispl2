"""
워크플로우 로그 저장 서비스
Multi-Agent 워크플로우의 각 단계를 데이터베이스에 기록
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from contextlib import asynccontextmanager

from models.database import WorkflowLog
from services.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class WorkflowLoggerService:
    """워크플로우 로그 저장 및 조회 서비스"""
    
    def __init__(self):
        self.logger = logger
    
    async def log_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        status: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        execution_time: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        워크플로우 단계 로그 저장
        
        Args:
            workflow_id: 워크플로우 고유 ID
            step_name: 단계명 (예: "PDF Analysis", "Text Extraction")
            status: 상태 ("completed", "error", "running", "pending")
            input_data: 입력 데이터 (dict)
            output_data: 출력 데이터 (dict)
            error_message: 오류 메시지
            execution_time: 실행 시간 (밀리초)
            
        Returns:
            생성된 로그의 ID
        """
        try:
            async with AsyncSessionLocal() as db:
                # JSON 직렬화
                input_json = json.dumps(input_data, ensure_ascii=False) if input_data else None
                output_json = json.dumps(output_data, ensure_ascii=False) if output_data else None
                
                # 기존 로그 찾기 (같은 workflow_id와 step_name)
                existing_log_query = select(WorkflowLog).where(
                    and_(
                        WorkflowLog.workflow_id == workflow_id,
                        WorkflowLog.step_name == step_name
                    )
                )
                result = await db.execute(existing_log_query)
                existing_log = result.scalars().first()
                
                if existing_log:
                    # 기존 로그 업데이트
                    existing_log.status = status
                    if input_json:
                        existing_log.input_data = input_json
                    if output_json:
                        existing_log.output_data = output_json
                    if error_message:
                        existing_log.error_message = error_message
                    if execution_time is not None:
                        existing_log.execution_time = execution_time
                    if end_time:
                        existing_log.end_time = end_time
                    # 완료/오류 상태일 때 종료시간 자동 설정
                    elif status in ["completed", "error"]:
                        existing_log.end_time = datetime.now()
                    
                    await db.commit()
                    await db.refresh(existing_log)
                    
                    self.logger.info(f"워크플로우 로그 업데이트 완료: {workflow_id} - {step_name} ({status})")
                    return existing_log.log_id
                else:
                    # 새 로그 생성
                    current_time = datetime.now()
                    workflow_log = WorkflowLog(
                        workflow_id=workflow_id,
                        step_name=step_name,
                        status=status,
                        input_data=input_json,
                        output_data=output_json,
                        error_message=error_message,
                        execution_time=execution_time,
                        start_time=start_time or current_time,
                        end_time=end_time if end_time else (current_time if status in ["completed", "error"] else None)
                    )
                    
                    db.add(workflow_log)
                    await db.commit()
                    await db.refresh(workflow_log)
                    
                    self.logger.info(f"워크플로우 로그 생성 완료: {workflow_id} - {step_name} ({status})")
                    return workflow_log.log_id
                
        except Exception as e:
            self.logger.error(f"워크플로우 로그 저장 실패: {e}")
            # 로그 저장 실패가 전체 워크플로우를 중단시키지 않도록 예외를 삼킴
            return -1
    
    async def get_workflow_logs(
        self,
        workflow_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        워크플로우 로그 조회
        
        Args:
            workflow_id: 특정 워크플로우 ID로 필터링
            status_filter: 상태로 필터링
            limit: 조회할 최대 개수
            offset: 오프셋
            
        Returns:
            워크플로우 로그 리스트
        """
        try:
            async with AsyncSessionLocal() as db:
                query = select(WorkflowLog)
                
                # 필터링 조건 추가
                conditions = []
                if workflow_id:
                    conditions.append(WorkflowLog.workflow_id == workflow_id)
                if status_filter:
                    conditions.append(WorkflowLog.status == status_filter)
                
                if conditions:
                    query = query.where(and_(*conditions))
                
                # 정렬 및 제한
                query = query.order_by(desc(WorkflowLog.created_at)).limit(limit).offset(offset)
                
                result = await db.execute(query)
                logs = result.scalars().all()
                
                # 딕셔너리 형태로 변환
                log_list = []
                for log in logs:
                    log_dict = {
                        "log_id": log.log_id,
                        "workflow_id": log.workflow_id,
                        "step_name": log.step_name,
                        "status": log.status,
                        "input_data": json.loads(log.input_data) if log.input_data else None,
                        "output_data": json.loads(log.output_data) if log.output_data else None,
                        "error_message": log.error_message,
                        "execution_time": log.execution_time,
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    }
                    log_list.append(log_dict)
                
                self.logger.debug(f"워크플로우 로그 조회 완료: {len(log_list)}개")
                return log_list
                
        except Exception as e:
            self.logger.error(f"워크플로우 로그 조회 실패: {e}")
            return []
    
    async def get_workflow_summary(self) -> Dict[str, Any]:
        """
        워크플로우 실행 요약 통계
        
        Returns:
            워크플로우 요약 정보
        """
        try:
            async with AsyncSessionLocal() as db:
                # 전체 로그 수 조회
                total_logs_query = select(WorkflowLog)
                total_result = await db.execute(total_logs_query)
                all_logs = total_result.scalars().all()
                
                if not all_logs:
                    return {
                        "total_workflows": 0,
                        "total_steps": 0,
                        "completed_steps": 0,
                        "error_steps": 0,
                        "running_steps": 0,
                        "success_rate": 0,
                        "avg_execution_time": 0,
                        "last_updated": datetime.now().isoformat()
                    }
                
                # 통계 계산
                total_workflows = len(set(log.workflow_id for log in all_logs))
                total_steps = len(all_logs)
                completed_steps = len([log for log in all_logs if log.status == "completed"])
                error_steps = len([log for log in all_logs if log.status == "error"])
                running_steps = len([log for log in all_logs if log.status == "running"])
                
                # 평균 실행 시간 계산
                execution_times = [log.execution_time for log in all_logs if log.execution_time is not None]
                avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
                
                # 성공률 계산
                success_rate = (completed_steps / total_steps * 100) if total_steps > 0 else 0
                
                summary = {
                    "total_workflows": total_workflows,
                    "total_steps": total_steps,
                    "completed_steps": completed_steps,
                    "error_steps": error_steps,
                    "running_steps": running_steps,
                    "success_rate": round(success_rate, 2),
                    "avg_execution_time": round(avg_execution_time / 1000, 2) if avg_execution_time else 0,  # ms -> s
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "database"
                }
                
                self.logger.debug(f"워크플로우 요약 생성 완료: {total_workflows}개 워크플로우, {total_steps}개 단계")
                return summary
                
        except Exception as e:
            self.logger.error(f"워크플로우 요약 조회 실패: {e}")
            return {
                "error": str(e),
                "data_source": "error"
            }
    
    async def get_workflow_executions(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        워크플로우 실행 목록 조회 (프론트엔드용)
        
        Args:
            status_filter: 상태 필터
            limit: 조회할 최대 개수
            
        Returns:
            워크플로우 실행 목록
        """
        try:
            async with AsyncSessionLocal() as db:
                # 모든 로그 조회
                query = select(WorkflowLog).order_by(desc(WorkflowLog.created_at))
                result = await db.execute(query)
                all_logs = result.scalars().all()
                
                if not all_logs:
                    return []
                
                # policy_id별로 그룹화 (중복 workflow_id 방지)
                workflows = {}
                for log in all_logs:
                    # policy_id 추출
                    policy_id = self._extract_policy_id(log.input_data)
                    if not policy_id:
                        continue
                        
                    if policy_id not in workflows:
                        workflows[policy_id] = {
                            "workflow_id": f"policy_{policy_id}",  # 통일된 workflow_id 사용
                            "document_name": self._extract_document_name(log.input_data),
                            "status": "pending",
                            "start_time": log.start_time.isoformat() if log.start_time else "",
                            "end_time": None,
                            "total_duration": 0,
                            "agents": [],
                            "earliest_start": log.start_time,  # 가장 빠른 시작 시간 추적
                            "latest_end": log.end_time         # 가장 늦은 종료 시간 추적
                        }
                    else:
                        # 시작/종료 시간 업데이트
                        if log.start_time and (not workflows[policy_id]["earliest_start"] or log.start_time < workflows[policy_id]["earliest_start"]):
                            workflows[policy_id]["earliest_start"] = log.start_time
                            workflows[policy_id]["start_time"] = log.start_time.isoformat()
                        if log.end_time and (not workflows[policy_id]["latest_end"] or log.end_time > workflows[policy_id]["latest_end"]):
                            workflows[policy_id]["latest_end"] = log.end_time
                    
                    # 에이전트 정보 추가
                    agent_info = {
                        "agent_name": log.step_name,
                        "name": log.step_name,
                        "status": log.status,
                        "start_time": log.start_time.isoformat() if log.start_time else "",
                        "end_time": log.end_time.isoformat() if log.end_time else None,
                        "execution_time": log.execution_time / 1000 if log.execution_time else None,  # ms -> s
                        "input_data": json.loads(log.input_data) if log.input_data else None,
                        "output_data": json.loads(log.output_data) if log.output_data else None,
                        "error_message": log.error_message
                    }
                    workflows[policy_id]["agents"].append(agent_info)
                    
                    # 워크플로우 총 실행 시간 계산
                    if log.execution_time:
                        workflows[policy_id]["total_duration"] += log.execution_time / 1000
                
                # 워크플로우 상태 결정 및 시간 정리
                for policy_id, workflow in workflows.items():
                    agents = workflow["agents"]
                    if any(agent["status"] == "error" for agent in agents):
                        workflow["status"] = "failed"
                    elif all(agent["status"] == "completed" for agent in agents):
                        workflow["status"] = "completed"
                    elif any(agent["status"] == "running" for agent in agents):
                        workflow["status"] = "running"
                    else:
                        workflow["status"] = "pending"
                    
                    # 종료시간 설정 (가장 늦은 종료시간 사용)
                    if workflow["latest_end"]:
                        workflow["end_time"] = workflow["latest_end"].isoformat()
                    
                    # 임시 필드 제거
                    workflow.pop("earliest_start", None)
                    workflow.pop("latest_end", None)
                
                # 리스트로 변환
                executions = list(workflows.values())
                
                # 상태 필터링
                if status_filter:
                    executions = [exec for exec in executions if exec.get("status") == status_filter]
                
                # 최신 순으로 정렬
                executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
                
                # 제한 적용
                executions = executions[:limit]
                
                self.logger.debug(f"워크플로우 실행 목록 조회 완료: {len(executions)}개")
                return executions
                
        except Exception as e:
            self.logger.error(f"워크플로우 실행 목록 조회 실패: {e}")
            return []
    
    def _extract_document_name(self, input_data_json: Optional[str]) -> str:
        """입력 데이터에서 문서명 추출"""
        try:
            if not input_data_json:
                return "알 수 없는 문서"
            
            input_data = json.loads(input_data_json)
            return input_data.get("file_name", input_data.get("document_name", "알 수 없는 문서"))
        except:
            return "알 수 없는 문서"
    
    def _extract_policy_id(self, input_data_json: Optional[str]) -> Optional[int]:
        """입력 데이터에서 policy_id 추출"""
        try:
            if not input_data_json:
                return None
            
            input_data = json.loads(input_data_json)
            policy_id = input_data.get("policy_id")
            return int(policy_id) if policy_id is not None else None
        except:
            return None
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """
        오래된 로그 정리
        
        Args:
            days: 보관 기간 (일)
            
        Returns:
            삭제된 로그 수
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            async with AsyncSessionLocal() as db:
                # 오래된 로그 조회
                query = select(WorkflowLog).where(WorkflowLog.created_at < cutoff_date)
                result = await db.execute(query)
                old_logs = result.scalars().all()
                
                if not old_logs:
                    return 0
                
                # 삭제
                for log in old_logs:
                    await db.delete(log)
                
                await db.commit()
                
                deleted_count = len(old_logs)
                self.logger.info(f"오래된 워크플로우 로그 정리 완료: {deleted_count}개 삭제")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"워크플로우 로그 정리 실패: {e}")
            return 0

# 싱글톤 인스턴스
_workflow_logger_instance = None

def get_workflow_logger() -> WorkflowLoggerService:
    """워크플로우 로거 싱글톤 인스턴스 반환"""
    global _workflow_logger_instance
    if _workflow_logger_instance is None:
        _workflow_logger_instance = WorkflowLoggerService()
    return _workflow_logger_instance
