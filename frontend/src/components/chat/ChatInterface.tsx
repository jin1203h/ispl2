'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import SearchResults from './SearchResults';

export default function ChatInterface() {
  const {
    currentSession,
    isLoading,
    error,
    sendMessage,
    createNewSession,
    clearCurrentSession,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // 메시지 목록 끝으로 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages]);

  // 디버그: currentSession 변화 추적
  useEffect(() => {
    console.log('ChatInterface - currentSession changed:', {
      sessionId: currentSession?.id,
      title: currentSession?.title,
      messageCount: currentSession?.messages?.length || 0
    });
  }, [currentSession]);

  // 메시지 전송 핸들러
  const handleSendMessage = async (query: string) => {
    await sendMessage(query);
  };

  // 빈 상태 렌더링
  const renderEmptyState = () => (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        
        <h2 className="text-2xl font-bold text-white mb-4">
          보험 약관 AI에 질문해보세요
        </h2>
        
        <p className="text-gray-400 mb-8 leading-relaxed">
          자연어로 보험 약관에 대해 질문하시면, AI가 관련 정보를 찾아 정확한 답변을 제공합니다.
        </p>
        
        <div className="grid gap-3 text-sm">
          <button
            onClick={() => handleSendMessage('암보험 가입 조건이 어떻게 되나요?')}
            className="p-3 text-left bg-gray-800 border border-gray-600 rounded-lg hover:bg-gray-700 hover:border-blue-500 transition-all duration-200 text-gray-300"
          >
            💊 암보험 가입 조건이 어떻게 되나요?
          </button>
          
          <button
            onClick={() => handleSendMessage('자동차보험에서 자차 손해는 어떻게 보상받나요?')}
            className="p-3 text-left bg-gray-800 border border-gray-600 rounded-lg hover:bg-gray-700 hover:border-blue-500 transition-all duration-200 text-gray-300"
          >
            🚗 자동차보험에서 자차 손해는 어떻게 보상받나요?
          </button>
          
          <button
            onClick={() => handleSendMessage('건강보험 실손의료비 청구 절차를 알려주세요.')}
            className="p-3 text-left bg-gray-800 border border-gray-600 rounded-lg hover:bg-gray-700 hover:border-blue-500 transition-all duration-200 text-gray-300"
          >
            🏥 건강보험 실손의료비 청구 절차를 알려주세요.
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* 헤더 */}
      <div className="flex-shrink-0 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold text-white">
              {currentSession ? currentSession.title : 'AI 채팅'}
            </h1>
            <p className="text-sm text-gray-400">
              자연어로 보험 약관 검색
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {currentSession && (
              <button
                onClick={() => {
                  console.log('헤더 새 대화 버튼 클릭');
                  createNewSession();
                }}
                className="px-3 py-2 text-sm text-blue-400 hover:text-blue-300 hover:bg-blue-900/20 rounded-lg transition-colors"
              >
                새 대화
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-hidden">
        <div 
          key={currentSession?.id || 'empty'}
          className="h-full overflow-y-auto px-6 py-4 space-y-4 chat-scroll scrollbar-thin bg-gray-900"
          ref={messagesContainerRef}
        >
          {!currentSession || currentSession.messages.length === 0 ? (
            renderEmptyState()
          ) : (
            <>
              {currentSession.messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              
              {/* 로딩 인디케이터 */}
              {isLoading && (
                <div className="flex items-center justify-start">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 max-w-[80%]">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                      <span className="text-sm text-gray-400">AI가 답변을 생성하고 있습니다...</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 오류 메시지 */}
      {error && (
        <div className="flex-shrink-0 px-6 py-3 bg-red-900/30 border-t border-red-600">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-red-300">{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* 입력 영역 */}
      <div className="flex-shrink-0 border-t border-gray-700 bg-gray-800">
        <div className="px-6 py-4">
          <ChatInput 
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            placeholder="보험 약관에 대해 질문해보세요..."
          />
        </div>
      </div>
    </div>
  );
}