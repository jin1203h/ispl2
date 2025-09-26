'use client';

import { useState } from 'react';
import { ChatMessage, SearchResult } from '@/types/api';

interface SearchResultsProps {
  messages: ChatMessage[];
  onClose: () => void;
}

export default function SearchResults({ messages, onClose }: SearchResultsProps) {
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [expandedMessage, setExpandedMessage] = useState<string | null>(null);

  // 모든 검색 결과 수집
  const allSearchResults = messages
    .filter(message => message.searchResults && message.searchResults.length > 0)
    .map(message => ({
      messageId: message.id,
      timestamp: message.timestamp,
      query: messages[messages.indexOf(message) - 1]?.content || '',
      results: message.searchResults || [],
    }));

  const getInsuranceTypeClass = (company: string) => {
    const companyLower = company.toLowerCase();
    if (companyLower.includes('삼성') || companyLower.includes('samsung')) return 'insurance-health';
    if (companyLower.includes('현대') || companyLower.includes('hyundai')) return 'insurance-auto';
    if (companyLower.includes('kb') || companyLower.includes('KB')) return 'insurance-life';
    return 'insurance-property';
  };

  const formatTimestamp = (timestamp: Date) => {
    return new Date(timestamp).toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="h-full flex flex-col">
      {/* 헤더 */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">검색 결과</h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="검색 결과 닫기"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* 검색 결과 목록 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {allSearchResults.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-sm text-gray-600">검색 결과가 없습니다</p>
            <p className="text-xs text-gray-500 mt-1">질문을 하시면 관련 약관을 찾아드립니다</p>
          </div>
        ) : (
          allSearchResults.map((searchGroup) => (
            <div key={searchGroup.messageId} className="space-y-3">
              {/* 질문 제목 */}
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-900 truncate">
                  {searchGroup.query}
                </h4>
                <span className="text-xs text-gray-500 ml-2">
                  {formatTimestamp(searchGroup.timestamp)}
                </span>
              </div>

              {/* 검색 결과들 */}
              <div className="space-y-2">
                {searchGroup.results.map((result, index) => (
                  <div
                    key={`${searchGroup.messageId}-${index}`}
                    className={`search-result-card cursor-pointer transition-all ${
                      selectedResult === result ? 'ring-2 ring-primary-500 bg-primary-50' : ''
                    }`}
                    onClick={() => setSelectedResult(selectedResult === result ? null : result)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {/* 회사 및 관련도 */}
                        <div className="flex items-center space-x-2 mb-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getInsuranceTypeClass(result.company)}`}>
                            {result.company}
                          </span>
                          <div className="flex items-center space-x-1">
                            <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                            <span className="text-xs text-gray-600">
                              {Math.round(result.relevance_score * 100)}%
                            </span>
                          </div>
                        </div>

                        {/* 약관명 */}
                        <h5 className="text-sm font-medium text-gray-900 mb-1 truncate">
                          {result.policy_name}
                        </h5>

                        {/* 매칭된 텍스트 미리보기 */}
                        <p className={`text-xs text-gray-600 ${
                          selectedResult === result ? '' : 'text-ellipsis-2'
                        }`}>
                          {result.matched_text}
                        </p>

                        {/* 페이지 정보 */}
                        {result.page_number && (
                          <div className="mt-2 text-xs text-gray-500">
                            페이지 {result.page_number}
                          </div>
                        )}
                      </div>

                      {/* 확장 아이콘 */}
                      <div className="ml-2 flex-shrink-0">
                        <svg 
                          className={`w-4 h-4 text-gray-400 transition-transform ${
                            selectedResult === result ? 'rotate-180' : ''
                          }`} 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>

                    {/* 확장된 정보 */}
                    {selectedResult === result && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-500">정책 ID</span>
                            <span className="font-mono">{result.policy_id}</span>
                          </div>
                          
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-500">관련도 점수</span>
                            <span className="font-mono">{(result.relevance_score * 100).toFixed(1)}%</span>
                          </div>

                          {/* 액션 버튼들 */}
                          <div className="flex items-center space-x-2 mt-3">
                            <button className="text-xs text-primary-600 hover:text-primary-700 underline">
                              전체 약관 보기
                            </button>
                            <span className="text-gray-300">|</span>
                            <button className="text-xs text-primary-600 hover:text-primary-700 underline">
                              PDF 다운로드
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* 질문별 구분선 */}
              {searchGroup !== allSearchResults[allSearchResults.length - 1] && (
                <hr className="border-gray-200 my-4" />
              )}
            </div>
          ))
        )}
      </div>

      {/* 푸터 통계 */}
      {allSearchResults.length > 0 && (
        <div className="bg-gray-50 border-t border-gray-200 p-4">
          <div className="text-xs text-gray-600 space-y-1">
            <div className="flex justify-between">
              <span>총 질문 수:</span>
              <span className="font-medium">{allSearchResults.length}개</span>
            </div>
            <div className="flex justify-between">
              <span>총 검색 결과:</span>
              <span className="font-medium">
                {allSearchResults.reduce((acc, group) => acc + group.results.length, 0)}개
              </span>
            </div>
            <div className="flex justify-between">
              <span>평균 관련도:</span>
              <span className="font-medium">
                {Math.round(
                  allSearchResults
                    .flatMap(group => group.results)
                    .reduce((acc, result) => acc + result.relevance_score, 0) /
                  allSearchResults.flatMap(group => group.results).length * 100
                )}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

