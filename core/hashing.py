"""Contract hashing (R3/R7): a change is contract-preserving iff the contract
file's hash is identical before and after. The hash is the evidence.

CLI:
  python -m core.hashing contracts/ledger.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def file_hash(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    for p in sys.argv[1:]:
        print(f"{file_hash(p)}  {p}")
