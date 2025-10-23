import apiService from './api';
import { Document, ValidationResult, PaginatedResponse, FilterOptions, UploadProgress } from '@/types';

class DocumentService {
  // Get documents with pagination and filtering
  async getDocuments(
    page: number = 1,
    pageSize: number = 20,
    filters?: FilterOptions
  ): Promise<PaginatedResponse<Document>> {
    const params: any = {};

    if (filters?.companyId) params.companyId = filters.companyId;
    if (filters?.userId) params.userId = filters.userId;
    if (filters?.documentType) params.documentType = filters.documentType;
    if (filters?.search) params.search = filters.search;
    if (filters?.dateRange) {
      params.startDate = filters.dateRange[0];
      params.endDate = filters.dateRange[1];
    }

    return apiService.getPaginated('/drive/files', page, pageSize, params);
  }

  // Get single document
  async getDocument(documentId: string): Promise<Document> {
    const response = await apiService.get(`/drive/files/${documentId}`);
    return response.data!;
  }

  // Upload document
  async uploadDocument(
    file: File,
    companyId: number,
    documentType: string,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<{ document: Document; validation: ValidationResult }> {
    const additionalData = {
      company_id: companyId,
      document_type: documentType,
    };

    return new Promise((resolve, reject) => {
      const progressCallback = (percentage: number) => {
        if (onProgress) {
          onProgress({
            loaded: percentage,
            total: 100,
            percentage,
            status: 'uploading',
          });
        }
      };

      apiService.uploadFile('/drive/upload', file, additionalData, progressCallback)
        .then((response) => {
          if (onProgress) {
            onProgress({
              loaded: 100,
              total: 100,
              percentage: 100,
              status: 'completed',
            });
          }
          resolve(response.data);
        })
        .catch((error) => {
          if (onProgress) {
            onProgress({
              loaded: 0,
              total: 100,
              percentage: 0,
              status: 'error',
              error: error.message,
            });
          }
          reject(error);
        });
    });
  }

  // Batch upload documents
  async uploadDocuments(
    files: File[],
    companyId: number,
    documentTypes: string[],
    onProgress?: (fileIndex: number, progress: UploadProgress) => void
  ): Promise<any[]> {
    const results = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const documentType = documentTypes[i] || 'lainnya';

      try {
        const result = await this.uploadDocument(
          file,
          companyId,
          documentType,
          (progress) => onProgress?.(i, progress)
        );
        results.push({ success: true, file: file.name, result });
      } catch (error: any) {
        results.push({ success: false, file: file.name, error: error.message });
      }
    }

    return results;
  }

  // Download document
  async downloadDocument(documentId: string, filename?: string): Promise<void> {
    await apiService.downloadFile(`/drive/files/${documentId}/download`, filename);
  }

  // Delete document
  async deleteDocument(documentId: string): Promise<void> {
    await apiService.delete(`/drive/files/${documentId}`);
  }

  // Update document metadata
  async updateDocument(documentId: string, metadata: Partial<Document>): Promise<Document> {
    const response = await apiService.put(`/drive/files/${documentId}`, metadata);
    return response.data!;
  }

  // Get document validation results
  async getValidationResults(documentId: string): Promise<ValidationResult> {
    const response = await apiService.get(`/validation/results/${documentId}`);
    return response.data!;
  }

  // Revalidate document
  async revalidateDocument(
    documentId: string,
    validationTypes: string[] = ['completeness', 'compliance', 'risk_assessment']
  ): Promise<ValidationResult> {
    const response = await apiService.post('/validation/revalidate', {
      document_id: documentId,
      validation_types: validationTypes,
    });
    return response.data!;
  }

  // Get document thumbnail
  getDocumentThumbnailUrl(documentId: string): string {
    return `${apiService['client'].defaults.baseURL}/drive/files/${documentId}/thumbnail`;
  }

  // Get document preview URL
  getDocumentPreviewUrl(documentId: string): string {
    return `${apiService['client'].defaults.baseURL}/drive/files/${documentId}/preview`;
  }

  // Search documents
  async searchDocuments(
    query: string,
    filters?: FilterOptions
  ): Promise<PaginatedResponse<Document>> {
    const params: any = { query };

    if (filters?.companyId) params.companyId = filters.companyId;
    if (filters?.documentType) params.documentType = filters.documentType;
    if (filters?.dateRange) {
      params.startDate = filters.dateRange[0];
      params.endDate = filters.dateRange[1];
    }

    return apiService.getPaginated('/drive/search', 1, 50, params);
  }

  // Get documents by company
  async getCompanyDocuments(
    companyId: number,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<Document>> {
    return this.getDocuments(page, pageSize, { companyId });
  }

  // Get documents by user
  async getUserDocuments(
    userId: number,
    page: number = 1,
    pageSize: number = 20
  ): Promise<PaginatedResponse<Document>> {
    return this.getDocuments(page, pageSize, { userId });
  }

  // Share document
  async shareDocument(
    documentId: string,
    email: string,
    role: string = 'reader'
  ): Promise<any> {
    const response = await apiService.post(`/drive/files/${documentId}/share`, {
      email,
      role,
    });
    return response.data;
  }

  // Get document sharing info
  async getDocumentSharing(documentId: string): Promise<any> {
    const response = await apiService.get(`/drive/files/${documentId}/sharing`);
    return response.data;
  }

  // Update document sharing
  async updateDocumentSharing(
    documentId: string,
    shareId: string,
    role: string
  ): Promise<any> {
    const response = await apiService.put(`/drive/files/${documentId}/sharing/${shareId}`, {
      role,
    });
    return response.data;
  }

  // Remove document sharing
  async removeDocumentSharing(documentId: string, shareId: string): Promise<void> {
    await apiService.delete(`/drive/files/${documentId}/sharing/${shareId}`);
  }

  // Get document analytics
  async getDocumentAnalytics(
    documentId: string,
    dateRange?: [string, string]
  ): Promise<any> {
    const params: any = {};
    if (dateRange) {
      params.startDate = dateRange[0];
      params.endDate = dateRange[1];
    }

    const response = await apiService.get(`/drive/files/${documentId}/analytics`, params);
    return response.data;
  }

  // Get document versions
  async getDocumentVersions(documentId: string): Promise<any[]> {
    const response = await apiService.get(`/drive/files/${documentId}/versions`);
    return response.data || [];
  }

  // Restore document version
  async restoreDocumentVersion(documentId: string, versionId: string): Promise<Document> {
    const response = await apiService.post(`/drive/files/${documentId}/versions/${versionId}/restore`);
    return response.data!;
  }
}

export default new DocumentService();