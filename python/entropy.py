# python/entropy.py
from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class EntropyResult:
    """
    v0.1 output schema (matches logging):
    - ea_norm, es_norm in [0, 1]
    - composite_percent in [0, 100]
    - composite_bp in [0, 10000]
    """
    ea_norm: float
    es_norm: float
    composite_percent: float
    composite_bp: int


def _clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


class CompositeEntropy:
    """
    Meridian v0.1 Composite Entropy (deterministic)
    - EA: amplitude "surprise" proxy (normalized dispersion of returns)
    - ES: structure "break" proxy (normalized sign-instability / alternation)

    NOTE:
    This is a v0.1 reference implementation.
    You can later replace internals while preserving:
      - output range [0,1]
      - composite = max(EA, ES)
      - bp scaling
    """

    def __init__(self, window: int):
        if window < 3:
            raise ValueError("window must be >= 3")
        self.window = int(window)

    def compute(self, prices: List[float]) -> EntropyResult:
        if len(prices) < self.window + 1:
            # not enough data => fully explainable by definition in v0.1
            return EntropyResult(ea_norm=0.0, es_norm=0.0, composite_percent=0.0, composite_bp=0)

        p = np.asarray(prices[-(self.window + 1):], dtype=float)
        # simple returns
        r = (p[1:] / p[:-1]) - 1.0

        # --- EA (Amplitude) ---
        # normalize by a robust scale to map into [0,1] without tuning:
        # use tanh on z-like value
        sigma = float(np.std(r))  # dispersion proxy
        # map: sigma 0.. ~ => 0..1 smoothly
        ea = float(np.tanh(sigma * 50.0))  # 50 is a gentle scaler for crypto-like returns

        # --- ES (Structure) ---
        # measure alternation / sign instability:
        # count sign changes in returns
        signs = np.sign(r)
        # treat zeros as previous sign to reduce noise
        for i in range(1, len(signs)):
            if signs[i] == 0:
                signs[i] = signs[i - 1]
        sign_changes = np.sum(signs[1:] * signs[:-1] < 0)
        # normalize by maximum possible changes (len-1)
        es = float(sign_changes / max(1, len(signs) - 1))

        ea_norm = _clamp01(ea)
        es_norm = _clamp01(es)

        comp = max(ea_norm, es_norm)
        comp_bp = int(round(comp * 10000))
        comp_pct = comp * 100.0

        return EntropyResult(
            ea_norm=ea_norm,
            es_norm=es_norm,
            composite_percent=float(comp_pct),
            composite_bp=int(comp_bp),
        )
