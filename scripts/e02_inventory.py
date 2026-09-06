#!/usr/bin/env python3
"""Inventory of the ink_9um training set from three primary sources (E02, plan step 1).

Sources, all fetched live and recorded with SHA-256 or counts:
  (a) the dataset README in the Hugging Face bucket (label name -> public segment -> source volume);
  (b) villa's training contract aligned21_fixed_scroll_prior.json at the frozen commit (29 representations);
  (c) the paginated bucket listing of ink_9um/labels (files, bytes, arrays per segment);
plus the OME-Zarr metadata of every source volume on S3 and of every label array.

Every disagreement between the sources is an assertion. The generated Markdown table is compared
row by row with the table frozen in the plan (section 2.2). `--check FILE` regenerates and compares.

Usage:
  python scripts/e02_inventory.py --out configs/e02/ink9um_inventory.json
  python scripts/e02_inventory.py --check configs/e02/ink9um_inventory.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "papyruslab-e02"
README_URL = "https://huggingface.co/buckets/scrollprize/datasets/resolve/ink_9um/README.md"
VILLA_COMMIT = "3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e"
CONTRACT_URL = (
    f"https://raw.githubusercontent.com/ScrollPrize/villa/{VILLA_COMMIT}"
    "/ink-detection/configs/aligned21_fixed_scroll_prior.json"
)
BUCKET_API = "https://huggingface.co/api/buckets/scrollprize/datasets/tree/ink_9um/labels"
BUCKET_RESOLVE = "https://huggingface.co/buckets/scrollprize/datasets/resolve/"
S3 = "https://vesuvius-challenge-open-data.s3.amazonaws.com/"
FAMILY = {"aligned": "aligned-scrollprizeorg-21slices", "native": "native9-scrollprizeorg-21slices"}
LEVEL_USED = {"aligned": "2", "native": "0"}      # pyramid level the models consume (model card / README)
LABEL_DEPTH = {"aligned": 21, "native": 28}
PLAN = ROOT / "docs" / "plans" / "2026-09-06-e02-costruire-il-metro.md"
CACHE = ROOT / "runs" / "E02-R01" / "inventory"

EXPECTED_DUAL = {
    "20260317000000-w035_2026031718", "20260302000000-w039_2026030210", "20250831000000-w040_2025083102",
    "20260108000000-w041_2026010816", "20260115000000-w044_2026011522",
}
EXPECTED_VALIDATION = {"pherc0139-w016", "pherc0814-46527", "pherc1667-w029"}
KNOWN_DUPLICATES_OUTSIDE_TRAINING = [{
    "scroll_dir": "PHerc0139", "public_segment": "20260325000000-w046_20260325",
    "duplicate_of": "20260126000000-w045_2026012619",
    "source": "villa issue #1547 (2026-08-20): valid masks identical, 81.4975% of vertices bit-identical",
    "evidence_level": "L1",
}]
VOLATILE_KEYS = {"generated_at", "fetched_at"}


# ------------------------------------------------------------------------------------------ network
def fetch(url: str, retries: int = 6, timeout: int = 120) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as ex:
            if ex.code == 404:
                raise
            last = ex
        except Exception as ex:  # noqa: BLE001 - transient network errors
            last = ex
        time.sleep(min(60, 5 * 2 ** attempt))
    raise RuntimeError(f"fetch failed for {url}: {last}")


def fetch_json(url: str) -> dict:
    return json.loads(fetch(url).decode("utf-8"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------------------------------ sources
def parse_readme(text: str) -> dict[str, dict]:
    """Return {label_name: {family, scroll_label, scroll_dir, public_segment, zarr, source_volume_url}}."""
    head, _, native_part = text.partition("Native 9.362")
    row = re.compile(r"^\|\s*([A-Za-z0-9_.-]+)\s*\|\s*([^|]+?)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|", re.M)
    out: dict[str, dict] = {}
    for family, part in (("aligned", head), ("native", native_part)):
        for name, scroll_label, link_text, url in row.findall(part):
            if name.lower() == "segment":
                continue
            m = re.search(r"#([^/]+)/segments/([^/]+)/surface-volumes/([^/]+)/?$", url)
            assert m, f"README link not understood for {name}: {url}"
            scroll_dir, public_segment, zarr = m.groups()
            out[name] = {
                "family": family, "scroll_label": scroll_label.strip(), "scroll_dir": scroll_dir,
                "public_segment": public_segment, "zarr": zarr,
                "source_volume_url": f"{S3}{scroll_dir}/segments/{public_segment}/surface-volumes/{zarr}",
                "readme_link_text": link_text.strip(),
            }
    return out


def list_bucket(use_cache: bool) -> list[tuple[str, int]]:
    cache = CACHE / "bucket_listing.json"
    if use_cache and cache.exists():
        return [tuple(x) for x in json.loads(cache.read_text(encoding="utf-8"))]
    files, url, pages = [], BUCKET_API, 0
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            files += [(e["path"], int(e.get("size", 0))) for e in json.load(r) if e.get("type") == "file"]
            m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", "") or "")
            url = m.group(1) if m else None
        pages += 1
        assert pages <= 2000, "bucket listing did not terminate"
    files.sort()
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(files), encoding="utf-8")
    return files


def group_bucket(files: list[tuple[str, int]]) -> dict[str, dict[str, dict]]:
    """{family_key: {segment: {file_count, byte_total, arrays}}}"""
    groups: dict[str, dict[str, dict]] = {"aligned": {}, "native": {}}
    fam_of = {v: k for k, v in FAMILY.items()}
    for path, size in files:
        parts = path.split("/")            # ink_9um/labels/<family>/<seg>/<array>.zarr/...
        assert parts[:2] == ["ink_9um", "labels"], path
        fam, seg = fam_of[parts[2]], parts[3]
        g = groups[fam].setdefault(seg, {"file_count": 0, "byte_total": 0, "arrays": set()})
        g["file_count"] += 1
        g["byte_total"] += size
        if len(parts) >= 5 and parts[4].endswith(".zarr"):
            g["arrays"].add(parts[4][len(seg) + 1:-5])      # "<seg>_inklabels.zarr" -> "inklabels"
    for fam in groups.values():
        for g in fam.values():
            g["arrays"] = sorted(g["arrays"])
    return groups


def zarr_level(url_base: str, level: str) -> dict:
    a = fetch_json(f"{url_base}/{level}/.zarray")
    comp = a.get("compressor")
    return {"shape": a["shape"], "chunks": a["chunks"], "dtype": a["dtype"],
            "compressor": comp.get("id") if isinstance(comp, dict) else None}


def scale_of(zattrs: dict, level: str) -> list | None:
    for ms in zattrs.get("multiscales", []):
        for ds in ms.get("datasets", []):
            if str(ds.get("path")) == level:
                for t in ds.get("coordinateTransformations", []):
                    if t.get("type") == "scale":
                        return t.get("scale")
    return None


# ------------------------------------------------------------------------------------------ build
def build(use_cache: bool) -> dict:
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    readme_bytes = fetch(README_URL)
    readme = parse_readme(readme_bytes.decode("utf-8"))
    contract_bytes = fetch(CONTRACT_URL)
    contract = json.loads(contract_bytes.decode("utf-8"))
    listing = list_bucket(use_cache)
    bucket = group_bucket(listing)

    readme_by_family = {f: {k for k, v in readme.items() if v["family"] == f} for f in FAMILY}
    contract_by_family = {
        "aligned": {r["segment"] for r in contract["representations"] if r["source_family"] == "public_2p4_level2_zmean4"},
        "native": {r["segment"] for r in contract["representations"] if r["source_family"] == "native_9p362_level0"},
    }
    for fam in FAMILY:
        assert readme_by_family[fam] == contract_by_family[fam] == set(bucket[fam]), (
            f"{fam}: README {sorted(readme_by_family[fam])} / contract {sorted(contract_by_family[fam])} / "
            f"bucket {sorted(bucket[fam])} differ")
    assert len(readme_by_family["aligned"]) == 24 and len(readme_by_family["native"]) == 5, "expected 24 + 5"
    contract_keys = {r["segment"]: r for r in contract["representations"]}

    representations = []
    for name, info in sorted(readme.items(), key=lambda kv: (kv[1]["family"], kv[0])):
        fam = info["family"]
        level = LEVEL_USED[fam]
        vol_attrs = fetch_json(f"{info['source_volume_url']}/.zattrs")
        levels = {"0": zarr_level(info["source_volume_url"], "0")}
        if level != "0":
            levels[level] = zarr_level(info["source_volume_url"], level)
        label_base = f"{BUCKET_RESOLVE}ink_9um/labels/{FAMILY[fam]}/{name}/{name}_inklabels.zarr"
        label_attrs = fetch_json(f"{label_base}/.zattrs")
        label0 = zarr_level(label_base, "0")
        b = bucket[fam][name]
        assert label0["shape"][1:] == levels[level]["shape"][1:], (
            f"{name}: label {label0['shape']} vs volume level {level} {levels[level]['shape']}")
        assert label0["shape"][0] == LABEL_DEPTH[fam], f"{name}: label depth {label0['shape'][0]}"
        assert {"inklabels", "supervision_mask"} <= set(b["arrays"]), f"{name}: arrays {b['arrays']}"
        rep = {
            "label_name": name, "family": FAMILY[fam], "family_key": fam,
            "scroll_label": info["scroll_label"], "scroll_dir": info["scroll_dir"],
            "public_segment": info["public_segment"], "source_zarr": info["zarr"],
            "source_volume_url": info["source_volume_url"], "source_level_used": level,
            "volume_num_slices": vol_attrs.get("num_slices"), "volume_axes": vol_attrs.get("note_axes_order"),
            "volume_scale_um_at_level": scale_of(vol_attrs, level), "volume_levels": levels,
            "label_shape": label0["shape"], "label_chunks": label0["chunks"], "label_dtype": label0["dtype"],
            "label_compressor": label0["compressor"], "label_arrays": b["arrays"],
            "label_file_count": b["file_count"], "label_byte_total": b["byte_total"],
            "has_validation_mask": "validation_mask" in b["arrays"],
            "annotation_center_channel": label_attrs.get("annotation_center_channel"),
            "source_z_slice": label_attrs.get("source_z_slice"),
            "label_format": label_attrs.get("format"),
            "contract_physical_key": contract_keys[name]["physical_segment_key"],
            "contract_representation_key": contract_keys[name]["representation_key"],
            "contract_scroll": contract_keys[name]["scroll"],
        }
        representations.append(rep)
        print(f"  {name:20s} {fam:8s} {info['scroll_dir']}/{info['public_segment']:45s} label {label0['shape']} files {b['file_count']}", flush=True)

    physical: dict[tuple[str, str], list[str]] = {}
    for r in representations:
        physical.setdefault((r["scroll_dir"], r["public_segment"]), []).append(r["label_name"])
    assert len(physical) == 24, f"physical segments: {len(physical)}"
    dual = {seg for (_, seg), names in physical.items() if len(names) == 2}
    assert dual == EXPECTED_DUAL, f"dual representations: {sorted(dual)}"
    assert all(len(n) <= 2 for n in physical.values())
    validation = {r["label_name"] for r in representations if r["has_validation_mask"]}
    assert validation == EXPECTED_VALIDATION, f"validation masks: {sorted(validation)}"
    mismatch = []
    for (sd, seg), names in sorted(physical.items()):
        keys = {contract_keys[n]["physical_segment_key"] for n in names}
        if len(keys) > 1:
            mismatch.append({"scroll_dir": sd, "public_segment": seg, "label_names": names, "contract_keys": sorted(keys)})

    inventory = {
        "generated_at": fetched_at,
        "plan": str(PLAN.relative_to(ROOT)).replace("\\", "/"),
        "sources": {
            "readme": {"url": README_URL, "sha256": sha256(readme_bytes), "bytes": len(readme_bytes), "fetched_at": fetched_at},
            "villa_contract": {"url": CONTRACT_URL, "commit": VILLA_COMMIT, "sha256": sha256(contract_bytes), "bytes": len(contract_bytes), "fetched_at": fetched_at},
            "bucket_listing": {"api": BUCKET_API, "file_count": len(listing), "byte_total": sum(s for _, s in listing), "fetched_at": fetched_at},
            "open_data_s3": {"base": S3, "fetched_at": fetched_at},
        },
        "counts": {"representations": len(representations), "physical_segments": len(physical), "dual_representations": len(dual),
                   "validation_mask_segments": len(validation),
                   "scrolls": sorted({r["scroll_dir"] for r in representations})},
        "representations": representations,
        "physical_segments": [{"scroll_dir": sd, "public_segment": seg, "label_names": names,
                               "has_validation_mask": any(r["has_validation_mask"] for r in representations if r["label_name"] in names)}
                              for (sd, seg), names in sorted(physical.items())],
        "dual_representations": sorted(dual),
        "validation_mask_segments": sorted(validation),
        "contract_physical_key_mismatch": mismatch,
        "known_physical_duplicates_outside_training": KNOWN_DUPLICATES_OUTSIDE_TRAINING,
        "traps": [
            "label names pherc0139-wNNN do not follow the public w-numbering (w016->w029, w017->w030, w028->w044, w029->w045)",
            "five physical segments appear in two representations (aligned 2.4 um pooled and native 9.362 um)",
            "villa's contract shares one physical budget for four dual pairs but not for pherc0139-w028 / w044 (same public segment)",
        ],
    }
    return inventory


# ------------------------------------------------------------------------------------------ table
def markdown_rows(inv: dict) -> list[tuple[str, str, str, str, str]]:
    """(public_segment, scroll_dir, aligned_label or '', native_label or '', 'si'|'no')."""
    rows = []
    reps = {r["label_name"]: r for r in inv["representations"]}
    for p in inv["physical_segments"]:
        aligned = [n for n in p["label_names"] if reps[n]["family_key"] == "aligned"]
        native = [n for n in p["label_names"] if reps[n]["family_key"] == "native"]
        rows.append((p["public_segment"], p["scroll_dir"], aligned[0] if aligned else "", native[0] if native else "",
                     "si" if p["has_validation_mask"] else "no"))
    return sorted(rows)


def plan_rows() -> list[tuple[str, str, str, str, str]]:
    text = PLAN.read_text(encoding="utf-8")
    sec = text.split("### 2.2", 1)[1].split("Le tre trappole", 1)[0]
    rows = []
    for line in sec.splitlines():
        m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*(\S+)\s*\|\s*(`[^`]+`|—)\s*\|\s*(`[^`]+`|—)\s*\|\s*(\*\*sì\*\*|no)\s*\|", line)
        if not m:
            continue
        pub, scroll, al, na, val = m.groups()
        rows.append((pub, scroll, al.strip("`") if al != "—" else "", na.strip("`") if na != "—" else "",
                     "si" if "sì" in val else "no"))
    return rows


def rows_match(plan_row, gen_row) -> bool:
    pub_plan, *rest_plan = plan_row
    pub_gen, *rest_gen = gen_row
    if "…" in pub_plan:
        head, tail = pub_plan.split("…", 1)
        ok = pub_gen.startswith(head) and pub_gen.endswith(tail)
    else:
        ok = pub_plan == pub_gen
    return ok and rest_plan == rest_gen


def compare_with_plan(inv: dict) -> None:
    gen = markdown_rows(inv)
    plan = plan_rows()
    assert len(plan) == 24, f"plan table has {len(plan)} rows"
    unmatched = [p for p in plan if not any(rows_match(p, g) for g in gen)]
    extra = [g for g in gen if not any(rows_match(p, g) for p in plan)]
    assert not unmatched and not extra, f"plan/inventory table differ: unmatched plan rows {unmatched}; extra generated rows {extra}"
    print("\n| Segmento pubblico | Rotolo | Label allineata | Label nativa | validation_mask |\n|---|---|---|---|---|")
    for pub, sd, al, na, val in gen:
        print(f"| `{pub}` | {sd} | {('`' + al + '`') if al else '—'} | {('`' + na + '`') if na else '—'} | {val} |")
    print(f"\ntabella: 24 righe, tutte coincidenti con il piano §2.2")


# ------------------------------------------------------------------------------------------ io
def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def strip_volatile(obj):
    if isinstance(obj, dict):
        return {k: strip_volatile(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [strip_volatile(v) for v in obj]
    return obj


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=None, help="write the inventory JSON here")
    ap.add_argument("--check", type=Path, default=None, help="regenerate and compare with this JSON (volatile keys excluded)")
    ap.add_argument("--use-cache", action="store_true", help="reuse runs/E02-R01/inventory/bucket_listing.json instead of re-listing")
    a = ap.parse_args()
    if not a.out and not a.check:
        ap.error("--out or --check required")
    inv = build(a.use_cache)
    compare_with_plan(inv)
    print(json.dumps(inv["counts"], indent=1), "\ncontract_physical_key_mismatch:", json.dumps(inv["contract_physical_key_mismatch"]))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(dumps(inv))
        print(f"scritto {a.out} ({a.out.stat().st_size} byte)")
    if a.check:
        old = json.loads(a.check.read_text(encoding="utf-8"))
        same = strip_volatile(old) == strip_volatile(inv)
        print("check:", "identico (chiavi volatili escluse)" if same else "DIVERSO")
        return 0 if same else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
