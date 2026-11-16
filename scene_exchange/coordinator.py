from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from scene_exchange.intake.demand_contract import ContractError, Decision, DomainRecord, records_from_fixture, stable_hash
from scene_exchange.registry.exchange_db import Repository
from scene_exchange.pilots.governance import advance_for_outcome, decide
from scene_exchange.briefing.decision_pack import export_bundle, verify_bundle
from scene_exchange.matching.bipartite import derive_context


class Application:
    def __init__(self, database: str | Path, context: Mapping[str, Any] | None = None):
        self.repository = Repository(database)
        self.context = dict(context or {})

    def ingest(self, record: DomainRecord) -> DomainRecord:
        current = self.repository.get_record(record.record_id)
        if current is None:
            self.repository.save_record(record)
            return record
        if current.fingerprint == record.fingerprint:
            return current
        replacement = DomainRecord(record.record_id, record.payload, current.state,
                                   current.version + 1, record.occurred_at, record.source)
        self.repository.save_record(replacement, expected_version=current.version)
        return replacement

    def process(self, record: DomainRecord) -> tuple[DomainRecord, Decision]:
        stored = self.ingest(record)
        context = dict(self.context)
        context.update(derive_context(stored, self.repository))
        decision = decide(stored, context)
        self.repository.save_decision(decision)
        advanced = advance_for_outcome(stored, decision)
        if advanced.fingerprint != stored.fingerprint:
            self.repository.save_record(advanced, expected_version=stored.version)
        return advanced, decision

    def run_fixture(self, fixture: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
        records = records_from_fixture(fixture)
        fixture_hash = stable_hash(fixture)
        run_id = self.repository.begin_run(fixture_hash, len(records))
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            return completed
        decisions: dict[str, Decision] = {}
        final_records: list[DomainRecord] = []
        for record in records:
            final_record, decision = self.process(record)
            final_records.append(final_record)
            decisions[record.record_id] = decision
        snapshot = self.repository.snapshot()
        if snapshot["chain_errors"]:
            raise ContractError("audit chain verification failed")
        manifest = export_bundle(output, final_records, decisions, snapshot, self.repository.event_rows())
        result = {"run_id": run_id, "fixture_hash": fixture_hash, "records": len(final_records),
                  "decisions": len(decisions), "manifest": manifest, "snapshot": snapshot}
        self.repository.finish_run(run_id, result)
        return result

    def inspect(self) -> dict[str, Any]:
        return {"snapshot": self.repository.snapshot(), "records": [record.__dict__ for record in self.repository.list_records()],
                "decisions": self.repository.decision_rows()}

    def register_supplier(self, supplier_id: str, slots: int) -> None:
        self.repository.register_supplier(supplier_id, slots)

    def revise_supplier_commitment(self, supplier_id: str, slots: int, reason: str,
                                   actor: str = "operations") -> dict[str, Any]:
        return self.repository.revise_supplier_commitment(supplier_id, slots, reason, actor)

    def accept_pilot(self, demand_id: str, supplier_id: str, units: int = 1,
                     **options: Any) -> dict[str, Any]:
        return self.repository.accept_pilot(demand_id, supplier_id, units, **options)

    def check_acceptance(self, demand_id: str, supplier_id: str, units: int = 1,
                         **options: Any) -> dict[str, Any]:
        return self.repository.check_acceptance(demand_id, supplier_id, units, **options)

    def finish_pilot(self, demand_id: str, status: str, realized_benefit: float | None = None,
                     actor: str = "operations", reason: str | None = None) -> dict[str, Any]:
        return self.repository.finish_pilot(demand_id, status, realized_benefit, actor, reason)

    def capacity_status(self, supplier_id: str) -> dict[str, Any]:
        return self.repository.capacity_status(supplier_id)

    def supplier_analysis(self, supplier_id: str) -> dict[str, Any]:
        return self.repository.supplier_analysis(supplier_id)

    def supply_analysis(self) -> dict[str, Any]:
        return self.repository.supply_analysis()

    def commitment_trail(self, demand_id: str | None = None,
                         supplier_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.commitment_trail(demand_id, supplier_id)

    def supplier_revisions(self, supplier_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.supplier_revisions(supplier_id)


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read fixture: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value


def run(fixture_path: str | Path, database: str | Path, output: str | Path,
        context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return Application(database, context).run_fixture(load_fixture(fixture_path), output)


def verify(database: str | Path, output: str | Path) -> dict[str, Any]:
    repository = Repository(database)
    chain_errors = repository.verify_chain()
    bundle_errors = verify_bundle(output)
    return {"ok": not chain_errors and not bundle_errors, "chain_errors": chain_errors,
            "bundle_errors": bundle_errors, "snapshot": repository.snapshot()}
