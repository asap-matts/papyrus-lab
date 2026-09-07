#!/usr/bin/env python3
"""Generate the Kaggle notebooks of E03 (plan docs/plans/2026-09-07-e03-tolleranza-offset-z.md, step 5).

Modes:
  prep-w016-z13            CPU: official pooling of w016, produces the source manifest (step 2b) and re-derives
                                the official input, whose fingerprint must equal the frozen E02 one.
  prep-<short>-z{m3,p3}    CPU: shifted pooling, verifies the source manifest, then proves slice-by-slice
                                equality with the official input mounted from the E02 dataset.
  infer-<short>-s<seed>-z<tag>   T4: one point of the curve, tag in zm5 zm3 zm2 zp2 zp3 zp5.

The reusable cells (environment, network, villa checkout, --no-deps install, checkpoints, labels, CPU model
build, persistence) are imported from scripts/build_e02_notebooks.py and only re-pathed e02 -> e03: the frozen
E02 artefacts are never modified. What is new here is the Z window, the shifted inputs, the segment whitelist
that protects the seal, and the per-run identity block written into every report.

Authority: the frozen plan and configs/e03/offsets.json decide; this generator only expands them mechanically
(review R1, finding 7). Every semantic value used below is read from offsets.json, never restated.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_e02_notebooks as e02gen  # noqa: E402  (frozen: imported, never modified)

KAGGLE_USER = "matteopontesilli"
RUN_ID = "e03-r01"
PLAN = "docs/plans/2026-09-07-e03-tolleranza-offset-z.md"
OFFSETS = json.loads((ROOT / "configs" / "e03" / "offsets.json").read_text(encoding="utf-8"))
DATASETS = ROOT / "configs" / "e03" / "datasets.json"
SOURCE_MANIFEST = ROOT / "configs" / "e03" / "source_manifest.json"
TORCH_EXPECTED = e02gen.TORCH_EXPECTED
PREP_TIMEOUT_S = e02gen.PREP_TIMEOUT_S
INFER_TIMEOUT_S = e02gen.INFER_TIMEOUT_S

SEGMENTS = {name: e02gen.SEGMENTS[name] for name in OFFSETS["segments"]}      # solo i due di sviluppo
SHORT_TO_SEG = {v["short"]: k for k, v in SEGMENTS.items()}
ROWS = {r["tag"]: r for r in OFFSETS["offsets"]}
SEEDS = [int(s) for s in OFFSETS["seeds"]]
SEALED = OFFSETS["sealed_segment_never_touched"]

# Impronte congelate delle label dei due segmenti di sviluppo (manifest E02): la lista bianca che protegge il
# sigillo non guarda i nomi ma le impronte (revisione R1, finding 4).
LABEL_ALLOWLIST = {
    "pherc0139-w016": "a62d3e0ecfc9305758fae3bc0d74d99ecf675bcf846aa910ee4a876ee26ccfd5",
    "pherc0814-46527": "5659236870d7d0408e330f05f6275bd821fc1d7bdea8c9c8f072dfd4ae8b54f0",
}

# Le celle di E02 riusate: solo le radici cambiano (e02 -> e03). L'ordine delle sostituzioni conta:
# '/kaggle/working/e02_guard.json' contiene '/kaggle/working/e02' come prefisso.
REPATH = [
    ("/kaggle/working/e02_guard.json", "/kaggle/working/e03_guard.json"),
    ("/kaggle/working/e02", "/kaggle/working/e03"),
    ("/tmp/e02", "/tmp/e03"),
    ("PapyrusLab E02", "PapyrusLab E03"),
]


def reuse(name: str) -> str:
    src = getattr(e02gen, name)
    for old, new in REPATH:
        src = src.replace(old, new)
    return src


def modes() -> list[str]:
    out = ["prep-w016-z13"]
    for seg in SEGMENTS.values():
        for tag in ("zm3", "zp3"):
            out.append(f"prep-{seg['short']}-{tag}")
    for seg in SEGMENTS.values():
        for seed in SEEDS:
            for tag in ("zm2", "zp2", "zm3", "zp3", "zm5", "zp5"):
                out.append(f"infer-{seg['short']}-s{seed}-{tag}")
    return out


def parse_mode(mode: str) -> tuple[str, str, int | None, str]:
    """-> (kind, segment_name, seed, tag)"""
    parts = mode.split("-")
    kind, short = parts[0], parts[1]
    if short not in SHORT_TO_SEG:
        raise AssertionError(f"{mode}: segmento '{short}' fuori dai due di sviluppo {sorted(SHORT_TO_SEG)}")
    if kind == "prep":
        return kind, SHORT_TO_SEG[short], None, parts[2]
    if kind != "infer":
        raise AssertionError(f"{mode}: tipo di run sconosciuto")
    return kind, SHORT_TO_SEG[short], int(parts[2][1:]), parts[3]


# --------------------------------------------------------------------------------------------
# Celle proprie di E03
# --------------------------------------------------------------------------------------------
CELL_INTRO_MD = """# PapyrusLab E03 — run `__MODE__` (segmento `__SEG__`, offset `__TAG__`)

Notebook generato da `scripts/build_e03_notebooks.py` (non modificare a mano). Piano congelato: `__PLAN__`.
Ogni controllo di arresto del piano è un'asserzione: se fallisce, il run si ferma e il log dice dove.
Fanno fede il piano e `configs/e03/offsets.json`; questo generatore ne è solo l'espansione meccanica.

- Output persistiti: `/kaggle/working/e03/out` e `/kaggle/working/e03/logs`
- File pesanti (codice, checkpoint, label, input, cache), non persistiti: `/tmp/e03`
"""

CELL_CONST_PY = '''MODE = "__MODE__"
KIND = "__KIND__"                  # prep | infer
SEG = "__SEG__"                    # nome della label, es. pherc0814-46527
SHORT = "__SHORT__"
SEED = __SEED__                    # None nel prep
TAG = "__TAG__"                    # z13 | zm3 | zp3 (prep) oppure zm5..zp5 (infer)
K = __K__                          # offset in slice poolate (None nel prep)
Z_START = __Z_START__              # primo piano sorgente della finestra di 84
SOURCE_Z_SLICE = __SOURCE_Z_SLICE__
LAYER_ARGS = "__LAYER_ARGS__"      # "" per la finestra di default, oppure --layer-start S --layer-end E
EXPECTED_INDICES = __EXPECTED_INDICES__
SETS = "held,train"                # i due segmenti di sviluppo hanno entrambi gli insiemi
WORK = "/kaggle/working/e03"
HEAVY = "/tmp/e03"
SRC_URL = "__SRC_URL__"
LABEL_SHAPE = __LABEL_SHAPE__
TORCH_EXPECTED = "__TORCH__"
LABEL_TREE_SHA256 = "__LABEL_TREE__"
LABEL_FILES, LABEL_BYTES = __LABEL_FILES__, __LABEL_BYTES__
LABEL_ALLOWLIST = __LABEL_ALLOWLIST__      # nome -> impronta congelata: il sigillo non dipende dai nomi
INPUT_TREE_SHA256 = "__INPUT_TREE__"       # input da usare in questo run (ufficiale o spostato)
OFFICIAL_INPUT_TREE_SHA256 = "__OFFICIAL_INPUT_TREE__"
SEALED_SEGMENT = "__SEALED__"
assert SEG in LABEL_ALLOWLIST and SEG != SEALED_SEGMENT, f"STOP: {SEG} non e' un segmento di sviluppo"
print("MODE", MODE, "SEG", SEG, "SEED", SEED, "TAG", TAG, "K", K, "z_start", Z_START, "layer", LAYER_ARGS or "default")
'''

CELL_GUARD_LABELS_PY = r'''# Guardia della lista bianca (revisione R1, finding 4): prima di qualunque lettura di maschera, la cartella
# delle label montata deve essere uno dei due segmenti di sviluppo E con l'impronta congelata. Il sigillo di
# __SEALED__ non dipende dal nome di una cartella.
import glob, hashlib, os

def tree_sha256(root):
    per_file = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            per_file[os.path.relpath(p, root).replace(os.sep, "/")] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    h = hashlib.sha256()
    for rel, digest in sorted(per_file.items()):
        h.update(f"{rel}\n{digest}\n".encode())
    return h.hexdigest(), len(per_file)

for root, dirs, files in os.walk("/kaggle/input"):
    depth = root.count("/") - 2
    if depth <= 3:
        print("  " * depth + os.path.basename(root) + "/", "(", len(files), "file )")
sealed_hits = glob.glob(f"/kaggle/input/**/{SEALED_SEGMENT}*", recursive=True)
assert not sealed_hits, f"STOP: il segmento sigillato {SEALED_SEGMENT} risulta montato: {sealed_hits[:3]}"
lab_hits = glob.glob(f"/kaggle/input/**/{SEG}/{SEG}_inklabels.zarr/0/.zarray", recursive=True)
assert lab_hits, f"STOP: label {SEG} non montata sotto /kaggle/input"
LABEL_DIR_MOUNTED = os.path.dirname(os.path.dirname(os.path.dirname(lab_hits[0])))
lsha, lfiles = tree_sha256(LABEL_DIR_MOUNTED)
print("label montata:", LABEL_DIR_MOUNTED, "file", lfiles, "tree_sha256", lsha)
assert os.path.basename(LABEL_DIR_MOUNTED) in LABEL_ALLOWLIST, f"STOP: {LABEL_DIR_MOUNTED} fuori dalla lista bianca"
assert lsha == LABEL_ALLOWLIST[SEG] == LABEL_TREE_SHA256, f"STOP: impronta delle label {lsha} diversa da quella congelata"
print("lista bianca superata")
'''

CELL_GUARD_INPUT_PY = r'''# Guardia dell'input (run GPU): l'input poolato di questo offset deve essere montato con l'impronta congelata,
# PRIMA di qualunque installazione. Nessun pooling in sessione GPU (piano E02 R1, finding 6).
import glob, json, os
name = f"{SEG}_pooled.zarr" if TAG in ("z0", "zm2", "zp2") else f"{SEG}_pooled_{TAG}.zarr"
hits = glob.glob(f"/kaggle/input/**/{name}/0/.zarray", recursive=True)
assert hits, f"STOP: input {name} non montato sotto /kaggle/input: ripararlo con un run prep (CPU), mai qui"
INPUT_ZARR = os.path.dirname(os.path.dirname(hits[0]))
tsha, nfiles = tree_sha256(INPUT_ZARR)
print("input:", INPUT_ZARR, "file", nfiles, "tree_sha256", tsha)
assert tsha == INPUT_TREE_SHA256, f"STOP: tree_sha256 dell'input montato ({tsha}) diverso da quello congelato ({INPUT_TREE_SHA256})"
import zarr
g = zarr.open(INPUT_ZARR, mode="r")
attrs = dict(g.attrs); print("attrs:", attrs)
assert list(attrs["source_z_slice"]) == SOURCE_Z_SLICE, f"STOP: finestra sorgente {attrs['source_z_slice']} diversa da {SOURCE_Z_SLICE}"
assert tuple(g["0"].shape) == tuple(LABEL_SHAPE), f"STOP: forma {g['0'].shape} diversa dalla label {LABEL_SHAPE}"
open("/kaggle/working/e03_guard.json", "w").write(json.dumps({"input_zarr": INPUT_ZARR, "input_tree_sha256": tsha,
                                                              "input_files": nfiles, "source_z_slice": SOURCE_Z_SLICE}))
'''

CELL_PREP_SHIFTED_PY = r'''# Passo 8 (prep) — pooling con finestra sorgente spostata, con verifica del manifest di sorgente (piano 2b)
import base64, hashlib, json, os, subprocess, sys, time
os.makedirs(f"{HEAVY}/repo/scripts", exist_ok=True); os.makedirs(f"{HEAVY}/repo/configs/e03", exist_ok=True)
open(f"{HEAVY}/repo/scripts/e03_pool_shifted.py", "w", encoding="utf-8", newline="\n").write(
    base64.b64decode("__POOL_B64__").decode("utf-8"))
MANIFEST_B64 = "__MANIFEST_B64__"
man_path = f"{HEAVY}/repo/configs/e03/source_manifest.json"
if MANIFEST_B64:
    open(man_path, "w", encoding="utf-8", newline="\n").write(base64.b64decode(MANIFEST_B64).decode("utf-8"))
    man_args = ["--verify-source-manifest", man_path]
    print("manifest di sorgente: verifica")
else:
    man_args = ["--source-manifest", f"{WORK}/out/source_manifest_{SEG}.json"]
    print("manifest di sorgente: produzione (primo pooling di questo segmento)")
out_zarr = f"{HEAVY}/input/{SEG}_pooled.zarr" if TAG == "z13" else f"{HEAVY}/input/{SEG}_pooled_{TAG}.zarr"
os.makedirs(f"{HEAVY}/input", exist_ok=True)
cmd = [sys.executable, f"{HEAVY}/repo/scripts/e03_pool_shifted.py", SRC_URL, out_zarr,
       "--level", "2", "--workers", "4", "--z-start", str(Z_START), "--segment", SEG] + man_args
print(" ".join(cmd), flush=True)
t0 = time.time()
r = subprocess.run(cmd, capture_output=True, text=True, timeout=__PREP_TIMEOUT__)
dur = int(time.time() - t0)
open(f"{WORK}/logs/prep_{SEG}_{TAG}.log", "w", encoding="utf-8").write(r.stdout + "\n--- stderr ---\n" + r.stderr)
print(r.stdout[-2000:]); print(r.stderr[-2000:] if r.returncode else "")
assert r.returncode == 0, f"STOP: pooling terminato con exit_code={r.returncode} dopo {dur}s"
print(f"durata_s={dur}")
'''

CELL_PREP_VERIFY_PY = r'''# Passo 8 (prep, segue) — forma, attributi, uguaglianza slice a slice con l'input ufficiale, tar + impronte
import glob, hashlib, io, json, os, tarfile
import numpy as np, zarr
g = zarr.open(out_zarr, mode="r"); a = g["0"]
lab = zarr.open(f"{LABEL_DIR_MOUNTED}/{SEG}_inklabels.zarr", mode="r")["0"]
print("input", a.shape, a.dtype, "| label", lab.shape, "| attrs", dict(g.attrs))
assert tuple(a.shape) == tuple(lab.shape) == tuple(LABEL_SHAPE), f"STOP: forma {a.shape} vs label {lab.shape}"
assert list(g.attrs["source_z_slice"]) == SOURCE_Z_SLICE and str(g.attrs["source_level"]) == "2"
assert g.attrs["source_shape_zyx"][0] == 109, "STOP: volume sorgente con profondita' diversa da 109"
if TAG == "z13":
    assert g.attrs["format"] == "level2-zmean4-21slice-v1", g.attrs["format"]
else:
    assert g.attrs["e03_z_shift_slices"] == (Z_START - 13) // 4 and g.attrs["format"].endswith("+zshift")
    # uguaglianza slice a slice con l'input UFFICIALE montato dal dataset E02: prova diretta dell'allineamento XY
    hits = glob.glob(f"/kaggle/input/**/{SEG}_pooled.zarr/0/.zarray", recursive=True)
    assert hits, "STOP: input ufficiale non montato: impossibile provare l'uguaglianza slice a slice"
    off_dir = os.path.dirname(os.path.dirname(hits[0]))
    osha, _ = tree_sha256(off_dir)
    assert osha == OFFICIAL_INPUT_TREE_SHA256, f"STOP: input ufficiale montato con impronta {osha}"
    a0 = zarr.open(off_dir, mode="r")["0"]
    lo_s, lo_0 = (3, 0) if Z_START < 13 else (0, 3)
    same = True
    for y in range(0, a.shape[1], 512):
        y1 = min(a.shape[1], y + 512)
        if not np.array_equal(np.asarray(a[lo_s:lo_s + 18, y:y1, :]), np.asarray(a0[lo_0:lo_0 + 18, y:y1, :])):
            same = False; print("DIFFERENZA nel blocco y", y, y1); break
    assert same, "STOP: le 18 slice condivise non coincidono con l'input ufficiale"
    print("uguaglianza slice a slice con l'ufficiale: verificata")

def tree_sha256_dir(root):
    per_file = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            per_file[os.path.relpath(p, root).replace(os.sep, "/")] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    h = hashlib.sha256()
    for rel, digest in sorted(per_file.items()):
        h.update(f"{rel}\n{digest}\n".encode())
    return h.hexdigest(), len(per_file)

tsha, nfiles = tree_sha256_dir(out_zarr)
tar_path = f"{WORK}/out/{os.path.basename(out_zarr)[:-5]}.tar"
with tarfile.open(tar_path, "w") as tar:
    for p in sorted(os.path.relpath(os.path.join(d, f), os.path.dirname(out_zarr))
                    for d, _, fs in os.walk(out_zarr) for f in fs):
        info = tar.gettarinfo(os.path.join(os.path.dirname(out_zarr), p), arcname=p)
        info.mtime = 0; info.uid = info.gid = 0; info.uname = info.gname = ""
        with open(os.path.join(os.path.dirname(out_zarr), p), "rb") as fh:
            tar.addfile(info, fh)
tar_sha = hashlib.sha256(open(tar_path, "rb").read()).hexdigest()
info = {"segment": SEG, "tag": TAG, "z_start": Z_START, "source_z_slice": SOURCE_Z_SLICE,
        "shape": list(a.shape), "tree_sha256": tsha, "files": nfiles,
        "tar_sha256": tar_sha, "tar_bytes": os.path.getsize(tar_path), "attrs": dict(g.attrs)}
json.dump(info, open(f"{WORK}/out/input_{SEG}_{TAG}.json", "w"), indent=1, sort_keys=True)
print(json.dumps(info, indent=1))
'''

CELL_INFER_BASH = r"""%%bash
# Passo 6/9 — inferenza seed __SEED__ con la finestra Z dell'offset __TAG__, una sola T4
source /kaggle/working/e03/env.sh
cd $HEAVY
INPUT_ZARR=$(python -c "import json; print(json.load(open('/kaggle/working/e03_guard.json'))['input_zarr'])")
echo "input=$INPUT_ZARR" | tee $WORK/logs/input_path.txt
disk_check "prima inferenza seed__SEED__ __TAG__"
nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv > $WORK/logs/nvidia-smi-before.txt \
  || { echo "STOP: nvidia-smi non disponibile: nessuna GPU assegnata"; exit 1; }
cat $WORK/logs/nvidia-smi-before.txt
export CUDA_VISIBLE_DEVICES=0
python -c "import torch; assert torch.cuda.is_available(); print(torch.__version__, 'visibili', torch.cuda.device_count(), torch.cuda.get_device_name(0))" | tee -a $WORK/logs/env_gpu.txt \
  || { echo "STOP: PyTorch non vede la GPU"; exit 1; }
nvidia-smi --query-gpu=timestamp,index,memory.used --format=csv,noheader,nounits -l 5 > $WORK/logs/gpu_samples.csv &
SAMPLER=$!
set -o pipefail
START=$(date +%s)
timeout -s INT -k 30 __INFER_TIMEOUT__ python -m koine_machines.inference.infer \
  "$INPUT_ZARR" checkpoints/ink_9um/hybrid_3d2d-seed__SEED__/step-075000.pth $WORK/out/__SEG___seed__SEED___step075000___TAG__.tif \
  --overlap 0.5 --blend-mode hann --no-compile --gpus 0 --batch-size 1 __LAYER_ARGS__ \
  2>&1 | tee $WORK/logs/infer_seed__SEED____TAG__.log
EXIT=${PIPESTATUS[0]}; END=$(date +%s)
kill $SAMPLER 2>/dev/null; wait $SAMPLER 2>/dev/null
CAUSA=normale; [ "$EXIT" -eq 124 ] && CAUSA=timeout___INFER_TIMEOUT__s
echo "exit_code=$EXIT durata_s=$((END-START)) causa=$CAUSA" | tee -a $WORK/logs/infer_seed__SEED____TAG__.log
nvidia-smi --query-gpu=index,memory.used --format=csv > $WORK/logs/nvidia-smi-after.txt; cat $WORK/logs/nvidia-smi-after.txt
disk_check "dopo inferenza"
"""

CELL_LOGCHECK_PY = '''# Passo 6/9 (segue) — controlli sul log: indici attesi per QUESTO offset, canali, GPU singola misurata
import csv, re
log = open(f"{WORK}/logs/infer_seed{SEED}_{TAG}.log", encoding="utf-8", errors="replace").read()
m = re.search(r"exit_code=(\\d+) durata_s=(\\d+) causa=(\\S+)", log); assert m, "STOP: riga finale di esito assente nel log"
exit_code, durata, causa = int(m.group(1)), int(m.group(2)), m.group(3)
print("exit_code", exit_code, "durata_s", durata, "causa", causa)
assert exit_code == 0, f"STOP: inferenza terminata con exit_code={exit_code} ({causa})"
expected = "Selected source layer indices=" + str(EXPECTED_INDICES)
assert expected in log, f"STOP: indici di layer diversi da quelli attesi per {TAG}: {EXPECTED_INDICES}"
assert "in_chans=17" in log, "STOP: in_chans diverso da 17"
assert "Using CUDA device 0 for inference." in log, "STOP: il log non conferma l'uso del solo device 0"
assert re.search(r"Wrote .*%s_seed%d_step075000_%s.tif" % (SEG, SEED, TAG), log), "STOP: il log non conferma la scrittura del TIFF"
before = open(f"{WORK}/logs/nvidia-smi-before.txt").read()
gpus_before = [l for l in before.splitlines()[1:] if l.strip()]
assert gpus_before and all("T4" in l for l in gpus_before), f"STOP: GPU inattese o assenti: {gpus_before}"
peak = {}
for row in csv.reader(open(f"{WORK}/logs/gpu_samples.csv")):
    if len(row) >= 3 and row[1].strip().isdigit():
        idx, mem = int(row[1]), int(row[2]); peak[idx] = max(peak.get(idx, 0), mem)
print("picco memoria per GPU (MiB):", peak, "| GPU allocate:", len(gpus_before))
assert peak.get(0, 0) > 200, "STOP: nessun uso misurato della GPU 0"
for idx in peak:
    if idx != 0:
        assert peak[idx] < 100, f"STOP: la GPU {idx} ha usato {peak[idx]} MiB: vincolo di una sola GPU non rispettato"
open(f"{WORK}/logs/gpu_peak.json", "w").write(str(peak))
GPU_DURATION_S = durata
'''

CELL_METRICS_PY = r'''# Passo 6/9 (segue) — metriche del punto della curva con gli script congelati, inlineati dal generatore.
# e02_metrics resta congelato; e03_metrics lo avvolge e aggiunge il blocco di identita' e03_point.
import base64, importlib, json, hashlib, os, sys
from pathlib import Path
repo = f"{WORK}/repo"
os.makedirs(f"{repo}/scripts", exist_ok=True); os.makedirs(f"{repo}/configs/e03", exist_ok=True)
for name, b64 in (("e02_metrics.py", "__E02_METRICS_B64__"), ("tree_sha256.py", "__TREE_B64__"),
                  ("e03_metrics.py", "__E03_METRICS_B64__")):
    src = base64.b64decode(b64).decode("utf-8")
    open(f"{repo}/scripts/{name}", "w", encoding="utf-8", newline="\n").write(src)
    open(f"{WORK}/logs/{name}.sha256", "w").write(hashlib.sha256(src.encode("utf-8")).hexdigest() + "\n")
open(f"{repo}/configs/e03/offsets.json", "w", encoding="utf-8", newline="\n").write(
    base64.b64decode("__OFFSETS_B64__").decode("utf-8"))
sys.path.insert(0, f"{repo}/scripts")
e03m = importlib.import_module("e03_metrics")
tif = Path(f"{WORK}/out/{SEG}_seed{SEED}_step075000_{TAG}.tif")
rep = e03m.build_run_report(tif, Path(LABEL_DIR_MOUNTED), k=K, seed=SEED, threshold=91,
                            input_tree_sha256=INPUT_TREE_SHA256, layer_indices=EXPECTED_INDICES,
                            source_z_slice=SOURCE_Z_SLICE, run_id="E03-R01", sets=("held", "train"))
assert rep["shape_ok"], f"STOP: TIFF {rep['shape']} {rep['dtype']} diverso dalla label"
train = rep["sets"]["train"]
ok_orient = train["orientation"]["orientamento_ok"]
disjoint = rep["disjoint_check"]["n_px_held_and_train"]
gate_A = "superato"
# L'orientamento e' bloccante solo sugli input ufficiali (|k| = 2): per gli input spostati l'allineamento XY e'
# gia' provato dall'uguaglianza slice a slice nel run prep, e a offset grandi il segnale puo' degradarsi.
blocking = (TAG in ("zm2", "zp2"))
if blocking:
    gate_B = "superato" if (ok_orient is True and disjoint == 0) else ("non_valutabile" if ok_orient is None else "fallito")
else:
    gate_B = "superato" if disjoint == 0 else "fallito"
rep.update({"gate_A": gate_A, "gate_B": gate_B, "gate_B_orientation_blocking": blocking,
            "gpu_duration_s": GPU_DURATION_S, "mode": MODE})
json.dump(rep, open(f"{WORK}/out/metrics_{SEG}_s{SEED}_{TAG}.json", "w"), indent=1, sort_keys=True, default=float)
h = rep["sets"]["held"]
print("AUROC held", h["auroc"], "| bestF1", h["best_f1"], "| F1@91", h["at_threshold"]["f1"])
print("AUROC train", train["auroc"], "| orientamento", ok_orient, "(bloccante:", blocking, ") | held&train", disjoint)
print("GATE A:", gate_A, "| GATE B:", gate_B)
'''

CELL_VERDICT_PY = '''# Verdetto del run: dopo la persistenza, un gate non superato rende il run 'error'
import json
res = json.load(open(f"{WORK}/out/metrics_{SEG}_s{SEED}_{TAG}.json"))
print("gate_A =", res["gate_A"], "| gate_B =", res["gate_B"], "| AUROC held =", res["sets"]["held"]["auroc"])
assert res["gate_A"] == "superato" and res["gate_B"] == "superato", \\
    f"E03 run {MODE} NON superato: gate_A={res['gate_A']} gate_B={res['gate_B']} (metriche e log persistiti)"
'''


# --------------------------------------------------------------------------------------------
def _b64(path: Path) -> str:
    return base64.b64encode(path.read_text(encoding="utf-8").encode("utf-8")).decode("ascii")


def build(mode: str, ds: dict, user: str, run_id: str) -> tuple[dict, dict]:
    kind, seg, seed, tag = parse_mode(mode)
    info = SEGMENTS[seg]
    row = ROWS[tag] if tag in ROWS else None
    lab = ds["labels"]["segments"][seg]
    gpu = kind == "infer"

    if kind == "prep":
        z_start = 13 if tag == "z13" else (1 if tag == "zm3" else 25)
        source_z = [z_start, z_start + 84]
        layer_args, expected_idx, k = "", None, None
        input_tree = ""
        manifest_b64 = ""
        if tag != "z13":
            man = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8")) if SOURCE_MANIFEST.exists() else {"segments": {}}
            assert seg in man.get("segments", {}), (
                f"{mode}: manifest di sorgente di {seg} assente in configs/e03/source_manifest.json "
                f"(eseguire prima il pooling ufficiale: locale per 46527, run prep-w016-z13 per w016)")
            manifest_b64 = base64.b64encode(
                json.dumps({"version": man.get("version"), "segments": {seg: man["segments"][seg]}},
                           indent=1, sort_keys=True).encode("utf-8")).decode("ascii")
    else:
        assert row is not None, f"{mode}: tag '{tag}' assente da offsets.json"
        k = int(row["k"])
        z_start = int(row["z_start"])
        source_z = list(row["source_z_slice"])
        expected_idx = list(row["expected_indices"])
        layer_args = ("" if row["layer_start"] is None
                      else f"--layer-start {row['layer_start']} --layer-end {row['layer_end']}")
        key = "official" if row["input"] == "official" else ("shifted_zm3" if row["input"] == "shifted_m3" else "shifted_zp3")
        entry = ds["inputs"][seg][key]
        input_tree = entry.get("tree_sha256") or ""
        assert input_tree, (f"{mode}: tree_sha256 dell'input '{key}' di {seg} ancora null in configs/e03/datasets.json "
                            f"(eseguire il run prep corrispondente e publish-input)")
        manifest_b64 = ""

    official_tree = ds["inputs"][seg]["official"]["tree_sha256"]
    for key in ("file_count", "byte_total", "tree_sha256"):
        assert lab.get(key) is not None, f"{mode}: costante label '{key}' assente"

    cells: list[tuple[str, str]] = [("markdown", CELL_INTRO_MD), ("code", CELL_CONST_PY),
                                    ("code", CELL_GUARD_LABELS_PY.replace("__SEALED__", SEALED))]
    if gpu:
        cells.append(("code", CELL_GUARD_INPUT_PY))
    cells += [("code", reuse("CELL_1_ENV_BASH")), ("code", reuse("CELL_2_NET_PY")), ("code", reuse("CELL_3_CHECKOUT_BASH"))]
    if kind == "prep":
        cells += [("code", reuse("CELL_4P_INSTALL_PREP_PY")), ("code", reuse("CELL_5A_LABEL_PY")),
                  ("code", CELL_PREP_SHIFTED_PY.replace("__PREP_TIMEOUT__", str(PREP_TIMEOUT_S))),
                  ("code", CELL_PREP_VERIFY_PY)]
    else:
        cells += [("code", reuse("CELL_4_INSTALL_PY")), ("code", reuse("CELL_5_CHECKPOINTS_BASH")),
                  ("code", reuse("CELL_5A_LABEL_PY")), ("code", reuse("CELL_6C_MODEL_CPU_PY")),
                  ("code", CELL_INFER_BASH.replace("__INFER_TIMEOUT__", str(INFER_TIMEOUT_S))),
                  ("code", CELL_LOGCHECK_PY), ("code", CELL_METRICS_PY)]
    cells.append(("code", reuse("CELL_10_PERSIST_BASH")))
    if gpu:
        cells.append(("code", CELL_VERDICT_PY))

    subs = {
        "__MODE__": mode, "__KIND__": kind, "__SEG__": seg, "__SHORT__": info["short"],
        "__SEED__": "None" if seed is None else str(seed), "__TAG__": tag,
        "__K__": "None" if k is None else str(k), "__Z_START__": str(z_start),
        "__SOURCE_Z_SLICE__": json.dumps(source_z), "__LAYER_ARGS__": layer_args,
        "__EXPECTED_INDICES__": json.dumps(expected_idx), "__SRC_URL__": info["source"],
        "__LABEL_SHAPE__": json.dumps(info["label_shape"]), "__TORCH__": TORCH_EXPECTED["gpu" if gpu else "cpu"],
        "__LABEL_TREE__": lab["tree_sha256"], "__LABEL_FILES__": str(lab["file_count"]),
        "__LABEL_BYTES__": str(lab["byte_total"]), "__LABEL_ALLOWLIST__": json.dumps(LABEL_ALLOWLIST),
        "__INPUT_TREE__": input_tree, "__OFFICIAL_INPUT_TREE__": official_tree, "__SEALED__": SEALED,
        "__PLAN__": PLAN, "__FAMILY__": info["family"],
        "__E02_METRICS_B64__": _b64(ROOT / "scripts" / "e02_metrics.py"),
        "__E03_METRICS_B64__": _b64(ROOT / "scripts" / "e03_metrics.py"),
        "__TREE_B64__": _b64(ROOT / "scripts" / "tree_sha256.py"),
        "__OFFSETS_B64__": _b64(ROOT / "configs" / "e03" / "offsets.json"),
        "__POOL_B64__": _b64(ROOT / "scripts" / "e03_pool_shifted.py"),
        "__MANIFEST_B64__": manifest_b64,
        # costanti delle celle riusate da E02 che qui non servono ma vanno comunque risolte
        "__SETS__": "held,train", "__INPUT_TREE_SHA256__": input_tree,
    }

    def sub(s: str) -> str:
        for key, value in subs.items():
            s = s.replace(key, value)
        return s

    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                     "language_info": {"name": "python"}},
        "cells": [e02gen.nb_cell(kind_, sub(src)) for kind_, src in cells],
    }
    slug = f"papyruslab-{run_id}-{mode}"
    sources = [f"{user}/{ds['labels']['slug']}"]
    if kind == "prep" and tag != "z13":
        sources.append(f"{user}/{ds['inputs'][seg]['official']['slug']}")          # per l'uguaglianza slice a slice
    if gpu:
        key = "official" if ROWS[tag]["input"] == "official" else ("shifted_zm3" if ROWS[tag]["input"] == "shifted_m3" else "shifted_zp3")
        sources.append(f"{user}/{ds['inputs'][seg][key]['slug']}")
    meta = {
        "id": f"{user}/{slug}", "title": slug, "code_file": f"{slug}.ipynb", "language": "python",
        "kernel_type": "notebook", "is_private": True, "enable_gpu": gpu, "enable_internet": True,
        "dataset_sources": sorted(set(sources)), "competition_sources": [], "kernel_sources": [], "model_sources": [],
    }
    if gpu:
        meta["machine_shape"] = "NvidiaTeslaT4"
    return notebook, meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", default=KAGGLE_USER)
    ap.add_argument("--run-id", default=RUN_ID)
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    ds = json.loads(DATASETS.read_text(encoding="utf-8"))
    generated, skipped = [], []
    for mode in modes():
        if a.only and mode not in a.only:
            continue
        try:
            notebook, meta = build(mode, ds, a.user, a.run_id)
        except AssertionError as ex:
            skipped.append((mode, str(ex)))
            continue
        folder = ROOT / "kaggle" / f"{a.run_id}-{mode}"
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / meta["code_file"], "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n")
        with open(folder / "kernel-metadata.json", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(meta, indent=2) + "\n")
        generated.append(mode)
        print(f"{folder.relative_to(ROOT)}: {len(notebook['cells'])} celle, gpu={meta['enable_gpu']}")
    for mode, why in skipped:
        print(f"non generato {mode}: {why}")
    if a.only and skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()
