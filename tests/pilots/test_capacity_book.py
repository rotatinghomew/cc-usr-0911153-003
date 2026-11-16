from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scene_exchange.coordinator import Application
from scene_exchange.intake.demand_contract import ContractError, DomainRecord


class CapacityBookTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "pilot.sqlite3"
        self.application = Application(self.database)
        for demand_id in ("pilot-1", "pilot-2"):
            self.application.repository.save_record(DomainRecord(demand_id, {"sector": "manufacturing"}))
        self.application.register_supplier("supplier-a", 1)

    def test_capacity_is_exclusive_and_release_retains_history(self):
        self.assertEqual(self.application.accept_pilot("pilot-1", "supplier-a")["status"], "active")
        self.assertEqual(self.application.accept_pilot("pilot-1", "supplier-a")["status"], "active")
        with self.assertRaisesRegex(ContractError, "no remaining"):
            Application(self.database).accept_pilot("pilot-2", "supplier-a")
        self.application.finish_pilot("pilot-1", "completed")
        self.assertEqual(self.application.capacity_status("supplier-a")["available"], 1)
        self.application.accept_pilot("pilot-2", "supplier-a")
        reopened = Application(self.database).capacity_status("supplier-a")
        self.assertEqual(reopened["available"], 0)
        self.assertEqual([item["status"] for item in reopened["reservations"]], ["completed", "active"])

    def test_supplier_scope_and_unknown_demand_are_guarded(self):
        with self.assertRaisesRegex(ContractError, "not registered"):
            self.application.accept_pilot("missing", "supplier-a")
        with self.assertRaisesRegex(ContractError, "separate review"):
            self.application.register_supplier("supplier-a", 2)
