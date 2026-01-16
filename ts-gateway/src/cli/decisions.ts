#!/usr/bin/env node
/**
 * PR173: v1.4 Decision Acknowledgement + Reviewer Trace v1 - CLI
 *
 * Purpose:
 *   View decision acknowledgement audit trail.
 *   READ-ONLY tool for viewing adoption decisions.
 *
 * Constitutional Constraints:
 *   - READ-ONLY: View only (no modification)
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows additional details
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/decisions.ts
 *   npx ts-node src/cli/decisions.ts --tail 50
 *   npx ts-node src/cli/decisions.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
 *   npx ts-node src/cli/decisions.ts --decision ADOPT
 *   npx ts-node src/cli/decisions.ts --reviewer HUMAN_PRIMARY
 *   npx ts-node src/cli/decisions.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/decisions.ts
 *   node dist/cli/decisions.js
 */

import { readRecentDecisionAcksV1 } from "../decision/store";
import {
  formatAckLines,
  sanitizeAckForDisplay,
  isDebugMode,
} from "../decision/guards";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  proposalId?: string;
  decision?: string;
  reviewer?: string;
  json?: boolean;
} {
  const args = process.argv.slice(2);
  const result: {
    tail?: number;
    proposalId?: string;
    decision?: string;
    reviewer?: string;
    json?: boolean;
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
    } else if (arg === "--reviewer" && i + 1 < args.length) {
      result.reviewer = args[i + 1];
      i++;
    } else if (arg === "--json") {
      result.json = true;
    }
  }

  return result;
}

/**
 * Main decisions CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Read decision acks with filters
    const { status, records, warnings } = readRecentDecisionAcksV1({
      tail: args.tail || 20,
      proposalId: args.proposalId,
      decision: args.decision,
      reviewer: args.reviewer,
    });

    if (warnings.length > 0 && debugMode) {
      console.log(`DECISION_WARNINGS: ${warnings.join(", ")}\n`);
    }

    if (records.length === 0) {
      console.log("NO_DECISIONS_FOUND");
      return;
    }

    // Display based on mode
    if (args.json) {
      // JSON mode (sanitized, or raw in debug mode)
      if (debugMode) {
        console.log(JSON.stringify(records, null, 2));
      } else {
        const sanitized = records.map((rec) =>
          sanitizeAckForDisplay(rec, false)
        );
        console.log(JSON.stringify(sanitized, null, 2));
      }
    } else {
      // Normal mode: formatted lines (label-only)
      for (const rec of records) {
        const lines = formatAckLines(rec, debugMode);
        for (const line of lines) {
          console.log(line);
        }
      }
    }
  } catch (error) {
    console.error("ERROR: Decisions CLI failed");
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
