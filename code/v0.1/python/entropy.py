"""
Meridian Entropy Module (v0.1/v0.2 compatible)
=============================================

This file implements the Entropy model specified in `docs/entropy_spec.md`.

Key guarantees (constitutional):
- Deterministic: same inputs -> same outputs
- Composable: amplitude entropy + sign entropy -> composite entropy
- Action-invalidating: entropy_bp >= CRITICAL_ENTROPY forbids execution
- Integer thresholds: compare basis points (bp) only (no float thresholding)

Terminology:
- EA: Amplitude Entropy (magnitude instability)
- ES: Sign Entropy (directional meaning collapse)
- E : Composite Entropy = wA * EA_norm + wS * ES_norm

Outputs:
- percent: 0.00 ~ 100.00
- basis points: 0 ~ 10000 (int)
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt
from typing import List, Optional, Tuple


# -----------------------------
# Utility: deterministic helpers
# -----------------------------

def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _mean(xs: List[float]) -> float:
    if not xs:
        return 0.0
    return sum(xs) / float(len(xs))


def _std_population(xs: List[float]) -> float:
    """
    Population standard deviation (ddof=0) for determinism.
    Using ddof=1 introduces edge-case variability for small windows.
    """
    n = len(xs)
    if n <= 1:
        return 0.0
    m = _mean(xs)
    var = sum((x - m) ** 2 for x in xs) / float(n)
    return sqrt(var)


def _log_returns(prices: List[float]) -> List[float]:
    """
    Compute log returns: r_t = ln(p_t / p_{t-1})
    Deterministic; ignores non-positive prices defensively.
    """
    rets: List[float] = []
    for i in range(1, len(prices)):
        p0 = prices[i - 1]
        p1 = prices[i]
        if p0 <= 0 or p1 <= 0:
            # invalid price -> treat as no return (deterministic fallback)
            rets.append(0.0)
        else:
            rets.append(log(p1 / p0))
    return rets


def _binary_entropy(p: float) -> float:
    """
    Binary entropy H(p) in bits, normalized to [0,1] by dividing by 1 (since max is 1 bit).
    H(p) = -p log2 p - (1-p) log2 (1-p)
    Edge-safe and deterministic.
    """
    p = _clamp(p, 0.0, 1.0)
    if p <= 0.0 or p >= 1.0:
        return 0.0
    # use natural log; convert to log2 by / ln(2)
    ln2 = log(2.0)
    return (-(p * log(p) + (1.0 - p) * log(1.0 - p)) / ln2)  # already in [0,1]


def _percentile(xs: List[float], q: float) -> float:
    """
    Deterministic percentile with linear interpolation.
    q in [0,1]. Returns 0 for empty list.

    Example: q=0.05 -> 5th percentile.
    """
    if not xs:
        return 0.0
    q = _clamp(q, 0.0, 1.0)
    ys = sorted(xs)
    n = len(ys)
    if n == 1:
        return ys[0]
    # position in [0, n-1]
    pos = q * (n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return ys[lo] * (1.0 - frac) + ys[hi] * frac


# -----------------------------
# Config + Output types
# -----------------------------

@dataclass(frozen=True)
class EntropyConfig:
    """
    Parameters aligned with docs/entropy_spec.md.

    window:
        Rolling window length for entropy computation.
        Requires at least window+1 prices to compute window returns.

    w_amplitude, w_sign:
        Composite weights (must sum to 1.0). Defaults: 0.4 / 0.6.

    amp_norm_lookback:
        Lookback length (in EA samples) to normalize EA via robust percentile bounds.
        This is "rolling robust min/max" in the spec.

    amp_norm_p_low, amp_norm_p_high:
        Robust bounds for EA normalization (e.g., 5th and 95th percentile).

    amp_floor:
        Small positive floor to prevent division by zero in normalization.

    Notes on determinism:
    - All operations are pure functions of input arrays.
    - No randomness, no time-dependent data.
    """
    window: int = 10

    w_amplitude: float = 0.4
    w_sign: float = 0.6

    amp_norm_lookback: int = 200
    amp_norm_p_low: float = 0.05
    amp_norm_p_high: float = 0.95
    amp_floor: float = 1e-12


@dataclass(frozen=True)
class EntropyResult:
    """
    All normalized values are in [0,1].
    Composite entropy is provided as both percent and basis points (int).
    """
    ea_norm: float
    es_norm: float
    composite_norm: float
    composite_percent: float
    composite_bp: int

    # raw intermediates (useful for debugging/logging)
    ea_raw: float
    sign_p_pos: float
    window_returns: int


# -----------------------------
# Core implementation
# -----------------------------

class EntropyCalculator:
    """
    Stateful helper for rolling EA normalization.

    Why stateful?
    - EA normalization uses a rolling history of EA samples (robust bounds).
    - This mirrors "rolling robust min/max" in the spec.
    - State is explicit and loggable.

    You can also use `compute_once(...)` for pure/stateless usage.
    """

    def __init__(self, config: Optional[EntropyConfig] = None):
        self.config = config or EntropyConfig()
        self._validate_config()
        self._ea_history: List[float] = []

    def _validate_config(self) -> None:
        c = self.config
        if c.window < 2:
            raise ValueError("window must be >= 2")
        if c.amp_norm_lookback < 10:
            # keep it sane; still deterministic
            raise ValueError("amp_norm_lookback should be >= 10")
        # weight sanity (allow small float error)
        s = c.w_amplitude + c.w_sign
        if abs(s - 1.0) > 1e-9:
            raise ValueError("w_amplitude + w_sign must equal 1.0")
        if not (0.0 <= c.amp_norm_p_low < c.amp_norm_p_high <= 1.0):
            raise ValueError("amp_norm_p_low < amp_norm_p_high and both in [0,1]")

    @property
    def ea_history_len(self) -> int:
        return len(self._ea_history)

    def compute(self, prices: List[float]) -> EntropyResult:
        """
        Compute entropy for the latest window, updating EA history for normalization.

        Requires >= window+1 prices (to create `window` returns).
        """
        res = self.compute_once(
            prices=prices,
            config=self.config,
            ea_history=self._ea_history,
        )
        # append latest EA sample after computing
        self._ea_history.append(res.ea_raw)
        # maintain fixed lookback for determinism and bounded memory
        if len(self._ea_history) > self.config.amp_norm_lookback:
            self._ea_history = self._ea_history[-self.config.amp_norm_lookback :]
        return res

    @staticmethod
    def compute_once(
        prices: List[float],
        config: Optional[EntropyConfig] = None,
        ea_history: Optional[List[float]] = None,
    ) -> EntropyResult:
        """
        Stateless compute that can optionally take a prior EA history for normalization.
        If `ea_history` is None or too short, EA normalization falls back to a safe mapping.

        This function is deterministic for any given (prices, config, ea_history).
        """
        c = config or EntropyConfig()
        ea_hist = list(ea_history) if ea_history is not None else []

        # --- ensure enough data
        # Need window+1 prices to compute window returns
        if len(prices) < c.window + 1:
            # Not enough data -> return neutral-high caution (entropy mid/high).
            # Deterministic fallback: composite = 1.0 (max) to forbid action early.
            return EntropyResult(
                ea_norm=1.0,
                es_norm=1.0,
                composite_norm=1.0,
                composite_percent=100.0,
                composite_bp=10000,
                ea_raw=0.0,
                sign_p_pos=0.5,
                window_returns=0,
            )

        # Use latest window+1 prices
        window_prices = prices[-(c.window + 1) :]
        rets = _log_returns(window_prices)  # length = window
        n_rets = len(rets)

        # -------------------------
        # EA: Amplitude Entropy (raw)
        # -------------------------
        abs_rets = [abs(r) for r in rets]
        ea_raw = _std_population(abs_rets)

        # -------------------------
        # ES: Sign Entropy (normalized already)
        # -------------------------
        # Define sign: positive if r > 0, negative otherwise (including 0)
        # This keeps it deterministic and avoids special-casing near-zero noise.
        pos = sum(1 for r in rets if r > 0.0)
        p_pos = pos / float(n_rets) if n_rets > 0 else 0.5
        es_norm = _binary_entropy(p_pos)  # in [0,1]

        # -------------------------
        # Normalize EA -> EA_norm in [0,1]
        # Robust percentile bounds from history (rolling robust min/max).
        # -------------------------
        ea_norm = EntropyCalculator._normalize_amplitude_entropy(ea_raw, ea_hist, c)

        # -------------------------
        # Composite entropy in [0,1]
        # -------------------------
        e = _clamp(c.w_amplitude * ea_norm + c.w_sign * es_norm, 0.0, 1.0)

        # Convert to percent and bp (integer comparison only)
        percent = e * 100.0
        bp = int(round(e * 10000.0))
        bp = max(0, min(10000, bp))

        return EntropyResult(
            ea_norm=ea_norm,
            es_norm=es_norm,
            composite_norm=e,
            composite_percent=percent,
            composite_bp=bp,
            ea_raw=ea_raw,
            sign_p_pos=p_pos,
            window_returns=n_rets,
        )

    @staticmethod
    def _normalize_amplitude_entropy(ea_raw: float, ea_history: List[float], c: EntropyConfig) -> float:
        """
        Normalize EA using robust percentile bounds.
        If history is insufficient, use a conservative mapping.

        Spec intent:
        - percentile-based bounds to avoid single-spike distortion
        - clipped defensively to preserve determinism
        """
        ea_raw = max(ea_raw, 0.0)

        # If not enough history, fall back to a conservative squashing.
        # This prevents overconfidence early and remains deterministic.
        if len(ea_history) < 20:
            # Simple monotonic mapping: ea_raw / (ea_raw + k)
            # Choose k as a small constant that keeps early EA_norm reasonably high.
            k = 0.01  # domain-dependent; acceptable as constitutional default
            return _clamp(ea_raw / (ea_raw + k), 0.0, 1.0)

        # Use history (bounded by amp_norm_lookback externally)
        lo = _percentile(ea_history, c.amp_norm_p_low)
        hi = _percentile(ea_history, c.amp_norm_p_high)

        # Defensive: ensure span > 0
        span = max(hi - lo, c.amp_floor)

        # Normalize and clamp
        x = (ea_raw - lo) / span
        return _clamp(x, 0.0, 1.0)


# -----------------------------
# Convenience: Freeze check
# -----------------------------

def should_freeze(entropy_bp: int, critical_entropy_bp: int) -> bool:
    """
    Constitutional check: action is forbidden when entropy_bp >= critical_entropy_bp.
    Use integers only.
    """
    return int(entropy_bp) >= int(critical_entropy_bp)


# -----------------------------
# Minimal self-test / demo
# -----------------------------

if __name__ == "__main__":
    # Demo: compute entropy on synthetic prices
    # (In production, you feed real price history.)
    import random

    random.seed(0)  # deterministic demo only

    prices = [100.0]
    for _ in range(300):
        # mild random walk for demo; deterministic due to seed
        prices.append(prices[-1] * (1.0 + random.uniform(-0.005, 0.005)))

    cfg = EntropyConfig(window=10, w_amplitude=0.4, w_sign=0.6)
    calc = EntropyCalculator(cfg)

    for i in range(50, len(prices), 50):
        r = calc.compute(prices[: i + 1])
        print(
            f"t={i:4d} EA_norm={r.ea_norm:.3f} ES_norm={r.es_norm:.3f} "
            f"E={r.composite_percent:6.2f}% ({r.composite_bp:5d}bp) "
            f"freeze={should_freeze(r.composite_bp, 9000)}"
        )
