from datetime import datetime
import time
import pandas as pd

from config import (
    MA_PERIOD,
    ENTROPY_WINDOW,
    CRITICAL_ENTROPY_BP,
    INTERVAL_SECONDS,
    ENV_NAME,
    AGENT_VERSION,
    SYMBOL,
)
from entropy import EntropyCalculator, EntropyConfig, should_freeze
from market.price_feed import fetch_price_with_time
from core.logging_schema import append_log_row
from core.risk_guard import RiskGuard
from core.meridian_policy_core import MeridianPolicyCore
from brokers.paper_broker import PaperBroker


class RealTimeMeridianAgent:
    def __init__(self):
        self.core = MeridianPolicyCore()
        self.guard = RiskGuard()
        self.broker = PaperBroker(init_cash=1.0)
        self.price_history: list[float] = []

        self.entropy_calc = EntropyCalculator(
            EntropyConfig(
                window=ENTROPY_WINDOW,
                w_amplitude=0.4,
                w_sign=0.6,
                amp_norm_lookback=200,
                amp_norm_p_low=0.05,
                amp_norm_p_high=0.95,
            )
        )

    def run(self):
        print("--- Meridian v0.1 (paper) / Composite Entropy ---")
        while True:
            now = datetime.utcnow()
            self.guard.clear()

            price, _price_ts = fetch_price_with_time()
            self.price_history.append(float(price))

            if len(self.price_history) < MA_PERIOD:
                time.sleep(INTERVAL_SECONDS)
                continue

            s = pd.Series(self.price_history, dtype=float)
            ma = float(s.rolling(MA_PERIOD).mean().iloc[-1])
            deviation = ((price - ma) / ma) * 100 if ma != 0 else 0.0

            er = self.entropy_calc.compute(self.price_history)
            entropy_bp = int(er.composite_bp)
            entropy_pct = float(er.composite_percent)

            vol_band = self.core.classify_volatility_band(entropy_bp)
            entropy_state = self.core.classify_entropy_state(entropy_bp)

            freeze = should_freeze(entropy_bp, CRITICAL_ENTROPY_BP)
            if freeze:
                self.guard.state.last_guard_type = "entropy_freeze"
                self.guard.state.emergency_reason = f"{entropy_bp}bp >= {CRITICAL_ENTROPY_BP}bp"
                target_w = 0.0
                action = "FREEZE"
            else:
                target_w = self.core.decide_target_weight(entropy_bp)
                dw = self.broker.rebalance_to_target_weight(target_w, float(price))
                action = "BUY" if dw > 0.02 else "SELL" if dw < -0.02 else "HOLD"

            eq = self.broker.equity(float(price))

            print(
                f"[{now}] P={price:.4f} Dev={deviation:+.2f}% "
                f"E={entropy_pct:6.2f}%({entropy_bp}bp) EA={er.ea_norm:.3f} ES={er.es_norm:.3f} "
                f"Band={vol_band} State={entropy_state} "
                f"Act={action} w*={target_w:.2f} Eq={eq:.4f} Guard={self.guard.state.last_guard_type}"
            )

            append_log_row({
                "timestamp_utc": now.isoformat(),
                "symbol": SYMBOL,
                "env": ENV_NAME,
                "agent_version": AGENT_VERSION,
                "price": float(price),
                "ma": float(ma),
                "deviation_pct": float(deviation),
                "entropy_pct": float(entropy_pct),
                "entropy_bp": int(entropy_bp),
                "ea_norm": float(er.ea_norm),
                "es_norm": float(er.es_norm),
                "volatility_band": vol_band,
                "entropy_state": entropy_state,
                "action_label": action,
                "target_weight": float(target_w),
                "equity": float(eq),
                "guard_type": self.guard.state.last_guard_type,
                "guard_reason": self.guard.state.emergency_reason,
            })

            time.sleep(INTERVAL_SECONDS)
