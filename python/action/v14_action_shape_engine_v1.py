#!/usr/bin/env python3
"""
PR147: v1.4 Action Shape Engine v1 (READ-ONLY)

Purpose:
    Build action shape guidance from artifact bundle.
    Bundles PR144/PR145/PR146/PR128 and returns label-only action shape.
    Action Shape = Display shape (not instruction, not recommendation).

API:
    build_action_shape_from_bundle_v1(artifact_bundle) -> dict

Bundle Interpretation:
    - PR144: safe_band_guidance (band bucket/status per role)
    - PR146: stress_rule (stress label CALM/TENSE/STRESSED/UNKNOWN)
    - PR145: stress_overlay (optional, conflict check with PR146)
    - PR128: eligibility (INELIGIBLE/ELIGIBLE_CONSIDERATION_ONLY/ELIGIBLE_DRY_RUN_ONLY)

Fixed Rule Table (Priority):
    1. draft/error/invalid → UNKNOWN + warning
    2. eligibility = INELIGIBLE → NO_ACTION
    3. stress = STRESSED → FREEZE_STATE
    4. stress = TENSE:
       - eligibility = CONSIDERATION_ONLY → CONSIDER_ONLY
       - else → SIMULATION_ONLY
    5. stress = CALM:
       - eligibility = CONSIDERATION_ONLY → CONSIDER_ONLY
       - else → OBSERVE_ONLY
    6. default → UNKNOWN

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Label-only extraction: No numeric values
    - Defensive: Invalid input → valid ERROR record
    - Warning-only: Never raises exceptions
"""

from typing import Any, Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from action.v14_action_shape_schema import (
    V14ActionShapeSchema,
    ACTION_VERSION_V1,
    ACTION_STATUS_AVAILABLE,
    ACTION_STATUS_ERROR,
    ACTION_MODE_READ_ONLY,
    ACTION_SHAPE_UNKNOWN,
    ACTION_SHAPE_NO_ACTION,
    ACTION_SHAPE_OBSERVE_ONLY,
    ACTION_SHAPE_SIMULATION_ONLY,
    ACTION_SHAPE_CONSIDER_ONLY,
    ACTION_SHAPE_CONSTRAINED_STATE,
    ACTION_SHAPE_FREEZE_STATE,
    ACTION_SCOPE_GLOBAL,
)


def _extract_stress_label_from_bundle(artifact_bundle: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Extract stress label from artifact bundle (PR146 priority).

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        Tuple of (stress_label, warnings)
    """
    warnings = []

    artifacts = artifact_bundle.get("artifacts", {})

    # Try PR146 stress_rule first (priority)
    stress_rule = artifacts.get("stress_rule")
    if stress_rule and isinstance(stress_rule, dict):
        stress_label = stress_rule.get("v14_stress_label", "UNKNOWN")
        if stress_label:
            return (stress_label, warnings)

    # Fallback to PR145 overlay (check for conflict later)
    stress_overlay = artifacts.get("stress_overlay")
    if stress_overlay and isinstance(stress_overlay, dict):
        overlay_stress_label = stress_overlay.get("v14_overlay_band_stress_label", "UNKNOWN")
        if overlay_stress_label:
            warnings.append("using stress_overlay label (PR146 stress_rule not found)")
            return (overlay_stress_label, warnings)

    warnings.append("no stress label found in bundle")
    return ("UNKNOWN", warnings)


def _extract_eligibility_label_from_bundle(artifact_bundle: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Extract eligibility label from artifact bundle (PR128).

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        Tuple of (eligibility_label, warnings)
    """
    warnings = []

    artifacts = artifact_bundle.get("artifacts", {})

    # Try PR128 eligibility record
    eligibility_record = artifacts.get("eligibility")
    if eligibility_record and isinstance(eligibility_record, dict):
        eligibility_label = eligibility_record.get("v12_eligibility_label", "UNKNOWN")
        if eligibility_label:
            return (eligibility_label, warnings)

    warnings.append("no eligibility label found in bundle")
    return ("UNKNOWN", warnings)


def _check_stress_conflict(artifact_bundle: Dict[str, Any]) -> List[str]:
    """
    Check for conflict between PR146 stress_rule and PR145 overlay.

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        List of warnings (empty if no conflict)
    """
    warnings = []

    artifacts = artifact_bundle.get("artifacts", {})

    stress_rule = artifacts.get("stress_rule")
    stress_overlay = artifacts.get("stress_overlay")

    if stress_rule and stress_overlay:
        if isinstance(stress_rule, dict) and isinstance(stress_overlay, dict):
            rule_label = stress_rule.get("v14_stress_label")
            overlay_label = stress_overlay.get("v14_overlay_band_stress_label")

            if rule_label and overlay_label and rule_label != overlay_label:
                warnings.append(f"stress_overlay_conflict: PR146={rule_label} PR145={overlay_label}, using PR146")

    return warnings


def _determine_action_shape(stress_label: str, eligibility_label: str) -> Tuple[str, List[str]]:
    """
    Determine action shape using fixed rule table.

    Args:
        stress_label: Stress label (CALM/TENSE/STRESSED/UNKNOWN)
        eligibility_label: Eligibility label

    Returns:
        Tuple of (action_shape, basis_labels)
    """
    # Priority rules (first-match-wins)

    # Rule 1: Invalid stress → UNKNOWN
    if stress_label == "UNKNOWN":
        return (ACTION_SHAPE_UNKNOWN, ["BASIS_STRESS_UNKNOWN"])

    # Rule 2: eligibility = INELIGIBLE → NO_ACTION
    if eligibility_label == "INELIGIBLE":
        return (ACTION_SHAPE_NO_ACTION, ["BASIS_ELIGIBILITY_INELIGIBLE"])

    # Rule 3: stress = STRESSED → FREEZE_STATE
    if stress_label == "STRESSED":
        return (ACTION_SHAPE_FREEZE_STATE, ["BASIS_STRESS_STRESSED"])

    # Rule 4: stress = TENSE
    if stress_label == "TENSE":
        if eligibility_label == "ELIGIBLE_CONSIDERATION_ONLY":
            return (ACTION_SHAPE_CONSIDER_ONLY, ["BASIS_STRESS_TENSE", "BASIS_ELIGIBILITY_CONSIDERATION_ONLY"])
        else:
            return (ACTION_SHAPE_SIMULATION_ONLY, ["BASIS_STRESS_TENSE"])

    # Rule 5: stress = CALM
    if stress_label == "CALM":
        if eligibility_label == "ELIGIBLE_CONSIDERATION_ONLY":
            return (ACTION_SHAPE_CONSIDER_ONLY, ["BASIS_STRESS_CALM", "BASIS_ELIGIBILITY_CONSIDERATION_ONLY"])
        else:
            return (ACTION_SHAPE_OBSERVE_ONLY, ["BASIS_STRESS_CALM"])

    # Rule 6: default → UNKNOWN
    return (ACTION_SHAPE_UNKNOWN, ["BASIS_DEFAULT_UNKNOWN"])


def _create_action_summary(action_shape: str) -> str:
    """
    Create non-prescriptive action summary.

    Args:
        action_shape: Action shape enum

    Returns:
        Summary string
    """
    # Templates (no forbidden vocabulary)
    templates = {
        ACTION_SHAPE_NO_ACTION: "action shape indicates no-action state under current eligibility label.",
        ACTION_SHAPE_OBSERVE_ONLY: "action shape indicates observe-only state under current stress label.",
        ACTION_SHAPE_SIMULATION_ONLY: "action shape indicates simulation-only state under current stress label.",
        ACTION_SHAPE_CONSIDER_ONLY: "action shape indicates consideration-only state under current stress and eligibility labels.",
        ACTION_SHAPE_CONSTRAINED_STATE: "action shape indicates constrained state under current conditions.",
        ACTION_SHAPE_FREEZE_STATE: "action shape indicates freeze state under elevated structural stress.",
        ACTION_SHAPE_UNKNOWN: "action shape could not be determined from available inputs.",
    }

    return templates.get(action_shape, "action shape determined from available inputs.")


def build_action_shape_from_bundle_v1(
    artifact_bundle: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build action shape guidance from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle with PR144/PR145/PR146/PR128 artifacts

    Returns:
        Dict with:
        - action_record: PR147-compliant action record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid artifact_bundle
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V14ActionShapeSchema.create_error_record(
            summary="action shape guidance generation failed: invalid artifact bundle."
        )
        return {
            "action_record": error_record,
            "warnings": warnings,
        }

    # Track input presence
    inputs_present = {
        "safe_band": False,
        "stress_rule": False,
        "stress_overlay": False,
        "eligibility": False,
    }

    artifacts = artifact_bundle.get("artifacts", {})

    if artifacts.get("safe_band_guidance"):
        inputs_present["safe_band"] = True

    if artifacts.get("stress_rule"):
        inputs_present["stress_rule"] = True

    if artifacts.get("stress_overlay"):
        inputs_present["stress_overlay"] = True

    if artifacts.get("eligibility"):
        inputs_present["eligibility"] = True

    # Extract stress label
    stress_label, stress_warnings = _extract_stress_label_from_bundle(artifact_bundle)
    warnings.extend(stress_warnings)

    # Extract eligibility label
    eligibility_label, eligibility_warnings = _extract_eligibility_label_from_bundle(artifact_bundle)
    warnings.extend(eligibility_warnings)

    # Check for stress conflict (PR146 vs PR145)
    conflict_warnings = _check_stress_conflict(artifact_bundle)
    warnings.extend(conflict_warnings)

    # Determine action shape from fixed rule table
    action_shape, basis_labels = _determine_action_shape(stress_label, eligibility_label)

    # Create summary
    action_summary = _create_action_summary(action_shape)

    # Create action record
    action_record = V14ActionShapeSchema.create_action_record(
        version=ACTION_VERSION_V1,
        status=ACTION_STATUS_AVAILABLE,
        mode=ACTION_MODE_READ_ONLY,
        action_shape=action_shape,
        scope=ACTION_SCOPE_GLOBAL,  # Default to GLOBAL for v1
        summary=action_summary,
        inputs_present=inputs_present,
        constraints=["LABEL_ONLY", "READ_ONLY"],
        basis=basis_labels,
        artifacts=["pr144_safe_band_guidance", "pr146_stress_rule", "pr145_overlay", "pr128_eligibility"],
        warnings=warnings,
    )

    # Validate schema
    schema_errors = V14ActionShapeSchema.validate_action_record(action_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Add warnings to action record
    action_record["v14_action_warnings"] = warnings

    return {
        "action_record": action_record,
        "warnings": warnings,
    }


def get_action_shape_engine_v1_info() -> Dict[str, Any]:
    """
    Get action shape engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "action_shape_guidance",
        "philosophy": "Action Shape ≠ Instruction. Display shape for user's own decision-making.",
        "input_formats": [
            "Artifact bundle: PR144 safe_band_guidance, PR146 stress_rule, PR145 stress_overlay (optional), PR128 eligibility",
        ],
        "output_format": "action_shape_record (PR147)",
        "rule_table_priority": [
            "1. Invalid → UNKNOWN",
            "2. INELIGIBLE → NO_ACTION",
            "3. STRESSED → FREEZE_STATE",
            "4. TENSE + CONSIDERATION_ONLY → CONSIDER_ONLY, else SIMULATION_ONLY",
            "5. CALM + CONSIDERATION_ONLY → CONSIDER_ONLY, else OBSERVE_ONLY",
            "6. default → UNKNOWN",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "label_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Action Shape Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: CALM + DRY_RUN_ONLY → OBSERVE_ONLY
    print("Test 1: CALM + DRY_RUN_ONLY → OBSERVE_ONLY")
    test_bundle1 = {
        "artifacts": {
            "stress_rule": {
                "v14_stress_label": "CALM",
            },
            "eligibility": {
                "v12_eligibility_label": "ELIGIBLE_DRY_RUN_ONLY",
            },
        }
    }
    result1 = build_action_shape_from_bundle_v1(test_bundle1)
    print(f"Action shape: {result1['action_record']['v14_action_action_shape']}")
    print(f"Warnings: {len(result1['warnings'])}")
    print()

    # Test 2: STRESSED → FREEZE_STATE
    print("Test 2: STRESSED → FREEZE_STATE")
    test_bundle2 = {
        "artifacts": {
            "stress_rule": {
                "v14_stress_label": "STRESSED",
            },
            "eligibility": {
                "v12_eligibility_label": "ELIGIBLE_DRY_RUN_ONLY",
            },
        }
    }
    result2 = build_action_shape_from_bundle_v1(test_bundle2)
    print(f"Action shape: {result2['action_record']['v14_action_action_shape']}")
    print(f"Warnings: {len(result2['warnings'])}")
    print()

    # Test 3: INELIGIBLE → NO_ACTION
    print("Test 3: INELIGIBLE → NO_ACTION")
    test_bundle3 = {
        "artifacts": {
            "stress_rule": {
                "v14_stress_label": "CALM",
            },
            "eligibility": {
                "v12_eligibility_label": "INELIGIBLE",
            },
        }
    }
    result3 = build_action_shape_from_bundle_v1(test_bundle3)
    print(f"Action shape: {result3['action_record']['v14_action_action_shape']}")
    print(f"Warnings: {len(result3['warnings'])}")
    print()

    # Test 4: Invalid bundle (defensive)
    print("Test 4: Invalid bundle (defensive)")
    result4 = build_action_shape_from_bundle_v1(None)
    print(f"Action status: {result4['action_record']['v14_action_status']}")
    print(f"Warnings: {len(result4['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
