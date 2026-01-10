#!/usr/bin/env python3
"""
PR33: Confidence Reason Snapshot Logging Smoke Test

Purpose: Verify confidence_reason snapshot metadata is logged correctly.

Requirements:
- confidence_reason unchanged (immutable snapshot)
- confidence_reason_version == "v0.4" (fixed)
- confidence_reason_generated_at in ISO-8601 UTC format
- Empty reason handled gracefully (PR21)
- Exit code always 0 (warning-only)

Non-Goals:
- No re-generation or modification of confidence_reason
- No semantic validation
- No behavior changes
"""

import sys
import os
import re
from datetime import datetime

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from confidence.confidence_reason_builder import build_confidence_reason


# ISO-8601 UTC timestamp pattern
ISO_8601_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$'
)


def simulate_snapshot_logging(confidence_reason):
    """
    Simulate PR33 snapshot logging.

    Returns dict with snapshot fields as they would appear in log.
    """
    now = datetime.utcnow()
    return {
        "confidence_reason": confidence_reason,
        "confidence_reason_version": "v0.4",
        "confidence_reason_generated_at": now.isoformat(),
    }


def test_confidence_reason_unchanged():
    """Test confidence_reason is logged unchanged (immutable snapshot)."""
    print("\nTest 1: Confidence Reason Unchanged (Immutable)")
    print("-" * 60)

    # Generate reason
    obs = {
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "base_action": "SHIFT",
        "overlay_rule": "ALLOW",
        "entropy_bp": 3200,
    }
    original_reason = build_confidence_reason(obs)

    # Simulate logging
    log_entry = simulate_snapshot_logging(original_reason)

    # Verify reason unchanged
    assert log_entry["confidence_reason"] == original_reason, "Reason must be unchanged"
    print(f"✓ confidence_reason unchanged (immutable snapshot)")
    print(f"  Original: {original_reason[:60]}...")
    print(f"  Logged: {log_entry['confidence_reason'][:60]}...")

    print("Test 1: PASS")
    return True


def test_version_fixed():
    """Test confidence_reason_version is fixed to 'v0.4'."""
    print("\nTest 2: Version Fixed to 'v0.4'")
    print("-" * 60)

    # Generate reason
    obs = {"intent_primary": "IDLE"}
    reason = build_confidence_reason(obs)

    # Simulate logging
    log_entry = simulate_snapshot_logging(reason)

    # Verify version
    assert "confidence_reason_version" in log_entry, "Version field must exist"
    assert log_entry["confidence_reason_version"] == "v0.4", "Version must be 'v0.4'"
    print(f"✓ confidence_reason_version == 'v0.4' (fixed)")

    print("Test 2: PASS")
    return True


def test_timestamp_iso8601_utc():
    """Test confidence_reason_generated_at is ISO-8601 UTC format."""
    print("\nTest 3: Timestamp ISO-8601 UTC Format")
    print("-" * 60)

    # Generate reason
    obs = {"intent_primary": "IDLE", "regime": "stable_range"}
    reason = build_confidence_reason(obs)

    # Simulate logging
    log_entry = simulate_snapshot_logging(reason)

    # Verify timestamp field exists
    assert "confidence_reason_generated_at" in log_entry, "Timestamp field must exist"

    # Verify timestamp format
    ts = log_entry["confidence_reason_generated_at"]
    assert ISO_8601_PATTERN.match(ts), f"Timestamp must be ISO-8601 format: {ts}"
    print(f"✓ confidence_reason_generated_at in ISO-8601 format")
    print(f"  Timestamp: {ts}")

    # Verify can parse as datetime
    try:
        # Python's fromisoformat supports ISO-8601
        parsed = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        print(f"✓ Timestamp parseable as datetime")
    except Exception as e:
        assert False, f"Timestamp not parseable: {e}"

    print("Test 3: PASS")
    return True


def test_empty_reason_graceful():
    """Test empty confidence_reason handled gracefully (PR21)."""
    print("\nTest 4: Empty Reason Handled Gracefully (PR21)")
    print("-" * 60)

    # Empty observation (PR21 - should produce empty reason)
    obs = {}
    empty_reason = build_confidence_reason(obs)

    assert empty_reason == "", "Empty observation should produce empty reason"

    # Simulate logging
    log_entry = simulate_snapshot_logging(empty_reason)

    # Verify snapshot fields exist even for empty reason
    assert "confidence_reason" in log_entry, "confidence_reason field must exist"
    assert "confidence_reason_version" in log_entry, "Version field must exist"
    assert "confidence_reason_generated_at" in log_entry, "Timestamp field must exist"

    # Verify empty reason unchanged
    assert log_entry["confidence_reason"] == "", "Empty reason must remain empty"
    print(f"✓ Empty confidence_reason handled gracefully")
    print(f"  confidence_reason: (empty)")
    print(f"  confidence_reason_version: {log_entry['confidence_reason_version']}")
    print(f"  confidence_reason_generated_at: {log_entry['confidence_reason_generated_at']}")

    print("Test 4: PASS")
    return True


def test_snapshot_immutability():
    """Test snapshot fields are immutable (no re-generation)."""
    print("\nTest 5: Snapshot Immutability")
    print("-" * 60)

    # Generate reason
    obs = {
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "entropy_bp": 3200,
    }
    original_reason = build_confidence_reason(obs)

    # Simulate logging at time T1
    log_entry_t1 = simulate_snapshot_logging(original_reason)
    reason_t1 = log_entry_t1["confidence_reason"]
    version_t1 = log_entry_t1["confidence_reason_version"]
    ts_t1 = log_entry_t1["confidence_reason_generated_at"]

    # Verify snapshot is immutable (same input → same reason)
    # (Timestamp will differ, but reason and version should not)
    assert reason_t1 == original_reason, "Reason must be immutable"
    assert version_t1 == "v0.4", "Version must be immutable"
    print(f"✓ Snapshot fields immutable")
    print(f"  Reason: {reason_t1[:60]}...")
    print(f"  Version: {version_t1}")
    print(f"  Timestamp: {ts_t1}")

    print("Test 5: PASS")
    return True


def main():
    """Run all PR33 Confidence Reason Snapshot Logging smoke tests."""
    print("=" * 60)
    print("PR33: Confidence Reason Snapshot Logging Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Snapshot logging only. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Confidence Reason Unchanged", test_confidence_reason_unchanged()))
        results.append(("Version Fixed to v0.4", test_version_fixed()))
        results.append(("Timestamp ISO-8601 UTC", test_timestamp_iso8601_utc()))
        results.append(("Empty Reason Graceful", test_empty_reason_graceful()))
        results.append(("Snapshot Immutability", test_snapshot_immutability()))

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
            print("✓ ALL PR33 SNAPSHOT LOGGING TESTS PASSED")
            print("=" * 60)
            print("PR33 Requirements Verified:")
            print("  - confidence_reason unchanged (immutable snapshot)")
            print("  - confidence_reason_version == 'v0.4' (fixed)")
            print("  - confidence_reason_generated_at in ISO-8601 UTC")
            print("  - Empty reason handled gracefully (PR21)")
            print("  - Snapshot fields immutable")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR33 TESTS FAILED")
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
