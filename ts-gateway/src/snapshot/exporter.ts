/**
 * PR165: v1.4 Market Regime Snapshot Export v1 - Exporter
 *
 * Purpose:
 *   Build and save market regime snapshots for strategy verification.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Snapshots are observations, not recommendations
 *   - Defensive: Never throws, always returns snapshot (even on error)
 *   - Fixed rules: No prediction, no optimization, no learning
 *   - Append-only: JSONL format, one snapshot per line
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  MarketRegimeSnapshotV1,
  SnapshotKind,
  SnapshotStatus,
  SnapshotPresence,
  SnapshotLabels,
  SnapshotNumerics,
} from "./types";
import { sanitizeSnapshotLabel } from "./guards";

/**
 * Snapshot inputs (from supervisor/state/runner)
 */
export interface SnapshotInputsV1 {
  // State path (optional)
  statePath?: string;

  // Latest results (from supervisor/runner)
  latest?: {
    shockPhase?: string;
    stress?: string;
    stressEscalated?: string;
    actionShape?: string;
    templateId?: string;
    route?: string;
    gateDecision?: "PASS" | "BLOCK" | "ERROR";
    blockReason?: string;
    policyDecision?: "ALLOW" | "DENY";
    policyReason?: string;
    hardStop?: "ACTIVE" | "INACTIVE" | "UNKNOWN";
    cooldown?: "ACTIVE" | "INACTIVE" | "UNKNOWN";
    drift?: "SMALL" | "OK" | "UNKNOWN";
    resume?: "NONE" | "RESUMABLE" | "WAIT" | "ABANDON" | "UNKNOWN";

    // PR154: Observation labels
    observation?: Partial<{
      impulse: "TRUE" | "FALSE" | "UNKNOWN";
      thinning: "TRUE" | "FALSE" | "UNKNOWN";
      dominance: "BUY" | "SELL" | "NONE" | "UNKNOWN";
      absorption: "ASK_PRESENT" | "BID_PRESENT" | "RELEASED" | "NONE" | "UNKNOWN";
    }>;

    // Numerics (save-only)
    numerics?: {
      notionalUsd?: number;
      targetNotionalUsd?: number;
      oracleAgeMs?: number;
    };
  };

  // Build provenance (optional)
  build?: {
    tag?: string;
    commit?: string;
  };
}

/**
 * Build presence flags from inputs
 *
 * @param inputs - Snapshot inputs
 * @returns Presence flags
 */
function buildPresence(inputs?: SnapshotInputsV1): SnapshotPresence {
  const latest = inputs?.latest;

  return {
    hasOracle:
      latest?.numerics?.oracleAgeMs !== undefined ||
      latest?.gateDecision !== undefined,
    hasObservationLabels: latest?.observation !== undefined,
    hasShockPhase: latest?.shockPhase !== undefined,
    hasStress: latest?.stress !== undefined,
    hasEscalation: latest?.stressEscalated !== undefined,
    hasActionShape: latest?.actionShape !== undefined,
    hasTemplateId: latest?.templateId !== undefined,
    hasRoute: latest?.route !== undefined,
    hasGate: latest?.gateDecision !== undefined,
    hasPolicy: latest?.policyDecision !== undefined,
    hasHardStop: latest?.hardStop !== undefined,
    hasCooldown: latest?.cooldown !== undefined,
    hasDrift: latest?.drift !== undefined,
    hasResume: latest?.resume !== undefined,
  };
}

/**
 * Build labels from inputs (label-only)
 *
 * @param inputs - Snapshot inputs
 * @returns Snapshot labels
 */
function buildLabels(inputs?: SnapshotInputsV1): SnapshotLabels {
  const latest = inputs?.latest;

  const labels: SnapshotLabels = {};

  // Observation labels (PR154)
  if (latest?.observation) {
    labels.impulse = latest.observation.impulse;
    labels.thinning = latest.observation.thinning;
    labels.dominance = latest.observation.dominance;
    labels.absorption = latest.observation.absorption;
  }

  // Higher-level labels
  if (latest?.shockPhase) labels.shockPhase = latest.shockPhase;
  if (latest?.stress) labels.stress = latest.stress;
  if (latest?.stressEscalated) labels.stressEscalated = latest.stressEscalated;
  if (latest?.actionShape) labels.actionShape = latest.actionShape;
  if (latest?.templateId) labels.templateId = latest.templateId;
  if (latest?.route) labels.route = latest.route;
  if (latest?.gateDecision) labels.gateDecision = latest.gateDecision;
  if (latest?.blockReason) labels.blockReason = latest.blockReason;
  if (latest?.policyDecision) labels.policyDecision = latest.policyDecision;
  if (latest?.policyReason) labels.policyReason = latest.policyReason;
  if (latest?.hardStop) labels.hardStop = latest.hardStop;
  if (latest?.cooldown) labels.cooldown = latest.cooldown;
  if (latest?.drift) labels.drift = latest.drift;
  if (latest?.resume) labels.resume = latest.resume;

  // Sanitize all labels
  for (const [key, value] of Object.entries(labels)) {
    if (typeof value === "string") {
      (labels as any)[key] = sanitizeSnapshotLabel(value);
    }
  }

  return labels;
}

/**
 * Determine snapshot status (AVAILABLE / PARTIAL / ERROR)
 *
 * Fixed rule:
 *   - AVAILABLE: hasShockPhase && hasStress && hasActionShape && hasTemplateId && hasGate && hasPolicy
 *   - PARTIAL: Snapshot built but missing some components
 *   - ERROR: Inputs invalid or construction failed
 *
 * @param presence - Presence flags
 * @returns Snapshot status
 */
function determineStatus(presence: SnapshotPresence): SnapshotStatus {
  const isAvailable =
    presence.hasShockPhase &&
    presence.hasStress &&
    presence.hasActionShape &&
    presence.hasTemplateId &&
    presence.hasGate &&
    presence.hasPolicy;

  if (isAvailable) {
    return "AVAILABLE";
  } else {
    return "PARTIAL";
  }
}

/**
 * Build market regime snapshot v1
 *
 * Purpose:
 *   Build a snapshot from current system state for strategy verification.
 *
 * @param inputs - Snapshot inputs (optional)
 * @returns Market regime snapshot (never throws)
 */
export async function buildMarketRegimeSnapshotV1(
  inputs?: SnapshotInputsV1
): Promise<MarketRegimeSnapshotV1> {
  const warnings: string[] = [];

  try {
    // Build presence flags
    const presence = buildPresence(inputs);

    // Build labels
    const labels = buildLabels(inputs);

    // Build numerics (save-only)
    const numerics: SnapshotNumerics | undefined = inputs?.latest?.numerics
      ? {
          notionalUsd: inputs.latest.numerics.notionalUsd,
          targetNotionalUsd: inputs.latest.numerics.targetNotionalUsd,
          oracleAgeMs: inputs.latest.numerics.oracleAgeMs,
        }
      : undefined;

    // Determine status
    const status = determineStatus(presence);

    // Generate snapshot ID (deterministic-ish)
    const ts = Date.now();
    const rand = Math.floor(Math.random() * 1000);
    const id = `snap_${ts}_${rand}`;

    // Build snapshot
    const snapshot: MarketRegimeSnapshotV1 = {
      version: "v1.0",
      kind: "REGIME_SNAPSHOT",
      status,
      ts,
      id,
      warnings,
      presence,
      labels,
      numerics,
      build: inputs?.build,
    };

    return snapshot;
  } catch (error) {
    // Defensive: Even on error, return a minimal snapshot
    warnings.push("WARN_SNAPSHOT_BUILD_ERROR");

    return {
      version: "v1.0",
      kind: "REGIME_SNAPSHOT",
      status: "ERROR",
      ts: Date.now(),
      id: `snap_error_${Date.now()}`,
      warnings,
      presence: {
        hasOracle: false,
        hasObservationLabels: false,
        hasShockPhase: false,
        hasStress: false,
        hasEscalation: false,
        hasActionShape: false,
        hasTemplateId: false,
        hasRoute: false,
        hasGate: false,
        hasPolicy: false,
        hasHardStop: false,
        hasCooldown: false,
        hasDrift: false,
        hasResume: false,
      },
      labels: {},
    };
  }
}

/**
 * Snapshot store configuration
 */
export interface SnapshotStoreConfig {
  path?: string; // Default: ~/.meridian/snapshots.log
  maxLines?: number; // Optional rotation (v1 optional)
}

/**
 * Resolve snapshot log path
 *
 * @returns Snapshot log file path
 */
export function resolveSnapshotLogPath(): string {
  return (
    process.env.MERIDIAN_SNAPSHOTS_PATH ||
    path.join(os.homedir(), ".meridian", "snapshots.log")
  );
}

/**
 * Append snapshot to log (JSONL format)
 *
 * Purpose:
 *   Append snapshot to JSONL file (one snapshot per line).
 *   Append-only, never modifies existing lines.
 *
 * @param snapshot - Snapshot to append
 * @param cfg - Configuration (optional)
 * @returns Result with status and warnings
 */
export async function appendSnapshotV1(
  snapshot: MarketRegimeSnapshotV1,
  cfg?: SnapshotStoreConfig
): Promise<{ status: "OK" | "ERROR"; warnings: string[] }> {
  const warnings: string[] = [];

  try {
    const logPath = cfg?.path || resolveSnapshotLogPath();

    // Ensure directory exists
    const dir = path.dirname(logPath);
    if (!fs.existsSync(dir)) {
      await fs.promises.mkdir(dir, { recursive: true });
    }

    // Serialize snapshot as JSONL (single line)
    const line = JSON.stringify(snapshot) + "\n";

    // Append to file
    await fs.promises.appendFile(logPath, line, "utf-8");

    return {
      status: "OK",
      warnings,
    };
  } catch (error) {
    warnings.push("WARN_SNAPSHOT_WRITE_FAILED");

    return {
      status: "ERROR",
      warnings,
    };
  }
}

/**
 * Read recent snapshots from log
 *
 * @param cfg - Configuration (optional)
 * @param opts - Read options (optional)
 * @returns Snapshots array and warnings
 */
export async function readRecentSnapshotsV1(
  cfg?: SnapshotStoreConfig,
  opts?: { maxLines?: number }
): Promise<{ snapshots: MarketRegimeSnapshotV1[]; warnings: string[] }> {
  const warnings: string[] = [];
  const snapshots: MarketRegimeSnapshotV1[] = [];
  const maxLines = opts?.maxLines || 200;

  try {
    const logPath = cfg?.path || resolveSnapshotLogPath();

    // Check if file exists
    if (!fs.existsSync(logPath)) {
      warnings.push("WARN_SNAPSHOT_LOG_NOT_FOUND");
      return { snapshots, warnings };
    }

    // Read file
    const content = await fs.promises.readFile(logPath, "utf-8");

    // Split into lines
    const lines = content.split("\n").filter((line) => line.trim() !== "");

    // Take last N lines
    const recentLines = lines.slice(-maxLines);

    // Parse each line
    for (const line of recentLines) {
      try {
        const parsed = JSON.parse(line);

        // Basic validation
        if (parsed.version === "v1.0" && parsed.ts && parsed.kind) {
          snapshots.push(parsed as MarketRegimeSnapshotV1);
        } else {
          warnings.push("WARN_SNAPSHOT_PARSE_INVALID_SCHEMA");
        }
      } catch (parseError) {
        warnings.push("WARN_SNAPSHOT_PARSE_FAILED_LINE");
        // Continue parsing other lines
      }
    }

    return { snapshots, warnings };
  } catch (error) {
    warnings.push("WARN_SNAPSHOT_READ_FAILED");

    return { snapshots, warnings };
  }
}

/**
 * Read filtered snapshots
 *
 * @param filter - Filter options
 * @param cfg - Configuration (optional)
 * @returns Filtered snapshots and warnings
 */
export async function readFilteredSnapshotsV1(
  filter: {
    status?: SnapshotStatus;
    kind?: SnapshotKind;
    maxLines?: number;
  },
  cfg?: SnapshotStoreConfig
): Promise<{ snapshots: MarketRegimeSnapshotV1[]; warnings: string[] }> {
  const result = await readRecentSnapshotsV1(cfg, {
    maxLines: filter.maxLines,
  });

  // Apply filters
  let filteredSnapshots = result.snapshots;

  if (filter.status) {
    filteredSnapshots = filteredSnapshots.filter(
      (s) => s.status === filter.status
    );
  }

  if (filter.kind) {
    filteredSnapshots = filteredSnapshots.filter((s) => s.kind === filter.kind);
  }

  return {
    snapshots: filteredSnapshots,
    warnings: result.warnings,
  };
}
