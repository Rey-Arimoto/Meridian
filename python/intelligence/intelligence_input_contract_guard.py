#!/usr/bin/env python3
"""
PR37: v0.5 Intelligence Input Contract Compliance Guard

Purpose: Mechanical enforcement of PR36 Input Contract Charter.

Validates:
- Import ban: v0.5 cannot import v0.4 builders/validators
- Input allowlist: v0.5 may only read declared input categories
- Featurization ban: v0.5 cannot score/featurize confidence_reason

Non-Goals:
- No runtime behavior changes
- No decision/control impact
- No exceptions raised (warning-only)

Exit code: Always 0 (warning-only)

Dependencies:
- PR35: Intelligence Boundary Charter
- PR36: Intelligence Input Contract Charter
"""

import re
from typing import List, Dict, Any


# PR36 Category A: Market/State Fields (non-exhaustive examples)
CATEGORY_A_MARKET_STATE = {
    "price",
    "volume",
    "spread",
    "volatility",
    "ma_short",
    "ma_long",
    "orderbook_depth",
    "position_size",
    "equity",
    "balance",
    "timestamp",
    "tick_count",
    "entropy_bp",
}

# PR36 Category B: Intent/Regime Fields
CATEGORY_B_INTENT_REGIME = {
    "intent_primary",
    "intent_reason",
    "regime",
    "base_action",
    "overlay_rule",
    "decision_reason",
}

# PR36 Category C: v0.4 Confidence Snapshot Fields (READ-ONLY)
CATEGORY_C_CONFIDENCE_SNAPSHOT = {
    "confidence_reason",
    "confidence_reason_version",
    "confidence_reason_generated_at",
    "confidence_value",  # Currently empty, reserved
}

# Combined allowlist
ALLOWED_INPUT_KEYS = (
    CATEGORY_A_MARKET_STATE
    | CATEGORY_B_INTENT_REGIME
    | CATEGORY_C_CONFIDENCE_SNAPSHOT
)

# PR36 Ban 4: Prohibited imports (v0.4 builders/validators)
PROHIBITED_IMPORTS = [
    "confidence.confidence_reason_builder",
    "confidence.confidence_reason_compliance",
]

# PR36 Ban 3: Featurization patterns (on confidence_reason)
FEATURIZATION_PATTERNS = [
    r'len\s*\(\s*.*confidence_reason.*\)',  # len(confidence_reason)
    r'.*confidence_reason.*\.split\s*\(',   # confidence_reason.split(
    r'hash\s*\(\s*.*confidence_reason.*\)', # hash(confidence_reason)
    r'embed\s*\(\s*.*confidence_reason.*\)', # embed(confidence_reason)
    r'confidence_reason.*\[.*:.*\]',        # confidence_reason[start:end] (slicing)
    r'confidence_reason.*\.count\s*\(',     # confidence_reason.count(
    r'confidence_reason.*\.find\s*\(',      # confidence_reason.find(
    r'confidence_reason.*\.index\s*\(',     # confidence_reason.index(
]


def validate_intelligence_imports(
    module_text: str, module_name: str = ""
) -> List[str]:
    """
    PR37: Validate v0.5 Intelligence imports against PR36 Import Ban.

    Detects prohibited imports:
    - confidence.confidence_reason_builder (v0.4 builder)
    - confidence.confidence_reason_compliance (v0.4 validator)

    Args:
        module_text: Source code text to validate
        module_name: Optional module name for warning context

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []
    module_context = f" in {module_name}" if module_name else ""

    for prohibited_import in PROHIBITED_IMPORTS:
        # Pattern: from <prohibited_import> import ...
        from_pattern = rf'from\s+{re.escape(prohibited_import)}\s+import'
        # Pattern: import <prohibited_import>
        import_pattern = rf'import\s+{re.escape(prohibited_import)}'

        if re.search(from_pattern, module_text) or re.search(import_pattern, module_text):
            warnings.append(
                f"PR36 Ban 4 violation: prohibited import '{prohibited_import}'{module_context}"
            )

    return warnings


def validate_intelligence_inputs(inputs: Dict[str, Any]) -> List[str]:
    """
    PR37: Validate v0.5 Intelligence inputs against PR36 Input Allowlist.

    Checks that all input keys are in declared allowlist:
    - Category A: Market/State fields
    - Category B: Intent/Regime fields
    - Category C: v0.4 Confidence Snapshot fields (READ-ONLY)

    Args:
        inputs: Dictionary of input keys to validate

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []

    for key in inputs.keys():
        if key not in ALLOWED_INPUT_KEYS:
            warnings.append(
                f"PR36 Input Contract violation: undeclared input key '{key}' "
                f"(not in Category A/B/C allowlist)"
            )

    return warnings


def validate_confidence_snapshot_usage(
    usage_text: str, module_name: str = ""
) -> List[str]:
    """
    PR37: Validate v0.5 usage of confidence_reason against PR36 Featurization Ban.

    Detects prohibited operations:
    - len(confidence_reason) — length scoring
    - confidence_reason.split() — tokenization
    - hash(confidence_reason) — hashing for features
    - embed(confidence_reason) — embedding generation
    - confidence_reason[start:end] — slicing for features
    - confidence_reason.count() — character counting
    - confidence_reason.find/index() — pattern matching for features

    Args:
        usage_text: Source code text to validate
        module_name: Optional module name for warning context

    Returns:
        List of warning strings (empty if compliant)

    Never raises exceptions.
    """
    warnings = []
    module_context = f" in {module_name}" if module_name else ""

    for pattern in FEATURIZATION_PATTERNS:
        if re.search(pattern, usage_text):
            warnings.append(
                f"PR36 Ban 3 violation: featurization pattern detected{module_context} "
                f"(pattern: {pattern})"
            )

    return warnings
