/**
 * PR179: v1.4 Spec Version Lock + Human ACK Gate v1 - Lock Evaluation
 *
 * Purpose:
 *   Evaluate spec lock status to determine if execution can proceed with new spec.
 *
 * Constitutional Constraints:
 *   - Fixed rules: Deterministic lock evaluation
 *   - Defensive: Never throws, always returns result
 *   - Safety: LOCKED_EXPIRED does not auto-unlock (observation label only)
 */

import {
  SpecLockConfig,
  SpecLockResultV1,
  SpecLockStatus,
} from "./types";
import {
  readLatestSpecRecordV1,
  readLatestAckedSpecV1,
  readLatestAckForSpecV1,
} from "./store";
import { buildLabelWarning } from "./guards";

/**
 * Default config
 */
const DEFAULT_CONFIG: SpecLockConfig = {
  ttlMs: 6 * 60 * 60 * 1000, // 6 hours
};

/**
 * Evaluate spec lock status
 *
 * @param cfg - Optional config override
 * @param pathOverride - Optional path override for testing
 * @returns Lock result
 */
export async function evaluateSpecLockV1(
  cfg?: Partial<SpecLockConfig>,
  pathOverride?: { specLog?: string; ackLog?: string }
): Promise<SpecLockResultV1> {
  const config = { ...DEFAULT_CONFIG, ...cfg };
  const warnings: string[] = [];

  try {
    // Read latest spec record
    const latestSpecRecord = await readLatestSpecRecordV1(
      pathOverride?.specLog
    );

    // Case A: No spec records
    if (!latestSpecRecord) {
      return {
        kind: "SPEC_LOCK_RESULT_V1",
        status: "ACTIVE_OK",
        activeSpec: "SPEC_NONE",
        warnings: [buildLabelWarning("INFO_NO_SPEC_RECORDS")],
      };
    }

    const latestSpec = latestSpecRecord.specVersion;

    // Read latest ACKed spec
    const latestAckedSpec = await readLatestAckedSpecV1(
      pathOverride?.ackLog
    );

    // Case B: Spec exists, but no ACK at all
    if (!latestAckedSpec) {
      return {
        kind: "SPEC_LOCK_RESULT_V1",
        status: "LOCKED_PENDING_ACK",
        latestSpec: latestSpec,
        activeSpec: undefined,
        ttlLabel: "TTL_UNKNOWN",
        warnings: [buildLabelWarning("WARN_NO_ACK_FOUND")],
      };
    }

    // Case C: Latest spec matches latest ACKed spec
    if (latestSpec === latestAckedSpec) {
      return {
        kind: "SPEC_LOCK_RESULT_V1",
        status: "ACTIVE_OK",
        activeSpec: latestAckedSpec,
        latestSpec: latestSpec,
        ttlLabel: "TTL_OK",
        warnings: [],
      };
    }

    // Case D: Latest spec != latest ACKed spec
    // Check TTL of latest spec
    const now = Date.now();
    const specAge = now - latestSpecRecord.createdAt;

    let status: SpecLockStatus = "LOCKED_PENDING_ACK";
    let ttlLabel: "TTL_OK" | "TTL_EXPIRED" | "TTL_UNKNOWN" = "TTL_OK";

    if (specAge > config.ttlMs) {
      status = "LOCKED_EXPIRED";
      ttlLabel = "TTL_EXPIRED";
      warnings.push(buildLabelWarning("WARN_SPEC_TTL_EXPIRED"));
    } else {
      warnings.push(buildLabelWarning("WARN_SPEC_PENDING_ACK"));
    }

    return {
      kind: "SPEC_LOCK_RESULT_V1",
      status: status,
      activeSpec: latestAckedSpec, // Use old ACKed spec for execution
      latestSpec: latestSpec,
      ttlLabel: ttlLabel,
      warnings: warnings,
    };
  } catch (error) {
    // Case E: Error during evaluation
    return {
      kind: "SPEC_LOCK_RESULT_V1",
      status: "ERROR",
      warnings: [buildLabelWarning("WARN_SPEC_LOCK_EVAL_FAILED")],
    };
  }
}
