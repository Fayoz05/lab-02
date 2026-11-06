"""Implement the public API described in README.md. No I/O at import time."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

@dataclass(frozen=True, slots=True)
class Transaction:
    tx_id: str
    account: str
    category: str
    amount: Decimal
    occurred_at: datetime
    currency: str = "USD"

    def __post_init__(self):
        raise NotImplementedError("T1: enforce canonical record invariants")

def parse_event(raw):
    raise NotImplementedError("T1: validate external input and normalize fields")

def iter_jsonl(path):
    raise NotImplementedError("T2: yield raw lines lazily")

class RollingWindow:
    def __init__(self, size=3):
        raise NotImplementedError("T3: initialize bounded rolling state")
    def __len__(self):
        raise NotImplementedError
    @property
    def total(self):
        raise NotImplementedError
    @property
    def mean(self):
        raise NotImplementedError
    @property
    def values(self):
        raise NotImplementedError
    def push(self, amount):
        raise NotImplementedError("T3: evict and update in O(1) arithmetic")

def monitor(lines: Iterable[str], window_size=3, threshold=Decimal("2")):
    raise NotImplementedError("T2/T3: consume, classify, update and summarize")
