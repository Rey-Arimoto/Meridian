# PR17 — v0.4 Confidence Charter（Confidence を第一級市民にする）

**Status:** Scope Lock
**Target:** v0.4
**Dependencies:** v0.3-intent-complete (PR14–PR16A)

---

## Goal

Meridian v0.4 introduces **Confidence** as a first-class citizen alongside Intent.

Confidence represents **how structurally robust the system's current judgment is**, independent of what that judgment is.

This separation enables:
- Explicit reasoning about judgment fragility
- Principled action sizing based on structural confidence
- Intent-preserving risk modulation
- Constitutional guardrails against overconfident execution

---

## Why Intent Alone Is Insufficient

v0.3 achieved Intent-primary architecture: the system knows **what** it wants to do and **why**.

However, Intent does not capture:

**How strongly should we execute this Intent?**

Consider these scenarios:

| Scenario | Intent | Missing Dimension |
|----------|--------|-------------------|
| Stable regime, clear signal, 50+ ticks of consistency | SEEK | High structural confidence → Full conviction |
| Stable regime, weak signal, 3 ticks since regime entry | SEEK | Low structural confidence → Tentative positioning |
| Volatile regime, capital at risk, entropy near threshold | DEFEND | Low structural confidence → Defensive posture fragile |
| Volatile regime, capital at risk, entropy stable for 20 ticks | DEFEND | High structural confidence → Defense well-founded |

**Same Intent. Different execution conviction.**

Intent tells us **what** to do. Confidence tells us **how hard** to do it.

---

## What Confidence Is NOT

Confidence is often confused with related but distinct concepts. Clarity requires explicit negation:

### ❌ Confidence is NOT Prediction Accuracy
- Prediction accuracy: "This trade will succeed"
- Confidence: "This judgment is structurally robust"

Meridian makes no predictions. Confidence is about **judgment fragility**, not outcome probability.

### ❌ Confidence is NOT Success Probability
- Success probability: P(profit | action)
- Confidence: Structural robustness of current assessment

Confidence does not estimate future outcomes. It assesses **current judgment stability**.

### ❌ Confidence is NOT Psychological Certainty
- Psychological certainty: Human emotional state
- Confidence: Measurable structural properties of decision context

Confidence is derived from **observable system state**, not subjective feelings.

### ❌ Confidence is NOT a Volatility Metric
- Volatility: Market price fluctuation
- Confidence: Judgment robustness

Low volatility can have low confidence (regime just entered, signal weak).
High volatility can have high confidence (regime stable for 50 ticks, signal strong).

---

## What Confidence IS

**Confidence is the system's internal assessment of how structurally robust its current judgment is.**

### Structural Robustness Means:
- **Regime stability:** How long has the current regime persisted?
- **Signal consistency:** How stable are entropy, MA, and other indicators?
- **Threshold distance:** How far are we from regime boundaries?
- **Recent transition count:** How many regime changes in recent history?
- **Overlay suppression history:** How often has SafetyOverlay blocked actions recently?

### Core Principle:

> Confidence measures how likely the current assessment is to remain valid over the next few ticks.

**Not**: "Will this action succeed?"
**But**: "Is this judgment built on stable foundations?"

---

## Intent × Confidence: Relationship Architecture

### Fundamental Constraint: Confidence Never Overrides Intent

```
Intent = What to do
Confidence = How hard to do it
```

**Confidence CANNOT:**
- Change SEEK → DEFEND
- Suppress PAUSE
- Override constitutional constraints
- Alter Intent priority hierarchy

**Confidence CAN:**
- Modulate action size within Intent
- Influence continuation vs. pause decisions
- Adjust risk exposure given Intent
- Inform overlay parameter selection

### Intent × Confidence Matrix (Conceptual)

| Intent | High Confidence | Low Confidence |
|--------|-----------------|----------------|
| **SEEK** | Full conviction opportunity search. Commit capital aggressively within constitutional bounds. | Tentative exploration. Minimal capital commitment, quick reversal readiness. |
| **HARVEST** | Strong value extraction. Maximize position while regime favorable. | Cautious harvesting. Lock partial gains, reduce exposure incrementally. |
| **DEFEND** | Principled defense. Capital protection well-founded, maintain defensive posture. | Fragile defense. Consider early exit, tighten stop-loss, reduce exposure preemptively. |
| **STABILIZE** | Structured unwinding. Regime transition confirmed, orderly reduction. | Emergency stabilization. Regime boundary unclear, rapid risk reduction. |
| **PAUSE** | Constitutional freeze with clear justification. Wait for regime clarity. | Constitutional freeze under fragile conditions. Extend pause, avoid premature re-entry. |
| **IDLE** | Stable idleness. No signal, no action, no urgency. | Uncertain idleness. Watch for regime shift, maintain readiness. |

**Key Insight:**
High Confidence amplifies Intent execution.
Low Confidence tempers Intent execution.
Intent itself remains unchanged.

---

## Confidence as Second-Class vs. First-Class Citizen

### If Confidence Were Second-Class (Rejected):
- Confidence computed implicitly within Intent selection
- No explicit Confidence value logged
- Intent selection logic contains hidden confidence assumptions
- Operators cannot audit confidence reasoning

### Confidence as First-Class Citizen (v0.4):
- Confidence computed explicitly before action sizing
- Confidence value logged alongside Intent
- Intent and Confidence auditable independently
- Operators can analyze Confidence × Intent distributions

**Why first-class?**
Confidence is as fundamental to execution as Intent is to direction. Both must be explicit, auditable, and constitutional.

---

## Confidence Computation: Explicitly Deferred

**v0.4 Charter does NOT define:**
- ❌ Confidence calculation formula
- ❌ Confidence scale (0–1? discrete levels? other?)
- ❌ Confidence input weights
- ❌ Confidence thresholds
- ❌ Confidence aggregation logic

**Why defer?**
v0.4 establishes Confidence as a **design primitive**. Computation details will emerge through careful implementation PRs (v0.4A, v0.4B, …), not upfront specification.

**What v0.4 Charter DOES define:**
- ✅ Confidence is structural robustness assessment
- ✅ Confidence modulates action size, not Intent
- ✅ Confidence is first-class citizen (logged, auditable)
- ✅ Confidence derived from observable system state
- ✅ Confidence deterministic (same state → same confidence)

---

## Constraints

### Constitutional Constraints (Preserved from v0.3)
- Intent priority hierarchy unchanged
- Safety overlay fail-closed guarantees preserved
- Emergency freeze supremacy maintained
- No action during PAUSE Intent (Confidence cannot override)

### Determinism (Preserved from v0.3)
- Confidence computation deterministic (same inputs → same confidence)
- No randomness, no learning, no hidden state
- Tick-based execution (no real-time dependencies)
- Auditable: Every Confidence value logged with derivation reason

### Scope Boundaries (v0.4)
- READ-ONLY for v0.3 Intent logic (no Intent changes)
- Confidence logic implemented as new modules (ConfidenceEstimator, ActionSizer)
- v0.3 validations continue to pass (PR14–PR16A)
- CSV schema extended (Confidence logged as additional column)

---

## Non-Goals (Deferred)

### Not in v0.4:
- ❌ Confidence-based learning or optimization
- ❌ Dynamic confidence threshold adjustment
- ❌ Confidence → Intent feedback (Confidence cannot change Intent)
- ❌ Multi-tick confidence smoothing or prediction
- ❌ Confidence-based portfolio rebalancing (beyond action sizing)

**Rationale:** v0.4 focuses on **architectural foundation**. Advanced Confidence mechanics deferred to v0.5+.

---

## Implementation Boundaries (What v0.4 PRs Will Do)

v0.4 development will implement:

1. **Confidence Estimation Module:**
   - Input: System state (entropy, regime, history)
   - Output: Confidence value (scale TBD)
   - Logic: Structural robustness assessment (formula TBD)

2. **Action Sizing Module:**
   - Input: Intent + Confidence + Current State
   - Output: Sized Action (target weight adjusted by Confidence)
   - Logic: Confidence-based action modulation (method TBD)

3. **Confidence Logging:**
   - Confidence value logged alongside Intent
   - Confidence derivation reason logged
   - Confidence distribution analysis in reports

4. **Validation & Smoke Tests:**
   - Confidence computation deterministic
   - Confidence never overrides Intent
   - Confidence modulation within constitutional bounds
   - v0.3 validations continue to pass

**Critical:** Each implementation PR will document its specific computation choices, but the **Charter defines the design space**, not the solution.

---

## Done Criteria

v0.4 Confidence Charter is complete when:

1. **Confidence Defined:** Structural robustness assessment as first-class citizen
2. **Intent × Confidence Separation:** Confidence modulates execution, never overrides Intent
3. **Confidence Logged:** CSV includes Confidence column with derivation reason
4. **Deterministic & Auditable:** Confidence computation reproducible and logged
5. **Constitutional Compliance:** All v0.3 constraints preserved
6. **v0.3 Validations Pass:** All PR14–PR16A validations continue to pass
7. **Confidence Distribution Analysis:** Reports include Confidence × Intent cross-tabulation

---

## Why Confidence?

**Intent without Confidence is dangerous:**
- SEEK with fragile regime → Overcommitment to unstable opportunity
- DEFEND with unstable entropy → Defense based on noise, not signal
- HARVEST with recent regime transition → Premature value extraction

**Confidence completes the decision architecture:**
- Regime answers: "What is the market state?"
- Intent answers: "What do we want to do about it?"
- Confidence answers: "How strongly should we execute?"
- Action answers: "What is the final sized position?"

This separation makes the system **more robust, more principled, and more constitutional**.

---

## Market Accident Prevention

Confidence directly addresses two failure modes:

### 1. Overconfident Execution in Fragile Regimes
**Without Confidence:**
- SEEK triggered by weak signal → Full capital commitment
- Regime flips 2 ticks later → Large loss

**With Confidence:**
- SEEK triggered by weak signal → Low Confidence detected
- Action sized conservatively → Small position, limited loss
- Regime flips → Minimal capital at risk

### 2. Under-Execution in Stable Opportunities
**Without Confidence:**
- SEEK triggered by strong signal → Conservative action (fear of reversal)
- Regime stable for 50 ticks → Missed alpha

**With Confidence:**
- SEEK triggered by strong signal → High Confidence detected
- Action sized aggressively → Full conviction position
- Regime stable → Alpha captured

**Confidence prevents both overcommitment to fragile judgments and undercommitment to robust ones.**

---

## Philosophical Foundation

Confidence is not a performance optimization. It is an **epistemic humility mechanism**.

The system must know:
- When its judgment is built on solid foundations (act boldly)
- When its judgment is fragile (act cautiously)
- When it cannot tell the difference (fail closed)

Meridian does not predict the future. But it can and must assess **how fragile its present understanding is**.

That assessment is Confidence.

---

**Meridian v0.4: Intelligence through Intent, Robustness through Confidence**
