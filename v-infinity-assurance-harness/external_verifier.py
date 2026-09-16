#!/usr/bin/env python3
"""Independent-process verifier for V∞ assurance artifacts.

This verifier checks artifact self-hashes and binds runtime evidence to the
workflow commit. It does NOT establish model identity, oracle independence,
holdout secrecy, or system-level security; those remain NOT_VERIFIED.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path

ARTIFACT_TYPES = {
    "V∞_RUNTIME_ATTESTATION",
    "V∞_HARNESS_SELF_TEST",
    "V∞_PROMOTION_DECISION",
    "V∞_HOLDOUT_SEAL",
    "V∞_EVIDENCE_RECORD",
}

def canonical(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def verify_hash(item: dict) -> bool:
    claimed = item.get("artifact_sha256")
    if not isinstance(claimed, str) or len(claimed) != 64:
        return False
    body = dict(item)
    body.pop("artifact_sha256", None)
    return hashlib.sha256(canonical(body)).hexdigest() == claimed

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--expected-commit", default=os.environ.get("GITHUB_SHA", "UNKNOWN"))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    files = sorted(args.artifacts.glob("*.json"))
    results = []
    all_hashes = True
    for path in files:
        try:
            item = load(path)
            ok_type = item.get("artifact_type") in ARTIFACT_TYPES
            ok_hash = verify_hash(item)
            all_hashes = all_hashes and ok_type and ok_hash
            results.append({"file": path.name, "artifact_type": item.get("artifact_type", "UNKNOWN"), "type_valid": ok_type, "hash_verified": ok_hash})
        except Exception as exc:
            all_hashes = False
            results.append({"file": path.name, "type_valid": False, "hash_verified": False, "error": type(exc).__name__})

    attestation = None
    for path in files:
        if path.name == "runtime_attestation.json":
            try: attestation = load(path)
            except Exception: attestation = None
    observed_commit = (attestation or {}).get("source", {}).get("git_commit", "UNKNOWN")
    commit_binding = observed_commit != "UNKNOWN" and args.expected_commit != "UNKNOWN" and observed_commit == args.expected_commit

    verifier_process = {
        "process_id": os.getpid(),
        "verifier_id": "v-infinity-external-verifier",
        "trust_domain": "verifier-runtime",
        "process_separation": "OBSERVED",
        "data_source": "DOWNLOADED_ARTIFACTS",
        "implementation_independence": "NOT_VERIFIED",
        "trust_domain_independence": "NOT_VERIFIED",
    }
    decision = {
        "artifact_type": "V∞_EXTERNAL_VERIFICATION",
        "verification_version": "1.0",
        "verified_at_unix": time.time(),
        "verifier": verifier_process,
        "checks": {
            "artifact_hash_integrity": "VERIFIED" if all_hashes and bool(files) else "INCONCLUSIVE",
            "workflow_commit_binding": "VERIFIED" if commit_binding else "NOT_VERIFIED",
            "model_identity": "NOT_VERIFIED",
            "oracle_independence": "NOT_VERIFIED",
            "generator_independence": "NOT_VERIFIED",
            "holdout_independence": "NOT_VERIFIED",
            "common_mode": "UNKNOWN",
            "system_security": "NOT_ESTABLISHED",
        },
        "artifacts": results,
        "claim_scope": "ARTIFACT_INTEGRITY_AND_COMMIT_BINDING_ONLY",
        "rule": "EXTERNAL_PROCESS != INDEPENDENT_ASSURANCE; VERIFIED artifact integrity does not imply VERIFIED system security.",
    }
    args.output.write_text(json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0 if decision["checks"]["artifact_hash_integrity"] == "VERIFIED" and decision["checks"]["workflow_commit_binding"] == "VERIFIED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
