#!/usr/bin/env node
/**
 * PR166: v1.4 Snapshot Analysis Helper v1 - CLI
 *
 * Purpose:
 *   Analyze snapshot logs for strategy improvement through deterministic
 *   frequency, confusion, and timing analysis.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Analysis reads logs only, no execution
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numeric counts
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/analyze.ts
 *   npx ts-node src/cli/analyze.ts --tail 200
 *   npx ts-node src/cli/analyze.ts --tail 500 --focus confusion
 *   npx ts-node src/cli/analyze.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/analyze.ts --tail 500
 *   node dist/cli/analyze.js
 */

import { readRecentSnapshotsV1 } from "../snapshot/exporter";
import { analyzeSnapshotsV1 } from "../analyze/analyzer";
import {
  sanitizeAnalysisForDisplay,
  formatAnalysisLabelOnlyLines,
  isDebugMode,
} from "../analyze/guards";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  focus?: string;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: { tail?: number; focus?: string; json?: boolean } = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--focus" && i + 1 < args.length) {
      result.focus = args[i + 1];
      i++;
    } else if (arg === "--json") {
      result.json = true;
    }
  }

  // Override from env
  if (process.env.MERIDIAN_SNAPSHOTS_MAXLINES) {
    result.tail = parseInt(process.env.MERIDIAN_SNAPSHOTS_MAXLINES, 10);
  }

  return result;
}

/**
 * Main analysis CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Read snapshots
    const snapshotResult = await readRecentSnapshotsV1(
      {},
      { maxLines: args.tail || 200 }
    );

    if (snapshotResult.warnings.length > 0) {
      console.log(`WARNINGS: ${snapshotResult.warnings.join(", ")}\n`);
    }

    if (snapshotResult.snapshots.length === 0) {
      console.log("NO_SNAPSHOTS_FOUND");
      return;
    }

    // Analyze snapshots
    const analysis = await analyzeSnapshotsV1(snapshotResult.snapshots);

    // Display based on mode
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify(analysis, null, 2));
      } else {
        const sanitized = sanitizeAnalysisForDisplay(analysis, false);
        console.log(JSON.stringify(sanitized, null, 2));
      }
    } else if (args.focus === "confusion") {
      // Focus mode: confusion signals only
      console.log("=== Confusion Signals Focus ===\n");

      const activeSignals = analysis.confusionSignals.filter((s) => s.active);

      if (activeSignals.length === 0) {
        console.log("NO_CONFUSION");
      } else {
        for (const signal of activeSignals) {
          console.log(`${signal.type}: ACTIVE`);
          if (signal.reasons.length > 0) {
            console.log(`  Reasons: ${signal.reasons.join(", ")}`);
          }
          if (signal.details) {
            console.log(`  Details: ${JSON.stringify(signal.details)}`);
          }
          console.log("");
        }
      }

      console.log("=== End Focus ===");
    } else {
      // Normal mode: full analysis (label-only)
      const sanitized = sanitizeAnalysisForDisplay(analysis, debugMode);
      const lines = formatAnalysisLabelOnlyLines(
        sanitized,
        debugMode,
        analysis
      );

      for (const line of lines) {
        console.log(line);
      }
    }
  } catch (error) {
    console.error("ERROR: Analysis CLI failed");
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
