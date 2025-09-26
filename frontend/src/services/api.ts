/**
 * ISPL Insurance AI API Service
 * Backend FastAPI와 통신하는 서비스 레이어
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  Policy,
  PolicyUploadRequest,
  PolicyUploadResponse,
  PolicyListResponse,
  SearchRequest,
  SearchResponse,
  WorkflowStatus,
  WorkflowExecution,
  SystemStats,
  PolicyStats,
} from '@/types/api';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30초 타임아웃
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터
    this.api.interceptors.request.use(
      (config) => {
        // 토큰 자동 추가
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`[API] Response ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('[API] Response error:', error);
        
        // 401 에러 시 토큰 제거 및 로그인 페이지로 리다이렉트
        if (error.response?.status === 401) {
          this.removeAuthToken();
          // 로그인 페이지로 리다이렉트 로직 추가 가능
        }
        
        return Promise.reject(error);
      }
    );
  }

  // =====================================
  // 인증 관련 메서드
  // =====================================

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  private setAuthToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  private removeAuthToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.api.post<LoginResponse>('/auth/login', {
      email: credentials.email,
      password: credentials.password,
    });

    // 토큰 저장
    if (response.data.access_token) {
      this.setAuthToken(response.data.access_token);
    }

    return response.data;
  }

  async logout(): Promise<void> {
    this.removeAuthToken();
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  // =====================================
  // 약관 관리 API
  // =====================================

  async uploadPolicy(
    file: File,
    metadata: PolicyUploadRequest,
    onProgress?: (progress: number) => void
  ): Promise<PolicyUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    // 메타데이터 추가
    Object.entries(metadata).forEach(([key, value]) => {
      formData.append(key, value);
    });

    const response = await this.api.post<PolicyUploadResponse>(
      '/policies/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      }
    );

    return response.data;
  }

  async getPolicies(
    page: number = 1,
    size: number = 20,
    company?: string,
    category?: string
  ): Promise<PolicyListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });

    if (company) params.append('company', company);
    if (category) params.append('category', category);

    const response = await this.api.get<PolicyListResponse>(`/policies?${params}`);
    return response.data;
  }

  async getPolicyById(policyId: number): Promise<Policy> {
    const response = await this.api.get<Policy>(`/policies/${policyId}`);
    return response.data;
  }

  async deletePolicy(policyId: number): Promise<void> {
    await this.api.delete(`/policies/${policyId}`);
  }

  async downloadPolicyPdf(policyId: number): Promise<Blob> {
    const response = await this.api.get(`/policies/${policyId}/download/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async downloadPolicyMarkdown(policyId: number): Promise<Blob> {
    const response = await this.api.get(`/policies/${policyId}/download/markdown`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // =====================================
  // 검색 API
  // =====================================

  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await this.api.post<SearchResponse>('/search', request);
    return response.data;
  }

  // =====================================
  // 워크플로우 모니터링 API
  // =====================================

  async getWorkflowStatus(taskId: string): Promise<WorkflowStatus> {
    const response = await this.api.get<WorkflowStatus>(`/workflow/status/${taskId}`);
    return response.data;
  }

  async getWorkflowExecutions(
    page: number = 1,
    size: number = 20
  ): Promise<WorkflowExecution[]> {
    const response = await this.api.get<WorkflowExecution[]>(
      `/workflow/executions?page=${page}&size=${size}`
    );
    return response.data;
  }

  async getWorkflowExecution(workflowId: string): Promise<WorkflowExecution> {
    const response = await this.api.get<WorkflowExecution>(`/workflow/executions/${workflowId}`);
    return response.data;
  }

  // =====================================
  // 통계 API
  // =====================================

  async getSystemStats(): Promise<SystemStats> {
    const response = await this.api.get<SystemStats>('/stats/system');
    return response.data;
  }

  async getPolicyStats(): Promise<PolicyStats> {
    const response = await this.api.get<PolicyStats>('/stats/policies');
    return response.data;
  }

  // =====================================
  // 헬스체크 API
  // =====================================

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.api.get('/health');
    return response.data;
  }

  // =====================================
  // 파일 다운로드 헬퍼
  // =====================================

  downloadFile(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // =====================================
  // WebSocket 연결 (향후 구현)
  // =====================================

  connectWebSocket(endpoint: string): WebSocket {
    const wsUrl = this.baseURL.replace(/^http/, 'ws');
    return new WebSocket(`${wsUrl}${endpoint}`);
  }
}

// 싱글톤 인스턴스 생성
export const apiService = new ApiService();
export default apiService;
