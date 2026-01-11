#!/usr/bin/env python3
"""
PR118: v1.0 CLI Demo v1 (READ-ONLY)

Purpose:
    One-command end-to-end pipeline execution with human-readable digest.
    CLI = Display (not instruction/recommendation).

Exports:
    - render_digest: Core digest rendering function
    - get_digest_renderer_v1_info: Renderer metadata
    - validate_cli_output: Constitutional guard for CLI output
"""

from .v10_digest_renderer_v1 import (
    render_digest,
    get_digest_renderer_v1_info,
)
from .v10_cli_constitutional_guard import (
    validate_cli_output,
)

__all__ = [
    "render_digest",
    "get_digest_renderer_v1_info",
    "validate_cli_output",
]
