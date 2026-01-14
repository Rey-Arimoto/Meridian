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
