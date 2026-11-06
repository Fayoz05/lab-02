"""Implement the public API described in README.md. No I/O at import time."""
import json
from collections import Counter, defaultdict, deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext

import pandas as pd


MAX_AMOUNT = Decimal("1000000000000")
CENT = Decimal("0.01")

SUMMARY_COLUMNS = [
    "account", "count", "total", "mean",
    "dominant_category", "window_values", "window_mean"
]

ANOMALY_COLUMNS = [
    "line", "tx_id", "account", "amount", "prior_mean", "ratio"
]

REJECTED_COLUMNS = ["line", "reason"]

REQUIRED_KEYS = {
    "tx_id", "account", "category",
    "amount", "occurred_at", "currency"
}

def _valid_amount(amount):
    """Check whether an amount follows the lab rules."""
    if not isinstance(amount, Decimal):
        return False

    if not amount.is_finite() or amount <= 0 or amount > MAX_AMOUNT:
        return False

    try:
        with localcontext() as context:
            context.prec = max(context.prec, 28)
            return amount == amount.quantize(CENT)
    except InvalidOperation:
        return False


def _divide(first, second):
    """Divide Decimal values with at least 28 digits of precision."""
    with localcontext() as context:
        context.prec = max(context.prec, 28)
        return first / second


@dataclass(frozen=True, slots=True)
class Transaction:
    tx_id: str
    account: str
    category: str
    amount: Decimal
    occurred_at: datetime
    currency: str = "USD"

    def __post_init__(self):
        for value in (self.tx_id, self.account, self.category):
            if (
                not isinstance(value, str)
                or not value
                or value != value.strip()
            ):
                raise ValueError("Invalid text field")

        if self.currency not in {"UZS", "USD"}:
            raise ValueError("Currency must be UZS or USD")

        if not _valid_amount(self.amount):
            raise ValueError("Invalid amount")

        if not isinstance(self.occurred_at, datetime):
            raise ValueError("Invalid datetime")

        if (
            self.occurred_at.tzinfo is None
            or self.occurred_at.utcoffset() is None
            or self.occurred_at.utcoffset().total_seconds() != 0
        ):
            raise ValueError("Datetime must be UTC")


def parse_event(raw):
    """Validate and normalize one transaction dictionary."""
    if not isinstance(raw, Mapping):
        raise ValueError("Event must be a mapping")

    if set(raw.keys()) != REQUIRED_KEYS:
        raise ValueError("Event must contain exactly six required keys")

    def clean_text(value, field):
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")

        value = value.strip()

        if not value:
            raise ValueError(f"{field} cannot be empty")

        return value

    tx_id = clean_text(raw["tx_id"], "tx_id")
    account = clean_text(raw["account"], "account")
    category = clean_text(raw["category"], "category")
    currency = clean_text(raw["currency"], "currency").upper()

    raw_amount = raw["amount"]

    if isinstance(raw_amount, bool) or not isinstance(
        raw_amount, (int, float, str)
    ):
        raise ValueError("Invalid amount type")

    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid amount") from None

    if not _valid_amount(amount):
        raise ValueError("Invalid amount")

    raw_date = raw["occurred_at"]

    if not isinstance(raw_date, str):
        raise ValueError("Date must be an ISO-8601 string")

    try:
        date_text = raw_date.strip()

        if date_text.endswith("Z"):
            date_text = date_text[:-1] + "+00:00"

        occurred_at = datetime.fromisoformat(date_text)

        if (
            occurred_at.tzinfo is None
            or occurred_at.utcoffset() is None
        ):
            raise ValueError("Timezone is required")

        occurred_at = occurred_at.astimezone(timezone.utc)

    except (ValueError, OverflowError):
        raise ValueError("Invalid datetime") from None

    return Transaction(
        tx_id=tx_id,
        account=account,
        category=category,
        amount=amount,
        occurred_at=occurred_at,
        currency=currency,
    )

def iter_jsonl(path):
    """Yield raw UTF-8 lines lazily and close the file afterwards."""
    with open(path, "r", encoding="utf-8") as file:
        yield from file

class RollingWindow:
    """Store the most recent accepted amounts for one account."""

    def __init__(self, size=3):
        if isinstance(size, bool) or not isinstance(size, int) or size < 3:
            raise ValueError("Window size must be an integer >= 3")

        self._size = size
        self._values = deque()
        self._total = Decimal("0")

    def __len__(self):
        return len(self._values)

    @property
    def total(self):
        return self._total

    @property
    def mean(self):
        if not self._values:
            return None

        return _divide(self._total, Decimal(len(self._values)))

    @property
    def values(self):
        return tuple(self._values)

    def push(self, amount):
        """Add an amount and evict the oldest value when necessary."""
        if not _valid_amount(amount):
            raise ValueError("Invalid amount")

        if len(self._values) == self._size:
            oldest = self._values.popleft()
            self._total -= oldest

        self._values.append(amount)
        self._total += amount


def monitor(
    lines: Iterable[str],
    window_size=3,
    threshold=Decimal("2")
):
    """Process a single-pass stream of JSONL transaction records."""

    # Validate arguments before reading input.
    if (
        isinstance(window_size, bool)
        or not isinstance(window_size, int)
        or window_size < 3
    ):
        raise ValueError("Window size must be an integer >= 3")

    if (
        not isinstance(threshold, Decimal)
        or not threshold.is_finite()
        or threshold < Decimal("1")
    ):
        raise ValueError("Threshold must be a finite Decimal >= 1")

    metrics = {
        "received": 0,
        "accepted": 0,
        "duplicates": 0,
        "rejected": 0,
    }

    seen_ids = set()
    windows = defaultdict(lambda: RollingWindow(window_size))
    accounts = defaultdict(
        lambda: {
            "count": 0,
            "total": Decimal("0"),
            "categories": Counter(),
        }
    )

    anomaly_rows = []
    rejected_rows = []

    for line_number, raw_line in enumerate(lines, start=1):
        metrics["received"] += 1

        # 1. Parse JSON.
        try:
            raw_event = json.loads(raw_line)
        except (json.JSONDecodeError, TypeError, ValueError):
            rejected_rows.append({
                "line": line_number,
                "reason": "invalid_json",
            })
            metrics["rejected"] += 1
            continue

        # 2. Validate event.
        try:
            transaction = parse_event(raw_event)
        except ValueError:
            rejected_rows.append({
                "line": line_number,
                "reason": "invalid_event",
            })
            metrics["rejected"] += 1
            continue

        # 3. Check duplicates only after successful validation.
        if transaction.tx_id in seen_ids:
            metrics["duplicates"] += 1
            continue

        seen_ids.add(transaction.tx_id)

        # 4. Check the previous account window.
        window = windows[transaction.account]

        if len(window) >= 3:
            prior_mean = window.mean

            if transaction.amount >= threshold * prior_mean:
                anomaly_rows.append({
                    "line": line_number,
                    "tx_id": transaction.tx_id,
                    "account": transaction.account,
                    "amount": transaction.amount,
                    "prior_mean": prior_mean,
                    "ratio": _divide(transaction.amount, prior_mean),
                })

        # 5. Update account statistics.
        account_data = accounts[transaction.account]

        account_data["count"] += 1
        account_data["total"] += transaction.amount
        account_data["categories"][transaction.category] += 1

        # 6. Add the payment to the rolling window.
        window.push(transaction.amount)

        metrics["accepted"] += 1

    # Build summary table.
    summary_rows = []

    for account in sorted(accounts):
        data = accounts[account]
        categories = data["categories"]

        dominant_category = min(
            categories,
            key=lambda category: (-categories[category], category)
        )

        summary_rows.append({
            "account": account,
            "count": data["count"],
            "total": data["total"],
            "mean": _divide(
                data["total"],
                Decimal(data["count"])
            ),
            "dominant_category": dominant_category,
            "window_values": windows[account].values,
            "window_mean": windows[account].mean,
        })

    summary = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    anomalies = pd.DataFrame(anomaly_rows, columns=ANOMALY_COLUMNS)
    rejected = pd.DataFrame(rejected_rows, columns=REJECTED_COLUMNS)

    return {
        "metrics": metrics,
        "summary": summary,
        "anomalies": anomalies,
        "rejected": rejected,
    }