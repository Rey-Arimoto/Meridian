/**
 * PR180: v1.4 Spec Change Digest v1 - Store
 *
 * Purpose:
 *   Append-only JSONL logs for digests.
 *
 * Constitutional Constraints:
 *   - Append-only: No mutations
 *   - Defensive: Corrupted lines are skipped, never throws
 *   - Label-only: Warnings must be sanitized (SpecChangeDigestV1 is already label-only)
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { SpecChangeDigestV1 } from "./types";

/**
 * Default storage path
 */
const DEFAULT_DIGEST_LOG = path.join(os.homedir(), ".meridian", "digests.log");

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
 * Append digest
 *
 * @param report - Digest report
 * @param pathOverride - Optional path override
 * @returns Result with status and warnings
 */
export async function appendDigestV1(
  report: SpecChangeDigestV1,
  pathOverride?: string
): Promise<{ ok: boolean; warnings: string[] }> {
  try {
    const logPath = pathOverride || DEFAULT_DIGEST_LOG;
    ensureDir(logPath);

    const line = JSON.stringify(report) + "\n";
    fs.appendFileSync(logPath, line, "utf8");

    return { ok: true, warnings: [] };
  } catch (error) {
    return { ok: false, warnings: ["WARN_DIGEST_APPEND_FAILED"] };
  }
}

/**
 * Read recent digests
 *
 * @param opts - Filter options
 * @param pathOverride - Optional path override
 * @returns Digests and warnings
 */
export async function readRecentDigestsV1(
  opts?: {
    tail?: number;
    proposalId?: string;
    status?: string;
  },
  pathOverride?: string
): Promise<{ items: SpecChangeDigestV1[]; warnings: string[] }> {
  const warnings: string[] = [];
  const items: SpecChangeDigestV1[] = [];

  try {
    const logPath = pathOverride || DEFAULT_DIGEST_LOG;

    if (!fs.existsSync(logPath)) {
      return { items: [], warnings: [] };
    }

    const content = fs.readFileSync(logPath, "utf8");
    const lines = content.trim().split("\n").filter((l) => l.length > 0);

    const tail = opts?.tail || 100;

    // Start from the end
    const startIdx = Math.max(0, lines.length - tail);

    for (let i = startIdx; i < lines.length; i++) {
      try {
        const parsed = JSON.parse(lines[i]) as SpecChangeDigestV1;

        // Apply filters
        if (opts?.status && parsed.status !== opts.status) {
          continue;
        }

        // Note: proposalId filter would require adding proposalId to SpecChangeDigestV1
        // For now, we skip this filter

        items.push(parsed);
      } catch {
        // Skip corrupted lines
        warnings.push("WARN_CORRUPT_LINE_SKIPPED");
        continue;
      }
    }

    return { items, warnings };
  } catch (error) {
    warnings.push("ERROR_DIGEST_READ_FAILED");
    return { items: [], warnings };
  }
}

/**
 * Get digest log path
 *
 * @returns Default digest log path
 */
export function getDigestLogPath(): string {
  return DEFAULT_DIGEST_LOG;
}
