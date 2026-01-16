#!/usr/bin/env node
/**
 * PR174: v1.4 Patch Effectiveness Tracker v1 - CLI
 *
 * Purpose:
 *   Track patch effectiveness by comparing Before/After snapshots.
 *   READ-ONLY tool for measuring "did the adoption actually improve things".
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only (no automatic adoption/execution)
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numerics
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/effect.ts
 *   npx ts-node src/cli/effect.ts --tail 2000
 *   npx ts-node src/cli/effect.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
 *   npx ts-node src/cli/effect.ts --decision ADOPT
 *   npx ts-node src/cli/effect.ts --json
 *   npx ts-node src/cli/effect.ts --no-save
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/effect.ts
 *   node dist/cli/effect.js
 */

import { readRecentSnapshotsV1 } from "../snapshot/exporter";
import { readRecentDecisionAcksV1 } from "../decision/store";
import { selectEffectWindowsV1 } from "../effect/selector";
import { summarizeWindowV1 } from "../effect/metrics";
import { evaluateEffectV1 } from "../effect/evaluator";
import { appendEffectReportV1 } from "../effect/store";
import {
  formatEffectLabelOnlyLinesV1,
  sanitizeEffectForDisplayV1,
  isDebugMode,
} from "../effect/guards";
import { PatchEffectReportV1 } from "../effect/types";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  proposalId?: string;
  decision?: string;
  json?: boolean;
  noSave?: boolean;
} {
  const args = process.argv.slice(2);
  const result: {
    tail?: number;
    proposalId?: string;
    decision?: string;
    json?: boolean;
    noSave?: boolean;
  } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--proposal" && i + 1 < args.length) {
      result.proposalId = args[i + 1];
      i++;
    } else if (arg === "--decision" && i + 1 < args.length) {
      result.decision = args[i + 1];
      i++;
    } else if (arg === "--json") {
      result.json = true;
    } else if (arg === "--no-save") {
      result.noSave = true;
    }
  }

  return result;
}

/**
 * Main effect CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();
    const snapshotTail = args.tail || 2000;

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // 1. Read decision acks
    const {
      status: ackStatus,
      records: acks,
      warnings: ackWarnings,
    } = readRecentDecisionAcksV1({
      tail: 1, // Get most recent ack
      proposalId: args.proposalId,
      decision: args.decision,
    });

    if (ackStatus === "ERROR") {
      console.log("ERROR_READING_DECISIONS");
      return;
    }

    if (acks.length === 0) {
      console.log("NO_DECISIONS_FOUND");
      return;
    }

    const ack = acks[0];

    if (debugMode && ackWarnings.length > 0) {
      console.log(`ACK_WARNINGS: ${ackWarnings.join(", ")}\n`);
    }

    // 2. Read snapshots
    const snapshotResult = await readRecentSnapshotsV1({}, { maxLines: snapshotTail });

    if (snapshotResult.warnings.length > 0 && debugMode) {
      console.log(`SNAPSHOT_WARNINGS: ${snapshotResult.warnings.join(", ")}\n`);
    }

    if (snapshotResult.snapshots.length === 0) {
      console.log("NO_SNAPSHOTS_FOUND");
      return;
    }

    // 3. Select windows
    const { before, afterShort, afterMedium, afterLong, warnings: selectWarnings } =
      selectEffectWindowsV1(snapshotResult.snapshots, ack);

    if (debugMode && selectWarnings.length > 0) {
      console.log(`SELECT_WARNINGS: ${selectWarnings.join(", ")}\n`);
    }

    // 4. Summarize windows
    const beforeSummary = summarizeWindowV1("WIN_BEFORE", before);
    const afterShortSummary = summarizeWindowV1("WIN_AFTER_SHORT", afterShort);
    const afterMediumSummary = summarizeWindowV1("WIN_AFTER_MEDIUM", afterMedium);
    const afterLongSummary = summarizeWindowV1("WIN_AFTER_LONG", afterLong);

    // 5. Evaluate effect
    const { decision, compare, rationale, warnings: evalWarnings } = evaluateEffectV1(
      beforeSummary,
      afterShortSummary,
      afterMediumSummary,
      afterLongSummary
    );

    // 6. Build effect report
    const report: PatchEffectReportV1 = {
      kind: "PATCH_EFFECT_V1",
      status: afterShort.length > 0 ? "AVAILABLE" : "PARTIAL",
      decisionAckRef: {
        proposalId: ack.refs.proposalId,
        decision: ack.rationale.decision,
        reviewerKind: ack.reviewer,
        timeLabel: ack.timeLabel,
      },
      windows: [beforeSummary, afterShortSummary, afterMediumSummary, afterLongSummary],
      compare,
      effectDecision: decision,
      rationale,
      warnings: [
        ...selectWarnings,
        ...beforeSummary.warnings,
        ...afterShortSummary.warnings,
        ...evalWarnings,
      ],
      ts: Date.now(),
    };

    // 7. Save to store (unless --no-save)
    if (!args.noSave) {
      const { status: saveStatus, warnings: saveWarnings } =
        appendEffectReportV1(report);

      if (saveStatus === "ERROR" && debugMode) {
        console.log(`SAVE_WARNINGS: ${saveWarnings.join(", ")}\n`);
      }
    }

    // 8. Display
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify(report, null, 2));
      } else {
        const sanitized = sanitizeEffectForDisplayV1(report, false);
        console.log(JSON.stringify(sanitized, null, 2));
      }
    } else {
      // Normal mode: formatted lines (label-only)
      const lines = formatEffectLabelOnlyLinesV1(report, debugMode);

      for (const line of lines) {
        console.log(line);
      }
    }
  } catch (error) {
    console.error("ERROR: Effect CLI failed");
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
