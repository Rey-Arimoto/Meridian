# PR20 — v0.4 Confidence Representation Charter（Confidence の"表現"だけを固定）

**Status:** Scope Lock
**Target:** v0.4
**Dependencies:** PR19A (Confidence seats reserved)

---

## Goal

This charter defines **how `confidence_value` is represented**, not how it is defined or used.

It establishes the **representation requirements** for the Confidence seat, enabling consistent interpretation across Agent, Reporting, and Validation layers.

**This charter does NOT define:**
- How Confidence is defined from observable state
- What specific values Confidence takes
- How Confidence is used in action sizing

**This charter ONLY defines:**
- What properties the representation must satisfy
- What characteristics enable architectural consistency
- What constraints preserve auditability

---

## Definition

**Representation** = The form in which `confidence_value` appears in logs and is interpreted by downstream layers.

The representation must support:
- Agent writing Confidence assessments
- Reporting analyzing Confidence distributions
- Validation checking Confidence integrity
- Operators auditing Confidence reasoning

---

## Seat Mapping

From PR18 Confidence Logging Charter:

| Column | Writer | Readers | Purpose |
|--------|--------|---------|---------|
| `confidence_value` | Agent (Layer A) | Reporting, Validation | Primary Confidence assessment |
| `confidence_reason` | Agent (Layer A) | Reporting, Validation | Human-readable explanation |

**Representation scope:** `confidence_value` only.

`confidence_reason` remains free-form text (human-readable explanation).

---

## Representation Goals

The representation must satisfy the following architectural requirements:

### 1. Interpretability
- Operators can understand Confidence assessment by reading log values
- Reporting can present Confidence without transformation
- Validation can check Confidence without interpretation ambiguity

### 2. Determinism
- Same structural robustness → same `confidence_value`
- No floating-point ambiguity in log interpretation
- Reproducible across log reads

### 3. Auditability
- `confidence_value` + `confidence_reason` together explain assessment
- Operators can verify Confidence reasoning from logs alone
- No hidden state or implicit assumptions

### 4. Compatibility
- v0.3 logs (without Confidence columns) continue to work
- v0.4 logs (with Confidence undefined) continue to work
- v0.4+ logs (with Confidence defined) enable full analysis

### 5. Symmetry with Intent
- Intent uses categorical values (`SEEK`, `DEFEND`, `PAUSE`, etc.)
- Confidence representation should align with Intent's clarity and directness
- Both should support cross-tabulation and distribution analysis

---

## Representation Candidates: Requirements

The representation must support:

### Clarity Over Precision
- Confidence represents structural robustness assessment
- Excessive granularity suggests false precision
- Representation should match decision granularity

### Categorical Interpretation
- Reporting analyzes Confidence distributions
- Validation checks Confidence integrity
- Operators review Confidence reasoning
- All layers benefit from clear boundaries

### Human-Readable Form
- `confidence_value` readable in CSV without transformation
- Operators can grep logs for specific Confidence states
- No decoding or lookup tables required

### Extensibility
- Future PRs may refine Confidence assessment
- Representation should accommodate evolution without breaking compatibility
- Clear migration path if representation changes

---

## Compatibility Strategy

### v0.3 Logs (No Confidence Columns)
- Pipeline continues processing
- Reporting skips Confidence analysis
- Validation skips Confidence checks

### v0.4 Logs (Confidence Undefined)
- `confidence_value = ""` (empty string)
- Pipeline continues processing
- Reporting skips Confidence analysis
- Validation treats as optional

### v0.4+ Logs (Confidence Defined)
- `confidence_value` contains representation-compliant value
- Reporting analyzes Confidence distribution
- Validation checks Confidence integrity
- Operators audit Confidence reasoning

**Backward Compatibility Guarantee:** v0.4+ pipeline processes v0.3 and v0.4-undefined logs without modification.

---

## Deferred (Explicitly NOT in This Charter)

**This charter does NOT define:**

### How Confidence is Defined
- Input signals (entropy, regime, history, etc.) → deferred
- Definition rules → deferred
- Assessment criteria → deferred
- Boundary conditions → deferred

### What Specific Values Exist
- Enumeration of possible values → deferred
- Meaning of each value → deferred
- Transition rules between values → deferred
- Default or initial values → deferred

### How Confidence is Used
- Action sizing modulation → deferred
- Overlay parameter selection → deferred
- Continuation vs. pause decisions → deferred
- Risk exposure adjustment → deferred

**Why defer?**

PR20 establishes **representation requirements**. Implementation PRs (PR21+) will define definition rules, values, and usage within these requirements.

---

## Done Criteria

PR20 Confidence Representation Charter is complete when:

1. **Representation Goals Defined:** Interpretability, Determinism, Auditability, Compatibility, Symmetry
2. **Requirements Specified:** Clarity, Categorical Interpretation, Human-Readable Form, Extensibility
3. **Compatibility Strategy:** v0.3/v0.4/v0.4+ migration documented
4. **Deferred Scope Explicit:** Definition rules, specific values, and usage deferred to future PRs
5. **Symmetry with Intent:** Confidence representation aligns with Intent's categorical clarity
6. **No Implementation Leakage:** No specific values or definition rules specified

**This charter does NOT require implementation.**

Implementation will occur in PR21+ following this representation blueprint.

---

## Why Representation Before Implementation?

### Without Representation Charter:
- Implementation PRs forced to decide representation + definition rules + usage simultaneously
- Risk of representation choices driven by definition convenience
- No clear boundary between "how it's represented" and "how it's defined"
- Difficult to validate representation consistency

### With Representation Charter:
- **PR20:** Establish representation requirements (form, properties, goals)
- **PR21+:** Implement definition rules (fill the representation with values)
- Clean separation of representation design from definition rules
- Representation choices driven by architectural needs, not implementation convenience

**The representation must serve the architecture, not the definition rules.**

---

**Meridian v0.4: Representation Precedes Implementation**
