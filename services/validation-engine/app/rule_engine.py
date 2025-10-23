"""
Rule engine for document validation
Handles custom compliance rules and validation logic
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from .models import (
    ComplianceRule,
    RuleValidationResult,
    RuleType,
    DocumentType,
    SeverityLevel
)


class RuleEngine:
    """Service for managing and applying validation rules"""

    def __init__(self):
        self.logger = structlog.get_logger().bind(component="RuleEngine")
        self.rules: Dict[str, ComplianceRule] = {}
        self.rule_stats = {
            "total_rules": 0,
            "active_rules": 0,
            "rules_by_type": {},
            "rules_by_document_type": {}
        }

    async def initialize(self):
        """Initialize the rule engine with default rules"""
        self.logger.info("Initializing Rule Engine")

        # Load default rules
        await self._load_default_rules()

        # Calculate statistics
        await self._calculate_stats()

        self.logger.info(
            "Rule Engine initialized",
            total_rules=self.rule_stats["total_rules"],
            active_rules=self.rule_stats["active_rules"]
        )

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Rule Engine")

    async def add_rule(self, rule: ComplianceRule) -> str:
        """
        Add a new validation rule

        Args:
            rule: The rule to add

        Returns:
            Rule ID of the added rule
        """
        try:
            rule_id = rule.id or str(uuid.uuid4())
            rule.id = rule_id
            rule.created_at = datetime.utcnow()

            # Validate rule condition
            if not await self._validate_rule_condition(rule.condition, rule.rule_type):
                raise ValueError(f"Invalid rule condition for rule: {rule.name}")

            self.rules[rule_id] = rule

            # Update statistics
            await self._calculate_stats()

            self.logger.info(
                "Rule added successfully",
                rule_id=rule_id,
                rule_name=rule.name,
                document_type=rule.document_type.value,
                rule_type=rule.rule_type.value
            )

            return rule_id

        except Exception as e:
            self.logger.error(
                "Failed to add rule",
                rule_name=rule.name,
                error=str(e)
            )
            raise

    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing rule

        Args:
            rule_id: ID of rule to update
            updates: Dictionary of fields to update

        Returns:
            True if update was successful, False if rule not found
        """
        try:
            if rule_id not in self.rules:
                self.logger.warning("Rule not found for update", rule_id=rule_id)
                return False

            rule = self.rules[rule_id]

            # Update fields
            for field, value in updates.items():
                if hasattr(rule, field):
                    setattr(rule, field, value)

            rule.updated_at = datetime.utcnow()

            # Validate updated rule
            if not await self._validate_rule_condition(rule.condition, rule.rule_type):
                raise ValueError(f"Invalid rule condition after update: {rule.name}")

            # Update statistics
            await self._calculate_stats()

            self.logger.info(
                "Rule updated successfully",
                rule_id=rule_id,
                rule_name=rule.name
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to update rule",
                rule_id=rule_id,
                error=str(e)
            )
            raise

    async def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a rule

        Args:
            rule_id: ID of rule to delete

        Returns:
            True if deletion was successful, False if rule not found
        """
        try:
            if rule_id not in self.rules:
                self.logger.warning("Rule not found for deletion", rule_id=rule_id)
                return False

            rule_name = self.rules[rule_id].name
            del self.rules[rule_id]

            # Update statistics
            await self._calculate_stats()

            self.logger.info(
                "Rule deleted successfully",
                rule_id=rule_id,
                rule_name=rule_name
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to delete rule",
                rule_id=rule_id,
                error=str(e)
            )
            raise

    async def list_rules(
        self,
        document_type: Optional[DocumentType] = None,
        rule_type: Optional[RuleType] = None,
        is_active: Optional[bool] = None
    ) -> List[ComplianceRule]:
        """
        List rules with optional filtering

        Args:
            document_type: Filter by document type
            rule_type: Filter by rule type
            is_active: Filter by active status

        Returns:
            List of matching rules
        """
        rules = list(self.rules.values())

        # Apply filters
        if document_type:
            rules = [rule for rule in rules if rule.document_type == document_type]

        if rule_type:
            rules = [rule for rule in rules if rule.rule_type == rule_type]

        if is_active is not None:
            rules = [rule for rule in rules if rule.is_active == is_active]

        return rules

    async def validate_document(
        self,
        ai_results: Dict[str, Any],
        document_type: DocumentType
    ) -> RuleValidationResult:
        """
        Apply all applicable rules to a document

        Args:
            ai_results: AI extraction results
            document_type: Type of document

        Returns:
            RuleValidationResult with validation details
        """
        try:
            start_time = asyncio.get_event_loop().time()
            self.logger.info(
                "Starting rule-based validation",
                document_type=document_type.value
            )

            # Get applicable rules
            applicable_rules = [
                rule for rule in self.rules.values()
                if rule.document_type == document_type and rule.is_active
            ]

            if not applicable_rules:
                self.logger.info(
                    "No applicable rules found",
                    document_type=document_type.value
                )
                return RuleValidationResult(
                    validation_passed=True,
                    rules_checked=0,
                    rules_passed=0,
                    rules_failed=0,
                    validation_summary="No applicable rules found"
                )

            document_data = ai_results.get("extracted_data", {})
            failed_rules = []
            rules_passed = 0

            # Apply each rule
            for rule in applicable_rules:
                try:
                    rule_result = await self._apply_rule(rule, document_data)
                    if not rule_result["passed"]:
                        failed_rules.append({
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "rule_type": rule.rule_type.value,
                            "severity": rule.severity.value,
                            "description": rule_result["description"],
                            "details": rule_result.get("details", {})
                        })
                    else:
                        rules_passed += 1

                except Exception as e:
                    self.logger.error(
                        "Rule application failed",
                        rule_id=rule.id,
                        rule_name=rule.name,
                        error=str(e)
                    )
                    failed_rules.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "rule_type": rule.rule_type.value,
                        "severity": SeverityLevel.HIGH.value,
                        "description": f"Rule execution error: {str(e)}",
                        "details": {"error": str(e)}
                    })

            rules_checked = len(applicable_rules)
            rules_failed = len(failed_rules)
            validation_passed = rules_failed == 0

            # Generate validation summary
            if validation_passed:
                summary = f"All {rules_checked} rules passed"
            else:
                summary = f"{rules_failed} of {rules_checked} rules failed"

            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

            result = RuleValidationResult(
                validation_passed=validation_passed,
                rules_checked=rules_checked,
                rules_passed=rules_passed,
                rules_failed=rules_failed,
                failed_rules=failed_rules,
                validation_summary=summary
            )

            self.logger.info(
                "Rule-based validation completed",
                document_type=document_type.value,
                validation_passed=validation_passed,
                rules_checked=rules_checked,
                rules_failed=rules_failed,
                processing_time_ms=processing_time
            )

            return result

        except Exception as e:
            self.logger.error(
                "Rule-based validation failed",
                document_type=document_type.value,
                error=str(e)
            )
            raise

    async def _apply_rule(self, rule: ComplianceRule, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single rule to document data"""
        condition = rule.condition

        if rule.rule_type == RuleType.REQUIREMENT:
            return await self._apply_requirement_rule(condition, document_data)
        elif rule.rule_type == RuleType.FORBIDDEN:
            return await self._apply_forbidden_rule(condition, document_data)
        elif rule.rule_type == RuleType.CONDITIONAL:
            return await self._apply_conditional_rule(condition, document_data)
        elif rule.rule_type == RuleType.FORMAT:
            return await self._apply_format_rule(condition, document_data)
        else:
            return {
                "passed": False,
                "description": f"Unknown rule type: {rule.rule_type}"
            }

    async def _apply_requirement_rule(self, condition: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply requirement rule - fields must be present and valid"""
        field_name = condition.get("field")
        required_value = condition.get("value")
        allow_empty = condition.get("allow_empty", False)

        if not field_name:
            return {"passed": False, "description": "Invalid requirement rule: no field specified"}

        field_value = document_data.get(field_name)

        # Check if field is missing
        if field_value is None:
            return {
                "passed": False,
                "description": f"Required field '{field_name}' is missing"
            }

        # Check if field is empty when not allowed
        if not allow_empty and not field_value:
            return {
                "passed": False,
                "description": f"Required field '{field_name}' is empty"
            }

        # Check if field has required value
        if required_value is not None:
            if isinstance(required_value, list):
                if field_value not in required_value:
                    return {
                        "passed": False,
                        "description": f"Field '{field_name}' value '{field_value}' not in allowed values",
                        "details": {"allowed_values": required_value, "actual_value": field_value}
                    }
            elif field_value != required_value:
                return {
                    "passed": False,
                    "description": f"Field '{field_name}' has incorrect value",
                    "details": {"expected": required_value, "actual": field_value}
                }

        return {"passed": True, "description": f"Requirement rule passed for field '{field_name}'"}

    async def _apply_forbidden_rule(self, condition: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply forbidden rule - fields must not be present or have certain values"""
        field_name = condition.get("field")
        forbidden_values = condition.get("values", [])

        if not field_name:
            return {"passed": False, "description": "Invalid forbidden rule: no field specified"}

        field_value = document_data.get(field_name)

        # If field shouldn't exist at all
        if not forbidden_values:
            if field_value is not None:
                return {
                    "passed": False,
                    "description": f"Forbidden field '{field_name}' is present"
                }
            return {"passed": True, "description": f"Forbidden rule passed: field '{field_name}' not present"}

        # Check for forbidden values
        if field_value in forbidden_values:
            return {
                "passed": False,
                "description": f"Field '{field_name}' has forbidden value",
                "details": {"forbidden_values": forbidden_values, "actual_value": field_value}
            }

        return {"passed": True, "description": f"Forbidden rule passed for field '{field_name}'"}

    async def _apply_conditional_rule(self, condition: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply conditional rule - if condition is met, then requirement must be satisfied"""
        if_condition = condition.get("if")
        then_condition = condition.get("then")

        if not if_condition or not then_condition:
            return {"passed": False, "description": "Invalid conditional rule: missing if/then conditions"}

        # Check if condition is met
        condition_met = await self._evaluate_condition(if_condition, document_data)

        if not condition_met:
            return {"passed": True, "description": "Conditional rule not triggered"}

        # Apply then condition
        then_result = await self._apply_requirement_rule(then_condition, document_data)
        then_result["description"] = f"Conditional rule triggered: {then_result['description']}"

        return then_result

    async def _apply_format_rule(self, condition: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply format rule - fields must match specified format"""
        field_name = condition.get("field")
        pattern = condition.get("pattern")
        min_length = condition.get("min_length")
        max_length = condition.get("max_length")

        if not field_name:
            return {"passed": False, "description": "Invalid format rule: no field specified"}

        field_value = document_data.get(field_name)

        if field_value is None:
            return {"passed": True, "description": f"Format rule not applicable: field '{field_name}' not present"}

        if not isinstance(field_value, str):
            return {
                "passed": False,
                "description": f"Field '{field_name}' must be a string for format validation"
            }

        # Check length constraints
        if min_length is not None and len(field_value) < min_length:
            return {
                "passed": False,
                "description": f"Field '{field_name}' is too short",
                "details": {"min_length": min_length, "actual_length": len(field_value)}
            }

        if max_length is not None and len(field_value) > max_length:
            return {
                "passed": False,
                "description": f"Field '{field_name}' is too long",
                "details": {"max_length": max_length, "actual_length": len(field_value)}
            }

        # Check pattern
        if pattern:
            import re
            if not re.match(pattern, field_value):
                return {
                    "passed": False,
                    "description": f"Field '{field_name}' doesn't match required format",
                    "details": {"pattern": pattern, "actual_value": field_value}
                }

        return {"passed": True, "description": f"Format rule passed for field '{field_name}'"}

    async def _evaluate_condition(self, condition: Dict[str, Any], document_data: Dict[str, Any]) -> bool:
        """Evaluate a simple condition"""
        field_name = condition.get("field")
        operator = condition.get("operator", "equals")
        value = condition.get("value")

        if not field_name:
            return False

        field_value = document_data.get(field_name)

        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "exists":
            return field_value is not None
        elif operator == "not_exists":
            return field_value is None
        elif operator == "contains":
            return value in str(field_value) if field_value else False
        elif operator == "in":
            return field_value in value if isinstance(value, list) else False
        else:
            return False

    async def _validate_rule_condition(self, condition: Dict[str, Any], rule_type: RuleType) -> bool:
        """Validate rule condition structure"""
        try:
            if rule_type == RuleType.REQUIREMENT:
                return "field" in condition
            elif rule_type == RuleType.FORBIDDEN:
                return "field" in condition
            elif rule_type == RuleType.CONDITIONAL:
                return "if" in condition and "then" in condition
            elif rule_type == RuleType.FORMAT:
                return "field" in condition
            else:
                return False
        except Exception:
            return False

    async def _load_default_rules(self):
        """Load default validation rules"""
        default_rules = [
            # KTP Rules
            ComplianceRule(
                name="KTP - NIK Format",
                document_type=DocumentType.KTP,
                rule_type=RuleType.FORMAT,
                condition={
                    "field": "nik",
                    "pattern": r"^\d{16}$"
                },
                severity=SeverityLevel.HIGH,
                description="NIK harus 16 digit angka"
            ),
            ComplianceRule(
                name="KTP - Umur Minimum",
                document_type=DocumentType.KTP,
                rule_type=RuleType.CONDITIONAL,
                condition={
                    "if": {
                        "field": "status_perkawinan",
                        "operator": "in",
                        "value": ["kawin", "menikah"]
                    },
                    "then": {
                        "field": "umur",
                        "operator": ">=",
                        "value": 21
                    }
                },
                severity=SeverityLevel.MEDIUM,
                description="Status kawin harus sesuai dengan umur minimum"
            ),

            # KK Rules
            ComplianceRule(
                name="KK - Nomor KK Format",
                document_type=DocumentType.KK,
                rule_type=RuleType.FORMAT,
                condition={
                    "field": "no_kk",
                    "pattern": r"^\d{16}$"
                },
                severity=SeverityLevel.HIGH,
                description="Nomor KK harus 16 digit angka"
            ),
            ComplianceRule(
                name="KK - Anggota Keluarga Minimum",
                document_type=DocumentType.KK,
                rule_type=RuleType.REQUIREMENT,
                condition={
                    "field": "anggota_keluarga",
                    "min_length": 1
                },
                severity=SeverityLevel.HIGH,
                description="KK harus memiliki minimal 1 anggota keluarga"
            ),

            # NPWP Rules
            ComplianceRule(
                name="NPWP - Format Valid",
                document_type=DocumentType.NPWP,
                rule_type=RuleType.FORMAT,
                condition={
                    "field": "npwp",
                    "pattern": r"^\d{2}\.\d{3}\.\d{3}\.\d{1}-\d{3}\.\d{3}$"
                },
                severity=SeverityLevel.HIGH,
                description="NPWP harus sesuai format standar"
            ),

            # SIUP Rules
            ComplianceRule(
                name="SIUP - Nomor Valid",
                document_type=DocumentType.SIUP,
                rule_type=RuleType.FORMAT,
                condition={
                    "field": "no_siup",
                    "min_length": 8,
                    "max_length": 12,
                    "pattern": r"^\d+$"
                },
                severity=SeverityLevel.HIGH,
                description="Nomor SIUP harus 8-12 digit angka"
            )
        ]

        for rule in default_rules:
            try:
                await self.add_rule(rule)
            except Exception as e:
                self.logger.error(
                    "Failed to load default rule",
                    rule_name=rule.name,
                    error=str(e)
                )

    async def _calculate_stats(self):
        """Calculate rule statistics"""
        self.rule_stats["total_rules"] = len(self.rules)
        self.rule_stats["active_rules"] = len([r for r in self.rules.values() if r.is_active])

        # Count by type
        self.rule_stats["rules_by_type"] = {}
        self.rule_stats["rules_by_document_type"] = {}

        for rule in self.rules.values():
            # Count by rule type
            rule_type = rule.rule_type.value
            self.rule_stats["rules_by_type"][rule_type] = self.rule_stats["rules_by_type"].get(rule_type, 0) + 1

            # Count by document type
            doc_type = rule.document_type.value
            self.rule_stats["rules_by_document_type"][doc_type] = self.rule_stats["rules_by_document_type"].get(doc_type, 0) + 1

    async def get_stats(self) -> Dict[str, Any]:
        """Get rule engine statistics"""
        return {
            **self.rule_stats,
            "service": "rule_engine",
            "status": "active"
        }