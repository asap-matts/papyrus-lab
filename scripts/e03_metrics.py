#!/usr/bin/env python3
"""E03 metrics: per-run reports with their identity, averages of two predictions, Spearman agreement.

Plan: docs/plans/2026-09-07-e03-tolleranza-offset-z.md (step 3). Three modes:

  --run PRED.tif      one point of the curve: wraps the frozen scripts/e02_metrics.py build_report() and adds
                      the `e03_point` block (segment, seed, k, hashes, source window, layer indices) so that a
                      renamed or duplicated file cannot silently move a point (review R1, finding 3).
  --average A.tif B.tif   a zero-GPU control: the mean of two predictions, evaluated WITHOUT rounding. The mean of
                      two uint8 has half points, so the sweep runs on the SUM (uint16, 0..510) and every threshold
                      is reported both as a sum and as a mean (sum/2). The frozen threshold 91 on the mean is
                      sum >= 182.
  --spearman A.tif B.tif  rank agreement between two predictions over the requested pixel sets.

Why the sweep is not imported from E02 (review R1, finding 1): scripts/e02_metrics.py is frozen at 256 levels --
`sweep` asserts a (256,) histogram and `at_threshold` does np.clip(t, 0, 255), so with an optimum above 255 it
would report a threshold whose statistics belong to 255. Verified with a counterexample on 2026-09-07. E03
therefore defines sweep_n / best_f1_n / at_threshold_n, with the same tie rule (lowest maximising threshold) and
the same single-quotient F1, and imports from E02 only what does not depend on the number of levels.

The seal of pherc1667-w029 does not depend on a folder name (review R1, finding 4): before any mask is read the
label directory must be in LABEL_ALLOWLIST *and* carry its frozen tree fingerprint.

Usage:
  python scripts/e03_metrics.py --run PRED.tif --labels DIR --out J --k -3 --seed 42 --threshold 91 \
      --input-tree-sha256 H --layer-indices 2,...,18 --source-z-slice 1,85 [--run-id E03-R01] [--sets held,train]
  python scripts/e03_metrics.py --average A.tif B.tif --labels DIR --out J --combination seedmean|zmean_m2p2 \
      [--seed 42] [--threshold-mean 91] [--sets held,train]
  python scripts/e03_metrics.py --spearman A.tif B.tif --labels DIR --out J [--sets held,train]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import e02_metrics as e02                     # frozen at version 1.2: imported, never modified
from tree_sha256 import tree_sha256

VERSION = "e03_metrics/1.0"
OFFSETS_PATH = ROOT / "configs" / "e03" / "offsets.json"

# Frozen fingerprints of the two development label folders (E02 manifest, verified on three machines).
# pherc1667-w029 (26cf3c17...) is deliberately absent: it is sealed until E05.
LABEL_ALLOWLIST = {
    "pherc0139-w016": "a62d3e0ecfc9305758fae3bc0d74d99ecf675bcf846aa910ee4a876ee26ccfd5",
    "pherc0814-46527": "5659236870d7d0408e330f05f6275bd821fc1d7bdea8c9c8f072dfd4ae8b54f0",
}


# ------------------------------------------------------------------------------------ level-agnostic sweep
def sweep_n(pos_hist, neg_hist) -> dict:
    """Precision/recall/F1/IoU at every threshold t of an arbitrary number of levels, 'predicted ink' = score >= t.
    Same shape as e02_metrics.sweep, without its 256-level assumption."""
    pos = np.asarray(pos_hist, dtype=np.int64)
    neg = np.asarray(neg_hist, dtype=np.int64)
    if pos.ndim != 1 or pos.shape != neg.shape:
        raise ValueError(f"histograms must be 1-D and of equal length, got {pos.shape} and {neg.shape}")
    tp = np.cumsum(pos[::-1])[::-1].astype(np.float64)
    fp = np.cumsum(neg[::-1])[::-1].astype(np.float64)
    total_pos, total_neg = float(pos.sum()), float(neg.sum())
    fn = total_pos - tp
    tn = total_neg - fp
    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(tp + fp > 0, tp / np.maximum(tp + fp, 1.0), 0.0)
        recall = np.where(total_pos > 0, tp / max(total_pos, 1.0), 0.0)
        denom = 2 * tp + fp + fn                       # F1 in a single quotient: exact plateaus (E02 R2, finding 2)
        f1 = np.where(denom > 0, 2 * tp / np.maximum(denom, 1.0), 0.0)
        iou = np.where(tp + fp + fn > 0, tp / np.maximum(tp + fp + fn, 1.0), 0.0)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall,
            "f1": f1, "iou": iou, "total_pos": total_pos, "total_neg": total_neg, "levels": int(pos.size)}


def at_threshold_n(sw: dict, t: int) -> dict:
    """Statistics AT the requested threshold. Refuses an out-of-range threshold instead of clipping it."""
    i = int(t)
    if not 0 <= i < sw["levels"]:
        raise ValueError(f"threshold {t} outside [0, {sw['levels'] - 1}]: refusing to report another threshold's numbers")
    out = {"threshold_sum": i, "tp": int(sw["tp"][i]), "fp": int(sw["fp"][i]), "fn": int(sw["fn"][i]),
           "tn": int(sw["tn"][i]), "precision": float(sw["precision"][i]), "recall": float(sw["recall"][i]),
           "f1": float(sw["f1"][i]), "iou": float(sw["iou"][i])}
    if sw["levels"] == 511:
        out["threshold_mean"] = i / 2 if i % 2 else i // 2
    return out


def best_f1_n(sw: dict) -> dict:
    """The LOWEST threshold among those maximising F1 (np.argmax returns the first maximum): same frozen tie rule."""
    i = int(np.argmax(sw["f1"]))
    out = at_threshold_n(sw, i)
    res = {"f1": out["f1"], "threshold": i, "precision": out["precision"], "recall": out["recall"], "iou": out["iou"]}
    if sw["levels"] == 511:
        res["threshold_sum"] = i
        res["threshold_mean"] = i / 2 if i % 2 else i // 2
    return res


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)


# ------------------------------------------------------------------------------------ seal (whitelist)
def check_labels_allowed(labels_dir: Path) -> str:
    """Fail-closed guard, called BEFORE any mask is opened: name in the allowlist AND frozen fingerprint."""
    labels_dir = Path(labels_dir)
    name = labels_dir.name
    if name not in LABEL_ALLOWLIST:
        raise ValueError(f"STOP: '{name}' non e' nella lista bianca dei segmenti di sviluppo "
                         f"{sorted(LABEL_ALLOWLIST)}: nessuna maschera viene aperta")
    digest, _ = tree_sha256(labels_dir)
    if digest != LABEL_ALLOWLIST[name]:
        raise ValueError(f"STOP: impronta delle label di '{name}' diversa da quella congelata "
                         f"({digest[:16]}… invece di {LABEL_ALLOWLIST[name][:16]}…): nessuna maschera viene aperta")
    return digest


# ------------------------------------------------------------------------------------ offsets
def load_offsets() -> dict:
    return json.loads(OFFSETS_PATH.read_text(encoding="utf-8"))


def offset_row(k: int) -> dict:
    for row in load_offsets()["offsets"]:
        if int(row["k"]) == int(k):
            return row
    raise ValueError(f"STOP: offset k={k} assente da configs/e03/offsets.json "
                     f"(ammessi: {[r['k'] for r in load_offsets()['offsets']]})")


# ------------------------------------------------------------------------------------ shared pieces
def _read(path: Path) -> np.ndarray:
    return e02.read_prediction(Path(path))


def _sum_of_two(paths) -> tuple[np.ndarray, list[dict]]:
    arrays, info = [], []
    for p in paths:
        p = Path(p)
        a = _read(p)
        if a.dtype != np.uint8:
            raise ValueError(f"STOP: {p} is not uint8")
        arrays.append(a.astype(np.uint16))
        info.append({"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                     "shape": list(a.shape), "dtype": str(a.dtype)})
    if arrays[0].shape != arrays[1].shape:
        raise ValueError(f"STOP: shapes differ: {arrays[0].shape} vs {arrays[1].shape}")
    return arrays[0] + arrays[1], info


def _set_metrics_n(score: np.ndarray, ink: np.ndarray, mask: np.ndarray, levels: int, threshold: int | None) -> dict:
    ink_set = ink & mask
    n_px, n_ink = int(mask.sum()), int(ink_set.sum())
    p = n_ink / n_px if n_px else 0.0
    out = {"n_px": n_px, "n_ink": n_ink, "ink_fraction": p, "trivial_floor": e02.trivial_floor(p),
           "auroc": e02._num(e02.auroc(score, ink_set, mask)) if n_px else None}
    if n_px:
        sw = sweep_n(np.bincount(score[ink_set], minlength=levels),
                     np.bincount(score[mask & ~ink], minlength=levels))
        out["best_f1"] = best_f1_n(sw)
        out["at_threshold"] = at_threshold_n(sw, threshold) if threshold is not None else None
        out["median_ink"] = float(np.median(score[ink_set])) if n_ink else None
        out["median_background"] = float(np.median(score[mask & ~ink])) if (n_px - n_ink) else None
    return out


def _sets_block(score: np.ndarray, masks: dict, sets, levels: int, threshold: int | None,
                edges, patch: int) -> dict:
    ink, train, held = masks["ink"], masks["train"], masks["held"]
    out: dict = {}
    if "train" in sets:
        out["train"] = _set_metrics_n(score, ink, train, levels, threshold)
    if "held" in sets:
        s = _set_metrics_n(score, ink, held, levels, threshold)
        st = e02.strata(held, train, edges, patch)
        s["distance_stats"] = st["distance_stats"]
        s["within_patch"] = st["within_patch"]
        s["within_two_patches"] = st["within_two_patches"]
        s["strata"] = [({"stratum": name, **_set_metrics_n(score, ink, m, levels, threshold)} if m.any()
                        else {"stratum": name, "n_px": 0}) for name, m in st["masks"]]
        s["regions"] = []
        for r in e02.regions(held, ink):
            row = {k: v for k, v in r.items() if k != "mask"}
            row.update({k: v for k, v in _set_metrics_n(score, ink, r["mask"], levels, threshold).items()
                        if k not in ("n_px", "n_ink", "ink_fraction")})
            s["regions"].append(row)
        out["held"] = s
    return out


def _base_report(labels_dir: Path, sets, edges, patch: int) -> tuple[dict, dict]:
    labels_dir = Path(labels_dir)
    label_tree = check_labels_allowed(labels_dir)                      # PRIMA di qualunque lettura di maschera
    masks = e02.load_masks(labels_dir, need_held=("held" in sets))
    n_overlap = int((masks["held"] & masks["train"]).sum()) if masks["held"] is not None else 0
    if n_overlap:
        raise ValueError(f"STOP: {n_overlap} px belong to both validation_mask and supervision_mask")
    report = {
        "version": VERSION, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "segment": labels_dir.name, "labels_dir": str(labels_dir), "labels_tree_sha256": label_tree,
        "annotated_plane": "shape[0] // 2", "patch": int(patch), "edges": [int(e) for e in edges],
        "disjoint_check": {"n_px_held_and_train": n_overlap}, "sets_requested": list(sets),
    }
    return report, masks


# ------------------------------------------------------------------------------------ modes
def build_run_report(pred_path, labels_dir, *, k: int, seed: int, threshold: int | None,
                     input_tree_sha256: str, layer_indices, source_z_slice, run_id: str = "E03-R01",
                     sets=("held", "train"), edges=e02.DEFAULT_EDGES, patch: int = e02.DEFAULT_PATCH) -> dict:
    """One point of the curve: the frozen E02 report, plus the identity block that makes it self-describing."""
    labels_dir = Path(labels_dir)
    check_labels_allowed(labels_dir)
    row = offset_row(k)
    if list(layer_indices) != list(row["expected_indices"]):
        raise ValueError(f"STOP: indici di layer {list(layer_indices)[:3]}… incoerenti con k={k:+d} "
                         f"(attesi {row['expected_indices'][0]}..{row['expected_indices'][-1]})")
    if list(source_z_slice) != list(row["source_z_slice"]):
        raise ValueError(f"STOP: finestra sorgente {list(source_z_slice)} incoerente con k={k:+d} "
                         f"(attesa {row['source_z_slice']})")
    rep = e02.build_report(Path(pred_path), labels_dir, sets=sets, threshold=threshold, edges=edges, patch=patch)
    rep["e03_point"] = {
        "run_id": run_id, "segment": labels_dir.name, "seed": int(seed), "k": int(k), "tag": row["tag"],
        "stage": row["stage"], "input": row["input"], "input_tree_sha256": input_tree_sha256,
        "source_z_slice": list(source_z_slice), "layer_indices": list(layer_indices),
        "sha256_pred": rep.get("sha256_pred"), "threshold": threshold,
        "orientation_gate": row["orientation_gate"], "micrometres": row["micrometres"],
        "e03_metrics_version": VERSION,
    }
    return rep


def build_average_report(preds, labels_dir, *, sets=("held", "train"), threshold_mean: int | None = None,
                         threshold_sum: int | None = None, combination: str = "mean_of_two",
                         seed=None, k=None, edges=e02.DEFAULT_EDGES, patch: int = e02.DEFAULT_PATCH) -> dict:
    """Mean of two predictions, evaluated on the SUM so that half points survive."""
    if len(list(preds)) != 2:
        raise ValueError("STOP: --average takes exactly two predictions")
    if threshold_mean is not None and threshold_sum is not None:
        raise ValueError("STOP: give either --threshold-mean or --threshold-sum")
    report, masks = _base_report(Path(labels_dir), sets, edges, patch)
    total, info = _sum_of_two(preds)
    if tuple(total.shape) != tuple(masks["ink"].shape):
        report.update({"inputs": info, "shape_ok": False})
        return report
    t = threshold_sum if threshold_sum is not None else (2 * threshold_mean if threshold_mean is not None else None)
    report.update({"inputs": info, "shape": list(total.shape), "dtype": "uint16 (sum of two uint8)",
                   "levels": 511, "combination": combination, "shape_ok": True,
                   "threshold_mean_arg": threshold_mean, "threshold_sum_used": t,
                   "seed": seed, "k": k})
    report["sets"] = _sets_block(total, masks, sets, 511, t, edges, patch)
    return report


def build_spearman_report(preds, labels_dir, *, sets=("held", "train"),
                          edges=e02.DEFAULT_EDGES, patch: int = e02.DEFAULT_PATCH, label: str | None = None) -> dict:
    if len(list(preds)) != 2:
        raise ValueError("STOP: --spearman takes exactly two predictions")
    report, masks = _base_report(Path(labels_dir), sets, edges, patch)
    a, b = (_read(Path(p)) for p in preds)
    if a.shape != b.shape or a.shape != masks["ink"].shape:
        raise ValueError(f"STOP: shapes differ: {a.shape}, {b.shape}, labels {masks['ink'].shape}")
    info = [{"path": str(Path(p)), "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in preds]
    out = {}
    for name, mask in (("held", masks["held"]), ("train", masks["train"])):
        if name in sets and mask is not None and mask.any():
            out[name] = spearman(a[mask], b[mask])
    report.update({"inputs": info, "spearman": out, "comparison": label})
    return report


def dumps(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True, default=float) + "\n"


# ------------------------------------------------------------------------------------ CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, default=None, help="prediction TIFF of one curve point")
    ap.add_argument("--average", type=Path, nargs=2, default=None, help="two prediction TIFFs to average")
    ap.add_argument("--spearman", type=Path, nargs=2, default=None, help="two prediction TIFFs to correlate")
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sets", default="held,train")
    ap.add_argument("--threshold", type=int, default=None, help="--run: frozen threshold on the uint8 prediction")
    ap.add_argument("--threshold-mean", type=int, default=None, help="--average: frozen threshold on the mean")
    ap.add_argument("--threshold-sum", type=int, default=None, help="--average: threshold on the sum (advanced)")
    ap.add_argument("--k", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--run-id", default="E03-R01")
    ap.add_argument("--input-tree-sha256", default=None)
    ap.add_argument("--layer-indices", default=None, help="comma-separated, as printed by infer.py")
    ap.add_argument("--source-z-slice", default=None, help="two comma-separated integers")
    ap.add_argument("--combination", default="mean_of_two")
    ap.add_argument("--label", default=None, help="--spearman: short description of the comparison")
    ap.add_argument("--edges", type=int, nargs="+", default=list(e02.DEFAULT_EDGES))
    ap.add_argument("--patch", type=int, default=e02.DEFAULT_PATCH)
    a = ap.parse_args(argv)
    chosen = [x for x in (a.run, a.average, a.spearman) if x]
    if len(chosen) != 1:
        print("STOP: choose exactly one of --run, --average, --spearman", file=sys.stderr)
        return 2
    sets = tuple(s.strip() for s in a.sets.split(",") if s.strip())
    try:
        if a.run:
            if a.k is None or a.seed is None or not a.input_tree_sha256 or not a.layer_indices or not a.source_z_slice:
                print("STOP: --run needs --k, --seed, --input-tree-sha256, --layer-indices, --source-z-slice", file=sys.stderr)
                return 2
            rep = build_run_report(a.run, a.labels, k=a.k, seed=a.seed, threshold=a.threshold,
                                   input_tree_sha256=a.input_tree_sha256,
                                   layer_indices=[int(x) for x in a.layer_indices.split(",")],
                                   source_z_slice=[int(x) for x in a.source_z_slice.split(",")],
                                   run_id=a.run_id, sets=sets, edges=a.edges, patch=a.patch)
        elif a.average:
            rep = build_average_report(a.average, a.labels, sets=sets, threshold_mean=a.threshold_mean,
                                       threshold_sum=a.threshold_sum, combination=a.combination,
                                       seed=a.seed, k=a.k, edges=a.edges, patch=a.patch)
        else:
            rep = build_spearman_report(a.spearman, a.labels, sets=sets, edges=a.edges, patch=a.patch, label=a.label)
    except (ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 3
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(dumps(rep), encoding="utf-8")
    summary = rep.get("sets", {})
    for name in ("held", "train"):
        if name in summary and summary[name].get("auroc") is not None:
            b = summary[name].get("best_f1", {})
            print(f"{name}: n={summary[name]['n_px']} auroc={summary[name]['auroc']:.4f} "
                  f"best_f1={b.get('f1', float('nan')):.4f}@{b.get('threshold')}")
    if "spearman" in rep:
        print("spearman: " + ", ".join(f"{k}={v:.4f}" for k, v in rep["spearman"].items()))
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
