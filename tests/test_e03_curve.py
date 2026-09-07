"""Tests for the E03 curve reader (plan docs/plans/2026-09-07-e03-tolleranza-offset-z.md, step 10).

The tolerance is a reading of a preregistered rule, not a choice, so the tests fix the rule on synthetic
curves (flat, decaying, asymmetric, anomalous) and, following R1 finding 3, prove that the reader REFUSES a
matrix that is incomplete, duplicated, or whose sign was flipped by a rename.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import e03_curve as curve  # noqa: E402

SEGMENTS = ["pherc0139-w016", "pherc0814-46527"]
SEEDS = [42, 43]
KS = [-5, -3, -2, 0, 2, 3, 5]
OFFSETS = json.loads((ROOT / "configs" / "e03" / "offsets.json").read_text(encoding="utf-8"))
ROW = {int(r["k"]): r for r in OFFSETS["offsets"]}
TEST_INPUT_SHA = "b" * 64


@pytest.fixture(autouse=True)
def datasets(tmp_path_factory, monkeypatch):
    """La validazione confronta le impronte degli input con configs/e03/datasets.json (revisione R2, finding 3).
    Qui si usa una copia con tutte le impronte riempite: quelle vere degli input spostati arrivano dai run prep."""
    real = json.loads((ROOT / "configs" / "e03" / "datasets.json").read_text(encoding="utf-8"))
    for seg in SEGMENTS:
        for key in ("official", "shifted_zm3", "shifted_zp3"):
            real["inputs"][seg][key]["tree_sha256"] = TEST_INPUT_SHA
    p = tmp_path_factory.mktemp("cfg") / "datasets.json"
    p.write_text(json.dumps(real), encoding="utf-8")
    monkeypatch.setattr(curve, "DATASETS_PATH", p)
    return p


def _point(tmp: Path, seg: str, seed: int, k: int, auroc: float, *, f1: float = 0.5,
           tag: str | None = None, seg_in_point: str | None = None, k_in_point: int | None = None) -> Path:
    row = ROW[k]
    tag = tag or row["tag"]
    rep = {
        "version": "e03_metrics/1.0", "segment": seg_in_point or seg, "sha256_pred": f"{abs(hash((seg, seed, k))):064x}"[:64],
        "sets": {"held": {"n_px": 1000, "n_ink": 200, "auroc": auroc,
                          "best_f1": {"f1": f1, "threshold": 99},
                          "at_threshold": {"threshold": 91, "f1": f1 - 0.005, "precision": 0.5, "recall": 0.5},
                          "strata": [], "regions": []},
                 "train": {"n_px": 5000, "auroc": 0.99, "best_f1": {"f1": 0.95, "threshold": 130},
                           "at_threshold": {"threshold": 91, "f1": 0.94}}},
    }
    rep["e03_point"] = {
        "run_id": "E03-R01", "segment": seg_in_point or seg, "seed": seed,
        "k": k if k_in_point is None else k_in_point, "tag": tag, "stage": row["stage"], "input": row["input"],
        "input_tree_sha256": TEST_INPUT_SHA, "source_z_slice": row["source_z_slice"],
        "layer_indices": row["expected_indices"], "sha256_pred": rep["sha256_pred"],
        "threshold": 91, "orientation_gate": row["orientation_gate"], "micrometres": row["micrometres"],
    }
    p = tmp / f"{seg}_s{seed}_{tag}.json"
    p.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    return p


def _matrix(tmp: Path, aurocs) -> Path:
    """aurocs[(seed, k)] -> valore, uguale per i due segmenti salvo override con (seed, k, seg)."""
    tmp.mkdir(parents=True, exist_ok=True)
    for seg in SEGMENTS:
        for seed in SEEDS:
            for k in KS:
                v = aurocs.get((seed, k, seg), aurocs.get((seed, k), 0.8))
                _point(tmp, seg, seed, k, v)
    return tmp


def _flat():
    return {(seed, k): 0.80 for seed in SEEDS for k in KS}


def _decaying():
    out = {}
    for seed in SEEDS:
        for k in KS:
            out[(seed, k)] = 0.80 - 0.02 * abs(k)          # -0,04 a |k|=2, -0,06 a 3, -0,10 a 5
    return out


# --------------------------------------------------------------------------------- validation
def test_complete_matrix_is_accepted(tmp_path):
    d = _matrix(tmp_path / "m", _flat())
    points = curve.load_points(d)
    curve.validate_matrix(points)
    assert len(points) == 28


def test_missing_point_is_refused(tmp_path):
    d = _matrix(tmp_path / "m", _flat())
    next(iter(d.glob("*_s43_zp5.json"))).unlink()
    with pytest.raises(ValueError, match="manca|mancano"):
        curve.validate_matrix(curve.load_points(d))


def test_duplicate_point_is_refused(tmp_path):
    d = _matrix(tmp_path / "m", _flat())
    src = d / f"{SEGMENTS[0]}_s42_zm3.json"
    (d / f"{SEGMENTS[0]}_s42_zm3_copy.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicat"):
        curve.validate_matrix(curve.load_points(d))


def test_filename_that_contradicts_the_point_is_refused(tmp_path):
    """Il caso che la revisione R1 temeva: un rinomino zm3 -> zp3 inverte un verso della curva."""
    d = _matrix(tmp_path / "m", _flat())
    p = d / f"{SEGMENTS[0]}_s42_zm3.json"
    rep = json.loads(p.read_text(encoding="utf-8"))
    p.unlink()
    (d / f"{SEGMENTS[0]}_s42_zp3.json").write_text(json.dumps(rep), encoding="utf-8")   # contenuto k=-3, nome zp3
    with pytest.raises(ValueError, match="nome|tag"):
        curve.validate_matrix(curve.load_points(d))


def test_point_whose_segment_disagrees_with_the_filename_is_refused(tmp_path):
    d = _matrix(tmp_path / "m", _flat())
    p = d / f"{SEGMENTS[0]}_s42_z0.json"
    rep = json.loads(p.read_text(encoding="utf-8"))
    rep["segment"] = SEGMENTS[1]                 # il report dice un segmento, il punto un altro
    p.write_text(json.dumps(rep), encoding="utf-8")
    with pytest.raises(ValueError, match="segmento"):
        curve.validate_matrix(curve.load_points(d))


def test_point_with_a_window_that_contradicts_k_is_refused(tmp_path):
    d = _matrix(tmp_path / "m", _flat())
    p = d / f"{SEGMENTS[0]}_s42_zm5.json"
    rep = json.loads(p.read_text(encoding="utf-8"))
    rep["e03_point"]["source_z_slice"] = [13, 97]
    p.write_text(json.dumps(rep), encoding="utf-8")
    with pytest.raises(ValueError, match="finestra|source_z_slice"):
        curve.validate_matrix(curve.load_points(d))


def test_a_report_on_another_segment_is_refused(tmp_path):
    d = _matrix(tmp_path / "m", _flat())
    _point(d, "pherc1667-w029", 42, 0, 0.9)
    with pytest.raises(ValueError, match="segment|w029"):
        curve.validate_matrix(curve.load_points(d))


# --------------------------------------------------------------------------------- readings
def test_flat_curve_reports_no_decay(tmp_path):
    res = curve.compute(curve.load_points(_matrix(tmp_path / "m", _flat())))
    for seed in SEEDS:
        assert res["tolerance"][str(seed)]["minus"] is None
        assert res["tolerance"][str(seed)]["plus"] is None
    assert res["H1"]["holds"] is True
    assert res["anomaly"]["triggered"] is False


def test_decaying_curve_gives_a_tolerance_and_supports_H2(tmp_path):
    res = curve.compute(curve.load_points(_matrix(tmp_path / "m", _decaying())))
    for seed in SEEDS:
        assert res["tolerance"][str(seed)]["minus"] == 3      # -0,04 a |k|=2, -0,06 a |k|=3 supera 0,05
        assert res["tolerance"][str(seed)]["plus"] == 3
    assert res["H1"]["holds"] is False                        # |Delta| = 0,04 > 0,02
    assert res["H2"]["holds"] is True


def test_asymmetric_curve_is_reported_per_direction(tmp_path):
    a = _flat()
    for seed in SEEDS:
        a[(seed, -3)] = 0.70; a[(seed, -5)] = 0.60           # decade solo verso il basso
    res = curve.compute(curve.load_points(_matrix(tmp_path / "m", a)))
    for seed in SEEDS:
        assert res["tolerance"][str(seed)]["minus"] == 3
        assert res["tolerance"][str(seed)]["plus"] is None
    assert res["asymmetric"] is True


def test_anomaly_rule_triggers_only_when_all_four_combinations_improve(tmp_path):
    a = _flat()
    for seed in SEEDS:
        a[(seed, 2)] = 0.85                                   # +0,05 su tutte e quattro
    res = curve.compute(curve.load_points(_matrix(tmp_path / "m", a)))
    assert res["anomaly"]["triggered"] is True and res["anomaly"]["k"] == [2]

    b = _flat()
    b[(42, 2, SEGMENTS[0])] = 0.85                            # solo una combinazione
    res2 = curve.compute(curve.load_points(_matrix(tmp_path / "n", b)))
    assert res2["anomaly"]["triggered"] is False


def test_delta_uses_the_same_seed_as_reference(tmp_path):
    a = _flat()
    a[(43, 0)] = 0.95                                          # il seed 43 parte piu' alto ovunque
    a[(43, -3)] = 0.93
    res = curve.compute(curve.load_points(_matrix(tmp_path / "m", a)))
    assert abs(res["delta"]["43"]["-3"]["mean"] - (-0.02)) < 1e-12      # non 0,93 - 0,80
    assert abs(res["delta"]["42"]["-3"]["mean"] - 0.0) < 1e-12
