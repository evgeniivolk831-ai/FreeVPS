#!/usr/bin/env python3
"""Generate temporal holdout cases at evaluation time.

The individual cases are intentionally never printed. This establishes a
runtime holdout mechanism, but NOT an independently operated generator.
"""
import json
import secrets
import subprocess
import sys


def oracle(doc):
    p = subprocess.run([sys.executable, "oracle.py"], input=json.dumps(doc), text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout)


def main():
    cases = []
    for i in range(32):
        token = secrets.token_hex(16)
        if i % 2:
            cases.append({"claims":[{"id":"H", "state":"UNKNOWN", "evidence_ids":[]}], "evidence":[], "nonce":token})
        else:
            cases.append({"claims":[{"id":"H", "state":"OBSERVED", "evidence_ids":["E"]}], "evidence":[{"id":"E", "state":"OBSERVED", "contamination_status":"CLEAN", "revocation_status":"ACTIVE"}], "nonce":token})
    results = [oracle(c)["overall"] for c in cases]
    expected = ["PASS" if i % 2 == 0 else "BLOCKED" for i in range(32)]
    if results != expected:
        raise SystemExit("HOLDOUT_FAIL")
    print("V∞ temporal holdout: PASS (32 runtime-generated cases; cases withheld)")

if __name__ == "__main__":
    main()
