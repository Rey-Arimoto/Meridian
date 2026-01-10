# PR25 — v0.4 Confidence Source Declaration Charter（Confidence の根拠カテゴリを固定）

**Status:** Scope Lock
**Target:** v0.4
**Dependencies:** PR20A (Representation), PR21 (Absence Semantics), PR24 (Evaluation Hook)

---

## Goal

This charter defines **which categories of information Confidence assessment may consider**, not how they are used.

It establishes the **source categories** from which Confidence can be evaluated, preventing future implementations from introducing arbitrary or hidden inputs.

**This charter does NOT define:**
- How sources are used
- How sources are combined
- What values sources produce
- How sources are prioritized

**This charter ONLY defines:**
- Which categories of information are valid sources
- What each source category represents conceptually
- Why each source category is relevant to structural robustness

---

## Definition: Source Category

A **source category** is a type of observable system state that provides information about the structural robustness of the current assessment.

Source categories are:
- Observable from logs and system state
- Relevant to judgment fragility assessment
- Independent conceptually (not mutually exclusive in practice)

---

## Source Categories

Confidence assessment may consider the following source categories:

### 1. Temporal Stability
**Concept:** How long has the current state persisted?

**Relevance to Structural Robustness:**
- Recent state changes suggest fragile assessment
- Persistent state suggests stable assessment
- Recency of transitions affects judgment reliability

**Observable From:**
- Regime transition history
- State persistence duration
- Recent volatility events

---

### 2. Regime Persistence
**Concept:** How consistently has the current regime been maintained?

**Relevance to Structural Robustness:**
- Frequent regime oscillation suggests fragile boundaries
- Stable regime classification suggests robust assessment
- Regime boundary proximity affects judgment fragility

**Observable From:**
- Current regime classification
- Regime transition frequency
- Regime stability indicators

---

### 3. Signal Consistency
**Concept:** How stable are the observable signals supporting current assessment?

**Relevance to Structural Robustness:**
- Contradictory signals suggest uncertain assessment
- Aligned signals suggest robust assessment
- Signal volatility affects judgment reliability

**Observable From:**
- Entropy trends
- Moving average stability
- Overlay intervention frequency

---

### 4. Decision Continuity
**Concept:** How consistent have recent decisions been?

**Relevance to Structural Robustness:**
- Frequent decision reversals suggest fragile assessment
- Consistent decisions suggest stable assessment
- Action continuity affects judgment reliability

**Observable From:**
- Recent Intent sequence
- Recent base action sequence
- Overlay suppression frequency

---

### 5. Observation Completeness
**Concept:** How complete is the observable information available for assessment?

**Relevance to Structural Robustness:**
- Missing or incomplete observations suggest uncertain assessment
- Complete observations suggest robust assessment
- Data availability affects judgment reliability

**Observable From:**
- Tick history length
- Data quality indicators
- System initialization state

---

## Source Category Properties

All source categories must satisfy:

### Observable
- Obtained from logged system state
- Reproducible from execution logs
- No hidden or external inputs

### Deterministic
- Same log state → same source observation
- No randomness
- No network calls

### Auditable
- Source category usage logged when Confidence evaluated
- Operators can verify source observations from logs
- Source contribution traceable

---

## Non-Source Categories (Explicitly Excluded)

The following are **NOT** valid Confidence source categories:

### Prediction-Based Sources
- Future price predictions
- Outcome probabilities
- Success likelihood estimates

**Why excluded:** Confidence assesses current judgment robustness, not future outcomes.

### External Sources
- Market sentiment data
- News feeds
- Social signals

**Why excluded:** Confidence must be reproducible from execution logs only.

### Optimization-Based Sources
- Backtest performance
- Parameter tuning results
- Historical win rates

**Why excluded:** Confidence assesses current structural state, not historical optimization.

### Subjective Sources
- User preferences
- Manual overrides
- Operator intuition

**Why excluded:** Confidence must be deterministic and reproducible.

---

## Deferred (Explicitly NOT in This Charter)

**This charter does NOT define:**

### How Sources Are Used
- Which source categories are actually used → deferred
- How source observations are interpreted → deferred
- How source observations are combined → deferred
- How source categories are prioritized → deferred

### Source Evaluation Methods
- How to measure temporal stability → deferred
- How to assess regime persistence → deferred
- How to detect signal consistency → deferred
- How to evaluate decision continuity → deferred
- How to check observation completeness → deferred

### Source Values
- What values source observations produce → deferred
- What ranges source observations take → deferred
- What representations source observations use → deferred

### Source Influence
- How source observations affect confidence_value → deferred
- How source observations affect confidence_reason → deferred
- How Confidence affects action sizing → deferred

**Why defer?**

PR25 establishes **source category boundaries**. Implementation PRs (PR26+) will define how source categories are observed, used, and combined within these boundaries.

---

## Done Criteria

PR25 Confidence Source Declaration Charter is complete when:

1. **Source Categories Defined:** Five categories specified (Temporal Stability, Regime Persistence, Signal Consistency, Decision Continuity, Observation Completeness)
2. **Relevance Established:** Each category's connection to structural robustness explained
3. **Observable Requirement:** All sources derivable from logged system state
4. **Non-Source Categories:** Prediction, external, optimization, and subjective sources explicitly excluded
5. **Deferred Scope Explicit:** Usage, evaluation, values, and influence deferred to future PRs
6. **No Implementation Leakage:** No evaluation methods, values, or priorities specified

**This charter does NOT require implementation.**

Implementation will occur in PR26+ following this source category blueprint.

---

## Why Source Declaration Before Implementation?

### Without Source Declaration Charter:
- Implementation PRs can introduce arbitrary inputs (news, sentiment, backtest results)
- No clear boundary between valid and invalid sources
- Risk of non-deterministic or non-reproducible Confidence
- Difficult to verify source usage from logs

### With Source Declaration Charter:
- **PR25:** Establish valid source categories (observable, deterministic, auditable)
- **PR26+:** Implement source observation and usage within boundaries
- Clean separation between "what sources exist" and "how sources are used"
- Source category constraints enforced by design

**Valid sources must be declared before they can be used.**

---

## Architectural Guarantee: Determinism from Logs

All source categories satisfy the **Log Reproducibility Guarantee**:

> Given the same execution log, Confidence assessment produces the same result.

This guarantee requires:
- No external data (news, sentiment, etc.)
- No network calls
- No randomness
- No hidden state
- All source observations derivable from logged fields

**Confidence must be auditable from logs alone.**

---

**Meridian v0.4: Source Categories Declared, Usage Deferred**
