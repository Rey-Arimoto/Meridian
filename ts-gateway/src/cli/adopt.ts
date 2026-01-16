#!/usr/bin/env node
/**
 * PR168: v1.4 Policy-First Adoption Loop - CLI
 * PR171: v1.4 Patch Preview Report v1 - CLI Integration
 * PR172: v1.4 Patch Review Checklist + Decision Rationale v1 - CLI Integration
 * PR173: v1.4 Decision Acknowledgement + Reviewer Trace v1 - CLI Integration
 *
 * Purpose:
 *   Policy-first adoption loop CLI that analyzes snapshots, generates proposals,
 *   builds patch plans, simulates replay compare, and decides ADOPT/HOLD/REJECT.
 *   PR171: Optionally generates preview reports before decision.
 *   PR172: Optionally runs preview → review → decision flow with structured checklist.
 *   PR173: Optionally records decision acknowledgement for audit trail.
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
 *   npx ts-node src/cli/adopt.ts --preview
 *   npx ts-node src/cli/adopt.ts --preview-only
 *   npx ts-node src/cli/adopt.ts --review
 *   npx ts-node src/cli/adopt.ts --ack
 *   npx ts-node src/cli/adopt.ts --ack-only
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
import { generatePreviewV1 } from "../preview/previewer";
import { appendPreviewV1, readRecentPreviewsV1 } from "../preview/store";
import { formatPreviewLines } from "../preview/guards";
import { reviewPatchPreviewV1 } from "../review/reviewer";
import { formatReviewLines } from "../review/guards";
import { buildDecisionAckV1 } from "../decision/ack";
import { appendDecisionAckV1 } from "../decision/store";
import { formatAckLines } from "../decision/guards";

/**
 * Parse CLI arguments
 */
function parseArgs(): {
  tail?: number;
  priority?: AdoptPriority;
  json?: boolean;
  preview?: boolean;
  previewOnly?: boolean;
  review?: boolean;
  ack?: boolean;
  ackOnly?: boolean;
} {
  const args = process.argv.slice(2);
  const result: {
    tail?: number;
    priority?: AdoptPriority;
    json?: boolean;
    preview?: boolean;
    previewOnly?: boolean;
    review?: boolean;
    ack?: boolean;
    ackOnly?: boolean;
  } = {};

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
    } else if (arg === "--preview") {
      result.preview = true;
    } else if (arg === "--preview-only") {
      result.previewOnly = true;
    } else if (arg === "--review") {
      result.review = true;
    } else if (arg === "--ack") {
      result.ack = true;
    } else if (arg === "--ack-only") {
      result.ackOnly = true;
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

    // PR173: --ack-only mode (read existing preview/review, create ack only)
    if (args.ackOnly) {
      // Read most recent preview
      const { previews, warnings: previewWarnings } = readRecentPreviewsV1({ tail: 1 });

      if (previews.length === 0) {
        console.log("NO_PREVIEW_FOUND_FOR_ACK");
        return;
      }

      const previewReport = previews[0];

      // Review the preview
      const reviewReport = reviewPatchPreviewV1(previewReport);

      // Build ack record
      const ackRecord = buildDecisionAckV1({
        reviewer: "HUMAN_PRIMARY", // Default for manual ack
        source: "CLI_ACK",
        proposalId: previewReport.proposalId,
        previewReport,
        reviewReport,
      });

      // Append to store
      const { status, warnings: ackWarnings } = appendDecisionAckV1(ackRecord);

      if (status === "ERROR") {
        console.log(`ACK_SAVE_FAILED: ${ackWarnings.join(", ")}`);
      }

      // Display ack
      console.log("\n=== Decision Acknowledgement ===\n");
      const ackLines = formatAckLines(ackRecord, debugMode);
      for (const line of ackLines) {
        console.log(line);
      }

      return;
    }

    // Adopt improvement
    const adoptResult = await adoptImprovementV1(
      snapshotResult.snapshots,
      args.priority,
      tailN
    );

    // PR173: --ack mode (full flow + acknowledgement)
    if (args.ack) {
      // 1. Generate preview report
      const previewReport = generatePreviewV1({
        patchOps: adoptResult.patchPlan?.ops || [],
        proposalId: adoptResult.proposalId,
        priority: adoptResult.priority,
        decisionCandidate: adoptResult.decision,
        evidence: [], // Evidence would need to be passed from proposer if available
        compareSignals: adoptResult.compare?.signals || [],
      });

      // Append to store
      appendPreviewV1(previewReport);

      // 2. Review the preview
      const reviewReport = reviewPatchPreviewV1(previewReport);

      // 3. Build ack record
      const ackRecord = buildDecisionAckV1({
        reviewer: "AUTO_ASSISTED", // Assisted by PR172 checklist
        source: "CLI_ADOPT",
        proposalId: adoptResult.proposalId,
        previewReport,
        reviewReport,
        decisionResult: adoptResult,
      });

      // Append to store
      const { status, warnings: ackWarnings } = appendDecisionAckV1(ackRecord);

      if (status === "ERROR" && debugMode) {
        console.log(`ACK_SAVE_WARNINGS: ${ackWarnings.join(", ")}\n`);
      }

      // 4. Display: Preview → Review → Decision → Acknowledgement
      console.log("\n=== Preview Summary ===\n");
      const previewLines = formatPreviewLines(previewReport, debugMode);
      for (const line of previewLines) {
        console.log(line);
      }

      console.log("\n=== Review Checklist ===\n");
      const reviewLines = formatReviewLines(reviewReport, debugMode);
      for (const line of reviewLines) {
        console.log(line);
      }

      console.log("\n=== Adoption Decision (PR168) ===\n");
      const adoptLines = formatAdoptResultLabelOnlyLines(adoptResult, debugMode);
      for (const line of adoptLines) {
        console.log(line);
      }

      console.log("\n=== Decision Acknowledgement (PR173) ===\n");
      const ackLines = formatAckLines(ackRecord, debugMode);
      for (const line of ackLines) {
        console.log(line);
      }

      return;
    }

    // PR172: Generate preview + review + decision if requested
    if (args.review) {
      // 1. Generate preview report
      const previewReport = generatePreviewV1({
        patchOps: adoptResult.patchPlan?.ops || [],
        proposalId: adoptResult.proposalId,
        priority: adoptResult.priority,
        decisionCandidate: adoptResult.decision,
        evidence: [], // Evidence would need to be passed from proposer if available
        compareSignals: adoptResult.compare?.signals || [],
      });

      // Append to store
      appendPreviewV1(previewReport);

      // 2. Review the preview
      const reviewReport = reviewPatchPreviewV1(previewReport);

      // 3. Display: Preview summary → Review checklist → Decision rationale → Adoption decision
      console.log("\n=== Preview Summary ===\n");
      const previewLines = formatPreviewLines(previewReport, debugMode);
      for (const line of previewLines) {
        console.log(line);
      }

      console.log("\n=== Review Checklist ===\n");
      const reviewLines = formatReviewLines(reviewReport, debugMode);
      for (const line of reviewLines) {
        console.log(line);
      }

      console.log("\n=== Adoption Decision (PR168) ===\n");
      const adoptLines = formatAdoptResultLabelOnlyLines(adoptResult, debugMode);
      for (const line of adoptLines) {
        console.log(line);
      }

      return;
    }

    // PR171: Generate preview report if requested
    if (args.preview || args.previewOnly) {
      const previewReport = generatePreviewV1({
        patchOps: adoptResult.patchPlan?.ops || [],
        proposalId: adoptResult.proposalId,
        priority: adoptResult.priority,
        decisionCandidate: adoptResult.decision,
        evidence: [], // Evidence would need to be passed from proposer if available
        compareSignals: adoptResult.compare?.signals || [],
      });

      // Append to store
      appendPreviewV1(previewReport);

      if (debugMode || args.previewOnly) {
        console.log("\n=== Preview Report ===\n");
        const previewLines = formatPreviewLines(previewReport, debugMode);
        for (const line of previewLines) {
          console.log(line);
        }
      } else {
        console.log("\nPREVIEW_AVAILABLE: Patch preview saved to previews.log\n");
      }

      // If preview-only, stop here
      if (args.previewOnly) {
        return;
      }
    }

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
