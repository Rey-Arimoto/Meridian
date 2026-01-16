/**
 * PR178: v1.4 Manual Review Trigger Hook v1 - Pipeline
 *
 * Purpose:
 *   Run complete review pipeline: snapshot → analyze → propose → preview → review
 *
 * Constitutional Constraints:
 *   - READ-ONLY: No execution/policy changes
 *   - Defensive: Never throws, returns status
 */

import { readRecentSnapshotsV1 } from "../snapshot/exporter";
import { analyzeSnapshotsV1 } from "../analyze/analyzer";
import { generateProposalsV1 } from "../propose/proposer";
import { generatePreviewV1 } from "../preview/previewer";
import { reviewPatchPreviewV1 } from "../review/reviewer";
import { appendPreviewV1 } from "../preview/store";
import { ReviewTriggerResultV1, ReviewTriggerOptions } from "./types";
import { sanitizeTriggerWarnings } from "./guards";

/**
 * Run manual review trigger pipeline
 *
 * @param opts - Trigger options
 * @returns Trigger result
 */
export async function runManualReviewTriggerV1(
  opts?: ReviewTriggerOptions
): Promise<ReviewTriggerResultV1> {
  const warnings: string[] = [];
  const tailSnapshots = opts?.tailSnapshots || 200;
  const priority = opts?.priority;

  const result: ReviewTriggerResultV1 = {
    status: "ERROR",
    ranSnapshot: false,
    ranAnalyze: false,
    ranPropose: false,
    ranPreview: false,
    ranReview: false,
    warnings: [],
  };

  try {
    // Step 1: Read recent snapshots
    try {
      const snapshotResult = await readRecentSnapshotsV1(
        {},
        { maxLines: tailSnapshots }
      );

      if (snapshotResult.snapshots.length === 0) {
        warnings.push("WARN_NO_SNAPSHOTS_FOUND");
        result.status = "ERROR";
        result.warnings = sanitizeTriggerWarnings(warnings);
        return result;
      }

      result.ranSnapshot = true;
      warnings.push(...snapshotResult.warnings);
    } catch (error) {
      warnings.push("ERROR_READING_SNAPSHOTS");
      result.status = "ERROR";
      result.warnings = sanitizeTriggerWarnings(warnings);
      return result;
    }

    // Step 2: Analyze snapshots
    try {
      const snapshotResult = await readRecentSnapshotsV1(
        {},
        { maxLines: tailSnapshots }
      );
      const analysis = await analyzeSnapshotsV1(snapshotResult.snapshots);

      result.ranAnalyze = true;
      warnings.push(...analysis.warnings);
    } catch (error) {
      warnings.push("ERROR_ANALYZING_SNAPSHOTS");
      result.status = "PARTIAL";
    }

    // Step 3: Generate proposals
    let proposals: any[] = [];
    try {
      const snapshotResult = await readRecentSnapshotsV1(
        {},
        { maxLines: tailSnapshots }
      );
      const analysis = await analyzeSnapshotsV1(snapshotResult.snapshots);

      const proposeResult = await generateProposalsV1(analysis);

      proposals = proposeResult.proposals;
      result.ranPropose = true;
      warnings.push(...proposeResult.warnings);

      if (proposals.length === 0) {
        warnings.push("WARN_NO_PROPOSALS_GENERATED");
      }
    } catch (error) {
      warnings.push("ERROR_GENERATING_PROPOSALS");
      result.status = "PARTIAL";
    }

    // Filter by priority if specified
    if (priority && priority !== "ALL") {
      proposals = proposals.filter((p) => p.priority === priority);
    }

    // Limit to top 3 proposals
    const topProposals = proposals.slice(0, 3);

    // Step 4: Generate previews
    const previews: any[] = [];
    try {
      for (const proposal of topProposals) {
        try {
          const preview = await generatePreviewV1(proposal);
          previews.push(preview);

          // Append to store
          await appendPreviewV1(preview);
        } catch (error) {
          warnings.push(`ERROR_GENERATING_PREVIEW_${proposal.proposalId}`);
        }
      }

      result.ranPreview = previews.length > 0;
    } catch (error) {
      warnings.push("ERROR_GENERATING_PREVIEWS");
      result.status = "PARTIAL";
    }

    // Step 5: Review previews
    try {
      for (const preview of previews) {
        try {
          const review = reviewPatchPreviewV1(preview);
          warnings.push(...review.warnings);
        } catch (error) {
          warnings.push(`ERROR_REVIEWING_PREVIEW_${preview.proposalId}`);
        }
      }

      result.ranReview = previews.length > 0;
    } catch (error) {
      warnings.push("ERROR_REVIEWING_PREVIEWS");
      result.status = "PARTIAL";
    }

    // Determine final status
    if (
      result.ranSnapshot &&
      result.ranAnalyze &&
      result.ranPropose &&
      result.ranPreview &&
      result.ranReview
    ) {
      result.status = "TRIGGERED";
    } else if (result.ranSnapshot) {
      result.status = "PARTIAL";
    } else {
      result.status = "ERROR";
    }

    result.warnings = sanitizeTriggerWarnings(warnings);
    return result;
  } catch (error) {
    // Fatal error: return ERROR status
    warnings.push("FATAL_ERROR_IN_TRIGGER_PIPELINE");
    result.status = "ERROR";
    result.warnings = sanitizeTriggerWarnings(warnings);
    return result;
  }
}
