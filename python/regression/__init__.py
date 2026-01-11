#!/usr/bin/env python3
"""
PR117: v1.0 Golden Regression Harness v1 (READ-ONLY)

Purpose:
    Golden regression testing for structural determinism.
    Harness = Determinism Proof (not optimization/profit test).

Exports:
    - run_golden_regression_v1: Core regression harness function
    - get_golden_regression_harness_v1_info: Harness metadata
"""

from .v10_golden_regression_harness_v1 import (
    run_golden_regression_v1,
    get_golden_regression_harness_v1_info,
)

__all__ = [
    "run_golden_regression_v1",
    "get_golden_regression_harness_v1_info",
]
