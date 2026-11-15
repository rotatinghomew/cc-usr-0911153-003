from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from scene_exchange.intake.demand_contract import DomainRecord, bounded, finite_number, normalized_text


@dataclass(frozen=True)
class MatchEdge:
    demand_id: str
    supplier_id: str
    fit: float
    conflicts: tuple[str, ...]
    evidence: tuple[str, ...]


def demand_vector(record: DomainRecord) -> dict[str, float]:
    payload = record.payload
    return {"severity": bounded(finite_number(payload.get("problem_severity", 0.0)) / 10.0),
            "readiness": bounded(finite_number(payload.get("data_readiness", 0.0))),
            "budget": bounded(finite_number(payload.get("budget_band", 0.0)) / 10.0),
            "safety": bounded(1.0 - finite_number(payload.get("safety_class", 0.0)) / 10.0),
            "localization": bounded(finite_number(payload.get("localization_need", 0.0))),
            "integration": bounded(1.0 - finite_number(payload.get("integration_count", 0.0)) / 20.0)}


def supplier_vector(record: DomainRecord) -> dict[str, float]:
    payload = record.payload
    return {"capacity": bounded(finite_number(payload.get("supplier_capacity", 0.0))),
            "evidence": bounded(finite_number(payload.get("evidence_strength", 0.0))),
            "conflict": bounded(1.0 - finite_number(payload.get("conflict_count", 0.0)) / 10.0),
            "benefit": bounded(finite_number(payload.get("expected_benefit", 0.0))),
            "window": bounded(1.0 - finite_number(payload.get("deployment_window", 0.0)) / 365.0)}


def match(record: DomainRecord, supplier_id: str, supplier: Mapping[str, float]) -> MatchEdge:
    demand = demand_vector(record)
    conflicts = []
    if supplier.get("capacity", 0.0) < demand["severity"] * 0.7:
        conflicts.append("capacity-below-severity")
    if supplier.get("localization", 0.0) < demand["localization"]:
        conflicts.append("localization-gap")
    if supplier.get("safety", 0.0) < 1.0 - demand["safety"]:
        conflicts.append("safety-disclosure-gap")
    components = [supplier.get("capacity", 0.0), supplier.get("evidence", 0.0),
                  supplier.get("localization", 0.0), supplier.get("integration", 0.0), demand["readiness"]]
    fit = bounded(sum(components) / len(components) - len(conflicts) * 0.12)
    evidence = tuple(key for key, value in supplier.items() if value >= 0.5)
    return MatchEdge(record.record_id, normalized_text(supplier_id), fit, tuple(conflicts), evidence)


def shortlist(record: DomainRecord, suppliers: Mapping[str, Mapping[str, float]], limit: int = 3) -> list[MatchEdge]:
    edges = [match(record, supplier_id, values) for supplier_id, values in suppliers.items()]
    return sorted(edges, key=lambda edge: (-edge.fit, len(edge.conflicts), edge.supplier_id))[:max(1, limit)]


def portfolio_pressure(records: Iterable[DomainRecord]) -> dict[str, float]:
    rows = list(records)
    sectors = {normalized_text(row.payload.get("sector", "unknown")) for row in rows}
    suppliers = [bounded(finite_number(row.payload.get("supplier_capacity", 0.0))) for row in rows]
    conflicts = [finite_number(row.payload.get("conflict_count", 0.0)) for row in rows]
    return {"sector_diversity": bounded(len(sectors) / 8.0),
            "capacity_mean": sum(suppliers) / max(1, len(suppliers)),
            "conflict_pressure": bounded(sum(conflicts) / max(1, len(rows) * 5.0))}


def derive_context(record: DomainRecord, repository: Any) -> dict[str, float]:
    supplier = supplier_vector(record)
    supplier_profile = supplier | {"localization": 0.75, "integration": 0.70, "safety": 0.80}
    edge = match(record, "self-declared", supplier_profile)
    pressure = portfolio_pressure(repository.list_records() or [record])
    return {"match_fit_weight": 0.6 + edge.fit * 0.6, "disclosure_quality_weight": 0.6 + supplier["evidence"] * 0.5,
            "pilot_feasibility_weight": 0.7 + supplier["capacity"] * 0.4,
            "supplier_concentration_weight": 1.1 - pressure["sector_diversity"] * 0.3,
            "exit_risk_weight": 0.7 + pressure["conflict_pressure"] * 0.7}
