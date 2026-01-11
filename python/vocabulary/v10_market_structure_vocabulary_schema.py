#!/usr/bin/env python3
"""
PR119: v1.0 Market Structure Vocabulary Schema v1 (READ-ONLY)

Purpose:
    Define schema for market structure vocabulary records.
    Vocabulary = Market Structure Language (not price, not ownership).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No numeric amounts: No prices, balances, counts
    - Vocabulary = structural description (not evaluation/action)

Vocabulary Philosophy:
    Vocabulary ≠ Evaluation
    Vocabulary ≠ Recommendation
    Vocabulary = Structural Language

    Vocabulary provides:
    - Fixed structural terms
    - Presence/absence descriptions
    - Market structure language
    - Stable reference tokens

    Vocabulary does NOT:
    - Contain amounts or prices
    - Contain token names
    - Contain addresses
    - Recommend actions
    - Evaluate quality

Vocabulary Fields:
    - v10_vocab_mode: ON/OFF
    - v10_vocab_status: AVAILABLE/ERROR
    - v10_vocab_terms: List[str] of vocabulary terms
    - v10_vocab_summary: non-evaluative summary string
    - v10_vocab_basis: list of field names used (structural)
    - v10_vocab_warnings: optional list of warning strings
    - v10_vocab_error_info: optional error description (if status=ERROR)

Vocabulary Term Families (v1):
    Market Cost Regime Presence:
        - COST_LOW_PRESENT
        - COST_MEDIUM_PRESENT
        - COST_HIGH_PRESENT

    Liquidity Regime Presence:
        - LIQUIDITY_LOW_PRESENT
        - LIQUIDITY_MEDIUM_PRESENT
        - LIQUIDITY_HIGH_PRESENT

    Event Activity:
        - EVENT_ACTIVITY_PRESENT
        - EVENT_ACTIVITY_ABSENT

    Object Dynamics Presence:
        - OBJECT_DYNAMICS_DECREASE_PRESENT
        - OBJECT_DYNAMICS_STABLE_PRESENT
        - OBJECT_DYNAMICS_INCREASE_PRESENT
"""

from typing import Any, Dict, List, Optional


class V10MarketStructureVocabularySchema:
    """Market structure vocabulary schema v1.0"""

    # Valid modes
    VALID_MODES = ["ON", "OFF"]

    # Valid statuses
    VALID_STATUSES = ["AVAILABLE", "ERROR"]

    # Valid vocabulary terms (fixed set for v1)
    VALID_TERMS = [
        # Market cost regime presence
        "COST_LOW_PRESENT",
        "COST_MEDIUM_PRESENT",
        "COST_HIGH_PRESENT",
        # Liquidity regime presence
        "LIQUIDITY_LOW_PRESENT",
        "LIQUIDITY_MEDIUM_PRESENT",
        "LIQUIDITY_HIGH_PRESENT",
        # Event activity
        "EVENT_ACTIVITY_PRESENT",
        "EVENT_ACTIVITY_ABSENT",
        # Object dynamics presence
        "OBJECT_DYNAMICS_DECREASE_PRESENT",
        "OBJECT_DYNAMICS_STABLE_PRESENT",
        "OBJECT_DYNAMICS_INCREASE_PRESENT",
    ]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty vocabulary record.

        Returns:
            Empty vocabulary record
        """
        return {
            "v10_vocab_mode": "ON",
            "v10_vocab_status": "AVAILABLE",
            "v10_vocab_terms": [],
            "v10_vocab_summary": "empty market structure vocabulary. no terms present.",
            "v10_vocab_basis": [],
        }

    @staticmethod
    def create_error_record(
        error_info: str = "unknown error",
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an error vocabulary record.

        Args:
            error_info: Error description
            warnings: Optional list of warnings

        Returns:
            Error vocabulary record
        """
        record = {
            "v10_vocab_mode": "ON",
            "v10_vocab_status": "ERROR",
            "v10_vocab_terms": [],
            "v10_vocab_summary": f"market structure vocabulary error. {error_info}",
            "v10_vocab_basis": [],
            "v10_vocab_error_info": error_info,
        }

        if warnings:
            record["v10_vocab_warnings"] = warnings

        return record

    @staticmethod
    def create_vocabulary_record(
        terms: List[str],
        summary: str,
        basis: List[str],
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a vocabulary record.

        Args:
            terms: List of vocabulary terms
            summary: Non-evaluative summary
            basis: List of field names used
            warnings: Optional list of warnings

        Returns:
            Vocabulary record
        """
        record = {
            "v10_vocab_mode": "ON",
            "v10_vocab_status": "AVAILABLE",
            "v10_vocab_terms": terms,
            "v10_vocab_summary": summary,
            "v10_vocab_basis": basis,
        }

        if warnings:
            record["v10_vocab_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate vocabulary record structure.

        Args:
            record: Vocabulary record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        required_fields = [
            "v10_vocab_mode",
            "v10_vocab_status",
            "v10_vocab_terms",
            "v10_vocab_summary",
            "v10_vocab_basis",
        ]

        for field in required_fields:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v10_vocab_mode" in record:
            if (
                record["v10_vocab_mode"]
                not in V10MarketStructureVocabularySchema.VALID_MODES
            ):
                warnings.append(f"Invalid vocab mode: {record['v10_vocab_mode']}")

        # Validate status
        if "v10_vocab_status" in record:
            if (
                record["v10_vocab_status"]
                not in V10MarketStructureVocabularySchema.VALID_STATUSES
            ):
                warnings.append(
                    f"Invalid vocab status: {record['v10_vocab_status']}"
                )

        # Validate terms
        if "v10_vocab_terms" in record:
            if not isinstance(record["v10_vocab_terms"], list):
                warnings.append("Vocab terms must be a list")
            else:
                for term in record["v10_vocab_terms"]:
                    if not isinstance(term, str):
                        warnings.append(f"Vocab term must be string: {term}")
                    elif (
                        term
                        not in V10MarketStructureVocabularySchema.VALID_TERMS
                    ):
                        warnings.append(f"Invalid vocab term: {term}")

        # Validate basis
        if "v10_vocab_basis" in record:
            if not isinstance(record["v10_vocab_basis"], list):
                warnings.append("Vocab basis must be a list")

        return warnings


def get_vocabulary_schema_info() -> Dict[str, Any]:
    """
    Get vocabulary schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "market_structure_vocabulary",
        "valid_modes": V10MarketStructureVocabularySchema.VALID_MODES,
        "valid_statuses": V10MarketStructureVocabularySchema.VALID_STATUSES,
        "valid_terms": V10MarketStructureVocabularySchema.VALID_TERMS,
        "term_families": {
            "market_cost_regime": ["COST_LOW_PRESENT", "COST_MEDIUM_PRESENT", "COST_HIGH_PRESENT"],
            "liquidity_regime": ["LIQUIDITY_LOW_PRESENT", "LIQUIDITY_MEDIUM_PRESENT", "LIQUIDITY_HIGH_PRESENT"],
            "event_activity": ["EVENT_ACTIVITY_PRESENT", "EVENT_ACTIVITY_ABSENT"],
            "object_dynamics": ["OBJECT_DYNAMICS_DECREASE_PRESENT", "OBJECT_DYNAMICS_STABLE_PRESENT", "OBJECT_DYNAMICS_INCREASE_PRESENT"],
        },
        "required_fields": [
            "v10_vocab_mode",
            "v10_vocab_status",
            "v10_vocab_terms",
            "v10_vocab_summary",
            "v10_vocab_basis",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Market Structure Vocabulary Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V10MarketStructureVocabularySchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V10MarketStructureVocabularySchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V10MarketStructureVocabularySchema.create_error_record(
        error_info="test error",
        warnings=["test warning"],
    )
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create vocabulary record
    print("Test 4: Create vocabulary record")
    vocab = V10MarketStructureVocabularySchema.create_vocabulary_record(
        terms=[
            "COST_LOW_PRESENT",
            "LIQUIDITY_LOW_PRESENT",
            "EVENT_ACTIVITY_ABSENT",
            "OBJECT_DYNAMICS_STABLE_PRESENT",
        ],
        summary="market structure vocabulary with 4 terms. low cost and low liquidity regimes present.",
        basis=["market_cost_regime_counts", "liquidity_regime_presence"],
    )
    print(json.dumps(vocab, indent=2))
    print()

    # Test 5: Validate vocabulary record
    print("Test 5: Validate vocabulary record")
    warnings = V10MarketStructureVocabularySchema.validate_structure(vocab)
    print(f"Warnings: {warnings}")
    print()

    # Test 6: Validate invalid term
    print("Test 6: Validate invalid term")
    invalid_vocab = V10MarketStructureVocabularySchema.create_vocabulary_record(
        terms=["INVALID_TERM", "COST_LOW_PRESENT"],
        summary="test",
        basis=[],
    )
    warnings = V10MarketStructureVocabularySchema.validate_structure(invalid_vocab)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
