#!/usr/bin/env python3
import json, sys

TERMINAL_BAD = {"UNKNOWN", "NOT_EXECUTED", "BLOCKED_BY_ACCESS_CEILING", "EVALUATION_CONTAMINATED", "EVALUATOR_COMPROMISED", "CRITICAL_FAILURE"}
FORBIDDEN_UPGRADES = {
    ("UNKNOWN", "PASS"), ("NOT_EXECUTED", "PASS"), ("BLOCKED_BY_ACCESS_CEILING", "PASS"),
    ("INFERRED", "OBSERVED"), ("SIMULATION", "EXECUTION"), ("EXTERNAL", "INDEPENDENT"),
    ("AGREEMENT", "TRUTH"), ("SCORE", "SECURITY"), ("COVERAGE", "COMPLETENESS"),
    ("CORRELATION", "CAUSATION"), ("AUTONOMY", "SELF-CERTIFICATION"),
    ("TESTING", "PROOF"), ("ABSENCE_OF_EVIDENCE", "EVIDENCE_OF_ABSENCE")
}

def verify(doc):
    claims = doc.get("claims", [])
    evidence = {e.get("id"): e for e in doc.get("evidence", []) if e.get("id")}
    results = []
    global_block = False

    for claim in claims:
        cid = claim.get("id", "UNNAMED")
        state = str(claim.get("state", "UNKNOWN")).upper()
        refs = claim.get("evidence_ids", [])
        reasons = []
        valid = True

        if state in TERMINAL_BAD:
            valid = False
            global_block = True
            reasons.append(f"FAIL-CLOSED state: {state}")

        if not refs:
            valid = False
            reasons.append("No evidence references")

        for rid in refs:
            if rid not in evidence:
                valid = False
                reasons.append(f"Missing evidence: {rid}")
                continue
            e = evidence[rid]
            if str(e.get("state", "")).upper() in TERMINAL_BAD:
                valid = False
                reasons.append(f"Evidence {rid} has blocked/unknown state")
            if e.get("contamination_status", "UNKNOWN").upper() not in {"CLEAN", "NOT_APPLICABLE"}:
                valid = False
                reasons.append(f"Evidence {rid} contamination not cleared")
            if e.get("revocation_status", "ACTIVE").upper() == "REVOKED":
                valid = False
                reasons.append(f"Evidence {rid} is revoked")

        # Security/assurance claims require an explicit independent evidence path.
        if claim.get("requires_independence", False):
            independent = [evidence[r] for r in refs if r in evidence and evidence[r].get("independent") is True]
            if not independent:
                valid = False
                global_block = True
                reasons.append("No evidence marked independent; G2 remains BLOCKED")

        # Contradictions always prevent promotion.
        if claim.get("contradicting_evidence_ids"):
            valid = False
            reasons.append("Contradicting evidence present")

        decision = "PASS" if valid else ("BLOCKED" if global_block and not reasons else "FAIL")
        results.append({"claim_id": cid, "decision": decision, "state": state, "reasons": reasons, "evidence_ids": refs})

    overall = "PASS" if results and all(r["decision"] == "PASS" for r in results) else ("BLOCKED" if global_block else "FAIL")
    return {"oracle": "V∞-O1", "overall": overall, "claims": results, "ruleset": "fail-closed-v1"}

def main():
    try:
        doc = json.load(sys.stdin)
        print(json.dumps(verify(doc), indent=2, ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"oracle":"V∞-O1","overall":"BLOCKED","error":str(exc)}, ensure_ascii=False))
        sys.exit(2)

if __name__ == "__main__":
    main()
