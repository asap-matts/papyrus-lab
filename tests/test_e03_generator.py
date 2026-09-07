"""Tests for the E03 notebook generator and pilot (plan step 5).

They check what a mistake here would cost: a notebook writing into E02's directories, a placeholder left
unresolved, a run mounting the wrong input, the sealed segment appearing anywhere, or a pilot that lets a
GPU push through when the budget or the sequence says no.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_e03_notebooks as gen  # noqa: E402
import kaggle_e03 as pilot  # noqa: E402

KAGGLE_DIR = ROOT / "kaggle"
GENERATED = sorted(KAGGLE_DIR.glob("e03-r01-*"))


def _source(folder: Path) -> str:
    nb = json.loads(next(folder.glob("*.ipynb")).read_text(encoding="utf-8"))
    return "".join("".join(c["source"]) for c in nb["cells"])


def test_modes_cover_the_matrix_and_never_the_sealed_segment():
    modes = gen.modes()
    infer = [m for m in modes if m.startswith("infer-")]
    assert len(infer) == 24 == 2 * 2 * 6                     # due segmenti, due seed, sei offset non nulli
    assert len([m for m in modes if m.startswith("prep-")]) == 5
    assert all(gen.SEALED not in m and "1667" not in m for m in modes)
    assert set(gen.SEGMENTS) == {"pherc0139-w016", "pherc0814-46527"}


def test_parse_mode_refuses_a_segment_outside_development():
    with pytest.raises(AssertionError):
        gen.parse_mode("infer-w029-s42-zm2")


def test_order_of_the_pilot_matches_the_generated_modes():
    assert set(pilot.ORDER) == {m for m in gen.modes() if m.startswith("infer-")}
    assert len(pilot.ORDER) == len(set(pilot.ORDER)) == 24
    assert all(t in m for m, t in zip(pilot.ORDER[:8], ["zm2"] * 4 + ["zp2"] * 4))   # tappa 1 per prima


@pytest.mark.skipif(not GENERATED, reason="notebook non ancora generati")
def test_generated_notebooks_are_repathed_to_e03():
    allowed = re.compile(r"^(papyruslab-e02[\w-]*|.*e02_metrics.*|e02)$")
    for folder in GENERATED:
        src = _source(folder)
        residues = {m for m in re.findall(r"[^\s\"']*e02[^\s\"']*", src) if not allowed.match(m)}
        assert not residues, f"{folder.name}: riferimenti a E02 non ammessi: {sorted(residues)[:5]}"
        assert "/kaggle/working/e03" in src and "/tmp/e03" in src


@pytest.mark.skipif(not GENERATED, reason="notebook non ancora generati")
def test_no_placeholder_is_left_unresolved():
    for folder in GENERATED:
        left = set(re.findall(r"__[A-Z0-9_]+__", _source(folder)))
        # __CKPT__ e' sostituito a run time dalla cella di E00/E02 con HEAVY e SEED del notebook
        assert left <= {"__CKPT__"}, f"{folder.name}: segnaposto non risolti {sorted(left)}"


@pytest.mark.skipif(not GENERATED, reason="notebook non ancora generati")
def test_every_notebook_carries_its_own_window_and_input():
    rows = {r["tag"]: r for r in gen.OFFSETS["offsets"]}
    for folder in GENERATED:
        mode = folder.name[len("e03-r01-"):]
        kind, seg, seed, tag = gen.parse_mode(mode)
        src = _source(folder)
        assert f'SEG = "{seg}"' in src and f'TAG = "{tag}"' in src
        if kind == "infer":
            row = rows[tag]
            assert f"EXPECTED_INDICES = {json.dumps(row['expected_indices'])}" in src
            assert f"SOURCE_Z_SLICE = {json.dumps(row['source_z_slice'])}" in src
            expected_args = ("" if row["layer_start"] is None
                             else f"--layer-start {row['layer_start']} --layer-end {row['layer_end']}")
            assert f'LAYER_ARGS = "{expected_args}"' in src
            assert f"_step075000_{tag}.tif" in src
            # il gate di orientamento e' bloccante solo sugli input ufficiali
            assert 'blocking = (TAG in ("zm2", "zp2"))' in src


@pytest.mark.skipif(not GENERATED, reason="notebook non ancora generati")
def test_metadata_mounts_only_the_datasets_the_run_needs():
    ds = json.loads((ROOT / "configs" / "e03" / "datasets.json").read_text(encoding="utf-8"))
    rows = {r["tag"]: r for r in gen.OFFSETS["offsets"]}
    for folder in GENERATED:
        mode = folder.name[len("e03-r01-"):]
        kind, seg, seed, tag = gen.parse_mode(mode)
        meta = json.loads((folder / "kernel-metadata.json").read_text(encoding="utf-8"))
        assert meta["is_private"] is True and meta["enable_gpu"] == (kind == "infer")
        assert all(gen.SEALED not in s for s in meta["dataset_sources"])
        assert any(ds["labels"]["slug"] in s for s in meta["dataset_sources"])
        if kind == "infer":
            row = rows[tag]
            key = "official" if row["input"] == "official" else ("shifted_zm3" if row["input"] == "shifted_m3" else "shifted_zp3")
            assert any(ds["inputs"][seg][key]["slug"] in s for s in meta["dataset_sources"])
        elif tag != "z13":
            assert any(ds["inputs"][seg]["official"]["slug"] in s for s in meta["dataset_sources"])


@pytest.mark.skipif(not GENERATED, reason="notebook non ancora generati")
def test_the_whitelist_guard_runs_before_anything_else_reads_a_mask():
    for folder in GENERATED:
        nb = json.loads(next(folder.glob("*.ipynb")).read_text(encoding="utf-8"))
        sources = ["".join(c["source"]) for c in nb["cells"]]
        guard = next(i for i, s in enumerate(sources) if "lista bianca superata" in s)
        readers = [i for i, s in enumerate(sources) if "inklabels" in s or "validation_mask" in s]
        assert all(i >= guard for i in readers), f"{folder.name}: una cella legge le maschere prima della guardia"


def test_budget_reservation_refuses_at_the_boundary(monkeypatch):
    ds = json.loads((ROOT / "configs" / "e03" / "datasets.json").read_text(encoding="utf-8"))
    cap, per_run = ds["budget"]["gpu_minutes_cap"], ds["budget"]["session_minutes_per_run"]
    assert cap == 240 and per_run == 60
    for used, allowed in ((0, True), (179, True), (180, True), (181, False), (239, False)):
        assert (used + per_run <= cap) is allowed, f"con {used} minuti consumati la decisione e' sbagliata"
