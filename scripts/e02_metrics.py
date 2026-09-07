#!/usr/bin/env python3
"""Frozen per-segment metrics for the E02 meter (plan docs/plans/2026-09-06-e02-costruire-il-metro.md, step 3).

Pixel sets, always on the annotated plane (shape[0] // 2 of the label arrays):
  held  = validation_mask == 1   (never used as supervision by the released ink_9um checkpoints)
  train = supervision_mask == 1  (memorised by the checkpoints: operational control, never generalisation)
The two are never mixed. With --sets train the prediction is never read on held-out coordinates: the
orientation test uses the intersection of the training mask with its transformed copy (review R1, round 2).

Measures per set: AUROC (E00 function, threshold-free), threshold sweep (precision/recall/F1 at every uint8
threshold, `score >= t`; best F1 at the LOWEST maximising threshold), trivial floor 2p/(1+p), medians; for the
training set the orientation gate; for the held-out set the distance strata to the nearest training pixel and
the per-region breakdown. --geometry reports masks only (no prediction).

The histogram sweep and the distance-strata approach are adapted from khj1222/vesuvius-challenge
(tools/eval_validation.py, tools/audit_holdout_masks.py, MIT License, commit 13920ba, registry R02).

Usage:
  python scripts/e02_metrics.py --pred PRED.tif --labels SEGMENT_DIR --out REPORT.json [--sets held,train] [--threshold N] [--edges 0 64 128 256] [--patch 128]
  python scripts/e02_metrics.py --geometry --labels SEGMENT_DIR --out GEOMETRY.json [--edges ...] [--patch 128]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

VERSION = "e02_metrics/1.1"      # 1.1: orientation transforms inside the bbox of the mask (plan amendment A1)
DEFAULT_EDGES = (0, 64, 128, 256)
DEFAULT_PATCH = 128
TRANSFORMS = {
    "originale": lambda a: a,
    "rot180": lambda a: a[::-1, ::-1],
    "flipY": lambda a: a[::-1, :],
    "flipX": lambda a: a[:, ::-1],
}


# ------------------------------------------------------------------------------------------ core metrics
def auroc(scores: np.ndarray, pos: np.ndarray, valid: np.ndarray) -> float:
    """AUROC of `scores` over the pixels in `valid`, positives = `pos`. Function of E00, unchanged
    (average rank on ties, mergesort). NaN when one class is missing."""
    s = scores[valid].astype(np.float64)
    y = pos[valid]
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    ss = s[order]
    i = 0
    while i < len(ss):
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def sweep(pos_hist: np.ndarray, neg_hist: np.ndarray) -> dict:
    """Precision/recall/F1/IoU at every uint8 threshold t, with 'predicted ink' = score >= t.
    Adapted from R02 tools/eval_validation.py (MIT)."""
    pos = np.asarray(pos_hist, dtype=np.int64)
    neg = np.asarray(neg_hist, dtype=np.int64)
    assert pos.shape == (256,) and neg.shape == (256,)
    tp = np.cumsum(pos[::-1])[::-1].astype(np.float64)
    fp = np.cumsum(neg[::-1])[::-1].astype(np.float64)
    total_pos, total_neg = float(pos.sum()), float(neg.sum())
    fn = total_pos - tp
    tn = total_neg - fp
    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(tp + fp > 0, tp / np.maximum(tp + fp, 1.0), 0.0)
        recall = np.where(total_pos > 0, tp / max(total_pos, 1.0), 0.0)
        f1 = np.where(precision + recall > 0, 2 * precision * recall / np.maximum(precision + recall, 1e-300), 0.0)
        iou = np.where(tp + fp + fn > 0, tp / np.maximum(tp + fp + fn, 1.0), 0.0)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "f1": f1, "iou": iou,
            "total_pos": total_pos, "total_neg": total_neg}


def at_threshold(sw: dict, t: int) -> dict:
    i = int(np.clip(int(t), 0, 255))
    return {"threshold": i, "tp": int(sw["tp"][i]), "fp": int(sw["fp"][i]), "fn": int(sw["fn"][i]), "tn": int(sw["tn"][i]),
            "precision": float(sw["precision"][i]), "recall": float(sw["recall"][i]),
            "f1": float(sw["f1"][i]), "iou": float(sw["iou"][i])}


def best_f1(sw: dict) -> dict:
    """The LOWEST threshold among those maximising F1 (np.argmax returns the first maximum). Frozen tie rule."""
    i = int(np.argmax(sw["f1"]))
    out = at_threshold(sw, i)
    return {"f1": out["f1"], "threshold": i, "precision": out["precision"], "recall": out["recall"], "iou": out["iou"]}


def trivial_floor(p: float) -> float:
    """F1 of the classifier that calls everything ink, for ink fraction p."""
    return 0.0 if p <= 0 else float(2 * p / (1 + p))


def _num(x: float) -> float | None:
    return None if x != x else float(x)        # NaN -> None (JSON-safe, comparable)


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    return int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1


def _transform_in_bbox(a: np.ndarray, kind: str, box: tuple[int, int, int, int]) -> np.ndarray:
    """Apply a transform inside `box` only (the rest is zero): a flip/rotation about the box centre."""
    y0, y1, x0, x1 = box
    out = np.zeros_like(a)
    out[y0:y1, x0:x1] = TRANSFORMS[kind](a[y0:y1, x0:x1])
    return out


def orientation(pred: np.ndarray, ink: np.ndarray, valid: np.ndarray) -> dict:
    """AUROC with the label as is and under three transforms applied INSIDE the bounding box of `valid`
    (rot180 / flipY / flipX about the box centre; plan amendment A1). Each variant is evaluated only on
    valid & T(valid): the prediction is never read outside the original mask (review R1, round 2), and the
    box-centred transform keeps the intersection large even for one compact annotated region (whole-image
    transforms had an empty intersection on pherc0814-46527, run infer-46527-seed42 v1).
    `orientamento_ok` is True when the original is strictly above every comparable variant, False when a
    variant ties or wins, None when no variant is comparable (empty or single-class intersection)."""
    out: dict = {}
    if not valid.any():
        out.update({k: None for k in TRANSFORMS})
        out.update({"comparabili": [], "orientamento_ok": None, "bbox_yyxx": None})
        return out
    box = _bbox(valid)
    out["originale"] = _num(auroc(pred, ink & valid, valid))
    for k in ("rot180", "flipY", "flipX"):
        v = valid & _transform_in_bbox(valid, k, box)
        p = _transform_in_bbox(ink, k, box) & v
        out[k] = _num(auroc(pred, p, v))
    out["bbox_yyxx"] = list(box)
    comparable = [k for k in ("rot180", "flipY", "flipX") if out[k] is not None]
    if out["originale"] is None or not comparable:
        ok = None
    else:
        ok = bool(all(out["originale"] > out[k] for k in comparable))
    out["comparabili"] = comparable
    out["orientamento_ok"] = ok
    return out


def strata(held: np.ndarray, supervision: np.ndarray, edges=DEFAULT_EDGES, patch: int = DEFAULT_PATCH) -> dict:
    """Held-out pixels split by Euclidean distance to the nearest supervised pixel (boundary excluded: d < hi).
    Adapted from R02 tools/audit_holdout_masks.py (MIT)."""
    from scipy import ndimage

    distance = ndimage.distance_transform_edt(~supervision)
    bounds = [float(e) for e in edges] + [np.inf]
    masks = []
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        name = f"<{hi:g}" if lo == 0 else (f">={lo:g}" if hi == np.inf else f"{lo:g}-{hi:g}")
        masks.append((name, held & (distance >= lo) & (distance < hi)))
    d = distance[held]
    if d.size:
        stats = {"min": float(d.min()), "p25": float(np.percentile(d, 25)), "median": float(np.median(d)),
                 "p75": float(np.percentile(d, 75)), "max": float(d.max())}
        within_patch = float(np.count_nonzero(d < patch) / d.size)
        within_two = float(np.count_nonzero(d < 2 * patch) / d.size)
    else:
        stats, within_patch, within_two = {}, 0.0, 0.0
    return {"masks": masks, "distance": distance, "distance_stats": stats, "within_patch": within_patch,
            "within_two_patches": within_two, "patch": int(patch), "edges": [int(e) for e in edges]}


def annotated_regions(held: np.ndarray, train: np.ndarray) -> dict:
    """Connected components of the whole annotation (held | train), 4-connectivity as in R02
    tools/audit_holdout_masks.py, and how many of them contain both held-out and training pixels."""
    from scipy import ndimage

    labels, n = ndimage.label(held | train)
    mixing = 0
    for idx, box in enumerate(ndimage.find_objects(labels), start=1):
        sub = labels[box] == idx
        if np.any(sub & held[box]) and np.any(sub & train[box]):
            mixing += 1
    return {"annotated_regions": int(n), "regions_mixing_held_and_training": int(mixing)}


def regions(held: np.ndarray, ink: np.ndarray) -> list[dict]:
    """Connected components of the held-out mask (4-connectivity, scipy default, as in R02), with pixel and
    ink counts and bbox."""
    from scipy import ndimage

    labels, n = ndimage.label(held)
    out = []
    for idx, box in enumerate(ndimage.find_objects(labels), start=1):
        mask = labels == idx
        n_px = int(mask.sum())
        n_ink = int((mask & ink).sum())
        out.append({"region": idx, "n_px": n_px, "n_ink": n_ink, "ink_fraction": n_ink / n_px,
                    "bbox_yyxx": [int(box[0].start), int(box[0].stop), int(box[1].start), int(box[1].stop)], "mask": mask})
    return out


# ------------------------------------------------------------------------------------------ segment io
def centre_plane(path: Path) -> np.ndarray:
    """Annotated plane (shape[0] // 2) of a label zarr, as bool. Same index rule as the trainer and R02."""
    import zarr

    if not path.exists():
        raise FileNotFoundError(path)
    node = zarr.open(str(path), mode="r")
    arr = node["0"] if hasattr(node, "array_keys") else node
    return np.asarray(arr[arr.shape[0] // 2]) > 0


def load_masks(labels_dir: Path, need_held: bool) -> dict:
    name = labels_dir.name
    ink = centre_plane(labels_dir / f"{name}_inklabels.zarr")
    train = centre_plane(labels_dir / f"{name}_supervision_mask.zarr")
    val_path = labels_dir / f"{name}_validation_mask.zarr"
    held = centre_plane(val_path) if (val_path.exists() or need_held) else None
    if need_held and held is None:
        raise FileNotFoundError(val_path)
    assert ink.shape == train.shape and (held is None or held.shape == ink.shape), "label arrays differ in shape"
    return {"name": name, "ink": ink, "train": train, "held": held}


def read_prediction(path: Path) -> np.ndarray:
    import tifffile

    pred = tifffile.imread(str(path))
    if pred.ndim != 2:
        raise ValueError(f"expected a 2-D prediction, got {pred.shape}")
    return pred


# ------------------------------------------------------------------------------------------ report
def _set_metrics(pred: np.ndarray, ink: np.ndarray, mask: np.ndarray, threshold: int | None) -> dict:
    ink_set = ink & mask
    n_px, n_ink = int(mask.sum()), int(ink_set.sum())
    p = n_ink / n_px if n_px else 0.0
    out = {"n_px": n_px, "n_ink": n_ink, "ink_fraction": p, "trivial_floor": trivial_floor(p),
           "auroc": _num(auroc(pred, ink_set, mask)) if n_px else None}
    if n_px:
        sw = sweep(np.bincount(pred[ink_set], minlength=256), np.bincount(pred[mask & ~ink], minlength=256))
        out["best_f1"] = best_f1(sw)
        out["at_threshold"] = at_threshold(sw, threshold) if threshold is not None else None
        out["median_ink"] = float(np.median(pred[ink_set])) if n_ink else None
        out["median_background"] = float(np.median(pred[mask & ~ink])) if (n_px - n_ink) else None
    return out


def geometry_report(masks: dict, edges, patch: int) -> dict:
    ink, train, held = masks["ink"], masks["train"], masks["held"]
    g = {"n_px_train": int(train.sum()), "n_ink_train": int((ink & train).sum()), "annotated_plane_shape": list(train.shape)}
    if held is not None:
        st = strata(held, train, edges, patch)
        regs = regions(held, ink)
        g.update({
            "n_px_held": int(held.sum()), "n_ink_held": int((ink & held).sum()),
            "n_px_held_and_train": int((held & train).sum()),
            "held_share_of_annotation": float(held.sum() / max(1, (held | train).sum())),
            **annotated_regions(held, train),
            "regions_held": len(regs),
            "regions": [{k: v for k, v in r.items() if k != "mask"} for r in regs],
            "distance_stats": st["distance_stats"], "within_patch": st["within_patch"],
            "within_two_patches": st["within_two_patches"], "patch": st["patch"], "edges": st["edges"],
            "strata": [{"stratum": name, "n_px": int(m.sum()), "n_ink": int((m & ink).sum()),
                        "ink_density": float((m & ink).sum() / m.sum()) if m.sum() else None} for name, m in st["masks"]],
        })
    return g


def build_report(pred_path: Path | None, labels_dir: Path, sets=("held", "train"), threshold: int | None = None,
                 edges=DEFAULT_EDGES, patch: int = DEFAULT_PATCH, geometry_only: bool = False) -> dict:
    sets = tuple(sets)
    masks = load_masks(labels_dir, need_held=("held" in sets) or geometry_only)
    report = {
        "version": VERSION, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "segment": masks["name"], "labels_dir": str(labels_dir), "annotated_plane": "shape[0] // 2",
        "patch": int(patch), "edges": [int(e) for e in edges], "threshold_arg": threshold,
        "disjoint_check": {"n_px_held_and_train": int((masks["held"] & masks["train"]).sum())} if masks["held"] is not None else None,
    }
    if geometry_only:
        report["geometry"] = geometry_report(masks, edges, patch)
        return report

    assert pred_path is not None
    pred = read_prediction(pred_path)
    report.update({"prediction": str(pred_path), "sha256_pred": hashlib.sha256(pred_path.read_bytes()).hexdigest(),
                   "shape": list(pred.shape), "dtype": str(pred.dtype), "sets_requested": list(sets)})
    if tuple(pred.shape) != tuple(masks["ink"].shape) or pred.dtype != np.uint8:
        report["shape_ok"] = False
        return report
    report["shape_ok"] = True
    ink, train, held = masks["ink"], masks["train"], masks["held"]
    out_sets: dict = {}
    if "train" in sets:
        s = _set_metrics(pred, ink, train, threshold)
        s["orientation"] = orientation(pred, ink, train)
        out_sets["train"] = s
    if "held" in sets:
        s = _set_metrics(pred, ink, held, threshold)
        st = strata(held, train, edges, patch)
        s["distance_stats"] = st["distance_stats"]
        s["within_patch"] = st["within_patch"]
        s["within_two_patches"] = st["within_two_patches"]
        s["strata"] = []
        for name, m in st["masks"]:
            row = {"stratum": name, **_set_metrics(pred, ink, m, threshold)} if m.any() else {"stratum": name, "n_px": 0}
            s["strata"].append(row)
        s["regions"] = []
        for r in regions(held, ink):
            row = {k: v for k, v in r.items() if k != "mask"}
            row.update({k: v for k, v in _set_metrics(pred, ink, r["mask"], threshold).items() if k not in ("n_px", "n_ink", "ink_fraction")})
            s["regions"].append(row)
        out_sets["held"] = s
    report["sets"] = out_sets
    return report


def dumps(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pred", type=Path, default=None, help="prediction TIFF (uint8) from koine_machines.inference.infer")
    ap.add_argument("--labels", type=Path, required=True, help="segment folder holding <seg>_inklabels.zarr etc.")
    ap.add_argument("--out", type=Path, required=True, help="JSON report path")
    ap.add_argument("--sets", default="held,train", help="comma-separated: held, train (default both); use 'train' for the sealed segment")
    ap.add_argument("--threshold", type=int, default=None, help="also report metrics at this frozen threshold (score >= t)")
    ap.add_argument("--edges", type=int, nargs="+", default=list(DEFAULT_EDGES), help="distance stratum edges in px")
    ap.add_argument("--patch", type=int, default=DEFAULT_PATCH, help="training patch width in label pixels (default 128)")
    ap.add_argument("--geometry", action="store_true", help="masks only: strata and regions, no prediction")
    a = ap.parse_args(argv)
    sets = tuple(s.strip() for s in a.sets.split(",") if s.strip())
    assert set(sets) <= {"held", "train"} and sets, f"--sets must be held and/or train, got {a.sets}"
    if not a.geometry and a.pred is None:
        ap.error("--pred is required unless --geometry")
    report = build_report(a.pred, a.labels.resolve(), sets, a.threshold, a.edges, a.patch, a.geometry)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps(report))
    if a.geometry:
        g = report["geometry"]
        print(f"{report['segment']}: train {g['n_px_train']} px" + (f", held {g['n_px_held']} px in {g['regions_held']} regions, "
              f"within one patch {g['within_patch']:.1%}, two {g['within_two_patches']:.1%}, held&train {g['n_px_held_and_train']}" if "n_px_held" in g else ""))
        return 0
    if not report["shape_ok"]:
        print(f"STOP: prediction {report['shape']} {report['dtype']} does not match the labels", file=sys.stderr)
        return 2
    for name, s in report["sets"].items():
        line = f"{report['segment']} [{name}] n={s['n_px']} ink={s['ink_fraction']:.4f} floor={s['trivial_floor']:.4f} AUROC={s['auroc']} bestF1={s['best_f1']['f1']:.4f}@{s['best_f1']['threshold']}"
        if name == "train":
            line += f" orientamento_ok={s['orientation']['orientamento_ok']}"
        print(line)
    print(f"report -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
