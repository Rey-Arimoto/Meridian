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

## PR176: Change Interaction Detector v1 (Patch Coupling Risk)

### Purpose
Detect patch coupling/interaction risks when multiple patches are adopted close together in time.
While individual patches may test well in isolation, combining them can create unexpected problems.

PR176 reads PR173 decisions.log and PR174 effects.log (and optionally PR175 regressions.log) to detect patterns like:
- Multiple adoptions in tight time window (≤30min)
- Regression appearing after pair of adoptions
- Effect worsening after pair of adoptions
- Coupling risk score exceeding threshold

This enables **相互作用リスク検知** (interaction risk detection): Users can objectively identify when patch combinations may be harmful.

### Constitutional Constraints
- **READ-ONLY**: Observation only (no automatic adoption/revert)
- **Fixed rules**: Hardcoded detection logic and thresholds (no learning)
- **Label-only**: Display mode sanitizes numerics (debug mode allows)
- **Defensive**: Never throws, always returns valid report
- **Append-only**: Audit trail in ~/.meridian/interactions.log

### Interaction Model

**Interaction Report**:
```typescript
{
  kind: "INTERACTION_REPORT_V1";
  status: InteractionStatus;        // AVAILABLE, PARTIAL, ERROR

  // Patch pair identity
  primaryProposalId?: string;
  secondaryProposalId?: string;
  primaryDecision?: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";
  secondaryDecision?: "ADOPT" | "HOLD" | "REJECT" | "UNKNOWN";

  // Interaction analysis
  interaction: InteractionDecision;  // INTERACTION_DETECTED, NO_INTERACTION, UNKNOWN
  interactionKind: InteractionKind;  // INT_PATCH_PAIR_REGRESSION, etc.
  strength: InteractionStrength;     // STRONG, MEDIUM, WEAK, UNKNOWN

  // Time labels only
  window: InteractionWindowLabel;    // W_TIGHT, W_NORMAL, W_WIDE
  timeLabel: InteractionTimeLabel;   // T_RECENT, T_MIN, T_HOUR, T_OLD

  // Explainability
  evidence: InteractionEvidence[];   // Max 3 pieces (label-only)
  warnings: string[];

  ts: number;                        // Internal storage only
}
```

**Interaction Evidence**:
```typescript
{
  kind: "EVID_DECISION" | "EVID_EFFECT" | "EVID_REGRESSION" | "EVID_NONE";
  label: string;          // Label-only (no numbers/tokens)
  strength: InteractionStrength;
}
```

### Fixed Detection Parameters

**Time Windows** (coarse classification):
- `W_TIGHT`: ≤ 30 minutes between adoptions
- `W_NORMAL`: ≤ 6 hours between adoptions
- `W_WIDE`: ≤ 24 hours between adoptions
- Beyond 24h: Not considered for interaction

**Scoring** (internal only, not displayed):
- Window scoring: W_TIGHT +2, W_NORMAL +1
- Regression involved: +3
- Effect worsened: +2
- Coupling risk threshold: ≥ 4 points

**Minimum Requirements**:
- At least 2 ADOPT decisions for pairing
- Effects/regressions are optional (improve evidence if available)

### Detection Priority (first-match-wins)

1. **INT_PATCH_PAIR_REGRESSION** (STRONG)
   - Regression detected after pair adoption
   - Evidence: EVID_REGRESSION with "REGRESSION_DETECTED_AFTER_PAIR"

2. **INT_COUPLING_RISK_HIGH** (STRONG/MEDIUM)
   - Internal coupling risk score ≥ threshold
   - Multiple evidence pieces combined

3. **INT_PATCH_FOLLOWS_WORSENING** (MEDIUM)
   - Effect worsened observed after pair
   - Evidence: EVID_EFFECT with "EFFECT_WORSENED_AFTER_PAIR"

4. **INT_MULTIPLE_ADOPTS_SAME_WINDOW** (MEDIUM/WEAK)
   - Multiple adoptions in tight/normal window
   - Evidence: EVID_DECISION with window label

5. **INT_UNKNOWN**
   - Ambiguous or insufficient data

### Interaction CLI

Detect patch coupling risks:

```bash
# View stored interaction reports
npx ts-node src/cli/interaction.ts

# Analyze decisions and detect new interactions
npx ts-node src/cli/interaction.ts --analyze

# Specify tail
npx ts-node src/cli/interaction.ts --tail 50

# Filter by proposal (matches primary or secondary)
npx ts-node src/cli/interaction.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# JSON output
npx ts-node src/cli/interaction.ts --json

# Debug mode (show numerics)
MERIDIAN_DEBUG=true npx ts-node src/cli/interaction.ts --analyze
```

### Example Output

**Normal Mode** (label-only):
```
=== Interaction Report V1 ===

Status: AVAILABLE
Primary: P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
Secondary: P0_ANOTHER_PATCH

Primary Decision: ADOPT
Secondary Decision: ADOPT

Interaction: INTERACTION_DETECTED
Kind: INT_PATCH_PAIR_REGRESSION
Strength: STRONG
Window: W_TIGHT
Time: T_RECENT

Evidence:
  - [EVID_REGRESSION] REGRESSION_DETECTED_AFTER_PAIR (STRONG)
  - [EVID_DECISION] ADOPT_WINDOW_TIGHT (MEDIUM)
```

**Debug Mode** (with numerics):
```json
{
  "kind": "INTERACTION_REPORT_V1",
  "status": "AVAILABLE",
  "primaryProposalId": "P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE",
  "secondaryProposalId": "P0_ANOTHER_PATCH",
  "primaryDecision": "ADOPT",
  "secondaryDecision": "ADOPT",
  "interaction": "INTERACTION_DETECTED",
  "interactionKind": "INT_PATCH_PAIR_REGRESSION",
  "strength": "STRONG",
  "window": "W_TIGHT",
  "timeLabel": "T_RECENT",
  "evidence": [
    {
      "kind": "EVID_REGRESSION",
      "label": "REGRESSION_DETECTED_AFTER_PAIR",
      "strength": "STRONG"
    },
    {
      "kind": "EVID_DECISION",
      "label": "ADOPT_WINDOW_TIGHT",
      "strength": "MEDIUM"
    }
  ],
  "warnings": [],
  "ts": 1705430400000
}
```

### Integration with Proposal/Review/Adopt Flow

PR176 strengthens the improvement loop by identifying coupling risks:

1. **PR167**: Propose patch based on analysis
2. **PR171**: Preview shows known interaction risks ← PR176 data
3. **PR172**: Review checklist considers coupling risk ← PR176 data
4. **PR168**: Adopt planning avoids simultaneous adoption ← PR176 data
5. **PR173**: Acknowledge adoption decision
6. **PR174**: Measure immediate effectiveness
7. **PR175**: Monitor persistence over time
8. **PR176**: Detect coupling when multiple patches interact ← NEW
9. **Back to PR167**: Use interaction evidence in next proposal

**Example Flow**:
- User adopts Patch A (reduce oracle blocks)
- 15 minutes later, adopts Patch B (adjust slippage limits)
- PR174: Both show IMPROVED immediately
- PR175: A shows regression after B adoption
- PR176: Detects INT_PATCH_PAIR_REGRESSION
- Evidence: "Patches A and B adopted in W_TIGHT window, regression detected"
- Next review: Checklist warns about coupling risk
- Adopt planning: Suggests spacing out similar patches

### Non-Claims

PR176 does **NOT**:
- ❌ Perform causal inference (correlation only, not causation)
- ❌ Automatically prevent adoptions (READ-ONLY observation only)
- ❌ Learn or optimize thresholds (fixed rules)
- ❌ Predict future interactions (pattern detection only)
- ❌ Provide trading advice (operational health monitoring only)

### What PR176 DOES

- ✅ Detect coupling patterns using fixed rules
- ✅ Identify adoption pairs close in time
- ✅ Correlate pairs with regressions/worsening
- ✅ Provide label-only evidence (normal mode)
- ✅ Strengthen proposal/review with coupling data
- ✅ Fail gracefully (defensive)

### Files

- src/interaction/types.ts: Interaction types
- src/interaction/guards.ts: Sanitization and formatting
- src/interaction/reader.ts: Read decisions/effects/regressions logs
- src/interaction/detector.ts: Interaction detection logic
- src/interaction/store.ts: JSONL storage
- src/interaction/index.ts: Barrel exports
- src/cli/interaction.ts: Interaction detection CLI
- tests/pr176.interaction_detector.test.ts: 14 comprehensive tests

**Purpose**: Detect patch coupling/interaction risks using READ-ONLY observation and fixed detection rules

## PR177: Pre-Adoption Risk Overlay v1 (Preview+Review Integration)

### Purpose
Inject known risk information from PR175 (regressions) and PR176 (interactions) into PR171 (preview) and PR172 (review) flows.
While PR175/176 detect problems after adoption, PR177 surfaces this knowledge before adoption.

Reads existing audit logs (READ-ONLY) to provide risk assessment overlay that appears in:
- Preview reports (PR171): riskOverlay field with label-only risk information
- Review checklists (PR172): Risk overlay acknowledgement items

This enables **採用前リスク可視化** (pre-adoption risk visualization): Users see known regression patterns and interaction risks before making adoption decisions.

### Constitutional Constraints
- **READ-ONLY**: Reads existing logs only (no modification/append)
- **Fixed rules**: Hardcoded risk assessment logic (no learning)
- **Label-only**: Display mode sanitizes numerics (normal mode)
- **Defensive**: Never throws, handles missing data gracefully
- **Non-blocking**: Overlay generation failures don't block adoption flow

### Overlay Model

**Risk Overlay**:
```typescript
{
  status: OverlayStatus;        // AVAILABLE, PARTIAL, ERROR

  proposalId: string;
  priority?: "P0" | "P1" | "P2" | "UNKNOWN";

  riskLevel: OverlayRiskLevel;  // RISK_HIGH, RISK_MEDIUM, RISK_LOW, RISK_UNKNOWN
  risks: Array<{                // Max 5, label-only
    kind: OverlayRiskKind;      // RISK_REGRESSION_HISTORY, RISK_INTERACTION_COUPLING, etc.
    label: string;
  }>;
  evidence: OverlayEvidence[];  // Max 3, sorted by strength

  warnings: string[];           // Label-only
}
```

**Evidence**:
```typescript
{
  kind: "EVID_REGRESSION" | "EVID_INTERACTION" | "EVID_NONE";
  label: string;                // Label-only (no numbers/tokens)
  strength: "STRONG" | "MEDIUM" | "WEAK" | "UNKNOWN";
}
```

### Fixed Risk Assessment Rules (priority-based)

1. **Regression evidence STRONG** → `RISK_HIGH`
   - Kind: `RISK_REGRESSION_HISTORY`
   - Label: "REGRESSION_STRONG_DETECTED_RECENTLY"
   - Evidence from PR175 regressions.log

2. **Interaction evidence STRONG** → `RISK_HIGH`
   - Kind: `RISK_INTERACTION_COUPLING`
   - Label: "INTERACTION_STRONG_DETECTED_RECENTLY"
   - Evidence from PR176 interactions.log

3. **Interaction evidence MEDIUM** → `RISK_MEDIUM`
   - Kind: `RISK_INTERACTION_COUPLING`
   - Label: "INTERACTION_MEDIUM_DETECTED_RECENTLY"

4. **Regression evidence MEDIUM** → `RISK_MEDIUM`
   - Kind: `RISK_REGRESSION_HISTORY`
   - Label: "REGRESSION_MEDIUM_DETECTED_RECENTLY"

5. **No evidence or UNKNOWN** → `RISK_UNKNOWN`
   - Kind: `RISK_EVIDENCE_WEAK`
   - Label: "NO_RECENT_EVIDENCE_FOUND"

6. **Otherwise** → `RISK_LOW`
   - Includes any weak evidence found

### Integration with Preview (PR171)

**Preview Report Enhanced**:
```typescript
{
  kind: "PATCH_PREVIEW_V1";
  ...
  riskOverlay?: RiskOverlayV1;  // ← PR177 adds this field
  ...
}
```

The overlay is automatically injected during preview generation:
- If overlay generation succeeds: `status: "AVAILABLE"`
- If logs are missing/incomplete: `status: "PARTIAL"` with warnings
- If overlay generation fails: `status: "ERROR"` (preview continues)

### Integration with Review (PR172)

Review checklist enhanced with risk overlay items (future enhancement):
- `CHECK_RISK_OVERLAY_PRESENT`: Overlay was generated
- `CHECK_RISK_OVERLAY_ACKED`: High-risk overlays acknowledged

**Example Review Flow**:
1. User requests `--review`
2. Preview is generated with overlay
3. Review checklist evaluates overlay presence
4. If `RISK_HIGH`: Adds warning to rationale
5. Reviewer must acknowledge risks before adoption

### Usage

Overlay is automatically generated when using preview/review:

```bash
# Preview with overlay (automatic)
npx ts-node src/cli/adopt.ts --preview --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# Review with overlay (automatic)
npx ts-node src/cli/adopt.ts --review --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE

# Overlay appears in preview.riskOverlay field
# Shows: riskLevel, risks (kinds + labels), evidence
```

### Example Output

**Preview with Risk Overlay**:
```
=== Patch Preview V1 ===

Proposal: P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
Priority: P0
Decision: ADOPT (candidate)

... (sections) ...

Risk Overlay:
  Status: AVAILABLE
  Risk Level: RISK_HIGH
  Risks:
    - [RISK_REGRESSION_HISTORY] REGRESSION_STRONG_DETECTED_RECENTLY
  Evidence:
    - [EVID_REGRESSION] REGRESSION_REGRESS_IMPROVED_TO_WORSENED (STRONG)
```

### Evidence Sorting

Evidence is automatically sorted by:
1. **Kind priority**: REGRESSION > INTERACTION > NONE
2. **Strength priority**: STRONG > MEDIUM > WEAK > UNKNOWN

This ensures the most critical evidence appears first (max 3 items shown).

### Non-Claims

PR177 does **NOT**:
- ❌ Perform causal inference (correlation only)
- ❌ Automatically block adoptions (READ-ONLY information only)
- ❌ Learn or optimize thresholds (fixed rules)
- ❌ Modify existing logs (reads only, no append)
- ❌ Provide trading advice (operational health monitoring only)

### What PR177 DOES

- ✅ Read existing regression/interaction logs
- ✅ Assess risk using fixed rules
- ✅ Inject risk overlay into preview reports
- ✅ Provide label-only evidence (normal mode)
- ✅ Surface known risks before adoption
- ✅ Fail gracefully (defensive)

### Files

- src/overlay/types.ts: Overlay types
- src/overlay/guards.ts: Sanitization and validation
- src/overlay/reader.ts: Read PR175/176 logs
- src/overlay/overlay.ts: Risk assessment engine
- src/overlay/index.ts: Barrel exports
- src/preview/types.ts: Added riskOverlay field (PR171 enhanced)
- tests/pr177.overlay_preview_review.test.ts: 12 comprehensive tests

**Purpose**: Surface known regression and interaction risks before adoption using READ-ONLY observation and fixed assessment rules

## PR178: Manual Review Trigger Hook v1

### Purpose
Provide a one-command human-initiated review pipeline that runs the complete analysis and review workflow:
**snapshot → analyze → propose → preview → review**

While Meridian normally operates in fully automatic execution mode, PR178 enables humans to trigger a comprehensive inspection when they notice something unusual: "Something feels off - run a full review and generate improvement proposals."

This separates **market response** (automatic, high-frequency) from **strategy improvement** (human-initiated, low-frequency).

### Constitutional Constraints
- **READ-ONLY**: No execution/policy changes, no trade stops, no state modification
- **Analysis only**: Does not affect automatic execution logic
- **Parallel operation**: Market response continues while review runs
- **Defensive**: Never throws, always returns status

### Architecture

**Automatic Execution (Unchanged)**:
```
Market Events → TWAP Engine → Execution
     ↓
  Snapshots (passive logging)
```

**Manual Review Pipeline (PR178 adds this)**:
```
Human Command
     ↓
Snapshot Read → Analyze → Propose → Preview → Review
     ↓
Improvement Proposals (for human decision)
```

Key insight: These run in **separate time scales**:
- **Automatic**: Milliseconds to seconds (market response)
- **Manual review**: Minutes to hours (strategy improvement)

### Pipeline Steps

1. **Snapshot**: Read recent snapshots from ~/.meridian/snapshots.log
2. **Analyze**: Run PR166 analysis on snapshots
3. **Propose**: Generate PR167 proposals with PR170 evidence
4. **Preview**: Create PR171 previews (with PR177 risk overlay)
5. **Review**: Run PR172 review checklist

**Execution Limits**:
- Default: 200 snapshots
- Top 3 proposals only (prevents overwhelming output)
- Priority filtering: P0, P1, P2, or ALL

### Usage

Run complete review pipeline:

```bash
# Basic usage
npx ts-node src/cli/review-trigger.ts

# Specify snapshot count
npx ts-node src/cli/review-trigger.ts --tail 300

# Filter by priority
npx ts-node src/cli/review-trigger.ts --priority P0

# JSON output
npx ts-node src/cli/review-trigger.ts --json

# Debug mode
MERIDIAN_DEBUG=true npx ts-node src/cli/review-trigger.ts --json
```

### Example Output

**Normal Mode**:
```
=== Manual Review Trigger ===

REVIEW_TRIGGER: TRIGGERED
SNAPSHOT: OK
ANALYZE: OK
PROPOSE: OK
PREVIEW: OK
REVIEW: OK

Warnings: WARN_NO_RECENT_REGRESSION_DATA
```

**Partial Success**:
```
=== Manual Review Trigger ===

REVIEW_TRIGGER: PARTIAL
SNAPSHOT: OK
ANALYZE: OK
PROPOSE: FAILED
PREVIEW: FAILED
REVIEW: FAILED

Warnings: ERROR_GENERATING_PROPOSALS, WARN_INSUFFICIENT_DATA
```

**JSON Mode** (with MERIDIAN_DEBUG=true):
```json
{
  "status": "TRIGGERED",
  "ranSnapshot": true,
  "ranAnalyze": true,
  "ranPropose": true,
  "ranPreview": true,
  "ranReview": true,
  "warnings": []
}
```

### Status Determination

- **TRIGGERED**: All steps succeeded
- **PARTIAL**: Some steps succeeded, some failed
- **ERROR**: Snapshot read failed or fatal error

All status transitions are defensive - the pipeline never throws exceptions.

### Integration with Existing Flow

PR178 leverages the complete analysis and review stack:

**Data Sources**:
- PR165: Snapshot storage
- PR175: Regression history (for overlay)
- PR176: Interaction history (for overlay)

**Analysis Pipeline**:
- PR166: Snapshot analysis
- PR167: Proposal generation
- PR170: Evidence collection
- PR171: Preview generation
- PR177: Risk overlay injection
- PR172: Review checklist

**Result**: Human gets comprehensive improvement proposals with:
- Evidence from recent operation
- Risk assessment from regression/interaction history
- Review checklist with recommendations
- All in one command

### Non-Claims

PR178 does **NOT**:
- ❌ Stop or pause automatic execution
- ❌ Modify trading logic or policy
- ❌ Automatically adopt proposals
- ❌ Affect TWAP engine or market response
- ❌ Change any system state

### What PR178 DOES

- ✅ Run complete analysis pipeline on demand
- ✅ Generate improvement proposals
- ✅ Surface regression and interaction risks
- ✅ Provide review checklist
- ✅ Enable human inspection without stopping execution
- ✅ Fail gracefully (defensive)

### Operational Philosophy

Meridian now operates in **two time scales**:

**Market Time** (Automatic):
- Execution: Continuous
- Response: Real-time
- Goal: Market participation

**Strategy Time** (Manual):
- Review: On-demand
- Response: Hours/days
- Goal: System improvement

This separation enables:
1. **Never miss market opportunities** (execution continues)
2. **Thoughtful improvement** (review at human pace)
3. **Professional risk management** (separate concerns)

### Files

- src/reviewTrigger/types.ts: Trigger types
- src/reviewTrigger/guards.ts: Sanitization
- src/reviewTrigger/pipeline.ts: Main orchestration logic
- src/reviewTrigger/index.ts: Barrel exports
- src/cli/review-trigger.ts: CLI tool
- tests/pr178.review_trigger.test.ts: 14 comprehensive tests

**Purpose**: Enable human-initiated comprehensive review without affecting automatic execution - separating market response from strategy improvement

---

## PR179: Spec Version Lock + Human ACK Gate v1

### Purpose

Spec generation (from PR166-178 analysis/propose/adopt) can be automatic, but **spec activation** requires human acknowledgement. This creates a gate between "spec produced" and "spec used for execution."

### Problem

Without PR179:
- New spec generated → immediately used for execution
- No human checkpoint before spec changes trading behavior
- Risk: Untested specs affecting live execution

With PR179:
- New spec generated → waits for human ACK
- Execution continues with last ACKed spec
- Human reviews → ACKs → new spec activated
- Real-time execution maintained (uses old ACKed spec)

### Spec Lock States

1. **ACTIVE_OK**: Latest spec is ACKed, execution proceeds normally
2. **LOCKED_PENDING_ACK**: New spec exists, awaiting human ACK
   - activeSpec = last ACKed version (execution continues)
   - latestSpec = newest version (not yet active)
3. **LOCKED_EXPIRED**: New spec TTL exceeded (6h default)
   - Still requires human ACK (v1 doesn't auto-unlock)
   - Execution continues with old ACKed spec
4. **ERROR**: Lock evaluation failed

### Constitutional Constraints

- **Fixed rules**: Deterministic lock evaluation
- **Defensive**: Never throws, always returns status
- **Label-only**: No numerics/addresses/tokens in output
- **Double-key preserved**: PR156 execution policy still applies
- **READ-ONLY**: Adds gate, doesn't modify trading logic

### Key Insight: Separation of Concerns

**Spec Generation ≠ Spec Activation**

- Analysis can run automatically
- Proposals can be generated automatically
- But **activation** requires human decision
- Maintains real-time execution with stable ACKed spec

### CLI Usage

```bash
# Check current spec lock status
npx ts-node src/cli/spec.ts status

# ACK the latest spec
npx ts-node src/cli/spec.ts ack --reviewer HUMAN_PRIMARY --reason READ_AND_ACCEPT

# View spec and ACK history
npx ts-node src/cli/spec.ts log --tail 20

# Debug mode (shows timestamps)
MERIDIAN_DEBUG=true npx ts-node src/cli/spec.ts status
```

### Executor Integration

The executor checks spec lock before allowing execution:

**Block Conditions**:
- status=ERROR → BLOCK_SPEC_LOCK_ERROR
- status=LOCKED_PENDING_ACK && !activeSpec → BLOCK_SPEC_ACK_REQUIRED

**Allow Conditions**:
- status=ACTIVE_OK → OK (use activeSpec)
- status=LOCKED_PENDING_ACK && activeSpec exists → OK (use old spec)
- status=LOCKED_EXPIRED && activeSpec exists → OK (use old spec, warn)

### TTL Design (6h Default)

TTL is an **observation label**, not automatic unlock:
- Within TTL → ttlLabel=TTL_OK
- Beyond TTL → ttlLabel=TTL_EXPIRED

**Important**: v1 does NOT auto-unlock on TTL expiration (safe default)
- Expired specs still require human ACK
- TTL helps humans identify "stale pending specs"
- Future versions may add auto-unlock with constraints

### Storage

Append-only JSONL logs:
- `~/.meridian/specs.log` - Spec records
- `~/.meridian/spec_acks.log` - ACK records

### Telemetry Events

- SPEC_LOCK_STATUS (INFO)
- SPEC_LOCK_EXPIRED (WARN)
- SPEC_LOCK_ERROR (ERROR)
- SPEC_ACK_WRITTEN (INFO)
- SPEC_RECORD_WRITTEN (INFO)

### Files

- src/spec/types.ts: Spec version types
- src/spec/guards.ts: Label-only sanitization
- src/spec/store.ts: Append-only JSONL logs
- src/spec/lock.ts: Lock evaluation logic
- src/spec/index.ts: Barrel exports
- src/cli/spec.ts: CLI tool
- tests/pr179.spec_lock.test.ts: 14 comprehensive tests

### Safety Properties

1. **Non-blocking**: Execution never stops, uses last ACKed spec
2. **Defensive**: Lock evaluation never throws
3. **Label-only**: All output sanitized
4. **Audit trail**: All specs and ACKs logged
5. **Human control**: Activation requires explicit ACK

**Purpose**: Require human ACK to activate new specs while maintaining real-time execution with stable ACKed specs - separating spec generation from spec activation.

---

## PR180: Spec Change Digest v1

### Purpose

PR179 introduced human ACK gates for spec activation. However, if the "reading cost" of ACK is high, improvement stalls. PR180 compresses pre-ACK information into a single screen (label-only) to answer:
- **What is changing?**
- **Why change it?**
- **Are there risks?**
- **What is the expected impact?**

Execution (trading) never stops. Only "reading spec changes without understanding" is prevented. PR180 makes "reading" dramatically lighter.

### Problem

Without PR180:
- ACK requires reading: spec lock + patch plan + preview + review + decision
- Too much information → ACK backlog → improvement stalls
- Reading cost becomes adoption bottleneck

With PR180:
- All information compressed into single digest (label-only)
- HEADLINE/WHY/WHAT/RISKS/CHECKLIST/RATIONALE in one view
- Reading time: seconds instead of minutes
- ACK throughput increases → improvement loop accelerates

### Digest Structure

```
HEADLINE: What is happening
  - PENDING_ACK
  - HAS_PREVIEW
  - HAS_REVIEW
  - HAS_PATCHPLAN

WHY: Why change
  - EVIDENCE_ORACLE_DOMINANT
  - BOTTLENECK_ORACLE

WHAT: What changes
  - PATCH_GATE_ORDER
  - PATCH_PHASE_POLICY

RISKS: What to watch
  - RISK_PATCH_NOT_ALLOWED_PRESENT
  - RISK_CHECKLIST_FAIL_PRESENT

CHECKLIST: Review summary
  - CHECK_EVIDENCE_PASS
  - CHECK_REGRESSION_PASS

RATIONALE: Decision basis
  - (from PR172 review rationale)

SUGGESTED_NEXT: ACK_OK|ACK_HOLD|ACK_REJECT|ACK_UNKNOWN

REFS: What was referenced
  - hasSpecLock: true
  - hasPatchPlan: true
  - hasPreview: true
  - hasReview: true
```

### Constitutional Constraints

- **READ-ONLY**: Digest generation is observation/summary only
- **Fixed rules**: Template/extraction/formatting are fixed rules
- **Label-only**: No numerics, prices, addresses, tokens, specific times in normal mode
- **Debug mode**: MERIDIAN_DEBUG=true allows internal JSON (but secrets always sanitized)
- **Defensive**: Never throws
- **No coupling**: Digest is "reading material", not execution instruction

### CLI Usage

```bash
# View latest digest (label-only)
npx ts-node src/cli/digest.ts

# View recent digests
npx ts-node src/cli/digest.ts --tail 20

# JSON format
npx ts-node src/cli/digest.ts --json

# Debug mode (internal timestamps)
MERIDIAN_DEBUG=true npx ts-node src/cli/digest.ts --json
```

### Inputs (Loosely Coupled)

Digest can reference (when available):
- PR179: Spec lock status
- PR168: Patch plan
- PR171: Preview
- PR172: Review
- PR173: Decision ACK
- PR174: Effects (optional)
- PR169: Attribution (optional)
- PR170: Evidence (optional)

All inputs are optional. Missing inputs → PARTIAL status + warnings.

### Extraction Rules (Fixed)

**Headline** (what is happening):
- Spec lock status
- Preview/review availability
- Decision ACK presence

**What** (what changes):
- Patch ops (max 3, order preserved)

**Why** (why change):
- Strong/medium evidence (max 3)
- Bottlenecks (max 2)

**Risks** (what to watch):
- Preview risks (max 3)
- Checklist failures
- NOT_ALLOWED patches

**Suggested Next** (reading recommendation, not command):
- CANDIDATE_ADOPT → ACK_OK
- CANDIDATE_HOLD → ACK_HOLD
- CANDIDATE_REJECT → ACK_REJECT

### Non-Claims

PR180 does **NOT**:
- ❌ Make predictions or forecasts
- ❌ Issue execution instructions
- ❌ Automatically adopt or ACK
- ❌ Learn or optimize
- ❌ Modify any system state

### What PR180 DOES

- ✅ Compress multi-source information
- ✅ Extract key signals using fixed rules
- ✅ Sanitize to label-only format
- ✅ Store digests for audit trail
- ✅ Reduce reading cost dramatically
- ✅ Enable faster ACK throughput

### Why This Matters for Policy-First

1. **PR179**: Separated execution from spec activation
2. **PR180**: Reduced spec reading cost to near-zero
3. **Result**: ACK throughput increases → improvement loop accelerates
4. **Benefit**: Real-time execution maintained + fast improvement

### Files

- src/digest/types.ts: Digest types
- src/digest/guards.ts: Label-only sanitization
- src/digest/templates.ts: Fixed extraction rules
- src/digest/digester.ts: Digest builder
- src/digest/store.ts: Append-only JSONL logs
- src/digest/index.ts: Barrel exports
- src/cli/digest.ts: CLI tool
- tests/pr180.digest.test.ts: 14 comprehensive tests

### Storage

Append-only JSONL log:
- `~/.meridian/digests.log`

**Purpose**: Compress pre-ACK reading cost from minutes to seconds using label-only fixed-rule extraction - enabling fast ACK throughput while maintaining execution safety.

---

## PR181: Observe 1s Loop + Chunk 10s + Immediate STOP v1

### Purpose

Trading requires real-time responsiveness. Observation updates every 1 second to keep state (shock/stress/trend/labels) current. Execution uses 10-second chunk intervals (PR160 FAST profile continued). When market deterioration is detected, STOP is immediate (including sleep interruption).

### Problem

Without PR181:
- Observation frequency unclear or too slow
- State becomes stale between ticks
- STOP detection delayed until next tick
- Sleep cannot be interrupted → delayed response

With PR181:
- Observation: 1-second fixed interval
- State: Always current (phase, trend, oracle, labels)
- STOP: Immediate via AbortSignal
- Sleep: Interruptible for instant STOP response

### Fixed Rules

**1. Observation Loop: 1 second**
- OBSERVE_INTERVAL_MS = 1000 (fixed)
- Every 1 second:
  1. observeAndLabel() (PR154)
  2. Shock Phase determination
  3. Stress/Policy latest (PR150/156)
  4. Trend (UP/DOWN/RANGE) determination
  5. Save to ObserveStateV1 in state

**2. Chunk Execution: 10 seconds**
- CHUNK_INTERVAL_MS = 10_000 (PR160 continued)
- Execution start: Immediate when conditions met
- Next chunk interval: 10 seconds only
- Large execution divided into 10-second chunks

**3. STOP: Immediate (sleep interruption)**
- Runner sleepMs(ms, signal) supports AbortSignal
- sleepMs(ms, signal): Resolves immediately on abort
- Observe loop detects STOP → updates global StopToken
- Runner checks stopToken before each chunk/quote/gate/sleep
- Immediate STOP on detection

### STOP Conditions (Fixed Table)

**PR181a Update**: Spec lock is NO LONGER a STOP reason. Market execution continues with activeSpec.

STOP signal triggered when:
1. **Phase**: PHASE_UNKNOWN, PHASE_ERROR, PHASE_PRE_SHOCK, PHASE_UP_SHOCK, PHASE_DOWN_SHOCK, PHASE_UP_REVERSAL, PHASE_DOWN_REVERSAL
2. **Oracle**: STALE or ERROR status
3. **HardStop**: active=true (PR156)

NO_STOP when:
- Phase: PHASE_NORMAL or PHASE_RECOVERY
- Oracle: AVAILABLE
- HardStop: inactive

**Spec ACK Status** (PR181a): Visible but NOT a STOP reason
- Spec lock pending/expired does NOT stop market execution
- Execution continues with last ACKed spec (activeSpec)
- Exception: Bootstrap (no activeSpec) requires initial ACK

### Data Structures

**ObserveStateV1** (saved to state):
```typescript
{
  status: "AVAILABLE" | "PARTIAL" | "ERROR",
  phaseLabel: "PHASE_*",
  trendLabel: "UP_TREND" | "DOWN_TREND" | "RANGE" | "UNKNOWN",
  labelsPresence: "HAS_LABELS" | "NO_LABELS",
  oracleStatus: "AVAILABLE" | "STALE" | "ERROR" | "UNKNOWN",
  stopSignal: "STOP" | "NO_STOP" | "UNKNOWN",
  specAckStatus?: "SPEC_ACK_OK" | "SPEC_ACK_PENDING" | "SPEC_ACK_EXPIRED" | "SPEC_ACK_REQUIRED_BOOTSTRAP" | "SPEC_ACK_UNKNOWN", // PR181a
  warnings: string[] // label-only
}
```

**StopTokenV1** (in-memory):
```typescript
{
  status: "STOP" | "CLEAR",
  reason: string, // label-only
  tsLabel: "T_RECENT" | "T_MIN" | "T_HOUR" | "T_OLD" | "T_UNKNOWN"
}
```

### Constitutional Constraints

- **Fixed rules**: No learning, optimization, or prediction
- **READ-ONLY**: Observation updates state only
- **Double-key preserved**: PR156 + PR179 still control execution
- **Label-only**: No numerics in normal mode (debug only)
- **Defensive**: Never throws, always returns result

### CLI Usage

```bash
# View observe state
npx ts-node src/cli/observe.ts status

# View stop token
npx ts-node src/cli/observe.ts stop-token

# JSON format
npx ts-node src/cli/observe.ts --json

# Debug mode
MERIDIAN_DEBUG=true npx ts-node src/cli/observe.ts --json
```

### Integration Points

**Supervisor (PR163)**:
- Tick triggers observe loop if not running
- Observe loop updates state only (no execution)
- Supervisor references latest observeState for decisions

**Runner (PR159)**:
- Sleep uses AbortSignal: sleepMs(ms, signal)
- Checks stopToken before each chunk/quote/gate
- Immediate STOP when token status = "STOP"

**State (PR163)**:
- MeridianStateV1.observeState stores latest observation
- Updated every 1 second by observe loop
- Persistent across supervisor restarts

### Telemetry Events (PR164)

- OBSERVE_TICK: Loop iteration completed
- OBSERVE_STATE: State updated successfully
- OBSERVE_ERROR: Observation error occurred
- STOP_SIGNAL_RAISED: STOP condition detected
- STOP_SIGNAL_CLEARED: Conditions safe again
- SPEC_ACK_PENDING_WARN: Spec ACK pending (PR181a)
- SPEC_ACK_EXPIRED_WARN: Spec ACK expired (PR181a)
- SPEC_ACK_REQUIRED_BOOTSTRAP_WARN: Spec ACK required bootstrap (PR181a)

### Files

- src/observeLoop/types.ts: Observe state types
- src/observeLoop/guards.ts: Label-only sanitization
- src/observeLoop/loop.ts: Main observe loop logic
- src/observeLoop/index.ts: Barrel exports
- src/cli/observe.ts: Observe state CLI
- tests/pr181.observe_loop.test.ts: 14 comprehensive tests

### Safety Properties

1. **Non-blocking**: Observation never blocks execution
2. **Defensive**: Loop never throws, always returns state
3. **Label-only**: All output sanitized
4. **Immediate**: STOP response < 1 second
5. **Interruptible**: Sleep can be aborted instantly

**Purpose**: Maintain real-time market observation (1s) with safe chunked execution (10s) and immediate STOP capability - ensuring fresh state while preserving execution safety.

⸻

## PR181a: Spec Lock ≠ STOP (Run-on-Old-Spec) v1

### Purpose

Separate market risk STOP conditions from spec ACK requirements. Spec lock pending/expired should NOT stop market execution - execution continues with the last ACKed spec (activeSpec). This prevents conflating "don't stop in the market" with "require human ACK for spec changes".

### Problem

**Before PR181a**:
- Spec lock pending/expired was treated as a STOP condition (PR181 line 103-106)
- Market execution would halt when waiting for human ACK
- Confuses two distinct concerns:
  1. Market risk safety (phase errors, oracle stale, hardStop)
  2. Human approval workflow (spec version ACK)

**After PR181a**:
- Spec lock status is VISIBLE but NOT a STOP reason
- Execution continues with activeSpec (last ACKed spec)
- Only bootstrap (no activeSpec) requires initial ACK
- Spec ACK status emits WARN events for visibility

### Fixed Rules

**1. STOP Conditions (Market Risk Only)**
- Phase: ERROR, UNKNOWN, or shock phases
- Oracle: STALE or ERROR
- HardStop: active=true

**2. Spec ACK Status (Visible, Not STOP)**
- SPEC_ACK_OK: activeSpec exists, latest spec ACKed
- SPEC_ACK_PENDING: latest spec not ACKed, continue with activeSpec
- SPEC_ACK_EXPIRED: TTL exceeded, continue with activeSpec
- SPEC_ACK_REQUIRED_BOOTSTRAP: no activeSpec (initial), ACK required

**3. Telemetry WARN Events**
- SPEC_ACK_PENDING_WARN: Latest spec awaiting human ACK
- SPEC_ACK_EXPIRED_WARN: Spec lock TTL exceeded
- SPEC_ACK_REQUIRED_BOOTSTRAP_WARN: Bootstrap requires initial ACK

### Code Changes

**evaluateStopSignal()** (src/observeLoop/loop.ts):
- Removed: specLockPending parameter
- Removed: spec lock as STOP condition
- Result: Only market risk conditions cause STOP

**evaluateSpecAckStatus()** (src/observeLoop/loop.ts):
- New function: Evaluates spec ACK status separately
- Returns: SpecAckStatusLabel (not StopSignal)
- Logic: hasActiveSpec determines if execution can continue

**runObserveTick()** (src/observeLoop/loop.ts):
- Added: getSpecLockStatus and getHasActiveSpec dependencies
- Added: specAckStatus evaluation
- Added: WARN event emission for spec ACK status
- Updated: observeState includes specAckStatus field

### Data Structures

**SpecAckStatusLabel** (new type):
```typescript
type SpecAckStatusLabel =
  | "SPEC_ACK_OK"
  | "SPEC_ACK_PENDING"
  | "SPEC_ACK_EXPIRED"
  | "SPEC_ACK_REQUIRED_BOOTSTRAP"
  | "SPEC_ACK_UNKNOWN";
```

**ObserveStateV1** (updated):
```typescript
{
  // ... existing fields ...
  specAckStatus?: SpecAckStatusLabel; // PR181a: visible but not STOP
}
```

### Constitutional Constraints

- **Separation of concerns**: Market risk vs spec approval workflow
- **Fixed rules**: No learning, optimization, or prediction
- **READ-ONLY**: Observation updates state only
- **Label-only**: All status values are strings
- **Defensive**: Never throws, always returns result

### Behavioral Changes

**Scenario 1**: Spec lock pending + activeSpec exists
- Before: STOP (execution halted)
- After: NO_STOP (continue with activeSpec, emit WARN)

**Scenario 2**: Spec lock expired + activeSpec exists
- Before: STOP (execution halted)
- After: NO_STOP (continue with activeSpec, emit WARN)

**Scenario 3**: No activeSpec (bootstrap)
- Before: STOP (via specLockPending flag)
- After: NO_STOP in observe, but executor/gate will BLOCK (unchanged)

**Scenario 4**: Oracle STALE
- Before: STOP
- After: STOP (unchanged - this is market risk)

### Integration

**Supervisor**:
- Observe loop updates specAckStatus in state
- Supervisor reads observeState.specAckStatus for visibility
- Execution decisions use activeSpec from spec store (PR179)

**Executor**:
- Spec lock check remains (PR179 executor.ts)
- Executor uses activeSpec when available
- Executor blocks only if no activeSpec exists

**Telemetry**:
- WARN events provide strong visibility
- Spec ACK status always visible in logs
- Human can monitor pending ACKs without execution stopping

### CLI Usage

```bash
# View observe state (includes specAckStatus)
npx ts-node src/cli/observe.ts status

# Expected output includes:
# - specAckStatus: SPEC_ACK_OK | SPEC_ACK_PENDING | etc
# - Note: specAckStatus is visible but NOT a STOP reason
```

### Safety Properties

1. **Market continuity**: Execution never stops due to spec ACK delay
2. **Visibility**: Spec ACK status always visible in telemetry/state
3. **Bootstrap safety**: Initial ACK still required (no activeSpec)
4. **Separation**: Market risk STOP vs spec approval clearly distinct
5. **Defensive**: All evaluations handle errors gracefully

**Purpose**: Decouple market execution continuity from spec approval workflow - allowing execution to continue with proven activeSpec while maintaining strong visibility of spec ACK status.
