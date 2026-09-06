#!/usr/bin/env python3
"""Generate the three Kaggle notebooks for experiment E00 (plan 2026-09-06).

One source of truth for the cells; three run modes:
  preflight  - steps 1-6 of the plan, no accelerator (network, install, hashes, label, remote read)
  seed42     - steps 1-8, one T4 (inference seed 42 + metrics)
  seed43     - steps 1-9, one T4 (inference seed 43 + comparison with the seed42 run output)

Every stop condition of the plan is an assertion or an `exit 1`: a failed check aborts the run
and the log says where. Heavy files live under /tmp/e00 (not persisted); outputs and logs under
/kaggle/working/e00 (persisted as kernel output).

Usage: python scripts/build_e00_notebooks.py   -> writes kaggle/e00-r01-<mode>/
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

KAGGLE_USER = "matteopontesilli"
RUN_ID = "e00-r01"
PLAN = "docs/plans/2026-09-06-e00-controllo-noto-w035.md"

ZARR_URL = (
    "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/"
    "20260317000000-w035_2026031718/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr"
)
VILLA_COMMIT = "3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e"
HF_REVISION = "7109667e2607db1b90c37c8b09cb876ea7fe7bb1"
SHA_SEED42 = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
SHA_SEED43 = "2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f"
LABEL_FILES = 5128
LABEL_BYTES = 737833
# Private Kaggle dataset built by scripts/build_w035_label_dataset.py from the bucket API listing
# (2026-09-06). Mounted read-only in every run; the tar hash is re-checked before extraction.
LABEL_DATASET = f"{KAGGLE_USER}/papyruslab-w035-labels"
LABEL_TAR_SHA256 = "0ba09a5353d39e0ed67e74f57f1555632503daf9f898bf322e48d5001125e8f0"
# Content hash of the label tree (sorted 'relpath\nsha256(file)\n' lines), printed by
# scripts/build_w035_label_dataset.py. Re-checked in every run, both on the dataset path and on the
# direct-download fallback: sizes alone would accept a corrupted or substituted label (Codex F1).
LABEL_TREE_SHA256 = "09037f1d0ccc008c5f619b2a4f41a554d1abf50739fd02469a9a2fb799731f27"
# Kaggle ships two images: CPU-only sessions have torch 2.10.0+cpu, GPU sessions 2.10.0+cu128
# (measured on the preflight run of 2026-09-06). The expected build depends on the run mode.
TORCH_EXPECTED = {"preflight": "2.10.0+cpu", "seed42": "2.10.0+cu128", "seed43": "2.10.0+cu128"}

# --------------------------------------------------------------------------------------------
# Cells. Bash cells start with %%bash; every bash cell re-sources env.sh (each cell is a new shell).
# Placeholders __MODE__ and __SEED__ are substituted per notebook.
# --------------------------------------------------------------------------------------------

CELL_INTRO_MD = f"""# PapyrusLab E00 — run `__MODE__`

Notebook generato da `scripts/build_e00_notebooks.py` (non modificare a mano). Piano congelato: `{PLAN}`.
Ogni controllo di arresto del piano è un'asserzione: se fallisce, il run si ferma e il log dice dove.

- Output persistiti: `/kaggle/working/e00/out` e `/kaggle/working/e00/logs`
- File pesanti (codice, checkpoint, cache), non persistiti: `/tmp/e00`
"""

CELL_CONST_PY = """MODE = "__MODE__"
SEED = __SEED__          # None nel preflight
WORK = "/kaggle/working/e00"
HEAVY = "/tmp/e00"
ZARR = "%(zarr)s"
TORCH_EXPECTED = "__TORCH__"   # immagine CPU di Kaggle: 2.10.0+cpu; immagine GPU: 2.10.0+cu128
print("MODE", MODE, "SEED", SEED, "torch atteso", TORCH_EXPECTED)
""" % {"zarr": ZARR_URL}

CELL_1_ENV_BASH = r"""%%bash
# Passo 1 — radice misurabile, cache e temporanei dirottati, guardia dei 10 GB
set -e
mkdir -p /kaggle/working/e00/out /kaggle/working/e00/logs /tmp/e00/tmp /tmp/e00/cache/pip /tmp/e00/cache/hf /tmp/e00/checkpoints /tmp/e00/labels
cat > /kaggle/working/e00/env.sh <<'EOF'
export WORK=/kaggle/working/e00
export HEAVY=/tmp/e00
export TMPDIR=$HEAVY/tmp PIP_CACHE_DIR=$HEAVY/cache/pip HF_HOME=$HEAVY/cache/hf
export ZARR="__ZARR__"
export LIMIT_BYTES=$((10*1024*1024*1024))
disk_check () {
  local used
  used=$(( $(du -sb "$WORK" | cut -f1) + $(du -sb "$HEAVY" | cut -f1) ))
  echo "spazio_byte=$used ($1)" | tee -a "$WORK/logs/disk_check.log"
  if [ "$used" -gt "$LIMIT_BYTES" ]; then echo "STOP: superati 10 GB ($1)" | tee -a "$WORK/logs/disk_check.log"; exit 1; fi
}
EOF
source /kaggle/working/e00/env.sh
echo "MODE=__MODE__ SEED=__SEED__ start=$(date -u +%FT%TZ)" > $WORK/logs/run_info.txt
disk_check "inizio"
df -h /kaggle/working /tmp | tail -2
""".replace("__ZARR__", ZARR_URL)

CELL_2_NET_PY = """# Passo 1 (segue) — versioni dell'ambiente e rete verso le tre sorgenti
import sys, platform, json, urllib.request, torch
env = {"python": sys.version.split()[0], "platform": platform.platform(),
       "torch": torch.__version__, "cuda_available": torch.cuda.is_available(),
       "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0}
print(json.dumps(env, indent=1))
json.dump(env, open(f"{WORK}/logs/env_before_install.json", "w"), indent=1)
assert env["torch"] == TORCH_EXPECTED, f"STOP: PyTorch inatteso {env['torch']} (atteso {TORCH_EXPECTED}): Kaggle ha cambiato immagine, aggiornare il dossier"
if MODE == "preflight":
    assert not env["cuda_available"], "STOP: il preflight deve girare senza acceleratore"
else:
    assert env["cuda_available"], "STOP: run GPU senza CUDA disponibile"
for url in [ZARR + "/0/.zarray",
            "https://huggingface.co/api/models/scrollprize/ink_9um",
            "https://huggingface.co/api/buckets/scrollprize/datasets"]:
    with urllib.request.urlopen(url, timeout=30) as r:
        print(r.status, url[:80]); assert r.status == 200, f"STOP: rete non raggiunge {url}"
"""

CELL_3_CHECKOUT_BASH = r"""%%bash
# Passo 2 — checkout parziale di villa al commit congelato
set -e
source /kaggle/working/e00/env.sh
cd $HEAVY
[ -d villa/.git ] || git clone -q --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa.git
cd villa
git sparse-checkout init --cone >/dev/null
git sparse-checkout set ink-detection vesuvius >/dev/null
git checkout -q __VILLA_COMMIT__
HEAD=$(git rev-parse HEAD); echo "villa HEAD=$HEAD" | tee $WORK/logs/villa_commit.txt
[ "$HEAD" = "__VILLA_COMMIT__" ] || { echo "STOP: commit villa diverso"; exit 1; }
ls -l ink-detection/koine_machines/inference/infer.py vesuvius/pyproject.toml ink-detection/uv.lock
disk_check "dopo checkout"
""".replace("__VILLA_COMMIT__", VILLA_COMMIT)

CELL_4_INSTALL_PY = r'''# Passo 3 — installazione sul Python di sistema, tutto con --no-deps, PyTorch intatto
import subprocess, re, json, sys
VILLA = f"{HEAVY}/villa"
PY = sys.executable

def sh(args):                      # argomenti come lista: nessuna interpretazione della shell
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

ALIAS = {"cv2": "opencv-contrib-python-headless", "PIL": "pillow", "yaml": "pyyaml",
         "cc3d": "connected-components-3d", "skimage": "scikit-image", "sklearn": "scikit-learn"}
added, numpy_downgraded = [], False
for attempt in range(12):
    r = sh([PY, "-c", "import koine_machines.inference.infer"])
    if r.returncode == 0:
        break
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
        added.append({"module": mod, "dist": dist, "version": ver}); print("aggiunto", dist, ver)
    elif "numpy" in err.lower() and not numpy_downgraded:
        # unica eccezione ammessa dal piano: NumPy piu' recente di 2.2
        r2 = pip("numpy<=2.2"); assert r2.returncode == 0, r2.stderr[-3000:]
        numpy_downgraded = True; added.append({"module": "numpy", "dist": "numpy", "version": "<=2.2 (eccezione piano)"})
    else:
        raise AssertionError("STOP: import fallito per motivo diverso da modulo mancante:\n" + err[-3000:])
assert r.returncode == 0, "STOP: import ancora fallito dopo i tentativi ammessi"
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
assert sh(["hf", "buckets", "--help"]).returncode == 0, "STOP: 'hf buckets' non disponibile: huggingface_hub troppo vecchio"
pipl = [l for l in sh([PY, "-m", "pip", "list"]).stdout.splitlines()
        if re.match(r"(?i)^(torch|torchvision|zarr|numcodecs|numpy|tifffile|timm|scipy|fsspec|s3fs|aiohttp|huggingface.hub|monai|koine.machines|vesuvius|albumentations|einops|opencv) ", l)]
open(f"{WORK}/logs/pip_versions.txt", "w").write("\n".join(pipl) + "\n")
info = {"torch_before": torch_before, "torch_after": torch_after, "added_packages": added, "hf_version": hf.stdout.strip()}
json.dump(info, open(f"{WORK}/logs/install.json", "w"), indent=1)
print(json.dumps(info, indent=1)); print("\n".join(pipl))
'''

CELL_5_DOWNLOADS_BASH = r"""%%bash
# Passo 4 — checkpoint e label, con verifica esatta di hash e conteggi
set -e
source /kaggle/working/e00/env.sh
cd $HEAVY
disk_check "prima dei download"
hf download scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth hybrid_3d2d-seed43/step-075000.pth \
   --revision __HF_REVISION__ --local-dir checkpoints/ink_9um > /dev/null
sha256sum checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth checkpoints/ink_9um/hybrid_3d2d-seed43/step-075000.pth | tee $WORK/logs/checkpoints_sha256.txt
stat -c "%s %n" checkpoints/ink_9um/hybrid_3d2d-seed4*/step-075000.pth | tee -a $WORK/logs/checkpoints_sha256.txt
grep -q "^__SHA42__  checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth" $WORK/logs/checkpoints_sha256.txt || { echo "STOP: SHA-256 seed42 diverso"; exit 1; }
grep -q "^__SHA43__  checkpoints/ink_9um/hybrid_3d2d-seed43/step-075000.pth" $WORK/logs/checkpoints_sha256.txt || { echo "STOP: SHA-256 seed43 diverso"; exit 1; }
disk_check "dopo i checkpoint"
""".replace("__HF_REVISION__", HF_REVISION).replace("__SHA42__", SHA_SEED42).replace("__SHA43__", SHA_SEED43)

# Deviazione registrata (preflight v2 del 6 settembre 2026): `hf buckets sync` sui 5.128 file della label
# non ha prodotto progresso per ~28 minuti ed e' stato cancellato dal timeout di piattaforma. Si usa il
# download diretto e parallelo dei file elencati dall'API del bucket, con verifica di conteggio e byte.
CELL_5A_LABEL_DATASET_PY = r'''# Passo 4 (segue) — label w035 dal dataset Kaggle privato, verificata file per file contro manifest.json
# Kaggle estrae automaticamente w035_labels.tar al caricamento: il dataset espone w035_labels/w035/... e manifest.json
# (elenco dell'API del bucket con percorsi e dimensioni). La verifica e' su percorsi, dimensioni e conteggi.
import hashlib, os, shutil, json, glob
EXPECTED = (__LABEL_FILES__, __LABEL_BYTES__)
LABEL_TREE_SHA256 = "__LABEL_TREE_SHA256__"
PREFIX = "ink_9um/labels/native9-scrollprizeorg-21slices/w035/"
LABEL_READY = False

def tree_sha256(root):
    """Stessa definizione di scripts/build_w035_label_dataset.py: sha256 su righe ordinate 'relpath\\nsha256(file)\\n'."""
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
    assert (n, b) == EXPECTED, f"STOP: label con {n} file / {b} byte, attesi {EXPECTED}"
    tsha, _ = tree_sha256(dest)
    assert tsha == LABEL_TREE_SHA256, f"STOP: contenuto della label diverso da quello congelato (tree sha256 {tsha})"
    open(f"{WORK}/logs/label_count.txt", "w").write(f"file={n} byte={b} tree_sha256={tsha} source={source_desc}\n")
    za = open(f"{dest}/w035_inklabels.zarr/0/.zarray").read(); open(f"{WORK}/logs/label_zarray.json", "w").write(za)
    print(f"label verificata: file={n} byte={b} tree_sha256={tsha} ({source_desc})"); print(za)
inputs = sorted(os.listdir("/kaggle/input")) if os.path.isdir("/kaggle/input") else []
manifests = glob.glob("/kaggle/input/*/manifest.json") + glob.glob("/kaggle/input/*/*/manifest.json")
roots = glob.glob("/kaggle/input/**/w035/w035_inklabels.zarr/0/.zarray", recursive=True)
print("montato in /kaggle/input:", inputs, "| manifest:", manifests, "| label:", roots)
if manifests and roots:
    manifest = json.load(open(manifests[0]))
    src = os.path.dirname(os.path.dirname(os.path.dirname(roots[0])))       # .../w035
    files = manifest["files"]
    assert (len(files), sum(f["size"] for f in files)) == EXPECTED, "STOP: manifest del dataset diverso dalla misura del 6 settembre 2026"
    missing = [f["path"] for f in files
               if not (os.path.isfile(os.path.join(src, f["path"][len(PREFIX):])) and os.path.getsize(os.path.join(src, f["path"][len(PREFIX):])) == f["size"])]
    assert not missing, f"STOP: {len(missing)} file della label mancanti o di dimensione diversa, p.es. {missing[:3]}"
    dest = f"{HEAVY}/labels/w035"
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    msha = hashlib.sha256(open(manifests[0], "rb").read()).hexdigest()
    check_label_tree(dest, f"kaggle_dataset manifest_sha256={msha}")
    LABEL_READY = True
else:
    print("dataset della label non montato: si passa al download diretto (cella successiva)")
'''.replace("__LABEL_FILES__", str(LABEL_FILES)).replace("__LABEL_BYTES__", str(LABEL_BYTES)).replace("__LABEL_TREE_SHA256__", LABEL_TREE_SHA256)

CELL_5B_LABEL_PY = r'''# Passo 4 (ripiego) — label w035: elenco dall'API del bucket e download diretto in parallelo (~8 min)
import json, os, re, time, urllib.request, concurrent.futures as cf
API = "https://huggingface.co/api/buckets/scrollprize/datasets/tree/ink_9um/labels/native9-scrollprizeorg-21slices/w035"
RESOLVE = "https://huggingface.co/buckets/scrollprize/datasets/resolve/"
PREFIX = "ink_9um/labels/native9-scrollprizeorg-21slices/w035/"
DEST = f"{HEAVY}/labels/w035"
EXPECTED = (__LABEL_FILES__, __LABEL_BYTES__)     # misurati via API il 6 settembre 2026

def list_label_files():
    files, url = [], API
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": "papyruslab-e00"})
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
            req = urllib.request.Request(RESOLVE + path, headers={"User-Agent": "papyruslab-e00"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) == size:
                with open(out, "wb") as fh:
                    fh.write(data)
                return size
            last = f"dimensione {len(data)} != {size}"
        except Exception as ex:      # HTTP 429 (rate limit) e 5xx: attesa crescente e nuovo tentativo
            last = ex
        time.sleep(min(60, 5 * 2 ** attempt))
    raise RuntimeError(f"STOP: download fallito per {path}: {last}")

def fallback_download():
    files = list_label_files(); total = sum(s for _, s in files)
    print("elencati", len(files), "file,", total, "byte")
    assert (len(files), total) == EXPECTED, f"STOP: label diversa dalla misura del 6 settembre 2026: {len(files)} file, {total} byte (attesi {EXPECTED})"
    t0 = time.time()
    # Hugging Face limita le richieste anonime parallele (HTTP 429 osservato dal run Kaggle del 6 settembre 2026): pochi thread
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        got = sum(ex.map(fetch, files))
    print(f"scaricati {got} byte in {time.time() - t0:.0f} s")
    check_label_tree(DEST, "direct_download")     # stesso controllo di contenuto del percorso dataset

if LABEL_READY:
    print("label gia' pronta dal dataset Kaggle: ripiego non necessario")
else:
    fallback_download()
'''.replace("__LABEL_FILES__", str(LABEL_FILES)).replace("__LABEL_BYTES__", str(LABEL_BYTES))

CELL_5C_DISK_BASH = r"""%%bash
source /kaggle/working/e00/env.sh
disk_check "dopo i download"
"""

CELL_6_PROBE_PY = """# Passo 5 — prova minima di lettura remota e della label (senza GPU)
import zarr, fsspec, numpy as np, json
root = zarr.open(fsspec.get_mapper(ZARR), mode="r")
a = root["0"]; print(a.shape, a.dtype, a.chunks)
assert tuple(a.shape) == (28, 5820, 5240) and str(a.dtype) == "uint8", "STOP: surface volume con forma o tipo inattesi"
blk = a[6:23, 2816:2944, 2560:2688]; print("blocco", blk.shape, int(blk.min()), int(blk.max()))
assert blk.shape == (17, 128, 128) and int(blk.max()) > 0, "STOP: lettura remota del blocco non valida"
lab = zarr.open(f"{HEAVY}/labels/w035/w035_inklabels.zarr", mode="r")["0"]
msk = zarr.open(f"{HEAVY}/labels/w035/w035_supervision_mask.zarr", mode="r")["0"]
assert tuple(lab.shape) == (28, 5820, 5240) and tuple(msk.shape) == (28, 5820, 5240), "STOP: label o maschera con forma inattesa"
counts = {"n_supervisionati": int((msk[14] > 0).sum()), "n_inchiostro": int(((lab[14] > 0) & (msk[14] > 0)).sum())}
print(counts); json.dump(counts, open(f"{WORK}/logs/label_counts.json", "w"), indent=1)
assert counts["n_supervisionati"] > 0 and counts["n_inchiostro"] > 0, "STOP: label o maschera vuote al piano Z=14"
"""

CELL_7_INFER_BASH = r"""%%bash
# Passo 7 — inferenza seed __SEED__ su una sola T4 (CUDA_VISIBLE_DEVICES=0), timeout automatico di 30 minuti
source /kaggle/working/e00/env.sh
cd $HEAVY
disk_check "prima inferenza seed__SEED__"
nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv > $WORK/logs/nvidia-smi-before-seed__SEED__.txt \
  || { echo "STOP: nvidia-smi non disponibile: nessuna GPU assegnata"; exit 1; }
cat $WORK/logs/nvidia-smi-before-seed__SEED__.txt
export CUDA_VISIBLE_DEVICES=0            # la seconda T4 dell'allocazione resta invisibile al processo
python -c "import torch; assert torch.cuda.is_available(); print(torch.__version__, 'visibili', torch.cuda.device_count(), torch.cuda.get_device_name(0))" | tee -a $WORK/logs/env_gpu.txt \
  || { echo "STOP: PyTorch non vede la GPU"; exit 1; }
# campionamento della memoria di ENTRAMBE le GPU fisiche durante l'inferenza (nvidia-smi ignora CUDA_VISIBLE_DEVICES)
nvidia-smi --query-gpu=timestamp,index,memory.used --format=csv,noheader,nounits -l 5 > $WORK/logs/gpu_samples_seed__SEED__.csv &
SAMPLER=$!
set -o pipefail
START=$(date +%s)
timeout -s INT -k 30 1800 python -m koine_machines.inference.infer \
  "$ZARR" checkpoints/ink_9um/hybrid_3d2d-seed__SEED__/step-075000.pth $WORK/out/w035_seed__SEED___step075000.tif \
  --overlap 0.5 --blend-mode hann --no-compile --gpus 0 --batch-size 1 \
  2>&1 | tee $WORK/logs/infer_seed__SEED__.log
EXIT=${PIPESTATUS[0]}; END=$(date +%s)
kill $SAMPLER 2>/dev/null; wait $SAMPLER 2>/dev/null
CAUSA=normale; [ "$EXIT" -eq 124 ] && CAUSA=timeout_1800s
echo "exit_code=$EXIT durata_s=$((END-START)) causa=$CAUSA" | tee -a $WORK/logs/infer_seed__SEED__.log
nvidia-smi --query-gpu=index,memory.used --format=csv > $WORK/logs/nvidia-smi-after-seed__SEED__.txt; cat $WORK/logs/nvidia-smi-after-seed__SEED__.txt
disk_check "dopo inferenza seed__SEED__"
"""

CELL_7B_LOGCHECK_PY = """# Passo 7 (segue) — controlli sul log: codice di uscita, slice, canali, GPU singola (misurata durante il run)
import re, csv
log = open(f"{WORK}/logs/infer_seed{SEED}.log", encoding="utf-8", errors="replace").read()
m = re.search(r"exit_code=(\\d+) durata_s=(\\d+) causa=(\\S+)", log); assert m, "STOP: riga finale di esito assente nel log"
exit_code, durata, causa = int(m.group(1)), int(m.group(2)), m.group(3)
print("exit_code", exit_code, "durata_s", durata, "causa", causa)
assert exit_code == 0, f"STOP: inferenza terminata con exit_code={exit_code} ({causa})"
# stringhe verificate in infer.py di villa @ 3ea17f5 (LOGGER.info: 'Selected source layer indices=%s', 'Input level=... in_chans=%d', 'Using CUDA device %d for inference.', 'Wrote %s')
expected = "Selected source layer indices=" + str(list(range(6, 23)))
assert expected in log, "STOP: indici di layer diversi da 6-22"
assert "in_chans=17" in log, "STOP: in_chans diverso da 17"
assert "Using CUDA device 0 for inference." in log, "STOP: il log non conferma l'uso del solo device 0"
assert re.search(r"Wrote .*w035_seed%d_step075000.tif" % SEED, log), "STOP: il log non conferma la scrittura del TIFF"
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
"""

CELL_8_MEASURE_PY = r'''# Passo 8 — criterio preregistrato: AUROC sui pixel supervisionati e test di orientamento
import numpy as np, tifffile, zarr, json, hashlib

def auroc(scores, pos, valid):
    s = scores[valid].astype(np.float64); y = pos[valid]
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort"); ranks = np.empty(len(s), dtype=np.float64)
    ss = s[order]; i = 0
    while i < len(ss):                      # rank medio per i valori uguali (uint8: molti pareggi)
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def measure(seed, out_dir=None):
    out_dir = out_dir or f"{WORK}/out"
    tif = f"{out_dir}/w035_seed{seed}_step075000.tif"
    pred = tifffile.imread(tif)
    lab = zarr.open(f"{HEAVY}/labels/w035/w035_inklabels.zarr", mode="r")["0"][14] > 0
    msk = zarr.open(f"{HEAVY}/labels/w035/w035_supervision_mask.zarr", mode="r")["0"][14] > 0
    res = {"seed": seed, "shape": list(pred.shape), "dtype": str(pred.dtype),
           "shape_ok": bool(pred.shape == (5820, 5240) and pred.dtype == np.uint8),
           "sha256_tif": hashlib.sha256(open(tif, "rb").read()).hexdigest()}
    if res["shape_ok"]:
        variants = {"originale": (lab, msk), "rot180": (lab[::-1, ::-1], msk[::-1, ::-1]),
                    "flipY": (lab[::-1, :], msk[::-1, :]), "flipX": (lab[:, ::-1], msk[:, ::-1])}
        for k, (l, m) in variants.items():
            res[k] = auroc(pred, l, m)
        res["orientamento_ok"] = bool(all(res["originale"] > res[k] for k in ["rot180", "flipY", "flipX"]))
        res["n_supervisionati"] = int(msk.sum()); res["n_inchiostro"] = int((lab & msk).sum())
        res["mediana_inchiostro"] = float(np.median(pred[lab & msk])); res["mediana_sfondo"] = float(np.median(pred[msk & ~lab]))
        res["gate_B"] = ("superato" if res["orientamento_ok"] and res["originale"] >= 0.90
                         else "anomalo" if res["orientamento_ok"] and res["originale"] >= 0.75 else "fallito")
        disp = (np.clip((pred.astype(np.float32) / 255 - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8)
        tifffile.imwrite(f"{WORK}/out/w035_seed{seed}_display.png", disp)   # sola visualizzazione, non per misure
    else:
        res["gate_B"] = "fallito"
    json.dump(res, open(f"{WORK}/out/metrics_seed{seed}.json", "w"), indent=1)
    return res

res = measure(SEED)
print(json.dumps(res, indent=1))
assert res["shape_ok"], "STOP: TIFF con forma o tipo inattesi"
print("GATE B:", res["gate_B"], "| orientamento_ok:", res["orientamento_ok"])
if res["gate_B"] != "superato":
    print("E00 NON SUPERATO su questo run: non eseguire il seed 43. Conservare tutto e compilare la scheda.")
'''

CELL_9_COMPARE_PY = """# Passo 9 — confronto con il run seed42, montato come sorgente in /kaggle/input
import json, numpy as np, tifffile, zarr, os
from scipy.stats import spearmanr
SRC = "/kaggle/input/papyruslab-e00-r01-seed42/e00/out"
assert os.path.exists(f"{SRC}/metrics_seed42.json"), "STOP: output del run seed42 non montato come kernel_source"
r42 = json.load(open(f"{SRC}/metrics_seed42.json")); r43 = json.load(open(f"{WORK}/out/metrics_seed43.json"))
assert r42["gate_B"] == "superato", "STOP: il run seed42 non ha superato il gate B; il seed 43 non andava eseguito"
msk = zarr.open(f"{HEAVY}/labels/w035/w035_supervision_mask.zarr", mode="r")["0"][14] > 0
p42 = tifffile.imread(f"{SRC}/w035_seed42_step075000.tif")[msk]
p43 = tifffile.imread(f"{WORK}/out/w035_seed43_step075000.tif")[msk]
cmp = {"spearman": float(spearmanr(p42, p43).statistic), "delta_auroc_43_meno_42": r43["originale"] - r42["originale"],
       "sha256_tif_seed42": r42["sha256_tif"], "sha256_tif_seed43": r43["sha256_tif"]}
print(json.dumps(cmp, indent=1)); json.dump(cmp, open(f"{WORK}/out/compare_seeds.json", "w"), indent=1)
"""

CELL_0_GUARD_SEED43_PY = """# Guardia iniziale del run seed43: il seed 42 deve avere superato il gate B, PRIMA di spendere GPU
import json, os
SRC = "/kaggle/input/papyruslab-e00-r01-seed42/e00/out"
assert os.path.exists(f"{SRC}/metrics_seed42.json"), "STOP: output del run seed42 non montato come kernel_source"
r42 = json.load(open(f"{SRC}/metrics_seed42.json"))
assert r42.get("gate_B") == "superato", f"STOP: il run seed42 non ha superato il gate B ({r42.get('gate_B')}): il seed 43 non va eseguito"
print("guardia seed43: seed42 gate_B =", r42["gate_B"], "| AUROC", r42.get("originale"))
"""

CELL_11_VERDICT_PY = """# Verdetto del run: dopo aver persistito metriche e hash, un gate B non superato rende il run 'error'
import json
res = json.load(open(f"{WORK}/out/metrics_seed{SEED}.json"))
print("gate_B =", res["gate_B"], "| orientamento_ok =", res.get("orientamento_ok"), "| AUROC originale =", res.get("originale"))
if MODE == "seed42":
    assert res["gate_B"] == "superato", f"E00 NON SUPERATO su seed42: gate_B={res['gate_B']} (metriche e log sono comunque persistiti)"
else:
    print("seed43 e' informativo: nessun verdetto bloccante")
"""

CELL_10_PERSIST_BASH = r"""%%bash
# Passo 10 — hash di tutto ciò che viene persistito, stato finale
set -e
source /kaggle/working/e00/env.sh
cp /kaggle/working/e00/env.sh $WORK/logs/env.sh.txt
echo "end=$(date -u +%FT%TZ)" >> $WORK/logs/run_info.txt
disk_check "finale"
cd $WORK && find out logs -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > out/SHA256SUMS
cat out/SHA256SUMS
echo "persistito: $(du -sh $WORK | cut -f1)"
"""


def nb_cell(kind: str, source: str) -> dict:
    cell = {"id": uuid.uuid5(uuid.NAMESPACE_URL, source).hex[:8], "cell_type": kind,
            "metadata": {}, "source": source}
    if kind == "code":
        cell.update({"execution_count": None, "outputs": []})
    return cell


def build(mode: str) -> tuple[dict, dict]:
    seed = {"preflight": None, "seed42": 42, "seed43": 43}[mode]
    gpu = mode != "preflight"
    cells = [
        ("markdown", CELL_INTRO_MD), ("code", CELL_CONST_PY), ("code", CELL_1_ENV_BASH), ("code", CELL_2_NET_PY),
        ("code", CELL_3_CHECKOUT_BASH), ("code", CELL_4_INSTALL_PY), ("code", CELL_5_DOWNLOADS_BASH),
        ("code", CELL_5A_LABEL_DATASET_PY), ("code", CELL_5B_LABEL_PY), ("code", CELL_5C_DISK_BASH), ("code", CELL_6_PROBE_PY),
    ]
    if mode == "seed43":
        cells.insert(2, ("code", CELL_0_GUARD_SEED43_PY))     # prima di qualunque setup o download
    if gpu:
        cells += [("code", CELL_7_INFER_BASH), ("code", CELL_7B_LOGCHECK_PY), ("code", CELL_8_MEASURE_PY)]
    if mode == "seed43":
        cells.append(("code", CELL_9_COMPARE_PY))
    cells.append(("code", CELL_10_PERSIST_BASH))
    if gpu:
        cells.append(("code", CELL_11_VERDICT_PY))            # dopo la persistenza: un gate fallito rende il run 'error'
    sub = lambda s: (s.replace("__MODE__", mode).replace("__SEED__", "None" if seed is None else str(seed))
                     .replace("__TORCH__", TORCH_EXPECTED[mode]))
    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                     "language_info": {"name": "python"}},
        "cells": [nb_cell(k, sub(s)) for k, s in cells],
    }
    slug = f"papyruslab-{RUN_ID}-{mode}"
    meta = {
        "id": f"{KAGGLE_USER}/{slug}", "title": slug, "code_file": f"{slug}.ipynb",
        "language": "python", "kernel_type": "notebook", "is_private": True,
        "enable_gpu": gpu, "enable_internet": True,
        "dataset_sources": [LABEL_DATASET], "competition_sources": [],
        "kernel_sources": [f"{KAGGLE_USER}/papyruslab-{RUN_ID}-seed42"] if mode == "seed43" else [],
        "model_sources": [],
    }
    if gpu:
        meta["machine_shape"] = "NvidiaTeslaT4"
    return notebook, meta


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for mode in ["preflight", "seed42", "seed43"]:
        notebook, meta = build(mode)
        folder = root / "kaggle" / f"{RUN_ID}-{mode}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / meta["code_file"]).write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (folder / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(f"{folder.relative_to(root)}: {len(notebook['cells'])} celle, gpu={meta['enable_gpu']}")


if __name__ == "__main__":
    main()
