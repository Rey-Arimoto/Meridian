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
AGENT_VERSION = "meridian_v0_2_constitutional"
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
