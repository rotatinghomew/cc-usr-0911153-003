from __future__ import annotations

import unittest
from scene_exchange.intake.demand_contract import DomainRecord
from scene_exchange.matching.bipartite import match, portfolio_pressure, shortlist


class MatchingTests(unittest.TestCase):
    def record(self, key):
        return DomainRecord(key, {"sector": "manufacturing", "problem_severity": 8, "data_readiness": 0.8,
            "deployment_window": 90, "budget_band": 7, "safety_class": 2, "localization_need": 0.6,
            "integration_count": 4, "supplier_capacity": 0.7, "evidence_strength": 0.8,
            "conflict_count": 1, "expected_benefit": 0.9})

    def test_shortlist_prefers_compatible_supplier(self):
        record = self.record("d1")
        suppliers = {"good": {"capacity": .9, "evidence": .9, "localization": .8, "integration": .8, "safety": .9},
                     "weak": {"capacity": .2, "evidence": .3, "localization": .1, "integration": .2, "safety": .1}}
        self.assertEqual(shortlist(record, suppliers, 1)[0].supplier_id, "good")
        self.assertGreater(match(record, "good", suppliers["good"]).fit, match(record, "weak", suppliers["weak"]).fit)

    def test_portfolio_pressure_tracks_diversity(self):
        self.assertGreater(portfolio_pressure([self.record("a"), self.record("b")])["capacity_mean"], 0.0)
