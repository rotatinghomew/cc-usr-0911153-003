from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scene_exchange.coordinator import Application
from scene_exchange.intake.demand_contract import ContractError, DomainRecord
from scene_exchange.pilots.capacity_book import CapacityConflict
from scene_exchange.pilots.reliability import estimate_supplier, wilson_interval


class ReliabilityEstimateTests(unittest.TestCase):
    def rows(self, *statuses):
        return [{"demand_id": f"pilot-{index}", "status": status, "committed_units": 1,
                 "match_score": 0.9, "benefit_score": 0.8, "realized_benefit": 0.7}
                for index, status in enumerate(statuses)]

    def test_wilson_lower_bound_shrinks_with_evidence(self):
        self.assertLess(wilson_interval(1, 1)[0], wilson_interval(10, 10)[0])
        self.assertGreater(wilson_interval(10, 10)[0], 0.8)
        self.assertEqual(wilson_interval(0, 0), (0.0, 1.0))

    def test_no_closed_pilots_caps_commitment(self):
        report = estimate_supplier("s", 8, self.rows("active"))
        self.assertEqual(report["commitment_range"]["recommended"], 1)
        self.assertEqual(report["commitment_range"]["maximum"], 1)
        self.assertFalse(report["evidence"]["mature"])
        self.assertEqual(report["occupancy"]["active_units"], 1)

    def test_high_expected_benefit_does_not_raise_evidence_poor_capacity(self):
        rows = [{"demand_id": "pilot-1", "status": "completed", "committed_units": 1,
                 "match_score": 0.99, "benefit_score": 0.99, "realized_benefit": 0.99}]
        report = estimate_supplier("s", 10, rows)
        self.assertEqual(report["commitment_range"]["recommended"], 1)
        self.assertEqual(report["commitment_range"]["maximum"], 1)
        self.assertAlmostEqual(report["benefit"]["realized_mean"], 0.99)
        self.assertAlmostEqual(report["benefit"]["expected_mean"], 0.99)
        self.assertTrue(any("probation" in note for note in report["notes"]))

    def test_mature_supplier_earns_headroom_but_withdrawals_reduce_it(self):
        clean = estimate_supplier("s", 6, self.rows("completed", "completed", "completed"))
        self.assertLess(clean["commitment_range"]["maximum"], 6)
        self.assertGreaterEqual(clean["commitment_range"]["recommended"], 2)
        mixed = estimate_supplier("s", 6, self.rows("completed", "completed", "withdrawn"))
        self.assertLessEqual(mixed["commitment_range"]["recommended"],
                             clean["commitment_range"]["recommended"])
        self.assertLess(mixed["commitment_range"]["maximum"], 6)

    def test_withdrawals_count_as_zero_realized_benefit(self):
        report = estimate_supplier("s", 4, self.rows("completed", "completed", "withdrawn"))
        self.assertEqual(report["benefit"]["imputed_zeros"], 1)
        self.assertLess(report["benefit"]["realized_mean"], report["benefit"]["expected_mean"])
        self.assertLess(report["benefit"]["upper"] - report["benefit"]["lower"], 1.0)

    def test_unreported_completions_are_excluded_but_disclosed(self):
        rows = self.rows("completed")
        rows[0]["realized_benefit"] = None
        report = estimate_supplier("s", 3, rows)
        self.assertEqual(report["benefit"]["unreported_completions"], 1)
        self.assertEqual(report["benefit"]["observations"], 0)
        self.assertTrue(any("no reported realized benefit" in note for note in report["notes"]))


class PilotCommitmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "pilot.sqlite3"
        self.application = Application(self.database)
        for index in range(1, 25):
            self.application.repository.save_record(
                DomainRecord(f"pilot-{index}", {"sector": "manufacturing"}))

    def complete(self, demand_id, supplier_id, benefit=0.7):
        self.application.accept_pilot(demand_id, supplier_id, match_score=0.9, benefit_score=0.8)
        self.application.finish_pilot(demand_id, "completed", realized_benefit=benefit)

    def test_confirmation_occupies_capacity_and_blocks_competition(self):
        self.application.register_supplier("supplier-a", 3)
        self.assertEqual(self.application.accept_pilot("pilot-1", "supplier-a")["units"], 1)
        with self.assertRaisesRegex(ContractError, "no remaining"):
            self.application.accept_pilot("pilot-2", "supplier-a")
        status = self.application.capacity_status("supplier-a")
        self.assertEqual(status["active_units"], 1)
        self.assertEqual(status["available"], 0)
        self.assertEqual([item["status"] for item in status["reservations"]], ["active"])

    def test_gaining_evidence_raises_supported_commitment_and_permits_more_pilots(self):
        self.application.register_supplier("supplier-a", 4)
        for index in range(1, 4):
            self.complete(f"pilot-{index}", "supplier-a")
        report = self.application.supplier_analysis("supplier-a")
        self.assertGreaterEqual(report["commitment_range"]["recommended"], 2)
        for index in range(4, 6):
            self.application.accept_pilot(f"pilot-{index}", "supplier-a")
        self.assertEqual(self.application.capacity_status("supplier-a")["active_units"], 2)

    def test_override_requires_approval_and_records_variance(self):
        self.application.register_supplier("supplier-a", 4)
        for index in range(1, 4):
            self.complete(f"pilot-{index}", "supplier-a")
        range_data = self.application.supplier_analysis("supplier-a")["commitment_range"]
        recommended, maximum = range_data["recommended"], range_data["maximum"]
        self.assertLess(recommended, maximum)
        for index in range(4, 4 + recommended):
            self.application.accept_pilot(f"pilot-{index}", "supplier-a")
        with self.assertRaises(CapacityConflict):
            self.application.accept_pilot("pilot-20", "supplier-a")
        with self.assertRaisesRegex(ContractError, "approver and a reason"):
            self.application.accept_pilot("pilot-20", "supplier-a", override=True,
                                          approver="ops-lead")
        result = self.application.accept_pilot("pilot-20", "supplier-a", override=True,
                                               approver="ops-lead", reason="time-boxed expansion")
        variance = result["commitment"]["variance"]
        self.assertGreater(variance["active_minus_recommended"], 0)
        self.assertEqual(variance["maximum_units"], maximum)
        self.assertTrue(self.application.commitment_trail(demand_id="pilot-20")[-1]["reason"])

    def test_override_cannot_exceed_supported_maximum(self):
        self.application.register_supplier("supplier-a", 4)
        for index in range(1, 4):
            self.complete(f"pilot-{index}", "supplier-a")
        maximum = self.application.supplier_analysis("supplier-a")["commitment_range"]["maximum"]
        for index in range(4, 4 + maximum):
            self.application.accept_pilot(f"pilot-{index}", "supplier-a",
                                          override=True, approver="ops-lead",
                                          reason="capacity expansion")
        with self.assertRaisesRegex(ContractError, "no remaining"):
            self.application.accept_pilot("pilot-20", "supplier-a", override=True,
                                          approver="ops-lead", reason="capacity expansion")

    def test_closing_releases_capacity_without_rewriting_history(self):
        self.application.register_supplier("supplier-a", 1)
        self.complete("pilot-1", "supplier-a", benefit=0.82)
        self.application.accept_pilot("pilot-2", "supplier-a")
        self.application.finish_pilot("pilot-2", "withdrawn")
        reservations = {item["demand_id"]: item for item in
                        self.application.capacity_status("supplier-a")["reservations"]}
        self.assertEqual(reservations["pilot-1"]["status"], "completed")
        self.assertEqual(reservations["pilot-1"]["realized_benefit"], 0.82)
        self.assertEqual(reservations["pilot-2"]["status"], "withdrawn")
        self.assertEqual(self.application.capacity_status("supplier-a")["active_units"], 0)
        self.application.accept_pilot("pilot-3", "supplier-a")
        self.assertEqual(self.application.capacity_status("supplier-a")["active_units"], 1)

    def test_stale_analysis_must_be_rechecked_before_confirmation(self):
        self.application.register_supplier("supplier-a", 2)
        reviewed = self.application.supplier_analysis("supplier-a")["fingerprint"]
        self.application.accept_pilot("pilot-1", "supplier-a")
        with self.assertRaisesRegex(ContractError, "analysis changed"):
            self.application.accept_pilot("pilot-2", "supplier-a",
                                          reviewed_fingerprint=reviewed)

    def test_check_acceptance_is_read_only(self):
        self.application.register_supplier("supplier-a", 2)
        preview = self.application.check_acceptance("pilot-1", "supplier-a")
        self.assertTrue(preview["within_recommendation"])
        self.assertEqual(preview["proposed_active"], 1)
        self.assertEqual(self.application.capacity_status("supplier-a")["active_units"], 0)
        self.assertEqual(self.application.commitment_trail(), [])

    def test_repeated_confirmation_does_not_inflate_the_trail(self):
        self.application.register_supplier("supplier-a", 2)
        first = self.application.accept_pilot("pilot-1", "supplier-a")
        second = self.application.accept_pilot("pilot-1", "supplier-a")
        self.assertTrue(second["replay"])
        self.assertEqual(first["commitment"]["entry_hash"], second["commitment"]["entry_hash"])
        self.assertEqual(len(self.application.commitment_trail(demand_id="pilot-1")), 1)

    def test_commitment_trail_links_recommendation_to_actual(self):
        self.application.register_supplier("supplier-a", 2)
        result = self.application.accept_pilot("pilot-1", "supplier-a")
        trail = self.application.commitment_trail(demand_id="pilot-1")
        self.assertEqual(len(trail), 1)
        entry = trail[0]
        self.assertEqual(entry["recommended_units"], result["assessment"]["commitment_range"]["recommended"])
        self.assertEqual(entry["requested_units"], 1)
        self.assertEqual(entry["status"], "active")
        self.assertIn("analysis_fingerprint", entry)
        self.assertEqual(entry["analysis_fingerprint"], result["assessment"]["fingerprint"])

    def test_revised_declared_slots_are_audited(self):
        self.application.register_supplier("supplier-a", 1)
        revised = self.application.revise_supplier_commitment("supplier-a", 3, "signed capacity addendum")
        self.assertTrue(revised["changed"])
        revisions = self.application.supplier_revisions("supplier-a")
        self.assertEqual(revisions[0]["previous_slots"], 1)
        self.assertEqual(revisions[0]["new_slots"], 3)
        with self.assertRaisesRegex(ContractError, "reason"):
            self.application.revise_supplier_commitment("supplier-a", 4, " ")

    def test_declared_slots_cannot_drop_below_active_units(self):
        self.application.register_supplier("supplier-a", 3)
        for index in range(1, 4):
            self.complete(f"pilot-{index}", "supplier-a")
        for index in (4, 5):
            self.application.accept_pilot(f"pilot-{index}", "supplier-a",
                                          override=True, approver="ops-lead",
                                          reason="documented expansion")
        self.assertEqual(self.application.capacity_status("supplier-a")["active_units"], 2)
        with self.assertRaisesRegex(CapacityConflict, "already committed"):
            self.application.revise_supplier_commitment("supplier-a", 1, "shrink")

    def test_two_pilots_competing_for_the_last_slot(self):
        self.application.register_supplier("supplier-a", 4)
        for index in range(1, 4):
            self.complete(f"pilot-{index}", "supplier-a")
        maximum = self.application.supplier_analysis("supplier-a")["commitment_range"]["maximum"]
        for index in range(4, 3 + maximum):
            self.application.accept_pilot(f"pilot-{index}", "supplier-a",
                                          override=True, approver="ops-lead",
                                          reason="fills supported maximum")
        winner = self.application.accept_pilot("pilot-24", "supplier-a", override=True,
                                               approver="ops-lead", reason="last supported slot")
        self.assertEqual(winner["portfolio"]["total_active_units"], maximum)
        with self.assertRaisesRegex(ContractError, "no remaining"):
            self.application.accept_pilot("pilot-23", "supplier-a")

    def test_portfolio_is_rejudged_when_a_supplier_falls_below_occupancy(self):
        self.application.register_supplier("supplier-a", 2)
        self.application.register_supplier("supplier-b", 2)
        self.application.accept_pilot("pilot-1", "supplier-a")
        import sqlite3
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE suppliers SET active_slots=1 WHERE supplier_id='supplier-a'")
            connection.execute(
                "INSERT INTO pilot_reservations(demand_id,supplier_id,status,accepted_at,"
                "committed_units) VALUES('pilot-2','supplier-a','active','2026-01-01',1)")
        analysis = self.application.supply_analysis()
        self.assertFalse(analysis["portfolio"]["executable"])
        self.assertEqual(analysis["portfolio"]["overcommitted_suppliers"], ["supplier-a"])
        with self.assertRaisesRegex(ContractError, "no longer be executable"):
            self.application.accept_pilot("pilot-3", "supplier-b")

    def test_supply_analysis_reports_concentration_and_immaturity(self):
        self.application.register_supplier("supplier-a", 3)
        self.application.register_supplier("supplier-b", 3)
        self.complete("pilot-1", "supplier-a")
        self.application.accept_pilot("pilot-2", "supplier-a")
        analysis = self.application.supply_analysis()
        portfolio = analysis["portfolio"]
        self.assertTrue(portfolio["executable"])
        self.assertEqual(portfolio["immature_active_pilots"], 1)
        self.assertIn("supplier-b", portfolio["suppliers_without_completed_pilots"])
        self.assertEqual(portfolio["benefit"]["unresolved"], 1)
        self.assertGreater(portfolio["concentration"]["largest_share"], 0.0)


if __name__ == "__main__":
    unittest.main()
