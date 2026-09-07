"""Negative tests for the manifest assembler's validation (E02, review R3 finding 1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import e02_manifest as mf  # noqa: E402

SEG = "pherc1667-w029"
TIF = "a" * 64
MJ = "b" * 64


def _sums(seed=42):
    return {f"out/{SEG}_seed{seed}_step075000.tif": TIF, f"out/metrics_{SEG}_seed{seed}.json": MJ}


def _kaggle(sets=("train",), sha=TIF):
    return {"sha256_pred": sha, "sets": {s: {} for s in sets}, "sets_requested": list(sets)}


def test_clean_sealed_reports_pass():
    mf.validate_reports(SEG, 42, _kaggle(), {"sha256_pred": TIF, "threshold_arg": 91, "sets": {"train": {}}}, {"spearman_train": 0.9}, _sums(), MJ, 91)


def test_held_set_in_sealed_report_is_refused():
    with pytest.raises(ValueError, match="seal"):
        mf.validate_reports(SEG, 42, _kaggle(sets=("held", "train")), None, None, _sums(), MJ, None)
    with pytest.raises(ValueError, match="seal"):
        mf.validate_reports(SEG, 42, _kaggle(), {"sha256_pred": TIF, "threshold_arg": None, "sets": {"held": {}, "train": {}}}, None, _sums(), MJ, None)
    with pytest.raises(ValueError, match="seal"):
        mf.validate_reports(SEG, 43, _kaggle(), None, {"spearman_held": 0.5}, _sums(43), MJ, None)


def test_hash_mismatches_are_refused():
    with pytest.raises(ValueError, match="SHA256SUMS"):
        mf.validate_reports(SEG, 42, _kaggle(), None, None, _sums(), "c" * 64, None)      # metrics JSON tampered
    with pytest.raises(ValueError, match="TIFF hash"):
        mf.validate_reports(SEG, 42, _kaggle(sha="d" * 64), None, None, _sums(), MJ, None)
    with pytest.raises(ValueError, match="different TIFF"):
        mf.validate_reports(SEG, 42, _kaggle(), {"sha256_pred": "e" * 64, "threshold_arg": None, "sets": {"train": {}}}, None, _sums(), MJ, None)


def test_local_report_must_use_frozen_threshold():
    with pytest.raises(ValueError, match="frozen threshold"):
        mf.validate_reports("pherc0814-46527", 42, {"sha256_pred": TIF, "sets": {"held": {}, "train": {}}, "sets_requested": ["held", "train"]},
                            {"sha256_pred": TIF, "threshold_arg": None, "sets": {"held": {}, "train": {}}}, None,
                            {"out/pherc0814-46527_seed42_step075000.tif": TIF, "out/metrics_pherc0814-46527_seed42.json": MJ}, MJ, 91)
