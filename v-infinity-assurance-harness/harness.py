#!/usr/bin/env python3
"""V∞ external assurance artifact harness."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, socket, subprocess, time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"; ARTIFACTS.mkdir(parents=True, exist_ok=True)
UNKNOWN, NOT_OBSERVED, NOT_EXECUTED = "UNKNOWN", "NOT_OBSERVED", "NOT_EXECUTED"

def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def canonical(obj: Any) -> bytes: return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
def write_artifact(name: str, obj: Dict[str, Any]) -> Path:
    digest = sha256_bytes(canonical(obj)); wrapped = dict(obj); wrapped["artifact_sha256"] = digest
    path = ARTIFACTS / name; path.write_text(json.dumps(wrapped, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"); return path

def git_value(args: list[str]) -> str:
    try: return subprocess.check_output(["git", *args], cwd=ROOT.parent, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception: return UNKNOWN

def attest() -> Path:
    return write_artifact("runtime_attestation.json", {
        "artifact_type":"V∞_RUNTIME_ATTESTATION", "attestation_version":"1.0", "observed_at_unix":time.time(),
        "observer":{"id":"v-infinity-harness","trust_domain":"harness-runtime"},
        "target":{"model_id":UNKNOWN,"model_version":UNKNOWN,"provider":UNKNOWN,"harness":UNKNOWN,"harness_version":UNKNOWN},
        "runtime":{"python":platform.python_version(),"platform":platform.platform(),"hostname":socket.gethostname(),"os":platform.system(),"os_release":platform.release(),"cwd":str(ROOT.parent)},
        "source":{"git_commit":git_value(["rev-parse","HEAD"]),"git_branch":git_value(["rev-parse","--abbrev-ref","HEAD"])},
        "epistemic":{"identity_verification":"NOT_VERIFIED","runtime_observation":"OBSERVED","independent_verification":"NOT_OBSERVED"}
    })

def seal_holdout(input_path: Path) -> Path:
    digest=sha256_bytes(input_path.read_bytes())
    return write_artifact("holdout_seal.json", {"artifact_type":"V∞_HOLDOUT_SEAL","holdout_id":f"holdout-{digest[:16]}","content_sha256":digest,"sealed_at_unix":time.time(),"source_path":str(input_path),"access_status":"SEALED_BY_HASH","contamination_status":"UNKNOWN","release_status":"NOT_RELEASED","observer":"v-infinity-harness","epistemic":{"holdout_integrity":"NOT_VERIFIED","independent_holdout_control":"NOT_VERIFIED"}})

def evidence(input_path: Path) -> Path:
    digest=sha256_bytes(input_path.read_bytes())
    return write_artifact("evidence_record.json", {"artifact_type":"V∞_EVIDENCE_RECORD","evidence_id":f"e-{digest[:16]}","source_path":str(input_path),"raw_result_sha256":digest,"observed_at_unix":time.time(),"observer_id":"v-infinity-harness","execution_id":os.environ.get("V_INFINITY_EXECUTION_ID",UNKNOWN),"target_version":os.environ.get("V_INFINITY_TARGET_VERSION",UNKNOWN),"state":"OBSERVED","contamination_status":"UNKNOWN","revocation_status":"ACTIVE","provenance":"HARNESS_OBSERVED","verification":"NOT_VERIFIED","independent":False,"trust_domain":"harness-runtime","epistemic":{"evidence_integrity":"HASH_OBSERVED_NOT_INDEPENDENTLY_VERIFIED","system_property":"NOT_ESTABLISHED"}})

def self_test() -> Path:
    checks={"unknown_not_pass":UNKNOWN!="PASS","not_executed_not_pass":NOT_EXECUTED!="PASS","not_observed_not_absent":NOT_OBSERVED!="ABSENT","external_not_independent":True,"instance_not_system_property":True,"hash_is_sha256":len(sha256_bytes("V∞".encode("utf-8")))==64}
    return write_artifact("harness_self_test.json", {"artifact_type":"V∞_HARNESS_SELF_TEST","executed":True,"checks":checks,"all_checks_true":all(checks.values()),"claim_scope":"HARNESS_INSTANCE","system_compliance":"NOT_VERIFIED"})

def main() -> int:
    parser=argparse.ArgumentParser(description="V∞ evidence-producing assurance harness"); sub=parser.add_subparsers(dest="command",required=True); sub.add_parser("attest")
    h=sub.add_parser("seal-holdout"); h.add_argument("--input",required=True,type=Path); e=sub.add_parser("evidence"); e.add_argument("--input",required=True,type=Path); sub.add_parser("self-test")
    args=parser.parse_args(); path=attest() if args.command=="attest" else seal_holdout(args.input) if args.command=="seal-holdout" else evidence(args.input) if args.command=="evidence" else self_test()
    print(json.dumps({"created":str(path),"sha256":sha256_bytes(path.read_bytes())},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
