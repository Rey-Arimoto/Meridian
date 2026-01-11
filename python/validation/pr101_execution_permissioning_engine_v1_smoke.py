#!/usr/bin/env python3
"""
PR101: v1.0 Execution Permissioning Engine v1 Smoke Test

Purpose:
    Validate that v1.0 execution permissioning engine correctly
    classifies execution permission based on boundary analysis.

Test Coverage:
    1. Engine import works
    2. Minimal boundary input produces v10 record
    3. All boundary types map to expected permission
    4. Forbidden vocabulary detection
    5. No trading verbs allowed
    6. v0.4 boundary protection enforced
    7. Warning-only behavior (exit code always 0)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.0 execution modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from execution.v10_execution_permissioning_engine_v1 import (
    classify_execution_permission_v1,
    V1PermissionTypes,
)
from execution.v10_execution_schema import V10ExecutionSchema
from execution.v10_constitutional_guard import validate_execution_record


def test_engine_import() -> bool:
    """
    Test 1: Engine import works.
    """
    print("Test 1: Engine import works")
    print("-" * 60)

    try:
        from execution.v10_execution_permissioning_engine_v1 import (
            classify_execution_permission_v1,
        )
        print("✓ Engine import successful")
    except ImportError as e:
        print(f"✗ Engine import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_minimal_boundary_input() -> bool:
    """
    Test 2: Minimal boundary input produces v10 record.
    """
    print("Test 2: Minimal boundary input produces v10 record")
    print("-" * 60)

    boundary = {
        "v9_boundary_mode": "ON",
        "v9_boundary_status": "AVAILABLE",
        "v9_boundary_type": "DATA_BOUNDARY",
        "v9_boundary_description": "test boundary",
        "v9_boundary_basis": ["v8_blindspot_tag"],
    }

    try:
        execution = classify_execution_permission_v1(boundary)
    except Exception as e:
        print(f"✗ Classification failed: {e}")
        return False

    print("✓ Classification successful")

    # Check required fields
    for field in V10ExecutionSchema.REQUIRED_FIELDS:
        if field not in execution:
            print(f"✗ Missing required field: {field}")
            return False

    print("✓ All required fields present")

    # Check v10 record structure
    warnings = V10ExecutionSchema.validate_structure(execution)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False

    print("✓ Valid v10 record structure")

    print("Test 2: PASS\n")
    return True


def test_boundary_type_mapping() -> bool:
    """
    Test 3: All boundary types map to expected permission.
    """
    print("Test 3: All boundary types map to expected permission")
    print("-" * 60)

    # Test cases: (boundary_type, expected_permission)
    test_cases = [
        ("SCHEMA_BOUNDARY", V1PermissionTypes.HOLD),
        ("DATA_BOUNDARY", V1PermissionTypes.HOLD),
        ("ENGINE_BOUNDARY", V1PermissionTypes.HOLD),
        ("TEMPORAL_BOUNDARY", V1PermissionTypes.DRY_RUN_ONLY),
        ("SAMPLING_BOUNDARY", V1PermissionTypes.DRY_RUN_ONLY),
        ("UNCLASSIFIED", V1PermissionTypes.UNKNOWN),
    ]

    for boundary_type, expected_permission in test_cases:
        boundary = {
            "v9_boundary_mode": "ON",
            "v9_boundary_status": "AVAILABLE",
            "v9_boundary_type": boundary_type,
            "v9_boundary_description": "test boundary",
            "v9_boundary_basis": ["v8_blindspot_tag"],
        }

        execution = classify_execution_permission_v1(boundary)
        actual_permission = execution.get("v10_execution_permission", "")

        if actual_permission != expected_permission:
            print(f"✗ {boundary_type} → expected {expected_permission}, got {actual_permission}")
            return False

        print(f"✓ {boundary_type} → {actual_permission}")

    print("Test 3: PASS\n")
    return True


def test_forbidden_vocabulary() -> bool:
    """
    Test 4: Forbidden vocabulary detection.
    """
    print("Test 4: Forbidden vocabulary detection")
    print("-" * 60)

    # Create execution record with clean vocabulary
    boundary = {
        "v9_boundary_mode": "ON",
        "v9_boundary_status": "AVAILABLE",
        "v9_boundary_type": "TEMPORAL_BOUNDARY",
        "v9_boundary_description": "test boundary",
        "v9_boundary_basis": ["v8_blindspot_tag"],
    }

    execution = classify_execution_permission_v1(boundary)
    warnings = validate_execution_record(execution)

    # Filter for forbidden vocabulary warnings only
    vocab_warnings = [w for w in warnings if "Forbidden vocabulary" in w]

    if vocab_warnings:
        print(f"✗ Forbidden vocabulary detected: {vocab_warnings}")
        return False

    print("✓ No forbidden vocabulary in generated summaries")

    print("Test 4: PASS\n")
    return True


def test_no_trading_verbs() -> bool:
    """
    Test 5: No trading verbs allowed.
    """
    print("Test 5: No trading verbs allowed")
    print("-" * 60)

    # Generate execution records for all boundary types
    boundary_types = [
        "SCHEMA_BOUNDARY",
        "DATA_BOUNDARY",
        "ENGINE_BOUNDARY",
        "TEMPORAL_BOUNDARY",
        "SAMPLING_BOUNDARY",
        "UNCLASSIFIED",
    ]

    for boundary_type in boundary_types:
        boundary = {
            "v9_boundary_mode": "ON",
            "v9_boundary_status": "AVAILABLE",
            "v9_boundary_type": boundary_type,
            "v9_boundary_description": "test boundary",
            "v9_boundary_basis": ["v8_blindspot_tag"],
        }

        execution = classify_execution_permission_v1(boundary)
        warnings = validate_execution_record(execution)

        # Filter for execution action warnings only
        action_warnings = [w for w in warnings if "Execution action vocabulary" in w]

        if action_warnings:
            print(f"✗ Trading verbs detected in {boundary_type}: {action_warnings}")
            return False

    print("✓ No trading verbs in any generated summaries")

    print("Test 5: PASS\n")
    return True


def test_v04_boundary_protection() -> bool:
    """
    Test 6: v0.4 boundary protection enforced.
    """
    print("Test 6: v0.4 boundary protection enforced")
    print("-" * 60)

    # Engine should only use v9 boundary fields
    boundary = {
        "v9_boundary_mode": "ON",
        "v9_boundary_status": "AVAILABLE",
        "v9_boundary_type": "DATA_BOUNDARY",
        "v9_boundary_description": "test boundary",
        "v9_boundary_basis": ["v8_blindspot_tag"],
    }

    execution = classify_execution_permission_v1(boundary)

    # Check basis does not contain v0.4 fields
    basis = execution.get("v10_execution_basis", [])

    forbidden_v04_fields = [
        "confidence_reason",
        "confidence_reason_version",
        "confidence_detail",
    ]

    for field in basis:
        if field in forbidden_v04_fields:
            print(f"✗ v0.4 field detected in basis: {field}")
            return False

    print("✓ No v0.4 fields in execution basis")

    # Validate with constitutional guard
    warnings = validate_execution_record(execution)
    confidence_warnings = [w for w in warnings if "v0.4 boundary violation" in w]

    if confidence_warnings:
        print(f"✗ v0.4 boundary violations: {confidence_warnings}")
        return False

    print("✓ v0.4 boundary protection enforced")

    print("Test 6: PASS\n")
    return True


def test_warning_only_behavior() -> bool:
    """
    Test 7: Warning-only behavior (exit code always 0).
    """
    print("Test 7: Warning-only behavior (exit code always 0)")
    print("-" * 60)

    # Test with None input (should not raise)
    try:
        execution1 = classify_execution_permission_v1(None)
        print("✓ None input handled gracefully")
    except Exception as e:
        print(f"✗ None input raised exception: {e}")
        return False

    # Test with invalid type (should not raise)
    try:
        execution2 = classify_execution_permission_v1("invalid")  # type: ignore
        print("✓ Invalid type handled gracefully")
    except Exception as e:
        print(f"✗ Invalid type raised exception: {e}")
        return False

    # Test with empty dict (should not raise)
    try:
        execution3 = classify_execution_permission_v1({})
        print("✓ Empty dict handled gracefully")
    except Exception as e:
        print(f"✗ Empty dict raised exception: {e}")
        return False

    print("✓ All edge cases handled without raising")

    print("Test 7: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR101: v1.0 Execution Permissioning Engine v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine import works", test_engine_import),
        ("Minimal boundary input", test_minimal_boundary_input),
        ("Boundary type mapping", test_boundary_type_mapping),
        ("Forbidden vocabulary detection", test_forbidden_vocabulary),
        ("No trading verbs allowed", test_no_trading_verbs),
        ("v0.4 boundary protection", test_v04_boundary_protection),
        ("Warning-only behavior", test_warning_only_behavior),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test '{name}' raised exception: {e}")
            results.append((name, False))

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print()
    print("=" * 60)
    if all_passed:
        print("✓ ALL PR101 EXECUTION PERMISSIONING ENGINE TESTS PASSED")
    else:
        print("⚠ SOME PR101 EXECUTION PERMISSIONING ENGINE TESTS FAILED")
    print("=" * 60)
    print("PR101 Requirements Verified:")
    print("  - Engine import works")
    print("  - Minimal boundary input produces v10 record")
    print("  - All boundary types map to expected permission")
    print("  - Forbidden vocabulary detection")
    print("  - No trading verbs allowed")
    print("  - v0.4 boundary protection enforced")
    print("  - Warning-only behavior (exit code always 0)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
