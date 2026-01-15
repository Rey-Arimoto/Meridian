#!/usr/bin/env node
/**
 * PR167: v1.4 Improvement Proposal Generator v1 - CLI
 *
 * Purpose:
 *   Generate fixed-rule improvement proposals from snapshot analysis.
 *   READ-ONLY suggestions based on deterministic triggers.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Proposals are suggestions, not actions
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numeric counts
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/propose.ts
 *   npx ts-node src/cli/propose.ts --tail 200
 *   npx ts-node src/cli/propose.ts --tail 500 --priority P0
 *   npx ts-node src/cli/propose.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/propose.ts --tail 500
 *   node dist/cli/propose.js
 */

import { readRecentSnapshotsV1 } from "../snapshot/exporter";
import { analyzeSnapshotsV1 } from "../analyze/analyzer";
import { generateProposalsV1 } from "../propose/proposer";
import {
  formatProposalLines,
  sanitizeProposeResultForDisplay,
  isDebugMode,
} from "../propose/guards";
import { ProposalPriority } from "../propose/types";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  priority?: ProposalPriority;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: { tail?: number; priority?: ProposalPriority; json?: boolean } =
    {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--tail" && i + 1 < args.length) {
      result.tail = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === "--priority" && i + 1 < args.length) {
      const priority = args[i + 1] as ProposalPriority;
      if (["P0", "P1", "P2", "UNKNOWN"].includes(priority)) {
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
 * Main proposal CLI function
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

    if (analysis.status === "ERROR") {
      console.log("ANALYSIS_ERROR");
      return;
    }

    // Generate proposals
    const proposeResult = await generateProposalsV1(analysis);

    // Filter by priority if specified
    if (args.priority) {
      proposeResult.proposals = proposeResult.proposals.filter(
        (p) => p.priority === args.priority
      );
    }

    // Display based on mode
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify(proposeResult, null, 2));
      } else {
        const sanitized = sanitizeProposeResultForDisplay(
          proposeResult,
          false
        );
        console.log(JSON.stringify(sanitized, null, 2));
      }
    } else {
      // Normal mode: formatted lines (label-only)
      const lines = formatProposalLines(proposeResult, debugMode);

      for (const line of lines) {
        console.log(line);
      }
    }
  } catch (error) {
    console.error("ERROR: Propose CLI failed");
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
