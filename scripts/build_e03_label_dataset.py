#!/usr/bin/env python3
"""Build the E03 label dataset: the two development segments only.

The E02 label dataset (papyruslab-e02-r01-labels) also holds pherc1667-w029: mounting it would bring the sealed
artefact inside every notebook's perimeter, and the generated guard would fail the run (review R2, finding 1).
E03 therefore publishes its own dataset, built from the local copies already verified in E02, using the frozen
helpers of scripts/build_label_dataset.py (imported, never modified). Nothing is downloaded: the local labels
are checked against the fingerprints frozen in configs/e02/datasets.json, and the deterministic tars come out
byte-identical to E02's -- which is the proof that this is the same content, minus the sealed segment.

The manifest carries the same schema the reused E02 notebook cell expects, per-file listing included: without
`segments.<seg>.files` that cell stops with a KeyError (run prep-w016-z13 v2, 7 September 2026).

Usage:
  python scripts/build_e03_label_dataset.py [--out runs/E03-R01/dataset-labels]
Then:
  python scripts/kaggle_e03.py publish-labels
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_label_dataset as bld  # noqa: E402  (frozen E02 helper: tree_sha256, deterministic_tar)

FAMILY = "aligned-scrollprizeorg-21slices"
SEGMENTS = ["pherc0814-46527", "pherc0139-w016"]          # i due di sviluppo, mai il sigillato
SEALED = "pherc1667-w029"
TITLE = "PapyrusLab E03-R01 labels (dev segments)"        # <= 50 caratteri: Kaggle rifiuta oltre
SLUG = "papyruslab-e03-r01-labels"


def build(out: Path, data_dir: Path, owner: str = "matteopontesilli") -> dict:
    frozen = json.loads((ROOT / "configs" / "e02" / "datasets.json").read_text(encoding="utf-8"))["labels"]["segments"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    manifest = {
        "run_id": "e03-r01",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("solo i due segmenti di sviluppo; il dataset delle label di E02 ne contiene un terzo, sigillato "
                 "fino a E05, che non va montato in E03 (revisione R2, finding 1)"),
        "segments": {},
    }
    for name in SEGMENTS:
        src = data_dir / FAMILY / name
        if not src.is_dir():
            raise SystemExit(f"copia locale assente: {src}")
        prefix = f"ink_9um/labels/{FAMILY}/{name}/"
        tsha, per_file = bld.tree_sha256(src)
        listing = sorted((prefix + rel, (src / rel).stat().st_size) for rel in per_file)
        tar_bytes = bld.deterministic_tar(src, name, listing, prefix)
        tar_name = f"{name}_labels.tar"
        (out / tar_name).write_bytes(tar_bytes)
        tar_sha = hashlib.sha256(tar_bytes).hexdigest()
        exp = frozen[name]
        if tsha != exp["tree_sha256"] or tar_sha != exp["tar_sha256"]:
            raise SystemExit(f"STOP: {name} non coincide con le impronte congelate di E02 "
                             f"(tree {tsha[:16]}…, tar {tar_sha[:16]}…)")
        if (len(listing), sum(s for _, s in listing)) != (exp["file_count"], exp["byte_total"]):
            raise SystemExit(f"STOP: {name} ha conteggi diversi da quelli congelati")
        manifest["segments"][name] = {
            "family": FAMILY, "segment": name, "source_prefix": prefix,
            "file_count": len(listing), "byte_total": sum(s for _, s in listing), "tree_sha256": tsha,
            "tar_name": tar_name, "tar_bytes": len(tar_bytes), "tar_sha256": tar_sha,
            "tar_layout": (f"{name}/{name}_inklabels.zarr/..., {name}/{name}_supervision_mask.zarr/..., "
                           f"{name}/{name}_validation_mask.zarr/..."),
            "files": [{"path": p, "size": s, "sha256": per_file[p[len(prefix):]]} for p, s in listing],
        }
        print(f"{name}: {len(listing)} file, {sum(s for _, s in listing)} byte, tree e tar identici a E02")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (out / "dataset-metadata.json").write_text(json.dumps(
        {"title": TITLE, "id": f"{owner}/{SLUG}", "licenses": [{"name": "other"}]}, indent=2) + "\n", encoding="utf-8")
    listed = [f["path"] for s in manifest["segments"].values() for f in s["files"]]
    if any(SEALED in p for p in listed) or SEALED in manifest["segments"]:
        raise SystemExit("STOP: il segmento sigillato compare nel dataset")
    if any(SEALED in p.name for p in out.rglob("*")):
        raise SystemExit("STOP: un file del dataset nomina il segmento sigillato")
    print(f"pronto: {out} ({len(listed)} file elencati, nessuno del segmento sigillato)")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "runs" / "E03-R01" / "dataset-labels")
    ap.add_argument("--data-dir", type=Path, default=ROOT / "data" / "labels")
    a = ap.parse_args(argv)
    build(a.out, a.data_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
