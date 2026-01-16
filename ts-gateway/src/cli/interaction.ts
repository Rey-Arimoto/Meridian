#!/usr/bin/env node
/**
 * PR176: v1.4 Change Interaction Detector v1 - CLI
 *
 * Purpose:
 *   Detect patch coupling/interaction risks.
 *   "Individual patches are good, but combination breaks things."
 *
 * Constitutional Constraints:
 *   - READ-ONLY: Observation only (no automatic adoption/revert)
 *   - Label-only: Normal mode uses labels (no counts/scores)
 *   - Debug mode: MERIDIAN_DEBUG=true allows numerics
 *   - Defensive: Never throws, handles errors gracefully
 *
 * Usage:
 *   npx ts-node src/cli/interaction.ts
 *   npx ts-node src/cli/interaction.ts --analyze
 *   npx ts-node src/cli/interaction.ts --tail 50
 *   npx ts-node src/cli/interaction.ts --proposal P0_REDUCE_ORACLE_STALE_BLOCKS_DEGRADE
 *   npx ts-node src/cli/interaction.ts --json
 *   MERIDIAN_DEBUG=true npx ts-node src/cli/interaction.ts --analyze
 *   node dist/cli/interaction.js
 */

import {
  readRecentDecisionsForInteraction,
  readRecentEffectsForInteraction,
  readRecentRegressionsForInteraction,
  extractAdoptionEvents,
} from "../interaction/reader";
import { detectInteractionsV1 } from "../interaction/detector";
import {
  appendInteractionReportV1,
  readRecentInteractionReportsV1,
} from "../interaction/store";
import {
  formatInteractionLinesV1,
  sanitizeInteractionForDisplayV1,
  isDebugMode,
} from "../interaction/guards";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  proposalId?: string;
  json?: boolean;
  analyze?: boolean;
} {
  const args = process.argv.slice(2);
  const result: {
    tail?: number;
    proposalId?: string;
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
    } else if (arg === "--json") {
      result.json = true;
    } else if (arg === "--analyze") {
      result.analyze = true;
    }
  }

  return result;
}

/**
 * Main interaction CLI function
 */
async function main(): Promise<void> {
  try {
    const args = parseArgs();
    const debugMode = isDebugMode();

    if (debugMode) {
      console.log("=== Debug Mode: MERIDIAN_DEBUG=true ===\n");
    }

    // Mode 1: Analyze mode - detect new interactions
    if (args.analyze) {
      console.log("=== Interaction Analysis Mode ===\n");

      // Read decisions (ADOPT events only)
      const {
        status: decisionStatus,
        records: decisions,
        warnings: decisionWarnings,
      } = readRecentDecisionsForInteraction({
        tail: args.tail || 100,
      });

      if (decisionStatus === "ERROR") {
        console.log("ERROR_READING_DECISIONS");
        return;
      }

      if (decisions.length === 0) {
        console.log("NO_ADOPT_DECISIONS_FOUND");
        return;
      }

      if (debugMode && decisionWarnings.length > 0) {
        console.log(`Decision warnings: ${decisionWarnings.join(", ")}\n`);
      }

      // Extract adoption events
      const adoptions = extractAdoptionEvents(decisions);

      console.log(`Found ${adoptions.length} adoption(s)\n`);

      if (adoptions.length < 2) {
        console.log("INSUFFICIENT_ADOPTIONS_FOR_INTERACTION_DETECTION");
        return;
      }

      // Read effects
      const proposalIds = adoptions.map((a) => a.proposalId);
      const { reports: effects, warnings: effectWarnings } =
        readRecentEffectsForInteraction({
          tail: args.tail || 200,
          proposalIds,
        });

      if (debugMode && effectWarnings.length > 0) {
        console.log(`Effect warnings: ${effectWarnings.join(", ")}\n`);
      }

      // Read regressions (optional)
      const { reports: regressions, warnings: regressionWarnings } =
        readRecentRegressionsForInteraction({
          tail: args.tail || 200,
          proposalIds,
        });

      if (debugMode && regressionWarnings.length > 0) {
        console.log(`Regression warnings: ${regressionWarnings.join(", ")}\n`);
      }

      // Detect interactions
      const interactions = detectInteractionsV1(adoptions, effects, regressions);

      console.log(`Detected ${interactions.length} interaction(s)\n`);

      if (interactions.length === 0) {
        console.log("NO_INTERACTIONS_DETECTED");
        return;
      }

      // Save and display each interaction
      for (const interaction of interactions) {
        // Save to store
        const { status: saveStatus, warnings: saveWarnings } =
          appendInteractionReportV1(interaction);

        if (saveStatus === "ERROR" && debugMode) {
          console.log(`Save warnings: ${saveWarnings.join(", ")}\n`);
        }

        // Display
        if (args.json) {
          if (debugMode) {
            console.log(JSON.stringify(interaction, null, 2));
          } else {
            const sanitized = sanitizeInteractionForDisplayV1(interaction, false);
            console.log(JSON.stringify(sanitized, null, 2));
          }
        } else {
          const lines = formatInteractionLinesV1(interaction, debugMode);
          for (const line of lines) {
            console.log(line);
          }
        }

        console.log(""); // Separator
      }

      return;
    }

    // Mode 2: View mode - read stored interaction reports
    console.log("=== Interaction Reports ===\n");

    const { reports, warnings } = readRecentInteractionReportsV1({
      tail: args.tail || 10,
      proposalId: args.proposalId,
    });

    if (debugMode && warnings.length > 0) {
      console.log(`Warnings: ${warnings.join(", ")}\n`);
    }

    if (reports.length === 0) {
      console.log("NO_INTERACTION_REPORTS_FOUND");
      console.log("\nTip: Use --analyze to detect new interactions");
      return;
    }

    console.log(`Found ${reports.length} report(s)\n`);

    // Display reports
    for (const report of reports) {
      if (args.json) {
        if (debugMode) {
          console.log(JSON.stringify(report, null, 2));
        } else {
          const sanitized = sanitizeInteractionForDisplayV1(report, false);
          console.log(JSON.stringify(sanitized, null, 2));
        }
      } else {
        const lines = formatInteractionLinesV1(report, debugMode);
        for (const line of lines) {
          console.log(line);
        }
      }

      console.log(""); // Separator
    }
  } catch (error) {
    console.error("ERROR: Interaction CLI failed");
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
