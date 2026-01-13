#!/usr/bin/env python3
"""
PR146: v1.4 Stress Rule Table v1 (READ-ONLY)

Purpose:
    Fixed table mapping (regime, band_bucket, distortion_presence) → stress_label.
    Table-first approach (not if-else inference).

Rule Table Structure:
    Key: (regime_label, band_bucket, distortion_presence)
    Value: (stress_label, basis_labels)

Absolute Rules (Priority):
    1. band_bucket == OUTSIDE → STRESSED (regardless of regime/distortion)
    2. regime == REGIME_CRITICAL → STRESSED (regardless of band/distortion)
    3. UNKNOWN inputs → UNKNOWN (but OUTSIDE/CRITICAL override)

Matrix (excluding OUTSIDE/CRITICAL):
    Regime LOW:
        SAFE + NONE → CALM
        SAFE + PRESENT → TENSE
        EDGE + NONE → TENSE
        EDGE + PRESENT → STRESSED

    Regime MEDIUM:
        SAFE + NONE → TENSE
        SAFE + PRESENT → STRESSED
        EDGE + NONE → STRESSED
        EDGE + PRESENT → STRESSED

    Regime HIGH:
        SAFE + NONE → STRESSED
        SAFE + PRESENT → STRESSED
        EDGE + NONE → STRESSED
        EDGE + PRESENT → STRESSED

    Regime CRITICAL:
        All → STRESSED

UNKNOWN Handling:
    - Distortion UNKNOWN: SAFE/EDGE → UNKNOWN
    - Regime UNKNOWN → UNKNOWN
    - Band UNKNOWN → UNKNOWN
    - OUTSIDE/CRITICAL override to STRESSED
"""

from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stress.v14_stress_rule_table_schema import (
    STRESS_CALM,
    STRESS_TENSE,
    STRESS_STRESSED,
    STRESS_UNKNOWN,
    BAND_SAFE,
    BAND_EDGE,
    BAND_OUTSIDE,
    BAND_UNKNOWN,
    DIST_NONE,
    DIST_PRESENT,
    DIST_UNKNOWN,
    REGIME_LOW,
    REGIME_MEDIUM,
    REGIME_HIGH,
    REGIME_CRITICAL,
    REGIME_UNKNOWN,
)


# Fixed Stress Rule Table v1
# Key: (regime_label, band_bucket, distortion_presence)
# Value: (stress_label, basis_labels)
RULE_TABLE_V1: Dict[Tuple[str, str, str], Tuple[str, List[str]]] = {
    # Regime LOW
    (REGIME_LOW, BAND_SAFE, DIST_NONE): (
        STRESS_CALM,
        ["BASIS_REGIME_LOW", "BASIS_BAND_SAFE", "BASIS_NO_DISTORTION"],
    ),
    (REGIME_LOW, BAND_SAFE, DIST_PRESENT): (
        STRESS_TENSE,
        ["BASIS_REGIME_LOW", "BASIS_BAND_SAFE", "BASIS_DISTORTION_PRESENT"],
    ),
    (REGIME_LOW, BAND_EDGE, DIST_NONE): (
        STRESS_TENSE,
        ["BASIS_REGIME_LOW", "BASIS_BAND_EDGE", "BASIS_NO_DISTORTION"],
    ),
    (REGIME_LOW, BAND_EDGE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_LOW", "BASIS_BAND_EDGE", "BASIS_DISTORTION_PRESENT"],
    ),
    (REGIME_LOW, BAND_SAFE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_LOW", "BASIS_BAND_SAFE", "BASIS_DISTORTION_UNKNOWN"],
    ),
    (REGIME_LOW, BAND_EDGE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_LOW", "BASIS_BAND_EDGE", "BASIS_DISTORTION_UNKNOWN"],
    ),
    # Regime LOW + OUTSIDE (priority override)
    (REGIME_LOW, BAND_OUTSIDE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_LOW, BAND_OUTSIDE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_LOW, BAND_OUTSIDE, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    # Regime LOW + UNKNOWN band
    (REGIME_LOW, BAND_UNKNOWN, DIST_NONE): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_LOW", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_LOW, BAND_UNKNOWN, DIST_PRESENT): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_LOW", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_LOW, BAND_UNKNOWN, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_LOW", "BASIS_BAND_UNKNOWN", "BASIS_DISTORTION_UNKNOWN"],
    ),
    # Regime MEDIUM
    (REGIME_MEDIUM, BAND_SAFE, DIST_NONE): (
        STRESS_TENSE,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_SAFE", "BASIS_NO_DISTORTION"],
    ),
    (REGIME_MEDIUM, BAND_SAFE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_SAFE", "BASIS_DISTORTION_PRESENT"],
    ),
    (REGIME_MEDIUM, BAND_EDGE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_EDGE", "BASIS_NO_DISTORTION"],
    ),
    (REGIME_MEDIUM, BAND_EDGE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_EDGE", "BASIS_DISTORTION_PRESENT"],
    ),
    (REGIME_MEDIUM, BAND_SAFE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_SAFE", "BASIS_DISTORTION_UNKNOWN"],
    ),
    (REGIME_MEDIUM, BAND_EDGE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_EDGE", "BASIS_DISTORTION_UNKNOWN"],
    ),
    # Regime MEDIUM + OUTSIDE (priority override)
    (REGIME_MEDIUM, BAND_OUTSIDE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_MEDIUM, BAND_OUTSIDE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_MEDIUM, BAND_OUTSIDE, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    # Regime MEDIUM + UNKNOWN band
    (REGIME_MEDIUM, BAND_UNKNOWN, DIST_NONE): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_MEDIUM, BAND_UNKNOWN, DIST_PRESENT): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_MEDIUM, BAND_UNKNOWN, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_MEDIUM", "BASIS_BAND_UNKNOWN", "BASIS_DISTORTION_UNKNOWN"],
    ),
    # Regime HIGH
    (REGIME_HIGH, BAND_SAFE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_SAFE", "BASIS_NO_DISTORTION"],
    ),
    (REGIME_HIGH, BAND_SAFE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_SAFE", "BASIS_DISTORTION_PRESENT"],
    ),
    (REGIME_HIGH, BAND_EDGE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_EDGE", "BASIS_NO_DISTORTION"],
    ),
    (REGIME_HIGH, BAND_EDGE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_EDGE", "BASIS_DISTORTION_PRESENT"],
    ),
    (REGIME_HIGH, BAND_SAFE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_SAFE", "BASIS_DISTORTION_UNKNOWN"],
    ),
    (REGIME_HIGH, BAND_EDGE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_EDGE", "BASIS_DISTORTION_UNKNOWN"],
    ),
    # Regime HIGH + OUTSIDE (priority override)
    (REGIME_HIGH, BAND_OUTSIDE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_HIGH, BAND_OUTSIDE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_HIGH, BAND_OUTSIDE, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    # Regime HIGH + UNKNOWN band
    (REGIME_HIGH, BAND_UNKNOWN, DIST_NONE): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_HIGH, BAND_UNKNOWN, DIST_PRESENT): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_HIGH, BAND_UNKNOWN, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_HIGH", "BASIS_BAND_UNKNOWN", "BASIS_DISTORTION_UNKNOWN"],
    ),
    # Regime CRITICAL (always STRESSED)
    (REGIME_CRITICAL, BAND_SAFE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_SAFE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_SAFE, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_EDGE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_EDGE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_EDGE, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_OUTSIDE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY", "BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_OUTSIDE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY", "BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_OUTSIDE, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY", "BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_UNKNOWN, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_UNKNOWN, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    (REGIME_CRITICAL, BAND_UNKNOWN, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_REGIME_CRITICAL_PRIORITY"],
    ),
    # Regime UNKNOWN (always UNKNOWN except OUTSIDE/CRITICAL override)
    (REGIME_UNKNOWN, BAND_SAFE, DIST_NONE): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_SAFE, DIST_PRESENT): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_SAFE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN", "BASIS_DISTORTION_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_EDGE, DIST_NONE): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_EDGE, DIST_PRESENT): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_EDGE, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN", "BASIS_DISTORTION_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_OUTSIDE, DIST_NONE): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_UNKNOWN, BAND_OUTSIDE, DIST_PRESENT): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_UNKNOWN, BAND_OUTSIDE, DIST_UNKNOWN): (
        STRESS_STRESSED,
        ["BASIS_BAND_OUTSIDE_PRIORITY"],
    ),
    (REGIME_UNKNOWN, BAND_UNKNOWN, DIST_NONE): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_UNKNOWN, DIST_PRESENT): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN", "BASIS_BAND_UNKNOWN"],
    ),
    (REGIME_UNKNOWN, BAND_UNKNOWN, DIST_UNKNOWN): (
        STRESS_UNKNOWN,
        ["BASIS_REGIME_UNKNOWN", "BASIS_BAND_UNKNOWN", "BASIS_DISTORTION_UNKNOWN"],
    ),
}


def lookup_stress_label_v1(
    regime_label: str,
    band_bucket: str,
    distortion_presence: str,
) -> Tuple[str, List[str], List[str]]:
    """
    Lookup stress label from fixed table.

    Args:
        regime_label: Regime label
        band_bucket: Band bucket
        distortion_presence: Distortion presence

    Returns:
        Tuple of (stress_label, basis_labels, warnings)
    """
    warnings = []

    # Lookup key
    key = (regime_label, band_bucket, distortion_presence)

    # Try table lookup
    if key in RULE_TABLE_V1:
        stress_label, basis_labels = RULE_TABLE_V1[key]
        return (stress_label, basis_labels, warnings)
    else:
        # Missing key → UNKNOWN with warning
        warnings.append(f"missing table entry for key: {key}, using UNKNOWN")
        return (
            STRESS_UNKNOWN,
            ["BASIS_TABLE_LOOKUP_FAILED"],
            warnings,
        )


def get_stress_rule_table_v1_info() -> Dict[str, any]:
    """
    Get stress rule table v1 information.

    Returns:
        Dict with table metadata
    """
    return {
        "table_version": "v1",
        "table_type": "stress_rule_table",
        "table_size": len(RULE_TABLE_V1),
        "philosophy": "Fixed table mapping (regime × band × distortion) → stress. Table-first approach.",
        "priority_rules": [
            "band_bucket == OUTSIDE → STRESSED (always)",
            "regime == REGIME_CRITICAL → STRESSED (always)",
            "UNKNOWN inputs → UNKNOWN (unless OUTSIDE/CRITICAL override)",
        ],
        "matrix_summary": {
            "REGIME_LOW": "SAFE+NONE→CALM, SAFE+PRESENT→TENSE, EDGE+NONE→TENSE, EDGE+PRESENT→STRESSED",
            "REGIME_MEDIUM": "SAFE+NONE→TENSE, SAFE+PRESENT→STRESSED, EDGE+NONE→STRESSED, EDGE+PRESENT→STRESSED",
            "REGIME_HIGH": "SAFE+NONE→STRESSED, SAFE+PRESENT→STRESSED, EDGE+NONE→STRESSED, EDGE+PRESENT→STRESSED",
            "REGIME_CRITICAL": "ALL→STRESSED",
        },
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Stress Rule Table - Self Test")
    print("=" * 60)
    print()

    # Test 1: Table info
    print("Test 1: Table info")
    info = get_stress_rule_table_v1_info()
    print(f"Table size: {info['table_size']} entries")
    print(f"Philosophy: {info['philosophy']}")
    print()

    # Test 2: CALM lookup (LOW + SAFE + NONE)
    print("Test 2: CALM lookup (LOW + SAFE + NONE)")
    label, basis, warnings = lookup_stress_label_v1(REGIME_LOW, BAND_SAFE, DIST_NONE)
    print(f"Label: {label}, Basis: {basis}, Warnings: {len(warnings)}")
    print()

    # Test 3: STRESSED lookup (CRITICAL + any)
    print("Test 3: STRESSED lookup (CRITICAL + SAFE + NONE)")
    label, basis, warnings = lookup_stress_label_v1(REGIME_CRITICAL, BAND_SAFE, DIST_NONE)
    print(f"Label: {label}, Basis: {basis}, Warnings: {len(warnings)}")
    print()

    # Test 4: STRESSED lookup (OUTSIDE priority)
    print("Test 4: STRESSED lookup (LOW + OUTSIDE + NONE)")
    label, basis, warnings = lookup_stress_label_v1(REGIME_LOW, BAND_OUTSIDE, DIST_NONE)
    print(f"Label: {label}, Basis: {basis}, Warnings: {len(warnings)}")
    print()

    # Test 5: Missing key → UNKNOWN
    print("Test 5: Missing key → UNKNOWN")
    label, basis, warnings = lookup_stress_label_v1("INVALID_REGIME", BAND_SAFE, DIST_NONE)
    print(f"Label: {label}, Basis: {basis}, Warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
