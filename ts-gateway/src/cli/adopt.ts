#!/usr/bin/env node
/**
 * PR168: v1.4 Policy-First Adoption Loop - CLI
 *
 * Purpose:
 *   Policy-first adoption loop CLI that analyzes snapshots, generates proposals,
 *   builds patch plans, simulates replay compare, and decides ADOPT/HOLD/REJECT.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No automatic application (proposals and comparison only)
 *   - Policy-First: Changes that reduce safety are PATCH_NOT_ALLOWED
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numeric counts
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/adopt.ts
 *   npx ts-node src/cli/adopt.ts --tail 500
 *   npx ts-node src/cli/adopt.ts --tail 500 --priority P0
 *   npx ts-node src/cli/adopt.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/adopt.ts --tail 500
 *   node dist/cli/adopt.js
 */

import { readRecentSnapshotsV1 } from "../snapshot/exporter";
import { adoptImprovementV1 } from "../adopt/adopter";
import {
  formatAdoptResultLabelOnlyLines,
  sanitizeAdoptResultForDisplay,
  isDebugMode,
} from "../adopt/guards";
import { AdoptPriority } from "../adopt/types";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  priority?: AdoptPriority;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: { tail?: number; priority?: AdoptPriority; json?: boolean } =
    {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--priority" && i + 1 < args.length) {
      const priority = args[i + 1] as AdoptPriority;
      if (["P0", "P1", "P2"].includes(priority)) {
        result.priority = priority;
      }
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
 * Main adoption CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();
    const tailN = args.tail || 200;

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Read snapshots
    const snapshotResult = await readRecentSnapshotsV1(
      {},
      { maxLines: tailN }
    );

    if (snapshotResult.warnings.length > 0) {
      console.log(`WARNINGS: ${snapshotResult.warnings.join(", ")}\n`);
    }

    if (snapshotResult.snapshots.length === 0) {
      console.log("NO_SNAPSHOTS_FOUND");
      return;
    }

    // Adopt improvement
    const adoptResult = await adoptImprovementV1(
      snapshotResult.snapshots,
      args.priority,
      tailN
    );

    // Display based on mode
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify(adoptResult, null, 2));
      } else {
        const sanitized = sanitizeAdoptResultForDisplay(adoptResult, false);
        console.log(JSON.stringify(sanitized, null, 2));
      }
    } else {
      // Normal mode: formatted lines (label-only)
      const lines = formatAdoptResultLabelOnlyLines(adoptResult, debugMode);

      for (const line of lines) {
        console.log(line);
      }
    }
  } catch (error) {
    console.error("ERROR: Adopt CLI failed");
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
