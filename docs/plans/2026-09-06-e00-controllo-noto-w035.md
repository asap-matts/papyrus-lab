# E00 — controllo noto della catena di ink detection su w035 (Kaggle)

**Scritto da:** Claude Code (writer, su incarico di Matteo) · **Esecutore previsto:** Matteo sul notebook Kaggle, assistito da Claude · **Revisore del piano:** Codex, sola lettura (un giro, 6 settembre 2026, 13 finding integrati) · **Revisore dell'esito:** Codex, sola lettura
**Data:** 2026-09-06 · **Branch PapyrusLab:** `main` · **Base documentale:** `d430456` (commit che contiene procedura e dossier corretti) · **Branch villa:** `merge-ink-pipelines` @ `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e`

> Questo piano è congelato in un commit dedicato, successivo a `d430456`, con messaggio `docs: freeze E00 execution plan (R01)`.
> Verifica prima di iniziare, dalla cartella del repository:
> `git status --short` deve essere **vuoto** e `git log -1 --format=%s` deve restituire esattamente quel messaggio.
> Se una delle due condizioni non vale, **fermati**: stai leggendo un piano non congelato o uno stato diverso.

---

## 1. Obiettivo

Alla fine deve essere vero **uno** dei due esiti, entrambi legittimi:

- **E00 superato:** il modello ufficiale `ink_9um` (seed 42, step 75000), eseguito su Kaggle sul surface volume pubblicato di w035, produce un TIFF `5820 × 5240` la cui separazione fra pixel d'inchiostro e di sfondo, misurata con la label ufficiale, supera il criterio preregistrato al §5;
- **E00 non superato o interrotto, documentato:** log, output parziali, metriche e causa dell'arresto sono conservati e scritti nella scheda dell'esperimento.

Un esperimento che si ferma per una stop condition e lo documenta è **un'esecuzione completata**, non un lavoro lasciato a metà. Livello di evidenza raggiungibile in caso di successo: **L3** (replica operativa). Non si dimostra nulla sulla generalizzazione.

---

## 2. Contesto necessario

Tutti i dati tecnici sono nel [dossier E00](../08-dossier-input-e00.md), verificati su fonti primarie il 6 settembre 2026 e riassunti qui dove servono. La procedura che governa il lavoro è [docs/07](../07-procedura-operativa.md); la revisione che ha portato a questo piano è in [docs/reports/2026-09-06-revisione-procedura-e00.md](../reports/2026-09-06-revisione-procedura-e00.md).

Un **surface volume** è una pila di 28 immagini (slice) campionate attorno alla superficie del papiro. Il **modello** legge 17 slice alla volta e produce, per ogni pixel, un valore fra 0 e 255 che cresce con la plausibilità dell'inchiostro. La **label** è un'immagine della stessa forma, disegnata a mano dagli organizzatori, che dice dove l'inchiostro c'è davvero; la **supervision mask** dice in quali pixel la label è affidabile. w035 fa parte dei dati con cui il modello è stato addestrato: per questo un buon risultato prova che la catena è collegata, non che il modello funzioni su papiri nuovi.

Su Kaggle un **notebook** è una pagina di celle eseguibili su un computer remoto. Le celle che iniziano con `%%bash` eseguono comandi di shell Linux; le altre eseguono Python. Ogni cella `%%bash` è una shell nuova: le variabili non sopravvivono da una cella all'altra, per questo ogni cella di shell di questo piano inizia con `source /kaggle/working/e00/env.sh`.

### Decisioni già prese, e perché

- **Segmento w035, surface volume nativo a 9,362 µm** — è l'esempio lavorato del tutorial ufficiale, ha una label nativa con la stessa forma, pesa 814 MiB. Scartato w043 (quick start del model card): 1,3 GiB e nel training solo nella rappresentazione ridotta.
- **Codice: branch `merge-ink-pipelines` di villa, commit `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e`, pacchetto `koine_machines`** — è il percorso citato dal model card, è fermo dal 14 agosto 2026 (quindi congelabile) e richiede `torch==2.10.0`, che Kaggle ha. Esiste un secondo percorso ufficiale, `vesuvius.ink_detection` su `main` di villa, usato dal tutorial: **non usarlo qui**, richiede PyTorch ≥ 2.12 che Kaggle non ha. Non è "sbagliato": è una scelta registrata.
- **Installazione sul Python di sistema di Kaggle con `pip install --no-deps`, non `uv run`** — il comando ufficiale `uv run` costruisce un ambiente da 4,3 GiB (3,8 GiB di PyTorch e librerie CUDA duplicate) che su Kaggle si azzererebbe a ogni sessione. Ogni pacchetto aggiunto si installa con `--no-deps`, versione registrata nel manifest. È una deviazione dal comando ufficiale e va dichiarata nella scheda dell'esperimento. Mai installare `vesuvius[models]` (richiede `torch<2.9`, in conflitto).
- **`--no-compile`** — `torch.compile` è attivo per default nel codice (`reduce-overhead`); il tempo di compilazione su T4 è un rischio di budget inutile per un controllo noto.
- **Una sola GPU (`--gpus 0`) e `--batch-size 1`** — con due GPU il codice disattiva la compilazione e usa `DataParallel`: un confronto 1-vs-2 cambierebbe due variabili. Kaggle offre però soltanto l'acceleratore `GPU T4 x2` (o una P100 singola, architettura diversa da quella del preflight): **l'allocazione è doppia, l'uso è singolo**, e il secondo dispositivo deve restare inutilizzato — si verifica dal log (`Using CUDA device 0`) e da `nvidia-smi` dopo il run (memoria della GPU 1 pressoché nulla). Batch 1 è il minimo consigliato dal tutorial quando la memoria è incerta.
- **Checkpoint `step-075000` per entrambi i seed, scelti prima di vedere l'output** — le dimensioni dei file identificano il seed ma non lo step (tutti gli step di un seed pesano uguale): l'unico controllo è lo SHA-256. Non cambiare step dopo aver visto il risultato; l'immagine ufficiale di confronto fra seed è a step 20000 e non è un riferimento a parità.
- **Direzione `forward` (default)** — il tutorial dichiara che i render pubblicati hanno l'orientamento in profondità delle label di training. `--direction both` serve per superfici proprie.
- **Slice attese 6–22** — il codice sceglie le 17 slice centrali: `(28 // 2) − (17 // 2) = 6`. Il centro è 14, il piano su cui la label è annotata. Se il log mostra indici diversi, fermarsi.
- **Criterio di esito preregistrato (§5)** — deciso prima dell'esecuzione, calcolato da uno script; l'ispezione visiva non decide l'esito.
- **Il seed 43 si esegue solo se il seed 42 supera i gate A e B** — è informativo e costa GPU: non si spende budget per confrontare due seed se la catena non è collegata.
- **Tetto di spazio 10 GB (misurato su una radice unica), tetto GPU 30 minuti per tentativo con timeout automatico, nessuna spesa** — decisioni di Matteo del 6 settembre 2026.
- **Il socio non partecipa** — ripeterà a E01 dalle sole istruzioni salvate; se vedesse l'esito, la ripetizione non proverebbe che le istruzioni bastano.

### Vincoli

- Nessun commit, push o pubblicazione senza richiesta esplicita di Matteo. Nessun invito, nessuna submission.
- Niente dataset, checkpoint, TIFF o log voluminosi in Git: solo scheda, manifest e notebook ripulito.
- La GPU si accende **soltanto** al passo 7, quando tutti i passi precedenti sono verificati.
- Non modificare il codice di villa. Se serve una modifica, fermarsi (§7).
- Ogni comando eseguito e il suo output vanno conservati nel notebook e nei log.

---

## 3. Perimetro

### File da creare o modificare (nel repository)

| File | Cosa fare |
|---|---|
| `docs/reports/2026-09-XX-e00-r01.md` | Scheda dell'esperimento compilata da `docs/templates/esperimento.md`, con esito, metriche, tempi, deviazioni |
| `docs/reports/2026-09-XX-e00-r01-manifest.json` | Manifest: commit, revisioni, hash di checkpoint e output, comando esatto, versioni, tempi (file piccolo) |
| `notebooks/e00-r01.ipynb` | Copia ripulita del notebook Kaggle, **senza** output voluminosi |

Su Kaggle (fuori da Git): radice unica `/kaggle/working/e00/` con `villa/`, `checkpoints/`, `labels/`, `out/`, `logs/`, `tmp/`, `cache/`. Sul fisso (fuori da Git, cartella ignorata): `C:\dev\papyrus-lab\runs\E00-R01\`.

### File da NON toccare

| File | Perché |
|---|---|
| `docs/07-procedura-operativa.md`, `docs/08-dossier-input-e00.md` | Sono congelati per questo esperimento; una correzione crea un nuovo commit e un nuovo piano |
| Codice di villa | Qualsiasi modifica renderebbe il risultato non riproducibile dal commit dichiarato |
| `.gitignore` | Copre già `*.tif`, `*.pth`, `*.zarr/`, `data/`, `checkpoints/`, `runs/`, `outputs/` |

---

## 4. Passi

Notebook Kaggle nuovo e privato: `papyruslab-e00-r01`. Fino al passo 7 la sessione gira **senza acceleratore** (impostazione "None"). Se attivare l'acceleratore al passo 7 riavvia la sessione, i passi 1–6 vanno rieseguiti: sono a costo zero di quota e ogni cella è scritta per essere rieseguibile.

### Passo 0 — Base verificata (sul fisso, PowerShell)

```powershell
Set-Location C:\dev\papyrus-lab
git status --short            # atteso: nessun output
git log -1 --format=%s        # atteso: docs: freeze E00 execution plan (R01)
```
**Fatto quando:** entrambe le condizioni valgono. Annotare `git rev-parse --short HEAD` nel manifest come `commit_papyruslab`.

### Passo 1 — Radice unica, ambiente e rete (GPU spenta)

**Cosa:** creare la radice misurabile, dirottarvi cache e file temporanei, registrare l'ambiente, verificare la rete.
**Come:** attivare "Internet" nelle impostazioni del notebook (è un'impostazione separata dall'acceleratore; richiede la verifica telefonica, già fatta). Prima cella, `%%bash`:
```bash
mkdir -p /kaggle/working/e00/{tmp,cache/pip,cache/hf,checkpoints,labels,out,logs}
cat > /kaggle/working/e00/env.sh <<'EOF'
export E00=/kaggle/working/e00
export TMPDIR=$E00/tmp PIP_CACHE_DIR=$E00/cache/pip HF_HOME=$E00/cache/hf
export ZARR="https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/20260317000000-w035_2026031718/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr"
export LIMIT_BYTES=$((10*1024*1024*1024))
disk_check () { local used; used=$(du -sb "$E00" | cut -f1); echo "spazio_e00_byte=$used ($1)"; if [ "$used" -gt "$LIMIT_BYTES" ]; then echo "STOP: superati 10 GB"; exit 1; fi; }
EOF
source /kaggle/working/e00/env.sh && disk_check "inizio" && df -h /kaggle/working | tail -1
```
Seconda cella, Python:
```python
import sys, platform, json, urllib.request, torch
ZARR = "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/20260317000000-w035_2026031718/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr"
env = {"python": sys.version.split()[0], "platform": platform.platform(),
       "torch": torch.__version__, "cuda_available": torch.cuda.is_available()}
print(json.dumps(env, indent=1)); json.dump(env, open("/kaggle/working/e00/logs/env_before_install.json", "w"), indent=1)
for url in [ZARR + "/0/.zarray",
            "https://huggingface.co/api/models/scrollprize/ink_9um",
            "https://huggingface.co/api/buckets/scrollprize/datasets"]:
    with urllib.request.urlopen(url, timeout=30) as r: print(r.status, url[:70])
```
**Fatto quando:** `env.sh` esiste; `torch` è `2.10.0+cu128`; le tre richieste restituiscono `200`; `cuda_available` è `False` (GPU spenta, atteso).
**Fermarsi se** `torch` non è `2.10.0+cu128`: Kaggle ha cambiato immagine dopo il preflight del 5 settembre; il dossier va aggiornato prima di continuare.

### Passo 2 — Checkout parziale di villa al commit congelato

`%%bash`:
```bash
source /kaggle/working/e00/env.sh && cd $E00
git clone --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa.git
cd villa && git sparse-checkout init --cone && git sparse-checkout set ink-detection vesuvius
git checkout 3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e
git rev-parse HEAD && ls ink-detection/koine_machines/inference/infer.py vesuvius/pyproject.toml && disk_check "dopo checkout"
```
**Fatto quando:** `git rev-parse HEAD` stampa `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e`; i due file esistono; `disk_check` non ferma.

### Passo 3 — Installazione sul Python di sistema

**Cosa:** rendere importabile `koine_machines` senza toccare PyTorch. Tutto con `--no-deps`.
`%%bash`:
```bash
source /kaggle/working/e00/env.sh && cd $E00/villa
pip install --no-deps -e vesuvius 2>&1 | tail -1
pip install --no-deps -e ink-detection 2>&1 | tail -1
pip install --no-deps "zarr==2.18.7" "numcodecs==0.15.1" 2>&1 | tail -1   # il codice usa l'API Zarr v2; Kaggle può avere Zarr 3
python -c "import torch; print('torch', torch.__version__)"
python -c "import koine_machines.inference.infer" 2>&1 | tail -3
```
Se l'import fallisce con `ModuleNotFoundError: No module named 'X'`: `pip install --no-deps "X==<versione>"` dove `<versione>` è quella in `ink-detection/uv.lock` (cercare `name = "X"` e la riga `version` successiva); annotare pacchetto e versione; ripetere l'import. Unica eccezione ammessa: se l'import fallisce per `numpy` più recente di 2.2, è consentito `pip install --no-deps "numpy<=2.2"`, registrandolo.
Poi:
```bash
source /kaggle/working/e00/env.sh
python -m koine_machines.inference.infer --help | grep -E "no-compile|--gpus|--layer-start"
python -c "import torch; print('torch', torch.__version__)"
hf --version 2>/dev/null || pip install --no-deps huggingface_hub 2>&1 | tail -1
hf --version && hf buckets --help | head -3
pip list 2>/dev/null | grep -iE "^(torch|torchvision|zarr|numcodecs|numpy|tifffile|timm|scipy|fsspec|s3fs|aiohttp|huggingface.hub|monai|koine.machines|vesuvius) " | tee $E00/logs/pip_versions.txt
disk_check "dopo installazione"
```
**Fatto quando:** `--help` mostra le tre opzioni; `torch` è **ancora** `2.10.0+cu128`; `hf buckets --help` funziona (il comando `buckets` richiede un `huggingface_hub` recente); `pip_versions.txt` è salvato e sarà copiato nel manifest insieme all'elenco dei pacchetti aggiunti.
**Fermarsi se:** la versione di `torch` è cambiata; oppure i pacchetti aggiunti superano dieci (l'approccio `--no-deps` non è più "minimo" e la deviazione va ridiscussa); oppure `hf buckets` non esiste (registrare la versione e fermarsi: il metodo di acquisizione della label va rivisto).

### Passo 4 — Checkpoint e label, con verifica degli hash

`%%bash`:
```bash
source /kaggle/working/e00/env.sh && cd $E00 && disk_check "prima dei download"
hf download scrollprize/ink_9um hybrid_3d2d-seed42/step-075000.pth hybrid_3d2d-seed43/step-075000.pth \
   --revision 7109667e2607db1b90c37c8b09cb876ea7fe7bb1 --local-dir checkpoints/ink_9um | tail -1
sha256sum checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth checkpoints/ink_9um/hybrid_3d2d-seed43/step-075000.pth | tee logs/checkpoints_sha256.txt
stat -c "%s %n" checkpoints/ink_9um/hybrid_3d2d-seed4*/step-075000.pth
```
Atteso, **esattamente**:
```
e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab  …seed42/step-075000.pth   (138360039 byte)
2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f  …seed43/step-075000.pth   (138360231 byte)
```
Poi la label, prima in prova e poi davvero:
```bash
source /kaggle/working/e00/env.sh && cd $E00
PREFIX=hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w035
hf buckets sync $PREFIX labels/w035 --dry-run | tail -3
hf buckets sync $PREFIX labels/w035 | tail -2
echo "file=$(find labels/w035 -type f | wc -l) byte=$(find labels/w035 -type f -printf '%s\n' | awk '{s+=$1} END{print s}')" | tee logs/label_count.txt
cat labels/w035/w035_inklabels.zarr/0/.zarray | tr -d ' \n'; echo
disk_check "dopo i download"
```
**Fatto quando:** i due SHA-256 coincidono; `label_count.txt` riporta **esattamente** `file=5128 byte=737833` (somma dei soli file, misurata via API il 6 settembre 2026); `.zarray` mostra `"shape":[28,5820,5240]` e `"dtype":"|u1"`.
**Fermarsi se:** un hash non coincide (non usare quel file, non riprovare con un altro step); oppure conteggio o byte della label differiscono **anche di uno**: il dataset a monte è cambiato dopo la misura, e il riferimento va ricontrollato prima di misurare qualunque cosa contro di esso.

### Passo 5 — Prova minima di lettura remota (GPU spenta)

Python:
```python
import zarr, fsspec, numpy as np, json
ZARR = "https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/20260317000000-w035_2026031718/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr"
root = zarr.open(fsspec.get_mapper(ZARR), mode="r")
a = root["0"]; print(a.shape, a.dtype, a.chunks)
blk = a[6:23, 2816:2944, 2560:2688]; print(blk.shape, int(blk.min()), int(blk.max()))
lab = zarr.open("/kaggle/working/e00/labels/w035/w035_inklabels.zarr", mode="r")["0"]
msk = zarr.open("/kaggle/working/e00/labels/w035/w035_supervision_mask.zarr", mode="r")["0"]
counts = {"n_supervisionati": int((msk[14] > 0).sum()), "n_inchiostro": int(((lab[14] > 0) & (msk[14] > 0)).sum())}
print(lab.shape, msk.shape, counts); json.dump(counts, open("/kaggle/working/e00/logs/label_counts.json", "w"))
```
**Fatto quando:** `(28, 5820, 5240) uint8 (28, 128, 128)`; il blocco è `(17, 128, 128)` con `max > 0`; label e maschera hanno forma `(28, 5820, 5240)`; entrambi i conteggi sono `> 0` e salvati.

### Passo 6 — Prova di persistenza degli output (GPU spenta)

**Cosa:** verificare, prima di spendere GPU, che un file prodotto nel notebook sopravviva alla sessione e arrivi sul fisso.
**Come:** `%%bash`:
```bash
source /kaggle/working/e00/env.sh && echo "persistenza $(date -u +%FT%TZ)" > $E00/out/persistence_test.txt && sha256sum $E00/out/persistence_test.txt | tee $E00/logs/persistence_test.sha256
```
Poi in Kaggle: *File → Save Version → Quick Save*, con "Save output for this version" attivo. Aprire la versione salvata, sezione *Output*, scaricare `e00/out/persistence_test.txt` sul fisso in `C:\dev\papyrus-lab\runs\E00-R01\out\`. Sul fisso, PowerShell:
```powershell
Set-Location C:\dev\papyrus-lab\runs\E00-R01
(Get-FileHash out\persistence_test.txt -Algorithm SHA256).Hash.ToLower()
```
**Fatto quando:** l'hash sul fisso coincide con `persistence_test.sha256`. Da qui in avanti si sa che il percorso "output della versione → download" funziona.
**Fermarsi se** il file non compare fra gli output o l'hash differisce: il modo di conservare i risultati va risolto prima di produrli.

### Passo 7 — Inferenza seed 42, una T4, timeout automatico

**Cosa:** eseguire il comando congelato, con GPU accesa per la prima volta.
**Come:** attivare l'acceleratore `GPU T4 x2`; se la sessione si riavvia, rieseguire i passi 1–6 (verifiche incluse). Poi, `%%bash`:
```bash
source /kaggle/working/e00/env.sh && cd $E00 && disk_check "prima inferenza seed42"
nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv | tee logs/nvidia-smi-before-seed42.txt
python -c "import torch; print(torch.__version__, torch.cuda.device_count(), torch.cuda.get_device_name(0))" | tee -a logs/env_gpu.txt
set -o pipefail
START=$(date +%s)
timeout -s INT -k 30 1800 python -m koine_machines.inference.infer \
  "$ZARR" checkpoints/ink_9um/hybrid_3d2d-seed42/step-075000.pth out/w035_seed42_step075000.tif \
  --overlap 0.5 --blend-mode hann --no-compile --gpus 0 --batch-size 1 \
  2>&1 | tee logs/infer_seed42.log
EXIT=${PIPESTATUS[0]}; END=$(date +%s)
echo "exit_code=$EXIT durata_s=$((END-START)) causa=$([ $EXIT -eq 124 ] && echo timeout_1800s || echo normale)" | tee -a logs/infer_seed42.log
nvidia-smi --query-gpu=index,memory.used --format=csv | tee logs/nvidia-smi-after-seed42.txt
disk_check "dopo inferenza seed42"
```
`timeout … 1800` interrompe da solo il comando dopo 30 minuti (codice di uscita `124`); `PIPESTATUS[0]` è il codice di uscita di Python, non di `tee`.
**Fatto quando:** `exit_code=0`; il log contiene `Selected source layer indices=[6, 7, …, 22]`, una riga `Input level=0 shape=(depth=28, height=5820, width=5240) … in_chans=17`, `Using CUDA device 0` e `Wrote out/w035_seed42_step075000.tif`; `nvidia-smi-after` mostra memoria usata pressoché nulla sulla GPU `1`.
**Fermarsi se:** `exit_code` ≠ 0 (compreso `124`: budget superato); indici diversi da 6–22; `in_chans` ≠ 17; errore di memoria (registrare; il piano dovrà valutare `--num-workers` o altro, non improvvisare); memoria significativa sulla GPU 1 (il vincolo "una GPU" non è rispettato: registrare).

### Passo 8 — Misura del criterio per il seed 42 (CPU)

**Cosa:** calcolare il criterio del §5 con uno script autonomo, riutilizzabile per il seed 43. Python:
```python
import numpy as np, tifffile, zarr, json, hashlib
E00 = "/kaggle/working/e00"

def auroc(scores, pos, valid):
    s = scores[valid].astype(np.float64); y = pos[valid]
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0: return float("nan")
    order = np.argsort(s, kind="mergesort"); ranks = np.empty(len(s), dtype=np.float64)
    ss = s[order]; i = 0
    while i < len(ss):                      # rank medio per i valori uguali (uint8: molti pareggi)
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def measure(seed):
    tif = f"{E00}/out/w035_seed{seed}_step075000.tif"
    pred = tifffile.imread(tif)
    lab = zarr.open(f"{E00}/labels/w035/w035_inklabels.zarr", mode="r")["0"][14] > 0
    msk = zarr.open(f"{E00}/labels/w035/w035_supervision_mask.zarr", mode="r")["0"][14] > 0
    res = {"seed": seed, "shape": list(pred.shape), "dtype": str(pred.dtype),
           "shape_ok": pred.shape == (5820, 5240) and pred.dtype == np.uint8}
    if not res["shape_ok"]:
        json.dump(res, open(f"{E00}/out/metrics_seed{seed}.json", "w"), indent=1); return res
    variants = {"originale": (lab, msk), "rot180": (lab[::-1, ::-1], msk[::-1, ::-1]),
                "flipY": (lab[::-1, :], msk[::-1, :]), "flipX": (lab[:, ::-1], msk[:, ::-1])}
    for k, (l, m) in variants.items(): res[k] = auroc(pred, l, m)
    res["orientamento_ok"] = all(res["originale"] > res[k] for k in ["rot180", "flipY", "flipX"])
    res["n_supervisionati"] = int(msk.sum()); res["n_inchiostro"] = int((lab & msk).sum())
    res["mediana_inchiostro"] = float(np.median(pred[lab & msk])); res["mediana_sfondo"] = float(np.median(pred[msk & ~lab]))
    res["sha256_tif"] = hashlib.sha256(open(tif, "rb").read()).hexdigest()
    res["gate_B"] = "superato" if res["orientamento_ok"] and res["originale"] >= 0.90 else ("anomalo" if res["orientamento_ok"] and res["originale"] >= 0.75 else "fallito")
    tifffile.imwrite(f"{E00}/out/w035_seed{seed}_display.png", (np.clip((pred / 255 - 0.25) / 0.5, 0, 1) * 255).astype(np.uint8))  # sola visualizzazione
    json.dump(res, open(f"{E00}/out/metrics_seed{seed}.json", "w"), indent=1); return res

r42 = measure(42); print(json.dumps(r42, indent=1))
```
**Fatto quando:** `out/metrics_seed42.json` esiste con `shape_ok`, i quattro AUROC, `orientamento_ok`, `gate_B` e lo SHA-256 del TIFF.
**STOP prima del passo 9 se** `shape_ok` è `False`, oppure `orientamento_ok` è `False`, oppure `gate_B` è `fallito` o `anomalo`: **non eseguire il seed 43**. Spegnere l'acceleratore e passare direttamente ai passi 10–11 con esito "non superato" (il costo del seed 43 non è giustificato finché la catena non è dimostrata collegata).

### Passo 9 — Seed 43, stessi parametri (solo se il passo 8 dà `gate_B = superato`)

`%%bash`: identico al passo 7, sostituendo ovunque `seed42` con `seed43` (checkpoint, TIFF, log, file `nvidia-smi`). Stesso timeout di 30 minuti, stesse condizioni di arresto. Poi, Python:
```python
import json, numpy as np, tifffile, zarr
from scipy.stats import spearmanr
E00 = "/kaggle/working/e00"
r43 = measure(43)                                   # la funzione del passo 8; se la sessione è stata riavviata, rieseguire prima quella cella
r42 = json.load(open(f"{E00}/out/metrics_seed42.json")); r43 = json.load(open(f"{E00}/out/metrics_seed43.json"))
msk = zarr.open(f"{E00}/labels/w035/w035_supervision_mask.zarr", mode="r")["0"][14] > 0
p42 = tifffile.imread(f"{E00}/out/w035_seed42_step075000.tif")[msk]
p43 = tifffile.imread(f"{E00}/out/w035_seed43_step075000.tif")[msk]
cmp = {"spearman": float(spearmanr(p42, p43).statistic), "delta_auroc_43_meno_42": r43["originale"] - r42["originale"]}
print(cmp); json.dump(cmp, open(f"{E00}/out/compare_seeds.json", "w"), indent=1)
```
**Fatto quando:** `metrics_seed43.json` e `compare_seeds.json` esistono. Il seed 43 è informativo: il suo esito non cambia il verdetto del §5.

### Passo 10 — Conservazione e manifest

`%%bash`:
```bash
source /kaggle/working/e00/env.sh && cd $E00 && sha256sum out/* logs/* > out/SHA256SUMS && cat out/SHA256SUMS && disk_check "finale"
```
Poi *File → Save Version → Quick Save* con "Save output" attivo (come al passo 6). Scaricare l'intero output `e00/out/` e `e00/logs/` sul fisso in `C:\dev\papyrus-lab\runs\E00-R01\` (che conterrà `out\` e `logs\`). Spegnere la sessione e annotare la quota GPU residua mostrata da Kaggle. Sul fisso, PowerShell:
```powershell
Set-Location C:\dev\papyrus-lab\runs\E00-R01
$bad = 0
Get-Content out\SHA256SUMS | ForEach-Object {
  $h, $p = $_ -split '\s+', 2; $p = $p.Trim('*')
  if ((Get-FileHash $p -Algorithm SHA256).Hash.ToLower() -ne $h) { "DIFFERISCE: $p"; $bad++ }
}
"file verificati: $((Get-Content out\SHA256SUMS).Count); differenze: $bad"
```
Scrivere `docs/reports/2026-09-XX-e00-r01-manifest.json` con: `commit_papyruslab` (passo 0), commit villa, revisione HF, hash e dimensioni dei checkpoint, comando esatto, contenuto di `pip_versions.txt` ed elenco dei pacchetti aggiunti, hash e dimensioni di TIFF e metriche, `exit_code`, `durata_s` e causa per ogni seed, GPU e memoria, spazio massimo raggiunto (dai `disk_check`), quota GPU residua.
**Fatto quando:** `differenze: 0`; il manifest è scritto.

### Passo 11 — Scheda dell'esperimento

Compilare `docs/reports/2026-09-XX-e00-r01.md` da `docs/templates/esperimento.md`, con verdetto secondo il §5 (o arresto documentato con passo e causa), deviazioni (installazione `--no-deps`, pacchetti aggiunti, allocazione doppia T4 con uso singolo), tempi, esiti negativi e prove interrotte. Concludere con una decisione: promuovere (→ E01), ripetere (`E00-R02`, con piano corretto), modificare, sospendere. Copiare il notebook ripulito in `notebooks/e00-r01.ipynb` (menu *Edit → Clear all outputs* prima dell'esportazione). Consegnare a Codex per la revisione dell'esito in sola lettura. **Nessun commit** finché Matteo non lo chiede.

---

## 5. Criterio di esito, deciso prima della prova

Tutte le misure solo sui pixel con `supervision_mask = 1`.

**A. Identità** (tutti, altrimenti E00 fallito): commit villa `3ea17f5…`; revisione HF `7109667…`; SHA-256 dei checkpoint uguali al passo 4; label con `file=5128 byte=737833`; log con indici 6–22 e `in_chans=17`; `exit_code=0`; TIFF `(5820, 5240)` `uint8` (`shape_ok`).

**B. Collegamento** (sul seed 42, campo `gate_B`):
- `orientamento_ok` deve essere `True`: l'AUROC con la label non trasformata è strettamente la massima delle quattro. Se `False`, **fallito** qualunque sia il valore.
- AUROC `originale` **≥ 0,90 → superato**; fra 0,75 e 0,90 → *anomalo*, E00 non superato, indagare prima l'offset Z; **< 0,75 → fallito**.

**C. Stabilità** (informativo, solo se B è superato): Spearman e differenza di AUROC fra i seed, registrati senza soglia. La concordanza non è indipendenza.

**Formulazione ammessa se superato:** "la catena dati → modello → output è collegata correttamente su un segmento del training set, con orientamento verificato" (L3). Non ammesso: "il modello funziona", "trova inchiostro", "è validato".

---

## 6. Verifica finale

Si distinguono due cose: **esecuzione completata** (il piano è stato seguito fino alla fine o fino a uno stop documentato, e gli artefatti sono conservati) ed **E00 superato** (il criterio del §5 è soddisfatto). La prima è obbligatoria; la seconda è un risultato, non un requisito.

Esecuzione completata quando, nell'ordine, sul fisso in PowerShell:
```powershell
Set-Location C:\dev\papyrus-lab\runs\E00-R01
Test-Path out\SHA256SUMS                                         # atteso: True, e "differenze: 0" al passo 10
Test-Path out\metrics_seed42.json                                # atteso: True (anche in caso di stop dopo il passo 8; False è ammesso solo con stop documentato ai passi 1–7)
Set-Location C:\dev\papyrus-lab
git status --short                                               # atteso: solo docs/reports/…e00-r01*.md/.json e notebooks/e00-r01.ipynb
git ls-files | Select-String -Pattern '\.(tif|tiff|pth|zarr)$'   # atteso: nessun output
```
E00 superato quando, in più:
```powershell
Get-Content runs\E00-R01\out\metrics_seed42.json | ConvertFrom-Json | Select-Object gate_B, orientamento_ok, originale
# atteso per "superato": gate_B = superato, orientamento_ok = True, originale >= 0.90
```

---

## 7. Se il piano è sbagliato

1. **Fermati.** Non improvvisare (in particolare: non cambiare step del checkpoint, non passare a `main` di villa, non aggiungere `--direction both`, non alzare il batch "per vedere", non rilanciare dopo un timeout).
2. Annota cosa hai trovato e a quale passo.
3. Conserva log e output parziali (sono il risultato dell'esperimento: un arresto documentato vale più di un successo improvvisato). Esegui comunque il passo 10 per quanto esiste.
4. Spegni la GPU. Segnala. Il piano verrà corretto in un nuovo commit e un nuovo tentativo avrà ID `E00-R02`.

Arresto obbligatorio: `torch` cambia versione (passi 1, 3); un hash o il conteggio della label non coincide (passo 4); la persistenza non funziona (passo 6); `exit_code` ≠ 0 o timeout (passi 7, 9); indici di layer diversi da 6–22 o `in_chans` ≠ 17; `shape_ok` o `orientamento_ok` `False`, o `gate_B` diverso da `superato` (passo 8 → niente seed 43); `disk_check` oltre 10 GB in qualunque punto; serve una spesa o un'azione esterna.

---

## 8. Fuori perimetro

Anche se sembrano utili o ovvie, **non** fare in questo lavoro:

- provare altri step, altri segmenti, `--tta-mirror`, `--direction both`, finestre Z diverse, due GPU, `torch.compile`;
- misurare tempi comparativi fra Kaggle e fisso (la GTX 1060 richiede un preflight separato);
- installare ScrollScout, VC3D o `vesuvius[models]`;
- interpretare i valori del TIFF come probabilità, o dichiarare "lettere" viste nell'immagine;
- coinvolgere il socio o Francesco;
- commit o push.

Se ne emergono altre: **annotarle, non farle.**

---

## 9. Al termine

- [ ] Esecuzione completata: passi 0–11 eseguiti, **oppure** stop documentato al passo N con causa
- [ ] Verifica finale di "esecuzione completata" superata; esito E00 (superato / non superato / interrotto) scritto nella scheda
- [ ] Scheda esperimento e manifest scritti; output sul fisso in `runs/E00-R01/` con `differenze: 0`
- [ ] Revisione dell'esito consegnata a Codex (sola lettura)
- [ ] **Nessun commit né push** senza richiesta esplicita di Matteo
- [ ] Fuori perimetro emersi: annotati
