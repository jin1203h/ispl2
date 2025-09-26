import React, { useState, useEffect } from 'react';
import { FileText, Trash2, Eye, Plus, File, Upload } from 'lucide-react';
import { apiService } from '../../services/api';

interface Policy {
  policy_id: number;
  company: string;
  category: string;
  product_type: string;
  product_name: string;
  summary: string;
  created_at: string;
  security_level: string;
}

interface PolicyManagementProps {
  isAuthenticated: boolean;
}

const PolicyManagement: React.FC<PolicyManagementProps> = ({ isAuthenticated }) => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showPdfModal, setShowPdfModal] = useState(false);
  const [showMdModal, setShowMdModal] = useState(false);
  const [selectedPdfUrl, setSelectedPdfUrl] = useState<string>('');
  const [selectedMdContent, setSelectedMdContent] = useState<string>('');
  const [selectedPolicyName, setSelectedPolicyName] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  // 업로드 폼 상태
  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    company: '',
    category: '',
    productType: '',
    productName: '',
    securityLevel: 'public'
  });

  useEffect(() => {
    loadPolicies();
  }, []);

  const showMessage = (message: string, type: 'success' | 'error') => {
    if (type === 'success') {
      setSuccessMessage(message);
      setErrorMessage('');
    } else {
      setErrorMessage(message);
      setSuccessMessage('');
    }
    setTimeout(() => {
      setSuccessMessage('');
      setErrorMessage('');
    }, 5000);
  };

  const loadPolicies = async () => {
    try {
      setLoading(true);
      console.log('약관 목록 로드 시도...');
      const response = await fetch('http://localhost:8000/policies');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      console.log('약관 목록 로드 성공:', data);
      setPolicies(data);
    } catch (error: any) {
      console.error('약관 목록 로드 실패:', error);
      showMessage(`약관 목록을 불러오는데 실패했습니다: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadForm(prev => ({ ...prev, file }));
      // 파일명에서 상품명 자동 추출
      if (!uploadForm.productName) {
        const fileName = file.name.replace(/\.[^/.]+$/, "");
        setUploadForm(prev => ({ ...prev, productName: fileName }));
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadForm.file) return;

    try {
      setUploading(true);
      setUploadProgress(0);
      console.log('업로드 시작:', uploadForm);
      
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('company', uploadForm.company);
      formData.append('category', uploadForm.category);
      formData.append('product_type', uploadForm.productType);
      formData.append('product_name', uploadForm.productName);
      formData.append('security_level', uploadForm.securityLevel);

      // 진행률 시뮬레이션 (실제 진행률은 서버에서 제공되어야 함)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('http://localhost:8000/policies/upload', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      console.log('업로드 결과:', result);
      
      setShowUploadModal(false);
      setUploadForm({
        file: null,
        company: '',
        category: '',
        productType: '',
        productName: '',
        securityLevel: 'public'
      });
      setUploadProgress(0);
      loadPolicies();
      showMessage('업로드가 완료되었습니다!', 'success');
    } catch (error: any) {
      console.error('업로드 실패:', error);
      showMessage(`업로드 실패: ${error.message}`, 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleViewPdf = async (policyId: number, policyName: string) => {
    try {
      console.log(`PDF 로드 시도: policyId=${policyId}, policyName=${policyName}`);
      const response = await fetch(`http://localhost:8000/policies/${policyId}/view`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      console.log('PDF URL 생성:', url);
      setSelectedPdfUrl(url);
      setSelectedPolicyName(policyName);
      setShowPdfModal(true);
    } catch (error: any) {
      console.error('PDF 로드 실패:', error);
      showMessage(`PDF 로드 실패: ${error.message}`, 'error');
    }
  };

  const handleViewMd = async (policyId: number, policyName: string) => {
    try {
      console.log(`MD 로드 시도: policyId=${policyId}, policyName=${policyName}`);
      const response = await fetch(`http://localhost:8000/policies/${policyId}/md`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      const mdContent = data?.content || data || 'MD 내용을 찾을 수 없습니다.';
      
      setSelectedMdContent(mdContent);
      setSelectedPolicyName(policyName);
      setShowMdModal(true);
    } catch (error: any) {
      console.error('MD 로드 실패:', error);
      showMessage(`MD 로드 실패: ${error.message}`, 'error');
    }
  };

  const closePdfModal = () => {
    setShowPdfModal(false);
    if (selectedPdfUrl) {
      URL.revokeObjectURL(selectedPdfUrl);
      setSelectedPdfUrl('');
    }
    setSelectedPolicyName('');
  };

  const closeMdModal = () => {
    setShowMdModal(false);
    setSelectedMdContent('');
    setSelectedPolicyName('');
  };

  const handleDelete = async (policyId: number) => {
    if (!window.confirm('정말로 이 약관을 삭제하시겠습니까?')) return;

    try {
      const response = await fetch(`http://localhost:8000/policies/${policyId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      loadPolicies();
      showMessage('약관이 삭제되었습니다.', 'success');
    } catch (error: any) {
      console.error('삭제 실패:', error);
      showMessage(`삭제 실패: ${error.message}`, 'error');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* 헤더 */}
      <div className="flex-shrink-0 p-6 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">약관 관리</h2>
            <p className="text-gray-400 mt-1">보험약관을 업로드하고 관리하세요</p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" />
            약관 업로드
          </button>
        </div>
      </div>

      {/* 메시지 표시 */}
      {(successMessage || errorMessage) && (
        <div className="p-4">
          {successMessage && (
            <div className="bg-green-900/30 border border-green-600 text-green-300 px-4 py-3 rounded-lg flex items-center justify-between">
              <span>{successMessage}</span>
              <button onClick={() => setSuccessMessage('')} className="text-green-400 hover:text-green-200">
                ×
              </button>
            </div>
          )}
          {errorMessage && (
            <div className="bg-red-900/30 border border-red-600 text-red-300 px-4 py-3 rounded-lg flex items-center justify-between">
              <span>{errorMessage}</span>
              <button onClick={() => setErrorMessage('')} className="text-red-400 hover:text-red-200">
                ×
              </button>
            </div>
          )}
        </div>
      )}

      {/* 약관 목록 */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : policies.length === 0 ? (
          <div className="text-center text-gray-400 mt-8">
            <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg">업로드된 약관이 없습니다</p>
            <p className="text-sm mt-2">새 약관을 업로드해보세요</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {policies.map((policy) => (
              <div
                key={policy.policy_id}
                className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {policy.product_name}
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-300 mb-3">
                      <div>
                        <span className="font-medium">보험사:</span> {policy.company || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">분류:</span> {policy.category || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">상품유형:</span> {policy.product_type || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">보안등급:</span> {policy.security_level}
                      </div>
                      {policy.file_size !== undefined && (
                        <div>
                          <span className="font-medium">파일 크기:</span> {(policy.file_size / (1024 * 1024)).toFixed(2)} MB
                        </div>
                      )}
                    </div>
                    {policy.summary && (
                      <p className="text-gray-400 text-sm mb-3 line-clamp-2">
                        {policy.summary}
                      </p>
                    )}
                    <div className="text-xs text-gray-500">
                      업로드일: {formatDate(policy.created_at)}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleViewPdf(policy.policy_id, policy.product_name)}
                      className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-900/20 rounded-lg transition-colors"
                      title="PDF 보기"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleViewMd(policy.policy_id, policy.product_name)}
                      className="p-2 text-green-400 hover:text-green-300 hover:bg-green-900/20 rounded-lg transition-colors"
                      title="MD 보기"
                    >
                      <File className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(policy.policy_id)}
                      className="p-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors"
                      title="삭제"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        </div>
      </div>

      {/* 업로드 모달 */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">약관 업로드</h3>
            
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  파일 선택
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="hidden"
                    id="file-upload"
                    required
                  />
                  <label
                    htmlFor="file-upload"
                    className="w-full flex items-center justify-center px-4 py-3 bg-gray-700 text-gray-300 border-2 border-dashed border-gray-600 rounded-lg cursor-pointer hover:bg-gray-600 hover:border-gray-500 transition-colors"
                  >
                    <Upload className="w-5 h-5 mr-2" />
                    {uploadForm.file ? uploadForm.file.name : 'PDF 파일을 선택하세요'}
                  </label>
                </div>
              </div>

              {uploadProgress > 0 && (
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  보험사
                </label>
                <input
                  type="text"
                  value={uploadForm.company}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, company: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                  placeholder="예: 삼성화재"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  분류
                </label>
                <select
                  value={uploadForm.category}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                  required
                >
                  <option value="">분류를 선택하세요</option>
                  <option value="건강보험">건강보험</option>
                  <option value="자동차보험">자동차보험</option>
                  <option value="생명보험">생명보험</option>
                  <option value="손해보험">손해보험</option>
                  <option value="여행보험">여행보험</option>
                  <option value="기타">기타</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  상품유형
                </label>
                <select
                  value={uploadForm.productType}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, productType: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                  required
                >
                  <option value="">상품유형을 선택하세요</option>
                  <option value="정액형">정액형</option>
                  <option value="실손형">실손형</option>
                  <option value="종합형">종합형</option>
                  <option value="일반형">일반형</option>
                  <option value="특약형">특약형</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  상품명
                </label>
                <input
                  type="text"
                  value={uploadForm.productName}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, productName: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                  placeholder="예: 삼성화재 건강보험 상품"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  보안등급
                </label>
                <select
                  value={uploadForm.securityLevel}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, securityLevel: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                >
                  <option value="public">공개망</option>
                  <option value="semi_closed">조건부 폐쇄망</option>
                  <option value="closed">완전 폐쇄망</option>
                </select>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadForm.file}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {uploading ? '업로드 중...' : '업로드'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PDF 보기 모달 */}
      {showPdfModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full h-full max-w-6xl max-h-[90vh] m-4 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">{selectedPolicyName}</h3>
              <button
                onClick={closePdfModal}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              {selectedPdfUrl && (
                <iframe
                  src={selectedPdfUrl}
                  className="w-full h-full border-0"
                  title="PDF Viewer"
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* MD 보기 모달 */}
      {showMdModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full h-full max-w-6xl max-h-[90vh] m-4 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">{selectedPolicyName} - MD 파일</h3>
              <button
                onClick={closeMdModal}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className="prose max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-code:text-pink-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-100 prose-pre:text-gray-800">
                {selectedMdContent ? (
                  <div className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-4 rounded-lg font-mono">
                    {selectedMdContent}
                  </div>
                ) : (
                  <div className="text-gray-500">MD 파일 내용을 불러오는 중...</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolicyManagement;