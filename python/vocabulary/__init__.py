#!/usr/bin/env python3
"""
PR119: v1.0 Market Structure Vocabulary Schema & Builder v1 (READ-ONLY)

Purpose:
    Market structure vocabulary layer for converting analytics to stable structural terms.
    Vocabulary = Market Structure Language (not price, not ownership).

Exports:
    - V10MarketStructureVocabularySchema: Vocabulary schema class
    - get_vocabulary_schema_info: Vocabulary schema metadata
    - build_market_structure_vocabulary_v1: Core vocabulary builder function
    - get_vocabulary_builder_v1_info: Builder metadata
    - validate_vocabulary_record: Constitutional guard for vocabulary records
"""

from .v10_market_structure_vocabulary_schema import (
    V10MarketStructureVocabularySchema,
    get_vocabulary_schema_info,
)
from .v10_market_structure_vocabulary_builder_v1 import (
    build_market_structure_vocabulary_v1,
    get_vocabulary_builder_v1_info,
)
from .v10_vocab_constitutional_guard import (
    validate_vocabulary_record,
)

__all__ = [
    "V10MarketStructureVocabularySchema",
    "get_vocabulary_schema_info",
    "build_market_structure_vocabulary_v1",
    "get_vocabulary_builder_v1_info",
    "validate_vocabulary_record",
]
