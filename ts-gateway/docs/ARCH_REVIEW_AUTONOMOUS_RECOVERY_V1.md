# Autonomous Recovery Architecture Review v1.4
## Safety Analysis: Supervisor Adaptive Recovery Pipeline

**Date**: 2026-01-19
**Scope**: PR213–PR220 autonomous recovery pipeline
**Focus**: Failure modes, oscillation, deadlock, adversarial resilience

---

## Executive Summary

The v1.4 autonomous recovery pipeline implements a multi-stage decision system:

```
STOP → Base Strategy (PR213)
     → Escalation Ladder (PR219, orch feedback)
     → Market Regime Derivation (PR220, signals)
     → Regime × Strategy Matrix Overlay (PR220)
     → Execution Mode Enforcement (PR214, safety cap)
     → Timing Control (PR215, delay/backoff)
     → Orchestrator Enqueue OR Immediate Execution
```

**Constitutional constraints verified**:
- ✓ READ-ONLY (no learning, fixed rules)
- ✓ Label-only (no numeric timestamps)
- ✓ Defensive (never throws)
- ✓ Deterministic (same inputs → same outputs)
- ✓ Safety-first (never escalates to LIVE)

**Critical findings**: 7 architectural failure modes identified, 3 high-severity.

---

## 1. Architectural Failure Modes

### 1.1 SEVERITY: HIGH - Strategy Oscillation via Policy Flapping

**Location**: `supervisor.ts:866-905` (Escalation Ladder)

**Mechanism**:
```
Tick 1: orch_last_status = "SUCCEEDED"
  → Escalation Rule E: escalate to RETRY_IMMEDIATE
  → Matrix: regime=NORMAL, keeps RETRY_IMMEDIATE
  → Enforcement: currentDesiredMode=undefined → defaults to SIM_ONLY (line 1639)
  → Execute → succeeds → orch reports SUCCEEDED

Tick 2: orch_last_status = "SUCCEEDED" (still)
  → Escalation Rule E: escalate to RETRY_IMMEDIATE again
  → BUT policy blocks (external trigger)
  → Orchestrator returns SKIPPED_POLICY

Tick 3: orch_last_status = "SKIPPED_POLICY"
  → Escalation Rule A: force WAIT_FOR_UNLOCK
  → Matrix: keeps WAIT_FOR_UNLOCK
  → Wait for policy unlock...

Tick 4: Policy unblocks
  → Escalation: no new orch feedback, Rule F keeps WAIT_FOR_UNLOCK
  → Execute → succeeds → orch reports SUCCEEDED

Tick 5: orch_last_status = "SUCCEEDED"
  → Escalation Rule E: escalate to RETRY_IMMEDIATE
  → CYCLE REPEATS
```

**Result**: System oscillates between RETRY_IMMEDIATE and WAIT_FOR_UNLOCK based on policy state.

**Root cause**:
- Escalation ladder has no hysteresis or dampening
- Policy state is external and can flap independently
- No "consecutive success" counter to stabilize escalation

**Impact**:
- Strategy churn prevents stable execution
- Telemetry pollution (constant strategy changes)
- Potential livelock if policy flaps faster than execution

**Mitigation for v2**:
```typescript
// Add to ResumeState
consecutiveSuccesses?: number;  // Track stability
lastEscalatedStrategy?: ResumeStrategyV1;  // Detect oscillation

// In deriveResumeEscalationV1
if (orchLastStatus === "SUCCEEDED") {
  const successCount = (resumeState.consecutiveSuccesses || 0) + 1;

  // Require 2 consecutive successes before escalating to IMMEDIATE
  if (successCount >= 2) {
    return { strategy: "RETRY_IMMEDIATE", codes: [...] };
  } else {
    return { strategy: baseStrategy, codes: ["STRAT_ESC_STABILITY_WAIT"] };
  }
}
```

---

### 1.2 SEVERITY: HIGH - Market Regime Signal Staleness

**Location**: `supervisor.ts:1600-1612` (Regime Signal Collection)

**Code**:
```typescript
const regimeSignals: MarketRegimeSignalsV1 = {
  phase_label: state.resumeState.lastPhaseLabel,
  // Other signals undefined (would be populated from deps.getResumeInputs in full impl)
};
```

**Problem**: Only `phase_label` is available from `resumeState.lastPhaseLabel`, which is captured at STOP time, not current tick time.

**Staleness scenarios**:
```
T0: Run stops due to PHASE_DOWN_SHOCK
  → resumeState.lastPhaseLabel = "PHASE_DOWN_SHOCK"
  → regime derivation sees PHASE_DOWN_SHOCK

T1 (5 minutes later): Supervisor tick
  → Actual phase now = "PHASE_NORMAL" (recovered)
  → BUT resumeState.lastPhaseLabel still = "PHASE_DOWN_SHOCK" (stale)
  → Regime incorrectly derived as REGIME_VOLATILE
  → Matrix forces RETRY_SAFE_SIM_ONLY (over-conservative)
```

**All other regime signals undefined**:
- `oracle_status` → undefined
- `gate_status` → undefined
- `gate_depth_status` → undefined
- `quote_status` → undefined
- `network_status` → undefined

**Regime derivation Rule 5** (`supervisor.ts:1048-1057`):
```typescript
// If no oracle, gate, or network signal → REGIME_UNKNOWN
if (!hasOracleSignal && !hasGateSignal && !hasNetworkSignal) {
  return { regime: "REGIME_UNKNOWN", codes: ["REGIME_BY_UNKNOWN"] };
}
```

**Result**: With only `phase_label` available, regime almost always falls through to:
- REGIME_VOLATILE (if phase is shock/reversal)
- REGIME_UNKNOWN (if phase is normal but no other signals)

**Impact**:
- Over-conservative strategy selection (stuck in SIM_ONLY / WAIT_FOR_RECOVERY)
- Defeats purpose of escalation ladder (matrix always demotes)
- Regime awareness is largely inoperative in v1

**Mitigation for v2**:
```typescript
// In supervisor tick, populate regime signals from CURRENT deps, not stale resumeState
if (deps?.getResumeInputs) {
  const inputs = await deps.getResumeInputs();

  const regimeSignals: MarketRegimeSignalsV1 = {
    oracle_status: inputs.oracleStatus === "AVAILABLE" ? "ORACLE_OK" :
                   inputs.oracleStatus === "STALE" ? "ORACLE_STALE" : "ORACLE_UNAVAILABLE",
    gate_status: inputs.gateStatus,
    phase_label: inputs.phaseLabel,  // Current phase, not stale
    network_status: inputs.networkHealthy ? "NET_OK" : "NET_DEGRADED",
    // ... populate all signals
  };
} else {
  // Fallback to resumeState (stale) with WARNING
  warnings.push("WARN_REGIME_SIGNALS_STALE");
}
```

---

### 1.3 SEVERITY: MEDIUM - Regime Flapping Without Hysteresis

**Location**: `supervisor.ts:1003-1066` (Market Regime Derivation)

**Problem**: Regime derivation is **instant and stateless**. No smoothing, averaging, or hysteresis.

**Oscillation scenario**:
```
Oracle signal flaps: OK → STALE → OK → STALE (every tick)

Tick 1: oracle_status = "ORACLE_STALE"
  → Rule 1: REGIME_ORACLE_UNCERTAIN
  → Matrix Rule 1: force WAIT_FOR_RECOVERY
  → Deferred to orchestrator

Tick 2: oracle_status = "ORACLE_OK" (transient recovery)
  → Rule 6: REGIME_NORMAL
  → Matrix Rule 4: keep escalated strategy (e.g., RETRY_IMMEDIATE)
  → Execute immediately

Tick 3: oracle_status = "ORACLE_STALE" (flaps back)
  → Rule 1: REGIME_ORACLE_UNCERTAIN again
  → Matrix forces WAIT_FOR_RECOVERY again
  → Deferred

Tick 4: oracle_status = "ORACLE_OK"
  → REGIME_NORMAL
  → Execute
  ...repeat
```

**Result**: Regime-driven execution oscillation if upstream signals are unstable.

**Impact**:
- Prevents stable execution
- Regime "flap detection" triggers false positives
- Orchestrator queue pollution (constant enqueue/dequeue)

**Mitigation for v2**:
```typescript
// Add to ResumeState
regimeHistory?: MarketRegimeV1[];  // Last N regimes (circular buffer, N=3)

// In deriveMarketRegimeV1
function deriveMarketRegimeV1WithHysteresis(
  signals: MarketRegimeSignalsV1,
  priorRegime?: MarketRegimeV1,
  regimeHistory?: MarketRegimeV1[]
): { regime: MarketRegimeV1; codes: string[] } {

  const instantRegime = deriveMarketRegimeV1(signals);  // Current instant reading

  // Hysteresis: require regime to be stable for 2 consecutive ticks before changing
  if (priorRegime && instantRegime.regime !== priorRegime) {
    // Check if last regime in history was also instantRegime
    const lastRegime = regimeHistory?.[regimeHistory.length - 1];
    if (lastRegime === instantRegime.regime) {
      // Confirmed change (2 consecutive ticks)
      return instantRegime;
    } else {
      // Tentative change, wait for confirmation
      return { regime: priorRegime, codes: ["REGIME_HYSTERESIS_HOLD"] };
    }
  }

  return instantRegime;
}
```

**Alternative (simpler)**: Sticky regime bias
```typescript
// If transitioning from NORMAL → VOLATILE, require 2 volatile signals
// If transitioning from VOLATILE → NORMAL, require 3 normal signals
// Asymmetric hysteresis: easier to enter safe mode, harder to exit
```

---

### 1.4 SEVERITY: HIGH - Orchestrator Feedback Staleness (No Timeout)

**Location**: `supervisor.ts:1291-1304` (Orchestrator Feedback Processing)

**Problem**: Once orchestrator reports feedback, `orchLastStatus` remains in `resumeState` indefinitely. No staleness timeout.

**Deadlock scenario**:
```
T0: Orchestrator reports orch_last_status = "FAILED_MARKET"
  → resumeState.orchLastStatus = "FAILED_MARKET"
  → Escalation Rule C: force WAIT_FOR_RECOVERY

T1 (1 hour later): Orchestrator dies (process crash, network partition)
  → No new feedback arrives
  → Escalation Rule F applies: "No new feedback → keep baseStrategy"
  → BUT resumeState.orchLastStatus still = "FAILED_MARKET" (not undefined)
  → Rule C still matches → force WAIT_FOR_RECOVERY
  → System stuck in WAIT_FOR_RECOVERY forever
```

**Current escalation logic** (`supervisor.ts:887-891`):
```typescript
// Rule C: FAILED_MARKET → WAIT_FOR_RECOVERY
if (orchLastStatus === "FAILED_MARKET") {
  codes.push("STRAT_ESC_FROM_ORCH_STATUS_FAILED_MARKET");
  codes.push("STRAT_ESC_TO_WAIT_FOR_RECOVERY");
  return { strategy: "WAIT_FOR_RECOVERY", codes: codes.sort() };
}
```

**No check for**:
- How long ago was `orchLastStatus` updated?
- Is orchestrator still alive?
- Should we ignore stale feedback?

**Impact**:
- System deadlocks if orchestrator stops reporting after negative feedback
- Requires manual intervention to clear `resumeState.orchLastStatus`
- Silent failure mode (no warning that feedback is stale)

**Mitigation for v2**:
```typescript
// Add to ResumeState
orchLastStatusTs?: number;  // Timestamp when orchLastStatus was set

// In supervisor tick, before escalation
const orchFeedbackAge = nowTs - (resumeState.orchLastStatusTs || 0);
const ORCH_FEEDBACK_STALE_MS = 15 * 60 * 1000;  // 15 minutes

let effectiveOrchLastStatus = resumeState.orchLastStatus;
if (orchFeedbackAge > ORCH_FEEDBACK_STALE_MS) {
  warnings.push("WARN_ORCH_FEEDBACK_STALE");
  effectiveOrchLastStatus = undefined;  // Ignore stale feedback
}

// Pass effectiveOrchLastStatus to escalation
const escalation = deriveResumeEscalationV1({
  orchLastStatus: effectiveOrchLastStatus,  // May be undefined if stale
  ...
});
```

**Alternative (stricter)**: Require heartbeat
```typescript
// Orchestrator must send heartbeat every 5 minutes
// If no heartbeat for 10 minutes, clear all orch feedback
```

---

### 1.5 SEVERITY: MEDIUM - Strategy Churn (Escalation Promotes, Matrix Demotes)

**Location**: `supervisor.ts:1590-1629` (Escalation → Matrix Pipeline)

**Problem**: Escalation ladder can promote strategy (e.g., to RETRY_IMMEDIATE), then matrix overlay immediately demotes based on regime.

**Churn scenario**:
```
Base strategy: RETRY_SAFE_SIM_ONLY
Orch feedback: SUCCEEDED
Regime: REGIME_VOLATILE (phase = DOWN_SHOCK)

Step 1: Escalation Rule E (line 901-905)
  → orchLastStatus = "SUCCEEDED"
  → Escalate to RETRY_IMMEDIATE

Step 2: Matrix Rule 2 (line 1113-1116)
  → regime = "REGIME_VOLATILE"
  → Force RETRY_SAFE_SIM_ONLY

Result: escalatedStrategy = RETRY_IMMEDIATE, but matrixStrategy = RETRY_SAFE_SIM_ONLY
  → Net effect: no change from base strategy
  → Escalation work is wasted
```

**Is this safe?** Yes (conservative bias).

**Is this efficient?** No (unnecessary computation).

**Telemetry impact**:
- `resume_escalated_strategy = "RETRY_IMMEDIATE"`
- `resume_matrix_strategy = "RETRY_SAFE_SIM_ONLY"`
- Shows escalation promoted, then matrix demoted
- Could be confusing in logs ("why did it escalate if we don't use it?")

**Mitigation for v2**: None required (this is feature, not bug). Matrix SHOULD override escalation for safety.

**Documentation improvement**: Clarify in telemetry that matrix has final authority:
```typescript
// Add label to matrix codes when demotion occurs
if (escalatedStrategy === "RETRY_IMMEDIATE" && matrixStrategy !== "RETRY_IMMEDIATE") {
  codes.push("MATRIX_DEMOTED_FROM_ESCALATION");
}
```

---

### 1.6 SEVERITY: LOW - Orchestrator Result Processing Race (Multiple Results in Single Tick)

**Location**: `supervisor.ts:1229-1306` (Orchestrator Feedback Loop)

**Code**:
```typescript
for (const result of orchResults) {
  // Process each result
  if (result.resume_id === (state.lastRun as any)?.resumeId) {
    // Update resumeState.orchLastStatus
    state.resumeState.orchLastStatus = result.status;  // LAST result wins
    state.resumeState.orchLastOutcomeCodes = result.outcome_codes || [];
    state.resumeState.orchLastResultId = result.result_id;
  }
}
```

**Problem**: If orchestrator writes multiple results in rapid succession, all are processed in a single tick. Only the LAST result is retained in `resumeState`.

**Lost information scenario**:
```
Orchestrator writes (in <1 second):
  Result 1: status=FAILED_NETWORK, result_id=R1
  Result 2: status=SUCCEEDED, result_id=R2

Supervisor tick processes both in loop:
  Iteration 1: orchLastStatus = "FAILED_NETWORK"
  Iteration 2: orchLastStatus = "SUCCEEDED"  (overwrites)

Final state: orchLastStatus = "SUCCEEDED"
  → Escalation Rule E: escalate to RETRY_IMMEDIATE
  → Lost information that there was a FAILED_NETWORK in between
```

**Is this correct?** Depends on semantics:
- If "latest feedback is most relevant" → Yes (current behavior is correct)
- If "should track all failures" → No (losing intermediate results)

**Impact**: Low (latest feedback is likely most relevant for next decision).

**Mitigation for v2** (if tracking all results is required):
```typescript
// Add to ResumeState
orchFeedbackHistory?: Array<{
  resultId: string;
  status: string;
  outcomeCodes: string[];
  seenAtTs: number;
}>;

// In feedback loop, append to history (keep last 10)
if (!state.resumeState.orchFeedbackHistory) {
  state.resumeState.orchFeedbackHistory = [];
}
state.resumeState.orchFeedbackHistory.push({
  resultId: result.result_id,
  status: result.status,
  outcomeCodes: result.outcome_codes || [],
  seenAtTs: Date.now(),
});
// Keep last 10, drop older
if (state.resumeState.orchFeedbackHistory.length > 10) {
  state.resumeState.orchFeedbackHistory.shift();
}
```

---

### 1.7 SEVERITY: MEDIUM - Timing Deferral Can Block Indefinitely

**Location**: `supervisor.ts:1721-1796` (Timing Decision Gate)

**Code**:
```typescript
if (resumeDelayClass && resumeDelayClass !== "IMMEDIATE") {
  // Enqueue to orchestrator
  await appendOrchQueueV1(orchInstruction);

  runResult = {
    status: "DEFERRED",
    reasons: ["REASON_RESUME_DEFERRED_BY_TIMING", ...],
  };
}
```

**Problem**: If orchestrator never executes the instruction (busy, dead, policy blocked), the resume never happens.

**Indefinite deferral scenario**:
```
Tick 1: resumeDelayClass = "BACKOFF_SHORT"
  → Deferred to orchestrator
  → Enqueued as instruction I1

Orchestrator: Policy hook blocks (not_before active for 1 hour)
  → Instruction I1 sits in queue

Tick 2-N (next hour): resumeState still exists
  → Same resumeDelayClass = "BACKOFF_SHORT"
  → Checks orchAckSet.has(resumeId) → not ACKed
  → Re-enqueues (idempotency via ACK prevents duplicate, but doesn't execute)
  → Still deferred

Hour passes, orchestrator tries to execute:
  → Policy still blocking (extended)
  → Instruction I1 never executes

Result: Resume never happens, stuck in DEFERRED forever
```

**Missing**:
- No "max defer time" (abandon after 24 hours)
- No "escalate to immediate after N deferrals"
- No warning if deferred too long

**Impact**: Silent resume abandonment if orchestrator is unavailable.

**Mitigation for v2**:
```typescript
// Add to ResumeState
deferralCount?: number;
firstDeferredAtTs?: number;

// In timing gate
if (resumeDelayClass && resumeDelayClass !== "IMMEDIATE") {
  const deferralCount = (resumeState.deferralCount || 0) + 1;
  const firstDeferredAtTs = resumeState.firstDeferredAtTs || nowTs;
  const deferralAge = nowTs - firstDeferredAtTs;

  const MAX_DEFERRAL_AGE_MS = 24 * 60 * 60 * 1000;  // 24 hours
  const MAX_DEFERRAL_COUNT = 50;  // 50 ticks

  if (deferralAge > MAX_DEFERRAL_AGE_MS || deferralCount > MAX_DEFERRAL_COUNT) {
    // Abandon resume (too many deferrals)
    warnings.push("WARN_RESUME_ABANDONED_MAX_DEFERRALS");
    await store.patchState({
      lastRun: { status: "ABANDONED", stopReason: "DEFERRED_TOO_LONG" },
      resumeState: undefined,
    });
    return { status: "OK", action: "ACTION_ABORT", warnings, notes };
  }

  // Update deferral tracking
  resumeState.deferralCount = deferralCount;
  resumeState.firstDeferredAtTs = firstDeferredAtTs;

  // ... proceed with enqueueing
}
```

---

## 2. Oscillation & Deadlock Analysis

### 2.1 Strategy Oscillation Conditions

**Condition 1**: Policy flapping + escalation ladder
- **Trigger**: External policy alternates between ALLOW and DENY
- **Cycle**: RETRY_IMMEDIATE ↔ WAIT_FOR_UNLOCK
- **Period**: 2-4 supervisor ticks (depends on policy check frequency)
- **Detection**: Track `resume_escalated_strategy` changes per minute
- **Mitigation**: Hysteresis (require 2 consecutive successes before escalating)

**Condition 2**: Regime signal flapping + matrix overlay
- **Trigger**: Oracle/network signals unstable
- **Cycle**: REGIME_NORMAL ↔ REGIME_VOLATILE → strategy changes
- **Period**: Every tick (instant regime derivation)
- **Detection**: Track `resume_market_regime` changes per minute
- **Mitigation**: Regime hysteresis (sticky regimes, 2-tick confirmation)

**Condition 3**: Escalation promotes, matrix demotes (churn)
- **Trigger**: Successful execution during volatile regime
- **Cycle**: Base → Escalate to IMMEDIATE → Matrix demotes to SIM_ONLY
- **Period**: Every tick where orch reports success during volatility
- **Detection**: Count `resume_escalated_strategy != resume_matrix_strategy`
- **Mitigation**: None required (safe churn, matrix correctness)

### 2.2 Deadlock Conditions

**Deadlock 1**: Stale orchestrator feedback
- **Trigger**: Orchestrator dies after reporting FAILED_MARKET
- **State**: `orchLastStatus = "FAILED_MARKET"` (permanent)
- **Result**: Stuck in WAIT_FOR_RECOVERY forever
- **Detection**: Track `orchLastStatusTs` age
- **Escape**: Timeout stale feedback (15 min), revert to baseStrategy

**Deadlock 2**: Indefinite timing deferral
- **Trigger**: Orchestrator unavailable, resumeDelayClass != IMMEDIATE
- **State**: Deferred to orchestrator, never executes
- **Result**: Resume never happens
- **Detection**: Track `deferralCount` and `firstDeferredAtTs`
- **Escape**: Abandon after 24 hours or 50 deferrals

**Deadlock 3**: Regime stuck in UNKNOWN (signal starvation)
- **Trigger**: No regime signals available (all undefined)
- **State**: `regime = REGIME_UNKNOWN` (permanent)
- **Result**: Matrix always demotes RETRY_IMMEDIATE to SIM_ONLY
- **Detection**: Track consecutive REGIME_UNKNOWN ticks
- **Escape**: Populate signals from `deps.getResumeInputs` (not just resumeState)

---

## 3. Pipeline Ordering Correctness

### 3.1 Current Order

```
Base Strategy (PR213)
  ↓
Escalation Ladder (PR219, uses orch feedback)
  ↓
Market Regime Derivation (PR220, uses signals)
  ↓
Regime × Strategy Matrix Overlay (PR220, uses escalated + regime)
  ↓
Execution Mode Enforcement (PR214, uses matrix)
  ↓
Timing Control (PR215, uses matrix)
```

### 3.2 Ordering Rationale

**Why Escalation before Matrix?**
- Escalation uses orchestrator feedback (past execution results)
- Matrix uses market regime (current market conditions)
- **Safety principle**: Current market state should override past success
- Example:
  - Escalation: "Last run succeeded → try RETRY_IMMEDIATE"
  - Matrix: "But market is volatile now → force SIM_ONLY"
  - Matrix wins (correct for safety)

**Alternative (Matrix before Escalation)?**
```
Base Strategy
  ↓
Regime → Matrix (constrains base by regime)
  ↓
Escalation (adjusts matrix output by orch feedback)
```
- **Problem**: Escalation rules don't know about regime
- Rule E (SUCCEEDED → RETRY_IMMEDIATE) would override regime constraint
- Example:
  - Matrix: "Regime volatile → force SIM_ONLY"
  - Escalation: "Orch succeeded → escalate to RETRY_IMMEDIATE"
  - Escalation wins (UNSAFE)

**Verdict**: **Current order is CORRECT**. Matrix must be final to enforce regime-based safety.

### 3.3 Enforcement Placement

**Why Enforcement after Matrix?**
- Enforcement caps execution mode based on FINAL strategy (matrix output)
- Ensures no strategy can bypass safety cap
- Example:
  - Matrix: "RETRY_IMMEDIATE"
  - Enforcement: "Cap at DRY_RUN (never LIVE)"
  - Even if matrix promotes, enforcement caps (defense in depth)

**Critical**: Enforcement reads `resumeStrategy` (line 1637), which is assigned `matrixStrategy` (line 1629).

**Safety verification**:
```typescript
// Line 1639: currentDesiredMode = undefined
const enforcement = deriveExecutionModeOverrideFromStrategyV1(
  resumeStrategy,  // = matrixStrategy
  undefined        // No current desired mode available
);

// Line 503-517: RETRY_IMMEDIATE with undefined mode
if (resumeStrategy === "RETRY_IMMEDIATE") {
  if (currentDesiredMode === "LIVE") {
    return { enforcedMode: "DRY_RUN", ... };  // Cap LIVE → DRY_RUN
  } else if (currentDesiredMode === "DRY_RUN") {
    return { enforcedMode: "DRY_RUN", ... };  // Keep DRY_RUN
  } else {
    // currentDesiredMode = undefined → default to SIM_ONLY
    return { enforcedMode: "SIM_ONLY", ... };  // MOST CONSERVATIVE
  }
}
```

**Result**: With `currentDesiredMode = undefined`, enforcement **always defaults to SIM_ONLY** for RETRY_IMMEDIATE.
- This is SAFER than documented cap at DRY_RUN
- But may be TOO conservative (defeats purpose of RETRY_IMMEDIATE)

**Recommendation for v2**: Pass actual desired mode from RunPlan or config
```typescript
const enforcement = deriveExecutionModeOverrideFromStrategyV1(
  resumeStrategy,
  runPlan.desiredExecutionMode || "DRY_RUN"  // Default to DRY_RUN, not undefined
);
```

---

## 4. Adversarial Market Conditions

### 4.1 Attack Vector: Oracle Signal Manipulation

**Scenario**: Attacker controls oracle feed, intentionally flaps STALE ↔ OK

**Impact**:
```
T0: oracle_status = "ORACLE_STALE"
  → REGIME_ORACLE_UNCERTAIN
  → Matrix forces WAIT_FOR_RECOVERY
  → Execution blocked

T1: oracle_status = "ORACLE_OK" (brief)
  → REGIME_NORMAL
  → Matrix allows execution
  → System executes

T2: oracle_status = "ORACLE_STALE" (flaps back)
  → REGIME_ORACLE_UNCERTAIN
  → Execution blocked again

Result: Attacker controls execution timing by flapping oracle signal
```

**Defense gaps**:
- No oracle signal validation (trust external source)
- No regime hysteresis (instant response to signal change)
- No "oracle anomaly detection" (rapid flaps)

**Mitigation**:
- Regime hysteresis (require 2-3 consecutive ticks before changing regime)
- Oracle health check (track flap rate, warn if >X flaps/minute)
- Multiple oracle sources (require 2/3 oracles to agree before marking STALE)

### 4.2 Attack Vector: Flash Crash → Regime Spike

**Scenario**: Attacker triggers flash crash (large sell order), phase detector marks PHASE_DOWN_SHOCK

**Impact**:
```
T0: Flash crash
  → phase_label = "PHASE_DOWN_SHOCK"
  → REGIME_VOLATILE
  → Matrix forces RETRY_SAFE_SIM_ONLY
  → All execution in SIM_ONLY mode

T1 (seconds later): Market recovers
  → phase_label = "PHASE_NORMAL"
  → REGIME_NORMAL
  → Matrix allows escalated strategy

T2: Attacker triggers another flash crash
  → REGIME_VOLATILE again

Result: Attacker can keep system in SIM_ONLY mode by triggering periodic crashes
```

**Defense gaps**:
- No flash crash detection (vs. sustained volatility)
- No regime stability confirmation
- Phase signal is instant (no smoothing)

**Mitigation**:
- Flash crash filter (require volatility to persist for >30 seconds before VOLATILE regime)
- Regime confirmation (require 3 consecutive VOLATILE ticks before forcing SIM_ONLY)
- Volume-weighted phase detection (ignore low-volume price spikes)

### 4.3 Attack Vector: Network Partition → Orchestrator Isolation

**Scenario**: Attacker partitions network, supervisor can't reach orchestrator

**Impact**:
```
T0: Network partition
  → Orchestrator unreachable
  → resumeDelayClass = BACKOFF_SHORT (timing rule)
  → Deferred to orchestrator
  → Enqueued but never executes

T1-T100: Supervisor ticks
  → resumeState still exists
  → Keeps deferring (waiting for orchestrator)
  → No execution happens

Result: Denial of service (system stops executing)
```

**Defense gaps**:
- No max deferral timeout
- No fallback to local execution if orchestrator unavailable
- No orchestrator health check

**Mitigation**:
- Deferral timeout (abandon after 24 hours)
- Orchestrator health check (ping before enqueueing)
- Fallback mode (execute locally with SIM_ONLY if orchestrator unavailable for >15 min)

### 4.4 Attack Vector: Policy DoS (Constant Blocking)

**Scenario**: Attacker controls policy service, always returns hardStopActive=true

**Impact**:
```
Every tick:
  → policyResult.hardStopActive = true
  → Supervisor returns ACTION_WAIT_HARDSTOP
  → No execution happens

Result: Complete denial of service
```

**Defense gaps**:
- No policy service health check
- No "policy override" for critical resumes
- No max hardstop duration

**Mitigation**:
- Policy health check (warn if hardstop active for >1 hour)
- Emergency policy bypass (allow SIM_ONLY execution after 24h hardstop)
- Policy source diversity (require 2/3 policy services to agree on hardstop)

---

## 5. Minimal State/Guards for v2

### 5.1 Additional ResumeState Fields

```typescript
export interface ResumeStateV2 {
  // ... existing v1 fields ...

  // Stability tracking
  consecutiveSuccesses?: number;
  consecutiveFailures?: number;
  lastEscalatedStrategy?: ResumeStrategyV1;

  // Regime stability
  regimeHistory?: MarketRegimeV1[];  // Last 3 regimes (circular buffer)
  priorRegime?: MarketRegimeV1;

  // Orchestrator feedback staleness
  orchLastStatusTs?: number;  // Timestamp when orchLastStatus was set
  orchFeedbackHistory?: Array<{
    resultId: string;
    status: string;
    outcomeCodes: string[];
    seenAtTs: number;
  }>;

  // Deferral tracking
  deferralCount?: number;
  firstDeferredAtTs?: number;
  lastDeferredTs?: number;

  // Oscillation detection
  strategyChangeCount?: number;  // Changes in last hour
  regimeChangeCount?: number;    // Changes in last hour
  lastStrategyChangeTs?: number;
  lastRegimeChangeTs?: number;
}
```

### 5.2 Guards for v2

**Guard 1: Escalation Stability**
```typescript
function shouldEscalate(
  orchLastStatus: string,
  consecutiveSuccesses: number
): boolean {
  if (orchLastStatus === "SUCCEEDED") {
    return consecutiveSuccesses >= 2;  // Require 2 consecutive
  }
  return true;  // Other statuses escalate immediately
}
```

**Guard 2: Regime Hysteresis**
```typescript
function confirmRegimeChange(
  instantRegime: MarketRegimeV1,
  priorRegime: MarketRegimeV1,
  regimeHistory: MarketRegimeV1[]
): MarketRegimeV1 {
  if (instantRegime === priorRegime) {
    return instantRegime;  // No change, use instant
  }

  // Changing regime: require 2 consecutive ticks to confirm
  const lastRegime = regimeHistory[regimeHistory.length - 1];
  if (lastRegime === instantRegime) {
    return instantRegime;  // Confirmed (2 consecutive)
  }

  return priorRegime;  // Hold prior regime (wait for confirmation)
}
```

**Guard 3: Orchestrator Feedback Staleness**
```typescript
function getEffectiveOrchStatus(
  orchLastStatus: string | undefined,
  orchLastStatusTs: number | undefined,
  nowTs: number
): string | undefined {
  const STALE_THRESHOLD_MS = 15 * 60 * 1000;  // 15 minutes

  if (!orchLastStatus || !orchLastStatusTs) {
    return undefined;
  }

  const age = nowTs - orchLastStatusTs;
  if (age > STALE_THRESHOLD_MS) {
    return undefined;  // Ignore stale feedback
  }

  return orchLastStatus;
}
```

**Guard 4: Max Deferral Limit**
```typescript
function shouldAbandonDeferral(
  deferralCount: number,
  firstDeferredAtTs: number,
  nowTs: number
): boolean {
  const MAX_DEFERRAL_AGE_MS = 24 * 60 * 60 * 1000;  // 24 hours
  const MAX_DEFERRAL_COUNT = 50;

  const age = nowTs - firstDeferredAtTs;
  return age > MAX_DEFERRAL_AGE_MS || deferralCount > MAX_DEFERRAL_COUNT;
}
```

**Guard 5: Oscillation Detection**
```typescript
function detectStrategyOscillation(
  strategyChangeCount: number,
  windowMs: number = 60 * 60 * 1000  // 1 hour
): boolean {
  const OSCILLATION_THRESHOLD = 10;  // >10 changes/hour
  return strategyChangeCount > OSCILLATION_THRESHOLD;
}
```

---

## 6. Recommendations

### 6.1 Immediate (Hotfix for v1.4.1)

1. **Add orchestrator feedback staleness timeout** (15 min)
   - Prevents deadlock from stale FAILED_MARKET feedback
   - Minimal code change (filter in supervisor tick)

2. **Add max deferral abandon** (24 hours)
   - Prevents indefinite deferral deadlock
   - Emits WARN_RESUME_ABANDONED_MAX_DEFERRALS

3. **Populate regime signals from current deps, not stale resumeState**
   - Fixes signal staleness (highest impact)
   - Requires wiring `deps.getResumeInputs()` to regime derivation

### 6.2 Short-term (v1.5)

4. **Add regime hysteresis (2-tick confirmation)**
   - Reduces regime flapping oscillation
   - Add regimeHistory to ResumeState

5. **Add escalation stability (2 consecutive successes for IMMEDIATE)**
   - Reduces policy flapping oscillation
   - Add consecutiveSuccesses to ResumeState

6. **Add oscillation detection telemetry**
   - Track strategyChangeCount and regimeChangeCount
   - Emit WARN_OSCILLATION_DETECTED if >10 changes/hour

### 6.3 Medium-term (v2.0)

7. **Add orchestrator health check / heartbeat**
   - Detect dead orchestrator before deferring
   - Fallback to local execution with SIM_ONLY

8. **Add flash crash detection (vs. sustained volatility)**
   - Filter transient phase spikes
   - Require volatility to persist >30 seconds

9. **Add policy service health check**
   - Detect policy DoS
   - Emergency bypass after 24h hardstop

10. **Add multiple signal sources (oracle, policy)**
    - Require 2/3 agreement before acting on critical signals
    - Defense against single-source manipulation

---

## 7. Conclusion

The v1.4 autonomous recovery pipeline is **fundamentally sound** in design:
- ✓ Pipeline ordering is correct (Matrix after Escalation ensures safety)
- ✓ Enforcement caps prevent LIVE execution (defense in depth)
- ✓ Constitutional constraints are met (READ-ONLY, label-only, defensive)

**Critical gaps**:
- ❌ Orchestrator feedback staleness can cause deadlock (HIGH)
- ❌ Regime signal staleness defeats purpose of regime awareness (HIGH)
- ❌ No hysteresis in escalation or regime → oscillation risk (MEDIUM)
- ❌ Indefinite deferral with no abandon timeout (MEDIUM)

**v2 priorities**:
1. Staleness timeouts (orch feedback, regime signals)
2. Hysteresis (regime, escalation)
3. Abandon limits (max deferral)
4. Oscillation detection
5. Health checks (orchestrator, policy)

**Overall safety grade**: B+ (safe under normal conditions, vulnerable to edge cases and adversarial inputs)

With recommended v2 improvements: **A** (production-ready for autonomous operation)

---

*End of Architectural Review*
