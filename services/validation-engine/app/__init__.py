"""
Validation Engine Service
Handles compliance validation, document completeness checking, and risk assessment
"""

from .main import app
from .compliance_checker import ComplianceChecker
from .rule_engine import RuleEngine
from .risk_assessor import RiskAssessor
from .models import (
    ValidationRequest,
    ValidationResponse,
    ComplianceRule,
    ComplianceRuleCreate,
    ComplianceRuleUpdate,
    ComplianceResult,
    RuleValidationResult,
    RiskAssessment,
    ValidationType,
    SeverityLevel,
    RuleType,
    DocumentType,
    ComplianceStatus,
    ValidationStats,
    ServiceHealth,
    ValidationError,
    BulkValidationRequest,
    BulkValidationResponse
)

__version__ = "1.0.0"
__service_name__ = "validation-engine"

__all__ = [
    "app",
    "ComplianceChecker",
    "RuleEngine",
    "RiskAssessor",
    "ValidationRequest",
    "ValidationResponse",
    "ComplianceRule",
    "ComplianceRuleCreate",
    "ComplianceRuleUpdate",
    "ComplianceResult",
    "RuleValidationResult",
    "RiskAssessment",
    "ValidationType",
    "SeverityLevel",
    "RuleType",
    "DocumentType",
    "ComplianceStatus",
    "ValidationStats",
    "ServiceHealth",
    "ValidationError",
    "BulkValidationRequest",
    "BulkValidationResponse"
]