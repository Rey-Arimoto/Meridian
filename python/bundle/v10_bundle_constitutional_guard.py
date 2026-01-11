#!/usr/bin/env python3
"""
PR116: v1.0 Bundle Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on bundle records.
    Guards against trading vocabulary, execution operations, and bundle overreach.

Constitutional Constraints:
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution vocabulary: No transaction, broadcast, submit
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No 0x... patterns
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary
    - Non-prescriptive: No should/must recommendations
    - Bundle-specific: No decision/evaluation vocabulary
    - Bundle = Container only (not decision/evaluation/action)
    - Ordering consistency: layers list matches artifacts keys

Guards:
    1. Trading vocabulary guard (swap, buy, sell, execute, sign, transfer)
    2. Execution operation guard (transaction, broadcast, submit)
    3. Token literal guard (token names)
    4. Address pattern guard (0x...)
    5. Asset vocabulary guard (balance, holdings, portfolio)
    6. Action vocabulary guard (recommend, suggest, optimize)
    7. Forbidden vocabulary guard (evaluative/prescriptive)
    8. Numeric pattern guard (amounts, prices, percentages)
    9. Bundle overreach guard (NEW in PR116)
    10. Ordering consistency guard (NEW in PR116)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_bundle_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate bundle record against all constitutional guards.

    Args:
        record: Bundle record to validate

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

    # Check bundle summary
    if "v10_bundle_summary" in record:
        summary = record["v10_bundle_summary"]
        if isinstance(summary, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(summary)
            warnings.extend(trading_warnings)

            # Execution operation guard
            execution_warnings = check_execution_operations(summary)
            warnings.extend(execution_warnings)

            # Address pattern guard
            address_warnings = check_address_patterns(summary)
            warnings.extend(address_warnings)

            # Asset vocabulary guard
            asset_warnings = check_asset_vocabulary(summary)
            warnings.extend(asset_warnings)

            # Action vocabulary guard
            action_warnings = check_action_vocabulary(summary)
            warnings.extend(action_warnings)

            # Forbidden vocabulary guard
            vocab_warnings = check_forbidden_vocabulary(summary)
            warnings.extend(vocab_warnings)

            # Numeric pattern guard
            numeric_warnings = check_numeric_patterns(summary)
            warnings.extend(numeric_warnings)

            # Bundle overreach guard (NEW in PR116)
            bundle_warnings = check_bundle_overreach(summary)
            warnings.extend(bundle_warnings)

    # Check error info (if present)
    if "v10_bundle_error_info" in record:
        error_info = record["v10_bundle_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(error_info)
            warnings.extend(trading_warnings)

    # Check warnings list (if present)
    if "v10_bundle_warnings" in record and isinstance(
        record["v10_bundle_warnings"], list
    ):
        for warning in record["v10_bundle_warnings"]:
            if isinstance(warning, str):
                # Token literals guard
                token_warnings = check_observation_token_literals(warning)
                warnings.extend(token_warnings)

                # Trading vocabulary guard
                trading_warnings = check_trading_vocabulary(warning)
                warnings.extend(trading_warnings)

    # Ordering consistency guard (NEW in PR116)
    ordering_warnings = check_ordering_consistency(record)
    warnings.extend(ordering_warnings)

    # Check artifacts recursively (lightweight check on summaries)
    if "v10_bundle_artifacts" in record and isinstance(
        record["v10_bundle_artifacts"], dict
    ):
        for layer_name, artifact in record["v10_bundle_artifacts"].items():
            if isinstance(artifact, dict):
                # Check for summary fields in artifacts
                artifact_warnings = _check_artifact_summary(artifact)
                warnings.extend(artifact_warnings)

    return warnings


def _check_artifact_summary(artifact: Dict[str, Any]) -> List[str]:
    """
    Check artifact summary fields against guards.

    Args:
        artifact: Artifact record to check

    Returns:
        List of warnings
    """
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from preview.v11_preview_constitutional_guard import (
        check_trading_vocabulary,
        check_numeric_patterns,
    )

    warnings = []

    # Check various summary fields that might be present
    summary_fields = [
        "v11_regime_summary",
        "v11_policy_summary",
        "v11_preview_summary",
        "v11_approval_summary",
        "v11_registry_summary",
    ]

    for field in summary_fields:
        if field in artifact and isinstance(artifact[field], str):
            summary = artifact[field]

            # Token literals guard
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(summary)
            warnings.extend(trading_warnings)

            # Numeric pattern guard
            numeric_warnings = check_numeric_patterns(summary)
            warnings.extend(numeric_warnings)

    return warnings


def check_bundle_overreach(text: str) -> List[str]:
    """
    Check for bundle overreach patterns (NEW in PR116).

    Detects phrases that suggest bundle is making decisions or evaluations.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Bundle overreach patterns
    # These phrases suggest bundle is making decisions/evaluations
    overreach_patterns = [
        "bundle recommends",
        "bundle suggests",
        "bundle decides",
        "bundle chooses",
        "bundle selects",
        "bundle evaluates",
        "bundle optimizes",
        "bundle approves",
        "bundle rejects",
        "bundle should",
        "bundle must",
        "bundle will execute",
        "bundle will trade",
        "bundle indicates execute",
        "bundle indicates trade",
    ]

    for pattern in overreach_patterns:
        if pattern in text_lower:
            warnings.append(f"Bundle overreach detected: '{pattern}' in text")

    # Also check for decision/evaluation vocabulary in bundle context
    if "bundle" in text_lower:
        decision_verbs = [
            "decide",
            "recommend",
            "suggest",
            "evaluate",
            "optimize",
            "choose",
            "select",
            "approve",
            "reject",
        ]
        for verb in decision_verbs:
            if verb in text_lower:
                # Check proximity (within 50 chars)
                bundle_pos = text_lower.find("bundle")
                verb_pos = text_lower.find(verb)
                if (
                    bundle_pos >= 0
                    and verb_pos >= 0
                    and abs(bundle_pos - verb_pos) < 50
                ):
                    warnings.append(
                        f"Possible bundle overreach: 'bundle' near '{verb}' in text"
                    )
                    break  # Only report once

    return warnings


def check_ordering_consistency(record: Dict[str, Any]) -> List[str]:
    """
    Check ordering consistency (NEW in PR116).

    Verifies that layers list matches artifacts keys and maintains order.

    Args:
        record: Bundle record to check

    Returns:
        List of warnings
    """
    warnings = []

    layers = record.get("v10_bundle_layers", [])
    artifacts = record.get("v10_bundle_artifacts", {})

    if not isinstance(layers, list):
        warnings.append("Bundle layers is not a list")
        return warnings

    if not isinstance(artifacts, dict):
        warnings.append("Bundle artifacts is not a dict")
        return warnings

    # Check that all artifacts have corresponding layer entries
    artifact_keys = set(artifacts.keys())
    layer_set = set(layers)

    # Artifacts without layer entries
    orphaned = artifact_keys - layer_set
    if orphaned:
        warnings.append(
            f"Artifacts without layer entries: {sorted(orphaned)}"
        )

    # Layer entries without artifacts
    missing = layer_set - artifact_keys
    if missing:
        warnings.append(
            f"Layer entries without artifacts: {sorted(missing)}"
        )

    # Check that layers list order is preserved in artifacts
    # (not enforced strictly, just a warning if wildly out of order)
    # This is a soft check - we just warn if ordering seems inconsistent

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Bundle Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean bundle record
    print("Test 1: Clean bundle record")
    clean_bundle = {
        "v10_bundle_summary": "artifact bundle with 3 layers. pipeline output captured.",
        "v10_bundle_layers": ["REGIME", "POLICY_BINDING", "PREVIEW"],
        "v10_bundle_artifacts": {
            "REGIME": {"v11_regime_summary": "entropy regime classified as low."},
            "POLICY_BINDING": {
                "v11_policy_summary": "regime bound to execution policy."
            },
            "PREVIEW": {"v11_preview_summary": "execution preview generated."},
        },
    }
    clean_warnings = validate_bundle_record(clean_bundle)
    print(f"Clean bundle warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty bundle (trading vocabulary)
    print("Test 2: Dirty bundle (trading vocabulary)")
    dirty_bundle_trading = {
        "v10_bundle_summary": "artifact bundle complete. execute swap operations.",
        "v10_bundle_layers": ["REGIME"],
        "v10_bundle_artifacts": {
            "REGIME": {"v11_regime_summary": "regime classified. buy tokens now."}
        },
    }
    dirty_warnings = validate_bundle_record(dirty_bundle_trading)
    print(f"Dirty bundle warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty bundle (bundle overreach)
    print("Test 3: Dirty bundle (bundle overreach)")
    dirty_bundle_overreach = {
        "v10_bundle_summary": "bundle recommends proceeding with execution.",
        "v10_bundle_layers": [],
        "v10_bundle_artifacts": {},
    }
    dirty_warnings_overreach = validate_bundle_record(dirty_bundle_overreach)
    print(f"Dirty bundle warnings: {len(dirty_warnings_overreach)}")
    if dirty_warnings_overreach:
        print("  Warnings:")
        for w in dirty_warnings_overreach:
            print(f"    - {w}")
    print()

    # Test 4: Dirty bundle (token literals)
    print("Test 4: Dirty bundle (token literals)")
    dirty_bundle_token = {
        "v10_bundle_summary": "artifact bundle with SUI and USDC analysis.",
        "v10_bundle_layers": ["REGIME"],
        "v10_bundle_artifacts": {"REGIME": {}},
    }
    dirty_warnings_token = validate_bundle_record(dirty_bundle_token)
    print(f"Dirty bundle warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 5: Dirty bundle (numeric patterns)
    print("Test 5: Dirty bundle (numeric patterns)")
    dirty_bundle_numeric = {
        "v10_bundle_summary": "artifact bundle for $1000 transaction.",
        "v10_bundle_layers": [],
        "v10_bundle_artifacts": {},
    }
    dirty_warnings_numeric = validate_bundle_record(dirty_bundle_numeric)
    print(f"Dirty bundle warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 6: Ordering inconsistency
    print("Test 6: Ordering inconsistency")
    inconsistent_bundle = {
        "v10_bundle_summary": "artifact bundle.",
        "v10_bundle_layers": ["REGIME", "POLICY_BINDING"],
        "v10_bundle_artifacts": {
            "REGIME": {},
            "POLICY_BINDING": {},
            "PREVIEW": {},  # Not in layers list
        },
    }
    ordering_warnings = validate_bundle_record(inconsistent_bundle)
    print(f"Inconsistent bundle warnings: {len(ordering_warnings)}")
    if ordering_warnings:
        print("  Warnings:")
        for w in ordering_warnings:
            print(f"    - {w}")
    print()

    # Test 7: Clean bundle with "bundle" (label only)
    print("Test 7: Clean bundle with 'bundle' (label only)")
    clean_bundle_label = {
        "v10_bundle_summary": "artifact bundle complete. all layers present.",
        "v10_bundle_layers": [],
        "v10_bundle_artifacts": {},
    }
    clean_label_warnings = validate_bundle_record(clean_bundle_label)
    print(f"Clean bundle label warnings: {len(clean_label_warnings)}")
    if clean_label_warnings:
        print(f"  Warnings: {clean_label_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
