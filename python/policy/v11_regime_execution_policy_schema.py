#!/usr/bin/env python3
"""
PR111: v1.1 Regime → Execution Policy Binding Schema (READ-ONLY)

Purpose:
    Schema for regime-execution policy binding records.
    Binding = Constitutional Gate (not action).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Override labels only (HOLD/DRY_RUN_ONLY/ALLOW/UNKNOWN)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - No execution vocabulary: No buy, sell, trade, swap
    - Non-evaluative: No good/bad vocabulary

Policy Binding Philosophy:
    Binding ≠ Decision
    Binding ≠ Action
    Binding = Constitutional Gate

    Policy binding establishes:
    - Execution permission overrides (based on regime)
    - Plan constraint additions (regime observation labels)
    - Basis (which regime fields informed policy)

    Policy binding does NOT:
    - Recommend trades
    - Optimize outcomes
    - Execute operations
    - Evaluate performance

Schema Design:
    - v11_policy_ prefix for policy fields
    - Permission overrides: UNKNOWN, HOLD, DRY_RUN_ONLY, ALLOW
    - Plan constraints: label strings only (no numbers)
    - Basis: regime field names only
"""

from typing import Any, Dict, List, Optional


class V11RegimeExecutionPolicySchema:
    """
    Schema for v1.1 regime-execution policy binding records.

    Binding = Constitutional Gate (not action).
    """

    # Required fields for policy record
    REQUIRED_FIELDS = [
        "v11_policy_mode",                      # Policy mode (ON/OFF)
        "v11_policy_status",                    # Policy status (AVAILABLE/UNAVAILABLE/ERROR)
        "v11_regime_level",                     # Regime level (from PR110)
        "v11_execution_permission_override",    # Permission override
        "v11_plan_constraints_append",          # Plan constraints to append
        "v11_policy_summary",                   # Summary of policy binding
        "v11_policy_basis",                     # Basis (regime fields used)
        "v11_policy_artifacts",                 # Artifacts (regime record reference)
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_policy_error_info",                # Error information if status is ERROR
        "v11_policy_metadata",                  # Additional metadata
    ]

    # Valid policy modes
    VALID_MODES = ["ON", "OFF"]

    # Valid policy statuses
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]

    # Valid regime levels (from PR110)
    VALID_REGIME_LEVELS = [
        "REGIME_LOW",
        "REGIME_MEDIUM",
        "REGIME_HIGH",
        "REGIME_CRITICAL",
        "UNCLASSIFIED",
    ]

    # Valid execution permission overrides
    VALID_PERMISSION_OVERRIDES = [
        "UNKNOWN",          # No override (defer to execution engine)
        "HOLD",             # Hard stop (critical regime)
        "DRY_RUN_ONLY",     # Simulation only (high regime)
        "ALLOW",            # Explicit permission (reserved for future use)
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate policy record structure.

        Args:
            record: Policy record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11RegimeExecutionPolicySchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_policy_mode" in record:
            mode = record["v11_policy_mode"]
            if mode not in V11RegimeExecutionPolicySchema.VALID_MODES:
                warnings.append(
                    f"Invalid v11_policy_mode: {mode}. "
                    f"Must be one of {V11RegimeExecutionPolicySchema.VALID_MODES}"
                )

        # Validate status
        if "v11_policy_status" in record:
            status = record["v11_policy_status"]
            if status not in V11RegimeExecutionPolicySchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v11_policy_status: {status}. "
                    f"Must be one of {V11RegimeExecutionPolicySchema.VALID_STATUSES}"
                )

        # Validate regime level
        if "v11_regime_level" in record:
            level = record["v11_regime_level"]
            if level not in V11RegimeExecutionPolicySchema.VALID_REGIME_LEVELS:
                warnings.append(
                    f"Invalid v11_regime_level: {level}. "
                    f"Must be one of {V11RegimeExecutionPolicySchema.VALID_REGIME_LEVELS}"
                )

        # Validate permission override
        if "v11_execution_permission_override" in record:
            override = record["v11_execution_permission_override"]
            if override not in V11RegimeExecutionPolicySchema.VALID_PERMISSION_OVERRIDES:
                warnings.append(
                    f"Invalid v11_execution_permission_override: {override}. "
                    f"Must be one of {V11RegimeExecutionPolicySchema.VALID_PERMISSION_OVERRIDES}"
                )

        # Validate plan constraints append
        if "v11_plan_constraints_append" in record:
            constraints = record["v11_plan_constraints_append"]
            if not isinstance(constraints, list):
                warnings.append("v11_plan_constraints_append must be a list")

        # Validate basis
        if "v11_policy_basis" in record:
            basis = record["v11_policy_basis"]
            if not isinstance(basis, list):
                warnings.append("v11_policy_basis must be a list")

        # Validate artifacts
        if "v11_policy_artifacts" in record:
            artifacts = record["v11_policy_artifacts"]
            if not isinstance(artifacts, list):
                warnings.append("v11_policy_artifacts must be a list")

        # Validate summary
        if "v11_policy_summary" in record:
            summary = record["v11_policy_summary"]
            if not isinstance(summary, str):
                warnings.append("v11_policy_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v11_policy_summary must not be empty")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty policy record with safe defaults.

        Returns:
            Empty policy record (unavailable state)
        """
        return {
            "v11_policy_mode": "OFF",
            "v11_policy_status": "UNAVAILABLE",
            "v11_regime_level": "UNCLASSIFIED",
            "v11_execution_permission_override": "UNKNOWN",
            "v11_plan_constraints_append": [],
            "v11_policy_summary": "policy binding unavailable. no regime classification available.",
            "v11_policy_basis": [],
            "v11_policy_artifacts": [],
        }

    @staticmethod
    def create_policy_record(
        regime_level: str,
        permission_override: str,
        plan_constraints_append: List[str],
        basis: List[str],
        artifacts: List[str],
    ) -> Dict[str, Any]:
        """
        Create policy binding record.

        Args:
            regime_level: Regime level (REGIME_LOW/MEDIUM/HIGH/CRITICAL/UNCLASSIFIED)
            permission_override: Permission override (UNKNOWN/HOLD/DRY_RUN_ONLY/ALLOW)
            plan_constraints_append: Plan constraints to append
            basis: List of regime fields that informed policy
            artifacts: List of artifact references

        Returns:
            Policy binding record
        """
        # Generate summary based on override
        if permission_override == "HOLD":
            summary = "regime binding applied. execution halted under critical regime conditions."
        elif permission_override == "DRY_RUN_ONLY":
            summary = "regime binding applied. execution limited to simulation under elevated regime conditions."
        elif permission_override == "UNKNOWN":
            summary = "regime binding applied. no permission override required."
        else:
            summary = "regime binding applied."

        return {
            "v11_policy_mode": "ON",
            "v11_policy_status": "AVAILABLE",
            "v11_regime_level": regime_level,
            "v11_execution_permission_override": permission_override,
            "v11_plan_constraints_append": plan_constraints_append,
            "v11_policy_summary": summary,
            "v11_policy_basis": basis,
            "v11_policy_artifacts": artifacts,
        }

    @staticmethod
    def create_error_record(
        error_info: str,
    ) -> Dict[str, Any]:
        """
        Create error policy record.

        Args:
            error_info: Error information

        Returns:
            Error policy record
        """
        return {
            "v11_policy_mode": "ON",
            "v11_policy_status": "ERROR",
            "v11_regime_level": "UNCLASSIFIED",
            "v11_execution_permission_override": "UNKNOWN",
            "v11_plan_constraints_append": [],
            "v11_policy_error_info": error_info,
            "v11_policy_summary": "policy binding error. defaulting to no override.",
            "v11_policy_basis": [],
            "v11_policy_artifacts": [],
        }


def get_regime_execution_policy_schema_info() -> Dict[str, Any]:
    """
    Get regime-execution policy schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "regime_execution_policy_binding",
        "required_fields": V11RegimeExecutionPolicySchema.REQUIRED_FIELDS,
        "optional_fields": V11RegimeExecutionPolicySchema.OPTIONAL_FIELDS,
        "valid_modes": V11RegimeExecutionPolicySchema.VALID_MODES,
        "valid_statuses": V11RegimeExecutionPolicySchema.VALID_STATUSES,
        "valid_regime_levels": V11RegimeExecutionPolicySchema.VALID_REGIME_LEVELS,
        "valid_permission_overrides": V11RegimeExecutionPolicySchema.VALID_PERMISSION_OVERRIDES,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Regime-Execution Policy Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V11RegimeExecutionPolicySchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V11RegimeExecutionPolicySchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: HOLD override
    print("Test 2: HOLD override (REGIME_CRITICAL)")
    hold_policy = V11RegimeExecutionPolicySchema.create_policy_record(
        regime_level="REGIME_CRITICAL",
        permission_override="HOLD",
        plan_constraints_append=["regime_critical_observed"],
        basis=["v11_regime_level"],
        artifacts=["pr110_regime_record"],
    )
    print(json.dumps(hold_policy, indent=2))
    warnings = V11RegimeExecutionPolicySchema.validate_structure(hold_policy)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: DRY_RUN_ONLY override
    print("Test 3: DRY_RUN_ONLY override (REGIME_HIGH)")
    dry_run_policy = V11RegimeExecutionPolicySchema.create_policy_record(
        regime_level="REGIME_HIGH",
        permission_override="DRY_RUN_ONLY",
        plan_constraints_append=["regime_high_observed"],
        basis=["v11_regime_level"],
        artifacts=["pr110_regime_record"],
    )
    print(json.dumps(dry_run_policy, indent=2))
    warnings = V11RegimeExecutionPolicySchema.validate_structure(dry_run_policy)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 4: No override (REGIME_LOW)
    print("Test 4: No override (REGIME_LOW)")
    no_override_policy = V11RegimeExecutionPolicySchema.create_policy_record(
        regime_level="REGIME_LOW",
        permission_override="UNKNOWN",
        plan_constraints_append=["regime_low_observed"],
        basis=["v11_regime_level"],
        artifacts=["pr110_regime_record"],
    )
    print(json.dumps(no_override_policy, indent=2))
    warnings = V11RegimeExecutionPolicySchema.validate_structure(no_override_policy)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
