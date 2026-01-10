# python/confidence/confidence_reason_compliance.py
"""
PR31: Confidence Reason Compliance Guard (READ-ONLY)

Purpose: Validate confidence_reason compliance with PR21/PR27/PR30.

This module provides validation functions to detect violations of:
- PR21: Absence Semantics (empty string is valid)
- PR27: Reason Structure (4-section format)
- PR30: Reason Vocabulary (frozen vocabulary)

Validation is warning-only. Never raises exceptions.
Never affects behavior, control flow, or fail conditions.
"""

import re


# PR30 Vocabulary (Frozen)
STABILITY_VOCABULARY = {
    "temporal indicators present",
    "temporal indicators absent",
}

CONSISTENCY_VOCABULARY = {
    "all core signals present",
    "some core signals present",
    "no core signals present",
}

COMPLETENESS_VOCABULARY = {
    "temporal and current observations",
    "current observations only",
    "no observations",
}


def validate_confidence_reason(reason: str) -> list:
    """
    Validate confidence_reason compliance with PR21/PR27/PR30.

    Args:
        reason: confidence_reason string to validate

    Returns:
        List of warning messages (empty list = compliant)

    Never raises exceptions.

    Checks:
    - PR21: Empty string is valid (no warnings)
    - PR27: Structure compliance (4 sections, correct order)
    - PR30: Vocabulary compliance (frozen vocabulary only)
    - Hard ban: No ASCII digits (0-9)
    """
    warnings = []

    # PR21: Empty string is always valid
    if not reason:
        return []

    # Hard ban: Check for ASCII digits
    if re.search(r'[0-9]', reason):
        warnings.append("Hard ban violation: confidence_reason contains ASCII digit(s)")

    # PR27: Structure validation
    # Expected format: Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>
    if not reason.startswith("Source:"):
        warnings.append("PR27 structure violation: confidence_reason must start with 'Source:'")

    if "; Stability:" not in reason:
        warnings.append("PR27 structure violation: missing '; Stability:' section")

    if "; Consistency:" not in reason:
        warnings.append("PR27 structure violation: missing '; Consistency:' section")

    if "; Completeness:" not in reason:
        warnings.append("PR27 structure violation: missing '; Completeness:' section")

    # Parse sections for vocabulary validation
    try:
        parts = reason.split("; ")
        if len(parts) != 4:
            warnings.append(f"PR27 structure violation: expected 4 sections, found {len(parts)}")
        else:
            # Extract section content
            source_part = parts[0]
            stability_part = parts[1] if len(parts) > 1 else ""
            consistency_part = parts[2] if len(parts) > 2 else ""
            completeness_part = parts[3] if len(parts) > 3 else ""

            # PR30: Stability vocabulary
            if stability_part.startswith("Stability:"):
                stability_content = stability_part[len("Stability:"):]
                if stability_content not in STABILITY_VOCABULARY:
                    warnings.append(f"PR30 vocabulary violation: Stability value '{stability_content}' not in frozen vocabulary")

            # PR30: Consistency vocabulary
            if consistency_part.startswith("Consistency:"):
                consistency_content = consistency_part[len("Consistency:"):]
                if consistency_content not in CONSISTENCY_VOCABULARY:
                    warnings.append(f"PR30 vocabulary violation: Consistency value '{consistency_content}' not in frozen vocabulary")

            # PR30: Completeness vocabulary
            if completeness_part.startswith("Completeness:"):
                completeness_content = completeness_part[len("Completeness:"):]
                if completeness_content not in COMPLETENESS_VOCABULARY:
                    warnings.append(f"PR30 vocabulary violation: Completeness value '{completeness_content}' not in frozen vocabulary")

            # PR30: Source format (should be comma-separated keys, no counts/summaries)
            if source_part.startswith("Source:"):
                source_content = source_part[len("Source:"):]
                # Check for prohibited patterns in Source
                if re.search(r'\d+\s+(field|signal|observation|key)', source_content):
                    warnings.append("PR30 vocabulary violation: Source contains count expression")

    except Exception:
        # Parsing error - structure violation already reported
        pass

    return warnings
