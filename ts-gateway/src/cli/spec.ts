#!/usr/bin/env node
/**
 * PR179: v1.4 Spec Version Lock + Human ACK Gate v1 - CLI
 *
 * Purpose:
 *   Human-initiated spec ACK and lock status visualization.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Displays lock status, writes ACKs (no execution changes)
 *   - Label-only: No numeric literals, addresses, or trading vocab in normal mode
 *   - Defensive: Never throws
 *
 * Usage:
 *   npx ts-node src/cli/spec.ts status
 *   npx ts-node src/cli/spec.ts ack --reviewer HUMAN_PRIMARY --reason READ_AND_ACCEPT
 *   npx ts-node src/cli/spec.ts log --tail 20
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/spec.ts status
 */

import { evaluateSpecLockV1 } from "../spec/lock";
import {
  readRecentSpecRecordsV1,
  readRecentSpecAcksV1,
  readLatestSpecRecordV1,
  appendSpecAckRecordV1,
} from "../spec/store";
import { sanitizeLabel } from "../spec/guards";
import { ReviewerKind, SpecAckRecordV1 } from "../spec/types";

/**
 * Check if debug mode is enabled
 *
 * @returns True if MERIDIAN_DEBUG=true
 */
function isDebugMode(): boolean {
  return process.env.MERIDIAN_DEBUG === "true";
}

/**
 * Format time label
 *
 * @param timestamp - Epoch ms
 * @returns Time label
 */
function formatTimeLabel(timestamp: number): string {
  const debugMode = isDebugMode();

  if (debugMode) {
    return new Date(timestamp).toISOString();
  }

  const now = Date.now();
  const diff = now - timestamp;

  if (diff < 60 * 1000) {
    return "T_RECENT";
  } else if (diff < 60 * 60 * 1000) {
    return "T_LAST_HOUR";
  } else if (diff < 24 * 60 * 60 * 1000) {
    return "T_TODAY";
  } else {
    return "T_PAST";
  }
}

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  command: string;
  tail?: number;
  reviewer?: ReviewerKind;
  reason?: string;
} {
  const args = process.argv.slice(2);
  const result: {
    command: string;
    tail?: number;
    reviewer?: ReviewerKind;
    reason?: string;
  } = {
    command: args[0] || "status",
  };

  for (let i = 1; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--reviewer" && i + 1 < args.length) {
      const reviewer = args[i + 1].toUpperCase();
      if (
        ["HUMAN_PRIMARY", "HUMAN_SECONDARY", "AUTO_ASSISTED", "UNKNOWN"].includes(
          reviewer
        )
      ) {
        result.reviewer = reviewer as ReviewerKind;
      }
      i++;
    } else if (arg === "--reason" && i + 1 < args.length) {
      result.reason = args[i + 1];
      i++;
    }
  }

  return result;
}

/**
 * Status command
 */
async function statusCommand(): Promise<void> {
  console.log("=== Spec Lock Status ===\n");

  const result = await evaluateSpecLockV1();

  console.log(`STATUS: ${result.status}`);

  if (result.activeSpec) {
    console.log(`ACTIVE_SPEC: ${result.activeSpec}`);
  } else {
    console.log(`ACTIVE_SPEC: NONE`);
  }

  if (result.latestSpec) {
    console.log(`LATEST_SPEC: ${result.latestSpec}`);
  }

  if (result.ttlLabel) {
    console.log(`TTL: ${result.ttlLabel}`);
  }

  if (result.warnings.length > 0) {
    console.log(`\nWarnings: ${result.warnings.join(", ")}`);
  }

  console.log("");
}

/**
 * ACK command
 */
async function ackCommand(reviewer?: ReviewerKind, reason?: string): Promise<void> {
  console.log("=== ACK Latest Spec ===\n");

  // Read latest spec
  const latestSpec = await readLatestSpecRecordV1();

  if (!latestSpec) {
    console.log("ERROR: No spec records found");
    process.exit(1);
  }

  console.log(`Spec Version: ${latestSpec.specVersion}`);
  console.log(`Created: ${formatTimeLabel(latestSpec.createdAt)}`);
  console.log(`Source: ${latestSpec.source}`);

  // Create ACK record
  const ackRecord: SpecAckRecordV1 = {
    kind: "SPEC_ACK_V1",
    specVersion: latestSpec.specVersion,
    ackAt: Date.now(),
    reviewer: reviewer || "HUMAN_PRIMARY",
    reason: sanitizeLabel(reason || "READ_AND_ACCEPT"),
    warnings: [],
  };

  // Append ACK
  const appendResult = await appendSpecAckRecordV1(ackRecord);

  if (appendResult.status === "OK") {
    console.log("\nACK_STATUS: OK");
    console.log(`Reviewer: ${ackRecord.reviewer}`);
    console.log(`Reason: ${ackRecord.reason}`);
  } else {
    console.log("\nACK_STATUS: ERROR");
    console.log(`Warnings: ${appendResult.warnings.join(", ")}`);
    process.exit(1);
  }

  console.log("");
}

/**
 * Log command
 */
async function logCommand(tail: number = 20): Promise<void> {
  console.log("=== Spec and ACK Logs ===\n");

  const specs = await readRecentSpecRecordsV1({ tail });
  const acks = await readRecentSpecAcksV1({ tail });

  console.log(`Recent Specs (${specs.length}):`);
  for (const spec of specs) {
    console.log(
      `  ${spec.specVersion} | ${formatTimeLabel(spec.createdAt)} | ${spec.source}`
    );
  }

  console.log(`\nRecent ACKs (${acks.length}):`);
  for (const ack of acks) {
    console.log(
      `  ${ack.specVersion} | ${formatTimeLabel(ack.ackAt)} | ${ack.reviewer} | ${ack.reason}`
    );
  }

  console.log("");
}

/**
 * Main CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    switch (args.command) {
      case "status":
        await statusCommand();
        break;

      case "ack":
        await ackCommand(args.reviewer, args.reason);
        break;

      case "log":
        await logCommand(args.tail);
        break;

      default:
        console.log("Usage:");
        console.log("  npx ts-node src/cli/spec.ts status");
        console.log(
          "  npx ts-node src/cli/spec.ts ack --reviewer HUMAN_PRIMARY --reason READ_AND_ACCEPT"
        );
        console.log("  npx ts-node src/cli/spec.ts log --tail 20");
        process.exit(1);
    }
  } catch (error) {
    console.error("ERROR: Spec CLI failed");
    console.error(error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error("FATAL:", error);
    process.exit(1);
  });
}

export { main };
