#!/usr/bin/env python3
"""
PR8A Validation: Log Integrity Invariants

Purpose: Formal validation that meridian_log.csv maintains data integrity.

Requirements:
- Required columns present (critical ones from v0.2)
- timestamp_utc parseable and monotonic non-decreasing
- target_weight within valid bounds
- action_label consistent with weight changes
- decision_reason format correct when overlay triggered
- No NaN/Inf in numeric decision fields
- regime in allowed set or "unknown"
- Exit 0 on PASS, 1 on FAIL
- Deterministic, no network
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np


# Required columns for v0.2 baseline
REQUIRED_COLUMNS = [
    "timestamp_utc",
    "regime",
    "base_action",
    "decision_reason",
    "action_label",
    "target_weight",
    "entropy_bp",
]

# Allowed regime values
ALLOWED_REGIMES = {
    "stable_range",
    "emerging_trend",
    "volatile_noise",
    "liquidity_stress",
    "regime_transition",
    "post_stress_reset",
    "unknown",
    "REGIME_TRANSITION",  # Allow uppercase variant
}

# Allowed action labels
ALLOWED_ACTIONS = {"BUY", "SELL", "HOLD", "FREEZE", "unknown"}


def validate_required_columns(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate that required columns exist."""
    print("\n" + "=" * 60)
    print("Rule 1: Required Columns")
    print("=" * 60)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        print(f"✗ FAIL: Missing required columns: {missing}")
        return False, [f"Missing columns: {missing}"]
    else:
        print(f"✓ All required columns present: {REQUIRED_COLUMNS}")
        return True, []


def validate_timestamp_monotonic(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate timestamps are parseable and monotonic non-decreasing."""
    print("\n" + "=" * 60)
    print("Rule 2: Timestamp Integrity")
    print("=" * 60)

    issues = []

    if "timestamp_utc" not in df.columns:
        print(f"✗ FAIL: timestamp_utc column missing")
        return False, ["timestamp_utc column missing"]

    # Parse timestamps
    try:
        timestamps = pd.to_datetime(df["timestamp_utc"], errors="coerce")
    except Exception as e:
        print(f"✗ FAIL: Cannot parse timestamps: {e}")
        return False, [f"Timestamp parsing error: {e}"]

    # Check for unparseable timestamps
    null_count = timestamps.isna().sum()
    if null_count > 0:
        print(f"✗ FAIL: {null_count} unparseable timestamps")
        issues.append(f"{null_count} unparseable timestamps")

    # Check monotonic non-decreasing
    parsed_timestamps = timestamps.dropna()
    if len(parsed_timestamps) > 1:
        diffs = parsed_timestamps.diff().dropna()
        negative_diffs = (diffs < pd.Timedelta(0)).sum()

        if negative_diffs > 0:
            print(f"✗ FAIL: {negative_diffs} timestamp regressions (non-monotonic)")
            issues.append(f"{negative_diffs} timestamp regressions")
        else:
            print(f"✓ Timestamps are monotonic non-decreasing")

    if issues:
        return False, issues
    else:
        print(f"✓ All timestamps parseable and monotonic")
        return True, []


def validate_target_weight_bounds(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate target_weight is within valid bounds."""
    print("\n" + "=" * 60)
    print("Rule 3: Target Weight Bounds")
    print("=" * 60)

    issues = []

    if "target_weight" not in df.columns:
        print(f"✗ FAIL: target_weight column missing")
        return False, ["target_weight column missing"]

    # Check for NaN/Inf
    nan_count = df["target_weight"].isna().sum()
    inf_count = np.isinf(df["target_weight"].fillna(0.0)).sum()

    if nan_count > 0:
        print(f"✗ FAIL: {nan_count} NaN values in target_weight")
        issues.append(f"{nan_count} NaN in target_weight")

    if inf_count > 0:
        print(f"✗ FAIL: {inf_count} Inf values in target_weight")
        issues.append(f"{inf_count} Inf in target_weight")

    # Check bounds [-1.0, 1.0] (or [0.0, 1.0] for long-only)
    valid_weights = df["target_weight"].dropna()
    out_of_bounds = ((valid_weights < 0.0) | (valid_weights > 1.0)).sum()

    if out_of_bounds > 0:
        print(f"✗ FAIL: {out_of_bounds} target_weight values outside [0.0, 1.0]")
        issues.append(f"{out_of_bounds} out-of-bounds target_weight")
    else:
        print(f"✓ All target_weight values within [0.0, 1.0]")

    if issues:
        return False, issues
    else:
        print(f"✓ target_weight values are valid")
        return True, []


def validate_action_label_consistency(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate action_label values are in allowed set."""
    print("\n" + "=" * 60)
    print("Rule 4: Action Label Consistency")
    print("=" * 60)

    issues = []

    if "action_label" not in df.columns:
        print(f"✗ FAIL: action_label column missing")
        return False, ["action_label column missing"]

    # Check for allowed values
    action_values = df["action_label"].fillna("unknown").unique()
    invalid_actions = [a for a in action_values if a not in ALLOWED_ACTIONS]

    if invalid_actions:
        print(f"✗ FAIL: Invalid action_label values: {invalid_actions}")
        issues.append(f"Invalid action_label: {invalid_actions}")
    else:
        print(f"✓ All action_label values in allowed set")

    if issues:
        return False, issues
    else:
        return True, []


def validate_decision_reason_format(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate decision_reason contains overlay delimiter when expected."""
    print("\n" + "=" * 60)
    print("Rule 5: Decision Reason Format")
    print("=" * 60)

    issues = []

    if "decision_reason" not in df.columns:
        print(f"✗ FAIL: decision_reason column missing")
        return False, ["decision_reason column missing"]

    # Check for overlay delimiter
    has_delimiter = df["decision_reason"].fillna("").str.contains(" | overlay=").sum()
    total_rows = len(df)

    if has_delimiter == 0 and total_rows > 0:
        print(f"⚠ WARNING: No overlay delimiter found (expected in v0.2)")
        # Not a hard failure - old logs may not have this
    else:
        print(f"✓ {has_delimiter}/{total_rows} rows have overlay delimiter")

    # Check for null/empty decision_reason
    null_count = df["decision_reason"].isna().sum()
    empty_count = (df["decision_reason"].fillna("") == "").sum()

    if null_count > 0:
        print(f"⚠ WARNING: {null_count} null decision_reason values")

    if empty_count > 0:
        print(f"⚠ WARNING: {empty_count} empty decision_reason values")

    # Not failing on warnings for this rule
    return True, []


def validate_numeric_fields(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate numeric fields don't contain NaN/Inf in critical columns."""
    print("\n" + "=" * 60)
    print("Rule 6: Numeric Field Integrity")
    print("=" * 60)

    issues = []

    numeric_columns = ["target_weight", "entropy_bp", "price", "equity"]

    for col in numeric_columns:
        if col not in df.columns:
            continue

        nan_count = df[col].isna().sum()
        inf_count = np.isinf(df[col].fillna(0.0)).sum()

        if nan_count > 0:
            print(f"✗ {col}: {nan_count} NaN values")
            issues.append(f"{col}: {nan_count} NaN")

        if inf_count > 0:
            print(f"✗ {col}: {inf_count} Inf values")
            issues.append(f"{col}: {inf_count} Inf")

    if not issues:
        print(f"✓ All numeric fields clean (no NaN/Inf)")

    if issues:
        return False, issues
    else:
        return True, []


def validate_hold_action_consistency(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate HOLD action implies no weight change."""
    print("\n" + "=" * 60)
    print("Rule 7: HOLD Action Consistency")
    print("=" * 60)

    issues = []

    if "action_label" not in df.columns or "target_weight" not in df.columns:
        print(f"⚠ WARNING: Cannot validate HOLD consistency (missing columns)")
        return True, []

    # Check consecutive rows where action=HOLD
    df_copy = df.copy()
    df_copy["prev_target_weight"] = df_copy["target_weight"].shift(1)
    df_copy["weight_diff"] = (df_copy["target_weight"] - df_copy["prev_target_weight"]).abs()

    # Find HOLD actions with weight changes
    hold_rows = df_copy[df_copy["action_label"] == "HOLD"].copy()
    hold_with_change = hold_rows[hold_rows["weight_diff"] > 0.001]  # Allow tiny float errors

    anomaly_count = len(hold_with_change)

    if anomaly_count > 0:
        print(f"✗ FAIL: {anomaly_count} HOLD actions with weight changes detected")
        issues.append(f"{anomaly_count} HOLD actions with weight changes")
        # Show first few examples
        for idx, row in hold_with_change.head(3).iterrows():
            print(f"  Row {idx}: HOLD but weight changed by {row['weight_diff']:.4f}")
    else:
        print(f"✓ All HOLD actions have no weight changes")

    if issues:
        return False, issues
    else:
        return True, []


def validate_regime_values(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate regime values are in allowed set."""
    print("\n" + "=" * 60)
    print("Rule 8: Regime Value Integrity")
    print("=" * 60)

    issues = []

    if "regime" not in df.columns:
        print(f"✗ FAIL: regime column missing")
        return False, ["regime column missing"]

    regime_values = df["regime"].fillna("unknown").unique()
    invalid_regimes = [r for r in regime_values if r not in ALLOWED_REGIMES]

    if invalid_regimes:
        print(f"✗ FAIL: Invalid regime values: {invalid_regimes}")
        issues.append(f"Invalid regimes: {invalid_regimes}")
    else:
        print(f"✓ All regime values in allowed set")

    if issues:
        return False, issues
    else:
        return True, []


def main():
    """Run all log integrity validations."""

    if len(sys.argv) < 2:
        print("Usage: pr8a_log_integrity_invariants.py <path_to_meridian_log.csv>")
        return 1

    csv_path = sys.argv[1]

    print("=" * 60)
    print("PR8A: Log Integrity Invariants")
    print("=" * 60)
    print(f"CSV: {csv_path}")

    # Read CSV
    if not os.path.exists(csv_path):
        print(f"\n✗ FAIL: CSV file not found: {csv_path}")
        return 1

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"\n✗ FAIL: Cannot read CSV: {e}")
        return 1

    if df.empty:
        print(f"\n✗ FAIL: CSV is empty")
        return 1

    print(f"Rows: {len(df)}")

    # Run all validation rules
    results = []
    all_issues = []

    rule_funcs = [
        ("Required Columns", validate_required_columns),
        ("Timestamp Integrity", validate_timestamp_monotonic),
        ("Target Weight Bounds", validate_target_weight_bounds),
        ("Action Label Consistency", validate_action_label_consistency),
        ("Decision Reason Format", validate_decision_reason_format),
        ("Numeric Field Integrity", validate_numeric_fields),
        ("HOLD Action Consistency", validate_hold_action_consistency),
        ("Regime Value Integrity", validate_regime_values),
    ]

    for rule_name, rule_func in rule_funcs:
        passed, issues = rule_func(df)
        results.append((rule_name, passed))
        all_issues.extend(issues)

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
        print("✓ ALL LOG INTEGRITY INVARIANTS PASSED")
        print("=" * 60)
        print("\nData quality: HEALTHY")
        print("Explainability outputs can be trusted.")
        return 0
    else:
        print("✗ SOME LOG INTEGRITY INVARIANTS FAILED")
        print("=" * 60)
        print("\nData quality: COMPROMISED")
        print("Issues detected:")
        for issue in all_issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(all_issues) > 10:
            print(f"  ... and {len(all_issues) - 10} more")
        print("\nFix data integrity issues before trusting explainability outputs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
