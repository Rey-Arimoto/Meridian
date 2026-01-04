# Entropy Specification

## Purpose

This document defines **what “Entropy” means in Meridian** and how it is used.

In Meridian, entropy is **not**:
- a volatility proxy
- a risk metric
- a statistical ornament

Entropy is the system’s **primary test of interpretability**.

If entropy is high, Meridian assumes that:

> **meaning has collapsed and action is no longer justified.**

---

## Design Principles

Meridian’s entropy model is built on four non-negotiable principles:

1. **Deterministic**  
   Given the same inputs, entropy must always evaluate to the same value.

2. **State-agnostic**  
   Entropy measures the environment, not the strategy.

3. **Composable**  
   Multiple entropy components can be combined without breaking interpretation.

4. **Action-invalidating**  
   Beyond a critical threshold, entropy forbids execution entirely.

---

## Why Entropy (Not Prediction)

Most systems attempt to predict outcomes.

Meridian instead asks:

> *Is there still a structure worth responding to?*

Entropy answers this question by measuring:
- loss of directional coherence
- collapse of sign consistency
- amplification of indistinguishable outcomes

When entropy is high, **correctness itself becomes undefined**.  
At that point, prediction is meaningless.

---

## Entropy Components

Meridian uses a **composite entropy** built from two orthogonal components.

---

### 1. Amplitude Entropy (EA)

**What it measures**  
The instability of price movement magnitude.

**Definition**
- Compute log returns over a rolling window
- Take the absolute value
- Measure dispersion (standard deviation)

**Interpretation**
- Low EA → movements have stable scale
- High EA → magnitude is erratic and unbounded

Amplitude entropy detects **structural turbulence**, not direction.

---

### 2. Sign Entropy (ES)

**What it measures**  
The loss of directional meaning.

**Definition**
- Observe the sign (+ / −) of returns
- Compute binary entropy of sign distribution
- Normalize to `[0, 1]`

**Interpretation**
- ES ≈ 0 → direction is consistent
- ES ≈ 1 → direction is indistinguishable from randomness

If sign entropy is high, **“up” and “down” no longer carry meaning**.

---

## Composite Entropy

Meridian combines amplitude and sign entropy into a single value:

E = wA * EA_norm + wS * ES_norm
Where:
- `EA_norm ∈ [0,1]`
- `ES_norm ∈ [0,1]`
- `wA + wS = 1`

**Default weights**
- `wA = 0.4`
- `wS = 0.6`

The system intentionally prioritizes **semantic collapse (sign entropy)**  
over raw turbulence.

---

## Normalization Strategy

### Sign Entropy
- Naturally normalized via information entropy
- No historical scaling required

### Amplitude Entropy
- Normalized using a rolling, robust min/max
- Percentile-based to avoid single-spike distortion
- Clipped defensively to preserve determinism

This ensures:
- comparability across environments
- resistance to regime-specific scale
- reproducible results

---

## Entropy Scale

Meridian represents entropy in two equivalent forms:

- **Percent**: `0.00 – 100.00`
- **Basis points (bp)**: `0 – 10000`

All execution logic compares **basis points**, never floats.  
This avoids threshold ambiguity.

---

## CRITICAL_ENTROPY

`CRITICAL_ENTROPY` defines the point at which action is **constitutionally forbidden**.

Example:
```text
CRITICAL_ENTROPY = 9000 bp  (90.00%)

When:
entropy_bp ≥ CRITICAL_ENTROPY

Meridian must:
	•	enter Freeze phase
	•	set target weight to zero
	•	record the reason
	•	refuse execution regardless of other signals

This rule has no override.

⸻

Entropy and NoOp

A NoOp triggered by entropy is not indecision.

It is an explicit conclusion that:

“The environment no longer supports meaningful action.”

Entropy-driven NoOp is always:
	•	intentional
	•	logged
	•	reproducible
	•	auditable

⸻

Entropy Is Not Optimized

Meridian does not tune entropy to improve returns.

Entropy thresholds are constitutional, not parameters.

Any system that weakens its entropy guard
in pursuit of performance
is considered to have lost semantic integrity.

⸻

Relationship to Future Agents

Future agent components may:
	•	explain entropy
	•	reason about its implications
	•	propose actions conditioned on it

They may never:
	•	override entropy thresholds
	•	suppress entropy-based freezes
	•	execute when entropy forbids action

Entropy remains the highest authority.

⸻

Summary

Entropy in Meridian is the system’s way of asking:

“Does the environment still mean something?”

When the answer is no,
Meridian does not guess, hedge, or hope.

It stops.
