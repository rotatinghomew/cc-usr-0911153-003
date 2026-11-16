from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable, Mapping

from scene_exchange.intake.demand_contract import (
    ContractError,
    canonical_json,
    stable_hash,
    utc_now,
)
from scene_exchange.pilots.reliability import DEFAULT_POLICY, estimate_supplier


class CapacityConflict(ContractError):
    """Raised when a confirmation would make the current pilot portfolio infeasible."""

    def __init__(self, message: str, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.details = dict(details or {})


def _ensure_columns(connection: sqlite3.Connection, table: str, columns: Mapping[str, str]) -> None:
    existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
    for name, declaration in columns.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")


def prepare_capacity(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS suppliers(
        supplier_id TEXT PRIMARY KEY, active_slots INTEGER NOT NULL CHECK(active_slots > 0),
        registered_at TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS pilot_reservations(
        demand_id TEXT PRIMARY KEY, supplier_id TEXT NOT NULL, status TEXT NOT NULL
        CHECK(status IN ('active','completed','withdrawn')),
        accepted_at TEXT NOT NULL, closed_at TEXT,
        committed_units INTEGER NOT NULL DEFAULT 1,
        match_score REAL, benefit_score REAL, realized_benefit REAL,
        analysis_fingerprint TEXT,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id)
    )""")
    _ensure_columns(connection, "pilot_reservations", {
        "committed_units": "INTEGER NOT NULL DEFAULT 1",
        "match_score": "REAL",
        "benefit_score": "REAL",
        "realized_benefit": "REAL",
        "analysis_fingerprint": "TEXT",
    })
    connection.execute("""CREATE TABLE IF NOT EXISTS commitment_entries(
        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        demand_id TEXT NOT NULL, supplier_id TEXT NOT NULL, action TEXT NOT NULL,
        status TEXT NOT NULL, requested_units INTEGER NOT NULL,
        recommended_units INTEGER, maximum_units INTEGER,
        registered_slots INTEGER, available_before INTEGER, analysis_fingerprint TEXT NOT NULL,
        analysis_json TEXT NOT NULL, variance_json TEXT NOT NULL,
        actor TEXT NOT NULL, reason TEXT, created_at TEXT NOT NULL,
        entry_hash TEXT NOT NULL UNIQUE
    )""")
    _ensure_columns(connection, "commitment_entries", {
        "analysis_fingerprint": "TEXT NOT NULL DEFAULT ''",
    })
    connection.execute("""CREATE TABLE IF NOT EXISTS supplier_revisions(
        revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id TEXT NOT NULL, previous_slots INTEGER NOT NULL,
        new_slots INTEGER NOT NULL, reason TEXT NOT NULL, actor TEXT NOT NULL,
        created_at TEXT NOT NULL, revision_hash TEXT NOT NULL UNIQUE
    )""")


def _supplier_row(connection: sqlite3.Connection, supplier_id: str) -> sqlite3.Row | None:
    return connection.execute("SELECT supplier_id,active_slots,registered_at FROM suppliers WHERE supplier_id=?",
                              (supplier_id,)).fetchone()


def _reservation_rows(connection: sqlite3.Connection, supplier_id: str | None = None) -> list[dict[str, Any]]:
    query = ("SELECT demand_id,supplier_id,status,accepted_at,closed_at,committed_units,"
             "match_score,benefit_score,realized_benefit,analysis_fingerprint "
             "FROM pilot_reservations")
    params: tuple[Any, ...] = ()
    if supplier_id is not None:
        query += " WHERE supplier_id=?"
        params = (supplier_id,)
    query += " ORDER BY demand_id"
    return [dict(row) for row in connection.execute(query, params)]


def _supplier_ids(connection: sqlite3.Connection) -> list[str]:
    return [row[0] for row in connection.execute("SELECT supplier_id FROM suppliers ORDER BY supplier_id")]


def _policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
    settings = dict(DEFAULT_POLICY)
    settings.update(policy or {})
    return settings


def supplier_analysis(connection: sqlite3.Connection, supplier_id: str,
                      policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    prepare_capacity(connection)
    supplier = _supplier_row(connection, supplier_id)
    if supplier is None:
        raise ContractError("unknown supplier")
    rows = _reservation_rows(connection, supplier_id)
    return estimate_supplier(supplier_id, supplier["active_slots"], rows, policy)


def _portfolio(reports: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    reports = list(reports)
    active_by_supplier = {report["supplier_id"]: report["occupancy"]["active_units"] for report in reports}
    total_active = sum(active_by_supplier.values())
    total_recommended = sum(report["commitment_range"]["recommended"] for report in reports)
    total_maximum = sum(report["commitment_range"]["maximum"] for report in reports)
    total_registered = sum(report["registered_slots"] for report in reports)
    overcommitted = [report["supplier_id"] for report in reports
                     if report["occupancy"]["active_units"] > report["commitment_range"]["maximum"]]
    above_recommendation = [report["supplier_id"] for report in reports
                            if report["commitment_range"]["recommended"]
                            < report["occupancy"]["active_units"] <= report["commitment_range"]["maximum"]]
    shares = {supplier_id: (units / total_active if total_active else 0.0)
              for supplier_id, units in active_by_supplier.items()}
    largest = max(shares.items(), key=lambda item: (item[1], item[0])) if shares else ("", 0.0)
    expected = [report["benefit"]["expected_mean"] for report in reports
                if report["benefit"]["expected_observations"]]
    realized = [report["benefit"]["realized_mean"] for report in reports
                if report["benefit"]["observations"]]
    reasons: list[str] = []
    if overcommitted:
        reasons.append("suppliers overcommitted: " + ", ".join(overcommitted))
    if total_active > total_maximum:
        reasons.append("active demand exceeds total supported maximum commitment")
    return {
        "executable": not reasons,
        "reasons": reasons or ["all active pilots fit within supported supplier commitments"],
        "total_registered_slots": total_registered,
        "total_supported_commitment": total_recommended,
        "total_supported_maximum": total_maximum,
        "total_active_units": total_active,
        "overcommitted_suppliers": overcommitted,
        "above_recommendation": above_recommendation,
        "suppliers_without_completed_pilots": [report["supplier_id"] for report in reports
                                               if report["evidence"]["completed"] == 0],
        "immature_active_pilots": sum(report["evidence"]["active"] for report in reports),
        "concentration": {
            "largest_supplier": largest[0],
            "largest_share": largest[1],
            "by_supplier": shares,
        },
        "benefit": {
            "expected_mean": sum(expected) / len(expected) if expected else 0.0,
            "realized_mean": sum(realized) / len(realized) if realized else 0.0,
            "suppliers_with_expected": len(expected),
            "suppliers_with_realized": len(realized),
            "unresolved": len(reports) - len(realized),
        },
    }


def supply_analysis(connection: sqlite3.Connection,
                    policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    prepare_capacity(connection)
    reports = [supplier_analysis(connection, supplier_id, policy)
               for supplier_id in _supplier_ids(connection)]
    return {
        "generated_at": utc_now(),
        "policy": _policy(policy),
        "suppliers": reports,
        "portfolio": _portfolio(reports),
    }


def _variance(connection: sqlite3.Connection, demand_id: str, assessment: Mapping[str, Any],
              *, requested_units: int, resulting_active: int, override: bool) -> dict[str, Any]:
    """Describe the gap between the latest recorded recommendation and this commitment."""
    range_data = assessment.get("commitment_range") or {}
    recommended = range_data.get("recommended", 0)
    previous = connection.execute(
        "SELECT recommended_units,maximum_units,registered_slots,analysis_fingerprint "
        "FROM commitment_entries WHERE demand_id=? AND supplier_id=? "
        "ORDER BY entry_id DESC LIMIT 1",
        (demand_id, assessment.get("supplier_id"))).fetchone()
    changes: list[str] = []
    if previous is not None:
        if previous["recommended_units"] != recommended:
            changes.append(f"recommended commitment moved from {previous['recommended_units']} "
                           f"to {recommended}")
        if previous["maximum_units"] != range_data.get("maximum"):
            changes.append(f"maximum commitment moved from {previous['maximum_units']} "
                           f"to {range_data.get('maximum')}")
        if previous["registered_slots"] != assessment.get("registered_slots"):
            changes.append(f"declared slots moved from {previous['registered_slots']} "
                           f"to {assessment.get('registered_slots')}")
        if previous["analysis_fingerprint"] != assessment.get("fingerprint"):
            changes.append("supporting analysis changed since the last recorded commitment")
    return {
        "analysis_changed": bool(changes),
        "changes": changes,
        "recommended_units": recommended,
        "maximum_units": range_data.get("maximum"),
        "requested_units": requested_units,
        "resulting_active_units": resulting_active,
        "active_minus_recommended": resulting_active - recommended,
        "active_minus_maximum": resulting_active - int(range_data.get("maximum") or 0),
        "override": override,
    }


def _append_entry(connection: sqlite3.Connection, *, demand_id: str, supplier_id: str, action: str,
                  status: str, requested_units: int, assessment: Mapping[str, Any],
                  variance: Mapping[str, Any], actor: str, reason: str | None) -> dict[str, Any]:
    analysis = dict(assessment)
    range_data = analysis.get("commitment_range") or {}
    occupancy = analysis.get("occupancy") or {}
    created_at = utc_now()
    body = {
        "demand_id": demand_id,
        "supplier_id": supplier_id,
        "action": action,
        "status": status,
        "requested_units": requested_units,
        "recommended_units": range_data.get("recommended"),
        "maximum_units": range_data.get("maximum"),
        "registered_slots": analysis.get("registered_slots"),
        "available_before": occupancy.get("available_units"),
        "analysis_fingerprint": analysis.get("fingerprint"),
        "analysis": analysis,
        "variance": dict(variance),
        "actor": actor,
        "reason": reason,
        "created_at": created_at,
    }
    entry_hash = stable_hash(body)
    connection.execute(
        "INSERT INTO commitment_entries(demand_id,supplier_id,action,status,requested_units,"
        "recommended_units,maximum_units,registered_slots,available_before,analysis_fingerprint,"
        "analysis_json,variance_json,actor,reason,created_at,entry_hash) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (demand_id, supplier_id, action, status, requested_units, body["recommended_units"],
         body["maximum_units"], body["registered_slots"], body["available_before"],
         body["analysis_fingerprint"], canonical_json(analysis), canonical_json(body["variance"]),
         actor, reason, created_at, entry_hash))
    return body | {"entry_hash": entry_hash}


def _optional_unit(value: Any) -> float | None:
    if value is None or value == "":
        return None
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ContractError("scores must be between 0 and 1")
    return number


def check_acceptance(connection: sqlite3.Connection, demand_id: str, supplier_id: str,
                     units: int = 1, *, policy: Mapping[str, Any] | None = None,
                     override: bool = False, approver: str | None = None,
                     reason: str | None = None,
                     reviewed_fingerprint: str | None = None) -> dict[str, Any]:
    """Evaluate a proposed confirmation without changing the capacity book."""
    prepare_capacity(connection)
    if not demand_id.strip():
        raise ContractError("pilot demand identifier is required")
    if type(units) is not int or units < 1:
        raise ContractError("pilot commitment must be a positive integer number of units")
    supplier = _supplier_row(connection, supplier_id)
    if supplier is None:
        raise ContractError("unknown supplier")
    assessment = supplier_analysis(connection, supplier_id, policy)
    if reviewed_fingerprint is not None and reviewed_fingerprint != assessment["fingerprint"]:
        raise CapacityConflict(
            "supplier analysis changed since it was reviewed; re-run the analysis before confirming",
            {"supplier_id": supplier_id, "reviewed_fingerprint": reviewed_fingerprint,
             "current_fingerprint": assessment["fingerprint"], "assessment": assessment})
    existing = connection.execute("SELECT supplier_id,status,committed_units FROM pilot_reservations "
                                  "WHERE demand_id=?", (demand_id,)).fetchone()
    if existing and (existing["supplier_id"] != supplier_id or existing["status"] != "active"):
        raise ContractError("closed or reassigned pilots require a new approval")
    range_data = assessment["commitment_range"]
    occupancy = assessment["occupancy"]
    replay = existing is not None
    if replay:
        if existing["committed_units"] != units:
            raise CapacityConflict("existing pilot already occupies a different number of units",
                                   {"existing_units": existing["committed_units"],
                                    "requested_units": units})
        proposed_active = occupancy["active_units"]
    else:
        proposed_active = occupancy["active_units"] + units
    within_recommendation = proposed_active <= range_data["recommended"]
    within_maximum = proposed_active <= range_data["maximum"]
    if not within_maximum:
        raise CapacityConflict(
            "supplier has no remaining pilot slots within its evidence-backed commitment",
            {"supplier_id": supplier_id, "requested_units": units,
             "active_units": occupancy["active_units"],
             "recommended": range_data["recommended"], "maximum": range_data["maximum"],
             "assessment": assessment})
    if not within_recommendation:
        if not override:
            raise CapacityConflict(
                "commitment would exceed the supplier's supported range",
                {"supplier_id": supplier_id, "requested_units": units,
                 "active_units": occupancy["active_units"],
                 "recommended": range_data["recommended"], "maximum": range_data["maximum"],
                 "assessment": assessment})
        if not approver or not reason:
            raise ContractError("an override needs an approver and a reason")
    return {"assessment": assessment, "existing": dict(existing) if existing else None,
            "replay": replay, "proposed_active": proposed_active,
            "within_recommendation": within_recommendation,
            "within_maximum": within_maximum, "override": not within_recommendation}


def accept_pilot(connection: sqlite3.Connection, demand_id: str, supplier_id: str,
                 units: int = 1, *, policy: Mapping[str, Any] | None = None,
                 override: bool = False, approver: str | None = None,
                 reason: str | None = None, actor: str = "operations",
                 match_score: float | None = None, benefit_score: float | None = None,
                 reviewed_fingerprint: str | None = None) -> dict[str, Any]:
    prepare_capacity(connection)
    check = check_acceptance(connection, demand_id, supplier_id, units, policy=policy,
                             override=override, approver=approver, reason=reason,
                             reviewed_fingerprint=reviewed_fingerprint)
    assessment = check["assessment"]
    existing = check["existing"]
    if existing:
        latest = connection.execute(
            "SELECT entry_id,recommended_units,maximum_units,registered_slots "
            "FROM commitment_entries WHERE demand_id=? AND supplier_id=? "
            "ORDER BY entry_id DESC LIMIT 1", (demand_id, supplier_id)).fetchone()
        range_data = assessment["commitment_range"]
        unchanged = latest is not None and (
            latest["recommended_units"], latest["maximum_units"], latest["registered_slots"]
        ) == (range_data["recommended"], range_data["maximum"],
              assessment["registered_slots"])
        if unchanged:
            return {"demand_id": demand_id, "supplier_id": supplier_id, "status": "active",
                    "units": units, "assessment": assessment, "replay": True,
                    "commitment": commitment_entry(connection, latest["entry_id"])}
        variance = _variance(connection, demand_id, assessment,
                             requested_units=units,
                             resulting_active=assessment["occupancy"]["active_units"],
                             override=False)
        entry = _append_entry(connection, demand_id=demand_id, supplier_id=supplier_id,
                              action="replayed", status="active", requested_units=units,
                              assessment=assessment, variance=variance, actor=actor,
                              reason=reason or "existing active pilot")
        return {"demand_id": demand_id, "supplier_id": supplier_id, "status": "active",
                "units": units, "assessment": assessment, "commitment": entry,
                "replay": True}

    # Confirmation must leave the whole portfolio executable.  If a prior
    # recommendation changed, or two pilots now compete for the last unit, the
    # combined state is re-checked before the reservation is written.
    provisional: dict[str, Any] = dict(assessment)
    provisional["occupancy"] = dict(assessment["occupancy"])
    provisional["occupancy"]["active_units"] = check["proposed_active"]
    provisional["occupancy"]["available_units"] = max(
        0, assessment["commitment_range"]["recommended"] - check["proposed_active"])
    reports = []
    for other_id in _supplier_ids(connection):
        reports.append(provisional if other_id == supplier_id
                       else supplier_analysis(connection, other_id, policy))
    portfolio = _portfolio(reports)
    if not portfolio["executable"]:
        raise CapacityConflict("pilot portfolio would no longer be executable",
                               {"proposed_active": check["proposed_active"],
                                "portfolio": portfolio})

    connection.execute(
        "INSERT INTO pilot_reservations(demand_id,supplier_id,status,accepted_at,closed_at,"
        "committed_units,match_score,benefit_score,realized_benefit,analysis_fingerprint) "
        "VALUES(?,?,?,?,NULL,?,?,?,NULL,?)",
        (demand_id, supplier_id, "active", utc_now(), units, _optional_unit(match_score),
         _optional_unit(benefit_score), assessment.get("fingerprint")))
    variance = _variance(connection, demand_id, assessment, requested_units=units,
                         resulting_active=check["proposed_active"],
                         override=check["override"])
    entry = _append_entry(connection, demand_id=demand_id, supplier_id=supplier_id,
                          action="accepted", status="active", requested_units=units,
                          assessment=assessment, variance=variance, actor=actor,
                          reason=reason or ("overridden" if check["override"] else None))
    return {"demand_id": demand_id, "supplier_id": supplier_id, "status": "active",
            "units": units, "assessment": assessment, "commitment": entry,
            "portfolio": portfolio}


def register_supplier(connection: sqlite3.Connection, supplier_id: str, slots: int) -> None:
    prepare_capacity(connection)
    if not supplier_id.strip() or type(slots) is not int or slots < 1:
        raise ContractError("supplier and positive integer capacity are required")
    old = connection.execute("SELECT active_slots FROM suppliers WHERE supplier_id=?", (supplier_id,)).fetchone()
    if old:
        if old[0] != slots:
            raise ContractError("changing a supplier commitment requires a separate review")
        return
    connection.execute("INSERT INTO suppliers VALUES(?,?,?)", (supplier_id, slots, utc_now()))


def revise_supplier_commitment(connection: sqlite3.Connection, supplier_id: str, slots: int,
                               reason: str, actor: str = "operations") -> dict[str, Any]:
    prepare_capacity(connection)
    if not supplier_id.strip() or type(slots) is not int or slots < 1:
        raise ContractError("supplier and positive integer capacity are required")
    if not reason.strip():
        raise ContractError("a commitment revision needs a reason")
    old = _supplier_row(connection, supplier_id)
    if old is None:
        raise ContractError("unknown supplier")
    if old["active_slots"] == slots:
        return {"supplier_id": supplier_id, "slots": slots, "changed": False,
                "analysis": supplier_analysis(connection, supplier_id)}
    active_units = supplier_analysis(connection, supplier_id)["occupancy"]["active_units"]
    if slots < active_units:
        raise CapacityConflict(
            "cannot reduce declared slots below units already committed to active pilots",
            {"supplier_id": supplier_id, "requested_slots": slots,
             "active_units": active_units})
    created_at = utc_now()
    body = {"supplier_id": supplier_id, "previous_slots": old["active_slots"],
            "new_slots": slots, "reason": reason, "actor": actor, "created_at": created_at}
    connection.execute("UPDATE suppliers SET active_slots=? WHERE supplier_id=?", (slots, supplier_id))
    connection.execute("INSERT INTO supplier_revisions(supplier_id,previous_slots,new_slots,reason,actor,"
                       "created_at,revision_hash) VALUES(?,?,?,?,?,?,?)",
                       (supplier_id, old["active_slots"], slots, reason, actor, created_at,
                        stable_hash(body)))
    return {"supplier_id": supplier_id, "slots": slots, "changed": True,
            "previous_slots": old["active_slots"], "analysis": supplier_analysis(connection, supplier_id),
            "revision_hash": stable_hash(body)}


def finish_pilot(connection: sqlite3.Connection, demand_id: str, status: str,
                 realized_benefit: float | None = None, actor: str = "operations",
                 reason: str | None = None) -> dict[str, Any]:
    prepare_capacity(connection)
    if status not in {"completed", "withdrawn"}:
        raise ContractError("pilot outcome must be completed or withdrawn")
    row = connection.execute("SELECT supplier_id,status,committed_units FROM pilot_reservations "
                             "WHERE demand_id=?", (demand_id,)).fetchone()
    if row is None:
        raise ContractError("unknown pilot")
    if row["status"] == status:
        return {"demand_id": demand_id, "supplier_id": row["supplier_id"], "status": status,
                "changed": False}
    if row["status"] != "active":
        raise ContractError("pilot already closed with another outcome")
    realized = _optional_unit(realized_benefit)
    connection.execute("UPDATE pilot_reservations SET status=?,closed_at=?,realized_benefit=? "
                       "WHERE demand_id=?", (status, utc_now(), realized, demand_id))
    # Closing releases the pilot's units for later use.  The closed row keeps its
    # original outcome and committed units, so reuse never rewrites fulfillment
    # statistics for the pilot that has already ended.
    analysis = supplier_analysis(connection, row["supplier_id"])
    variance = {"realized_benefit": realized,
                "benefit_source": "observed" if realized is not None
                else ("withdrawal" if status == "withdrawn" else "unreported")}
    entry = _append_entry(connection, demand_id=demand_id, supplier_id=row["supplier_id"],
                          action=status, status=status, requested_units=row["committed_units"],
                          assessment=analysis, variance=variance, actor=actor, reason=reason)
    return {"demand_id": demand_id, "supplier_id": row["supplier_id"], "status": status,
            "units_released": row["committed_units"], "analysis": analysis,
            "commitment": entry}


def capacity_status(connection: sqlite3.Connection, supplier_id: str) -> dict[str, Any]:
    prepare_capacity(connection)
    supplier = _supplier_row(connection, supplier_id)
    if supplier is None:
        raise ContractError("unknown supplier")
    analysis = supplier_analysis(connection, supplier_id)
    reservations = [dict(entry) for entry in connection.execute(
        "SELECT demand_id,status,accepted_at,closed_at,committed_units,match_score,"
        "benefit_score,realized_benefit "
        "FROM pilot_reservations WHERE supplier_id=? ORDER BY demand_id", (supplier_id,))]
    return {"supplier_id": supplier_id, "slots": supplier["active_slots"],
            "available": analysis["occupancy"]["available_units"],
            "active": sum(item["status"] == "active" for item in reservations),
            "active_units": analysis["occupancy"]["active_units"],
            "supported_commitment": analysis["commitment_range"]["recommended"],
            "maximum_commitment": analysis["commitment_range"]["maximum"],
            "reservations": reservations,
            "analysis": analysis}


def _entry_record(row: Mapping[str, Any]) -> dict[str, Any]:
    record = dict(row)
    record["analysis"] = json.loads(record.pop("analysis_json"))
    record["variance"] = json.loads(record.pop("variance_json"))
    return record


def commitment_entry(connection: sqlite3.Connection, entry_id: int) -> dict[str, Any]:
    prepare_capacity(connection)
    row = connection.execute("SELECT * FROM commitment_entries WHERE entry_id=?",
                             (entry_id,)).fetchone()
    if row is None:
        raise ContractError("unknown commitment entry")
    return _entry_record(row)


def commitment_trail(connection: sqlite3.Connection, demand_id: str | None = None,
                     supplier_id: str | None = None) -> list[dict[str, Any]]:
    prepare_capacity(connection)
    query = "SELECT * FROM commitment_entries"
    clauses: list[str] = []
    params: list[Any] = []
    if demand_id is not None:
        clauses.append("demand_id=?")
        params.append(demand_id)
    if supplier_id is not None:
        clauses.append("supplier_id=?")
        params.append(supplier_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY entry_id"
    return [_entry_record(row) for row in connection.execute(query, tuple(params)).fetchall()]


def supplier_revisions(connection: sqlite3.Connection,
                       supplier_id: str | None = None) -> list[dict[str, Any]]:
    prepare_capacity(connection)
    if supplier_id is None:
        rows = connection.execute("SELECT * FROM supplier_revisions ORDER BY revision_id").fetchall()
    else:
        rows = connection.execute("SELECT * FROM supplier_revisions WHERE supplier_id=? "
                                  "ORDER BY revision_id", (supplier_id,)).fetchall()
    return [dict(row) for row in rows]
