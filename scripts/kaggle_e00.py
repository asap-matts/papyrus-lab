#!/usr/bin/env python3
"""Drive the E00 Kaggle runs from the command line (no clicks).

Wraps the official `kaggle` CLI (kernels push / status / output). Requires prior `kaggle auth login`.

  python scripts/kaggle_e00.py push   preflight|seed42|seed43     # upload and start the run
  python scripts/kaggle_e00.py status preflight|seed42|seed43     # one status line
  python scripts/kaggle_e00.py wait   preflight|seed42|seed43     # poll every 60 s until finished
  python scripts/kaggle_e00.py output preflight|seed42|seed43     # download to runs/E00-R01/<mode>/ and verify SHA256SUMS

Platform timeouts (seconds) are a second guard on top of the 1800 s inner timeout of the inference:
preflight 1800, GPU runs 3600 (setup + one inference + metrics). A GPU push consumes Matteo's GPU quota:
run it only on his explicit go.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "e00-r01"
# Windows console may not encode every character the Kaggle CLI prints (progress bars, arrows)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass
TIMEOUTS = {"preflight": 1800, "seed42": 3600, "seed43": 3600}


def folder(mode: str) -> Path:
    return ROOT / "kaggle" / f"{RUN_ID}-{mode}"


def kernel_id(mode: str) -> str:
    return json.loads((folder(mode) / "kernel-metadata.json").read_text(encoding="utf-8"))["id"]


def run(cmd: list[str], check: bool = True) -> str:
    print("$", " ".join(cmd), flush=True)
    # PYTHONUTF8=1: the Kaggle CLI writes the kernel log with the locale encoding; on Windows (cp1252)
    # non-Latin characters in the log make that write fail and leave an empty .log file.
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    print(out.strip(), flush=True)
    if check and p.returncode != 0:
        sys.exit(f"comando fallito (exit {p.returncode})")
    return out


REQUIRED_OUTPUTS = {
    "preflight": ["logs/run_info.txt", "logs/install.json", "logs/checkpoints_sha256.txt", "logs/label_count.txt", "logs/label_counts.json"],
    "seed42": ["logs/run_info.txt", "logs/infer_seed42.log", "out/w035_seed42_step075000.tif", "out/metrics_seed42.json"],
    "seed43": ["logs/run_info.txt", "logs/infer_seed43.log", "out/w035_seed43_step075000.tif", "out/metrics_seed43.json", "out/compare_seeds.json"],
}


def push(mode: str) -> None:
    if mode == "seed43":
        m42 = ROOT / "runs" / "E00-R01" / "seed42" / "e00" / "out" / "metrics_seed42.json"
        if not m42.exists():
            sys.exit("seed43 rifiutato: scaricare prima l'output di seed42 (python scripts/kaggle_e00.py output seed42)")
        gate = json.loads(m42.read_text(encoding="utf-8")).get("gate_B")
        if gate != "superato":
            sys.exit(f"seed43 rifiutato: il run seed42 ha gate_B={gate!r}, non 'superato'")
    meta = json.loads((folder(mode) / "kernel-metadata.json").read_text(encoding="utf-8"))
    cmd = ["kaggle", "kernels", "push", "-p", str(folder(mode)), "-t", str(TIMEOUTS[mode])]
    if meta.get("enable_gpu"):
        cmd += ["--accelerator", meta.get("machine_shape", "NvidiaTeslaT4")]
    run(cmd)


def status(mode: str) -> str:
    out = run(["kaggle", "kernels", "status", kernel_id(mode)], check=False)
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
    dest = ROOT / "runs" / "E00-R01" / mode
    dest.mkdir(parents=True, exist_ok=True)
    run(["kaggle", "kernels", "output", kernel_id(mode), "-p", str(dest)])
    sums = next(dest.rglob("SHA256SUMS"), None)
    if sums is None:
        sys.exit("SHA256SUMS non trovato negli output: il run non ha raggiunto il passo 10")
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["push", "status", "wait", "output"])
    ap.add_argument("mode", choices=["preflight", "seed42", "seed43"])
    a = ap.parse_args()
    {"push": push, "status": lambda m: print(status(m)), "wait": wait_cmd, "output": output}[a.action](a.mode)


if __name__ == "__main__":
    main()
