# Entropy Specification  
**Meridian Entropy Model (Canonical Definition)**

---

## 1. Purpose

This document defines **entropy** as used in Meridian.

Entropy in Meridian is **not**:
- a metaphor borrowed from physics,
- a volatility indicator,
- a price prediction signal.

It is a **state variable** whose sole purpose is to determine
whether action itself is justified.

This document is the single source of truth for entropy semantics across:
- code,
- documentation,
- architecture,
- and constitutional rules.

---

## 2. Core Definition

In Meridian, entropy represents:

> **How unexplainable the current market behavior is relative to existing rules,
> assumptions, and strategies.**

Entropy measures **explanation failure**, not opportunity, direction, or return.

When entropy is high, acting on any signal becomes indistinguishable from noise.

---

## 3. Entropy as a State Variable

Entropy in Meridian has the following properties:

- **Stateful**: derived from recent market history
- **Non-directional**: independent of price up or down
- **Pre-strategic**: evaluated before any strategy logic
- **Regime-defining**: governs which actions are valid
- **Deterministic**: identical input produces identical output

Entropy does not answer *what to do*.  
It answers *whether doing anything makes sense*.

---

## 4. Components of Entropy (v0.1)

Meridian v0.1 defines entropy as a **composite of two independent dimensions**.

### 4.1 Entropy of Amplitude (EA)

EA captures **magnitude instability**.

It reflects situations where:
- price changes exceed historical scale,
- return dispersion expands abruptly,
- movement size violates model expectations.

EA asks:

> *Is the size of recent movement still within what our assumptions can explain?*

---

### 4.2 Entropy of Structure (ES)

ES captures **structural inconsistency**.

It reflects situations where:
- local coherence collapses,
- rolling windows diverge,
- simple explanatory structures (e.g. moving averages) fail.

ES asks:

> *Does recent market behavior still resemble a coherent, explainable structure?*

---

## 5. Normalization

Each entropy component is normalized to a closed interval:
EA_norm ∈ [0.0, 1.0]
ES_norm ∈ [0.0, 1.0]
Where:
- `0.0` represents a market state that is fully explainable
  under the current set of assumptions and models.
- `1.0` represents a state where those assumptions have
  completely lost explanatory power.

Intermediate values represent the **fraction of explanatory capacity
that has collapsed**, not probability or signal strength.

---

## 6. Composite Entropy

Composite entropy is defined as:
Entropy = max(EA_norm, ES_norm)
Explanation fails if **either magnitude or structure collapses**.
Averaging would mask failure in one dimension.

---

## 7. Representation

For auditability and determinism:
Entropy_pct = Entropy × 100
Entropy_bp  = round(Entropy × 10,000)
`Entropy_bp` is the canonical value used for decisions and logging.

---

## 8. Entropy Regimes

Entropy defines **Entropy Regimes**, which govern action validity.

| Regime | Entropy_bp | Meaning |
|---|---|---|
| Stable | < 3000 | Assumptions hold |
| Unstable | 3000–7999 | Assumptions weakening |
| Chaotic | ≥ 8000 | Explanation failure |
| Reformation | High → falling | Order reforming |

Regimes do not predict opportunity.
They define **the boundary of intelligence**.

---

## 9. Constitutional Freeze

Meridian enforces a non-negotiable rule:
If Entropy_bp ≥ CRITICAL_ENTROPY_BP:
Action = FREEZE (NoOp enforced)
Default v0.1:
CRITICAL_ENTROPY_BP = 9000
This rule cannot be overridden.

---

## 10. NoOp Semantics

**NoOp is a first-class action.**

- Not inactivity
- Not indecision
- Intentional refusal to act under entropy

NoOp preserves capital and optionality.

---

## 11. Determinism and Auditability

v0.1 guarantees:

- deterministic computation
- no learning
- reproducibility
- full auditability

Same history → same entropy → same regime → same action.

---

## 12. What Entropy Is Not

Entropy does **not**:
- predict prices
- optimize trades
- adapt strategies
- respond to news

It answers only:

> *Should we act at all?*

---

## 13. Evolution Path

- v0.1: Composite entropy, off-chain
- v0.2: On-chain entropy state
- v0.5+: Constrained agent planning
- v1.0: Integrated intelligence

---

## 14. Summary

- Entropy measures explanation failure
- It is a state variable, not a signal
- High entropy forbids action
- NoOp is enforced intelligence
- Survival precedes optimization

**Entropy defines the boundary of intelligence.**

---

*Intelligence Against Entropy.*
