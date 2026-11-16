from __future__ import annotations

import sqlite3
from typing import Any

from scene_exchange.intake.demand_contract import ContractError, utc_now


def prepare_capacity(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS suppliers(
        supplier_id TEXT PRIMARY KEY, active_slots INTEGER NOT NULL CHECK(active_slots > 0),
        registered_at TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS pilot_reservations(
        demand_id TEXT PRIMARY KEY, supplier_id TEXT NOT NULL, status TEXT NOT NULL
        CHECK(status IN ('active','completed','withdrawn')),
        accepted_at TEXT NOT NULL, closed_at TEXT,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id)
    )""")


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


def accept_pilot(connection: sqlite3.Connection, demand_id: str, supplier_id: str) -> dict[str, Any]:
    prepare_capacity(connection)
    if not demand_id.strip():
        raise ContractError("pilot demand identifier is required")
    supplier = connection.execute("SELECT active_slots FROM suppliers WHERE supplier_id=?", (supplier_id,)).fetchone()
    if supplier is None:
        raise ContractError("unknown supplier")
    existing = connection.execute("SELECT supplier_id,status FROM pilot_reservations WHERE demand_id=?",
                                  (demand_id,)).fetchone()
    if existing:
        if existing[0] != supplier_id or existing[1] != "active":
            raise ContractError("closed or reassigned pilots require a new approval")
        return {"demand_id": demand_id, "supplier_id": supplier_id, "status": "active"}
    used = connection.execute("SELECT COUNT(*) FROM pilot_reservations WHERE supplier_id=? AND status='active'",
                              (supplier_id,)).fetchone()[0]
    if used >= supplier[0]:
        raise ContractError("supplier has no remaining pilot slots")
    connection.execute("INSERT INTO pilot_reservations VALUES(?,?,?,?,NULL)",
                       (demand_id, supplier_id, "active", utc_now()))
    return {"demand_id": demand_id, "supplier_id": supplier_id, "status": "active"}


def finish_pilot(connection: sqlite3.Connection, demand_id: str, status: str) -> None:
    prepare_capacity(connection)
    if status not in {"completed", "withdrawn"}:
        raise ContractError("pilot outcome must be completed or withdrawn")
    row = connection.execute("SELECT status FROM pilot_reservations WHERE demand_id=?", (demand_id,)).fetchone()
    if row is None:
        raise ContractError("unknown pilot")
    if row[0] == status:
        return
    if row[0] != "active":
        raise ContractError("pilot already closed with another outcome")
    connection.execute("UPDATE pilot_reservations SET status=?,closed_at=? WHERE demand_id=?",
                       (status, utc_now(), demand_id))


def capacity_status(connection: sqlite3.Connection, supplier_id: str) -> dict[str, Any]:
    prepare_capacity(connection)
    row = connection.execute("SELECT active_slots FROM suppliers WHERE supplier_id=?", (supplier_id,)).fetchone()
    if row is None:
        raise ContractError("unknown supplier")
    reservations = [dict(entry) for entry in connection.execute(
        "SELECT demand_id,status,accepted_at,closed_at FROM pilot_reservations WHERE supplier_id=? ORDER BY demand_id",
        (supplier_id,))]
    active = sum(item["status"] == "active" for item in reservations)
    return {"supplier_id": supplier_id, "slots": row[0], "available": row[0] - active,
            "reservations": reservations}
