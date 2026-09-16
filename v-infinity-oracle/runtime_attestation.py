#!/usr/bin/env python3
"""Runtime provenance attestation for V∞ evaluation environments."""
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ["oracle.py", "schema.json", "validate_policies.py"]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    out = {
        "status": "OBSERVED",
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pid": os.getpid(),
        "files": {name: sha256(ROOT / name) for name in FILES},
    }
    try:
        out["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT.parent, text=True
        ).strip()
    except Exception:
        out["git_commit"] = "UNKNOWN"
    print(json.dumps(out, sort_keys=True))

if __name__ == "__main__":
    main()
