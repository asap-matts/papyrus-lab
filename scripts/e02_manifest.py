#!/usr/bin/env python3
"""Assemble the E02-R01 manifest from the verified run downloads (plan step 9).

Reads, for every run mode, the latest download folder under runs/E02-R01/<mode>/<timestamp>/ (only folders whose
SHA256SUMS was verified by scripts/kaggle_e02.py output), the local metrics in runs/E02-R01/metrics/, the label
manifest, configs/e02/*.json and the geometry JSONs, and writes docs/reports/<date>-e02-r01-manifest.json.
Nothing here reads a prediction: the sealed segment (pherc1667-w029) is reported from its training-only metrics.

Usage:
  python scripts/e02_manifest.py --out docs/reports/2026-09-07-e02-r01-manifest.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_e02_notebooks as gen  # noqa: E402

RUNS = ROOT / "runs" / "E02-R01"
# Kaggle kernel versions actually executed (from the pilot's push output, recorded during execution)
KAGGLE_VERSIONS = {
    "prep-46527": {"v1": "error: asciitree missing (install cell)", "v2": "complete"},
    "prep-w016": {"v1": "complete"}, "prep-w029": {"v1": "complete"},
    "infer-46527-seed42": {"v1": "error: orientation gate not evaluable before amendment A1 (outputs persisted)", "v2": "complete"},
    "infer-w016-seed42": {"v1": "complete"}, "infer-w029-seed42": {"v1": "complete"},
    "infer-46527-seed43": {"v1": "complete"}, "infer-w016-seed43": {"v2": "complete (v1 pushed by an interrupted command, identical notebook)"},
    "infer-w029-seed43": {"v1": "complete"},
}
# R02 docs/14 (khj1222/vesuvius-challenge @ 13920ba), best F1 at step 75k; held-out of w029 is compared only in E05
R02_BEST_F1 = {
    "pherc0139-w016": {"seed42": {"held": 0.531, "train": 0.984}, "seed43": {"held": 0.755, "train": 0.985}},
    "pherc0814-46527": {"seed42": {"held": 0.753, "train": 0.989}, "seed43": {"held": 0.740, "train": 0.988}},
    "pherc1667-w029": {"seed42": {"held": None, "train": 0.986}, "seed43": {"held": None, "train": 0.983}},
}
TOLERANCE = {"concordante": 0.03, "anomalo": 0.10}


def latest(mode: str) -> Path | None:
    base = RUNS / mode
    if not base.is_dir():
        return None
    c = sorted(p for p in base.iterdir() if p.is_dir() and (p / "e02" / "out" / "SHA256SUMS").exists())
    return c[-1] if c else None


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def run_info(d: Path) -> dict:
    txt = (d / "e02" / "logs" / "run_info.txt").read_text(encoding="utf-8")
    start = re.search(r"start=(\S+)", txt); end = re.search(r"end=(\S+)", txt)
    sums = [l.split(None, 1) for l in (d / "e02" / "out" / "SHA256SUMS").read_text(encoding="utf-8").splitlines() if l.strip()]
    return {"download_folder": str(d.relative_to(ROOT)).replace("\\", "/"), "start_utc": start.group(1) if start else None,
            "end_utc": end.group(1) if end else None, "files_persisted": len(sums),
            "sha256sums": {p.strip().lstrip("*"): h for h, p in sums}}


SEALED = "pherc1667-w029"
KEEP = ("stratum", "region", "n_px", "n_ink", "ink_fraction", "auroc", "best_f1", "at_threshold")


def summarize_sets(rep: dict) -> dict:
    out = {}
    for name, s in rep.get("sets", {}).items():
        row = {"n_px": s["n_px"], "n_ink": s["n_ink"], "ink_fraction": s["ink_fraction"], "trivial_floor": s["trivial_floor"],
               "auroc": s["auroc"], "best_f1": s["best_f1"], "at_threshold": s.get("at_threshold"),
               "median_ink": s.get("median_ink"), "median_background": s.get("median_background")}
        if "orientation" in s:
            row["orientation"] = s["orientation"]
        if "strata" in s:
            row["within_patch"] = s["within_patch"]; row["within_two_patches"] = s["within_two_patches"]
            row["strata"] = [{k: v for k, v in st.items() if k in KEEP} for st in s["strata"]]
            row["regions"] = [{k: v for k, v in r.items() if k in KEEP} for r in s["regions"]]
        out[name] = row
    return out


def sha256_file(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate_reports(seg: str, seed: int, kaggle_rep: dict, local_rep: dict | None, compare: dict | None,
                     sums: dict, kaggle_metrics_sha256: str, threshold: int | None) -> None:
    """Refuse, before anything is written, every inconsistency that would break the identity chain or the seal
    (review R3, finding 1). Raises ValueError with the reason."""
    tif = f"out/{seg}_seed{seed}_step075000.tif"
    mjson = f"out/metrics_{seg}_seed{seed}.json"
    if sums.get(mjson) != kaggle_metrics_sha256:
        raise ValueError(f"{seg} seed{seed}: the Kaggle metrics JSON does not match SHA256SUMS ({sums.get(mjson)} vs {kaggle_metrics_sha256})")
    if sums.get(tif) != kaggle_rep.get("sha256_pred"):
        raise ValueError(f"{seg} seed{seed}: TIFF hash in SHA256SUMS ({sums.get(tif)}) differs from the Kaggle report ({kaggle_rep.get('sha256_pred')})")
    if local_rep is not None and local_rep.get("sha256_pred") != kaggle_rep.get("sha256_pred"):
        raise ValueError(f"{seg} seed{seed}: local report computed on a different TIFF ({local_rep.get('sha256_pred')})")
    if local_rep is not None and threshold is not None and local_rep.get("threshold_arg") != threshold:
        raise ValueError(f"{seg} seed{seed}: local report not computed at the frozen threshold {threshold} (threshold_arg={local_rep.get('threshold_arg')})")
    if seg == SEALED:
        for name, rep in (("kaggle", kaggle_rep), ("local", local_rep)):
            if rep is None:
                continue
            if "held" in rep.get("sets", {}) or "held" in (rep.get("sets_requested") or []):
                raise ValueError(f"{seg}: the {name} report contains the held-out set: seal violated")
        if compare and any("held" in k for k in compare):
            raise ValueError(f"{seg}: compare_seeds contains held-out comparisons: seal violated")


def classify(delta: float | None) -> str | None:
    if delta is None:
        return None
    a = abs(delta)
    return "concordante" if a <= TOLERANCE["concordante"] else ("anomalo" if a <= TOLERANCE["anomalo"] else "fallito")


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    ds = read_json(ROOT / "configs" / "e02" / "datasets.json")
    baseline = read_json(ROOT / "configs" / "e02" / "baseline.json")
    split = read_json(ROOT / "configs" / "e02" / "split.json")
    inventory = read_json(ROOT / "configs" / "e02" / "ink9um_inventory.json")
    label_manifest = read_json(RUNS / "dataset-labels" / "manifest.json")

    runs, replica, missing, checked_seal = {}, [], [], []
    for mode in gen.modes():
        d = latest(mode)
        if d is None:
            missing.append(mode); continue
        kind, seg, seed = gen.parse_mode(mode)
        info = run_info(d)
        info["kaggle_versions"] = KAGGLE_VERSIONS.get(mode)
        info["install"] = read_json(d / "e02" / "logs" / "install.json")
        info["villa_commit"] = (d / "e02" / "logs" / "villa_commit.txt").read_text(encoding="utf-8").strip() if (d / "e02" / "logs" / "villa_commit.txt").exists() else None
        if kind == "prep":
            m = read_json(d / "e02" / "out" / f"prep_manifest_{seg}.json")
            info["prep"] = {k: m[k] for k in ("shape", "file_count", "byte_total", "tree_sha256", "tar_name", "tar_bytes", "tar_sha256", "zero_fraction_plane10", "prepare_script_sha256")}
            info["prep"]["attrs"] = m["attrs"]
            log = (d / "e02" / "logs" / f"prep_{seg}.log").read_text(encoding="utf-8", errors="replace")
            mm = re.search(r"exit_code=(\d+) durata_s=(\d+)", log); info["prep"]["exit_code"], info["prep"]["duration_s"] = (int(mm.group(1)), int(mm.group(2))) if mm else (None, None)
        else:
            k = read_json(d / "e02" / "out" / f"metrics_{seg}_seed{seed}.json")
            local = read_json(RUNS / "metrics" / f"{seg}_seed{seed}.json")
            cmp = read_json(d / "e02" / "out" / f"compare_seeds_{seg}.json")
            validate_reports(seg, seed, k, local, cmp, info["sha256sums"],
                             sha256_file(d / "e02" / "out" / f"metrics_{seg}_seed{seed}.json"), baseline.get("threshold_dev"))
            checked_seal.append(seg == SEALED)
            log = (d / "e02" / "logs" / f"infer_seed{seed}.log").read_text(encoding="utf-8", errors="replace")
            mm = re.search(r"exit_code=(\d+) durata_s=(\d+) causa=(\S+)", log)
            info["inference"] = {"exit_code": int(mm.group(1)), "duration_s": int(mm.group(2)), "cause": mm.group(3)} if mm else None
            info["layer_indices_ok"] = "Selected source layer indices=" + str(gen.LAYER_INDICES) in log
            info["gpu_peak_mib"] = (d / "e02" / "logs" / f"gpu_peak_seed{seed}.json").read_text(encoding="utf-8").strip()
            info["checkpoints_sha256"] = (d / "e02" / "logs" / "checkpoints_sha256.txt").read_text(encoding="utf-8").strip().splitlines()
            info["label_count"] = (d / "e02" / "logs" / "label_count.txt").read_text(encoding="utf-8").strip()
            info["guard"] = read_json(d / "e02" / "logs" / "guard.json")
            info["metrics_kaggle"] = {"version": k["version"], "gate_A": k["gate_A"], "gate_B": k["gate_B"], "sha256_pred": k["sha256_pred"], "shape": k["shape"],
                                     "sets_requested": k["sets_requested"], "disjoint_check": k["disjoint_check"], "sets": summarize_sets(k)}
            info["metrics_local"] = {"version": local["version"], "sha256_pred": local["sha256_pred"], "sets": summarize_sets(local),
                                     "auroc_equal_to_kaggle": {n: local["sets"][n]["auroc"] == k["sets"][n]["auroc"] for n in local["sets"]}} if local else None
            info["sealed_held_out"] = (seg == SEALED)
            if cmp:
                info["compare_seeds"] = cmp
            for name, s in k["sets"].items():
                ref = R02_BEST_F1[seg][f"seed{seed}"][name]
                delta = (s["best_f1"]["f1"] - ref) if ref is not None else None
                replica.append({"segment": seg, "seed": seed, "set": name, "ours_best_f1": s["best_f1"]["f1"], "r02_best_f1": ref,
                                "delta": delta, "class": classify(delta), "in_criterion_C": (seed == 42)})
        runs[mode] = info

    geometry = {}
    for seg in gen.SEGMENTS:
        g = read_json(ROOT / "docs" / "reports" / f"2026-09-07-e02-geometry-{seg}.json")
        if g:
            geometry[seg] = {k: g["geometry"][k] for k in ("annotated_regions", "n_px_held", "n_px_train", "held_share_of_annotation",
                                                         "regions_mixing_held_and_training", "within_patch", "within_two_patches", "distance_stats", "n_px_held_and_train", "regions_held")}

    manifest = {
        "experiment": "E02-R01", "plan": "docs/plans/2026-09-06-e02-costruire-il-metro.md",
        "commits_papyruslab": {"plan_frozen": "68bc1b8", "steps_1_3_partner_base": "337d4a4", "generator": "5a2ad9a", "labels_geometry": "21065df",
                               "amendment_A1": "aab84dd", "review_R2": "d6da61a", "manifest_head": git("rev-parse", "--short", "HEAD")},
        "baseline": baseline, "split": split, "datasets_kaggle": ds,
        "inventory_counts": inventory["counts"], "inventory_sources": inventory["sources"], "contract_physical_key_mismatch": inventory["contract_physical_key_mismatch"],
        "labels": {seg: {k: v for k, v in s.items() if k != "files"} for seg, s in label_manifest["segments"].items()} if label_manifest else None,
        "mask_geometry": geometry,
        "partner_tasks": {"branch": "e02-socio", "commit": "007f653", "S1": "geometry JSONs byte-identical to ours; 0814 and w029 identical to R02 docs/17, w016 differs (dataset side)",
                          "S2": "pooled input of pherc0814-46527 tree_sha256 bc742343... on the Mac, identical to the laptop and to Kaggle prep-46527"},
        "runs": runs, "runs_missing": missing,
        "replica_R02": replica,
        "criterion_C_decision": "Matteo, 2026-09-07: concordante on held-out (2/2) and on training of 0814 and w029; anomalo on training of w016 (delta -0.032), cause attributed to the w016 masks (geometry differs from R02 for both operators; bucket files unchanged since 2026-08-18); meter not blocked",
        "sealed_segment": {"segment": SEALED, "reports_checked": int(sum(checked_seal)),
                           "held_out_pixels_read_in_E02": False if sum(checked_seal) >= 2 else None,      # attested only after both w029 reports passed validate_reports
                           "opened_in": "E05"},
        "frozen_threshold_used_in_local_reports": baseline.get("threshold_dev"),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"manifest -> {a.out} ({a.out.stat().st_size} byte); run presenti: {len(runs)}; mancanti: {missing}")
    for r in replica:
        print(f"  {r['segment']:16s} seed{r['seed']} {r['set']:5s} ours={r['ours_best_f1']:.3f} r02={r['r02_best_f1']} delta={r['delta'] if r['delta'] is None else round(r['delta'], 3)} -> {r['class']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
