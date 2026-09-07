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
import math
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
CONTROL_STRICT = 0.0     # "aiuta" per riga = miglioramento stretto su entrambi i segmenti (scelta 5 del socio)
IT = {"pherc0139-w016": "w016", "pherc0814-46527": "0814"}


def _num(s: str) -> float:
    v = float(s.strip().replace("−", "-").replace(",", ".").replace("+", ""))
    if not math.isfinite(v):
        raise ValueError(f"valore non finito nel rapporto del socio: {s!r}")
    return v


def _show(commit: str, path: str) -> str:
    out = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if out.returncode != 0:
        raise ValueError(f"file del socio assente in {commit}: {path}")
    return out.stdout


TOL_CELL = 5e-6          # il socio stampa sei decimali: scarto ammesso per cella
S1_VERDICTS = ("nessun lavoro equivalente trovato", "trovato lavoro parziale", "trovato lavoro equivalente")
COMBOS = ("w016/s42", "w016/s43", "0814/s42", "0814/s43")
KS = (-5, -3, -2, 0, 2, 3, 5)
KS_HEAD = ("−5", "−3", "−2", "0", "+2", "+3", "+5")


def _section(text: str, heading: str) -> str:
    """Corpo della sezione markdown che inizia con la riga `heading`, fino al titolo successivo di pari o superiore livello."""
    level = len(heading) - len(heading.lstrip("#"))
    m = re.search(r"^" + re.escape(heading) + r"\n(.*?)(?=^#{1," + str(level) + r"} |\Z)", text, re.M | re.S)
    if not m:
        raise ValueError(f"sezione mancante nel rapporto del socio: {heading!r}")
    return m.group(1)


def _table(body: str, header: tuple[str, ...]) -> list[list[str]]:
    """Righe della prima tabella markdown di `body`; l'intestazione deve coincidere esattamente con `header`."""
    m = re.search(r"^((?:\|.*\n)+)", body, re.M)
    if not m:
        raise ValueError("tabella mancante nel rapporto del socio")
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in m.group(1).splitlines()]
    if len(rows) < 3 or tuple(rows[0]) != tuple(header):
        raise ValueError(f"intestazione di tabella diversa dall'attesa: {rows[0] if rows else None} contro {list(header)}")
    if len(rows[1]) != len(header) or not all(re.fullmatch(r":?-+:?", c) for c in rows[1]):
        raise ValueError("separatore di tabella non valido")
    for r in rows[2:]:
        if len(r) != len(header):
            raise ValueError(f"riga con {len(r)} celle invece di {len(header)}: {r}")
    return rows[2:]


def _close(a: float, b: float, what: str) -> None:
    if abs(a - b) > TOL_CELL:
        raise ValueError(f"S3: {what}: {a} contro {b}")


def _yesno(cell: str) -> bool:
    if cell not in ("sì", "no"):
        raise ValueError(f"cella sì/no non riconosciuta: {cell!r}")
    return cell == "sì"


def _tol(cell: str):
    if cell == TOL_NONE:
        return None
    m = re.fullmatch(r"(\d) slice", cell)
    if not m:
        raise ValueError(f"cella di tolleranza non riconosciuta: {cell!r}")
    return int(m.group(1))


def _combo(short: str) -> tuple[str, str]:
    seg, s = short.split("/s")
    return next(g for g, sh in IT.items() if sh == seg), s


def _offset_rows(body: str, header: tuple[str, ...]) -> dict[int, list[str]]:
    """Tabella indicizzata dall'offset: esattamente i 7 offset, ciascuno una volta."""
    out = {}
    for r in _table(body, header):
        k = int(_num(r[0]))
        if k in out:
            raise ValueError(f"S3: offset {k} duplicato")
        out[k] = r[1:]
    if set(out) != set(KS):
        raise ValueError(f"S3: offset {sorted(out)} diversi da {list(KS)}")
    return out


def check_s1(s1: dict, s1_md: str) -> dict:
    v = s1.get("verdict")
    if v not in S1_VERDICTS:
        raise ValueError(f"verdetto S1 non riconosciuto: {v!r}")
    body = _section(s1_md, "## Verdetto")
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines or lines[0] != f"**{v}**":
        raise ValueError(f"S1: la sezione Verdetto non dichiara {v!r} come prima riga")
    others = [w for w in S1_VERDICTS if w != v and w in body]
    if others:
        raise ValueError(f"S1: la sezione Verdetto contiene anche {others}")
    counts = s1["counts"]
    return {"verdict": v, "pertinent_sources": int(counts["pertinent_sources"]),
            "network_queries": int(counts["network_queries"]), "queried_at_utc": s1["queried_at_utc"]}


def check_s2(s2: str, ds: dict, script_sha: str) -> dict:
    seg = "pherc0814-46527"
    got = {}
    for r in _table(_section(s2, "## Risultati"),
                    ("`z-start`", "offset", "intervallo sorgente", "formato", "forma", "tree SHA-256", "file / byte", "tempo reale", "spazio (`du -sh`)")):
        if not re.fullmatch(r"`[0-9a-f]{64}`", r[5]):
            raise ValueError(f"riga S2 senza impronta: {r}")
        z = int(r[0])
        if z in got:
            raise ValueError(f"S2: z-start {z} duplicato")
        got[z] = r[5].strip("`")
    expected = {13: ds["inputs"][seg]["official"]["tree_sha256"], 1: ds["inputs"][seg]["shifted_zm3"]["tree_sha256"],
                25: ds["inputs"][seg]["shifted_zp3"]["tree_sha256"]}
    if got != expected:
        raise ValueError(f"impronte S2 del socio diverse da datasets.json: {got}")
    m = re.search(r"`scripts/e03_pool_shifted.py`: SHA-256 `([0-9a-f]{64})`", s2)
    if not m or m.group(1) != script_sha:
        raise ValueError("S2: impronta dello script assente o diversa da quella in main")
    eq = _section(s2, "## Uguaglianza slice a slice")
    eq_m3 = "offset −3 (`z-start 1`): le slice 3..20 dello spostato sono identiche alle slice 0..17 del centrale — `True`." in eq
    eq_p3 = "offset +3 (`z-start 25`): le slice 0..17 dello spostato sono identiche alle slice 3..20 del centrale — `True`." in eq
    if not (eq_m3 and eq_p3):
        raise ValueError("S2: uguaglianza slice a slice non dichiarata per entrambi gli spostamenti")
    return {"segment": seg, "tree_sha256": {f"z{z}": h for z, h in sorted(got.items())},
            "identical_to_datasets_json": True, "slice_equality_declared": True, "script_sha256_identical_to_main": True}


def check_s3(s3: str, curve: dict) -> dict:
    """Confronta ogni cella numerica e ogni verdetto del rapporto S3 con curve.json. Ogni divergenza è un errore."""
    cells = 0
    head = ("offset",) + COMBOS
    # AUROC held-out, F1 alla soglia, Δ rispetto allo zero: 7 offset × 4 combinazioni ciascuna
    for heading, pick in (("## AUROC held-out", lambda s, k, g: curve["auroc_held"][s][str(k)][g]),
                          ("## F1 held-out alla soglia 91", lambda s, k, g: curve["f1_at_frozen_threshold"][s][str(k)][g]),
                          ("## Differenze AUROC rispetto allo zero dello stesso seed",
                           lambda s, k, g: 0.0 if k == 0 else curve["delta"][s][str(k)]["per_segment"][g])):
        for k, vals in _offset_rows(_section(s3, heading), head).items():
            for short, cell in zip(COMBOS, vals):
                g, s = _combo(short)
                _close(_num(cell), float(pick(s, k, g)), f"{heading[3:]} {short} k={k}"); cells += 1
    # media di Δ sui due segmenti: 2 seed × 7 offset
    body = _section(s3, "## Differenze AUROC rispetto allo zero dello stesso seed")
    mean_tab = body.split("Media di Δ sui due segmenti", 1)
    if len(mean_tab) != 2:
        raise ValueError("S3: tabella delle medie di Δ assente")
    seeds_seen = set()
    for r in _table(mean_tab[1].split("\n\n", 1)[1], ("seed",) + KS_HEAD):
        s = r[0]
        if s not in ("42", "43") or s in seeds_seen:
            raise ValueError(f"S3: riga delle medie non valida o duplicata: {r}")
        seeds_seen.add(s)
        for k, cell in zip(KS, r[1:]):
            _close(_num(cell), 0.0 if k == 0 else float(curve["delta"][s][str(k)]["mean"]), f"media Δ seed {s} k={k}"); cells += 1
    if seeds_seen != {"42", "43"}:
        raise ValueError("S3: medie di Δ non per entrambi i seed")
    # tolleranza: le 6 chiavi (aggregazione, seed), una volta ciascuna
    tol = {}
    for r in _table(_section(s3, "## Tolleranza preregistrata"), ("aggregazione", "seed", "verso −", "verso +")):
        if (r[0], r[1]) in tol:
            raise ValueError(f"S3: riga di tolleranza duplicata: {r}")
        tol[(r[0], r[1])] = (_tol(r[2]), _tol(r[3]))
    want = {("media dei due segmenti", s) for s in ("42", "43")} | {(sh, s) for sh in IT.values() for s in ("42", "43")}
    if set(tol) != want:
        raise ValueError(f"S3: chiavi di tolleranza {sorted(tol)} diverse dalle 6 attese")
    for (agg, s), (mn, pl) in tol.items():
        ours = curve["tolerance"][s] if agg.startswith("media") else \
            curve["tolerance"][s]["per_segment"][next(g for g, sh in IT.items() if sh == agg)]
        if (mn, pl) != (ours["minus"], ours["plus"]):
            raise ValueError(f"S3: tolleranza diversa per {agg} seed {s}: {(mn, pl)} contro {(ours['minus'], ours['plus'])}")
        cells += 2
    # H1: conteggio dichiarato, insieme completo delle violazioni con Δ e margine
    h1 = _section(s3, "## H1 — piatta entro ±2")
    m = re.search(r"\*\*Violata su (\d+) coppie combinazione-offset su (\d+)\.\*\*", h1)
    if not m or (int(m.group(1)), int(m.group(2))) != (len(curve["H1"]["violations"]), 2 * len(COMBOS)):
        raise ValueError("S3: conteggio H1 assente o diverso")
    band = float(curve["H1"]["band"])
    theirs = {}
    for r in _table(h1, ("combinazione", "offset", "Δ", f"oltre il limite di {str(band).replace('.', ',')}")):
        g, s = _combo(r[0]); k = int(_num(r[1])); d = _num(r[2])
        if (g, s, k) in theirs:
            raise ValueError(f"S3: violazione H1 duplicata: {r}")
        _close(_num(r[3]), abs(d) - band, f"margine H1 {r[0]} k={k}")
        theirs[(g, s, k)] = d
    ours_h1 = {(v["segment"], str(v["seed"]), int(v["k"])): float(v["delta"]) for v in curve["H1"]["violations"]}
    if set(theirs) != set(ours_h1):
        raise ValueError(f"S3: violazioni H1 diverse: {sorted(theirs)} contro {sorted(ours_h1)}")
    for key, d in theirs.items():
        _close(d, ours_h1[key], f"Δ H1 {key}"); cells += 2
    # H2: 4 righe (seed, verso) con i tre Δ̄, i due confronti e l'esito, tutti derivati dai numeri
    h2 = {}
    for r in _table(_section(s3, "## H2 — decadimento oltre ±2"),
                    ("seed", "verso", "Δ̄ a 2", "Δ̄ a 3", "Δ̄ a 5", "3 < 2", "5 < 3", "H2 nel verso")):
        key = (r[0], r[1])
        if key in h2:
            raise ValueError(f"S3: riga H2 duplicata: {r}")
        d2, d3, d5 = _num(r[2]), _num(r[3]), _num(r[4])
        c32, c53 = _yesno(r[5]), _yesno(r[6])
        if r[7] not in ("**sì**", "**no**"):
            raise ValueError(f"S3: esito H2 non riconosciuto: {r[7]!r}")
        h2[key] = (d2, d3, d5, c32, c53, r[7] == "**sì**")
    ours_h2 = {(str(r["seed"]), "−" if r["direction"] == "minus" else "+"): r for r in curve["H2"]["rows"]}
    if set(h2) != set(ours_h2):
        raise ValueError(f"S3: righe H2 {sorted(h2)} diverse da {sorted(ours_h2)}")
    for key, (d2, d3, d5, c32, c53, mono) in h2.items():
        o = ours_h2[key]
        _close(d2, float(o["delta_2"]), f"H2 Δ̄2 {key}"); _close(d3, float(o["delta_3"]), f"H2 Δ̄3 {key}"); _close(d5, float(o["delta_5"]), f"H2 Δ̄5 {key}")
        if c32 != (o["delta_3"] < o["delta_2"]) or c53 != (o["delta_5"] < o["delta_3"]) or mono != (c32 and c53) or mono != bool(o["monotone"]):
            raise ValueError(f"S3: confronti H2 non coerenti con i numeri per {key}")
        cells += 6
    # anomalia
    anom = re.search(r"^\*\*(Non attivata|Attivata)\.\*\*", _section(s3, "## Regola di anomalia"), re.M)
    if not anom or (anom.group(1) == "Attivata") != bool(curve["anomaly"]["triggered"]):
        raise ValueError("S3: regola di anomalia assente o diversa")
    # controlli a costo zero: ogni Δ, ogni "aiuta?" derivato dai numeri, verdetto complessivo coerente con le righe e con la curva
    ctrl = _section(s3, "## Controlli a costo zero")
    sm = curve["controls"]["seed_mean"]; zm = curve["controls"]["z_mean_m2p2"]
    for heading, header, rows_expected, pick, ours_help in (
            ("### Media dei seed", ("riferimento a offset 0", "Δ w016", "Δ 0814", "aiuta?"), {"seed 42": "42", "seed 43": "43"},
             lambda s, g: sm["per_segment"][g]["vs"][s], bool(sm["helps"])),
            ("### Media delle finestre −2/+2", ("seed", "Δ w016", "Δ 0814", "aiuta?"), {"42": "42", "43": "43"},
             lambda s, g: zm["per_combination"][f"{g}|{s}"]["vs_zero"], bool(zm["helps"]))):
        sec = _section(ctrl, heading)
        seen, row_helps = set(), []
        for r in _table(sec, header):
            if r[0] not in rows_expected or r[0] in seen:
                raise ValueError(f"S3: riga del controllo non valida o duplicata: {r}")
            seen.add(r[0]); s = rows_expected[r[0]]
            ds_ = [_num(r[1]), _num(r[2])]
            for g, d in zip(("pherc0139-w016", "pherc0814-46527"), ds_):
                _close(d, float(pick(s, g)), f"controllo {heading[4:]} {r[0]} {g}"); cells += 1
            helps_row = all(float(pick(s, g)) > CONTROL_STRICT for g in ("pherc0139-w016", "pherc0814-46527"))
            if _yesno(r[3]) != helps_row:
                raise ValueError(f"S3: 'aiuta?' non coerente con i numeri per {heading[4:]} {r[0]}")
            row_helps.append(helps_row)
        if seen != set(rows_expected):
            raise ValueError(f"S3: righe del controllo {heading[4:]} incomplete")
        vm = re.findall(r"\*\*Verdetto complessivo: (aiuta|non aiuta)\.\*\*", sec)
        if len(vm) != 1 or (vm[0] == "aiuta") != all(row_helps) or (vm[0] == "aiuta") != ours_help:
            raise ValueError(f"S3: verdetto del controllo {heading[4:]} assente, multiplo o non coerente")
    return {"cells_compared": cells, "tolerance_identical": True, "H1_identical": True,
            "H1_violations_compared": len(ours_h1), "H2_identical": True, "anomaly_identical": True, "controls_identical": True}


def partner_block(ds: dict, curve: dict) -> dict:
    """Legge i rapporti S1–S3 dal branch del socio e li confronta con i nostri valori (R3, finding 4).
    Il confronto è strutturale (tabelle con chiavi esatte, senza duplicati, valori finiti) e ogni divergenza è un errore."""
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
    s1 = check_s1(json.loads(_show(tip, PARTNER_FILES[0])), _show(tip, PARTNER_FILES[1]))
    s2 = check_s2(_show(tip, PARTNER_FILES[2]), ds, sha256_file(ROOT / "scripts" / "e03_pool_shifted.py"))
    s3 = check_s3(_show(tip, PARTNER_FILES[3]), curve)
    return {"branch": "e03-socio", "start_commit": start, "delivery_commit": tip, "files": list(PARTNER_FILES),
            "executor": "Codex (gpt-5.6-sol) sul Mac del socio, procedura unica",
            "S1_novelty": s1, "S2_pooling": s2, "S3_blind_recomputation": s3}


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
