import copy
import json
import unittest
from dataclasses import FrozenInstanceError
from datetime import timezone
from decimal import Decimal
from pathlib import Path
from src import solution as s

def event(t="T1", account="A1", amount="10.00", category="food", **kw):
    d=dict(tx_id=t,account=account,category=category,amount=amount,occurred_at="2026-09-01T15:00:00+05:00",currency="USD")
    d.update(kw)
    return d

def stream(rows):
    return (json.dumps(row) for row in rows)

class PublicTests(unittest.TestCase):
    def test_parse_normalization_and_immutability(self):
        raw=event(tx_id=" T1 ",currency=" usd ")
        before=copy.deepcopy(raw)
        tx=s.parse_event(raw)
        self.assertEqual(tx.tx_id,"T1")
        self.assertEqual(tx.amount,Decimal("10.00"))
        self.assertEqual(tx.occurred_at.hour,10)
        self.assertEqual(tx.occurred_at.utcoffset(),timezone.utc.utcoffset(tx.occurred_at))
        self.assertEqual(raw,before)
        with self.assertRaises(FrozenInstanceError): tx.amount=Decimal("1")
    def test_invalid_values(self):
        for patch in [dict(amount=True),dict(amount="NaN"),dict(amount="-1"),dict(currency="EUR"),dict(occurred_at="2026-09-01T10:00:00")]:
            with self.subTest(patch=patch), self.assertRaises(ValueError): s.parse_event(event(**patch))
    def test_rolling_eviction_exact(self):
        w=s.RollingWindow(3)
        self.assertIsNone(w.mean)
        for amount in ["0.10","0.20","0.30","0.40"]: w.push(Decimal(amount))
        self.assertEqual(w.values,(Decimal(".20"),Decimal(".30"),Decimal(".40")))
        self.assertEqual(w.total,Decimal(".90"))
        self.assertEqual(w.mean,Decimal(".30"))
    def test_prior_window_threshold_and_dedup(self):
        rows=[event("T1",amount="10"),event("T2",amount="11"),event("T3",amount="12"),event("T4",amount="22"),event("T4",amount="99")]
        out=s.monitor(stream(rows))
        self.assertEqual(out['metrics'],dict(received=5,accepted=4,duplicates=1,rejected=0))
        self.assertEqual(out['anomalies']['tx_id'].tolist(),['T4'])
        self.assertEqual(out['anomalies'].iloc[0]['prior_mean'],Decimal('11'))
        self.assertEqual(out['summary'].iloc[0]['total'],Decimal('55'))
    def test_validation_before_dedup(self):
        out=s.monitor(stream([event('X',amount='0'),event('X',amount='5'),event('X',amount='-1')]))
        self.assertEqual(out['metrics'],dict(received=3,accepted=1,duplicates=0,rejected=2))
    def test_fixture_input_is_single_pass(self):
        path=Path(__file__).resolve().parents[1]/'data'/'transactions.jsonl'
        lines=s.iter_jsonl(path)
        self.assertIs(iter(lines),lines)
        self.assertTrue(next(lines).startswith('{'))
        self.assertEqual(len(list(lines)),19)
        self.assertEqual(list(lines),[])

if __name__=='__main__': unittest.main()
