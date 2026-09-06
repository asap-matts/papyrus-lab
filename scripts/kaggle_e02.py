#!/usr/bin/env python3
"""Drive the E02 Kaggle runs from the command line (plan step 5-8). Same pattern as scripts/kaggle_e00.py (frozen).

  python scripts/kaggle_e02.py push   <mode>               # upload and start (prep-*: CPU, 14400 s; infer-*: T4, 3600 s)
  python scripts/kaggle_e02.py status <mode>
  python scripts/kaggle_e02.py wait   <mode>               # poll every 60 s; exit 0 only on 'complete'
  python scripts/kaggle_e02.py output <mode>               # download to runs/E02-R01/<mode>/<timestamp>/ and verify SHA256SUMS
  python scripts/kaggle_e02.py publish-labels              # runs/E02-R01/dataset-labels -> dataset papyruslab-e02-labels; fills configs/e02/datasets.json
  python scripts/kaggle_e02.py publish-input <short>       # latest prep download -> dataset papyruslab-e02-input-<short>; fills datasets.json
  python scripts/kaggle_e02.py publish-seed42-out <short>  # latest infer-<short>-seed42 download -> dataset ...-seed42-out; fills datasets.json

Modes come from scripts/build_e02_notebooks.py. Before `push infer-*` the pilot checks that the label and input
datasets are `ready` and that their hashes are in configs/e02/datasets.json; before `push infer-*-seed43` it also
requires a verified local seed42 download with both gates passed. A GPU push consumes the account owner's GPU
quota: run it only on an explicit go. Every download goes to a new timestamped folder.
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
sys.path.insert(0, str(ROOT / "scripts"))
import build_e02_notebooks as gen  # noqa: E402

DATASETS = ROOT / "configs" / "e02" / "datasets.json"
RUN_ID = "e02-r01"
TIMEOUTS = {"prep": 14400, "infer": 3600}
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass
KAGGLE = [shutil.which("kaggle")] if shutil.which("kaggle") else [sys.executable, "-m", "kaggle"]


def load_ds() -> dict:
    return json.loads(DATASETS.read_text(encoding="utf-8"))


def save_ds(ds: dict) -> None:
    with open(DATASETS, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(ds, indent=2, ensure_ascii=False) + "\n")


def folder(mode: str) -> Path:
    return ROOT / "kaggle" / f"{RUN_ID}-{mode}"


def meta(mode: str) -> dict:
    p = folder(mode) / "kernel-metadata.json"
    if not p.exists():
        sys.exit(f"notebook per {mode} non generato: python scripts/build_e02_notebooks.py")
    return json.loads(p.read_text(encoding="utf-8"))


def kernel_id(mode: str) -> str:
    return meta(mode)["id"]


def runs_dir() -> Path:
    return ROOT / "runs" / RUN_ID.upper()


def run(cmd: list[str], check: bool = True) -> str:
    print("$", " ".join(cmd), flush=True)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    print("\n".join(l for l in out.splitlines() if "DeprecationWarning" not in l and "trace-deprecation" not in l).strip(), flush=True)
    if check and p.returncode != 0:
        sys.exit(f"comando fallito (exit {p.returncode})")
    return out


def required_outputs(mode: str) -> list[str]:
    kind, seg, seed = gen.parse_mode(mode)
    if kind == "prep":
        return ["logs/run_info.txt", "logs/install.json", "logs/label_count.txt", f"logs/prep_{seg}.log", f"out/{seg}_pooled.tar", f"out/prep_manifest_{seg}.json"]
    req = ["logs/run_info.txt", "logs/install.json", "logs/checkpoints_sha256.txt", "logs/label_count.txt", f"logs/infer_seed{seed}.log",
           f"out/{seg}_seed{seed}_step075000.tif", f"out/metrics_{seg}_seed{seed}.json"]
    if seed == 43:
        req.append(f"out/compare_seeds_{seg}.json")
    return req


def latest_download(mode: str) -> Path | None:
    base = runs_dir() / mode
    if not base.is_dir():
        return None
    cands = sorted(p for p in base.iterdir() if p.is_dir() and (p / "e02" / "out" / "SHA256SUMS").exists())
    return cands[-1] if cands else None


def dataset_status(ds_id: str) -> str:
    out = run([*KAGGLE, "datasets", "status", ds_id], check=False)
    return "ready" if "ready" in out.lower() else out.strip().splitlines()[-1] if out.strip() else "unknown"


def push(mode: str) -> None:
    m = meta(mode)
    kind, seg, seed = gen.parse_mode(mode)
    ds = load_ds()
    user = ds["owner"]
    lab = ds["labels"]["segments"][seg]
    assert lab["tree_sha256"], "costanti delle label mancanti in datasets.json"
    if kind == "infer":
        inp = ds["inputs"][seg]
        if not inp["tree_sha256"]:
            sys.exit(f"push rifiutato: input poolato di {seg} senza hash (eseguire prep e publish-input)")
        for ds_id in (f"{user}/{ds['labels']['slug']}", f"{user}/{inp['slug']}"):
            st = dataset_status(ds_id)
            if st != "ready":
                sys.exit(f"push rifiutato: dataset {ds_id} non 'ready' ({st})")
        if seed == 43:
            d = latest_download(f"infer-{gen.SEGMENTS[seg]['short']}-seed42")
            if d is None:
                sys.exit("push rifiutato: scaricare prima l'output del seed42 dello stesso segmento")
            r42 = json.loads((d / "e02" / "out" / f"metrics_{seg}_seed42.json").read_text(encoding="utf-8"))
            if r42.get("gate_A") != "superato" or r42.get("gate_B") != "superato":
                sys.exit(f"push rifiutato: seed42 con gate_A={r42.get('gate_A')} gate_B={r42.get('gate_B')}")
            if not ds["seed42_outputs"][seg]["sha256_tif"]:
                sys.exit("push rifiutato: pubblicare prima l'output del seed42 (publish-seed42-out)")
            st = dataset_status(f"{user}/{ds['seed42_outputs'][seg]['slug']}")
            if st != "ready":
                sys.exit(f"push rifiutato: dataset seed42-out non 'ready' ({st})")
        print(f"ATTENZIONE: {mode} consuma quota GPU: procedere solo con il via esplicito di Matteo", flush=True)
    cmd = [*KAGGLE, "kernels", "push", "-p", str(folder(mode)), "-t", str(TIMEOUTS[kind])]
    if m.get("enable_gpu"):
        cmd += ["--accelerator", m.get("machine_shape", "NvidiaTeslaT4")]
    run(cmd)


def status(mode: str) -> str:
    out = run([*KAGGLE, "kernels", "status", kernel_id(mode)], check=False)
    m = re.search(r'status\s+"?(?:KernelWorkerStatus\.)?(\w+)"?', out)
    return m.group(1).lower() if m else "unknown"


def wait(mode: str, every: int = 60, max_minutes: int = 300) -> str:
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
        sys.exit(2)


def output(mode: str) -> None:
    dest = runs_dir() / mode / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest.mkdir(parents=True, exist_ok=True)
    run([*KAGGLE, "kernels", "output", kernel_id(mode), "-p", str(dest)])
    sums = next(dest.rglob("SHA256SUMS"), None)
    if sums is None:
        print(f"SHA256SUMS non trovato: il run non ha raggiunto la persistenza. Log e output parziali in {dest}")
        sys.exit(1)
    base = sums.parent.parent
    bad, listed = 0, set()
    lines = [l for l in sums.read_text(encoding="utf-8").splitlines() if l.strip()]
    for line in lines:
        h, p = line.split(None, 1)
        p = p.strip().lstrip("*"); listed.add(p)
        f = base / p
        if not (f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == h):
            bad += 1; print("DIFFERISCE o manca:", p)
    missing = [r for r in required_outputs(mode) if r not in listed]
    print(f"file verificati: {len(lines)}; differenze: {bad}; richiesti mancanti: {missing or 'nessuno'}; cartella: {base}")
    if bad or missing:
        sys.exit(1)


def create_or_version(ds_dir: Path, message: str) -> None:
    out = run([*KAGGLE, "datasets", "create", "-p", str(ds_dir)], check=False)
    if "already exists" in out.lower() or "409" in out:
        run([*KAGGLE, "datasets", "version", "-p", str(ds_dir), "-m", message])


def publish_labels() -> None:
    src = runs_dir() / "dataset-labels"
    man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    ds = load_ds()
    for seg, s in man["segments"].items():
        assert seg in ds["labels"]["segments"], seg
        ds["labels"]["segments"][seg].update({"file_count": s["file_count"], "byte_total": s["byte_total"], "tree_sha256": s["tree_sha256"], "tar_sha256": s["tar_sha256"]})
    save_ds(ds)
    create_or_version(src, "update E02 labels")
    print("datasets.json aggiornato con le costanti delle label; dataset", f"{ds['owner']}/{ds['labels']['slug']}")


def publish_input(short: str) -> None:
    seg = gen.SHORT_TO_SEG[short]
    d = latest_download(f"prep-{short}")
    if d is None:
        sys.exit(f"nessun output verificato di prep-{short}: eseguire prima 'output prep-{short}'")
    man = json.loads((d / "e02" / "out" / f"prep_manifest_{seg}.json").read_text(encoding="utf-8"))
    tar = d / "e02" / "out" / man["tar_name"]
    sha = hashlib.sha256(tar.read_bytes()).hexdigest()
    assert sha == man["tar_sha256"], f"tar locale {sha} != manifest {man['tar_sha256']}"
    ds = load_ds()
    ds_dir = runs_dir() / f"dataset-input-{short}"
    if ds_dir.exists():
        shutil.rmtree(ds_dir)
    ds_dir.mkdir(parents=True)
    shutil.copy2(tar, ds_dir / tar.name)
    shutil.copy2(d / "e02" / "out" / f"prep_manifest_{seg}.json", ds_dir / "manifest.json")
    (ds_dir / "dataset-metadata.json").write_text(json.dumps({"title": f"PapyrusLab {RUN_ID.upper()} pooled input {seg}",
        "id": f"{ds['owner']}/{ds['inputs'][seg]['slug']}", "licenses": [{"name": "other"}]}, indent=2) + "\n", encoding="utf-8")
    create_or_version(ds_dir, f"update pooled input {seg}")
    ds["inputs"][seg].update({"tree_sha256": man["tree_sha256"], "tar_sha256": man["tar_sha256"], "tar_bytes": man["tar_bytes"]})
    assert ds["inputs"][seg]["shape"] == man["shape"], f"forma {man['shape']} diversa da quella attesa {ds['inputs'][seg]['shape']}"
    save_ds(ds)
    print(f"dataset {ds['owner']}/{ds['inputs'][seg]['slug']} pubblicato; tree_sha256 {man['tree_sha256']} scritto in datasets.json")


def publish_seed42_out(short: str) -> None:
    seg = gen.SHORT_TO_SEG[short]
    d = latest_download(f"infer-{short}-seed42")
    if d is None:
        sys.exit("nessun output seed42 verificato in locale")
    out_dir, logs = d / "e02" / "out", d / "e02" / "logs"
    m = json.loads((out_dir / f"metrics_{seg}_seed42.json").read_text(encoding="utf-8"))
    tif = out_dir / f"{seg}_seed42_step075000.tif"
    sha = hashlib.sha256(tif.read_bytes()).hexdigest()
    assert sha == m["sha256_pred"], f"SHA-256 del TIFF locale ({sha}) diverso da quello nelle metriche ({m['sha256_pred']})"
    ds = load_ds()
    ds_dir = runs_dir() / f"dataset-{short}-seed42-out"
    if ds_dir.exists():
        shutil.rmtree(ds_dir)
    ds_dir.mkdir(parents=True)
    for f in (out_dir / f"metrics_{seg}_seed42.json", tif, logs / "infer_seed42.log"):
        shutil.copy2(f, ds_dir / f.name)
    (ds_dir / "dataset-metadata.json").write_text(json.dumps({"title": f"PapyrusLab {RUN_ID.upper()} {seg} seed42 output",
        "id": f"{ds['owner']}/{ds['seed42_outputs'][seg]['slug']}", "licenses": [{"name": "other"}]}, indent=2) + "\n", encoding="utf-8")
    create_or_version(ds_dir, f"update seed42 output {seg}")
    ds["seed42_outputs"][seg]["sha256_tif"] = sha
    save_ds(ds)
    print(f"dataset {ds['owner']}/{ds['seed42_outputs'][seg]['slug']} pubblicato (privato); TIFF sha256 {sha}")


def main() -> None:
    global RUN_ID
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", default=RUN_ID)
    ap.add_argument("action", choices=["push", "status", "wait", "output", "publish-labels", "publish-input", "publish-seed42-out"])
    ap.add_argument("target", nargs="?", help="mode (push/status/wait/output) or segment short id (publish-input/publish-seed42-out)")
    a = ap.parse_args()
    RUN_ID = a.run_id
    if a.action == "publish-labels":
        publish_labels(); return
    if a.target is None:
        ap.error("target richiesto per questa azione")
    if a.action == "publish-input":
        publish_input(a.target); return
    if a.action == "publish-seed42-out":
        publish_seed42_out(a.target); return
    assert a.target in gen.modes(), f"modo sconosciuto {a.target}; validi: {gen.modes()}"
    {"push": push, "status": lambda m: print(status(m)), "wait": wait_cmd, "output": output}[a.action](a.target)


if __name__ == "__main__":
    main()
