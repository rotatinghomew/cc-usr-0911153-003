from __future__ import annotations

import math
import statistics
from typing import Any, Iterable, Mapping

from scene_exchange.intake.demand_contract import bounded, finite_number, stable_hash


DEFAULT_POLICY: dict[str, Any] = {
    "confidence_z": 1.2815515655446004,
    "evidence_prior": 2.0,
    "min_evidence": 3,
    "probation_slots": 1,
}


def wilson_interval(successes: int, trials: int, z: float = 1.2815515655446004) -> tuple[float, float]:
    """Wilson score interval for a binomial success rate.

    The lower bound is used as a conservative fulfillment estimate: a supplier
    with only a handful of pilots, or with withdrawals, cannot claim a large
    share of its declared slots.
    """
    if trials <= 0:
        return 0.0, 1.0
    successes = min(max(0, int(successes)), int(trials))
    p = successes / trials
    denominator = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denominator
    margin = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _units(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 1
    return max(0, number)


def _benefit_summary(rows: list[dict[str, Any]], active: int, discount: float,
                     z: float) -> dict[str, Any]:
    expected_values = [bounded(row["benefit_score"]) for row in rows
                       if row.get("benefit_score") is not None]
    observed: list[float] = []
    imputed = 0
    unreported = 0
    for row in rows:
        if row.get("status") == "completed":
            if row.get("realized_benefit") is None:
                unreported += 1
            else:
                observed.append(bounded(row["realized_benefit"]))
        elif row.get("status") == "withdrawn":
            observed.append(0.0)
            imputed += 1
    observations = len(observed)
    if observations >= 2:
        mean = statistics.fmean(observed)
        spread = statistics.pstdev(observed)
        error = z * spread / math.sqrt(observations)
        lower = max(0.0, mean - error)
        upper = min(1.0, mean + error)
        width = upper - lower
    else:
        mean = observed[0] if observed else 0.0
        spread = 0.0
        lower, upper, width = 0.0, 1.0, 1.0
    return {
        "expected_mean": statistics.fmean(expected_values) if expected_values else 0.0,
        "expected_observations": len(expected_values),
        "realized_mean": mean,
        "realized_stdev": spread,
        "lower": lower,
        "upper": upper,
        "interval_width": width,
        "observations": observations,
        "imputed_zeros": imputed,
        "unreported_completions": unreported,
        "active_unresolved": active,
        "confidence": bounded(1.0 - width) * discount if observations else 0.0,
    }


def estimate_supplier(supplier_id: str, registered_slots: int,
                      rows: Iterable[Mapping[str, Any]],
                      policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Estimate the concurrent commitment a supplier can support.

    Capacity is driven only by closed-pilot evidence.  Expected benefit and the
    single-demand match score are reported for context but never raise the
    ceiling, so an evidence-poor supplier cannot be allocated indefinitely just
    because its average benefit looks attractive.
    """
    settings = dict(DEFAULT_POLICY)
    settings.update(policy or {})
    registered = max(1, int(registered_slots))
    reservations = [dict(row) for row in rows]

    completed = sum(1 for row in reservations if row.get("status") == "completed")
    withdrawn = sum(1 for row in reservations if row.get("status") == "withdrawn")
    active = sum(1 for row in reservations if row.get("status") == "active")
    closed = completed + withdrawn
    active_units = sum(_units(row.get("committed_units")) for row in reservations
                       if row.get("status") == "active")
    closed_units = sum(_units(row.get("committed_units")) for row in reservations
                       if row.get("status") in {"completed", "withdrawn"})

    z = finite_number(settings.get("confidence_z"), DEFAULT_POLICY["confidence_z"])
    prior = max(0.0, finite_number(settings.get("evidence_prior"), DEFAULT_POLICY["evidence_prior"]))
    min_evidence = max(0, int(settings.get("min_evidence", DEFAULT_POLICY["min_evidence"])))
    probation_setting = int(settings.get("probation_slots", DEFAULT_POLICY["probation_slots"]))
    probation = max(1, min(registered, probation_setting))

    if closed:
        success_point = (completed + 1.0) / (closed + 2.0)
        success_lower, success_upper = wilson_interval(completed, closed, z)
        evidence_discount = closed / (closed + prior) if closed + prior else 0.0
    else:
        success_point = 0.5
        success_lower, success_upper = 0.0, 1.0
        evidence_discount = 0.0

    if closed < min_evidence:
        # Until enough pilots have closed, the supplier may run one pilot at a
        # time no matter how attractive its expected benefit looks.
        recommended = probation
        maximum = probation
    else:
        recommended = max(1, min(registered, math.floor(registered * success_lower)))
        maximum = max(1, min(registered, math.floor(registered * success_point)))
        maximum = max(recommended, maximum)
    recommended = max(0, min(registered, recommended))
    maximum = max(recommended, min(registered, maximum)) if recommended else 0
    available = max(0, recommended - active_units)

    benefit = _benefit_summary(reservations, active, evidence_discount, z)
    match_values = [bounded(row["match_score"]) for row in reservations
                    if row.get("match_score") is not None]
    matching = {
        "mean_match_score": statistics.fmean(match_values) if match_values else None,
        "observations": len(match_values),
        "best_match_score": max(match_values) if match_values else None,
    }
    notes: list[str] = []
    if closed == 0:
        notes.append("no closed pilots; commitment is limited to probation capacity")
    elif closed < min_evidence:
        notes.append(f"only {closed} closed pilot(s); commitment remains at probation capacity")
    elif withdrawn and completed == 0:
        notes.append("every closed pilot withdrew; commitment remains at probation capacity")
    if withdrawn:
        notes.append(f"{withdrawn} of {closed} closed pilot(s) withdrew; "
                     "the supported range stays below declared slots")
    if active:
        notes.append(f"{active} active pilot(s) are immature and excluded from realized benefit")
    if imputed_zeros := benefit["imputed_zeros"]:
        notes.append(f"{imputed_zeros} withdrawal(s) count as zero realized benefit")
    if unreported := benefit["unreported_completions"]:
        notes.append(f"{unreported} completed pilot(s) have no reported realized benefit "
                     "and are excluded from the realized mean")
    notes.append("benefit estimates are reported separately and do not raise the capacity ceiling")
    notes.append("match score describes a single demand; it does not establish concurrent delivery")

    basis = {
        "supplier_id": supplier_id,
        "registered_slots": registered,
        "completed": completed,
        "withdrawn": withdrawn,
        "active": active,
        "active_units": active_units,
        "recommended": recommended,
        "maximum": maximum,
        "policy": {
            "confidence_z": z,
            "evidence_prior": prior,
            "min_evidence": min_evidence,
            "probation_slots": probation_setting,
        },
    }
    return {
        "supplier_id": supplier_id,
        "registered_slots": registered,
        "evidence": {
            "completed": completed,
            "withdrawn": withdrawn,
            "active": active,
            "closed": closed,
            "mature": closed >= min_evidence,
            "min_required": min_evidence,
        },
        "reliability": {
            "fulfillment_rate": (completed / closed) if closed else None,
            "success_point": success_point,
            "success_lower": success_lower,
            "success_upper": success_upper,
            "evidence_discount": evidence_discount,
        },
        "commitment_range": {
            "minimum": 1 if recommended else 0,
            "recommended": recommended,
            "maximum": maximum,
            "declared_slots": registered,
            "unit": "parallel pilot slots",
        },
        "occupancy": {
            "active_units": active_units,
            "closed_units": closed_units,
            "available_units": available,
            "headroom_units": max(0, maximum - active_units),
            "overcommitted_units": max(0, active_units - maximum),
            "load": (active_units / recommended) if recommended else None,
        },
        "benefit": benefit,
        "matching": matching,
        "notes": notes,
        "basis": basis,
        "fingerprint": stable_hash({"supplier_id": supplier_id, "basis": basis}),
    }
