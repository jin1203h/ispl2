'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface WorkflowExecution {
  id: string;
  documentName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  agents: AgentExecution[];
}

interface AgentExecution {
  agentName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  duration?: number;
  inputData?: any;
  outputData?: any;
  errorMessage?: string;
}

export default function WorkflowMonitoring() {
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [filter, setFilter] = useState<'all' | 'running' | 'completed' | 'failed'>('all');
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 실제 워크플로우 데이터 가져오기
  const fetchWorkflowData = async () => {
    try {
      setError(null);
      
      // 워크플로우 실행 목록 가져오기
      const response = await apiService.getWorkflowExecutions();
      
      if (response.success && response.data.workflow_executions) {
        // 백엔드 데이터를 프론트엔드 형식으로 변환
        const transformedExecutions: WorkflowExecution[] = response.data.workflow_executions.map((workflow: any, index: number) => ({
          id: workflow.workflow_id || `workflow-${index}`,
          documentName: workflow.document_name || `문서-${index + 1}`,
          status: mapWorkflowStatus(workflow.status),
          progress: calculateProgress(workflow.agents || []),
          startedAt: workflow.start_time || new Date().toISOString(),
          completedAt: workflow.end_time,
          duration: workflow.total_duration,
          agents: (workflow.agents || []).map((agent: any) => ({
            agentName: agent.agent_name || agent.name,
            status: mapAgentStatus(agent.status),
            startTime: agent.start_time ? new Date(agent.start_time).toLocaleTimeString('ko-KR') : undefined,
            endTime: agent.end_time ? new Date(agent.end_time).toLocaleTimeString('ko-KR') : undefined,
            duration: agent.execution_time,
            inputData: agent.input_data,
            outputData: agent.output_data,
            errorMessage: agent.error_message
          }))
        }));
        
        setExecutions(transformedExecutions);
      } else {
        // 백엔드 데이터가 없으면 데모 데이터 사용
        setExecutions(getDemoExecutions());
      }
    } catch (err) {
      console.error('워크플로우 데이터 가져오기 실패:', err);
      setError('워크플로우 데이터를 불러오는데 실패했습니다.');
      // 오류 시 데모 데이터 사용
      setExecutions(getDemoExecutions());
    } finally {
      setLoading(false);
    }
  };

  // 상태 매핑 함수들
  const mapWorkflowStatus = (status: string): 'pending' | 'running' | 'completed' | 'failed' => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'success':
        return 'completed';
      case 'running':
      case 'processing':
      case 'in_progress':
        return 'running';
      case 'failed':
      case 'error':
        return 'failed';
      default:
        return 'pending';
    }
  };

  const mapAgentStatus = (status: string): 'pending' | 'running' | 'completed' | 'failed' => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'success':
        return 'completed';
      case 'running':
      case 'processing':
        return 'running';
      case 'failed':
      case 'error':
        return 'failed';
      default:
        return 'pending';
    }
  };

  const calculateProgress = (agents: any[]): number => {
    if (!agents || agents.length === 0) return 0;
    
    const completedAgents = agents.filter(agent => 
      agent.status === 'completed' || agent.status === 'success'
    ).length;
    
    return Math.round((completedAgents / agents.length) * 100);
  };

  // 데모 데이터 (백엔드 연결 실패 시 사용)
  const getDemoExecutions = (): WorkflowExecution[] => [
    {
      id: 'exec-001',
      documentName: '삼성생명_암보험약관.pdf',
      status: 'completed',
      progress: 100,
      startedAt: '2024-09-24T10:30:00Z',
      completedAt: '2024-09-24T10:35:30Z',
      duration: 330,
      agents: [
        {
          agentName: 'PDFProcessor',
          status: 'completed',
          startTime: '10:30:00',
          endTime: '10:30:45',
          duration: 45
        },
        {
          agentName: 'TextProcessor',
          status: 'completed',
          startTime: '10:30:45',
          endTime: '10:32:15',
          duration: 90
        },
        {
          agentName: 'TableProcessor',
          status: 'completed',
          startTime: '10:32:15',
          endTime: '10:33:30',
          duration: 75
        },
        {
          agentName: 'ImageProcessor',
          status: 'completed',
          startTime: '10:33:30',
          endTime: '10:34:00',
          duration: 30
        },
        {
          agentName: 'EmbeddingAgent',
          status: 'completed',
          startTime: '10:34:00',
          endTime: '10:35:30',
          duration: 90
        }
      ]
    },
    {
      id: 'exec-002',
      documentName: '현대해상_자동차보험약관.pdf',
      status: 'running',
      progress: 60,
      startedAt: '2024-09-24T11:00:00Z',
      agents: [
        {
          agentName: 'PDFProcessor',
          status: 'completed',
          startTime: '11:00:00',
          endTime: '11:00:30',
          duration: 30
        },
        {
          agentName: 'TextProcessor',
          status: 'completed',
          startTime: '11:00:30',
          endTime: '11:02:00',
          duration: 90
        },
        {
          agentName: 'TableProcessor',
          status: 'running',
          startTime: '11:02:00'
        },
        {
          agentName: 'ImageProcessor',
          status: 'pending'
        },
        {
          agentName: 'EmbeddingAgent',
          status: 'pending'
        }
      ]
    },
    {
      id: 'exec-003',
      documentName: 'KB손해보험_실손의료보험약관.pdf',
      status: 'failed',
      progress: 30,
      startedAt: '2024-09-24T09:45:00Z',
      agents: [
        {
          agentName: 'PDFProcessor',
          status: 'completed',
          startTime: '09:45:00',
          endTime: '09:45:30',
          duration: 30
        },
        {
          agentName: 'TextProcessor',
          status: 'failed',
          startTime: '09:45:30',
          errorMessage: 'OCR 처리 중 오류 발생'
        }
      ]
    }
  ];

  // useEffect로 데이터 가져오기 및 자동 새로고침 설정
  useEffect(() => {
    fetchWorkflowData();

    // 자동 새로고침 설정 (5초마다)
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchWorkflowData, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const filteredExecutions = executions.filter(exec => 
    filter === 'all' || exec.status === filter
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'running':
        return (
          <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  return (
    <div className="h-full flex bg-gray-50">
      {/* 왼쪽: 실행 목록 */}
      <div className="w-1/2 border-r border-gray-200 bg-white">
        {/* 헤더 */}
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">워크플로우 모니터링</h1>
              <p className="text-sm text-gray-600 mt-1">Multi-Agent 처리 과정을 실시간으로 확인하세요</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`flex items-center space-x-1 px-3 py-1 text-xs rounded ${
                  autoRefresh 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                <div className={`w-2 h-2 rounded-full ${autoRefresh ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <span>{autoRefresh ? '실시간' : '일시정지'}</span>
              </button>
              <button
                onClick={fetchWorkflowData}
                disabled={loading}
                className="flex items-center space-x-1 px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
              >
                <svg className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>새로고침</span>
              </button>
              <span className="text-sm text-gray-500">총 {executions.length}개 실행</span>
            </div>
          </div>

          {/* 필터 */}
          <div className="mt-4 flex space-x-2">
            {(['all', 'running', 'completed', 'failed'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                  filter === status 
                    ? 'bg-primary-100 text-primary-700 border border-primary-200' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {status === 'all' ? '전체' : 
                 status === 'running' ? '실행중' :
                 status === 'completed' ? '완료' : '실패'}
              </button>
            ))}
          </div>
        </div>

        {/* 실행 목록 */}
        <div className="overflow-y-auto h-full pb-20">
          {loading && executions.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <svg className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <p className="text-gray-600">워크플로우 데이터를 불러오는 중...</p>
              </div>
            </div>
          ) : error && executions.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <svg className="w-8 h-8 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-600 mb-4">{error}</p>
                <button
                  onClick={fetchWorkflowData}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  다시 시도
                </button>
              </div>
            </div>
          ) : filteredExecutions.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <svg className="w-8 h-8 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p className="text-gray-600">
                  {filter === 'all' ? '실행된 워크플로우가 없습니다.' : `${filter} 상태의 워크플로우가 없습니다.`}
                </p>
              </div>
            </div>
          ) : (
            filteredExecutions.map((execution) => (
            <div
              key={execution.id}
              onClick={() => setSelectedExecution(execution)}
              className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                selectedExecution?.id === execution.id ? 'bg-primary-50 border-l-4 border-l-primary-500' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-900 truncate">
                  {execution.documentName}
                </h3>
                <div className="flex items-center space-x-1">
                  {getStatusIcon(execution.status)}
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(execution.status)}`}>
                    {execution.status === 'completed' ? '완료' :
                     execution.status === 'running' ? '실행중' :
                     execution.status === 'failed' ? '실패' : '대기'}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                {/* 진행률 */}
                <div>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>진행률</span>
                    <span>{execution.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div 
                      className={`h-1.5 rounded-full transition-all duration-300 ${
                        execution.status === 'failed' ? 'bg-red-500' : 
                        execution.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${execution.progress}%` }}
                    ></div>
                  </div>
                </div>

                {/* 시간 정보 */}
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600">시작: <span className="text-gray-900 font-mono">{new Date(execution.startedAt).toLocaleTimeString('ko-KR')}</span></span>
                  {execution.duration && (
                    <span className="text-gray-600">소요: <span className="text-blue-600 font-semibold">{Math.floor(execution.duration / 60)}분 {execution.duration % 60}초</span></span>
                  )}
                </div>
              </div>
            </div>
            ))
          )}
        </div>
      </div>

      {/* 오른쪽: 상세 정보 */}
      <div className="w-1/2 bg-white">
        {selectedExecution ? (
          <div className="h-full flex flex-col">
            {/* 상세 헤더 */}
            <div className="border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{selectedExecution.documentName}</h2>
                  <p className="text-sm text-gray-600 mt-1">실행 ID: {selectedExecution.id}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(selectedExecution.status)}
                  <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(selectedExecution.status)}`}>
                    {selectedExecution.status === 'completed' ? '완료' :
                     selectedExecution.status === 'running' ? '실행중' :
                     selectedExecution.status === 'failed' ? '실패' : '대기'}
                  </span>
                </div>
              </div>
            </div>

            {/* 에이전트 실행 상세 */}
            <div className="flex-1 overflow-y-auto p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Agent 실행 상세</h3>
              
              <div className="space-y-4">
                {selectedExecution.agents.map((agent, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${
                          agent.status === 'completed' ? 'bg-green-500' :
                          agent.status === 'running' ? 'bg-blue-500 animate-pulse' :
                          agent.status === 'failed' ? 'bg-red-500' : 'bg-gray-300'
                        }`}></div>
                        <h4 className="font-medium text-gray-900">{agent.agentName}</h4>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(agent.status)}`}>
                        {agent.status === 'completed' ? '완료' :
                         agent.status === 'running' ? '실행중' :
                         agent.status === 'failed' ? '실패' : '대기'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {agent.startTime && (
                        <div>
                          <span className="text-gray-500">시작 시간:</span>
                          <span className="ml-2 font-mono text-gray-900">{agent.startTime}</span>
                        </div>
                      )}
                      {agent.endTime && (
                        <div>
                          <span className="text-gray-500">종료 시간:</span>
                          <span className="ml-2 font-mono text-gray-900">{agent.endTime}</span>
                        </div>
                      )}
                      {agent.duration && (
                        <div>
                          <span className="text-gray-500">소요 시간:</span>
                          <span className="ml-2 font-mono text-blue-600 font-semibold">{agent.duration}초</span>
                        </div>
                      )}
                    </div>

                    {agent.errorMessage && (
                      <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                        <strong>오류:</strong> {agent.errorMessage}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">워크플로우 실행 선택</h3>
              <p className="text-gray-600">왼쪽에서 실행을 선택하면 상세 정보를 확인할 수 있습니다</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

