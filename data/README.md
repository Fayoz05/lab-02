# Where the data comes from

`transactions.jsonl` is used for this lab. It has no real customer data. It has 20 physical lines, including deliberately invalid lines. Read them in file order.

Examples include mixed accounts, exact cents, repeated IDs, a valid retry after an invalid record, out-of-order event times, and a value exactly at the warning threshold. The small file can be checked by hand.

For large experiments, make other synthetic records in memory or a temporary file. Do not overwrite this supplied file.
