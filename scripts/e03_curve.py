#!/usr/bin/env python3
"""Read the E03 curve: AUROC(offset), differences, tolerance, preregistered checks.

Plan: docs/plans/2026-09-07-e03-tolleranza-offset-z.md, section 5 C (the rules) and step 10 (the artefact).
Nothing here chooses anything: the tolerance is a reading of a rule fixed before the runs, and every number is
reported for all four (segment, seed) combinations.

Before reading anything, the matrix is validated (review R1, finding 3): exactly 2 segments x 2 seeds x
7 offsets, unique keys, and every report's `e03_point` consistent with its file name, with
configs/e03/offsets.json and with its own prediction hash. A missing, duplicated or renamed point is an error,
not a warning -- otherwise a rename could flip one direction of the curve and the partner's blind
recomputation would repeat the same mistake.

Usage:
  python scripts/e03_curve.py [--metrics docs/reports/e03-r01/metrics] [--out .../curve.json] [--markdown OUT.md]
  python scripts/e03_curve.py --validate-only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFSETS_PATH = ROOT / "configs" / "e03" / "offsets.json"
DEFAULT_METRICS = ROOT / "docs" / "reports" / "e03-r01" / "metrics"

VERSION = "e03_curve/1.0"
TOL_DROP = 0.05          # perdita media che definisce la tolleranza
H1_BAND = 0.02           # piattezza attesa entro +-2 slice (jitter del training)
ANOMALY_GAIN = 0.02      # guadagno che, se presente su tutte e quattro le combinazioni, e' un allarme
CONTROL_WORSE = 0.01     # peggioramento massimo tollerato da un controllo a costo zero

RUN_RE = re.compile(r"^(?P<seg>[a-z0-9-]+)_s(?P<seed>\d+)_(?P<tag>z0|zm2|zm3|zm5|zp2|zp3|zp5)$")

_OFF = json.loads(OFFSETS_PATH.read_text(encoding="utf-8"))
ROWS = {int(r["k"]): r for r in _OFF["offsets"]}
TAGS = {r["tag"]: int(r["k"]) for r in _OFF["offsets"]}
SEGMENTS = list(_OFF["segments"])
SEEDS = [int(s) for s in _OFF["seeds"]]
KS = sorted(ROWS)
SEALED = _OFF["sealed_segment_never_touched"]


# ------------------------------------------------------------------------------------ loading
def load_points(metrics_dir: Path) -> dict:
    """Every per-run report of the curve, keyed by (segment, seed, k). Averages, Spearman files and
    curve.json are ignored here: they are read separately."""
    points: dict[tuple[str, int, int], dict] = {}
    seen_files: dict[tuple[str, int, int], list[str]] = {}
    for path in sorted(Path(metrics_dir).glob("*.json")):
        if path.name == "curve.json":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "e03_point" not in doc:
            continue                                            # medie e spearman: non sono punti della curva
        pt = doc["e03_point"]
        key = (str(pt.get("segment")), int(pt.get("seed")), int(pt.get("k")))
        seen_files.setdefault(key, []).append(path.name)
        doc["_file"] = path.name
        points[key] = doc
    for key, files in seen_files.items():
        if len(files) > 1:
            raise ValueError(f"STOP: punto duplicato {key}: {files}")
    return points


def load_extras(metrics_dir: Path) -> dict:
    """Averages and Spearman reports, keyed by file stem."""
    out = {}
    for path in sorted(Path(metrics_dir).glob("*.json")):
        if path.name == "curve.json":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "e03_point" in doc:
            continue
        out[path.stem] = doc
    return out


# ------------------------------------------------------------------------------------ validation
def validate_matrix(points: dict) -> None:
    # 1) coerenza di ogni singolo report: un file mal nominato va detto per quello che e', non come
    #    "punto mancante" (l'errore piu' insidioso di R1, finding 3, e' proprio un rinomino).
    for (seg, seed, k), doc in sorted(points.items()):
        if k not in ROWS:
            raise ValueError(f"STOP: offset k={k:+d} assente da configs/e03/offsets.json in {doc['_file']}")
        pt, row, stem = doc["e03_point"], ROWS[k], Path(doc["_file"]).stem
        m = RUN_RE.match(stem)
        if not m:
            raise ValueError(f"STOP: nome file fuori convenzione: {doc['_file']} "
                             f"(atteso <segmento>_s<seed>_z<tag>.json)")
        if m.group("seg") != seg:
            raise ValueError(f"STOP: segmento del nome ({m.group('seg')}) diverso da quello del contenuto ({seg}) "
                             f"in {doc['_file']}")
        if int(m.group("seed")) != seed:
            raise ValueError(f"STOP: seed del nome ({m.group('seed')}) diverso da quello del contenuto ({seed}) "
                             f"in {doc['_file']}")
        if TAGS[m.group("tag")] != k or pt.get("tag") != row["tag"]:
            raise ValueError(f"STOP: il tag del nome ({m.group('tag')}) non corrisponde a k={k:+d} "
                             f"in {doc['_file']}: un rinomino puo' invertire un verso della curva")
        if doc.get("segment") != seg:
            raise ValueError(f"STOP: segmento incoerente fra report ({doc.get('segment')}) e punto ({seg}) "
                             f"in {doc['_file']}")
        if list(pt.get("source_z_slice", [])) != list(row["source_z_slice"]):
            raise ValueError(f"STOP: finestra sorgente {pt.get('source_z_slice')} incoerente con k={k:+d} "
                             f"(attesa {row['source_z_slice']}) in {doc['_file']}")
        if list(pt.get("layer_indices", [])) != list(row["expected_indices"]):
            raise ValueError(f"STOP: indici di layer incoerenti con k={k:+d} in {doc['_file']}")
        if not pt.get("input_tree_sha256"):
            raise ValueError(f"STOP: input_tree_sha256 assente in {doc['_file']}")
        if pt.get("sha256_pred") != doc.get("sha256_pred"):
            raise ValueError(f"STOP: impronta della predizione incoerente fra report e punto in {doc['_file']}")
        held = doc.get("sets", {}).get("held", {})
        if held.get("auroc") is None:
            raise ValueError(f"STOP: AUROC held-out assente in {doc['_file']}")

    # 2) completezza e assenza di intrusi
    expected = {(seg, seed, k) for seg in SEGMENTS for seed in SEEDS for k in KS}
    got = set(points)
    extra = got - expected
    if extra:
        names = sorted(f"{s}/s{d}/k{k:+d}" for s, d, k in extra)
        raise ValueError(f"STOP: punti fuori matrice (segment/seed/offset non previsti): {names}"
                         + (f" — il segmento sigillato {SEALED} non deve comparire" if any(SEALED in n for n in names) else ""))
    missing = expected - got
    if missing:
        names = sorted(f"{s}/s{d}/k{k:+d}" for s, d, k in missing)
        raise ValueError(f"STOP: mancano {len(missing)} punti della matrice 2x2x7: {names}")

    # 3) ogni combinazione (segmento, tipo di input) deve usare sempre lo stesso input
    by_input: dict[tuple[str, str], set[str]] = {}
    for (seg, seed, k), doc in points.items():
        pt = doc["e03_point"]
        by_input.setdefault((seg, str(pt.get("input"))), set()).add(str(pt.get("input_tree_sha256")))
    for (seg, kind), hashes in sorted(by_input.items()):
        if len(hashes) > 1:
            raise ValueError(f"STOP: {seg} usa {len(hashes)} input diversi per '{kind}': {sorted(hashes)}")


# ------------------------------------------------------------------------------------ readings
def _auroc(points, seg, seed, k) -> float:
    return float(points[(seg, seed, k)]["sets"]["held"]["auroc"])


def _f1(points, seg, seed, k):
    return points[(seg, seed, k)]["sets"]["held"].get("at_threshold", {}).get("f1")


def compute(points: dict, extras: dict | None = None) -> dict:
    validate_matrix(points)
    extras = extras or {}
    delta: dict[str, dict[str, dict]] = {}
    for seed in SEEDS:
        delta[str(seed)] = {}
        for k in KS:
            per_seg = {seg: _auroc(points, seg, seed, k) - _auroc(points, seg, seed, 0) for seg in SEGMENTS}
            delta[str(seed)][str(k)] = {"per_segment": per_seg,
                                        "mean": sum(per_seg.values()) / len(per_seg)}

    tolerance = {}
    for seed in SEEDS:
        row = {}
        for name, ks in (("minus", [-2, -3, -5]), ("plus", [2, 3, 5])):
            hit = None
            for k in ks:                                   # gia' in ordine di |k| crescente
                if delta[str(seed)][str(k)]["mean"] <= -TOL_DROP:
                    hit = abs(k)
                    break
            row[name] = hit
        row["per_segment"] = {
            seg: {name: next((abs(k) for k in ks
                              if delta[str(seed)][str(k)]["per_segment"][seg] <= -TOL_DROP), None)
                  for name, ks in (("minus", [-2, -3, -5]), ("plus", [2, 3, 5]))}
            for seg in SEGMENTS
        }
        row["delta_at_5"] = {"minus": delta[str(seed)]["-5"]["mean"], "plus": delta[str(seed)]["5"]["mean"]}
        tolerance[str(seed)] = row

    h1_viol = [{"segment": seg, "seed": seed, "k": k, "delta": delta[str(seed)][str(k)]["per_segment"][seg]}
               for seed in SEEDS for seg in SEGMENTS for k in (-2, 2)
               if abs(delta[str(seed)][str(k)]["per_segment"][seg]) > H1_BAND]
    h1 = {"band": H1_BAND, "holds": not h1_viol, "violations": h1_viol}

    h2_rows, h2_ok = [], True
    for seed in SEEDS:
        for name, (a, b, c) in (("minus", (-2, -3, -5)), ("plus", (2, 3, 5))):
            d2, d3, d5 = (delta[str(seed)][str(x)]["mean"] for x in (a, b, c))
            ok = d3 < d2 and d5 < d3
            h2_ok = h2_ok and ok
            h2_rows.append({"seed": seed, "direction": name, "delta_2": d2, "delta_3": d3, "delta_5": d5,
                            "monotone": ok})
    h2 = {"holds": h2_ok, "rows": h2_rows}

    anomaly_ks = [k for k in KS if k != 0
                  and all(delta[str(seed)][str(k)]["per_segment"][seg] >= ANOMALY_GAIN
                          for seed in SEEDS for seg in SEGMENTS)]
    anomaly = {"gain": ANOMALY_GAIN, "triggered": bool(anomaly_ks), "k": anomaly_ks,
               "meaning": "un offset diverso da zero migliora ovunque: possibile disallineamento fra label e "
                          "centro del segnale. Fermarsi e indagare (piano sezione 7)." if anomaly_ks else None}

    asym = any((tolerance[str(s)]["minus"] is None) != (tolerance[str(s)]["plus"] is None)
               or (tolerance[str(s)]["minus"] or 0) != (tolerance[str(s)]["plus"] or 0) for s in SEEDS)

    controls = _controls(points, extras)

    return {
        "version": VERSION, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": {"tolerance_drop": TOL_DROP, "H1_band": H1_BAND, "anomaly_gain": ANOMALY_GAIN,
                 "control_worse": CONTROL_WORSE,
                 "note": "soglie di utilita' pratica fissate prima della prova, non livelli di significativita'"},
        "segments": SEGMENTS, "seeds": SEEDS, "offsets": KS,
        "auroc_held": {str(seed): {str(k): {seg: _auroc(points, seg, seed, k) for seg in SEGMENTS} for k in KS}
                       for seed in SEEDS},
        "f1_at_frozen_threshold": {str(seed): {str(k): {seg: _f1(points, seg, seed, k) for seg in SEGMENTS} for k in KS}
                                   for seed in SEEDS},
        "auroc_train": {str(seed): {str(k): {seg: points[(seg, seed, k)]["sets"].get("train", {}).get("auroc")
                                             for seg in SEGMENTS} for k in KS} for seed in SEEDS},
        "delta": delta, "tolerance": tolerance, "asymmetric": bool(asym),
        "H1": h1, "H2": h2, "anomaly": anomaly, "controls": controls,
        "points": {f"{seg}|{seed}|{k}": points[(seg, seed, k)]["_file"]
                   for seg in SEGMENTS for seed in SEEDS for k in KS},
        "formulation": ("Sui pixel held-out di sviluppo dei due segmenti, i due modelli mostrano la curva "
                        "AUROC(k) riportata per offset uniformi della finestra Z. L'errore simulato e' uniforme "
                        "e non rappresenta errori locali della superficie, normali sbagliate o cambi di foglio."),
    }


def _controls(points: dict, extras: dict) -> dict:
    """I due controlli a costo zero: media dei seed e media delle finestre -2/+2, sempre contro il proprio
    riferimento. 'Aiuta' solo se migliora su entrambi i segmenti senza peggiorare oltre CONTROL_WORSE."""
    out: dict = {"seed_mean": None, "z_mean_m2p2": None}

    seed_mean = {}
    for seg in SEGMENTS:
        doc = extras.get(f"{seg}_seedmean")
        if doc:
            seed_mean[seg] = {"auroc": doc["sets"]["held"]["auroc"],
                              "vs": {str(seed): doc["sets"]["held"]["auroc"] - _auroc(points, seg, seed, 0)
                                     for seed in SEEDS}}
    if len(seed_mean) == len(SEGMENTS):
        helps = all(v["vs"][str(seed)] > 0 for v in seed_mean.values() for seed in SEEDS)
        worst = min(v["vs"][str(seed)] for v in seed_mean.values() for seed in SEEDS)
        out["seed_mean"] = {"per_segment": seed_mean, "helps": bool(helps), "worst_delta": worst,
                            "criterion": "AUROC held superiore a entrambi i seed su entrambi i segmenti"}

    z_mean = {}
    for seg in SEGMENTS:
        for seed in SEEDS:
            doc = extras.get(f"{seg}_s{seed}_zmean_m2p2")
            if doc:
                z_mean[f"{seg}|{seed}"] = {"auroc": doc["sets"]["held"]["auroc"],
                                           "vs_zero": doc["sets"]["held"]["auroc"] - _auroc(points, seg, seed, 0)}
    if len(z_mean) == len(SEGMENTS) * len(SEEDS):
        helps = all(v["vs_zero"] > 0 for v in z_mean.values())
        out["z_mean_m2p2"] = {"per_combination": z_mean, "helps": bool(helps),
                              "worst_delta": min(v["vs_zero"] for v in z_mean.values()),
                              "criterion": "AUROC held superiore alla finestra centrale dello stesso seed, "
                                           "su entrambi i segmenti"}
    return out


# ------------------------------------------------------------------------------------ markdown
def to_markdown(res: dict) -> str:
    lines = ["# E03 — curva della tolleranza all'offset Z", "",
             f"Generata da `{VERSION}` il {res['generated_at']}. Regola preregistrata: perdita media di "
             f"{res['rule']['tolerance_drop']} di AUROC (piano sezione 5 C).", "",
             "## AUROC sui pixel held-out", ""]
    head = "| k (slice) | µm |" + "".join(f" {seg} s{seed} |" for seg in res["segments"] for seed in res["seeds"])
    lines += [head, "|" + "---|" * (2 + len(res["segments"]) * len(res["seeds"]))]
    for k in res["offsets"]:
        cells = "".join(f" {res['auroc_held'][str(seed)][str(k)][seg]:.4f} |"
                        for seg in res["segments"] for seed in res["seeds"])
        lines.append(f"| {k:+d} | {ROWS[k]['micrometres']:+.1f} |" + cells)
    lines += ["", "## Differenza rispetto all'offset zero dello stesso seed", "",
              "| k | " + " | ".join(f"Δ̄ seed {s}" for s in res["seeds"]) + " |",
              "|" + "---|" * (1 + len(res["seeds"]))]
    for k in res["offsets"]:
        lines.append(f"| {k:+d} | " + " | ".join(f"{res['delta'][str(s)][str(k)]['mean']:+.4f}" for s in res["seeds"]) + " |")
    lines += ["", "## Tolleranza", ""]
    for seed in res["seeds"]:
        t = res["tolerance"][str(seed)]
        def fmt(x):
            return (f"{x} slice ({x * 9.596:.1f} µm)" if x else
                    "nessun decadimento di 0,05 rilevato fino a 5 slice (48 µm) agli offset campionati")
        lines.append(f"- **seed {seed}** — verso negativo: {fmt(t['minus'])}; verso positivo: {fmt(t['plus'])}; "
                     f"Δ̄ a ±5: {t['delta_at_5']['minus']:+.4f} / {t['delta_at_5']['plus']:+.4f}")
    lines += ["", f"- **H1** (piatta entro ±2, banda {res['rule']['H1_band']}): "
                  f"{'rispettata' if res['H1']['holds'] else 'violata'}"
                  + ("" if res["H1"]["holds"] else " — " + ", ".join(
                      f"{v['segment']} s{v['seed']} k{v['k']:+d}: {v['delta']:+.4f}" for v in res["H1"]["violations"])),
              f"- **H2** (decade oltre ±2): {'rispettata ovunque' if res['H2']['holds'] else 'non ovunque'}",
              f"- **Regola di anomalia**: {'ATTIVATA su k=' + str(res['anomaly']['k']) if res['anomaly']['triggered'] else 'non attivata'}"]
    if res["controls"]["seed_mean"]:
        c = res["controls"]["seed_mean"]
        lines.append(f"- **Media dei seed**: {'aiuta' if c['helps'] else 'non aiuta'} (differenza peggiore {c['worst_delta']:+.4f})")
    if res["controls"]["z_mean_m2p2"]:
        c = res["controls"]["z_mean_m2p2"]
        lines.append(f"- **Media delle finestre −2/+2**: {'aiuta' if c['helps'] else 'non aiuta'} "
                     f"(differenza peggiore {c['worst_delta']:+.4f})")
    lines += ["", "> " + res["formulation"], ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    ap.add_argument("--out", type=Path, default=None, help="default: <metrics>/curve.json")
    ap.add_argument("--markdown", type=Path, default=None)
    ap.add_argument("--validate-only", action="store_true")
    a = ap.parse_args(argv)
    try:
        points = load_points(a.metrics)
        if a.validate_only:
            validate_matrix(points)
            print(f"matrice valida: {len(points)} punti "
                  f"({len(SEGMENTS)} segmenti x {len(SEEDS)} seed x {len(KS)} offset)")
            return 0
        res = compute(points, load_extras(a.metrics))
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 3
    out = a.out or (Path(a.metrics) / "curve.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    md = to_markdown(res)
    if a.markdown:
        a.markdown.write_text(md + "\n", encoding="utf-8")
    print(md)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
