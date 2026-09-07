#!/usr/bin/env python3
"""Pool a 2.4 um surface volume to the ~9.6 um isotropic 21-slice input, with a whole-slice Z shift.

Faithful reproduction of ScrollPrize/villa `ink-detection/scripts/prepare_9um_isotropic_input.py` at commit
3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e (SHA-256 3afff4f240ff6e09227502f3158af2b9d90888e9e646a388d41477a912dd01af),
with one addition required by E03: `--z-start`, which moves the 84-plane source window by a whole number of
pooled slices (4 source planes each). At `--z-start 13` (the default, `ceil((109-84)/2)`) this script must be
byte-identical to the official one: same tiling, same float32 mean, same np.rint, same chunks, same compressor,
same attributes. That identity is verified against the frozen fingerprint of E02
(pherc0814-46527: bc7423431221bf24b247a8ba80d264b0306f816c52b4ecc0d08115a82305ac52) before any shifted input is used.

Villa's code is frozen for PapyrusLab (E00-E02 reproducibility): it is reproduced here, never modified.
Original licence: see https://github.com/ScrollPrize/villa.

Source manifest (plan step 2b, review R1 finding 2). The official pooling only reads source planes 13-96, so the
planes 1-12 and 97-108 -- which feed the three new slices of every shifted input -- have no frozen identity. At
level 2 a chunk is [109, 128, 128]: the whole depth travels anyway, so hashing the full-depth block per tile costs
no extra traffic. `--source-manifest` writes those per-tile hashes, `--verify-source-manifest` checks them and
stops at the first difference.

Usage:
  python scripts/e03_pool_shifted.py <input_zarr|URL> <output.zarr> [--level 2] [--workers 4] [--z-start 13]
                                     [--segment NAME] [--source-manifest OUT.json] [--verify-source-manifest IN.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from numcodecs import Blosc
import zarr

VERSION = "e03_pool_shifted/1.0"
OUTPUT_Z = 21
POOL_Z = 4
INPUT_Z = OUTPUT_Z * POOL_Z          # 84
TILE = 512
CHUNK_XY = 128
OFFICIAL_FORMAT = "level2-zmean4-21slice-v1"


# ------------------------------------------------------------------------------------ villa, reproduced
def centered_slice(length: int, requested: int) -> tuple[int, int]:
    if requested > length:
        raise ValueError(f"Cannot take {requested} centered planes from {length}")
    start = math.ceil((length - requested) / 2)
    return start, start + requested


def open_source_array(path: str, level: str) -> zarr.Array:
    node = zarr.open(path, mode="r")
    if isinstance(node, zarr.Array):
        return node
    if level not in node:
        available = sorted(node.array_keys())
        raise KeyError(f"Pyramid level '{level}' not found in {path}; available: {available}")
    return node[level]


def pool_block(full: np.ndarray, z0: int, z1: int) -> np.ndarray:
    """The official arithmetic: float32 mean of 4 planes, np.rint, uint8. `full` is the full-depth block."""
    block = full[z0:z1].astype(np.float32)
    return np.rint(block.reshape(OUTPUT_Z, POOL_Z, block.shape[1], block.shape[2]).mean(axis=1)).astype(np.uint8)


# ------------------------------------------------------------------------------------ source manifest
def tile_key(y0: int, x0: int) -> str:
    return f"{y0}_{x0}"


def tile_hash(full: np.ndarray) -> str:
    """SHA-256 of the full-depth source block, C-contiguous uint8: covers every plane, 0..shape[0]-1."""
    return hashlib.sha256(np.ascontiguousarray(full, dtype=np.uint8).tobytes()).hexdigest()


def load_manifest(path: Path, segment: str, expect: dict) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    segments = doc.get("segments", {})
    if segment not in segments:
        raise ValueError(f"STOP: manifest {path} has no entry for segment '{segment}' "
                         f"(present: {sorted(segments)})")
    entry = segments[segment]
    for key in ("source", "level", "source_shape_zyx", "tile"):
        if entry.get(key) != expect[key]:
            raise ValueError(f"STOP: manifest {path} disagrees on '{key}': "
                             f"manifest {entry.get(key)!r} vs source {expect[key]!r}")
    return entry


def write_manifest(path: Path, segment: str, entry: dict) -> None:
    path = Path(path)
    doc = {"version": VERSION, "segments": {}}
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc.setdefault("segments", {})
        doc["version"] = VERSION
    doc["segments"][segment] = entry
    doc["segments"] = {k: doc["segments"][k] for k in sorted(doc["segments"])}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


# ------------------------------------------------------------------------------------ run
def run(input_zarr: str, output_zarr: Path | str, *, level: str = "2", workers: int = 4,
        z_start: int | None = None, segment: str | None = None,
        manifest_out: Path | str | None = None, manifest_verify: Path | str | None = None) -> dict:
    output_zarr = Path(output_zarr)
    source = open_source_array(input_zarr, level)
    shape = tuple(int(v) for v in source.shape)
    if source.dtype != np.uint8 or len(shape) != 3:
        raise ValueError(f"Expected 3D uint8 source, got {shape} {source.dtype}")

    z_default, _ = centered_slice(shape[0], INPUT_Z)
    if z_start is None:
        z0 = z_default
    else:
        z0 = int(z_start)
        if z0 < 0 or z0 + INPUT_Z > shape[0]:
            raise ValueError(f"STOP: --z-start {z0} out of range: it must lie in [0, {shape[0] - INPUT_Z}] "
                             f"for a source with {shape[0]} planes")
        if (z0 - z_default) % POOL_Z != 0:
            raise ValueError(f"STOP: --z-start {z0} is not a whole-slice shift from the official {z_default} "
                             f"(a pooled slice is {POOL_Z} source planes)")
    z1 = z0 + INPUT_Z
    shift = (z0 - z_default) // POOL_Z

    if (manifest_out or manifest_verify) and not segment:
        raise ValueError("STOP: --segment is required together with --source-manifest / --verify-source-manifest")

    expect = {"source": str(input_zarr), "level": str(level), "source_shape_zyx": list(shape), "tile": TILE}
    verify_entry = load_manifest(Path(manifest_verify), segment, expect) if manifest_verify else None

    partial = output_zarr.with_name(output_zarr.name + ".partial")
    if output_zarr.exists() or partial.exists():
        raise FileExistsError(f"Refusing to replace {output_zarr} or {partial}")

    attrs = {
        "format": OFFICIAL_FORMAT if shift == 0 else OFFICIAL_FORMAT + "+zshift",
        "source": str(input_zarr),
        "source_level": str(level),
        "source_shape_zyx": list(shape),
        "source_z_slice": [z0, z1],
        "z_pool": "rounded mean of 4 centered source planes",
    }
    if shift != 0:
        attrs["e03_z_shift_slices"] = int(shift)

    group = zarr.open_group(str(partial), mode="w")
    group.attrs.update(attrs)
    target = group.create_dataset(
        "0",
        shape=(OUTPUT_Z, shape[1], shape[2]),
        chunks=(OUTPUT_Z, min(CHUNK_XY, shape[1]), min(CHUNK_XY, shape[2])),
        dtype=np.uint8,
        compressor=Blosc(cname="zstd", clevel=5, shuffle=Blosc.BITSHUFFLE),
        fill_value=0,
    )
    tiles = [
        (y0, min(shape[1], y0 + TILE), x0, min(shape[2], x0 + TILE))
        for y0 in range(0, shape[1], TILE)
        for x0 in range(0, shape[2], TILE)
    ]

    hashes: dict[str, str] = {}
    lock = threading.Lock()

    def process(tile: tuple[int, int, int, int]) -> int:
        y0, y1, x0, x1 = tile
        full = np.asarray(source[:, y0:y1, x0:x1])        # profondita' piena: stessi chunk, nessun traffico in piu'
        if manifest_out or verify_entry is not None:
            digest = tile_hash(full)
            key = tile_key(y0, x0)
            if verify_entry is not None:
                expected = verify_entry["tiles"].get(key)
                if expected is None:
                    raise ValueError(f"STOP: source manifest has no tile {key}")
                if expected != digest:
                    raise ValueError(f"STOP: source manifest mismatch on tile {key} "
                                     f"(planes 0-{shape[0] - 1}): the source changed upstream or is corrupt")
            with lock:
                hashes[key] = digest
        target[:, y0:y1, x0:x1] = pool_block(full, z0, z1)
        return 1

    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for count in ex.map(process, tiles):
            completed += count
            if completed % 50 == 0 or completed == len(tiles):
                print(f"tiles={completed}/{len(tiles)}", flush=True)

    if verify_entry is not None:
        missing = set(verify_entry["tiles"]) - set(hashes)
        if missing:
            raise ValueError(f"STOP: source manifest lists {len(missing)} tiles never read: {sorted(missing)[:5]}")

    partial.replace(output_zarr)
    if manifest_out:
        write_manifest(Path(manifest_out), segment, {
            "source": str(input_zarr), "level": str(level), "source_shape_zyx": list(shape),
            "tile": TILE, "hash_of": "sha256 of the C-contiguous uint8 bytes of source[:, y0:y1, x0:x1] (all planes)",
            "covers_all_source_planes": True, "n_tiles": len(tiles),
            "tiles": {k: hashes[k] for k in sorted(hashes)},
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "version": VERSION,
        })
    print(f"wrote {output_zarr} shape={tuple(target.shape)} z_start={z0} z_shift_slices={shift:+d}")
    return {"shape": tuple(target.shape), "z_start": z0, "z_slice": [z0, z1], "shift": shift,
            "tiles": len(tiles), "attrs": attrs}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input_zarr", help="Surface-volume OME-Zarr group path or URL (or a bare 3D array).")
    p.add_argument("output_zarr", type=Path, help="Output Zarr path; refuses to overwrite.")
    p.add_argument("--level", default="2", help="Input pyramid level to read (default 2).")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--z-start", type=int, default=None,
                   help="First source plane of the 84-plane window; default = the official centred start (13 of 109). "
                        "Must differ from it by a whole number of pooled slices (4 planes).")
    p.add_argument("--segment", default=None, help="Segment name, required with the manifest options.")
    p.add_argument("--source-manifest", type=Path, default=None, help="Write per-tile full-depth source hashes here.")
    p.add_argument("--verify-source-manifest", type=Path, default=None, help="Verify against this manifest while reading.")
    a = p.parse_args(argv)
    try:
        run(a.input_zarr, a.output_zarr, level=a.level, workers=a.workers, z_start=a.z_start,
            segment=a.segment, manifest_out=a.source_manifest, manifest_verify=a.verify_source_manifest)
    except (ValueError, FileExistsError, KeyError) as exc:
        print(str(exc), file=__import__("sys").stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
