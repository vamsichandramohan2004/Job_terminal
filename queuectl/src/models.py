from dataclasses import dataclass, asdict
from typing import Optional
import datetime

@dataclass
class Job:
    id: str
    command: str
    state: str = 'pending'       # pending | processing | completed
    attempts: int = 0
    max_retries: int = 3
    created_at: str = None
    updated_at: str = None
    next_attempt_ts: int = 0     # epoch seconds
    timeout: int = 60            # seconds

    def __post_init__(self):
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now