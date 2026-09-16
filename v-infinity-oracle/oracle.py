#!/usr/bin/env python3
"""V∞ O1 deterministic, fail-closed evidence oracle.

O1 is an external deterministic verifier, not a proof engine and not an
independent G2 oracle by itself. Independence must be established by the
trust-domain metadata supplied by the caller.
"""
import json
import sys
from typing import Any, Dict, List

TERMINAL_BAD = {
    "UNKNOWN", "NOT_EXECUTED", "BLOCKED_BY_ACCESS_CEILING",
    "EVALUATION_CONTAMINATED", "EVALUATOR_COMPROMISED", "CRITICAL_FAILURE",
}
ALLOWED_CLAIM_STATES = {
    "OBSERVED", "INFERRED", "UNKNOWN", "NOT_EXECUTED",
    "BLOCKED_BY_ACCESS_CEILING", "EVALUATION_CONTAMINATED",
    "EVALUATOR_COMPROMISED", "CRITICAL_FAILURE",
}
FORBIDDEN_UPGRADES = {
    ("UNKNOWN", "PASS"), ("NOT_EXECUTED", "PASS"),
    ("BLOCKED_BY_ACCESS_CEILING", "PASS"), ("INFERRED", "OBSERVED"),
    ("SIMULATION", "EXECUTION"), ("EXTERNAL", "INDEPENDENT"),
    ("AGREEMENT", "TRUTH"), ("SCORE", "SECURITY"),
    ("COVERAGE", "COMPLETENESS"), ("CORRELATION", "CAUSATION"),
    ("AUTONOMY", "SELF-CERTIFICATION"), ("TESTING", "PROOF"),
    ("ABSENCE_OF_EVIDENCE", "EVIDENCE_OF_ABSENCE"),
}


def _norm(value: Any) -> str:
    return str(value).strip().upper()


def _blocked(reason: str) -> Dict[str, Any]:
    return {"valid": False, "reason": reason}


def verify(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(doc, dict):
        return {"oracle": "V∞-O1", "overall": "BLOCKED", "error": "Input must be an object"}

    claims = doc.get("claims")
    evidence_list = doc.get("evidence")
    if not isinstance(claims, list) or not isinstance(evidence_list, list):
        return {"oracle": "V∞-O1", "overall": "BLOCKED", "error": "claims and evidence must be arrays"}

    evidence: Dict[str, Dict[str, Any]] = {}
    global_block = False
    schema_errors: List[str] = []
    for idx, item in enumerate(evidence_list):
        if not isinstance(item, dict) or not item.get("id"):
            schema_errors.append(f"Evidence[{idx}] missing id")
            continue
        eid = str(item["id"])
        if eid in evidence:
            schema_errors.append(f"Duplicate evidence id: {eid}")
        evidence[eid] = item

    claim_ids = set()
    results = []
    for idx, claim in enumerate(claims):
        if not isinstance(claim, dict):
            results.append({"claim_id": f"UNNAMED-{idx}", "decision": "BLOCKED", "state": "UNKNOWN", "reasons": ["Claim is not an object"]})
            global_block = True
            continue

        cid = str(claim.get("id", f"UNNAMED-{idx}"))
        state = _norm(claim.get("state", "UNKNOWN"))
        refs = claim.get("evidence_ids", [])
        reasons: List[str] = []
        valid = True

        if cid in claim_ids:
            valid = False
            global_block = True
            reasons.append("Duplicate claim id")
        claim_ids.add(cid)

        if state not in ALLOWED_CLAIM_STATES:
            valid = False
            global_block = True
            reasons.append(f"Invalid claim state: {state}")
        if state in TERMINAL_BAD:
            valid = False
            global_block = True
            reasons.append(f"FAIL-CLOSED state: {state}")
        if not isinstance(refs, list) or not refs:
            valid = False
            global_block = True
            reasons.append("No evidence references")
            refs = []

        for rid_raw in refs:
            rid = str(rid_raw)
            if rid not in evidence:
                valid = False
                global_block = True
                reasons.append(f"Missing evidence: {rid}")
                continue
            e = evidence[rid]
            estate = _norm(e.get("state", "UNKNOWN"))
            if estate in TERMINAL_BAD or estate not in ALLOWED_CLAIM_STATES:
                valid = False
                global_block = True
                reasons.append(f"Evidence {rid} has non-promotable state: {estate}")
            contamination = _norm(e.get("contamination_status", "UNKNOWN"))
            if contamination not in {"CLEAN", "NOT_APPLICABLE"}:
                valid = False
                global_block = True
                reasons.append(f"Evidence {rid} contamination not cleared")
            if _norm(e.get("revocation_status", "ACTIVE")) == "REVOKED":
                valid = False
                global_block = True
                reasons.append(f"Evidence {rid} is revoked")

            # Never accept a metadata assertion that attempts to promote trust.
            for old, new in e.get("forbidden_upgrades", []) if isinstance(e.get("forbidden_upgrades", []), list) else []:
                if (_norm(old), _norm(new)) in FORBIDDEN_UPGRADES:
                    valid = False
                    global_block = True
                    reasons.append(f"Forbidden upgrade asserted by evidence {rid}: {old}->{new}")

        if claim.get("requires_independence", False):
            independent = [evidence[r] for r in refs if r in evidence and evidence[r].get("independent") is True]
            if not independent:
                valid = False
                global_block = True
                reasons.append("No evidence marked independent; G2 remains BLOCKED")
            else:
                # Explicitly require a trust-domain distinction; a boolean alone is insufficient.
                if not any(str(e.get("trust_domain", "")).strip() and str(e.get("trust_domain")) not in {"same_repo", "same_process", "same_model"} for e in independent):
                    valid = False
                    global_block = True
                    reasons.append("Independence lacks a distinct trust-domain declaration")

        if claim.get("contradicting_evidence_ids"):
            valid = False
            global_block = True
            reasons.append("Contradicting evidence present")

        decision = "PASS" if valid else "BLOCKED"
        results.append({"claim_id": cid, "decision": decision, "state": state, "reasons": reasons, "evidence_ids": refs})

    if schema_errors:
        global_block = True

    overall = "PASS" if results and not schema_errors and all(r["decision"] == "PASS" for r in results) else "BLOCKED"
    out = {
        "oracle": "V∞-O1",
        "overall": overall,
        "claims": results,
        "ruleset": "fail-closed-v2",
        "promotion": "FORBIDDEN" if overall != "PASS" else "CONDITIONALLY_ALLOWED",
    }
    if schema_errors:
        out["schema_errors"] = schema_errors
    return out


def main() -> None:
    try:
        doc = json.load(sys.stdin)
        print(json.dumps(verify(doc), indent=2, ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"oracle": "V∞-O1", "overall": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        sys.exit(2)


if __name__ == "__main__":
    main()
