"use strict";
/**
 * PR152: v1.4 TS Rebalance Template Resolver (READ-ONLY)
 *
 * Purpose:
 *   Resolve template_id (from Python PR151) to actual token weight ratios.
 *   This is the ONLY file that holds token weight percentages.
 *
 * Constitutional Constraints:
 *   - Fixed table only (no dynamic calculation)
 *   - Token names are only in TS side (Python never sees wBTC/USDC)
 *   - Weights are abstract risk/safe ratios
 *
 * Template Philosophy:
 *   - TPL_RISK_0: Maximum safe (0% risk asset, 100% stable)
 *   - TPL_RISK_20: Low risk (20% risk asset, 80% stable)
 *   - TPL_RISK_50: Balanced (50% risk asset, 50% stable)
 *   - TPL_RISK_90: High risk (90% risk asset, 10% stable)
 *   - TPL_UNKNOWN: Unknown state (default to balanced 50/50 for safety)
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.resolveTemplate = resolveTemplate;
exports.isValidTemplateId = isValidTemplateId;
exports.getSupportedTemplateIds = getSupportedTemplateIds;
/**
 * FIXED TEMPLATE TABLE
 *
 * IMPORTANT: This is the ONLY location where token weight percentages are stored.
 * Do NOT add weight numbers anywhere else in the codebase.
 *
 * Python side does NOT know these weights exist.
 * Python only knows abstract template IDs.
 */
var TEMPLATE_TABLE = {
    TPL_RISK_0: {
        wbtcWeight: 0.0, // 0% wBTC (maximum safe)
        usdcWeight: 1.0, // 100% USDC
    },
    TPL_RISK_20: {
        wbtcWeight: 0.2, // 20% wBTC (low risk)
        usdcWeight: 0.8, // 80% USDC
    },
    TPL_RISK_50: {
        wbtcWeight: 0.5, // 50% wBTC (balanced)
        usdcWeight: 0.5, // 50% USDC
    },
    TPL_RISK_90: {
        wbtcWeight: 0.9, // 90% wBTC (high risk)
        usdcWeight: 0.1, // 10% USDC
    },
    TPL_UNKNOWN: {
        wbtcWeight: 0.5, // 50% wBTC (safe default - balanced)
        usdcWeight: 0.5, // 50% USDC
    },
};
/**
 * Resolve template ID to token weights
 *
 * @param templateId - Template ID from Python PR151
 * @returns Token weight targets
 *
 * @example
 * const weights = resolveTemplate("TPL_RISK_90");
 * // { wbtcWeight: 0.9, usdcWeight: 0.1 }
 */
function resolveTemplate(templateId) {
    var weights = TEMPLATE_TABLE[templateId];
    if (!weights) {
        // Defensive: fallback to balanced if unknown
        console.warn("[TEMPLATE] Unknown template ID: ".concat(templateId, ", falling back to TPL_UNKNOWN"));
        return TEMPLATE_TABLE.TPL_UNKNOWN;
    }
    return weights;
}
/**
 * Validate template ID
 *
 * @param templateId - Template ID to validate
 * @returns True if valid
 */
function isValidTemplateId(templateId) {
    return templateId in TEMPLATE_TABLE;
}
/**
 * Get all supported template IDs
 *
 * @returns Array of template IDs
 */
function getSupportedTemplateIds() {
    return Object.keys(TEMPLATE_TABLE);
}
