"""Unit tests for scripts/e02_metrics.py (E02, plan step 3). Written before the implementation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import e02_metrics as m  # noqa: E402


def test_auroc_perfect_and_random():
    scores = np.zeros((8, 8), np.uint8); scores[:, 4:] = 255
    ink = np.zeros((8, 8), bool); ink[:, 4:] = True
    valid = np.ones((8, 8), bool)
    assert m.auroc(scores, ink, valid) == 1.0
    assert m.auroc(np.full((8, 8), 7, np.uint8), ink, valid) == 0.5      # tutti pareggi -> 0,5
    assert np.isnan(m.auroc(scores, np.zeros((8, 8), bool), valid))      # una sola classe -> NaN


def test_best_f1_threshold_and_floor():
    pos = np.bincount([200, 210, 220], minlength=256); neg = np.bincount([10, 20, 30], minlength=256)
    s = m.sweep(pos, neg); b = m.best_f1(s)
    assert b["f1"] == 1.0 and b["threshold"] == 31          # F1 = 1 per ogni t in 31..200: si congela la piu' bassa
    assert m.at_threshold(s, 200)["f1"] == 1.0 and m.at_threshold(s, 201)["recall"] < 1.0
    assert m.at_threshold(s, 0)["recall"] == 1.0 and m.at_threshold(s, 0)["precision"] == 0.5
    assert abs(m.trivial_floor(0.5) - 2 / 3) < 1e-12
    assert m.trivial_floor(0.0) == 0.0


def test_best_f1_plateau_is_exact_lowest_threshold():
    # controesempio di R2 (finding 2): F1 = 2/7 esatto sia per t in 1..100 sia per t in 101..200; con precision e
    # recall arrotondati il secondo plateau risultava maggiore di un ulp e vinceva la soglia 101
    pos = np.bincount([100, 200], minlength=256)
    neg = np.bincount([0] * 200 + [100] * 6 + [200] * 4, minlength=256)
    s = m.sweep(pos, neg)
    assert s["f1"][1] == s["f1"][101] == 2 / 7
    assert m.best_f1(s)["threshold"] == 1


def test_overlapping_masks_are_refused_before_reading_prediction(tmp_path):
    import tifffile
    import zarr

    name = "segov"; seg = tmp_path / name; seg.mkdir()
    ink = np.zeros((3, 16, 16), np.uint8); ink[1, 2:6, 2:6] = 1
    sup = np.zeros((3, 16, 16), np.uint8); sup[1, :, :9] = 1
    val = np.zeros((3, 16, 16), np.uint8); val[1, :, 7:] = 1          # colonne 7 e 8 in entrambe le maschere
    for kind, arr in (("inklabels", ink), ("supervision_mask", sup), ("validation_mask", val)):
        zarr.open_group(str(seg / f"{name}_{kind}.zarr"), mode="w").create_dataset("0", data=arr, chunks=(3, 16, 16))
    tifffile.imwrite(str(tmp_path / "p.tif"), np.zeros((16, 16), np.uint8))
    with pytest.raises(ValueError):
        m.build_report(tmp_path / "p.tif", seg, sets=("train",))
    assert m.main(["--pred", str(tmp_path / "p.tif"), "--labels", str(seg), "--out", str(tmp_path / "o.json"), "--sets", "train"]) == 3
    assert not (tmp_path / "o.json").exists()
    g = m.build_report(None, seg, geometry_only=True)                  # la geometria conserva la diagnostica
    assert g["geometry"]["n_px_held_and_train"] == 32


def test_strata_partition_held_pixels():
    sup = np.zeros((64, 64), bool); sup[:, :8] = True
    held = np.zeros((64, 64), bool); held[:, 16:] = True
    st = m.strata(held, sup, edges=[0, 8, 16, 32], patch=8)
    assert sum(int(mask.sum()) for _, mask in st["masks"]) == int(held.sum())
    assert st["within_patch"] == 0.0                                   # tutti a >= 8 px
    assert st["within_two_patches"] > 0.0                              # colonne 16..22 stanno sotto 16 px
    assert [name for name, _ in st["masks"]] == ["<8", "8-16", "16-32", ">=32"]
    assert st["distance_stats"]["min"] == 9.0


def test_orientation_detects_flip():
    # inchiostro solo nel quadrante in alto a sinistra: ogni trasformazione lo sposta altrove
    pred = np.zeros((16, 16), np.uint8); pred[:8, :8] = 255
    ink = np.zeros((16, 16), bool); ink[:8, :8] = True
    o = m.orientation(pred, ink, np.ones((16, 16), bool))
    # trasformata: i 64 positivi hanno score 0; fra i 192 negativi, 128 hanno score 0 (pareggio, 0,5) e 64 hanno 255
    # -> AUROC = 128 * 0,5 / 192 = 1/3, non 0 (verificato da Codex in R1 con la funzione di E00)
    assert o["originale"] == 1.0
    for k in ("flipY", "flipX", "rot180"):
        assert abs(o[k] - 1 / 3) < 1e-9
    assert o["orientamento_ok"] is True
    # simmetria in X: flipX pareggia l'originale, quindi "strettamente massima" deve fallire
    pred2 = np.zeros((16, 16), np.uint8); pred2[:8] = 255
    ink2 = np.zeros((16, 16), bool); ink2[:8] = True
    assert m.orientation(pred2, ink2, np.ones((16, 16), bool))["orientamento_ok"] is False


def test_orientation_compact_region_is_evaluable_with_bbox_transforms():
    # maschera compatta in un angolo (come la supervisione di pherc0814-46527): con le trasformate applicate
    # nel bounding box della maschera (emendamento A1) le varianti restano confrontabili, e leggono solo la maschera
    valid = np.zeros((16, 16), bool); valid[:4, :4] = True
    ink = np.zeros((16, 16), bool); ink[:2, :2] = True
    pred = np.zeros((16, 16), np.uint8); pred[:2, :2] = 200
    o = m.orientation(pred, ink, valid)
    assert o["originale"] == 1.0 and o["comparabili"] == ["rot180", "flipY", "flipX"] and o["orientamento_ok"] is True
    assert o["bbox_yyxx"] == [0, 4, 0, 4]
    # cambiare la predizione FUORI dalla maschera non cambia nulla
    pred2 = pred.copy(); pred2[4:, :] = 255; pred2[:, 4:] = 255
    assert m.orientation(pred2, ink, valid) == o


def test_orientation_not_evaluable_when_single_class():
    # tutta la maschera e' inchiostro: AUROC indefinita per ogni variante -> gate non valutabile
    valid = np.zeros((16, 16), bool); valid[:4, :4] = True
    ink = valid.copy()
    pred = np.full((16, 16), 200, np.uint8)
    o = m.orientation(pred, ink, valid)
    assert o["originale"] is None and o["comparabili"] == [] and o["orientamento_ok"] is None


def test_held_out_pixels_are_never_read():
    # maschera di training a sinistra, held-out a destra, disgiunte: cambiare SOLO le predizioni held-out
    # non deve cambiare nessuna metrica ne' il gate quando si misura l'insieme 'train' (R1, secondo giro)
    rng = np.random.default_rng(0)
    train = np.zeros((32, 32), bool); train[:, :12] = True
    held = np.zeros((32, 32), bool); held[:, 20:] = True
    ink = np.zeros((32, 32), bool); ink[4:12, 2:8] = True; ink[10:20, 22:30] = True
    pred = rng.integers(0, 256, (32, 32)).astype(np.uint8); pred[ink] = 240
    pred2 = pred.copy(); pred2[held] = rng.integers(0, 256, int(held.sum())).astype(np.uint8)
    a, b = m.orientation(pred, ink, train), m.orientation(pred2, ink, train)
    assert a == b
    assert m.auroc(pred, ink & train, train) == m.auroc(pred2, ink & train, train)
    assert (train & held).sum() == 0


def test_regions_counts_components():
    held = np.zeros((32, 32), bool); held[2:6, 2:6] = True; held[20:30, 20:30] = True
    ink = np.zeros((32, 32), bool); ink[3:5, 3:5] = True
    regs = m.regions(held, ink)
    assert len(regs) == 2
    assert sorted(r["n_px"] for r in regs) == [16, 100]
    assert sum(r["n_ink"] for r in regs) == 4


# ------------------------------------------------------------------------------ CLI on synthetic zarr labels
@pytest.fixture
def synthetic_segment(tmp_path):
    import tifffile
    import zarr

    name = "segx"
    seg = tmp_path / name
    seg.mkdir()
    H = W = 64
    # blocco di training fuori centro in X rispetto al bbox della supervisione (colonne 0..31): con l'emendamento A1
    # le trasformate sono centrate sul bbox, e un blocco centrato in X pareggerebbe l'originale sotto flipX
    ink = np.zeros((H, W), np.uint8); ink[8:24, 4:14] = 1; ink[40:56, 40:56] = 1
    sup = np.zeros((H, W), np.uint8); sup[:, :32] = 1
    val = np.zeros((H, W), np.uint8); val[:, 36:] = 1
    for kind, plane in (("inklabels", ink), ("supervision_mask", sup), ("validation_mask", val)):
        arr = np.zeros((3, H, W), np.uint8); arr[1] = plane          # piano annotato = shape[0] // 2 = 1
        g = zarr.open_group(str(seg / f"{name}_{kind}.zarr"), mode="w")
        g.create_dataset("0", data=arr, chunks=(3, 32, 32))
    rng = np.random.default_rng(1)
    pred = rng.integers(0, 120, (H, W)).astype(np.uint8); pred[ink.astype(bool)] = 230
    tifffile.imwrite(str(tmp_path / "pred.tif"), pred)
    pred2 = pred.copy(); pred2[val.astype(bool)] = rng.integers(0, 256, int(val.sum())).astype(np.uint8)
    tifffile.imwrite(str(tmp_path / "pred_heldout_changed.tif"), pred2)
    return {"dir": seg, "pred": tmp_path / "pred.tif", "pred2": tmp_path / "pred_heldout_changed.tif", "tmp": tmp_path}


def _load(p: Path) -> dict:
    d = json.loads(p.read_text(encoding="utf-8"))
    d.pop("generated_at", None)
    return d


def test_report_is_deterministic(synthetic_segment):
    s = synthetic_segment
    a, b = s["tmp"] / "a.json", s["tmp"] / "b.json"
    assert m.main(["--pred", str(s["pred"]), "--labels", str(s["dir"]), "--out", str(a), "--patch", "8", "--edges", "0", "8", "16", "32"]) == 0
    assert m.main(["--pred", str(s["pred"]), "--labels", str(s["dir"]), "--out", str(b), "--patch", "8", "--edges", "0", "8", "16", "32"]) == 0
    ra, rb = _load(a), _load(b)
    assert ra == rb
    assert set(ra["sets"]) == {"held", "train"}
    assert ra["disjoint_check"]["n_px_held_and_train"] == 0
    assert ra["sets"]["held"]["auroc"] > 0.9 and ra["sets"]["train"]["auroc"] > 0.9
    assert ra["sets"]["train"]["orientation"]["orientamento_ok"] is True
    assert len(ra["sets"]["held"]["regions"]) == 1 and len(ra["sets"]["held"]["strata"]) == 4


def test_cli_sets_train_ignores_held_out_pixels(synthetic_segment):
    s = synthetic_segment
    a, b = s["tmp"] / "t1.json", s["tmp"] / "t2.json"
    assert m.main(["--pred", str(s["pred"]), "--labels", str(s["dir"]), "--out", str(a), "--sets", "train"]) == 0
    assert m.main(["--pred", str(s["pred2"]), "--labels", str(s["dir"]), "--out", str(b), "--sets", "train"]) == 0
    ra, rb = _load(a), _load(b)
    assert "held" not in ra["sets"] and "held" not in rb["sets"]
    ra.pop("sha256_pred"); rb.pop("sha256_pred")           # i TIFF differiscono per costruzione
    ra.pop("prediction"); rb.pop("prediction")
    assert ra == rb


def test_geometry_mode_needs_no_prediction(synthetic_segment):
    s = synthetic_segment
    out = s["tmp"] / "geo.json"
    assert m.main(["--geometry", "--labels", str(s["dir"]), "--out", str(out), "--patch", "8", "--edges", "0", "8", "16", "32"]) == 0
    g = _load(out)
    assert g["geometry"]["n_px_held"] == int(64 * 28) and g["geometry"]["n_px_train"] == int(64 * 32)
    assert g["geometry"]["regions_held"] == 1 and "prediction" not in g
    # held (colonne 36..63) e train (0..31) sono separati da 4 colonne vuote: due regioni annotate, nessuna mista
    assert g["geometry"]["annotated_regions"] == 2 and g["geometry"]["regions_mixing_held_and_training"] == 0


def test_annotated_regions_mixing():
    held = np.zeros((16, 16), bool); held[:, 8:] = True
    train = np.zeros((16, 16), bool); train[:, :8] = True       # adiacenti: una sola regione annotata, mista
    r = m.annotated_regions(held, train)
    assert r == {"annotated_regions": 1, "regions_mixing_held_and_training": 1}
