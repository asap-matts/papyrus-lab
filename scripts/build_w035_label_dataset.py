#!/usr/bin/env python3
"""Build the private Kaggle dataset holding the w035 ink labels for E00.

Why: `hf buckets sync` on the 5,128 small files stalled for ~28 min in the preflight run of
2026-09-06, and a direct parallel download takes ~8 min (latency-bound). Mounting a Kaggle
dataset costs nothing at run time and freezes the label with a hash.

Provenance chain, all recorded in manifest.json:
  Hugging Face bucket API listing (prefix below)  ->  per-file download with size check
  ->  w035_labels.tar (dotfiles preserved)  ->  SHA-256  ->  Kaggle dataset  ->  notebook re-checks
      tar SHA-256, file count and byte total after extraction.

Usage:
  python scripts/build_w035_label_dataset.py [--from <dir already holding labels/w035>] [--out <dir>]
  then: kaggle datasets create -p <out>      (first time)   |   kaggle datasets version -p <out> -m "<msg>"
Default out dir: runs/E00-R01/dataset-w035-labels (ignored by Git; the dataset is rebuilt from this script).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import os
import re
import tarfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KAGGLE_USER = "matteopontesilli"
DATASET_SLUG = "papyruslab-w035-labels"
API = "https://huggingface.co/api/buckets/scrollprize/datasets/tree/ink_9um/labels/native9-scrollprizeorg-21slices/w035"
RESOLVE = "https://huggingface.co/buckets/scrollprize/datasets/resolve/"
PREFIX = "ink_9um/labels/native9-scrollprizeorg-21slices/w035/"
EXPECTED = (5128, 737833)   # measured via the bucket API on 2026-09-06


def list_files() -> list[tuple[str, int]]:
    files, url = [], API
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": "papyruslab-e00"})
        with urllib.request.urlopen(req, timeout=60) as r:
            files += [(e["path"], int(e["size"])) for e in json.load(r) if e.get("type") == "file"]
            m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", "") or "")
            url = m.group(1) if m else None
    return sorted(files)


def fetch(item: tuple[str, int], dest: Path) -> int:
    path, size = item
    assert path.startswith(PREFIX) and ".." not in path, path
    out = dest / path[len(PREFIX):]
    if out.exists() and out.stat().st_size == size:
        return size
    out.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(RESOLVE + path, timeout=60) as r:
                data = r.read()
            if len(data) == size:
                out.write_bytes(data)
                return size
            last = f"size {len(data)} != {size}"
        except Exception as ex:  # transient 429/5xx
            last = ex
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"download failed for {path}: {last}")


def local_stats(root: Path) -> tuple[int, int]:
    files = [p for p in root.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def tree_sha256(root: Path) -> tuple[str, dict[str, str]]:
    """Content hash of a directory tree: sha256 over sorted 'relpath\\nsha256(file)\\n' lines.

    The same function is embedded in the notebooks (CELL_5A) so the run can re-check the label
    content, not only file sizes, against the constant LABEL_TREE_SHA256 in the generator."""
    per_file = {}
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        per_file[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    h = hashlib.sha256()
    for rel, digest in sorted(per_file.items()):
        h.update(f"{rel}\n{digest}\n".encode())
    return h.hexdigest(), per_file


def main() -> None:
    global KAGGLE_USER
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default=None, help="directory already containing labels/w035 (verified download)")
    ap.add_argument("--out", default=str(ROOT / "runs" / "E00-R01" / "dataset-w035-labels"))
    ap.add_argument("--user", default=KAGGLE_USER, help="Kaggle username that will own the dataset")
    a = ap.parse_args()
    KAGGLE_USER = a.user
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    listing = list_files()
    total = sum(s for _, s in listing)
    print(f"API listing: {len(listing)} files, {total} bytes")
    assert (len(listing), total) == EXPECTED, f"label changed upstream: {len(listing)}, {total} != {EXPECTED}"

    if a.src:
        src = Path(a.src) / "labels" / "w035"
        assert src.is_dir(), src
    else:
        # staging OUTSIDE the dataset folder: `kaggle datasets create -p out` uploads everything under out
        src = out.parent / f"{out.name}-stage" / "labels" / "w035"
        t0 = time.time()
        with cf.ThreadPoolExecutor(max_workers=24) as ex:
            got = sum(ex.map(lambda it: fetch(it, src), listing))
        print(f"downloaded {got} bytes in {time.time() - t0:.0f} s")
    n, b = local_stats(src)
    assert (n, b) == EXPECTED, f"local tree {n} files / {b} bytes != {EXPECTED}"
    # every listed file must exist locally with the listed size
    for path, size in listing:
        p = src / path[len(PREFIX):]
        assert p.is_file() and p.stat().st_size == size, f"mismatch for {path}"

    # deterministic tar: sorted names, fixed mtime/uid/gid, dotfiles included
    tar_path = out / "w035_labels.tar"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for path, size in listing:
            rel = path[len(PREFIX):]
            info = tarfile.TarInfo(name="w035/" + rel)
            info.size = size; info.mtime = 0; info.uid = info.gid = 0; info.uname = info.gname = ""; info.mode = 0o644
            with open(src / rel, "rb") as fh:
                tf.addfile(info, fh)
    tar_bytes = buf.getvalue(); tar_path.write_bytes(tar_bytes)
    sha = hashlib.sha256(tar_bytes).hexdigest()
    print(f"{tar_path.name}: {len(tar_bytes)} bytes, sha256 {sha}")
    tree_sha, per_file = tree_sha256(src)
    print(f"tree sha256 (paths + per-file sha256): {tree_sha}")

    manifest = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_api": API, "source_resolve_base": RESOLVE, "source_prefix": PREFIX,
        "source_dataset_readme": "https://huggingface.co/buckets/scrollprize/datasets/tree/ink_9um",
        "file_count": len(listing), "byte_total": total,
        "tar_name": tar_path.name, "tar_bytes": len(tar_bytes), "tar_sha256": sha,
        "tar_layout": "w035/w035_inklabels.zarr/..., w035/w035_supervision_mask.zarr/...",
        "tree_sha256": tree_sha,
        "tree_sha256_definition": "sha256 over sorted lines 'relpath\\nsha256(file)\\n', relpath relative to w035/",
        "files": [{"path": p, "size": s, "sha256": per_file[p[len(PREFIX):]]} for p, s in listing],
        "note": "Labels only; CT data are not included. Built by scripts/build_w035_label_dataset.py for PapyrusLab E00.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (out / "dataset-metadata.json").write_text(json.dumps({
        "title": "PapyrusLab w035 ink labels (ink_9um native9)",
        "id": f"{KAGGLE_USER}/{DATASET_SLUG}",
        "licenses": [{"name": "other"}],
    }, indent=2), encoding="utf-8")
    print(f"dataset folder ready: {out}")
    print(f"TAR_SHA256={sha}")
    print(f"LABEL_TREE_SHA256={tree_sha}   <- copy into scripts/build_e00_notebooks.py")


if __name__ == "__main__":
    main()
