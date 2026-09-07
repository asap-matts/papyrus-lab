#!/usr/bin/env python3
"""Generate the Kaggle notebooks for experiment E02 (plan docs/plans/2026-09-06-e02-costruire-il-metro.md, step 5).

One source of truth for the cells (most copied from scripts/build_e00_notebooks.py, the frozen E00 generator);
run modes, one notebook each:
  prep-<short>          - no accelerator: labels, official pooling of the 2.4 um volume (level 2 -> 21 slices), checks, tar, hashes
  infer-<short>-seed42  - one T4: mounted input + labels verified BEFORE any install, inference, log checks, minimal metrics
  infer-<short>-seed43  - one T4: same, guarded by the seed42 outcome of the same segment
with <short> in 46527 (pherc0814-46527), w016 (pherc0139-w016), w029 (pherc1667-w029).

Every stop condition of the plan is an assertion or an `exit 1`. Heavy files live under /tmp/e02 (not persisted);
outputs and logs under /kaggle/working/e02 (persisted as kernel output). Constants (dataset slugs and hashes) come
from configs/e02/datasets.json; a notebook that needs a constant still null is not generated.

Usage:
  python scripts/build_e02_notebooks.py [--user <kaggle-user>] [--run-id e02-r01] [--only prep-46527 ...]
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KAGGLE_USER = "matteopontesilli"
RUN_ID = "e02-r01"
PLAN = "docs/plans/2026-09-06-e02-costruire-il-metro.md"
DATASETS = ROOT / "configs" / "e02" / "datasets.json"
METRICS_SRC = ROOT / "scripts" / "e02_metrics.py"

VILLA_COMMIT = "3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e"
HF_REVISION = "7109667e2607db1b90c37c8b09cb876ea7fe7bb1"
SHA_SEED42 = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
SHA_SEED43 = "2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f"
TORCH_EXPECTED = {"cpu": "2.10.0+cpu", "gpu": "2.10.0+cu128"}
LIMIT_GB = 15
PREP_TIMEOUT_S = 12600
INFER_TIMEOUT_S = 1800

S3 = "https://vesuvius-challenge-open-data.s3.amazonaws.com/"
SEGMENTS = {
    "pherc0814-46527": {
        "short": "46527", "family": "aligned-scrollprizeorg-21slices", "scroll_dir": "PHerc0814",
        "source": S3 + "PHerc0814/segments/20260226000000-46527_2um_try2/surface-volumes/2.399um-0.22m-78keV-volume-20260309142202.zarr",
        "label_shape": [21, 2130, 3455], "sets": "held,train",
    },
    "pherc0139-w016": {
        "short": "w016", "family": "aligned-scrollprizeorg-21slices", "scroll_dir": "PHerc0139",
        "source": S3 + "PHerc0139/segments/20250108000004-w029_2025010827/surface-volumes/2.399um-0.22m-78keV-volume-20260102150214.zarr",
        "label_shape": [21, 7020, 7220], "sets": "held,train",
    },
    "pherc1667-w029": {
        "short": "w029", "family": "aligned-scrollprizeorg-21slices", "scroll_dir": "PHerc1667",
        "source": S3 + "PHerc1667/segments/20251212185248-w029_20251212185248662_flatboi/surface-volumes/2.399um-0.22m-78keV-volume-20251217075048.zarr",
        "label_shape": [21, 9500, 7830], "sets": "train",          # verification segment: held-out pixels sealed until E05
    },
}
SHORT_TO_SEG = {v["short"]: k for k, v in SEGMENTS.items()}
LAYER_INDICES = list(range(2, 19))          # (21 // 2) - (17 // 2) = 2 -> 2..18, centre 10 = annotated plane


def modes() -> list[str]:
    out = []
    for seg in SEGMENTS.values():
        out.append(f"prep-{seg['short']}")
    for seg in SEGMENTS.values():
        out += [f"infer-{seg['short']}-seed42", f"infer-{seg['short']}-seed43"]
    return out


def parse_mode(mode: str) -> tuple[str, str, int | None]:
    """-> (kind, segment_name, seed)"""
    parts = mode.split("-")
    kind, short = parts[0], parts[1]
    seed = int(parts[2][4:]) if len(parts) > 2 else None
    assert kind in ("prep", "infer") and short in SHORT_TO_SEG, mode
    return kind, SHORT_TO_SEG[short], seed


# --------------------------------------------------------------------------------------------
# Cells (placeholders __X__ are substituted per notebook)
# --------------------------------------------------------------------------------------------

CELL_INTRO_MD = f"""# PapyrusLab E02 — run `__MODE__` (segmento `__SEG__`)

Notebook generato da `scripts/build_e02_notebooks.py` (non modificare a mano). Piano congelato: `{PLAN}`.
Ogni controllo di arresto del piano è un'asserzione: se fallisce, il run si ferma e il log dice dove.

- Output persistiti: `/kaggle/working/e02/out` e `/kaggle/working/e02/logs`
- File pesanti (codice, checkpoint, label, input, cache), non persistiti: `/tmp/e02`
"""

CELL_CONST_PY = """MODE = "__MODE__"
KIND = "__KIND__"            # prep | infer
SEG = "__SEG__"              # nome della label, es. pherc0814-46527
SHORT = "__SHORT__"
SEED = __SEED__              # None nel prep
SETS = "__SETS__"            # insiemi di pixel misurati: 'held,train' oppure 'train' (segmento di verifica sigillato)
WORK = "/kaggle/working/e02"
HEAVY = "/tmp/e02"
SRC_URL = "__SRC_URL__"      # volume 2,4 um sorgente (solo prep)
LABEL_SHAPE = __LABEL_SHAPE__
TORCH_EXPECTED = "__TORCH__"
LABEL_TREE_SHA256 = "__LABEL_TREE__"
LABEL_FILES, LABEL_BYTES = __LABEL_FILES__, __LABEL_BYTES__
INPUT_TREE_SHA256 = "__INPUT_TREE__"     # atteso solo nei run infer
print("MODE", MODE, "SEG", SEG, "SEED", SEED, "SETS", SETS, "torch atteso", TORCH_EXPECTED)
"""

CELL_GUARD_INPUT_PY = r'''# Guardia iniziale (run GPU): input poolato e label devono essere montati e con hash corretto PRIMA di qualunque
# installazione (piano §4 passo 5, revisione R1 finding 6). Nessun pooling in sessione GPU.
import glob, hashlib, os, json

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
hits = glob.glob(f"/kaggle/input/**/{SEG}_pooled.zarr/0/.zarray", recursive=True)
assert hits, f"STOP: input poolato {SEG}_pooled.zarr non montato sotto /kaggle/input: ripararlo con il run prep (CPU), mai qui"
INPUT_ZARR = os.path.dirname(os.path.dirname(hits[0]))
tsha, nfiles = tree_sha256(INPUT_ZARR)
print("input:", INPUT_ZARR, "file", nfiles, "tree_sha256", tsha)
assert tsha == INPUT_TREE_SHA256, f"STOP: tree_sha256 dell'input montato ({tsha}) diverso da quello congelato ({INPUT_TREE_SHA256})"
lab_hits = glob.glob(f"/kaggle/input/**/{SEG}/{SEG}_inklabels.zarr/0/.zarray", recursive=True)
assert lab_hits, f"STOP: label {SEG} non montata sotto /kaggle/input (dataset delle label assente)"
print("label montata:", os.path.dirname(os.path.dirname(os.path.dirname(lab_hits[0]))))
open(f"/kaggle/working/e02_guard.json", "w").write(json.dumps({"input_zarr": INPUT_ZARR, "input_tree_sha256": tsha, "input_files": nfiles}))
'''

CELL_GUARD_SEED43_PY = r'''# Guardia del run seed43: il seed 42 dello stesso segmento deve avere superato i gate, PRIMA di spendere GPU (come E00).
import json, os, glob, hashlib
hits = glob.glob(f"/kaggle/input/**/metrics_{SEG}_seed42.json", recursive=True)
assert hits, f"STOP: metrics_{SEG}_seed42.json non trovato sotto /kaggle/input (dataset seed42-out non montato)"
SRC42 = os.path.dirname(hits[0])
r42 = json.load(open(hits[0]))
assert r42.get("gate_A") == "superato" and r42.get("gate_B") == "superato", f"STOP: il run seed42 non ha superato i gate ({r42.get('gate_A')}, {r42.get('gate_B')})"
TIF42 = os.path.join(SRC42, f"{SEG}_seed42_step075000.tif")
assert os.path.exists(TIF42), f"STOP: TIFF del seed42 assente accanto a {hits[0]}"
sha42 = hashlib.sha256(open(TIF42, "rb").read()).hexdigest()
# la chiave del report di e02_metrics e' sha256_pred (revisione R2, finding 1: 'sha256_tif' non esiste nel JSON)
assert sha42 == r42["sha256_pred"], f"STOP: SHA-256 del TIFF seed42 montato ({sha42}) diverso da quello registrato ({r42['sha256_pred']})"
print("guardia seed43 superata: seed42 gate_A/B =", r42["gate_A"], r42["gate_B"], "| TIFF verificato in", SRC42)
'''

CELL_1_ENV_BASH = r"""%%bash
# Passo 1 — radice misurabile, cache e temporanei dirottati, guardia dei __LIMIT_GB__ GB
set -e
mkdir -p /kaggle/working/e02/out /kaggle/working/e02/logs /tmp/e02/tmp /tmp/e02/cache/pip /tmp/e02/cache/hf /tmp/e02/checkpoints /tmp/e02/labels /tmp/e02/input
cat > /kaggle/working/e02/env.sh <<'EOF'
export WORK=/kaggle/working/e02
export HEAVY=/tmp/e02
export TMPDIR=$HEAVY/tmp PIP_CACHE_DIR=$HEAVY/cache/pip HF_HOME=$HEAVY/cache/hf
export LIMIT_BYTES=$((__LIMIT_GB__*1024*1024*1024))
disk_check () {
  local used
  used=$(( $(du -sb "$WORK" | cut -f1) + $(du -sb "$HEAVY" | cut -f1) ))
  echo "spazio_byte=$used ($1)" | tee -a "$WORK/logs/disk_check.log"
  if [ "$used" -gt "$LIMIT_BYTES" ]; then echo "STOP: superati __LIMIT_GB__ GB ($1)" | tee -a "$WORK/logs/disk_check.log"; exit 1; fi
}
EOF
source /kaggle/working/e02/env.sh
echo "MODE=__MODE__ SEG=__SEG__ SEED=__SEED__ start=$(date -u +%FT%TZ)" > $WORK/logs/run_info.txt
disk_check "inizio"
df -h /kaggle/working /tmp | tail -2
""".replace("__LIMIT_GB__", str(LIMIT_GB))

CELL_2_NET_PY = """# Passo 1 (segue) — versioni dell'ambiente e rete verso le sorgenti
import sys, platform, json, urllib.request, torch
env = {"python": sys.version.split()[0], "platform": platform.platform(),
       "torch": torch.__version__, "cuda_available": torch.cuda.is_available(),
       "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0}
print(json.dumps(env, indent=1))
json.dump(env, open(f"{WORK}/logs/env_before_install.json", "w"), indent=1)
assert env["torch"] == TORCH_EXPECTED, f"STOP: PyTorch inatteso {env['torch']} (atteso {TORCH_EXPECTED}): Kaggle ha cambiato immagine, aggiornare il piano"
if KIND == "prep":
    assert not env["cuda_available"], "STOP: il run prep deve girare senza acceleratore"
else:
    assert env["cuda_available"], "STOP: run GPU senza CUDA disponibile"
urls = ["https://huggingface.co/api/models/scrollprize/ink_9um", "https://huggingface.co/api/buckets/scrollprize/datasets"]
if KIND == "prep":
    urls.insert(0, SRC_URL + "/2/.zarray")
for url in urls:
    with urllib.request.urlopen(url, timeout=30) as r:
        print(r.status, url[:90]); assert r.status == 200, f"STOP: rete non raggiunge {url}"
"""

CELL_3_CHECKOUT_BASH = r"""%%bash
# Passo 2 — checkout parziale di villa al commit congelato
set -e
source /kaggle/working/e02/env.sh
cd $HEAVY
[ -d villa/.git ] || git clone -q --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa.git
cd villa
git sparse-checkout init --cone >/dev/null
git sparse-checkout set ink-detection vesuvius >/dev/null
git checkout -q __VILLA_COMMIT__
HEAD=$(git rev-parse HEAD); echo "villa HEAD=$HEAD" | tee $WORK/logs/villa_commit.txt
[ "$HEAD" = "__VILLA_COMMIT__" ] || { echo "STOP: commit villa diverso"; exit 1; }
ls -l ink-detection/koine_machines/inference/infer.py ink-detection/scripts/prepare_9um_isotropic_input.py vesuvius/pyproject.toml ink-detection/uv.lock
sha256sum ink-detection/scripts/prepare_9um_isotropic_input.py | tee $WORK/logs/prepare_script_sha256.txt
disk_check "dopo checkout"
""".replace("__VILLA_COMMIT__", VILLA_COMMIT)

# Same install cell as E00 (frozen procedure): system Python, --no-deps, PyTorch untouched.
CELL_4_INSTALL_PY = r'''# Passo 3 — installazione sul Python di sistema, tutto con --no-deps, PyTorch intatto (cella di E00, invariata)
import subprocess, re, json, sys
VILLA = f"{HEAVY}/villa"
PY = sys.executable

def sh(args):
    return subprocess.run(args, capture_output=True, text=True)

def pip(*args):
    return sh([PY, "-m", "pip", "install", "--no-deps", *args])

def torch_version():
    return sh([PY, "-c", "import torch; print(torch.__version__)"]).stdout.strip()

torch_before = torch_version()
for pkg in ["vesuvius", "ink-detection"]:
    r = pip("-e", f"{VILLA}/{pkg}")
    assert r.returncode == 0, "STOP: pip install fallita\n" + r.stderr[-3000:]
r = pip("zarr==2.18.7", "numcodecs==0.15.1")   # il codice usa l'API Zarr v2
assert r.returncode == 0, "STOP: pip install zarr/numcodecs fallita\n" + r.stderr[-3000:]

lock = open(f"{VILLA}/ink-detection/uv.lock", encoding="utf-8").read()
def locked_version(dist):
    m = re.search(r'\[\[package\]\]\nname = "' + re.escape(dist.lower()) + r'"\nversion = "([^"]+)"', lock)
    return m.group(1) if m else None

ALIAS = {"cv2": "opencv-contrib-python-headless", "PIL": "pillow", "yaml": "pyyaml", "nrrd": "pynrrd",
         "cc3d": "connected-components-3d", "skimage": "scikit-image", "sklearn": "scikit-learn"}
added, numpy_downgraded = [], False

def ensure_import(modname):
    global numpy_downgraded
    for attempt in range(12):
        r = sh([PY, "-c", f"import {modname}"])
        if r.returncode == 0:
            return
        err = r.stderr
        m = re.search(r"No module named '([^'.]+)", err)
        if m:
            mod = m.group(1)
            assert re.fullmatch(r"[A-Za-z0-9_]+", mod), f"STOP: nome di modulo inatteso {mod!r}"
            cands = ([ALIAS[mod]] if mod in ALIAS else []) + [mod, mod.replace("_", "-")]
            dist = next((c for c in cands if locked_version(c)), None)
            assert dist, f"STOP: modulo mancante '{mod}' non presente in uv.lock:\n" + err[-2000:]
            ver = locked_version(dist)
            r2 = pip(f"{dist}=={ver}")
            assert r2.returncode == 0, f"STOP: pip install {dist}=={ver} fallita\n" + r2.stderr[-3000:]
            added.append({"module": mod, "dist": dist, "version": ver}); print("aggiunto", dist, ver, "per", modname)
        elif "numpy" in err.lower() and not numpy_downgraded:
            r2 = pip("numpy<=2.2"); assert r2.returncode == 0, r2.stderr[-3000:]
            numpy_downgraded = True; added.append({"module": "numpy", "dist": "numpy", "version": "<=2.2 (eccezione piano)"})
        else:
            raise AssertionError(f"STOP: import di {modname} fallito per motivo diverso da modulo mancante:\n" + err[-3000:])
    raise AssertionError(f"STOP: import di {modname} ancora fallito dopo i tentativi ammessi")

for modname in ["koine_machines.inference.infer", "vesuvius", "vesuvius.models.build.build_network_from_config",
                "koine_machines.models.make_model"]:
    ensure_import(modname)
for lazy in ["imagecodecs"]:
    if sh([PY, "-c", f"import {lazy}"]).returncode != 0:
        ver = locked_version(lazy); assert ver, f"STOP: {lazy} non presente in uv.lock"
        r2 = pip(f"{lazy}=={ver}"); assert r2.returncode == 0, f"STOP: pip install {lazy}=={ver} fallita\n" + r2.stderr[-3000:]
        added.append({"module": lazy, "dist": lazy, "version": ver}); print("aggiunto", lazy, ver, "(dipendenza pigra di tifffile)")
assert len(added) <= 10, f"STOP: {len(added)} pacchetti aggiunti, oltre il limite di dieci del piano"

torch_after = torch_version()
assert torch_after == torch_before == TORCH_EXPECTED, f"STOP: PyTorch cambiato da {torch_before} a {torch_after}"
helptxt = sh([PY, "-m", "koine_machines.inference.infer", "--help"]).stdout
for flag in ["--no-compile", "--gpus", "--layer-start"]:
    assert flag in helptxt, f"STOP: opzione {flag} assente nell'entry point"
hf = sh(["hf", "--version"])
if hf.returncode != 0:
    r2 = pip("huggingface_hub"); assert r2.returncode == 0, r2.stderr[-2000:]
    hf = sh(["hf", "--version"]); added.append({"module": "hf", "dist": "huggingface_hub", "version": hf.stdout.strip()})
pipl = [l for l in sh([PY, "-m", "pip", "list"]).stdout.splitlines()
        if re.match(r"(?i)^(torch|torchvision|zarr|numcodecs|numpy|tifffile|timm|scipy|fsspec|s3fs|aiohttp|huggingface.hub|monai|koine.machines|vesuvius|albumentations|einops|opencv|imagecodecs) ", l)]
open(f"{WORK}/logs/pip_versions.txt", "w").write("\n".join(pipl) + "\n")
info = {"torch_before": torch_before, "torch_after": torch_after, "added_packages": added, "hf_version": hf.stdout.strip()}
json.dump(info, open(f"{WORK}/logs/install.json", "w"), indent=1)
print(json.dumps(info, indent=1)); print("\n".join(pipl))
'''

# prep runs need only zarr/numcodecs (Zarr v2 API) for the official pooling script: no koine_machines install.
CELL_4P_INSTALL_PREP_PY = r'''# Passo 3 (prep) — sole dipendenze del pooling ufficiale: zarr 2.18.7 e numcodecs 0.15.1 (come E00), niente altro
import subprocess, sys, json, re
PY = sys.executable
torch_before = subprocess.run([PY, "-c", "import torch; print(torch.__version__)"], capture_output=True, text=True).stdout.strip()
r = subprocess.run([PY, "-m", "pip", "install", "--no-deps", "zarr==2.18.7", "numcodecs==0.15.1"], capture_output=True, text=True)
assert r.returncode == 0, "STOP: pip install zarr/numcodecs fallita\n" + r.stderr[-3000:]
# Tentativo 1 di prep-46527 (7 settembre 2026): zarr 2.18.7 importa `asciitree`, assente sull'immagine CPU di Kaggle.
# Stesso ciclo di E00: ogni modulo mancante si installa con --no-deps nella versione del lock di villa (max 10).
lock = open(f"{HEAVY}/villa/ink-detection/uv.lock", encoding="utf-8").read()
def locked_version(dist):
    m = re.search(r'\[\[package\]\]\nname = "' + re.escape(dist.lower()) + r'"\nversion = "([^"]+)"', lock)
    return m.group(1) if m else None
added = []
for attempt in range(10):
    chk = subprocess.run([PY, "-c", "import zarr, numcodecs, numpy, fsspec, aiohttp; print(zarr.__version__, numcodecs.__version__, numpy.__version__, fsspec.__version__, aiohttp.__version__)"], capture_output=True, text=True)
    if chk.returncode == 0:
        break
    m = re.search(r"No module named '([^'.]+)", chk.stderr)
    assert m, "STOP: import fallito per motivo diverso da modulo mancante\n" + chk.stderr[-2000:]
    mod = m.group(1); assert re.fullmatch(r"[A-Za-z0-9_]+", mod), mod
    dist = next((c for c in (mod, mod.replace("_", "-")) if locked_version(c)), None)
    assert dist, f"STOP: modulo mancante '{mod}' non presente in uv.lock"
    r2 = subprocess.run([PY, "-m", "pip", "install", "--no-deps", f"{dist}=={locked_version(dist)}"], capture_output=True, text=True)
    assert r2.returncode == 0, f"STOP: pip install {dist} fallita\n" + r2.stderr[-2000:]
    added.append({"module": mod, "dist": dist, "version": locked_version(dist)}); print("aggiunto", dist, locked_version(dist))
assert chk.returncode == 0, "STOP: import ancora fallito dopo i tentativi ammessi\n" + chk.stderr[-2000:]
torch_after = subprocess.run([PY, "-c", "import torch; print(torch.__version__)"], capture_output=True, text=True).stdout.strip()
assert torch_after == torch_before == TORCH_EXPECTED, f"STOP: PyTorch cambiato da {torch_before} a {torch_after}"
vers = chk.stdout.strip().split()
assert vers[0] == "2.18.7", f"STOP: zarr {vers[0]} invece di 2.18.7"
info = {"torch_before": torch_before, "torch_after": torch_after, "zarr": vers[0], "numcodecs": vers[1], "numpy": vers[2], "fsspec": vers[3], "aiohttp": vers[4], "added_packages": added}
json.dump(info, open(f"{WORK}/logs/install.json", "w"), indent=1); print(info)
'''

CELL_5_CHECKPOINTS_BASH = r"""%%bash
# Passo 4 — checkpoint con verifica esatta di hash e dimensioni (cella di E00)
set -e
source /kaggle/working/e02/env.sh
cd $HEAVY
disk_check "prima dei checkpoint"
hf download scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth hybrid_3d2d-seed43/step-075000.pth \
   --revision __HF_REVISION__ --local-dir checkpoints/ink_9um > /dev/null
sha256sum checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth checkpoints/ink_9um/hybrid_3d2d-seed43/step-075000.pth | tee $WORK/logs/checkpoints_sha256.txt
stat -c "%s %n" checkpoints/ink_9um/hybrid_3d2d-seed4*/step-075000.pth | tee -a $WORK/logs/checkpoints_sha256.txt
grep -q "^__SHA42__  checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth" $WORK/logs/checkpoints_sha256.txt || { echo "STOP: SHA-256 seed42 diverso"; exit 1; }
grep -q "^__SHA43__  checkpoints/ink_9um/hybrid_3d2d-seed43/step-075000.pth" $WORK/logs/checkpoints_sha256.txt || { echo "STOP: SHA-256 seed43 diverso"; exit 1; }
disk_check "dopo i checkpoint"
""".replace("__HF_REVISION__", HF_REVISION).replace("__SHA42__", SHA_SEED42).replace("__SHA43__", SHA_SEED43)

CELL_5A_LABEL_PY = r'''# Passo 4 (segue) — label del segmento dal dataset Kaggle privato (ricerca ricorsiva: il mount cambia fra sessioni
# CPU e GPU, lezione di E00), verificata file per file contro manifest.json e per contenuto (tree_sha256);
# ripiego: download diretto dal bucket con 4 thread e attesa crescente (HTTP 429), come E00.
import hashlib, os, shutil, json, glob, re, time, urllib.request, concurrent.futures as cf
PREFIX = f"ink_9um/labels/__FAMILY__/{SEG}/"
API = "https://huggingface.co/api/buckets/scrollprize/datasets/tree/" + PREFIX.rstrip("/")
RESOLVE = "https://huggingface.co/buckets/scrollprize/datasets/resolve/"
DEST = f"{HEAVY}/labels/{SEG}"

def tree_sha256(root):
    per_file = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            per_file[os.path.relpath(p, root).replace(os.sep, "/")] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    h = hashlib.sha256()
    for rel, digest in sorted(per_file.items()):
        h.update(f"{rel}\n{digest}\n".encode())
    return h.hexdigest(), per_file

def check_label_tree(dest, source_desc):
    n = sum(len(fs) for _, _, fs in os.walk(dest)); b = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(dest) for f in fs)
    assert (n, b) == (LABEL_FILES, LABEL_BYTES), f"STOP: label con {n} file / {b} byte, attesi {(LABEL_FILES, LABEL_BYTES)}"
    tsha, _ = tree_sha256(dest)
    assert tsha == LABEL_TREE_SHA256, f"STOP: contenuto della label diverso da quello congelato (tree sha256 {tsha})"
    open(f"{WORK}/logs/label_count.txt", "w").write(f"seg={SEG} file={n} byte={b} tree_sha256={tsha} source={source_desc}\n")
    za = json.load(open(f"{dest}/{SEG}_inklabels.zarr/0/.zarray")); open(f"{WORK}/logs/label_zarray.json", "w").write(json.dumps(za))
    assert za["shape"] == LABEL_SHAPE, f"STOP: forma della label {za['shape']} diversa da {LABEL_SHAPE}"
    print(f"label verificata: file={n} byte={b} tree_sha256={tsha} ({source_desc}) shape={za['shape']}")

roots = glob.glob(f"/kaggle/input/**/{SEG}/{SEG}_inklabels.zarr/0/.zarray", recursive=True)
manifests = [m for m in glob.glob("/kaggle/input/**/manifest.json", recursive=True) if SEG in json.load(open(m)).get("segments", {})]
print("label montata:", roots[:1], "| manifest:", manifests[:1])
if os.path.isdir(DEST):
    shutil.rmtree(DEST)
if roots and manifests:
    src = os.path.dirname(os.path.dirname(os.path.dirname(roots[0])))       # .../<SEG>
    man = json.load(open(manifests[0]))["segments"][SEG]
    files = man["files"]
    assert (len(files), sum(f["size"] for f in files)) == (LABEL_FILES, LABEL_BYTES), "STOP: manifest del dataset diverso dalle costanti congelate"
    missing = [f["path"] for f in files if not (os.path.isfile(os.path.join(src, f["path"][len(PREFIX):])) and os.path.getsize(os.path.join(src, f["path"][len(PREFIX):])) == f["size"])]
    assert not missing, f"STOP: {len(missing)} file della label mancanti o di dimensione diversa, p.es. {missing[:3]}"
    shutil.copytree(src, DEST)
    check_label_tree(DEST, f"kaggle_dataset manifest_sha256={hashlib.sha256(open(manifests[0], 'rb').read()).hexdigest()}")
else:
    assert KIND == "prep", "STOP: nei run GPU la label deve essere montata (nessun ripiego di rete con la GPU allocata)"
    def list_label_files():
        files, url = [], API
        while url:
            req = urllib.request.Request(url, headers={"User-Agent": "papyruslab-e02"})
            with urllib.request.urlopen(req, timeout=60) as r:
                files += [(e["path"], int(e["size"])) for e in json.load(r) if e.get("type") == "file"]
                m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", "") or "")
                url = m.group(1) if m else None
        return files
    def fetch(item):
        path, size = item
        assert path.startswith(PREFIX) and ".." not in path, f"STOP: percorso inatteso {path}"
        out = os.path.join(DEST, path[len(PREFIX):])
        if os.path.exists(out) and os.path.getsize(out) == size:
            return size
        os.makedirs(os.path.dirname(out), exist_ok=True)
        last = None
        for attempt in range(8):
            try:
                req = urllib.request.Request(RESOLVE + path, headers={"User-Agent": "papyruslab-e02"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = r.read()
                if len(data) == size:
                    open(out, "wb").write(data); return size
                last = f"dimensione {len(data)} != {size}"
            except Exception as ex:
                last = ex
            time.sleep(min(60, 5 * 2 ** attempt))
        raise RuntimeError(f"STOP: download fallito per {path}: {last}")
    files = list_label_files(); total = sum(s for _, s in files)
    assert (len(files), total) == (LABEL_FILES, LABEL_BYTES), f"STOP: label diversa dalla misura congelata: {len(files)} file, {total} byte"
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        got = sum(ex.map(fetch, files))
    print(f"scaricati {got} byte in {time.time() - t0:.0f} s")
    check_label_tree(DEST, "direct_download")
'''

CELL_6_PREP_BASH = r"""%%bash
# Passo 5 (prep) — pooling ufficiale: livello 2 del volume 2,4 um, 84 piani centrali mediati a 4 a 4 -> 21 slice
set -e
source /kaggle/working/e02/env.sh
cd $HEAVY
disk_check "prima del pooling"
START=$(date +%s)
set -o pipefail
timeout -s INT -k 60 __PREP_TIMEOUT__ python villa/ink-detection/scripts/prepare_9um_isotropic_input.py \
  "__SRC_URL__" input/__SEG___pooled.zarr --level 2 --workers 4 2>&1 | tee $WORK/logs/prep___SEG__.log
EXIT=${PIPESTATUS[0]}; END=$(date +%s)
echo "exit_code=$EXIT durata_s=$((END-START))" | tee -a $WORK/logs/prep___SEG__.log
[ "$EXIT" -eq 0 ] || { echo "STOP: pooling terminato con exit_code=$EXIT"; exit 1; }
du -sh input/__SEG___pooled.zarr | tee -a $WORK/logs/prep___SEG__.log
disk_check "dopo il pooling"
""".replace("__PREP_TIMEOUT__", str(PREP_TIMEOUT_S))

CELL_6B_PREP_VERIFY_PY = r'''# Passo 5 (prep, segue) — verifica dell'input poolato contro la label, tar deterministico, hash
import json, os, io, tarfile, hashlib, time
import numpy as np, zarr
P = f"{HEAVY}/input/{SEG}_pooled.zarr"
g = zarr.open(P, mode="r"); a = g["0"]
lab = zarr.open(f"{HEAVY}/labels/{SEG}/{SEG}_inklabels.zarr", mode="r")["0"]
print("input", a.shape, a.dtype, a.chunks, "| label", lab.shape, "| attrs", dict(g.attrs))
assert tuple(a.shape) == tuple(lab.shape) == tuple(LABEL_SHAPE), f"STOP: input poolato {a.shape} vs label {lab.shape}"
assert list(g.attrs["source_z_slice"]) == [13, 97] and str(g.attrs["source_level"]) == "2" and str(a.dtype) == "uint8", g.attrs
assert g.attrs["source_shape_zyx"][0] == 109, "STOP: volume sorgente con profondita' diversa da 109"
cy, cx = a.shape[1] // 2, a.shape[2] // 2
blk = a[:, cy - 64: cy + 64, cx - 64: cx + 64]
assert blk.max() > 0, "STOP: blocco centrale vuoto"
zero_frac = float((a[10] == 0).mean())
print("frazione di zeri al piano 10:", round(zero_frac, 4))

def tree_sha256(root):
    per_file = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            per_file[os.path.relpath(p, root).replace(os.sep, "/")] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    h = hashlib.sha256()
    for rel, digest in sorted(per_file.items()):
        h.update(f"{rel}\n{digest}\n".encode())
    return h.hexdigest(), per_file

tsha, per_file = tree_sha256(P)
rels = sorted(per_file)
t0 = time.time()
tar_path = f"{WORK}/out/{SEG}_pooled.tar"
with tarfile.open(tar_path, mode="w", format=tarfile.PAX_FORMAT) as tf:      # deterministico: ordine, mtime 0, uid/gid 0
    for rel in rels:
        full = os.path.join(P, rel)
        info = tarfile.TarInfo(name=f"{SEG}_pooled.zarr/{rel}")
        info.size = os.path.getsize(full); info.mtime = 0; info.uid = info.gid = 0; info.uname = info.gname = ""; info.mode = 0o644
        with open(full, "rb") as fh:
            tf.addfile(info, fh)
tar_sha = hashlib.sha256(open(tar_path, "rb").read()).hexdigest()
tar_bytes = os.path.getsize(tar_path)
assert tar_bytes < 5 * 1024 ** 3, f"STOP: tar di {tar_bytes} byte oltre i 5 GB"
man = {"segment": SEG, "source_volume_url": SRC_URL, "source_level": "2", "attrs": dict(g.attrs), "shape": list(a.shape), "dtype": str(a.dtype),
       "chunks": list(a.chunks), "zero_fraction_plane10": zero_frac, "file_count": len(rels), "byte_total": sum(os.path.getsize(os.path.join(P, r)) for r in rels),
       "tree_sha256": tsha, "tar_name": os.path.basename(tar_path), "tar_bytes": tar_bytes, "tar_sha256": tar_sha,
       "tree_sha256_definition": "sha256 over sorted lines 'relpath\\nsha256(file)\\n', relpath relative to <SEG>_pooled.zarr/",
       "prepare_script_sha256": open(f"{WORK}/logs/prepare_script_sha256.txt").read().split()[0], "tar_seconds": round(time.time() - t0, 1)}
json.dump(man, open(f"{WORK}/out/prep_manifest_{SEG}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in man.items() if k != "attrs"}, indent=1))
'''

CELL_6C_MODEL_CPU_PY = """# Passo 5 (infer) — costruire il modello dal checkpoint su CPU come fa infer.py, in sottoprocesso (cella di E00)
import subprocess, sys, json
code = r'''
import argparse, json, torch
from koine_machines.inference import infer as kinfer
args = argparse.Namespace(checkpoint="__CKPT__", amp_dtype="auto", model_type="auto", metadata_json=None)
cm = kinfer.configure_model(args)
info = {"in_chans": int(cm.in_chans), "amp_dtype": str(cm.amp_dtype),
        "n_params": int(sum(p.numel() for p in cm.model.parameters())),
        "model_class": type(cm.model).__name__, "preprocessing": str(cm.preprocessing)[:200]}
print("MODEL_BUILD_JSON=" + json.dumps(info))
'''.replace("__CKPT__", f"{HEAVY}/checkpoints/ink_9um/hybrid_3d2d-seed{SEED}/step-075000.pth")
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
print(r.stdout[-1500:]); print(r.stderr[-1500:])
assert r.returncode == 0, "STOP: costruzione del modello su CPU fallita (vedi stderr sopra)"
info = json.loads(r.stdout.split("MODEL_BUILD_JSON=")[1].splitlines()[0])
json.dump(info, open(f"{WORK}/logs/model_build_cpu.json", "w"), indent=1)
assert info["in_chans"] == 17, "STOP: il checkpoint non dichiara 17 slice in ingresso"
assert "float16" in info["amp_dtype"], f"STOP: AMP dtype inatteso {info['amp_dtype']}"
print("modello costruito su CPU:", info)
"""

CELL_7_INFER_BASH = r"""%%bash
# Passo 7 — inferenza seed __SEED__ sull'input poolato montato, una sola T4 (CUDA_VISIBLE_DEVICES=0), timeout 30 minuti
source /kaggle/working/e02/env.sh
cd $HEAVY
INPUT_ZARR=$(python -c "import json; print(json.load(open('/kaggle/working/e02_guard.json'))['input_zarr'])")
echo "input=$INPUT_ZARR" | tee $WORK/logs/input_path.txt
disk_check "prima inferenza seed__SEED__"
nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv > $WORK/logs/nvidia-smi-before-seed__SEED__.txt \
  || { echo "STOP: nvidia-smi non disponibile: nessuna GPU assegnata"; exit 1; }
cat $WORK/logs/nvidia-smi-before-seed__SEED__.txt
export CUDA_VISIBLE_DEVICES=0
python -c "import torch; assert torch.cuda.is_available(); print(torch.__version__, 'visibili', torch.cuda.device_count(), torch.cuda.get_device_name(0))" | tee -a $WORK/logs/env_gpu.txt \
  || { echo "STOP: PyTorch non vede la GPU"; exit 1; }
nvidia-smi --query-gpu=timestamp,index,memory.used --format=csv,noheader,nounits -l 5 > $WORK/logs/gpu_samples_seed__SEED__.csv &
SAMPLER=$!
set -o pipefail
START=$(date +%s)
timeout -s INT -k 30 __INFER_TIMEOUT__ python -m koine_machines.inference.infer \
  "$INPUT_ZARR" checkpoints/ink_9um/hybrid_3d2d-seed__SEED__/step-075000.pth $WORK/out/__SEG___seed__SEED___step075000.tif \
  --overlap 0.5 --blend-mode hann --no-compile --gpus 0 --batch-size 1 \
  2>&1 | tee $WORK/logs/infer_seed__SEED__.log
EXIT=${PIPESTATUS[0]}; END=$(date +%s)
kill $SAMPLER 2>/dev/null; wait $SAMPLER 2>/dev/null
CAUSA=normale; [ "$EXIT" -eq 124 ] && CAUSA=timeout___INFER_TIMEOUT__s
echo "exit_code=$EXIT durata_s=$((END-START)) causa=$CAUSA" | tee -a $WORK/logs/infer_seed__SEED__.log
nvidia-smi --query-gpu=index,memory.used --format=csv > $WORK/logs/nvidia-smi-after-seed__SEED__.txt; cat $WORK/logs/nvidia-smi-after-seed__SEED__.txt
disk_check "dopo inferenza seed__SEED__"
""".replace("__INFER_TIMEOUT__", str(INFER_TIMEOUT_S))

CELL_7B_LOGCHECK_PY = """# Passo 7 (segue) — controlli sul log: codice di uscita, finestra Z 2-18, canali, GPU singola misurata (cella di E00 adattata)
import re, csv
log = open(f"{WORK}/logs/infer_seed{SEED}.log", encoding="utf-8", errors="replace").read()
m = re.search(r"exit_code=(\\d+) durata_s=(\\d+) causa=(\\S+)", log); assert m, "STOP: riga finale di esito assente nel log"
exit_code, durata, causa = int(m.group(1)), int(m.group(2)), m.group(3)
print("exit_code", exit_code, "durata_s", durata, "causa", causa)
assert exit_code == 0, f"STOP: inferenza terminata con exit_code={exit_code} ({causa})"
expected = "Selected source layer indices=" + str(__LAYER_INDICES__)
assert expected in log, "STOP: indici di layer diversi da 2-18 (input a 21 slice)"
assert "in_chans=17" in log, "STOP: in_chans diverso da 17"
assert "Using CUDA device 0 for inference." in log, "STOP: il log non conferma l'uso del solo device 0"
assert re.search(r"Wrote .*%s_seed%d_step075000.tif" % (SEG, SEED), log), "STOP: il log non conferma la scrittura del TIFF"
before = open(f"{WORK}/logs/nvidia-smi-before-seed{SEED}.txt").read()
gpus_before = [l for l in before.splitlines()[1:] if l.strip()]
assert gpus_before and all("T4" in l for l in gpus_before), f"STOP: GPU inattese o assenti prima del run: {gpus_before}"
peak = {}
for row in csv.reader(open(f"{WORK}/logs/gpu_samples_seed{SEED}.csv")):
    if len(row) >= 3 and row[1].strip().isdigit():
        idx, mem = int(row[1]), int(row[2]); peak[idx] = max(peak.get(idx, 0), mem)
print("campioni memoria (MiB, picco per GPU):", peak, "| GPU allocate:", len(gpus_before))
assert peak.get(0, 0) > 200, "STOP: nessun uso misurato della GPU 0 durante l'inferenza"
for idx in peak:
    if idx != 0:
        assert peak[idx] < 100, f"STOP: la GPU {idx} ha usato {peak[idx]} MiB: il vincolo di una sola GPU non e' rispettato"
open(f"{WORK}/logs/gpu_peak_seed{SEED}.json", "w").write(str(peak))
""".replace("__LAYER_INDICES__", str(LAYER_INDICES))

CELL_8_METRICS_PY = r'''# Passo 8 — metriche minime con lo script congelato scripts/e02_metrics.py (inlineato dal generatore: il repository e' privato)
import json, hashlib, os, sys, importlib, base64
METRICS_SOURCE = base64.b64decode("__METRICS_B64__").decode("utf-8")
open(f"{WORK}/e02_metrics.py", "w", encoding="utf-8", newline="\n").write(METRICS_SOURCE)
open(f"{WORK}/logs/e02_metrics_sha256.txt", "w").write(hashlib.sha256(METRICS_SOURCE.encode("utf-8")).hexdigest() + "\n")
sys.path.insert(0, WORK); m = importlib.import_module("e02_metrics")
from pathlib import Path
tif = Path(f"{WORK}/out/{SEG}_seed{SEED}_step075000.tif")
sets = tuple(s for s in SETS.split(",") if s)
rep = m.build_report(tif, Path(f"{HEAVY}/labels/{SEG}"), sets=sets, threshold=None, edges=(0, 64, 128, 256), patch=128)
assert rep["shape_ok"], f"STOP: TIFF {rep['shape']} {rep['dtype']} diverso dalla label"
assert "held" not in rep["sets"] or SETS != "train", "STOP: insieme held calcolato su un segmento sigillato"
train = rep["sets"]["train"]
gate_A = "superato"     # identita': commit, hash checkpoint, label, indici 2-18, exit 0, forma: tutti asseriti nelle celle precedenti
ok_orient = train["orientation"]["orientamento_ok"]
disjoint = rep["disjoint_check"]["n_px_held_and_train"] if rep["disjoint_check"] else None
gate_B = "superato" if (ok_orient is True and disjoint == 0) else ("non_valutabile" if ok_orient is None else "fallito")
rep.update({"gate_A": gate_A, "gate_B": gate_B, "seed": SEED, "segment_label": SEG})
json.dump(rep, open(f"{WORK}/out/metrics_{SEG}_seed{SEED}.json", "w"), indent=1, sort_keys=True)
print("AUROC train", train["auroc"], "| bestF1 train", train["best_f1"], "| orientamento", train["orientation"], "| held&train", disjoint)
if "held" in rep["sets"]:
    h = rep["sets"]["held"]; print("AUROC held", h["auroc"], "| bestF1 held", h["best_f1"], "| within patch", h["within_patch"])
print("GATE A:", gate_A, "| GATE B:", gate_B)
'''

CELL_9_COMPARE_PY = """# Passo 8 (seed43) — concordanza con il seed 42: Spearman sui pixel di training; sui pixel held-out solo se SETS li include
import json, numpy as np, tifffile, zarr, os
from scipy.stats import spearmanr
r43 = json.load(open(f"{WORK}/out/metrics_{SEG}_seed43.json"))
lab_dir = f"{HEAVY}/labels/{SEG}"
def plane(kind):
    a = zarr.open(f"{lab_dir}/{SEG}_{kind}.zarr", mode="r")["0"]; return np.asarray(a[a.shape[0] // 2]) > 0
train = plane("supervision_mask")
p42 = tifffile.imread(TIF42); p43 = tifffile.imread(f"{WORK}/out/{SEG}_seed43_step075000.tif")
cmp = {"spearman_train": float(spearmanr(p42[train], p43[train]).statistic),
       "delta_auroc_train_43_meno_42": r43["sets"]["train"]["auroc"] - r42["sets"]["train"]["auroc"],
       "sha256_tif_seed42": r42["sha256_pred"], "sha256_tif_seed43": r43["sha256_pred"]}
if "held" in r43["sets"] and "held" in r42["sets"]:
    held = plane("validation_mask")
    cmp["spearman_held"] = float(spearmanr(p42[held], p43[held]).statistic)
    cmp["delta_auroc_held_43_meno_42"] = r43["sets"]["held"]["auroc"] - r42["sets"]["held"]["auroc"]
print(json.dumps(cmp, indent=1)); json.dump(cmp, open(f"{WORK}/out/compare_seeds_{SEG}.json", "w"), indent=1)
"""

CELL_10_PERSIST_BASH = r"""%%bash
# Persistenza — hash di tutto cio' che viene conservato, stato finale
set -e
source /kaggle/working/e02/env.sh
cp /kaggle/working/e02/env.sh $WORK/logs/env.sh.txt
[ -f /kaggle/working/e02_guard.json ] && cp /kaggle/working/e02_guard.json $WORK/logs/guard.json
echo "end=$(date -u +%FT%TZ)" >> $WORK/logs/run_info.txt
disk_check "finale"
cd $WORK && find out logs -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > out/SHA256SUMS
cat out/SHA256SUMS
echo "persistito: $(du -sh $WORK | cut -f1)"
"""

CELL_11_VERDICT_PY = """# Verdetto del run: dopo la persistenza, un gate non superato rende il run 'error'
import json
res = json.load(open(f"{WORK}/out/metrics_{SEG}_seed{SEED}.json"))
print("gate_A =", res["gate_A"], "| gate_B =", res["gate_B"], "| AUROC train =", res["sets"]["train"]["auroc"])
assert res["gate_A"] == "superato" and res["gate_B"] == "superato", f"E02 run {MODE} NON superato: gate_A={res['gate_A']} gate_B={res['gate_B']} (metriche e log persistiti)"
"""


def nb_cell(kind: str, source: str) -> dict:
    cell = {"id": uuid.uuid5(uuid.NAMESPACE_URL, source).hex[:8], "cell_type": kind, "metadata": {}, "source": source}
    if kind == "code":
        cell.update({"execution_count": None, "outputs": []})
    return cell


def build(mode: str, ds: dict, user: str, run_id: str) -> tuple[dict, dict]:
    kind, seg, seed = parse_mode(mode)
    info = SEGMENTS[seg]
    lab = ds["labels"]["segments"][seg]
    for k in ("file_count", "byte_total", "tree_sha256", "tar_sha256"):
        assert lab.get(k) is not None, f"{mode}: costante label '{k}' ancora null in configs/e02/datasets.json (passo 2/4)"
    inp = ds["inputs"][seg]
    if kind == "infer":
        assert inp.get("tree_sha256"), f"{mode}: tree_sha256 dell'input poolato ancora null (eseguire prep-{info['short']} e publish-input)"
        if seed == 43:
            assert ds["seed42_outputs"][seg].get("sha256_tif"), f"{mode}: esito del seed42 non ancora pubblicato (publish-seed42-out)"
    gpu = kind == "infer"
    cells = [("markdown", CELL_INTRO_MD), ("code", CELL_CONST_PY)]
    if gpu:
        cells.append(("code", CELL_GUARD_INPUT_PY))
        if seed == 43:
            cells.append(("code", CELL_GUARD_SEED43_PY))
    cells += [("code", CELL_1_ENV_BASH), ("code", CELL_2_NET_PY), ("code", CELL_3_CHECKOUT_BASH)]
    if kind == "prep":
        cells += [("code", CELL_4P_INSTALL_PREP_PY), ("code", CELL_5A_LABEL_PY), ("code", CELL_6_PREP_BASH), ("code", CELL_6B_PREP_VERIFY_PY)]
    else:
        cells += [("code", CELL_4_INSTALL_PY), ("code", CELL_5_CHECKPOINTS_BASH), ("code", CELL_5A_LABEL_PY), ("code", CELL_6C_MODEL_CPU_PY),
                  ("code", CELL_7_INFER_BASH), ("code", CELL_7B_LOGCHECK_PY), ("code", CELL_8_METRICS_PY)]
        if seed == 43:
            cells.append(("code", CELL_9_COMPARE_PY))
    cells.append(("code", CELL_10_PERSIST_BASH))
    if gpu:
        cells.append(("code", CELL_11_VERDICT_PY))

    metrics_source = METRICS_SRC.read_text(encoding="utf-8")
    metrics_b64 = base64.b64encode(metrics_source.encode("utf-8")).decode("ascii")

    def sub(s: str) -> str:
        return (s.replace("__MODE__", mode).replace("__KIND__", kind).replace("__SEG__", seg).replace("__SHORT__", info["short"])
                 .replace("__SEED__", "None" if seed is None else str(seed)).replace("__SETS__", info["sets"])
                 .replace("__SRC_URL__", info["source"]).replace("__LABEL_SHAPE__", json.dumps(info["label_shape"]))
                 .replace("__TORCH__", TORCH_EXPECTED["gpu" if gpu else "cpu"])
                 .replace("__LABEL_TREE__", lab["tree_sha256"]).replace("__LABEL_FILES__", str(lab["file_count"])).replace("__LABEL_BYTES__", str(lab["byte_total"]))
                 .replace("__INPUT_TREE__", inp.get("tree_sha256") or "").replace("__FAMILY__", info["family"])
                 .replace("__METRICS_B64__", metrics_b64))

    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}},
        "cells": [nb_cell(k, sub(s)) for k, s in cells],
    }
    slug = f"papyruslab-{run_id}-{mode}"
    dataset_sources = [f"{user}/{ds['labels']['slug']}"]
    if gpu:
        dataset_sources.append(f"{user}/{inp['slug']}")
        if seed == 43:
            dataset_sources.append(f"{user}/{ds['seed42_outputs'][seg]['slug']}")
    meta = {
        "id": f"{user}/{slug}", "title": slug, "code_file": f"{slug}.ipynb", "language": "python", "kernel_type": "notebook",
        "is_private": True, "enable_gpu": gpu, "enable_internet": True, "dataset_sources": dataset_sources,
        "competition_sources": [], "kernel_sources": [], "model_sources": [],
    }
    if gpu:
        meta["machine_shape"] = "NvidiaTeslaT4"
    return notebook, meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=KAGGLE_USER)
    ap.add_argument("--run-id", default=RUN_ID)
    ap.add_argument("--only", nargs="*", default=None, help="generate only these modes (default: every mode whose constants are known)")
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
