"""
Compliance checker for document validation
Handles document completeness and compliance validation
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from .models import (
    ComplianceResult,
    ComplianceIssue,
    DocumentType,
    SeverityLevel,
    ComplianceStatus
)


class ComplianceChecker:
    """Service for checking document compliance and completeness"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="ComplianceChecker")

        # Define required fields for each document type
        self.required_fields = {
            DocumentType.KTP: {
                "nama": "Nama lengkap",
                "nik": "Nomor Induk Kependudukan",
                "tempat_lahir": "Tempat lahir",
                "tanggal_lahir": "Tanggal lahir",
                "jenis_kelamin": "Jenis kelamin",
                "golongan_darah": "Golongan darah",
                "alamat": "Alamat lengkap",
                "rt": "RT",
                "rw": "RW",
                "kelurahan": "Kelurahan",
                "kecamatan": "Kecamatan",
                "kabupaten_kota": "Kabupaten/Kota",
                "provinsi": "Provinsi",
                "agama": "Agama",
                "status_perkawinan": "Status perkawinan",
                "pekerjaan": "Pekerjaan",
                "kewarganegaraan": "Kewarganegaraan",
                "berlaku_hingga": "Masa berlaku"
            },
            DocumentType.KK: {
                "no_kk": "Nomor Kartu Keluarga",
                "nama_kepala_keluarga": "Nama kepala keluarga",
                "alamat": "Alamat lengkap",
                "rt": "RT",
                "rw": "RW",
                "kelurahan": "Kelurahan",
                "kecamatan": "Kecamatan",
                "kabupaten_kota": "Kabupaten/Kota",
                "provinsi": "Provinsi",
                "kode_pos": "Kode pos"
            },
            DocumentType.NPWP: {
                "nama": "Nama lengkap",
                "npwp": "Nomor Pokok Wajib Pajak",
                "alamat": "Alamat",
                "kpp": "KPP terdaftar"
            },
            DocumentType.SIUP: {
                "nama_perusahaan": "Nama perusahaan",
                "no_siup": "Nomor SIUP",
                "nama_pemilik": "Nama pemilik",
                "alamat": "Alamat perusahaan",
                "jenis_usaha": "Jenis usaha",
                "modal": "Modal usaha"
            }
        }

        # Define field validation rules
        self.field_validators = {
            "nik": self._validate_nik,
            "tanggal_lahir": self._validate_date,
            "npwp": self._validate_npwp,
            "no_siup": self._validate_siup,
            "no_kk": self._validate_kk,
            "jenis_kelamin": self._validate_jenis_kelamin,
            "agama": self._validate_agama,
            "status_perkawinan": self._validate_status_perkawinan
        }

    async def initialize(self):
        """Initialize the compliance checker"""
        self.logger.info("Initializing Compliance Checker")
        # Load any additional compliance rules from database
        self.logger.info("Compliance Checker initialized")

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Compliance Checker")

    async def validate_document(
        self,
        ai_results: Dict[str, Any],
        document_type: DocumentType,
        company_info: Optional[Dict[str, Any]] = None
    ) -> ComplianceResult:
        """
        Validate document compliance and completeness

        Args:
            ai_results: AI extraction results from document
            document_type: Type of document being validated
            company_info: Optional company information for context

        Returns:
            ComplianceResult with validation details
        """
        try:
            start_time = asyncio.get_event_loop().time()
            self.logger.info(
                "Starting document compliance validation",
                document_type=document_type.value
            )

            # Extract document data from AI results
            document_data = ai_results.get("extracted_data", {})

            # Get required fields for this document type
            required_fields = self.required_fields.get(document_type, {})

            # Check for missing required fields
            missing_fields = []
            for field_name, field_label in required_fields.items():
                if not document_data.get(field_name):
                    missing_fields.append(f"{field_label} ({field_name})")

            # Validate existing fields
            issues = []
            for field_name, field_value in document_data.items():
                if field_name in self.field_validators:
                    validation_issues = await self.field_validators[field_name](field_value)
                    issues.extend(validation_issues)

            # Document type specific validations
            if document_type == DocumentType.KTP:
                ktp_issues = await self._validate_ktp_specific(document_data)
                issues.extend(ktp_issues)
            elif document_type == DocumentType.KK:
                kk_issues = await self._validate_kk_specific(document_data)
                issues.extend(kk_issues)
            elif document_type == DocumentType.NPWP:
                npwp_issues = await self._validate_npwp_specific(document_data)
                issues.extend(npwp_issues)

            # Calculate compliance score
            total_required = len(required_fields)
            total_present = total_required - len(missing_fields)

            # Factor in field validation issues
            field_penalty = len([issue for issue in issues if issue.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]])
            compliance_score = max(0, (total_present / total_required * 100) - (field_penalty * 5))

            # Determine compliance status
            is_compliant = len(missing_fields) == 0 and not any(
                issue.severity == SeverityLevel.CRITICAL for issue in issues
            )

            # Generate validation summary
            if is_compliant:
                summary = f"Dokumen {document_type.value} compliant dan lengkap"
            elif len(missing_fields) > 0:
                summary = f"Dokumen {document_type.value} tidak lengkap: {len(missing_fields)} field wajib hilang"
            else:
                summary = f"Dokumen {document_type.value} memiliki {len(issues)} isu compliance"

            # Generate recommendations
            recommendations = []
            if missing_fields:
                recommendations.append("Lengkapi field-field wajib yang hilang")
            if issues:
                recommendations.append("Perbaiki isu compliance yang teridentifikasi")
            if compliance_score < 80:
                recommendations.append("Tinjau kembali kualitas dan kelengkapan dokumen")

            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

            result = ComplianceResult(
                is_compliant=is_compliant,
                compliance_score=compliance_score,
                issues=issues,
                missing_fields=missing_fields,
                validation_summary=summary,
                recommendations=recommendations
            )

            self.logger.info(
                "Document compliance validation completed",
                document_type=document_type.value,
                is_compliant=is_compliant,
                compliance_score=compliance_score,
                missing_fields=len(missing_fields),
                issues=len(issues),
                processing_time_ms=processing_time
            )

            return result

        except Exception as e:
            self.logger.error(
                "Document compliance validation failed",
                document_type=document_type.value,
                error=str(e)
            )
            raise

    async def _validate_nik(self, nik_value: str) -> List[ComplianceIssue]:
        """Validate NIK (Nomor Induk Kependudukan)"""
        issues = []

        if not isinstance(nik_value, str):
            issues.append(ComplianceIssue(
                field_name="nik",
                issue_type="format",
                description="NIK harus berupa string",
                severity=SeverityLevel.HIGH
            ))
            return issues

        # Remove any spaces or dashes
        nik_clean = nik_value.replace(" ", "").replace("-", "")

        # Check length
        if len(nik_clean) != 16:
            issues.append(ComplianceIssue(
                field_name="nik",
                issue_type="length",
                description="NIK harus 16 digit",
                severity=SeverityLevel.HIGH,
                suggested_fix="Pastikan NIK memiliki 16 digit"
            ))

        # Check if all digits
        if not nik_clean.isdigit():
            issues.append(ComplianceIssue(
                field_name="nik",
                issue_type="format",
                description="NIK harus berisi angka saja",
                severity=SeverityLevel.HIGH,
                suggested_fix="Hapus karakter non-angka dari NIK"
            ))

        return issues

    async def _validate_npwp(self, npwp_value: str) -> List[ComplianceIssue]:
        """Validate NPWP format"""
        issues = []

        if not isinstance(npwp_value, str):
            issues.append(ComplianceIssue(
                field_name="npwp",
                issue_type="format",
                description="NPWP harus berupa string",
                severity=SeverityLevel.HIGH
            ))
            return issues

        # Remove formatting characters
        npwp_clean = npwp_value.replace(".", "").replace("-", "")

        # Check length
        if len(npwp_clean) != 15:
            issues.append(ComplianceIssue(
                field_name="npwp",
                issue_type="length",
                description="NPWP harus 15 digit",
                severity=SeverityLevel.HIGH,
                suggested_fix="Pastikan NPWP memiliki 15 digit"
            ))

        # Check if all digits
        if not npwp_clean.isdigit():
            issues.append(ComplianceIssue(
                field_name="npwp",
                issue_type="format",
                description="NPWP harus berisi angka saja",
                severity=SeverityLevel.HIGH,
                suggested_fix="Hapus karakter non-angka dari NPWP"
            ))

        return issues

    async def _validate_date(self, date_value: str) -> List[ComplianceIssue]:
        """Validate date format"""
        issues = []

        if not isinstance(date_value, str):
            issues.append(ComplianceIssue(
                field_name="tanggal",
                issue_type="format",
                description="Tanggal harus berupa string",
                severity=SeverityLevel.MEDIUM
            ))
            return issues

        # Try to parse common date formats
        date_formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y"
        ]

        valid_format = False
        for fmt in date_formats:
            try:
                datetime.strptime(date_value, fmt)
                valid_format = True
                break
            except ValueError:
                continue

        if not valid_format:
            issues.append(ComplianceIssue(
                field_name="tanggal",
                issue_type="format",
                description="Format tanggal tidak valid",
                severity=SeverityLevel.MEDIUM,
                suggested_fix="Gunakan format DD-MM-YYYY atau DD/MM/YYYY"
            ))

        return issues

    async def _validate_jenis_kelamin(self, value: str) -> List[ComplianceIssue]:
        """Validate jenis kelamin"""
        issues = []

        valid_values = ["laki-laki", "perempuan", "l", "p", "male", "female"]

        if isinstance(value, str) and value.lower() not in valid_values:
            issues.append(ComplianceIssue(
                field_name="jenis_kelamin",
                issue_type="value",
                description="Jenis kelamin tidak valid",
                severity=SeverityLevel.MEDIUM,
                suggested_fix="Gunakan 'Laki-laki' atau 'Perempuan'"
            ))

        return issues

    async def _validate_agama(self, value: str) -> List[ComplianceIssue]:
        """Validate agama"""
        issues = []

        valid_agama = [
            "islam", "kristen", "katolik", "hindu", "budha", "khonghucu",
            "protestan", "kristen protestan"
        ]

        if isinstance(value, str) and value.lower() not in valid_agama:
            issues.append(ComplianceIssue(
                field_name="agama",
                issue_type="value",
                description="Agama tidak valid",
                severity=SeverityLevel.LOW,
                suggested_fix="Pilih dari agama yang diakui"
            ))

        return issues

    async def _validate_status_perkawinan(self, value: str) -> List[ComplianceIssue]:
        """Validate status perkawinan"""
        issues = []

        valid_status = [
            "belum kawin", "kawin", "cerai hidup", "cerai mati",
            "single", "menikah", "janda", "duda"
        ]

        if isinstance(value, str) and value.lower() not in valid_status:
            issues.append(ComplianceIssue(
                field_name="status_perkawinan",
                issue_type="value",
                description="Status perkawinan tidak valid",
                severity=SeverityLevel.LOW,
                suggested_fix="Gunakan status perkawinan yang sesuai"
            ))

        return issues

    async def _validate_siup(self, siup_value: str) -> List[ComplianceIssue]:
        """Validate SIUP format"""
        issues = []

        if not isinstance(siup_value, str):
            issues.append(ComplianceIssue(
                field_name="no_siup",
                issue_type="format",
                description="Nomor SIUP harus berupa string",
                severity=SeverityLevel.HIGH
            ))
            return issues

        # Basic validation - SIUP typically has 8-12 digits
        siup_clean = siup_value.replace(".", "").replace("-", "").replace(" ", "")

        if len(siup_clean) < 8 or len(siup_clean) > 12:
            issues.append(ComplianceIssue(
                field_name="no_siup",
                issue_type="length",
                description="Nomor SIUP harus 8-12 digit",
                severity=SeverityLevel.MEDIUM
            ))

        return issues

    async def _validate_kk(self, kk_value: str) -> List[ComplianceIssue]:
        """Validate Kartu Keluarga number"""
        issues = []

        if not isinstance(kk_value, str):
            issues.append(ComplianceIssue(
                field_name="no_kk",
                issue_type="format",
                description="Nomor KK harus berupa string",
                severity=SeverityLevel.HIGH
            ))
            return issues

        # KK has 16 digits
        kk_clean = kk_value.replace(".", "").replace("-", "").replace(" ", "")

        if len(kk_clean) != 16:
            issues.append(ComplianceIssue(
                field_name="no_kk",
                issue_type="length",
                description="Nomor KK harus 16 digit",
                severity=SeverityLevel.HIGH
            ))

        return issues

    async def _validate_ktp_specific(self, data: Dict[str, Any]) -> List[ComplianceIssue]:
        """KTP-specific validations"""
        issues = []

        # Validate age from birth date
        if "tanggal_lahir" in data:
            try:
                birth_date = datetime.strptime(data["tanggal_lahir"], "%d-%m-%Y")
                age = datetime.now().year - birth_date.year

                if age < 17 and data.get("status_perkawinan", "").lower() in ["kawin", "menikah"]:
                    issues.append(ComplianceIssue(
                        field_name="status_perkawinan",
                        issue_type="consistency",
                        description="Status kawin tidak konsisten dengan usia",
                        severity=SeverityLevel.MEDIUM
                    ))

            except ValueError:
                pass  # Date format already validated earlier

        return issues

    async def _validate_kk_specific(self, data: Dict[str, Any]) -> List[ComplianceIssue]:
        """KK-specific validations"""
        issues = []

        # Validate that KK has at least one family member
        if not data.get("anggota_keluarga"):
            issues.append(ComplianceIssue(
                field_name="anggota_keluarga",
                issue_type="completeness",
                description="KK harus memiliki minimal satu anggota keluarga",
                severity=SeverityLevel.HIGH
            ))

        return issues

    async def _validate_npwp_specific(self, data: Dict[str, Any]) -> List[ComplianceIssue]:
        """NPWP-specific validations"""
        issues = []

        # Validate that NPWP matches company if provided
        if "nama_perusahaan" in data and "nama" in data:
            if data.get("nama_perusahaan") != data.get("nama"):
                issues.append(ComplianceIssue(
                    field_name="nama",
                    issue_type="consistency",
                    description="Nama pada NPWP harus sesuai dengan nama perusahaan",
                    severity=SeverityLevel.MEDIUM
                ))

        return issues

    async def get_supported_document_types(self) -> List[str]:
        """Get list of supported document types"""
        return [doc_type.value for doc_type in DocumentType]

    async def get_stats(self) -> Dict[str, Any]:
        """Get compliance checker statistics"""
        return {
            "supported_document_types": len(self.required_fields),
            "field_validators": len(self.field_validators),
            "service": "compliance_checker",
            "status": "active"
        }