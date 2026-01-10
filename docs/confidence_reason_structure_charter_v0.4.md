# PR27 — v0.4 Confidence Reason Structure Charter（Confidence Reason の"構造"だけを固定）

**Status:** Scope Lock
**Target:** v0.4
**Dependencies:** PR20A (Representation), PR21 (Absence Semantics), PR24A (Eval Hook), PR25 (Source Categories), PR26 (Observation Wiring)

---

## Goal

This charter defines **the structure of `confidence_reason`**, not how it is generated or what values it contains.

It establishes the **structural requirements** for Confidence reasoning explanations, ensuring they are auditable, reproducible, and human-readable.

**This charter does NOT define:**
- How reason text is generated
- What specific words or phrases appear in reasons
- How reasons are used for decisions
- Any numeric or categorical values within reasons

**This charter ONLY defines:**
- Required structural components
- Format specification
- Properties the structure must satisfy

---

## Definition: Structured Reason

**Structured Reason** = A human-readable text string with defined semantic components, formatted for auditability.

Unlike free-form text, structured reasons:
- Have required semantic sections
- Follow a consistent format
- Support automated parsing (if needed)
- Enable systematic auditing

---

## Required Components

Every `confidence_reason` (when present) must address these semantic categories:

### 1. Source
**Purpose:** Identify which observation category informed this assessment

**Relevance:** Links Confidence to PR25 source categories (Temporal Stability, Regime Persistence, Signal Consistency, Decision Continuity, Observation Completeness)

**Example structure:** `Source:<category>`

### 2. Stability
**Purpose:** Describe continuity of current state

**Relevance:** Temporal stability directly affects structural robustness (PR25 Temporal Stability category)

**Example structure:** `Stability:<description>`

### 3. Consistency
**Purpose:** Describe alignment of recent observations

**Relevance:** Signal/decision consistency affects assessment reliability (PR25 Signal Consistency, Decision Continuity categories)

**Example structure:** `Consistency:<description>`

### 4. Completeness
**Purpose:** Describe availability of observations

**Relevance:** Missing data affects confidence in assessment (PR25 Observation Completeness category)

**Example structure:** `Completeness:<description>`

---

## Format Specification

### Structure
`confidence_reason` must follow this format:

```
Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>
```

### Format Rules

1. **Component Order:** Source, Stability, Consistency, Completeness (fixed order)
2. **Separator:** Components separated by `; ` (semicolon + space)
3. **Component Format:** `<ComponentName>:<description>`
4. **Single Line:** Entire reason on one line (no newlines)

### Examples (Structure Only - Content Not Prescribed)

**Full observation:**
```
Source:Regime Persistence; Stability:Current regime maintained; Consistency:Recent observations aligned; Completeness:All observations available
```

**Partial observation:**
```
Source:Temporal Stability; Stability:Recent state change; Consistency:Observations vary; Completeness:Some data missing
```

**Note:** These are **structural examples only**. Actual text content will be defined by implementation PRs.

---

## Required Properties

All `confidence_reason` values must satisfy:

### 1. Human-Readable
- Uses natural language descriptions
- Operator can understand reasoning without decoding
- No cryptic abbreviations or codes

### 2. Auditable
- Each component traceable to observation context (PR26)
- Reasoning reproducible from execution logs
- No hidden or external information

### 3. Deterministic
- Same observation context → same reason text
- No randomness in text generation
- Reproducible from logs

### 4. Non-Numeric
- Reason text contains descriptions, not numbers
- No scores, percentages, or measurements in reason
- Qualitative descriptions only

### 5. Optional (PR21 Compliance)
- Empty string `""` is always valid (undefined Confidence)
- Absence of reason does not break pipeline
- When present, must follow structure

---

## Non-Goals (Explicitly Deferred)

**This charter does NOT define:**

### Text Generation Logic
- How descriptions are created → deferred
- What words or phrases are used → deferred
- How observations map to descriptions → deferred
- Templates or text patterns → deferred

### Content Vocabulary
- Specific terms for stability states → deferred
- Specific phrases for consistency → deferred
- Specific descriptions for completeness → deferred
- Language style or tone → deferred

### Reason Usage
- How reasons are displayed to operators → deferred
- How reasons are parsed or analyzed → deferred
- How reasons affect decisions → deferred (never should)
- Reason-based alerting or monitoring → deferred

### Validation Rules
- Maximum length → deferred
- Allowed characters → deferred
- Forbidden words → deferred
- Format validation enforcement → deferred

**Why defer?**

PR27 establishes **structural requirements**. Implementation PRs (PR28+) will define text generation logic and content within these structural constraints.

---

## Compatibility with PR21 Absence Semantics

### Undefined Confidence
When Confidence is undefined (`confidence_value = ""`):
- `confidence_reason = ""` (empty string)
- No structure required for empty string
- Pipeline continues normally

### Defined Confidence
When Confidence is defined (`confidence_value` contains assessment):
- `confidence_reason` must follow structure
- All four components required
- Format specification enforced

**Guarantee:** Structure requirement applies only when Confidence is evaluated, never when absent/undefined.

---

## Done Criteria

PR27 Confidence Reason Structure Charter is complete when:

1. **Components Defined:** Source, Stability, Consistency, Completeness specified
2. **Format Specified:** `<Name>:<text>; ` format documented
3. **Properties Established:** Human-readable, Auditable, Deterministic, Non-numeric, Optional
4. **Non-Goals Explicit:** Text generation, content vocabulary, usage, validation deferred
5. **PR21 Compatibility:** Absence semantics preserved (empty string always valid)
6. **No Implementation Leakage:** No text templates, phrases, or generation logic specified

**This charter does NOT require implementation.**

Implementation will occur in PR28+ following this structural blueprint.

---

## Why Structure Before Content?

### Without Structure Charter:
- Implementation PRs invent arbitrary reason formats
- Inconsistent reason text across different Confidence states
- Difficult to parse or audit programmatically
- No guarantee of semantic completeness

### With Structure Charter:
- **PR27:** Establish structural requirements (components, format, properties)
- **PR28+:** Implement text generation within structure
- Clean separation of "what sections exist" from "what text goes in them"
- Structural consistency guaranteed by design

**The structure must exist before we fill it with content.**

---

## Example: Structure vs. Content

**What PR27 defines (structure):**
```
Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>
```

**What PR27 does NOT define (content - examples only):**
```
Source:Regime Persistence; Stability:Regime stable for 10 ticks; ...
Source:Temporal Stability; Stability:Recent regime transition; ...
Source:Signal Consistency; Stability:Entropy volatile; ...
```

The actual phrases, words, and descriptions will be defined by implementation PRs, but the structure (four components, semicolon-separated, specific order) is fixed by this charter.

---

**Meridian v0.4: Structure Precedes Content**
