#!/usr/bin/env python3
"""
PR151: v1.4 Rebalance Template Guidance Engine v1 (READ-ONLY)

Purpose:
    Map Shock Phase + Stress + Action Shape + Trend → Template ID using fixed rules.
    First-match-wins rule table with guard priority.

    IMPORTANT: Python does NOT hold token names (wBTC/USDC).
    IMPORTANT: Python does NOT output numeric ratios in text.
    Output is template_id only (e.g., TPL_RISK_90).
    TS side resolves template_id to actual token ratios.

Fixed Rule Table (first-match-wins):
    Guards (highest priority):
    1. action_shape == FREEZE_STATE → TPL_RISK_0 (RULE_GUARD_FREEZE)
    2. stress == STRESSED → TPL_RISK_0 (RULE_GUARD_STRESSED)

    Shock Phase:
    3. phase == PHASE_DOWN_SHOCK → TPL_RISK_0 (RULE_DOWN_SHOCK)
    4. phase == PHASE_DOWN_REVERSAL → TPL_RISK_50 (RULE_DOWN_REVERSAL)
    5. phase == PHASE_UP_SHOCK → TPL_RISK_90 (RULE_UP_SHOCK)
    6. phase == PHASE_UP_REVERSAL → TPL_RISK_0 (RULE_UP_REVERSAL)

    NORMAL + Trend:
    7. phase == PHASE_NORMAL and trend == UP_TREND → TPL_RISK_90 (RULE_NORMAL_UP_TREND)
    8. phase == PHASE_NORMAL and trend == DOWN_TREND → TPL_RISK_20 (RULE_NORMAL_DOWN_TREND)
    9. phase == PHASE_NORMAL and trend == RANGE → TPL_RISK_50 (RULE_NORMAL_RANGE)

    Fallback:
    10. fallback → TPL_UNKNOWN (RULE_FALLBACK_UNKNOWN)

API:
    build_rebalance_template_guidance_v1(artifact_bundle) -> dict
    extract_rebalance_inputs_v1(artifact_bundle) -> (phase, stress, action_shape, trend, presence)
    get_rebalance_engine_info() -> dict

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No token names: No wBTC/USDC/SUI
    - No numeric ratios: No percentages in text
    - Non-prescriptive: No should/must/recommend/advise
    - Defensive: Invalid input → ERROR record
    - Warning-only: Never raises exceptions
"""

from typing import Any, Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rebalance.v14_rebalance_template_schema import (
    V14RebalanceTemplateSchema,
    REBALANCE_VERSION_V1,
    REBALANCE_STATUS_AVAILABLE,
    REBALANCE_STATUS_ERROR,
    TPL_UNKNOWN,
    TPL_RISK_0,
    TPL_RISK_20,
    TPL_RISK_50,
    TPL_RISK_90,
    SCOPE_PORTFOLIO_REBALANCE,
    RULE_GUARD_FREEZE,
    RULE_GUARD_STRESSED,
    RULE_DOWN_SHOCK,
    RULE_DOWN_REVERSAL,
    RULE_UP_SHOCK,
    RULE_UP_REVERSAL,
    RULE_NORMAL_UP_TREND,
    RULE_NORMAL_DOWN_TREND,
    RULE_NORMAL_RANGE,
    RULE_FALLBACK_UNKNOWN,
)

# Trend labels (minimal definition for PR151)
TREND_UP_TREND = "UP_TREND"
TREND_DOWN_TREND = "DOWN_TREND"
TREND_RANGE = "RANGE"
TREND_UNKNOWN = "UNKNOWN"


def extract_rebalance_inputs_v1(
    artifact_bundle: Optional[Dict[str, Any]],
) -> Tuple[str, str, str, str, Dict[str, bool]]:
    """
    Extract rebalance inputs from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle with shock/stress/action_shape/trend records

    Returns:
        Tuple of (phase_label, stress_label, action_shape_label, trend_label, presence_map)
    """
    phase_label = ""
    stress_label = ""
    action_shape_label = ""
    trend_label = ""

    presence = {
        "shock_phase": False,
        "stress": False,
        "action_shape": False,
        "trend": False,
    }

    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        return (phase_label, stress_label, action_shape_label, trend_label, presence)

    artifacts = artifact_bundle.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return (phase_label, stress_label, action_shape_label, trend_label, presence)

    # Extract shock phase (PR149)
    shock_phase_record = artifacts.get("shock_phase_record")
    if shock_phase_record and isinstance(shock_phase_record, dict):
        phase_label = shock_phase_record.get("v14_shock_phase_label", "")
        if phase_label:
            presence["shock_phase"] = True

    # Extract stress (PR150 escalation output)
    stress_escalation_record = artifacts.get("stress_escalation_record")
    if stress_escalation_record and isinstance(stress_escalation_record, dict):
        stress_label = stress_escalation_record.get("v14_escalation_output_stress_label", "")
        if stress_label:
            presence["stress"] = True

    # Extract action shape (PR147)
    action_shape_record = artifacts.get("action_shape_record")
    if action_shape_record and isinstance(action_shape_record, dict):
        action_shape_label = action_shape_record.get("v14_action_shape_label", "")
        if action_shape_label:
            presence["action_shape"] = True

    # Extract trend (minimal definition - may not exist yet)
    trend_record = artifacts.get("trend_record")
    if trend_record and isinstance(trend_record, dict):
        trend_label = trend_record.get("v14_trend_label", "")
        if trend_label:
            presence["trend"] = True

    return (phase_label, stress_label, action_shape_label, trend_label, presence)


def _apply_rebalance_rules_v1(
    phase_label: str,
    stress_label: str,
    action_shape_label: str,
    trend_label: str,
) -> Tuple[str, str]:
    """
    Apply rebalance rules (first-match-wins).

    Args:
        phase_label: Shock phase label from PR149
        stress_label: Stress label from PR150 (escalation output)
        action_shape_label: Action shape label from PR147
        trend_label: Trend label

    Returns:
        Tuple of (template_id, rule_id)
    """
    # Rule 1: Guard - FREEZE_STATE (highest priority)
    if action_shape_label == "FREEZE_STATE":
        return (TPL_RISK_0, RULE_GUARD_FREEZE)

    # Rule 2: Guard - STRESSED
    if stress_label == "STRESS_STRESSED":
        return (TPL_RISK_0, RULE_GUARD_STRESSED)

    # Rule 3: DOWN_SHOCK
    if phase_label == "PHASE_DOWN_SHOCK":
        return (TPL_RISK_0, RULE_DOWN_SHOCK)

    # Rule 4: DOWN_REVERSAL
    if phase_label == "PHASE_DOWN_REVERSAL":
        return (TPL_RISK_50, RULE_DOWN_REVERSAL)

    # Rule 5: UP_SHOCK
    if phase_label == "PHASE_UP_SHOCK":
        return (TPL_RISK_90, RULE_UP_SHOCK)

    # Rule 6: UP_REVERSAL
    if phase_label == "PHASE_UP_REVERSAL":
        return (TPL_RISK_0, RULE_UP_REVERSAL)

    # Rule 7: NORMAL + UP_TREND
    if phase_label == "PHASE_NORMAL" and trend_label == TREND_UP_TREND:
        return (TPL_RISK_90, RULE_NORMAL_UP_TREND)

    # Rule 8: NORMAL + DOWN_TREND
    if phase_label == "PHASE_NORMAL" and trend_label == TREND_DOWN_TREND:
        return (TPL_RISK_20, RULE_NORMAL_DOWN_TREND)

    # Rule 9: NORMAL + RANGE
    if phase_label == "PHASE_NORMAL" and trend_label == TREND_RANGE:
        return (TPL_RISK_50, RULE_NORMAL_RANGE)

    # Rule 10: Fallback (safe default)
    return (TPL_UNKNOWN, RULE_FALLBACK_UNKNOWN)


def build_rebalance_template_guidance_v1(
    artifact_bundle: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build rebalance template guidance from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle with shock/stress/action_shape/trend records

    Returns:
        Dict with:
        - rebalance_record: PR151-compliant rebalance record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid artifact_bundle
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V14RebalanceTemplateSchema.build_rebalance_record_error(warnings=warnings)
        return {
            "rebalance_record": error_record,
            "warnings": warnings,
        }

    # Extract inputs
    phase_label, stress_label, action_shape_label, trend_label, presence = extract_rebalance_inputs_v1(
        artifact_bundle
    )

    # Warn if inputs are missing
    if not presence["shock_phase"]:
        warnings.append("missing shock_phase_record in artifact_bundle")
    if not presence["stress"]:
        warnings.append("missing stress_escalation_record in artifact_bundle")
    if not presence["action_shape"]:
        warnings.append("missing action_shape_record in artifact_bundle")
    if not presence["trend"]:
        warnings.append("missing trend_record in artifact_bundle (safe default: UNKNOWN)")

    # Apply rules (first-match-wins)
    template_id, rule_id = _apply_rebalance_rules_v1(
        phase_label,
        stress_label,
        action_shape_label,
        trend_label if trend_label else TREND_UNKNOWN,
    )

    # Build basis labels
    basis_labels = {
        "shock_phase": phase_label if phase_label else "UNKNOWN",
        "stress": stress_label if stress_label else "UNKNOWN",
        "action_shape": action_shape_label if action_shape_label else "UNKNOWN",
        "trend": trend_label if trend_label else TREND_UNKNOWN,
    }

    # Build rebalance record
    rebalance_record = V14RebalanceTemplateSchema.build_rebalance_record_ok(
        template_id=template_id,
        rule_id=rule_id,
        basis_labels=basis_labels,
        inputs_present=presence,
        warnings=warnings,
    )

    # Validate schema
    is_valid, schema_warnings = V14RebalanceTemplateSchema.validate_rebalance_record(rebalance_record)
    if not is_valid:
        warnings.extend([f"schema validation: {w}" for w in schema_warnings])

    return {
        "rebalance_record": rebalance_record,
        "warnings": warnings,
    }


def get_rebalance_engine_info() -> Dict[str, Any]:
    """
    Get rebalance engine information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "rebalance_template_guidance",
        "philosophy": "Template ID only. TS side resolves to actual token ratios. No token names in Python.",
        "rule_table": {
            "1_GUARD_FREEZE": "action_shape=FREEZE_STATE → TPL_RISK_0",
            "2_GUARD_STRESSED": "stress=STRESSED → TPL_RISK_0",
            "3_DOWN_SHOCK": "phase=DOWN_SHOCK → TPL_RISK_0",
            "4_DOWN_REVERSAL": "phase=DOWN_REVERSAL → TPL_RISK_50",
            "5_UP_SHOCK": "phase=UP_SHOCK → TPL_RISK_90",
            "6_UP_REVERSAL": "phase=UP_REVERSAL → TPL_RISK_0",
            "7_NORMAL_UP_TREND": "phase=NORMAL + trend=UP_TREND → TPL_RISK_90",
            "8_NORMAL_DOWN_TREND": "phase=NORMAL + trend=DOWN_TREND → TPL_RISK_20",
            "9_NORMAL_RANGE": "phase=NORMAL + trend=RANGE → TPL_RISK_50",
            "10_FALLBACK": "fallback → TPL_UNKNOWN",
        },
        "rule_priority": "first-match-wins (guards have highest priority)",
        "template_ids": [TPL_UNKNOWN, TPL_RISK_0, TPL_RISK_20, TPL_RISK_50, TPL_RISK_90],
        "constitutional_guarantees": [
            "READ-ONLY",
            "no_token_names",
            "no_numeric_ratios_in_text",
            "non_prescriptive",
            "label_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Rebalance Template Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: Guard - FREEZE_STATE
    print("Test 1: Guard - FREEZE_STATE → TPL_RISK_0")
    bundle1 = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "FREEZE_STATE"},
            "trend_record": {"v14_trend_label": "UP_TREND"},
        }
    }
    result1 = build_rebalance_template_guidance_v1(bundle1)
    print(f"Template: {result1['rebalance_record']['v14_rebalance_template_id']}")
    print(f"Rule: {result1['rebalance_record']['v14_rebalance_rule_id']}")
    print()

    # Test 2: UP_SHOCK
    print("Test 2: UP_SHOCK → TPL_RISK_90")
    bundle2 = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_UP_SHOCK"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UNKNOWN"},
        }
    }
    result2 = build_rebalance_template_guidance_v1(bundle2)
    print(f"Template: {result2['rebalance_record']['v14_rebalance_template_id']}")
    print(f"Rule: {result2['rebalance_record']['v14_rebalance_rule_id']}")
    print()

    # Test 3: NORMAL + UP_TREND
    print("Test 3: NORMAL + UP_TREND → TPL_RISK_90")
    bundle3 = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UP_TREND"},
        }
    }
    result3 = build_rebalance_template_guidance_v1(bundle3)
    print(f"Template: {result3['rebalance_record']['v14_rebalance_template_id']}")
    print(f"Rule: {result3['rebalance_record']['v14_rebalance_rule_id']}")
    print()

    # Test 4: Fallback (missing inputs)
    print("Test 4: Fallback (missing inputs) → TPL_UNKNOWN")
    bundle4 = {"artifacts": {}}
    result4 = build_rebalance_template_guidance_v1(bundle4)
    print(f"Template: {result4['rebalance_record']['v14_rebalance_template_id']}")
    print(f"Rule: {result4['rebalance_record']['v14_rebalance_rule_id']}")
    print(f"Warnings: {len(result4['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
