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
