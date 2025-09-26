/**
 * Chat 관련 React Hook
 * 채팅 상태 관리 및 검색 기능
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';
// UUID 생성 함수 (uuid 라이브러리 없이)
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};
import { ChatMessage, ChatSession, SearchRequest, SearchResponse } from '@/types/api';
import { apiService } from '@/services/api';

interface UseChatOptions {
  maxMessages?: number;
  autoSave?: boolean;
}

interface UseChatReturn {
  // 상태
  currentSession: ChatSession | null;
  sessions: ChatSession[];
  isLoading: boolean;
  error: string | null;
  
  // 액션
  sendMessage: (query: string, policyIds?: number[]) => Promise<void>;
  createNewSession: () => void;
  loadSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  clearCurrentSession: () => void;
  retryLastMessage: () => Promise<void>;
  
  // 유틸리티
  exportSession: (sessionId: string) => string;
  importSession: (sessionData: string) => boolean;
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const { maxMessages = 100, autoSave = true } = options;
  
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshCounter, setRefreshCounter] = useState(0);
  
  const lastMessageRef = useRef<string>('');

  // 로컬 스토리지에서 세션 로드
  const loadSessionsFromStorage = useCallback(() => {
    if (typeof window !== 'undefined') {
      try {
        const savedSessions = localStorage.getItem('chat_sessions');
        if (savedSessions) {
          const parsedSessions = JSON.parse(savedSessions);
          setSessions(parsedSessions);
          
          // 초기 로딩 시에는 자동으로 세션을 로드하지 않음
          // 사용자가 명시적으로 대화를 선택할 때까지 빈 상태 유지
          console.log('Sessions loaded from storage, but no auto-loading session');
        }
      } catch (error) {
        console.error('Failed to load sessions from storage:', error);
      }
    }
  }, []);

  // 로컬 스토리지에 세션 저장
  const saveSessionsToStorage = useCallback((updatedSessions: ChatSession[]) => {
    if (typeof window !== 'undefined' && autoSave) {
      try {
        localStorage.setItem('chat_sessions', JSON.stringify(updatedSessions));
      } catch (error) {
        console.error('Failed to save sessions to storage:', error);
      }
    }
  }, [autoSave]);

  // 현재 세션 초기화
  const clearCurrentSession = useCallback(() => {
    console.log('Clearing current session');
    setCurrentSession(null);
    setError(null);
    
    // 로컬 스토리지에서 마지막 활성 세션 제거
    if (typeof window !== 'undefined') {
      localStorage.removeItem('last_active_session');
    }
  }, []);

  // 사이드바 강제 업데이트 (세션 목록 재로딩)
  const refreshSidebar = useCallback(() => {
    console.log('Refreshing sidebar - reloading sessions');
    // 강제 리렌더링을 위한 카운터 증가
    setRefreshCounter(prev => prev + 1);
    // 세션 목록을 localStorage에서 다시 로드
    loadSessionsFromStorage();
  }, [loadSessionsFromStorage]);

  // 새 세션 생성
  const createNewSession = useCallback(() => {
    const newSession: ChatSession = {
      id: generateId(),
      title: '새 대화',
      messages: [],
      created_at: new Date(),
      updated_at: new Date(),
    };

    console.log('Creating new session:', newSession.id);
    console.log('New session data:', newSession);
    
    // 에러 상태 초기화
    setError(null);
    
    // 즉시 새 세션으로 설정 (강제 동기화)
    flushSync(() => {
      setCurrentSession(newSession);
    });
    console.log('Current session set to:', newSession.id);
    
    // 세션 목록에 추가 (기존 세션들과 함께)
    setSessions(prev => {
      const updated = [newSession, ...prev];
      saveSessionsToStorage(updated);
      return updated;
    });

    // 활성 세션 저장
    if (typeof window !== 'undefined') {
      localStorage.setItem('last_active_session', newSession.id);
    }

    setError(null);
  }, [saveSessionsToStorage]);

  // 세션 로드
  const loadSession = useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      console.log('Loading session:', session.title, 'with', session.messages.length, 'messages');
      console.log('Session data:', session);
      
      // 즉시 세션으로 설정 (강제 동기화)
      flushSync(() => {
        setCurrentSession(session);
      });
      console.log('Current session set to:', session.id);
      
      // 활성 세션 저장
      if (typeof window !== 'undefined') {
        localStorage.setItem('last_active_session', sessionId);
      }
      
      setError(null);
    } else {
      console.warn('Session not found:', sessionId);
    }
  }, [sessions]);

  // 세션 삭제
  const deleteSession = useCallback((sessionId: string) => {
    setSessions(prev => {
      const updated = prev.filter(s => s.id !== sessionId);
      saveSessionsToStorage(updated);
      return updated;
    });

    // 현재 세션이 삭제된 세션이면 초기화
    if (currentSession?.id === sessionId) {
      setCurrentSession(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('last_active_session');
      }
    }
  }, [currentSession, saveSessionsToStorage]);


  // 메시지 전송
  const sendMessage = useCallback(async (query: string, policyIds?: number[]) => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    lastMessageRef.current = query;

    try {
      // 현재 세션이 없으면 새로 생성
      let session = currentSession;
      if (!session) {
        session = {
          id: generateId(),
          title: query.length > 50 ? query.substring(0, 50) + '...' : query,
          messages: [],
          created_at: new Date(),
          updated_at: new Date(),
        };
        setCurrentSession(session);
      }

      // 사용자 메시지 추가
      const userMessage: ChatMessage = {
        id: generateId(),
        type: 'user',
        content: query,
        timestamp: new Date(),
      };

      const updatedMessages = [...session.messages, userMessage];
      
      // 메시지 수 제한
      const limitedMessages = updatedMessages.slice(-maxMessages);

      const updatedSession: ChatSession = {
        ...session,
        messages: limitedMessages,
        updated_at: new Date(),
        // 첫 번째 메시지일 때만 제목 업데이트
        title: session.messages.length === 0 ? (query.length > 50 ? query.substring(0, 50) + '...' : query) : session.title,
      };

      setCurrentSession(updatedSession);

      // 검색 요청
      const searchRequest: SearchRequest = {
        query,
        policy_ids: policyIds,
        limit: 10,
      };

      const startTime = Date.now();
      const searchResponse: SearchResponse = await apiService.search(searchRequest);
      const processingTime = Date.now() - startTime;

      // AI 응답 메시지 추가
      const assistantMessage: ChatMessage = {
        id: generateId(),
        type: 'assistant',
        content: searchResponse.answer,
        timestamp: new Date(),
        searchResults: searchResponse.results,
        processingTime,
        confidence: searchResponse.results.length > 0 ? searchResponse.results[0].relevance_score : 0,
        sources: searchResponse.results.map(r => `${r.company} - ${r.policy_name}`),
      };

      const finalMessages = [...limitedMessages, assistantMessage];
      const finalSession: ChatSession = {
        ...updatedSession,
        messages: finalMessages,
        updated_at: new Date(),
      };

      setCurrentSession(finalSession);

      // 세션 목록 업데이트
      setSessions(prev => {
        const existingIndex = prev.findIndex(s => s.id === finalSession.id);
        let updated: ChatSession[];
        
        if (existingIndex >= 0) {
          updated = [...prev];
          updated[existingIndex] = finalSession;
        } else {
          updated = [finalSession, ...prev];
        }
        
        saveSessionsToStorage(updated);
        return updated;
      });

      // 활성 세션 저장
      if (typeof window !== 'undefined') {
        localStorage.setItem('last_active_session', finalSession.id);
      }

    } catch (err) {
      console.error('Failed to send message:', err);
      setError(err instanceof Error ? err.message : '메시지 전송에 실패했습니다.');
      
      // 에러 메시지 추가
      if (currentSession) {
        const errorMessage: ChatMessage = {
          id: generateId(),
          type: 'system',
          content: '죄송합니다. 요청을 처리하는 중 오류가 발생했습니다. 다시 시도해 주세요.',
          timestamp: new Date(),
        };

        const errorSession: ChatSession = {
          ...currentSession,
          messages: [...currentSession.messages, errorMessage],
          updated_at: new Date(),
        };

        setCurrentSession(errorSession);
      }
    } finally {
      setIsLoading(false);
    }
  }, [currentSession, isLoading, maxMessages, saveSessionsToStorage]);

  // 마지막 메시지 재시도
  const retryLastMessage = useCallback(async () => {
    if (lastMessageRef.current && !isLoading) {
      // 현재 세션의 마지막 메시지가 에러 메시지면 제거
      if (currentSession && currentSession.messages.length > 0) {
        const lastMessage = currentSession.messages[currentSession.messages.length - 1];
        if (lastMessage.type === 'system') {
          const updatedSession = {
            ...currentSession,
            messages: currentSession.messages.slice(0, -1),
          };
          setCurrentSession(updatedSession);
        }
      }
      
      await sendMessage(lastMessageRef.current);
    }
  }, [currentSession, isLoading, sendMessage]);

  // 세션 내보내기
  const exportSession = useCallback((sessionId: string): string => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return '';
    
    return JSON.stringify(session, null, 2);
  }, [sessions]);

  // 세션 가져오기
  const importSession = useCallback((sessionData: string): boolean => {
    try {
      const session: ChatSession = JSON.parse(sessionData);
      
      // 기본 유효성 검사
      if (!session.id || !session.messages || !Array.isArray(session.messages)) {
        return false;
      }

      // 새 ID 생성 (중복 방지)
      const newSession: ChatSession = {
        ...session,
        id: generateId(),
        created_at: new Date(session.created_at),
        updated_at: new Date(),
      };

      setSessions(prev => {
        const updated = [newSession, ...prev];
        saveSessionsToStorage(updated);
        return updated;
      });

      return true;
    } catch (error) {
      console.error('Failed to import session:', error);
      return false;
    }
  }, [saveSessionsToStorage]);

  // 초기 로드
  useEffect(() => {
    loadSessionsFromStorage();
  }, [loadSessionsFromStorage]);

  return {
    currentSession,
    sessions,
    isLoading,
    error,
    sendMessage,
    createNewSession,
    loadSession,
    deleteSession,
    clearCurrentSession,
    refreshSidebar,
    retryLastMessage,
    exportSession,
    importSession,
  };
}
