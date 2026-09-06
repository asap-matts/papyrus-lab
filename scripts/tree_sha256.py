#!/usr/bin/env python3
"""Print the content hash of a directory tree (E02 helper, same definition everywhere in PapyrusLab).

Definition (scripts/build_w035_label_dataset.py, E00): sha256 over the sorted lines 'relpath\\nsha256(file)\\n',
relpath relative to the given directory, POSIX separators. Two trees with the same hash have identical files.

Usage:
  python scripts/tree_sha256.py <directory> [--list]     # --list also prints one line per file
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def tree_sha256(root: Path) -> tuple[str, dict[str, str]]:
    per_file = {}
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        per_file[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    h = hashlib.sha256()
    for rel, digest in sorted(per_file.items()):
        h.update(f"{rel}\n{digest}\n".encode())
    return h.hexdigest(), per_file


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("directory", type=Path)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    root = a.directory.resolve()
    assert root.is_dir(), f"not a directory: {root}"
    digest, per_file = tree_sha256(root)
    if a.list:
        for rel, d in sorted(per_file.items()):
            print(d, rel)
    total = sum((root / rel).stat().st_size for rel in per_file)
    print(f"tree_sha256={digest} files={len(per_file)} bytes={total} root={root}")


if __name__ == "__main__":
    main()
