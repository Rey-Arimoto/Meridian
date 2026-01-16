/**
 * PR171: v1.4 Patch Preview Report v1 - Templates
 *
 * Purpose:
 *   Fixed mapping from patch operations to preview sections.
 *   All templates are label-only (no numerics, no rule values).
 *
 * Constitutional Constraints:
 *   - Fixed mapping: Deterministic patch op → section
 *   - Label-only: All strings are labels (no numerics)
 *   - No prescriptive language: Use descriptive labels only
 */

import { PreviewSection } from "./types";

/**
 * Preview Template
 *
 * Fixed template for one patch operation type.
 */
export interface PreviewTemplate {
  /**
   * Patch operation type (matches PatchKind from PR168)
   */
  patchKind: string;

  /**
   * Preview section template
   */
  section: PreviewSection;
}

/**
 * Fixed templates for all patch operations
 *
 * Maps PatchKind to PreviewSection (label-only).
 */
export const PREVIEW_TEMPLATES: PreviewTemplate[] = [
  // PATCH_PHASE_POLICY
  {
    patchKind: "PATCH_PHASE_POLICY",
    section: {
      title: "SECTION_PHASE_POLICY",
      before: ["BEFORE_STOP_RULES_CURRENT"],
      after: ["AFTER_STOP_RULES_TUNED"],
      notes: [
        "NOTE_STOP_WAIT_BALANCE_CHANGED",
        "NOTE_SAFETY_CONSTRAINTS_PRESERVED",
      ],
    },
  },

  // PATCH_GATE_ORDER
  {
    patchKind: "PATCH_GATE_ORDER",
    section: {
      title: "SECTION_GATE_PRIORITY",
      before: ["BEFORE_GATE_PRIORITY_CURRENT"],
      after: ["AFTER_GATE_PRIORITY_REORDERED"],
      notes: ["NOTE_BLOCK_REASON_SHIFT_EXPECTED"],
    },
  },

  // PATCH_ROUTER_TIEBREAK
  {
    patchKind: "PATCH_ROUTER_TIEBREAK",
    section: {
      title: "SECTION_ROUTER_TIEBREAK",
      before: ["BEFORE_ROUTE_TIEBREAK_CURRENT"],
      after: ["AFTER_ROUTE_TIEBREAK_CHANGED"],
      notes: ["NOTE_EXECUTION_PATH_VARIANCE"],
    },
  },

  // PATCH_NOT_ALLOWED
  {
    patchKind: "PATCH_NOT_ALLOWED",
    section: {
      title: "SECTION_NOT_ALLOWED",
      before: ["BEFORE_PATCH_NOT_ALLOWED_PRESENT"],
      after: ["AFTER_PATCH_NOT_ALLOWED_REJECT_EXPECTED"],
      notes: ["NOTE_POLICY_FIRST_REJECT"],
    },
  },

  // PATCH_TEMPLATE_SELECTION (optional, if exists in PR168)
  {
    patchKind: "PATCH_TEMPLATE_SELECTION",
    section: {
      title: "SECTION_TEMPLATE_SELECTION",
      before: ["BEFORE_TEMPLATE_SELECTION_CURRENT"],
      after: ["AFTER_TEMPLATE_SELECTION_TUNED"],
      notes: [
        "NOTE_RISK_PROFILE_SHIFT_EXPECTED",
        "NOTE_SAFETY_BOUNDS_PRESERVED",
      ],
    },
  },

  // PATCH_OBSERVABLE (optional, if exists in PR168)
  {
    patchKind: "PATCH_OBSERVABLE",
    section: {
      title: "SECTION_OBSERVABLE",
      before: ["BEFORE_OBSERVABLE_CURRENT"],
      after: ["AFTER_OBSERVABLE_ENHANCED"],
      notes: ["NOTE_NO_POLICY_CHANGE", "NOTE_MONITORING_ONLY"],
    },
  },

  // PATCH_UNKNOWN (fallback)
  {
    patchKind: "PATCH_UNKNOWN",
    section: {
      title: "SECTION_UNKNOWN_PATCH",
      before: ["BEFORE_UNKNOWN"],
      after: ["AFTER_UNKNOWN"],
      notes: ["NOTE_PATCH_TYPE_UNRECOGNIZED"],
    },
  },
];

/**
 * Get preview section template for patch operation
 *
 * @param patchKind - Patch operation type
 * @returns Preview section (or UNKNOWN template if not found)
 */
export function getSectionTemplate(patchKind: string): PreviewSection {
  const template = PREVIEW_TEMPLATES.find((t) => t.patchKind === patchKind);

  if (template) {
    // Return deep copy to avoid mutation
    return {
      title: template.section.title,
      before: [...template.section.before],
      after: [...template.section.after],
      notes: [...template.section.notes],
    };
  }

  // Fallback: UNKNOWN template
  const unknownTemplate = PREVIEW_TEMPLATES.find(
    (t) => t.patchKind === "PATCH_UNKNOWN"
  );

  return {
    title: "SECTION_UNKNOWN_PATCH",
    before: ["BEFORE_UNKNOWN"],
    after: ["AFTER_UNKNOWN"],
    notes: [`NOTE_PATCH_TYPE_UNRECOGNIZED_${patchKind}`],
  };
}

/**
 * Get all preview sections for patch operations
 *
 * @param patchOps - Array of patch operation types
 * @returns Array of preview sections (in order)
 */
export function getSectionsForPatchOps(patchOps: string[]): PreviewSection[] {
  return patchOps.map(getSectionTemplate);
}
