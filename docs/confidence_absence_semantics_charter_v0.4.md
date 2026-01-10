# PR21 — v0.4 Confidence Absence Semantics Charter（Confidence が"ない"時の意味論）

**Status:** Scope Lock
**Target:** v0.4
**Dependencies:** PR20A (Confidence representation locked)

---

## Goal

This charter defines **what it means when Confidence is undefined or absent**, not what values Confidence takes when present.

It establishes the **semantics of Confidence absence** across Agent, Reporting, and Validation layers.

**This charter does NOT define:**
- What Confidence values exist when present
- How Confidence is defined from observable state
- When Confidence transitions from absent to present

**This charter ONLY defines:**
- What "undefined" means
- What "absent" means
- How the system behaves when Confidence not evaluated
- Guarantees when Confidence unavailable

---

## Definition: Undefined vs. Absent

### Undefined Confidence
**Meaning:** Confidence seat exists in log, but value not evaluated.

**Log representation:**
- `confidence_value = ""` (empty string)
- `confidence_reason = ""` (empty string)

**Semantic:** Agent decided not to evaluate Confidence for this tick.

### Absent Confidence
**Meaning:** Confidence columns do not exist in log.

**Log representation:**
- No `confidence_value` column
- No `confidence_reason` column

**Semantic:** Log created before v0.4 (backward compatibility).

---

## Semantic Requirements

Confidence absence must satisfy the following guarantees:

### 1. Non-Influential
When Confidence undefined or absent:
- Agent behavior unchanged from Confidence-unaware operation
- Intent selection proceeds normally
- Action sizing proceeds normally
- Safety overlay proceeds normally
- No implicit substitution or assumption

**Guarantee:** Absence = no influence.

### 2. Neutral
When Confidence undefined or absent:
- No warnings, no errors, no alerts
- Pipeline continues processing
- Reports generate successfully
- Validation passes successfully

**Guarantee:** Absence = safe to ignore.

### 3. Auditable
When Confidence undefined:
- Agent may log reason for non-evaluation in `confidence_reason`
- Operators can distinguish "not evaluated" from "evaluated as X"
- Absence is explicit, never ambiguous

**Guarantee:** Absence = visible and intentional.

### 4. Fail-Safe
When Confidence absent or undefined:
- Agent never crashes
- Reporting never crashes
- Validation never crashes
- Pipeline never fails

**Guarantee:** Absence = never breaks system.

---

## Layer Responsibilities

### Agent (Layer A)

**When Confidence not evaluated:**
- Write `confidence_value = ""`
- Write `confidence_reason = ""` OR explanatory text (e.g., "Confidence not evaluated this tick")
- Proceed with Intent-based decision as normal
- No implicit Confidence assumption

**Agent MUST NOT:**
- Crash when Confidence not evaluated
- Make action sizing decisions based on absent Confidence
- Infer or substitute Confidence values

### Reporting (Layer B)

**When Confidence undefined or absent:**
- Skip Confidence distribution analysis
- Skip Confidence × Intent cross-tabulation
- Generate all other reports normally
- Include note: "Confidence analysis unavailable (not evaluated)"

**Reporting MUST NOT:**
- Crash when Confidence columns missing
- Crash when Confidence values empty
- Infer or substitute Confidence values
- Report zero/null/missing as a Confidence value

### Validation (Layer C)

**When Confidence undefined or absent:**
- Skip Confidence integrity checks
- Skip Confidence reasoning validation
- Run all other validations normally
- Mark Confidence checks as "not applicable"

**Validation MUST NOT:**
- Fail when Confidence columns missing
- Fail when Confidence values empty
- Infer or substitute Confidence values
- Treat absence as validation failure

---

## Compatibility Strategy

### v0.3 Logs (Confidence Absent)
- Columns: No `confidence_value`, no `confidence_reason`
- Agent: Not applicable (v0.3 agent)
- Reporting: Skip Confidence analysis, generate all other reports
- Validation: Skip Confidence checks, run all other validations
- Pipeline: Continue processing

### v0.4 Logs (Confidence Undefined)
- Columns: `confidence_value = ""`, `confidence_reason = ""`
- Agent: Confidence not evaluated this tick
- Reporting: Skip Confidence analysis, generate all other reports
- Validation: Skip Confidence checks, run all other validations
- Pipeline: Continue processing

### v0.4+ Logs (Confidence Present)
- Columns: `confidence_value = <value>`, `confidence_reason = <text>`
- Agent: Confidence evaluated and logged
- Reporting: Analyze Confidence distribution
- Validation: Check Confidence integrity
- Pipeline: Full Confidence-aware operation

**Backward Compatibility Guarantee:**
- v0.4+ pipeline processes v0.3 logs without Confidence columns
- v0.4+ pipeline processes v0.4 logs with undefined Confidence
- Absence never breaks pipeline

---

## Architectural Symmetry: Intent vs. Confidence

| First-Class Citizen | Present | Undefined | Absent |
|---------------------|---------|-----------|--------|
| **Intent** | `intent_primary = "SEEK"` | Not possible (Intent always evaluated) | v0.2 logs (pre-Intent) |
| **Confidence** | `confidence_value = <value>` | `confidence_value = ""` | v0.3 logs (pre-Confidence) |

**Key Difference:**
- Intent: Always evaluated (constitutional requirement)
- Confidence: May be undefined (evaluation optional in v0.4)

**Why?**
- Intent drives decisions (required for operation)
- Confidence modulates execution (optional enhancement)

---

## Deferred (Explicitly NOT in This Charter)

**This charter does NOT define:**

### When Confidence is Evaluated
- Under what conditions Agent evaluates Confidence → deferred
- When Confidence transitions from undefined to present → deferred
- Triggers for Confidence evaluation → deferred

### What Confidence Values Exist
- Enumeration of possible values → deferred
- Meaning of each value → deferred
- Representation of present Confidence → deferred (see PR20)

### How Confidence is Used
- Action sizing modulation when Confidence present → deferred
- Overlay parameter selection when Confidence present → deferred
- Decision logic when Confidence present → deferred

**Why defer?**

PR21 establishes **absence semantics**. Implementation PRs (PR22+) will define when Confidence is evaluated and what values it takes.

---

## Done Criteria

PR21 Confidence Absence Semantics Charter is complete when:

1. **Undefined vs. Absent Distinction:** Clear definitions for both states
2. **Semantic Requirements:** Non-Influential, Neutral, Auditable, Fail-Safe guarantees defined
3. **Layer Responsibilities:** Agent, Reporting, Validation behavior when Confidence absent
4. **Compatibility Strategy:** v0.3/v0.4/v0.4+ absence handling documented
5. **Symmetry with Intent:** Confidence absence semantics align with Intent's always-present requirement
6. **Deferred Scope Explicit:** Evaluation triggers, values, and usage deferred to future PRs

**This charter does NOT require implementation.**

Implementation will occur in PR22+ following this semantic blueprint.

---

## Why Absence Semantics Matter

### Without Absence Semantics Charter:
- Unclear whether undefined Confidence should crash or continue
- No guarantee that v0.3 logs continue working
- Implementation PRs must decide absence behavior + evaluation logic simultaneously
- Risk of implicit substitution (treating absence as "low confidence")

### With Absence Semantics Charter:
- **PR21:** Establish absence guarantees (safe, neutral, non-influential)
- **PR22+:** Implement evaluation logic (when and how Confidence evaluated)
- Clean separation of "what absence means" from "when presence occurs"
- v0.3 compatibility guaranteed by design

**Absence must be safe before presence can be meaningful.**

---

## Philosophical Foundation

Confidence is an **optional enhancement**, not a constitutional requirement.

The system must operate correctly when Confidence:
- Not present in codebase
- Not evaluated this tick
- Not available in historical logs

This is fundamentally different from Intent, which is constitutionally required for every decision.

**Confidence absence = system continues unchanged.**
**Intent absence = system cannot operate.**

This asymmetry is intentional and architectural.

---

**Meridian v0.4: Safe Absence Enables Meaningful Presence**
