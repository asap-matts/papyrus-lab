"""Tests for the E03 metrics (plan docs/plans/2026-09-07-e03-tolleranza-offset-z.md, step 3).

Written before the implementation. Two of them exist because Codex's R1 review found the defects they cover:
  - finding 1: the frozen E02 helpers clip the threshold index to 255, so a 511-level sweep would report a
    threshold it did not measure. Here the optimum is deliberately placed above 255.
  - finding 4: the seal of pherc1667-w029 must not depend on a folder name. The whitelist is checked against
    the frozen label fingerprint BEFORE any mask is opened.
No network, no real data: synthetic TIFFs and Zarr label folders.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import tifffile
import zarr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import e02_metrics as e02  # noqa: E402
import e03_metrics as e03  # noqa: E402
from tree_sha256 import tree_sha256  # noqa: E402


# --------------------------------------------------------------------------------- 511-level sweep
def test_sweep_n_accepts_any_number_of_levels():
    pos = np.zeros(511, np.int64); neg = np.zeros(511, np.int64)
    pos[300] = 3; neg[100] = 3
    sw = e03.sweep_n(pos, neg)
    assert sw["f1"].shape == (511,)


def test_best_f1_above_255_is_measured_not_clipped():
    """Il difetto trovato da Codex (R1, finding 1): con gli helper di E02 la stessa curva riporta la soglia
    chiesta ma le statistiche dell'indice 255. Qui devono coincidere."""
    pos = np.zeros(511, np.int64); neg = np.zeros(511, np.int64)
    pos[400] = 7            # tutti i positivi molto in alto
    neg[300] = 5            # negativi appena sotto: F1 vale 1 per ogni soglia in 301..400
    sw = e03.sweep_n(pos, neg)
    best = e03.best_f1_n(sw)
    assert best["f1"] == 1.0
    assert best["threshold"] == 301                      # soglia piu' bassa fra i massimi, comunque oltre 255
    at = e03.at_threshold_n(sw, best["threshold"])
    assert at["tp"] == 7 and at["fp"] == 0 and at["fn"] == 0 and at["f1"] == 1.0
    assert e03.at_threshold_n(sw, 400)["tp"] == 7        # ogni soglia del plateau e' misurabile davvero
    # a 255 i numeri sono diversi: se lo script tagliasse l'indice a 255, riporterebbe questi
    assert e03.at_threshold_n(sw, 255)["fp"] == 5


def test_at_threshold_n_refuses_an_out_of_range_threshold():
    sw = e03.sweep_n(np.ones(511, np.int64), np.ones(511, np.int64))
    with pytest.raises(ValueError):
        e03.at_threshold_n(sw, 511)
    with pytest.raises(ValueError):
        e03.at_threshold_n(sw, -1)


def test_best_f1_n_keeps_the_lowest_threshold_among_maxima():
    pos = np.zeros(511, np.int64); neg = np.zeros(511, np.int64)
    pos[[200, 210, 220]] = 1; neg[[10, 20, 30]] = 1
    b = e03.best_f1_n(e03.sweep_n(pos, neg))
    assert b["f1"] == 1.0 and b["threshold"] == 31


def test_sweep_n_matches_e02_on_256_levels():
    rng = np.random.default_rng(3)
    pos = rng.integers(0, 40, 256).astype(np.int64); neg = rng.integers(0, 40, 256).astype(np.int64)
    a, b = e03.sweep_n(pos, neg), e02.sweep(pos, neg)
    for key in ("tp", "fp", "fn", "tn", "precision", "recall", "f1", "iou"):
        assert np.allclose(a[key], b[key])
    assert e03.best_f1_n(a) == e02.best_f1(b)


# --------------------------------------------------------------------------------- fixtures
def _labels(tmp_path: Path, name: str, shape=(21, 40, 48), seed=0) -> Path:
    """Cartella di label sintetica con lo stesso schema del dataset ufficiale."""
    rng = np.random.default_rng(seed)
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    plane = shape[0] // 2
    ink = np.zeros(shape, np.uint8); train = np.zeros(shape, np.uint8); held = np.zeros(shape, np.uint8)
    train[plane, :, :20] = 1
    held[plane, :, 28:] = 1
    ink[plane, 5:15, 2:10] = 1
    ink[plane, 5:25, 30:40] = 1
    for kind, arr in (("inklabels", ink), ("supervision_mask", train), ("validation_mask", held)):
        g = zarr.open_group(str(d / f"{name}_{kind}.zarr"), mode="w")
        g.create_dataset("0", data=arr, chunks=shape, dtype=np.uint8)
    return d


def _pred(tmp_path: Path, name: str, labels_dir: Path, seed=0) -> Path:
    rng = np.random.default_rng(seed)
    ink = np.asarray(zarr.open(str(labels_dir / f"{labels_dir.name}_inklabels.zarr"), mode="r")["0"])
    plane = ink.shape[0] // 2
    p = rng.integers(30, 90, ink.shape[1:]).astype(np.uint8)
    p[ink[plane] > 0] = rng.integers(140, 220, int((ink[plane] > 0).sum())).astype(np.uint8)
    path = tmp_path / name
    tifffile.imwrite(str(path), p, compression="lzw")
    return path


@pytest.fixture()
def seg(tmp_path, monkeypatch):
    """Un segmento sintetico ammesso dalla lista bianca (l'elenco reale resta congelato nello script)."""
    d = _labels(tmp_path, "seg-dev")
    digest, _ = tree_sha256(d)
    monkeypatch.setattr(e03, "LABEL_ALLOWLIST", {"seg-dev": digest})
    return d


# --------------------------------------------------------------------------------- whitelist (seal)
def test_labels_outside_the_allowlist_are_refused_before_any_mask_is_opened(tmp_path, monkeypatch):
    d = _labels(tmp_path, "pherc1667-w029")
    monkeypatch.setattr(e03, "LABEL_ALLOWLIST", {"seg-dev": "0" * 64})
    opened = []
    monkeypatch.setattr(e03.e02, "centre_plane", lambda p: opened.append(p) or np.zeros((4, 4), bool))
    with pytest.raises(ValueError, match="lista bianca"):
        e03.check_labels_allowed(d)
    assert opened == []


def test_labels_with_a_different_fingerprint_are_refused(tmp_path, monkeypatch):
    d = _labels(tmp_path, "seg-dev")
    monkeypatch.setattr(e03, "LABEL_ALLOWLIST", {"seg-dev": "0" * 64})
    with pytest.raises(ValueError, match="impronta"):
        e03.check_labels_allowed(d)


def test_the_real_allowlist_holds_only_the_two_development_segments():
    assert set(e03.LABEL_ALLOWLIST) == {"pherc0139-w016", "pherc0814-46527"}
    assert all(len(h) == 64 for h in e03.LABEL_ALLOWLIST.values())


# --------------------------------------------------------------------------------- --average
def test_average_of_a_tiff_with_itself_reproduces_the_e02_report(tmp_path, seg):
    """La media di X con X e' X: stessa AUROC, stessa best-F1 e, alla soglia congelata, gli stessi conteggi.
    Sulla somma tutti i valori sono pari, quindi le soglie 2t-1 e 2t selezionano gli stessi pixel e la regola
    'soglia piu' bassa fra i massimi' sceglie la dispari: e' equivalente, non un'incoerenza."""
    pred = _pred(tmp_path, "x.tif", seg)
    ref = e02.build_report(pred, seg, sets=("held", "train"), threshold=91)
    rep = e03.build_average_report([pred, pred], seg, sets=("held", "train"), threshold_mean=91)
    for s in ("held", "train"):
        a, b = rep["sets"][s], ref["sets"][s]
        assert abs(a["auroc"] - b["auroc"]) < 1e-12
        assert abs(a["best_f1"]["f1"] - b["best_f1"]["f1"]) < 1e-12
        assert a["best_f1"]["threshold_sum"] in (2 * b["best_f1"]["threshold"] - 1, 2 * b["best_f1"]["threshold"])
        assert a["best_f1"]["threshold_mean"] * 2 == a["best_f1"]["threshold_sum"]
        assert abs(a["best_f1"]["precision"] - b["best_f1"]["precision"]) < 1e-12
        assert abs(a["best_f1"]["recall"] - b["best_f1"]["recall"]) < 1e-12
        # alla soglia congelata (media 91 = somma 182) i conteggi devono coincidere esattamente
        assert a["at_threshold"]["tp"] == b["at_threshold"]["tp"] and a["at_threshold"]["fp"] == b["at_threshold"]["fp"]
        assert a["at_threshold"]["fn"] == b["at_threshold"]["fn"] and a["at_threshold"]["tn"] == b["at_threshold"]["tn"]
        assert abs(a["at_threshold"]["f1"] - b["at_threshold"]["f1"]) < 1e-12
    held_a, held_b = rep["sets"]["held"], ref["sets"]["held"]      # strati e regioni solo sull'held-out
    assert len(held_a["strata"]) == len(held_b["strata"]) and len(held_a["regions"]) == len(held_b["regions"])
    assert held_a["within_patch"] == held_b["within_patch"]
    assert rep["levels"] == 511 and rep["combination"] == "mean_of_two"
    json.loads(e03.dumps(rep))                       # serializzabile


def test_average_keeps_half_points(tmp_path, seg):
    """La media di 100 e 101 e' 100,5: deve stare sopra la soglia media 100,5 e sotto 101."""
    a = np.full((40, 48), 100, np.uint8); b = np.full((40, 48), 101, np.uint8)
    pa, pb = tmp_path / "a.tif", tmp_path / "b.tif"
    tifffile.imwrite(str(pa), a); tifffile.imwrite(str(pb), b)
    rep = e03.build_average_report([pa, pb], seg, sets=("train",), threshold_mean=None, threshold_sum=201)
    assert rep["sets"]["train"]["at_threshold"]["threshold_sum"] == 201
    assert rep["sets"]["train"]["at_threshold"]["tp"] + rep["sets"]["train"]["at_threshold"]["fp"] > 0
    rep2 = e03.build_average_report([pa, pb], seg, sets=("train",), threshold_mean=None, threshold_sum=202)
    assert rep2["sets"]["train"]["at_threshold"]["tp"] + rep2["sets"]["train"]["at_threshold"]["fp"] == 0


def test_threshold_mean_91_is_sum_182(tmp_path, seg):
    pred = _pred(tmp_path, "x.tif", seg)
    rep = e03.build_average_report([pred, pred], seg, sets=("held",), threshold_mean=91)
    assert rep["sets"]["held"]["at_threshold"]["threshold_sum"] == 182
    assert rep["sets"]["held"]["at_threshold"]["threshold_mean"] == 91


def test_average_report_is_deterministic(tmp_path, seg):
    pred = _pred(tmp_path, "x.tif", seg)
    a = e03.build_average_report([pred, pred], seg, sets=("held",), threshold_mean=91)
    b = e03.build_average_report([pred, pred], seg, sets=("held",), threshold_mean=91)
    a.pop("generated_at"); b.pop("generated_at")
    assert e03.dumps(a) == e03.dumps(b)


# --------------------------------------------------------------------------------- --spearman
def test_spearman_of_a_tiff_with_itself_and_with_its_inverse(tmp_path, seg):
    pred = _pred(tmp_path, "x.tif", seg)
    inv = tmp_path / "inv.tif"
    tifffile.imwrite(str(inv), (255 - tifffile.imread(str(pred))).astype(np.uint8))
    same = e03.build_spearman_report([pred, pred], seg, sets=("held", "train"))
    opp = e03.build_spearman_report([pred, inv], seg, sets=("held",))
    assert abs(same["spearman"]["held"] - 1.0) < 1e-12
    assert abs(opp["spearman"]["held"] + 1.0) < 1e-12


# --------------------------------------------------------------------------------- --run wrapper
def test_run_report_wraps_e02_and_adds_the_point(tmp_path, seg):
    pred = _pred(tmp_path, "x.tif", seg)
    ref = e02.build_report(pred, seg, sets=("held", "train"), threshold=91)
    rep = e03.build_run_report(pred, seg, k=-3, seed=42, threshold=91,
                               input_tree_sha256="a" * 64, layer_indices=list(range(2, 19)),
                               source_z_slice=[1, 85], run_id="E03-R01")
    assert rep["sets"]["held"]["auroc"] == ref["sets"]["held"]["auroc"]
    pt = rep["e03_point"]
    assert pt["segment"] == "seg-dev" and pt["seed"] == 42 and pt["k"] == -3 and pt["tag"] == "zm3"
    assert pt["sha256_pred"] == ref["sha256_pred"] and pt["input_tree_sha256"] == "a" * 64
    assert pt["source_z_slice"] == [1, 85] and pt["layer_indices"] == list(range(2, 19))


def test_run_report_refuses_an_offset_not_in_the_matrix(tmp_path, seg):
    pred = _pred(tmp_path, "x.tif", seg)
    with pytest.raises(ValueError, match="offsets.json"):
        e03.build_run_report(pred, seg, k=+1, seed=42, threshold=91, input_tree_sha256="a" * 64,
                             layer_indices=list(range(2, 19)), source_z_slice=[13, 97], run_id="E03-R01")


def test_run_report_refuses_layer_indices_that_contradict_k(tmp_path, seg):
    pred = _pred(tmp_path, "x.tif", seg)
    with pytest.raises(ValueError, match="indici"):
        e03.build_run_report(pred, seg, k=-3, seed=42, threshold=91, input_tree_sha256="a" * 64,
                             layer_indices=list(range(0, 17)), source_z_slice=[1, 85], run_id="E03-R01")


def test_run_report_refuses_a_source_window_that_contradicts_k(tmp_path, seg):
    pred = _pred(tmp_path, "x.tif", seg)
    with pytest.raises(ValueError, match="finestra"):
        e03.build_run_report(pred, seg, k=-3, seed=42, threshold=91, input_tree_sha256="a" * 64,
                             layer_indices=list(range(2, 19)), source_z_slice=[13, 97], run_id="E03-R01")
