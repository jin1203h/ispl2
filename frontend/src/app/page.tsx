'use client';

import { useState } from 'react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/layout/Sidebar';
import ChatInterface from '../components/chat/ChatInterface';
import PolicyManagement from '../components/policies/PolicyManagement';
import WorkflowMonitoring from '../components/workflow/WorkflowMonitoring';
import PerformanceDashboard from '../components/dashboard/PerformanceDashboard';
import Login from '../components/auth/Login';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// React Query 클라이언트 생성
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5분
    },
    mutations: {
      retry: 1,
    },
  },
});

function HomePage() {
  const [activeTab, setActiveTab] = useState<string>('chat');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const { isAuthenticated } = useAuth();

  const handleLoginClick = () => {
    setShowLoginModal(true);
  };

  const handleCloseLogin = () => {
    setShowLoginModal(false);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatInterface />;
      case 'policies':
        return <PolicyManagement isAuthenticated={isAuthenticated} />;
      case 'workflow':
        return <WorkflowMonitoring />;
      case 'dashboard':
        return <PerformanceDashboard />;
      default:
        return <ChatInterface />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen flex bg-gray-900">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onLoginClick={handleLoginClick}
        />
        <main className="flex-1 overflow-hidden bg-gray-900">
          {renderContent()}
        </main>
        
        {/* 로그인 모달 */}
        {showLoginModal && (
          <Login onClose={handleCloseLogin} />
        )}

        {/* 토스트 알림 */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#374151',
              color: '#f3f4f6',
              border: '1px solid #4b5563',
              borderRadius: '0.5rem',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#374151',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#374151',
              },
            },
          }}
        />
      </div>
    </QueryClientProvider>
  );
}

export default function Home() {
  return (
    <AuthProvider>
      <HomePage />
    </AuthProvider>
  );
}