#!/usr/bin/env python3
"""
PR23: Confidence Invariants (Warning-only)

Purpose: Validate Confidence column presence/absence invariants from PR21.

Requirements (PR21 Confidence Absence Semantics):
- confidence_value and confidence_reason must both exist or both be absent
- v0.3 logs (no confidence columns) → 0 warnings
- v0.4 logs (confidence columns present but undefined) → 0 warnings
- One-sided presence (only one column exists) → warning
- One-sided content (one column has values, other is always empty) → warning

Non-Goals:
- No Confidence value validation (content is not checked)
- No pipeline failure (warnings only)
- No exit code changes (always returns warnings list)
"""

import csv
from typing import List, Dict, Any


def validate_confidence_columns(csv_path: str) -> List[str]:
    """
    Validate Confidence column invariants from PR21.

    Args:
        csv_path: Path to CSV file

    Returns:
        List of warning messages (empty if no warnings)

    Never raises exceptions - returns warnings list.
    """
    warnings = []

    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)

            # Get header
            if not reader.fieldnames:
                # Empty file
                return warnings

            header = list(reader.fieldnames)

            # Check 1: Column pair consistency
            has_value = 'confidence_value' in header
            has_reason = 'confidence_reason' in header

            # PR21: Both present or both absent
            if has_value and not has_reason:
                warnings.append("confidence_value present but confidence_reason missing (both or neither required)")
            elif has_reason and not has_value:
                warnings.append("confidence_reason present but confidence_value missing (both or neither required)")

            # If one-sided presence detected, stop here (structural issue)
            if len(warnings) > 0:
                return warnings

            # If both absent (v0.3), no warnings
            if not has_value and not has_reason:
                return warnings

            # If both present, check content consistency (sample-based)
            # Read sample rows to detect one-sided content
            rows = []
            for i, row in enumerate(reader):
                rows.append(row)
                if i >= 9:  # Sample first 10 rows
                    break

            if len(rows) == 0:
                # Empty file with header only
                return warnings

            # Check for one-sided content in sample
            value_defined_count = 0
            reason_defined_count = 0

            for row in rows:
                val = row.get('confidence_value', '')
                reas = row.get('confidence_reason', '')

                # Undefined = empty string or missing
                if val and val.strip():
                    value_defined_count += 1
                if reas and reas.strip():
                    reason_defined_count += 1

            # One-sided content: one column always empty, other has values
            if value_defined_count > 0 and reason_defined_count == 0:
                warnings.append(f"confidence_value has values in sample ({value_defined_count}/{len(rows)}) but confidence_reason always empty (inconsistent)")
            elif reason_defined_count > 0 and value_defined_count == 0:
                warnings.append(f"confidence_reason has values in sample ({reason_defined_count}/{len(rows)}) but confidence_value always empty (inconsistent)")

    except FileNotFoundError:
        warnings.append(f"File not found: {csv_path}")
    except Exception as e:
        # Never crash - append exception as warning
        warnings.append(f"Unexpected error reading CSV: {e}")

    return warnings


def format_warnings_report(csv_path: str, warnings: List[str]) -> str:
    """
    Format warnings into human-readable report.

    Args:
        csv_path: Path to CSV file
        warnings: List of warning messages

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("PR23: Confidence Invariants (Warning-only)")
    lines.append("=" * 70)
    lines.append(f"File: {csv_path}")
    lines.append("")

    if len(warnings) == 0:
        lines.append("✓ No warnings (PR21 invariants satisfied)")
    else:
        lines.append(f"⚠ {len(warnings)} warning(s) detected:")
        lines.append("")
        for i, w in enumerate(warnings, 1):
            lines.append(f"  {i}. {w}")

    lines.append("=" * 70)
    return "\n".join(lines)
