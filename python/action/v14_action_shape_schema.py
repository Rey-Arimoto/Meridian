#!/usr/bin/env python3
"""
PR147: v1.4 Action Shape Guidance v1 Schema (READ-ONLY)

Purpose:
    Define schema for action shape guidance records.
    Action Shape = Display shape (not instruction, not recommendation).

    Bundles PR144 (safe band), PR146 (stress), PR145 (overlay), PR128 (eligibility)
    and returns a label-only action shape for user's own decision-making.

Record Prefix:
    v14_action_

Required Fields:
    v14_action_version: "v1"
    v14_action_status: AVAILABLE | ERROR
    v14_action_mode: READ_ONLY
    v14_action_action_shape: Action shape enum
    v14_action_scope: GLOBAL | *_ROLE_ONLY
    v14_action_summary: Non-prescriptive summary
    v14_action_inputs_present: Dict[str, bool] (presence flags)
    v14_action_constraints: List[str] (label-only)
    v14_action_basis: List[str] (label-only)
    v14_action_artifacts: List[str] (artifact references)
    v14_action_warnings: List[str]

Optional:
    v14_action_notes: List[str] (short descriptions, no forbidden vocab)

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading verbs: No buy/sell/swap/execute/sign/transfer
    - No token literals: No SUI/USDC/BTC/ETH
    - No numeric values in text: Label-only output
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/means
    - No prescriptive language: No should/must/need to/recommend
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Action version
ACTION_VERSION_V1 = "v1"

# Action status constants
ACTION_STATUS_AVAILABLE = "AVAILABLE"
ACTION_STATUS_ERROR = "ERROR"

# Action mode constants
ACTION_MODE_READ_ONLY = "READ_ONLY"

# Action shape constants (neutral vocabulary only)
ACTION_SHAPE_UNKNOWN = "ACTION_SHAPE_UNKNOWN"
ACTION_SHAPE_NO_ACTION = "ACTION_SHAPE_NO_ACTION"
ACTION_SHAPE_OBSERVE_ONLY = "ACTION_SHAPE_OBSERVE_ONLY"
ACTION_SHAPE_SIMULATION_ONLY = "ACTION_SHAPE_SIMULATION_ONLY"
ACTION_SHAPE_CONSIDER_ONLY = "ACTION_SHAPE_CONSIDER_ONLY"
ACTION_SHAPE_CONSTRAINED_STATE = "ACTION_SHAPE_CONSTRAINED_STATE"
ACTION_SHAPE_FREEZE_STATE = "ACTION_SHAPE_FREEZE_STATE"

# Action scope constants
ACTION_SCOPE_GLOBAL = "GLOBAL"
ACTION_SCOPE_VOLATILITY_ROLE_ONLY = "VOLATILITY_ROLE_ONLY"
ACTION_SCOPE_LIQUIDITY_ROLE_ONLY = "LIQUIDITY_ROLE_ONLY"
ACTION_SCOPE_STABILITY_ROLE_ONLY = "STABILITY_ROLE_ONLY"
ACTION_SCOPE_HEDGE_ROLE_ONLY = "HEDGE_ROLE_ONLY"
ACTION_SCOPE_GAS_ROLE_ONLY = "GAS_ROLE_ONLY"


class V14ActionShapeSchema:
    """Schema for action shape guidance records."""

    # Valid statuses
    VALID_STATUSES = [
        ACTION_STATUS_AVAILABLE,
        ACTION_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        ACTION_MODE_READ_ONLY,
    ]

    # Valid action shapes
    VALID_ACTION_SHAPES = [
        ACTION_SHAPE_UNKNOWN,
        ACTION_SHAPE_NO_ACTION,
        ACTION_SHAPE_OBSERVE_ONLY,
        ACTION_SHAPE_SIMULATION_ONLY,
        ACTION_SHAPE_CONSIDER_ONLY,
        ACTION_SHAPE_CONSTRAINED_STATE,
        ACTION_SHAPE_FREEZE_STATE,
    ]

    # Valid scopes
    VALID_SCOPES = [
        ACTION_SCOPE_GLOBAL,
        ACTION_SCOPE_VOLATILITY_ROLE_ONLY,
        ACTION_SCOPE_LIQUIDITY_ROLE_ONLY,
        ACTION_SCOPE_STABILITY_ROLE_ONLY,
        ACTION_SCOPE_HEDGE_ROLE_ONLY,
        ACTION_SCOPE_GAS_ROLE_ONLY,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v14_action_version",
        "v14_action_status",
        "v14_action_mode",
        "v14_action_action_shape",
        "v14_action_scope",
        "v14_action_summary",
        "v14_action_inputs_present",
        "v14_action_constraints",
        "v14_action_basis",
        "v14_action_artifacts",
        "v14_action_warnings",
    ]

    @staticmethod
    def create_action_record(
        version: str = ACTION_VERSION_V1,
        status: str = ACTION_STATUS_AVAILABLE,
        mode: str = ACTION_MODE_READ_ONLY,
        action_shape: str = ACTION_SHAPE_UNKNOWN,
        scope: str = ACTION_SCOPE_GLOBAL,
        summary: str = "",
        inputs_present: Optional[Dict[str, bool]] = None,
        constraints: Optional[List[str]] = None,
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create action shape guidance record.

        Args:
            version: Action version (default "v1")
            status: AVAILABLE | ERROR
            mode: READ_ONLY
            action_shape: Action shape enum
            scope: GLOBAL | *_ROLE_ONLY
            summary: Non-prescriptive summary
            inputs_present: Dict of input presence flags
            constraints: List of constraint labels
            basis: List of basis labels
            artifacts: List of artifact references
            warnings: List of warning strings
            notes: Optional notes

        Returns:
            Action shape record
        """
        record = {
            "v14_action_version": version,
            "v14_action_status": status,
            "v14_action_mode": mode,
            "v14_action_action_shape": action_shape,
            "v14_action_scope": scope,
            "v14_action_summary": summary,
            "v14_action_inputs_present": inputs_present if inputs_present else {},
            "v14_action_constraints": constraints if constraints else [],
            "v14_action_basis": basis if basis else [],
            "v14_action_artifacts": artifacts if artifacts else [],
            "v14_action_warnings": warnings if warnings else [],
        }

        # Add optional fields if provided
        if notes is not None:
            record["v14_action_notes"] = notes

        return record

    @staticmethod
    def create_error_record(
        summary: str = "action shape guidance generation failed.",
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary

        Returns:
            Error record
        """
        return V14ActionShapeSchema.create_action_record(
            status=ACTION_STATUS_ERROR,
            action_shape=ACTION_SHAPE_UNKNOWN,
            scope=ACTION_SCOPE_GLOBAL,
            summary=summary,
            inputs_present={},
            constraints=[],
            basis=[],
            artifacts=[],
            warnings=[],
        )

    @staticmethod
    def validate_action_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate action shape record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14ActionShapeSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v14_action_version")
        if version != ACTION_VERSION_V1:
            errors.append(f"invalid version: {version} (expected {ACTION_VERSION_V1})")

        # Validate status
        status = record.get("v14_action_status")
        if status not in V14ActionShapeSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v14_action_mode")
        if mode not in V14ActionShapeSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate action_shape
        action_shape = record.get("v14_action_action_shape")
        if action_shape not in V14ActionShapeSchema.VALID_ACTION_SHAPES:
            errors.append(f"invalid action_shape: {action_shape}")

        # Validate scope
        scope = record.get("v14_action_scope")
        if scope not in V14ActionShapeSchema.VALID_SCOPES:
            errors.append(f"invalid scope: {scope}")

        # Validate types
        if not isinstance(record.get("v14_action_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v14_action_inputs_present"), dict):
            errors.append("inputs_present must be dict")

        if not isinstance(record.get("v14_action_constraints"), list):
            errors.append("constraints must be list")

        if not isinstance(record.get("v14_action_basis"), list):
            errors.append("basis must be list")

        if not isinstance(record.get("v14_action_artifacts"), list):
            errors.append("artifacts must be list")

        if not isinstance(record.get("v14_action_warnings"), list):
            errors.append("warnings must be list")

        return errors


def get_action_shape_schema_info() -> Dict[str, Any]:
    """
    Get action shape schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "action_shape_guidance",
        "record_prefix": "v14_action_",
        "valid_statuses": V14ActionShapeSchema.VALID_STATUSES,
        "valid_modes": V14ActionShapeSchema.VALID_MODES,
        "valid_action_shapes": V14ActionShapeSchema.VALID_ACTION_SHAPES,
        "valid_scopes": V14ActionShapeSchema.VALID_SCOPES,
        "philosophy": "Action Shape ≠ Instruction. Display shape for user's own decision-making.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "no_numeric_values_in_text",
            "no_addresses",
            "no_causal_coupling",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Action Shape Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V14ActionShapeSchema.create_action_record(
        status=ACTION_STATUS_AVAILABLE,
        action_shape=ACTION_SHAPE_CONSIDER_ONLY,
        scope=ACTION_SCOPE_GLOBAL,
        summary="action shape indicates consideration-only state under current stress and eligibility labels.",
        inputs_present={
            "safe_band": True,
            "stress_rule": True,
            "eligibility": True,
        },
        constraints=["LABEL_ONLY", "READ_ONLY"],
        basis=["stress_label", "eligibility_label"],
    )
    errors1 = V14ActionShapeSchema.validate_action_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V14ActionShapeSchema.create_error_record(
        summary="action shape guidance generation failed: invalid inputs."
    )
    errors2 = V14ActionShapeSchema.validate_action_record(record2)
    print(f"Error record status: {record2['v14_action_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    info = get_action_shape_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
