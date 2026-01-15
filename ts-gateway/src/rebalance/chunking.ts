/**
 * PR159: v1.4 Chunked Execution / TWAP-lite v1 (READ-ONLY)
 *
 * Purpose:
 *   Split large rebalances into multiple smaller chunks to avoid self-induced market shocks.
 *   Notional-based chunking with fixed parameters.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Fixed rules, no learning, no optimization, no prediction
 *   - Deterministic: Same input always produces same chunk plan
 *   - Label-only output: No numbers in reasons (internal numeric values OK)
 *   - Conservative: Safe defaults, prefer STOP when uncertain
 *   - TWAP-lite: Not strict TWAP, simplified interval-based execution
 */

import { RunPlan, ChunkPlan } from "./types";

/**
 * Fixed chunking parameters (constitutional constants)
 * PR160: FAST Profile v1.1 - Updated for faster execution
 */
const CHUNKING_PARAMS = {
  // Maximum notional USD per run (aligned with PR153/155/156 cap)
  MAX_NOTIONAL_USD_PER_RUN: 200_000,

  // Maximum number of chunks per run (PR160: 6 → 3)
  MAX_CHUNKS: 3,

  // Minimum notional USD per chunk (chunks below this are skipped)
  MIN_CHUNK_NOTIONAL_USD: 10_000,

  // Target chunk size (notional USD) (PR160: 50k → 70k)
  TARGET_CHUNK_NOTIONAL_USD: 70_000,

  // Interval between chunks (milliseconds) (PR160: 30s → 10s)
  CHUNK_INTERVAL_MS: 10_000, // 10 seconds

  // Maximum run duration (milliseconds) (PR160: 10min → 60s)
  MAX_RUN_DURATION_MS: 60_000, // 60 seconds
};

/**
 * Build chunk plans from total notional (v1)
 *
 * @param args - Chunking parameters
 * @returns Run plan with chunk plans
 *
 * Fixed rules (deterministic):
 *   1. If baseIntent = NOOP → chunks = [], status = COMPLETED
 *   2. If totalNotionalUsd = 0 → chunks = [], status = COMPLETED
 *   3. If totalNotionalUsd > MAX_NOTIONAL_USD_PER_RUN → cap and warn
 *   4. Calculate chunkSize = min(DEFAULT_CHUNK_NOTIONAL_USD, totalNotionalUsd)
 *   5. Calculate numChunks = ceil(totalNotionalUsd / chunkSize)
 *   6. If numChunks > MAX_CHUNKS → cap at MAX_CHUNKS
 *   7. Distribute notional across chunks (last chunk gets remainder)
 *   8. Skip chunks with notional < MIN_CHUNK_NOTIONAL_USD
 *
 * IMPORTANT: Returns label-only reasons (no numeric values in reasons)
 */
export function buildChunkPlansV1(args: {
  totalNotionalUsd: number;
  templateId: string;
  baseIntent: "INCREASE_WBTC" | "DECREASE_WBTC" | "NOOP";
  maxChunks?: number;
  chunkNotionalUsd?: number;
  runId?: string;
  getNowMs?: () => number;
}): RunPlan {
  const reasons: string[] = [];
  const nowMs = args.getNowMs ? args.getNowMs() : Date.now();
  const runId = args.runId || `run-${nowMs}`;

  // Step 1: Check if baseIntent is NOOP
  if (args.baseIntent === "NOOP") {
    reasons.push("REASON_BASE_INTENT_NOOP");

    return {
      runId,
      status: "COMPLETED",
      createdAtMs: nowMs,
      templateId: args.templateId,
      totalNotionalUsd: 0,
      chunks: [],
      reasons,
    };
  }

  // Step 2: Check if totalNotionalUsd is zero or negative
  if (args.totalNotionalUsd <= 0) {
    reasons.push("REASON_TOTAL_NOTIONAL_ZERO");

    return {
      runId,
      status: "COMPLETED",
      createdAtMs: nowMs,
      templateId: args.templateId,
      totalNotionalUsd: 0,
      chunks: [],
      reasons,
    };
  }

  // Step 3: Cap totalNotionalUsd if exceeds MAX_NOTIONAL_USD_PER_RUN
  let effectiveNotional = args.totalNotionalUsd;

  if (effectiveNotional > CHUNKING_PARAMS.MAX_NOTIONAL_USD_PER_RUN) {
    reasons.push("REASON_NOTIONAL_CAPPED_AT_MAX");
    effectiveNotional = CHUNKING_PARAMS.MAX_NOTIONAL_USD_PER_RUN;
  }

  // Step 4: Calculate number of chunks (PR160: 70k target, max 3)
  const targetChunkSize =
    args.chunkNotionalUsd ?? CHUNKING_PARAMS.TARGET_CHUNK_NOTIONAL_USD;
  const maxChunks = args.maxChunks ?? CHUNKING_PARAMS.MAX_CHUNKS;

  // idealChunks = ceil(total / 70k)
  const idealChunks = Math.ceil(effectiveNotional / targetChunkSize);

  // chunkCount = clamp(idealChunks, 1, maxChunks)
  let numChunks = Math.max(1, Math.min(idealChunks, maxChunks));

  if (idealChunks > maxChunks) {
    reasons.push("REASON_CHUNK_COUNT_LIMITED");
  }

  // Step 5: Distribute notional evenly across chunks
  // baseChunk = floor(total / chunkCount)
  // remainder = total - baseChunk * chunkCount
  const baseChunkNotional = Math.floor(effectiveNotional / numChunks);
  const remainder = effectiveNotional - baseChunkNotional * numChunks;

  // Step 6: Build chunks with even distribution + remainder in first chunks
  const chunks: ChunkPlan[] = [];

  for (let i = 0; i < numChunks; i++) {
    // Add +1 USD to first 'remainder' chunks
    const chunkNotional = baseChunkNotional + (i < remainder ? 1 : 0);

    // Skip chunks with notional below minimum (rare with max 3 chunks)
    if (chunkNotional < CHUNKING_PARAMS.MIN_CHUNK_NOTIONAL_USD) {
      reasons.push("REASON_CHUNK_NOTIONAL_TOO_SMALL_SKIPPED");
      continue;
    }

    chunks.push({
      chunkId: `${runId}-chunk-${i + 1}`,
      notionalUsd: chunkNotional,
      intent: args.baseIntent,
      templateId: args.templateId,
    });
  }

  // Step 7: If no chunks after filtering, mark as COMPLETED
  if (chunks.length === 0) {
    reasons.push("REASON_NO_VALID_CHUNKS");

    return {
      runId,
      status: "COMPLETED",
      createdAtMs: nowMs,
      templateId: args.templateId,
      totalNotionalUsd: effectiveNotional,
      chunks: [],
      reasons,
    };
  }

  // Step 8: Add informational reason
  reasons.push("REASON_CHUNKED_EXECUTION_ENABLED");

  return {
    runId,
    status: "PLANNED",
    createdAtMs: nowMs,
    templateId: args.templateId,
    totalNotionalUsd: effectiveNotional,
    chunks,
    reasons,
  };
}

/**
 * Get chunking summary (for logging/debugging)
 *
 * @param plan - Run plan
 * @returns Summary string (label-only)
 */
export function getChunkingSummary(plan: RunPlan): string {
  if (plan.status === "COMPLETED" && plan.chunks.length === 0) {
    return "CHUNKING_NO_CHUNKS";
  }

  if (plan.status === "PLANNED" && plan.chunks.length > 0) {
    return "CHUNKING_PLANNED";
  }

  return `CHUNKING_${plan.status}`;
}

/**
 * Export chunking parameters for testing
 */
export { CHUNKING_PARAMS };
