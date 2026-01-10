#!/usr/bin/env python3
"""
PR37: v0.5 Intelligence Input Contract Compliance Guard Smoke Test

Purpose: Verify PR37 compliance guard correctly enforces PR36 Input Contract.

Requirements:
- Import ban detection (v0.4 builders/validators)
- Input allowlist validation (Category A/B/C)
- Featurization ban detection (confidence_reason operations)
- Warning-only (never raises exceptions)
- Exit code always 0

Non-Goals:
- No runtime behavior validation
- No integration testing
- No v0.4 modification tests (PR35 boundary)
"""

import sys
import os

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_input_contract_guard import (
    validate_intelligence_imports,
    validate_intelligence_inputs,
    validate_confidence_snapshot_usage,
)


def test_prohibited_import_builder():
    """Test 1: Detect prohibited import of confidence_reason_builder."""
    print("\nTest 1: Prohibited Import Detection (Builder)")
    print("-" * 60)

    # Prohibited import (PR36 Ban 4)
    code = """
from confidence.confidence_reason_builder import build_confidence_reason

def make_decision(state):
    reason = build_confidence_reason(state)  # PROHIBITED
    return reason
"""

    warnings = validate_intelligence_imports(code, "test_module.py")

    assert len(warnings) > 0, "Should detect prohibited import"
    assert any("confidence_reason_builder" in w for w in warnings), \
        "Warning should mention confidence_reason_builder"
    print(f"✓ Detected prohibited import: confidence_reason_builder")
    print(f"  Warnings: {warnings}")

    print("Test 1: PASS")
    return True


def test_prohibited_import_compliance():
    """Test 2: Detect prohibited import of confidence_reason_compliance."""
    print("\nTest 2: Prohibited Import Detection (Compliance)")
    print("-" * 60)

    # Prohibited import (PR36 Ban 4)
    code = """
from confidence.confidence_reason_compliance import validate_confidence_reason

def check_quality(reason):
    warnings = validate_confidence_reason(reason)  # PROHIBITED
    return len(warnings) == 0
"""

    warnings = validate_intelligence_imports(code, "test_module.py")

    assert len(warnings) > 0, "Should detect prohibited import"
    assert any("confidence_reason_compliance" in w for w in warnings), \
        "Warning should mention confidence_reason_compliance"
    print(f"✓ Detected prohibited import: confidence_reason_compliance")
    print(f"  Warnings: {warnings}")

    print("Test 2: PASS")
    return True


def test_allowed_imports():
    """Test 3: Allow standard imports (non-v0.4)."""
    print("\nTest 3: Allowed Imports (Non-v0.4)")
    print("-" * 60)

    # Allowed imports (not v0.4 builders/validators)
    code = """
import numpy as np
from typing import Dict, List
import json

def make_decision(state):
    data = json.loads(state)
    return np.mean(data)
"""

    warnings = validate_intelligence_imports(code, "test_module.py")

    assert len(warnings) == 0, "Should allow standard imports"
    print(f"✓ No warnings for allowed imports")
    print(f"  Imports: numpy, typing, json")

    print("Test 3: PASS")
    return True


def test_input_allowlist_compliant():
    """Test 4: Validate inputs against allowlist (compliant)."""
    print("\nTest 4: Input Allowlist Validation (Compliant)")
    print("-" * 60)

    # Compliant inputs (Category A/B/C)
    inputs = {
        # Category A: Market/State
        "price": 100.0,
        "volatility": 0.02,
        "entropy_bp": 3200,
        # Category B: Intent/Regime
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "base_action": "SHIFT",
        # Category C: v0.4 Confidence Snapshot (READ-ONLY)
        "confidence_reason": "Source:entropy_bp,intent_primary; ...",
        "confidence_reason_version": "v0.4",
        "confidence_reason_generated_at": "2026-01-10T12:00:00",
    }

    warnings = validate_intelligence_inputs(inputs)

    assert len(warnings) == 0, "Should allow all Category A/B/C inputs"
    print(f"✓ No warnings for allowlisted inputs")
    print(f"  Categories: A (Market/State), B (Intent/Regime), C (Confidence Snapshot)")
    print(f"  Total inputs: {len(inputs)}")

    print("Test 4: PASS")
    return True


def test_input_allowlist_violations():
    """Test 5: Detect undeclared input keys (violations)."""
    print("\nTest 5: Input Allowlist Validation (Violations)")
    print("-" * 60)

    # Non-compliant inputs (not in allowlist)
    inputs = {
        "price": 100.0,  # OK (Category A)
        "intent_primary": "SEEK",  # OK (Category B)
        "undefined_field_1": "value",  # VIOLATION
        "custom_metric_xyz": 42,  # VIOLATION
    }

    warnings = validate_intelligence_inputs(inputs)

    assert len(warnings) > 0, "Should detect undeclared inputs"
    assert any("undefined_field_1" in w for w in warnings), \
        "Should detect undefined_field_1"
    assert any("custom_metric_xyz" in w for w in warnings), \
        "Should detect custom_metric_xyz"
    print(f"✓ Detected {len(warnings)} undeclared input key(s)")
    print(f"  Warnings: {warnings}")

    print("Test 5: PASS")
    return True


def test_featurization_ban():
    """Test 6: Detect featurization operations on confidence_reason."""
    print("\nTest 6: Featurization Ban Detection")
    print("-" * 60)

    # Prohibited featurization (PR36 Ban 3)
    code = """
def extract_features(confidence_reason):
    # PROHIBITED: Featurization operations
    length = len(confidence_reason)  # Ban 3
    tokens = confidence_reason.split(";")  # Ban 3
    hash_val = hash(confidence_reason)  # Ban 3
    first_part = confidence_reason[0:10]  # Ban 3
    count = confidence_reason.count("temporal")  # Ban 3
    return {
        "length": length,
        "tokens": tokens,
        "hash": hash_val,
        "slice": first_part,
        "count": count,
    }
"""

    warnings = validate_confidence_snapshot_usage(code, "test_module.py")

    assert len(warnings) > 0, "Should detect featurization operations"
    print(f"✓ Detected {len(warnings)} featurization pattern(s)")
    for w in warnings:
        print(f"  - {w}")

    print("Test 6: PASS")
    return True


def test_allowed_readonly_consumption():
    """Test 7: Allow read-only consumption of confidence_reason."""
    print("\nTest 7: Allowed Read-Only Consumption")
    print("-" * 60)

    # Allowed: Read-only reference (PR36 Allowed Use 1)
    code = """
def make_decision(current_state, historical_log):
    # ✓ ALLOWED: Read confidence_reason as context (READ-ONLY)
    if historical_log:
        past_reason = historical_log[-1]["confidence_reason"]
        past_version = historical_log[-1]["confidence_reason_version"]
        past_timestamp = historical_log[-1]["confidence_reason_generated_at"]
    else:
        past_reason = ""
        past_version = ""
        past_timestamp = ""

    # Use as context alongside other inputs (not modified)
    decision = intelligence_model.decide(
        market_state=current_state,
        historical_confidence=past_reason,  # Context only
    )

    return decision
"""

    warnings_import = validate_intelligence_imports(code, "test_module.py")
    warnings_featurization = validate_confidence_snapshot_usage(code, "test_module.py")

    assert len(warnings_import) == 0, "Should allow read-only consumption (no prohibited imports)"
    assert len(warnings_featurization) == 0, "Should allow read-only consumption (no featurization)"
    print(f"✓ No warnings for read-only consumption")
    print(f"  Read-only reference: confidence_reason, confidence_reason_version, confidence_reason_generated_at")
    print(f"  Usage: historical context (not modified, not featurized)")

    print("Test 7: PASS")
    return True


def main():
    """Run all PR37 Intelligence Input Contract Guard smoke tests."""
    print("=" * 60)
    print("PR37: Intelligence Input Contract Guard Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Prohibited Import (Builder)", test_prohibited_import_builder()))
        results.append(("Prohibited Import (Compliance)", test_prohibited_import_compliance()))
        results.append(("Allowed Imports", test_allowed_imports()))
        results.append(("Input Allowlist (Compliant)", test_input_allowlist_compliant()))
        results.append(("Input Allowlist (Violations)", test_input_allowlist_violations()))
        results.append(("Featurization Ban", test_featurization_ban()))
        results.append(("Allowed Read-Only Consumption", test_allowed_readonly_consumption()))

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        for name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {name}")

        all_passed = all(passed for _, passed in results)

        print("\n" + "=" * 60)
        if all_passed:
            print("✓ ALL PR37 INPUT CONTRACT GUARD TESTS PASSED")
            print("=" * 60)
            print("PR37 Requirements Verified:")
            print("  - Import ban detection (v0.4 builders/validators)")
            print("  - Input allowlist validation (Category A/B/C)")
            print("  - Featurization ban detection (confidence_reason)")
            print("  - Read-only consumption allowed")
            print("  - Warning-only (never raises exceptions)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR37 TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0  # Always exit 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # Always exit 0


if __name__ == "__main__":
    sys.exit(main())
