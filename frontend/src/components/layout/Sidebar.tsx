import React from 'react';
import { MessageCircle, FileText, Activity, LogIn, LogOut, BarChart3 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onLoginClick: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, onLoginClick }) => {
  const { user, isAuthenticated, logout } = useAuth();

  const menuItems = [
    { id: 'chat', label: 'AI 채팅', icon: MessageCircle, requiresAuth: false },
    { id: 'policies', label: '약관 관리', icon: FileText, requiresAuth: true },
    { id: 'workflow', label: '워크플로우', icon: Activity, requiresAuth: true },
    { id: 'dashboard', label: '모니터링 대시보드', icon: BarChart3, requiresAuth: true },
  ];


  return (
    <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* 로고 */}
      <div className="p-6 border-b border-gray-700">
        <h2 className="text-xl font-bold text-white">ISPL AI</h2>
        <p className="text-sm text-gray-400">보험약관 AI</p>
      </div>

      {/* 메뉴 네비게이션 */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isDisabled = item.requiresAuth && !isAuthenticated;
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => {
                    if (isDisabled) {
                      onLoginClick();
                    } else {
                      setActiveTab(item.id);
                    }
                  }}
                  className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors ${
                    activeTab === item.id
                      ? 'bg-blue-600 text-white'
                      : isDisabled
                      ? 'text-gray-500 cursor-not-allowed'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                  disabled={isDisabled}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.label}
                  {isDisabled && <span className="ml-auto text-xs">(로그인 필요)</span>}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>



      {/* 사용자 정보 및 로그인/로그아웃 - 맨 아래 고정 */}
      <div className="mt-auto p-4 border-t border-gray-700 bg-gray-800">
        {isAuthenticated ? (
          <>
            {/* 사용자 계정 정보 */}
            <div className="flex items-center mb-3 p-3 bg-gray-900/50 rounded-lg">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.email}</p>
                <p className="text-xs text-gray-400 capitalize">{user?.role || '사용자'}</p>
              </div>
            </div>
            
            {/* 로그아웃 버튼 */}
            <button
              onClick={logout}
              className="w-full flex items-center justify-center px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors border border-gray-600 hover:border-gray-500"
            >
              <LogOut className="w-4 h-4 mr-2" />
              로그아웃
            </button>
          </>
        ) : (
          <>
            {/* 로그인 안내 */}
            <div className="text-center mb-3">
              <p className="text-xs text-gray-400 mb-2">더 많은 기능을 이용하려면</p>
            </div>
            
            {/* 로그인 버튼 */}
            <button
              onClick={onLoginClick}
              className="w-full flex items-center justify-center px-4 py-3 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors font-medium"
            >
              <LogIn className="w-4 h-4 mr-2" />
              로그인
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default Sidebar;