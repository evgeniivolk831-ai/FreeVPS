#!/usr/bin/env python3
"""Fail-closed G0-G12 promotion evaluator.

Consumes evidence artifacts and emits a bounded promotion decision. It never
upgrades UNKNOWN/NOT_EXECUTED/NOT_VERIFIED into PASS.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

BLOCKING = {"UNKNOWN", "UNKNOWN_CAPABILITY", "NOT_OBSERVED", "NOT_EXECUTED", "NOT_VERIFIED", "CONTAMINATED", "INCONCLUSIVE"}


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(root: Path):
    files = sorted((root / "artifacts").glob("*.json"))
    evidence = [load(p) for p in files if p.name != "promotion_decision.json"]
    gates = {f"G{i}": {"behavioral": "UNKNOWN", "assurance": "NOT_VERIFIED"} for i in range(13)}

    for item in evidence:
        typ = item.get("artifact_type", "")
        if typ == "V∞_RUNTIME_ATTESTATION":
            gates["G0"]["behavioral"] = "OBSERVED"
            if item.get("epistemic", {}).get("identity_verification") != "INDEPENDENTLY_VERIFIED":
                gates["G0"]["assurance"] = "NOT_VERIFIED"
        elif typ == "V∞_HOLDOUT_SEAL":
            gates["G7"]["behavioral"] = "OBSERVED"
            gates["G7"]["assurance"] = item.get("epistemic", {}).get("holdout_integrity", "NOT_VERIFIED")
        elif typ == "V∞_EVIDENCE_RECORD":
            if item.get("verification") == "INDEPENDENTLY_VERIFIED":
                gates["G12"]["assurance"] = "VERIFIED"
            else:
                gates["G12"]["assurance"] = "NOT_VERIFIED"

    full_pass = all(g["assurance"] == "VERIFIED" for g in gates.values())
    blockers = [
        {"gate": gid, "assurance": g["assurance"]}
        for gid, g in gates.items() if g["assurance"] in BLOCKING
    ]
    state = "FULL_PROMOTION" if full_pass and not blockers else "BOUNDED_ASSURANCE"
    result = {
        "artifact_type": "V∞_PROMOTION_DECISION",
        "promotion_state": state,
        "full_promotion": full_pass and not blockers,
        "gates": gates,
        "blocking_unknowns": blockers,
        "evidence_files": [p.name for p in files],
        "rule": "No gate may be promoted without explicit verified evidence; this evaluator does not establish independence by declaration."
    }
    result["artifact_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = evaluate(args.root)
    out = args.output or args.root / "artifacts" / "promotion_decision.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["full_promotion"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
