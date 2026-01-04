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
AGENT_VERSION = "meridian_v0_1_composite_entropy"
ENV_NAME = "local_paper"
