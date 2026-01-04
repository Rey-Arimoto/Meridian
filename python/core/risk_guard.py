from dataclasses import dataclass
from typing import Optional

@dataclass
class RiskState:
    last_guard_type: Optional[str] = None
    emergency_reason: Optional[str] = None

class RiskGuard:
    def __init__(self):
        self.state = RiskState()

    def clear(self):
        self.state.last_guard_type = None
        self.state.emergency_reason = None
