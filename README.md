# Lab 02

**Course:** Data Exploration and Extraction, MSc Data Science  
**Marks:** 100 %  
**Python:** 3.12.2

## Your goal

Read payment records one line at a time. Check each record. For each account, compare a new payment with recent valid payments. Mark payments that meet the large-payment rule. This is a warning rule, not proof of fraud.

Use short sentences, tables, and examples in your report. You do not need complex English.

## Before you start

Read [FUNCTION_GUIDE.md](FUNCTION_GUIDE.md) for exact rules. Write functions in `src/solution.py`. Show results in `notebooks/lab.ipynb`. Copy `REPORT_TEMPLATE.md` to `REPORT.md`.

Use `data/transactions.jsonl`. JSONL means one JSON value on each line. These records are made up for teaching. Some lines have errors on purpose. **Do not edit the file or sort it by time. Read lines in file order.**

## Words you need

| Word | Meaning here |
|---|---|
| Stream | Data read one item at a time |
| Valid | Meets all required rules |
| Duplicate | Another valid event with an ID already accepted |
| Window | The last few accepted amounts for one account |
| Prior window | The window before adding the new payment |
| Anomaly | A payment that meets the warning rule |
| Lazy input | Read the next line only when needed |
| Benchmark | An experiment that measures time or memory |

## T1 — Make and check transaction records

1. Complete the frozen `Transaction` dataclass. Frozen means its fields cannot be changed after creation.
2. Implement `parse_event(raw)`. Check the six keys and their values.
3. Strip spaces around IDs and categories. Keep their letter case. Make currency uppercase and accept only USD.
4. Use `Decimal` for amounts. Convert times with a timezone to UTC.
5. Test invalid values: `True`, infinity, a wrong currency, and a time without a timezone.

**Example:** amount `'12.50'` is valid; `'12.501'` is invalid because it has a fraction of one cent. Currency `' usd '` becomes `'USD'`.

**Show:** a valid parsed record and at least four invalid-input checks.

## T2 — Read lines and handle repeated IDs

1. Implement `iter_jsonl(path)` as a lazy iterator. Do not load the whole file.
2. In `monitor`, count every physical line, including empty lines.
3. Read JSON, then validate the event, then check its ID.
4. Accept the first valid event for each ID. Ignore later valid events with the same ID.
5. Put invalid lines in the error table. A rejected event must not reserve its ID.

**Example:** the first `T1` row has amount `-5` and is rejected. A later `T1` row has amount `5` and can be accepted. The rejected row did not reserve `T1`.

**Show:** received, accepted, duplicate, and rejected counts. Check `received = accepted + duplicates + rejected`.

## T3 — Keep recent amounts and find anomalies

1. Complete `RollingWindow` and `monitor`. Keep a separate window for each account. The default size is three accepted amounts.
2. Keep a running sum: subtract the value leaving the window and add the new value. Do not run `sum(window)` for each payment.
3. **Before** adding an amount, check the account's prior window.
4. If it has at least three amounts, flag when `amount >= 2 * prior_mean`.
5. Add flagged accepted amounts to the window and totals too. Bad records and duplicates do not enter them.
6. Return the four outputs in the function guide, including correct empty tables.

**Example:** prior values are `[10, 11, 12]`. The mean is `11`. A new `22` is flagged because `22 >= 2 * 11`. The new window is `[11, 12, 22]`.

**Show:** summaries, anomalies, errors, and an example exactly at the threshold.

## T4 — Measure time and memory

1. Compare list and set membership, such as `target in values`.
2. Use at least three sizes. Example: 100, 1,000, and 10,000.
3. Repeat each experiment at least five times. Report the median time.
4. State whether timing includes making the collection or only querying it. Use a practical number of queries so the experiment finishes locally.
5. Use `tracemalloc` to compare lazy input with loading all input first. Explain that it tracks Python allocations, not all computer memory.
6. Record Python version and platform. Save a table and one labeled chart.

**Show:** sizes, repeat count, median times, memory results, and your explanation. There is no required speed ratio.

## T5 — Explain choices and limits

1. Show a reference, shallow copy, and deep copy of a nested record.
2. Explain why the first few payments cannot be flagged by this rule.
3. Explain how a flagged large payment can raise the next window mean.
4. Explain arrival order versus event-time order. Suggest one other baseline and its limit.
5. Discuss memory using U = unique valid IDs, A = accounts, W = window size, C = stored categories, O = retained output rows.
6. Explain which parts grow with more input. Small windows do not make the whole program use fixed memory. The seen-ID set and outputs can grow.
7. Suggest a rule for deleting old state. Explain which guarantee changes.

**Example:** deleting old IDs saves memory, but an old repeated ID may then be accepted again.

## T6 — Finish and explain your work

Write **800–1,100 words**, excluding tables and code. Save summaries, anomalies, rejected lines, and metrics under `outputs/`. Write Decimal values as strings in JSON. Include the benchmark table and chart, and your extra tests.

Run the notebook from a fresh kernel. Be ready to explain a case selected by the teacher.

Use [SUBMISSION.md](SUBMISSION.md) for setup and submission. Read [RUBRIC.md](RUBRIC.md) for marks and [LECTURE_MAP.md](LECTURE_MAP.md) for lecture sources. Public tests fail until you complete the missing functions. This is expected.

Need help with a word? Read [GLOSSARY.md](GLOSSARY.md).
