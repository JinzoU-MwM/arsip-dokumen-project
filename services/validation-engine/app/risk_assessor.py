"""
Risk assessor for document validation
Handles risk assessment and scoring for documents
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime
import re

from .models import (
    RiskAssessment,
    SeverityLevel,
    DocumentType
)


class RiskAssessor:
    """Service for assessing document risks"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="RiskAssessor")

        # Define risk factors for different document types
        self.risk_factors = {
            DocumentType.KTP: {
                "high_risk_fields": ["nik", "nama", "tanggal_lahir"],
                "sensitive_data_fields": ["nik", "nama", "alamat", "tanggal_lahir"],
                "verification_importance": "high"
            },
            DocumentType.KK: {
                "high_risk_fields": ["no_kk", "nama_kepala_keluarga"],
                "sensitive_data_fields": ["no_kk", "nama_kepala_keluarga", "alamat"],
                "verification_importance": "high"
            },
            DocumentType.NPWP: {
                "high_risk_fields": ["npwp", "nama"],
                "sensitive_data_fields": ["npwp", "nama", "alamat"],
                "verification_importance": "critical"
            },
            DocumentType.SIUP: {
                "high_risk_fields": ["no_siup", "nama_perusahaan"],
                "sensitive_data_fields": ["no_siup", "nama_perusahaan", "alamat"],
                "verification_importance": "high"
            }
        }

        # Define risk patterns
        self.suspicious_patterns = {
            "nik": [
                r"0000000000000000",  # All zeros
                r"1111111111111111",  # All ones
                r"1234567890123456",  # Sequential
                r"(\d)\1{15}"        # Repeated single digit
            ],
            "nama": [
                r"TEST",              # Test names
                r"DEMO",              # Demo names
                r"SAMPLE",            # Sample names
                r"^\d+$"              # All numbers
            ],
            "tanggal_lahir": [
                r"01-01-19\d\d",     # Common placeholder dates
                r"31-12-19\d\d",     # Common placeholder dates
                r"01-01-2000",       # Y2K placeholder
            ]
        }

    async def initialize(self):
        """Initialize the risk assessor"""
        self.logger.info("Initializing Risk Assessor")
        # Load any additional risk factors from configuration
        self.logger.info("Risk Assessor initialized")

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Risk Assessor")

    async def assess_risk(
        self,
        ai_results: Dict[str, Any],
        compliance_result: Optional[Any] = None,
        document_type: DocumentType = DocumentType.LAINNYA
    ) -> RiskAssessment:
        """
        Assess risk level for a document

        Args:
            ai_results: AI extraction results
            compliance_result: Optional compliance validation result
            document_type: Type of document

        Returns:
            RiskAssessment with risk details
        """
        try:
            start_time = asyncio.get_event_loop().time()
            self.logger.info(
                "Starting risk assessment",
                document_type=document_type.value
            )

            document_data = ai_results.get("extracted_data", {})
            risk_factors = []
            risk_score = 0

            # Check for suspicious patterns
            pattern_risks = await self._check_suspicious_patterns(document_data)
            risk_factors.extend(pattern_risks)
            risk_score += sum(risk["score"] for risk in pattern_risks)

            # Check data consistency
            consistency_risks = await self._check_data_consistency(document_data, document_type)
            risk_factors.extend(consistency_risks)
            risk_score += sum(risk["score"] for risk in consistency_risks)

            # Check compliance issues impact
            if compliance_result:
                compliance_risks = await self._assess_compliance_risks(compliance_result)
                risk_factors.extend(compliance_risks)
                risk_score += sum(risk["score"] for risk in compliance_risks)

            # Check data completeness impact
            completeness_risks = await self._assess_completeness_risks(document_data, document_type)
            risk_factors.extend(completeness_risks)
            risk_score += sum(risk["score"] for risk in completeness_risks)

            # Check AI confidence
            ai_risks = await self._assess_ai_confidence_risks(ai_results)
            risk_factors.extend(ai_risks)
            risk_score += sum(risk["score"] for risk in ai_risks)

            # Normalize risk score to 0-100
            risk_score = min(100, max(0, risk_score))

            # Determine risk level
            risk_level = await self._determine_risk_level(risk_score)

            # Generate mitigation suggestions
            mitigation_suggestions = await self._generate_mitigation_suggestions(
                risk_factors, risk_level, document_type
            )

            # Generate assessment summary
            assessment_summary = await self._generate_assessment_summary(
                risk_level, risk_score, len(risk_factors)
            )

            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

            result = RiskAssessment(
                risk_level=risk_level,
                risk_score=risk_score,
                risk_factors=risk_factors,
                mitigation_suggestions=mitigation_suggestions,
                assessment_summary=assessment_summary
            )

            self.logger.info(
                "Risk assessment completed",
                document_type=document_type.value,
                risk_level=risk_level.value,
                risk_score=risk_score,
                risk_factors=len(risk_factors),
                processing_time_ms=processing_time
            )

            return result

        except Exception as e:
            self.logger.error(
                "Risk assessment failed",
                document_type=document_type.value,
                error=str(e)
            )
            raise

    async def _check_suspicious_patterns(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for suspicious patterns in document data"""
        risks = []

        for field_name, field_value in document_data.items():
            if not isinstance(field_value, str):
                continue

            # Check against suspicious patterns for this field
            patterns = self.suspicious_patterns.get(field_name, [])
            for pattern in patterns:
                if re.search(pattern, field_value, re.IGNORECASE):
                    risks.append({
                        "type": "suspicious_pattern",
                        "field": field_name,
                        "description": f"Suspicious pattern detected in {field_name}",
                        "severity": SeverityLevel.HIGH,
                        "score": 25,
                        "details": {
                            "pattern": pattern,
                            "value": field_value
                        }
                    })
                    break  # Only add one risk per field

        return risks

    async def _check_data_consistency(self, document_data: Dict[str, Any], document_type: DocumentType) -> List[Dict[str, Any]]:
        """Check for data consistency issues"""
        risks = []

        # Date consistency checks
        if "tanggal_lahir" in document_data and "tanggal_terbit" in document_data:
            try:
                birth_date = datetime.strptime(document_data["tanggal_lahir"], "%d-%m-%Y")
                issue_date = datetime.strptime(document_data["tanggal_terbit"], "%d-%m-%Y")

                if issue_date < birth_date:
                    risks.append({
                        "type": "data_inconsistency",
                        "field": "tanggal_terbit",
                        "description": "Document issue date is before birth date",
                        "severity": SeverityLevel.HIGH,
                        "score": 30,
                        "details": {
                            "birth_date": document_data["tanggal_lahir"],
                            "issue_date": document_data["tanggal_terbit"]
                        }
                    })
            except ValueError:
                pass  # Date format issues already caught by compliance checker

        # Name consistency checks
        if "nama" in document_data and "nama_pemilik" in document_data:
            if document_data["nama"] != document_data["nama_pemilik"]:
                risks.append({
                    "type": "data_inconsistency",
                    "field": "nama_pemilik",
                    "description": "Name inconsistency between different fields",
                    "severity": SeverityLevel.MEDIUM,
                    "score": 15,
                    "details": {
                        "nama": document_data["nama"],
                        "nama_pemilik": document_data["nama_pemilik"]
                    }
                })

        # Document type specific consistency checks
        if document_type == DocumentType.KTP:
            risks.extend(await self._check_ktp_consistency(document_data))
        elif document_type == DocumentType.KK:
            risks.extend(await self._check_kk_consistency(document_data))

        return risks

    async def _check_ktp_consistency(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """KTP-specific consistency checks"""
        risks = []

        # Check age consistency with marriage status
        if "tanggal_lahir" in document_data and "status_perkawinan" in document_data:
            try:
                birth_date = datetime.strptime(document_data["tanggal_lahir"], "%d-%m-%Y")
                age = datetime.now().year - birth_date.year

                if age < 17 and document_data["status_perkawinan"].lower() in ["kawin", "menikah"]:
                    risks.append({
                        "type": "data_inconsistency",
                        "field": "status_perkawinan",
                        "description": "Marriage status inconsistent with age",
                        "severity": SeverityLevel.MEDIUM,
                        "score": 20,
                        "details": {
                            "age": age,
                            "marital_status": document_data["status_perkawinan"]
                        }
                    })
            except ValueError:
                pass

        return risks

    async def _check_kk_consistency(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """KK-specific consistency checks"""
        risks = []

        # Check if family member count is reasonable
        if "anggota_keluarga" in document_data:
            anggota_count = len(document_data["anggota_keluarga"]) if isinstance(document_data["anggota_keluarga"], list) else 1

            if anggota_count > 10:
                risks.append({
                    "type": "data_anomaly",
                    "field": "anggota_keluarga",
                    "description": "Unusually high number of family members",
                    "severity": SeverityLevel.MEDIUM,
                    "score": 10,
                    "details": {"member_count": anggota_count}
                })

        return risks

    async def _assess_compliance_risks(self, compliance_result: Any) -> List[Dict[str, Any]]:
        """Assess risks based on compliance validation results"""
        risks = []

        # Check missing critical fields
        if hasattr(compliance_result, 'missing_fields'):
            missing_critical = [field for field in compliance_result.missing_fields if "nik" in field.lower() or "nama" in field.lower()]
            if missing_critical:
                risks.append({
                    "type": "compliance_risk",
                    "field": "missing_fields",
                    "description": "Critical fields are missing",
                    "severity": SeverityLevel.HIGH,
                    "score": 20,
                    "details": {"missing_critical_fields": missing_critical}
                })

        # Check compliance score
        if hasattr(compliance_result, 'compliance_score'):
            if compliance_result.compliance_score < 60:
                risks.append({
                    "type": "compliance_risk",
                    "field": "compliance_score",
                    "description": "Very low compliance score",
                    "severity": SeverityLevel.HIGH,
                    "score": 25,
                    "details": {"compliance_score": compliance_result.compliance_score}
                })
            elif compliance_result.compliance_score < 80:
                risks.append({
                    "type": "compliance_risk",
                    "field": "compliance_score",
                    "description": "Low compliance score",
                    "severity": SeverityLevel.MEDIUM,
                    "score": 10,
                    "details": {"compliance_score": compliance_result.compliance_score}
                })

        return risks

    async def _assess_completeness_risks(self, document_data: Dict[str, Any], document_type: DocumentType) -> List[Dict[str, Any]]:
        """Assess risks based on data completeness"""
        risks = []

        # Get document type specific factors
        doc_factors = self.risk_factors.get(document_type, {})
        high_risk_fields = doc_factors.get("high_risk_fields", [])

        # Check if high-risk fields are missing
        for field in high_risk_fields:
            if field not in document_data or not document_data[field]:
                risks.append({
                    "type": "completeness_risk",
                    "field": field,
                    "description": f"Critical field {field} is missing or empty",
                    "severity": SeverityLevel.HIGH,
                    "score": 15
                })

        # Check overall data completeness
        total_fields = len(document_data)
        empty_fields = len([k for k, v in document_data.items() if not v])
        completeness_ratio = (total_fields - empty_fields) / total_fields if total_fields > 0 else 0

        if completeness_ratio < 0.5:
            risks.append({
                "type": "completeness_risk",
                "field": "overall_completeness",
                "description": "Document data is largely incomplete",
                "severity": SeverityLevel.HIGH,
                "score": 20,
                "details": {"completeness_ratio": completeness_ratio}
            })

        return risks

    async def _assess_ai_confidence_risks(self, ai_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess risks based on AI extraction confidence"""
        risks = []

        # Check overall confidence score
        confidence_score = ai_results.get("confidence_score", 1.0)
        if confidence_score < 0.7:
            risks.append({
                "type": "ai_confidence_risk",
                "field": "confidence_score",
                "description": "Low AI extraction confidence",
                "severity": SeverityLevel.MEDIUM,
                "score": 10,
                "details": {"confidence_score": confidence_score}
            })
        elif confidence_score < 0.9:
            risks.append({
                "type": "ai_confidence_risk",
                "field": "confidence_score",
                "description": "Moderate AI extraction confidence",
                "severity": SeverityLevel.LOW,
                "score": 5,
                "details": {"confidence_score": confidence_score}
            })

        # Check field-specific confidence scores
        field_confidences = ai_results.get("field_confidence", {})
        for field, confidence in field_confidences.items():
            if confidence < 0.6:
                risks.append({
                    "type": "ai_confidence_risk",
                    "field": field,
                    "description": f"Low confidence in extracting {field}",
                    "severity": SeverityLevel.MEDIUM,
                    "score": 8,
                    "details": {"field_confidence": confidence}
                })

        return risks

    async def _determine_risk_level(self, risk_score: float) -> SeverityLevel:
        """Determine risk level based on risk score"""
        if risk_score >= 70:
            return SeverityLevel.CRITICAL
        elif risk_score >= 50:
            return SeverityLevel.HIGH
        elif risk_score >= 30:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    async def _generate_mitigation_suggestions(
        self,
        risk_factors: List[Dict[str, Any]],
        risk_level: SeverityLevel,
        document_type: DocumentType
    ) -> List[str]:
        """Generate risk mitigation suggestions"""
        suggestions = []

        # Group risk factors by type
        risk_types = set(risk["type"] for risk in risk_factors)

        if "suspicious_pattern" in risk_types:
            suggestions.append("Verifikasi manual dokumen yang mencurigakan")
            suggestions.append("Periksa kembali data yang terdeteksi pola mencurigakan")

        if "data_inconsistency" in risk_types:
            suggestions.append("Validasi konsistensi data antar field")
            suggestions.append("Lakukan cross-check dengan sumber data lain")

        if "compliance_risk" in risk_types:
            suggestions.append("Lengkapi field-field yang hilang")
            suggestions.append("Perbaiki isu compliance yang teridentifikasi")

        if "completeness_risk" in risk_types:
            suggestions.append("Pindai ulang dokumen untuk kualitas lebih baik")
            suggestions.append("Verifikasi kelengkapan data manual")

        if "ai_confidence_risk" in risk_types:
            suggestions.append("Gunakan OCR berkualitas tinggi atau input manual")
            suggestions.append("Verifikasi ekstraksi AI dengan review manual")

        # Document type specific suggestions
        if document_type == DocumentType.KTP:
            suggestions.append("Pastikan KTP asli dan masih berlaku")
            suggestions.append("Verifikasi NIK dengan database DUKCAPIL")
        elif document_type == DocumentType.NPWP:
            suggestions.append("Verifikasi NPWP dengan database DJP")
            suggestions.append("Pastikan NPWP masih aktif")

        # Risk level specific suggestions
        if risk_level == SeverityLevel.CRITICAL:
            suggestions.append("TOLAK DOKUMEN - Memerlukan verifikasi mendalam")
        elif risk_level == SeverityLevel.HIGH:
            suggestions.append("PERLU PERHATIAN KHUSUS - Review manual menyeluruh")
        elif risk_level == SeverityLevel.MEDIUM:
            suggestions.append("Review manual disarankan sebelum persetujuan")

        return list(set(suggestions))  # Remove duplicates

    async def _generate_assessment_summary(self, risk_level: SeverityLevel, risk_score: float, factor_count: int) -> str:
        """Generate assessment summary"""
        if risk_level == SeverityLevel.CRITICAL:
            return f"RISIKO KRITIS - Skor risiko {risk_score:.1f} dengan {factor_count} faktor risiko. Perlu penolakan atau verifikasi ekstensif."
        elif risk_level == SeverityLevel.HIGH:
            return f"Risiko tinggi - Skor risiko {risk_score:.1f} dengan {factor_count} faktor risiko. Perlu review manual menyeluruh."
        elif risk_level == SeverityLevel.MEDIUM:
            return f"Risiko sedang - Skor risiko {risk_score:.1f} dengan {factor_count} faktor risiko. Review manual disarankan."
        else:
            return f"Risiko rendah - Skor risiko {risk_score:.1f}. Dokumen dapat diproses dengan risiko minimal."

    async def get_stats(self) -> Dict[str, Any]:
        """Get risk assessor statistics"""
        return {
            "supported_document_types": len(self.risk_factors),
            "suspicious_patterns": sum(len(patterns) for patterns in self.suspicious_patterns.values()),
            "service": "risk_assessor",
            "status": "active"
        }