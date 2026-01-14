#!/usr/bin/env python3
"""
PR150: v1.4 Stress Escalation Binding Engine v1 (READ-ONLY)

Purpose:
    Bind Shock Phase (PR149) to Stress (PR146) with escalate-only logic.
    Escalate-only: max(current_stress, min_required_by_phase)
    No de-escalation: Never lower stress (de-escalation is out of scope)

API:
    build_stress_escalation_record_v1(phase_record, stress_record) -> dict
    build_stress_escalation_from_bundle_v1(artifact_bundle) -> dict
    get_stress_escalation_info() -> dict

Fixed Escalation Table:
    PHASE_UNKNOWN → STRESS_UNKNOWN (immutable)
    PHASE_ERROR → STRESS_UNKNOWN (immutable)
    PHASE_NORMAL → NO_CHANGE
    PHASE_PRE_SHOCK → STRESS_TENSE
    PHASE_UP_SHOCK → STRESS_STRESSED
    PHASE_DOWN_SHOCK → STRESS_STRESSED
    PHASE_UP_REVERSAL → STRESS_TENSE
    PHASE_DOWN_REVERSAL → STRESS_TENSE
    PHASE_RECOVERY → NO_CHANGE

Stress Priority:
    STRESS_STRESSED > STRESS_TENSE > STRESS_CALM > STRESS_UNKNOWN

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only output: No numeric values in text
    - Escalate-only: Never lower stress
    - Defensive: Invalid input → valid ERROR record
    - Warning-only: Never raises exceptions
"""

from typing import Any, Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from escalation.v14_stress_escalation_schema import (
    V14StressEscalationSchema,
    ESCALATION_VERSION_V1,
    ESCALATION_STATUS_AVAILABLE,
    ESCALATION_STATUS_UNKNOWN,
    ESCALATION_STATUS_ERROR,
    ESCALATION_MODE_READ_ONLY,
    ESCALATED_FLAG_ON,
    ESCALATED_FLAG_OFF,
    ESCALATED_FLAG_UNKNOWN,
)

# Import from PR149 (shock)
from shock.v14_shock_phase_schema import (
    PHASE_UNKNOWN,
    PHASE_NORMAL,
    PHASE_PRE_SHOCK,
    PHASE_UP_SHOCK,
    PHASE_DOWN_SHOCK,
    PHASE_UP_REVERSAL,
    PHASE_DOWN_REVERSAL,
    PHASE_RECOVERY,
    PHASE_ERROR,
)

# Import from PR146 (stress)
from stress.v14_stress_rule_table_schema import (
    STRESS_CALM,
    STRESS_TENSE,
    STRESS_STRESSED,
    STRESS_UNKNOWN,
)


# Fixed escalation table (Phase → Minimum Stress)
ESCALATION_TABLE_V1 = {
    PHASE_UNKNOWN: STRESS_UNKNOWN,  # Immutable
    PHASE_ERROR: STRESS_UNKNOWN,  # Immutable
    PHASE_NORMAL: None,  # NO_CHANGE
    PHASE_PRE_SHOCK: STRESS_TENSE,
    PHASE_UP_SHOCK: STRESS_STRESSED,
    PHASE_DOWN_SHOCK: STRESS_STRESSED,
    PHASE_UP_REVERSAL: STRESS_TENSE,
    PHASE_DOWN_REVERSAL: STRESS_TENSE,
    PHASE_RECOVERY: None,  # NO_CHANGE
}

# Stress priority (for comparison)
STRESS_PRIORITY = {
    STRESS_STRESSED: 3,
    STRESS_TENSE: 2,
    STRESS_CALM: 1,
    STRESS_UNKNOWN: 0,
}


def _get_min_required_stress(phase_label: str) -> Optional[str]:
    """
    Get minimum required stress for a given phase.

    Args:
        phase_label: Phase label from PR149

    Returns:
        Minimum stress label or None (NO_CHANGE)
    """
    return ESCALATION_TABLE_V1.get(phase_label, None)


def _compare_stress(stress_a: str, stress_b: str) -> int:
    """
    Compare two stress labels.

    Args:
        stress_a: First stress label
        stress_b: Second stress label

    Returns:
        1 if stress_a > stress_b, -1 if stress_a < stress_b, 0 if equal
    """
    priority_a = STRESS_PRIORITY.get(stress_a, 0)
    priority_b = STRESS_PRIORITY.get(stress_b, 0)

    if priority_a > priority_b:
        return 1
    elif priority_a < priority_b:
        return -1
    else:
        return 0


def _escalate_stress(
    input_stress: str,
    min_required: Optional[str],
    phase_label: str,
) -> Tuple[str, str, List[str]]:
    """
    Escalate stress (escalate-only, never lower).

    Args:
        input_stress: Current stress label
        min_required: Minimum required stress (None = NO_CHANGE)
        phase_label: Phase label (for diagnostics)

    Returns:
        Tuple of (output_stress, escalated_flag, warnings)
    """
    warnings = []

    # Rule 1: If input is UNKNOWN, cannot escalate (immutable)
    if input_stress == STRESS_UNKNOWN:
        warnings.append(f"current stress is UNKNOWN, cannot escalate (phase={phase_label})")
        return (STRESS_UNKNOWN, ESCALATED_FLAG_UNKNOWN, warnings)

    # Rule 2: If phase requires UNKNOWN (phase=ERROR/UNKNOWN), cannot change
    if min_required == STRESS_UNKNOWN:
        warnings.append(f"phase {phase_label} requires UNKNOWN, current stress maintained")
        return (input_stress, ESCALATED_FLAG_OFF, warnings)

    # Rule 3: If min_required is None (NO_CHANGE), keep input
    if min_required is None:
        return (input_stress, ESCALATED_FLAG_OFF, warnings)

    # Rule 4: Escalate-only: max(input, min_required)
    comparison = _compare_stress(input_stress, min_required)

    if comparison >= 0:
        # input >= min_required, keep input (no escalation needed)
        return (input_stress, ESCALATED_FLAG_OFF, warnings)
    else:
        # input < min_required, escalate to min_required
        return (min_required, ESCALATED_FLAG_ON, warnings)


def build_stress_escalation_record_v1(
    phase_record: Optional[Dict[str, Any]],
    stress_record: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build stress escalation record from phase and stress records.

    Args:
        phase_record: Shock phase record from PR149
        stress_record: Stress record from PR146

    Returns:
        Dict with:
        - escalation_record: PR150-compliant escalation record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid phase_record
    if phase_record is None or not isinstance(phase_record, dict):
        warnings.append("invalid phase_record (expected dict, got None or non-dict)")
        error_record = V14StressEscalationSchema.create_error_record(warnings=warnings)
        return {
            "escalation_record": error_record,
            "warnings": warnings,
        }

    # Defensive: Handle invalid stress_record
    if stress_record is None or not isinstance(stress_record, dict):
        warnings.append("invalid stress_record (expected dict, got None or non-dict)")
        error_record = V14StressEscalationSchema.create_error_record(warnings=warnings)
        return {
            "escalation_record": error_record,
            "warnings": warnings,
        }

    # Extract phase label
    phase_label = phase_record.get("v14_shock_phase_label", "")
    if not phase_label:
        warnings.append("missing v14_shock_phase_label in phase_record")
        phase_label = PHASE_UNKNOWN

    # Extract stress label
    input_stress = stress_record.get("v14_stress_label", "")
    if not input_stress:
        warnings.append("missing v14_stress_label in stress_record")
        input_stress = STRESS_UNKNOWN

    # Track input presence
    inputs_present = {
        "phase": bool(phase_label and phase_label != PHASE_UNKNOWN),
        "stress": bool(input_stress and input_stress != STRESS_UNKNOWN),
    }

    # Get minimum required stress from table
    min_required = _get_min_required_stress(phase_label)
    min_required_label = min_required if min_required else "NO_CHANGE"

    # Escalate stress
    output_stress, escalated_flag, escalation_warnings = _escalate_stress(
        input_stress,
        min_required,
        phase_label,
    )
    warnings.extend(escalation_warnings)

    # Create escalation record
    escalation_record = V14StressEscalationSchema.create_escalation_record(
        version=ESCALATION_VERSION_V1,
        status=ESCALATION_STATUS_AVAILABLE,
        mode=ESCALATION_MODE_READ_ONLY,
        phase_label=phase_label,
        input_stress_label=input_stress,
        min_required_stress_label=min_required_label,
        output_stress_label=output_stress,
        escalated_flag=escalated_flag,
        inputs_present=inputs_present,
        warnings=warnings,
    )

    # Validate schema
    schema_errors = V14StressEscalationSchema.validate_escalation_record(escalation_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    return {
        "escalation_record": escalation_record,
        "warnings": warnings,
    }


def build_stress_escalation_from_bundle_v1(
    artifact_bundle: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build stress escalation record from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle with phase and stress records

    Returns:
        Dict with:
        - escalation_record: PR150-compliant escalation record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid artifact_bundle
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V14StressEscalationSchema.create_error_record(warnings=warnings)
        return {
            "escalation_record": error_record,
            "warnings": warnings,
        }

    # Extract from bundle
    artifacts = artifact_bundle.get("artifacts", {})

    # Try to get shock phase record
    phase_record = artifacts.get("shock_phase_record")
    if not phase_record:
        warnings.append("missing shock_phase_record in artifacts")
        phase_record = {}

    # Try to get stress record
    stress_record = artifacts.get("stress_record")
    if not stress_record:
        warnings.append("missing stress_record in artifacts")
        stress_record = {}

    # Build escalation record
    return build_stress_escalation_record_v1(phase_record, stress_record)


def get_stress_escalation_info() -> Dict[str, Any]:
    """
    Get stress escalation information.

    Returns:
        Dict with escalation metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "stress_escalation_binding",
        "philosophy": "Escalate-only: max(current, min_required_by_phase). No de-escalation in PR150.",
        "escalation_table": {
            "PHASE_UNKNOWN": "STRESS_UNKNOWN (immutable)",
            "PHASE_ERROR": "STRESS_UNKNOWN (immutable)",
            "PHASE_NORMAL": "NO_CHANGE",
            "PHASE_PRE_SHOCK": "STRESS_TENSE",
            "PHASE_UP_SHOCK": "STRESS_STRESSED",
            "PHASE_DOWN_SHOCK": "STRESS_STRESSED",
            "PHASE_UP_REVERSAL": "STRESS_TENSE",
            "PHASE_DOWN_REVERSAL": "STRESS_TENSE",
            "PHASE_RECOVERY": "NO_CHANGE",
        },
        "stress_priority": "STRESSED > TENSE > CALM > UNKNOWN",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "label_output_only",
            "escalate_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Stress Escalation Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: PRE_SHOCK escalates CALM to TENSE
    print("Test 1: PRE_SHOCK escalates CALM to TENSE")
    phase_rec1 = {"v14_shock_phase_label": PHASE_PRE_SHOCK}
    stress_rec1 = {"v14_stress_label": STRESS_CALM}
    result1 = build_stress_escalation_record_v1(phase_rec1, stress_rec1)
    print(f"Input: {stress_rec1['v14_stress_label']}, Output: {result1['escalation_record']['v14_escalation_output_stress_label']}")
    print(f"Escalated: {result1['escalation_record']['v14_escalation_escalated_flag']}")
    print()

    # Test 2: UP_SHOCK escalates CALM to STRESSED
    print("Test 2: UP_SHOCK escalates CALM to STRESSED")
    phase_rec2 = {"v14_shock_phase_label": PHASE_UP_SHOCK}
    stress_rec2 = {"v14_stress_label": STRESS_CALM}
    result2 = build_stress_escalation_record_v1(phase_rec2, stress_rec2)
    print(f"Input: {stress_rec2['v14_stress_label']}, Output: {result2['escalation_record']['v14_escalation_output_stress_label']}")
    print(f"Escalated: {result2['escalation_record']['v14_escalation_escalated_flag']}")
    print()

    # Test 3: NORMAL does not escalate
    print("Test 3: NORMAL does not escalate")
    phase_rec3 = {"v14_shock_phase_label": PHASE_NORMAL}
    stress_rec3 = {"v14_stress_label": STRESS_TENSE}
    result3 = build_stress_escalation_record_v1(phase_rec3, stress_rec3)
    print(f"Input: {stress_rec3['v14_stress_label']}, Output: {result3['escalation_record']['v14_escalation_output_stress_label']}")
    print(f"Escalated: {result3['escalation_record']['v14_escalation_escalated_flag']}")
    print()

    # Test 4: Current STRESSED stays STRESSED (no de-escalation)
    print("Test 4: Current STRESSED stays STRESSED")
    phase_rec4 = {"v14_shock_phase_label": PHASE_PRE_SHOCK}  # min=TENSE
    stress_rec4 = {"v14_stress_label": STRESS_STRESSED}
    result4 = build_stress_escalation_record_v1(phase_rec4, stress_rec4)
    print(f"Input: {stress_rec4['v14_stress_label']}, Output: {result4['escalation_record']['v14_escalation_output_stress_label']}")
    print(f"Escalated: {result4['escalation_record']['v14_escalation_escalated_flag']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
