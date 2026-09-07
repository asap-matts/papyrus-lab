"""Tests for the E03 shifted pooling (plan docs/plans/2026-09-07-e03-tolleranza-offset-z.md, steps 1, 2 and 2b).

Written before the implementation, as the plan requires. No network: every test builds a small synthetic
source Zarr. The invariants under test are the ones a mistake would silently break: the offset arithmetic,
byte-identity with the official formula at shift zero, slice-to-slice equality between shifted and official
inputs, refusal of out-of-range shifts, and a source manifest that also covers the planes OUTSIDE the
official window 13-96 (review R1, finding 2).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import zarr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import e03_pool_shifted as pool  # noqa: E402

OFFSETS = json.loads((ROOT / "configs" / "e03" / "offsets.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------- step 1: the matrix
def test_offset_matrix_is_consistent():
    """Every row of configs/e03/offsets.json must follow from the pooling and window rules."""
    rows = OFFSETS["offsets"]
    assert [r["k"] for r in rows] == [-5, -3, -2, 0, 2, 3, 5]
    src, pooled, model = OFFSETS["source_planes"], OFFSETS["pooled_slices"], OFFSETS["model_slices"]
    for r in rows:
        z0, z1 = r["source_z_slice"]
        assert z1 - z0 == pooled * 4 and 0 <= z0 and z1 <= src, r
        assert z0 == r["z_start"] and (z0 - OFFSETS["official_z_start"]) == 4 * r["pool_shift_slices"]
        start = 2 if r["layer_start"] is None else r["layer_start"]
        idx = list(range(start, start + model))
        assert idx == r["expected_indices"] and 0 <= idx[0] and idx[-1] <= pooled - 1
        assert r["layer_end"] is None or r["layer_end"] == start + model
        seen = [z0 + 4 * idx[0], z0 + 4 * (idx[-1] + 1)]
        assert seen == r["source_planes_seen"] and seen[1] - seen[0] == 4 * model
        centre = (seen[0] + seen[1]) // 2
        assert centre == r["centre_plane"] == OFFSETS["centre_plane_at_k0"] + 4 * r["k"]
        assert abs(r["micrometres"] - r["k"] * OFFSETS["slice_um"]) < 1e-6
        assert r["tag"] == ("z0" if r["k"] == 0 else ("zm%d" % -r["k"] if r["k"] < 0 else "zp%d" % r["k"]))
        assert r["stage"] == (0 if r["k"] == 0 else (1 if abs(r["k"]) == 2 else 2))
        assert r["input"] == ("official" if r["z_start"] == 13 else ("shifted_m3" if r["z_start"] < 13 else "shifted_p3"))
        assert r["orientation_gate"] == ("bloccante" if abs(r["k"]) == 2 else ("baseline E02" if r["k"] == 0 else "registrato"))


def test_offset_matrix_never_names_the_sealed_segment():
    assert OFFSETS["segments"] == ["pherc0139-w016", "pherc0814-46527"]
    assert OFFSETS["sealed_segment_never_touched"] not in OFFSETS["segments"]


# --------------------------------------------------------------------------------- helpers
def _source(tmp_path: Path, shape=(109, 40, 48), seed=0) -> Path:
    rng = np.random.default_rng(seed)
    data = rng.integers(0, 256, shape, dtype=np.uint8)
    path = tmp_path / "src.zarr"
    g = zarr.open_group(str(path), mode="w")
    g.create_dataset("2", data=data, chunks=(shape[0], 16, 16), dtype=np.uint8)
    return path


def _read(path: Path) -> np.ndarray:
    return np.asarray(zarr.open(str(path), mode="r")["0"][:])


def _official(data: np.ndarray, z0: int) -> np.ndarray:
    """The formula of villa's prepare_9um_isotropic_input.py, written out."""
    block = data[z0:z0 + 84].astype(np.float32)
    return np.rint(block.reshape(21, 4, data.shape[1], data.shape[2]).mean(axis=1)).astype(np.uint8)


# --------------------------------------------------------------------------------- step 2: identity
def test_centered_slice_matches_villa():
    assert pool.centered_slice(109, 84) == (13, 97)
    assert pool.centered_slice(84, 84) == (0, 84)


def test_pool_at_shift_zero_matches_official_formula(tmp_path):
    src = _source(tmp_path)
    data = np.asarray(zarr.open(str(src), mode="r")["2"][:])
    out = tmp_path / "z13.zarr"
    pool.run(str(src), out, level="2", workers=2, z_start=None)
    assert np.array_equal(_read(out), _official(data, 13))


def test_attrs_at_shift_zero_are_exactly_villas(tmp_path):
    src = _source(tmp_path)
    out = tmp_path / "z13.zarr"
    pool.run(str(src), out, level="2", workers=2, z_start=None)
    attrs = dict(zarr.open(str(out), mode="r").attrs)
    assert attrs == {
        "format": "level2-zmean4-21slice-v1",
        "source": str(src),
        "source_level": "2",
        "source_shape_zyx": [109, 40, 48],
        "source_z_slice": [13, 97],
        "z_pool": "rounded mean of 4 centered source planes",
    }


def test_shifted_attrs_declare_the_shift(tmp_path):
    src = _source(tmp_path)
    out = tmp_path / "zm3.zarr"
    pool.run(str(src), out, level="2", workers=2, z_start=1)
    attrs = dict(zarr.open(str(out), mode="r").attrs)
    assert attrs["format"] == "level2-zmean4-21slice-v1+zshift"
    assert attrs["source_z_slice"] == [1, 85] and attrs["e03_z_shift_slices"] == -3


def test_shifted_slices_equal_the_official_ones(tmp_path):
    """The 18 shared slices must be identical, not merely similar: same source planes, same arithmetic."""
    src = _source(tmp_path)
    a0 = _read(tmp_path / "z13.zarr") if (tmp_path / "z13.zarr").exists() else None
    if a0 is None:
        pool.run(str(src), tmp_path / "z13.zarr", level="2", workers=2, z_start=None)
        a0 = _read(tmp_path / "z13.zarr")
    pool.run(str(src), tmp_path / "zm3.zarr", level="2", workers=2, z_start=1)
    pool.run(str(src), tmp_path / "zp3.zarr", level="2", workers=2, z_start=25)
    am3, ap3 = _read(tmp_path / "zm3.zarr"), _read(tmp_path / "zp3.zarr")
    assert np.array_equal(am3[3:21], a0[0:18])
    assert np.array_equal(ap3[0:18], a0[3:21])
    assert not np.array_equal(am3[0:3], a0[0:3])          # le tre slice nuove vengono da piani nuovi


@pytest.mark.parametrize("z_start", [-1, 26, 100])
def test_z_start_out_of_range_is_refused(tmp_path, z_start):
    src = _source(tmp_path)
    with pytest.raises(ValueError):
        pool.run(str(src), tmp_path / "bad.zarr", level="2", workers=2, z_start=z_start)


def test_z_start_not_a_whole_slice_is_refused(tmp_path):
    src = _source(tmp_path)
    with pytest.raises(ValueError):
        pool.run(str(src), tmp_path / "bad.zarr", level="2", workers=2, z_start=14)   # 13 + 1 piano


def test_refuses_to_overwrite(tmp_path):
    src = _source(tmp_path)
    out = tmp_path / "z13.zarr"
    pool.run(str(src), out, level="2", workers=2, z_start=None)
    with pytest.raises(FileExistsError):
        pool.run(str(src), out, level="2", workers=2, z_start=None)


# --------------------------------------------------------------------------------- step 2b: source manifest
def test_source_manifest_is_deterministic_and_covers_all_planes(tmp_path):
    src = _source(tmp_path)
    m1, m2 = tmp_path / "m1.json", tmp_path / "m2.json"
    pool.run(str(src), tmp_path / "a.zarr", level="2", workers=2, z_start=None, segment="seg-a", manifest_out=m1)
    pool.run(str(src), tmp_path / "b.zarr", level="2", workers=2, z_start=1, segment="seg-a", manifest_out=m2)
    d1 = json.loads(m1.read_text(encoding="utf-8"))["segments"]["seg-a"]
    d2 = json.loads(m2.read_text(encoding="utf-8"))["segments"]["seg-a"]
    assert d1["tiles"] == d2["tiles"]                     # le impronte non dipendono dallo spostamento
    assert d1["source_shape_zyx"] == [109, 40, 48] and d1["covers_all_source_planes"] is True
    assert set(d1["tiles"]) == {"0_0"}                    # 40x48 sta in un solo tile da 512


@pytest.mark.parametrize("plane", [5, 50, 100])
def test_manifest_detects_a_changed_plane_inside_and_outside_the_official_window(tmp_path, plane):
    """Il punto del manifest: i piani 1-12 e 97-108 non entrano nel pooling ufficiale ma alimentano
    le slice nuove degli input spostati. Una loro alterazione deve fermare il run."""
    src = _source(tmp_path)
    man = tmp_path / "m.json"
    pool.run(str(src), tmp_path / "a.zarr", level="2", workers=2, z_start=None, segment="seg-a", manifest_out=man)
    arr = zarr.open(str(src), mode="a")["2"]
    arr[plane, 0, 0] = np.uint8((int(arr[plane, 0, 0]) + 1) % 256)
    with pytest.raises(ValueError, match="manifest"):
        pool.run(str(src), tmp_path / "b.zarr", level="2", workers=2, z_start=1, segment="seg-a", manifest_verify=man)


def test_manifest_of_another_segment_is_refused(tmp_path):
    src = _source(tmp_path)
    man = tmp_path / "m.json"
    pool.run(str(src), tmp_path / "a.zarr", level="2", workers=2, z_start=None, segment="seg-a", manifest_out=man)
    with pytest.raises(ValueError, match="manifest"):
        pool.run(str(src), tmp_path / "c.zarr", level="2", workers=2, z_start=1, segment="seg-b", manifest_verify=man)


def test_manifest_refuses_a_different_source_shape(tmp_path):
    man = tmp_path / "m.json"
    src_a = _source(tmp_path / "a", shape=(109, 40, 48))
    (tmp_path / "a").mkdir(exist_ok=True)
    pool.run(str(src_a), tmp_path / "a.zarr", level="2", workers=2, z_start=None, segment="seg-a", manifest_out=man)
    src_b = _source(tmp_path / "b", shape=(109, 32, 32), seed=1)
    with pytest.raises(ValueError, match="manifest"):
        pool.run(str(src_b), tmp_path / "d.zarr", level="2", workers=2, z_start=1, segment="seg-a", manifest_verify=man)


def test_cli_runs_and_reports_the_shift(tmp_path):
    src = _source(tmp_path)
    out = tmp_path / "cli.zarr"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e03_pool_shifted.py"), str(src), str(out),
                        "--level", "2", "--workers", "2", "--z-start", "25"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "z_shift_slices=+3" in r.stdout and out.exists()
