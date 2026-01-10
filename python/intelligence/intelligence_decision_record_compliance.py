#!/usr/bin/env python3
"""
PR39: v0.5 Intelligence Decision Record Compliance Guard

Purpose: Mechanical enforcement of PR38 Decision Record Charter.

Validates:
- Decision Record structure (required fields, types)
- Immutability (no regeneration or rewriting)
- Post-hoc rationalization detection (outcome vocabulary)
- v0.4 Confidence boundary protection (no erosion)

Non-Goals:
- No decision correctness evaluation
- No decision flow modification
- No exceptions raised (warning-only)

Exit code: Always 0 (warning-only)

Dependencies:
- PR34: v0.4 Confidence Release Declaration
- PR35: Intelligence Boundary Charter
- PR36: Intelligence Input Contract Charter
- PR37: Intelligence Input Contract Compliance Guard
- PR38: Intelligence Decision Record Charter
"""

import re
from datetime import datetime
from typing import List, Dict, Any


# PR38: Required Decision Record fields
REQUIRED_FIELDS = [
    "decision_action",
    "decision_reason",
    "decision_inputs",
    "decision_version",
    "decision_generated_at",
]

# PR38: Expected version
EXPECTED_VERSION = "v0.5"

# ISO-8601 UTC timestamp pattern
ISO_8601_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$'
)

# Post-hoc rationalization: Outcome vocabulary (PR38 Ban 2)
OUTCOME_VOCABULARY = [
    "outcome",
    "result",
    "profit",
    "loss",
    "pnl",
    "success",
    "failure",
    "win",
    "lose",
    "correct",
    "incorrect",
    "right",
    "wrong",
]

# v0.4 Confidence erosion: Evaluative patterns (PR35 Ban 6, PR38 Ban 6)
CONFIDENCE_EROSION_PATTERNS = [
    r"confidence.*correct",
    r"confidence.*incorrect",
    r"confidence.*right",
    r"confidence.*wrong",
    r"good.*confidence",
    r"bad.*confidence",
    r"confidence.*quality",
    r"confidence.*accurate",
    r"confidence.*inaccurate",
    r"regenerate.*confidence_reason",
    r"improve.*confidence_reason",
]

# Decision regeneration: Code patterns (PR38 Ban 1)
# Matches both direct assignment and dictionary assignment:
#   decision_reason = regenerate(...)
#   row["decision_reason"] = regenerate(...)
DECISION_REGENERATION_PATTERNS = [
    r'decision_reason.*=.*regenerate',
    r'decision_reason.*=.*improve',
    r'decision_reason.*=.*recompute',
    r'decision_reason.*=.*recalculate',
    r'decision_action.*=.*regenerate',
    r'decision_action.*=.*recompute',
]


def validate_decision_record_structure(
    decision_record: Dict[str, Any]
) -> List[str]:
    """
    PR39: Validate Decision Record structure against PR38 specification.

    Checks:
    - Required fields present
    - Field types correct
    - version == "v0.5"
    - timestamp in ISO-8601 UTC format

    Args:
        decision_record: Dictionary representing Decision Record

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in decision_record:
            warnings.append(
                f"PR38 structure violation: missing required field '{field}'"
            )

    # If critical fields missing, cannot continue validation
    if not all(f in decision_record for f in REQUIRED_FIELDS):
        return warnings

    # Validate field types
    if not isinstance(decision_record.get("decision_action"), str):
        warnings.append(
            f"PR38 type violation: 'decision_action' must be string, "
            f"got {type(decision_record.get('decision_action')).__name__}"
        )

    if not isinstance(decision_record.get("decision_reason"), str):
        warnings.append(
            f"PR38 type violation: 'decision_reason' must be string, "
            f"got {type(decision_record.get('decision_reason')).__name__}"
        )

    if not isinstance(decision_record.get("decision_inputs"), list):
        warnings.append(
            f"PR38 type violation: 'decision_inputs' must be list, "
            f"got {type(decision_record.get('decision_inputs')).__name__}"
        )

    if not isinstance(decision_record.get("decision_version"), str):
        warnings.append(
            f"PR38 type violation: 'decision_version' must be string, "
            f"got {type(decision_record.get('decision_version')).__name__}"
        )

    if not isinstance(decision_record.get("decision_generated_at"), str):
        warnings.append(
            f"PR38 type violation: 'decision_generated_at' must be string, "
            f"got {type(decision_record.get('decision_generated_at')).__name__}"
        )

    # Validate version
    version = decision_record.get("decision_version", "")
    if version != EXPECTED_VERSION:
        warnings.append(
            f"PR38 version violation: expected '{EXPECTED_VERSION}', got '{version}'"
        )

    # Validate timestamp format
    timestamp = decision_record.get("decision_generated_at", "")
    if timestamp and not ISO_8601_PATTERN.match(timestamp):
        warnings.append(
            f"PR38 timestamp violation: not ISO-8601 UTC format: '{timestamp}'"
        )

    # Validate decision_action non-empty
    action = decision_record.get("decision_action", "")
    if isinstance(action, str) and not action:
        warnings.append(
            "PR38 content violation: 'decision_action' cannot be empty"
        )

    # Validate decision_reason non-empty
    reason = decision_record.get("decision_reason", "")
    if isinstance(reason, str) and not reason:
        warnings.append(
            "PR38 content violation: 'decision_reason' cannot be empty"
        )

    return warnings


def detect_decision_regeneration(
    code_text: str, module_name: str = ""
) -> List[str]:
    """
    PR39: Detect decision regeneration patterns in code.

    Detects prohibited patterns:
    - decision_reason = regenerate(...)
    - decision_action = recompute(...)
    - decision_reason = improve(...)

    Args:
        code_text: Source code text to analyze
        module_name: Optional module name for warning context

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []
    module_context = f" in {module_name}" if module_name else ""

    for pattern in DECISION_REGENERATION_PATTERNS:
        if re.search(pattern, code_text, re.IGNORECASE):
            warnings.append(
                f"PR38 Ban 1 violation: decision regeneration pattern detected{module_context} "
                f"(pattern: {pattern})"
            )

    return warnings


def detect_posthoc_rationalization(
    decision_reason: str
) -> List[str]:
    """
    PR39: Detect post-hoc rationalization in decision_reason.

    Detects outcome vocabulary that suggests decision_reason
    was written after observing results.

    Outcome vocabulary (prohibited):
    - outcome, result, profit, loss, pnl
    - success, failure, win, lose
    - correct, incorrect, right, wrong

    Args:
        decision_reason: The decision_reason text to analyze

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []

    if not isinstance(decision_reason, str):
        return warnings

    reason_lower = decision_reason.lower()

    for vocab in OUTCOME_VOCABULARY:
        if vocab in reason_lower:
            warnings.append(
                f"PR38 Ban 2 violation: post-hoc rationalization detected "
                f"(outcome vocabulary '{vocab}' in decision_reason)"
            )

    return warnings


def detect_confidence_erosion(
    decision_text: str, module_name: str = ""
) -> List[str]:
    """
    PR39: Detect v0.4 Confidence boundary erosion.

    Detects prohibited patterns:
    - Evaluating confidence_reason correctness
    - Using evaluative language about confidence
    - Regenerating confidence_reason
    - Treating confidence as decision quality indicator

    Args:
        decision_text: Text to analyze (decision_reason or code)
        module_name: Optional module name for warning context

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []
    module_context = f" in {module_name}" if module_name else ""

    if not isinstance(decision_text, str):
        return warnings

    for pattern in CONFIDENCE_EROSION_PATTERNS:
        if re.search(pattern, decision_text, re.IGNORECASE):
            warnings.append(
                f"PR35/PR38 Ban 6 violation: v0.4 Confidence erosion detected{module_context} "
                f"(pattern: {pattern})"
            )

    return warnings


def validate_decision_record_full(
    decision_record: Dict[str, Any], module_name: str = ""
) -> List[str]:
    """
    PR39: Full Decision Record validation (all checks).

    Combines all compliance checks:
    - Structure validation
    - Post-hoc rationalization detection
    - Confidence erosion detection

    Args:
        decision_record: Decision Record to validate
        module_name: Optional module name for warning context

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []

    # Structure validation
    warnings.extend(validate_decision_record_structure(decision_record))

    # Post-hoc rationalization detection
    if "decision_reason" in decision_record:
        warnings.extend(
            detect_posthoc_rationalization(decision_record["decision_reason"])
        )

    # Confidence erosion detection (in decision_reason)
    if "decision_reason" in decision_record:
        warnings.extend(
            detect_confidence_erosion(
                decision_record["decision_reason"], module_name
            )
        )

    return warnings
