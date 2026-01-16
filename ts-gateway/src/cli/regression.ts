#!/usr/bin/env node
/**
 * PR175: v1.4 Regression Guard v1 - CLI
 *
 * Purpose:
 *   Monitor patch effectiveness persistence.
 *   Detect when improvements regress (don't persist).
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only (no automatic revert)
 *   - Label-only: Normal mode uses labels (no counts)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numerics
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/regression.ts
 *   npx ts-node src/cli/regression.ts --tail 50
 *   npx ts-node src/cli/regression.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
 *   npx ts-node src/cli/regression.ts --decision REGRESSION_DETECTED
 *   npx ts-node src/cli/regression.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/regression.ts
 *   node dist/cli/regression.js
 */

import {
  readRecentEffectsV1,
  readRecentDecisionsV1,
  groupEffectsByProposal,
} from "../regress/reader";
import { detectRegressionV1 } from "../regress/detector";
import {
  appendRegressionReportV1,
  readRecentRegressionReportsV1,
} from "../regress/store";
import {
  formatRegressionLinesV1,
  sanitizeRegressionForDisplayV1,
  isDebugMode,
} from "../regress/guards";
import { RegressionReportV1 } from "../regress/types";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  proposalId?: string;
  decision?: string;
  json?: boolean;
  analyze?: boolean;
} {
  const args = process.argv.slice(2);
  const result: {
    tail?: number;
    proposalId?: string;
    decision?: string;
    json?: boolean;
    analyze?: boolean;
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
    } else if (arg === "--analyze") {
      result.analyze = true;
    }
  }

  return result;
}

/**
 * Main regression CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Mode 1: Analyze mode - read effects and detect regressions
    if (args.analyze) {
      console.log("=== Regression Analysis Mode ===\n");

      // Read effects
      const { status: effectStatus, reports: effects, warnings: effectWarnings } =
        readRecentEffectsV1({
          tail: args.tail || 100,
          proposalId: args.proposalId,
        });

      if (effectStatus === "ERROR") {
        console.log("ERROR_READING_EFFECTS");
        return;
      }

      if (effects.length === 0) {
        console.log("NO_EFFECTS_FOUND");
        return;
      }

      if (debugMode && effectWarnings.length > 0) {
        console.log(`Effect warnings: ${effectWarnings.join(", ")}\n`);
      }

      // Group effects by proposal
      const grouped = groupEffectsByProposal(effects);

      console.log(`Analyzing ${grouped.size} proposal(s)...\n`);

      // Analyze each proposal
      for (const [proposalId, proposalEffects] of grouped.entries()) {
        const analysis = detectRegressionV1(proposalId, proposalEffects);

        // Build report
        const report: RegressionReportV1 = {
          kind: "REGRESSION_REPORT_V1",
          status: "AVAILABLE",
          analysis,
          ts: Date.now(),
          warnings: analysis.warnings,
        };

        // Save to store
        const { status: saveStatus, warnings: saveWarnings } =
          appendRegressionReportV1(report);

        if (saveStatus === "ERROR" && debugMode) {
          console.log(`Save warnings: ${saveWarnings.join(", ")}\n`);
        }

        // Display
        if (args.json) {
          if (debugMode) {
            console.log(JSON.stringify(report, null, 2));
          } else {
            const sanitized = sanitizeRegressionForDisplayV1(report, false);
            console.log(JSON.stringify(sanitized, null, 2));
          }
        } else {
          const lines = formatRegressionLinesV1(report, debugMode);
          for (const line of lines) {
            console.log(line);
          }
        }

        console.log(""); // Separator between proposals
      }

      return;
    }

    // Mode 2: View mode - read stored regression reports
    console.log("=== Regression Reports ===\n");

    const { reports, warnings } = readRecentRegressionReportsV1({
      tail: args.tail || 10,
      proposalId: args.proposalId,
      decision: args.decision,
    });

    if (debugMode && warnings.length > 0) {
      console.log(`Warnings: ${warnings.join(", ")}\n`);
    }

    if (reports.length === 0) {
      console.log("NO_REGRESSION_REPORTS_FOUND");
      console.log("\nTip: Use --analyze to analyze effects and detect regressions");
      return;
    }

    console.log(`Found ${reports.length} report(s)\n`);

    // Display reports
    for (const report of reports) {
      if (args.json) {
        if (debugMode) {
          console.log(JSON.stringify(report, null, 2));
        } else {
          const sanitized = sanitizeRegressionForDisplayV1(report, false);
          console.log(JSON.stringify(sanitized, null, 2));
        }
      } else {
        const lines = formatRegressionLinesV1(report, debugMode);
        for (const line of lines) {
          console.log(line);
        }
      }

      console.log(""); // Separator
    }
  } catch (error) {
    console.error("ERROR: Regression CLI failed");
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
