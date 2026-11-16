from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scene_exchange.commands import main
from scene_exchange.coordinator import Application
from scene_exchange.intake.demand_contract import DomainRecord


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = str(Path(temporary.name) / "cli.sqlite3")
        application = Application(self.database)
        for index in range(1, 5):
            application.repository.save_record(DomainRecord(f"pilot-{index}", {"sector": "health"}))
        application.register_supplier("supplier-a", 2)

    def invoke(self, *argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, json.loads(buffer.getvalue())

    def test_supply_and_commitment_commands_round_trip(self):
        code, supply = self.invoke("supply", "--database", self.database, "--supplier", "supplier-a")
        self.assertEqual(code, 0)
        self.assertEqual(supply["commitment_range"]["maximum"], 1)

        code, accepted = self.invoke(
            "pilot-accept", "--database", self.database, "--demand", "pilot-1",
            "--supplier", "supplier-a", "--match-score", "0.9", "--benefit-score", "0.8")
        self.assertEqual(code, 0)
        self.assertEqual(accepted["status"], "active")

        code, rejected = self.invoke(
            "pilot-accept", "--database", self.database, "--demand", "pilot-2",
            "--supplier", "supplier-a")
        self.assertEqual(code, 1)
        self.assertFalse(rejected["ok"])
        self.assertIn("no remaining", rejected["error"])

        code, finished = self.invoke(
            "pilot-finish", "--database", self.database, "--demand", "pilot-1",
            "--status", "completed", "--realized-benefit", "0.62")
        self.assertEqual(code, 0)
        self.assertEqual(finished["units_released"], 1)

        code, trail = self.invoke("commitment-trail", "--database", self.database,
                                  "--demand", "pilot-1")
        self.assertEqual(code, 0)
        self.assertEqual([entry["action"] for entry in trail], ["accepted", "completed"])
        self.assertEqual(trail[0]["requested_units"], 1)


if __name__ == "__main__":
    unittest.main()
