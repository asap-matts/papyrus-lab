#!/usr/bin/env python3
"""Drive the E00/E01 Kaggle runs from the command line (no clicks).

Wraps the official `kaggle` CLI (kernels push / status / output, datasets create / version).
Requires a Kaggle token (`kaggle auth login`, or ~/.kaggle/access_token).

  python scripts/kaggle_e00.py [--run-id e00-r01] push   preflight|seed42|seed43   # upload and start the run
  python scripts/kaggle_e00.py [--run-id ...]     status <mode>                    # one status line
  python scripts/kaggle_e00.py [--run-id ...]     wait   <mode>                    # poll every 60 s; exit 0 only on 'complete'
  python scripts/kaggle_e00.py [--run-id ...]     output <mode>                    # download to runs/<RUN-ID>/<mode>/<timestamp>/ and verify SHA256SUMS
  python scripts/kaggle_e00.py [--run-id ...]     publish-seed42-out              # publish the latest seed42 output as a private dataset (needed by seed43)

Platform timeouts (seconds) are a second guard on top of the 1800 s inner timeout of the inference:
preflight 1800, GPU runs 3600. A GPU push consumes the account owner's GPU quota: run it only on an
explicit go. Every download goes to a new timestamped folder so failed attempts keep their logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ID = "e00-r01"
TIMEOUTS = {"preflight": 1800, "seed42": 3600, "seed43": 3600}
REQUIRED_OUTPUTS = {
    "preflight": ["logs/run_info.txt", "logs/install.json", "logs/checkpoints_sha256.txt", "logs/label_count.txt", "logs/label_counts.json"],
    "seed42": ["logs/run_info.txt", "logs/infer_seed42.log", "out/w035_seed42_step075000.tif", "out/metrics_seed42.json"],
    "seed43": ["logs/run_info.txt", "logs/infer_seed43.log", "out/w035_seed43_step075000.tif", "out/metrics_seed43.json", "out/compare_seeds.json"],
}
# Windows console may not encode every character the Kaggle CLI prints (progress bars, arrows)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

RUN_ID = DEFAULT_RUN_ID
# On macOS a `pip install --user kaggle` often lands outside PATH: fall back to `python -m kaggle`.
KAGGLE = [shutil.which("kaggle")] if shutil.which("kaggle") else [sys.executable, "-m", "kaggle"]


def folder(mode: str) -> Path:
    return ROOT / "kaggle" / f"{RUN_ID}-{mode}"


def meta(mode: str) -> dict:
    return json.loads((folder(mode) / "kernel-metadata.json").read_text(encoding="utf-8"))


def kernel_id(mode: str) -> str:
    return meta(mode)["id"]


def runs_dir() -> Path:
    return ROOT / "runs" / RUN_ID.upper()


def run(cmd: list[str], check: bool = True) -> str:
    print("$", " ".join(cmd), flush=True)
    # PYTHONUTF8=1: the Kaggle CLI writes the kernel log with the locale encoding; on Windows (cp1252)
    # non-Latin characters in the log make that write fail and leave an empty .log file.
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    print("\n".join(l for l in out.splitlines() if "DeprecationWarning" not in l and "trace-deprecation" not in l).strip(), flush=True)
    if check and p.returncode != 0:
        sys.exit(f"comando fallito (exit {p.returncode})")
    return out


def latest_download(mode: str) -> Path | None:
    base = runs_dir() / mode
    if not base.is_dir():
        return None
    cands = sorted(p for p in base.iterdir() if p.is_dir() and (p / "e00" / "out" / "SHA256SUMS").exists())
    return cands[-1] if cands else None


def push(mode: str) -> None:
    m = meta(mode)
    if mode == "seed43":
        d = latest_download("seed42")
        if d is None:
            sys.exit("seed43 rifiutato: scaricare prima l'output di seed42 (python scripts/kaggle_e00.py output seed42)")
        gate = json.loads((d / "e00" / "out" / "metrics_seed42.json").read_text(encoding="utf-8")).get("gate_B")
        if gate != "superato":
            sys.exit(f"seed43 rifiutato: il run seed42 ha gate_B={gate!r}, non 'superato'")
    cmd = [*KAGGLE, "kernels", "push", "-p", str(folder(mode)), "-t", str(TIMEOUTS[mode])]
    if m.get("enable_gpu"):
        cmd += ["--accelerator", m.get("machine_shape", "NvidiaTeslaT4")]
    run(cmd)


def status(mode: str) -> str:
    out = run([*KAGGLE, "kernels", "status", kernel_id(mode)], check=False)
    # Kaggle CLI 2.2.4 prints e.g.: <kernel> has status "KernelWorkerStatus.ERROR"
    m = re.search(r'status\s+"?(?:KernelWorkerStatus\.)?(\w+)"?', out)
    return m.group(1).lower() if m else "unknown"


def wait(mode: str, every: int = 60, max_minutes: int = 90) -> str:
    start = time.time(); unknown = 0
    while True:
        st = status(mode)
        print(f"[{time.strftime('%H:%M:%S')}] {mode}: {st}", flush=True)
        if st in {"complete", "error", "cancel_acknowledged", "cancelacknowledged", "cancelled"}:
            return st
        unknown = unknown + 1 if st == "unknown" else 0
        if unknown >= 5:
            return "status_unavailable"
        if (time.time() - start) / 60 > max_minutes:
            return "timeout_polling"
        time.sleep(every)


def wait_cmd(mode: str) -> None:
    st = wait(mode)
    print(st)
    if st != "complete":
        sys.exit(2)           # any state other than a clean completion is a non-zero exit for callers


def output(mode: str) -> None:
    dest = runs_dir() / mode / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest.mkdir(parents=True, exist_ok=True)
    run([*KAGGLE, "kernels", "output", kernel_id(mode), "-p", str(dest)])
    sums = next(dest.rglob("SHA256SUMS"), None)
    if sums is None:
        print(f"SHA256SUMS non trovato negli output: il run non ha raggiunto il passo 10. Log e output parziali in {dest}")
        sys.exit(1)
    base = sums.parent.parent  # SHA256SUMS sits in <base>/out/; paths inside are relative to <base>
    bad = 0
    lines = [l for l in sums.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        sys.exit("SHA256SUMS vuoto: persistenza non verificabile")
    listed = set()
    for line in lines:
        h, p = line.split(None, 1)
        p = p.strip().lstrip("*"); listed.add(p)
        f = base / p
        ok = f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == h
        if not ok:
            bad += 1
            print("DIFFERISCE o manca:", p)
    missing = [r for r in REQUIRED_OUTPUTS[mode] if r not in listed]
    print(f"file verificati: {len(lines)}; differenze: {bad}; richiesti mancanti: {missing or 'nessuno'}; cartella: {base}")
    if bad or missing:
        sys.exit(1)


def publish_seed42_out() -> None:
    """Publish metrics, TIFF and log of the latest verified seed42 download as a private dataset for the seed43 run."""
    d = latest_download("seed42")
    if d is None:
        sys.exit("nessun output seed42 verificato in locale: eseguire prima 'output seed42'")
    src_out, src_logs = d / "e00" / "out", d / "e00" / "logs"
    m = json.loads((src_out / "metrics_seed42.json").read_text(encoding="utf-8"))
    tif = src_out / "w035_seed42_step075000.tif"
    sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    if sha != m["sha256_tif"]:
        sys.exit(f"SHA-256 del TIFF locale ({sha}) diverso da quello nelle metriche ({m['sha256_tif']})")
    user = kernel_id("seed42").split("/")[0]
    ds = runs_dir() / "dataset-seed42-out"
    if ds.exists():
        shutil.rmtree(ds)
    ds.mkdir(parents=True)
    for f in (src_out / "metrics_seed42.json", tif, src_logs / "infer_seed42.log"):
        shutil.copy2(f, ds / f.name)
    (ds / "dataset-metadata.json").write_text(json.dumps({
        "title": f"PapyrusLab {RUN_ID.upper()} seed42 output", "id": f"{user}/papyruslab-{RUN_ID}-seed42-out",
        "licenses": [{"name": "other"}]}, indent=2) + "\n", encoding="utf-8")
    out = run([*KAGGLE, "datasets", "create", "-p", str(ds)], check=False)
    if "already exists" in out.lower() or "409" in out:
        run([*KAGGLE, "datasets", "version", "-p", str(ds), "-m", "update seed42 output"])
    print(f"dataset {user}/papyruslab-{RUN_ID}-seed42-out pubblicato (privato); TIFF sha256 {sha}")


def main() -> None:
    global RUN_ID
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID, help="run identifier matching kaggle/<run-id>-<mode>/ (e.g. e00-r01, e01-r01)")
    ap.add_argument("action", choices=["push", "status", "wait", "output", "publish-seed42-out"])
    ap.add_argument("mode", nargs="?", choices=["preflight", "seed42", "seed43"])
    a = ap.parse_args()
    RUN_ID = a.run_id
    if a.action == "publish-seed42-out":
        publish_seed42_out(); return
    if a.mode is None:
        ap.error("mode richiesto per questa azione")
    {"push": push, "status": lambda m: print(status(m)), "wait": wait_cmd, "output": output}[a.action](a.mode)


if __name__ == "__main__":
    main()
