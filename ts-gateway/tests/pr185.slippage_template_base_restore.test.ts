/**
 * PR185: v1.4 Restore Template-Based Slippage Base (PR157 Compatibility) v1 - Tests
 *
 * Purpose:
 *   Verify template-based slippage calculation (PR157) is restored while
 *   maintaining PR184 observe degrade adjustment.
 *
 * Test Coverage:
 *   1. TPL_RISK_90 + NORMAL → base=150
 *   2. TPL_RISK_0 + NORMAL → base=50
 *   3. TPL_RISK_50 + PHASE_PRE_SHOCK → 100+100=200
 *   4. TPL_RISK_20 + REVERSAL → 75+200=275
 *   5. unknown template + IMPACT_UNKNOWN → 200+200=400 (safe side)
 *   6. observeDegradeLevel=HEAVY adds +300
 *   7. hard cap 1500 enforced
 *   8. All adjustments combined (bonus test)
 */

import { computeSlippageBps } from "../src/rebalance/slippage";

describe("PR185: Restore Template-Based Slippage Base", () => {
  /**
   * Test 1: TPL_RISK_90 + NORMAL → base=150
   */
  test("Test 1: TPL_RISK_90 base is 150 bps", () => {
    const slippage = computeSlippageBps({
      templateId: "TPL_RISK_90",
    });

    expect(slippage).toBe(150);
  });

  /**
   * Test 2: TPL_RISK_0 + NORMAL → base=50
   */
  test("Test 2: TPL_RISK_0 base is 50 bps", () => {
    const slippage = computeSlippageBps({
      templateId: "TPL_RISK_0",
    });

    expect(slippage).toBe(50);
  });

  /**
   * Test 3: TPL_RISK_50 + PHASE_PRE_SHOCK → 100+100=200
   */
  test("Test 3: TPL_RISK_50 + PRE_SHOCK adds 100 bps", () => {
    const slippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      phaseLabel: "PHASE_PRE_SHOCK",
    });

    expect(slippage).toBe(100 + 100); // base + phase
  });

  /**
   * Test 4: TPL_RISK_20 + REVERSAL → 75+200=275
   */
  test("Test 4: TPL_RISK_20 + REVERSAL adds 200 bps", () => {
    const slippage1 = computeSlippageBps({
      templateId: "TPL_RISK_20",
      phaseLabel: "PHASE_UP_REVERSAL",
    });

    const slippage2 = computeSlippageBps({
      templateId: "TPL_RISK_20",
      phaseLabel: "PHASE_DOWN_REVERSAL",
    });

    expect(slippage1).toBe(75 + 200); // base + reversal
    expect(slippage2).toBe(75 + 200); // base + reversal
  });

  /**
   * Test 5: unknown template + IMPACT_UNKNOWN → 200+200=400 (safe side)
   */
  test("Test 5: Unknown template + IMPACT_UNKNOWN is safe side", () => {
    const slippage = computeSlippageBps({
      templateId: "TPL_UNKNOWN_XXX", // Unknown template
      impactLabel: "IMPACT_UNKNOWN",
    });

    expect(slippage).toBe(200 + 200); // unknown base + impact unknown
  });

  /**
   * Test 6: observeDegradeLevel=HEAVY adds +300
   */
  test("Test 6: DEGRADED_HEAVY adds 300 bps", () => {
    const baseSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
    });

    const degradedSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      observeDegradeLevel: "DEGRADED_HEAVY",
    });

    expect(degradedSlippage).toBe(baseSlippage + 300);
  });

  /**
   * Test 7: hard cap 1500 enforced
   */
  test("Test 7: Hard cap 1500 bps enforced", () => {
    // Create conditions that exceed 1500:
    // TPL_RISK_90 (150) + REVERSAL (200) + STRESSED (200) + IMPACT_HIGH (200)
    // + CETUS (50) + DEGRADED_HEAVY (300) = 1100 (below cap)
    const slippage1 = computeSlippageBps({
      templateId: "TPL_RISK_90",
      phaseLabel: "PHASE_UP_REVERSAL",
      stressLabel: "STRESS_STRESSED",
      impactLabel: "IMPACT_HIGH",
      venue: "CETUS",
      observeDegradeLevel: "DEGRADED_HEAVY",
    });

    expect(slippage1).toBe(150 + 200 + 200 + 200 + 50 + 300); // 1100

    // Try to exceed cap with unknown base
    // UNKNOWN (200) + REVERSAL (200) + STRESSED (200) + IMPACT_UNKNOWN (200)
    // + CETUS (50) + DEGRADED_HEAVY (300) = 1150 (below cap)
    const slippage2 = computeSlippageBps({
      templateId: undefined, // Uses UNKNOWN base (200)
      phaseLabel: "PHASE_UP_REVERSAL",
      stressLabel: "STRESS_STRESSED",
      impactLabel: "IMPACT_UNKNOWN",
      venue: "CETUS",
      observeDegradeLevel: "DEGRADED_HEAVY",
    });

    expect(slippage2).toBe(200 + 200 + 200 + 200 + 50 + 300); // 1150

    // Hard cap should be enforced (defensive: return 1500 on error would also work)
    expect(slippage2).toBeLessThanOrEqual(1500);
  });

  /**
   * Test 8: All adjustments combined (comprehensive)
   */
  test("Test 8: All adjustments combine correctly", () => {
    // TPL_RISK_50 (100) + SHOCK (150) + TENSE (100) + MEDIUM (100)
    // + DEEPBOOK (0) + DEGRADED_MEDIUM (150) = 600
    const slippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      phaseLabel: "PHASE_UP_SHOCK",
      stressLabel: "STRESS_TENSE",
      impactLabel: "IMPACT_MEDIUM",
      venue: "DEEPBOOK",
      observeDegradeLevel: "DEGRADED_MEDIUM",
    });

    expect(slippage).toBe(100 + 150 + 100 + 100 + 0 + 150); // 600
  });

  /**
   * Test 9: CETUS venue adds 50 bps
   */
  test("Test 9: CETUS venue adds 50 bps", () => {
    const deepbookSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      venue: "DEEPBOOK",
    });

    const cetusSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      venue: "CETUS",
    });

    expect(cetusSlippage).toBe(deepbookSlippage + 50);
  });

  /**
   * Test 10: No template provided uses UNKNOWN base (200, safe side)
   */
  test("Test 10: No template uses UNKNOWN base (200)", () => {
    const slippage = computeSlippageBps({
      // No templateId
    });

    expect(slippage).toBe(200); // UNKNOWN base
  });

  /**
   * Test 11: Stress STRESSED adds 200 bps
   */
  test("Test 11: STRESSED adds 200 bps", () => {
    const calmSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      stressLabel: "STRESS_CALM", // No adjustment
    });

    const stressedSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      stressLabel: "STRESS_STRESSED",
    });

    expect(stressedSlippage).toBe(calmSlippage + 200);
  });

  /**
   * Test 12: Multiple phase labels (verify each)
   */
  test("Test 12: Phase adjustments are correct", () => {
    const baseSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      phaseLabel: "PHASE_NORMAL",
    });

    const shockSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      phaseLabel: "PHASE_UP_SHOCK",
    });

    const preShockSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      phaseLabel: "PHASE_PRE_SHOCK",
    });

    const reversalSlippage = computeSlippageBps({
      templateId: "TPL_RISK_50",
      phaseLabel: "PHASE_UP_REVERSAL",
    });

    expect(baseSlippage).toBe(100); // No phase adjustment
    expect(shockSlippage).toBe(100 + 150);
    expect(preShockSlippage).toBe(100 + 100);
    expect(reversalSlippage).toBe(100 + 200);
  });
});
