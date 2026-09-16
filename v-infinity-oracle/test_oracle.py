#!/usr/bin/env python3
import json
from oracle import verify


def run():
    clean = {
        "claims": [{"id": "c1", "state": "OBSERVED", "evidence_ids": ["e1"]}],
        "evidence": [{"id": "e1", "state": "OBSERVED", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"}],
    }
    assert verify(clean)["overall"] == "PASS"

    blocked_state = {
        "claims": [{"id": "c1", "state": "UNKNOWN", "evidence_ids": ["e1"]}],
        "evidence": [{"id": "e1", "state": "OBSERVED", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"}],
    }
    assert verify(blocked_state)["overall"] == "BLOCKED"

    blocked_independence = {
        "claims": [{"id": "c1", "state": "OBSERVED", "requires_independence": True, "evidence_ids": ["e1"]}],
        "evidence": [{"id": "e1", "state": "OBSERVED", "independent": True, "trust_domain": "same_repo", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"}],
    }
    assert verify(blocked_independence)["overall"] == "BLOCKED"

    allowed_independence = {
        "claims": [{"id": "c1", "state": "OBSERVED", "requires_independence": True, "evidence_ids": ["e1"]}],
        "evidence": [{"id": "e1", "state": "OBSERVED", "independent": True, "trust_domain": "separate_verifier_service", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"}],
    }
    assert verify(allowed_independence)["overall"] == "PASS"

    contradiction = {
        "claims": [{"id": "c1", "state": "OBSERVED", "evidence_ids": ["e1"], "contradicting_evidence_ids": ["e2"]}],
        "evidence": [
            {"id": "e1", "state": "OBSERVED", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"},
            {"id": "e2", "state": "OBSERVED", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"},
        ],
    }
    assert verify(contradiction)["overall"] == "BLOCKED"

    duplicate = {
        "claims": [{"id": "c1", "state": "OBSERVED", "evidence_ids": ["e1"]}],
        "evidence": [
            {"id": "e1", "state": "OBSERVED", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"},
            {"id": "e1", "state": "OBSERVED", "contamination_status": "CLEAN", "revocation_status": "ACTIVE"},
        ],
    }
    assert verify(duplicate)["overall"] == "BLOCKED"

    print(json.dumps({"tests": "PASS", "cases": 6}, sort_keys=True))


if __name__ == "__main__":
    run()
