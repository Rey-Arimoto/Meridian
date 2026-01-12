#!/usr/bin/env python3
"""
PR128: Eligibility Constitutional Guard (READ-ONLY)

Enforces:
- no token literals
- no numeric patterns
- no addresses
- no execution/trading vocabulary
- no prescriptive coupling ("eligible therefore ...")
Warning-only: returns list of warnings; never raises.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List

# Minimal local forbidden set (keep conservative)
FORBIDDEN_VOCAB = {
    "swap", "trade", "buy", "sell", "execute", "sign", "transfer", "broadcast", "submit",
    "should", "must", "recommend", "therefore", "so", "hence",
}

TOKEN_LITERALS = {"SUI", "USDC", "BTC", "ETH"}
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{6,}\b")
NUMERIC_RE = re.compile(r"(?<![A-Za-z])\d+(\.\d+)?(?![A-Za-z])")

COUPLING_RE = re.compile(
    r"\b(eligible|ineligible)\b.{0,40}\b(so|therefore|hence|thus)\b",
    re.IGNORECASE | re.DOTALL,
)

def _flatten_text(rec: Dict[str, Any]) -> str:
    # Only fields that can contain text.
    parts: List[str] = []
    for k in ["v12_elig_summary"]:
        v = rec.get(k, "")
        if isinstance(v, str):
            parts.append(v)
    # signals: labels only, but still text
    sig = rec.get("v12_elig_signals", {})
    if isinstance(sig, dict):
        for _, v in sig.items():
            if isinstance(v, str):
                parts.append(v)
    return " ".join(parts)

def check_eligibility_record(rec: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    try:
        text = _flatten_text(rec)

        if any(t in text for t in TOKEN_LITERALS):
            warnings.append("token literal detected in eligibility record text.")

        if ADDRESS_RE.search(text):
            warnings.append("address-like pattern detected in eligibility record text.")

        if NUMERIC_RE.search(text):
            warnings.append("numeric pattern detected in eligibility record text.")

        lower = text.lower()
        for w in FORBIDDEN_VOCAB:
            if re.search(rf"\b{re.escape(w)}\b", lower):
                # allow the word "therefore" to be caught here too; redundancy is fine.
                warnings.append(f"forbidden vocabulary detected: {w}")
                break

        if COUPLING_RE.search(text):
            warnings.append("eligibility coupling pattern detected (eligible therefore...).")

        return warnings

    except Exception as e:
        return [f"guard exception: {type(e).__name__}"]
