# Entropy Specification  
**Meridian Canonical Definition**

---

## 1. Purpose

This document defines **Entropy** as used by Meridian.

It is not a generic statistical entropy.
It is not volatility.
It is not randomness.

Entropy in Meridian is a **state variable** that determines whether action is permissible.

This specification exists to ensure:
- determinism,
- reproducibility,
- constitutional enforcement,
- and future on-chain verification.

---

## 2. Conceptual Definition

> **Entropy measures how much the current market state becomes unexplainable by existing rules, assumptions, and strategies.**

Entropy is not about price direction.
It is about **model validity**.

When entropy rises:
- causal structure weakens,
- regime assumptions fail,
- prediction confidence collapses.

When entropy exceeds a critical threshold, **all actions must stop**.

---

## 3. Relationship to Classical Entropy

Meridian entropy is conceptually aligned with entropy in physics and information theory:

| Domain | Entropy Meaning |
|------|-----------------|
| Thermodynamics | Loss of usable energy |
| Information Theory | Uncertainty / information dispersion |
| Meridian | Loss of explanatory power |

In all cases, entropy represents **irreversibility and loss of structure**.

Meridian treats markets as **information-processing systems**,  
and entropy as **structural information decay**.

---

## 4. What Entropy Is NOT

Entropy is explicitly **not**:
- volatility (price amplitude),
- variance,
- randomness,
- noise,
- unpredictability in isolation.

High volatility with stable structure is **low entropy**.  
Low volatility with broken assumptions is **high entropy**.

---

## 5. Formal Properties

Meridian entropy `H_t` satisfies the following:

- Domain:

H_t ∈ [0, 1]

- Monotonic meaning:

higher H_t ⇒ lower action permissibility

- Deterministic:  
Same inputs must produce the same `H_t`.

- Observable:  
`H_t` must be derivable from observable market data.

---

## 6. Composite Entropy (v0.1)

In v0.1, entropy is implemented as **Composite Entropy**, combining:

### 6.1 Entropy Acceleration (EA)

Measures **how quickly structure is degrading**.

Intuition:
- Sudden regime changes
- Non-linear transitions
- Reflexive feedback loops

EA captures second-order instability.

---

### 6.2 Entropy Saturation (ES)

Measures **how close the system is to structural collapse**.

Intuition:
- Persistent explanation failure
- Regime exhaustion
- Lack of recoverable structure

ES captures proximity to irreversibility.

---

### 6.3 Composite Form

H_t = f(EA_t, ES_t)

Where `f` is deterministic and bounded.

The exact function is implementation-specific but must preserve:
- monotonicity,
- boundedness,
- reproducibility.

---

## 7. Phase Classification

Based on `H_t`, Meridian classifies market states:

| Phase | Condition | Interpretation |
|-----|----------|---------------|
| Order (O) | `H_t < H_low` | Stable, explainable |
| Transition (T) | `H_low ≤ H_t < H_high` | Structure degrading |
| Disorder (D) | `H_t ≥ H_high` | Explanation failure |

---

## 8. Constitutional Freeze

A hard threshold exists:

H_t ≥ H_critical ⇒ FREEZE

Properties:
- Mandatory
- Immediate
- Non-optimizable
- Non-overridable

Freeze is **not a strategy**.  
It is constitutional law.

---

## 9. NoOp as First-Class Outcome

Meridian explicitly records **NoOp** as a decision.

NoOp occurs when:
- entropy is too high,
- signal confidence collapses,
- constitutional constraints activate.

NoOp is not absence of action.
It is **intentional restraint**.

---

## 10. Determinism and Auditability

Entropy computation must be:
- deterministic,
- replayable,
- auditable.

This enables:
- backtesting integrity,
- on-chain verification (v0.2+),
- dispute resolution,
- trustless operation.

---

## 11. Future Extensions

Planned extensions include:
- multi-timescale entropy,
- cross-market entropy correlation,
- on-chain entropy commitments,
- entropy proofs for NoOp justification.

However:
> **No learning, no stochasticity, no optimization may violate constitutional thresholds.**

---

## 12. Summary

Entropy in Meridian is:

- a measure of explanation failure,
- a gatekeeper of action,
- the foundation of survival-first intelligence.

> **Meridian extracts alpha from order,  
> and preserves capital against entropy.**

This specification defines the boundary.
