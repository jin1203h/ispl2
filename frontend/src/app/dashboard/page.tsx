'use client';

import { useState } from 'react';
import PerformanceDashboard from '@/components/dashboard/PerformanceDashboard';
import WorkflowMonitoring from '@/components/workflow/WorkflowMonitoring';
import {
  BarChart3,
  Activity,
  Settings,
  Monitor
} from 'lucide-react';

type DashboardTab = 'performance' | 'workflow' | 'settings';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<DashboardTab>('performance');

  const tabs = [
    {
      id: 'performance' as DashboardTab,
      name: '성능 대시보드',
      icon: BarChart3,
      description: '시스템 성능 및 에이전트 메트릭'
    },
    {
      id: 'workflow' as DashboardTab,
      name: '워크플로우 모니터링',
      icon: Activity,
      description: '실시간 워크플로우 실행 상태'
    },
    {
      id: 'settings' as DashboardTab,
      name: '모니터링 설정',
      icon: Settings,
      description: '모니터링 시스템 설정'
    }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'performance':
        return <PerformanceDashboard />;
      case 'workflow':
        return <WorkflowMonitoring />;
      case 'settings':
        return <MonitoringSettings />;
      default:
        return <PerformanceDashboard />;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 상단 네비게이션 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Monitor className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">ISPL 모니터링 대시보드</h1>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">
              Multi-Agent 워크플로우 모니터링 시스템
            </div>
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="mt-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-100 text-blue-700 border border-blue-200'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
          
          {/* 활성 탭 설명 */}
          <div className="mt-2">
            <p className="text-sm text-gray-600">
              {tabs.find(tab => tab.id === activeTab)?.description}
            </p>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="flex-1 overflow-hidden">
        {renderContent()}
      </div>
    </div>
  );
}

// 모니터링 설정 컴포넌트
function MonitoringSettings() {
  const [langfuseEnabled, setLangfuseEnabled] = useState(true);
  const [localMonitorEnabled, setLocalMonitorEnabled] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [maxMetricsHistory, setMaxMetricsHistory] = useState(1000);

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">모니터링 시스템 설정</h2>
            <p className="text-sm text-gray-600 mt-1">
              LangFuse 및 로컬 모니터링 시스템 설정을 관리합니다.
            </p>
          </div>

          <div className="p-6 space-y-6">
            {/* LangFuse 설정 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">LangFuse 모니터링</h3>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">LangFuse 연동</h4>
                  <p className="text-sm text-gray-600">외부 LangFuse 서비스와 연동하여 고급 분석 제공</p>
                </div>
                <button
                  onClick={() => setLangfuseEnabled(!langfuseEnabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    langfuseEnabled ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      langfuseEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {langfuseEnabled && (
                <div className="ml-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">LangFuse 서버 URL</label>
                      <input
                        type="text"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        placeholder="https://cloud.langfuse.com"
                        defaultValue="https://cloud.langfuse.com"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Public Key</label>
                        <input
                          type="text"
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                          placeholder="pk-..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Secret Key</label>
                        <input
                          type="password"
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                          placeholder="sk-..."
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 로컬 모니터링 설정 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">로컬 모니터링</h3>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">로컬 메트릭 수집</h4>
                  <p className="text-sm text-gray-600">시스템 리소스 및 에이전트 성능 메트릭 수집</p>
                </div>
                <button
                  onClick={() => setLocalMonitorEnabled(!localMonitorEnabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    localMonitorEnabled ? 'bg-green-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      localMonitorEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {localMonitorEnabled && (
                <div className="ml-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">새로고침 간격 (초)</label>
                      <select
                        value={refreshInterval}
                        onChange={(e) => setRefreshInterval(Number(e.target.value))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      >
                        <option value={1}>1초</option>
                        <option value={5}>5초</option>
                        <option value={10}>10초</option>
                        <option value={30}>30초</option>
                        <option value={60}>1분</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">최대 메트릭 히스토리</label>
                      <select
                        value={maxMetricsHistory}
                        onChange={(e) => setMaxMetricsHistory(Number(e.target.value))}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      >
                        <option value={100}>100개</option>
                        <option value={500}>500개</option>
                        <option value={1000}>1,000개</option>
                        <option value={5000}>5,000개</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 알림 설정 */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">알림 설정</h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">에이전트 실행 실패 시 알림</span>
                  <input type="checkbox" className="rounded" defaultChecked />
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">시스템 리소스 임계값 초과 시 알림</span>
                  <input type="checkbox" className="rounded" defaultChecked />
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">워크플로우 완료 시 알림</span>
                  <input type="checkbox" className="rounded" />
                </div>
              </div>
            </div>

            {/* 저장 버튼 */}
            <div className="flex justify-end pt-6 border-t border-gray-200">
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                설정 저장
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}




