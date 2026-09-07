#!/usr/bin/env python3
"""Assemble the E03-R01 manifest from the verified run downloads (plan step 12; same pattern as e02_manifest.py).

For every mode it reads the latest VERIFIED download under runs/E03-R01/<mode>/<timestamp>/, the local per-point
reports in docs/reports/e03-r01/metrics/, configs/e03/*.json, the GPU ledger and curve.json, and writes one JSON.
Everything is verified before being written (E02 review R3, finding 1): the Kaggle metrics JSON and the TIFF must
match SHA256SUMS, the local report must be computed on the same TIFF at the frozen threshold, the e03_point must
agree with offsets.json and datasets.json, and no report may mention the sealed segment. Failed attempts are
listed from the download folders that carry no VERIFIED marker.

Usage:
  python scripts/e03_manifest.py --out docs/reports/2026-09-07-e03-r01-manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_e03_notebooks as gen  # noqa: E402

RUNS = ROOT / "runs" / "E03-R01"
METRICS = ROOT / "docs" / "reports" / "e03-r01" / "metrics"
SEALED = gen.SEALED
FROZEN_THRESHOLD = 91
KEEP = ("stratum", "region", "n_px", "n_ink", "ink_fraction", "auroc", "best_f1", "at_threshold")


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout.strip()


def attempts(mode: str) -> list[dict]:
    base = RUNS / mode
    if not base.is_dir():
        return []
    out = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        verified = (d / "VERIFIED.json").exists()
        minutes = None
        for log in d.glob("*.log"):
            try:
                entries = json.loads(log.read_text(encoding="utf-8", errors="replace"))
                minutes = round(max(float(x["time"]) for x in entries if "time" in x) / 60, 2)
            except (ValueError, KeyError, TypeError):
                pass
        out.append({"download": d.name, "verified": verified, "session_minutes_from_log": minutes})
    return out


def latest_verified(mode: str) -> Path | None:
    c = [Path(a["download"]) for a in attempts(mode) if a["verified"]]
    return (RUNS / mode / c[-1]) if c else None


def run_info(d: Path) -> dict:
    txt = (d / "e03" / "logs" / "run_info.txt").read_text(encoding="utf-8")
    start = re.search(r"start=(\S+)", txt); end = re.search(r"end=(\S+)", txt)
    sums = [l.split(None, 1) for l in (d / "e03" / "out" / "SHA256SUMS").read_text(encoding="utf-8").splitlines() if l.strip()]
    return {"download_folder": str(d.relative_to(ROOT)).replace("\\", "/"),
            "start_utc": start.group(1) if start else None, "end_utc": end.group(1) if end else None,
            "files_persisted": len(sums), "sha256sums": {p.strip().lstrip("*"): h for h, p in sums}}


def summarize_sets(rep: dict) -> dict:
    out = {}
    for name, s in rep.get("sets", {}).items():
        row = {"n_px": s["n_px"], "n_ink": s["n_ink"], "ink_fraction": s["ink_fraction"], "auroc": s["auroc"],
               "best_f1": s["best_f1"], "at_threshold": s.get("at_threshold"),
               "median_ink": s.get("median_ink"), "median_background": s.get("median_background")}
        if "orientation" in s:
            row["orientation"] = s["orientation"]
        if "strata" in s:
            row["strata"] = [{k: v for k, v in st.items() if k in KEEP} for st in s["strata"]]
            row["regions"] = [{k: v for k, v in r.items() if k in KEEP} for r in s["regions"]]
        out[name] = row
    return out


def validate_point(mode: str, seg: str, seed: int, tag: str, kaggle_rep: dict, local_rep: dict, sums: dict,
                   kaggle_json_sha: str, ds: dict, rows: dict) -> None:
    tif = f"out/{seg}_seed{seed}_step075000_{tag}.tif"
    mjson = f"out/metrics_{seg}_s{seed}_{tag}.json"
    if SEALED in json.dumps(kaggle_rep) + json.dumps(local_rep):
        raise ValueError(f"{mode}: a report mentions the sealed segment")
    if sums.get(mjson) != kaggle_json_sha:
        raise ValueError(f"{mode}: Kaggle metrics JSON does not match SHA256SUMS")
    if sums.get(tif) != kaggle_rep.get("sha256_pred"):
        raise ValueError(f"{mode}: TIFF hash in SHA256SUMS differs from the Kaggle report")
    if local_rep.get("sha256_pred") != kaggle_rep.get("sha256_pred"):
        raise ValueError(f"{mode}: local report computed on a different TIFF")
    if local_rep.get("threshold_arg") != FROZEN_THRESHOLD:
        raise ValueError(f"{mode}: local report not at the frozen threshold {FROZEN_THRESHOLD}")
    for s in ("held", "train"):
        if local_rep["sets"][s]["auroc"] != kaggle_rep["sets"][s]["auroc"]:
            raise ValueError(f"{mode}: AUROC {s} differs between Kaggle and local")
    pt, row = local_rep["e03_point"], rows[tag]
    if (pt["segment"], int(pt["seed"]), int(pt["k"])) != (seg, seed, int(row["k"])):
        raise ValueError(f"{mode}: e03_point identity does not match the mode")
    if list(pt["layer_indices"]) != list(row["expected_indices"]) or list(pt["source_z_slice"]) != list(row["source_z_slice"]):
        raise ValueError(f"{mode}: e03_point window disagrees with offsets.json")
    key = {"official": "official", "shifted_m3": "shifted_zm3", "shifted_p3": "shifted_zp3"}[row["input"]]
    if pt["input_tree_sha256"] != ds["inputs"][seg][key]["tree_sha256"]:
        raise ValueError(f"{mode}: input fingerprint differs from datasets.json ({key})")
    if kaggle_rep.get("gate_A") != "superato" or kaggle_rep.get("gate_B") != "superato":
        raise ValueError(f"{mode}: gates not passed ({kaggle_rep.get('gate_A')}, {kaggle_rep.get('gate_B')})")


def recompute_curve(curve_file: dict) -> dict:
    """Ricalcola la curva dai 28 report e la confronta con curve.json (R3, finding 4): il manifest attesta solo ciò che ha rifatto."""
    import e03_curve as ec  # noqa: E402
    points = ec.load_points(METRICS)
    ec.validate_matrix(points)
    fresh = ec.compute(points, ec.load_extras(METRICS))
    diff = [k for k in set(fresh) | set(curve_file) if k != "generated_at" and fresh.get(k) != curve_file.get(k)]
    if diff:
        raise ValueError(f"curve.json non coincide con il ricalcolo dai report: campi {sorted(diff)}")
    return {"points_recomputed": len(points), "matches_curve_json": True,
            "tolerance": fresh["tolerance"], "H1": {"holds": fresh["H1"]["holds"], "violations": len(fresh["H1"]["violations"])},
            "H2_holds": fresh["H2"]["holds"], "anomaly_triggered": fresh["anomaly"]["triggered"],
            "controls": {k: (v["helps"] if v else None) for k, v in fresh["controls"].items()},
            "auroc_held": fresh["auroc_held"]}


def sealed_scan(runs: dict) -> dict:
    """Cerca il nome del segmento sigillato in tutti i JSON di metriche e nei modi eseguiti; nessun valore è presunto."""
    files = sorted(METRICS.glob("*.json"))
    hits = [f.name for f in files if SEALED in f.read_text(encoding="utf-8")]
    modes_hit = [m for m in runs if SEALED in m]
    if hits or modes_hit:
        raise ValueError(f"segmento sigillato citato: file {hits}, modi {modes_hit}")
    return {"segment": SEALED, "json_scanned": len(files), "mentioned_in_any_report": False,
            "runs_on_it": len(modes_hit)}


PARTNER_BRANCH = "origin/e03-socio"
PARTNER_PLAN = ROOT / "docs" / "plans" / "2026-09-07-e03-compiti-socio.md"
PARTNER_FILES = ("docs/reports/2026-09-07-e03-socio-s1-fonti.json", "docs/reports/2026-09-07-e03-socio-s1-novita.md",
                 "docs/reports/2026-09-07-e03-socio-s2-pooling-46527.md", "docs/reports/2026-09-07-e03-socio-s3-ricalcolo.md",
                 "scripts/socio/e03_socio_curve.py")
TOL_NONE = "nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati"
IT = {"pherc0139-w016": "w016", "pherc0814-46527": "0814"}


def _num(s: str) -> float:
    return float(s.replace("−", "-").replace(",", ".").replace("+", ""))


def _show(commit: str, path: str) -> str:
    out = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if out.returncode != 0:
        raise ValueError(f"file del socio assente in {commit}: {path}")
    return out.stdout


def _tol(cell: str):
    cell = cell.strip()
    if cell == TOL_NONE:
        return None
    m = re.fullmatch(r"(\d) slice", cell)
    if not m:
        raise ValueError(f"cella di tolleranza non riconosciuta: {cell!r}")
    return int(m.group(1))


def partner_block(ds: dict, curve: dict) -> dict:
    """Legge i rapporti S1–S3 dal branch del socio e li confronta con i nostri valori (R3, finding 4). Fallisce su ogni divergenza."""
    header = re.search(r"\*\*Commit di partenza:\*\* `branch e03-socio` — (.+)", PARTNER_PLAN.read_text(encoding="utf-8"))
    if not header:
        raise ValueError("piano del socio senza 'Commit di partenza' compilato")
    subject = header.group(1).strip()
    start = git("log", "--format=%h", "-1", "--fixed-strings", f"--grep={subject}", PARTNER_BRANCH)
    if not start or git("log", "-1", "--format=%s", start) != subject:
        raise ValueError(f"commit di partenza del socio non trovato su {PARTNER_BRANCH}: {subject!r}")
    tip = git("rev-parse", "--short", PARTNER_BRANCH)
    delivered = sorted(git("diff", "--name-only", start, tip).splitlines())
    if delivered != sorted(PARTNER_FILES):
        raise ValueError(f"file consegnati dal socio diversi dall'atteso: {delivered}")

    s1 = json.loads(_show(tip, PARTNER_FILES[0]))
    s1_md = _show(tip, PARTNER_FILES[1])
    if s1.get("verdict") not in s1_md:
        raise ValueError("verdetto S1 del JSON assente dal rapporto S1")
    s2 = _show(tip, PARTNER_FILES[2])
    rows = {int(m.group(1)): m.group(2) for m in re.finditer(r"^\|\s*(\d+)\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*`([0-9a-f]{64})`", s2, re.M)}
    seg = "pherc0814-46527"
    expected = {13: ds["inputs"][seg]["official"]["tree_sha256"], 1: ds["inputs"][seg]["shifted_zm3"]["tree_sha256"],
                25: ds["inputs"][seg]["shifted_zp3"]["tree_sha256"]}
    if rows != expected:
        raise ValueError(f"impronte S2 del socio diverse da datasets.json: {rows}")
    m = re.search(r"`scripts/e03_pool_shifted.py`: SHA-256 `([0-9a-f]{64})`", s2)
    script_same = bool(m) and m.group(1) == sha256_file(ROOT / "scripts" / "e03_pool_shifted.py")
    slice_eq = s2.count("— `True`") == 2
    if not (script_same and slice_eq):
        raise ValueError("S2: script diverso o uguaglianza slice non dichiarata")

    s3 = _show(tip, PARTNER_FILES[3])
    table = re.search(r"## AUROC held-out\n\n(.*?)\n\n", s3, re.S).group(1).splitlines()[2:]
    cols = ["pherc0139-w016|42", "pherc0139-w016|43", "pherc0814-46527|42", "pherc0814-46527|43"]
    max_diff, n = 0.0, 0
    for line in table:
        cells = [c.strip() for c in line.strip("|").split("|")]
        k = int(_num(cells[0]))
        for col, cell in zip(cols, cells[1:]):
            g, s = col.split("|")
            max_diff = max(max_diff, abs(_num(cell) - curve["auroc_held"][s][str(k)][g])); n += 1
    if n != 28 or max_diff > 5e-6:
        raise ValueError(f"tabella AUROC S3: {n} celle, scarto massimo {max_diff}")
    tol_rows = re.findall(r"^\| (media dei due segmenti|w016|0814) \| (4[23]) \| (.+?) \| (.+?) \|$", s3, re.M)
    if len(tol_rows) != 6:
        raise ValueError("tabella di tolleranza S3 incompleta")
    for agg, s, minus, plus in tol_rows:
        ours = curve["tolerance"][s] if agg.startswith("media") else \
            curve["tolerance"][s]["per_segment"][next(g for g, short in IT.items() if short == agg)]
        if (_tol(minus), _tol(plus)) != (ours["minus"], ours["plus"]):
            raise ValueError(f"tolleranza S3 diversa: {agg} seed {s}")
    h1 = re.search(r"\*\*Violata su (\d) coppie", s3)
    if not h1 or int(h1.group(1)) != len(curve["H1"]["violations"]):
        raise ValueError("H1 S3 diversa")
    h2 = re.findall(r"^\| (4[23]) \| ([−+]) \|.*\| \*\*(sì|no)\*\* \|$", s3, re.M)
    ours_h2 = {(str(r["seed"]), "−" if r["direction"] == "minus" else "+"): r["monotone"] for r in curve["H2"]["rows"]}
    if len(h2) != 4 or any(ours_h2[(s, d)] != (v == "sì") for s, d, v in h2):
        raise ValueError("H2 S3 diversa")
    if "## Regola di anomalia\n\n**Non attivata.**" not in s3 or curve["anomaly"]["triggered"]:
        raise ValueError("anomalia S3 diversa")
    if s3.count("**Verdetto complessivo: non aiuta.**") != 2 or any(v["helps"] for v in curve["controls"].values() if v):
        raise ValueError("controlli S3 diversi")
    return {"branch": "e03-socio", "start_commit": start, "delivery_commit": tip, "files": list(PARTNER_FILES),
            "executor": "Codex (gpt-5.6-sol) sul Mac del socio, procedura unica",
            "S1_novelty": {"verdict": s1["verdict"], "pertinent_sources": s1["counts"]["pertinent_sources"],
                           "network_queries": s1["counts"]["network_queries"], "queried_at_utc": s1["queried_at_utc"]},
            "S2_pooling": {"segment": seg, "tree_sha256": {f"z{z}": h for z, h in rows.items()},
                           "identical_to_datasets_json": True, "slice_equality_declared": slice_eq,
                           "script_sha256_identical_to_main": script_same},
            "S3_blind_recomputation": {"auroc_cells_compared": n, "auroc_table_max_abs_diff": max_diff,
                                       "tolerance_identical": True, "H1_identical": True, "H2_identical": True,
                                       "anomaly_identical": True, "controls_identical": True}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    ds = read_json(ROOT / "configs" / "e03" / "datasets.json")
    offsets = read_json(ROOT / "configs" / "e03" / "offsets.json")
    rows = {r["tag"]: r for r in offsets["offsets"]}
    source_manifest = read_json(ROOT / "configs" / "e03" / "source_manifest.json")
    ledger = read_json(RUNS / "gpu_ledger.json") or []
    curve = read_json(METRICS / "curve.json")
    label_manifest = read_json(RUNS / "dataset-labels" / "manifest.json")

    runs, missing, points_checked = {}, [], 0
    for mode in gen.modes():
        d = latest_verified(mode)
        info = {"attempts": attempts(mode)}
        if d is None:
            missing.append(mode); runs[mode] = info; continue
        kind, seg, seed, tag = gen.parse_mode(mode)
        info.update(run_info(d))
        info["install"] = read_json(d / "e03" / "logs" / "install.json")
        vc = d / "e03" / "logs" / "villa_commit.txt"
        info["villa_commit"] = vc.read_text(encoding="utf-8").strip() if vc.exists() else None
        if kind == "prep":
            m = read_json(d / "e03" / "out" / f"input_{seg}_{tag}.json")
            info["prep"] = m
            log = (d / "e03" / "logs" / f"prep_{seg}_{tag}.log").read_text(encoding="utf-8", errors="replace")
            # durata e conferme le stampa la cella del notebook: stanno nel log del kernel, non in quello del pooling
            klog = ""
            for lf in d.glob("*.log"):
                try:
                    klog += "\n".join(str(x.get("data", "")) for x in json.loads(lf.read_text(encoding="utf-8", errors="replace")))
                except ValueError:
                    pass
            mm = re.search(r"durata_s=(\d+)", log + "\n" + klog)
            info["prep"]["duration_s"] = int(mm.group(1)) if mm else None
            info["prep"]["source_manifest"] = ("prodotto" if "manifest di sorgente: produzione" in klog
                                               else "verificato" if "manifest di sorgente: verifica" in klog else None)
            info["prep"]["slice_equality_with_official"] = (("uguaglianza slice a slice con l'ufficiale: verificata" in klog)
                                                            if tag != "z13" else None)
            info["prep"]["whitelist_passed"] = "lista bianca superata" in klog
        else:
            k = read_json(d / "e03" / "out" / f"metrics_{seg}_s{seed}_{tag}.json")
            local = read_json(METRICS / f"{seg}_s{seed}_{tag}.json")
            validate_point(mode, seg, seed, tag, k, local, info["sha256sums"],
                           sha256_file(d / "e03" / "out" / f"metrics_{seg}_s{seed}_{tag}.json"), ds, rows)
            points_checked += 1
            log = (d / "e03" / "logs" / f"infer_seed{seed}_{tag}.log").read_text(encoding="utf-8", errors="replace")
            mm = re.search(r"exit_code=(\d+) durata_s=(\d+) causa=(\S+)", log)
            info["inference"] = {"exit_code": int(mm.group(1)), "duration_s": int(mm.group(2)), "cause": mm.group(3)} if mm else None
            info["layer_indices_ok"] = f"Selected source layer indices={rows[tag]['expected_indices']}" in log
            gp = d / "e03" / "logs" / "gpu_peak.json"
            info["gpu_peak_mib"] = gp.read_text(encoding="utf-8").strip() if gp.exists() else None
            info["checkpoints_sha256"] = (d / "e03" / "logs" / "checkpoints_sha256.txt").read_text(encoding="utf-8").strip().splitlines()
            info["guard"] = read_json(d / "e03" / "logs" / "guard.json")
            info["point"] = local["e03_point"]
            info["gates"] = {"gate_A": k["gate_A"], "gate_B": k["gate_B"], "orientation_blocking": k["gate_B_orientation_blocking"],
                             "orientamento_ok": k["sets"]["train"]["orientation"]["orientamento_ok"]}
            info["metrics"] = summarize_sets(local)
            sp = read_json(METRICS / f"{seg}_s{seed}_{tag}_spearman_z0.json")
            info["spearman_vs_zero"] = sp["spearman"] if sp else None
        runs[mode] = info

    zero_points = {}
    for seg in gen.SEGMENTS:
        for seed in gen.SEEDS:
            z = read_json(METRICS / f"{seg}_s{seed}_z0.json")
            if z and z["e03_point"]["k"] == 0:
                zero_points[f"{seg}|s{seed}"] = {"sha256_pred": z["sha256_pred"], "auroc_held": z["sets"]["held"]["auroc"],
                                                 "source": "E02-R01 TIFF, recomputed with e03_metrics --run at threshold 91"}
    controls = {n: read_json(METRICS / f"{n}.json") for n in
                [f"{seg}_seedmean" for seg in gen.SEGMENTS] + [f"{seg}_s{seed}_zmean_m2p2" for seg in gen.SEGMENTS for seed in gen.SEEDS]}
    controls_summary = {n: {"auroc_held": c["sets"]["held"]["auroc"], "inputs": [i["sha256"] for i in c["inputs"]]}
                        for n, c in controls.items() if c}

    if curve is None:
        raise ValueError("curve.json assente")
    curve_summary = recompute_curve(curve)
    partner = partner_block(ds, curve)
    sealed = sealed_scan(runs)

    manifest = {
        "experiment": "E03-R01", "plan": "docs/plans/2026-09-07-e03-tolleranza-offset-z.md",
        "commits_papyruslab": {"plan_frozen": "9e7f1d0", "steps_0_5": "4c60e43", "review_R2_fixes": "4520815",
                               "curve": "d85ee42", "partner_start": partner["start_commit"],
                               "partner_delivery": partner["delivery_commit"],
                               "manifest_head": git("rev-parse", "--short", "HEAD")},
        "offsets": offsets, "datasets_kaggle": ds,
        "source_manifest": {seg: {k: v for k, v in e.items() if k != "tiles"} | {"n_tiles": e["n_tiles"]}
                            for seg, e in (source_manifest or {}).get("segments", {}).items()},
        "labels": {seg: {k: v for k, v in s.items() if k != "files"} for seg, s in label_manifest["segments"].items()} if label_manifest else None,
        "zero_points_from_E02": zero_points,
        "runs": runs, "runs_missing": missing, "points_validated": points_checked,
        "controls_zero_gpu": controls_summary,
        "gpu_ledger": ledger,
        "gpu_minutes_total": round(sum(float(e.get("settled_minutes") or e["reserved_minutes"]) for e in ledger), 1),
        "curve_summary": curve_summary,
        "sealed_segment": sealed,
        "frozen_threshold": FROZEN_THRESHOLD,
        "partner_tasks": partner,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"manifest -> {a.out} ({a.out.stat().st_size} byte); run verificati: {len(runs) - len(missing)}; "
          f"mancanti: {missing or 'nessuno'}; punti validati: {points_checked}; GPU: {manifest['gpu_minutes_total']} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
