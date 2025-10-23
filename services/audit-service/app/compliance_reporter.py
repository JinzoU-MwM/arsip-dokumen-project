"""
Compliance Reporter
Generates compliance reports and ensures regulatory requirements are met
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta
from jinja2 import Template
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from .models import (
    ComplianceReport,
    ReportType,
    ComplianceMetrics
)


class ComplianceReporter:
    """Service for generating compliance reports"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="ComplianceReporter")
        self.report_cache = {}
        self.compliance_standards = {
            "SOC2": {
                "name": "SOC 2 Type II",
                "requirements": [
                    "audit_trail_completeness",
                    "data_access_logging",
                    "change_management",
                    "incident_response",
                    "risk_assessment"
                ]
            },
            "ISO27001": {
                "name": "ISO 27001",
                "requirements": [
                    "information_security_policy",
                    "access_control",
                    "cryptography",
                    "physical_security",
                    "operations_security"
                ]
            },
            "GDPR": {
                "name": "GDPR",
                "requirements": [
                    "data_protection",
                    "consent_management",
                    "data_breach_notification",
                    "data_subject_rights",
                    "privacy_by_design"
                ]
            }
        }

    async def initialize(self):
        """Initialize the compliance reporter"""
        self.logger.info("Initializing Compliance Reporter")

        try:
            # Load report templates
            await self._load_report_templates()

            # Initialize compliance checks
            await self._initialize_compliance_checks()

            self.logger.info("Compliance Reporter initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize Compliance Reporter", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Compliance Reporter")
        self.report_cache.clear()

    async def generate_report(
        self,
        start_date: datetime,
        end_date: datetime,
        company_id: Optional[int] = None,
        report_type: str = "standard"
    ) -> ComplianceReport:
        """Generate compliance report"""
        try:
            report_id = str(uuid.uuid4())
            generated_at = datetime.utcnow()

            self.logger.info("Generating compliance report",
                           report_id=report_id,
                           report_type=report_type,
                           start_date=start_date,
                           end_date=end_date,
                           company_id=company_id)

            # Gather compliance data
            compliance_data = await self._gather_compliance_data(start_date, end_date, company_id)

            # Analyze compliance
            compliance_analysis = await self._analyze_compliance(compliance_data, report_type)

            # Generate findings and recommendations
            findings = await self._generate_findings(compliance_analysis, report_type)
            recommendations = await self._generate_recommendations(findings, report_type)

            # Calculate compliance score
            compliance_score = await self._calculate_compliance_score(compliance_analysis)

            # Generate summary
            summary = await self._generate_summary(compliance_analysis, compliance_score, report_type)

            # Create report object
            report = ComplianceReport(
                report_id=report_id,
                report_type=ReportType(report_type),
                generated_at=generated_at,
                generated_by=1,  # Would get from auth context
                start_date=start_date,
                end_date=end_date,
                company_id=company_id,
                summary=summary,
                findings=findings,
                recommendations=recommendations,
                statistics=compliance_analysis.get("statistics", {}),
                status="generated"
            )

            # Generate report file
            file_path = await self._generate_report_file(report)
            report.file_path = file_path

            # Cache the report
            self.report_cache[report_id] = report

            self.logger.info("Compliance report generated successfully",
                           report_id=report_id,
                           compliance_score=compliance_score)

            return report

        except Exception as e:
            self.logger.error("Compliance report generation failed", error=str(e))
            raise

    async def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get compliance report by ID"""
        try:
            # Check cache first
            if report_id in self.report_cache:
                return self.report_cache[report_id]

            # Load from database
            report = await self._load_report_from_database(report_id)
            if report:
                self.report_cache[report_id] = report

            return report

        except Exception as e:
            self.logger.error("Failed to get compliance report", report_id=report_id, error=str(e))
            return None

    async def get_compliance_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        company_id: Optional[int] = None
    ) -> ComplianceMetrics:
        """Get compliance metrics"""
        try:
            compliance_data = await self._gather_compliance_data(start_date, end_date, company_id)
            analysis = await self._analyze_compliance(compliance_data, "standard")

            return ComplianceMetrics(
                compliance_score=analysis.get("overall_score", 0),
                audit_trail_coverage=analysis.get("audit_trail_coverage", 0),
                data_access_logs=analysis.get("data_access_logging", 0),
                authentication_events=analysis.get("auth_events_count", 0),
                authorization_events=analysis.get("authz_events_count", 0),
                data_modification_events=analysis.get("data_mod_events_count", 0),
                compliance_gaps=analysis.get("compliance_gaps", []),
                recommendations=analysis.get("recommendations", [])
            )

        except Exception as e:
            self.logger.error("Failed to get compliance metrics", error=str(e))
            raise

    async def _gather_compliance_data(
        self,
        start_date: datetime,
        end_date: datetime,
        company_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gather data for compliance analysis"""
        try:
            # Would query actual database here
            # This is a placeholder implementation
            data = {
                "audit_events": await self._get_audit_events(start_date, end_date, company_id),
                "security_events": await self._get_security_events(start_date, end_date, company_id),
                "user_activities": await self._get_user_activities(start_date, end_date, company_id),
                "data_access_logs": await self._get_data_access_logs(start_date, end_date, company_id),
                "system_changes": await self._get_system_changes(start_date, end_date, company_id),
                "incidents": await self._get_incidents(start_date, end_date, company_id)
            }

            return data

        except Exception as e:
            self.logger.error("Failed to gather compliance data", error=str(e))
            raise

    async def _analyze_compliance(self, data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Analyze compliance data"""
        try:
            analysis = {
                "statistics": {},
                "compliance_gaps": [],
                "recommendations": [],
                "overall_score": 0
            }

            # Analyze audit trail coverage
            audit_coverage = await self._analyze_audit_trail_coverage(data)
            analysis["audit_trail_coverage"] = audit_coverage["coverage_percentage"]
            analysis["statistics"]["audit_events"] = audit_coverage["total_events"]
            analysis["statistics"]["event_types_covered"] = audit_coverage["event_types"]

            # Analyze data access logging
            access_logging = await self._analyze_data_access_logging(data)
            analysis["data_access_logging"] = access_logging["coverage_percentage"]
            analysis["statistics"]["data_access_events"] = access_logging["total_events"]
            analysis["statistics"]["unauthorized_access"] = access_logging["unauthorized_events"]

            # Analyze authentication and authorization
            auth_analysis = await self._analyze_auth_events(data)
            analysis["auth_events_count"] = auth_analysis["auth_events"]
            analysis["authz_events_count"] = auth_analysis["authz_events"]
            analysis["statistics"]["failed_logins"] = auth_analysis["failed_logins"]

            # Analyze data modification events
            data_mod_analysis = await self._analyze_data_modification(data)
            analysis["data_mod_events_count"] = data_mod_analysis["modification_events"]
            analysis["statistics"]["data_modifications"] = data_mod_analysis["total_modifications"]

            # Identify compliance gaps
            analysis["compliance_gaps"] = await self._identify_compliance_gaps(analysis)

            # Calculate overall score
            analysis["overall_score"] = await self._calculate_compliance_score(analysis)

            return analysis

        except Exception as e:
            self.logger.error("Failed to analyze compliance", error=str(e))
            raise

    async def _analyze_audit_trail_coverage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audit trail coverage"""
        try:
            audit_events = data.get("audit_events", [])
            total_events = len(audit_events)

            if total_events == 0:
                return {"coverage_percentage": 0, "total_events": 0, "event_types": []}

            # Check event type coverage
            required_event_types = [
                "user_login", "user_logout", "data_access", "data_modification",
                "permission_change", "system_configuration", "security_event"
            ]

            covered_types = set()
            for event in audit_events:
                covered_types.add(event.get("event_type", ""))

            coverage_percentage = (len(covered_types.intersection(required_event_types)) / len(required_event_types)) * 100

            return {
                "coverage_percentage": coverage_percentage,
                "total_events": total_events,
                "event_types": list(covered_types)
            }

        except Exception as e:
            self.logger.error("Failed to analyze audit trail coverage", error=str(e))
            return {"coverage_percentage": 0, "total_events": 0, "event_types": []}

    async def _analyze_data_access_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data access logging"""
        try:
            access_logs = data.get("data_access_logs", [])
            total_events = len(access_logs)

            # Check if all access is properly logged
            unauthorized_events = [log for log in access_logs if log.get("outcome") == "denied"]

            coverage_percentage = min(100, (total_events / max(1, total_events + len(unauthorized_events))) * 100)

            return {
                "coverage_percentage": coverage_percentage,
                "total_events": total_events,
                "unauthorized_events": len(unauthorized_events)
            }

        except Exception as e:
            self.logger.error("Failed to analyze data access logging", error=str(e))
            return {"coverage_percentage": 0, "total_events": 0, "unauthorized_events": 0}

    async def _analyze_auth_events(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze authentication and authorization events"""
        try:
            audit_events = data.get("audit_events", [])
            auth_events = [e for e in audit_events if e.get("event_type") in ["user_login", "user_logout"]]
            authz_events = [e for e in audit_events if e.get("event_type") in ["permission_granted", "permission_revoked"]]
            failed_logins = [e for e in audit_events if e.get("event_type") == "failed_login"]

            return {
                "auth_events": len(auth_events),
                "authz_events": len(authz_events),
                "failed_logins": len(failed_logins)
            }

        except Exception as e:
            self.logger.error("Failed to analyze auth events", error=str(e))
            return {"auth_events": 0, "authz_events": 0, "failed_logins": 0}

    async def _analyze_data_modification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data modification events"""
        try:
            audit_events = data.get("audit_events", [])
            modification_events = [e for e in audit_events if e.get("event_category") == "data_modification"]

            return {
                "modification_events": len(modification_events),
                "total_modifications": len(modification_events)
            }

        except Exception as e:
            self.logger.error("Failed to analyze data modification", error=str(e))
            return {"modification_events": 0, "total_modifications": 0}

    async def _identify_compliance_gaps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify compliance gaps"""
        try:
            gaps = []

            # Check audit trail coverage
            if analysis.get("audit_trail_coverage", 0) < 90:
                gaps.append({
                    "area": "Audit Trail Coverage",
                    "severity": "high" if analysis["audit_trail_coverage"] < 70 else "medium",
                    "description": f"Audit trail coverage is {analysis['audit_trail_coverage']:.1f}%, below recommended 90%",
                    "recommendation": "Implement comprehensive logging for all critical system events"
                })

            # Check data access logging
            if analysis.get("data_access_logging", 0) < 95:
                gaps.append({
                    "area": "Data Access Logging",
                    "severity": "high" if analysis["data_access_logging"] < 80 else "medium",
                    "description": f"Data access logging coverage is {analysis['data_access_logging']:.1f}%",
                    "recommendation": "Ensure all data access attempts are properly logged"
                })

            # Check failed login rate
            failed_logins = analysis.get("statistics", {}).get("failed_logins", 0)
            auth_events = analysis.get("auth_events_count", 0)
            if auth_events > 0:
                failure_rate = (failed_logins / auth_events) * 100
                if failure_rate > 10:
                    gaps.append({
                        "area": "Authentication Security",
                        "severity": "high",
                        "description": f"Failed login rate is {failure_rate:.1f}%, indicating potential brute force attacks",
                        "recommendation": "Implement account lockout policies and enhanced monitoring"
                    })

            return gaps

        except Exception as e:
            self.logger.error("Failed to identify compliance gaps", error=str(e))
            return []

    async def _calculate_compliance_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        try:
            scores = []

            # Audit trail coverage (30% weight)
            audit_score = min(100, analysis.get("audit_trail_coverage", 0))
            scores.append(("audit_trail", audit_score, 0.3))

            # Data access logging (25% weight)
            access_score = min(100, analysis.get("data_access_logging", 0))
            scores.append(("data_access", access_score, 0.25))

            # Authentication events (20% weight)
            auth_events = analysis.get("auth_events_count", 0)
            auth_score = min(100, (auth_events / 100) * 100) if auth_events > 0 else 0
            scores.append(("authentication", auth_score, 0.2))

            # Data modification logging (15% weight)
            data_mod_score = 100 if analysis.get("data_mod_events_count", 0) > 0 else 50
            scores.append(("data_modification", data_mod_score, 0.15))

            # Security event logging (10% weight)
            security_score = 100 if analysis.get("statistics", {}).get("security_events", 0) > 0 else 80
            scores.append(("security", security_score, 0.1))

            # Calculate weighted average
            total_score = sum(score * weight for _, score, weight in scores)

            return round(total_score, 1)

        except Exception as e:
            self.logger.error("Failed to calculate compliance score", error=str(e))
            return 0.0

    async def _generate_findings(self, analysis: Dict[str, Any], report_type: str) -> List[Dict[str, Any]]:
        """Generate compliance findings"""
        try:
            findings = []

            # Overall compliance status
            overall_score = analysis.get("overall_score", 0)
            if overall_score >= 90:
                compliance_status = "Excellent"
            elif overall_score >= 80:
                compliance_status = "Good"
            elif overall_score >= 70:
                compliance_status = "Needs Improvement"
            else:
                compliance_status = "Non-Compliant"

            findings.append({
                "category": "Overall Compliance",
                "status": compliance_status,
                "score": overall_score,
                "description": f"Overall compliance score is {overall_score:.1f}%",
                "impact": "High" if overall_score < 70 else "Medium" if overall_score < 85 else "Low"
            })

            # Add specific findings for each area
            findings.extend(await self._generate_specific_findings(analysis))

            return findings

        except Exception as e:
            self.logger.error("Failed to generate findings", error=str(e))
            return []

    async def _generate_specific_findings(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific compliance findings"""
        findings = []

        # Audit trail findings
        audit_coverage = analysis.get("audit_trail_coverage", 0)
        findings.append({
            "category": "Audit Trail Coverage",
            "status": "Compliant" if audit_coverage >= 90 else "Non-Compliant",
            "score": audit_coverage,
            "description": f"Audit trail covers {audit_coverage:.1f}% of required event types",
            "impact": "High" if audit_coverage < 80 else "Medium"
        })

        # Data access findings
        access_coverage = analysis.get("data_access_logging", 0)
        findings.append({
            "category": "Data Access Logging",
            "status": "Compliant" if access_coverage >= 95 else "Non-Compliant",
            "score": access_coverage,
            "description": f"Data access logging coverage is {access_coverage:.1f}%",
            "impact": "High" if access_coverage < 85 else "Medium"
        })

        return findings

    async def _generate_recommendations(self, findings: List[Dict[str, Any]], report_type: str) -> List[str]:
        """Generate compliance recommendations"""
        try:
            recommendations = []

            # Based on findings
            for finding in findings:
                if finding.get("status") == "Non-Compliant":
                    category = finding.get("category", "")
                    if "Audit Trail" in category:
                        recommendations.append("Implement comprehensive logging for all system events")
                        recommendations.append("Ensure log integrity and tamper-proof storage")
                    elif "Data Access" in category:
                        recommendations.append("Enhance data access monitoring and logging")
                        recommendations.append("Implement real-time access alerting")
                    elif "Authentication" in category:
                        recommendations.append("Strengthen authentication mechanisms")
                        recommendations.append("Implement multi-factor authentication")

            # General recommendations
            recommendations.extend([
                "Regularly review and update compliance policies",
                "Conduct periodic compliance assessments",
                "Implement automated compliance monitoring",
                "Provide regular compliance training to staff"
            ])

            return list(set(recommendations))  # Remove duplicates

        except Exception as e:
            self.logger.error("Failed to generate recommendations", error=str(e))
            return []

    async def _generate_summary(self, analysis: Dict[str, Any], compliance_score: float, report_type: str) -> Dict[str, Any]:
        """Generate report summary"""
        try:
            summary = {
                "compliance_score": compliance_score,
                "compliance_status": "Compliant" if compliance_score >= 80 else "Non-Compliant",
                "period_analyzed": f"{analysis.get('start_date', 'N/A')} to {analysis.get('end_date', 'N/A')}",
                "total_events_analyzed": analysis.get("statistics", {}).get("audit_events", 0),
                "key_findings": len(analysis.get("compliance_gaps", [])),
                "recommendations_count": len(analysis.get("recommendations", [])),
                "critical_areas": [
                    gap["area"] for gap in analysis.get("compliance_gaps", [])
                    if gap.get("severity") == "high"
                ]
            }

            return summary

        except Exception as e:
            self.logger.error("Failed to generate summary", error=str(e))
            return {}

    async def _generate_report_file(self, report: ComplianceReport) -> str:
        """Generate report file (PDF)"""
        try:
            # This would generate an actual PDF file
            # For now, return a placeholder path
            file_path = f"/tmp/compliance_report_{report.report_id}.pdf"
            return file_path

        except Exception as e:
            self.logger.error("Failed to generate report file", error=str(e))
            raise

    async def _load_report_from_database(self, report_id: str) -> Optional[ComplianceReport]:
        """Load report from database"""
        try:
            # Would load from actual database
            return None

        except Exception as e:
            self.logger.error("Failed to load report from database", error=str(e))
            return None

    async def _load_report_templates(self):
        """Load report templates"""
        try:
            # Would load Jinja2 templates from files
            pass

        except Exception as e:
            self.logger.error("Failed to load report templates", error=str(e))

    async def _initialize_compliance_checks(self):
        """Initialize compliance checks"""
        try:
            # Would initialize compliance check configurations
            pass

        except Exception as e:
            self.logger.error("Failed to initialize compliance checks", error=str(e))

    async def _get_audit_events(self, start_date: datetime, end_date: datetime, company_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get audit events for period"""
        # Would query actual database
        return []

    async def _get_security_events(self, start_date: datetime, end_date: datetime, company_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get security events for period"""
        # Would query actual database
        return []

    async def _get_user_activities(self, start_date: datetime, end_date: datetime, company_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get user activities for period"""
        # Would query actual database
        return []

    async def _get_data_access_logs(self, start_date: datetime, end_date: datetime, company_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get data access logs for period"""
        # Would query actual database
        return []

    async def _get_system_changes(self, start_date: datetime, end_date: datetime, company_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get system changes for period"""
        # Would query actual database
        return []

    async def _get_incidents(self, start_date: datetime, end_date: datetime, company_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get incidents for period"""
        # Would query actual database
        return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get compliance reporter statistics"""
        return {
            "service": "compliance_reporter",
            "status": "active",
            "cached_reports": len(self.report_cache),
            "supported_standards": list(self.compliance_standards.keys()),
            "report_types": ["standard", "security", "access", "data_protection", "user_activity", "system_audit", "full"]
        }