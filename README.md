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

## Status

Meridian is under active development.
v0.2 implements constitutional regime-first decision making with full compliance validation.
v0.5 completes observation infrastructure (shadow diff, analytics, reporting).
v0.6 introduces interpretation (structural meaning without judgment).

Meridian optimizes for **survival first**, because only surviving systems get to compound.

---

**Meridian**  
*Intelligence Against Entropy.*
