'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChatMessage as ChatMessageType } from '@/types/api';

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [showSources, setShowSources] = useState(false);

  const formatTimestamp = (timestamp: Date) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getInsuranceTypeClass = (company: string) => {
    const companyLower = company.toLowerCase();
    if (companyLower.includes('삼성') || companyLower.includes('samsung')) return 'insurance-health';
    if (companyLower.includes('현대') || companyLower.includes('hyundai')) return 'insurance-auto';
    if (companyLower.includes('kb') || companyLower.includes('KB')) return 'insurance-life';
    return 'insurance-property';
  };

  // 사용자 메시지
  if (message.type === 'user') {
    return (
      <div className="flex justify-end">
        <div className="message-user">
          <p className="text-white">{message.content}</p>
          <div className="flex items-center justify-end mt-2 space-x-2">
            <span className="text-xs text-blue-100">
              {formatTimestamp(message.timestamp)}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // 시스템 메시지
  if (message.type === 'system') {
    return (
      <div className="flex justify-center">
        <div className="message-system">
          <p>{message.content}</p>
        </div>
      </div>
    );
  }

  // AI 응답 메시지
  return (
    <div className="flex justify-start">
      <div className="message-assistant">
        {/* AI 아바타 */}
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          
          <div className="flex-1 min-w-0">
            {/* 메시지 내용 */}
            <div className="chat-message">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="text-sm">{children}</li>,
                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                  em: ({ children }) => <em className="italic">{children}</em>,
                  code: ({ children }) => (
                    <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">
                      {children}
                    </code>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primary-200 pl-4 italic text-gray-600 my-2">
                      {children}
                    </blockquote>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>

            {/* 검색 결과 미리보기 */}
            {message.searchResults && message.searchResults.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-700">
                    관련 약관 {message.searchResults.length}개
                  </h4>
                  <button
                    onClick={() => setShowSources(!showSources)}
                    className="text-xs text-primary-600 hover:text-primary-700"
                  >
                    {showSources ? '접기' : '자세히 보기'}
                  </button>
                </div>
                
                {showSources && (
                  <div className="space-y-2">
                    {message.searchResults.slice(0, 3).map((result, index) => (
                      <div key={index} className="search-result-card">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getInsuranceTypeClass(result.company)}`}>
                                {result.company}
                              </span>
                              <span className="text-xs text-gray-500">
                                관련도 {Math.round(result.relevance_score * 100)}%
                              </span>
                            </div>
                            <h5 className="text-sm font-medium text-gray-900 mt-1 truncate">
                              {result.policy_name}
                            </h5>
                            <p className="text-xs text-gray-600 mt-1 text-ellipsis-2">
                              {result.matched_text}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {message.searchResults.length > 3 && (
                      <div className="text-xs text-gray-500 text-center py-1">
                        +{message.searchResults.length - 3}개 더 있음
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* 메타데이터 */}
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>{formatTimestamp(message.timestamp)}</span>
                
                {message.processingTime && (
                  <span>
                    응답시간: {(message.processingTime / 1000).toFixed(1)}초
                  </span>
                )}
                
                {message.confidence && (
                  <span className="flex items-center space-x-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>신뢰도: {Math.round(message.confidence * 100)}%</span>
                  </span>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                {/* 복사 버튼 */}
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(message.content);
                    // TODO: 토스트 알림 추가
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  title="답변 복사"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
                
                {/* 좋아요/싫어요 (향후 구현) */}
                <div className="flex items-center space-x-1">
                  <button
                    className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                    title="도움이 되었어요"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                    </svg>
                  </button>
                  <button
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                    title="도움이 되지 않았어요"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

