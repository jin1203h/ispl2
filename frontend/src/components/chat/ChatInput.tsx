'use client';

import { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSendMessage,
  disabled = false,
  placeholder = "메시지를 입력하세요...",
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 자동 높이 조절
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 120); // 최대 120px
      textarea.style.height = `${newHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [message]);

  // 메시지 전송
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedMessage = message.trim();
    if (!trimmedMessage || disabled || isComposing) return;

    onSendMessage(trimmedMessage);
    setMessage('');
    
    // 텍스트 영역 높이 초기화
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }, 0);
  };

  // 키보드 단축키 처리
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Shift + Enter: 새 줄
        return;
      } else {
        // Enter: 전송
        e.preventDefault();
        handleSubmit(e);
      }
    }
  };

  // 예시 질문들
  const exampleQuestions = [
    '암보험 가입 조건은?',
    '자동차 보험료 계산법',
    '실손의료보험 보장 범위',
    '건강보험 특약 종류',
  ];

  const [showExamples, setShowExamples] = useState(false);

  return (
    <div className="relative">
      {/* 예시 질문 버블 */}
      {showExamples && message.length === 0 && (
        <div className="absolute bottom-full left-0 right-0 pb-2">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 mx-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-900">질문 예시</h4>
              <button
                onClick={() => setShowExamples(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {exampleQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setMessage(question);
                    setShowExamples(false);
                    textareaRef.current?.focus();
                  }}
                  className="text-left p-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 입력 폼 */}
      <form onSubmit={handleSubmit} className="p-6">
        <div className="relative flex items-end space-x-3">
          {/* 예시 질문 버튼 */}
          <button
            type="button"
            onClick={() => setShowExamples(!showExamples)}
            className={`flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 transition-colors ${
              showExamples ? 'text-primary-600' : ''
            }`}
            title="질문 예시 보기"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>

          {/* 텍스트 입력 영역 */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onCompositionStart={() => setIsComposing(true)}
              onCompositionEnd={() => setIsComposing(false)}
              placeholder={placeholder}
              disabled={disabled}
              className="w-full resize-none bg-white border border-gray-300 rounded-xl px-4 py-3 pr-12 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
              style={{ minHeight: '52px', maxHeight: '120px' }}
              rows={1}
            />
            
            {/* 문자 수 표시 */}
            {message.length > 0 && (
              <div className="absolute bottom-1 right-14 text-xs text-gray-400">
                {message.length}/2000
              </div>
            )}
          </div>

          {/* 전송 버튼 */}
          <button
            type="submit"
            disabled={!message.trim() || disabled || isComposing}
            className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
              message.trim() && !disabled && !isComposing
                ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-md'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
            title={disabled ? '답변 생성 중...' : '메시지 전송 (Enter)'}
          >
            {disabled ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>

        {/* 도움말 텍스트 */}
        <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <span>Enter로 전송, Shift+Enter로 줄바꿈</span>
            {disabled && (
              <span className="flex items-center space-x-1 text-amber-600">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>답변 생성 중...</span>
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <span>ISPL AI</span>
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          </div>
        </div>
      </form>
    </div>
  );
}

