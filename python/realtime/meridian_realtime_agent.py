# python/realtime/meridian_realtime_agent.py
from datetime import datetime
import time
import sys
import json
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
    DECISION_ENGINE_VERSION,  # PR43: Engine selector
    DECISION_ENGINE_SHADOW_MODE,  # PR44: Shadow mode
    DECISION_ENGINE_DIFF_LOGGING,  # PR45: Diff logging
    DECISION_ENGINE_DIFF_SEMANTICS,  # PR46: Semantics tagging
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
from intelligence.intelligence_decision_engine_v1 import generate_decision_record_v1  # PR41: Decision record generation v1
from intelligence.intelligence_decision_engine_v2 import generate_decision_record_v2  # PR42: Decision record generation v2
from intelligence.intelligence_decision_record_compliance import validate_decision_record_full  # PR41: Decision record compliance guard


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
            # PR32B: Normalized warning format
            compliance_warnings = validate_confidence_reason(confidence_reason)
            if compliance_warnings:
                # Output warnings (never stops execution, never affects behavior)
                ts_str = now.isoformat() if 'now' in locals() else ""
                print(f"[WARNING][PR31][confidence_reason] violations={' | '.join(compliance_warnings)} ts={ts_str}")

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

                # PR33: Confidence Reason Snapshot Logging (READ-ONLY)
                "confidence_reason_version": "v0.4",
                "confidence_reason_generated_at": now.isoformat(),
            }

            # PR44: v0.5 Decision Engine Shadow Mode (Dual Record Logging, READ-ONLY)
            try:
                # PR43/PR44: Select decision engine based on config
                primary_engine = DECISION_ENGINE_VERSION
                shadow_mode = DECISION_ENGINE_SHADOW_MODE

                # PR44: Determine shadow engine (opposite of primary)
                if primary_engine == "v1":
                    shadow_engine = "v2"
                elif primary_engine == "v2":
                    shadow_engine = "v1"
                else:
                    # Invalid primary engine: fallback to v1 primary, v2 shadow
                    print(f"[WARNING][PR44] Invalid DECISION_ENGINE_VERSION '{primary_engine}', falling back to v1")
                    primary_engine = "v1"
                    shadow_engine = "v2"

                # PR44: Generate PRIMARY decision record (PR43 logic)
                if primary_engine == "v2":
                    primary_record = generate_decision_record_v2(row_dict)
                    primary_engine_used = "v2"
                else:  # v1
                    primary_record = generate_decision_record_v1(row_dict)
                    primary_engine_used = "v1"

                # PR44: Record primary engine and fields
                row_dict["v5_decision_engine"] = primary_engine_used
                row_dict["v5_decision_action"] = primary_record.get("decision_action", "UNKNOWN")
                row_dict["v5_decision_reason"] = primary_record.get("decision_reason", "")

                # PR41A: decision_inputs in both formats
                primary_inputs_list = primary_record.get("decision_inputs", [])
                row_dict["v5_decision_inputs"] = ",".join(primary_inputs_list) if primary_inputs_list else ""
                row_dict["v5_decision_inputs_json"] = json.dumps(primary_inputs_list)

                # PR41A: decision_version always "v0.5"
                row_dict["v5_decision_version"] = "v0.5"
                row_dict["v5_decision_generated_at"] = primary_record.get("decision_generated_at", "")

                # PR41A/PR44: Always validate primary decision record (PR39 compliance guard)
                primary_compliance_warnings = validate_decision_record_full(primary_record, "meridian_realtime_agent")
                if primary_compliance_warnings:
                    ts_str = now.isoformat()
                    print(f"[WARNING][PR39][decision_record][primary] violations={' | '.join(primary_compliance_warnings)} ts={ts_str}")

                # PR44: Generate SHADOW decision record (only if shadow mode enabled)
                if shadow_mode:
                    try:
                        # PR44: Generate shadow record using opposite engine
                        if shadow_engine == "v2":
                            shadow_record = generate_decision_record_v2(row_dict)
                            shadow_engine_used = "v2"
                        else:  # v1
                            shadow_record = generate_decision_record_v1(row_dict)
                            shadow_engine_used = "v1"

                        # PR44: Record shadow engine and fields
                        row_dict["v5_shadow_decision_engine"] = shadow_engine_used
                        row_dict["v5_shadow_decision_action"] = shadow_record.get("decision_action", "UNKNOWN")
                        row_dict["v5_shadow_decision_reason"] = shadow_record.get("decision_reason", "")

                        # PR41A/PR44: shadow decision_inputs in both formats
                        shadow_inputs_list = shadow_record.get("decision_inputs", [])
                        row_dict["v5_shadow_decision_inputs"] = ",".join(shadow_inputs_list) if shadow_inputs_list else ""
                        row_dict["v5_shadow_decision_inputs_json"] = json.dumps(shadow_inputs_list)

                        # PR41A/PR44: shadow decision_version always "v0.5"
                        row_dict["v5_shadow_decision_version"] = "v0.5"
                        row_dict["v5_shadow_decision_generated_at"] = shadow_record.get("decision_generated_at", "")

                        # PR41A/PR44: Always validate shadow decision record (PR39 compliance guard)
                        shadow_compliance_warnings = validate_decision_record_full(shadow_record, "meridian_realtime_agent")
                        if shadow_compliance_warnings:
                            ts_str = now.isoformat()
                            print(f"[WARNING][PR39][decision_record][shadow] violations={' | '.join(shadow_compliance_warnings)} ts={ts_str}")

                    except Exception as shadow_e:
                        # PR44: Shadow failure must not stop execution (warning-only)
                        print(f"[WARNING][PR44][shadow_record] Failed to generate shadow record: {shadow_e}")
                        # PR44: Shadow safe defaults
                        row_dict["v5_shadow_decision_engine"] = "UNKNOWN"
                        row_dict["v5_shadow_decision_action"] = "UNKNOWN"
                        row_dict["v5_shadow_decision_reason"] = ""
                        row_dict["v5_shadow_decision_inputs"] = ""
                        row_dict["v5_shadow_decision_inputs_json"] = "[]"
                        row_dict["v5_shadow_decision_version"] = "v0.5"
                        row_dict["v5_shadow_decision_generated_at"] = now.isoformat()

            except Exception as e:
                # PR44: Primary decision record generation must never stop execution (warning-only)
                print(f"[WARNING][PR44][decision_record_wiring] Failed to generate primary decision record: {e}")
                # PR44: Try fallback to v1 if primary v2 failed
                try:
                    if primary_engine == "v2":
                        print(f"[WARNING][PR44] Attempting fallback to v1 after primary v2 failure")
                        primary_record = generate_decision_record_v1(row_dict)
                        primary_engine_used = "v1"
                        row_dict["v5_decision_engine"] = primary_engine_used
                        row_dict["v5_decision_action"] = primary_record.get("decision_action", "UNKNOWN")
                        row_dict["v5_decision_reason"] = primary_record.get("decision_reason", "")
                        primary_inputs_list = primary_record.get("decision_inputs", [])
                        row_dict["v5_decision_inputs"] = ",".join(primary_inputs_list) if primary_inputs_list else ""
                        row_dict["v5_decision_inputs_json"] = json.dumps(primary_inputs_list)
                        row_dict["v5_decision_version"] = "v0.5"
                        row_dict["v5_decision_generated_at"] = primary_record.get("decision_generated_at", "")
                    else:
                        raise  # Re-raise if v1 itself failed
                except Exception as fallback_e:
                    # PR44: Even fallback failed, use safe defaults
                    print(f"[WARNING][PR44] Primary fallback also failed: {fallback_e}")
                    row_dict["v5_decision_engine"] = "UNKNOWN"
                    row_dict["v5_decision_action"] = "UNKNOWN"
                    row_dict["v5_decision_reason"] = ""
                    row_dict["v5_decision_inputs"] = ""
                    row_dict["v5_decision_inputs_json"] = "[]"
                    row_dict["v5_decision_version"] = "v0.5"
                    row_dict["v5_decision_generated_at"] = now.isoformat()

            # PR45: v0.5 Decision Engine Shadow Diff Logging (READ-ONLY, non-evaluative)
            try:
                diff_logging_enabled = DECISION_ENGINE_DIFF_LOGGING

                if not diff_logging_enabled:
                    # PR45: Diff logging disabled
                    row_dict["v5_decision_diff_mode"] = "OFF"
                    row_dict["v5_decision_diff_status"] = "UNAVAILABLE"
                    row_dict["v5_decision_diff_pair"] = "UNKNOWN"
                    row_dict["v5_decision_diff_summary"] = "diff logging disabled."

                elif not shadow_mode:
                    # PR45: Diff logging enabled but shadow mode disabled
                    row_dict["v5_decision_diff_mode"] = "ON"
                    row_dict["v5_decision_diff_status"] = "UNAVAILABLE"
                    row_dict["v5_decision_diff_pair"] = "UNKNOWN"
                    row_dict["v5_decision_diff_summary"] = "shadow record not present."

                else:
                    # PR45: Diff logging enabled and shadow mode enabled
                    row_dict["v5_decision_diff_mode"] = "ON"

                    # PR45: Determine diff pair (which engines are being compared)
                    primary_engine_val = row_dict.get("v5_decision_engine", "UNKNOWN")
                    shadow_engine_val = row_dict.get("v5_shadow_decision_engine", "UNKNOWN")

                    if primary_engine_val == "v1" and shadow_engine_val == "v2":
                        diff_pair = "v1_vs_v2"
                    elif primary_engine_val == "v2" and shadow_engine_val == "v1":
                        diff_pair = "v2_vs_v1"
                    else:
                        diff_pair = "UNKNOWN"

                    row_dict["v5_decision_diff_pair"] = diff_pair

                    # PR45: Determine diff status (aligned/diverged/unavailable)
                    primary_action = row_dict.get("v5_decision_action", "")
                    shadow_action = row_dict.get("v5_shadow_decision_action", "")

                    # PR45: Check if both actions are valid (non-empty, non-UNKNOWN)
                    primary_valid = primary_action and primary_action != "UNKNOWN"
                    shadow_valid = shadow_action and shadow_action != "UNKNOWN"

                    if primary_valid and shadow_valid:
                        if primary_action == shadow_action:
                            diff_status = "ALIGNED"
                            diff_summary = "primary and shadow actions aligned."
                        else:
                            diff_status = "DIVERGED"
                            diff_summary = "primary and shadow actions diverged."
                    else:
                        diff_status = "UNAVAILABLE"
                        diff_summary = "diff unavailable due to missing actions."

                    row_dict["v5_decision_diff_status"] = diff_status
                    row_dict["v5_decision_diff_summary"] = diff_summary

            except Exception as diff_e:
                # PR45: Diff generation failure must not stop execution (warning-only)
                print(f"[WARNING][PR45][diff] Failed to compute decision diff: {diff_e} ts={now.isoformat()}")
                # PR45: Safe defaults (non-numeric, non-evaluative)
                row_dict["v5_decision_diff_mode"] = "ON"
                row_dict["v5_decision_diff_status"] = "UNAVAILABLE"
                row_dict["v5_decision_diff_pair"] = "UNKNOWN"
                row_dict["v5_decision_diff_summary"] = "diff failed safely."

            # PR46: v0.5 Decision Diff Semantics Tagging (READ-ONLY, non-evaluative classification)
            try:
                semantics_enabled = DECISION_ENGINE_DIFF_SEMANTICS

                if not semantics_enabled:
                    # PR46: Semantics tagging disabled
                    row_dict["v5_decision_diff_semantics_mode"] = "OFF"
                    row_dict["v5_decision_diff_semantics_status"] = "UNAVAILABLE"
                    row_dict["v5_decision_diff_semantics_tag"] = "NO_SHADOW"
                    row_dict["v5_decision_diff_semantics_context"] = "context_missing"
                    row_dict["v5_decision_diff_semantics_summary"] = "semantics tagging disabled."

                elif not diff_logging_enabled or not shadow_mode:
                    # PR46: Semantics enabled but no shadow/diff available
                    row_dict["v5_decision_diff_semantics_mode"] = "ON"
                    row_dict["v5_decision_diff_semantics_status"] = "UNAVAILABLE"
                    row_dict["v5_decision_diff_semantics_tag"] = "NO_SHADOW"
                    row_dict["v5_decision_diff_semantics_context"] = "context_missing"
                    row_dict["v5_decision_diff_semantics_summary"] = "shadow record not present."

                else:
                    # PR46: Semantics enabled and diff available
                    row_dict["v5_decision_diff_semantics_mode"] = "ON"

                    # Get diff status from PR45
                    diff_status = row_dict.get("v5_decision_diff_status", "UNAVAILABLE")
                    primary_action = row_dict.get("v5_decision_action", "")
                    shadow_action = row_dict.get("v5_shadow_decision_action", "")

                    # PR46: Determine semantics tag (non-evaluative classification)
                    if diff_status == "UNAVAILABLE" or not primary_action or not shadow_action or \
                       primary_action == "UNKNOWN" or shadow_action == "UNKNOWN":
                        # Missing actions
                        semantics_tag = "MISSING_ACTIONS"
                        semantics_status = "UNAVAILABLE"
                        semantics_summary = "actions missing or unavailable."

                    elif diff_status == "ALIGNED":
                        # Actions match
                        semantics_tag = "ALIGNED"
                        semantics_status = "AVAILABLE"
                        semantics_summary = "actions aligned."

                    elif diff_status == "DIVERGED":
                        # Actions differ - classify divergence type (READ-ONLY, no evaluation)
                        semantics_status = "AVAILABLE"

                        # PR46: Detect overlay pattern (cautious or halted)
                        # Cautious: SHIFT/BUY/SELL → HOLD
                        # Halted: anything → PAUSE
                        aggressive_actions = {"SHIFT", "BUY", "SELL"}
                        conservative_action = "HOLD"
                        halted_action = "PAUSE"

                        # Check if one is HOLD and the other is aggressive
                        cautious_pattern = (
                            (primary_action == conservative_action and shadow_action in aggressive_actions) or
                            (shadow_action == conservative_action and primary_action in aggressive_actions)
                        )

                        # Check if one is PAUSE (halted override)
                        halted_pattern = (primary_action == halted_action or shadow_action == halted_action)

                        if cautious_pattern or halted_pattern:
                            semantics_tag = "DIVERGED_RULE_OVERLAY"
                            semantics_summary = "divergence tagged as rule overlay."
                        else:
                            semantics_tag = "DIVERGED_UNKNOWN"
                            semantics_summary = "divergence type unknown."

                    else:
                        # Unexpected diff status
                        semantics_tag = "DIVERGED_UNKNOWN"
                        semantics_status = "UNAVAILABLE"
                        semantics_summary = "unexpected diff status."

                    row_dict["v5_decision_diff_semantics_tag"] = semantics_tag
                    row_dict["v5_decision_diff_semantics_status"] = semantics_status
                    row_dict["v5_decision_diff_semantics_summary"] = semantics_summary

                    # PR46: Determine context tag (presence only, no causation)
                    regime_present = bool(row_dict.get("regime"))
                    intent_present = bool(row_dict.get("intent_primary"))

                    if regime_present and intent_present:
                        context_tag = "regime_and_intent_present"
                    elif regime_present:
                        context_tag = "regime_present"
                    elif intent_present:
                        context_tag = "intent_present"
                    else:
                        context_tag = "context_missing"

                    row_dict["v5_decision_diff_semantics_context"] = context_tag

            except Exception as semantics_e:
                # PR46: Semantics generation failure must not stop execution (warning-only)
                print(f"[WARNING][PR46][semantics] Failed to compute semantics: {semantics_e} ts={now.isoformat()}")
                # PR46: Safe defaults (non-numeric, non-evaluative)
                row_dict["v5_decision_diff_semantics_mode"] = "ON"
                row_dict["v5_decision_diff_semantics_status"] = "UNAVAILABLE"
                row_dict["v5_decision_diff_semantics_tag"] = "MISSING_ACTIONS"
                row_dict["v5_decision_diff_semantics_context"] = "context_missing"
                row_dict["v5_decision_diff_semantics_summary"] = "semantics failed safely."

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
