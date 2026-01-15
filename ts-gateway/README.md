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
