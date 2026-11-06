# Lab 02 report

**Student ID:** MDS 1015  
**Submission PR/LMS link:** TODO — add your Pull Request link and final commit SHA  
**Python and package versions:** Python 3.12.2, Windows 11, pytest 9.2.0. pandas version 2.2.3


## 1. Reading and checking records (T1–T2)

The input is a JSON Lines file. I used a lazy iterator so that the program reads one physical line when it is requested instead of loading the complete file into memory. Every physical line is counted, including a malformed or blank line.

The processing order is important: first the line is decoded as JSON, then the event is validated, and only then is its transaction ID checked for duplication. This means an invalid record cannot reserve an ID. The first valid record with an ID is accepted. A later valid record with the same ID is counted as a duplicate and does not change any totals or account windows.

The supplied dataset contains 20 physical lines: 20 received, 11 accepted, 1 duplicate, and 8 rejected. The reconciliation check passes:

11 + 1 + 8 = 20.

Line 6 repeats the valid `T4` ID from line 5 and is counted as a duplicate. Line 7 has amount `0.00` and is rejected; line 8 reuses ID `T5` with a valid amount and is accepted. This demonstrates that a rejected event does not reserve its ID. Line 18 contains malformed JSON and is rejected as `invalid_json`; the invalid event records are reported as `invalid_event`.

For T1, a valid example normalizes surrounding spaces in the transaction ID, account, and category. It converts the ISO-8601 timestamp to a UTC-aware datetime and stores the amount as `Decimal('12.50')`. Invalid-input checks cover a Boolean amount, a non-finite amount, an amount with a fraction of a cent, an unsupported currency, and a timestamp without a timezone.

## 2. Windows and data structures (T1–T3)

`Transaction` is a frozen, slotted dataclass. Its validated fields cannot be reassigned, and slots avoid a normal per-instance attribute dictionary. `parse_event` validates and normalizes the input. `Decimal` is used for monetary values because binary floating-point cannot represent every decimal fraction exactly.

The JSONL generator does not retain all input lines. A set tracks accepted transaction IDs, `defaultdict` creates per-account state, `Counter` tracks category frequencies, and a bounded `deque` stores recent amounts. The rolling window keeps a running `Decimal` total: when the window is full, it subtracts the oldest value and adds the new one. This makes each update O(1), rather than summing the whole window for every payment.

The anomaly rule checks a payment against the prior window before adding it, so the payment cannot change its own baseline. At least three prior accepted payments are required. In the exact-threshold example, the previous values are 10.00, 11.00, and 12.00. Their mean is 11.00, so an amount of 22.00 is exactly twice the prior mean and meets a threshold of 2. A flagged payment is still accepted and added to the account totals and rolling window.

The dataset produces three anomalies: line 5 (`T4`, amount 22.00, prior mean 11.00), line 11 (`B4`, amount 0.40, prior mean 0.20), and line 19 (`T6`, amount 100.00, prior mean approximately 15.6667).

The account summary reports six accepted events and a total of 168.00 for A1, and five accepted events and a total of 1.10 for A2. An amount must be positive, finite, no more than 10^12, and exact to a cent. Decimal calculations use a precision of at least 28 digits; division can still be rounded by the active Decimal context.

## 3. Time and memory experiment (T4)

The benchmark compares list and set membership at collection sizes 100, 1,000, and 10,000. Each size uses five repeats and 500 membership queries per repeat. Collection construction is outside the timed section, so the measurement covers membership queries only.

The earlier recorded benchmark was run with Python 3.14.6 on Windows 11, not the project interpreter Python 3.12.2. Its preliminary medians were:

| Size | List median (ms) | Set median (ms) |
|---:|---:|---:|
| 100 | 12.8257 | 0.0896 |
| 1,000 | 80.8142 | 0.1900 |
| 10,000 | 378.9029 | 0.0836 |

These values are preliminary results only. They must not be described as the final Python 3.12.2 benchmark. After running all notebook cells with the `Python 3.12 (lab-02)` kernel, replace this table with the newly generated `outputs/t4_benchmark.csv` values and confirm that `outputs/t4_benchmark.png` is the matching chart.

The earlier `tracemalloc` run measured 141,729 bytes (about 138.41 KB) for lazy reading and 144,336 bytes (about 140.95 KB) for eager loading of the 20-line file. These are also preliminary measurements from the earlier run. `tracemalloc` tracks Python memory allocations; it does not represent all process memory, native-library allocations, or operating-system memory.

With U unique IDs, A accounts, window size W, C stored account-category combinations, and O retained output rows, memory is approximately O(U + A × W + C + O). The windows are bounded, but the ID set and retained result rows can grow with the input.

## 4. Limits and copying (T5)

A reference is another name for the same object. A shallow copy creates a new outer dictionary but shares nested objects with the original. A deep copy recursively copies nested objects, so a change to a nested list or dictionary in the deep copy does not change the original.

The first three accepted payments for an account cannot be flagged because there are not yet three prior values. A flagged large payment is still added to the rolling window and can raise the next mean, making later alerts less likely. The monitor processes records in physical arrival order, not sorted event-time order. A late event is therefore compared with the state already built from earlier-arriving records. An event-time design could buffer or reorder records, but it would need an explicit policy for late arrivals.

A rolling median is an alternative baseline that is less affected by one extreme value, although it may react more slowly to genuine behaviour changes and requires additional tracking. Old transaction IDs could be removed after a retention period to limit memory, but an expired duplicate could then be accepted again. Duplicate detection would be guaranteed only within the retention period.

## 5. Run and check (T6)

The required public-test command was run from the project virtual environment:

```text
python -m unittest discover -s tests -p "test_public.py" -v

Ran 6 tests in 0.012s

OK
```

All six public tests passed. The same test suite was also run with pytest and reported six passed tests and five passed subtests.

The notebook contains the T1–T6 tasks and exports the monitor results, benchmark data, memory data, and chart under `outputs/`. The final fresh-kernel execution of the submitted notebook must be confirmed before submission. Select `Python 3.12 (lab-02)`, restart the kernel, run all cells, and confirm that no cell reports an error. Then update the benchmark and memory figures in this section from the regenerated output files.

The currency instructions are inconsistent: the README mentions USD, while the function guide and supplied dataset specify UZS. The implementation and dataset examples were checked against the function guide's UZS requirement. This discrepancy should be clarified with the instructor if the README is intended to take priority.