import apiService from './api';
import { ValidationResult, ComplianceResult, RuleValidationResult, RiskAssessment, PaginatedResponse } from '@/types';

class ValidationService {
  // Validate document
  async validateDocument(
    documentId: string,
    validationTypes: string[] = ['completeness', 'compliance', 'risk_assessment']
  ): Promise<ValidationResult> {
    const response = await apiService.post('/validation/validate', {
      document_id: documentId,
      validation_types: validationTypes,
    });
    return response.data!;
  }

  // Get validation results
  async getValidationResults(documentId: string): Promise<ValidationResult> {
    const response = await apiService.get(`/validation/results/${documentId}`);
    return response.data!;
  }

  // Get compliance results
  async getComplianceResults(documentId: string): Promise<ComplianceResult> {
    const response = await apiService.get(`/validation/compliance/${documentId}`);
    return response.data!;
  }

  // Get rule validation results
  async getRuleValidationResults(documentId: string): Promise<RuleValidationResult> {
    const response = await apiService.get(`/validation/rules/${documentId}`);
    return response.data!;
  }

  // Get risk assessment results
  async getRiskAssessment(documentId: string): Promise<RiskAssessment> {
    const response = await apiService.get(`/validation/risk/${documentId}`);
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

  // Get validation rules
  async getValidationRules(
    page: number = 1,
    pageSize: number = 20,
    filters?: any
  ): Promise<PaginatedResponse<any>> {
    const params: any = {};

    if (filters?.documentType) params.document_type = filters.documentType;
    if (filters?.ruleType) params.rule_type = filters.ruleType;
    if (filters?.isActive !== undefined) params.is_active = filters.isActive;

    return apiService.getPaginated('/validation/rules', page, pageSize, params);
  }

  // Create validation rule
  async createValidationRule(ruleData: any): Promise<any> {
    const response = await apiService.post('/validation/rules', ruleData);
    return response.data;
  }

  // Update validation rule
  async updateValidationRule(ruleId: string, ruleData: any): Promise<any> {
    const response = await apiService.put(`/validation/rules/${ruleId}`, ruleData);
    return response.data;
  }

  // Delete validation rule
  async deleteValidationRule(ruleId: string): Promise<void> {
    await apiService.delete(`/validation/rules/${ruleId}`);
  }

  // Get validation statistics
  async getValidationStats(
    dateRange?: [string, string],
    companyId?: number
  ): Promise<any> {
    const params: any = {};
    if (dateRange) {
      params.startDate = dateRange[0];
      params.endDate = dateRange[1];
    }
    if (companyId) params.companyId = companyId;

    const response = await apiService.get('/validation/stats', params);
    return response.data;
  }

  // Get compliance trends
  async getComplianceTrends(
    dateRange?: [string, string],
    companyId?: number
  ): Promise<any> {
    const params: any = {};
    if (dateRange) {
      params.startDate = dateRange[0];
      params.endDate = dateRange[1];
    }
    if (companyId) params.companyId = companyId;

    const response = await apiService.get('/validation/trends/compliance', params);
    return response.data;
  }

  // Get risk trends
  async getRiskTrends(
    dateRange?: [string, string],
    companyId?: number
  ): Promise<any> {
    const params: any = {};
    if (dateRange) {
      params.startDate = dateRange[0];
      params.endDate = dateRange[1];
    }
    if (companyId) params.companyId = companyId;

    const response = await apiService.get('/validation/trends/risk', params);
    return response.data;
  }

  // Get validation summary by document type
  async getValidationSummaryByDocumentType(
    dateRange?: [string, string],
    companyId?: number
  ): Promise<any> {
    const params: any = {};
    if (dateRange) {
      params.startDate = dateRange[0];
      params.endDate = dateRange[1];
    }
    if (companyId) params.companyId = companyId;

    const response = await apiService.get('/validation/summary/document-types', params);
    return response.data;
  }

  // Get common validation issues
  async getCommonValidationIssues(
    dateRange?: [string, string],
    companyId?: number,
    limit: number = 10
  ): Promise<any> {
    const params: any = { limit };
    if (dateRange) {
      params.startDate = dateRange[0];
      params.endDate = dateRange[1];
    }
    if (companyId) params.companyId = companyId;

    const response = await apiService.get('/validation/issues/common', params);
    return response.data;
  }

  // Get validation queue status
  async getValidationQueueStatus(): Promise<any> {
    const response = await apiService.get('/validation/queue/status');
    return response.data;
  }

  // Batch validate documents
  async batchValidateDocuments(
    documentIds: string[],
    validationTypes: string[] = ['completeness', 'compliance', 'risk_assessment']
  ): Promise<any[]> {
    const response = await apiService.post('/validation/batch', {
      document_ids: documentIds,
      validation_types: validationTypes,
    });
    return response.data || [];
  }

  // Get validation history
  async getValidationHistory(
    documentId: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<PaginatedResponse<ValidationResult>> {
    return apiService.getPaginated(`/validation/history/${documentId}`, page, pageSize);
  }

  // Export validation results
  async exportValidationResults(
    filters: any,
    format: string = 'csv'
  ): Promise<any> {
    const response = await apiService.post('/validation/export', {
      filters,
      format,
    });
    return response.data;
  }

  // Get validation performance metrics
  async getValidationPerformanceMetrics(
    dateRange?: [string, string]
  ): Promise<any> {
    const params: any = {};
    if (dateRange) {
      params.startDate = dateRange[0];
      params.endDate = dateRange[1];
    }

    const response = await apiService.get('/validation/performance', params);
    return response.data;
  }

  // Trigger validation for AI results
  async validateAIResults(
    aiResults: any,
    documentType: string,
    validationTypes: string[] = ['completeness', 'compliance', 'risk_assessment']
  ): Promise<ValidationResult> {
    const response = await apiService.post('/validation/validate-ai', {
      ai_results: aiResults,
      document_type: documentType,
      validation_types: validationTypes,
    });
    return response.data!;
  }
}

export default new ValidationService();