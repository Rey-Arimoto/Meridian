# Meridian

**Intelligence Against Entropy**

Meridian is an entropy-native intelligence layer for markets.  
It exists to preserve, grow, and protect capital when markets become unexplainable.

---

## What is Meridian?

Meridian is **not a trading bot** and **not a price prediction system**.

It is a system that continuously measures **market entropy** —  
how explainable the current market state is relative to existing rules, assumptions, and strategies —  
and decides **whether action itself is justified**.

When explanation collapses, Meridian does not attempt to trade.
It refuses to act.

This refusal is not passive.
It is enforced intelligence.

---

## Alpha: Intelligence Against Entropy

Meridian does not seek alpha by predicting prices better.

It extracts alpha by **measuring entropy** and **aligning action with market explainability**.

Markets are classified into **Entropy Regimes**:

- **Stable Regime** — low entropy, assumptions hold
- **Unstable Regime** — entropy rising, assumptions weakening
- **Chaotic Regime** — high entropy, behavior unexplainable
- **Reformation Regime** — entropy declining, new order forming

All strategies are subordinated to the current Entropy Regime.

### The NoOp Premium

Meridian’s most distinctive alpha source is **NoOp**.

In Chaotic Regimes:
- signals lose meaning,
- correlations spike,
- forced action destroys capital.

Meridian treats **not acting** as a first-class strategic action, enforced by constitutional rules.

Avoiding catastrophic loss during chaos — and re-entering early during reformation —  
creates a compounding advantage others cannot replicate.

👉 For a detailed explanation, see [docs/alpha.md](docs/alpha.md).

---

## Why Entropy?

Traditional systems assume markets are always interpretable.

Meridian rejects this assumption.

Entropy answers a different question:

> *Is the market still explainable by what we think we know?*

When the answer is no, prediction is meaningless.
Meridian stops.

Entropy in Meridian is a **state variable**, not a signal.

👉 See [docs/entropy_spec.md](docs/entropy_spec.md).

---

## Architecture (v0.1)

Meridian v0.1 is intentionally simple and conservative.

- Composite entropy calculation (volatility + structural dispersion)
- Entropy expressed in **basis points (bp)**
- Constitutional freeze above critical entropy
- Explicit NoOp / Freeze behavior
- Deterministic, explainable decisions
- Full CSV logging (every decision is auditable)

There is no learning, no optimization, and no hidden behavior.

Stability precedes intelligence.

---

## Development Roadmap

**Phase 1 — v0.1: Entropy Constitutional Core**
- Entropy measurement
- Freeze enforcement
- Deterministic paper trading
- Immutable decision logs

**Phase 2 — v0.2: State Objectization (Sui)**
- On-chain MeridianState
- Entropy Regime as persistent state
- Deterministic state transitions

**Phase 3 — v0.5–0.8: Agent Core (Constrained)**
- Plan / Act separation
- Suggestions without execution authority
- Hard constitutional guards remain dominant

**Phase 4 — v1.0: Integrated Intelligence**
- Multi-market, multi-strategy
- Regime-driven strategy selection
- Self-diagnosis and automatic contraction

---

## Design Principles (Constitution)

- **Regime overrides strategy**
- **NoOp is a valid action**
- **High entropy forces non-action**
- **Determinism before learning**
- **Survival before profit**

These rules are non-negotiable.

---

## Documentation

- Alpha model: [docs/alpha.md](docs/alpha.md)
- Entropy specification: [docs/entropy_spec.md](docs/entropy_spec.md)
- Design decisions (ADR): [docs/decisions.md](docs/decisions.md)
- Vision: [docs/vision.md](docs/vision.md)
- v0.3 Intent Charter: [docs/intent_charter_v0.3.md](docs/intent_charter_v0.3.md)
- v0.4 Confidence Charter: [docs/confidence_charter_v0.4.md](docs/confidence_charter_v0.4.md)
- v0.4 Confidence Logging Charter: [docs/confidence_logging_charter_v0.4.md](docs/confidence_logging_charter_v0.4.md)
- v0.4 Confidence Representation Charter: [docs/confidence_representation_charter_v0.4.md](docs/confidence_representation_charter_v0.4.md)
- v0.4 Confidence Absence Semantics Charter: [docs/confidence_absence_semantics_charter_v0.4.md](docs/confidence_absence_semantics_charter_v0.4.md)
- v0.4 Confidence Source Declaration Charter: [docs/confidence_source_charter_v0.4.md](docs/confidence_source_charter_v0.4.md)
- v0.4 Confidence Reason Structure Charter: [docs/confidence_reason_structure_charter_v0.4.md](docs/confidence_reason_structure_charter_v0.4.md)
- v0.4 Confidence Reason Vocabulary Charter: [docs/confidence_reason_vocabulary_charter_v0.4.md](docs/confidence_reason_vocabulary_charter_v0.4.md)
- v0.4 Confidence Release Declaration: [docs/v0.4_confidence_release_declaration.md](docs/v0.4_confidence_release_declaration.md)
- v0.5 Intelligence Boundary Charter: [docs/v0.5_intelligence_boundary_charter.md](docs/v0.5_intelligence_boundary_charter.md)
- v0.5 Intelligence Input Contract Charter: [docs/v0.5_intelligence_input_contract_charter.md](docs/v0.5_intelligence_input_contract_charter.md)
- v0.5 Intelligence Decision Record Charter: [docs/v0.5_intelligence_decision_record_charter.md](docs/v0.5_intelligence_decision_record_charter.md)

---

## Why Now

Markets are becoming:
- faster,
- more composable,
- more reflexive,
- more chaotic.

On-chain systems amplify entropy instead of absorbing it.

In such an environment, **entropy-aware intelligence is no longer optional infrastructure**.

---

## Why It Is Hard to Copy

- Entropy is not a price signal
- NoOp must be enforced against incentives
- Regime must dominate strategy
- Constitutional freezes cannot be overridden
- Loss avoidance is culturally undervalued but mathematically dominant

---

## Validation (v0.2)

Meridian v0.2 includes constitutional compliance validation scripts that verify:
- Hysteresis stability (regime transitions don't oscillate)
- Matrix invariants (Act forbidden in volatile/transition regimes)
- Policy decision integrity (regime-first enforcement)
- Log schema compliance (decision audit trail)

Run validations:
```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr4a_hysteresis_stability.py
python3 python/validation/pr4a_matrix_invariants.py
python3 python/validation/pr4a_policy_decision_invariants.py
python3 python/validation/pr4a_log_schema_smoke.py
```

All scripts exit 0 on PASS, 1 on FAIL.

---

## Validation (v0.5)

Meridian v0.5 includes Intelligence Layer compliance validation that verifies:
- Input contract compliance (allowlist enforcement)
- Import ban detection (v0.4 builders/validators)
- Featurization ban detection (confidence_reason operations)
- Read-only consumption validation
- Decision Record immutability (no regeneration or post-hoc rationalization)
- v0.4 Confidence boundary protection (no erosion)
- Decision Engine v1 (mirror base-action, non-numeric, non-evaluative)
- Decision Engine v2 (rule overlay, regime-aware, non-numeric, non-evaluative)
- Decision Record wiring (v5_decision_* fields logged correctly)
- Decision Engine selector (v1/v2 switch, auditable)
- Decision Engine shadow mode (dual record logging for comparison)
- Decision Engine shadow diff logging (machine-readable comparison, non-evaluative)
- Decision diff semantics tagging (non-evaluative classification of divergence types)
- Shadow diff analytics export (daily summary aggregation for comparison analysis)
- Shadow diff report generator (human-readable Markdown/HTML reports, non-evaluative)
- Shadow diff report indexer (archive organization and TOC generation, non-evaluative)
- Daily shadow diff pipeline (orchestrates PR47→PR48A→PR48B in sequence, non-evaluative)
- Daily shadow diff pipeline scheduler (GitHub Actions + launchd templates for automated execution)
- Weekly shadow diff digest (7-day summary, observational only, READ-ONLY)

Run validations:
```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr37_intelligence_input_contract_guard_smoke.py
python3 python/validation/pr39_intelligence_decision_record_compliance_smoke.py
python3 python/validation/pr40_intelligence_decision_engine_v1_smoke.py
python3 python/validation/pr41_decision_record_wiring_smoke.py
python3 python/validation/pr41a_decision_record_wiring_consistency_smoke.py
python3 python/validation/pr42_intelligence_decision_engine_v2_smoke.py
python3 python/validation/pr43_decision_engine_selector_wiring_smoke.py
python3 python/validation/pr44_decision_engine_shadow_mode_smoke.py
python3 python/validation/pr45_decision_engine_shadow_diff_smoke.py
python3 python/validation/pr46_decision_diff_semantics_smoke.py
python3 python/validation/pr47_shadow_diff_analytics_export_smoke.py
python3 python/validation/pr48a_shadow_diff_report_generator_smoke.py
python3 python/validation/pr48b_shadow_diff_report_indexer_smoke.py
python3 python/validation/pr49_daily_shadow_diff_pipeline_smoke.py
python3 python/validation/pr50_scheduler_assets_smoke.py
python3 python/validation/pr51_weekly_shadow_diff_digest_smoke.py
```

All scripts exit 0 (warning-only, never fails).

**Analytics Tools:**

Generate human-readable reports from PR47 analytics:
```bash
cd ~/Meridian
source .venv/bin/activate

# Generate Markdown/HTML reports from PR47 outputs
python3 python/analytics/pr48a_shadow_diff_report_generator.py \
  --in_dir analytics_out \
  --out_dir reports

# Format options: md, html, or both (default: both)
python3 python/analytics/pr48a_shadow_diff_report_generator.py \
  --in_dir analytics_out \
  --out_dir reports \
  --format md

# Filter by specific day
python3 python/analytics/pr48a_shadow_diff_report_generator.py \
  --in_dir analytics_out \
  --out_dir reports \
  --day 2026-01-10

# Archive reports and generate index
python3 python/analytics/pr48b_shadow_diff_report_indexer.py \
  --reports_dir reports

# Archive specific day only
python3 python/analytics/pr48b_shadow_diff_report_indexer.py \
  --reports_dir reports \
  --day 2026-01-10

# Complete pipeline (PR47→PR48A→PR48B)
python3 python/analytics/pr49_daily_shadow_diff_pipeline.py \
  --log_path logs/meridian_log.csv \
  --analytics_out_dir analytics_out \
  --reports_dir reports

# Rebuild specific day
python3 python/analytics/pr49_daily_shadow_diff_pipeline.py \
  --log_path logs/meridian_log.csv \
  --day 2026-01-10 \
  --analytics_out_dir analytics_out \
  --reports_dir reports \
  --format both

# Generate weekly digest (auto end_day from latest available report)
python3 python/analytics/pr51_weekly_shadow_diff_digest.py \
  --reports_dir reports \
  --out_dir reports/weekly \
  --format both

# Generate weekly digest ending on specific day
python3 python/analytics/pr51_weekly_shadow_diff_digest.py \
  --reports_dir reports \
  --end_day 2026-01-11 \
  --days 7 \
  --out_dir reports/weekly \
  --format both
```

**Archive Structure:**

After running the indexer, reports are organized as:
```
reports/
  index.md          # Human-readable table of contents
  index.json        # Machine-readable registry
  _archive/
    2026-01-10/
      shadow_diff_report.md
      shadow_diff_report.html
      meta.json
    2026-01-11/
      ...
```

---

## Daily Pipeline Scheduling (PR50)

Meridian v0.5 provides two options for scheduling the daily shadow diff pipeline (PR49):

### Option 1: GitHub Actions (Recommended for CI/CD)

A GitHub Actions workflow is provided for daily automated execution:

**Location:** `.github/workflows/pr50_daily_shadow_diff_pipeline.yml`

**Schedule:** Daily at 00:30 UTC (09:30 JST)

**Features:**
- Scheduled execution via cron
- Manual execution via workflow_dispatch (optional day parameter)
- Artifact upload (analytics_out, reports) with 90-day retention
- Warning-only (never fails workflow)
- Constitutional constraints enforced

**Manual Trigger:**
- Go to Actions tab in GitHub
- Select "PR50 Daily Shadow Diff Pipeline"
- Click "Run workflow"
- Optional: Specify day (YYYY-MM-DD) and log path

### Option 2: Local Scheduling (macOS launchd)

Templates for local scheduling on macOS are provided:

**Location:** `scripts/com.meridian.pr49.daily.plist` (template)

**Installation:**
```bash
cd ~/Meridian

# Option A: Use helper script (recommended)
bash scripts/pr50_launchd_install.sh

# Option B: Manual installation
# 1. Customize the plist template (replace /path/to/meridian with actual path)
# 2. Copy to ~/Library/LaunchAgents/
# 3. Load with launchctl
cp scripts/com.meridian.pr49.daily.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.meridian.pr49.daily.plist
```

**Schedule:** Daily at 00:30 local time

**Management:**
```bash
# Start manually
launchctl start com.meridian.pr49.daily

# Unload
launchctl unload ~/Library/LaunchAgents/com.meridian.pr49.daily.plist

# Remove
rm ~/Library/LaunchAgents/com.meridian.pr49.daily.plist
```

**Logs:**
- stdout: `logs/pr49_daily_stdout.log`
- stderr: `logs/pr49_daily_stderr.log`

**Note:** Customize paths in the plist template before installation. The helper script does this automatically.

---

## Canonical Report Generation (PR8B + PR9A)

The following command is the **canonical and supported way** to generate all Meridian reports from an execution log.

It enforces data integrity gates and produces all reporting artifacts in a single run.

**Execution Command:**

```bash
cd ~/Meridian && source .venv/bin/activate && \
python3 python/tools/pr8b_integrity_gate_runner.py meridian_log.csv \
  --prefix meridian \
  --out-dir artifacts
```

**Generated Artifacts**

If the integrity gate passes, the following files will be generated in the `artifacts` directory:

- `meridian_health.md` — Data health and integrity report (PR8A)
- `meridian_investor_report.md` — Investor-facing summary (PR7A)
- `meridian_performance.md` — Performance and risk summary (PR9A)
- `meridian_dashboard.html` — Interactive dashboard (PR7C)
- `meridian_timeline.png` — Timeline visualization (PR7B)
- `meridian_overlay_hist.png` — Overlay distribution (PR7B)
- `meridian_regime_dist.png` — Regime distribution (PR7B)

**Notes**

- Reports are generated only if all integrity checks pass.
- No assumptions are made about tick frequency, capital scaling, or annualization.
- This command is read-only and does not modify logs or trading logic.

---

## v0.2 Log Requirements (PR13B)

**IMPORTANT:** Meridian v0.2 requires all execution logs to include the following columns:

- `regime` — Constitutional regime classification (e.g., `stable_range`, `emerging_trend`, `volatile_noise`, `REGIME_TRANSITION`)
- `base_action` — Base policy decision before overlay (e.g., `HOLD`, `SHIFT`, `PAUSE`)
- `decision_reason` — Human-readable decision explanation

**What happens if these columns are missing:**

1. **At agent startup** — The agent will detect pre-v0.2 logs and refuse to start. You must delete or rename the old log file.
2. **At runtime** — If the agent tries to write a row without these columns (code bug), it will exit immediately with a fatal error.
3. **At pipeline time** — PR8B integrity gate will reject logs missing these columns with a fail-closed error.

These guards ensure that v0.2 constitutional decision logs are **auditable, complete, and pipeline-compatible by design**.

---

## Production Workflow (PR10)

**Standard operating procedure for real log processing:**

1. **Put logs in `logs/`** — Place execution logs in the `logs/` directory
2. **Run canonical command** — Use `pr10_run_pipeline.py` for timestamped isolation
3. **Artifacts are time-stamped** — All outputs go to `artifacts/_<timestamp>/`

```bash
cd ~/Meridian && source .venv/bin/activate && \
python3 python/tools/pr10_run_pipeline.py \
  --log logs/meridian_log_latest.csv \
  --prefix meridian
```

This pipeline:
- Copies the input log to `artifacts/_<timestamp>/input_log.csv` (fixed copy)
- Runs PR8B integrity gate on the fixed copy
- Generates all reports and visualizations
- Creates `index.md` as entry point for all artifacts
- Isolates all outputs in the timestamped directory
- Prevents log mixing, overwrite, and collision

**Reading artifacts:**
- Artifacts include `index.md` (entry point).
- Open `index.md` first for recommended reading order.

---

## Validation (v0.6)

Meridian v0.6 introduces the **Interpretation Layer**: mapping observations to structural meaning types without evaluation or judgment.

### v0.6 Philosophy: Observation → Interpretation

v0.5 completed observation (what happened).
v0.6 maps observation to meaning type (what structure this represents).
That is not judgment, but structural language.

### Interpretation ≠ Evaluation

- **Interpretation** = Structural Mapping (what structure)
- **Interpretation** ≠ Evaluation (good/bad judgment)
- **Interpretation** ≠ Recommendation (what should be done)

### v0.6 Schema (PR60)

Interpretation records use `v6_` prefix:

- `v6_meaning_mode`: ON | OFF
- `v6_meaning_status`: AVAILABLE | UNAVAILABLE
- `v6_meaning_tag`: Structural meaning type (non-evaluative)
- `v6_meaning_summary`: Non-evaluative explanation
- `v6_meaning_basis`: Array of observation field names used

### v0.6 Interpretation Engine v1 (PR61)

**Interpretation v1 = Static Structural Mapping**

Engine v1 maps observations to meaning types using static rules:

**Meaning Tags (v1 Fixed Set):**
- `OVERLAY_OBSERVED`: Overlay pattern detected
- `ALIGNMENT_STABLE`: Actions aligned with shadow present
- `DIVERGENCE_WITHOUT_CLASS`: Divergence observed but type unclear
- `SHADOW_ABSENT_OR_UNAVAILABLE`: Shadow data not available
- `OBSERVATION_INSUFFICIENT`: Required fields missing
- `UNCLASSIFIED`: Cannot classify with current rules

**Note:** UNKNOWN/UNCLASSIFIED are normal outcomes (not failures).

**Static Mapping Examples:**
- `semantics_tag == DIVERGED_RULE_OVERLAY` → `OVERLAY_OBSERVED`
- `diff_status == ALIGNED` + shadow present → `ALIGNMENT_STABLE`
- `diff_status == DIVERGED` + semantics unclear → `DIVERGENCE_WITHOUT_CLASS`

This is not "getting smarter". This is structural language for what we can understand.

### v0.6 Interpretation Output Wiring (PR62)

**Purpose:** Wire v6 interpretation data into reports and digest (READ-ONLY, display only).

**Changes (PR62):**

1. **PR48A Daily Reports** — Add "Interpretation (v0.6)" section
   - Displays `meaning_status_counts` distribution
   - Displays `meaning_tag_counts` distribution
   - Supports degraded mode when v6 data absent

2. **PR51 Weekly Digest** — Add meaning aggregation
   - Aggregates `meaning_status_counts` across 7 days
   - Aggregates `meaning_tag_counts` across 7 days
   - Supports degraded mode when v6 data absent

**READ-ONLY Guarantee:**
- No execution logic changes
- No decision flow changes
- Display/presentation layer only
- Existing v0.5 sections unchanged

### v0.6 Interpretation Engine v2 (PR63)

**Interpretation v2 = Compositional Structural Mapping**

v1 was a point (single label). v2 is a surface (compositional decomposition).

**v2 Philosophy:**

v2 increases interpretation resolution by decomposing observations into multiple structural elements:

1. **Primary Meaning** — Main structural type (same as v1)
2. **Factors** — Structural elements present (e.g., REGIME_PRESENT, INTENT_PRESENT)
3. **Signals** — Concrete observational signs (e.g., DIFF_STATUS_ALIGNED, SEMANTICS_RULE_OVERLAY)

**Processing Order (v2):**

```
Observation → Signals → Factors → Primary Meaning → Summary
```

First decompose, then compose. This is structural language without loss.

**v2 Extended Output:**

```json
{
  "v6_meaning_tag": "OVERLAY_OBSERVED",
  "v6_meaning_factors": ["REGIME_PRESENT", "INTENT_PRESENT", "SHADOW_PRESENT"],
  "v6_meaning_signals": ["DIFF_STATUS_DIVERGED", "SEMANTICS_RULE_OVERLAY"],
  "v6_meaning_summary": "overlay pattern observed in decision divergence, with regime context.",
  "v6_meaning_basis": ["v5_decision_diff_status", "v5_decision_diff_semantics_tag", "regime"]
}
```

**Factors (Structural Elements):**
- `REGIME_PRESENT` / `REGIME_TRANSITION_PRESENT`
- `INTENT_PRESENT` / `INTENT_ABSENT`
- `SEMANTICS_AVAILABLE` / `SEMANTICS_UNAVAILABLE`
- `SHADOW_PRESENT` / `SHADOW_ABSENT`

**Signals (Observational Signs):**
- `DIFF_STATUS_ALIGNED` / `DIFF_STATUS_DIVERGED` / `DIFF_STATUS_UNAVAILABLE`
- `SEMANTICS_RULE_OVERLAY` / `SEMANTICS_ALIGNED` / `SEMANTICS_UNKNOWN`
- `PAIR_IDENTIFIED` / `PAIR_UNKNOWN`

**Important:**
- v2 does NOT lose information vs v1
- v2 does NOT evaluate or judge
- v2 is decomposition without optimization
- UNKNOWN/UNCLASSIFIED remain normal outcomes

This is not "getting smarter". This is structure without compression.

### v0.6 Interpretation Analytics (PR64)

**Purpose:** Observe meaning as landscape (distribution, transition).

PR61/PR63 create and decompose meaning (point, structure).
PR64 observes meaning distribution and transitions over time.

**Philosophy:**

This is analysis, not optimization.
This is insight, not recommendation.

**Questions PR64 Answers:**
- Which meaning tags exist, how many?
- Which factors/signals appear, in what structure?
- How do meanings transition day-to-day?

**Questions PR64 Does NOT Answer:**
- Is this good or bad?
- Did it improve or degrade?
- What should be done?

**Outputs:**

1. **Meaning Distribution**
   - `meaning_tag_counts`: Distribution across primary meanings
   - `factor_counts`: Structural element distribution
   - `signal_counts`: Observational sign distribution

2. **Meaning Transitions**
   - `daily_distributions`: Per-day meaning distribution
   - `transitions`: Day-to-day meaning changes (observational only)

**Example Usage:**

```bash
python3 python/analytics/pr64_interpretation_analytics.py \
  --in_file interpretation_records.jsonl \
  --out_dir analytics_out \
  --format both
```

**Outputs:**
- `pr64_interpretation_analytics.json` (full analytics)
- `pr64_meaning_tag_distribution.csv` (tag counts)
- `pr64_factor_distribution.csv` (factor counts)
- `pr64_signal_distribution.csv` (signal counts)
- `pr64_daily_meaning_distribution.csv` (daily transitions)

**Important:**
- READ-ONLY: Only reads interpretation records
- Non-evaluative: Only counts and distributions, no judgment
- No action changes: Pure observational visibility

This observes "what structure exists" and "how structure changes".
No evaluation. No recommendation.

### Constitutional Constraints (v0.6)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Observation-bound**: Only uses observation fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis

### Run Validations (v0.6)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr60_interpretation_schema_smoke.py
python3 python/validation/pr61_interpretation_engine_v1_smoke.py
python3 python/validation/pr62_interpretation_report_integration_smoke.py
python3 python/validation/pr63_interpretation_engine_v2_smoke.py
python3 python/validation/pr64_interpretation_analytics_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v0.7 — Reflection Constitution (READ-ONLY)

### v0.7 Philosophy: Interpretation → Reflection

v0.6 completed interpretation (observation → meaning).
v0.7 observes the interpretation system itself.

Reflection observes:
- What meanings are frequently/rarely observed
- What combinations have never appeared
- What the interpretation engine implicitly assumes

**Reflection ≠ Evaluation**
- **Reflection** = Interpretive System Description
- **Reflection** ≠ Evaluation (good/bad judgment)
- **Reflection** ≠ Recommendation (what should be done)
- **Reflection** ≠ Optimization (improve/fix)

### v0.7 Reflection Schema (PR70)

Reflection records use `v7_` prefix:

- `v7_reflection_mode`: ON | OFF
- `v7_reflection_status`: AVAILABLE | UNAVAILABLE
- `v7_reflection_tag`: Reflection type (non-evaluative)
- `v7_reflection_summary`: Non-evaluative system description
- `v7_reflection_basis`: Array of interpretation field names used
- `v7_reflection_artifacts`: Array of analytics artifacts referenced

**Example Reflection Record:**

```json
{
  "v7_reflection_mode": "ON",
  "v7_reflection_status": "AVAILABLE",
  "v7_reflection_tag": "COVERAGE_GAP_DETECTED",
  "v7_reflection_summary": "certain factor combinations not observed in data.",
  "v7_reflection_basis": ["v6_factors", "pr64_interpretation_analytics"],
  "v7_reflection_artifacts": ["interpretation_distribution.json"]
}
```

**Important:**
- Reflection observes interpretation system characteristics
- No evaluation of whether patterns are good/bad
- No recommendations for what should be changed
- UNKNOWN/UNCLASSIFIED remain normal outcomes

### v0.7 Reflection Engine v1 (PR71)

Engine v1 = **Static Structural Self-Description**

Generates reflection records by observing interpretation analytics from PR64:

**Reflection Tags (v1 Fixed Set):**
- `MEANING_COVERAGE_NARROW`: Limited meaning types observed (≤ 2 types)
- `MEANING_COVERAGE_BROAD`: Diverse meaning types observed (≥ 4 types)
- `MEANING_DISTRIBUTION_SKEWED`: Concentration on limited subset (≥ 80%)
- `FACTOR_DOMINANCE_OBSERVED`: Certain factors almost always present (≥ 90%)
- `UNSEEN_MEANING_COMBINATIONS`: Theoretically possible combinations never observed
- `SIGNAL_NEVER_OBSERVED`: Certain signals not present in data
- `REFLECTION_INSUFFICIENT`: Analytics data insufficient
- `UNCLASSIFIED`: Cannot classify with current rules (normal outcome)

**Detection Logic:**
- **Coverage**: Count distinct meaning types in distribution
- **Skew**: Measure concentration of dominant meaning tag
- **Unseen**: Identify gaps in observed structural patterns
- **No judgment**: All tags are neutral observations

**Usage:**

```python
from reflection.v7_reflection_engine_v1 import reflect_v1, V1ReflectionTags
from analytics.pr64_interpretation_analytics import generate_interpretation_analytics

# Generate analytics from interpretation records
analytics = generate_interpretation_analytics(interpretation_records)

# Generate reflection
reflection = reflect_v1(analytics)

print(reflection["v7_reflection_tag"])
print(reflection["v7_reflection_summary"])
print(reflection["v7_reflection_basis"])
```

**Example Output:**

```json
{
  "v7_reflection_mode": "ON",
  "v7_reflection_status": "AVAILABLE",
  "v7_reflection_tag": "MEANING_DISTRIBUTION_SKEWED",
  "v7_reflection_summary": "observed interpretation output concentrates on limited subset. 'OVERLAY_OBSERVED' appears in 85% of records.",
  "v7_reflection_basis": ["meaning_tag_counts", "total_records"],
  "v7_reflection_artifacts": ["pr64_interpretation_analytics"]
}
```

**Rule Priority:**
1. Coverage narrow/broad (primary structural observation)
2. Skew detection (concentration patterns)
3. Factor dominance (v2 compositional patterns)
4. Signal never observed (gap detection)

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v7 record
- Exit code always 0

### Constitutional Constraints (v0.7)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Interpretation-bound**: Only uses interpretation fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access

### Run Validations (v0.7)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr70_reflection_schema_smoke.py
python3 python/validation/pr71_reflection_engine_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v0.8 — Blindspot Constitution (READ-ONLY)

### v0.8 Philosophy: Reflection → Blindspot

v0.6 completed interpretation (observation → meaning).
v0.7 completed reflection (interpretation → system description).
v0.8 observes structural absences — what the system cannot see.

Blindspot observes:
- Signal types never observed
- Factor types never observed
- Meaning types never observed
- Transitions never observed
- Structures the schema cannot express

**Blindspot ≠ Evaluation**
- **Blindspot** = Structural Absence Description
- **Blindspot** ≠ Evaluation (good/bad judgment)
- **Blindspot** ≠ Recommendation (what should be done)
- **Blindspot** ≠ Optimization (improve/fix)

### v0.8 Blindspot Schema (PR80)

Blindspot records use `v8_` prefix:

- `v8_blindspot_mode`: ON | OFF
- `v8_blindspot_status`: AVAILABLE | UNAVAILABLE
- `v8_blindspot_tag`: Structural absence type (non-evaluative)
- `v8_blindspot_summary`: Non-evaluative structural absence description
- `v8_blindspot_basis`: Array of interpretation/reflection field names used
- `v8_blindspot_artifacts`: Array of analytics artifacts referenced

**Example Blindspot Record:**

```json
{
  "v8_blindspot_mode": "ON",
  "v8_blindspot_status": "AVAILABLE",
  "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
  "v8_blindspot_summary": "certain signal types not observed in data.",
  "v8_blindspot_basis": ["v6_signals", "v7_reflection_tag"],
  "v8_blindspot_artifacts": ["pr64_interpretation_analytics", "pr71_reflection_record"]
}
```

**Important:**
- Blindspot observes structural absences in interpretation/reflection systems
- No evaluation of whether absences are good/bad
- No recommendations for what should be changed
- UNKNOWN/UNCLASSIFIED remain normal outcomes

**Blindspot Tags (v1 Fixed Set):**
- `ABSENCE_INSUFFICIENT_EVIDENCE` - Analytics data insufficient
- `ABSENCE_UNSEEN_SIGNAL_TYPES` - Certain signal types not observed
- `ABSENCE_UNSEEN_FACTOR_TYPES` - Certain factor types not observed
- `ABSENCE_UNOBSERVED_MEANING_TYPES` - Certain meaning types not observed
- `ABSENCE_TRANSITION_NOT_OBSERVED` - Certain transitions not observed
- `ABSENCE_SCHEMA_CANNOT_EXPRESS` - Structure cannot be expressed in current schema
- `UNCLASSIFIED` - Cannot classify with current rules (normal outcome)

### v0.8 Blindspot Detection Engine v1 (PR81)

Engine v1 = **Structural Absence Scan**

Detects structural absences by enumerating differences between possible structures and observed structures.

**Detection Philosophy:**
- Enumerate what exists in definition space but not in observed space
- No judgment about whether absences are problems
- No inference about why absences exist
- Pure set difference operation

**Detection Targets:**
- **Unseen Signal Types**: Signals defined but never observed
- **Unseen Factor Types**: Factors defined but never observed
- **Unobserved Meaning Types**: Meanings defined but never observed
- **Transition Gaps**: Theoretically possible transitions never observed

**Usage:**

```python
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1, V1BlindspotTags
from analytics.pr64_interpretation_analytics import generate_interpretation_analytics

# Generate analytics from interpretation records
analytics = generate_interpretation_analytics(interpretation_records)

# Detect blindspot
blindspot = detect_blindspot_v1(analytics)

print(blindspot["v8_blindspot_tag"])
print(blindspot["v8_blindspot_summary"])
print(blindspot["v8_blindspot_basis"])
```

**Example Output:**

```json
{
  "v8_blindspot_mode": "ON",
  "v8_blindspot_status": "AVAILABLE",
  "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
  "v8_blindspot_summary": "6 signal types not observed in data. certain observational patterns not present.",
  "v8_blindspot_basis": ["meaning_tag_counts", "total_records", "signal_counts"],
  "v8_blindspot_artifacts": ["pr64_interpretation_analytics"]
}
```

**Detection Logic:**
1. Extract observed sets from analytics (signals, factors, meanings, transitions)
2. Compare against known definition space
3. Enumerate differences as structural absences
4. No evaluation, no recommendation

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v8 record
- Exit code always 0

### Constitutional Constraints (v0.8)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Interpretation/Reflection-bound**: Only uses v6/v7 fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access

### Run Validations (v0.8)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr80_blindspot_schema_smoke.py
python3 python/validation/pr81_blindspot_detection_engine_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v0.9 — Boundary Constitution (READ-ONLY)

### v0.9 Philosophy: Blindspot → Boundary

v0.6 completed interpretation (observation → meaning).
v0.7 completed reflection (interpretation → system description).
v0.8 completed blindspot (structural absences enumeration).
v0.9 classifies where observability ends — the boundary itself.

Boundary answers a different question than Blindspot:
- **Blindspot**: What is absent?
- **Boundary**: At which structural boundary does the absence occur?

Boundary treats absences not as failures, but as topological limits of the system.

**Boundary ≠ Evaluation**
- **Boundary** = Structural Limit Description
- **Boundary** ≠ Evaluation (good/bad judgment)
- **Boundary** ≠ Recommendation (what should be done)
- **Boundary** ≠ Optimization (improve/fix)
- **Boundary** ≠ Root-cause analysis

### v0.9 Boundary Schema (PR90)

Boundary records use `v9_` prefix:

- `v9_boundary_mode`: ON | OFF
- `v9_boundary_status`: AVAILABLE | UNAVAILABLE
- `v9_boundary_type`: Structural boundary type (non-evaluative)
- `v9_boundary_description`: Non-evaluative structural limit description
- `v9_boundary_basis`: Array of blindspot/interpretation/reflection field names used
- `v9_boundary_artifacts`: Array of analytics artifacts referenced

**Example Boundary Record:**

```json
{
  "v9_boundary_mode": "ON",
  "v9_boundary_status": "AVAILABLE",
  "v9_boundary_type": "SCHEMA_BOUNDARY",
  "v9_boundary_description": "observability limit at schema layer. structure cannot be expressed with current schema.",
  "v9_boundary_basis": ["v8_blindspot_tag", "v7_reflection_tag"],
  "v9_boundary_artifacts": ["pr81_blindspot_record"]
}
```

**Important:**
- Boundary classifies structural limits of observability
- No evaluation of whether boundaries are good/bad
- No recommendations for what should be changed
- UNKNOWN/UNCLASSIFIED remain normal outcomes

**Boundary Types (v1):**
- `SCHEMA_BOUNDARY` - Structure cannot be expressed with current schema
- `DATA_BOUNDARY` - Required data does not exist or is insufficient
- `ENGINE_BOUNDARY` - Interpretation/reflection rules cannot map structure
- `SAMPLING_BOUNDARY` - Structure exists in definition space but not observed
- `TEMPORAL_BOUNDARY` - Structure exists but cannot be observed in time window
- `UNCLASSIFIED` - Cannot classify with current rules (normal outcome)

### v0.9 Boundary Classification Engine v1 (PR91)

Engine v1 = **Structural Limit Mapping**

Classifies blindspots into structural boundary types using static rules.

**Classification Philosophy:**
- Map blindspot to boundary layer (not evaluation)
- Static rules (if/elif), no learning, no inference
- No judgment about whether boundaries are problems
- No inference about why boundaries exist

**Classification Rules:**
1. **ABSENCE_INSUFFICIENT_EVIDENCE** → `DATA_BOUNDARY`
2. **ABSENCE_SCHEMA_CANNOT_EXPRESS** → `SCHEMA_BOUNDARY`
3. **ABSENCE_TRANSITION_NOT_OBSERVED** →
   - Observation period < 30 days → `TEMPORAL_BOUNDARY`
   - Observation period ≥ 30 days → `SAMPLING_BOUNDARY`
4. **ABSENCE_UNSEEN_SIGNAL/FACTOR/MEANING_TYPES** → `SAMPLING_BOUNDARY`
5. **All others** → `UNCLASSIFIED`

**Usage:**

```python
from boundary.v9_boundary_classification_engine_v1 import classify_boundary_v1, V1BoundaryTypes
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1

# Detect blindspot from analytics
blindspot = detect_blindspot_v1(interpretation_analytics)

# Classify boundary
boundary = classify_boundary_v1(blindspot)

print(boundary["v9_boundary_type"])
print(boundary["v9_boundary_description"])
print(boundary["v9_boundary_basis"])
```

**Example Output:**

```json
{
  "v9_boundary_mode": "ON",
  "v9_boundary_status": "AVAILABLE",
  "v9_boundary_type": "SAMPLING_BOUNDARY",
  "v9_boundary_description": "observability limit at sampling layer. certain structural types exist in definition space but not observed in data.",
  "v9_boundary_basis": ["v8_blindspot_tag"],
  "v9_boundary_artifacts": ["pr81_blindspot_record"]
}
```

**Classification Logic:**
1. Extract blindspot tag from v8 record
2. Apply static mapping rules
3. Classify into boundary type
4. No evaluation, no recommendation

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v9 record
- Exit code always 0

### Constitutional Constraints (v0.9)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Blindspot-bound**: Only uses v8/v7/v6 fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access

### Run Validations (v0.9)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr90_boundary_schema_smoke.py
python3 python/validation/pr91_boundary_classification_engine_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.0 — Execution Constitution (READ-ONLY)

### v1.0 Philosophy: Boundary → Execution

v0.6 completed interpretation (observation → meaning).
v0.7 completed reflection (interpretation → system description).
v0.8 completed blindspot (structural absences enumeration).
v0.9 completed boundary (structural limits of observability).
v1.0 describes executability — whether execution is available and what intent exists.

Execution answers a different question than Decision:
- **Execution** = Executability Description
- **Execution** ≠ Trading (no swap/transfer/send/approve/sign)
- **Execution** ≠ Position changes (no fund movement/rebalancing)
- **Execution** ≠ Recommendations (no should/must)

**Execution ≠ Trading**
- **Execution** = Description of execution intent
- **Execution** ≠ Evaluation (good/bad judgment)
- **Execution** ≠ Profit/loss analysis
- **Execution** ≠ Scoring or optimization
- **Execution** ≠ Trading commands

### v1.0 Execution Schema (PR100)

Execution records use `v10_` prefix:

- `v10_execution_mode`: ON | OFF
- `v10_execution_status`: AVAILABLE | UNAVAILABLE
- `v10_execution_intent`: Structural execution intent type (non-evaluative)
- `v10_execution_permission`: Execution permission level
- `v10_execution_summary`: Non-evaluative execution description
- `v10_execution_basis`: Array of boundary/blindspot/reflection/interpretation field names used
- `v10_execution_artifacts`: Array of analytics artifacts referenced (optional)
- `v10_execution_constraints`: Execution constraints (optional)

**Example Execution Record:**

```json
{
  "v10_execution_mode": "ON",
  "v10_execution_status": "AVAILABLE",
  "v10_execution_intent": "REBALANCE_INTENT",
  "v10_execution_permission": "DRY_RUN_ONLY",
  "v10_execution_summary": "rebalance intent observed. execution available in dry-run mode.",
  "v10_execution_basis": ["v9_boundary_type", "v8_blindspot_tag"],
  "v10_execution_artifacts": ["pr91_boundary_record"],
  "v10_execution_constraints": ["dry_run_only", "no_fund_movement"]
}
```

**Important:**
- Execution describes executability, not trading
- No evaluation of whether execution is good/bad
- No recommendations for what should be executed
- NONE/UNKNOWN/HOLD remain normal outcomes

**Execution Intent Types (v1):**
- `NONE` - No execution intent detected
- `MAINTENANCE` - Maintenance execution intent
- `REBALANCE_INTENT` - Rebalance execution intent
- `HEDGE_INTENT` - Hedge execution intent
- `LIQUIDITY_INTENT` - Liquidity execution intent
- `UNCLASSIFIED` - Cannot classify with current rules (normal outcome)

**Execution Permission Types (v1):**
- `UNKNOWN` - Permission status unknown
- `DRY_RUN_ONLY` - Execution permitted in dry-run mode only
- `HOLD` - Execution on hold
- `ALLOW` - Execution allowed

### v1.0 Constitutional Guards (PR100)

PR100 introduces constitutional guards to enforce v1.0 execution principles:

**1. Forbidden Vocabulary Guard**
- Detects evaluative vocabulary (good/bad, correct/wrong)
- Detects scoric vocabulary (score/grade/rank)
- Detects prescriptive vocabulary (should/must/recommend)

**2. Execution Safety Guard (NEW in v1.0)**
- Detects trading action vocabulary (swap/transfer/send/approve/sign)
- Detects position management vocabulary (open/close/liquidate)
- Excludes valid intent type descriptions (e.g., "rebalance intent")

**3. v0.4 Boundary Guard**
- Detects confidence_reason field access
- Execution must not access v0.4 confidence layer

**4. Observation Boundary Guard**
- Detects v5 observation field access
- Execution must only access v6/v7/v8/v9 fields as basis

**Usage:**

```python
from execution.v10_execution_schema import V10ExecutionSchema
from execution.v10_constitutional_guard import validate_execution_record

# Create execution record
record = V10ExecutionSchema.create_empty_record()
record["v10_execution_intent"] = "REBALANCE_INTENT"
record["v10_execution_permission"] = "DRY_RUN_ONLY"

# Validate against constitutional guards
warnings = validate_execution_record(record)

if warnings:
    for warning in warnings:
        print(f"⚠ {warning}")
```

**Example Validation:**

```python
# Clean execution description (no warnings)
record = {
    "v10_execution_intent": "MAINTENANCE",
    "v10_execution_summary": "maintenance intent observed. execution available.",
    "v10_execution_basis": ["v9_boundary_type", "v8_blindspot_tag"]
}
warnings = validate_execution_record(record)  # []

# Forbidden vocabulary (triggers warning)
record = {
    "v10_execution_intent": "REBALANCE_INTENT",
    "v10_execution_summary": "this is a good opportunity that should be taken",
    "v10_execution_basis": ["v9_boundary_type"]
}
warnings = validate_execution_record(record)
# ["Forbidden vocabulary detected: 'good' in text",
#  "Forbidden vocabulary detected: 'should' in text"]

# Trading vocabulary (triggers warning)
record = {
    "v10_execution_intent": "REBALANCE_INTENT",
    "v10_execution_summary": "swap tokens and transfer funds",
    "v10_execution_basis": ["v9_boundary_type"]
}
warnings = validate_execution_record(record)
# ["Execution action vocabulary detected: 'swap' in text",
#  "Execution action vocabulary detected: 'transfer' in text"]
```

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully
- Always returns warnings list
- Exit code always 0

### Constitutional Constraints (v1.0)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **Boundary-bound**: Only uses v6/v7/v8/v9 fields as basis
- **v0.4 boundary protection**: No confidence_reason analysis
- **Observation boundary protection**: No direct v5 field access
- **Execution safety**: No trading action vocabulary

### v1.0 Execution Permissioning Engine v1 (PR101)

Engine v1 = **Structural Boundary-to-Permission Mapping**

Classifies execution permission based on boundary type using static rules.

**Permissioning Philosophy:**
- Map boundary to permission level (not evaluation)
- Static rules (if/elif), no learning, no inference
- No judgment about whether permission is good/bad
- No recommendation about what should be executed

**Permission Types (v1):**
- `UNKNOWN` - Insufficient structural clarity
- `HOLD` - Execution structurally disallowed
- `DRY_RUN_ONLY` - Observation-only execution allowed
- `ALLOW` - Execution structurally permitted (rare in v1)

**Classification Rules (v1 - Static):**
1. **SCHEMA_BOUNDARY** → `HOLD`
2. **DATA_BOUNDARY** → `HOLD`
3. **ENGINE_BOUNDARY** → `HOLD`
4. **TEMPORAL_BOUNDARY** → `DRY_RUN_ONLY`
5. **SAMPLING_BOUNDARY** → `DRY_RUN_ONLY`
6. **UNCLASSIFIED** → `UNKNOWN`

**Usage:**

```python
from execution.v10_execution_permissioning_engine_v1 import classify_execution_permission_v1
from boundary.v9_boundary_classification_engine_v1 import classify_boundary_v1
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1

# Detect blindspot from analytics
blindspot = detect_blindspot_v1(interpretation_analytics)

# Classify boundary
boundary = classify_boundary_v1(blindspot)

# Classify execution permission
execution = classify_execution_permission_v1(boundary)

print(execution["v10_execution_permission"])
print(execution["v10_execution_summary"])
print(execution["v10_execution_basis"])
```

**Example Output:**

```json
{
  "v10_execution_mode": "ON",
  "v10_execution_status": "AVAILABLE",
  "v10_execution_intent": "NONE",
  "v10_execution_permission": "DRY_RUN_ONLY",
  "v10_execution_summary": "execution permitted only in dry-run mode. sampling boundary detected. structure exists in definition space but not observed.",
  "v10_execution_basis": ["v9_boundary_type"],
  "v10_execution_artifacts": [],
  "v10_execution_constraints": []
}
```

**Classification Logic:**
1. Extract boundary type from v9 record
2. Apply static mapping rules
3. Classify into permission level
4. No evaluation, no recommendation

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 record
- Exit code always 0

### v1.0 Execution Plan Schema v1 (PR102)

Schema v1 = **Typed Plan Shape (Structural Only)**

Defines execution plan records that describe plan shapes without amounts, token names, or trading actions.

**Plan Philosophy:**
- Plan = Structural plan shape description
- No amounts, prices, or quantities
- No token literals (SUI, USDC, BTC, etc.)
- No addresses or wallet interactions
- No trading verbs or commands

**Plan Types (v1):**
- `NOOP` - No operation plan
- `MAINTENANCE` - Maintenance plan
- `REBALANCE` - Rebalance plan shape
- `HEDGE` - Hedge plan shape
- `LIQUIDITY` - Liquidity plan shape
- `UNCLASSIFIED` - Cannot classify with current rules

**Schema Fields (v10_plan_ prefix):**
- `v10_plan_mode`: ON | OFF
- `v10_plan_status`: AVAILABLE | UNAVAILABLE
- `v10_plan_type`: Structural plan type
- `v10_plan_description`: Non-evaluative plan shape description
- `v10_plan_constraints`: Structural constraints (time/frequency only)
- `v10_plan_basis`: Array of execution field names referenced
- `v10_plan_artifacts`: Array of artifact names (optional)

**Constraint Types (Structural Only):**
- `time_window` - e.g., "business_hours_only"
- `frequency_limit` - e.g., "once_per_day"
- `dry_run_only` - e.g., "no_live_execution"
- `manual_approval` - e.g., "requires_manual_approval"

**Constitutional Guards:**

**1. Token Literal Guard (NEW in PR102)**
- Detects token names (SUI, USDC, BTC, ETH, etc.)
- Prevents concrete token references in plans
- Maintains abstract plan descriptions

**2. Numeric Pattern Guard (NEW in PR102)**
- Detects amounts (1000, 0.5, etc.)
- Detects prices ($100, €50, etc.)
- Detects addresses (0x...)
- Plans remain purely structural

**3. Forbidden Vocabulary & Execution Safety**
- All PR100 guards apply to plan descriptions
- No evaluative/prescriptive vocabulary
- No trading action verbs

**Usage:**

```python
from execution.v10_execution_plan_schema import V10ExecutionPlanSchema
from execution.v10_plan_constitutional_guard import validate_plan_record

# Create plan record
plan = V10ExecutionPlanSchema.create_empty_record()
plan["v10_plan_mode"] = "ON"
plan["v10_plan_status"] = "AVAILABLE"
plan["v10_plan_type"] = "REBALANCE"
plan["v10_plan_description"] = "rebalance plan available based on boundary analysis."
plan["v10_plan_constraints"] = ["dry_run_only", "time_window_business_hours"]
plan["v10_plan_basis"] = ["v10_execution_permission"]

# Validate against constitutional guards
warnings = validate_plan_record(plan)

if warnings:
    for warning in warnings:
        print(f"⚠ {warning}")
```

**Example Plan Record:**

```json
{
  "v10_plan_mode": "ON",
  "v10_plan_status": "AVAILABLE",
  "v10_plan_type": "REBALANCE",
  "v10_plan_description": "rebalance plan available based on sampling boundary.",
  "v10_plan_constraints": ["dry_run_only", "frequency_limit_once_per_day"],
  "v10_plan_basis": ["v10_execution_permission"],
  "v10_plan_artifacts": ["pr101_execution_record"]
}
```

**Important:**
- Plans describe structure, not specific trades
- No amounts, no token names, no addresses
- Constraints are time/frequency based only
- All trading vocabulary is forbidden

**Warning-Only Validation:**
- Never raises exceptions
- Detects violations via constitutional guards
- Always returns warnings list
- Exit code always 0

### v1.0 Execution Plan Generator v1 (PR103)

Generator v1 = **Static Plan Synthesis**

Generates execution plan records based on permission and boundary analysis using static rules.

**Generator Philosophy:**
- Generate plan shape from permission (not execution)
- Static rules (if/elif), no learning, no inference
- No amounts, no token names, no addresses
- No trading verbs or execution commands

**Generation Rules (v1 - Static):**
1. **HOLD** → `NOOP` + `manual_approval`
   - Execution structurally disallowed
2. **UNKNOWN** → `UNCLASSIFIED` + `manual_approval`
   - Insufficient structural clarity
3. **DRY_RUN_ONLY** → `MAINTENANCE` + `dry_run_only` + `frequency_limit_once_per_day`
   - Observation-only execution
4. **ALLOW** → Intent-based type + `manual_approval`
   - REBALANCE_INTENT → `REBALANCE`
   - HEDGE_INTENT → `HEDGE`
   - LIQUIDITY_INTENT → `LIQUIDITY`
   - MAINTENANCE → `MAINTENANCE`
   - Other → `UNCLASSIFIED`

**Usage:**

```python
from execution.v10_execution_plan_generator_v1 import generate_execution_plan_v1
from execution.v10_execution_permissioning_engine_v1 import classify_execution_permission_v1
from boundary.v9_boundary_classification_engine_v1 import classify_boundary_v1
from blindspot.v8_blindspot_detection_engine_v1 import detect_blindspot_v1

# Full pipeline: Blindspot → Boundary → Permission → Plan
blindspot = detect_blindspot_v1(interpretation_analytics)
boundary = classify_boundary_v1(blindspot)
execution = classify_execution_permission_v1(boundary)
plan = generate_execution_plan_v1(execution, boundary)

print(plan["v10_plan_type"])
print(plan["v10_plan_description"])
print(plan["v10_plan_constraints"])
```

**Example Output (DRY_RUN_ONLY):**

```json
{
  "v10_plan_mode": "ON",
  "v10_plan_status": "AVAILABLE",
  "v10_plan_type": "MAINTENANCE",
  "v10_plan_description": "maintenance plan available in dry-run-only mode due to boundary constraints.",
  "v10_plan_constraints": ["dry_run_only", "frequency_limit_once_per_day"],
  "v10_plan_basis": ["v10_execution_permission", "v9_boundary_type"],
  "v10_plan_artifacts": []
}
```

**Example Output (ALLOW + REBALANCE_INTENT):**

```json
{
  "v10_plan_mode": "ON",
  "v10_plan_status": "AVAILABLE",
  "v10_plan_type": "REBALANCE",
  "v10_plan_description": "rebalance plan shape available under allow permission; manual approval required.",
  "v10_plan_constraints": ["manual_approval"],
  "v10_plan_basis": ["v10_execution_permission", "v10_execution_intent"],
  "v10_plan_artifacts": []
}
```

**Generation Logic:**
1. Extract permission from v10 execution record
2. Apply static mapping rules
3. Generate plan type and constraints
4. No evaluation, no recommendation, no trading

**Constitutional Guarantees:**
- No amounts, prices, or quantities generated
- No token literals (SUI, USDC, etc.) in descriptions
- No addresses or wallet references
- No trading verbs (swap, transfer, sign, etc.)
- All generated plans pass PR102 constitutional guards

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 plan record
- Exit code always 0

### v1.0 Execution Simulation Engine v1 (PR104)

Engine v1 = **Plan Applicability Scan**

Simulates plan applicability based on constraints without execution, PnL, or evaluation.

**Simulation Philosophy:**
- Simulate = Plan applicability description
- Enumerate constraints as events
- No execution, no wallet, no transactions
- No amounts, no token names, no PnL

**Schema Fields (v10_simulation_ prefix):**
- `v10_simulation_mode`: ON | OFF
- `v10_simulation_status`: AVAILABLE | UNAVAILABLE
- `v10_simulation_type`: PLAN_APPLICABILITY_SCAN | UNCLASSIFIED
- `v10_simulation_summary`: Non-evaluative simulation description
- `v10_simulation_basis`: Array of field names referenced
- `v10_simulation_artifacts`: Array of artifact names (optional)
- `v10_simulation_trace`: Array of simulation events (optional)

**Trace Event Structure:**
- `event_type`: CONSTRAINT_APPLIED | PLAN_APPLICABLE | PLAN_NOT_APPLIED | WINDOW_ADVANCED
- `event_summary`: Non-evaluative event description
- `event_basis`: Array of field names referenced

**Simulation Logic (v1):**
1. Check plan availability
2. Enumerate constraints as CONSTRAINT_APPLIED events
3. Determine applicability based on constraints
4. Generate trace of constraint applications

**Constraint Types Detected:**
- `dry_run_only` - Observation-only mode
- `manual_approval` - Human review required
- `frequency_limit` - Rate limiting active
- `time_window` - Time-based restrictions

**Usage:**

```python
from execution.v10_execution_simulation_engine_v1 import simulate_execution_plan_v1
from execution.v10_execution_plan_generator_v1 import generate_execution_plan_v1
from execution.v10_execution_permissioning_engine_v1 import classify_execution_permission_v1

# Full pipeline: Permission → Plan → Simulation
execution = classify_execution_permission_v1(boundary)
plan = generate_execution_plan_v1(execution, boundary)
simulation = simulate_execution_plan_v1(plan)

print(simulation["v10_simulation_type"])
print(simulation["v10_simulation_summary"])
for event in simulation["v10_simulation_trace"]:
    print(f"  {event['event_type']}: {event['event_summary']}")
```

**Example Output (dry_run_only constraint):**

```json
{
  "v10_simulation_mode": "ON",
  "v10_simulation_status": "AVAILABLE",
  "v10_simulation_type": "PLAN_APPLICABILITY_SCAN",
  "v10_simulation_summary": "plan applicability scan complete. plan type MAINTENANCE applicable under constraint.",
  "v10_simulation_basis": ["v10_plan_mode", "v10_plan_status", "v10_plan_type", "v10_plan_constraints"],
  "v10_simulation_trace": [
    {
      "event_type": "CONSTRAINT_APPLIED",
      "event_summary": "dry-run-only constraint applied. execution limited to observation mode.",
      "event_basis": ["v10_plan_constraints"]
    },
    {
      "event_type": "PLAN_APPLICABLE",
      "event_summary": "plan applicable under constraint. constraints enumerated above.",
      "event_basis": ["v10_plan_constraints"]
    }
  ]
}
```

**Simulation Guarantees:**
- No execution (READ-ONLY)
- No amounts, prices, or quantities
- No token literals (SUI, USDC, etc.)
- No addresses or wallet references
- No trading verbs or commands
- No PnL calculation
- No evaluation (good/bad judgment)

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 simulation record
- Exit code always 0

### v1.0 Execution Audit Trail v1 (PR105)

Engine v1 = **Causal Chain Trace**

Documents the causal chain from interpretation through simulation without execution, evaluation, or trading.

**Audit Trail Philosophy:**
- Audit Trail = Causal chain documentation
- Link artifacts as explicit chain-of-custody
- No execution, no evaluation, no recommendations
- Fixed layer order (cannot reorder)

**Schema Fields (v10_audit_ prefix):**
- `v10_audit_mode`: ON | OFF
- `v10_audit_status`: AVAILABLE | UNAVAILABLE
- `v10_audit_chain`: Array of chain events (ordered)
- `v10_audit_summary`: Non-evaluative audit description

**Chain Event Structure:**
- `layer`: Layer name (INTERPRETATION_ANALYTICS, BLINDSPOT, etc.)
- `artifact`: Artifact identifier (pr81_blindspot_record, etc.)
- `basis`: Array of field names referenced

**Chain Layers (Fixed Order in v1):**
1. **INTERPRETATION_ANALYTICS** (PR64) - Observation → meaning
2. **BLINDSPOT** (PR81) - Structural absences
3. **BOUNDARY** (PR91) - Observability limits
4. **PERMISSION** (PR101) - Executability permission
5. **PLAN** (PR103) - Plan shape generation
6. **SIMULATION** (PR104) - Plan applicability scan

**Usage:**

```python
from audit.v10_execution_audit_trail_engine_v1 import build_execution_audit_trail_v1

# Full pipeline audit trail
trail = build_execution_audit_trail_v1(
    interpretation_analytics=analytics,
    blindspot_record=blindspot,
    boundary_record=boundary,
    permission_record=execution,
    plan_record=plan,
    simulation_record=simulation
)

print(trail["v10_audit_status"])
print(trail["v10_audit_summary"])
for event in trail["v10_audit_chain"]:
    print(f"  {event['layer']}: {event['artifact']}")
```

**Example Output (full chain):**

```json
{
  "v10_audit_mode": "ON",
  "v10_audit_status": "AVAILABLE",
  "v10_audit_summary": "audit trail built with multiple layers of causal chain. chain links interpretation through simulation.",
  "v10_audit_chain": [
    {
      "layer": "BLINDSPOT",
      "artifact": "pr81_blindspot_record",
      "basis": ["v8_blindspot_tag", "v8_blindspot_basis"]
    },
    {
      "layer": "BOUNDARY",
      "artifact": "pr91_boundary_record",
      "basis": ["v9_boundary_type", "v9_boundary_basis"]
    },
    {
      "layer": "PERMISSION",
      "artifact": "pr101_execution_record",
      "basis": ["v10_execution_permission", "v10_execution_basis"]
    },
    {
      "layer": "PLAN",
      "artifact": "pr103_plan_record",
      "basis": ["v10_plan_type", "v10_plan_constraints", "v10_plan_basis"]
    },
    {
      "layer": "SIMULATION",
      "artifact": "pr104_simulation_record",
      "basis": ["v10_simulation_type", "v10_simulation_basis"]
    }
  ]
}
```

**Audit Trail Guarantees:**
- Fixed layer order (no reordering)
- Defensive (None/invalid → skip layer)
- No execution (READ-ONLY)
- No amounts, prices, or quantities
- No token literals (SUI, USDC, etc.)
- No addresses or wallet references
- No trading verbs or commands
- No evaluation (good/bad judgment)

**Complete Pipeline:**

```
Interpretation Analytics (PR64)
         ↓
    Blindspot (PR81)
         ↓
    Boundary (PR91)
         ↓
    Permission (PR101)
         ↓
    Plan (PR103)
         ↓
    Simulation (PR104)
         ↓
    Audit Trail (PR105) ← Documents entire causal chain
```

**Warning-Only Validation:**
- Never raises exceptions
- Handles edge cases gracefully (None, invalid types)
- Always returns valid v10 audit trail record
- Exit code always 0

### Run Validations (v1.0)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr100_execution_schema_smoke.py
python3 python/validation/pr101_execution_permissioning_engine_v1_smoke.py
python3 python/validation/pr102_execution_plan_schema_smoke.py
python3 python/validation/pr103_execution_plan_generator_v1_smoke.py
python3 python/validation/pr104_execution_simulation_engine_v1_smoke.py
python3 python/validation/pr105_execution_audit_trail_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.1 — Intelligence Native Market (READ-ONLY)

### v1.1 Philosophy: Execution → Market Intelligence

v1.0 completed execution constitution (boundary → executability).
v1.1 integrates onchain market intelligence — regime classification, policy binding, execution preview, and human approval.

**v1.1 Pipeline:**
```
Onchain Connection (PR106)
         ↓
Onchain Observation (PR107)
         ↓
Observation Bridge (PR108)
         ↓
Analytics Extension (PR109)
         ↓
Entropy Regime (PR110)
         ↓
Policy Binding (PR111)
         ↓
Execution Preview (PR112)
         ↓
Human Approval Gate (PR113)
```

### v1.1 Entropy Regime Classification (PR110)

**Purpose:** Classify entropy regime from onchain analytics.

**Regime Philosophy:**
- Regime = State Classification (not action)
- No recommendations, no optimization
- READ-ONLY, non-evaluative, non-prescriptive

**Regime Levels:**
- `REGIME_LOW` - Low variation (stable)
- `REGIME_MEDIUM` - Moderate variation
- `REGIME_HIGH` - High variation (elevated)
- `REGIME_CRITICAL` - Extreme variation or no observations

**Classification Metrics:**
- Market cost regime distribution (entropy)
- Liquidity regime diversity (count)
- Event activity variation (entropy)
- Object dynamics variation (entropy)

**Constitutional Guarantees:**
- No token literals (SUI/USDC prohibited)
- No amounts or addresses
- No asset vocabulary
- No action vocabulary
- Defensive (never raises)
- Warning-only (exit 0)

### v1.1 Regime → Execution Policy Binding (PR111)

**Purpose:** Bind regime classification to execution policy.

**Binding Philosophy:**
- Binding = Constitutional Gate (not action/decision)
- No recommendations, no optimization
- READ-ONLY, non-evaluative, non-prescriptive

**Binding Rules (v1):**
- `REGIME_CRITICAL` → `HOLD` + `["regime_critical_observed"]`
- `REGIME_HIGH` → `DRY_RUN_ONLY` + `["regime_high_observed"]`
- `REGIME_MEDIUM` → `UNKNOWN` + `["regime_medium_observed"]`
- `REGIME_LOW` → `UNKNOWN` + `["regime_low_observed"]`

**Permission Overrides:**
- `HOLD` - Hard stop (critical regime)
- `DRY_RUN_ONLY` - Simulation only (high regime)
- `UNKNOWN` - No override (defer to execution engine)
- `ALLOW` - Explicit permission (reserved)

**Constitutional Guarantees:**
- No amounts (override labels only)
- No token literals, addresses
- No asset/action vocabulary
- Defensive, warning-only

### v1.1 Execution Preview Engine (PR112)

**Purpose:** Describe structural impact shape of potential execution.

**Preview Philosophy:**
- Preview = Impact Shape Description (not simulation/execution)
- No execution, no signing, no transactions
- READ-ONLY, non-evaluative, non-prescriptive

**Preview Fields:**
- `v11_preview_exposure_change`: NONE/INCREASE/DECREASE
- `v11_preview_interaction_type`: NONE/POOL_TOUCH/EVENT_INTERACTION
- `v11_preview_risk_surface`: LOW/MEDIUM/HIGH
- `v11_preview_status`: AVAILABLE/BLOCKED/ERROR

**Static Preview Rules (v1):**

**Exposure Change:**
- NOOP/MAINTENANCE → NONE
- REBALANCE → DECREASE (conservative)
- HEDGE → DECREASE
- LIQUIDITY → INCREASE

**Interaction Type:**
- MAINTENANCE → NONE
- REBALANCE/HEDGE/LIQUIDITY → POOL_TOUCH
- NOOP → NONE

**Risk Surface:**
- REGIME_LOW → LOW
- REGIME_MEDIUM → MEDIUM
- REGIME_HIGH → HIGH
- REGIME_CRITICAL → BLOCKED

**Constitutional Guarantees:**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals, addresses, amounts
- No asset/action vocabulary
- Defensive, warning-only

### v1.1 Human Approval Gate (PR113)

**Purpose:** Determine human approval requirement from upstream records.

**Approval Philosophy:**
- Approval Gate = State Machine (not action/recommendation)
- "APPROVED" is a state label only (not instruction)
- No execution, no recommendations, no evaluation

**Approval Requirement Levels:**
- `NOT_REQUIRED` - No approval needed
- `REQUIRED` - Approval recommended
- `REQUIRED_STRICT` - Approval mandatory (hard gate)

**Approval States:**
- `UNREQUESTED` - No approval requested yet
- `REQUESTED` - Approval requested, pending
- `APPROVED` - Approved (state label only)
- `REJECTED` - Rejected
- `EXPIRED` - Approval expired

**Static Approval Rules (v1 - First Match Wins):**
1. Preview status == `BLOCKED` → `REQUIRED_STRICT`
2. Execution permission == `HOLD` → `REQUIRED_STRICT`
3. Regime level == `REGIME_CRITICAL` → `REQUIRED_STRICT`
4. Execution permission == `DRY_RUN_ONLY` → `REQUIRED`
5. Regime level == `REGIME_HIGH` → `REQUIRED`
6. Default → `NOT_REQUIRED`

**Example Approval Record:**

```json
{
  "v11_approval_mode": "ON",
  "v11_approval_status": "AVAILABLE",
  "v11_approval_requirement": "REQUIRED_STRICT",
  "v11_approval_state": "UNREQUESTED",
  "v11_approval_summary": "approval required under critical regime conditions. no approval requested.",
  "v11_approval_basis": ["v11_regime_level", "v11_preview_risk_surface"],
  "v11_approval_artifacts": ["pr110_regime_record", "pr112_preview_record"]
}
```

**Constitutional Guarantees:**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals, addresses, amounts
- No asset/action vocabulary
- No approval-specific vocabulary (go ahead/proceed/instruction)
- "APPROVED" must not be described as instruction
- Defensive, warning-only

**Usage Pipeline:**

```python
from approval import gate_human_approval_v1

# Gate approval from upstream records
approval = gate_human_approval_v1(
    execution_record=execution,
    plan_record=plan,
    simulation_record=simulation,
    regime_record=regime,
    policy_record=policy,
    preview_record=preview,
)

print(approval["v11_approval_requirement"])  # REQUIRED_STRICT
print(approval["v11_approval_state"])        # UNREQUESTED
print(approval["v11_approval_summary"])
```

---

## v1.1 Human Interface Layer (READ-ONLY)

### v1.1 Philosophy: Structural Situation Summary for Human Review

The Human Interface Layer packages structural state into non-prescriptive context for human review.

**Key Principles:**
- **Context ≠ Action** - Explanation provides situation summary, not recommendations
- **Context ≠ Recommendation** - No prescriptive language, no "should"
- **Structural Signals Only** - Regime, drift, permission states (no raw values)
- **No Prescriptive Coupling** - No "approved therefore execute" patterns
- **Label-Only Signals** - Signal names only (no embedded values)

**Explanation Context Philosophy:**
```
Context provides:
  - Current state signals (regime, drift, permission)
  - Artifact references (which records explain state)
  - Non-evaluative summary
  - Basis field names (no raw values)

Context does NOT:
  - Recommend actions
  - Evaluate quality (good/bad)
  - Contain token names, amounts, addresses
  - Prescribe responses
```

### v1.1 Human Explanation Context Schema v1 (PR122)

**Purpose:** Define schema for packaging structural situation as human-readable context.

**Explanation Context = Structural Situation Summary (not action/recommendation)**

**Schema Fields:**
- `v11_explain_mode` - ON | OFF
- `v11_explain_status` - AVAILABLE | UNAVAILABLE
- `v11_explain_summary` - Non-evaluative structural situation description
- `v11_explain_signals` - Array of structural signal labels (regime, drift, permission)
- `v11_explain_basis` - Array of field names referenced (not values)
- `v11_explain_artifacts` - Array of artifact names referenced

**Example Signals (Extensible):**
- Regime: `REGIME_LOW`, `REGIME_MEDIUM`, `REGIME_HIGH`, `REGIME_CRITICAL`
- Drift: `DRIFT_NONE`, `DRIFT_LOW`, `DRIFT_MEDIUM`, `DRIFT_HIGH`, `DRIFT_CRITICAL`
- Permission: `PERMISSION_UNKNOWN`, `PERMISSION_HOLD`, `PERMISSION_DRY_RUN_ONLY`, `PERMISSION_ALLOW`
- Preview: `PREVIEW_BLOCKED`, `PREVIEW_AVAILABLE`
- Approval: `APPROVAL_NOT_REQUIRED`, `APPROVAL_REQUIRED`, `APPROVAL_REQUIRED_STRICT`

**Example Explanation Context:**

```json
{
  "v11_explain_mode": "ON",
  "v11_explain_status": "AVAILABLE",
  "v11_explain_summary": "current structural situation: regime medium, drift low, permission dry-run-only.",
  "v11_explain_signals": [
    "REGIME_MEDIUM",
    "DRIFT_LOW",
    "PERMISSION_DRY_RUN_ONLY"
  ],
  "v11_explain_basis": [
    "v11_regime_level",
    "v10_drift_level",
    "v10_execution_permission"
  ],
  "v11_explain_artifacts": [
    "pr110_regime_record",
    "pr120_drift_record",
    "pr101_execution_record"
  ]
}
```

**Constitutional Guarantees (PR122):**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals (SUI/USDC/BTC/ETH), addresses, amounts
- No numeric patterns (counts, percentages, scores)
- No forbidden vocabulary (good/bad, correct/wrong)
- **No prescriptive coupling** (NEW):
  - No "approved therefore execute" patterns
  - No "if approved then execute" patterns
  - No "upon approval execute" patterns
  - No action coupling to approval state
- Signals are label-only (no embedded values)
- Defensive, warning-only (exit 0 always)

**Usage Example:**

```python
from explain import (
    V11HumanExplanationContextSchema,
    validate_explanation_context,
)

# Create explanation context
explanation = V11HumanExplanationContextSchema.create_explanation_record(
    summary="current structural situation: regime medium, drift low, permission dry-run-only.",
    signals=["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
    basis=["v11_regime_level", "v10_drift_level", "v10_execution_permission"],
    artifacts=["pr110_regime_record", "pr120_drift_record", "pr101_execution_record"],
)

# Validate against constitutional guards
warnings = validate_explanation_context(explanation)
if warnings:
    print(f"Constitutional warnings: {warnings}")

print(explanation["v11_explain_summary"])
print(explanation["v11_explain_signals"])
```

**Prescriptive Coupling Guard (NEW in PR122):**

Detects and warns on:
- "approved therefore execute" / "approved so execute"
- "if approved then execute" / "when approved execute"
- "approval means execute" / "approval triggers execution"
- Generic action coupling to approval state

Example violations:
```python
# VIOLATION: Prescriptive coupling
"approval state available. if approved then execute the swap operation."

# CLEAN: Structural state only
"current structural situation: approval required, regime medium, permission dry-run-only."
```

### v1.1 Human Narrative Builder v1 (PR123)

**Purpose:** Convert explanation context (PR122) into human-readable narrative.

**Narrative = Structural Situation Story (not action/recommendation)**

**Narrative Philosophy:**
```
Narrative ≠ Instruction
Narrative ≠ Recommendation
Narrative = Structural Situation Description

Narrative provides:
  - Human-readable story of current state
  - Label-based language (regime, drift, permission)
  - Non-evaluative description
  - Artifact references

Narrative does NOT:
  - Recommend actions
  - Evaluate quality (good/bad)
  - Contain token names, amounts, addresses
  - Prescribe responses
  - Use imperative language
```

**Schema Fields:**
- `v11_narrative_mode` - ON | OFF
- `v11_narrative_status` - AVAILABLE | UNAVAILABLE | ERROR
- `v11_narrative_style` - CONCISE | STANDARD | DETAILED
- `v11_narrative_text` - Human-readable narrative (non-prescriptive)
- `v11_narrative_sections` - Optional array of labeled sections
- `v11_narrative_basis` - Array of field names referenced
- `v11_narrative_artifacts` - Array of artifact names referenced

**Narrative Styles:**
- **CONCISE** - Minimal verbosity (e.g., "regime label medium. drift label low.")
- **STANDARD** - Balanced narrative (default)
- **DETAILED** - Extended narrative with context

**Example Narrative (STANDARD):**

```json
{
  "v11_narrative_mode": "ON",
  "v11_narrative_status": "AVAILABLE",
  "v11_narrative_style": "STANDARD",
  "v11_narrative_text": "current regime label indicates elevated uncertainty. structural drift label indicates shifting market vocabulary. execution permission label limits consideration to dry-run-only. approval label indicates human withholding may be required.",
  "v11_narrative_basis": [
    "v11_regime_level",
    "v10_drift_level",
    "v10_execution_permission",
    "v11_approval_requirement"
  ],
  "v11_narrative_artifacts": [
    "pr110_regime_record",
    "pr120_drift_record",
    "pr101_execution_record",
    "pr113_approval_record"
  ]
}
```

**Narrative Language Patterns:**
- Use "may / can / indicates / is labeled as" language
- Avoid "should / must / do X" language
- Use passive/descriptive voice
- Focus on state labels, not values

**Example Comparison:**

```python
# CONCISE (68 chars)
"regime label medium. drift label low. permission label dry-run-only."

# STANDARD (160 chars)
"current regime label indicates elevated uncertainty. structural drift label indicates low vocabulary shift. execution permission label limits consideration to dry-run-only."

# DETAILED (320 chars)
"current entropy regime label indicates elevated market uncertainty. structural assumptions may weaken. structural vocabulary drift label indicates low language shift. market structure vocabulary shows minor changes. execution permission label limits consideration to dry-run-only. live execution operations are withheld."
```

**Constitutional Guarantees (PR123):**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals (SUI/USDC/BTC/ETH), addresses, amounts
- No numeric patterns (counts, percentages, scores)
- No forbidden vocabulary (good/bad, correct/wrong)
- No prescriptive language (should/must/need to)
- No prescriptive coupling ("approved therefore execute")
- **No narrative coupling** (NEW):
  - No "this means X" / "this implies Y"
  - No "therefore X" / "thus Y" causal patterns
  - No "because X, Y" causal structures
- Deterministic templates (no LLM, no randomness)
- Defensive, warning-only (exit 0 always)

**Usage Example:**

```python
from explain import V11HumanExplanationContextSchema
from narrative import build_human_narrative_v1

# Create explanation context
explanation = V11HumanExplanationContextSchema.create_explanation_record(
    summary="current structural situation: regime medium, drift low, permission dry-run-only.",
    signals=["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
    basis=["v11_regime_level", "v10_drift_level", "v10_execution_permission"],
    artifacts=["pr110_regime_record", "pr120_drift_record", "pr101_execution_record"],
)

# Build narrative (STANDARD style by default)
narrative = build_human_narrative_v1(explanation, style="STANDARD")

print(narrative["v11_narrative_text"])
# Output: "current regime label indicates elevated uncertainty. structural drift label indicates low vocabulary shift. execution permission label limits consideration to dry-run-only."

# Try CONCISE style
concise = build_human_narrative_v1(explanation, style="CONCISE")
print(concise["v11_narrative_text"])
# Output: "regime label medium. drift label low. permission label dry-run-only."
```

**Pipeline Flow (Context → Narrative):**

```
PR122: Explanation Context (structural signals)
         ↓
PR123: Narrative Builder (human-readable story)
         ↓
PR124: Approval Packet Builder (review unit carrier)
```

### v1.1 Approval Packet Builder v1 (PR124)

**Purpose:** Bundle component records into a single review unit for human interface.

**Packet = Review Unit Carrier (not decision/instruction)**

**Packet Philosophy:**
```
Packet ≠ Decision
Packet ≠ Instruction
Packet = Review Unit Carrier

Packet provides:
  - Bundled component records (context, narrative, preview, gate, registry)
  - Non-prescriptive summary
  - Artifact references and basis
  - Current approval state (as label only)

Packet does NOT:
  - Recommend actions
  - Evaluate quality (good/bad)
  - Contain token names, amounts, addresses
  - Prescribe responses
  - Imply what to do next
```

**Schema Fields:**
- `v11_packet_mode` - ON | OFF
- `v11_packet_status` - AVAILABLE | UNAVAILABLE | ERROR
- `v11_packet_packet_type` - APPROVAL_PACKET | UNCLASSIFIED
- `v11_packet_summary` - Short non-prescriptive summary
- `v11_packet_components` - Object of embedded component records:
  - `explain_context` - PR122 record or minimal projection
  - `narrative` - PR123 record or minimal projection
  - `preview` - PR112 record or minimal projection
  - `approval_gate` - PR113 record or minimal projection
  - `approval_registry` - PR114 record or minimal projection
- `v11_packet_basis` - Array of field names used (references only)
- `v11_packet_artifacts` - Array of artifact labels

**Component Projection:**

To avoid duplicating large nested objects, components can be stored as:
1. **Full records** - Complete component with all fields
2. **Minimal projections** - Only mode/status/type/labels + basis/artifacts

**Example Approval Packet:**

```json
{
  "v11_packet_mode": "ON",
  "v11_packet_status": "AVAILABLE",
  "v11_packet_packet_type": "APPROVAL_PACKET",
  "v11_packet_summary": "approval packet assembled. context, narrative, preview, gate included. approval requirement labeled as REQUIRED. preview risk surface labeled as CONSTRAINED.",
  "v11_packet_components": {
    "explain_context": {
      "v11_explain_mode": "ON",
      "v11_explain_status": "AVAILABLE",
      "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW"],
      "v11_explain_basis": ["v11_regime_level", "v10_drift_level"]
    },
    "narrative": {
      "v11_narrative_mode": "ON",
      "v11_narrative_status": "AVAILABLE",
      "v11_narrative_style": "STANDARD",
      "v11_narrative_text": "current regime label indicates elevated uncertainty. structural drift label indicates low vocabulary shift."
    },
    "preview": {
      "v11_preview_mode": "ON",
      "v11_preview_status": "AVAILABLE",
      "v11_preview_risk_surface": "CONSTRAINED"
    },
    "approval_gate": {
      "v11_approval_mode": "ON",
      "v11_approval_status": "AVAILABLE",
      "v11_approval_requirement": "REQUIRED",
      "v11_approval_state": "UNREQUESTED"
    }
  },
  "v11_packet_basis": [
    "v11_regime_level",
    "v10_drift_level",
    "v10_execution_permission"
  ],
  "v11_packet_artifacts": [
    "pr110_regime_record",
    "pr120_drift_record",
    "pr101_execution_record"
  ]
}
```

**Packet Summary Templates:**

Non-prescriptive summary generation:
- "approval packet assembled."
- "context, narrative, preview, gate included."
- "approval requirement labeled as REQUIRED."
- "preview risk surface labeled as CONSTRAINED."

No "approve now", "execute", "do X" language.

**Constitutional Guarantees (PR124):**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals (SUI/USDC/BTC/ETH), addresses, amounts
- No numeric patterns (counts, percentages, scores)
- No forbidden vocabulary (good/bad, correct/wrong)
- No prescriptive language (should/must/need to)
- No prescriptive coupling ("approved therefore execute")
- No narrative coupling ("this means X", "therefore Y")
- **No cross-component coupling** (NEW):
  - No "APPROVED therefore ALLOW" patterns
  - No "REQUIRED so execute" patterns
  - No approval state proximity to execution verbs
  - No state label coupling to action words
- Defensive (never raises exceptions)
- Warning-only (exit 0 always)

**Usage Example:**

```python
from explain import V11HumanExplanationContextSchema
from narrative import build_human_narrative_v1
from packet import build_approval_packet_v1

# Create explanation context
explanation = V11HumanExplanationContextSchema.create_explanation_record(
    summary="current structural situation: regime medium, drift low, permission dry-run-only.",
    signals=["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
    basis=["v11_regime_level", "v10_drift_level", "v10_execution_permission"],
    artifacts=["pr110_regime_record", "pr120_drift_record", "pr101_execution_record"],
)

# Build narrative
narrative = build_human_narrative_v1(explanation, style="STANDARD")

# Assemble approval packet
packet = build_approval_packet_v1(
    explain_context_record=explanation,
    narrative_record=narrative,
    preview_record=preview,  # from PR112
    approval_gate_record=approval_gate,  # from PR113
)

print(packet["v11_packet_summary"])
# Output: "approval packet assembled. context, narrative, preview, gate included. approval requirement labeled as REQUIRED."

print(list(packet["v11_packet_components"].keys()))
# Output: ['explain_context', 'narrative', 'preview', 'approval_gate']
```

**Pipeline Flow (Complete):**

```
Observation (PR107) → Analytics (PR109) → Vocabulary (PR119)
         ↓
Drift Detection (PR120)
         ↓
Regime Classification (PR110)
         ↓
Policy Binding (PR111)
         ↓
Preview Engine (PR112)
         ↓
Approval Gate (PR113)
         ↓
Explanation Context (PR122) ← Bundles structural signals
         ↓
Narrative Builder (PR123) ← Human-readable story
         ↓
Approval Packet (PR124) ← Review unit carrier
         ↓
Human Review Renderer (PR125) ← Formats for display
         ↓
[Human Review Interface] (CLI/UI presentation ready)
```

### v1.1 Human Review Renderer v1 (PR125)

**Purpose:** Render approval packet (PR124) into human-readable format for CLI/UI display.

**Render = Display Shape (not instruction/conclusion)**

**Render Philosophy:**
```
Render ≠ Instruction
Render ≠ Conclusion
Render = Display Shape

Render provides:
  - Formatted output for human reading (Markdown/Text)
  - Structured presentation of packet contents
  - Non-prescriptive labels and state descriptions
  - Clear section organization

Render does NOT:
  - Recommend actions
  - Draw conclusions
  - Contain token names, amounts, addresses
  - Prescribe responses
  - Imply next steps
```

**Schema Fields:**
- `v11_render_mode` - ON | OFF
- `v11_render_status` - AVAILABLE | UNAVAILABLE | ERROR
- `v11_render_format` - MARKDOWN | TEXT
- `v11_render_style` - CONCISE | STANDARD | DETAILED
- `v11_render_summary` - Short non-prescriptive summary
- `v11_render_output` - Formatted text string (Markdown or plain text)
- `v11_render_basis` - Array of field names referenced

**Render Styles:**
- **CONCISE** - One screen view (minimal sections)
- **STANDARD** - Normal operation (Labels, Narrative, Preview, Approval)
- **DETAILED** - Full view (includes Basis & Artifacts)

**Render Sections (Markdown):**

1. **Title**: `# Approval Packet (READ-ONLY)`
2. **Labels**: Regime, drift, permission, preview, approval labels
3. **Narrative**: Human-readable story (PR123) - STANDARD/DETAILED only
4. **Preview**: Impact shape description (PR112) - STANDARD/DETAILED only
5. **Approval**: Gate + Registry state labels (PR113/114) - STANDARD/DETAILED only
6. **Metadata**: Basis & Artifacts - DETAILED only

**Example Rendered Output (STANDARD, Markdown):**

```markdown
# Approval Packet (READ-ONLY)

## Labels

- REGIME_MEDIUM
- DRIFT_LOW
- PERMISSION_DRY_RUN_ONLY
- PREVIEW_RISK_SURFACE: CONSTRAINED
- APPROVAL_REQUIREMENT: REQUIRED
- APPROVAL_STATE: UNREQUESTED

## Narrative

current regime label indicates elevated uncertainty. structural drift label indicates low vocabulary shift. execution permission label limits consideration to dry-run-only.

## Preview

Risk Surface: CONSTRAINED
Status: AVAILABLE

## Approval

Requirement: REQUIRED
State: UNREQUESTED
```

**Constitutional Guarantees (PR125):**
- No trading vocabulary (swap/buy/sell/execute/sign/transfer)
- No execution operations (transaction/broadcast/submit)
- No token literals (SUI/USDC/BTC/ETH), addresses, amounts
- No numeric patterns (counts, percentages, scores)
- No forbidden vocabulary (good/bad, correct/wrong)
- No prescriptive language (should/must/need to)
- No evaluative language (quality judgments)
- No causal coupling ("therefore", "so", "hence")
- Defensive (never raises exceptions)
- Warning-only (exit 0 always)

**Usage Example:**

```python
from packet import build_approval_packet_v1
from render import render_review_packet_v1

# Build approval packet (from PR124)
packet = build_approval_packet_v1(
    explain_context_record=explanation,
    narrative_record=narrative,
    preview_record=preview,
    approval_gate_record=approval_gate,
)

# Render for human review (MARKDOWN, STANDARD style)
render = render_review_packet_v1(packet, fmt="MARKDOWN", style="STANDARD")

# Display to terminal/UI
print(render["v11_render_output"])

# Try CONCISE style for compact view
concise_render = render_review_packet_v1(packet, fmt="MARKDOWN", style="CONCISE")
print(concise_render["v11_render_output"])

# Try TEXT format for plain terminal
text_render = render_review_packet_v1(packet, fmt="TEXT", style="STANDARD")
print(text_render["v11_render_output"])
```

**Style Comparison:**

```python
# CONCISE (one screen)
"""
# Approval Packet (READ-ONLY)

## Labels

- REGIME_MEDIUM
- DRIFT_LOW
- PERMISSION_DRY_RUN_ONLY
- APPROVAL_REQUIREMENT: REQUIRED
"""

# STANDARD (normal operation)
"""
# Approval Packet (READ-ONLY)

## Labels
[labels...]

## Narrative
[human-readable story...]

## Preview
[impact shape...]

## Approval
[gate state...]
"""

# DETAILED (everything)
"""
[...all sections plus...]

## Metadata

**Basis Fields:**
- v11_regime_level
- v10_drift_level
- v10_execution_permission

**Artifacts:**
- pr110_regime_record
- pr120_drift_record
- pr101_execution_record
"""
```

---

### Constitutional Constraints (v1.1)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **No amounts**: Numeric patterns prohibited
- **No token literals**: SUI, USDC, BTC, ETH prohibited
- **No addresses**: 0x... patterns prohibited
- **No trading vocabulary**: swap, buy, sell, execute, sign, transfer prohibited
- **Defensive**: Never raises exceptions
- **Warning-only**: Exit code always 0

### Run Validations (v1.1)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr110_entropy_regime_classification_smoke.py
python3 python/validation/pr111_regime_execution_policy_binding_smoke.py
python3 python/validation/pr112_execution_preview_engine_v1_smoke.py
python3 python/validation/pr113_human_approval_gate_v1_smoke.py
python3 python/validation/pr122_human_explanation_context_smoke.py
python3 python/validation/pr123_human_narrative_builder_v1_smoke.py
python3 python/validation/pr124_approval_packet_builder_v1_smoke.py
python3 python/validation/pr125_human_review_renderer_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.2 Continuous Permission Monitor (READ-ONLY)

### v1.2 Philosophy: Permission as State Trajectory

The Continuous Permission Monitor treats **permission as a state trajectory**, not a point-in-time flag.

**Key Principles:**
- **Permission = State Trajectory** - Track evolution over time, not isolated snapshots
- **Monitor ≠ Execution** - Monitoring does not trigger actions
- **Monitor ≠ Recommendation** - No prescriptive language or "should" statements
- **Transition Detection** - Identify permission degradation/recovery events
- **Suppression States** - Label trajectory direction: STABLE/DEGRADING/RECOVERING/SUPPRESSED
- **No Trajectory Coupling** - Forbid "permission improved therefore act" patterns

**Permission Monitor Philosophy:**
```
Monitor provides:
  - Permission state trajectory (sequence of permission labels)
  - Transition event detection (DEGRADATION/RECOVERY/SUPPRESSION)
  - Suppression state labels (STABLE/DEGRADING/RECOVERING/SUPPRESSED)
  - Non-prescriptive summary of state evolution
  - Basis field names (which artifacts informed state)

Monitor does NOT:
  - Recommend actions ("you should execute")
  - Evaluate quality (good/bad permissions)
  - Execute or trigger execution
  - Contain token names, amounts, addresses
  - Couple trajectory to action ("improved therefore act")
```

**Pipeline Position:**
```
Policy Binding (PR111)
         ↓
Execution Preview (PR112)
         ↓
Human Approval Gate (PR113)
         ↓
Permission Monitor (PR126) ← NEW: Track permission trajectory
         ↓
[Human Interface Layer]
```

### v1.2 Continuous Permission Monitor v1 (PR126)

**Purpose:** Monitor execution permission state evolution over time, detecting degradation/recovery transitions.

**Monitor Function:**
```python
from monitor import monitor_permission_v1

# Input: window of timestep records (each containing all artifacts)
records_window = [
    {"v10_execution_permission": "ALLOW", "v11_policy_permission": "ALLOW"},
    {"v10_execution_permission": "DRY_RUN_ONLY", "v11_policy_permission": "DRY_RUN_ONLY"},
    {"v10_execution_permission": "HOLD", "v11_policy_permission": "HOLD"},
]

# Monitor permission trajectory
monitor = monitor_permission_v1(
    records_window=records_window,
    window_label="MEDIUM",  # SHORT | MEDIUM | LONG (no numbers)
)

# Output schema (v12_monitor_ prefix)
print(monitor["v12_monitor_status"])              # AVAILABLE | UNAVAILABLE | ERROR
print(monitor["v12_monitor_current_permission"])  # HOLD | DRY_RUN_ONLY | ALLOW | UNKNOWN
print(monitor["v12_monitor_suppression_state"])   # STABLE | DEGRADING | RECOVERING | SUPPRESSED
print(monitor["v12_monitor_permission_trajectory"]) # ["ALLOW", "DRY_RUN_ONLY", "HOLD"]
print(monitor["v12_monitor_transition_events"])   # List of transition dicts
print(monitor["v12_monitor_summary"])             # Non-prescriptive summary
print(monitor["v12_monitor_basis"])               # ["v11_policy_permission", "v10_execution_permission"]
```

**Permission Source Priority (per timestep):**
1. If `v11_policy_permission` exists → use it
2. Else use `v10_execution_permission`
3. Default to `UNKNOWN`

**Permission Restrictiveness Order:**
```
HOLD (most restrictive)
  ↓
DRY_RUN_ONLY
  ↓
ALLOW
  ↓
UNKNOWN (least restrictive)
```

**Transition Detection:**
Emit transition event when permission label changes:
- **DEGRADATION** - Moving toward more restrictive (ALLOW → DRY_RUN_ONLY)
- **RECOVERY** - Moving toward less restrictive (HOLD → DRY_RUN_ONLY)
- **SUPPRESSION** - Transitioning to HOLD
- **PERMISSION_CHANGE** - Same restrictiveness level

**Suppression State (derived from last two steps):**
- If current permission == HOLD → **SUPPRESSED**
- If moved toward more restrictive → **DEGRADING**
- If moved toward less restrictive → **RECOVERING**
- Else → **STABLE**

**Example: ALLOW → DRY_RUN_ONLY → HOLD**
```python
window = [
    {"v10_execution_permission": "ALLOW"},
    {"v10_execution_permission": "DRY_RUN_ONLY"},
    {"v10_execution_permission": "HOLD"},
]
result = monitor_permission_v1(window)

# Step 1: ALLOW → DRY_RUN_ONLY
# - Event: DEGRADATION
# - Suppression state: DEGRADING

# Step 2: DRY_RUN_ONLY → HOLD
# - Event: SUPPRESSION
# - Suppression state: SUPPRESSED (current permission is HOLD)

print(result["v12_monitor_current_permission"])  # "HOLD"
print(result["v12_monitor_suppression_state"])   # "SUPPRESSED"
print(len(result["v12_monitor_transition_events"]))  # 2
```

**Example: HOLD → DRY_RUN_ONLY (Recovery)**
```python
window = [
    {"v10_execution_permission": "HOLD"},
    {"v10_execution_permission": "DRY_RUN_ONLY"},
]
result = monitor_permission_v1(window)

# Event: RECOVERY (moving toward less restrictive)
# Suppression state: RECOVERING

print(result["v12_monitor_current_permission"])  # "DRY_RUN_ONLY"
print(result["v12_monitor_suppression_state"])   # "RECOVERING"
print(result["v12_monitor_transition_events"][0]["event_type"])  # "RECOVERY"
```

**Transition Event Schema:**
```python
{
    "event_type": "DEGRADATION",        # DEGRADATION | RECOVERY | SUPPRESSION | PERMISSION_CHANGE
    "from_permission": "ALLOW",
    "to_permission": "DRY_RUN_ONLY",
    "position": 1,                      # Index in trajectory
}
```

**Defensive Design:**
- Invalid input (None, empty list) → Valid ERROR record
- Invalid window_label → Default to "MEDIUM"
- Missing permission fields → Default to "UNKNOWN"
- Always returns valid schema (never raises)

**Constitutional Guarantees (PR126):**
- **READ-ONLY** - No execution, no recommendations
- **Non-evaluative** - No good/bad vocabulary
- **Non-prescriptive** - No "should" language
- **No token literals** - No SUI, USDC, BTC, ETH
- **No amounts** - No numeric values in output
- **No addresses** - No 0x... patterns
- **No trajectory coupling** (NEW) - Forbid "permission improved therefore act"
- **Deterministic** - Same inputs → same outputs
- **Defensive** - Never raises exceptions

**NEW: Trajectory Coupling Guard (PR126)**

Detects and warns on action coupling to state trajectory:

```python
from monitor import check_trajectory_coupling

# Forbidden patterns:
check_trajectory_coupling("permission allowed therefore execute")
# → Warning: Trajectory coupling detected

check_trajectory_coupling("state is suppressed so stop operations")
# → Warning: Trajectory coupling detected

check_trajectory_coupling("recovering therefore proceed with action")
# → Warning: Trajectory coupling detected

# Clean patterns:
check_trajectory_coupling("current permission labeled as DRY_RUN_ONLY")
# → No warnings (labels state, no action coupling)
```

**Forbidden Trajectory Coupling Patterns:**
- "permission improved therefore act"
- "suppressed so do X"
- "recovering therefore execute"
- "if permission allowed then execute"
- "when recovering, proceed"
- State trajectory coupling to action

**Window Labels (no numbers):**
- `SHORT` - Recent history
- `MEDIUM` - Mid-term history
- `LONG` - Extended history

No window sizes are specified numerically to maintain constitutional constraints.

**Schema Fields (v12_monitor_ prefix):**
- `v12_monitor_mode` - ON | OFF
- `v12_monitor_status` - AVAILABLE | UNAVAILABLE | ERROR
- `v12_monitor_window` - SHORT | MEDIUM | LONG
- `v12_monitor_current_permission` - UNKNOWN | HOLD | DRY_RUN_ONLY | ALLOW
- `v12_monitor_permission_trajectory` - List of permission labels
- `v12_monitor_transition_events` - List of transition event dicts
- `v12_monitor_suppression_state` - STABLE | DEGRADING | RECOVERING | SUPPRESSED
- `v12_monitor_summary` - Non-prescriptive summary text
- `v12_monitor_basis` - Array of field names referenced

**Files:**
- `python/monitor/v12_permission_monitor_schema.py` - Schema definition
- `python/monitor/v12_continuous_permission_monitor_engine_v1.py` - Monitor engine
- `python/monitor/v12_monitor_constitutional_guard.py` - Constitutional validation
- `python/monitor/__init__.py` - Package exports

---

### v1.2 Permission Trajectory → Human Interface Binding v1 (PR127)

**Purpose:** Bind PR126 monitor records into human-readable trajectory signals for v1.1 Human Interface Layer (PR122-PR125).

**Binding Philosophy:**
```
Binding ≠ Conclusion
Trajectory ≠ Permission to act
Signal = Human-readable structural label

"改善"や"回復"は 状態記述 であり、次の一手 ではない
(Improvement/recovery is state description, not next action)
```

**Pipeline Integration:**
```
... → Policy (PR111) → Preview (PR112) → Approval Gate (PR113)
         ↓
Permission Monitor (PR126) → Trajectory Signal (PR127) ← NEW
         ↓
Explanation Context (PR122) → Narrative (PR123) → Packet (PR124) → Render (PR125)
```

**Binding Function:**
```python
from signal import bind_permission_trajectory_signal_v1
from monitor import monitor_permission_v1

# Step 1: Monitor permission trajectory (PR126)
monitor_record = monitor_permission_v1(records_window)

# Step 2: Bind to human interface signal (PR127)
signal = bind_permission_trajectory_signal_v1(monitor_record)

# Output schema (v12_signal_ prefix)
print(signal["v12_signal_status"])              # AVAILABLE | UNAVAILABLE | ERROR
print(signal["v12_signal_permission_level"])    # HOLD | DRY_RUN_ONLY | ALLOW | UNKNOWN
print(signal["v12_signal_suppression_state"])   # STABLE | DEGRADING | RECOVERING | SUPPRESSED
print(signal["v12_signal_transition_label"])    # NONE | DEGRADATION | RECOVERY | SUPPRESSION
print(signal["v12_signal_window_label"])        # SHORT | MEDIUM | LONG (no numbers)
print(signal["v12_signal_summary"])             # Non-prescriptive summary
print(signal["v12_signal_basis"])               # ["v12_monitor_*"] field names
```

**Static Mapping (v1):**
```
Monitor → Signal Binding:

v12_monitor_current_permission → v12_signal_permission_level
v12_monitor_suppression_state → v12_signal_suppression_state
v12_monitor_window → v12_signal_window_label

Transition Events:
  event_type == "DEGRADATION" → transition_label = DEGRADATION
  event_type == "RECOVERY" → transition_label = RECOVERY
  event_type == "SUPPRESSION" → transition_label = SUPPRESSION
  event_type == "PERMISSION_CHANGE" → transition_label = NONE

Summary Template (non-prescriptive):
  "permission level labeled as {level}. suppression state labeled as {state}."
  NO "therefore", "so", "execute", "should"
```

**Example: DEGRADATION Signal**
```python
monitor = {
    "v12_monitor_status": "AVAILABLE",
    "v12_monitor_current_permission": "DRY_RUN_ONLY",
    "v12_monitor_suppression_state": "DEGRADING",
    "v12_monitor_transition_events": [{
        "event_type": "DEGRADATION",
        "from_permission": "ALLOW",
        "to_permission": "DRY_RUN_ONLY",
    }],
    "v12_monitor_window": "MEDIUM",
}

signal = bind_permission_trajectory_signal_v1(monitor)

# Result:
# v12_signal_permission_level: "DRY_RUN_ONLY"
# v12_signal_suppression_state: "DEGRADING"
# v12_signal_transition_label: "DEGRADATION"
# v12_signal_summary: "permission level labeled as DRY_RUN_ONLY. suppression state labeled as DEGRADING. transition labeled as DEGRADATION. window labeled as MEDIUM."
```

**Example: RECOVERY Signal**
```python
monitor = {
    "v12_monitor_status": "AVAILABLE",
    "v12_monitor_current_permission": "DRY_RUN_ONLY",
    "v12_monitor_suppression_state": "RECOVERING",
    "v12_monitor_transition_events": [{
        "event_type": "RECOVERY",
        "from_permission": "HOLD",
        "to_permission": "DRY_RUN_ONLY",
    }],
    "v12_monitor_window": "SHORT",
}

signal = bind_permission_trajectory_signal_v1(monitor)

# Result:
# v12_signal_permission_level: "DRY_RUN_ONLY"
# v12_signal_suppression_state: "RECOVERING"
# v12_signal_transition_label: "RECOVERY"
```

**Human Interface Extension (Optional):**

Extend PR122 explanation context with trajectory signals:

```python
from explain.v12_explain_context_permission_trajectory_extension import (
    extend_explanation_context_with_trajectory_signals,
    get_trajectory_signal_types,
)

# Extend context with trajectory signals (append-only, backward compatible)
extended_context = extend_explanation_context_with_trajectory_signals(
    context_record=context,  # PR122 context
    trajectory_signal=signal,  # PR127 signal
)

# New signal types added to context:
# TRAJECTORY_DEGRADING - Permission trajectory moving toward more restrictive
# TRAJECTORY_RECOVERING - Permission trajectory moving toward less restrictive
# TRAJECTORY_SUPPRESSED - Permission trajectory currently suppressed
# TRAJECTORY_STABLE - Permission trajectory stable (no change)
```

**Strengthened Trajectory Coupling Guard:**

PR127 adds signal-specific coupling detection:

```python
from signal import check_signal_trajectory_coupling

# Forbidden patterns:
check_signal_trajectory_coupling("level improved therefore execute")
# → Warning: Signal trajectory coupling detected

check_signal_trajectory_coupling("state degrading so halt operations")
# → Warning: Signal trajectory coupling detected

check_signal_trajectory_coupling("recovering means proceed")
# → Warning: Signal trajectory coupling detected

# Clean patterns:
check_signal_trajectory_coupling("permission level labeled as DRY_RUN_ONLY")
# → No warnings (labels state, no action coupling)
```

**Forbidden Signal Coupling Patterns:**
- "level improved therefore act"
- "state degrading so halt"
- "recovering means execute"
- "if stable then execute"
- "transition indicates action"
- Signal label coupling to action

**Defensive Design:**
- Invalid input (None, empty dict) → Valid ERROR record
- Monitor ERROR → Signal ERROR
- Monitor UNAVAILABLE → Signal ERROR
- Always returns valid schema (never raises)

**Constitutional Guarantees (PR127):**
- **READ-ONLY** - No execution, no recommendations
- **Non-evaluative** - No good/bad vocabulary
- **Non-prescriptive** - No "should" language
- **No token literals** - No SUI, USDC, BTC, ETH
- **No amounts** - No numeric values in output
- **No addresses** - No 0x... patterns
- **No trajectory coupling** - Strengthened guard for signal patterns
- **Deterministic** - Same inputs → same outputs
- **Defensive** - Never raises exceptions

**Schema Fields (v12_signal_ prefix):**
- `v12_signal_mode` - ON | OFF
- `v12_signal_status` - AVAILABLE | UNAVAILABLE | ERROR
- `v12_signal_permission_level` - UNKNOWN | HOLD | DRY_RUN_ONLY | ALLOW
- `v12_signal_suppression_state` - STABLE | DEGRADING | RECOVERING | SUPPRESSED
- `v12_signal_transition_label` - NONE | DEGRADATION | RECOVERY | SUPPRESSION
- `v12_signal_window_label` - SHORT | MEDIUM | LONG (no numbers)
- `v12_signal_summary` - Non-prescriptive summary text
- `v12_signal_basis` - Array of v12_monitor_* field names referenced

**Files:**
- `python/signal/v12_permission_trajectory_signal_schema.py` - Signal schema definition
- `python/signal/v12_permission_trajectory_binding_engine_v1.py` - Binding engine
- `python/signal/v12_signal_constitutional_guard.py` - Constitutional validation (strengthened)
- `python/signal/__init__.py` - Package exports
- `python/explain/v12_explain_context_permission_trajectory_extension.py` - Human interface extension

**Final Declaration (PR127):**

Japanese:
```
PR126 は許可の揺れを記録した。
PR127 はその揺れを、人間が読める信号に変換した。
それは指示ではない。軌跡の表示である。
```

English:
```
PR126 recorded permission as trajectory.
PR127 renders that trajectory into human-readable signals.
This is not instruction. This is trajectory display.
```

---

### v1.2 Role × Distortion Eligibility Engine v1 (PR128)

**Purpose:** Classify eligibility based on Role × Distortion × Regime × Boundary × Suppression. This is a labeling engine (not action, not recommendation).

**Eligibility Philosophy:**
```
Eligibility ≠ Permission ≠ Action
Eligibility = "Touchability classification"

Eligibility provides:
  - Asset functional role label
  - Market distortion type label
  - Regime × Role × Distortion alignment
  - Hard boundary exclusions
  - Permission trajectory integration

Eligibility does NOT:
  - Recommend actions
  - Execute or trigger execution
  - Contain token names, amounts, addresses
  - Prescribe responses
```

**Classification Function:**
```python
from eligibility import classify_role_distortion_eligibility_v1

# Input: Regime, Distortion, Role, Boundary, Permission Monitor records
result = classify_role_distortion_eligibility_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    role_record={"v12_role_type": "VOLATILITY_ROLE"},
    boundary_record={"v9_boundary_type": "UNCLASSIFIED"},
    permission_monitor_record={"v12_monitor_suppression_state": "STABLE"},
)

# Output schema (v12_elig_ prefix)
print(result.v12_elig_status)        # AVAILABLE | ERROR
print(result.v12_elig_eligibility)   # INELIGIBLE | ELIGIBLE_CONSIDERATION_ONLY | ELIGIBLE_DRY_RUN_ONLY
print(result.v12_elig_summary)       # Non-prescriptive summary
print(result.v12_elig_signals)       # {"regime": "REGIME_MEDIUM", "role": "VOLATILITY_ROLE", ...}
print(result.v12_elig_basis)         # ["v11_regime_level", "v12_distortion_type", ...]
```

**Static Classification Rules (first-match-wins):**

```
1. REGIME_CRITICAL → INELIGIBLE
   Hard stop: Critical regime gates all eligibility

2. Hard Boundary (SCHEMA/DATA/ENGINE) → INELIGIBLE
   Hard stop: Boundary violations gate eligibility

3. Suppression = SUPPRESSED → INELIGIBLE
   Hard stop: Suppressed permission trajectory gates eligibility

4. REGIME_HIGH → ELIGIBLE_DRY_RUN_ONLY
   High regime limits to dry-run only

5. REGIME_LOW → ELIGIBLE_DRY_RUN_ONLY
   Low regime limits to dry-run only

6. REGIME_MEDIUM:
   a. VOLATILITY_ROLE × Defined Distortion (D1-D5) → ELIGIBLE_CONSIDERATION_ONLY
      The only "consideration zone" alignment

   b. else → ELIGIBLE_DRY_RUN_ONLY
      MEDIUM without volatility-role + distortion alignment

7. Default (UNCLASSIFIED regime) → ELIGIBLE_DRY_RUN_ONLY
   Defensive default
```

**Eligibility Labels:**
- **INELIGIBLE** - Not touchable (hard stops)
- **ELIGIBLE_CONSIDERATION_ONLY** - May be considered (MEDIUM × VOLATILITY × D1-D5 only)
- **ELIGIBLE_DRY_RUN_ONLY** - Dry-run simulation only

**Role Types (asset functional role):**
- `VOLATILITY_ROLE` - Volatility-bearing assets
- `LIQUIDITY_ROLE` - Liquidity provision assets
- `STABILITY_ROLE` - Stable value assets
- `HEDGE_ROLE` - Hedging instruments
- `GAS_ROLE` - Gas/fee payment assets
- `UNCLASSIFIED` - Unknown role

**Distortion Types (market structure distortions):**
- `D1_LIQUIDATION` - Liquidation cascade patterns
- `D2_RANGE_STICKINESS` - Price range adhesion
- `D3_BOOK_HOLLOWING` - Order book depth erosion
- `D4_EVENT_DISTORTION` - Event-driven distortions
- `D5_CORRELATION_DISTORTION` - Correlation breakdown
- `UNCLASSIFIED` - Unknown distortion

**Regime Labels (from PR110):**
- `REGIME_LOW` - Low entropy
- `REGIME_MEDIUM` - Medium entropy
- `REGIME_HIGH` - High entropy
- `REGIME_CRITICAL` - Critical entropy
- `UNCLASSIFIED` - Unknown regime

**Boundary Types (from PR105-PR108):**
- `SCHEMA_BOUNDARY` - Schema constraint violation
- `DATA_BOUNDARY` - Data quality violation
- `ENGINE_BOUNDARY` - Engine computation violation
- `TEMPORAL_BOUNDARY` - Time-based constraint
- `SAMPLING_BOUNDARY` - Sampling constraint
- `UNCLASSIFIED` - No boundary violation

**Suppression States (from PR126):**
- `STABLE` - Permission trajectory stable
- `DEGRADING` - Permission trajectory degrading
- `RECOVERING` - Permission trajectory recovering
- `SUPPRESSED` - Permission trajectory suppressed
- `UNCLASSIFIED` - Unknown suppression state

**Example: CRITICAL Regime → INELIGIBLE**
```python
result = classify_role_distortion_eligibility_v1(
    regime_record={"v11_regime_level": "REGIME_CRITICAL"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    role_record={"v12_role_type": "VOLATILITY_ROLE"},
)

# Result:
# v12_elig_eligibility: "INELIGIBLE"
# v12_elig_summary: "eligibility label indicates ineligible under critical regime."
```

**Example: MEDIUM × VOLATILITY × D1 → CONSIDERATION_ONLY**
```python
result = classify_role_distortion_eligibility_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    role_record={"v12_role_type": "VOLATILITY_ROLE"},
)

# Result:
# v12_elig_eligibility: "ELIGIBLE_CONSIDERATION_ONLY"
# v12_elig_summary: "eligibility label indicates consideration-only under medium regime with volatility role and defined distortion."
```

**Example: Hard Boundary → INELIGIBLE**
```python
result = classify_role_distortion_eligibility_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    role_record={"v12_role_type": "VOLATILITY_ROLE"},
    boundary_record={"v9_boundary_type": "SCHEMA_BOUNDARY"},
)

# Result:
# v12_elig_eligibility: "INELIGIBLE"
# v12_elig_summary: "eligibility label indicates ineligible under hard boundary type."
```

**Example: Suppressed Permission → INELIGIBLE**
```python
result = classify_role_distortion_eligibility_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    role_record={"v12_role_type": "VOLATILITY_ROLE"},
    permission_monitor_record={"v12_monitor_suppression_state": "SUPPRESSED"},
)

# Result:
# v12_elig_eligibility: "INELIGIBLE"
# v12_elig_summary: "eligibility label indicates ineligible under suppressed permission trajectory."
```

**Defensive Design:**
- Invalid input (None, empty dict) → Defensive default (ELIGIBLE_DRY_RUN_ONLY)
- Exception during classification → ERROR record (INELIGIBLE)
- Unknown regime → Defensive default (ELIGIBLE_DRY_RUN_ONLY)
- Always returns valid record (never raises)

**Constitutional Guarantees (PR128):**
- **READ-ONLY** - No execution, no recommendations
- **Non-evaluative** - No good/bad vocabulary
- **Non-prescriptive** - No "should" language
- **No token literals** - No SUI, USDC, BTC, ETH
- **No amounts** - No numeric values in output
- **No addresses** - No 0x... patterns
- **No trading vocabulary** - No swap, buy, sell, execute, sign, transfer
- **No eligibility coupling** - No "eligible therefore act" patterns
- **Deterministic** - Same inputs → same outputs
- **Defensive** - Never raises exceptions

**Schema Fields (v12_elig_ prefix):**
- `v12_elig_mode` - ON | OFF
- `v12_elig_status` - AVAILABLE | ERROR
- `v12_elig_eligibility` - INELIGIBLE | ELIGIBLE_CONSIDERATION_ONLY | ELIGIBLE_DRY_RUN_ONLY
- `v12_elig_summary` - Non-prescriptive summary text
- `v12_elig_signals` - Dict of label signals (regime, distortion, role, boundary, suppression)
- `v12_elig_basis` - Array of field names referenced
- `v12_elig_warnings` - Optional array of warnings

**Files:**
- `python/eligibility/v12_role_distortion_eligibility_schema.py` - Schema definition
- `python/eligibility/v12_role_distortion_eligibility_engine_v1.py` - Classification engine
- `python/eligibility/v12_eligibility_constitutional_guard.py` - Constitutional validation
- `python/eligibility/__init__.py` - Package exports

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` from entropy regime classification
- **Role (PR130)**: `v12_role_type` from asset role classification
- **Distortion (PR129)**: `v12_distortion_type` from distortion detection
- **Boundary (PR105-PR108)**: `v9_boundary_type` from boundary detection
- **Permission Monitor (PR126)**: `v12_monitor_suppression_state` from permission trajectory

**Philosophy (PR128):**
```
Eligibility = Touchability classification
Role = Asset functional role
Distortion = Market structure aberration
Regime × Role × Distortion = Alignment signal

This is not permission.
This is not action.
This is structural alignment detection.
```

---

### v1.2 Distortion Detector v1 (PR129)

**Purpose:** Classify market structure distortion types (D0-D5) from existing pipeline artifacts.

**What is Distortion?**

Distortion ≠ Signal
Distortion ≠ Recommendation
Distortion = Structural label (failure-mode classification)

**Distortion Types:**

```python
D0_NONE                     # No distortion (REGIME_CRITICAL state)
D1_LIQUIDATION             # Decrease + forced events
D2_RANGE_STICKINESS        # Stable liquidity + low drift
D3_BOOK_HOLLOWING          # Low liquidity + decrease
D4_EVENT_DISTORTION        # Event activity present
D5_CORRELATION_DISTORTION  # Correlation drift detected
DISTORTION_UNCLASSIFIED    # Default when no rules match
```

**Classification Rules (First-match-wins):**

1. **REGIME_CRITICAL** → D0_NONE (no distortion in critical regime)
2. **Event activity present** → D4_EVENT_DISTORTION (unless also decrease → D1)
3. **Correlation present + drift >= MEDIUM** → D5_CORRELATION_DISTORTION
4. **Low liquidity + decrease** → D3_BOOK_HOLLOWING (unless also events → D1)
5. **Decrease + events** → D1_LIQUIDATION (priority over D3/D4)
6. **Stable liquidity + no events + low drift** → D2_RANGE_STICKINESS
7. **Default** → DISTORTION_UNCLASSIFIED

**Example:**

```python
from distortion import detect_distortion_v1, D1_LIQUIDATION, D4_EVENT_DISTORTION

# Detect distortion from pipeline artifacts
result = detect_distortion_v1(
    regime_record=regime,
    analytics_record=analytics,
    drift_record=drift,
    bridge_record=bridge,
)

# Check distortion type
if result["v12_distortion_type"] == D1_LIQUIDATION:
    print("Liquidation distortion detected")
elif result["v12_distortion_type"] == D4_EVENT_DISTORTION:
    print("Event distortion detected")
```

**Distortion Schema Fields:**

```python
{
    "v12_distortion_mode": "ON",
    "v12_distortion_status": "AVAILABLE",
    "v12_distortion_type": "D1_LIQUIDATION",
    "v12_distortion_summary": "distortion label classified as D1_LIQUIDATION...",
    "v12_distortion_basis": ["object_dynamics", "event_activity_present"],
    "v12_distortion_artifacts": ["v109_analytics", "v108_bridge"],
}
```

**Files:**
- `python/distortion/v12_distortion_schema.py` - Schema definition
- `python/distortion/v12_distortion_detector_engine_v1.py` - Detection engine
- `python/distortion/v12_distortion_constitutional_guard.py` - Constitutional validation
- `python/distortion/__init__.py` - Package exports

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` for D0_NONE detection
- **Analytics (PR109)**: `event_activity_present`, `liquidity_regime`, `object_dynamics`
- **Drift (PR120)**: `v10_drift_label`, `v10_vocab_family_presence`
- **Bridge (PR108)**: `event_activity` fallback

**Constitutional Guarantees (PR129):**
- READ-ONLY classification only
- No token literals (SUI, USDC, BTC, ETH)
- No numeric patterns (counts, percentages)
- No prescriptive language ("should", "must")
- No distortion coupling ("D1 therefore act") ← NEW
- Warning-only guards (never fail)

**Philosophy (PR129):**
```
Distortion = Structural aberration label
D1-D5 = Failure mode classification
Detection = Pattern recognition (not judgment)

This is not signal.
This is not recommendation.
This is structural classification.
```

---

### v1.2 Role Carrier Qualification Engine v1 (PR130)

**Purpose:** Assess asset-to-role fit through 4-axis asset profile analysis.

**What is Role Carrier Qualification?**

Qualification ≠ Signal
Qualification ≠ Recommendation
Qualification = Structural fit classification

**4-Axis Asset Profile:**

```python
# Observability: Can role-bearing properties be structurally observed?
OBS_LOW, OBS_MEDIUM, OBS_HIGH

# Censorship Resistance: Can asset function persist under constraint?
CENS_LOW, CENS_MEDIUM, CENS_HIGH

# Liquidatability: Can role be rebalanced under stress?
LIQ_LOW, LIQ_MEDIUM, LIQ_HIGH

# Dependency: Does it depend on external systems that can fail?
DEP_NONE, DEP_LOW, DEP_MEDIUM, DEP_HIGH
```

**5 Role Types:**

```python
GAS_ROLE           # Network operation utility carrier
STABILITY_ROLE     # Value stability carrier
LIQUIDITY_ROLE     # Market depth carrier
VOLATILITY_ROLE    # Price movement carrier
HEDGE_ROLE         # Directional offset carrier
```

**Role Requirements (Example: GAS_ROLE):**

```python
{
    "min_observability": OBS_HIGH,           # Must be highly observable
    "min_censorship_resistance": CENS_HIGH,  # Must resist censorship
    "min_liquidatability": LIQ_MEDIUM,       # Moderate liquidity needed
    "max_dependency": DEP_LOW,               # Low dependency tolerance
}
```

**Qualification Logic:**

1. Check each axis against role requirements
2. Track failed axes
3. Return:
   - **QUALIFIED**: 0 failures (all axes meet requirements)
   - **PARTIALLY_QUALIFIED**: 1-3 failures (some axes meet requirements)
   - **DISQUALIFIED**: 4 failures (no axes meet requirements)

**Example:**

```python
from role import (
    V12AssetProfileSchema,
    qualify_asset_for_role_v1,
    GAS_ROLE,
    QUALIFIED,
    OBS_HIGH,
    CENS_HIGH,
    LIQ_MEDIUM,
    DEP_LOW,
)

# Step 1: Create asset profile
asset_profile = V12AssetProfileSchema.create_asset_profile(
    observability=OBS_HIGH,
    censorship_resistance=CENS_HIGH,
    liquidatability=LIQ_MEDIUM,
    dependency=DEP_LOW,
)

# Step 2: Assess fit for GAS_ROLE
result = qualify_asset_for_role_v1(asset_profile, GAS_ROLE)

# Check qualification
if result["v12_role_carrier_qualification_status"] == QUALIFIED:
    print("Asset QUALIFIED for GAS_ROLE")
    print(f"Failed axes: {result['v12_role_carrier_failed_axes']}")
```

**Qualification Schema Fields:**

```python
{
    "v12_role_carrier_mode": "ON",
    "v12_role_carrier_status": "AVAILABLE",
    "v12_role_carrier_role_type": "GAS_ROLE",
    "v12_role_carrier_qualification_status": "QUALIFIED",
    "v12_role_carrier_failed_axes": [],
    "v12_role_carrier_summary": "asset labeled QUALIFIED for GAS_ROLE...",
    "v12_role_carrier_basis": ["asset_profile_observability", ...],
}
```

**Files:**
- `python/role/v12_asset_profile_schema.py` - Asset profile definition
- `python/role/v12_role_requirements_schema.py` - Role requirements
- `python/role/v12_role_carrier_qualification_schema.py` - Qualification schema
- `python/role/v12_role_carrier_qualification_engine_v1.py` - Qualification engine
- `python/role/v12_role_carrier_constitutional_guard.py` - Constitutional validation
- `python/role/__init__.py` - Package exports

**Integration Points:**
- **Eligibility (PR128)**: Uses `v12_role_type` from qualification
- **Distortion (PR129)**: Combines with distortion for eligibility assessment
- **Future**: Asset profile can be enriched by observation/analytics layers

**Constitutional Guarantees (PR130):**
- READ-ONLY classification only
- No token literals (SUI, USDC, BTC, ETH, DEEP, CETUS)
- No numeric patterns (counts, percentages, scores)
- No prescriptive language ("should", "must")
- No role coupling ("QUALIFIED therefore act") ← NEW
- Warning-only guards (never fail)

**Philosophy (PR130):**
```
Asset Profile = Abstract structural descriptor
Role = Functional carrier classification
Qualification = Structural fit assessment

Profile describes observable properties.
Role defines required properties.
Qualification labels the match.

This is not signal.
This is not recommendation.
This is structural classification.
```

---

### v1.2 Role × Distortion × Regime Contribution Model v1 (PR131)

**Purpose:** Classify structural return contribution from regime × role × distortion combinations.

**What is Contribution?**

Contribution ≠ Performance
Contribution ≠ Return guarantee
Contribution = Structural side-effect label

**Core Thesis:**
Returns emerge not from "trading skill" but from market design constraints:
1. Structure is intelligible (MEDIUM regime)
2. Touchability is constrained (eligibility gates)
3. Distortion is present (failure mode exists)

Meridian creates a market that suppresses action in non-intelligible regimes. Returns exist only where structure is intelligible and touchability is constrained.

**Contribution Labels:**

```python
CONTRIB_STRONGLY_POSITIVE  # ++ (primary alpha zone)
CONTRIB_POSITIVE           # + (secondary zone)
CONTRIB_NEUTRAL            # 0 (no contribution by design)
CONTRIB_NEGATIVE           # - (structure breakdown risk)
CONTRIB_STRONGLY_NEGATIVE  # -- (critical regime)
CONTRIB_UNKNOWN            # ? (unclassified)
```

**Classification Rules (First-match-wins):**

1. **REGIME_CRITICAL** → CONTRIB_STRONGLY_NEGATIVE (always)
2. **INELIGIBLE** → CONTRIB_NEUTRAL (no touchability by design)
3. **REGIME_HIGH** → CONTRIB_NEGATIVE (mostly), CONTRIB_NEUTRAL for VOLATILITY × D1/D3/D4
4. **REGIME_LOW** → CONTRIB_NEUTRAL (thin opportunity)
5. **REGIME_MEDIUM** → Primary alpha zone:
   - VOLATILITY × D1-D5 × ELIGIBLE_CONSIDERATION_ONLY → **CONTRIB_STRONGLY_POSITIVE**
   - VOLATILITY × D1-D5 (other) → CONTRIB_POSITIVE
   - LIQUIDITY × D1/D3 → CONTRIB_POSITIVE
   - STABILITY → CONTRIB_NEUTRAL
   - HEDGE × D5 → CONTRIB_POSITIVE
   - GAS → CONTRIB_NEUTRAL

**Example:**

```python
from contribution import classify_contribution_v1, CONTRIB_STRONGLY_POSITIVE

# Primary alpha zone: MEDIUM × VOLATILITY × D1 × ELIGIBLE_CONSIDERATION_ONLY
result = classify_contribution_v1(
    regime_level="REGIME_MEDIUM",
    role_type="VOLATILITY_ROLE",
    distortion_type="D1_LIQUIDATION",
    eligibility_label="ELIGIBLE_CONSIDERATION_ONLY",
)

# Check contribution
if result["v12_contrib_contribution_label"] == CONTRIB_STRONGLY_POSITIVE:
    print("Primary alpha zone detected")
    print(f"Rationale: {result['v12_contrib_contribution_rationale']}")
    # Output: ['DISTORTION_CAPTURE_ZONE', 'STRUCTURE_INTELLIGIBLE']
```

**Contribution Schema Fields:**

```python
{
    "v12_contrib_mode": "ON",
    "v12_contrib_status": "AVAILABLE",
    "v12_contrib_regime_level": "REGIME_MEDIUM",
    "v12_contrib_role_type": "VOLATILITY_ROLE",
    "v12_contrib_distortion_type": "D1_LIQUIDATION",
    "v12_contrib_eligibility_label": "ELIGIBLE_CONSIDERATION_ONLY",
    "v12_contrib_contribution_label": "CONTRIB_STRONGLY_POSITIVE",
    "v12_contrib_contribution_rationale": [
        "DISTORTION_CAPTURE_ZONE",
        "STRUCTURE_INTELLIGIBLE"
    ],
    "v12_contrib_summary": "contribution labeled CONTRIB_STRONGLY_POSITIVE...",
    "v12_contrib_basis": ["regime_level", "role_type", "distortion_type", "eligibility_label"],
}
```

**Files:**
- `python/contribution/v12_contribution_schema.py` - Schema definition
- `python/contribution/v12_role_distortion_regime_contribution_engine_v1.py` - Classification engine
- `python/contribution/v12_contribution_constitutional_guard.py` - Constitutional validation
- `python/contribution/__init__.py` - Package exports
- `python/explain/v12_explain_context_contribution_extension.py` - PR122 integration

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` for entropy classification
- **Role (PR130)**: `v12_role_type` for asset role
- **Distortion (PR129)**: `v12_distortion_type` for market structure aberration
- **Eligibility (PR128)**: `v12_eligibility_label` for touchability gate
- **Explanation (PR122)**: Append-only signal extension

**Constitutional Guarantees (PR131):**
- READ-ONLY classification only
- No numeric patterns whatsoever (digits, %, decimals, time periods)
- No token literals (SUI, USDC, BTC, ETH, DEEP, CETUS)
- No return guarantee language ("assured", "annual return", "backtest")
- No prescriptive language ("should", "must")
- No contribution coupling ("++ therefore trade", "-- therefore stop") ← NEW
- Warning-only guards (never fail)

**Philosophy (PR131):**
```
Contribution = Where returns can exist as structural side-effect
Market Design = Restrict touchability to intelligible regimes
Alpha = Side-effect of constraint, not skill

MEDIUM regime = Primary alpha zone (structure intelligible)
HIGH regime = Structure breaking down (negative contribution)
CRITICAL regime = Structure broken (strongly negative)
LOW regime = Opportunity thin (neutral contribution)

This is not performance model.
This is not return guarantee.
This is structural constraint model.

"年利30%" comes from design (restricting where you touch),
not from trading skill.
```

---

### v1.2 Contribution → Constraint Binding v1 (PR132)

**Purpose:** Bind contribution model (PR131) to existing pipeline as non-prescriptive constraint labels.

**What is Binding?**

Binding ≠ Decision
Binding ≠ Instruction
Binding = Label propagation

**Zone Labels:**

```python
CONTRIB_ZONE_PRIMARY    # Contribution center (MEDIUM × VOLATILITY × D1-D5)
CONTRIB_ZONE_SECONDARY  # Non-MEDIUM regime (HIGH/LOW)
CONTRIB_ZONE_BLOCKED    # Critical/Ineligible/Suppressed
CONTRIB_ZONE_NONE       # Default (no zone detected)
```

**Binding Rules (First-match-wins):**

1. **REGIME_CRITICAL** → `CONTRIB_ZONE_BLOCKED` (always blocked)
2. **INELIGIBLE** → `CONTRIB_ZONE_BLOCKED` (no touchability)
3. **SUPPRESSED** (PR126) → `CONTRIB_ZONE_BLOCKED` (permission suppressed)
4. **REGIME_HIGH or LOW** → `CONTRIB_ZONE_SECONDARY` (non-MEDIUM)
5. **REGIME_MEDIUM × VOLATILITY × D1-D5** → `CONTRIB_ZONE_PRIMARY` (contribution center)
6. **Default** → `CONTRIB_ZONE_NONE` (no zone)

**Example:**

```python
from bind import bind_contribution_constraints_v1, CONTRIB_ZONE_PRIMARY

# Bind contribution to constraint labels
result = bind_contribution_constraints_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
)

# Check zone
if result["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_PRIMARY:
    print("Primary contribution zone observed")
    print(f"Constraints: {result['v12_contrib_constraint_labels']}")
    # Output: ['contrib_primary_medium_volatility_distortion']
```

**Constraint Schema Fields:**

```python
{
    "v12_contrib_constraint_mode": "ON",
    "v12_contrib_constraint_status": "AVAILABLE",
    "v12_contrib_constraint_zone_label": "CONTRIB_ZONE_PRIMARY",
    "v12_contrib_constraint_labels": [
        "contrib_primary_medium_volatility_distortion"
    ],
    "v12_contrib_constraint_regime_level": "REGIME_MEDIUM",
    "v12_contrib_constraint_role_type": "VOLATILITY_ROLE",
    "v12_contrib_constraint_distortion_type": "D1_LIQUIDATION",
    "v12_contrib_constraint_summary": "contribution zone labeled CONTRIB_ZONE_PRIMARY...",
    "v12_contrib_constraint_basis": ["regime_level", "role_type", "distortion_type"],
}
```

**Files:**
- `python/bind/v12_contribution_constraint_schema.py` - Schema definition
- `python/bind/v12_contribution_constraint_binding_engine_v1.py` - Binding engine
- `python/bind/v12_contribution_binding_constitutional_guard.py` - Constitutional validation
- `python/bind/__init__.py` - Package exports
- `python/bridge/v12_contrib_constraints_to_explain_context_extension.py` - PR122 integration

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` → zone classification
- **Role (PR130)**: `v12_role_carrier_role_type` → PRIMARY zone filter
- **Distortion (PR129)**: `v12_distortion_type` → PRIMARY zone filter
- **Eligibility (PR128)**: `v12_eligibility_status` → BLOCKED zone check
- **Permission Monitor (PR126)**: `v12_monitor_suppression_state` → BLOCKED zone check
- **Explanation (PR122)**: Append-only constraint labels

**Constitutional Guarantees (PR132):**
- READ-ONLY binding (label propagation only)
- No numeric patterns
- No token literals
- No trading vocabulary
- No prescriptive language
- No contribution zone coupling ("primary therefore trade", "blocked so stop") ← NEW
- Warning-only guards (never fail)

**Philosophy (PR132):**
```
Binding = Label propagation (not decision)
Zone = Structural observation (not recommendation)
Constraint = Label for explain/plan/preview (not instruction)

PRIMARY zone = Contribution center observed
SECONDARY zone = Non-MEDIUM regime observed
BLOCKED zone = Critical/ineligible/suppressed observed
NONE zone = Default (no zone detected)

Binding does NOT change behavior.
Binding does NOT trigger execution.
Binding ONLY appends labels to existing pipeline.

This is NOT decision logic.
This is NOT instruction.
This is label propagation for human interface and artifact chain-of-custody.
```

---

### v1.2 Role Rescue Relation v1 (PR133)

**Purpose:** Classify ROLE→ROLE structural rescue relations as dependency edges (not actions, not recommendations).

**What is Rescue?**

Rescue ≠ Action
Rescue ≠ Recommendation
Rescue = Structural dependency edge

**Edge Types:**

```python
RESCUE_EDGE_BUFFER      # Role provides stability buffer to target
RESCUE_EDGE_ANCHOR      # Role provides anchoring/reference for target
RESCUE_EDGE_CONTINUITY  # Role provides continuity/operational support
RESCUE_EDGE_ESCAPE      # Role provides escape valve for target
RESCUE_EDGE_DAMPEN      # Role dampens volatility for target
RESCUE_EDGE_UNCLASSIFIED # Relation exists but type unclear
```

**Strength Levels:**

```python
RESCUE_STRENGTH_NONE     # No rescue relation present
RESCUE_STRENGTH_WEAK     # Minimal structural support
RESCUE_STRENGTH_MODERATE # Moderate structural support
RESCUE_STRENGTH_STRONG   # Strong structural support
```

**Classification Rules (First-match-wins):**

1. **Hard stops → NONE**:
   - `REGIME_CRITICAL`
   - `SCHEMA_BOUNDARY`, `DATA_BOUNDARY`, `ENGINE_BOUNDARY`
   - `SUPPRESSED` (PR126)
   - `INELIGIBLE` (PR128)
2. **REGIME_HIGH or LOW** → max strength `WEAK` (capped)
3. **REGIME_MEDIUM** → Use distortion × role mapping:
   - `STABILITY → VOLATILITY` (D1/D5) → `BUFFER`/`ANCHOR`, `MODERATE`
   - `LIQUIDITY → VOLATILITY` (D2/D3) → `DAMPEN`, `MODERATE`
   - `HEDGE → VOLATILITY` (D4/D5) → `BUFFER`, `WEAK`
   - `GAS → VOLATILITY` (any) → `CONTINUITY`, `WEAK`
   - `LIQUIDITY → STABILITY` (D2/D3) → `DAMPEN`, `WEAK`
   - `STABILITY → LIQUIDITY` (D2/D3) → `ANCHOR`, `WEAK`
4. **Default** → `UNCLASSIFIED`, `WEAK`

**Example:**

```python
from rescue import (
    classify_role_rescue_relation_v1,
    RESCUE_EDGE_BUFFER,
    RESCUE_STRENGTH_MODERATE,
    ROLE_STABILITY,
    ROLE_VOLATILITY,
)

# Classify rescue relation
result = classify_role_rescue_relation_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    role_from=ROLE_STABILITY,
    role_to=ROLE_VOLATILITY,
)

# Check rescue edge
if result["v12_rescue_strength"] != "NONE":
    print(f"Rescue edge: {result['v12_rescue_edge_type']}")
    print(f"Strength: {result['v12_rescue_strength']}")
    # Output: BUFFER, MODERATE
```

**Rescue Relation Schema Fields:**

```python
{
    "v12_rescue_mode": "READ_ONLY",
    "v12_rescue_status": "AVAILABLE",
    "v12_rescue_relation_type": "ROLE_RESCUE_RELATION",
    "v12_rescue_role_from": "STABILITY_ROLE",
    "v12_rescue_role_to": "VOLATILITY_ROLE",
    "v12_rescue_edge_type": "BUFFER",
    "v12_rescue_strength": "MODERATE",
    "v12_rescue_summary": "Role rescue relation from STABILITY_ROLE to VOLATILITY_ROLE may provide edge type BUFFER with strength MODERATE.",
    "v12_rescue_basis": ["v11_regime_level", "v12_distortion_type"],
    "v12_rescue_regime_level": "REGIME_MEDIUM",
    "v12_rescue_distortion_type": "D1_LIQUIDATION",
}
```

**Files:**
- `python/rescue/v12_role_rescue_relation_schema.py` - Schema definition with edge types and strength levels
- `python/rescue/v12_role_rescue_relation_engine_v1.py` - Classification engine with first-match-wins rules
- `python/rescue/v12_rescue_constitutional_guard.py` - Constitutional validation with rescue coupling guard
- `python/rescue/__init__.py` - Package exports

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` → strength caps and hard stops
- **Distortion (PR129)**: `v12_distortion_type` → edge type classification
- **Role (PR130)**: `role_from` × `role_to` → structural rescue mapping
- **Eligibility (PR128)**: `v12_eligibility_status` → INELIGIBLE blocks rescue
- **Permission Monitor (PR126)**: `v12_monitor_suppression_state` → SUPPRESSED blocks rescue
- **Boundary (PR111)**: Hard boundaries → rescue blocked

**Constitutional Guarantees (PR133):**
- READ-ONLY classification (no execution)
- No numeric patterns
- No token literals
- No trading vocabulary
- No prescriptive language
- No rescue coupling ("rescue therefore act", "buffer so trade") ← NEW
- Warning-only guards (never fail)

**Philosophy (PR133):**
```
Rescue = Structural dependency edge (not action)
Edge = Label propagation (not recommendation)
Strength = Structural support level (not priority)

BUFFER edge = Stability buffer observed
ANCHOR edge = Anchoring reference observed
CONTINUITY edge = Operational support observed
ESCAPE edge = Escape valve observed
DAMPEN edge = Volatility dampening observed

Rescue does NOT instruct action.
Rescue does NOT change behavior.
Rescue ONLY classifies structural dependency as labeled edge.

This is NOT decision logic.
This is NOT instruction.
This is label propagation for structural dependency graph.
```

**Use Cases:**

1. **Role graph construction**: Build ROLE→ROLE dependency graph for visualization
2. **Structural analysis**: Understand which roles support which other roles
3. **Explain context**: Add rescue edges to PR122 explanation context
4. **Plan artifact**: Include rescue relations in planning artifacts
5. **Human review**: Present structural dependencies to human operators

---

### v1.2 Distortion Subtype Taxonomy & Classifier v1 (PR134)

**Purpose:** Classify distortion subtypes (D1A-D5C) for fine-grained distortion taxonomy.

**What is a Subtype?**

Subtype ≠ Action
Subtype ≠ Signal
Subtype = Fine-grained label propagation

**Distortion Subtype Taxonomy (v1):**

```python
# D1 (Liquidation) Subtypes
D1A_FORCED_FLOW       # Forced liquidation flow detected
D1B_CASCADE_RISK      # Cascade liquidation risk observed
D1C_STRESS_UNWIND     # Stress position unwinding observed

# D2 (Range Stickiness) Subtypes
D2A_MEAN_REVERT_PRESSURE  # Mean reversion pressure observed
D2B_RANGE_PINNING         # Range pinning behavior observed
D2C_BREAKOUT_FAKEOUT      # Breakout fakeout pattern observed

# D3 (Book Hollowing) Subtypes
D3A_TOP_GAP              # Top-of-book gap observed
D3B_DEPTH_EVAPORATION    # Depth evaporation observed
D3C_SPREAD_SHOCK         # Spread shock observed

# D4 (Event Distortion) Subtypes
D4A_EVENT_SPIKE       # Event spike observed
D4B_EVENT_AFTERSHOCK  # Event aftershock observed
D4C_EVENT_SILENCE     # Event silence observed

# D5 (Correlation Distortion) Subtypes
D5A_COUPLING_TIGHTEN  # Coupling tightening observed
D5B_DECOUPLING        # Decoupling observed
D5C_ROTATION_PRESSURE # Rotation pressure observed
```

**Classification Rules (First-match-wins):**

1. **Invalid inputs** → `ERROR`
2. **Parent distortion D1-D5** → classify subtype using qualitative inputs:
   - **D1**: market_cost_regime × liquidity_regime
   - **D2**: range_pattern
   - **D3**: book_pattern
   - **D4**: event_pattern
   - **D5**: correlation_pattern
3. **Default** → first subtype for parent (D1A, D2A, D3A, D4A, D5A)

**Example:**

```python
from distortion import (
    classify_distortion_subtype_v1,
    SUBTYPE_D1B_CASCADE_RISK,
    D1_LIQUIDATION,
)

# Classify D1 subtype
result = classify_distortion_subtype_v1(
    parent_distortion_record={"v12_distortion_type": D1_LIQUIDATION},
    analytics={
        "market_cost_regime": "HIGH",
        "liquidity_regime": "DECREASING",
    },
)

# Check subtype
if result["v12_subtype_label"] == SUBTYPE_D1B_CASCADE_RISK:
    print("Cascade risk subtype detected")
    # Output: D1B_CASCADE_RISK
```

**Subtype Schema Fields:**

```python
{
    "v12_subtype_mode": "READ_ONLY",
    "v12_subtype_status": "AVAILABLE",
    "v12_subtype_parent_distortion": "D1_LIQUIDATION",
    "v12_subtype_label": "D1B_CASCADE_RISK",
    "v12_subtype_summary": "Distortion subtype D1B_CASCADE_RISK observed for parent distortion D1_LIQUIDATION.",
    "v12_subtype_basis": ["v12_distortion_type", "analytics"],
}
```

**Files:**
- `python/distortion/v12_distortion_subtype_schema.py` - Subtype taxonomy with 15 subtypes
- `python/distortion/v12_distortion_subtype_classifier_v1.py` - Classification engine
- `python/distortion/v12_distortion_subtype_constitutional_guard.py` - Subtype coupling guard
- `python/distortion/__init__.py` - Updated package exports (PR129 + PR134)

**Integration Points:**
- **Parent Distortion (PR129)**: `v12_distortion_type` → subtype classification
- **Analytics**: Qualitative labels (market_cost_regime, liquidity_regime, etc.) → subtype selection
- **Eligibility (PR128)**: Subtypes available for future eligibility refinement (append-only, does not change PR128 rules yet)

**Constitutional Guarantees (PR134):**
- READ-ONLY classification (no execution)
- No numeric patterns
- No token literals
- No trading vocabulary
- No prescriptive language
- No subtype coupling ("D1B therefore act", "subtype implies trade") ← NEW
- Warning-only guards (never fail)

**Philosophy (PR134):**
```
Subtype = Fine-grained label (not action)
D1A/D1B/D1C = Liquidation variants (not recommendations)
Classification = Static deterministic mapping (not learning)

Subtypes refine parent distortion types with qualitative labels.
Subtypes do NOT change behavior.
Subtypes ONLY provide fine-grained taxonomy for:
  - Human review and explanation
  - Future eligibility refinement (v2)
  - Structural analysis and pattern detection
  - Artifact labeling and chain-of-custody

This is NOT decision logic.
This is NOT instruction.
This is label propagation for fine-grained distortion taxonomy.
```

**Use Cases:**

1. **Fine-grained explanation**: Explain D1B cascade risk vs D1A forced flow
2. **Pattern detection**: Identify recurring subtype patterns over time
3. **Future eligibility**: Enable subtype-specific eligibility rules (v2)
4. **Human review**: Present detailed distortion classification to operators
5. **Artifact labeling**: Tag records with fine-grained distortion subtypes

**Note:** PR134 is append-only. It does NOT change PR128 eligibility rules. Subtype-specific eligibility refinement is reserved for future PRs.

---

### v1.2 Edge Type Classification Engine v1 (PR135)

**Purpose:** Classify edge types for regime × role × distortion combinations as structural labels.

**What is EdgeType?**

EdgeType ≠ Action
EdgeType ≠ Recommendation
EdgeType = Structural label propagation

**Edge Type Labels (v1):**

```python
EDGE_NONE      # No edge classification (default/unclassified)
EDGE_AMPLIFY   # Amplification pattern observed (MEDIUM × VOLATILITY × distortion)
EDGE_SHIELD    # Shielding pattern observed (CRITICAL/GAS/STABILITY/HEDGE)
EDGE_LEAK      # Leak pattern observed (HIGH × LIQUIDITY × distortion)
EDGE_NEUTRAL   # Neutral pattern observed (LOW regime or baseline)
```

**Classification Rules (First-match-wins):**

1. **Invalid inputs** → `EDGE_NEUTRAL` (defensive, never errors)
2. **REGIME_CRITICAL** → `EDGE_SHIELD` (always shield)
3. **GAS_ROLE** → `EDGE_SHIELD` (always shield)
4. **STABILITY_ROLE** + distortion in {D1,D3,D4,D5} → `EDGE_SHIELD`
5. **HEDGE_ROLE** + regime in {MEDIUM,HIGH,CRITICAL} → `EDGE_SHIELD`
6. **LIQUIDITY_ROLE** + regime in {HIGH,CRITICAL} → `EDGE_LEAK`
7. **LIQUIDITY_ROLE** + regime MEDIUM → `EDGE_NEUTRAL`
8. **REGIME_MEDIUM + VOLATILITY_ROLE** + distortion D1-D5 → `EDGE_AMPLIFY`
9. **REGIME_HIGH** → `EDGE_LEAK` (esp LIQUIDITY + D3)
10. **REGIME_LOW** → `EDGE_NEUTRAL`
11. **Default** → `EDGE_NEUTRAL` (defensive)

**Example:**

```python
from edge import (
    classify_edge_type_v1,
    EDGE_AMPLIFY,
)

# Classify edge type
result = classify_edge_type_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    subtype_record={"v12_subtype_label": "D1B_CASCADE_RISK"},
)

# Check edge type
if result["v12_edge_type"] == EDGE_AMPLIFY:
    print("Amplification edge detected")
    # Output: EDGE_AMPLIFY
```

**Edge Type Schema Fields:**

```python
{
    "v12_edge_mode": "READ_ONLY",
    "v12_edge_status": "AVAILABLE",
    "v12_edge_type": "EDGE_AMPLIFY",
    "v12_edge_regime": "REGIME_MEDIUM",
    "v12_edge_role": "VOLATILITY_ROLE",
    "v12_edge_distortion": "D1_LIQUIDATION",
    "v12_edge_subtype_label": "D1B_CASCADE_RISK",
    "v12_edge_summary": "Edge type EDGE_AMPLIFY may indicate structural pattern for REGIME_MEDIUM × VOLATILITY_ROLE × D1_LIQUIDATION.",
    "v12_edge_basis": ["v11_regime_level", "v12_role_carrier_role_type", "v12_distortion_type", "v12_subtype_label"],
}
```

**Files:**
- `python/edge/v12_edge_type_schema.py` - Edge type schema with 5 labels
- `python/edge/v12_edge_type_classifier_v1.py` - Classification engine with first-match-wins rules
- `python/edge/v12_edge_constitutional_guard.py` - Edge coupling guard
- `python/edge/__init__.py` - Package exports

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` → edge classification
- **Role (PR130)**: `v12_role_carrier_role_type` → edge classification
- **Distortion (PR129)**: `v12_distortion_type` → edge classification
- **Distortion Subtype (PR134)**: `v12_subtype_label` → optional refinement
- **Contribution (PR131)**: `v12_contrib_contribution_label` → optional annotation
- **Constraints (PR132)**: `v12_contrib_constraint_zone_label` → optional annotation

**Constitutional Guarantees (PR135):**
- READ-ONLY classification (no execution)
- No numeric patterns
- No token literals
- No trading vocabulary
- No prescriptive language
- No edge coupling ("EDGE_AMPLIFY therefore trade", "EDGE_SHIELD so stop") ← NEW
- Warning-only guards (never fail)
- Defensive error handling (never raises)

**Philosophy (PR135):**
```
EdgeType = Structural label (not action)
EDGE_AMPLIFY = Amplification pattern observed (not "go ahead")
EDGE_SHIELD = Shielding pattern observed (not "protect yourself")
EDGE_LEAK = Leak pattern observed (not "avoid this")
EDGE_NEUTRAL = Neutral pattern observed (not "baseline safe")

Edge types classify structural patterns in regime × role × distortion space.
Edge types do NOT instruct action.
Edge types do NOT change behavior.
Edge types ONLY provide structural labels for:
  - Human review and explanation
  - Pattern recognition across time
  - Structural analysis and visualization
  - Artifact labeling and chain-of-custody

This is NOT decision logic.
This is NOT instruction.
This is label propagation for structural pattern classification.
```

**Use Cases:**

1. **Structural pattern analysis**: Identify AMPLIFY/SHIELD/LEAK patterns across regime transitions
2. **Human explanation**: Present edge type context to operators for review
3. **Pattern visualization**: Build time-series graphs of edge type transitions
4. **Artifact labeling**: Tag records with structural edge type labels
5. **Integration with contribution/constraints**: Combine with PR131/PR132 for multi-layer labeling

---

### v1.2 Rescue Strength Classification Engine v1 (PR136)

**Purpose:** Classify rescue strength (RESCUE_NONE/WEAK/MEDIUM/STRONG) with strict conditions for STRONG requiring explicit ALLOW_RESCUE_STRONG constraint binding.

**What is Rescue Strength?**

RescueStrength ≠ Action
RescueStrength ≠ Recommendation
RescueStrength = Structural label propagation

**Rescue Strength Labels (v1):**

```python
RESCUE_NONE     # No rescue strength (default/blocked)
RESCUE_WEAK     # Weak rescue strength observed
RESCUE_MEDIUM   # Medium rescue strength observed
RESCUE_STRONG   # Strong rescue strength observed (strict conditions)
```

**Classification Rules (First-match-wins):**

0. **Invalid inputs** → `RESCUE_NONE` (defensive, never errors)
1. **REGIME_CRITICAL** → `RESCUE_NONE`
2. **INELIGIBLE** → `RESCUE_NONE`
3. **EDGE_LEAK** → `RESCUE_NONE`
3.5. **ELIGIBLE_DRY_RUN_ONLY** → cap at `RESCUE_WEAK`
4. **RESCUE_STRONG (strict)**:
   - REGIME_MEDIUM + EDGE_SHIELD + STABILITY/HEDGE + D1/D4/D5
   - constraint_binding contains "ALLOW_RESCUE_STRONG"
   - eligibility != INELIGIBLE and != ELIGIBLE_DRY_RUN_ONLY
   - NEVER for VOLATILITY_ROLE or EDGE_AMPLIFY
5. **RESCUE_MEDIUM**:
   - REGIME_MEDIUM + SHIELD/NEUTRAL + STABILITY/HEDGE/LIQUIDITY
6. **RESCUE_WEAK**:
   - REGIME_HIGH/LOW + EDGE_SHIELD
7. **Default** → `RESCUE_NONE`

**Example:**

```python
from rescue import (
    classify_rescue_strength_v1,
    RESCUE_STRONG,
)

# Classify rescue strength (STRONG requires ALLOW_RESCUE_STRONG)
result = classify_rescue_strength_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
    distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    edge_record={"v12_edge_type": "EDGE_SHIELD"},
    eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
    constraint_binding_record={"v12_contrib_constraint_labels": ["ALLOW_RESCUE_STRONG"]},
)

# Check rescue strength
if result["v12_rescue_strength"] == RESCUE_STRONG:
    print("Strong rescue strength observed")
    # Output: RESCUE_STRONG
```

**Rescue Strength Schema Fields:**

```python
{
    "v12_rescue_mode": "READ_ONLY",
    "v12_rescue_status": "AVAILABLE",
    "v12_rescue_strength": "RESCUE_STRONG",
    "v12_rescue_regime": "REGIME_MEDIUM",
    "v12_rescue_role": "STABILITY_ROLE",
    "v12_rescue_distortion": "D1_LIQUIDATION",
    "v12_rescue_edge_type": "EDGE_SHIELD",
    "v12_rescue_eligibility": "ELIGIBLE_CONSIDERATION_ONLY",
    "v12_rescue_summary": "Rescue strength RESCUE_STRONG may indicate structural pattern for REGIME_MEDIUM × STABILITY_ROLE × D1_LIQUIDATION × EDGE_SHIELD.",
    "v12_rescue_basis": ["v11_regime_level", "v12_role_carrier_role_type", "v12_distortion_type", "v12_edge_type"],
}
```

**Files:**
- `python/rescue/v12_rescue_strength_schema.py` - Rescue strength schema with 4 labels
- `python/rescue/v12_rescue_strength_engine_v1.py` - Classification engine with strict STRONG conditions
- `python/rescue/v12_rescue_constitutional_guard.py` - Rescue coupling guard (updated)
- `python/rescue/__init__.py` - Package exports

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` → strength classification and blocking
- **Role (PR130)**: `v12_role_carrier_role_type` → strength classification
- **Distortion (PR129)**: `v12_distortion_type` → STRONG conditions (D1/D4/D5)
- **Edge Type (PR135)**: `v12_edge_type` → STRONG requires EDGE_SHIELD, blocks EDGE_LEAK
- **Eligibility (PR128)**: `v12_eligibility_status` → INELIGIBLE blocks, DRY_RUN_ONLY caps at WEAK
- **Constraints (PR132)**: `v12_contrib_constraint_labels` → ALLOW_RESCUE_STRONG enables STRONG

**Constitutional Guarantees (PR136):**
- READ-ONLY classification (no execution)
- No numeric patterns
- No token literals
- No trading vocabulary
- No prescriptive language
- No rescue coupling ("RESCUE_STRONG therefore trade", "strong rescue means proceed") ← ENHANCED
- Warning-only guards (never fail)
- Defensive error handling (never raises)

**Philosophy (PR136):**
```
RescueStrength = Structural label (not action)
RESCUE_STRONG = Strong structural pattern observed (not "act now")
RESCUE_MEDIUM = Medium structural pattern observed (not "consider acting")
RESCUE_WEAK = Weak structural pattern observed (not "minor action ok")
RESCUE_NONE = No structural pattern observed (not "blocked")

Rescue strength classifies structural pattern strength in regime × role × distortion × edge space.
Rescue strength does NOT instruct action.
Rescue strength does NOT change behavior.
Rescue strength ONLY provides structural labels for:
  - Human review and explanation
  - Pattern strength recognition across time
  - Structural analysis and visualization
  - Artifact labeling and chain-of-custody

RESCUE_STRONG has strict conditions to prevent false positives:
  - Requires explicit ALLOW_RESCUE_STRONG constraint binding
  - Never granted to VOLATILITY_ROLE or EDGE_AMPLIFY
  - Blocked by DRY_RUN_ONLY eligibility status
  - Only for STABILITY/HEDGE roles with specific distortions (D1/D4/D5)

This is NOT decision logic.
This is NOT instruction.
This is label propagation for structural pattern strength classification.
```

**Use Cases:**

1. **Structural strength analysis**: Identify strong/medium/weak rescue patterns across regime transitions
2. **Human explanation**: Present rescue strength context to operators for review
3. **Pattern strength visualization**: Build time-series graphs of rescue strength transitions
4. **Artifact labeling**: Tag records with structural rescue strength labels
5. **Integration with edge types**: Combine with PR135 edge types for multi-layer structural labeling
6. **Constraint binding validation**: ALLOW_RESCUE_STRONG acts as explicit gatekeeper for STRONG classification

---

### v1.2 Rescue Flow Graph Engine v1 (PR137)

**Purpose:** Build READ-ONLY graph artifact describing ROLE-to-ROLE rescue structure using label-only edges from PR135 EdgeType and PR136 RescueStrength.

**What is a Rescue Flow Graph?**

FlowGraph ≠ Action
FlowGraph ≠ Instruction
FlowGraph = Structural mapping

**Graph Structure:**

```python
# Nodes: 5 ROLE labels (fixed)
GAS_ROLE
STABILITY_ROLE
LIQUIDITY_ROLE
VOLATILITY_ROLE
HEDGE_ROLE

# Edges: Label-only connections with edge_type + rescue_strength
{
    "from_role": "STABILITY_ROLE",
    "to_role": "VOLATILITY_ROLE",
    "edge_type": "EDGE_SHIELD",           # PR135
    "rescue_strength": "RESCUE_MEDIUM",   # PR136
    "conditions": ["REGIME_MEDIUM", "D1_LIQUIDATION"],
    "note": "Stability provides shielding support to volatility role"
}
```

**Canonical Rescue Map (v1):**

```python
# Fixed structural edges (v1)
STABILITY_ROLE -> LIQUIDITY_ROLE  (EDGE_SHIELD)
STABILITY_ROLE -> VOLATILITY_ROLE (EDGE_SHIELD)
HEDGE_ROLE     -> VOLATILITY_ROLE (EDGE_SHIELD)
LIQUIDITY_ROLE -> VOLATILITY_ROLE (EDGE_NEUTRAL)
GAS_ROLE       -> ALL_ROLES       (EDGE_NEUTRAL)
```

**Non-rescue Constraints:**

- `EDGE_AMPLIFY` edges must have `RESCUE_NONE` (amplify ≠ rescue)
- `EDGE_LEAK` edges must have `RESCUE_NONE` (leak ≠ rescue)

**Rescue Strength Assignment:**

1. Match from PR136 `rescue_strength_records` by (role, regime, distortion, edge_type) if provided
2. Conservative defaults if not provided:
   - REGIME_MEDIUM + EDGE_SHIELD from STABILITY/HEDGE → `RESCUE_MEDIUM`
   - REGIME_HIGH/LOW + EDGE_SHIELD → `RESCUE_WEAK`
   - Default → `RESCUE_NONE`

**Example:**

```python
from flow import (
    build_rescue_flow_graph_v1,
    FLOW_MODE_ON,
)

# Build rescue flow graph
result = build_rescue_flow_graph_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_catalog_record={"v12_distortion_type": "D1_LIQUIDATION"},
)

# Check flow graph
if result["v12_flow_mode"] == FLOW_MODE_ON:
    print(f"Flow graph has {len(result['v12_flow_nodes'])} nodes")
    print(f"Flow graph has {len(result['v12_flow_edges'])} edges")

    # Inspect edges
    for edge in result["v12_flow_edges"]:
        print(f"{edge['from_role']} -> {edge['to_role']}: {edge['edge_type']} ({edge['rescue_strength']})")
```

**Flow Graph Schema Fields:**

```python
{
    "v12_flow_mode": "ON",
    "v12_flow_status": "AVAILABLE",
    "v12_flow_graph_type": "RESCUE_FLOW_GRAPH",
    "v12_flow_summary": "Rescue flow graph available. 5 role nodes and 8 rescue edges assembled as structural mapping.",
    "v12_flow_nodes": ["GAS_ROLE", "STABILITY_ROLE", "LIQUIDITY_ROLE", "VOLATILITY_ROLE", "HEDGE_ROLE"],
    "v12_flow_edges": [
        {
            "from_role": "STABILITY_ROLE",
            "to_role": "LIQUIDITY_ROLE",
            "edge_type": "EDGE_SHIELD",
            "rescue_strength": "RESCUE_MEDIUM",
            "conditions": ["REGIME_MEDIUM", "EDGE_SHIELD", "D1_LIQUIDATION"],
            "note": "Stability provides shielding support to liquidity role"
        },
        // ... more edges
    ],
    "v12_flow_basis": ["v11_regime_level", "v12_distortion_type"],
}
```

**Graph Visualization Example:**

```
STABILITY_ROLE ─[EDGE_SHIELD, RESCUE_MEDIUM]─> LIQUIDITY_ROLE
               └[EDGE_SHIELD, RESCUE_MEDIUM]─> VOLATILITY_ROLE

HEDGE_ROLE     ─[EDGE_SHIELD, RESCUE_MEDIUM]─> VOLATILITY_ROLE

LIQUIDITY_ROLE ─[EDGE_NEUTRAL, RESCUE_NONE]──> VOLATILITY_ROLE

GAS_ROLE       ─[EDGE_NEUTRAL, RESCUE_NONE]──> STABILITY_ROLE
               ├[EDGE_NEUTRAL, RESCUE_NONE]──> LIQUIDITY_ROLE
               ├[EDGE_NEUTRAL, RESCUE_NONE]──> VOLATILITY_ROLE
               └[EDGE_NEUTRAL, RESCUE_NONE]──> HEDGE_ROLE
```

**Files:**
- `python/flow/v12_rescue_flow_graph_schema.py` - Flow graph schema with edge structure
- `python/flow/v12_rescue_flow_graph_engine_v1.py` - Graph builder with canonical map
- `python/flow/v12_flow_constitutional_guard.py` - Flow coupling guard
- `python/flow/__init__.py` - Package exports

**Integration Points:**
- **Regime (PR110)**: `v11_regime_level` → rescue strength defaults
- **Role (PR130)**: ROLE labels as graph nodes
- **Distortion (PR129)**: `v12_distortion_type` → conditions labeling
- **Edge Type (PR135)**: `v12_edge_type` → edge classification
- **Rescue Strength (PR136)**: `v12_rescue_strength` → edge strength annotation
- **Constraints (PR132)**: `v12_contrib_constraint_labels` → optional constraints

**Constitutional Guarantees (PR137):**
- READ-ONLY graph construction (no execution)
- No numeric patterns
- No token literals (only ROLE labels)
- No trading vocabulary
- No prescriptive language
- No flow coupling ("this edge means execute", "strong rescue therefore trade") ← NEW
- Warning-only guards (never fail)
- Defensive error handling (never raises)

**Philosophy (PR137):**
```
FlowGraph = Structural mapping (not action)
Edges = Label-only connections (not instructions)
Rescue = Structural dependency (not recommendation)

Flow graph nodes are ROLE labels ONLY.
Flow graph edges are structural annotations ONLY.

EDGE_SHIELD + RESCUE_MEDIUM = Shielding pattern with medium strength observed (not "use this edge")
EDGE_NEUTRAL + RESCUE_NONE = Neutral pattern with no rescue observed (not "ignore this")

Flow graph describes structural ROLE-to-ROLE relationships.
Flow graph does NOT instruct action.
Flow graph does NOT change behavior.
Flow graph ONLY provides structural mapping for:
  - Human review and visualization
  - Pattern analysis across regime transitions
  - Structural dependency understanding
  - Artifact labeling and chain-of-custody

Canonical map is FIXED (v1).
No dynamic edge generation.
No role creation.
No token/asset/pool/address references.

This is NOT decision logic.
This is NOT instruction.
This is label propagation for structural ROLE-to-ROLE mapping.
```

**Use Cases:**

1. **Structural visualization**: Render ROLE-to-ROLE rescue graph for human operators
2. **Pattern analysis**: Track how rescue edges change across regime transitions
3. **Human explanation**: Present structural dependencies in explainable format
4. **Artifact labeling**: Tag flow graphs with structural rescue context
5. **Integration with PR135/PR136**: Combine edge types and rescue strengths for multi-layer analysis
6. **Canonical baseline**: Use fixed canonical map as structural reference point

---

### v1.2 Rescue Flow → Human Review Renderer Extension v1 (PR138)

**Purpose:** Extend Human Review Renderer (PR125) to display Rescue Flow Graph (PR137) as label-only structure visible to humans.

**What is Rescue Flow Rendering?**

Render = Display shape (not instruction)
Rescue Flow Render = Structural mapping visible to humans

**Extension:**

Adds optional Rescue Flow section to review render output with ROLE-to-ROLE structural rescue edges.

**Rendering Rules:**

- **CONCISE**: No rescue flow (omitted)
- **STANDARD**: Up to 8 edges, sorted by priority (no conditions)
- **DETAILED**: All edges + conditions + basis

**Edge Sorting Priority:**

1. `rescue_strength` (STRONG > MEDIUM > WEAK > NONE)
2. `edge_type` (EDGE_SHIELD first)
3. `from_role` (STABILITY > HEDGE > LIQUIDITY > VOLATILITY > GAS)

**Example Output (STANDARD style):**

```markdown
## Rescue Flow

ROLE-to-ROLE structural rescue mapping (label-only):

- STABILITY_ROLE → VOLATILITY_ROLE | EDGE_SHIELD | RESCUE_MEDIUM
- STABILITY_ROLE → LIQUIDITY_ROLE | EDGE_SHIELD | RESCUE_MEDIUM
- HEDGE_ROLE → VOLATILITY_ROLE | EDGE_SHIELD | RESCUE_WEAK
- GAS_ROLE → STABILITY_ROLE | EDGE_NEUTRAL | RESCUE_NONE
```

**Example Output (DETAILED style):**

```markdown
## Rescue Flow

ROLE-to-ROLE structural rescue mapping (label-only):

- STABILITY_ROLE → VOLATILITY_ROLE | EDGE_SHIELD | RESCUE_MEDIUM | conditions: REGIME_MEDIUM, EDGE_SHIELD, D1_LIQUIDATION
- STABILITY_ROLE → LIQUIDITY_ROLE | EDGE_SHIELD | RESCUE_MEDIUM | conditions: REGIME_MEDIUM, EDGE_SHIELD
- HEDGE_ROLE → VOLATILITY_ROLE | EDGE_SHIELD | RESCUE_WEAK | conditions: REGIME_MEDIUM, EDGE_SHIELD
```

**Usage:**

```python
from render import render_review_packet_v1
from flow import build_rescue_flow_graph_v1

# Build flow graph (PR137)
flow_graph = build_rescue_flow_graph_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_catalog_record={"v12_distortion_type": "D1_LIQUIDATION"},
)

# Render review packet with rescue flow (PR138)
result = render_review_packet_v1(
    packet_record=packet,
    fmt="MARKDOWN",
    style="STANDARD",
    rescue_flow_graph=flow_graph,  # Optional parameter
)

# Check output
if "## Rescue Flow" in result["v11_render_output"]:
    print("Rescue Flow section included in render")
```

**Files:**
- `python/render/v11_review_render_schema.py` - Extended with `v11_render_sections_present`
- `python/render/v12_rescue_flow_render_adapter.py` - Adapter for projecting flow graph
- `python/render/v11_human_review_renderer_engine_v1.py` - Extended with rescue flow section
- `python/render/v11_render_constitutional_guard.py` - Extended with flow coupling guard

**Integration Points:**
- **Human Review Renderer (PR125)**: Extended with optional rescue flow section
- **Rescue Flow Graph (PR137)**: Rendered as label-only structure
- **Edge Type (PR135)**: Displayed in edge format
- **Rescue Strength (PR136)**: Displayed in edge format

**Constitutional Guarantees (PR138):**
- Backward compatible (optional parameter, defaults to no rescue flow)
- CONCISE style excludes rescue flow
- STANDARD/DETAILED include rescue flow if provided
- No token literals (only ROLE labels)
- No numeric patterns
- No trading vocabulary
- No prescriptive language
- No flow coupling ("this edge means execute") ← ENFORCED
- Warning-only guards (never fail)

**Philosophy (PR138):**
```
Render = Display shape (not instruction)
Rescue Flow Render = Structural mapping visible to humans

The rendered rescue flow shows ROLE-to-ROLE edges with:
  - Label-only format
  - Non-prescriptive wording
  - Constitutional guarantees enforced

EDGE_SHIELD + RESCUE_MEDIUM displayed = Shielding pattern with medium strength observed
NOT: "use this edge"
NOT: "this means act"
NOT: "execute based on this"

Rescue flow render provides:
  - Human-readable structural mapping
  - Label-only edge presentation
  - Non-prescriptive context display

Rescue flow render does NOT:
  - Recommend actions
  - Imply next steps
  - Contain trading instructions
  - Include token/amount/address references
```

**Use Cases:**

1. **Human review**: Present structural rescue mapping to operators
2. **Visual context**: Show ROLE-to-ROLE relationships in approval packet
3. **Audit trail**: Include structural context in review artifacts
4. **Explanation**: Add rescue flow context to human-readable output
5. **Backward compatibility**: Render works with or without rescue flow parameter

---

### v1.2 Rescue Flow Narrative Extension v1 (PR139)

**Purpose:** Add Rescue Flow Graph (PR137) to Human Narrative Builder (PR123) output as "structural explanation" (not instruction/conclusion).

**What is Rescue Flow Narrative?**

Narrative ≠ Instruction ≠ Conclusion
Rescue Flow Narrative = Structural description in natural language

**Extension:**

Adds rescue flow structural narrative to human-readable explanation context with label-focused text generation.

**Text Generation Rules:**

- **CONCISE**: 1-2 lines (existence statement only)
- **STANDARD**: 2-4 paragraphs (existence, support directions, strength distribution)
- **DETAILED**: STANDARD + up to 6 edge lines

**Text Style:**

- Deterministic text generation (no LLM, no randomness)
- Label-focused structural description
- Non-prescriptive language only
- Allowed: "indicates", "may", "can", "tends to", "is labeled as"
- Forbidden: "therefore", "so", "means", "should", "must", "execute", "trade", "swap"

**Example Output (CONCISE style):**

```
rescue flow graph indicates structural ROLE-to-ROLE rescue relationships. graph contains 2 labeled edges across 3 role labels.
```

**Example Output (STANDARD style):**

```
rescue flow graph indicates structural ROLE-to-ROLE rescue relationships. graph contains 2 labeled edges across 3 role labels.

HEDGE may support VOLATILITY. STABILITY may support VOLATILITY.

rescue strength labels range from MEDIUM to WEAK.
```

**Example Output (DETAILED style):**

```
rescue flow graph indicates structural ROLE-to-ROLE rescue relationships. graph contains 2 labeled edges across 3 role labels.

HEDGE may support VOLATILITY. STABILITY may support VOLATILITY.

rescue strength labels range from MEDIUM to WEAK.

edge details: STABILITY may support VOLATILITY | RESCUE_MEDIUM | HEDGE may support VOLATILITY | RESCUE_WEAK
```

**Usage:**

```python
from narrative import build_rescue_flow_narrative_extension_v1
from flow import build_rescue_flow_graph_v1

# Build flow graph (PR137)
flow_graph = build_rescue_flow_graph_v1(
    regime_record={"v11_regime_level": "REGIME_MEDIUM"},
    distortion_catalog_record={"v12_distortion_type": "D1_LIQUIDATION"},
)

# Build rescue flow narrative extension (PR139)
narrative_extension = build_rescue_flow_narrative_extension_v1(
    rescue_flow_graph_record=flow_graph,
    style="STANDARD",
    mode="ON",
)

# Check output
if narrative_extension["v12_rescue_narrative_status"] == "AVAILABLE":
    for paragraph in narrative_extension["v12_rescue_narrative_paragraphs"]:
        print(paragraph)
```

**Files:**
- `python/narrative/v12_narrative_rescue_flow_extension_schema.py` - Schema for rescue narrative
- `python/narrative/v12_rescue_flow_narrative_extension_engine_v1.py` - Narrative generation engine
- `python/narrative/v12_rescue_flow_narrative_constitutional_guard.py` - Constitutional guards
- `python/narrative/__init__.py` - Extended with rescue narrative exports

**Integration Points:**
- **Human Narrative Builder (PR123)**: Extended with rescue flow structural narrative
- **Rescue Flow Graph (PR137)**: Converted to natural language description
- **Edge Type (PR135)**: Expressed as "may support", "is neutral to", etc.
- **Rescue Strength (PR136)**: Expressed in strength distribution text

**Constitutional Guarantees (PR139):**
- Non-prescriptive language only ("may", "indicates", not "should", "must")
- No action vocabulary ("execute", "trade", "swap", "buy", "sell")
- No causal coupling ("RESCUE_STRONG therefore execute")
- No token literals (only ROLE labels)
- No numeric patterns beyond structural counts
- Narrative ≠ Instruction ≠ Conclusion
- Warning-only guards (never fail)

**Philosophy (PR139):**
```
Narrative = Structural description (not instruction)
Rescue Flow Narrative = Label-focused explanation in natural language

The rescue flow narrative describes ROLE-to-ROLE patterns with:
  - Non-prescriptive language
  - Structural focus only
  - Constitutional guarantees enforced

"STABILITY may support VOLATILITY" = Structural pattern observed
NOT: "therefore execute trade"
NOT: "this means act"
NOT: "system should swap"

Rescue flow narrative provides:
  - Human-readable structural explanation
  - Label-focused natural language
  - Non-prescriptive context description

Rescue flow narrative does NOT:
  - Recommend actions
  - Imply next steps
  - Contain trading instructions
  - Include token/amount/address references
  - Use causal coupling language
```

**Use Cases:**

1. **Human context**: Add structural narrative to explanation context for operators
2. **Natural language**: Convert flow graph to readable text for non-technical review
3. **Audit trail**: Include rescue flow explanation in narrative artifacts
4. **Extension architecture**: Add rescue context without modifying PR123 core
5. **Constitutional enforcement**: Prevent prescriptive language in narrative generation

---

### v1.2 Approval Packet Integration Orchestrator v1 (PR140)

**Purpose:** Integration orchestrator for v1.2 components. Assembles approval packet + render + rescue extensions from artifact bundle.

**⚠️ Constitutional Notice - Integration ≠ Judgment:**

```
This orchestrator does NOT:
- Recommend approval decisions
- Contain "should approve" logic
- Make approval judgments
- Execute transactions

This orchestrator ONLY:
- Assembles information from v1.2 components
- Generates human-readable packet + render
- Collects constitutional warnings
```

**What is v1.2 Integration?**

Integration = Assembly (not judgment)
Orchestrator = Information bundler (not approval decider)

**Architecture:**

```
Artifact Bundle (PR115/PR116)
    ↓
v1.2 Integration Orchestrator (PR140)
    ├─ Extract artifacts from bundle
    ├─ Build missing components (explain_context, narrative, preview, approval_gate)
    ├─ Apply label-only projection to inputs
    ├─ Assemble v1.2 packet using PR124 builder
    │  └─ Components: trajectory, distortion, eligibility, contribution, rescue
    ├─ Render packet using PR125/PR138 renderer
    │  └─ Optional: Rescue Flow section (PR138)
    ├─ Generate rescue narrative extension (PR139, if mode ON)
    └─ Collect constitutional warnings from all components
    ↓
{approval_packet, render_record, rescue_narrative_extension, warnings}
```

**Integrated Components:**

- **PR124**: Approval Packet Builder (reused, not modified)
- **PR125/PR138**: Human Review Renderer with Rescue Flow
- **PR139**: Rescue Flow Narrative Extension
- **PR126**: Continuous Permission Monitor
- **PR127**: Permission Trajectory Binding
- **PR128**: Role-Distortion Eligibility
- **PR129/PR134**: Distortion Detection & Subtype
- **PR130**: Role Carrier Qualification
- **PR131/PR132**: Contribution Model & Constraints
- **PR133**: Role Rescue Relation
- **PR135**: Edge Type Classification
- **PR136**: Rescue Strength Classification
- **PR137**: Rescue Flow Graph

**Usage:**

```python
from packet import build_approval_packet_v12

# Prepare artifact bundle (PR115/PR116 format)
artifact_bundle = {
    "artifacts": {
        # Required
        "regime_record": regime,
        "drift_record": drift,

        # Optional v1.2 components
        "permission_record": permission,
        "trajectory_record": trajectory,
        "distortion_catalog_record": distortion,
        "eligibility_record": eligibility,
        "role_qualification_record": qualification,
        "contribution_record": contribution,
        "rescue_flow_graph": rescue_flow,

        # Optional pre-built components
        "explain_context_record": explain_context,
        "narrative_record": narrative,
        "preview_record": preview,
        "approval_gate_record": approval_gate,
        "approval_registry_record": approval_registry,
    }
}

# Build v1.2 approval packet (integration orchestration)
result = build_approval_packet_v12(
    artifact_bundle=artifact_bundle,
    narrative_style="STANDARD",
    render_style="STANDARD",
    render_format="MARKDOWN",
    rescue_narrative_mode="ON",
)

# Access outputs
packet = result["approval_packet"]
render = result["render_record"]
rescue_narrative = result["rescue_narrative_extension"]
warnings = result["warnings"]

# Check packet status
if packet["v11_packet_status"] == "AVAILABLE":
    # Packet ready for human review
    print(render["v11_render_output"])
```

**Files:**
- `python/packet/v12_approval_packet_integration_orchestrator_engine_v1.py` - Integration engine
- `python/packet/__init__.py` - Extended with v12 exports
- `python/validation/pr140_approval_packet_integration_orchestrator_v1_smoke.py` - Integration tests

**Integration Points:**
- **Reuses PR124**: Calls v1.1 approval packet builder (no modification)
- **Artifact Bundle (PR115/PR116)**: Input format
- **All v1.2 components**: Orchestrates PR126-PR139
- **Constitutional guards**: Collects warnings from packet/render/narrative

**Constitutional Guarantees (PR140):**
- READ-ONLY: No execution logic
- Non-prescriptive: No "should approve" language
- No approval recommendation: Assembly only, no judgment
- Defensive: Invalid input → graceful ERROR + warnings
- Warning-only: All guards return warnings (never fail)
- Label-only projection: Removes numeric patterns/token literals before downstream

**Philosophy (PR140):**
```
Integration = Assembly (not judgment)
Orchestrator = Information bundler (not approval decider)

The v1.2 integration orchestrator:
  - Assembles artifacts into packet
  - Generates human-readable render
  - Collects constitutional warnings
  - Provides complete review bundle

The v1.2 integration orchestrator does NOT:
  - Recommend approval decisions
  - Contain "should approve" language
  - Make approval judgments
  - Execute transactions
  - Modify PR124 (reuses existing builder)

PR124 Relationship:
  - PR124 = v1.1 packet builder (core component assembly)
  - PR140 = v1.2 integration orchestrator (artifact bundle → packet + render + warnings)
  - PR140 calls PR124 internally (adapter pattern)
  - PR124 remains unchanged (backward compatible)
```

**Use Cases:**

1. **End-to-end v1.2 testing**: Validate full pipeline from artifacts to render
2. **Human review preparation**: Generate complete packet + render for operator interface
3. **Constitutional validation**: Collect all warnings across v1.2 components
4. **Artifact bundling**: Convert individual v1.2 records into unified review bundle
5. **Integration testing**: Verify PR126-PR139 components work together correctly

---

## v1.3 Infrastructure — Execution Bridge (READ-ONLY)

### v1.3 Execution Draft Schema v1 (PR141)

**Purpose:** Define strict schema for "execution draft" generated from approval packets. This is NOT an instruction, NOT a recommendation, NOT a transaction. It is a structured, non-custodial, execution-shaped draft record.

**⚠️ Constitutional Notice - Draft ≠ Action:**

```
This draft schema does NOT:
- Contain instructions
- Recommend actions
- Build transactions
- Include signing logic
- Reference addresses
- Contain token literals or amounts

This draft schema ONLY:
- Defines structured record format
- Provides label-only references
- Records constraints and boundaries
- Maintains READ-ONLY guarantees
```

**What is an Execution Draft?**

Draft ≠ Action ≠ Recommendation
Execution Draft = Structured shape reference (not instruction)

**Schema Design:**

Record prefix: `v13_draft_`

**Required Fields:**
- `v13_draft_version`: "v1"
- `v13_draft_status`: AVAILABLE | ERROR
- `v13_draft_mode`: READ_ONLY
- `v13_draft_summary`: Non-prescriptive summary
- `v13_draft_inputs`: References to artifact ids / component presence labels only
- `v13_draft_constraints`: Labels only (permission/trajectory/eligibility/boundary)
- `v13_draft_intended_shape`: Labels only (ACTION_CLASS = NONE / DRAFT_ONLY)
- `v13_draft_basis`: List of strings (no numbers)
- `v13_draft_artifacts`: List of strings (no numeric pattern ids)
- `v13_draft_warnings`: List of strings

**Optional Fields:**
- `v13_draft_components_present`: Dict of booleans
- `v13_draft_notes`: String (guarded)

**Example Record (labels only):**

```python
{
    "v13_draft_version": "v1",
    "v13_draft_status": "AVAILABLE",
    "v13_draft_mode": "READ_ONLY",
    "v13_draft_summary": "execution draft available. inputs present.",
    "v13_draft_inputs": {
        "packet_id": "approval_packet_v1",
        "components_present": ["explain_context", "narrative", "preview"]
    },
    "v13_draft_constraints": {
        "permission": "ALLOWED",
        "trajectory": "IMPROVING",
        "eligibility": "ELIGIBLE",
        "boundary": "WITHIN_LIMITS"
    },
    "v13_draft_intended_shape": {
        "action_class": "DRAFT_ONLY"
    },
    "v13_draft_basis": ["v13_approval_packet", "v11_regime_level"],
    "v13_draft_artifacts": ["approval_packet_v12"],
    "v13_draft_warnings": []
}
```

**Usage:**

```python
from draft import V13ExecutionDraftSchema, DRAFT_STATUS_AVAILABLE, ACTION_CLASS_DRAFT_ONLY

# Create execution draft record
draft_record = V13ExecutionDraftSchema.create_draft_record(
    status=DRAFT_STATUS_AVAILABLE,
    summary="execution draft available.",
    inputs={"packet_id": "approval_packet_v1"},
    constraints={"permission": "ALLOWED", "eligibility": "ELIGIBLE"},
    intended_shape={"action_class": ACTION_CLASS_DRAFT_ONLY},
    basis=["v13_approval_packet"],
)

# Validate draft record
errors = V13ExecutionDraftSchema.validate_draft_record(draft_record)
if len(errors) == 0:
    print("Draft record is valid")
```

**Files:**
- `python/draft/v13_execution_draft_schema.py` - Schema definition
- `python/draft/v13_draft_constitutional_guard.py` - Constitutional guards
- `python/draft/__init__.py` - Package exports
- `python/validation/pr141_execution_draft_schema_v1_smoke.py` - 10 smoke tests

**Constitutional Guarantees (PR141):**
- READ-ONLY: No signing, no sending, no tx building, no calldata, no addresses
- No token literals, no amounts, no numeric patterns
- No trading verbs (swap/buy/sell/execute/sign/transfer/bridge)
- No prescriptive language (should/must/need to)
- No causal coupling ("approved therefore", "eligible so", "recovered means")
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR141):**
```
Draft = Structured shape reference (not instruction)
Execution Draft = Non-custodial record format (not transaction)

The execution draft schema defines:
  - Label-only record structure
  - Non-prescriptive field names
  - Constitutional constraints enforcement
  - Defensive error handling

The execution draft schema does NOT:
  - Contain instructions
  - Build transactions
  - Reference addresses or amounts
  - Include signing logic
  - Recommend actions

Relationship to v1.2:
  - Input: v1.2 approval packet (PR140)
  - Process: Extract labels and constraints
  - Output: v1.3 execution draft (label-only)
  - Bridge: v1.2 (human review) → v1.3 (execution shape)
```

**Use Cases:**

1. **Schema definition**: Strict format for execution draft records
2. **Label-only projection**: Extract labels from approval packets
3. **Constitutional validation**: Enforce READ-ONLY guarantees
4. **Execution bridge**: Connect v1.2 human review to v1.3 execution layer
5. **Defensive error handling**: Graceful degradation on invalid input

---

### v1.3 Approval Packet → Execution Draft Binding Engine v1 (PR142)

**Purpose:** Map v1.2 Approval Packet (PR124/PR140) or Artifact Bundle (PR115/PR116) to PR141 Execution Draft Schema (v13_draft_) with labels and constraints only.

**⚠️ Constitutional Notice - Binding Only:**

```
This binding engine does NOT:
- Recommend actions
- Provide instructions
- Build transactions
- Make trading decisions
- Suggest execution strategies

This binding engine ONLY:
- Maps labels from packet to draft
- Extracts constraints (labels only, no values)
- Projects source presence (flags only, no data)
- Determines structural shape (not recommendation)
- Maintains READ-ONLY guarantees
```

**What is Binding?**

Binding = Label projection (not recommendation, not instruction)
Draft Binding = Structural mapping (not decision)

**API:**

```python
from bind import build_execution_draft_from_bundle_v1, build_execution_draft_from_packet_v1

# From artifact bundle
result = build_execution_draft_from_bundle_v1(artifact_bundle, mode="DRAFT_ONLY")

# From approval packet
result = build_execution_draft_from_packet_v1(approval_packet, mode="DRAFT_ONLY")

# Result structure:
{
    "execution_draft": {
        "v13_draft_status": "AVAILABLE",
        "v13_draft_inputs": {...},      # Source presence only
        "v13_draft_constraints": {...},  # Labels only
        "v13_draft_intended_shape": {...}, # Structural label
        ...
    },
    "warnings": [...]
}
```

**Intended Shape Mapping (structural binding, not recommendation):**

| Input Constraint | Intended Shape Output |
|------------------|----------------------|
| INELIGIBLE | NO_ACTION |
| SUPPRESSED | NO_ACTION |
| REQUIRED | HUMAN_REVIEW_REQUIRED |
| DRY_RUN_ONLY | SIMULATION_ONLY |
| CONSIDERATION_ONLY | CONSIDERATION_ONLY |
| (default) | SIMULATION_ONLY |

**Label Projection Rules:**

1. **Inputs**: Source presence only (no values)
   - ✓ `{"regime_record_present": "true"}`
   - ✗ `{"sui_amount": "1000000000"}`

2. **Constraints**: Labels only (no numeric values)
   - ✓ `{"permission": "PERMISSION_ALLOWED"}`
   - ✗ `{"token_pair": "SUI/USDC"}`

3. **Intended Shape**: Structural label (not prescriptive)
   - ✓ `{"action_class": "SIMULATION_ONLY"}`
   - ✗ `{"action_class": "YOU_SHOULD_EXECUTE_THIS"}`

**Files:**
- `python/bind/v13_packet_to_draft_binding_engine_v1.py` - Binding engine
- `python/bind/v13_bind_constitutional_guard.py` - Constitutional guards
- `python/bind/__init__.py` - Package exports
- `python/validation/pr142_packet_to_draft_binding_v1_smoke.py` - 10 smoke tests

**Constitutional Guarantees (PR142):**
- READ-ONLY: No execution logic or transaction building
- Label projection only: No numeric values, no token literals
- Source presence only: Inputs are flags, not data
- Structural binding: Intended shape is label, not recommendation
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR142):**
```
Binding = Label projection (not recommendation)
Structural mapping = Constraint extraction (not decision)

The binding engine:
  - Maps labels from packet to draft
  - Extracts constraint labels (no values)
  - Projects source presence (no data)
  - Determines structural shape (no action recommendation)

The binding engine does NOT:
  - Recommend actions
  - Provide instructions
  - Build transactions
  - Make trading decisions
  - Suggest execution strategies

Relationship to v1.2:
  - Input: v1.2 approval packet (PR140) OR artifact bundle (PR115)
  - Process: Label projection + constraint extraction
  - Output: v1.3 execution draft (PR141)
  - Bridge: v1.2 (human review) → v1.3 (execution shape)
```

**Use Cases:**

1. **Packet → Draft mapping**: Convert approval packets to execution drafts
2. **Label-only projection**: Extract labels without numeric values
3. **Source presence tracking**: Record artifact presence without data
4. **Structural shape binding**: Determine intended shape without recommendation
5. **Constitutional validation**: Enforce READ-ONLY guarantees across binding

---

### v1.3 Execution Gate (Always-Blocked) v1 (PR143)

**Purpose:** Build execution gate from execution draft (PR141/PR142). ALWAYS returns BLOCKED with structural block reasons. This gate explains why execution is not reachable.

**⚠️ Constitutional Notice - Always Blocked:**

```
This gate does NOT:
- Allow execution
- Permit transactions
- Provide "ready to execute" signals
- Recommend actions
- Make decisions

This gate ONLY:
- Returns BLOCKED state (always)
- Enumerates block reasons (structural labels)
- Explains why execution is not reachable
- Maintains READ-ONLY guarantees
```

**What is an Execution Gate?**

Gate ≠ Allow
Gate = Explain why execution is not reachable (yet)
Execution is defined by prohibition first.

**Gate Behavior:**

The execution gate ALWAYS returns:
- `gate_state: "BLOCKED"` (constant, never ALLOW)
- Block reasons (list of structural labels)
- Reason details (label-only context)

**API:**

```python
from gate import build_execution_gate_from_draft_v1, build_execution_gate_from_bundle_v1

# From execution draft
result = build_execution_gate_from_draft_v1(draft_record)

# From artifact bundle
result = build_execution_gate_from_bundle_v1(artifact_bundle)

# Result structure:
{
    "execution_gate": {
        "v13_gate_status": "AVAILABLE",
        "v13_gate_gate_state": "BLOCKED",  # ALWAYS
        "v13_gate_block_reasons": [...],   # Structural labels
        "v13_gate_reason_details": [...],  # Label-only context
        ...
    },
    "warnings": [...]
}
```

**Block Reason Mapping (structural, label-only):**

| Draft Condition | Block Reason |
|----------------|--------------|
| draft.status == "ERROR" | REASON_INVALID_DRAFT |
| ACTION_CLASS_NO_ACTION | REASON_NO_ACTION_SHAPE |
| ACTION_CLASS_HUMAN_REVIEW_REQUIRED | REASON_HUMAN_REVIEW_REQUIRED |
| ACTION_CLASS_SIMULATION_ONLY | REASON_SIMULATION_ONLY |
| ACTION_CLASS_CONSIDERATION_ONLY | REASON_CONSIDERATION_ONLY |
| HARD_* constraints | REASON_HARD_CONSTRAINT |
| SUPPRESSED | REASON_SUPPRESSED |
| Missing inputs | REASON_MISSING_INPUTS |
| Draft warnings present | REASON_DRAFT_WARNINGS |
| (always included) | REASON_NO_EXECUTION_LOGIC |

**Example Output:**

```python
{
    "v13_gate_version": "v1.3",
    "v13_gate_status": "AVAILABLE",
    "v13_gate_mode": "READ_ONLY",
    "v13_gate_summary": "execution gate produced. state blocked. reasons enumerated.",
    "v13_gate_gate_state": "BLOCKED",  # ALWAYS
    "v13_gate_block_reasons": [
        "REASON_SIMULATION_ONLY",
        "REASON_NO_EXECUTION_LOGIC"
    ],
    "v13_gate_reason_details": [
        {
            "reason": "REASON_SIMULATION_ONLY",
            "source": "execution_draft",
            "action_class": "SIMULATION_ONLY"
        },
        {
            "reason": "REASON_NO_EXECUTION_LOGIC",
            "source": "execution_draft"
        }
    ],
    "v13_gate_basis": ["v13_execution_draft"],
    "v13_gate_artifacts": ["v13_execution_draft"],
    "v13_gate_warnings": []
}
```

**Files:**
- `python/gate/v13_execution_gate_schema.py` - Gate schema
- `python/gate/v13_execution_gate_engine_v1.py` - Gate engine
- `python/gate/v13_gate_constitutional_guard.py` - Constitutional guards
- `python/gate/__init__.py` - Package exports
- `python/validation/pr143_execution_gate_v1_smoke.py` - 12 smoke tests

**Constitutional Guarantees (PR143):**
- READ-ONLY: No execution logic
- Always BLOCKED: Never produces ALLOW/PERMITTED/READY states
- No execution: Gate never allows transactions
- Label-only: No numeric values, no token literals
- No prescriptive language: No should/must/need to
- No action vocabulary: No execute/sign/transfer/swap/buy/sell
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR143):**
```
Gate = Prohibition enumeration (not permission)
Execution Gate = Structural block reasons (not recommendation)

The execution gate:
  - ALWAYS returns BLOCKED state
  - Enumerates structural reasons why execution is not reachable
  - Maps draft labels to block reason labels
  - Maintains READ-ONLY guarantees

The execution gate does NOT:
  - Allow execution
  - Provide permission
  - Recommend actions
  - Make decisions
  - Build transactions

Relationship to v1.3:
  - Input: v1.3 execution draft (PR141/PR142)
  - Process: Block reason enumeration
  - Output: v1.3 execution gate (always BLOCKED)
  - Purpose: Explain why execution is not reachable (yet)
```

**Use Cases:**

1. **Block reason enumeration**: Explain why execution is not reachable
2. **Structural prohibition**: Map draft labels to block reasons
3. **Constitutional validation**: Enforce always-blocked guarantees
4. **Defensive error handling**: Graceful degradation on invalid input
5. **Execution bridge**: Connect v1.3 draft to prohibition layer

**Explicit Non-Claims:**
- This gate does NOT allow execution
- This gate does NOT permit transactions
- This gate does NOT provide "ready to execute" signals
- This gate does NOT recommend actions
- This gate does NOT make decisions
- Gate state is ALWAYS "BLOCKED" (never ALLOW/PERMITTED/READY)

---

### Constitutional Constraints (v1.2)

- **READ-ONLY**: No execution logic or decision changes
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **No amounts**: Numeric patterns prohibited
- **No token literals**: SUI, USDC, BTC, ETH, DEEP, CETUS prohibited
- **No addresses**: 0x... patterns prohibited
- **No trading vocabulary**: swap, buy, sell, execute, sign, transfer prohibited
- **No trajectory coupling**: "permission improved therefore act" patterns prohibited (PR127)
- **No distortion coupling**: "D1 therefore act" patterns prohibited (PR129)
- **No role coupling**: "QUALIFIED therefore act" patterns prohibited (PR130)
- **No contribution coupling**: "++ therefore trade", "-- therefore stop" patterns prohibited (PR131)
- **No return guarantee language**: "annual return", "backtest", "assured" prohibited (PR131)
- **No contribution zone coupling**: "primary therefore trade", "blocked so stop" patterns prohibited (PR132)
- **No rescue coupling**: "rescue therefore act", "buffer so trade", "救えるので触ってよい" patterns prohibited (PR133)
- **No subtype coupling**: "D1B therefore act", "subtype implies trade" patterns prohibited (PR134)
- **No edge coupling**: "EDGE_AMPLIFY therefore trade", "EDGE_SHIELD so stop" patterns prohibited (PR135)
- **No rescue strength coupling**: "RESCUE_STRONG therefore trade", "strong rescue means proceed" patterns prohibited (PR136)
- **No flow coupling**: "this edge means execute", "flow graph therefore act" patterns prohibited (PR137)
- **No rescue narrative coupling**: "RESCUE_STRONG therefore execute", "rescue flow means trade" patterns prohibited (PR139)
- **No integration recommendation coupling** (NEW): "packet AVAILABLE therefore approve", "warnings empty means proceed" patterns prohibited (PR140)
- **Defensive**: Never raises exceptions
- **Warning-only**: Exit code always 0

### Run Validations (v1.2)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr126_continuous_permission_monitor_v1_smoke.py
python3 python/validation/pr127_permission_trajectory_binding_v1_smoke.py
python3 python/validation/pr128_role_distortion_eligibility_v1_smoke.py
python3 python/validation/pr129_distortion_detector_v1_smoke.py
python3 python/validation/pr130_role_carrier_qualification_v1_smoke.py
python3 python/validation/pr131_contribution_model_v1_smoke.py
python3 python/validation/pr132_contribution_constraint_binding_v1_smoke.py
python3 python/validation/pr133_role_rescue_relation_v1_smoke.py
python3 python/validation/pr134_distortion_subtype_classifier_v1_smoke.py
python3 python/validation/pr135_edge_type_classifier_v1_smoke.py
python3 python/validation/pr136_rescue_strength_engine_v1_smoke.py
python3 python/validation/pr137_rescue_flow_graph_v1_smoke.py
python3 python/validation/pr138_rescue_flow_render_extension_smoke.py
python3 python/validation/pr139_rescue_flow_narrative_extension_v1_smoke.py
python3 python/validation/pr140_approval_packet_integration_orchestrator_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

### Run Validations (v1.3)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr141_execution_draft_schema_v1_smoke.py
python3 python/validation/pr142_packet_to_draft_binding_v1_smoke.py
python3 python/validation/pr143_execution_gate_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.4 Infrastructure — Guidance & Display Shape (READ-ONLY)

### v1.4 Role Safe Band Guidance v1 (PR144)

**Purpose:** Build role safe band guidance from portfolio snapshot and regime record. This describes whether role allocations are BELOW/WITHIN/ABOVE structurally safe bands. This is NOT advice, NOT instruction, NOT recommendation.

**⚠️ Constitutional Notice - Guidance ≠ Instruction:**

```
This guidance does NOT:
- Recommend actions
- Provide trading advice
- Instruct what to do
- Make decisions
- Suggest trades

This guidance ONLY:
- Describes allocation status (BELOW/WITHIN/ABOVE safe band)
- Outputs bucket labels (no raw numeric values)
- Provides non-prescriptive interpretations
- Maps regime × role to safe band (static table)
- Maintains READ-ONLY guarantees
```

**What is Guidance?**

Guidance ≠ Instruction
Guidance = Describe shape, not recommend action

**API:**

```python
from guidance import build_role_safe_band_guidance_v1

# Build guidance from portfolio + regime
result = build_role_safe_band_guidance_v1(
    portfolio_snapshot={
        "VOLATILITY_ROLE": 0.30,
        "LIQUIDITY_ROLE": 0.25,
        "STABILITY_ROLE": 0.20,
        "HEDGE_ROLE": 0.15,
        "GAS_ROLE": 0.10,
    },
    regime_record={
        "v11_regime_level": "REGIME_MEDIUM"
    }
)

# Result structure:
{
    "guidance_record": {
        "v14_guidance_status": "AVAILABLE",
        "v14_guidance_regime_label": "REGIME_MEDIUM",
        "v14_guidance_roles": {
            "VOLATILITY_ROLE": {
                "current_ratio_bucket": "RATIO_MEDIUM",
                "safe_band_bucket": "BAND_MEDIUM",
                "status": "WITHIN_SAFE",
                "interpretation": "allocation appears within the structurally safe band..."
            },
            ...
        }
    },
    "warnings": [...]
}
```

**Safe Band Table (Static, Deterministic):**

Maps (regime × role) to safe band bucket:

| Regime | VOLATILITY | LIQUIDITY | STABILITY | HEDGE | GAS |
|--------|-----------|-----------|-----------|-------|-----|
| CRITICAL | BAND_ZERO | BAND_HIGH | BAND_HIGH | BAND_MEDIUM | BAND_MINIMAL |
| HIGH | BAND_LOW | BAND_MEDIUM | BAND_MEDIUM | BAND_MEDIUM | BAND_MINIMAL |
| MEDIUM | BAND_MEDIUM | BAND_MEDIUM | BAND_LOW | BAND_LOW | BAND_MINIMAL |
| LOW | BAND_MEDIUM | BAND_LOW | BAND_LOW | BAND_MINIMAL | BAND_MINIMAL |

**Bucket Labels:**

Ratio Buckets (current allocation):
- RATIO_ZERO (0-1%)
- RATIO_MINIMAL (1-10%)
- RATIO_LOW (10-25%)
- RATIO_MEDIUM (25-50%)
- RATIO_HIGH (50-75%)
- RATIO_MAXIMAL (75-100%)
- RATIO_UNKNOWN

Safe Band Buckets (target range):
- BAND_ZERO (0-1%)
- BAND_MINIMAL (1-10%)
- BAND_LOW (10-25%)
- BAND_MEDIUM (25-50%)
- BAND_HIGH (50-75%)
- BAND_MAXIMAL (75-100%)
- BAND_UNKNOWN

Status Labels:
- STATUS_BELOW_SAFE: Allocation below safe band
- STATUS_WITHIN_SAFE: Allocation within safe band
- STATUS_ABOVE_SAFE: Allocation above safe band
- STATUS_UNKNOWN: Status cannot be determined

**Files:**
- `python/guidance/v14_role_safe_band_schema.py` - Guidance schema
- `python/guidance/v14_role_safe_band_engine_v1.py` - Guidance engine
- `python/guidance/v14_guidance_constitutional_guard.py` - Constitutional guards
- `python/guidance/__init__.py` - Package exports
- `python/validation/pr144_role_safe_band_guidance_v1_smoke.py` - 12 smoke tests

**Constitutional Guarantees (PR144):**
- READ-ONLY: No execution, no trading
- Non-prescriptive: No should/must/recommend/advise
- No trading verbs: No buy/sell/swap/execute/sign/transfer
- No token literals: No SUI/USDC/BTC/ETH
- Bucket output only: No raw numeric values in text
- No addresses: No 0x... patterns
- Static safe band table: Deterministic (regime × role → band)
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR144):**
```
Guidance = Display shape (not instruction)
Role Safe Band Guidance = Describe status (not recommend action)

The guidance engine:
  - Maps portfolio snapshot to ratio buckets
  - Compares to safe band table (static, deterministic)
  - Determines status: BELOW/WITHIN/ABOVE
  - Provides non-prescriptive interpretations
  - Outputs bucket labels only (no raw numbers)

The guidance engine does NOT:
  - Recommend actions
  - Provide trading advice
  - Instruct what to do
  - Make decisions
  - Suggest trades

Relationship to v1.2:
  - Input: v1.2 regime record + portfolio snapshot
  - Process: Safe band comparison (static table)
  - Output: v1.4 guidance record (bucket labels + status)
  - Purpose: Display shape for human review
```

**Use Cases:**

1. **Allocation status display**: Show BELOW/WITHIN/ABOVE for each role
2. **Regime-aware guidance**: Safe bands adapt to regime label
3. **Non-prescriptive interpretation**: Describe without recommending
4. **Bucket-only output**: No raw numeric values in text
5. **Constitutional validation**: Enforce guidance ≠ instruction

**Explicit Non-Claims:**
- This is NOT trading advice
- This is NOT a recommendation
- This is NOT an instruction
- This is NOT a decision
- Safe band status is descriptive only (not prescriptive)

---

### v1.4 Safe Band × Distortion Stress Overlay v1 (PR145)

**Purpose:** Overlay static safe band guidance (PR144) with dynamic distortion signals (PR129/PR134) to produce a structural stress label for human understanding. This is NOT eligibility, NOT permission, NOT recommendation, NOT instruction.

**⚠️ Constitutional Notice - Stress State ≠ Permission:**

```
This overlay does NOT:
- Grant permission to act
- Determine eligibility
- Recommend actions
- Provide trading advice
- Make decisions
- Suggest trades

This overlay ONLY:
- Describes structural stress state (CALM/TENSE/STRESSED/UNKNOWN)
- Overlays static safe band with dynamic distortion signals
- Outputs stress label for human review
- Maintains READ-ONLY guarantees
- Uses deterministic rules
```

**What is Stress State?**

Stress State = Structural tension indicator (not action permission)
- CALM: Safe band + no distortion
- TENSE: Safe band + distortion present (moderate regime)
- STRESSED: Constrained regime/bucket + distortion present
- UNKNOWN: Cannot determine from available inputs

**API:**

```python
from guidance import build_safe_band_distortion_overlay_v1

# Build overlay from artifact bundle
result = build_safe_band_distortion_overlay_v1(
    artifact_bundle={
        "artifacts": {
            "regime_record": {
                "v11_regime_level": "REGIME_MEDIUM"
            },
            "role_safe_band_guidance": {
                "v14_guidance_roles": {
                    "VOLATILITY_ROLE": {
                        "safe_band_bucket": "BAND_MEDIUM"
                    }
                }
            },
            "distortion_catalog_record": {
                "v12_distortion_records": [
                    {"distortion_subtype": "SUBTYPE_A"}
                ]
            }
        }
    }
)

# Result structure:
{
    "overlay_record": {
        "v14_overlay_status": "AVAILABLE",
        "v14_overlay_regime_label": "REGIME_MEDIUM",
        "v14_overlay_role_type": "VOLATILITY_ROLE",
        "v14_overlay_safe_band_bucket": "BAND_MEDIUM",
        "v14_overlay_distortion_presence": "PRESENT",
        "v14_overlay_distortion_subtypes": ["SUBTYPE_A"],
        "v14_overlay_band_stress_label": "TENSE",
        "v14_overlay_notes": [
            "allocation within safe band but distortion signal present indicates structural tension."
        ],
        ...
    },
    "warnings": [...]
}
```

**Deterministic Stress Rules:**

Distortion Presence:
- NONE: No distortion detected
- PRESENT: One distortion detected
- MULTIPLE: Multiple distortions detected
- UNKNOWN: Cannot determine

Band Stress Label (structural only, NOT action):
- Regime CRITICAL → STRESSED (always)
- Distortion NONE → CALM (after checking regime)
- Safe band bucket BAND_ZERO + distortion → STRESSED
- Regime HIGH + distortion → STRESSED
- Regime MEDIUM + distortion → TENSE
- Regime LOW + distortion → TENSE
- Invalid inputs → ERROR or UNKNOWN (defensive)

**Files:**
- `python/guidance/v14_safe_band_distortion_overlay_schema.py` - Overlay schema
- `python/guidance/v14_safe_band_distortion_overlay_engine_v1.py` - Overlay engine
- `python/guidance/v14_overlay_constitutional_guard.py` - Overlay guards
- `python/guidance/__init__.py` - Package exports (updated)
- `python/validation/pr145_safe_band_distortion_overlay_v1_smoke.py` - 12 smoke tests

**Constitutional Guarantees (PR145):**
- READ-ONLY: No execution, no trading
- Non-prescriptive: No should/must/recommend/advise
- No trading verbs: No buy/sell/swap/execute/sign/transfer
- No token literals: No SUI/USDC/BTC/ETH
- No numeric values in text: Bucket/stress labels only
- No addresses: No 0x... patterns
- No causal coupling: No therefore/so/hence
- No eligibility coupling: No "eligible therefore", "permission improved so"
- Deterministic rules: Stress label is predictable
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR145):**
```
Stress State = Display structural tension (not permission)
Overlay = Combine static guidance + dynamic distortion signals

The overlay engine:
  - Extracts regime label, safe band bucket, distortion signals
  - Determines distortion presence (NONE/PRESENT/MULTIPLE/UNKNOWN)
  - Applies deterministic stress rules
  - Outputs stress label (CALM/TENSE/STRESSED/UNKNOWN)
  - Provides non-prescriptive overlay notes

The overlay engine does NOT:
  - Grant permission to act
  - Determine eligibility
  - Recommend actions
  - Provide trading advice
  - Make decisions
  - Link stress state to permission

Relationship to v1.4:
  - Input: PR144 safe band guidance + PR129/PR134 distortion signals
  - Process: Overlay static + dynamic (deterministic rules)
  - Output: Structural stress label (no eligibility/permission)
  - Purpose: Display stress state for human understanding
```

**Use Cases:**
1. **Stress state display**: Show CALM/TENSE/STRESSED for human review
2. **Static + dynamic overlay**: Combine safe band guidance with distortion signals
3. **Non-prescriptive interpretation**: Describe tension without recommending action
4. **Stress label only**: No raw numeric values or eligibility claims
5. **Constitutional validation**: Enforce stress state ≠ permission

**Explicit Non-Claims:**
- This is NOT eligibility determination
- This is NOT permission granting
- This is NOT trading advice
- This is NOT a recommendation
- This is NOT an instruction
- This is NOT a decision
- Stress state is descriptive only (not prescriptive or permissive)

---

### v1.4 Stress Rule Table v1 (PR146)

**Purpose:** Fixed table mapping (regime × band_bucket × distortion_presence) → stress_label. Stress = structural load state (not action, not instruction). Table-first approach with deterministic lookups.

**⚠️ Constitutional Notice - Stress ≠ Action:**

```
This stress label does NOT:
- Recommend actions
- Provide trading advice
- Instruct what to do
- Make decisions
- Suggest trades

This stress label ONLY:
- Describes structural load state (CALM/TENSE/STRESSED/UNKNOWN)
- Uses fixed table lookup (deterministic)
- Outputs label-only (no numeric values)
- Maintains READ-ONLY guarantees
```

**What is Stress?**

Stress = Structural load state (not action directive)
- CALM: Safe band + no distortion (stable)
- TENSE: Moderate stress (regime constraints or distortion present)
- STRESSED: High stress (critical regime or outside band or both)
- UNKNOWN: Cannot determine from available inputs

**API:**

```python
from stress import build_stress_label_from_inputs_v1, build_stress_label_from_bundle_v1

# Direct inputs
result = build_stress_label_from_inputs_v1(
    regime_label="REGIME_LOW",
    band_bucket="SAFE",
    distortion_presence="NONE"
)
print(result["stress_record"]["v14_stress_label"])  # CALM

# Artifact bundle
result = build_stress_label_from_bundle_v1(
    artifact_bundle={
        "artifacts": {
            "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
            "role_safe_band_guidance": {
                "v14_guidance_roles": {
                    "VOLATILITY_ROLE": {"status": "WITHIN_SAFE"}
                }
            },
            "distortion_catalog_record": {
                "v12_distortion_records": [{"distortion_subtype": "SUBTYPE_A"}]
            }
        }
    }
)
print(result["stress_record"]["v14_stress_label"])  # STRESSED or TENSE
```

**Stress Rule Table (Fixed, Deterministic):**

Absolute Priority Rules:
1. band_bucket == OUTSIDE → STRESSED (always)
2. regime == REGIME_CRITICAL → STRESSED (always)
3. UNKNOWN inputs → UNKNOWN (but OUTSIDE/CRITICAL override)

Matrix (excluding OUTSIDE/CRITICAL):

| Regime | Band | Distortion NONE | Distortion PRESENT |
|--------|------|-----------------|-------------------|
| LOW | SAFE | CALM | TENSE |
| LOW | EDGE | TENSE | STRESSED |
| MEDIUM | SAFE | TENSE | STRESSED |
| MEDIUM | EDGE | STRESSED | STRESSED |
| HIGH | SAFE | STRESSED | STRESSED |
| HIGH | EDGE | STRESSED | STRESSED |
| CRITICAL | ANY | STRESSED | STRESSED |

Band Bucket Mapping (PR144 → simplified):
- STATUS_BELOW_SAFE → OUTSIDE
- STATUS_WITHIN_SAFE → SAFE
- STATUS_ABOVE_SAFE → EDGE
- STATUS_UNKNOWN → UNKNOWN

Or direct bucket mapping:
- BAND_ZERO → OUTSIDE (0-1%, most constrained)
- BAND_MINIMAL → EDGE (1-10%)
- BAND_LOW/MEDIUM/HIGH → SAFE (10-75%)
- BAND_MAXIMAL → EDGE (75-100%)
- BAND_UNKNOWN → UNKNOWN

Worst Bucket Priority (for multiple roles):
OUTSIDE > EDGE > SAFE > UNKNOWN

**Files:**
- `python/stress/v14_stress_rule_table_schema.py` - Stress schema
- `python/stress/v14_stress_rule_table_v1.py` - Fixed mapping table (102 entries)
- `python/stress/v14_stress_engine_v1.py` - Stress engine
- `python/stress/v14_stress_constitutional_guard.py` - Constitutional guards
- `python/stress/__init__.py` - Package exports
- `python/validation/pr146_stress_rule_table_v1_smoke.py` - 12 smoke tests

**Constitutional Guarantees (PR146):**
- READ-ONLY: No execution, no trading
- Non-prescriptive: No should/must/recommend/advise
- No trading verbs: No buy/sell/swap/execute/sign/transfer
- No token literals: No SUI/USDC/BTC/ETH
- Label-only output: No numeric values in text
- No addresses: No 0x... patterns
- No causal coupling: No therefore/so/hence
- Table-first: Deterministic lookup (not inference)
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR146):**
```
Stress = Structural load state (not action)
Table-first approach = Fixed mapping, no inference

The stress engine:
  - Extracts regime label, band bucket, distortion presence
  - Looks up stress label from fixed table
  - Returns label-only result (CALM/TENSE/STRESSED/UNKNOWN)
  - Uses worst bucket across roles
  - Defensive: missing key → UNKNOWN + warning

The stress engine does NOT:
  - Recommend actions
  - Provide trading advice
  - Make decisions
  - Infer stress from other signals
  - Generate dynamic mappings

Relationship to v1.4:
  - Input: PR144 safe band guidance + PR129/PR134 distortion signals + v1.2 regime
  - Process: Fixed table lookup (regime × band × distortion)
  - Output: Stress label (no action recommendation)
  - Purpose: Display structural load state for human understanding
```

**Use Cases:**
1. **Stress state display**: Show CALM/TENSE/STRESSED for human review
2. **Fixed table lookup**: Deterministic, predictable results
3. **Bundle extraction**: Extract from artifact bundle automatically
4. **Worst bucket logic**: Handle multiple roles safely
5. **Constitutional validation**: Enforce stress ≠ action

**Explicit Non-Claims:**
- This is NOT an action recommendation
- This is NOT trading advice
- This is NOT a decision
- This is NOT eligibility determination
- This is NOT permission granting
- Stress label is descriptive only (not prescriptive or directive)

---

### v1.4 Action Shape Guidance v1 (PR147)

**Purpose:** Bundles PR144 (safe band) + PR146 (stress) + PR145 (overlay) + PR128 (eligibility) and returns label-only action shape. Action Shape = Display shape for user's own decision-making (not instruction, not recommendation). Table-first approach with fixed priority rules.

**⚠️ Constitutional Notice - Action Shape ≠ Instruction:**

```
This action shape does NOT:
- Recommend actions
- Provide trading advice
- Instruct what to do
- Make decisions
- Suggest trades
- Grant permission

This action shape ONLY:
- Describes action display shape (OBSERVE_ONLY/SIMULATION_ONLY/etc.)
- Uses fixed rule table (deterministic)
- Outputs label-only (no numeric values)
- Maintains READ-ONLY guarantees
- Displays shape for user's own decision-making
```

**What is Action Shape?**

Action Shape = Display shape label for user review (not action directive)
- UNKNOWN: Cannot determine from available inputs
- NO_ACTION: Ineligible state (no action consideration)
- OBSERVE_ONLY: Calm state, observe-only display (DRY_RUN_ONLY eligibility)
- SIMULATION_ONLY: Tense state, simulation display (DRY_RUN_ONLY eligibility)
- CONSIDER_ONLY: Consideration display (CONSIDERATION_ONLY eligibility)
- FREEZE_STATE: Elevated stress, freeze state display
- CONSTRAINED_STATE: Constrained state display

**API:**

```python
from action import build_action_shape_from_bundle_v1

# Artifact bundle
result = build_action_shape_from_bundle_v1(
    artifact_bundle={
        "artifacts": {
            "stress_rule": {"v14_stress_label": "CALM"},
            "eligibility": {"v12_eligibility_label": "ELIGIBLE_DRY_RUN_ONLY"},
        }
    }
)
print(result["action_record"]["v14_action_action_shape"])  # OBSERVE_ONLY
print(result["action_record"]["v14_action_summary"])  # Non-prescriptive summary
```

**Action Shape Rule Table (Fixed, Deterministic):**

Priority Rules (first-match-wins):
1. stress == UNKNOWN → UNKNOWN
2. eligibility == INELIGIBLE → NO_ACTION
3. stress == STRESSED → FREEZE_STATE
4. stress == TENSE:
   - eligibility == CONSIDERATION_ONLY → CONSIDER_ONLY
   - else → SIMULATION_ONLY
5. stress == CALM:
   - eligibility == CONSIDERATION_ONLY → CONSIDER_ONLY
   - else → OBSERVE_ONLY
6. default → UNKNOWN

**Stress Conflict Detection:**
- PR146 stress_rule (priority) vs PR145 stress_overlay (fallback)
- Conflict detected → warning + use PR146

**Files:**
- `python/action/v14_action_shape_schema.py` - Action shape schema
- `python/action/v14_action_shape_engine_v1.py` - Action shape engine
- `python/action/v14_action_constitutional_guard.py` - Constitutional guards
- `python/action/__init__.py` - Package exports
- `python/validation/pr147_action_shape_guidance_v1_smoke.py` - 14 smoke tests

**Constitutional Guarantees (PR147):**
- READ-ONLY: No execution, no trading
- Non-prescriptive: No should/must/recommend/advise
- No trading verbs: No buy/sell/swap/execute/sign/transfer
- No token literals: No SUI/USDC/BTC/ETH
- Label-only output: No numeric values in text
- No addresses: No 0x... patterns
- No causal coupling: No therefore/so/hence
- No action coupling: No "stressed so exit", "eligible therefore act"
- Table-first: Deterministic lookup (not inference)
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR147):**
```
Action Shape ≠ Instruction
Action Shape = Display shape for user's own decision-making

The action engine:
  - Extracts stress label (PR146) and eligibility label (PR128)
  - Checks for stress conflicts (PR146 vs PR145)
  - Looks up action shape from fixed rule table
  - Returns label-only result (no numeric values)
  - Creates non-prescriptive summary

The action engine does NOT:
  - Recommend actions
  - Provide trading advice
  - Make decisions
  - Grant permission
  - Instruct what to do
  - Infer action shape from other signals
  - Generate dynamic mappings

Relationship to v1.4:
  - Input: PR144 safe band + PR146 stress + PR145 overlay + PR128 eligibility
  - Process: Fixed rule table (stress × eligibility)
  - Output: Action shape label (no instruction)
  - Purpose: Display shape for user's own decision-making
```

**Use Cases:**
1. **Action shape display**: Show OBSERVE_ONLY/SIMULATION_ONLY/etc. for human review
2. **Fixed table lookup**: Deterministic, predictable results
3. **Bundle extraction**: Extract from artifact bundle automatically
4. **Stress conflict detection**: Detect and warn on PR146 vs PR145 conflicts
5. **Constitutional validation**: Enforce action shape ≠ instruction

**Explicit Non-Claims:**
- This is NOT an action recommendation
- This is NOT trading advice
- This is NOT a decision
- This is NOT an instruction
- This is NOT permission granting
- This is NOT a suggestion
- Action shape is display-only (not prescriptive, not directive, not permissive)

---

### v1.4 Watchlist + Observation Profile v1 (PR148)

**Purpose:** Define monitoring targets by pair_ref (= pair×source) and separate observation profiles. Watchlist = "What to observe" (pair_ref × source × profile_ref). Profile = "How to observe" (windows / cadence / featureset). Windows are NOT in watchlist, but in observation profiles to avoid combinatorial explosion.

**⚠️ Constitutional Notice - Watchlist ≠ Instruction:**

```
This watchlist does NOT:
- Recommend actions
- Provide trading advice
- Instruct what to do
- Make decisions
- Suggest trades
- Grant permission

This watchlist ONLY:
- Declares observation targets (pair_ref × source × profile_ref)
- References observation profiles for window configuration
- Maintains READ-ONLY guarantees
- Provides structure for observation planning
```

**What is Watchlist vs Profile?**

Watchlist = "What to observe"
- pair_ref: Unique identifier (e.g., "deep:SUI/USDC", treated as anonymous ID)
- source: Source label (e.g., "deep", "cetus")
- profile_ref: Observation profile reference (e.g., "CORE_3W")
- priority: CORE | EXTENDED | EXPERIMENTAL
- enabled: ON | OFF
- NO windows in watchlist items

Profile = "How to observe"
- windows_enabled: List of windows (SHORT/MEDIUM/LONG)
- cadence_label: Cadence (FAST/NORMAL/SLOW)
- featureset_ref: Featureset (FULL_MINIMAL/ALERT_MINIMAL/RESEARCH_MINIMAL)

**Why Separate Windows from Watchlist?**

Reason: Avoid combinatorial explosion and improve operational safety
- Without separation: N pairs × M windows = N×M items (explosion)
- With separation: N pairs + M profiles (manageable)
- Profiles are fixed, reusable templates
- Window changes affect all items using that profile

**API:**

```python
from watchlist import (
    build_watchlist_record_v1,
    expand_watchlist_to_observation_plan_v1,
    extract_pair_refs_v1,
    get_default_profiles,
)

# Build watchlist
items = [
    {
        "pair_ref": "deep:SUI/USDC",
        "source": "deep",
        "profile_ref": "CORE_3W",
        "priority": "CORE",
        "enabled": "ON",
    },
    {
        "pair_ref": "deep:DEEP/USDC",
        "source": "deep",
        "profile_ref": "ALERT_ONLY",
        "priority": "EXTENDED",
        "enabled": "ON",
    },
]
result = build_watchlist_record_v1(items)
watchlist_record = result["watchlist_record"]

# Expand to observation plan (adds windows from profiles)
plan_result = expand_watchlist_to_observation_plan_v1(watchlist_record)
observation_plan = plan_result["observation_plan"]

# deep:SUI/USDC → windows [SHORT, MEDIUM, LONG] (from CORE_3W)
# deep:DEEP/USDC → windows [SHORT] (from ALERT_ONLY)

# Extract pair_refs for TS-side data fetch bridge
pair_refs = extract_pair_refs_v1(watchlist_record, enabled_only=True)
# Returns: ["deep:SUI/USDC", "deep:DEEP/USDC"]
```

**Default Profiles (Built-in):**

- **CORE_3W**: SHORT/MEDIUM/LONG, NORMAL cadence, FULL_MINIMAL features
- **CORE_2W**: SHORT/MEDIUM, NORMAL cadence, FULL_MINIMAL features
- **ALERT_ONLY**: SHORT, FAST cadence, ALERT_MINIMAL features
- **RESEARCH**: MEDIUM/LONG, SLOW cadence, RESEARCH_MINIMAL features

**Engine Functions:**

1. `build_watchlist_record_v1(items, profiles=None)` - Build watchlist from items
2. `expand_watchlist_to_observation_plan_v1(watchlist_record, profiles_record=None)` - Expand watchlist with profile windows
3. `extract_pair_refs_v1(watchlist_record, enabled_only=True)` - Extract pair_refs for TS bridge

**Rules:**
- Watchlist items do NOT contain windows (windows come from profiles)
- Unknown profile_ref → UNKNOWN + warning (watchlist stays AVAILABLE)
- enabled=OFF excluded from observation plan
- Defensive: Invalid input → valid ERROR record
- Warning-only: Never raises exceptions

**Files:**
- `python/watchlist/v14_watchlist_schema.py` - Watchlist schema
- `python/watchlist/v14_observation_profile_schema.py` - Profile schema + default profiles
- `python/watchlist/v14_watchlist_engine_v1.py` - Engine (build/expand/extract)
- `python/watchlist/v14_watchlist_constitutional_guard.py` - Constitutional guards
- `python/watchlist/__init__.py` - Package exports
- `python/validation/pr148_watchlist_profile_v1_smoke.py` - 14 smoke tests

**Constitutional Guarantees (PR148):**
- READ-ONLY: No execution, no trading
- Non-prescriptive: No should/must/recommend/advise
- No trading verbs: No buy/sell/swap/execute/sign/transfer
- No token literals: No SUI/USDC/BTC/ETH in text fields
- Label-only output: No numeric values in text
- No addresses: No 0x... patterns
- No causal coupling: No therefore/so/hence
- No windows in watchlist: Windows belong in profiles
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR148):**
```
Watchlist = "What to observe" (pair_ref × source × profile_ref)
Profile = "How to observe" (windows / cadence / featureset)

The watchlist engine:
  - Builds watchlist from items (pair_ref × source × profile_ref)
  - Expands watchlist to observation plan by adding windows from profiles
  - Extracts pair_refs for TS-side data fetch bridge
  - Does NOT contain windows in watchlist items

The watchlist engine does NOT:
  - Recommend actions
  - Provide trading advice
  - Make decisions
  - Grant permission
  - Instruct what to do
  - Store windows in watchlist items (windows are in profiles)

Relationship to v1.4:
  - Input: Watchlist items (pair_ref × source × profile_ref)
  - Process: Expand with observation profiles
  - Output: Observation plan (items + windows)
  - Purpose: Declaration of observation targets and methodology
```

**Use Cases:**
1. **Watchlist declaration**: Define what to observe (pair_ref × source)
2. **Profile reuse**: Use fixed observation profiles across multiple pairs
3. **Observation plan generation**: Expand watchlist with profile windows
4. **TS bridge integration**: Extract pair_refs for data fetch
5. **Constitutional validation**: Enforce watchlist ≠ instruction

**Explicit Non-Claims:**
- This is NOT an action recommendation
- This is NOT trading advice
- This is NOT a decision
- This is NOT an instruction
- This is NOT permission granting
- This is NOT a suggestion
- Watchlist is declaration-only (not prescriptive, not directive, not permissive)
- pair_ref is treated as anonymous ID (Python does NOT interpret token names)

---

### v1.4 Shock Phase Detection Engine v1 (PR149)

**Purpose:** Detect shock phase from observation labels using fixed rules. Shock Phase = Structural phase label (not instruction, not prediction). Detects market state phases from Deep/Cetus observations (pair_ref-centric) for integration with v1.4 Stress / Action Shape / TS Executor.

**⚠️ Constitutional Notice - Shock Phase ≠ Instruction:**

```
This shock phase does NOT:
- Recommend actions
- Provide trading advice
- Instruct what to do
- Make decisions
- Suggest trades
- Grant permission
- Predict future outcomes

This shock phase ONLY:
- Describes structural phase label (PRE_SHOCK/UP_SHOCK/DOWN_SHOCK/etc.)
- Uses fixed rule detection from observation labels
- Outputs label-only (no numeric values)
- Maintains READ-ONLY guarantees
```

**What is Shock Phase?**

Shock Phase = Structural phase label based on observation labels (not raw numeric values)
- PHASE_UNKNOWN: Cannot determine from available observations
- PHASE_NORMAL: Normal market state (no shock pattern)
- PHASE_PRE_SHOCK: Pre-shock state (liquidity thinning + impulse)
- PHASE_UP_SHOCK: Upward shock (impulse_up + ask_absorption or agg_buy_dominance)
- PHASE_DOWN_SHOCK: Downward shock (impulse_down + bid_absorption or agg_sell_dominance)
- PHASE_UP_REVERSAL: Upward reversal (prev UP_SHOCK + impulse_down + agg_sell)
- PHASE_DOWN_REVERSAL: Downward reversal (prev DOWN_SHOCK + impulse_up + agg_buy)
- PHASE_RECOVERY: Recovery state (prev reversal/shock + impulse_flat + no_absorption)
- PHASE_ERROR: Detection error

**Observation Labels (Input):**

Observation labels (provided by upstream, not calculated by PR149):
- `price_impulse_label`: IMPULSE_UP / IMPULSE_DOWN / IMPULSE_FLAT / IMPULSE_UNKNOWN
- `absorption_label`: ASK_ABSORPTION / BID_ABSORPTION / NO_ABSORPTION / ABSORPTION_UNKNOWN
- `flow_dominance_label`: AGG_BUY_DOMINANCE / AGG_SELL_DOMINANCE / FLOW_BALANCED / FLOW_UNKNOWN
- `liquidity_thinning_label`: LIQUIDITY_THINNING / LIQUIDITY_OK / LIQUIDITY_UNKNOWN
- `shock_state_memory` (optional): prev_phase, prev_phase_age_label

**API:**

```python
from shock import detect_shock_phase_from_bundle_v1

# Artifact bundle with observations
bundle = {
    "artifacts": {
        "observations": {
            "deep:wBTC/USDC": {
                "price_impulse_label": "IMPULSE_DOWN",
                "absorption_label": "BID_ABSORPTION",
                "flow_dominance_label": "AGG_SELL_DOMINANCE",
                "liquidity_thinning_label": "LIQUIDITY_OK",
            }
        }
    }
}

result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
shock_record = result["shock_record"]

print(shock_record["v14_shock_phase_label"])  # PHASE_DOWN_SHOCK
print(shock_record["v14_shock_phase_direction"])  # DOWN
print(shock_record["v14_shock_basis_labels"])  # ["BASIS_IMPULSE_DOWN", "BASIS_BID_ABSORPTION", ...]
```

**Fixed Detection Rules (Priority, first-match-wins):**

1. Invalid input → PHASE_ERROR
2. Observation labels missing → PHASE_UNKNOWN
3. PRE_SHOCK: liquidity_thinning + (impulse_up or impulse_down) + flow_dominance != unknown
4. DOWN_REVERSAL: prev in {DOWN_SHOCK, PRE_SHOCK} + impulse_up + agg_buy_dominance
5. UP_REVERSAL: prev in {UP_SHOCK, PRE_SHOCK} + impulse_down + agg_sell_dominance
6. DOWN_SHOCK: impulse_down + (bid_absorption or agg_sell_dominance)
7. UP_SHOCK: impulse_up + (ask_absorption or agg_buy_dominance)
8. RECOVERY: prev in {UP_REVERSAL, DOWN_REVERSAL, UP_SHOCK, DOWN_SHOCK} + impulse_flat + no_absorption
9. NORMAL: impulse present but no rule matches

**Phase Direction:**
- UP_SHOCK, UP_REVERSAL → DIRECTION_UP
- DOWN_SHOCK, DOWN_REVERSAL → DIRECTION_DOWN
- PRE_SHOCK, NORMAL, RECOVERY → DIRECTION_NONE
- Others → DIRECTION_UNKNOWN

**Files:**
- `python/shock/v14_shock_phase_schema.py` - Shock phase schema (9 phase labels, 4 directions)
- `python/shock/v14_shock_phase_engine_v1.py` - Detection engine (fixed rules)
- `python/shock/v14_shock_constitutional_guard.py` - Constitutional guards
- `python/shock/__init__.py` - Package exports
- `python/validation/pr149_shock_phase_engine_v1_smoke.py` - 14 smoke tests

**Constitutional Guarantees (PR149):**
- READ-ONLY: No execution, no trading
- Non-prescriptive: No should/must/recommend/advise
- No trading verbs: No buy/sell/swap/execute/sign/transfer
- No token literals: No BTC/USDC/SUI/ETH in text
- Label-only output: No numeric values in text
- No addresses: No 0x... patterns
- No causal coupling: No therefore/so/hence
- No phase coupling: No "phase=DOWN_SHOCK therefore sell"
- Fixed rules: Deterministic detection (not inference, not prediction)
- Defensive: Invalid input → valid ERROR record
- Warning-only guards: Always exit 0

**Philosophy (PR149):**
```
Shock Phase = Structural phase label (not instruction, not prediction)

The shock phase engine:
  - Extracts observation labels from artifact bundle
  - Applies fixed detection rules (first-match-wins)
  - Returns label-only shock phase record
  - Tracks observation presence for diagnostics
  - Does NOT calculate observations (upstream responsibility)

The shock phase engine does NOT:
  - Recommend actions
  - Provide trading advice
  - Make decisions
  - Grant permission
  - Instruct what to do
  - Predict future phases
  - Calculate observation values (uses labels only)

Relationship to v1.4:
  - Input: Artifact bundle + pair_ref + observation labels
  - Process: Fixed rule detection
  - Output: Shock phase record (label-only)
  - Purpose: Structural phase detection for integration with Stress/Action Shape
```

**Use Cases:**
1. **Shock phase detection**: Detect PRE_SHOCK/UP_SHOCK/DOWN_SHOCK/REVERSAL/RECOVERY
2. **Fixed rule detection**: Deterministic, predictable results
3. **Bundle integration**: Extract from artifact bundle automatically
4. **State machine support**: Track prev_phase for reversal detection
5. **Constitutional validation**: Enforce shock phase ≠ instruction

**Explicit Non-Claims:**
- This is NOT an action recommendation
- This is NOT trading advice
- This is NOT a decision
- This is NOT an instruction
- This is NOT permission granting
- This is NOT a suggestion
- This is NOT a prediction of future phases
- Shock phase is label-only (not prescriptive, not directive, not predictive)
- Observation labels are provided by upstream (PR149 does NOT calculate them)

---

### Run Validations (v1.4)

```bash
cd ~/Meridian
source .venv/bin/activate

# PR144: Role Safe Band Guidance v1
python3 python/validation/pr144_role_safe_band_guidance_v1_smoke.py

# PR145: Safe Band × Distortion Stress Overlay v1
python3 python/validation/pr145_safe_band_distortion_overlay_v1_smoke.py

# PR146: Stress Rule Table v1
python3 python/validation/pr146_stress_rule_table_v1_smoke.py

# PR147: Action Shape Guidance v1
python3 python/validation/pr147_action_shape_guidance_v1_smoke.py

# PR148: Watchlist + Observation Profile v1
python3 python/validation/pr148_watchlist_profile_v1_smoke.py

# PR149: Shock Phase Detection Engine v1
python3 python/validation/pr149_shock_phase_engine_v1_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## v1.0 Infrastructure — Market Structure Intelligence Pipeline (READ-ONLY)

### v1.0 Philosophy: Intelligence Native Market Architecture

v1.0 Infrastructure builds on the execution constitution (v1.0) and intelligence native market (v1.1) to provide:
- End-to-end pipeline orchestration
- Artifact bundling and chain-of-custody
- Golden regression testing for determinism
- CLI demonstration interface
- Market structure vocabulary abstraction
- Vocabulary drift detection

**Pipeline Flow:**
```
Onchain Observation (PR107)
         ↓
Analytics Extension (PR109)
         ↓
Market Structure Vocabulary (PR119) ← Convert analytics to structural terms
         ↓
Vocabulary Drift Detection (PR120) ← Detect structural language shifts
         ↓
Entropy Regime (PR110)
         ↓
Policy Binding (PR111)
         ↓
Execution Preview (PR112)
         ↓
Human Approval Gate (PR113)
         ↓
Pipeline Orchestrator (PR115) ← Coordinate all layers
         ↓
Artifact Bundle (PR116) ← Chain-of-custody container
         ↓
CLI Demo (PR118) ← Human-readable digest
```

### v1.0 Pipeline Orchestrator v1 (PR115)

**Purpose:** Coordinate observation → vocabulary → drift → regime → policy → preview → approval pipeline.

**Orchestrator Philosophy:**
- Orchestrator = Pipeline Coordinator (not execution)
- Defensive layer-by-layer execution
- No execution, no trading, no recommendations
- READ-ONLY, non-evaluative, non-prescriptive

**Pipeline Stages (Ordered):**
1. **Onchain Observation** - Read pool/object state
2. **Analytics Extension** - Compute market structure metrics
3. **Market Structure Vocabulary** - Convert analytics to structural terms
4. **Vocabulary Drift Detection** - Detect term set changes (NEW in PR120)
5. **Entropy Regime** - Classify regime level
6. **Policy Binding** - Apply regime → permission rules
7. **Execution Preview** - Describe structural impact shape
8. **Human Approval** - Gate approval requirement

**Orchestrator Output:**
```json
{
  "orchestrator_status": "SUCCESS",
  "observation": {...},
  "analytics": {...},
  "vocabulary": {...},
  "drift": {...},
  "regime": {...},
  "policy": {...},
  "preview": {...},
  "approval": {...},
  "warnings": [...]
}
```

**Constitutional Guarantees:**
- Never raises exceptions (defensive)
- Skips failed layers (continues with warnings)
- No trading vocabulary or execution
- Exit code always 0 (warning-only)

### v1.0 Artifact Bundle Schema v1 (PR116)

**Purpose:** Chain-of-custody container for pipeline artifacts.

**Bundle Philosophy:**
- Bundle = Artifact Container (not execution)
- Fixed layer ordering (14 valid layer names)
- Digest-based integrity verification
- READ-ONLY, non-evaluative

**Valid Layer Names (Fixed Set):**
- `connection`, `provider_config`, `observation`
- `analytics`, `vocabulary`, `drift`
- `regime`, `policy`, `preview`, `approval`
- `orchestrator_output`, `bundle_metadata`
- `warnings`, `errors`

**Bundle Guards:**
1. **Overreach Guard** - Detects invalid layer names
2. **Ordering Consistency Guard** - Verifies layer order matches definition

**Example Bundle:**
```json
{
  "bundle_status": "AVAILABLE",
  "bundle_layers": [
    {"layer": "observation", "artifact": {...}},
    {"layer": "analytics", "artifact": {...}},
    {"layer": "vocabulary", "artifact": {...}},
    {"layer": "drift", "artifact": {...}},
    {"layer": "regime", "artifact": {...}}
  ],
  "bundle_digest": "sha256:abcd1234...",
  "bundle_warnings": []
}
```

### v1.0 Golden Fixtures & Regression Harness (PR117)

**Purpose:** Determinism proof using golden test vectors.

**Regression Philosophy:**
- Regression = Output Stability Verification (not optimization)
- Golden fixtures = Canonical test cases
- Deterministic output required (no randomness)
- READ-ONLY, non-evaluative

**Fixtures (v1.0):**
- `mock_connection.json` - Mock onchain connection
- `mock_provider_config.json` - Provider configuration
- `mock_observations_case_A.json` - Stable/low activity case
- `mock_observations_case_B.json` - High variation case
- `expected_bundle_case_A.json` - Expected output A
- `expected_bundle_case_B.json` - Expected output B

**Harness Checks:**
- Output matches expected bundle structure
- All required layers present
- No unexpected layers added
- Digest verification passes

### v1.0 CLI Demo v1 (PR118)

**Purpose:** One-command end-to-end pipeline with human-readable digest.

**CLI Philosophy:**
- CLI = Demo Interface (not production execution)
- Human-readable digest rendering
- No execution, no trading, no recommendations
- READ-ONLY, non-evaluative

**Usage:**
```bash
python3 python/cli/v10_meridian_cli.py \
  --connection mock_connection.json \
  --provider_config mock_provider_config.json
```

**Digest Output:**
```
Bundle Status: AVAILABLE

Observation: 10 observations collected
Analytics: Market cost regime counts available
Vocabulary: 8 structural terms identified
Drift: DRIFT_LOW classification (minor structural changes)
Regime: REGIME_MEDIUM (moderate variation)
Policy: DRY_RUN_ONLY (regime-based constraint)
Preview: Risk surface MEDIUM
Approval: REQUIRED (approval recommended)
```

**Constitutional Guard:**
- Detects instruction vocabulary in CLI output
- No "execute", "run", "approve" commands
- CLI is display-only interface

### v1.0 Market Structure Vocabulary Schema & Builder v1 (PR119)

**Purpose:** Convert analytics to stable structural vocabulary terms.

**Vocabulary Philosophy:**
- Vocabulary = Market Structure Language (not price, not ownership)
- Fixed term set (11 terms in 4 families)
- Presence-only mapping (no counts in output)
- READ-ONLY, non-evaluative

**Vocabulary Term Families:**

**1. Market Cost Regime (3 terms):**
- `COST_LOW_PRESENT` / `COST_MEDIUM_PRESENT` / `COST_HIGH_PRESENT`

**2. Liquidity Regime (3 terms):**
- `LIQUIDITY_LOW_PRESENT` / `LIQUIDITY_MEDIUM_PRESENT` / `LIQUIDITY_HIGH_PRESENT`

**3. Event Activity (2 terms):**
- `EVENT_ACTIVITY_PRESENT` / `EVENT_ACTIVITY_ABSENT`

**4. Object Dynamics (3 terms):**
- `OBJECT_DYNAMICS_DECREASE_PRESENT`
- `OBJECT_DYNAMICS_STABLE_PRESENT`
- `OBJECT_DYNAMICS_INCREASE_PRESENT`

**Mapping Rules:**
- Analytics distribution → Vocabulary term presence
- Count > 0 → `_PRESENT`
- Count == 0 → `_ABSENT`
- No numeric counts in output (constitutional)

**Example Vocabulary Record:**
```json
{
  "v10_vocab_mode": "ON",
  "v10_vocab_status": "AVAILABLE",
  "v10_vocab_terms": [
    "COST_LOW_PRESENT",
    "COST_MEDIUM_PRESENT",
    "LIQUIDITY_LOW_PRESENT",
    "EVENT_ACTIVITY_PRESENT",
    "OBJECT_DYNAMICS_STABLE_PRESENT"
  ],
  "v10_vocab_summary": "market structure vocabulary extracted from analytics. multiple regime types present.",
  "v10_vocab_basis": ["market_cost_regime_counts", "liquidity_regime_presence", "event_activity_frequency"]
}
```

**Constitutional Guards:**
- Token literal guard (SUI, USDC, BTC, ETH prohibited)
- Numeric pattern guard (counts, percentages, scores prohibited)
- Address pattern guard (0x... prohibited)
- Trading vocabulary guard (swap, buy, sell prohibited)
- Vocabulary term validation (only approved terms allowed)

### v1.0 Vocabulary Drift Detection Engine v1 (PR120)

**Purpose:** Detect market structure drift by comparing vocabulary windows.

**Drift Philosophy:**
- Drift = Structural Language Shift (not evaluation, not prediction)
- Qualitative classification only (no numeric output)
- Evidence = Term names only (no counts)
- READ-ONLY, non-evaluative, non-prescriptive

**Detection Approach (v1 - Static, Qualitative):**

1. **Extract term presence sets** from each window:
   - Window A (past): union of all terms across all vocab records
   - Window B (current): union of all terms across all vocab records

2. **Compute structural deltas:**
   - `terms_added`: terms in B but not in A (B \ A)
   - `terms_removed`: terms in A but not in B (A \ B)

3. **Bucket into drift levels** (INTERNAL bucketing - NO numbers in output):
   - `DRIFT_NONE`: no delta
   - `DRIFT_LOW`: small delta (1-2 terms)
   - `DRIFT_MEDIUM`: moderate delta (3-4 terms)
   - `DRIFT_HIGH`: large delta (5-6 terms)
   - `DRIFT_CRITICAL`: very large delta (7+ terms)
   - `UNCLASSIFIED`: insufficient data

4. **Generate evidence list** (term names only, no counts):
   - Format: `"{TERM_NAME}_ADDED"` or `"{TERM_NAME}_REMOVED"`
   - Example: `["COST_HIGH_PRESENT_ADDED", "EVENT_ACTIVITY_ABSENT_REMOVED"]`

**Example Drift Record:**
```json
{
  "v10_drift_mode": "ON",
  "v10_drift_status": "AVAILABLE",
  "v10_drift_level": "DRIFT_MEDIUM",
  "v10_drift_summary": "market structure drift classified as drift_medium. moderate structural changes detected. terms added and removed.",
  "v10_drift_basis": ["vocab_window_A", "vocab_window_B"],
  "v10_drift_evidence": [
    "COST_HIGH_PRESENT_ADDED",
    "LIQUIDITY_MEDIUM_PRESENT_ADDED",
    "EVENT_ACTIVITY_ABSENT_REMOVED",
    "OBJECT_DYNAMICS_DECREASE_PRESENT_REMOVED"
  ],
  "v10_drift_warnings": []
}
```

**Constitutional Guards (STRENGTHENED for PR120):**

**1. Numeric Pattern Guard (STRENGTHENED):**
- Detects explicit counts: "3 terms", "5 changes", "10 deltas"
- Detects percentages: "50%", "10 percent"
- Detects numeric assignments: "delta=3", "count=5", "score=0.8"
- Detects decimal numbers (excluding version numbers like "v1.0")
- Detects currency symbols ($, ¥, €)

**2. Drift Level Validation (NEW):**
- Validates drift level is from approved set
- Only `DRIFT_NONE`, `DRIFT_LOW`, `DRIFT_MEDIUM`, `DRIFT_HIGH`, `DRIFT_CRITICAL`, `UNCLASSIFIED` allowed

**3. Inherited Guards:**
- Token literal guard (from PR119)
- Trading vocabulary guard (from PR112)
- Execution operation guard (from PR100)
- Address pattern guard (from PR102)
- Asset vocabulary guard (from PR108)
- Action vocabulary guard (from PR111)
- Forbidden vocabulary guard (from PR100)

**Important Constraints:**
- **NO numeric patterns in output** - Summary must use qualitative language only
  - ❌ "5 terms added and 3 terms removed"
  - ✅ "terms added and removed"
  - ✅ "moderate structural changes detected"
- **Evidence format** - Term names only, no counts
  - ❌ "COST_HIGH_PRESENT_ADDED (count=5)"
  - ✅ "COST_HIGH_PRESENT_ADDED"
- **Drift level** - Decided internally, never exposed as numbers
  - Internal: `total_delta = len(terms_added) + len(terms_removed)`
  - External: `"DRIFT_MEDIUM"` (label only)

**Usage:**
```python
from drift import detect_market_structure_drift_v1, validate_drift_record

# Detect drift between two vocabulary windows
vocab_window_A = [vocab_record_1, vocab_record_2]  # Past window
vocab_window_B = [vocab_record_3, vocab_record_4]  # Current window

drift = detect_market_structure_drift_v1(vocab_window_A, vocab_window_B)

# Validate against constitutional guards
warnings = validate_drift_record(drift)

if warnings:
    print(f"Constitutional violations detected: {len(warnings)} warnings")
    for warning in warnings:
        print(f"  - {warning}")
```

**Defensive Behavior:**
- None/empty windows → `UNCLASSIFIED` or `ERROR`
- Invalid inputs → `ERROR` record (never raises)
- Warning-only (exit code always 0)

### v1.0 Drift → Reflection/Boundary/Execution Binding v1 (PR121)

**Purpose:** Bind drift classification into downstream constitutional layers as structure, not action.

**Binding Philosophy:**
- Drift does not mean "trade" or "stop"
- Drift means: structure is moving
- Binding = Constitutional Gate (not action/recommendation)

PR121 integrates drift detection (PR120) into the explainability chain:

**1. Drift Reflection Attachment v1**

Attaches drift classification to reflection records as structural addenda.

**File:** `python/bridge/v10_drift_to_reflection_attachment_v1.py`

**Behavior:**
- Adds `pr120_drift_record` to reflection artifacts
- Adds `v10_drift_level` to reflection basis
- Appends drift context to reflection summary (non-prescriptive)
- Never modifies reflection tag
- Defensive (None → return original or empty)

**Example:**
```python
from bridge.v10_drift_to_reflection_attachment_v1 import attach_drift_to_reflection_v1

# Attach drift to reflection
enhanced = attach_drift_to_reflection_v1(reflection_record, drift_record)

# Result includes drift artifacts and basis
print(enhanced["v7_reflection_artifacts"])  # ["pr120_drift_record"]
print(enhanced["v7_reflection_basis"])      # [..., "v10_drift_level"]
```

**2. Drift Boundary Hinting v1**

Enhances boundary records with drift-based observability stability hints.

**File:** `python/boundary/v10_drift_boundary_hint_engine_v1.py`

**Behavior:**
- Adds drift hint to boundary description (non-prescriptive)
- Maps drift levels to observability stability:
  - `DRIFT_CRITICAL` → "observability unstable under critical drift"
  - `DRIFT_HIGH` → "observability unstable under high drift"
  - `DRIFT_MEDIUM` → "observability moderate under drift"
  - `DRIFT_LOW` → "observability stable under low drift"
  - `DRIFT_NONE` → "observability stable with no drift"
- Never modifies boundary type
- Defensive (None → return original or empty)

**Example:**
```python
from boundary.v10_drift_boundary_hint_engine_v1 import hint_boundary_with_drift_v1

# Hint boundary with drift
enhanced = hint_boundary_with_drift_v1(boundary_record, drift_record)

# Result includes drift-based observability hint
print(enhanced["v9_boundary_description"])
# "sampling boundary detected. observability unstable under critical drift."
```

**3. Drift Execution Policy Binding v1 (Conservative)**

Binds drift classification to execution permission with conservative rules.

**File:** `python/policy/v10_drift_execution_policy_binding_v1.py`

**Static Binding Rules (v1 - Conservative):**

| Drift Level | Permission Override | Constraint Label |
|-------------|---------------------|------------------|
| `DRIFT_CRITICAL` | `HOLD` | `drift_critical_observed` |
| `DRIFT_HIGH` | `DRY_RUN_ONLY` | `drift_high_observed` |
| `DRIFT_MEDIUM` | No override | `drift_medium_observed` |
| `DRIFT_LOW` | No override | `drift_low_observed` |
| `DRIFT_NONE` | No override | `drift_none_observed` |
| `UNCLASSIFIED` | No override | `drift_unclassified` |

**Permission Override Logic:**
- **HOLD**: Hard stop (critical drift - structure highly unstable)
- **DRY_RUN_ONLY**: Simulation only (high drift - structure unstable)
- **No override**: Defer to upstream execution engine (low/medium/none drift)

**Restrictiveness Order:** `HOLD` > `DRY_RUN_ONLY` > `ALLOW` > `UNKNOWN`
- Always selects more restrictive permission between current and override

**Example:**
```python
from policy.v10_drift_execution_policy_binding_v1 import bind_drift_to_execution_policy_v1

# Bind drift to execution policy
enhanced = bind_drift_to_execution_policy_v1(execution_record, drift_record)

# DRIFT_CRITICAL overrides permission to HOLD
print(enhanced["v10_execution_permission"])  # "HOLD"
print(enhanced["v10_execution_constraints"]) # ["drift_critical_observed"]
```

**4. Drift Policy Constitutional Guard**

Enforces constitutional constraints on drift policy binding outputs.

**File:** `python/policy/v10_drift_policy_constitutional_guard.py`

**Guards (STRENGTHENED):**
1. **Numeric Pattern Guard** - No counts, percentages, scores
2. **Token Literal Guard** - No SUI, USDC, BTC, ETH
3. **Address Pattern Guard** - No 0x... patterns
4. **Trading Vocabulary Guard** - No swap, buy, sell, execute
5. **Execution Operation Guard** - No transaction, broadcast, submit
6. **Forbidden Vocabulary Guard** - No good/bad, correct/wrong
7. **Prescriptive Language Guard (NEW)** - No should/must, proceed/stop/pause

**Example:**
```python
from policy.v10_drift_policy_constitutional_guard import validate_drift_policy_binding

# Validate binding output
warnings = validate_drift_policy_binding(enhanced_execution)

# Detects violations
if warnings:
    for warning in warnings:
        print(f"⚠ {warning}")
```

**Integration into Pipeline:**

```
Vocabulary (PR119)
         ↓
Drift Detection (PR120) ← Detect structural language shifts
         ↓
Drift Reflection Attachment (PR121) ← Add to explainability chain
         ↓
Drift Boundary Hinting (PR121) ← Enhance observability description
         ↓
Drift Execution Binding (PR121) ← Conservative permission gating
         ↓
Regime Classification (PR110)
         ↓
Policy Binding (PR111)
         ↓
Execution Preview (PR112)
```

**Important:**
- Drift binding is **classification only** (not action)
- HOLD/DRY_RUN_ONLY are **permission labels** (not commands)
- All outputs remain **non-prescriptive** (no "should", "must", "pause")
- Constraint labels are **structural context only** (not instructions)

### Constitutional Constraints (v1.0 Infrastructure)

All v1.0 infrastructure components enforce:

- **READ-ONLY**: No execution, no signing, no transaction construction
- **Non-evaluative**: No good/bad, correct/wrong vocabulary
- **Non-scoric**: No scores, grades, rankings
- **Non-prescriptive**: No "should" or recommendations
- **No amounts**: Numeric patterns prohibited in output
- **No token literals**: SUI, USDC, BTC, ETH prohibited
- **No addresses**: 0x... patterns prohibited
- **No trading vocabulary**: swap, buy, sell, execute, sign, transfer prohibited
- **Defensive**: Never raises exceptions (returns ERROR records)
- **Warning-only**: Exit code always 0

### Run Validations (v1.0 Infrastructure)

```bash
cd ~/Meridian
source .venv/bin/activate
python3 python/validation/pr115_pipeline_orchestrator_v1_smoke.py
python3 python/validation/pr116_artifact_bundle_schema_smoke.py
python3 python/validation/pr117_golden_regression_harness_smoke.py
python3 python/validation/pr118_cli_demo_smoke.py
python3 python/validation/pr119_market_structure_vocabulary_smoke.py
python3 python/validation/pr120_market_structure_drift_smoke.py
python3 python/validation/pr121_drift_binding_smoke.py
```

All scripts exit 0 (warning-only, never fails).

---

## Status

Meridian is under active development.
v0.2 implements constitutional regime-first decision making with full compliance validation.
v0.5 completes observation infrastructure (shadow diff, analytics, reporting).
v0.6 introduces interpretation (structural meaning without judgment).
v0.7 introduces reflection (observing interpretation system characteristics).
v0.8 introduces blindspot (observing structural absences in interpretation/reflection systems).
v0.9 introduces boundary (classifying structural limits of observability).
v1.0 introduces execution constitution (boundary → executability without trading).
v1.1 introduces intelligence native market (onchain regime classification, policy binding, execution preview, human approval).
v1.0 infrastructure completes end-to-end pipeline (orchestrator, artifact bundling, regression testing, CLI demo, market structure vocabulary, vocabulary drift detection, drift binding into explainability chain).

Meridian optimizes for **survival first**, because only surviving systems get to compound.

---

**Meridian**  
*Intelligence Against Entropy.*
