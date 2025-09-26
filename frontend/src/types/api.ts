/**
 * ISPL Insurance AI API Types
 * Backend FastAPI와 연동되는 타입 정의
 */

// =====================================
// 공통 타입
// =====================================

export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  status: 'success' | 'error';
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// =====================================
// 인증 관련 타입
// =====================================

export interface User {
  user_id: number;
  email: string;
  role: 'ADMIN' | 'USER';
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// =====================================
// 약관 관리 타입
// =====================================

export interface Policy {
  policy_id: number;
  company: string;
  category: string;
  product_type: string;
  product_name: string;
  sale_start_dt: string;
  sale_end_dt: string;
  sale_stat: string;
  summary: string;
  original_path: string;
  md_path: string;
  pdf_path: string;
  created_at: string;
  security_level: string;
}

export interface PolicyUploadRequest {
  company: string;
  category: string;
  product_type: string;
  product_name: string;
  sale_start_dt: string;
  sale_end_dt: string;
  sale_stat: string;
  security_level: string;
}

export interface PolicyUploadResponse {
  policy_id: number;
  message: string;
  summary?: string;
  processing_status: 'uploaded' | 'processing' | 'completed' | 'failed';
  processing_time?: number;
}

export interface PolicyListResponse extends PaginatedResponse<Policy> {}

// =====================================
// 검색 관련 타입
// =====================================

export interface SearchRequest {
  query: string;
  policy_ids?: number[];
  limit?: number;
  security_level?: string;
}

export interface SearchResult {
  policy_id: number;
  policy_name: string;
  company: string;
  relevance_score: number;
  matched_text: string;
  page_number?: number;
}

export interface SearchResponse {
  answer: string;
  results: SearchResult[];
}

// =====================================
// 채팅 관련 타입
// =====================================

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  searchResults?: SearchResult[];
  processingTime?: number;
  confidence?: number;
  sources?: string[];
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: Date;
  updated_at: Date;
}

// =====================================
// 워크플로우 모니터링 타입
// =====================================

export interface WorkflowStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  started_at?: string;
  completed_at?: string;
  result?: any;
}

export interface AgentExecution {
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  start_time?: string;
  end_time?: string;
  duration?: number;
  input_data?: any;
  output_data?: any;
  error_message?: string;
}

export interface WorkflowExecution {
  workflow_id: string;
  document_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at: string;
  completed_at?: string;
  total_duration?: number;
  agents: AgentExecution[];
}

// =====================================
// 파일 업로드 타입
// =====================================

export interface FileUploadProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
  message?: string;
  result?: PolicyUploadResponse;
}

// =====================================
// 설정 관련 타입
// =====================================

export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  sidebarWidth: number;
  chatMaxMessages: number;
  enableWorkflowMonitoring: boolean;
  enableMcpIntegration: boolean;
  maxFileSize: number;
}

// =====================================
// 통계 관련 타입
// =====================================

export interface SystemStats {
  total_policies: number;
  total_searches: number;
  total_embeddings: number;
  avg_response_time: number;
  system_health: 'healthy' | 'degraded' | 'down';
  last_updated: string;
}

export interface PolicyStats {
  by_company: Record<string, number>;
  by_category: Record<string, number>;
  by_security_level: Record<string, number>;
  recent_uploads: Policy[];
}

