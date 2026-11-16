from __future__ import annotations

import argparse
import json
from typing import Any, Sequence

from scene_exchange.coordinator import Application, run, verify
from scene_exchange.intake.demand_contract import ContractError


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='scene_exchange', description='人工智能开放场景需求撮合与试点治理平台')
    commands = root.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--fixture", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--database", required=True)
    check.add_argument("--output", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--database", required=True)

    supply = commands.add_parser("supply", help="show supplier reliability and commitment ranges")
    supply.add_argument("--database", required=True)
    supply.add_argument("--supplier")

    status = commands.add_parser("pilot-status", help="show occupancy for one supplier")
    status.add_argument("--database", required=True)
    status.add_argument("--supplier", required=True)

    accept = commands.add_parser("pilot-accept", help="confirm a pilot against current capacity")
    accept.add_argument("--database", required=True)
    accept.add_argument("--demand", required=True)
    accept.add_argument("--supplier", required=True)
    accept.add_argument("--units", type=int, default=1)
    accept.add_argument("--match-score", type=float)
    accept.add_argument("--benefit-score", type=float)
    accept.add_argument("--reviewed-fingerprint")
    accept.add_argument("--override", action="store_true")
    accept.add_argument("--approver")
    accept.add_argument("--reason")
    accept.add_argument("--actor", default="operations")

    finish = commands.add_parser("pilot-finish", help="record a completed or withdrawn pilot")
    finish.add_argument("--database", required=True)
    finish.add_argument("--demand", required=True)
    finish.add_argument("--status", required=True, choices=["completed", "withdrawn"])
    finish.add_argument("--realized-benefit", type=float)
    finish.add_argument("--reason")
    finish.add_argument("--actor", default="operations")

    trail = commands.add_parser("commitment-trail", help="trace recommendations against commitments")
    trail.add_argument("--database", required=True)
    trail.add_argument("--demand")
    trail.add_argument("--supplier")

    revise = commands.add_parser("supplier-revise", help="record a reviewed change of declared slots")
    revise.add_argument("--database", required=True)
    revise.add_argument("--supplier", required=True)
    revise.add_argument("--slots", type=int, required=True)
    revise.add_argument("--reason", required=True)
    revise.add_argument("--actor", default="operations")
    return root


def _execute(args: argparse.Namespace) -> Any:
    application = Application(args.database)
    if args.command == "run":
        return run(args.fixture, args.database, args.output)
    if args.command == "verify":
        return verify(args.database, args.output)
    if args.command == "inspect":
        return application.inspect()
    if args.command == "supply":
        if args.supplier:
            return application.supplier_analysis(args.supplier)
        return application.supply_analysis()
    if args.command == "pilot-status":
        return application.capacity_status(args.supplier)
    if args.command == "pilot-accept":
        return application.accept_pilot(
            args.demand, args.supplier, args.units,
            match_score=args.match_score, benefit_score=args.benefit_score,
            reviewed_fingerprint=args.reviewed_fingerprint, override=args.override,
            approver=args.approver, reason=args.reason, actor=args.actor)
    if args.command == "pilot-finish":
        return application.finish_pilot(args.demand, args.status, args.realized_benefit,
                                        args.actor, args.reason)
    if args.command == "commitment-trail":
        return application.commitment_trail(args.demand, args.supplier)
    if args.command == "supplier-revise":
        return application.revise_supplier_commitment(args.supplier, args.slots,
                                                      args.reason, args.actor)
    raise ContractError("unsupported command")


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = _execute(args)
    except ContractError as exc:
        details = getattr(exc, "details", None)
        print(json.dumps({"ok": False, "error": str(exc), "details": details},
                         ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not isinstance(result, dict) or result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
