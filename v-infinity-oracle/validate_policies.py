#!/usr/bin/env python3
"""Static executable checks for V∞ policy artifacts.

This does not certify the target. It verifies that required policy artifacts
are internally coherent and that the repository's fail-closed declarations
are present. Runtime independence/holdout isolation remain separate claims.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = {
    "evidence_policy.json",
    "holdout_policy.json",
    "threat_matrix.json",
    "common_mode_matrix.md",
    "adversarial_policy.json",
    "evaluator_security_policy.md",
    "environment_integrity.md",
    "regression_matrix.json",
}

def main():
    missing = sorted(p for p in REQUIRED if not (ROOT / p).exists())
    if missing:
        raise SystemExit("BLOCKED: missing policy artifacts: " + ", ".join(missing))

    for name in ["evidence_policy.json", "holdout_policy.json", "threat_matrix.json", "adversarial_policy.json", "regression_matrix.json"]:
        with open(ROOT / name, encoding="utf-8") as f:
            json.load(f)

    evidence = json.loads((ROOT / "evidence_policy.json").read_text(encoding="utf-8"))
    assert evidence["fail_closed"] is True
    assert evidence["promotion_rules"]["unknown_to_pass"] is False
    assert evidence["independence"]["boolean_only_is_insufficient"] is True

    holdout = json.loads((ROOT / "holdout_policy.json").read_text(encoding="utf-8"))
    assert holdout["holdout_required_for_promotion"] is True
    assert holdout["execution"]["target_access"] is False

    threat = json.loads((ROOT / "threat_matrix.json").read_text(encoding="utf-8"))
    assert len(threat["classes"]) >= 30

    adv = json.loads((ROOT / "adversarial_policy.json").read_text(encoding="utf-8"))
    assert adv["adaptive"] is True

    regression = json.loads((ROOT / "regression_matrix.json").read_text(encoding="utf-8"))
    assert len(regression["required_suites"]) >= 10

    print("V∞ policy validation: PASS")

if __name__ == "__main__":
    main()
