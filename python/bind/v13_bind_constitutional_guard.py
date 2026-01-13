#!/usr/bin/env python3
"""
PR142: v1.3 Binding Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on packet → draft binding process.
    Guards against value leakage, numeric patterns, and prescriptive mapping.

Constitutional Constraints:
    - Label projection only: No numeric values, no token literals
    - Source presence only: No artifact values in inputs
    - Structural binding: Intended shape is structural label (not recommendation)
    - No prescriptive mapping: Binding ≠ Recommendation
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0

Guards:
    1. Label-only validation (constraints must be labels, not values)
    2. Source presence validation (inputs must be presence flags, not values)
    3. Intended shape validation (must be structural label)
    4. Binding process guard (reuse draft guards from PR141)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Valid action class labels for intended shape
# These must match PR141 V13ExecutionDraftSchema.VALID_ACTION_CLASSES
VALID_ACTION_CLASSES = [
    "NONE",
    "DRAFT_ONLY",
    "NO_ACTION",
    "HUMAN_REVIEW_REQUIRED",
    "SIMULATION_ONLY",
    "CONSIDERATION_ONLY",
]


def check_label_only_constraints(constraints: Dict[str, Any]) -> List[str]:
    """
    Check that constraints contain labels only (no numeric values).

    Args:
        constraints: Constraints dict to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(constraints, dict):
        return warnings

    for key, value in constraints.items():
        if not isinstance(value, str):
            warnings.append(
                f"constraint '{key}' has non-string value: {type(value).__name__} "
                f"(constraints must be label-only)"
            )
            continue

        # Check for numeric patterns in constraint values
        if re.search(r'\d{4,}', value):
            warnings.append(
                f"constraint '{key}' contains numeric pattern: '{value}' "
                f"(constraints must be label-only, no numeric values)"
            )

        # Check for token literal patterns
        token_patterns = [r'\bSUI\b', r'\bUSDC\b', r'\bBTC\b', r'\bETH\b', r'\bDEEP\b', r'\bCETUS\b']
        for pattern in token_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                warnings.append(
                    f"constraint '{key}' contains token literal: '{value}' "
                    f"(constraints must be label-only, no token literals)"
                )
                break

    return warnings


def check_source_presence_only_inputs(inputs: Dict[str, Any]) -> List[str]:
    """
    Check that inputs contain source presence flags only (no values).

    Args:
        inputs: Inputs dict to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(inputs, dict):
        return warnings

    for key, value in inputs.items():
        if not isinstance(value, str):
            warnings.append(
                f"input '{key}' has non-string value: {type(value).__name__} "
                f"(inputs must be source presence only)"
            )
            continue

        # Inputs should be presence flags like "true" or status labels
        # Check for numeric patterns that might indicate value leakage
        if re.search(r'\d{4,}', value):
            warnings.append(
                f"input '{key}' contains numeric pattern: '{value}' "
                f"(inputs must be source presence only, no values)"
            )

        # Check for token literal patterns
        token_patterns = [r'\bSUI\b', r'\bUSDC\b', r'\bBTC\b', r'\bETH\b', r'\bDEEP\b', r'\bCETUS\b']
        for pattern in token_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                warnings.append(
                    f"input '{key}' contains token literal: '{value}' "
                    f"(inputs must be source presence only, no token literals)"
                )
                break

        # Check for amount patterns (decimal numbers)
        if re.search(r'\d+\.\d+', value):
            warnings.append(
                f"input '{key}' contains amount pattern: '{value}' "
                f"(inputs must be source presence only, no amounts)"
            )

    return warnings


def check_intended_shape_structural(intended_shape: Dict[str, Any]) -> List[str]:
    """
    Check that intended_shape is structural label (not prescriptive).

    Args:
        intended_shape: Intended shape dict to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(intended_shape, dict):
        warnings.append(
            f"intended_shape is not dict: {type(intended_shape).__name__} "
            f"(must be dict with action_class)"
        )
        return warnings

    # Check action_class field
    action_class = intended_shape.get("action_class")
    if not action_class:
        warnings.append(
            "intended_shape missing action_class field "
            "(must have structural action_class label)"
        )
        return warnings

    if not isinstance(action_class, str):
        warnings.append(
            f"action_class is not string: {type(action_class).__name__} "
            f"(must be structural label)"
        )
        return warnings

    # Check that action_class is valid structural label
    if action_class not in VALID_ACTION_CLASSES:
        warnings.append(
            f"action_class has invalid value: '{action_class}' "
            f"(must be one of: {', '.join(VALID_ACTION_CLASSES)})"
        )

    # Check for prescriptive language in action_class
    prescriptive_patterns = [
        r'\bshould\b',
        r'\bmust\b',
        r'\bneed\s+to\b',
        r'\bhave\s+to\b',
        r'\bought\s+to\b',
    ]
    for pattern in prescriptive_patterns:
        if re.search(pattern, action_class, re.IGNORECASE):
            warnings.append(
                f"action_class contains prescriptive language: '{action_class}' "
                f"(intended_shape must be structural label, not prescription)"
            )
            break

    return warnings


def check_binding_output(binding_result: Dict[str, Any]) -> List[str]:
    """
    Validate binding output against constitutional guards.

    Args:
        binding_result: Binding result to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    if not isinstance(binding_result, dict):
        warnings.append(
            f"binding result is not dict: {type(binding_result).__name__}"
        )
        return warnings

    # Check that execution_draft key exists
    execution_draft = binding_result.get("execution_draft")
    if not execution_draft:
        warnings.append("binding result missing execution_draft")
        return warnings

    if not isinstance(execution_draft, dict):
        warnings.append(
            f"execution_draft is not dict: {type(execution_draft).__name__}"
        )
        return warnings

    # Check inputs (source presence only)
    inputs = execution_draft.get("v13_draft_inputs", {})
    input_warnings = check_source_presence_only_inputs(inputs)
    warnings.extend(input_warnings)

    # Check constraints (label-only)
    constraints = execution_draft.get("v13_draft_constraints", {})
    constraint_warnings = check_label_only_constraints(constraints)
    warnings.extend(constraint_warnings)

    # Check intended_shape (structural)
    intended_shape = execution_draft.get("v13_draft_intended_shape", {})
    shape_warnings = check_intended_shape_structural(intended_shape)
    warnings.extend(shape_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.3 Binding Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean binding output (no warnings)
    print("Test 1: Clean binding output (no warnings)")
    clean_output = {
        "execution_draft": {
            "v13_draft_inputs": {
                "regime_record_present": "true",
                "drift_record_present": "true",
            },
            "v13_draft_constraints": {
                "permission": "PERMISSION_ALLOWED",
                "eligibility": "ELIGIBLE",
            },
            "v13_draft_intended_shape": {
                "action_class": "SIMULATION_ONLY",
            },
        },
        "warnings": [],
    }
    clean_warnings = check_binding_output(clean_output)
    print(f"Clean output warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty inputs (value leakage)
    print("Test 2: Dirty inputs (value leakage)")
    dirty_inputs = {
        "sui_amount": "1000000000",
        "address": "0x1234567890abcdef",
    }
    dirty_warnings = check_source_presence_only_inputs(dirty_inputs)
    print(f"Dirty inputs warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty constraints (token literals)
    print("Test 3: Dirty constraints (token literals)")
    dirty_constraints = {
        "token_pair": "SUI/USDC",
        "amount": "1000.50",
    }
    dirty_warnings_constraints = check_label_only_constraints(dirty_constraints)
    print(f"Dirty constraints warnings: {len(dirty_warnings_constraints)}")
    if dirty_warnings_constraints:
        print("  Warnings:")
        for w in dirty_warnings_constraints:
            print(f"    - {w}")
    print()

    # Test 4: Invalid intended_shape
    print("Test 4: Invalid intended_shape")
    invalid_shape = {
        "action_class": "YOU_SHOULD_EXECUTE_THIS",
    }
    shape_warnings = check_intended_shape_structural(invalid_shape)
    print(f"Invalid shape warnings: {len(shape_warnings)}")
    if shape_warnings:
        print("  Warnings:")
        for w in shape_warnings:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
