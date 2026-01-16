/**
 * PR179: v1.4 Spec Version Lock + Human ACK Gate v1 - Store
 *
 * Purpose:
 *   Append-only JSONL logs for spec records and ACKs.
 *
 * Constitutional Constraints:
 *   - Append-only: No mutations
 *   - Defensive: Corrupted lines are skipped, never throws
 *   - Label-only: Warnings must be sanitized
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { SpecRecordV1, SpecAckRecordV1 } from "./types";
import { sanitizeWarnings } from "./guards";

/**
 * Default storage paths
 */
const DEFAULT_SPEC_LOG = path.join(os.homedir(), ".meridian", "specs.log");
const DEFAULT_ACK_LOG = path.join(os.homedir(), ".meridian", "spec_acks.log");

/**
 * Ensure directory exists
 *
 * @param filePath - File path
 */
function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * Append spec record
 *
 * @param rec - Spec record
 * @param pathOverride - Optional path override
 * @returns Result with status and warnings
 */
export async function appendSpecRecordV1(
  rec: SpecRecordV1,
  pathOverride?: string
): Promise<{ status: "OK" | "ERROR"; warnings: string[] }> {
  try {
    const logPath = pathOverride || DEFAULT_SPEC_LOG;
    ensureDir(logPath);

    // Sanitize warnings
    const sanitized = {
      ...rec,
      warnings: sanitizeWarnings(rec.warnings),
    };

    const line = JSON.stringify(sanitized) + "\n";
    fs.appendFileSync(logPath, line, "utf8");

    return { status: "OK", warnings: [] };
  } catch (error) {
    return { status: "ERROR", warnings: ["WARN_SPEC_APPEND_FAILED"] };
  }
}

/**
 * Append spec ACK record
 *
 * @param rec - ACK record
 * @param pathOverride - Optional path override
 * @returns Result with status and warnings
 */
export async function appendSpecAckRecordV1(
  rec: SpecAckRecordV1,
  pathOverride?: string
): Promise<{ status: "OK" | "ERROR"; warnings: string[] }> {
  try {
    const logPath = pathOverride || DEFAULT_ACK_LOG;
    ensureDir(logPath);

    // Sanitize warnings
    const sanitized = {
      ...rec,
      warnings: sanitizeWarnings(rec.warnings),
    };

    const line = JSON.stringify(sanitized) + "\n";
    fs.appendFileSync(logPath, line, "utf8");

    return { status: "OK", warnings: [] };
  } catch (error) {
    return { status: "ERROR", warnings: ["WARN_ACK_APPEND_FAILED"] };
  }
}

/**
 * Read recent spec records
 *
 * @param opts - Options with tail limit
 * @param pathOverride - Optional path override
 * @returns Spec records
 */
export async function readRecentSpecRecordsV1(
  opts: { tail: number },
  pathOverride?: string
): Promise<SpecRecordV1[]> {
  try {
    const logPath = pathOverride || DEFAULT_SPEC_LOG;

    if (!fs.existsSync(logPath)) {
      return [];
    }

    const content = fs.readFileSync(logPath, "utf8");
    const lines = content.trim().split("\n").filter((l) => l.length > 0);

    const records: SpecRecordV1[] = [];

    // Start from the end
    const startIdx = Math.max(0, lines.length - opts.tail);

    for (let i = startIdx; i < lines.length; i++) {
      try {
        const parsed = JSON.parse(lines[i]);
        if (parsed.kind === "SPEC_RECORD_V1") {
          records.push(parsed);
        }
      } catch {
        // Skip corrupted lines
        continue;
      }
    }

    return records;
  } catch {
    return [];
  }
}

/**
 * Read recent ACK records
 *
 * @param opts - Options with tail limit
 * @param pathOverride - Optional path override
 * @returns ACK records
 */
export async function readRecentSpecAcksV1(
  opts: { tail: number },
  pathOverride?: string
): Promise<SpecAckRecordV1[]> {
  try {
    const logPath = pathOverride || DEFAULT_ACK_LOG;

    if (!fs.existsSync(logPath)) {
      return [];
    }

    const content = fs.readFileSync(logPath, "utf8");
    const lines = content.trim().split("\n").filter((l) => l.length > 0);

    const records: SpecAckRecordV1[] = [];

    // Start from the end
    const startIdx = Math.max(0, lines.length - opts.tail);

    for (let i = startIdx; i < lines.length; i++) {
      try {
        const parsed = JSON.parse(lines[i]);
        if (parsed.kind === "SPEC_ACK_V1") {
          records.push(parsed);
        }
      } catch {
        // Skip corrupted lines
        continue;
      }
    }

    return records;
  } catch {
    return [];
  }
}

/**
 * Read latest spec record
 *
 * @param pathOverride - Optional path override
 * @returns Latest spec record or undefined
 */
export async function readLatestSpecRecordV1(
  pathOverride?: string
): Promise<SpecRecordV1 | undefined> {
  const records = await readRecentSpecRecordsV1({ tail: 100 }, pathOverride);
  return records.length > 0 ? records[records.length - 1] : undefined;
}

/**
 * Read latest ACK for a specific spec version
 *
 * @param specVersion - Spec version
 * @param pathOverride - Optional path override
 * @returns Latest ACK record or undefined
 */
export async function readLatestAckForSpecV1(
  specVersion: string,
  pathOverride?: string
): Promise<SpecAckRecordV1 | undefined> {
  const acks = await readRecentSpecAcksV1({ tail: 100 }, pathOverride);

  // Find latest ACK for this spec
  for (let i = acks.length - 1; i >= 0; i--) {
    if (acks[i].specVersion === specVersion) {
      return acks[i];
    }
  }

  return undefined;
}

/**
 * Read latest ACKed spec version
 *
 * @param pathOverride - Optional path override
 * @returns Latest ACKed spec version or undefined
 */
export async function readLatestAckedSpecV1(
  pathOverride?: string
): Promise<string | undefined> {
  const acks = await readRecentSpecAcksV1({ tail: 100 }, pathOverride);

  if (acks.length === 0) {
    return undefined;
  }

  // Return the spec version from the most recent ACK
  return acks[acks.length - 1].specVersion;
}
