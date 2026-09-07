#!/usr/bin/env python3
"""Download ink_9um label sets from the Hugging Face bucket and package them for Kaggle (E02, plan step 2).

Generalisation of scripts/build_w035_label_dataset.py (E00) to a list of segments: one deterministic tar per
segment, a manifest.json with the bucket listing, per-file SHA-256, tree-SHA-256 and tar-SHA-256, and the
Kaggle dataset-metadata.json. Provenance chain, all recorded in manifest.json:
  bucket API listing (paginated)  ->  per-file download with size check (4 threads, backoff on 429)
  ->  <seg>_labels.tar  ->  SHA-256  ->  Kaggle dataset (plan step 4)  ->  notebooks re-check file by file.

Usage:
  python scripts/build_label_dataset.py --run-id e02-r01 --segments <family>/<seg> [<family>/<seg> ...] [--user <kaggle-user>]
Outputs (all ignored by Git):
  runs/<RUN-ID>/dataset-labels-stage/labels/<family>/<seg>/   verified download
  data/labels/<family>/<seg>/                                  local working copy for scripts/e02_metrics.py
  runs/<RUN-ID>/dataset-labels/                                tar files + manifest.json + dataset-metadata.json
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import re
import shutil
import tarfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "papyruslab-e02"
API = "https://huggingface.co/api/buckets/scrollprize/datasets/tree/ink_9um/labels/"
RESOLVE = "https://huggingface.co/buckets/scrollprize/datasets/resolve/"
PREFIX_ROOT = "ink_9um/labels/"
# measured via the bucket API on 2026-09-06 (plan step 2); a segment not listed here is accepted but flagged
EXPECTED = {
    "aligned-scrollprizeorg-21slices/pherc0814-46527": (1386, 118869),
    "aligned-scrollprizeorg-21slices/pherc0139-w016": (9414, 746565),
    "aligned-scrollprizeorg-21slices/pherc1667-w029": (13959, 1108191),
    "native9-scrollprizeorg-21slices/w035": (5128, 737833),
}


def list_files(segment: str) -> list[tuple[str, int]]:
    files, url = [], API + segment
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            files += [(e["path"], int(e["size"])) for e in json.load(r) if e.get("type") == "file"]
            m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", "") or "")
            url = m.group(1) if m else None
    return sorted(files)


def fetch(item: tuple[str, int], prefix: str, dest: Path) -> int:
    path, size = item
    assert path.startswith(prefix) and ".." not in path, path
    out = dest / path[len(prefix):]
    if out.exists() and out.stat().st_size == size:
        return size
    out.parent.mkdir(parents=True, exist_ok=True)
    last: object = None
    for attempt in range(8):
        try:
            req = urllib.request.Request(RESOLVE + path, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) == size:
                out.write_bytes(data)
                return size
            last = f"size {len(data)} != {size}"
        except urllib.error.HTTPError as ex:      # 429 rate limit, 5xx
            last = ex
        except Exception as ex:  # noqa: BLE001
            last = ex
        time.sleep(min(60, 5 * 2 ** attempt))
    raise RuntimeError(f"download failed for {path}: {last}")


def verify_decompress(seg_dir: Path) -> list[Path]:
    """Read every chunk of every zarr array under seg_dir; return the chunk files that fail to decompress.

    A size check alone accepts a chunk whose bytes are wrong but whose length matches (observed on 2026-09-07:
    17 chunks of pherc1667-w029_supervision_mask, 78 bytes each, unreadable; R02 docs/13 reports the same trap)."""
    import zarr

    bad: list[Path] = []
    for zpath in sorted(p for p in seg_dir.iterdir() if p.is_dir() and p.suffix == ".zarr"):
        node = zarr.open(str(zpath), mode="r")
        for level in sorted(node.array_keys(), key=int):
            a = node[level]
            cz, cy, cx = a.chunks
            for iy in range(0, a.shape[1], cy):
                for ix in range(0, a.shape[2], cx):
                    try:
                        a[:, iy:iy + cy, ix:ix + cx]
                    except Exception:  # noqa: BLE001 - any decompression error marks the chunk
                        bad.append(zpath / level / f"0.{iy // cy}.{ix // cx}")
    return bad


def tree_sha256(root: Path) -> tuple[str, dict[str, str]]:
    """Same definition as scripts/build_w035_label_dataset.py: sha256 over sorted 'relpath\\nsha256(file)\\n' lines."""
    per_file = {}
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        per_file[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    h = hashlib.sha256()
    for rel, digest in sorted(per_file.items()):
        h.update(f"{rel}\n{digest}\n".encode())
    return h.hexdigest(), per_file


def deterministic_tar(root: Path, arcname_root: str, listing: list[tuple[str, int]], prefix: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for path, size in listing:                       # listing is sorted: stable order
            rel = path[len(prefix):]
            info = tarfile.TarInfo(name=f"{arcname_root}/{rel}")
            info.size = size; info.mtime = 0; info.uid = info.gid = 0; info.uname = info.gname = ""; info.mode = 0o644
            with open(root / rel, "rb") as fh:
                tf.addfile(info, fh)
    return buf.getvalue()


def build_segment(segment: str, stage: Path, out: Path, data_dir: Path, workers: int) -> dict:
    family, name = segment.split("/", 1)
    prefix = f"{PREFIX_ROOT}{segment}/"
    listing = list_files(segment)
    total = sum(s for _, s in listing)
    print(f"[{name}] API listing: {len(listing)} files, {total} bytes", flush=True)
    if segment in EXPECTED:
        assert (len(listing), total) == EXPECTED[segment], f"{segment}: label changed upstream: {len(listing)}, {total} != {EXPECTED[segment]}"
    else:
        print(f"[{name}] WARNING: no expected counts for this segment; recording measured values", flush=True)
    src = stage / "labels" / family / name
    t0 = time.time()
    for attempt in range(1, 4):
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            got = sum(ex.map(lambda it: fetch(it, prefix, src), listing))
        print(f"[{name}] downloaded/verified {got} bytes in {time.time() - t0:.0f} s (pass {attempt})", flush=True)
        bad = verify_decompress(src)
        if not bad:
            print(f"[{name}] every chunk decompresses", flush=True)
            break
        print(f"[{name}] {len(bad)} chunk(s) fail to decompress, e.g. {[str(b.relative_to(src)) for b in bad[:3]]}: re-downloading", flush=True)
        for b in bad:
            b.unlink(missing_ok=True)
    else:
        raise RuntimeError(f"{name}: chunks still corrupted after 3 passes")
    for path, size in listing:
        p = src / path[len(prefix):]
        assert p.is_file() and p.stat().st_size == size, f"mismatch for {path}"
    n_local = sum(1 for p in src.rglob("*") if p.is_file())
    assert n_local == len(listing), f"{name}: {n_local} local files != {len(listing)} listed"
    tsha, per_file = tree_sha256(src)
    tar_bytes = deterministic_tar(src, name, listing, prefix)
    tar_name = f"{name}_labels.tar"
    (out / tar_name).write_bytes(tar_bytes)
    tar_sha = hashlib.sha256(tar_bytes).hexdigest()
    dest = data_dir / family / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"[{name}] tree_sha256={tsha} tar={tar_name} ({len(tar_bytes)} bytes) tar_sha256={tar_sha}", flush=True)
    return {
        "family": family, "segment": name, "source_prefix": prefix, "source_api": API + segment,
        "file_count": len(listing), "byte_total": total, "tree_sha256": tsha,
        "tar_name": tar_name, "tar_bytes": len(tar_bytes), "tar_sha256": tar_sha,
        "tar_layout": f"{name}/{name}_inklabels.zarr/..., {name}/{name}_supervision_mask.zarr/..., {name}/{name}_validation_mask.zarr/... (if present)",
        "local_copy": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "files": [{"path": p, "size": s, "sha256": per_file[p[len(prefix):]]} for p, s in listing],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", default="e02-r01")
    ap.add_argument("--segments", nargs="+", required=True, help="<family>/<segment>, e.g. aligned-scrollprizeorg-21slices/pherc0814-46527")
    ap.add_argument("--user", default="matteopontesilli", help="Kaggle username that will own the dataset")
    ap.add_argument("--slug", default=None, help="dataset slug (default papyruslab-<run-id>-labels)")
    ap.add_argument("--workers", type=int, default=4, help="parallel downloads (Hugging Face rate-limits anonymous requests)")
    ap.add_argument("--data-dir", default=str(ROOT / "data" / "labels"))
    a = ap.parse_args()
    run_dir = ROOT / "runs" / a.run_id.upper()
    stage, out = run_dir / "dataset-labels-stage", run_dir / "dataset-labels"
    out.mkdir(parents=True, exist_ok=True)
    slug = a.slug or f"papyruslab-{a.run_id}-labels"
    segments = {}
    for seg in a.segments:
        segments[seg.split("/", 1)[1]] = build_segment(seg, stage, out, Path(a.data_dir), a.workers)
    manifest = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_resolve_base": RESOLVE, "source_dataset_readme": "https://huggingface.co/buckets/scrollprize/datasets/tree/ink_9um",
        "tree_sha256_definition": "sha256 over sorted lines 'relpath\\nsha256(file)\\n', relpath relative to <segment>/",
        "segments": segments,
        "note": "Labels only; CT data are not included. Built by scripts/build_label_dataset.py for PapyrusLab E02.",
    }
    with open(out / "manifest.json", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=1) + "\n")
    with open(out / "dataset-metadata.json", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"title": f"PapyrusLab {a.run_id.upper()} ink_9um labels", "id": f"{a.user}/{slug}",
                             "licenses": [{"name": "other"}]}, indent=2) + "\n")
    print(f"dataset folder ready: {out}")
    for name, s in segments.items():
        print(f"  {name}: files={s['file_count']} bytes={s['byte_total']} tree_sha256={s['tree_sha256']} tar_sha256={s['tar_sha256']}")


if __name__ == "__main__":
    main()
