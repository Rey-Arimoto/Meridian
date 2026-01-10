#!/usr/bin/env python3
"""
PR16A: Intent Integrity Check (Warning-only)

Purpose: Check logical consistency of Intent columns without blocking pipeline.

This is NOT a safety gate. This is an interpretation health layer.

Checks:
1. intent_primary value validity (SEEK/HARVEST/DEFEND/STABILIZE/PAUSE/IDLE/N/A only)
2. intent_reason type check (must be str or empty)
3. Intent × Action/Regime weak consistency (heuristic warnings)

Important:
- WARNING-ONLY: Never fails, never blocks pipeline
- Never crashes on missing columns
- Works with both v0.2 (no Intent) and v0.3 (with Intent) logs
- Deterministic, no network, no randomness
- Never modifies data
"""

import pandas as pd
from typing import List, Dict, Any


# Valid Intent values (canonical)
VALID_INTENTS = {"SEEK", "HARVEST", "DEFEND", "STABILIZE", "PAUSE", "IDLE", "N/A"}


def check_intent_integrity(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Check Intent integrity and return warnings (never fails).

    Args:
        df: DataFrame with log data (may or may not have Intent columns)

    Returns:
        List of warning dicts, each containing:
        - type: warning type (str)
        - count: number of rows affected (int)
        - details: additional info (str, optional)

    Notes:
    - Returns empty list if no warnings
    - Never raises exceptions (fail-safe)
    - Skips checks if Intent columns don't exist
    """
    warnings = []

    try:
        # Check 1: intent_primary value validity
        if "intent_primary" in df.columns:
            intent_col = df["intent_primary"].fillna("N/A").astype(str).str.strip()
            invalid_intents = intent_col[~intent_col.isin(VALID_INTENTS)]

            if len(invalid_intents) > 0:
                # Count occurrences of each invalid value
                invalid_counts = invalid_intents.value_counts()
                for value, count in invalid_counts.items():
                    warnings.append({
                        "type": "invalid_intent_primary",
                        "count": int(count),
                        "details": f'Invalid value: "{value}"'
                    })

        # Check 2: intent_reason type check
        if "intent_reason" in df.columns:
            reason_col = df["intent_reason"]
            non_string_count = 0

            for idx, val in reason_col.items():
                if pd.notna(val) and not isinstance(val, str):
                    non_string_count += 1

            if non_string_count > 0:
                warnings.append({
                    "type": "invalid_intent_reason_type",
                    "count": non_string_count,
                    "details": "intent_reason must be str or NaN"
                })

        # Check 3: Intent × Action/Regime weak consistency (heuristic)
        if "intent_primary" in df.columns:
            intent_col = df["intent_primary"].fillna("").astype(str).str.strip()

            # Check 3a: PAUSE intent without PAUSE indicators
            if "base_action" in df.columns and "decision_reason" in df.columns:
                pause_intent_mask = (intent_col == "PAUSE")
                if pause_intent_mask.any():
                    base_action = df["base_action"].fillna("").astype(str).str.strip().str.lower()
                    decision_reason = df["decision_reason"].fillna("").astype(str).str.strip().str.lower()

                    # PAUSE intent but base_action != "pause" AND decision_reason doesn't contain pause/freeze
                    suspicious_pause = (
                        pause_intent_mask &
                        (base_action != "pause") &
                        ~decision_reason.str.contains("pause", case=False, na=False) &
                        ~decision_reason.str.contains("emergency_freeze", case=False, na=False)
                    )

                    suspicious_count = suspicious_pause.sum()
                    if suspicious_count > 0:
                        warnings.append({
                            "type": "pause_intent_weak_inconsistency",
                            "count": int(suspicious_count),
                            "details": "PAUSE intent without PAUSE action/reason"
                        })

            # Check 3b: STABILIZE intent without TRANSITION regime
            if "regime" in df.columns:
                stabilize_intent_mask = (intent_col == "STABILIZE")
                if stabilize_intent_mask.any():
                    regime = df["regime"].fillna("").astype(str).str.strip().str.lower()

                    # STABILIZE intent but regime doesn't contain "transition"
                    suspicious_stabilize = (
                        stabilize_intent_mask &
                        ~regime.str.contains("transition", case=False, na=False)
                    )

                    suspicious_count = suspicious_stabilize.sum()
                    if suspicious_count > 0:
                        warnings.append({
                            "type": "stabilize_intent_weak_inconsistency",
                            "count": int(suspicious_count),
                            "details": "STABILIZE intent without TRANSITION regime"
                        })

    except Exception as e:
        # Fail-safe: If any check crashes, report it as a warning but don't fail
        warnings.append({
            "type": "integrity_check_error",
            "count": 0,
            "details": f"Integrity check encountered error: {str(e)[:100]}"
        })

    return warnings


def format_warnings_text(warnings: List[Dict[str, Any]]) -> str:
    """
    Format warnings as plain text report.

    Args:
        warnings: List of warning dicts from check_intent_integrity()

    Returns:
        Formatted text string
    """
    if not warnings:
        return "No Intent integrity warnings detected."

    lines = []
    lines.append(f"Total intent warnings: {sum(w['count'] for w in warnings)}")
    lines.append("")

    for warning in warnings:
        count = warning["count"]
        details = warning.get("details", warning["type"])
        lines.append(f"- {details} ({count} row{'s' if count != 1 else ''})")

    lines.append("")
    lines.append("Note:")
    lines.append("These are warnings only. Pipeline execution is not blocked.")

    return "\n".join(lines)


def format_warnings_markdown(warnings: List[Dict[str, Any]]) -> str:
    """
    Format warnings as markdown report.

    Args:
        warnings: List of warning dicts from check_intent_integrity()

    Returns:
        Formatted markdown string
    """
    if not warnings:
        return "**No Intent integrity warnings detected.**"

    lines = []
    lines.append(f"**Total intent warnings:** {sum(w['count'] for w in warnings)}")
    lines.append("")

    for warning in warnings:
        count = warning["count"]
        details = warning.get("details", warning["type"])
        lines.append(f"- {details} ({count} row{'s' if count != 1 else ''})")

    lines.append("")
    lines.append("*Note: These are warnings only. Pipeline execution is not blocked.*")

    return "\n".join(lines)


def main():
    """
    Standalone CLI for Intent integrity check.

    Usage: python3 pr16a_intent_integrity_check.py <csv_path>

    Exit codes:
    - 0: Always (warning-only, never fails)
    """
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python3 pr16a_intent_integrity_check.py <csv_path>")
        return 0

    csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return 0  # Warning-only, don't fail

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return 0  # Warning-only, don't fail

    print("=" * 70)
    print("PR16A: Intent Integrity Check (Warning-only)")
    print("=" * 70)
    print(f"CSV: {csv_path}")
    print(f"Rows: {len(df)}")
    print("")

    # Check Intent columns existence
    has_intent = "intent_primary" in df.columns
    has_reason = "intent_reason" in df.columns

    if has_intent:
        print(f"✓ intent_primary column found")
    else:
        print(f"ℹ intent_primary column not found (v0.2 log or pre-PR15A)")

    if has_reason:
        print(f"✓ intent_reason column found")
    else:
        print(f"ℹ intent_reason column not found (v0.2 log or pre-PR15A)")

    print("")

    # Run integrity check
    warnings = check_intent_integrity(df)

    print("-" * 70)
    print("Intent Integrity (Warning)")
    print("-" * 70)
    print(format_warnings_text(warnings))
    print("")

    print("=" * 70)
    print("Check complete. Exit code: 0 (warning-only, never fails)")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
