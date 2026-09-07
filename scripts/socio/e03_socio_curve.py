#!/usr/bin/env python3
"""Independent E03 curve recomputation for the PapyrusLab partner task.

This script intentionally reads individual metric reports only. It does not read
the team's curve summary or analysis implementation and never uses the network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SEGMENTS = ("pherc0139-w016", "pherc0814-46527")
SEEDS = (42, 43)
OFFSETS = (-5, -3, -2, 0, 2, 3, 5)
OFFSET_TOKEN = {-5: "m5", -3: "m3", -2: "m2", 0: "0", 2: "p2", 3: "p3", 5: "p5"}
NO_DECAY = "nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=Path("docs/reports/e03-r01/metrics"),
        help="Directory containing the individual E03 metric JSON files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runs/E03-SOCIO/s3/e03_socio_curve.json"),
        help="Deterministic JSON output path",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing required metric file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def point_path(metrics_dir: Path, segment: str, seed: int, offset: int) -> Path:
    return metrics_dir / f"{segment}_s{seed}_z{OFFSET_TOKEN[offset]}.json"


def held_values(report: dict[str, Any], path: Path) -> tuple[float, float]:
    try:
        held = report["sets"]["held"]
        auroc = float(held["auroc"])
        f1_at_91 = float(held["at_threshold"]["f1"])
        threshold = held["at_threshold"].get("threshold", held["at_threshold"].get("threshold_mean"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"missing or invalid held metric in {path}: {exc}") from exc
    if threshold != 91:
        raise ValueError(f"expected held threshold 91 in {path}, got {threshold!r}")
    return auroc, f1_at_91


def first_decay(values: dict[int, float], direction: int) -> int | str:
    for magnitude in (2, 3, 5):
        if values[direction * magnitude] <= -0.05:
            return magnitude
    return NO_DECAY


def markdown_table(title: str, values: dict[int, dict[str, float]], columns: list[str]) -> None:
    print(f"\n{title}")
    print("| offset | " + " | ".join(columns) + " |")
    print("|---:|" + "---:|" * len(columns))
    for offset in OFFSETS:
        row = [f"{values[offset][column]:.6f}" for column in columns]
        print(f"| {offset:+d} | " + " | ".join(row) + " |")


def main() -> int:
    args = parse_args()
    columns = [f"{segment}/s{seed}" for segment in SEGMENTS for seed in SEEDS]
    auroc: dict[int, dict[str, float]] = {offset: {} for offset in OFFSETS}
    f1_at_91: dict[int, dict[str, float]] = {offset: {} for offset in OFFSETS}
    inputs: list[str] = []

    for segment in SEGMENTS:
        for seed in SEEDS:
            column = f"{segment}/s{seed}"
            for offset in OFFSETS:
                path = point_path(args.metrics_dir, segment, seed, offset)
                report = load_json(path)
                inputs.append(path.as_posix())
                value_auroc, value_f1 = held_values(report, path)
                auroc[offset][column] = value_auroc
                f1_at_91[offset][column] = value_f1

    delta: dict[int, dict[str, float]] = {offset: {} for offset in OFFSETS}
    for offset in OFFSETS:
        for column in columns:
            delta[offset][column] = auroc[offset][column] - auroc[0][column]

    mean_delta: dict[str, dict[int, float]] = {}
    for seed in SEEDS:
        mean_delta[str(seed)] = {}
        for offset in OFFSETS:
            mean_delta[str(seed)][offset] = sum(
                delta[offset][f"{segment}/s{seed}"] for segment in SEGMENTS
            ) / len(SEGMENTS)

    tolerance_by_seed: dict[str, dict[str, int | str]] = {}
    for seed in SEEDS:
        tolerance_by_seed[str(seed)] = {
            "negative": first_decay(mean_delta[str(seed)], -1),
            "positive": first_decay(mean_delta[str(seed)], 1),
        }

    tolerance_by_segment: dict[str, dict[str, dict[str, int | str]]] = {}
    for segment in SEGMENTS:
        tolerance_by_segment[segment] = {}
        for seed in SEEDS:
            series = {offset: delta[offset][f"{segment}/s{seed}"] for offset in OFFSETS}
            tolerance_by_segment[segment][str(seed)] = {
                "negative": first_decay(series, -1),
                "positive": first_decay(series, 1),
            }

    h1_violations: list[dict[str, Any]] = []
    for offset in (-2, 2):
        for column in columns:
            value = delta[offset][column]
            if abs(value) > 0.02:
                h1_violations.append(
                    {"combination": column, "offset": offset, "delta": value, "excess": abs(value) - 0.02}
                )

    h2: dict[str, dict[str, dict[str, Any]]] = {}
    for seed in SEEDS:
        h2[str(seed)] = {}
        for label, direction in (("negative", -1), ("positive", 1)):
            d2 = mean_delta[str(seed)][direction * 2]
            d3 = mean_delta[str(seed)][direction * 3]
            d5 = mean_delta[str(seed)][direction * 5]
            h2[str(seed)][label] = {
                "delta_2": d2,
                "delta_3": d3,
                "delta_5": d5,
                "three_below_two": d3 < d2,
                "five_below_three": d5 < d3,
                "holds": d3 < d2 and d5 < d3,
            }

    anomaly_offsets = [
        offset
        for offset in OFFSETS
        if offset != 0 and all(delta[offset][column] >= 0.02 for column in columns)
    ]

    seedmean_by_reference: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
        changes: dict[str, float] = {}
        for segment in SEGMENTS:
            path = args.metrics_dir / f"{segment}_seedmean.json"
            report = load_json(path)
            if path.as_posix() not in inputs:
                inputs.append(path.as_posix())
            mean_auroc, _ = held_values(report, path)
            changes[segment] = mean_auroc - auroc[0][f"{segment}/s{seed}"]
        seedmean_by_reference[str(seed)] = {
            "delta_by_segment": changes,
            "helps": all(value > 0.0 for value in changes.values())
            and all(value >= -0.01 for value in changes.values()),
        }
    seedmean_control = {
        "by_reference_seed": seedmean_by_reference,
        "helps": all(item["helps"] for item in seedmean_by_reference.values()),
    }

    zmean_by_seed: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
        changes = {}
        for segment in SEGMENTS:
            path = args.metrics_dir / f"{segment}_s{seed}_zmean_m2p2.json"
            report = load_json(path)
            inputs.append(path.as_posix())
            mean_auroc, _ = held_values(report, path)
            changes[segment] = mean_auroc - auroc[0][f"{segment}/s{seed}"]
        zmean_by_seed[str(seed)] = {
            "delta_by_segment": changes,
            "helps": all(value > 0.0 for value in changes.values())
            and all(value >= -0.01 for value in changes.values()),
        }
    zmean_control = {
        "by_seed": zmean_by_seed,
        "helps": all(item["helps"] for item in zmean_by_seed.values()),
    }

    ambiguities = [
        "Tolerance uses the inclusive <= -0.05 boundary exactly as preregistered.",
        "H1 uses the inclusive <= 0.02 boundary; only strictly larger absolute losses are violations.",
        "H2 uses strict comparisons, so a tie does not satisfy the monotonic-decay rule.",
        "The anomaly boundary is inclusive: delta exactly +0.02 activates that combination.",
        "For a control to 'help', 'exceeds on both segments' is treated as strict improvement; a tie is not improvement.",
        "Control decisions are made separately against both seed-zero references (seed mean) and both seeds (window mean); the overall verdict requires every prescribed comparison to help.",
        "All decisions use full JSON precision; six-decimal rounding is display-only.",
        "Tolerance selects the smallest sampled magnitude meeting the loss boundary even if the sampled curve is non-monotonic.",
        "H1 violation count is the number of combination-offset pairs, because each of the four segment/seed combinations is tested at both -2 and +2.",
        "A missing required file or metric is an error and no value is estimated.",
    ]

    result = {
        "schema": "e03-socio-curve/1.0",
        "segments": list(SEGMENTS),
        "seeds": list(SEEDS),
        "offsets": list(OFFSETS),
        "inputs": sorted(inputs),
        "auroc_held": {str(offset): auroc[offset] for offset in OFFSETS},
        "f1_at_91_held": {str(offset): f1_at_91[offset] for offset in OFFSETS},
        "delta_auroc": {str(offset): delta[offset] for offset in OFFSETS},
        "mean_delta_by_seed": {
            seed: {str(offset): values[offset] for offset in OFFSETS}
            for seed, values in mean_delta.items()
        },
        "mean_delta_at_abs5": {
            seed: {"negative": values[-5], "positive": values[5]}
            for seed, values in mean_delta.items()
        },
        "tolerance_by_seed": tolerance_by_seed,
        "tolerance_by_segment": tolerance_by_segment,
        "h1": {"holds": not h1_violations, "violations": h1_violations},
        "h2": h2,
        "anomaly": {"activated": bool(anomaly_offsets), "offsets": anomaly_offsets},
        "controls": {"seed_mean": seedmean_control, "zmean_m2p2": zmean_control},
        "ambiguities": ambiguities,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")

    markdown_table("AUROC held-out", auroc, columns)
    markdown_table("F1 held-out alla soglia 91", f1_at_91, columns)
    markdown_table("Delta AUROC rispetto a offset 0 dello stesso seed", delta, columns)
    print("\nDelta media sui due segmenti")
    for seed in SEEDS:
        values = " ".join(f"{offset:+d}:{mean_delta[str(seed)][offset]:+.6f}" for offset in OFFSETS)
        print(f"seed {seed}: {values}")
    print("\nTolleranza per seed:", json.dumps(tolerance_by_seed, ensure_ascii=False, sort_keys=True))
    print("Tolleranza per segmento:", json.dumps(tolerance_by_segment, ensure_ascii=False, sort_keys=True))
    print("H1:", "rispettata" if not h1_violations else f"violata su {len(h1_violations)} combinazioni-offset")
    print("H2:", json.dumps(h2, ensure_ascii=False, sort_keys=True))
    print("Anomalia:", "attivata" if anomaly_offsets else "non attivata", anomaly_offsets)
    print("Controllo media seed:", "aiuta" if seedmean_control["helps"] else "non aiuta")
    print("Controllo media -2/+2:", "aiuta" if zmean_control["helps"] else "non aiuta")
    print("Output:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
