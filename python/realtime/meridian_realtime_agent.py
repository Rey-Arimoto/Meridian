# python/realtime/meridian_realtime_agent.py
from datetime import datetime
import time
import sys
import pandas as pd

from config import (
    SYMBOL,
    MA_PERIOD,
    ENTROPY_WINDOW,
    CRITICAL_ENTROPY_BP,
    INTERVAL_SECONDS,
    ENV_NAME,
    AGENT_VERSION,
    OVERLAY_ENABLED,
    COOLDOWN_SECONDS,
    MAX_DW_PER_STEP,
    MIN_DW_IGNORE,
    V0_2_REQUIRED_COLUMNS,
)

from entropy import CompositeEntropy
from market.price_feed import fetch_price_with_time
from core.logging_schema import append_log_row
from core.risk_guard import RiskGuard
from core.meridian_policy_core import MeridianPolicyCore
from core.safety_overlay import SafetyOverlay
from brokers.paper_broker import PaperBroker
from core.intent import classify_intent_from_fields  # PR15A: Intent classification
from confidence.confidence_evaluator import evaluate_confidence  # PR24: Confidence evaluation hook
from confidence.confidence_observation import build_confidence_observation  # PR26: Observation wiring
from confidence.confidence_reason_compliance import validate_confidence_reason  # PR32: Compliance guard wiring


def validate_log_row_v0_2(row_dict):
    """
    PR13B: Validate that log row contains all v0.2 required columns.

    Args:
        row_dict: dict to be written to log

    Returns:
        (ok: bool, missing: list) - ok=True if all required columns present,
                                     missing=list of missing column names

    This is a fail-fast guard to prevent generating incomplete logs
    that would be rejected by PR8B integrity gate.
    """
    missing = [col for col in V0_2_REQUIRED_COLUMNS if col not in row_dict]
    return (len(missing) == 0, missing)


def should_freeze(entropy_bp: int, threshold_bp: int) -> bool:
    return int(entropy_bp) >= int(threshold_bp)


class RealTimeMeridianAgent:
    """
    Meridian v0.1 (paper):
      - Observe: price
      - Compute: MA, deviation, composite entropy (EA/ES), bp scaling
      - Enforce: constitutional freeze if entropy_bp >= threshold
      - Act: paper rebalance to target weight (simple policy)
      - Log: one CSV row per tick (auditable)
    """

    def __init__(self):
        self.price_history = []
        self.entropy_calc = CompositeEntropy(window=ENTROPY_WINDOW)
        self.guard = RiskGuard()
        self.core = MeridianPolicyCore()
        self.overlay = SafetyOverlay(
            enabled=OVERLAY_ENABLED,
            cooldown_seconds=COOLDOWN_SECONDS,
            max_dw_per_step=MAX_DW_PER_STEP,
            min_dw_ignore=MIN_DW_IGNORE,
        )
        self.broker = PaperBroker(init_cash=1.0)

    def run(self):
        print("--- Meridian v0.1 (paper) / Composite Entropy ---")
        while True:
            now = datetime.utcnow()

            # (1) observe price
            price, _price_ts = fetch_price_with_time()
            self.price_history.append(float(price))

            # wait until MA is available
            if len(self.price_history) < MA_PERIOD:
                time.sleep(INTERVAL_SECONDS)
                continue

            # (2) compute MA & deviation
            s = pd.Series(self.price_history, dtype=float)
            ma = float(s.rolling(MA_PERIOD).mean().iloc[-1])
            deviation = ((price - ma) / ma) * 100 if ma != 0 else 0.0

            # (3) compute entropy (canonical output in bp)
            er = self.entropy_calc.compute(self.price_history)
            entropy_bp = int(er.composite_bp)
            entropy_pct = float(er.composite_percent)

            vol_band = self.core.classify_volatility_band(entropy_bp)
            entropy_state = self.core.classify_entropy_state(entropy_bp)

            # (4) constitutional freeze
            self.guard.clear()
            freeze = should_freeze(entropy_bp, CRITICAL_ENTROPY_BP)

            # Get current weight before decision
            current_w = self.broker.current_weight()

            if freeze:
                self.guard.state.last_guard_type = "entropy_freeze"
                self.guard.state.emergency_reason = f"{entropy_bp}bp >= {CRITICAL_ENTROPY_BP}bp"

                # Apply overlay (will respect emergency freeze)
                overlay_result = self.overlay.apply(
                    decision=None,
                    current_weight=current_w,
                    now_utc=now,
                    emergency_freeze=True,
                )

                final_w = overlay_result.final_target_weight
                action = "FREEZE"
                regime_str = "REGIME_TRANSITION"
                base_action_str = "PAUSE"
                decision_reason = f"EMERGENCY_FREEZE | overlay={overlay_result.overlay_rule}"
                overlay_rule = overlay_result.overlay_rule
            else:
                # v0.2: Constitutional regime-first decision
                decision = self.core.decide(entropy_bp, current_w)

                # PR5: Apply safety overlay
                overlay_result = self.overlay.apply(
                    decision=decision,
                    current_weight=current_w,
                    now_utc=now,
                    emergency_freeze=False,
                )

                final_w = overlay_result.final_target_weight
                regime_str = decision.regime.value
                base_action_str = decision.base_action.value
                decision_reason = f"{decision.reason} | overlay={overlay_result.overlay_rule}"
                overlay_rule = overlay_result.overlay_rule

                dw = self.broker.rebalance_to_target_weight(final_w, float(price))
                action = "BUY" if dw > 0.02 else "SELL" if dw < -0.02 else "HOLD"

            eq = self.broker.equity(float(price))

            # (5) print + log
            print(
                f"[{now}] P={price:.4f} Dev={deviation:+.2f}% "
                f"E={entropy_pct:6.2f}%({entropy_bp}bp) EA={er.ea_norm:.3f} ES={er.es_norm:.3f} "
                f"Band={vol_band} State={entropy_state} "
                f"Regime={regime_str} BaseAction={base_action_str} "
                f"Overlay={overlay_rule} "
                f"Act={action} w*={final_w:.2f} Eq={eq:.4f} Guard={self.guard.state.last_guard_type}"
            )

            # PR15A: Classify Intent (Layer A - decision time)
            intent_primary, intent_reason = classify_intent_from_fields(
                regime=regime_str,
                base_action=base_action_str,
                decision_reason=decision_reason,
                action_label=action
            )

            # PR26: Build observation context for Confidence evaluation
            # Observation wiring enforces PR25 source category boundaries
            confidence_observation = build_confidence_observation(
                intent_primary=intent_primary,
                regime=regime_str,
                base_action=base_action_str,
                overlay_rule=overlay_rule,
                entropy_bp=entropy_bp,
            )
            confidence_value, confidence_reason = evaluate_confidence(confidence_observation)

            # PR32: Compliance guard wiring (READ-ONLY, warning-only)
            compliance_warnings = validate_confidence_reason(confidence_reason)
            if compliance_warnings:
                # Output warnings (never stops execution, never affects behavior)
                ts_str = now.isoformat() if 'now' in locals() else ""
                print(f"[WARNING][PR31] confidence_reason non-compliant: {' | '.join(compliance_warnings)} (ts={ts_str})")

            # PR13B: Build row dict and validate before logging
            row_dict = {
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
                "target_weight": float(final_w),  # PR5: final weight after overlay
                "equity": float(eq),

                "guard_type": self.guard.state.last_guard_type,
                "guard_reason": self.guard.state.emergency_reason,

                # v0.2 Constitutional decision fields (PR3 + PR5 overlay appended)
                "regime": regime_str,
                "base_action": base_action_str,
                "decision_reason": decision_reason,  # Includes overlay rule

                # PR15A: v0.3 Intent fields (Layer A - first-class citizen)
                "intent_primary": intent_primary,
                "intent_reason": intent_reason,

                # PR24: v0.4 Confidence fields (evaluated via hook)
                "confidence_value": confidence_value,
                "confidence_reason": confidence_reason,
            }

            # PR13B: Validate row before writing (fail-fast at source)
            ok, missing = validate_log_row_v0_2(row_dict)
            if not ok:
                print("=" * 70)
                print("FATAL ERROR: Log row missing v0.2 required columns")
                print("=" * 70)
                print(f"Missing columns: {', '.join(missing)}")
                print("")
                print("This is a code bug. The agent must always generate")
                print("v0.2-compliant log rows with regime, base_action, decision_reason.")
                print("")
                print("Stopping agent to prevent generating invalid logs.")
                print("=" * 70)
                sys.exit(1)

            append_log_row(row_dict)

            time.sleep(INTERVAL_SECONDS)
