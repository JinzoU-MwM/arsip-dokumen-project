"""
Pydantic models for the Validation Engine Service
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class ValidationType(str, Enum):
    """Types of validation that can be performed"""
    COMPLETENESS = "completeness"
    COMPLIANCE = "compliance"
    RISK_ASSESSMENT = "risk_assessment"
    RULE_VALIDATION = "rule_validation"


class SeverityLevel(str, Enum):
    """Severity levels for compliance issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleType(str, Enum):
    """Types of compliance rules"""
    REQUIREMENT = "requirement"  # Must have certain fields
    FORBIDDEN = "forbidden"      # Cannot have certain fields
    CONDITIONAL = "conditional"  # Dependent conditions
    FORMAT = "format"           # Format validation rules


class ComplianceStatus(str, Enum):
    """Compliance status values"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING_REVIEW = "pending_review"


class DocumentType(str, Enum):
    """Supported document types"""
    KTP = "ktp"
    KK = "kk"
    AKTA_KELAHIRAN = "akta_kelahiran"
    AKTA_KEMATIAN = "akta_kematian"
    AKTA_PERNIKAHAN = "akta_pernikahan"
    AKTA_PERCERAIAN = "akta_perceraian"
    IZIN_LOKASI = "izin_lokasi"
    SURAT_KEPEMILIKAN_TANAH = "surat_kepemilikan_tanah"
    NPWP = "npwp"
    SIUP = "siup"
    TDP = "tdp"
    LAINNYA = "lainnya"


# Request Models
class ValidationRequest(BaseModel):
    """Request model for document validation"""
    ai_results: Dict[str, Any] = Field(..., description="AI extraction results")
    document_type: DocumentType = Field(..., description="Type of document")
    company_info: Optional[Dict[str, Any]] = Field(None, description="Company information")
    validation_type: ValidationType = Field(ValidationType.COMPLETENESS, description="Type of validation")
    user_id: Optional[int] = Field(None, description="User requesting validation")


class ComplianceRule(BaseModel):
    """Model for compliance rules"""
    id: Optional[str] = None
    name: str = Field(..., description="Rule name")
    document_type: DocumentType = Field(..., description="Applicable document type")
    rule_type: RuleType = Field(..., description="Type of rule")
    condition: Dict[str, Any] = Field(..., description="Rule condition definition")
    severity: SeverityLevel = Field(SeverityLevel.MEDIUM, description="Rule severity")
    description: Optional[str] = Field(None, description="Rule description")
    is_active: bool = Field(True, description="Whether rule is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ComplianceRuleCreate(BaseModel):
    """Request model for creating compliance rules"""
    name: str = Field(..., description="Rule name")
    document_type: DocumentType = Field(..., description="Applicable document type")
    rule_type: RuleType = Field(..., description="Type of rule")
    condition: Dict[str, Any] = Field(..., description="Rule condition definition")
    severity: SeverityLevel = Field(SeverityLevel.MEDIUM, description="Rule severity")
    description: Optional[str] = Field(None, description="Rule description")
    is_active: bool = Field(True, description="Whether rule is active")


class ComplianceRuleUpdate(BaseModel):
    """Request model for updating compliance rules"""
    name: Optional[str] = None
    rule_type: Optional[RuleType] = None
    condition: Optional[Dict[str, Any]] = None
    severity: Optional[SeverityLevel] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# Response Models
class ComplianceIssue(BaseModel):
    """Individual compliance issue"""
    field_name: str = Field(..., description="Field that has the issue")
    issue_type: str = Field(..., description="Type of issue")
    description: str = Field(..., description="Issue description")
    severity: SeverityLevel = Field(..., description="Issue severity")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the issue")


class ComplianceResult(BaseModel):
    """Result of compliance validation"""
    is_compliant: bool = Field(..., description="Whether document is compliant")
    compliance_score: float = Field(..., description="Compliance score (0-100)")
    issues: List[ComplianceIssue] = Field(default_factory=list, description="List of compliance issues")
    missing_fields: List[str] = Field(default_factory=list, description="Missing required fields")
    validation_summary: str = Field(..., description="Summary of validation results")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")


class RuleValidationResult(BaseModel):
    """Result of rule-based validation"""
    validation_passed: bool = Field(..., description="Whether validation passed")
    rules_checked: int = Field(..., description="Number of rules checked")
    rules_passed: int = Field(..., description="Number of rules passed")
    rules_failed: int = Field(..., description="Number of rules failed")
    failed_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Details of failed rules")
    validation_summary: str = Field(..., description="Summary of rule validation")


class RiskAssessment(BaseModel):
    """Risk assessment result"""
    risk_level: SeverityLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., description="Risk score (0-100)")
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Identified risk factors")
    mitigation_suggestions: List[str] = Field(default_factory=list, description="Suggestions for risk mitigation")
    assessment_summary: str = Field(..., description="Summary of risk assessment")


class ValidationResponse(BaseModel):
    """Complete validation response"""
    success: bool = Field(..., description="Whether validation was successful")
    validation_type: ValidationType = Field(..., description="Type of validation performed")
    document_type: DocumentType = Field(..., description="Type of document validated")
    ai_results: Dict[str, Any] = Field(..., description="Original AI extraction results")
    company_info: Dict[str, Any] = Field(default_factory=dict, description="Company information")
    timestamp: float = Field(..., description="Validation timestamp")
    compliance_result: Optional[ComplianceResult] = Field(None, description="Compliance validation result")
    rule_result: Optional[RuleValidationResult] = Field(None, description="Rule validation result")
    risk_assessment: Optional[RiskAssessment] = Field(None, description="Risk assessment result")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


# Statistics Models
class ValidationStats(BaseModel):
    """Validation service statistics"""
    total_validations: int = Field(..., description="Total validations performed")
    successful_validations: int = Field(..., description="Successful validations")
    failed_validations: int = Field(..., description="Failed validations")
    average_processing_time: float = Field(..., description="Average processing time (ms)")
    compliance_rate: float = Field(..., description="Overall compliance rate")
    document_type_stats: Dict[str, int] = Field(default_factory=dict, description="Stats by document type")
    last_updated: datetime = Field(..., description="Last updated timestamp")


class ServiceHealth(BaseModel):
    """Service health information"""
    status: str = Field(..., description="Service status")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    version: str = Field(..., description="Service version")
    components: Dict[str, bool] = Field(..., description="Component health status")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")


# Error Models
class ValidationError(BaseModel):
    """Validation error information"""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    field_name: Optional[str] = Field(None, description="Field that caused the error")
    severity: SeverityLevel = Field(SeverityLevel.MEDIUM, description="Error severity")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class BulkValidationRequest(BaseModel):
    """Request for bulk validation of multiple documents"""
    documents: List[ValidationRequest] = Field(..., description="Documents to validate")
    validation_types: List[ValidationType] = Field(default_factory=list, description="Validations to perform")
    user_id: Optional[int] = Field(None, description="User requesting validation")


class BulkValidationResponse(BaseModel):
    """Response for bulk validation"""
    total_documents: int = Field(..., description="Total documents processed")
    successful_validations: int = Field(..., description="Successful validations")
    failed_validations: int = Field(..., description="Failed validations")
    results: List[ValidationResponse] = Field(..., description="Validation results")
    processing_time_ms: float = Field(..., description="Total processing time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")