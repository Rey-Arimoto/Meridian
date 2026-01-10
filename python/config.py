# python/config.py
SYMBOL = "sui"
VS_CURRENCY = "usd"

# Signal windows
MA_PERIOD = 14
ENTROPY_WINDOW = 10

# Constitutional freeze threshold (basis points: 0..10000)
CRITICAL_ENTROPY_BP = 9000  # 90.00%

# Runtime
INTERVAL_SECONDS = 60

# Logs (repo root 기준: logs/...)
LOG_CSV_PATH = "logs/meridian_realtime_log.csv"

# Identity
AGENT_VERSION = "meridian_v0_3_intent"  # PR15A: Intent as first-class citizen
ENV_NAME = "local_paper"

# Regime classifier thresholds (v0.2)
# NOTE: RegimeClassifier uses these by default but they can be overridden
REGIME_THRESHOLDS = {
    "critical_entropy_bp": 9000,  # HALT threshold (must match CRITICAL_ENTROPY_BP)
    "volatile_entry": 7000,       # Enter volatile regime
    "volatile_exit": 6000,        # Exit volatile regime (hysteresis)
    "emerging_entry": 3500,       # Enter emerging trend
    "emerging_exit": 2500,        # Exit emerging trend (hysteresis)
    "stable_max": 2000,           # Max entropy for stable regime
}

# Safety Overlay parameters (v0.2 PR5)
# NOTE: These are fixed values for PR5; tuning deferred to PR6
OVERLAY_ENABLED = True
COOLDOWN_SECONDS = 600          # 10 minutes between weight changes
MAX_DW_PER_STEP = 0.05          # Maximum 5% weight change per step
MIN_DW_IGNORE = 0.02            # Ignore changes below 2%

# v0.2 Required Log Columns (PR13B)
# These columns are mandatory for v0.2 pipeline (PR8B gate will reject logs without them)
V0_2_REQUIRED_COLUMNS = ["regime", "base_action", "decision_reason"]

# v0.5 Decision Engine Selector (PR43)
# Controls which decision engine generates v0.5 decision records
# Options: "v1" (mirror base_action), "v2" (rule overlay / regime-aware)
# Default: "v1" (safe, minimal)
DECISION_ENGINE_VERSION = "v1"

# v0.5 Decision Engine Shadow Mode (PR44)
# Controls whether to generate both v1 and v2 decision records simultaneously
# False (default): Only primary engine generates record (PR43 behavior)
# True: Both v1 and v2 generate records (primary + shadow for comparison)
# Shadow mode enables future comparison without changing behavior
DECISION_ENGINE_SHADOW_MODE = False
