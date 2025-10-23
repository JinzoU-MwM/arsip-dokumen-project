export interface User {
  id: number;
  email: string;
  username: string;
  fullName: string;
  role: UserRole;
  companyId?: number;
  permissions: string[];
  isActive: boolean;
  createdAt: string;
  lastLogin?: string;
}

export interface Company {
  id: number;
  name: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  industry?: string;
  size?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Document {
  id: string;
  name: string;
  documentType: DocumentType;
  mimeType: string;
  size: number;
  createdTime: string;
  modifiedTime: string;
  companyId: number;
  userId?: number;
  driveUrl: string;
  thumbnailLink?: string;
  description?: string;
  tags: string[];
  processingStatus: ProcessingStatus;
  validationResults?: ValidationResult;
  riskAssessment?: RiskAssessment;
}

export interface ValidationResult {
  success: boolean;
  validationType: ValidationType;
  documentType: DocumentType;
  complianceResult?: ComplianceResult;
  ruleResult?: RuleValidationResult;
  riskAssessment?: RiskAssessment;
  timestamp: string;
  processingTimeMs?: number;
}

export interface ComplianceResult {
  isCompliant: boolean;
  complianceScore: number;
  issues: ComplianceIssue[];
  missingFields: string[];
  validationSummary: string;
  recommendations: string[];
}

export interface ComplianceIssue {
  fieldName: string;
  issueType: string;
  description: string;
  severity: SeverityLevel;
  suggestedFix?: string;
}

export interface RuleValidationResult {
  validationPassed: boolean;
  rulesChecked: number;
  rulesPassed: number;
  rulesFailed: number;
  failedRules: FailedRule[];
  validationSummary: string;
}

export interface FailedRule {
  ruleId: string;
  ruleName: string;
  ruleType: string;
  severity: string;
  description: string;
  details: any;
}

export interface RiskAssessment {
  riskLevel: SeverityLevel;
  riskScore: number;
  riskFactors: RiskFactor[];
  mitigationSuggestions: string[];
  assessmentSummary: string;
}

export interface RiskFactor {
  type: string;
  field?: string;
  description: string;
  severity: SeverityLevel;
  score: number;
  details?: any;
}

export interface AuditEvent {
  eventId: string;
  timestamp: string;
  userId?: number;
  companyId?: number;
  eventType: string;
  eventCategory: string;
  resourceType?: string;
  resourceId?: string;
  action: string;
  description: string;
  outcome: string;
  ipAddress?: string;
  userAgent?: string;
  details?: any;
}

export interface ComplianceReport {
  reportId: string;
  reportType: ReportType;
  generatedAt: string;
  startPeriod: string;
  endPeriod: string;
  companyId?: number;
  complianceScore: number;
  summary: any;
  findings: any[];
  recommendations: string[];
  status: string;
}

export interface DashboardStats {
  totalDocuments: number;
  documentsToday: number;
  totalUsers: number;
  activeUsers: number;
  totalCompanies: number;
  activeCompanies: number;
  validationStats: {
    total: number;
    compliant: number;
    nonCompliant: number;
    pending: number;
  };
  riskStats: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  recentActivity: ActivityItem[];
  securityAlerts: SecurityAlert[];
}

export interface ActivityItem {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  userId?: number;
  userName?: string;
  companyId?: number;
  companyName?: string;
}

export interface SecurityAlert {
  id: string;
  type: string;
  severity: SeverityLevel;
  description: string;
  timestamp: string;
  userId?: number;
  resolved: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  totalCount: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface FilterOptions {
  dateRange?: [string, string];
  companyId?: number;
  userId?: number;
  documentType?: DocumentType;
  validationType?: ValidationType;
  riskLevel?: SeverityLevel;
  outcome?: string;
  search?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

// Enums
export enum UserRole {
  ADMIN = 'admin',
  LEGAL_ADMIN = 'legal_admin',
  COMPANY_USER = 'company_user',
  VIEWER = 'viewer'
}

export enum DocumentType {
  KTP = 'ktp',
  KK = 'kk',
  AKTA_KELAHIRAN = 'akta_kelahiran',
  AKTA_KEMATIAN = 'akta_kematian',
  AKTA_PERNIKAHAN = 'akta_pernikahan',
  AKTA_PERCERAIAN = 'akta_perceraian',
  IZIN_LOKASI = 'izin_lokasi',
  SURAT_KEPEMILIKAN_TANAH = 'surat_kepemilikan_tanah',
  NPWP = 'npwp',
  SIUP = 'siup',
  TDP = 'tdp',
  LAINNYA = 'lainnya'
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum ValidationType {
  COMPLETENESS = 'completeness',
  COMPLIANCE = 'compliance',
  RISK_ASSESSMENT = 'risk_assessment',
  RULE_VALIDATION = 'rule_validation'
}

export enum SeverityLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum ReportType {
  STANDARD = 'standard',
  SECURITY = 'security',
  ACCESS = 'access',
  DATA_PROTECTION = 'data_protection',
  USER_ACTIVITY = 'user_activity',
  SYSTEM_AUDIT = 'system_audit',
  FULL = 'full'
}

// Form Types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface UserFormData {
  email: string;
  username: string;
  fullName: string;
  role: UserRole;
  companyId?: number;
  phoneNumber?: string;
  password?: string;
}

export interface CompanyFormData {
  name: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  industry?: string;
  size?: string;
}

export interface ValidationRuleFormData {
  name: string;
  documentType: DocumentType;
  ruleType: string;
  condition: any;
  severity: SeverityLevel;
  description?: string;
  isActive: boolean;
}

// Chart Data Types
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
}

// Navigation Types
export interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  children?: NavigationItem[];
  permissions?: string[];
}