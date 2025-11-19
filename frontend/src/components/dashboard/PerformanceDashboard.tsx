'use client';

import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Cpu,
  MemoryStick,
  Zap,
  RefreshCw
} from 'lucide-react';
import { apiService } from '@/services/api';

interface DashboardMetrics {
  summary: {
    total_agent_executions: number;
    total_workflows: number;
    avg_agent_execution_time: number;
    overall_success_rate: number;
    system_health: string;
  };
  recent_activity: {
    last_10_agents: number;
    last_5_workflows: number;
    active_monitoring: boolean;
  };
  performance_overview: {
    fastest_agent: string;
    slowest_agent: string;
    most_reliable: string;
    bottlenecks_detected: number;
  };
}

interface AgentPerformance {
  [key: string]: {
    execution_count: number;
    avg_execution_time: number;
    success_rate: number;
    avg_memory_usage_mb: number;
    total_errors: number;
  };
}

interface SystemMetrics {
  avg_cpu_usage: number;
  max_cpu_usage: number;
  avg_memory_usage: number;
  max_memory_usage: number;
  samples_count: number;
}

export default function PerformanceDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentPerformance | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 데모 메트릭 데이터 가져오기 (인증 불필요)
      const demoResponse = await apiService.getDemoMetrics();
      if (demoResponse.success) {
        setMetrics(demoResponse.data);
      }

      // 에이전트 메트릭 가져오기 시도 (인증 필요)
      try {
        const agentResponse = await apiService.getAgentMetrics();
        if (agentResponse.success) {
          setAgentMetrics(agentResponse.data.agent_performance);
        }
      } catch (authError) {
        console.log('에이전트 메트릭 인증 필요 (예상됨)');
      }

      // 시스템 메트릭 가져오기 시도 (인증 필요)
      try {
        const systemResponse = await apiService.getSystemMetrics();
        if (systemResponse.success) {
          setSystemMetrics(systemResponse.data.system_performance);
        }
      } catch (authError) {
        console.log('시스템 메트릭 인증 필요 (예상됨)');
      }

      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // 자동 새로고침 설정 (5초마다)
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchDashboardData, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'good': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatExecutionTime = (seconds: number) => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`;
  };

  // 에이전트 성능 차트 데이터 준비
  const agentChartData = agentMetrics ? Object.entries(agentMetrics).map(([name, data]) => ({
    name: name.replace('_', ' '),
    execution_time: data.avg_execution_time,
    success_rate: data.success_rate * 100,
    memory_usage: data.avg_memory_usage_mb,
    executions: data.execution_count
  })) : [];

  // 시스템 리소스 차트 데이터
  const systemChartData = systemMetrics ? [
    { name: 'CPU 사용률', current: systemMetrics.avg_cpu_usage, max: systemMetrics.max_cpu_usage },
    { name: '메모리 사용률', current: systemMetrics.avg_memory_usage, max: systemMetrics.max_memory_usage }
  ] : [];

  if (loading && !metrics) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">성능 메트릭을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      {/* 헤더 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">성능 대시보드</h1>
            <p className="text-sm text-gray-600 mt-1">
              Multi-Agent 워크플로우 실시간 성능 모니터링
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`flex items-center space-x-1 px-3 py-1 text-sm rounded ${
                  autoRefresh 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                <Activity className="w-4 h-4" />
                <span>{autoRefresh ? '실시간' : '일시정지'}</span>
              </button>
              <button
                onClick={fetchDashboardData}
                disabled={loading}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>새로고침</span>
              </button>
            </div>
            <div className="text-xs text-gray-500">
              마지막 업데이트: {lastUpdated.toLocaleTimeString('ko-KR')}
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* 요약 카드 */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Activity className="w-8 h-8 text-blue-500" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">총 에이전트 실행</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {metrics.summary.total_agent_executions}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Clock className="w-8 h-8 text-green-500" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">평균 실행 시간</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatExecutionTime(metrics.summary.avg_agent_execution_time)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircle className="w-8 h-8 text-emerald-500" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">성공률</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {(metrics.summary.overall_success_rate * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Zap className="w-8 h-8 text-purple-500" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">시스템 상태</p>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getHealthColor(metrics.summary.system_health)}`}>
                      {metrics.summary.system_health === 'good' ? '양호' : 
                       metrics.summary.system_health === 'warning' ? '주의' : '위험'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 에이전트 성능 차트 */}
        {agentChartData.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">에이전트별 실행 시간</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={agentChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${value}초`, '실행 시간']} />
                  <Bar dataKey="execution_time" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">에이전트별 성공률</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={agentChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value) => [`${value}%`, '성공률']} />
                  <Bar dataKey="success_rate" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* 시스템 리소스 모니터링 */}
        {systemChartData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">시스템 리소스 사용률</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={systemChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => [`${value}%`, '사용률']} />
                <Bar dataKey="current" fill="#8B5CF6" name="평균" />
                <Bar dataKey="max" fill="#EF4444" name="최대" />
                <Legend />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 성능 개요 */}
        {metrics && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">성능 개요</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-green-800">가장 빠른 에이전트</span>
                </div>
                <p className="text-lg font-bold text-green-900 mt-1">
                  {metrics.performance_overview.fastest_agent}
                </p>
              </div>

              <div className="p-4 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <TrendingDown className="w-5 h-5 text-red-600" />
                  <span className="text-sm font-medium text-red-800">가장 느린 에이전트</span>
                </div>
                <p className="text-lg font-bold text-red-900 mt-1">
                  {metrics.performance_overview.slowest_agent}
                </p>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800">가장 안정적</span>
                </div>
                <p className="text-lg font-bold text-blue-900 mt-1">
                  {metrics.performance_overview.most_reliable}
                </p>
              </div>

              <div className="p-4 bg-yellow-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-800">병목 지점</span>
                </div>
                <p className="text-lg font-bold text-yellow-900 mt-1">
                  {metrics.performance_overview.bottlenecks_detected}개
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 실시간 활동 */}
        {metrics && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">실시간 활동</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.recent_activity.last_10_agents}
                </p>
                <p className="text-sm text-gray-600">최근 에이전트 실행</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.recent_activity.last_5_workflows}
                </p>
                <p className="text-sm text-gray-600">최근 워크플로우</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    metrics.recent_activity.active_monitoring ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <p className="text-sm font-medium text-gray-900">
                    {metrics.recent_activity.active_monitoring ? '모니터링 활성' : '모니터링 비활성'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}




