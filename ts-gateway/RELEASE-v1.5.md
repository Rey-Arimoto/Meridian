# v1.5 Stability Guards Release

**Release Tag**: `v1.5-stability-guards-v1`
**Commit**: `f3647be`
**Date**: 2026-01-19

## Overview

v1.5 introduces stability guards to prevent rapid oscillation in autonomous recovery, improving system resilience under volatile market conditions.

## Features

### PR224: Regime Hysteresis (2-tick confirmation)

**Problem**: Instant regime detection could oscillate between VOLATILE/NORMAL on transient signals.

**Solution**: Require 2 consecutive ticks with same regime before confirming change.

**Implementation**:
- Added `priorRegime`, `regimeHistory` to ResumeState
- `confirmRegimeChangeV1()` helper enforces hysteresis
- Labels: `H0_NO_CHANGE`, `H1_CONFIRMED`, `H2_HOLD`

**Telemetry**:
```json
{
  "resume_regime_hysteresis": "H1_CONFIRMED",
  "resume_market_regime": "REGIME_VOLATILE"
}
```

### PR225: Consecutive Success Gating

**Problem**: Single SUCCEEDED status could escalate to RETRY_IMMEDIATE, then fail and oscillate.

**Solution**: Require 2 consecutive SUCCEEDED statuses before escalating to RETRY_IMMEDIATE.

**Implementation**:
- Added `consecutiveSuccesses`, `lastOrchEffectiveStatus` to ResumeState
- Modified `deriveResumeEscalationV1()` to gate escalation
- Labels: `S0`, `S1`, `S2_PLUS` / `GATE_PASS`, `GATE_WAIT`, `GATE_NA`

**Telemetry**:
```json
{
  "resume_success_streak_status": "S2_PLUS",
  "resume_success_gate": "GATE_PASS",
  "resume_escalated_strategy": "RETRY_IMMEDIATE"
}
```

### PR226: Oscillation Detection Telemetry

**Problem**: No visibility when strategy/regime flapping occurs.

**Solution**: Emit warning telemetry when >10 changes/hour detected (warning-only, no intervention).

**Implementation**:
- Added oscillation tracking fields to ResumeState
- `detectOscillationV1()` helper detects patterns
- Rolling 1-hour window, threshold=10
- Labels: `OSC_NONE`, `OSC_WARN_STRATEGY`, `OSC_WARN_REGIME`, `OSC_WARN_BOTH`

**Telemetry**:
```json
{
  "resume_oscillation_status": "OSC_WARN_STRATEGY",
  "resume_oscillation_codes": "OSC_STRATEGY_OVER_THRESHOLD",
  "warnings": ["WARN_STRATEGY_OSCILLATION_DETECTED"]
}
```

## Constitutional Compliance

All features maintain constitutional constraints:
- **READ-ONLY**: No learning, all rules deterministic
- **Label-only**: No raw numeric telemetry (counts → classes)
- **Defensive**: Never throws, handles malformed state gracefully
- **Backward compatible**: New fields optional, existing behavior preserved

## Test Coverage

### Stability Tests (7/7 PASS)
- `tools/test-pr224-pr225-pr226-stability.ts`
- PR224 hysteresis: tentative change, confirmed change
- PR225 gating: 0/1/2 successes, reset on status change
- PR226 detection: no oscillation baseline

### Oscillation WARN Tests (4/4 PASS)
- `tools/test-pr226-oscillation-warn.ts`
- PR226-A: Strategy oscillation >10/hour → WARN
- PR226-B: Regime oscillation >10/hour → WARN
- PR226-C: 1-hour window reset clears WARN
- PR226-D: Defensive error handling

## Verification

```bash
# Run full release verification
bash tools/verify-v1.5-release.sh

# Expected output:
# ✓ Build: PASS
# ✓ Stability tests (7/7): PASS
# ✓ Oscillation WARN tests (4/4): PASS
```

## Migration Guide

### For Operators

**No action required** - v1.5 is backward compatible. New fields initialize on first read.

**New telemetry to monitor**:
1. `resume_regime_hysteresis`: Watch for `H2_HOLD` (regime flapping suppressed)
2. `resume_success_gate`: Watch for `GATE_WAIT` (escalation delayed)
3. `resume_oscillation_status`: Watch for `OSC_WARN_*` (flapping detected)

**Dashboards**:
- Add `WARN_STRATEGY_OSCILLATION_DETECTED` alert (investigate policy/signals)
- Add `WARN_REGIME_OSCILLATION_DETECTED` alert (investigate market conditions)
- Chart `resume_regime_hysteresis` distribution (H0/H1/H2 ratio)

### For Developers

**New ResumeState fields**:
```typescript
interface ResumeState {
  // PR224: Regime hysteresis
  priorRegime?: MarketRegimeV1;
  regimeHistory?: MarketRegimeV1[];

  // PR225: Consecutive success gating
  consecutiveSuccesses?: number;
  lastOrchEffectiveStatus?: string;

  // PR226: Oscillation detection
  strategyChangeCount?: number;
  lastStrategyChangeTs?: number;
  regimeChangeCount?: number;
  lastRegimeChangeTs?: number;
  lastObservedStrategy?: ResumeStrategyV1;
  lastObservedRegime?: MarketRegimeV1;
}
```

**Helper functions**:
- `confirmRegimeChangeV1()` - Apply hysteresis to regime
- `detectOscillationV1()` - Detect strategy/regime oscillation
- `deriveResumeEscalationV1()` - Now includes gating logic

## Rollback Plan

If v1.5 causes issues:

1. **Revert to v1.4.1**:
   ```bash
   git checkout v1.4.1-hotfix-safety-guards
   npm run build
   # Deploy
   ```

2. **Symptoms requiring rollback**:
   - Excessive `H2_HOLD` (hysteresis too aggressive)
   - Excessive `GATE_WAIT` (gating too aggressive)
   - False positive oscillation WARNs

3. **Tuning (if rollback not needed)**:
   - Hysteresis: Adjust `regimeHistory` buffer size (currently 3)
   - Gating: Adjust threshold (currently 2 consecutive)
   - Oscillation: Adjust threshold (currently >10/hour)

## Known Limitations

1. **Hysteresis window**: Fixed at 2 ticks (not configurable)
2. **Success gating**: Fixed at 2 consecutive (not configurable)
3. **Oscillation threshold**: Fixed at 10 changes/hour (not configurable)

Future work (v1.6+):
- Make thresholds configurable via policy
- Add hysteresis for strategy changes (currently regime-only)
- Add oscillation intervention (currently warning-only)

## References

- **Architecture Review**: See conversation history for deadlock/oscillation analysis
- **v1.4.1 Hotfixes**: PR221 (orch staleness), PR222 (max deferral), PR223 (regime signal freshness)
- **Telemetry Spec**: `src/telemetry/types.ts` for event types

## Changelog

### v1.5-stability-guards-v1 (f3647be)
- Add PR226 oscillation WARN tests (4/4 scenarios)
- Add defensive check for empty regimeHistory

### v1.5 (8a93678)
- Implement PR224: Regime hysteresis
- Implement PR225: Consecutive success gating
- Implement PR226: Oscillation detection telemetry
- Add stability tests (7/7 scenarios)

---

**Verification**: ✓ All tests PASS
**Constitutional**: ✓ READ-ONLY, label-only, defensive, backward compatible
**Ready for production**: ✓ Yes
