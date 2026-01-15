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
