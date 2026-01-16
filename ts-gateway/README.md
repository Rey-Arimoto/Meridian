# Meridian TS Gateway (v0.1)

This gateway is the "hands" for Meridian.
It holds the Sui private key **only here** and exposes minimal HTTP APIs for swaps.

## Guarantees (v0.1)
- Private key never leaves TS gateway
- Python calls gateway over HTTP only
- Minimal health + swap endpoint

## Setup
```bash
cd ts-gateway
cp .env.example .env
# edit .env and set SUI_PRIVATE_KEY
npm install
npm run dev

Endpoints
	•	GET /api/health
	•	POST /api/swap_deepbook (v0.1: skeleton; amountOut parsing may be TODO)

v0.1 focuses on wiring and safety boundaries.
v0.2+ will harden swap correctness, quote validation, and amountOut parsing.

---

# `ts-gateway/src/` 以下

## `ts-gateway/src/types.ts`

```ts
export type DeepSwapSide = "base_to_quote" | "quote_to_base";

export interface DeepSwapRequest {
  side: DeepSwapSide;
  poolKey: string;

  /**
   * v0.1 semantics:
   * - base_to_quote: amount = base amount in
   * - quote_to_base: amount = quote amount in
   */
  amount: number;

  /**
   * Deep incentives / routing parameter (optional for v0.1)
   */
  deepAmount: number;

  /**
   * Minimum output amount (slippage guard lives on caller side)
   */
  minOut: number;

  clientOrderId?: string;
}

export interface DeepSwapResponse {
  ok: boolean;
  side: DeepSwapSide;
  poolKey: string;

  amount: number;
  amountOut: number;

  txDigest?: string;
  clientOrderId?: string;

  errorMessage?: string;
}
```

---

## PR156: Auto Execution Policy (Aggressive + HardStop) v1

### Double-Key System
Execution is controlled by two keys that must BOTH be satisfied:
1. **Env Key**: `MERIDIAN_EXECUTION_ENABLED="true"` must be set
2. **Policy Key**: HardStop must not be active

Formula: `allowExecution = envOk && policyOk`

### Policy Status
- `ALLOW`: Both keys OK, execution allowed
- `SIM_ONLY`: Env disabled (envOk=false)
- `BLOCKED`: HardStop active (policyOk=false)
- `ERROR`: Policy evaluation failed

### Aggressive + HardStop Strategy
**Aggressive**: Don't stop for transient issues
- `BLOCK_IMPACT_HIGH`, `BLOCK_SLIPPAGE_HIGH`, `BLOCK_DEPTH_THIN` → Skip that round only
- `BLOCK_ORACLE_STALE` → Skip that round only
- `NO_ROUTE` → Skip that round (but track streak)

**HardStop**: Stop only when truly broken (with TTL auto-recovery)
- Oracle.ERROR × 3 consecutive → 30 min lock
- Simulation FAIL × 2 consecutive → 60 min lock
- Unexpected exception × 1 → 60 min lock
- NO_ROUTE × 10 consecutive → 15 min lock

### HardStop Auto-Recovery
All HardStops have TTL (Time To Live) and automatically release when expired.
- No manual intervention required for v1
- Future versions may add manual release

### Heartbeat Monitoring
System health check endpoint for continuous monitoring:
```typescript
{
  status: "OK" | "DEGRADED" | "CRITICAL" | "ERROR",
  executionAllowed: boolean,
  components: {
    oracle: "AVAILABLE" | "DEGRADED" | "ERROR",
    router: "AVAILABLE" | "DEGRADED" | "ERROR",
    simulation: "AVAILABLE" | "DEGRADED" | "ERROR"
  },
  hardStopActive: boolean,
  warnings: string[],
  timestamp: number
}
```

### Usage
```typescript
import { evaluateExecutionPolicy, runHeartbeat } from "./policy";

// Evaluate policy before execution
const policyResult = evaluateExecutionPolicy(
  {
    oracleStatus: "AVAILABLE",
    simulationStatus: "PASS",
    routeStatus: "AVAILABLE"
  },
  currentHardStopState
);

if (policyResult.status === "ALLOW") {
  // Execute transaction
} else {
  // Skip execution (SIM_ONLY or BLOCKED)
}

// Check system health
const heartbeat = runHeartbeat(input, policyResult);
console.log(`System status: ${heartbeat.status}`);
```

---

## PR157: Slippage + minOut Guard + Quote Consistency v1

### Purpose
Calculate minOut and validate quote integrity before swap execution using fixed rules. Conservative approach: prefer execution with appropriate slippage over unnecessary blocking.

### Fixed Slippage Rules
Slippage tolerance is calculated deterministically from:
1. **Template base** (risk level)
   - TPL_RISK_90: 150 bps
   - TPL_RISK_50: 100 bps
   - TPL_RISK_20: 75 bps
   - TPL_RISK_0: 50 bps

2. **Shock phase adjustment**
   - UP/DOWN_SHOCK: +150 bps
   - PRE_SHOCK: +100 bps
   - REVERSAL: +200 bps

3. **Stress adjustment**
   - STRESSED: +200 bps
   - TENSE: +100 bps

4. **Impact adjustment**
   - HIGH: +200 bps
   - MEDIUM: +100 bps
   - UNKNOWN: +200 bps

5. **Venue adjustment**
   - CETUS: +50 bps (AMM)
   - DEEPBOOK: 0 bps

**Hard limit**: 1500 bps (15%) → BLOCK if exceeded

### minOut Calculation
```
minOut = amountOut * (1 - slippageBps/10000)
```
Floor rounding for safety. If amountOut invalid → BLOCK_MINOUT_UNAVAILABLE

### Quote Consistency Check
Two requirements (both required):
1. **Freshness**: amountIn > 0, amountOut > 0, timestamp < 60s old
2. **Price consistency**: Implied price within ±5% of oracle price

If oracle unavailable → BLOCK_QUOTE_CONSISTENCY_UNAVAILABLE (conservative)

### New Block Reasons
- `BLOCK_MINOUT_UNAVAILABLE`: Cannot calculate minOut
- `BLOCK_SLIPPAGE_TOO_HIGH`: Exceeds 15% cap
- `BLOCK_QUOTE_INCONSISTENT`: Price deviation > ±5%
- `BLOCK_QUOTE_STALE`: Quote timestamp too old
- `BLOCK_QUOTE_CONSISTENCY_UNAVAILABLE`: Oracle unavailable for consistency check

### Usage
```typescript
import { calculateSlippageAndMinOut, checkQuoteConsistency } from "./rebalance";

// Calculate slippage and minOut
const slippageResult = calculateSlippageAndMinOut({
  templateId: "TPL_RISK_50",
  shockPhase: "PHASE_NORMAL",
  stress: "STRESS_CALM",
  impactLabel: "IMPACT_LOW",
  venue: "CETUS",
  amountOut: 1000000
});

// Check quote consistency
const consistencyResult = checkQuoteConsistency({
  quote: quoteResult,
  oraclePrices: { wbtcUsd: 45000, usdcUsd: 1.0 },
  oracleStatus: "AVAILABLE"
});
```

**Note**: Execution still disabled by default (PR156 policy controls execution)

---

## PR158: Position Drift Monitor + Cooldown Gate v1

### Purpose
Prevent unnecessary execution noise through drift monitoring and cooldown enforcement:
- **Drift**: Evaluate if weight drift is too small (< 7%) → NOOP (prevent micro-adjustments)
- **Cooldown**: Track last activity and block execution within cooldown period (10 min) → prevent rapid-fire execution

### Fixed Thresholds

**Drift Threshold**:
- minAbsDeltaToAct: 0.07 (7%)
- If abs(target.WBTC - current.WBTC) < 7% → driftTooSmall=true

**Cooldown Period**:
- cooldownMs: 600,000 (10 minutes)
- countSimulationAsActivity: true (default)

### Drift Monitor

Evaluates if position drift is actionable:

```typescript
import { evaluateDriftV1 } from "./rebalance/drift";

const driftResult = evaluateDriftV1(
  snapshot,
  { WBTC: 0.6, USDC: 0.4 }
);

if (driftResult.driftTooSmall) {
  // Skip rebalance (drift < 7%)
}
```

**Drift Status**:
- `AVAILABLE`: Drift evaluated successfully
- `UNKNOWN`: Weights unavailable (oracle failure)
- `ERROR`: Evaluation error

### Cooldown Gate

Tracks last activity and enforces cooldown period:

```typescript
import {
  initCooldownStateV1,
  evaluateCooldownV1,
  markActivityV1
} from "./rebalance/cooldown";

// Initialize state (first time)
let cooldownState = initCooldownStateV1();

// Evaluate cooldown
const cooldownResult = evaluateCooldownV1(cooldownState, Date.now());

if (cooldownResult.blocked) {
  // Skip execution (within cooldown period)
}

// After successful execution
cooldownState = markActivityV1(cooldownState, Date.now(), "EXECUTED");
```

**Cooldown Status**:
- `AVAILABLE`: Cooldown expired or no activity yet
- `BLOCKED`: Within cooldown period
- `UNKNOWN`: Cooldown state unavailable
- `ERROR`: Evaluation error

### Gate Integration

**Priority Order** (first-match-wins):
1. Upper-level prohibitions (FREEZE/STRESSED/SHOCK)
2. Execution impossibility (NO_ROUTE/ORACLE/SIMULATION)
3. **Cooldown check** (PR158)
4. **Drift check** (PR158)
5. Trade safety (GAS/NOTIONAL/IMPACT/SLIPPAGE/DEPTH)

**New Block Reasons**:
- `BLOCK_COOLDOWN_ACTIVE`: Within cooldown period
- `BLOCK_DRIFT_TOO_SMALL`: Drift below 7% threshold

**Approach B (Cooldown Unknown)**:
- If cooldown state unknown → WARN only, don't BLOCK
- `WARN_COOLDOWN_UNAVAILABLE`: Cooldown state missing

### Planner Integration

The planner automatically evaluates drift and overrides intent to NOOP if drift is too small:

```typescript
import { buildRebalancePlan } from "./rebalance/planner";

const plan = buildRebalancePlan(snapshot, "TPL_RISK_50", constraints);

// Drift metadata included in plan
console.log(plan.drift?.driftTooSmall); // true if drift < 7%
console.log(plan.intent); // "NOOP" if drift too small
```

### Executor Integration

Use helper functions to manage cooldown state:

```typescript
import {
  evaluateCooldownForPlan,
  updateCooldownAfterActivity
} from "./rebalance/executor";

// Add cooldown to plan
const planWithCooldown = evaluateCooldownForPlan(plan, cooldownState);

// After execution/simulation
const newCooldownState = updateCooldownAfterActivity(
  cooldownState,
  "EXECUTED"
);
```

### Usage Example

```typescript
// 1. Build plan (drift evaluated automatically)
const plan = buildRebalancePlan(snapshot, "TPL_RISK_50", constraints);

// 2. Evaluate cooldown and add to plan
const planWithCooldown = evaluateCooldownForPlan(plan, cooldownState);

// 3. Gate checks both drift and cooldown
const gateResult = runSafetyGateWithSimulation(
  planWithCooldown,
  route,
  signals,
  constraints,
  portfolio,
  simulation
);

// 4. After successful execution, update cooldown
if (executionResult.ok) {
  cooldownState = updateCooldownAfterActivity(cooldownState, "EXECUTED");
}
```

---

## PR159: Chunked Execution / TWAP-lite v1
## PR160: FAST Profile v1.1 - Optimized for Speed

### Purpose
Avoid self-induced market shocks by splitting large rebalances into multiple smaller chunks executed over time:
- **Problem**: $200k one-shot swap → high slippage/impact → self-induced SHOCK
- **Solution**: Split into ~$70k chunks with 10s intervals → faster but gradual execution
- **Philosophy**: "Holding BTC is not evil. Slow reactions are evil." → Execute decisively but gradually
- **PR160 Update**: Faster execution profile for operational efficiency (60s completion vs 10min)

### Fixed Parameters (Constitutional Constants)

**Chunking Parameters** (PR160: FAST Profile):
- MAX_NOTIONAL_USD_PER_RUN: 200,000 (aligned with PR153/155/156 cap)
- MAX_CHUNKS: 3 (PR160: reduced from 6)
- MIN_CHUNK_NOTIONAL_USD: 10,000
- TARGET_CHUNK_NOTIONAL_USD: 70,000 (PR160: increased from 50,000)

**Execution Parameters** (PR160: FAST Profile):
- CHUNK_INTERVAL_MS: 10,000 (PR160: 10 seconds, reduced from 30s)
- MAX_RUN_DURATION_MS: 60,000 (PR160: 60 seconds, reduced from 10 minutes)
- MAX_BLOCKED_STREAK: 2 (STOP after 2 consecutive BLOCKs)

### Chunking Logic

Build chunk plans with deterministic rules:

```typescript
import { buildChunkPlansV1 } from "./rebalance/chunking";

const runPlan = buildChunkPlansV1({
  totalNotionalUsd: 200000,
  templateId: "TPL_RISK_50",
  baseIntent: "INCREASE_WBTC",
});

// Result: 3 chunks (evenly distributed) (PR160: FAST profile)
console.log(runPlan.chunks.length); // 3
console.log(runPlan.chunks[0].notionalUsd); // 66667
console.log(runPlan.chunks[1].notionalUsd); // 66667
console.log(runPlan.chunks[2].notionalUsd); // 66666
```

**Chunking Rules** (PR160: Updated):
1. If baseIntent = NOOP → chunks = []
2. If totalNotionalUsd = 0 → chunks = []
3. If totalNotionalUsd > 200k → cap at 200k, warn
4. Calculate idealChunks = ceil(totalNotionalUsd / 70k)
5. Calculate numChunks = clamp(idealChunks, 1, 3)
6. Distribute notional evenly: baseChunk = floor(total / numChunks)
7. Add remainder (+1 USD) to first chunks
8. Skip chunks with notional < 10k (rare with max 3 chunks)

### Runner (TWAP-lite Execution)

Execute chunked plan with per-chunk refreshing:

```typescript
import { runChunkedExecutionV1 } from "./rebalance/runner";

const result = await runChunkedExecutionV1(runPlan, {
  getPortfolioSnapshot: async () => refreshPortfolio(),
  evaluateGate: async ({ chunkPlan, portfolio }) => runGate(chunkPlan, portfolio),
  evaluatePolicy: async ({ portfolio }) => checkPolicy(portfolio),
  buildTxDraft: async ({ chunkPlan, portfolio }) => buildDraft(chunkPlan, portfolio),
  executeTx: async ({ txDraft, policy }) => execute(txDraft, policy),
});

console.log(result.status); // "COMPLETED" | "STOPPED" | "ERROR"
console.log(result.chunkResults); // Array of chunk execution results
```

**Per-Chunk Execution Pipeline** (PR160: 10s intervals):
1. Sleep (10s interval, except first chunk)
2. Refresh portfolio snapshot
3. Evaluate gate (PR153/155/157/158)
4. Evaluate policy (PR156)
5. Build transaction draft
6. Execute or simulate

### STOP Conditions (Safe Defaults)

The runner will STOP the entire run when:

1. **Policy denies execution**:
   - MERIDIAN_EXECUTION_ENABLED not "true"
   - HardStop active (PR156)

2. **Critical gate BLOCK**:
   - BLOCK_ORACLE_UNAVAILABLE
   - BLOCK_ORACLE_STALE
   - BLOCK_IMPACT_HIGH
   - BLOCK_QUOTE_INCONSISTENT
   - BLOCK_NOTIONAL_UNAVAILABLE
   - BLOCK_NO_ROUTE

3. **Consecutive BLOCK streak**:
   - 2 consecutive non-critical BLOCKs → STOP

4. **Run duration exceeded** (PR160: 60s):
   - Elapsed time > 60 seconds → STOP

### SKIP Conditions (Continue to Next Chunk)

The runner will SKIP a chunk (but continue to next) when:

- BLOCK_DELTA_TOO_SMALL (micro-change)
- BLOCK_DRIFT_TOO_SMALL (drift < 7%)

### Non-Claims (What This Is NOT)

**TWAP-lite does NOT**:
- ❌ Learn from market behavior
- ❌ Optimize chunk sizes dynamically
- ❌ Predict future market conditions
- ❌ Implement strict TWAP (Time-Weighted Average Price)
- ❌ Adjust intervals based on market depth

**TWAP-lite DOES**:
- ✅ Use fixed parameters (deterministic)
- ✅ Refresh market data per chunk
- ✅ Stop on critical failures
- ✅ Respect double-key execution gate (PR156)
- ✅ Maintain label-only output (no numeric logs)

### Safety Guarantees

**Constitutional Constraints Maintained**:
- READ-ONLY: No learning, no optimization
- Double-key: Execution still requires env + policy approval
- Safe defaults: Uncertain → STOP
- Label-only: No numbers in reasons/warnings
- Defensive: Never throws, always returns RunResult

**Example: $200k Rebalance Flow** (PR160: FAST Profile)

```typescript
// 1. Plan: $200k → 3 chunks (~67k each)
const plan = buildChunkPlansV1({
  totalNotionalUsd: 200000,
  templateId: "TPL_RISK_50",
  baseIntent: "INCREASE_WBTC",
});

// 2. Execute with fast gradual execution (10s intervals, 60s max)
const result = await runChunkedExecutionV1(plan, deps);

// Result scenarios:
// - COMPLETED: All 3 chunks executed successfully (~30s total: 0s + 10s + 10s)
// - STOPPED: Critical BLOCK after chunk 2 (chunk 3 not attempted)
// - ERROR: Unexpected failure (defensive, no throw)
```

### Integration with Existing Systems

**Chunking respects all existing gates**:
- Drift monitor (PR158): Each chunk checks drift
- Cooldown (PR158): Each chunk checks cooldown
- Slippage (PR157): Each chunk recalculates minOut
- Policy (PR156): Each chunk checks HardStop
- Oracle (PR155): Each chunk requires fresh oracle data
- Gate (PR153): Each chunk passes all safety checks

**Execution flow** (PR160: 10s intervals):
```
Per chunk:
  ↓
Portfolio refresh
  ↓
Gate (FREEZE/SHOCK/ORACLE/SIM/COOLDOWN/DRIFT/TRADE_SAFETY)
  ↓
Policy (env key + HardStop)
  ↓
TxDraft build (with fresh quote)
  ↓
Execute or Simulate
  ↓
10s sleep (PR160: reduced from 30s)
  ↓
Next chunk (or STOP/COMPLETE)

Total time for 3 chunks: ~20s (0s + exec + 10s + exec + 10s + exec)
Max duration: 60s (PR160: reduced from 10min)
```

---

## PR161: TWAP-lite Phase Re-eval STOP + Per-Chunk Route Reselect v1

### Purpose
"React correctly" by stopping on dangerous phase escalations and reselecting routes per chunk:
- **Phase Re-eval STOP**: Mid-execution phase escalation detection with fixed STOP table
- **Route Reselection**: Mandatory fresh route selection for every chunk

### Phase STOP Policy (Fixed Decision Table)

**STOP Immediately When**:
1. `now = PHASE_UNKNOWN` → STOP_PHASE_UNKNOWN (data loss is unsafe)
2. `now = PHASE_ERROR` → STOP_PHASE_ERROR (observation failure)
3. `prev in {NORMAL, RECOVERY}` and `now = PRE_SHOCK` → STOP_PHASE_ESCALATED (escalation)
4. `prev = PRE_SHOCK` and `now in {UP_SHOCK, DOWN_SHOCK}` → STOP_PHASE_ESCALATED (escalation)
5. `prev = UP_SHOCK` and `now = UP_REVERSAL` → STOP_PHASE_CHANGED (template flip)
6. `prev = DOWN_SHOCK` and `now = DOWN_REVERSAL` → STOP_PHASE_CHANGED (template flip)
7. `prev = PRE_SHOCK` and `now in {UP_REVERSAL, DOWN_REVERSAL}` → STOP_PHASE_CHANGED (skip transition)

**NO STOP (Continue) When**:
- `now = PHASE_RECOVERY` → continue (de-escalation)
- `SHOCK → NORMAL` → continue (de-escalation)
- Same phase → continue
- First chunk (no previous phase) → continue

### Route Reselection (Per Chunk Mandatory)

**Fixed Requirement**:
- Every chunk MUST call `selectRoute()` with fresh market data
- Route may change between chunks (CETUS → DEEPBOOK or vice versa)
- Route change tracked in ChunkResult diagnostics: `routeSelected`, `routeChanged`

**Integration**:
```typescript
// Runner calls selectRoute per chunk (Step 1.6)
const routeResult = await selectRoute({
  chunkPlan,
  portfolio: freshPortfolio,
  phaseLabel: currentPhase,
  prevVenue: lastVenue,
});

// Diagnostics recorded in ChunkResult
chunkResult.routeSelected = routeResult.venue; // "CETUS" | "DEEPBOOK" | "NONE"
chunkResult.routeChanged = routeResult.venue !== lastVenue; // true if changed
```

### Execution Pipeline Update

**Per-Chunk Pipeline** (PR161 adds steps 1.5 and 1.6):
1. Sleep (10s interval, except first chunk)
2. Refresh portfolio snapshot
3. **1.5. Evaluate phase (NEW)**: Check for dangerous escalation
4. **1.6. Select route (NEW)**: Fresh route selection with market data
5. Evaluate gate (PR153/155/157/158)
6. Evaluate policy (PR156)
7. Build transaction draft
8. Execute or simulate

**STOP Trigger** (PR161 addition):
- Phase escalation detected (any of 7 STOP rules) → STOP_PHASE_ESCALATED/CHANGED/UNKNOWN/ERROR
- Run stops immediately, remaining chunks not executed

### Phase Label Types

```typescript
type PhaseLabel =
  | "PHASE_UNKNOWN"    // Data loss → STOP
  | "PHASE_NORMAL"     // Calm market
  | "PHASE_PRE_SHOCK"  // Early warning
  | "PHASE_UP_SHOCK"   // Upward shock
  | "PHASE_DOWN_SHOCK" // Downward shock
  | "PHASE_UP_REVERSAL"   // Reversal from up
  | "PHASE_DOWN_REVERSAL" // Reversal from down
  | "PHASE_RECOVERY"   // De-escalation
  | "PHASE_ERROR";     // Observation error → STOP
```

### Non-Claims (What This Is NOT)

**Phase Policy does NOT**:
- ❌ Predict future phase transitions
- ❌ Optimize execution timing based on phase
- ❌ Learn from historical phase patterns
- ❌ Dynamically adjust thresholds
- ❌ Implement optimal execution strategy

**Route Reselection does NOT**:
- ❌ Predict which route will be better
- ❌ Learn from previous route performance
- ❌ Optimize route selection dynamically
- ❌ Balance execution across venues
- ❌ Implement smart order routing

**Phase Policy DOES**:
- ✅ Use fixed STOP rules (no prediction, no learning)
- ✅ Detect dangerous escalations only
- ✅ Safe default: uncertain → STOP
- ✅ Label-only output (no numeric logging)
- ✅ Never throws (defensive)

**Route Reselection DOES**:
- ✅ Refresh route selection per chunk (mandatory)
- ✅ Use fresh market data (depth, oracle, signals)
- ✅ Track route changes for diagnostics
- ✅ Respect gate BLOCK_NO_ROUTE
- ✅ Label-only output

### Safety: STOP ≠ HardStop

**CRITICAL DISTINCTION**:
- **STOP** (PR161): Pause for re-planning (phase escalation detected)
  - Intent: "Market changed dramatically, let's re-evaluate template"
  - Action: Stop current run, return to planner for new decision
  - Recovery: Immediate (next planning cycle uses new phase)

- **HardStop** (PR156): System-level lockdown (system is broken)
  - Intent: "Something is fundamentally broken, lock down everything"
  - Action: Block ALL execution until TTL expires or manual release
  - Recovery: Time-based (15-60 min TTL) or manual intervention

**STOP does NOT activate HardStop**.
Phase escalation is expected market behavior, not system failure.

### Usage

```typescript
import { evaluatePhaseStopPolicyV1 } from "./rebalance/phasePolicy";

// Evaluate phase policy per chunk
const phaseDecision = evaluatePhaseStopPolicyV1(
  prevPhase,  // undefined if first chunk
  currentPhase
);

if (phaseDecision.shouldStop) {
  // Stop run: STOP_PHASE_ESCALATED/CHANGED/UNKNOWN/ERROR
  return {
    status: "STOPPED",
    reasons: [phaseDecision.reason, ...phaseDecision.warnings],
  };
}

// Continue to next chunk
```

### Example: 3-Chunk Run with Phase Escalation

```typescript
// Chunk 1: PHASE_NORMAL → Execute successfully
//   prevPhase: undefined, nowPhase: "PHASE_NORMAL" → NO_STOP
//   route: CETUS, routeChanged: false

// Chunk 2: PHASE_NORMAL → Execute successfully
//   prevPhase: "PHASE_NORMAL", nowPhase: "PHASE_NORMAL" → NO_STOP
//   route: DEEPBOOK, routeChanged: true (route switched)

// Chunk 3: PHASE_PRE_SHOCK → STOP immediately
//   prevPhase: "PHASE_NORMAL", nowPhase: "PHASE_PRE_SHOCK" → STOP_PHASE_ESCALATED
//   reasons: ["STOP_PHASE_ESCALATED", "WARN_PHASE_ESCALATED_TO_PRE_SHOCK"]
//   status: "STOPPED" (chunk 3 not executed)

// Result: RunResult.status = "STOPPED"
// Next planning cycle will use PHASE_PRE_SHOCK and select TPL_RISK_20 or TPL_RISK_0
```

### Integration with Existing Systems

**Phase evaluation respects**:
- Fixed observation pipeline (PR149/PR154): Phase labels come from external observation
- Constitutional constraints: READ-ONLY, no prediction, no learning
- Safe defaults: UNKNOWN/ERROR → STOP immediately

**Route reselection respects**:
- Route selection logic (PR155): Uses same selectRoute() function
- Gate integration (PR153): NO_ROUTE still triggers BLOCK
- Venue constraints: Only CETUS and DEEPBOOK supported

**Execution flow**:
```
Per chunk:
  ↓
Portfolio refresh
  ↓
Phase evaluation (PR161: NEW)
  ↓  [If STOP → exit immediately]
Route selection (PR161: NEW, fresh per chunk)
  ↓
Gate (FREEZE/SHOCK/ORACLE/SIM/COOLDOWN/DRIFT/TRADE_SAFETY)
  ↓
Policy (env key + HardStop)
  ↓
TxDraft build (with fresh quote)
  ↓
Execute or Simulate
  ↓
10s sleep
  ↓
Next chunk (or STOP/COMPLETE)
```

### Diagnostics (Label-Only)

**ChunkResult metadata** (PR161 additions):
```typescript
interface ChunkResult {
  // ... existing fields ...

  // Phase diagnostics (label-only)
  phaseLabel?: string;  // e.g., "PHASE_PRE_SHOCK"

  // Route diagnostics (label-only)
  routeSelected?: "CETUS" | "DEEPBOOK" | "NONE";
  routeChanged?: boolean;  // true if different from previous chunk
}
```

**Purpose**: Debugging and observability, NOT for decision-making (READ-ONLY)

---

## PR162: Partial Resume Policy v1

### Purpose
Define fixed "resume conditions" for stopped TWAP-lite runs to enable safe automatic resumption:
- **STOP ≠ Failure**: STOP means "wait until conditions improve", not termination
- **Fixed Decision Table**: Per-reason resume conditions (no learning, no prediction)
- **Safe Resumption**: Only resume when all safety conditions are met

### Resume Status

**Four possible states**:
- **RESUMABLE**: All conditions OK, can resume execution now
- **WAIT**: Waiting for specific condition to improve (oracle, gate, phase, route, etc.)
- **ABANDON**: Cannot resume, give up (duration exceeded, policy permanently denied)
- **UNKNOWN**: Insufficient inputs or evaluation error

### Fixed Resume Decision Table

**Priority order (first-match-wins)**:

**A. ABANDON (cannot resume)**:
1. `STOP_DURATION_EXCEEDED` → ABANDON (run took too long)
2. `STOP_POLICY_DENY` → ABANDON (env key missing, config issue)

**B. WAIT (wait for conditions)**:
3. `STOP_HARDSTOP_ACTIVE` + hardStop=true → WAIT (until HardStop releases)
4. `STOP_ORACLE_STALE` → WAIT (until oracle=AVAILABLE)
5. `STOP_ORACLE_ERROR` → WAIT (until oracle=AVAILABLE)
6. `STOP_NO_ROUTE` → WAIT (until routeAvailable=true)
7. `STOP_PHASE_POLICY` → WAIT (until phase=NORMAL/RECOVERY)
8. `STOP_QUOTE_STALE` → WAIT (until gate=PASS)
9. `STOP_QUOTE_INCONSISTENT` → WAIT (until gate=PASS)
10. `STOP_IMPACT_HIGH` → WAIT (until gate=PASS)
11. `STOP_SLIPPAGE_HIGH` → WAIT (until gate=PASS)
12. `STOP_DEPTH_THIN` → WAIT (until gate=PASS)
13. `STOP_BLOCKED_STREAK` → WAIT (until resumeAfterTs, 30s cooldown)

**C. RESUMABLE (can resume now)**:
14. All conditions OK:
    - policyEnvEnabled=true
    - hardStopActive=false
    - oracleStatus=AVAILABLE
    - gateStatus=PASS
    - phaseLabel in {NORMAL, RECOVERY}
    - routeAvailable=true
    → RESUMABLE

**D. UNKNOWN**:
15. Missing critical inputs / evaluation error → UNKNOWN

### Resume State (Observability Metadata)

When a run STOPs, a `ResumeState` is saved in `RunResult.resumeState`:

```typescript
interface ResumeState {
  status: "STOPPED";                 // constant
  stopReason: StopReason;            // label-only
  stopAtTs: number;                  // internal numeric only
  resumeAfterTs?: number;            // internal numeric only (for cooldowns)
  lastPhaseLabel?: string;           // label-only observability
  lastRoute?: string;                // label-only observability
  lastTemplateId?: string;           // label-only observability
  lastIntent?: string;               // label-only observability
  warnings: string[];                // label-only
}
```

**Important**: Numeric timestamps (`stopAtTs`, `resumeAfterTs`) are internal only—never appear in warnings/reasons/logs.

### Integration with Runner

**On STOP** (any of 11 stop scenarios):
- Runner creates `ResumeState` with `createResumeState()`
- Includes stop reason, timestamp, and observability metadata
- Adds `resumeState` to `RunResult`

**On Next Run** (future PR):
- Check if previous `ResumeState` exists
- Call `evaluateResumeV1(resumeState, currentInputs)`
- If RESUMABLE → continue run
- If WAIT → skip run, check again next tick
- If ABANDON → mark run as abandoned, don't retry
- If UNKNOWN → log warning, treat as WAIT

### Cooldown Periods (Fixed)

**Two stop reasons have automatic cooldowns**:
- `STOP_BLOCKED_STREAK`: 30 seconds (short pause before retry)
- `STOP_PHASE_POLICY`: 10 seconds (FAST, phase can change quickly)

These are set in `resumeAfterTs` and checked by policy.

### Non-Claims (What This Is NOT)

**Resume Policy does NOT**:
- ❌ Predict when conditions will improve
- ❌ Learn optimal retry timing from history
- ❌ Dynamically adjust cooldown periods
- ❌ Implement exponential backoff strategies
- ❌ Optimize execution scheduling

**Resume Policy DOES**:
- ✅ Use fixed decision table (no prediction, no learning)
- ✅ Check current conditions only (stateless evaluation)
- ✅ Safe defaults: uncertain → WAIT or UNKNOWN
- ✅ Label-only output (no numeric logs)
- ✅ Never throws (defensive)

### Safety: STOP ≠ HardStop

**CRITICAL DISTINCTION**:
- **STOP** (PR162): Pause until conditions improve
  - Intent: "Oracle is stale, let's wait for fresh data"
  - Action: Save resume state, check conditions on next tick
  - Recovery: Automatic when conditions improve (seconds to minutes)

- **HardStop** (PR156): System-level lockdown
  - Intent: "System is fundamentally broken, lock down everything"
  - Action: Block ALL execution until TTL expires
  - Recovery: Time-based (15-60 min TTL) or manual intervention

**STOP does NOT activate HardStop**.
Transient issues (stale oracle, phase escalation) are expected, not system failures.

### Usage

```typescript
import { evaluateResumeV1 } from "./rebalance/resumePolicy";

// After a run STOPs with resumeState
const resumeDecision = evaluateResumeV1(resumeState, {
  nowTs: Date.now(),
  oracleStatus: "AVAILABLE",
  gateStatus: "PASS",
  phaseLabel: "PHASE_NORMAL",
  routeAvailable: true,
  hardStopActive: false,
  policyEnvEnabled: true,
});

if (resumeDecision.status === "RESUMABLE") {
  // Safe to resume execution
} else if (resumeDecision.status === "WAIT") {
  // Wait for conditions to improve
  console.log(`Wait: ${resumeDecision.reasons.join(", ")}`);
  console.log(`Next check: ${resumeDecision.nextCheckHint}`); // SOON/NORMAL/SLOW
} else if (resumeDecision.status === "ABANDON") {
  // Cannot resume, give up
  console.log(`Abandon: ${resumeDecision.reasons.join(", ")}`);
}
```

### Example: Oracle Stale Recovery Flow

```typescript
// Chunk 1: Oracle goes stale during execution
//   status: "STOPPED", stopReason: "STOP_ORACLE_STALE"
//   resumeState saved with lastPhase="PHASE_NORMAL", lastRoute="CETUS"

// Next tick (10s later): Oracle still stale
//   evaluateResumeV1() → WAIT, reason: "REASON_WAIT_ORACLE_STALE"
//   nextCheckHint: "SOON" (oracle can recover quickly)
//   Action: Skip execution, check again next tick

// Next tick (20s later): Oracle recovered
//   oracleStatus: "AVAILABLE", gate: "PASS", phase: "NORMAL"
//   evaluateResumeV1() → RESUMABLE, reason: "REASON_RESUMABLE_ALL_CONDITIONS_OK"
//   Action: Resume execution from where it stopped
```

### Integration with Existing Systems

**Resume policy respects**:
- Phase evaluation (PR161): Wait until phase is safe (NORMAL/RECOVERY)
- Gate checks (PR153/155/157/158): Wait until gate passes
- Policy checks (PR156): Wait until HardStop releases and env key is set
- Route selection (PR155): Wait until route is available

**All conditions must be satisfied** for RESUMABLE status (conservative approach).

### Diagnostics (Label-Only)

**Stop Reasons** (all label-only):
```typescript
type StopReason =
  | "STOP_PHASE_POLICY"         // Phase escalated
  | "STOP_NO_ROUTE"             // No route available
  | "STOP_ORACLE_STALE"         // Oracle stale
  | "STOP_ORACLE_ERROR"         // Oracle error
  | "STOP_QUOTE_STALE"          // Quote stale
  | "STOP_QUOTE_INCONSISTENT"   // Quote inconsistent
  | "STOP_IMPACT_HIGH"          // Impact too high
  | "STOP_SLIPPAGE_HIGH"        // Slippage too high
  | "STOP_DEPTH_THIN"           // Depth too thin
  | "STOP_POLICY_DENY"          // Policy denied (env key)
  | "STOP_HARDSTOP_ACTIVE"      // HardStop active
  | "STOP_DURATION_EXCEEDED"    // Run took too long
  | "STOP_BLOCKED_STREAK"       // Consecutive blocks
  | "STOP_ERROR"                // Unexpected error
  | "STOP_UNKNOWN";             // Unknown reason
```

**Purpose**: Debugging and observability, NOT for decision-making (READ-ONLY)


---

## PR163: Supervisor Loop + Persistent State + Status CLI v1

### Purpose
Transform Meridian from "functions available" to "24/7 operational system":
- **Persistent State**: Save/restore HardStop, Cooldown, ResumeState, lastRun
- **Supervisor Loop**: Tick periodically, evaluate resume conditions, run when safe
- **Status CLI**: Monitor "what's happening now?" at a glance

### Persistent State Schema

**Saved to `~/.meridian/state.json` (configurable via `MERIDIAN_STATE_PATH`)**:

All state is label-only with internal timestamps. Numeric timestamps never appear in CLI output or logs.

### State Store (Atomic Writes)

File-based storage with defensive reads:
- Atomic writes: tmp→rename to prevent corruption
- Missing file → empty state (defensive default)
- Corrupted JSON → ERROR status + warnings (never throws)
- Forward-compatible: Unknown fields ignored

### Supervisor Loop (24/7 Tick)

Fixed tick flow evaluates policy, resume conditions, and executes TWAP when safe.

### Status CLI (Monitoring)

Display current state in label-only format:
```bash
npx ts-node src/cli/status.ts
node dist/cli/status.js
```

All output is label-only: No prices, balances, timestamps, or addresses.

### Non-Claims

Supervisor does NOT predict, learn, optimize, or provide trading advice.
Supervisor DOES use fixed tick logic and respect all existing safety systems.

**Purpose**: 24/7 operational readiness, NOT trading advice or execution signals

---

## PR164: Telemetry + Audit Log + Replay v1

### Purpose
Add observability to Meridian through append-only audit logging:
- **Telemetry Events**: Structured events emitted from Supervisor and Runner
- **Audit Log**: Append-only JSONL file with label-only events
- **Replay CLI**: Display recent events for troubleshooting and monitoring

### Constitutional Constraints
- **READ-ONLY**: Record facts only, no learning, no optimization
- **Label-only**: No numerics, no prices, no addresses in output
- **Defensive**: Telemetry failures never break execution
- **Append-only**: JSONL format, one event per line

### Event Types

**11 telemetry event types**:
- `SUPERVISOR_TICK`: Supervisor tick started
- `RESUME_EVAL`: Resume evaluation completed
- `RUN_START`: TWAP run started (reserved)
- `RUN_STOP`: TWAP run stopped
- `CHUNK_START`: Chunk execution started
- `CHUNK_RESULT`: Chunk execution completed
- `POLICY_BLOCK`: Policy blocked execution
- `GATE_BLOCK`: Gate blocked execution
- `ROUTE_SELECTED`: Route selected for chunk
- `ORACLE_STATUS`: Oracle status changed (reserved)
- `ERROR`: Error occurred

### Event Levels

**Three severity levels**:
- `INFO`: Normal operational events
- `WARN`: Warning conditions (blocks, stops)
- `ERROR`: Error conditions

### Event Structure

**MeridianEventV1**:
```typescript
{
  v: "v1",                    // Schema version
  ts: number,                 // Timestamp (internal only)
  level: "INFO" | "WARN" | "ERROR",
  type: TelemetryEventType,
  labels: Record<string, string | undefined>,
  warnings: string[]
}
```

### Guards (Forbidden Patterns)

Labels are sanitized to prevent leaking sensitive data:
- **Token addresses**: `0x...` → REDACTED
- **Prices**: `1234.56` → REDACTED
- **Trading vocab**: `buy`, `sell`, `swap`, `trade` → REDACTED
- **Prescriptive**: `should`, `must`, `recommend` → REDACTED
- **Numeric amounts**: Removed from labels

### Audit Log Format

**JSONL (JSON Lines)**:
- One event per line
- Append-only (never modified)
- Default path: `~/.meridian/events.log`
- Configurable via `MERIDIAN_EVENTS_PATH`

### Replay CLI

Display recent events:
```bash
# Default: 200 most recent events
npx ts-node src/cli/replay.ts

# Custom line count
npx ts-node src/cli/replay.ts --lines 500

# Filter by event type
npx ts-node src/cli/replay.ts --type GATE_BLOCK

# Filter by level
npx ts-node src/cli/replay.ts --level ERROR

# Combined filters
npx ts-node src/cli/replay.ts --type RUN_STOP --level WARN --lines 100

# Built version
node dist/cli/replay.js
```

### Label-Only Output

All CLI output is label-only with timestamp labels:
- `T_RECENT`: < 60 seconds ago
- `T_MIN`: 1-60 minutes ago
- `T_HOUR`: 1-24 hours ago
- `T_OLD`: > 24 hours ago

Example output:
```
=== Meridian Event Replay ===

EVENTS: 5

T_RECENT INFO  SUPERVISOR_TICK      action=TICK_START
T_RECENT INFO  CHUNK_START          chunk_id=chunk_1 chunk_index=1/3
T_RECENT INFO  ROUTE_SELECTED       route=CETUS route_changed=NO phase=PHASE_NORMAL
T_RECENT WARN  GATE_BLOCK           gate_reason=BLOCK_ORACLE_STALE consecutive_blocks=1
T_RECENT WARN  RUN_STOP             run_status=STOPPED stop_reason=STOP_ORACLE_STALE

=== End Replay ===
```

### Integration with Supervisor

**Supervisor emits events at key points**:
- `SUPERVISOR_TICK`: At start of each tick
- `POLICY_BLOCK`: When HardStop is active
- `RESUME_EVAL`: After resume evaluation

Events are emitted defensively (failures are caught and ignored).

### Integration with Runner

**Runner emits events during chunk execution**:
- `CHUNK_START`: At start of each chunk
- `ROUTE_SELECTED`: After route selection
- `GATE_BLOCK`: When gate blocks execution
- `CHUNK_RESULT`: After chunk completes (EXECUTED/SIMULATED/ERROR)
- `RUN_STOP`: When run stops (any stop reason)

All events include relevant labels (status, reason, phase, route).

### Usage

```typescript
import { createEventV1, appendEventV1 } from "./telemetry";

// Create event
const event = createEventV1("GATE_BLOCK", "WARN", {
  gate_reason: "BLOCK_ORACLE_STALE",
  consecutive_blocks: "1",
});

// Append to log (defensive)
await appendEventV1(event).catch(() => {
  // Telemetry failure doesn't break execution
});
```

### Reading Events

```typescript
import { readRecentEventsV1, readFilteredEventsV1 } from "./telemetry";

// Read recent events
const recent = await readRecentEventsV1({}, { maxLines: 200 });
console.log(`Found ${recent.events.length} events`);

// Filter by type
const gateBlocks = await readFilteredEventsV1({
  type: "GATE_BLOCK",
  maxLines: 100,
});

// Filter by level
const errors = await readFilteredEventsV1({
  level: "ERROR",
  maxLines: 50,
});
```

### Label-Only Formatting

```typescript
import { formatLabelOnlyLine } from "./telemetry";

const line = formatLabelOnlyLine(event);
// Output: "T_RECENT WARN  GATE_BLOCK           gate_reason=BLOCK_ORACLE_STALE"
```

### Non-Claims

**Telemetry does NOT**:
- ❌ Predict future events or failures
- ❌ Learn from historical patterns
- ❌ Optimize execution based on telemetry
- ❌ Provide trading recommendations
- ❌ Expose sensitive data (prices, balances, addresses)

**Telemetry DOES**:
- ✅ Record facts only (what happened, when)
- ✅ Use label-only output (no numerics in display)
- ✅ Fail gracefully (never breaks execution)
- ✅ Append-only (immutable audit trail)
- ✅ Support filtering and replay for debugging

### Safety Guarantees

**Defensive design**:
- Telemetry failures never throw exceptions
- Failures return warnings but don't stop execution
- Missing log file → empty array (not an error)
- Corrupted lines → skip with warning (continue parsing)

**Privacy protection**:
- Guards prevent token addresses in logs
- Guards prevent prices in logs
- Guards prevent trading vocabulary in logs
- Timestamp labels (T_RECENT) instead of numeric timestamps in output

### Environment Variables

- `MERIDIAN_EVENTS_PATH`: Log file path (default: `~/.meridian/events.log`)
- `MERIDIAN_EVENTS_MAXLINES`: Max lines for replay CLI (default: 200)

### Files

- `src/telemetry/types.ts`: Event types, levels, schema
- `src/telemetry/guards.ts`: Sanitization, validation, formatting
- `src/telemetry/eventLog.ts`: JSONL append-only log
- `src/telemetry/index.ts`: Barrel exports
- `src/cli/replay.ts`: Replay CLI tool
- `tests/pr164.telemetry_replay.test.ts`: 10 comprehensive tests

**Purpose**: Observability and debugging, NOT trading signals or execution advice

---

## PR165: Market Regime Snapshot Export v1

### Purpose
Export "what Meridian saw at that moment" for strategy verification and post-analysis:
- **Market Regime Snapshots**: Capture system state (phase, stress, template, gate, policy)
- **Append-only Log**: JSONL format (~/.meridian/snapshots.log)
- **CLI Display**: Label-only (no numerics, prices, or addresses)
- **Strategy Verification**: Replay decisions for improvement/comparison

### Constitutional Constraints
- **READ-ONLY**: Snapshots are observations, NOT recommendations or execution signals
- **Label-only**: CLI/telemetry display uses labels (numerics allowed in saved files)
- **Defensive**: Snapshot failures never break execution
- **Fixed rules**: No prediction, no optimization, no learning

### Snapshot Schema

**MarketRegimeSnapshotV1**:
```typescript
{
  version: "v1.0",
  kind: "REGIME_SNAPSHOT" | "RUN_SNAPSHOT" | "TICK_SNAPSHOT",
  status: "AVAILABLE" | "PARTIAL" | "ERROR",
  ts: number,                  // Timestamp (internal only)
  id: string,                  // Snapshot ID
  warnings: string[],          // Label-only warnings
  presence: {                  // Which components were available
    hasOracle: boolean,
    hasObservationLabels: boolean,
    hasShockPhase: boolean,
    hasStress: boolean,
    hasActionShape: boolean,
    hasTemplateId: boolean,
    hasRoute: boolean,
    hasGate: boolean,
    hasPolicy: boolean,
    hasHardStop: boolean,
    hasCooldown: boolean,
    hasDrift: boolean,
    hasResume: boolean
  },
  labels: {                    // Label-only domain
    shockPhase?: string,       // e.g., PHASE_UP_SHOCK
    stress?: string,           // CALM/TENSE/STRESSED
    actionShape?: string,      // FREEZE_STATE / CONSIDER_ONLY / ...
    templateId?: string,       // TPL_RISK_90 etc.
    route?: string,            // ROUTE_CETUS / ROUTE_DEEPBOOK / NONE
    gateDecision?: string,     // PASS / BLOCK / ERROR
    policyDecision?: string,   // ALLOW / DENY
    hardStop?: string,         // ACTIVE / INACTIVE
    // PR154 observation labels
    impulse?: string,
    thinning?: string,
    dominance?: string,
    absorption?: string
  },
  numerics?: {                 // Save-only (NEVER display in CLI)
    notionalUsd?: number,
    targetNotionalUsd?: number,
    oracleAgeMs?: number
  }
}
```

### Snapshot Status

**Three status levels**:
- **AVAILABLE**: All required components present (phase, stress, action, template, gate, policy)
- **PARTIAL**: Snapshot created but missing some components
- **ERROR**: Snapshot creation failed (but record still returned)

**Fixed AVAILABLE criteria**:
- hasShockPhase && hasStress && hasActionShape && hasTemplateId && hasGate && hasPolicy

### Storage Format

**JSONL (JSON Lines)**:
- One snapshot per line
- Append-only (never modified)
- Default path: `~/.meridian/snapshots.log`
- Configurable via `MERIDIAN_SNAPSHOTS_PATH`

### Snapshot CLI

Display recent snapshots:
```bash
# Default: 200 most recent snapshots
npx ts-node src/cli/snapshot.ts

# Custom tail count
npx ts-node src/cli/snapshot.ts --tail 50

# Filter by status
npx ts-node src/cli/snapshot.ts --level AVAILABLE

# JSON output (sanitized)
npx ts-node src/cli/snapshot.ts --json

# Built version
node dist/cli/snapshot.js
```

### Label-Only Display

All CLI output is label-only:
- Timestamp → `T_RECENT` / `T_MIN` / `T_HOUR` / `T_OLD`
- Snapshot ID → `HAS_ID` / `NO_ID`
- Numerics → REMOVED (not displayed)

Example output:
```
=== Meridian Snapshot CLI ===

SNAPSHOTS: 2

T_RECENT REGIME_SNAPSHOT AVAILABLE
  ID: HAS_ID
  Presence: SHOCK_PHASE, STRESS, ACTION, TEMPLATE, ROUTE, GATE, POLICY
  Labels: shockPhase=PHASE_NORMAL, stress=STRESS_CALM, actionShape=ACTION_NORMAL, templateId=TPL_RISK_50, route=ROUTE_CETUS, gateDecision=PASS, policyDecision=ALLOW

T_MIN REGIME_SNAPSHOT PARTIAL
  ID: HAS_ID
  Presence: SHOCK_PHASE, STRESS
  Labels: shockPhase=PHASE_PRE_SHOCK, stress=STRESS_TENSE
  Warnings: WARN_MISSING_COMPONENTS

=== End Snapshots ===
```

### Integration with Supervisor

**Supervisor emits snapshots at tick completion**:
- After all policy/gate/resume checks complete
- Snapshot saved to JSONL log (defensive)
- Telemetry event emitted: `SNAPSHOT_SAVED` or `SNAPSHOT_ERROR`
- Failures logged but don't abort tick

### Guards (Forbidden Patterns)

Snapshot labels/warnings are sanitized to prevent:
- **Token literals**: wBTC, USDC, SUI → REDACTED
- **Trading vocabulary**: buy, sell, swap, execute → REDACTED
- **Prescriptive language**: should, must, recommend → REDACTED
- **Addresses/prices**: 0x..., 123.45 → REDACTED

### Usage

```typescript
import {
  buildMarketRegimeSnapshotV1,
  appendSnapshotV1,
  SnapshotInputsV1,
} from "./snapshot";

// Build snapshot from current state
const inputs: SnapshotInputsV1 = {
  latest: {
    shockPhase: "PHASE_NORMAL",
    stress: "STRESS_CALM",
    actionShape: "ACTION_NORMAL",
    templateId: "TPL_RISK_50",
    gateDecision: "PASS",
    policyDecision: "ALLOW",
    // Numerics (save-only)
    numerics: {
      notionalUsd: 100000,
      oracleAgeMs: 5000,
    },
  },
};

const snapshot = await buildMarketRegimeSnapshotV1(inputs);

// Save snapshot (defensive)
await appendSnapshotV1(snapshot).catch(() => {
  // Snapshot failure doesn't break execution
});
```

### Reading Snapshots

```typescript
import {
  readRecentSnapshotsV1,
  readFilteredSnapshotsV1,
} from "./snapshot";

// Read recent snapshots
const recent = await readRecentSnapshotsV1({}, { maxLines: 200 });
console.log(`Found ${recent.snapshots.length} snapshots`);

// Filter by status
const available = await readFilteredSnapshotsV1({
  status: "AVAILABLE",
  maxLines: 100,
});

// Filter by kind
const regimeSnapshots = await readFilteredSnapshotsV1({
  kind: "REGIME_SNAPSHOT",
  maxLines: 50,
});
```

### Sanitization for Display

```typescript
import {
  sanitizeSnapshotForDisplay,
  formatSnapshotLabelOnlyLines,
} from "./snapshot/guards";

// Sanitize snapshot (removes numerics)
const sanitized = sanitizeSnapshotForDisplay(snapshot);
// sanitized.numerics → undefined (removed)
// sanitized.timeLabel → "T_RECENT" (not numeric ts)
// sanitized.idLabel → "HAS_ID" (not actual ID)

// Format as CLI lines
const lines = formatSnapshotLabelOnlyLines(sanitized);
lines.forEach((line) => console.log(line));
```

### Non-Claims

**Snapshots do NOT**:
- ❌ Predict future market conditions
- ❌ Provide trading recommendations
- ❌ Optimize execution strategies
- ❌ Learn from historical patterns
- ❌ Trigger execution or trading decisions

**Snapshots DO**:
- ✅ Record observed state (what Meridian saw)
- ✅ Enable strategy verification (reproducibility)
- ✅ Use label-only display (privacy protection)
- ✅ Fail gracefully (never break execution)
- ✅ Append-only storage (immutable audit trail)

### Safety Guarantees

**Defensive design**:
- Snapshot failures never throw exceptions
- Failures logged to telemetry (SNAPSHOT_ERROR)
- Missing components → PARTIAL status (not ERROR)
- Invalid inputs → ERROR record returned (not thrown)

**Privacy protection**:
- Guards prevent token names in display
- Guards prevent prices in display
- Guards prevent addresses in display
- Numerics allowed in saved files (for analysis)
- Numerics REMOVED in CLI/telemetry display

**Execution safety**:
- Snapshot is POST-execution (doesn't affect decisions)
- Snapshot failures don't abort supervisor tick
- Snapshot is observability, NOT control

### Environment Variables

- `MERIDIAN_SNAPSHOTS_PATH`: Log file path (default: `~/.meridian/snapshots.log`)
- `MERIDIAN_SNAPSHOTS_MAXLINES`: Max lines for CLI (default: 200)

### Files

- `src/snapshot/types.ts`: Snapshot schema, types, status
- `src/snapshot/guards.ts`: Sanitization, validation, display formatting
- `src/snapshot/exporter.ts`: Snapshot generation, JSONL storage
- `src/snapshot/index.ts`: Barrel exports
- `src/cli/snapshot.ts`: Snapshot CLI tool
- `tests/pr165.snapshot_export.test.ts`: 12 comprehensive tests

**Purpose**: Strategy verification and post-analysis, NOT trading signals or execution advice

---

## PR166: Snapshot Analysis Helper v1

### Purpose
Deterministic analysis of snapshot logs for strategy improvement through:
- **A) Frequency Analysis**: Phase/stress/template/gate distribution
- **B) Confusion Signals**: Regime misidentification indicators
- **C) Timing Analysis**: Phase transition timing and stop reasons

### Constitutional Constraints
- **READ-ONLY**: Analysis reads snapshot logs only, no execution
- **Label-only**: Normal output uses labels (numeric counts only in debug mode)
- **Defensive**: Never throws, always returns result (even on error)
- **Fixed rules**: No prediction, no optimization, no recommendations

### Analysis Categories

**A) Frequency Analysis**:
- Phase label distribution
- Stress label distribution
- Template ID distribution
- Gate decision distribution
- Block reason ranking (top N)

**B) Confusion Signals** (label-only detection):
- `CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT`: UP_REVERSAL/DOWN_SHOCK with TPL_RISK_90 frequent (>30% threshold)
- `CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT`: PRE_SHOCK but no template change
- `CONFUSION_GATE_BLOCK_DOMINATES`: BLOCK dominates PASS (>50% threshold)

**C) Timing Analysis**:
- Phase transitions (PRE_SHOCK → SHOCK, SHOCK → REVERSAL, REVERSAL → RECOVERY)
- Lag labels: `LAG_NONE` / `LAG_SHORT` (1-3 ticks) / `LAG_MEDIUM` (4-10 ticks) / `LAG_LONG` (11+ ticks)
- Stop reason breakdown: PHASE_POLICY / GATE / POLICY_HARDSTOP / DURATION / BLOCK_STREAK

### Analysis CLI

Run analysis on snapshot logs:
```bash
# Default: 200 most recent snapshots
npx ts-node src/cli/analyze.ts

# Custom tail count
npx ts-node src/cli/analyze.ts --tail 500

# Focus on confusion signals only
npx ts-node src/cli/analyze.ts --focus confusion

# JSON output (sanitized)
npx ts-node src/cli/analyze.ts --json

# Debug mode (allows numeric counts)
MERIDIAN_DEBUG=true npx ts-node src/cli/analyze.ts --tail 500

# Built version
node dist/cli/analyze.js
```

### Normal Mode vs Debug Mode

**Normal Mode** (default):
- Label-only output (no counts, no numerics)
- Presence/absence of patterns indicated by labels
- Example: `Snapshots: HAS_SNAPSHOTS` (not "Snapshots: 142")

**Debug Mode** (`MERIDIAN_DEBUG=true`):
- Numeric counts displayed for analysis
- Useful for detailed investigation
- Example: `Snapshots: 142` (actual count)
- **Note**: Addresses/secrets still sanitized (always)

### Example Output (Normal Mode)

```
=== Meridian Snapshot Analysis ===

Status: COMPLETE
Snapshots: HAS_SNAPSHOTS

=== Frequency Analysis ===
Phase Labels: PHASE_NORMAL, PHASE_PRE_SHOCK, PHASE_UP_SHOCK
Stress Labels: STRESS_CALM, STRESS_TENSE
Template IDs: TPL_RISK_50, TPL_RISK_20, TPL_RISK_90
Gate Decisions: PASS, BLOCK
Block Reasons (Top): BLOCK_ORACLE_STALE, BLOCK_IMPACT_HIGH

=== Confusion Signals ===
CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT: ACTIVE
  Reasons: REASON_SHOCK_PHASE_WITH_HIGH_RISK_TEMPLATE, RATIO_ABOVE_THRESHOLD

=== Timing Analysis ===
Phase Transitions:
  PHASE_NORMAL → PHASE_PRE_SHOCK: LAG_SHORT
  PHASE_PRE_SHOCK → PHASE_UP_SHOCK: LAG_MEDIUM
Stop Reasons: STOP_BY_PHASE_POLICY, STOP_BY_GATE

=== End Analysis ===
```

### Example Output (Focus: Confusion)

```bash
npx ts-node src/cli/analyze.ts --focus confusion
```

```
=== Confusion Signals Focus ===

CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT: ACTIVE
  Reasons: REASON_SHOCK_PHASE_WITH_HIGH_RISK_TEMPLATE, RATIO_ABOVE_THRESHOLD
  Details: {"dominantLabel":"TPL_RISK_90"}

=== End Focus ===
```

### Confusion Signal Thresholds (Fixed/Deterministic)

**1) CONFUSION_SHOCK_BUT_RISK_HIGH_FREQUENT**:
- Threshold: >30% of shock phase snapshots use TPL_RISK_90
- Rationale: High-risk template should be rare in reversal/shock phases

**2) CONFUSION_PRE_SHOCK_NO_TEMPLATE_SHIFT**:
- Threshold: PRE_SHOCK exists (>3 snapshots) but only 1 template ID
- Rationale: PRE_SHOCK should trigger template adjustment

**3) CONFUSION_GATE_BLOCK_DOMINATES**:
- Threshold: >50% of gate decisions are BLOCK
- Rationale: BLOCK should be minority (system should mostly run)
- Details: Categorizes block reasons (ORACLE / IMPACT / SLIPPAGE / COOLDOWN / DRIFT / PHASE_POLICY / POLICY)

### Timing Analysis Details

**Phase Transitions**:
- Tracks: `from` phase → `to` phase
- Lag: Tick count between transitions
- Lag Labels:
  - `LAG_NONE`: 0 ticks (immediate)
  - `LAG_SHORT`: 1-3 ticks
  - `LAG_MEDIUM`: 4-10 ticks
  - `LAG_LONG`: 11+ ticks

**Stop Reason Breakdown**:
- `STOP_BY_PHASE_POLICY`: Phase escalation (PRE_SHOCK → SHOCK, etc.)
- `STOP_BY_GATE`: Gate block (oracle stale, impact high, etc.)
- `STOP_BY_POLICY_HARDSTOP`: HardStop active
- `STOP_BY_DURATION`: Run duration exceeded
- `STOP_BY_BLOCK_STREAK`: Consecutive blocks exceeded
- `STOP_UNKNOWN`: Reason unclear

### Usage

```typescript
import { analyzeSnapshotsV1 } from "./analyze";
import { readRecentSnapshotsV1 } from "./snapshot";

// Read snapshots
const snapshotResult = await readRecentSnapshotsV1({}, { maxLines: 200 });

// Analyze snapshots
const analysis = await analyzeSnapshotsV1(snapshotResult.snapshots);

// Check confusion signals
for (const signal of analysis.confusionSignals) {
  if (signal.active) {
    console.log(`${signal.type}: ACTIVE`);
    console.log(`Reasons: ${signal.reasons.join(", ")}`);
  }
}

// Check timing
for (const transition of analysis.timing.transitions) {
  console.log(`${transition.from} → ${transition.to}: ${transition.lag}`);
}
```

### Sanitization for Display

```typescript
import { sanitizeAnalysisForDisplay, isDebugMode } from "./analyze/guards";

const debugMode = isDebugMode(); // MERIDIAN_DEBUG=true

// Sanitize for display (removes counts in normal mode)
const sanitized = sanitizeAnalysisForDisplay(analysis, debugMode);

// In normal mode:
// sanitized.snapshotCountLabel → "HAS_SNAPSHOTS" (not numeric count)
// sanitized.frequency.phaseLabels → string[] (no count field)

// In debug mode:
// analysis.snapshotCount → 142 (actual count)
// analysis.frequency.phaseLabels → FrequencyItem[] (with count field)
```

### Non-Claims

**Analysis does NOT**:
- ❌ Predict future market conditions
- ❌ Provide trading recommendations
- ❌ Optimize execution strategies
- ❌ Learn from patterns (just reports observed patterns)
- ❌ Trigger execution or trading decisions

**Analysis DOES**:
- ✅ Report observed patterns (frequency, confusion, timing)
- ✅ Use fixed thresholds (deterministic, no adaptation)
- ✅ Support strategy improvement (manual review)
- ✅ Fail gracefully (never throws)
- ✅ Respect label-only constraints (normal mode)

### Safety Guarantees

**Defensive design**:
- Analysis never throws exceptions
- Empty input → PARTIAL status with warnings
- Invalid input → ERROR status with minimal result
- Always returns AnalysisResultV1 (defensive)

**Privacy protection**:
- Normal mode: label-only (no counts)
- Debug mode: allows counts (but not addresses/secrets)
- Guards sanitize: token literals, trading vocab, prescriptive language
- Addresses always REDACTED (even in debug mode)

**Read-only operation**:
- Analysis reads snapshot logs only
- No execution, no trading, no state modification
- Post-hoc analysis for strategy improvement

### Environment Variables

- `MERIDIAN_DEBUG`: Set to "true" to enable debug mode (numeric counts)
- `MERIDIAN_SNAPSHOTS_PATH`: Snapshot log path (default: `~/.meridian/snapshots.log`)
- `MERIDIAN_SNAPSHOTS_MAXLINES`: Max lines for analysis (default: 200)

### Files

- `src/analyze/types.ts`: Analysis result types, signal types, lag labels
- `src/analyze/guards.ts`: Sanitization, validation, label-only formatting
- `src/analyze/analyzer.ts`: Core analysis logic (frequency, confusion, timing)
- `src/analyze/index.ts`: Barrel exports
- `src/cli/analyze.ts`: Analysis CLI tool
- `tests/pr166.analyze.test.ts`: 12 comprehensive tests

**Purpose**: Strategy improvement through deterministic analysis, NOT trading signals or execution advice

---

## PR167: Improvement Proposal Generator v1

### Purpose
Generate fixed-rule improvement proposals from snapshot analysis through:
- **P0 Proposals**: Gate threshold degradation (reduce blocks)
- **P1 Proposals**: Template/phase/gate policy restrictions (reduce confusion)
- **P2 Proposals**: Observable improvements (logging, monitoring)

### Constitutional Constraints
- **READ-ONLY**: Proposals are suggestions, not actions
- **Label-only**: Normal output uses labels (numeric counts only in debug mode)
- **Fixed rules**: All triggers and proposals are predetermined
- **Policy-first**: P0 = degrade policy, P1 = template/gate policy, P2 = observable
- **Defensive**: Never throws, always returns result

### Proposal Priorities

**P0 (Highest)**: Degrade gate thresholds to reduce blocks
- `P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE`
- `P0_REDUCE_IMPACT_BLOCKS_DEGRADE`
- `P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE`
- `P0_REDUCE_DRIFT_BLOCKS_DEGRADE`
- `P0_REDUCE_COOLDOWN_BLOCKS_DEGRADE`

**P1**: Template/gate policy restrictions
- `P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT`
- `P1_PRE_SHOCK_NO_SHIFT_TEMPLATE_POLICY_TRIGGER`
- `P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW`
- `P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW`

**P2**: Observable improvements
- `P2_FREQUENT_TRANSITIONS_OBSERVABLE_LOG`
- `P2_LAG_LONG_OBSERVABLE_LOG`
- `P2_HARDSTOP_FREQUENT_OBSERVABLE_LOG`

### Fixed Triggers

**Confusion Signals** (from PR166):
- `TRG_GATE_BLOCK_DOMINATES`: Gate BLOCK dominates PASS (>50%)
- `TRG_SHOCK_RISK90_OVERUSE`: SHOCK phases with TPL_RISK_90 frequent (>30%)
- `TRG_PRE_SHOCK_NO_SHIFT`: PRE_SHOCK without template shift

**Frequency Patterns**:
- `TRG_ORACLE_STALE_TOP`: ORACLE_STALE is top block reason
- `TRG_IMPACT_HIGH_TOP`: IMPACT_HIGH is top block reason
- `TRG_SLIPPAGE_HIGH_TOP`: SLIPPAGE_HIGH is top block reason
- `TRG_DRIFT_HIGH_TOP`: DRIFT_HIGH is top block reason
- `TRG_COOLDOWN_TOP`: COOLDOWN is top block reason

**Timing Patterns**:
- `TRG_PHASE_ESCALATION_FREQUENT`: Phase escalation blocks in top 3
- `TRG_TRANSITIONS_FREQUENT`: Phase transitions with LAG_SHORT majority (>50%)
- `TRG_LAG_LONG_FREQUENT`: LAG_LONG transitions frequent (>20%)
- `TRG_HARDSTOP_FREQUENT`: HardStop in top 3 stop reasons

### Proposal CLI

Generate proposals from snapshot analysis:
```bash
# Default: 200 most recent snapshots
npx ts-node src/cli/propose.ts

# Custom tail count
npx ts-node src/cli/propose.ts --tail 500

# Filter by priority (P0 only)
npx ts-node src/cli/propose.ts --priority P0

# JSON output (sanitized)
npx ts-node src/cli/propose.ts --json

# Debug mode (allows numeric counts)
MERIDIAN_DEBUG=true npx ts-node src/cli/propose.ts --tail 500

# Built version
node dist/cli/propose.js
```

### Normal Mode vs Debug Mode

**Normal Mode** (default):
- Label-only output (no counts, no numerics)
- triggered_by shown as `HAS_TRIGGERS` / `NO_TRIGGERS`
- Example: `Triggered By: HAS_TRIGGERS` (not list of IDs)

**Debug Mode** (`MERIDIAN_DEBUG=true`):
- Full trigger IDs displayed
- Numeric counts displayed
- Example: `Triggered By: TRG_GATE_BLOCK_DOMINATES, TRG_ORACLE_STALE_TOP`

### Example Output (Normal Mode)

```
=== Improvement Proposals v1 ===

Status: AVAILABLE
Snapshot Count: HAS_SNAPSHOTS

--- P0: Degrade Policy (Highest Priority) ---

[P0] DEGRADE_ORACLE_STALE_THRESHOLD
  ID: P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
  Category: GATE_POLICY

  Rationale:
    - GATE_BLOCK_DOMINATES_WITH_ORACLE_CATEGORY
    - ORACLE_STALE_IS_TOP_BLOCK_REASON
    - REDUCING_STALE_THRESHOLD_MAY_INCREASE_PASS_RATIO

  Expected Effects:
    - REDUCE_ORACLE_STALE_BLOCKS
    - INCREASE_GATE_PASS_RATIO
    - ALLOW_MORE_RECENT_ORACLE_DATA

  Side Effects:
    - MAY_INCREASE_STALE_DATA_RISK
    - MAY_DEGRADE_EXECUTION_QUALITY

  Safe Guards:
    - MONITOR_ORACLE_AGE_DISTRIBUTION
    - TEST_IN_DRY_RUN_MODE
    - SET_MINIMUM_THRESHOLD

  Applies When: WHEN_GATE_BLOCK_RATIO_HIGH_AND_ORACLE_STALE_TOP_AND_ORACLE_CATEGORY

---

--- P1: Template/Gate Policy ---

[P1] RESTRICT_TPL_RISK_90_IN_SHOCK_PHASES
  ID: P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT
  Category: TEMPLATE_POLICY

  Rationale:
    - SHOCK_PHASES_WITH_TPL_RISK_90_FREQUENT
    - HIGH_RISK_TEMPLATE_IN_SHOCK_IS_CONFUSION
    - RESTRICTING_TPL_RISK_90_MAY_REDUCE_CONFUSION

  Expected Effects:
    - REDUCE_TPL_RISK_90_IN_SHOCK
    - INCREASE_TEMPLATE_CONSISTENCY
    - REDUCE_CONFUSION_SIGNAL

  Side Effects:
    - MAY_REDUCE_AVAILABLE_TEMPLATE_OPTIONS
    - MAY_REQUIRE_NEW_TEMPLATE_LOGIC

  Safe Guards:
    - MONITOR_TEMPLATE_DISTRIBUTION
    - TEST_IN_DRY_RUN_MODE
    - ENSURE_ALTERNATIVE_TEMPLATES_EXIST

  Applies When: WHEN_SHOCK_PHASES_WITH_TPL_RISK_90_RATIO_ABOVE_THRESHOLD

---

=== End Proposals ===
```

### Proposal Structure

Each proposal includes:
- **ID**: Fixed proposal identifier
- **Priority**: P0 (highest) > P1 > P2
- **Category**: GATE_POLICY / TEMPLATE_POLICY / PHASE_POLICY / COOLDOWN_POLICY / HARDSTOP_POLICY / OBSERVABLE
- **Title**: Label-only title (no numerics)
- **Rationale**: Why this proposal exists (label-only)
- **Expected Effects**: What should happen (label-only)
- **Side Effects**: Potential risks (label-only)
- **Safe Guards**: How to mitigate side effects (label-only)
- **Applies When**: Trigger conditions (label-only)
- **Triggered By**: Which triggers activated this proposal (hidden in normal mode)

### Usage

```typescript
import { analyzeSnapshotsV1 } from "./analyze";
import { generateProposalsV1 } from "./propose";
import { readRecentSnapshotsV1 } from "./snapshot";

// Read and analyze snapshots
const snapshotResult = await readRecentSnapshotsV1({}, { maxLines: 200 });
const analysis = await analyzeSnapshotsV1(snapshotResult.snapshots);

// Generate proposals
const proposeResult = await generateProposalsV1(analysis);

// Check P0 proposals (highest priority)
const p0Proposals = proposeResult.proposals.filter((p) => p.priority === "P0");

for (const proposal of p0Proposals) {
  console.log(`[${proposal.priority}] ${proposal.title}`);
  console.log(`  Category: ${proposal.category}`);
  console.log(`  Expected Effects: ${proposal.expected_effects.join(", ")}`);
  console.log(`  Safe Guards: ${proposal.safe_guards.join(", ")}`);
}
```

### Sanitization for Display

```typescript
import { sanitizeProposeResultForDisplay, isDebugMode } from "./propose/guards";

const debugMode = isDebugMode(); // MERIDIAN_DEBUG=true

// Sanitize for display (removes counts in normal mode)
const sanitized = sanitizeProposeResultForDisplay(proposeResult, debugMode);

// In normal mode:
// sanitized.ts_label → "HAS_TIMESTAMP" (not numeric timestamp)
// sanitized.proposals[0].triggered_by_count → "HAS_TRIGGERS" (not array)

// In debug mode:
// proposeResult.ts → 1701234567890 (actual timestamp)
// proposeResult.proposals[0].triggered_by → ["TRG_GATE_BLOCK_DOMINATES", "TRG_ORACLE_STALE_TOP"]
```

### Non-Claims

**Proposals do NOT**:
- ❌ Automatically execute changes
- ❌ Provide trading advice
- ❌ Predict future outcomes
- ❌ Optimize strategies (just suggest based on observed patterns)
- ❌ Learn from patterns (fixed rules only)

**Proposals DO**:
- ✅ Suggest policy adjustments based on fixed triggers
- ✅ Use predetermined thresholds (deterministic)
- ✅ Support manual strategy improvement
- ✅ Fail gracefully (never throws)
- ✅ Respect label-only constraints (normal mode)

### Safety Guarantees

**Defensive design**:
- Proposal generation never throws exceptions
- Invalid analysis → ERROR status with empty proposals
- No triggers active → NO_PROPOSALS status
- Always returns ProposeResultV1 (defensive)

**Privacy protection**:
- Normal mode: label-only (no counts)
- Debug mode: allows trigger IDs (but not addresses/secrets)
- Guards sanitize: token literals, trading vocab, prescriptive language
- Addresses always REDACTED (even in debug mode)

**Read-only operation**:
- Proposals are suggestions only
- No execution, no trading, no state modification
- Manual review required before implementation

### Environment Variables

- `MERIDIAN_DEBUG`: Set to "true" to enable debug mode (full trigger IDs)
- `MERIDIAN_SNAPSHOTS_PATH`: Snapshot log path (default: `~/.meridian/snapshots.log`)
- `MERIDIAN_SNAPSHOTS_MAXLINES`: Max lines for analysis (default: 200)

### Files

- `src/propose/types.ts`: Proposal types, priority types, trigger types
- `src/propose/guards.ts`: Sanitization, validation, label-only formatting
- `src/propose/rules.ts`: Fixed trigger rules and proposal templates
- `src/propose/proposer.ts`: Core proposal engine (trigger evaluation)
- `src/propose/index.ts`: Barrel exports
- `src/cli/propose.ts`: Proposal CLI tool
- `tests/pr167.propose.test.ts`: 12 comprehensive tests

**Purpose**: Strategy improvement through fixed-rule proposals, NOT automatic optimization or trading advice

---

## PR168: Policy-First Adoption Loop (PatchPlan + ReplayCompare) v1

### Purpose
Complete the improvement cycle by converting proposals into patch plans and comparing before/after via snapshot replay:
- **PatchPlan**: Convert proposals into concrete specification diffs (1-3 ops)
- **ReplayCompare**: Simulate before/after metrics without code changes
- **Decision**: ADOPT / HOLD / REJECT based on fixed rules

### Constitutional Constraints
- **READ-ONLY**: No automatic application (proposals and comparison only)
- **Policy-First**: Changes that reduce safety are PATCH_NOT_ALLOWED → REJECT
- **Label-only**: Normal output uses labels (numeric counts only in debug mode)
- **Defensive**: Never throws, always returns result
- **Deterministic**: Fixed rules only (no learning, no optimization)

### Adoption Flow

**Complete Flow** (PR165 → PR166 → PR167 → PR168):
1. **PR165**: Read snapshots from log
2. **PR166**: Analyze snapshots (frequency, confusion, timing)
3. **PR167**: Generate improvement proposals (P0/P1/P2)
4. **PR168**: Select proposal → Build patch plan → Simulate replay → Decide

**PR168 Steps**:
1. Select top proposal by priority (P0 > P1 > P2)
2. Build patch plan (map proposal to ops)
3. Simulate replay compare (virtual remapping)
4. Decide ADOPT/HOLD/REJECT (fixed decision rules)

### Patch Kinds

**Allowed Patches**:
- `PATCH_PHASE_POLICY`: Phase escalation/resume policy changes
- `PATCH_GATE_ORDER`: Gate evaluation order changes (BLOCK → SKIP, not EXECUTE)
- `PATCH_ROUTER_TIEBREAK`: Router tie-break logic changes
- `PATCH_SLIPPAGE_RULES`: Slippage calculation rule changes (logging only)
- `PATCH_COOLDOWN_RULES`: Cooldown duration/behavior changes (logging only)
- `PATCH_DRIFT_RULES`: Drift threshold changes (logging only)

**NOT ALLOWED Patches** (reduce safety):
- `PATCH_NOT_ALLOWED`: Used for proposals that reduce safety
  - Example: Degrade oracle stale threshold (would allow stale execution)
  - Example: Increase slippage tolerance (would allow higher slippage)
  - Example: Reduce cooldown duration (would reduce observation time)

**Policy-First Principle**: Any change that reduces safety guardrails is automatically marked as PATCH_NOT_ALLOWED and rejected.

### Patch Operations

Each patch plan contains 1-3 operations (keep it small):
- **kind**: Patch type (PATCH_PHASE_POLICY, etc.)
- **target**: Target component (PHASE_POLICY, GATE, etc.)
- **opId**: Fixed operation identifier (OP_PHASE_RECOVERY_RESUME_V1)
- **change**: Label-only description (REMAP_PHASE_POLICY_STOP_TO_WAIT)
- **safety**: Safety guarantees (KEEP_DOUBLE_KEY, KEEP_LABEL_ONLY, etc.)
- **notAllowedReason**: Reason for rejection (if NOT_ALLOWED)

### Virtual Remapping (Replay Compare)

Replay compare simulates "what would happen if patch was applied" WITHOUT modifying code:

**PATCH_PHASE_POLICY**:
- Remaps: `STOP_BY_PHASE_POLICY` → `WAIT_RESUME` (not EXECUTE)
- Effect: Reduces phase policy stops in replay analysis

**PATCH_GATE_ORDER**:
- Remaps: Minor blocks (DRIFT_SMALL, DELTA_SMALL) → `SKIP` (not EXECUTE)
- Effect: Reduces gate block ratio in replay analysis

**PATCH_ORACLE_FRESHNESS**:
- Remaps: `BLOCK_ORACLE_STALE` → `WAIT_RESUME` (not EXECUTE)
- Effect: Reduces oracle stale blocks (but still blocked, just category change)

**Key Principle**: Virtual remapping NEVER converts blocks to EXECUTE. It only changes categorization (STOP → WAIT, BLOCK → SKIP) to simulate policy adjustments.

### Compare Signals

**Improvement Signals**:
- `IMPROVED_BLOCK_DOMINANCE`: Gate BLOCK ratio decreased (>5%)
- `IMPROVED_STOP_BY_PHASE_POLICY`: Phase policy stops decreased
- `IMPROVED_ORACLE_STALE_RATE`: Oracle stale blocks decreased
- `IMPROVED_IMPACT_BLOCK_RATE`: Impact blocks decreased
- `IMPROVED_SLIPPAGE_BLOCK_RATE`: Slippage blocks decreased
- `IMPROVED_COOLDOWN_BLOCK_RATE`: Cooldown blocks decreased
- `IMPROVED_DRIFT_NOOP_RATE`: Drift no-op rate decreased

**Worsening Signals**:
- `WORSENED_BLOCK_DOMINANCE`: Gate BLOCK ratio increased (>5%)
- `WORSENED_STOP_UNKNOWN`: Unknown stops increased

**Other Signals**:
- `NO_CHANGE`: No significant change detected
- `COMPARE_UNAVAILABLE`: Comparison failed or insufficient data

### Decision Rules

Fixed decision rules (deterministic):

**REJECT** (do not adopt):
- Patch plan contains `PATCH_NOT_ALLOWED` operations
- Reason: Would reduce safety

**HOLD** (needs review):
- Compare unavailable (cannot verify improvement)
- Worsening signal detected (WORSENED_*)
- No change + P1/P2 priority (require clear improvement)

**ADOPT** (can be adopted):
- Improvement signal detected (IMPROVED_*) + no worsening
- No change + P0 priority (accept no worsening)

**Priority Bias**:
- P0: ADOPT-leaning (high confidence in critical changes)
- P1/P2: HOLD-leaning (require clear improvement)

### Adoption CLI

Run complete adoption loop:
```bash
# Default: 200 most recent snapshots, P0 priority
npx ts-node src/cli/adopt.ts

# Custom tail count
npx ts-node src/cli/adopt.ts --tail 500

# Filter by priority (P0, P1, or P2)
npx ts-node src/cli/adopt.ts --priority P1

# JSON output (sanitized)
npx ts-node src/cli/adopt.ts --json

# Debug mode (allows numeric counts)
MERIDIAN_DEBUG=true npx ts-node src/cli/adopt.ts --tail 500

# Built version
node dist/cli/adopt.js
```

### Normal Mode vs Debug Mode

**Normal Mode** (default):
- Label-only output (no counts, no numerics)
- Operations shown as count labels (`HAS_OPS` / `NO_OPS`)
- Example: `Operations: HAS_OPS` (not "Operations: 2")

**Debug Mode** (`MERIDIAN_DEBUG=true`):
- Full operation details displayed
- Numeric counts displayed
- Example: `Operations: 2` with full op details

### Example Output (Normal Mode)

```
=== Policy-First Adoption Loop v1 ===

Status: COMPLETE
Decision: ADOPT
Priority: P1
Proposal ID: P1_SHOCK_RISK90_OVERUSE_TEMPLATE_POLICY_RESTRICT

--- Patch Plan ---

Status: COMPLETE
Operations: 1

[PATCH_PHASE_POLICY]
  Target: PHASE_POLICY
  Op ID: OP_SHOCK_RISK90_RESTRICT_V1
  Change: RESTRICT_TPL_RISK_90_IN_SHOCK_REVERSAL
  Safety: KEEP_DOUBLE_KEY, KEEP_LABEL_ONLY, KEEP_BLOCK_ON_UNCERTAIN

--- Replay Compare ---

Status: COMPLETE
Window: TAIL_200

Before:
  - GATE_BLOCK_FREQUENT
  - TOP_BLOCK_BLOCK_ORACLE_STALE
  - PHASE_POLICY_STOPS_PRESENT

After:
  - GATE_BLOCK_REDUCED
  - TOP_BLOCK_BLOCK_ORACLE_STALE
  - PHASE_POLICY_STOPS_REDUCED

Signals:
  - IMPROVED_BLOCK_DOMINANCE
  - IMPROVED_STOP_BY_PHASE_POLICY

--- Decision Reasons ---

  - ADOPT_IMPROVED_WITHOUT_WORSENING

=== End Adoption ===
```

### Usage

```typescript
import { adoptImprovementV1 } from "./adopt";
import { readRecentSnapshotsV1 } from "./snapshot";

// Read snapshots
const snapshotResult = await readRecentSnapshotsV1({}, { maxLines: 200 });

// Adopt improvement (complete flow)
const adoptResult = await adoptImprovementV1(
  snapshotResult.snapshots,
  "P0", // priority filter
  200   // tail count
);

// Check decision
console.log(`Decision: ${adoptResult.decision}`);
console.log(`Reasons: ${adoptResult.reasons.join(", ")}`);

// Check patch plan
for (const op of adoptResult.patchPlan.ops) {
  console.log(`[${op.kind}] ${op.change}`);
}

// Check comparison
for (const signal of adoptResult.compare.signals) {
  console.log(`Signal: ${signal}`);
}
```

### Non-Claims

**Adoption does NOT**:
- ❌ Automatically apply patches (manual implementation required)
- ❌ Modify code or execute changes
- ❌ Provide trading advice or execution decisions
- ❌ Learn from patterns (fixed rules only)
- ❌ Predict future outcomes

**Adoption DOES**:
- ✅ Convert proposals into concrete patch plans
- ✅ Simulate before/after comparison via replay
- ✅ Decide ADOPT/HOLD/REJECT based on fixed rules
- ✅ Enforce Policy-First (reject safety reductions)
- ✅ Fail gracefully (never throws)
- ✅ Respect label-only constraints (normal mode)

### Safety Guarantees

**Defensive design**:
- Adoption never throws exceptions
- Invalid input → ERROR status with HOLD decision
- No proposals → HOLD decision
- Always returns AdoptResultV1 (defensive)

**Privacy protection**:
- Normal mode: label-only (no counts)
- Debug mode: allows operation details (but not addresses/secrets)
- Guards sanitize: token literals, trading vocab, prescriptive language
- Addresses always REDACTED (even in debug mode)

**Read-only operation**:
- No automatic application (proposals and comparison only)
- Manual implementation required for adoption
- No execution, no trading, no state modification

**Policy-First enforcement**:
- PATCH_NOT_ALLOWED for safety reductions
- Automatic REJECT for safety violations
- Virtual remapping NEVER enables execution (only categorization changes)

### Environment Variables

- `MERIDIAN_DEBUG`: Set to "true" to enable debug mode (full operation details)
- `MERIDIAN_SNAPSHOTS_PATH`: Snapshot log path (default: `~/.meridian/snapshots.log`)
- `MERIDIAN_SNAPSHOTS_MAXLINES`: Max lines for analysis (default: 200)

### Files

- `src/adopt/types.ts`: Adoption types, patch types, decision types
- `src/adopt/guards.ts`: Sanitization, validation, label-only formatting
- `src/adopt/rules.ts`: Fixed proposal-to-patch mapping rules
- `src/adopt/patcher.ts`: Proposal selection and patch plan generation
- `src/adopt/replay.ts`: Virtual remapping and replay comparison
- `src/adopt/adopter.ts`: Main adoption engine and decision logic
- `src/adopt/index.ts`: Barrel exports
- `src/cli/adopt.ts`: Adoption CLI tool
- `tests/pr168.adopt_patch_replay.test.ts`: 12 comprehensive tests

**Purpose**: Close the improvement cycle through Policy-First adoption with replay verification, NOT automatic optimization or code modification

---

## PR169: Policy Attribution Graph v1

### Purpose
Identify causal chains (attribution paths) that lead to outcomes like BLOCK, STOP, etc.
While PR166/167/168 detect "results" (BLOCK/STOP dominance), PR169 identifies **"why"** by analyzing causal chains:
- Example: `PHASE_PRE_SHOCK → PHASE_POLICY_STOP → STOP` is frequent
- Example: `ORACLE_STALE → GATE_BLOCK → STOP` dominates
- Example: `ROUTE_CHANGE → IMPACT_HIGH → BLOCK` is rare

This provides the **"where to fix"** that makes PR167's proposals answerable with "why?".

### Constitutional Constraints
- **READ-ONLY**: Analysis only (no proposals, no execution, no changes)
- **Fixed rules**: No learning, no optimization, no estimation
- **Defensive**: Never throws, always returns result
- **Label-only**: Normal output uses labels (numeric counts only in debug mode)
- **Deterministic**: Same snapshots → same attribution result

### Attribution Model

**Node Extraction Order** (fixed sequence from PR165 snapshots):
1. **PHASE**: Shock phase (PHASE_NORMAL, PHASE_PRE_SHOCK, etc.)
2. **STRESS**: Market stress (STRESS_CALM, STRESS_TENSE, etc.)
3. **ACTION_SHAPE**: Action shape (if available)
4. **TEMPLATE**: Risk template (TPL_RISK_50, etc.)
5. **GATE_DECISION**: Gate decision (PASS, BLOCK, ERROR, UNKNOWN)
6. **GATE_BLOCK_REASON**: Block reason (if BLOCK) - BLOCK_ORACLE_STALE, etc.
7. **POLICY**: Policy decision (ALLOW, DENY, UNKNOWN)
8. **RUN_STOP**: Stop reason category (STOP_BY_PHASE_POLICY, STOP_BY_GATE, etc.)
9. **RESUME**: Resume state (RESUMABLE, WAIT, ABANDON, UNKNOWN)
10. **ROUTE**: Venue route (CETUS, DEEPBOOK, NONE, UNKNOWN)

**Note**: If a field is missing in the snapshot, the corresponding node is skipped. Presence flags track which components appear in the data.

### Path and Edge Aggregation

**Paths**: Ordered sequences of nodes representing causal chains
- Each snapshot is converted to a node sequence
- Identical sequences are grouped and counted
- Top N paths (default: 10) are returned sorted by count

**Edges**: Adjacent pairs of nodes
- Each snapshot's node sequence generates adjacent pairs (from → to)
- Identical pairs are grouped and counted
- Top N edges (default: 15) are returned sorted by count

**Example Path**:
```
PHASE:PHASE_PRE_SHOCK →
STRESS:STRESS_TENSE →
TEMPLATE:TPL_RISK_20 →
GATE_DECISION:BLOCK →
GATE_BLOCK_REASON:BLOCK_ORACLE_STALE →
POLICY:DENY
```

### Bottlenecks (Dominant Patterns)

Bottlenecks are frequent patterns that dominate the attribution graph (threshold: >30% of total edge count):

**Identified Bottlenecks**:
- `BOTTLENECK_GATE_BLOCK_FREQUENT`: Gate BLOCK edges dominate
- `BOTTLENECK_STOP_FREQUENT`: RUN_STOP edges dominate
- `BOTTLENECK_ORACLE_DOMINANT`: ORACLE block reasons dominate
- `BOTTLENECK_PHASE_POLICY_DOMINANT`: PHASE_POLICY stops dominate
- `BOTTLENECK_MARKET_IMPACT_DOMINANT`: IMPACT/SLIPPAGE blocks dominate

### Weak Links (Rare Patterns)

Weak links are infrequent patterns that rarely appear in the attribution graph:

**Identified Weak Links**:
- `WEAKLINK_RESUME_RARE`: RESUME edges rarely appear
- `WEAKLINK_ROUTE_CHANGE_RARE`: ROUTE edges rarely appear
- `WEAKLINK_PASS_RARE`: Gate PASS edges rarely appear
- `WEAKLINK_NO_RECOVERY_OBSERVED`: RECOVERY phase edges absent

### Attribution CLI

Analyze attribution paths from snapshot logs:
```bash
# Default: 200 most recent snapshots
npx ts-node src/cli/attribution.ts

# Custom tail count
npx ts-node src/cli/attribution.ts --tail 500

# Focus on specific section
npx ts-node src/cli/attribution.ts --focus top_paths
npx ts-node src/cli/attribution.ts --focus bottlenecks

# JSON output (sanitized)
npx ts-node src/cli/attribution.ts --json

# Debug mode (allows numeric counts)
MERIDIAN_DEBUG=true npx ts-node src/cli/attribution.ts --tail 500

# Built version
node dist/cli/attribution.js
```

### Normal Mode vs Debug Mode

**Normal Mode** (default):
- Label-only output (no counts, no numerics)
- Paths and edges shown without counts
- Example: `PHASE:PHASE_NORMAL → TEMPLATE:TPL_RISK_50`

**Debug Mode** (`MERIDIAN_DEBUG=true`):
- Counts displayed for paths and edges
- Example: `PHASE:PHASE_NORMAL → TEMPLATE:TPL_RISK_50 (count: 42)`

### Example Output (Normal Mode)

```
=== Policy Attribution Graph v1 ===

Status: COMPLETE

Presence: HAS_SNAPSHOTS HAS_PHASE HAS_STRESS HAS_TEMPLATE HAS_GATE

--- Top Attribution Paths ---

  PHASE:PHASE_PRE_SHOCK → STRESS:STRESS_TENSE → TEMPLATE:TPL_RISK_20 → GATE_DECISION:BLOCK → GATE_BLOCK_REASON:BLOCK_ORACLE_STALE → POLICY:DENY
  PHASE:PHASE_NORMAL → STRESS:STRESS_CALM → TEMPLATE:TPL_RISK_50 → GATE_DECISION:PASS
  PHASE:PHASE_UP_SHOCK → STRESS:STRESS_STRESSED → TEMPLATE:TPL_RISK_90 → GATE_DECISION:BLOCK → GATE_BLOCK_REASON:BLOCK_IMPACT_HIGH

--- Top Edges ---

  PHASE:PHASE_PRE_SHOCK → STRESS:STRESS_TENSE
  STRESS:STRESS_TENSE → TEMPLATE:TPL_RISK_20
  TEMPLATE:TPL_RISK_20 → GATE_DECISION:BLOCK
  GATE_DECISION:BLOCK → GATE_BLOCK_REASON:BLOCK_ORACLE_STALE

--- Bottlenecks ---

  - BOTTLENECK_ORACLE_DOMINANT
  - BOTTLENECK_GATE_BLOCK_FREQUENT

--- Weak Links ---

  - WEAKLINK_RESUME_RARE
  - WEAKLINK_PASS_RARE

=== End Attribution ===
```

### Focus Modes

**TOP_PATHS**: Show only top attribution paths
```bash
npx ts-node src/cli/attribution.ts --focus top_paths
```

**TOP_EDGES**: Show only top edges
```bash
npx ts-node src/cli/attribution.ts --focus top_edges
```

**BOTTLENECKS**: Show only bottlenecks
```bash
npx ts-node src/cli/attribution.ts --focus bottlenecks
```

**WEAK_LINKS**: Show only weak links
```bash
npx ts-node src/cli/attribution.ts --focus weak_links
```

### Usage

```typescript
import { attributeSnapshotsV1 } from "./attribution";
import { readRecentSnapshotsV1 } from "./snapshot";

// Read snapshots
const snapshotResult = await readRecentSnapshotsV1({}, { maxLines: 200 });

// Attribute snapshots
const attributionResult = attributeSnapshotsV1(snapshotResult.snapshots, {
  tail: 200,
  maxPaths: 10,
  maxEdges: 15,
  minCount: 2,
});

// Check top paths
for (const path of attributionResult.topPaths) {
  console.log(`Path (count: ${path.count}):`);
  for (const node of path.nodes) {
    console.log(`  ${node.t}: ${node.v}`);
  }
}

// Check bottlenecks
for (const bottleneck of attributionResult.bottlenecks) {
  console.log(`Bottleneck: ${bottleneck}`);
}

// Check weak links
for (const weakLink of attributionResult.weakLinks) {
  console.log(`Weak link: ${weakLink}`);
}
```

### Non-Claims

**Attribution does NOT**:
- ❌ Prove causation (only shows observed chains/correlations)
- ❌ Provide trading advice or execution decisions
- ❌ Predict future outcomes
- ❌ Learn from patterns (fixed rules only)
- ❌ Optimize strategies automatically

**Attribution DOES**:
- ✅ Identify frequent causal chains (paths)
- ✅ Show dominant patterns (bottlenecks)
- ✅ Highlight rare patterns (weak links)
- ✅ Use fixed thresholds (deterministic)
- ✅ Fail gracefully (never throws)
- ✅ Respect label-only constraints (normal mode)

### Safety Guarantees

**Defensive design**:
- Attribution never throws exceptions
- Invalid input → ERROR status with minimal result
- Malformed snapshots skipped (with warnings)
- Always returns AttributionResultV1

**Privacy protection**:
- Normal mode: label-only (no counts)
- Debug mode: allows counts (but not addresses/secrets)
- Guards sanitize: token literals, trading vocab, prescriptive language
- Addresses always REDACTED (even in debug mode)

**Read-only operation**:
- Analysis only (no execution, no trading, no state modification)
- No proposals, no automatic changes

### Environment Variables

- `MERIDIAN_DEBUG`: Set to "true" to enable debug mode (numeric counts)
- `MERIDIAN_SNAPSHOTS_PATH`: Snapshot log path (default: `~/.meridian/snapshots.log`)
- `MERIDIAN_SNAPSHOTS_MAXLINES`: Max lines for analysis (default: 200)

### Files

- `src/attribution/types.ts`: Attribution types, node types, config
- `src/attribution/guards.ts`: Sanitization, validation, label-only formatting
- `src/attribution/model.ts`: Node extraction, path/edge building
- `src/attribution/attributor.ts`: Main attribution engine, bottleneck/weak link detection
- `src/attribution/index.ts`: Barrel exports
- `src/cli/attribution.ts`: Attribution CLI tool
- `tests/pr169.attribution.test.ts`: 12 comprehensive tests

---

## PR170: Evidence-Linked Proposals v1

### Purpose
Link PR169 attribution results (bottlenecks, paths, edges) as **"evidence"** to PR167 proposals, making proposals explainable with "why they were generated".

While PR167 generates proposals based on PR166 analysis (confusion/timing patterns), PR170 attaches **attribution evidence** to show the causal chains that support each proposal:
- Example: `P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE` has evidence `BOTTLENECK_ORACLE_DOMINANT` (STRONG)
- Example: `P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW` has evidence from path `PHASE_PRE_SHOCK → STOP` (MEDIUM)
- Example: Proposals can have multiple evidence records from different sources

This makes proposals **answerable**: "Why was this proposed?" → "Because ORACLE blocks dominate the attribution graph (STRONG evidence)".

### Constitutional Constraints
- **READ-ONLY**: Evidence extraction is analysis only (no execution, no changes)
- **Fixed rules**: Deterministic mapping from attribution to evidence
- **Policy-first**: Evidence strengthens proposals, but doesn't change priority (P0 > P1 > P2)
- **Label-only**: All evidence labels are sanitized (no counts in normal mode)
- **Defensive**: Malformed attribution → empty evidence (never throws)

### Evidence Model

**Evidence Types** (EvidenceKind):
- `EVID_BOTTLENECK`: From attribution bottlenecks (>30% threshold)
- `EVID_TOP_PATH`: From attribution top paths (frequent causal chains)
- `EVID_TOP_EDGE`: From attribution top edges (frequent transitions)
- `EVID_NONE`: No evidence available

**Evidence Strength** (fixed levels):
- `EVIDENCE_STRONG`: Clear match (bottleneck → proposal)
- `EVIDENCE_MEDIUM`: Partial match (top path → proposal)
- `EVIDENCE_WEAK`: Indirect match (top edge → proposal)
- `EVIDENCE_UNKNOWN`: No match or unavailable

**Evidence Record** (ProposalEvidence):
```typescript
{
  kind: EvidenceKind;           // Evidence type
  label: string;                 // Sanitized label (e.g., "BOTTLENECK_ORACLE_DOMINANT")
  strength: EvidenceStrength;    // STRONG, MEDIUM, WEAK, UNKNOWN
  context?: string;              // Optional context (e.g., "FROM_ATTRIBUTION_BOTTLENECK_ANALYSIS")
}
```

### Evidence Mapping (Fixed Rules)

**Bottleneck → Proposal (STRONG)**:
- `BOTTLENECK_ORACLE_DOMINANT` → `P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE`
- `BOTTLENECK_MARKET_IMPACT_DOMINANT` → `P0_REDUCE_IMPACT_BLOCKS_DEGRADE`, `P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE`
- `BOTTLENECK_GATE_BLOCK_FREQUENT` → `P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW`
- `BOTTLENECK_PHASE_POLICY_DOMINANT` → `P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW`

**Path Pattern → Proposal (MEDIUM)**:
- Paths matching `/ORACLE/i` → `P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE`
- Paths matching `/IMPACT/i` → `P0_REDUCE_IMPACT_BLOCKS_DEGRADE`
- Paths matching `/SLIPPAGE/i` → `P0_REDUCE_SLIPPAGE_BLOCKS_DEGRADE`
- Paths matching `/PHASE.*ESCALATION/i` → `P1_PHASE_ESCALATION_DOMINATES_PHASE_POLICY_REVIEW`

**Edge Pattern → Proposal (WEAK)**:
- Edges matching `/ORACLE.*BLOCK/i` → `P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE`
- Edges matching `/IMPACT.*BLOCK/i` → `P0_REDUCE_IMPACT_BLOCKS_DEGRADE`
- Edges matching `/GATE.*BLOCK/i` → `P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW`

### Proposal CLI with Evidence

Generate proposals with evidence attached:
```bash
# Default: no evidence (backward compatible)
npx ts-node src/cli/propose.ts

# With evidence (runs attribution analysis automatically)
npx ts-node src/cli/propose.ts --with-evidence

# Focus on evidence only
npx ts-node src/cli/propose.ts --with-evidence --focus evidence

# JSON output with evidence
npx ts-node src/cli/propose.ts --with-evidence --json

# Debug mode (shows strength and context)
MERIDIAN_DEBUG=true npx ts-node src/cli/propose.ts --with-evidence

# Built version
node dist/cli/propose.js --with-evidence
```

### Example Output with Evidence

**Normal Mode** (--with-evidence):
```
[P0] DEGRADE_ORACLE_STALE_THRESHOLD
  ID: P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
  Category: GATE_POLICY

  ...

  Evidence (PR170):
    - [EVID_BOTTLENECK] BOTTLENECK_ORACLE_DOMINANT
    - [EVID_TOP_PATH] PATH_ORACLE_PATH
    - [EVID_TOP_EDGE] EDGE_ORACLE_BLOCK_EDGE
```

**Debug Mode** (MERIDIAN_DEBUG=true --with-evidence):
```
[P0] DEGRADE_ORACLE_STALE_THRESHOLD
  ...

  Evidence (PR170):
    - [EVID_BOTTLENECK] [EVIDENCE_STRONG] BOTTLENECK_ORACLE_DOMINANT
      Context: FROM_ATTRIBUTION_BOTTLENECK_ANALYSIS
    - [EVID_TOP_PATH] [EVIDENCE_MEDIUM] PATH_ORACLE_PATH
      Context: FROM_ATTRIBUTION_TOP_PATHS
    - [EVID_TOP_EDGE] [EVIDENCE_WEAK] EDGE_ORACLE_BLOCK_EDGE
      Context: FROM_ATTRIBUTION_TOP_EDGES
```

**Focus Evidence Mode** (--focus evidence):
```
=== Proposal Evidence Focus ===

[P0] P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
  - [EVID_BOTTLENECK] BOTTLENECK_ORACLE_DOMINANT
  - [EVID_TOP_PATH] PATH_ORACLE_PATH
  - [EVID_TOP_EDGE] EDGE_ORACLE_BLOCK_EDGE

[P1] P1_GATE_BLOCK_DOMINATES_GATE_POLICY_REVIEW
  - [EVID_BOTTLENECK] BOTTLENECK_GATE_BLOCK_FREQUENT

=== End Evidence Focus ===
```

### Non-Claims

**Evidence does NOT**:
- ❌ Prove causation (only shows observed correlations)
- ❌ Change proposal priority (P0 > P1 > P2 remains fixed)
- ❌ Create new proposals (only links existing proposals to evidence)
- ❌ Provide trading advice
- ❌ Predict future patterns

**Evidence DOES**:
- ✅ Explain why proposals were generated
- ✅ Use fixed mapping rules (deterministic)
- ✅ Support multiple evidence per proposal
- ✅ Respect label-only constraints (normal mode)
- ✅ Fail gracefully (empty evidence on error)

### Safety Guarantees

**Defensive design**:
- Evidence extraction never throws exceptions
- Malformed attribution → empty evidence array
- Missing attribution → empty evidence array
- Always returns valid ProposalEvidence[]

**Privacy protection**:
- Normal mode: label-only (no counts, no strength in display)
- Debug mode: shows strength and context
- Guards sanitize: token literals, trading vocab, prescriptive language
- Addresses always REDACTED (even in debug mode)

**Read-only operation**:
- Evidence extraction is analysis only (no execution, no trading)
- No automatic adoption or policy changes

### Environment Variables

Same as PR167:
- `MERIDIAN_DEBUG`: Set to "true" to enable debug mode (shows evidence strength/context)
- `MERIDIAN_SNAPSHOTS_PATH`: Snapshot log path (default: `~/.meridian/snapshots.log`)
- `MERIDIAN_SNAPSHOTS_MAXLINES`: Max lines for analysis (default: 200)

### Files

- `src/propose/types.ts`: Updated with EvidenceKind, EvidenceStrength, ProposalEvidence types
- `src/propose/guards.ts`: Updated with evidence sanitization (sanitizeEvidence)
- `src/propose/evidence.ts`: Evidence extraction logic (extractEvidenceForProposal)
- `src/propose/proposer.ts`: Updated to attach evidence from attribution
- `src/propose/rules.ts`: Updated to initialize evidence field
- `src/propose/index.ts`: Updated to export evidence functions
- `src/cli/propose.ts`: Updated with --with-evidence and --focus evidence options
- `tests/pr170.propose_evidence.test.ts`: 12 comprehensive tests

**Purpose**: Identify causal chains to understand "why" outcomes occur, supporting Policy-First improvement, NOT causal inference or automatic optimization

---

## PR171: Patch Preview Report v1

### Purpose
Convert PR168's PatchPlan to human-readable change previews for adoption review.
Shows "what will change" before adoption (READ-ONLY, no automatic application).

While PR168 generates PatchPlan with technical operations (PATCH_PHASE_POLICY, PATCH_GATE_ORDER, etc.), PR171 converts these into **human-readable previews** that explain:
- What will change (which policy areas affected)
- Safety implications (Policy-First risk detection)
- Supporting evidence (proposal + attribution + compare signals)

This enables **review before adoption**: Users can read preview reports before deciding to adopt changes.

### Constitutional Constraints
- **READ-ONLY**: Report generation only (no automatic adoption, no code changes)
- **Fixed mapping**: patch op → report sections (predetermined templates)
- **Label-only**: All output is sanitized (no numerics in normal mode)
- **Defensive**: Never throws, always returns result
- **Forbidden patterns**: Token literals, trading vocab, addresses, numerics (normal mode)

### Preview Model

**Preview Section** (one per patch operation):
```typescript
{
  title: string;        // Section title (e.g., "SECTION_GATE_PRIORITY")
  before: string[];     // Before state (label-only)
  after: string[];      // After state (label-only)
  notes: string[];      // Explanatory notes (label-only)
}
```

**Preview Report** (full change preview):
```typescript
{
  kind: "PATCH_PREVIEW_V1";
  status: PreviewStatus;              // AVAILABLE, PARTIAL, ERROR
  proposalId?: string;                 // From PR167
  priority?: "P0" | "P1" | "P2";      // From PR167
  decisionCandidate?: "ADOPT" | "HOLD" | "REJECT";  // From PR168
  patchOps: string[];                  // Patch operations (label-only)
  sections: PreviewSection[];          // One per patchOp
  riskLabels: string[];                // Risk warnings (label-only)
  readiness: string[];                 // Readiness status (label-only)
  evidence: Array<...>;                // From PR170 (max 3, strength-sorted)
  compareSignals: string[];            // From PR168 (label-only)
  warnings: string[];                  // Non-fatal issues
  timeLabel: PreviewTimeLabel;         // T_RECENT, T_MIN, T_HOUR, T_OLD, T_UNKNOWN
  ts: number;                          // Timestamp (for storage)
}
```

### Fixed Mapping (Patch Op → Section)

**PATCH_PHASE_POLICY**:
- Title: SECTION_PHASE_POLICY
- Before: BEFORE_STOP_RULES_CURRENT
- After: AFTER_STOP_RULES_TUNED
- Notes: NOTE_STOP_WAIT_BALANCE_CHANGED, NOTE_SAFETY_CONSTRAINTS_PRESERVED

**PATCH_GATE_ORDER**:
- Title: SECTION_GATE_PRIORITY
- Before: BEFORE_GATE_PRIORITY_CURRENT
- After: AFTER_GATE_PRIORITY_REORDERED
- Notes: NOTE_BLOCK_REASON_SHIFT_EXPECTED

**PATCH_ROUTER_TIEBREAK**:
- Title: SECTION_ROUTER_TIEBREAK
- Before: BEFORE_ROUTE_TIEBREAK_CURRENT
- After: AFTER_ROUTE_TIEBREAK_CHANGED
- Notes: NOTE_EXECUTION_PATH_VARIANCE

**PATCH_NOT_ALLOWED**:
- Title: SECTION_NOT_ALLOWED
- Before: BEFORE_PATCH_NOT_ALLOWED_PRESENT
- After: AFTER_PATCH_NOT_ALLOWED_REJECT_EXPECTED
- Notes: NOTE_POLICY_FIRST_REJECT
- Risk: RISK_PATCH_NOT_ALLOWED_PRESENT
- Readiness: NOT_REVIEWABLE_REJECT_EXPECTED

### Preview CLI

View and filter preview reports from previews.log:
```bash
# View all recent previews
npx ts-node src/cli/preview.ts

# Tail N most recent
npx ts-node src/cli/preview.ts --tail 10

# Filter by proposal ID
npx ts-node src/cli/preview.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# Filter by priority
npx ts-node src/cli/preview.ts --priority P0

# Filter by decision
npx ts-node src/cli/preview.ts --decision ADOPT

# JSON output
npx ts-node src/cli/preview.ts --json

# Debug mode
MERIDIAN_DEBUG=true npx ts-node src/cli/preview.ts --tail 10
```

### Adopt CLI with Preview

Generate preview reports during adoption loop:
```bash
# With preview (generates and saves preview before decision)
npx ts-node src/cli/adopt.ts --preview

# Preview only (generates preview, skips decision display)
npx ts-node src/cli/adopt.ts --preview-only

# Preview with debug mode
MERIDIAN_DEBUG=true npx ts-node src/cli/adopt.ts --preview
```

### Storage

**JSONL Append-Only Log**:
- Path: ~/.meridian/previews.log
- Format: One JSON object per line
- Defensive: Corrupt lines skipped with warnings

**Environment Variables**:
- MERIDIAN_PREVIEW_PATH: Preview log path
- MERIDIAN_DEBUG: Set to "true" to enable debug mode

### Non-Claims

**Preview does NOT**:
- ❌ Automatically apply changes
- ❌ Modify code or policies
- ❌ Provide trading advice
- ❌ Learn from patterns
- ❌ Display numeric values in normal mode

**Preview DOES**:
- ✅ Convert PatchPlan to human-readable sections
- ✅ Show what will change (before/after/notes)
- ✅ Detect Policy-First risks
- ✅ Include supporting evidence (max 3)
- ✅ Use fixed templates
- ✅ Fail gracefully

### Files

- src/preview/types.ts: Preview types
- src/preview/guards.ts: Sanitization and formatting
- src/preview/templates.ts: Fixed patch op mapping
- src/preview/previewer.ts: Preview generation engine
- src/preview/store.ts: JSONL storage
- src/preview/index.ts: Barrel exports
- src/cli/preview.ts: Preview viewing CLI
- src/cli/adopt.ts: Updated with --preview options
- tests/pr171.preview.test.ts: 12 comprehensive tests

**Purpose**: Show human-readable change previews before adoption, supporting Policy-First review

## PR172: Patch Review Checklist + Decision Rationale v1

### Purpose
Add structured review checklists and decision rationale to PR171's previews.
Provides standardized safety checks and reasoning before adoption (READ-ONLY, no automatic adoption).

While PR171 generates human-readable previews, PR172 adds **structured review** that evaluates:
- 6 fixed safety checklist items (PASS/FAIL/UNKNOWN)
- Decision rationale (CANDIDATE_ADOPT/HOLD/REJECT)
- Supporting reasons (label-only)

This enables **policy-first review**: Users see checklist results and rationale before deciding to adopt changes.

### Constitutional Constraints
- **READ-ONLY**: Review generation only (suggests decision, does not auto-adopt)
- **Fixed rules**: All checklist items predetermined (no learning, no optimization)
- **Label-only**: All output is sanitized (no numerics in normal mode)
- **Defensive**: Never throws, always returns result
- **Safety-first**: NOT_REVIEWABLE checks have highest priority
- **Forbidden patterns**: Token literals, trading vocab, addresses, prescriptive language

### Review Model

**Review Checklist Item**:
```typescript
{
  id: string;                    // Check ID (e.g., "CHECK_NO_NOT_ALLOWED_PATCH")
  label: string;                 // Human-readable label
  status: ChecklistItemStatus;   // PASS, FAIL, UNKNOWN
  detail?: string;               // Optional detail (label-only)
}
```

**Decision Rationale**:
```typescript
{
  decisionCandidate: DecisionCandidate;  // CANDIDATE_ADOPT, CANDIDATE_HOLD, CANDIDATE_REJECT
  reasons: string[];                      // Supporting reasons (label-only)
}
```

**Review Report** (full review result):
```typescript
{
  kind: "PATCH_REVIEW_V1";
  status: ReviewStatus;           // REVIEWABLE, NOT_REVIEWABLE, ERROR
  checklist: ReviewChecklistItem[];  // 6 fixed checks
  rationale: DecisionRationale;      // Decision + reasons
  warnings: string[];                // Non-fatal issues
  ts: number;                        // Timestamp
}
```

### Fixed Checklist Items (6 Checks)

1. **CHECK_NO_NOT_ALLOWED_PATCH**: No safety-reducing patches present
   - FAIL if PATCH_NOT_ALLOWED in patchOps
   - PASS otherwise

2. **CHECK_PREVIEW_REVIEWABLE**: Preview marked as reviewable
   - FAIL if NOT_REVIEWABLE in readiness
   - PASS otherwise

3. **CHECK_HAS_EVIDENCE**: Supporting evidence present
   - FAIL if evidence.length === 0
   - PASS otherwise

4. **CHECK_NO_WORSENING_SIGNAL**: No worsening signals in comparison
   - FAIL if WORSENED in compareSignals
   - PASS otherwise

5. **CHECK_SCOPE_NOT_MULTI**: Change scope limited to single area
   - FAIL if patchOps.length > 2
   - PASS otherwise

6. **CHECK_PRIORITY_P0_SAFE**: P0 priority has strong evidence
   - FAIL if priority === "P0" and no strong evidence
   - PASS otherwise

### Decision Rationale Rules

**Priority Order** (highest to lowest):

1. **CANDIDATE_REJECT** (safety issues):
   - REASON_PREVIEW_NOT_REVIEWABLE
   - REASON_PATCH_NOT_ALLOWED_PRESENT
   - REASON_COMPARE_SHOWS_WORSENING

2. **CANDIDATE_HOLD** (weak evidence or multi-area):
   - REASON_CHECKLIST_FAILURES
   - REASON_INSUFFICIENT_CONFIRMATION
   - REASON_EVIDENCE_WEAK_ONLY
   - REASON_NO_EVIDENCE
   - REASON_MULTI_AREA_CHANGE

3. **CANDIDATE_ADOPT** (all checks pass):
   - REASON_STRONG_EVIDENCE_PRESENT
   - REASON_NO_WORSENING_SIGNAL
   - REASON_CHANGE_SCOPE_LIMITED

### Review CLI

Review patch preview reports:
```bash
# Review most recent preview
npx ts-node src/cli/review.ts

# Review specific proposal
npx ts-node src/cli/review.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# JSON output
npx ts-node src/cli/review.ts --json

# Debug mode (shows check details)
MERIDIAN_DEBUG=true npx ts-node src/cli/review.ts
```

### Adopt CLI with Review

Run preview → review → decision flow:
```bash
# Full review flow (preview + review + decision)
npx ts-node src/cli/adopt.ts --review

# Display order:
# 1. Preview summary
# 2. Review checklist
# 3. Decision rationale
# 4. Adoption decision (PR168)

# With debug mode
MERIDIAN_DEBUG=true npx ts-node src/cli/adopt.ts --review
```

### Example Output

**Normal Mode** (label-only):
```
=== Preview Summary ===
Proposal: P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
Priority: P0
Status: COMPLETE
...

=== Review Checklist ===
✓ [PASS] No safety-reducing patches present
✓ [PASS] Preview marked as reviewable
✓ [PASS] Supporting evidence present
✓ [PASS] No worsening signals in comparison
✓ [PASS] Change scope limited to single area
✓ [PASS] P0 priority has strong evidence

=== Decision Rationale ===
Suggested Decision: CANDIDATE_ADOPT

Reasons:
  - REASON_STRONG_EVIDENCE_PRESENT
  - REASON_NO_WORSENING_SIGNAL
  - REASON_CHANGE_SCOPE_LIMITED
```

**Debug Mode** (with details):
```
MERIDIAN_DEBUG=true enables:
- Check evaluation details
- Numeric timestamps
- Additional warnings
```

### Non-Claims

**Review does NOT**:
- ❌ Automatically adopt changes
- ❌ Learn from patterns or optimize rules
- ❌ Make final decisions (READ-ONLY suggestions only)
- ❌ Display numeric values in normal mode
- ❌ Use prescriptive language ("should", "must", "will")

**Review DOES**:
- ✅ Evaluate 6 fixed checklist items
- ✅ Generate decision rationale (ADOPT/HOLD/REJECT)
- ✅ Use predetermined rules only
- ✅ Sanitize all output (label-only)
- ✅ Fail gracefully (defensive)

### Files

- src/review/types.ts: Review types
- src/review/rules.ts: Fixed checklist items and decision rules
- src/review/guards.ts: Sanitization and formatting
- src/review/reviewer.ts: Review engine
- src/review/index.ts: Barrel exports
- src/cli/review.ts: Review viewing CLI
- src/cli/adopt.ts: Updated with --review option
- tests/pr172.review_checklist.test.ts: 12 comprehensive tests

**Purpose**: Provide structured safety checklists and decision rationale before adoption, supporting Policy-First review

## PR173: Decision Acknowledgement + Reviewer Trace v1

### Purpose
Add adoption decision audit trail with READ-ONLY recording and viewing.
Captures "who decided what, when, and why" for adoption accountability.

While PR172 generates decision rationale, PR173 adds **adoption acknowledgement** that records:
- Who made the decision (reviewer kind)
- What was decided (ADOPT/HOLD/REJECT)
- When (discretized time label)
- Why (rationale labels from PR172)
- What was referenced (proposal, preview, review, patch plan)

This enables **adoption audit trail**: Users can view complete decision history with full traceability.

### Constitutional Constraints
- **READ-ONLY**: Records and displays only (no automatic adoption)
- **Fixed rules**: Deterministic record building
- **Label-only**: All output sanitized (no numerics in normal mode)
- **Defensive**: Never throws, always returns valid record
- **Append-only**: Immutable JSONL audit log

### Decision Ack Model

**Decision Acknowledgement Record**:
```typescript
{
  kind: "DECISION_ACK_V1";
  status: DecisionAckStatus;        // AVAILABLE, PARTIAL, ERROR

  ts: number;                       // Internal storage only
  timeLabel: TimeLabel;             // Display-safe (T_RECENT, T_MIN, T_HOUR, T_OLD)

  reviewer: ReviewerKind;           // HUMAN_PRIMARY, HUMAN_SECONDARY, AUTO_ASSISTED, POLICY_ONLY
  source: AckSource;                // CLI_ADOPT, CLI_ACK, UNKNOWN

  refs: {
    proposalId?: string;            // e.g., "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE"
    previewId?: string;             // e.g., "PREVIEW_PRESENT"
    reviewId?: string;              // e.g., "REVIEW_PRESENT"
    patchPlanId?: string;           // e.g., "PATCHPLAN_PRESENT"
  };

  rationale: {
    decision: AckDecision;          // ADOPT, HOLD, REJECT, UNKNOWN
    rationaleLabels: string[];      // e.g., ["REASON_STRONG_EVIDENCE_PRESENT"]
    checklistSummary: string[];     // e.g., ["CHECK_NO_NOT_ALLOWED_PATCH:PASS"]
    evidenceSummary: string[];      // e.g., ["EVIDENCE_STRONG"]
    compareSummary: string[];       // e.g., ["IMPROVED_BLOCK_DOMINANCE"]
  };

  warnings: string[];               // Label-only
}
```

### Reviewer Kinds

- **HUMAN_PRIMARY**: Primary human decision maker
- **HUMAN_SECONDARY**: Secondary human reviewer
- **AUTO_ASSISTED**: Human with automated assistance (e.g., PR172 checklist)
- **POLICY_ONLY**: Policy-first automated decision (PR168)
- **UNKNOWN**: Reviewer kind not specified

### Decision Building Rules

**Decision Priority** (fixed):
1. `decisionResult.decision` (from PR168)
2. `reviewReport.rationale.decisionCandidate` (from PR172)
3. Fallback to `UNKNOWN`

**Status**:
- `AVAILABLE`: proposalId + decision present
- `PARTIAL`: decision is UNKNOWN
- `ERROR`: input shape corrupted (but returns valid record)

**Rationale Building**:
- `rationaleLabels`: From PR172 review report reasons (max 3)
- `checklistSummary`: From PR172 checklist items (PASS/FAIL/UNKNOWN)
- `evidenceSummary`: From PR171 preview evidence (max 3)
- `compareSummary`: From PR171 preview compare signals (max 3)

### Decisions CLI

View decision acknowledgement audit trail:
```bash
# View recent decisions
npx ts-node src/cli/decisions.ts

# Tail N most recent
npx ts-node src/cli/decisions.ts --tail 50

# Filter by proposal
npx ts-node src/cli/decisions.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# Filter by decision
npx ts-node src/cli/decisions.ts --decision ADOPT

# Filter by reviewer
npx ts-node src/cli/decisions.ts --reviewer HUMAN_PRIMARY

# JSON output
npx ts-node src/cli/decisions.ts --json

# Debug mode
MERIDIAN_DEBUG=true npx ts-node src/cli/decisions.ts
```

### Adopt CLI with Acknowledgement

Record decision acknowledgements during adoption:
```bash
# Full flow with acknowledgement (preview + review + decision + ack)
npx ts-node src/cli/adopt.ts --ack

# Ack-only mode (read existing preview/review, create ack only)
npx ts-node src/cli/adopt.ts --ack-only

# Display order (--ack):
# 1. Preview summary
# 2. Review checklist
# 3. Adoption decision (PR168)
# 4. Decision acknowledgement (PR173)

# With debug mode
MERIDIAN_DEBUG=true npx ts-node src/cli/adopt.ts --ack
```

### Example Output

**Normal Mode** (label-only):
```
DECISION_ACK_V1 AVAILABLE T_MIN
REVIEWER HUMAN_PRIMARY SOURCE CLI_ADOPT
PROPOSAL P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
PREVIEW PREVIEW_PRESENT
REVIEW REVIEW_PRESENT
PATCHPLAN PATCHPLAN_PRESENT
DECISION ADOPT
RATIONALE REASON_STRONG_EVIDENCE_PRESENT, REASON_NO_WORSENING_SIGNAL
CHECKLIST CHECK_NO_NOT_ALLOWED_PATCH:PASS, CHECK_HAS_EVIDENCE:PASS, ...
EVIDENCE EVIDENCE_STRONG
COMPARE IMPROVED_BLOCK_DOMINANCE, NO_WORSENING
WARNINGS NONE
---
```

**Debug Mode** (with timestamp):
```
MERIDIAN_DEBUG=true enables:
- Numeric timestamp (DEBUG_TS)
- Additional warnings
- Raw record structure
```

### Storage

**JSONL Append-Only Log**:
- Path: ~/.meridian/decisions.log
- Format: One JSON object per line
- Defensive: Corrupt lines skipped with warnings

**Environment Variables**:
- MERIDIAN_DECISION_PATH: Decision log path
- MERIDIAN_DEBUG: Set to "true" to enable debug mode

### Non-Claims

**Decision Ack does NOT**:
- ❌ Automatically adopt changes
- ❌ Modify code or policies
- ❌ Make decisions (only records them)
- ❌ Learn from patterns or optimize rules
- ❌ Display numeric values in normal mode

**Decision Ack DOES**:
- ✅ Record adoption decisions with full context
- ✅ Provide audit trail for accountability
- ✅ Link to proposal, preview, review, patch plan
- ✅ Use label-only output (sanitized)
- ✅ Fail gracefully (defensive)
- ✅ Support filtering by proposal/decision/reviewer

### Files

- src/decision/types.ts: Decision ack types
- src/decision/guards.ts: Sanitization and formatting
- src/decision/ack.ts: Ack record builder
- src/decision/store.ts: JSONL storage
- src/decision/index.ts: Barrel exports
- src/cli/decisions.ts: Decision viewing CLI
- src/cli/adopt.ts: Updated with --ack and --ack-only options
- tests/pr173.decision_ack.test.ts: 12 comprehensive tests

**Purpose**: Record adoption decision audit trail for accountability and traceability

## PR174: Patch Effectiveness Tracker v1

### Purpose
Track patch effectiveness by measuring "did the adoption actually improve things" post-adoption.
Compares Before/After snapshots using fixed thresholds (READ-ONLY observation only).

While PR173 records adoption decisions, PR174 adds **effectiveness verification** that measures:
- Before window: Snapshots before adoption (default: 120)
- After windows: Short/Medium/Long-term snapshots after adoption (60/180/600)
- Fixed metrics: Gate pass/block rate, stop rate, confusion signals
- Fixed thresholds: 10% point change = significant

This enables **post-adoption verification**: Users can objectively measure whether adopted changes actually improved operational health.

### Constitutional Constraints
- **READ-ONLY**: Observation only (no automatic adoption/execution)
- **Fixed rules**: Fixed thresholds (10% point change, no learning/optimization)
- **Label-only**: Display mode sanitizes numerics (debug mode allows)
- **Defensive**: Never throws, always returns valid report
- **NOT trading advice**: Measures operational health, not profits

### Effect Model

**Patch Effect Report**:
```typescript
{
  kind: "PATCH_EFFECT_V1";
  status: EffectStatus;        // AVAILABLE, PARTIAL, ERROR

  decisionAckRef: {
    proposalId?: string;       // From PR173
    decision?: string;         // ADOPT/HOLD/REJECT from PR173
    reviewerKind?: string;
    timeLabel?: string;
  };

  windows: EffectWindowSummary[];  // Before + After (Short/Medium/Long)

  compare: {
    improved: string[];        // e.g., ["IMPROVED_BLOCK_RATE"]
    worsened: string[];        // e.g., ["WORSENED_STOP_RATE"]
    unchanged: string[];
    unavailable: string[];
  };

  effectDecision: EffectDecision;  // EFFECT_IMPROVED/WORSENED/NO_CHANGE/MIXED/UNKNOWN

  rationale: string[];         // Label-only reasons
  warnings: string[];
  ts: number;                  // Internal storage only
}
```

**Window Summary**:
```typescript
{
  window: WindowLabel;         // WIN_BEFORE, WIN_AFTER_SHORT, etc.
  status: EffectStatus;

  counts: {
    nSnapshots: number;        // Internal only (debug mode displays)
    nGatePass: number;
    nGateBlock: number;
    nStop: number;
  };

  rates: {
    passRate?: number;         // Internal only (debug mode displays)
    blockRate?: number;
    stopRate?: number;
  };

  tops: {
    topPhase?: string;         // Most common phase (label)
    topTemplate?: string;
    topBlockReason?: string;
    topStopCategory?: string;
  };

  confusionSignals: string[];  // From PR166 patterns
  bottlenecks: string[];       // e.g., "BOTTLENECK_ORACLE_DOMINANT"
  warnings: string[];
}
```

### Fixed Window Config

**Default Windows**:
- **Before**: 120 snapshots before adoption
- **After Short**: 60 snapshots after adoption (primary evaluation)
- **After Medium**: 180 snapshots after adoption (confirmation)
- **After Long**: 600 snapshots after adoption (long-term trend)

### Fixed Thresholds

**Significant Change**: 10% point change

**Improvement Signals** (10%pt decrease = improvement):
- `IMPROVED_BLOCK_RATE`: Block rate decreased by 10%pt+
- `IMPROVED_STOP_RATE`: Stop rate decreased by 10%pt+
- `IMPROVED_PASS_RATE`: Pass rate increased by 10%pt+
- `IMPROVED_CONFUSION_BLOCK_DOMINATES_RESOLVED`: Confusion signal removed
- `IMPROVED_BOTTLENECK_RESOLVED_*`: Bottleneck removed

**Worsening Signals** (10%pt increase = worsening):
- `WORSENED_BLOCK_RATE`: Block rate increased by 10%pt+
- `WORSENED_STOP_RATE`: Stop rate increased by 10%pt+
- `WORSENED_PASS_RATE`: Pass rate decreased by 10%pt+
- `WORSENED_NEW_CONFUSION_*`: New confusion signal appeared
- `WORSENED_NEW_BOTTLENECK_*`: New bottleneck appeared

### Effect Decision Rules

**Priority** (fixed):
1. No afterShort → `EFFECT_UNKNOWN`
2. Improved only (no worsening) → `EFFECT_IMPROVED`
3. Worsened only (no improvement) → `EFFECT_WORSENED`
4. Both improved and worsened → `EFFECT_MIXED`
5. No significant change → `EFFECT_NO_CHANGE`

### Effect CLI

Track patch effectiveness:
```bash
# Track most recent adoption
npx ts-node src/cli/effect.ts

# Specify snapshot window
npx ts-node src/cli/effect.ts --tail 2000

# Filter by proposal
npx ts-node src/cli/effect.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# Filter by ack decision
npx ts-node src/cli/effect.ts --decision ADOPT

# JSON output
npx ts-node src/cli/effect.ts --json

# Don't save to effects.log
npx ts-node src/cli/effect.ts --no-save

# Debug mode (show numerics)
MERIDIAN_DEBUG=true npx ts-node src/cli/effect.ts
```

### Example Output

**Normal Mode** (label-only):
```
=== Patch Effect Report v1 ===

Status: AVAILABLE
Effect Decision: EFFECT_IMPROVED

Proposal: P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
Original Decision: ADOPT
Reviewer: AUTO_ASSISTED
Time: T_MIN

--- Time Windows ---

Window: WIN_BEFORE (AVAILABLE)
  Top Phase: PHASE_WAIT
  Top Block Reason: BLOCK_ORACLE_STALE
  Confusion: CONFUSION_GATE_BLOCK_DOMINATES

Window: WIN_AFTER_SHORT (AVAILABLE)
  Top Phase: PHASE_PREPARE
  Top Block Reason: BLOCK_SLIPPAGE
  Confusion: NONE

--- Comparison ---

Improved: IMPROVED_BLOCK_RATE, IMPROVED_CONFUSION_BLOCK_DOMINATES_RESOLVED
Worsened: NONE
Unchanged: UNCHANGED_STOP_RATE

--- Rationale ---

  - REASON_BLOCK_RATE_DECREASED
  - REASON_CONFUSION_BLOCK_RESOLVED
  - REASON_OVERALL_IMPROVED

=== End Report ===
```

**Debug Mode** (with numerics):
```
MERIDIAN_DEBUG=true enables:
- Numeric counts (nSnapshots, nGatePass, nGateBlock, nStop)
- Numeric rates (passRate, blockRate, stopRate)
- Timestamp
```

### Storage

**JSONL Append-Only Log**:
- Path: ~/.meridian/effects.log
- Format: One JSON object per line
- Defensive: Corrupt lines skipped with warnings

**Environment Variables**:
- MERIDIAN_EFFECT_PATH: Effect log path
- MERIDIAN_DEBUG: Set to "true" to enable debug mode

### Non-Claims

**Effect Tracker does NOT**:
- ❌ Automatically adopt changes
- ❌ Make trading decisions
- ❌ Guarantee profits or performance
- ❌ Learn or optimize thresholds
- ❌ Execute trades automatically

**Effect Tracker DOES**:
- ✅ Measure operational health changes
- ✅ Compare Before/After snapshots objectively
- ✅ Use fixed thresholds (10% point change)
- ✅ Provide label-only output (normal mode)
- ✅ Support post-adoption verification
- ✅ Fail gracefully (defensive)

### Files

- src/effect/types.ts: Effect types
- src/effect/guards.ts: Sanitization and formatting
- src/effect/selector.ts: Window selection
- src/effect/metrics.ts: Window metrics calculation
- src/effect/evaluator.ts: Effect evaluation
- src/effect/store.ts: JSONL storage
- src/effect/index.ts: Barrel exports
- src/cli/effect.ts: Effect tracking CLI
- tests/pr174.effectiveness.test.ts: 12 comprehensive tests

**Purpose**: Measure patch effectiveness post-adoption using READ-ONLY observation and fixed thresholds
## PR175: Regression Guard v1 (Effect Persistence Monitor)

### Purpose
Monitor patch effectiveness persistence by detecting when improvements don't persist (regress).
While PR174 measures "did it improve?", PR175 tracks "did the improvement last?"

Reads PR174's effects.log to detect regression patterns like:
- IMPROVED → quickly WORSENED
- IMPROVED → dominance re-emerges (BLOCK/STOP)
- Effect flapping (oscillation between IMPROVED/WORSENED)
- Category shift worsening

This enables **持続性の検証** (persistence verification): Users can objectively measure whether adopted changes maintain their improvements or regress over time.

### Constitutional Constraints
- **READ-ONLY**: Observation only (no automatic revert)
- **Fixed rules**: Hardcoded thresholds and detection logic (no learning)
- **Label-only**: Display mode sanitizes numerics (debug mode allows)
- **Defensive**: Never throws, always returns valid report
- **Append-only**: Audit trail in ~/.meridian/regressions.log

### Regression Model

**Regression Report**:
```typescript
{
  kind: "REGRESSION_REPORT_V1";
  status: RegressionStatus;    // AVAILABLE, PARTIAL, ERROR

  analysis: {
    proposalId: string;
    decision: RegressionDecision;    // REGRESSION_DETECTED, NO_REGRESSION, REGRESSION_UNKNOWN
    kind: RegressionKind;            // REGRESS_IMPROVED_TO_WORSENED, etc.
    strength: RegressionStrength;    // STRONG, MEDIUM, WEAK, UNKNOWN
    windowLabel: RegressionWindowLabel; // W_SHORT, W_MEDIUM, W_LONG
    evidence: RegressionEvidence[];  // Max 3 pieces of evidence (label-only)
    warnings: string[];
  };

  ts: number;                  // Internal storage only
  warnings: string[];
}
```

**Regression Evidence**:
```typescript
{
  kind: "EVID_EFFECT" | "EVID_DECISION" | "EVID_NONE";
  label: string;          // Label-only (no numbers/tokens)
  strength: RegressionStrength;
}
```

### Fixed Detection Rules

**Constants**:
- `MIN_EFFECTS_FOR_EVAL = 3`: Minimum effects needed for evaluation
- `STRONG_REGRESS_LOOKBACK = 5`: Lookback window for strong regression
- `FLAP_THRESHOLD = 3`: Min oscillations to detect flapping
- `IMPROVE_TO_WORSE_WITHIN = 2`: Window for IMPROVED→WORSENED detection

**Detection Priority** (first-match-wins):

1. **IMPROVED → WORSENED within 2 effects**
   - Kind: `REGRESS_IMPROVED_TO_WORSENED`
   - Strength: `STRONG`
   - Window: `W_SHORT`

2. **IMPROVED → BLOCK dominance re-emerges**
   - Kind: `REGRESS_IMPROVED_TO_BLOCK_DOMINANT`
   - Strength: `MEDIUM` or `STRONG`
   - Window: `W_MEDIUM`

3. **IMPROVED → STOP dominance re-emerges**
   - Kind: `REGRESS_IMPROVED_TO_STOP_DOMINANT`
   - Strength: `MEDIUM` or `STRONG`
   - Window: `W_MEDIUM`

4. **Category shift worsening**
   - Kind: `REGRESS_CATEGORY_SHIFT_WORSENED`
   - Strength: `MEDIUM`
   - Example: Block rate improved but stop rate worsened

5. **Effect flapping** (oscillation ≥ 3 times)
   - Kind: `REGRESS_EFFECT_FLAPPING`
   - Strength: `MEDIUM`
   - Window: `W_LONG`

6. **NO_REGRESSION**: Recent effects are IMPROVED/NO_CHANGE
   - Decision: `NO_REGRESSION`

7. **UNKNOWN**: Ambiguous data
   - Decision: `REGRESSION_UNKNOWN`

### Regression CLI

Monitor patch effectiveness persistence:

```bash
# View stored regression reports
npx ts-node src/cli/regression.ts

# Analyze effects and detect regressions
npx ts-node src/cli/regression.ts --analyze

# Specify tail
npx ts-node src/cli/regression.ts --tail 50

# Filter by proposal
npx ts-node src/cli/regression.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# Filter by regression decision
npx ts-node src/cli/regression.ts --decision REGRESSION_DETECTED

# JSON output
npx ts-node src/cli/regression.ts --json

# Debug mode (show numerics)
MERIDIAN_DEBUG=true npx ts-node src/cli/regression.ts --analyze
```

### Example Output

**Normal Mode** (label-only):
```
=== Regression Report V1 ===

Status: AVAILABLE
Proposal: P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
Decision: REGRESSION_DETECTED
Kind: REGRESS_IMPROVED_TO_WORSENED
Strength: STRONG
Window: W_SHORT

Evidence:
  - [EVID_EFFECT] IMPROVED_AT_0_WORSENED_AT_2_WITHIN_2 (STRONG)
```

**Debug Mode** (with numerics):
```json
{
  "kind": "REGRESSION_REPORT_V1",
  "status": "AVAILABLE",
  "analysis": {
    "proposalId": "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
    "decision": "REGRESSION_DETECTED",
    "kind": "REGRESS_IMPROVED_TO_WORSENED",
    "strength": "STRONG",
    "windowLabel": "W_SHORT",
    "evidence": [
      {
        "kind": "EVID_EFFECT",
        "label": "IMPROVED_AT_0_WORSENED_AT_2_WITHIN_2",
        "strength": "STRONG"
      }
    ],
    "warnings": []
  },
  "ts": 1705430400000,
  "warnings": []
}
```

### Integration with Proposal/Review/Adopt Flow

PR175 strengthens the improvement loop:

1. **PR167**: Propose patch based on analysis
2. **PR172**: Review patch with checklist
3. **PR173**: Acknowledge adoption decision
4. **PR174**: Measure immediate effectiveness
5. **PR175**: Monitor persistence over time ← NEW
6. **Back to PR167**: Use regression evidence in next proposal

**Example Flow**:
- User adopts patch to reduce oracle blocks
- PR174: Immediate effect shows IMPROVED (block rate decreased)
- PR175: After 5 more effects, detects REGRESS_IMPROVED_TO_WORSENED
- Evidence: "Block rate improved initially but returned to high levels"
- Next proposal can reference this regression evidence
- Review checklist considers persistence history

### Non-Claims

PR175 does **NOT**:
- ❌ Automatically revert adoptions (READ-ONLY observation only)
- ❌ Predict future regressions (fixed rules, no learning)
- ❌ Optimize thresholds (fixed constants)
- ❌ Provide trading advice (operational health monitoring only)

### What PR175 DOES

- ✅ Detect regression patterns using fixed rules
- ✅ Monitor improvement persistence objectively
- ✅ Provide label-only evidence (normal mode)
- ✅ Support post-adoption long-term monitoring
- ✅ Strengthen proposal/review process with persistence data
- ✅ Fail gracefully (defensive)

### Files

- src/regress/types.ts: Regression types
- src/regress/guards.ts: Sanitization and formatting
- src/regress/reader.ts: Read effects/decisions logs
- src/regress/detector.ts: Regression detection logic
- src/regress/store.ts: JSONL storage
- src/regress/index.ts: Barrel exports
- src/cli/regression.ts: Regression monitoring CLI
- tests/pr175.regression_guard.test.ts: 14 comprehensive tests

**Purpose**: Monitor patch effectiveness persistence using READ-ONLY observation and fixed detection rules
