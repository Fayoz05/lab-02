# Lab 02 — Exact function rules

Keep these public names. Do not change the caller's input objects.

## Event input rules

Each event must be an object with exactly six keys: `tx_id, account, category, amount, occurred_at, currency`. Missing or extra keys are errors.

- IDs and category must be strings. Strip spaces at both ends. Reject empty results. Keep letter case.
- Strip currency spaces and make it uppercase. Accept only `UZS`.
- Amount may be a JSON number or string, but not a Boolean. Use `Decimal(str(value))`.
- Amount must be finite, positive, at most `Decimal('1000000000000')` (10^12 UZS),
  and have no fraction of a cent: `amount == amount.quantize(Decimal('0.01'))`.
- `1.000` is allowed; `1.001` is not. Reject NaN and infinity.
- Use Decimal precision of at least 28. Assume each account total stays below 10^24 UZS.
  Cent totals are exact within these limits. Division may round repeating decimals.
  Do not round a mean again before comparing it with a new amount.
- Time must be an ISO-8601 string with a UTC offset or `Z`. Convert to UTC.
  Event times may be out of order. Process the physical lines in arrival order.

Example valid input:

```json
{"tx_id":"T1","account":"A1","category":"food","amount":"12.50","occurred_at":"2026-09-01T10:00:00Z","currency":"UZS"}
```

## `Transaction`

Use a frozen, slotted dataclass with fields: `tx_id: str, account: str, category: str, amount: Decimal, occurred_at: datetime, currency: str`. Its constructor checks already-normalized values: stripped nonempty strings, a valid Decimal amount, a UTC-aware datetime, and currency exactly `UZS`. Raise `ValueError` for invalid construction.

## `parse_event(raw)`

Check an external mapping using the event rules. Normalize values and return a `Transaction`. Raise `ValueError` for all invalid inputs, including values that are not objects and objects with missing or extra keys.

## `iter_jsonl(path)`

Return a lazy iterator of raw UTF-8 lines, including blank lines. Do not load the whole file. Close the file when the iterator finishes or is closed.

## `RollingWindow(size=3)`

Size must be an integer at least 3. Do not accept a Boolean size.

| Member | Required result |
|---|---|
| `.total` | Decimal total; initially zero |
| `.mean` | Decimal mean, or `None` when empty |
| `.values` | Independent tuple of current amounts |
| `len(window)` | Current number of amounts |
| `.push(amount)` | Check a Decimal amount, remove the oldest value if full, then update values and total |

Use the event amount limits in `push`. Invalid amounts raise `ValueError` and do not change the window. Use a fixed number of arithmetic updates per event, called O(1) work. Do not sum the whole window for every event.

## `monitor(lines, window_size=3, threshold=Decimal('2'))`

Read a single-pass iterable of raw JSON lines. Do not loop through it twice. Threshold must be a finite Decimal at least 1. Validate threshold and window size before processing, even when input is empty.

For each line: parse JSON → validate event → check duplicate → check prior window → update state. A bad record does not reserve its ID. The first valid event for an ID wins across all accounts. Later valid duplicates never change totals or windows, even if their values differ.

Flag a payment when its prior account window has at least three values and `amount >= threshold * prior_mean`. Compare before adding the payment. Flagged accepted payments still enter totals and windows.

## Return dictionary from `monitor`

Return these four outputs. Empty tables must still have these columns in this order:

| Key | Required result |
|---|---|
| `metrics` | Dictionary of integer counts: `received, accepted, duplicates, rejected` |
| `summary` | DataFrame: `account, count, total, mean, dominant_category, window_values, window_mean` |
| `anomalies` | DataFrame: `line, tx_id, account, amount, prior_mean, ratio` |
| `rejected` | DataFrame: `line, reason` |

- Count every physical line as received. Other counts must add up to received.
- Sort summary by account. Use accepted events only for counts, totals, and means.
- Dominant category means the most frequent accepted category. If counts tie,
  choose the smallest category string in Python string order.
- Monetary values, window means, and ratios use Decimal. `window_values` is a tuple.
- Anomaly `ratio = amount / prior_mean`. Keep anomaly and error rows in arrival order.
- `line` starts at 1. Count blank lines too.
- Use `invalid_json` for JSON-reading errors, including blank lines.
- Use `invalid_event` for decoded JSON that fails event rules. Do not count it as a duplicate.

Use a generator, seen-ID set, per-account bounded `deque`, running totals, `defaultdict`, and `Counter`. Do not keep a full accepted-event list. The seen-ID set, accounts, categories, and saved output rows can still grow.
