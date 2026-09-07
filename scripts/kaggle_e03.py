#!/usr/bin/env python3
"""Drive the E03 Kaggle runs from the command line (plan step 5-9). Same pattern as the frozen kaggle_e02.py.

  python scripts/kaggle_e03.py push   <mode>                 # upload and start (prep-*: CPU 14400 s; infer-*: T4 3600 s)
  python scripts/kaggle_e03.py status <mode>
  python scripts/kaggle_e03.py wait   <mode>                 # poll every 60 s; exit 0 only on 'complete'
  python scripts/kaggle_e03.py output <mode>                 # download to runs/E03-R01/<mode>/<timestamp>/, verify SHA256SUMS
  python scripts/kaggle_e03.py publish-input <short> <tag>   # latest prep download -> dataset papyruslab-e03-input-<short>-<tag>
  python scripts/kaggle_e03.py publish-manifest              # source manifest produced by prep-w016-z13 -> configs/e03/source_manifest.json
  python scripts/kaggle_e03.py budget                        # GPU minutes already consumed, and what is still allowed

Three guards, all fail-closed:
  * the sealed segment can never appear in a mode, a dataset or a download;
  * the runs of a stage go in the frozen order and each one requires the previous to be downloaded, verified and
    with both gates passed (E02's deviation 7 -- runs started in parallel before the checks -- must not repeat);
  * the GPU ceiling is a RESERVATION, not a tally (review R1, finding 5): a push is refused when the minutes
    already consumed plus the maximum this run may occupy would exceed the cap.
A GPU push consumes the account owner's quota: run it only on Matteo's explicit go, one run at a time.
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
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_e03_notebooks as gen  # noqa: E402

DATASETS = ROOT / "configs" / "e03" / "datasets.json"
SOURCE_MANIFEST = ROOT / "configs" / "e03" / "source_manifest.json"
RUN_ID = "e03-r01"
TIMEOUTS = {"prep": 14400, "infer": 3600}
SEALED = gen.SEALED

# Ordine congelato dei run GPU (piano §4 passo 5): tappa 1 tutta, poi tappa 2. Un push e' ammesso solo se tutti
# i run che lo precedono in questa lista sono stati scaricati, verificati e con i gate superati.
ORDER = ([f"infer-{s}-s{seed}-{t}" for t in ("zm2", "zp2") for s in ("46527", "w016") for seed in (42, 43)]
         + [f"infer-{s}-s{seed}-{t}" for t in ("zm3", "zp3", "zm5", "zp5") for s in ("46527", "w016") for seed in (42, 43)])

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass
KAGGLE = [shutil.which("kaggle")] if shutil.which("kaggle") else [sys.executable, "-m", "kaggle"]


def load_ds() -> dict:
    return json.loads(DATASETS.read_text(encoding="utf-8"))


def save_ds(ds: dict) -> None:
    DATASETS.write_text(json.dumps(ds, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def folder(mode: str) -> Path:
    return ROOT / "kaggle" / f"{RUN_ID}-{mode}"


def meta(mode: str) -> dict:
    p = folder(mode) / "kernel-metadata.json"
    if not p.exists():
        sys.exit(f"{p} assente: eseguire prima 'python scripts/build_e03_notebooks.py'")
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
    print("\n".join(l for l in out.splitlines()
                    if "DeprecationWarning" not in l and "trace-deprecation" not in l).strip(), flush=True)
    if check and p.returncode != 0:
        sys.exit(f"comando fallito (exit {p.returncode})")
    return out


def check_not_sealed(*texts: str) -> None:
    for t in texts:
        if SEALED in str(t) or "w029" in str(t).replace("pherc0139-w016", ""):
            sys.exit(f"STOP: riferimento al segmento sigillato in '{t}': E03 non lo tocca")


def required_outputs(mode: str) -> list[str]:
    kind, seg, seed, tag = gen.parse_mode(mode)
    if kind == "prep":
        req = ["logs/run_info.txt", "logs/install.json", "logs/label_count.txt",
               f"logs/prep_{seg}_{tag}.log", f"out/input_{seg}_{tag}.json"]
        req.append(f"out/{seg}_pooled.tar" if tag == "z13" else f"out/{seg}_pooled_{tag}.tar")
        if tag == "z13":
            req.append(f"out/source_manifest_{seg}.json")
        return req
    return ["logs/run_info.txt", "logs/install.json", "logs/checkpoints_sha256.txt", "logs/label_count.txt",
            f"logs/infer_seed{seed}_{tag}.log", f"out/{seg}_seed{seed}_step075000_{tag}.tif",
            f"out/metrics_{seg}_s{seed}_{tag}.json"]


VERIFIED_MARKER = "VERIFIED.json"


def latest_download(mode: str) -> Path | None:
    """Solo un download che ha superato per intero la verifica di `output()` conta come disponibile: la presenza
    di SHA256SUMS non basta, perche' resta anche quando la verifica fallisce (revisione R2, finding 4)."""
    base = runs_dir() / mode
    if not base.is_dir():
        return None
    cands = sorted(p for p in base.iterdir() if p.is_dir() and (p / VERIFIED_MARKER).exists())
    return cands[-1] if cands else None


def dataset_status(ds_id: str) -> str:
    out = run([*KAGGLE, "datasets", "status", ds_id], check=False)
    return "ready" if "ready" in out.lower() else (out.strip().splitlines()[-1] if out.strip() else "unknown")


# ------------------------------------------------------------------------------------ budget
def _minutes(d: Path) -> float:
    info = (d / "e03" / "logs" / "run_info.txt")
    if not info.exists():
        return 0.0
    txt = info.read_text(encoding="utf-8")
    s = re.search(r"start=(\S+)", txt); e = re.search(r"end=(\S+)", txt)
    if not (s and e):
        return 0.0
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        return (datetime.strptime(e.group(1), fmt) - datetime.strptime(s.group(1), fmt)).total_seconds() / 60
    except ValueError:
        return 0.0


def ledger_path() -> Path:
    return runs_dir() / "gpu_ledger.json"


def load_ledger() -> list[dict]:
    p = ledger_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def reserve(mode: str, minutes: float) -> None:
    """Prenotazione persistente scritta PRIMA del push: un secondo push dello stesso modo, o di un altro, la
    trova gia' contata anche se il run e' ancora in volo (revisione R2, finding 5)."""
    entries = load_ledger()
    entries.append({"mode": mode, "reserved_minutes": minutes,
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    ledger_path().parent.mkdir(parents=True, exist_ok=True)
    ledger_path().write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")


def consumed_minutes(verbose: bool = False) -> float:
    """Quota impegnata: per ogni run GPU vale la durata misurata dei download verificati, oppure -- se il run e'
    stato lanciato e non ancora scaricato -- la prenotazione scritta nel registro. Mai meno del reale."""
    per_mode: dict[str, float] = {}
    for mode in gen.modes():
        if not mode.startswith("infer-"):
            continue
        base = runs_dir() / mode
        if base.is_dir():
            for d in sorted(p for p in base.iterdir() if p.is_dir()):
                m = _minutes(d)
                per_mode[mode] = per_mode.get(mode, 0.0) + m
                if verbose and m:
                    print(f"  {mode:32} {d.name}  {m:6.1f} min (misurato)")
    reserved: dict[str, float] = {}
    for entry in load_ledger():
        reserved[entry["mode"]] = reserved.get(entry["mode"], 0.0) + float(entry["reserved_minutes"])
    for mode, minutes in sorted(reserved.items()):
        measured = per_mode.get(mode, 0.0)
        if minutes > measured:                       # run lanciato e non ancora (interamente) scaricato
            per_mode[mode] = minutes
            if verbose:
                print(f"  {mode:32} {'prenotato':>17}  {minutes:6.1f} min (in volo o non scaricato)")
    total = sum(per_mode.values())
    for entry in load_ds().get("budget", {}).get("manual_entries", []):
        total += float(entry.get("minutes", 0))
        if verbose:
            print(f"  {entry.get('mode', '?'):32} {entry.get('version', '?')}  {entry.get('minutes', 0):6.1f} min "
                  f"(a mano: {entry.get('why', '')})")
    return total


def budget_cmd() -> None:
    b = load_ds()["budget"]
    used = consumed_minutes(verbose=True)
    cap, per_run = float(b["gpu_minutes_cap"]), float(b["session_minutes_per_run"])
    print(f"\nquota GPU consumata: {used:.1f} min su {cap:.0f} (tetto del piano)")
    print(f"prenotazione per il prossimo run: {per_run:.0f} min -> "
          f"{'AMMESSO' if used + per_run <= cap else 'RIFIUTATO'} (consumato + prenotazione = {used + per_run:.1f})")


# ------------------------------------------------------------------------------------ push
def _gates_ok(mode: str) -> tuple[bool, str]:
    d = latest_download(mode)
    if d is None:
        return False, "nessun output scaricato e verificato"
    kind, seg, seed, tag = gen.parse_mode(mode)
    if kind == "prep":
        return ((d / "e03" / "out" / f"input_{seg}_{tag}.json").exists(),
                "manifest dell'input assente" if not (d / "e03" / "out" / f"input_{seg}_{tag}.json").exists() else "")
    p = d / "e03" / "out" / f"metrics_{seg}_s{seed}_{tag}.json"
    if not p.exists():
        return False, "metriche assenti"
    r = json.loads(p.read_text(encoding="utf-8"))
    ok = r.get("gate_A") == "superato" and r.get("gate_B") == "superato"
    return ok, "" if ok else f"gate_A={r.get('gate_A')} gate_B={r.get('gate_B')}"


def push(mode: str) -> None:
    check_not_sealed(mode)
    m = meta(mode)
    kind, seg, seed, tag = gen.parse_mode(mode)
    ds = load_ds()
    user = ds["owner"]
    check_not_sealed(*m["dataset_sources"])

    for ds_id in m["dataset_sources"]:
        st = dataset_status(ds_id)
        if st != "ready":
            sys.exit(f"push rifiutato: dataset {ds_id} non 'ready' ({st})")

    if kind == "infer":
        idx = ORDER.index(mode)
        for earlier in ORDER[:idx]:
            if not folder(earlier).exists():
                sys.exit(f"push rifiutato: il run precedente {earlier} non e' nemmeno generato. L'ordine congelato "
                         f"non si salta: rigenerare i notebook (senza --only) ed eseguirli in sequenza.")
            ok, why = _gates_ok(earlier)
            if not ok:
                sys.exit(f"push rifiutato: il run precedente {earlier} non e' concluso e verificato ({why}). "
                         f"Un run per volta, con i controlli in mezzo (piano §2, deviazione 7 di E02).")
        # il modo corrente non deve essere gia' in volo, e un suo run concluso va prima scaricato e verificato
        st = status(mode)
        if st in {"running", "queued", "pending"}:
            sys.exit(f"push rifiutato: {mode} risulta gia' '{st}' su Kaggle: aspettare la fine, poi 'output {mode}'.")
        if st == "complete" and latest_download(mode) is None:
            sys.exit(f"push rifiutato: {mode} risulta 'complete' ma il suo output non e' stato scaricato e verificato: "
                     f"eseguire 'output {mode}' prima di rilanciarlo.")
        b = ds["budget"]
        per_run = float(b["session_minutes_per_run"])
        used = consumed_minutes()
        if used + per_run > float(b["gpu_minutes_cap"]):
            sys.exit(f"push rifiutato: prenotazione oltre il tetto: impegnato {used:.1f} min + {per_run:.0f} min di "
                     f"sessione > {b['gpu_minutes_cap']} min. Fermarsi e chiedere a Matteo.")
        reserve(mode, per_run)                    # scritta PRIMA del push: un secondo push la trova gia' contata
        print(f"ATTENZIONE: {mode} consuma quota GPU (impegnata finora {used:.1f} min, prenotati altri {per_run:.0f}): "
              f"procedere solo con il via esplicito di Matteo", flush=True)

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
            bad += 1
            print("DIFFERISCE o manca:", p)
    missing = [r for r in required_outputs(mode) if r not in listed]
    for name in listed:
        check_not_sealed(name)
    print(f"file verificati: {len(lines)}; differenze: {bad}; richiesti mancanti: {missing or 'nessuno'}; cartella: {base}")
    if bad or missing:
        print("verifica NON superata: questa cartella non varra' come output disponibile "
              f"(nessun {VERIFIED_MARKER} scritto)")
        sys.exit(1)
    (dest / VERIFIED_MARKER).write_text(json.dumps(
        {"mode": mode, "files": len(lines), "differences": 0, "required_missing": [],
         "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "minutes": round(_minutes(dest), 2)}, indent=1) + "\n", encoding="utf-8")
    print(f"marcatore di verifica scritto: {dest / VERIFIED_MARKER}")


# ------------------------------------------------------------------------------------ publish
def create_or_version(ds_dir: Path, message: str) -> None:
    out = run([*KAGGLE, "datasets", "create", "-p", str(ds_dir)], check=False)
    low = out.lower()
    if "already exists" in low or "already in use" in low or "409" in out:
        run([*KAGGLE, "datasets", "version", "-p", str(ds_dir), "-m", message])
    elif "error" in low:
        sys.exit("creazione del dataset fallita (vedi sopra)")


def publish_labels() -> None:
    """Pubblica il dataset delle label di E03: i soli due segmenti di sviluppo. Quello di E02 contiene anche il
    segmento sigillato e non va montato (revisione R2, finding 1)."""
    src = runs_dir() / "dataset-labels"
    if not src.is_dir():
        sys.exit(f"{src} assente: ricostruire la cartella dalle copie locali verificate delle label")
    man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    ds = load_ds()
    if set(man["segments"]) != set(ds["labels"]["segments"]):
        sys.exit(f"il manifest contiene {sorted(man['segments'])}, attesi {sorted(ds['labels']['segments'])}")
    for p in src.rglob("*"):
        check_not_sealed(p.name)
    for seg, s in man["segments"].items():
        frozen = ds["labels"]["segments"][seg]
        if s["tree_sha256"] != frozen["tree_sha256"] or s["tar_sha256"] != frozen["tar_sha256"]:
            sys.exit(f"STOP: le label di {seg} non coincidono con quelle congelate")
    create_or_version(src, "E03 labels: development segments only")
    print(f"dataset {ds['owner']}/{ds['labels']['slug']} pubblicato (privato), "
          f"con i soli segmenti {sorted(man['segments'])}")


def publish_input(short: str, tag: str) -> None:
    if tag not in ("zm3", "zp3"):
        sys.exit("publish-input accetta solo gli input spostati: zm3 o zp3")
    seg = gen.SHORT_TO_SEG[short]
    check_not_sealed(seg)
    mode = f"prep-{short}-{tag}"
    d = latest_download(mode)
    if d is None:
        sys.exit(f"nessun output verificato di {mode}: eseguire prima 'output {mode}'")
    info = json.loads((d / "e03" / "out" / f"input_{seg}_{tag}.json").read_text(encoding="utf-8"))
    tar = d / "e03" / "out" / f"{seg}_pooled_{tag}.tar"
    sha = hashlib.sha256(tar.read_bytes()).hexdigest()
    if sha != info["tar_sha256"]:
        sys.exit(f"tar locale {sha} != manifest {info['tar_sha256']}")
    ds = load_ds()
    entry = ds["inputs"][seg][f"shifted_{tag}"]
    if entry["shape"] != info["shape"]:
        sys.exit(f"forma {info['shape']} diversa da quella attesa {entry['shape']}")
    local = entry.get("local_tree_sha256")
    if local and local != info["tree_sha256"]:
        sys.exit(f"STOP: impronta su Kaggle {info['tree_sha256']} diversa da quella locale {local}: "
                 f"l'aritmetica del pooling non e' deterministica fra piattaforme. Fermarsi e registrare.")
    ds_dir = runs_dir() / f"dataset-input-{short}-{tag}"
    if ds_dir.exists():
        shutil.rmtree(ds_dir)
    ds_dir.mkdir(parents=True)
    shutil.copy2(tar, ds_dir / tar.name)
    shutil.copy2(d / "e03" / "out" / f"input_{seg}_{tag}.json", ds_dir / "manifest.json")
    (ds_dir / "dataset-metadata.json").write_text(json.dumps(
        {"title": f"PapyrusLab {RUN_ID.upper()} shifted input {seg} {tag}",
         "id": f"{ds['owner']}/{entry['slug']}", "licenses": [{"name": "other"}]}, indent=2) + "\n", encoding="utf-8")
    create_or_version(ds_dir, f"update shifted input {seg} {tag}")
    entry.update({"tree_sha256": info["tree_sha256"], "tar_sha256": info["tar_sha256"], "tar_bytes": info["tar_bytes"]})
    save_ds(ds)
    print(f"dataset {ds['owner']}/{entry['slug']} pubblicato; tree_sha256 {info['tree_sha256']} scritto in datasets.json"
          + (f"; identico all'impronta locale" if local else ""))


def publish_manifest() -> None:
    """Il manifest di sorgente prodotto dal run prep-w016-z13 entra in configs/e03/source_manifest.json."""
    seg = gen.SHORT_TO_SEG["w016"]
    d = latest_download("prep-w016-z13")
    if d is None:
        sys.exit("nessun output verificato di prep-w016-z13")
    produced = json.loads((d / "e03" / "out" / f"source_manifest_{seg}.json").read_text(encoding="utf-8"))
    info = json.loads((d / "e03" / "out" / f"input_{seg}_z13.json").read_text(encoding="utf-8"))
    ds = load_ds()
    official = ds["inputs"][seg]["official"]["tree_sha256"]
    if info["tree_sha256"] != official:
        sys.exit(f"STOP: il pooling ufficiale di {seg} su Kaggle da' {info['tree_sha256']}, "
                 f"diverso dall'impronta congelata di E02 {official}. Fermarsi.")
    doc = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8")) if SOURCE_MANIFEST.exists() else {"segments": {}}
    doc.setdefault("segments", {})
    doc["segments"][seg] = produced["segments"][seg] if "segments" in produced else produced
    doc["version"] = produced.get("version", doc.get("version"))
    doc["segments"] = {k: doc["segments"][k] for k in sorted(doc["segments"])}
    SOURCE_MANIFEST.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"manifest di sorgente di {seg} scritto; input ufficiale riprodotto su Kaggle identico a E02 ({official})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["push", "status", "wait", "output", "publish-labels", "publish-input",
                                       "publish-manifest", "budget"])
    ap.add_argument("target", nargs="?")
    ap.add_argument("tag", nargs="?")
    a = ap.parse_args()
    if a.action == "budget":
        budget_cmd(); return
    if a.action == "publish-labels":
        publish_labels(); return
    if a.action == "publish-manifest":
        publish_manifest(); return
    if a.action == "publish-input":
        if not a.target or not a.tag:
            sys.exit("uso: publish-input <short> <zm3|zp3>")
        publish_input(a.target, a.tag); return
    if not a.target:
        sys.exit(f"manca il modo: {', '.join(gen.modes()[:4])} …")
    if a.target not in gen.modes():
        sys.exit(f"modo sconosciuto: {a.target}")
    if a.action == "push":
        push(a.target)
    elif a.action == "status":
        print(status(a.target))
    elif a.action == "wait":
        st = wait(a.target)
        print(st)
        if st != "complete":
            sys.exit(2)
    else:
        output(a.target)


if __name__ == "__main__":
    main()
