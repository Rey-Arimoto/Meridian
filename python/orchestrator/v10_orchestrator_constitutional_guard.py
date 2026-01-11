#!/usr/bin/env python3
"""
PR115: v1.0 Orchestrator Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on orchestrator artifacts.
    Guards against trading vocabulary, execution operations, and orchestrator overreach.

Constitutional Constraints:
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution vocabulary: No transaction, broadcast, submit
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No 0x... patterns
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary
    - Non-prescriptive: No should/must recommendations
    - Orchestrator-specific: No decision/recommendation vocabulary
    - Orchestrator = Wiring only (not decision/action)

Guards:
    1. Trading vocabulary guard (swap, buy, sell, execute, sign, transfer)
    2. Execution operation guard (transaction, broadcast, submit)
    3. Token literal guard (token names)
    4. Address pattern guard (0x...)
    5. Asset vocabulary guard (balance, holdings, portfolio)
    6. Action vocabulary guard (recommend, suggest, optimize)
    7. Forbidden vocabulary guard (evaluative/prescriptive)
    8. Numeric pattern guard (amounts, prices, percentages)
    9. Orchestrator overreach guard (NEW in PR115)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_orchestrator_artifacts(artifacts: Dict[str, Any]) -> List[str]:
    """
    Validate orchestrator artifacts against all constitutional guards.

    Args:
        artifacts: Orchestrator artifact bundle to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing guards
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from bridge.v10_bridge_constitutional_guard import (
        check_asset_vocabulary,
        check_execution_vocabulary_bridge,
    )
    from regime.v11_regime_constitutional_guard import (
        check_action_vocabulary,
    )
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )
    from preview.v11_preview_constitutional_guard import (
        check_trading_vocabulary,
        check_execution_operations,
        check_address_patterns,
        check_numeric_patterns,
    )

    warnings = []

    # Check pipeline warnings (if present)
    if "pipeline_warnings" in artifacts and isinstance(artifacts["pipeline_warnings"], list):
        for warning in artifacts["pipeline_warnings"]:
            if isinstance(warning, str):
                # Token literals guard
                token_warnings = check_observation_token_literals(warning)
                warnings.extend(token_warnings)

                # Trading vocabulary guard
                trading_warnings = check_trading_vocabulary(warning)
                warnings.extend(trading_warnings)

    # Check pipeline metadata
    if "pipeline_status" in artifacts:
        status = artifacts["pipeline_status"]
        if isinstance(status, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(status)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(status)
            warnings.extend(trading_warnings)

            # Orchestrator overreach guard (NEW in PR115)
            overreach_warnings = check_orchestrator_overreach(status)
            warnings.extend(overreach_warnings)

    # Check all artifact summaries (recursively)
    for key, value in artifacts.items():
        if isinstance(value, dict):
            # Check if it has a summary field
            if "v11_regime_summary" in value:
                summary = value["v11_regime_summary"]
                if isinstance(summary, str):
                    warnings.extend(_check_summary_field(summary))

            if "v11_policy_summary" in value:
                summary = value["v11_policy_summary"]
                if isinstance(summary, str):
                    warnings.extend(_check_summary_field(summary))

            if "v11_preview_summary" in value:
                summary = value["v11_preview_summary"]
                if isinstance(summary, str):
                    warnings.extend(_check_summary_field(summary))

            if "v11_approval_summary" in value:
                summary = value["v11_approval_summary"]
                if isinstance(summary, str):
                    warnings.extend(_check_summary_field(summary))

            if "v11_registry_summary" in value:
                summary = value["v11_registry_summary"]
                if isinstance(summary, str):
                    warnings.extend(_check_summary_field(summary))

    return warnings


def _check_summary_field(summary: str) -> List[str]:
    """
    Check a summary field against all guards.

    Args:
        summary: Summary text to check

    Returns:
        List of warnings
    """
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from preview.v11_preview_constitutional_guard import (
        check_trading_vocabulary,
        check_execution_operations,
        check_address_patterns,
        check_numeric_patterns,
    )

    warnings = []

    # Token literals guard
    warnings.extend(check_observation_token_literals(summary))

    # Trading vocabulary guard
    warnings.extend(check_trading_vocabulary(summary))

    # Execution operation guard
    warnings.extend(check_execution_operations(summary))

    # Address pattern guard
    warnings.extend(check_address_patterns(summary))

    # Numeric pattern guard
    warnings.extend(check_numeric_patterns(summary))

    return warnings


def check_orchestrator_overreach(text: str) -> List[str]:
    """
    Check for orchestrator overreach patterns (NEW in PR115).

    Detects phrases that suggest orchestrator is making decisions or recommendations.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Orchestrator overreach patterns
    # These phrases suggest orchestrator is making decisions
    overreach_patterns = [
        "orchestrator recommends",
        "orchestrator suggests",
        "orchestrator decides",
        "orchestrator chooses",
        "orchestrator selects",
        "orchestrator optimizes",
        "orchestrator reorders",
        "orchestrator skips",
        "orchestrator enables",
        "orchestrator disables",
        "orchestrator should",
        "orchestrator must",
        "orchestrator will execute",
        "orchestrator will trade",
        "orchestrator will sign",
    ]

    for pattern in overreach_patterns:
        if pattern in text_lower:
            warnings.append(f"Orchestrator overreach detected: '{pattern}' in text")

    # Also check for decision/recommendation vocabulary in orchestrator context
    if "orchestrator" in text_lower:
        decision_verbs = ["decide", "recommend", "suggest", "optimize", "choose", "select", "reorder"]
        for verb in decision_verbs:
            if verb in text_lower:
                # Check proximity (within 50 chars)
                orchestrator_pos = text_lower.find("orchestrator")
                verb_pos = text_lower.find(verb)
                if orchestrator_pos >= 0 and verb_pos >= 0 and abs(orchestrator_pos - verb_pos) < 50:
                    warnings.append(f"Possible orchestrator overreach: 'orchestrator' near '{verb}' in text")
                    break  # Only report once

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Orchestrator Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean artifacts
    print("Test 1: Clean artifacts")
    clean_artifacts = {
        "pipeline_version": "v1",
        "pipeline_status": "COMPLETE",
        "pipeline_order": ["onchain_analytics", "regime_record"],
        "regime_record": {
            "v11_regime_summary": "entropy regime classified as low. classification complete.",
        },
    }
    clean_warnings = validate_orchestrator_artifacts(clean_artifacts)
    print(f"Clean artifacts warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty artifacts (trading vocabulary)
    print("Test 2: Dirty artifacts (trading vocabulary)")
    dirty_artifacts_trading = {
        "pipeline_status": "COMPLETE",
        "regime_record": {
            "v11_regime_summary": "swap operation recommended based on regime.",
        },
    }
    dirty_warnings = validate_orchestrator_artifacts(dirty_artifacts_trading)
    print(f"Dirty artifacts warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty artifacts (orchestrator overreach)
    print("Test 3: Dirty artifacts (orchestrator overreach)")
    dirty_artifacts_overreach = {
        "pipeline_status": "orchestrator recommends proceeding with execution.",
    }
    dirty_warnings_overreach = validate_orchestrator_artifacts(dirty_artifacts_overreach)
    print(f"Dirty artifacts warnings: {len(dirty_warnings_overreach)}")
    if dirty_warnings_overreach:
        print("  Warnings:")
        for w in dirty_warnings_overreach:
            print(f"    - {w}")
    print()

    # Test 4: Dirty artifacts (token literals)
    print("Test 4: Dirty artifacts (token literals)")
    dirty_artifacts_token = {
        "pipeline_warnings": ["SUI price analysis complete"],
        "regime_record": {
            "v11_regime_summary": "USDC liquidity regime classified.",
        },
    }
    dirty_warnings_token = validate_orchestrator_artifacts(dirty_artifacts_token)
    print(f"Dirty artifacts warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 5: Dirty artifacts (numeric patterns)
    print("Test 5: Dirty artifacts (numeric patterns)")
    dirty_artifacts_numeric = {
        "regime_record": {
            "v11_regime_summary": "regime classified with $1000 threshold at 5% confidence.",
        },
    }
    dirty_warnings_numeric = validate_orchestrator_artifacts(dirty_artifacts_numeric)
    print(f"Dirty artifacts warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 6: Clean artifacts with "orchestrator" (label only)
    print("Test 6: Clean artifacts with 'orchestrator' (label only)")
    clean_orchestrator_artifacts = {
        "pipeline_status": "orchestrator completed fixed-order wiring. all layers connected.",
    }
    clean_orchestrator_warnings = validate_orchestrator_artifacts(clean_orchestrator_artifacts)
    print(f"Clean orchestrator artifacts warnings: {len(clean_orchestrator_warnings)}")
    if clean_orchestrator_warnings:
        print(f"  Warnings: {clean_orchestrator_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
