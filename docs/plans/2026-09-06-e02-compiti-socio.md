# E02 — compiti del socio: S1 audit indipendente delle maschere, S2 pooling indipendente (Mac, CPU)

**Scritto da:** Claude Code (writer, su incarico di Matteo) · **Esecutore previsto:** Codex del socio, sul Mac M3 Pro, cartella `~/dev/papyrus-lab` · **Revisore:** Claude Code in sola lettura, poi decisione di fusione di Matteo
**Data:** 2026-09-06 · **Branch:** `e02-socio` · **Commit di partenza:** quello con messaggio `feat: E02 steps 1-3 (inventory, split, labels, metrics with tests)` (lo script di avvio lo verifica)
**Piano madre:** [E02 — costruire il metro](2026-09-06-e02-costruire-il-metro.md), §9

> Verifica prima di iniziare: `git branch --show-current` deve stampare `e02-socio`, `git status --short` deve essere vuoto e `git log -1 --format=%s` deve restituire esattamente il messaggio sopra. Altrimenti **fermati** e chiedi a Matteo.

---

## 1. Obiettivo

Alla fine devono esistere sul branch `e02-socio`, e solo lì, due rapporti scritti **senza aver visto i numeri di Matteo**:

- **S1:** per ciascuno dei tre segmenti con maschera di validazione ufficiale, i numeri di geometria delle maschere (pixel held-out, regioni, distanza dal training più vicino) prodotti dallo script del repository, confrontati con la tabella pubblicata da R02.
- **S2:** l'impronta (SHA-256 dell'albero di file) dell'input poolato di `pherc0814-46527` prodotto sul Mac con lo script ufficiale di villa al commit congelato, con forma e attributi verificati.

Se un passo non si può eseguire, un rapporto che dice dove e perché è un risultato valido.

---

## 2. Contesto necessario

Nel dataset ufficiale `ink_9um` ogni segmento ha una **label** (dove c'è inchiostro), una **supervision mask** (i pixel usati per addestrare il modello) e, in tre casi soltanto, una **validation mask**: pixel annotati che gli organizzatori hanno tenuto fuori dal training ("held-out"). Il piano E02 costruisce il metro su quei pixel. Un modello che ha imparato a memoria una lettera riconosce anche la metà accanto: per questo conta **quanto i pixel held-out sono vicini a quelli di training**. La misura è la distanza euclidea, in pixel, dal pixel di training più vicino; una **patch** di training è di 128 px, quindi "entro una patch" significa distanza < 128 px, "entro due" < 256 px.

R02 (`khj1222/vesuvius-challenge`, docs/17, commit `13920ba`, licenza MIT) ha pubblicato questi numeri (livello di evidenza L1: risultato esterno). S1 li **replica** con il nostro script (L3): se coincidono, il metro poggia su un fatto verificato da due operatori su due macchine.

| Segmento | Regioni annotate | Held-out (px) | Quota held-out | Regioni miste | < 128 px | < 256 px | Distanza mediana |
|---|---:|---:|---:|---:|---:|---:|---:|
| `pherc0139-w016` | 3 | 175.222 | 29,5 % | 2 di 3 | 58,6 % | 99,1 % | 108 |
| `pherc0814-46527` | 1 | 161.051 | 27,3 % | 1 di 1 | 45,0 % | 87,8 % | 142 |
| `pherc1667-w029` | 8 | 382.353 | 24,0 % | 1 di 8 | 23,2 % | 45,4 % | 283 |

Per S2: i segmenti allineati esistono a 2,4 µm; il modello vuole ~9,6 µm. Lo script ufficiale `prepare_9um_isotropic_input.py` legge il livello 2 della piramide (9,596 µm), prende 84 piani centrali dei 109 e li media a 4 a 4 → 21 slice. Matteo esegue lo stesso pooling su Kaggle; S2 lo esegue sul Mac. Se le due impronte coincidono, l'input del metro è identico fra piattaforme.

### Decisioni già prese, e perché

- **Ambiente Python: `.venv` da `requirements-cpu.txt`, non `uv run`** — lo script di pooling usa solo `numpy`, `zarr`, `numcodecs` (più `fsspec`/`aiohttp` per leggere l'URL); il venv ha le stesse versioni fissate del portatile di Matteo e di Kaggle (zarr 2.18.7, numcodecs 0.15.1), quindi il confronto delle impronte non dipende dalle librerie. `uv run` costruirebbe 4,3 GiB di ambiente con PyTorch, inutile qui.
- **Checkout parziale di villa al commit `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e`** — lo stesso di E00, E01 e del piano E02: lo script deve essere byte per byte quello congelato.
- **4 workers nel pooling** — R02 ha osservato disconnessioni da S3 con 24 connessioni.
- **Non leggere `main`, `docs/reports/2026-09-*e02*`, `runs/` di Matteo né i suoi numeri prima di consegnare** — S1 e S2 valgono perché sono indipendenti. Il commit di partenza non contiene numeri di E02.
- **Nessun Kaggle** — S1 e S2 sono lavoro CPU locale; lo script delle label prepara anche una cartella per Kaggle, ma **non va pubblicata** dal socio.

### Vincoli

- Solo il branch `e02-socio`; nessun commit su `main`, nessuna pull request, nessuna fusione.
- Nessun file `.zarr/`, `.tif`, `.tar` in Git (sono già ignorati): controllare `git status` prima del commit.
- Spazio: circa 1 GB per S2 (input letto da rete ≈0,8 GB, output ≈0,15 GB); S1 ≈5 MB ma **circa 25.000 file piccoli**: il download può richiedere 30–60 minuti per i limiti di Hugging Face alle richieste anonime (lo script attende e riprova da solo).
- Percorsi relativi alla radice del repository nei comandi; usare `.venv/bin/python` per ogni comando Python.

---

## 3. Perimetro

### File che Codex crea (solo sul branch `e02-socio`)

| File | Cosa contiene |
|---|---|
| `docs/reports/2026-09-XX-e02-socio-s1-audit-maschere.md` | Tabella per segmento (nostri numeri accanto a quelli di R02), differenze, ambiguità e ostacoli, tempi |
| `docs/reports/2026-09-XX-e02-socio-s1-<segmento>.json` (×3) | Output di `scripts/e02_metrics.py --geometry` (file piccoli) |
| `docs/reports/2026-09-XX-e02-socio-s2-pooling-46527.md` | Comando eseguito, attributi del risultato, forma, `tree_sha256`, tempi, ostacoli |

`XX` = giorno di esecuzione. Fuori da Git: `data/labels/…`, `runs/E02-SOCIO/…`, `runs/villa/`.

### File da NON toccare

| File | Perché |
|---|---|
| Tutto il resto del repository | Un solo writer per cartella: Matteo e Claude scrivono su `main`; una modifica qui creerebbe conflitti e invaliderebbe l'indipendenza |
| `scripts/*.py` | Se uno script non funziona sul Mac, non correggerlo: fermati e registra l'ostacolo nel rapporto. È un risultato |

---

## 4. Passi

### Passo 0 — Avvio (persona: il socio)

```bash
gh auth status || gh auth login
bash ~/dev/papyrus-lab/scripts/e02_bootstrap_mac.sh     # repository, branch e02-socio, Python >= 3.11, .venv
```
**Fatto quando:** lo script stampa "Tutto pronto".

### Passo 1 — Verifica dello stato (Codex)

```bash
cd ~/dev/papyrus-lab && git branch --show-current && git status --short && git log -1 --format=%s
.venv/bin/python -m pytest tests/test_e02_metrics.py -q
```
**Fatto quando:** branch `e02-socio`, stato vuoto, messaggio atteso, test tutti superati. Registrare `sw_vers`, `.venv/bin/python --version`, `git --version` per il rapporto.

### Passo 2 — Scaricare le tre label (S1, ~30–60 minuti, rete)

```bash
.venv/bin/python scripts/build_label_dataset.py --run-id e02-socio --user micheleghisa \
  --segments aligned-scrollprizeorg-21slices/pherc0814-46527 aligned-scrollprizeorg-21slices/pherc0139-w016 aligned-scrollprizeorg-21slices/pherc1667-w029
```
Lo script si ferma da solo se i conteggi differiscono da quelli misurati il 6 settembre 2026 (1.386 / 118.869 byte; 9.414 / 746.565; 13.959 / 1.108.191). Copia le label in `data/labels/aligned-scrollprizeorg-21slices/<seg>/`. **Non** eseguire `kaggle datasets create`.
**Fatto quando:** l'ultima riga stampa `tree_sha256` e `tar_sha256` per i tre segmenti; annotarli nel rapporto S1.

### Passo 3 — Geometria delle maschere (S1)

Per ciascun segmento:
```bash
.venv/bin/python scripts/e02_metrics.py --geometry --patch 128 --edges 0 64 128 256 \
  --labels data/labels/aligned-scrollprizeorg-21slices/<seg> --out docs/reports/2026-09-XX-e02-socio-s1-<seg>.json
```
Dal JSON (chiave `geometry`): `annotated_regions`, `n_px_held`, `held_share_of_annotation`, `regions_mixing_held_and_training`, `within_patch`, `within_two_patches`, `distance_stats.median`, `n_px_held_and_train` (atteso **0** per tutti e tre). Compilare la tabella del rapporto S1 con i nostri valori accanto a quelli di R02 (§2) e la differenza.
**Fatto quando:** tre JSON e la tabella; ogni differenza rispetto a R02 è scritta, anche se piccola. Non "aggiustare" nulla per farli coincidere.

### Passo 4 — Pooling indipendente di `pherc0814-46527` (S2, ~0,8 GB di rete)

```bash
mkdir -p runs/villa && cd runs/villa
git clone -q --filter=blob:none --no-checkout https://github.com/ScrollPrize/villa.git && cd villa
git sparse-checkout init --cone >/dev/null && git sparse-checkout set ink-detection >/dev/null
git checkout -q 3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e && git rev-parse HEAD      # atteso: 3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e
cd ~/dev/papyrus-lab
shasum -a 256 runs/villa/villa/ink-detection/scripts/prepare_9um_isotropic_input.py     # annotare nel rapporto
mkdir -p runs/E02-SOCIO/input
SRC="https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0814/segments/20260226000000-46527_2um_try2/surface-volumes/2.399um-0.22m-78keV-volume-20260309142202.zarr"
time .venv/bin/python runs/villa/villa/ink-detection/scripts/prepare_9um_isotropic_input.py "$SRC" runs/E02-SOCIO/input/pherc0814-46527_pooled.zarr --level 2 --workers 4
.venv/bin/python - <<'EOF'
import json, zarr
g = zarr.open("runs/E02-SOCIO/input/pherc0814-46527_pooled.zarr", mode="r"); a = g["0"]
print("shape", a.shape, "dtype", a.dtype, "chunks", a.chunks)
print(json.dumps(dict(g.attrs), indent=1))
assert tuple(a.shape) == (21, 2130, 3455), "STOP: forma diversa dalla label (21, 2130, 3455)"
assert g.attrs["source_z_slice"] == [13, 97] and g.attrs["source_level"] == "2", "STOP: attributi inattesi"
EOF
.venv/bin/python scripts/tree_sha256.py runs/E02-SOCIO/input/pherc0814-46527_pooled.zarr
```
**Fatto quando:** il commit di villa coincide; la forma è `(21, 2130, 3455)`; gli attributi sono quelli attesi; `tree_sha256=…` è annotato nel rapporto S2 con il tempo di esecuzione e la dimensione della cartella (`du -sh`). Se la rete si interrompe (`ServerDisconnectedError`, 5xx), cancellare la cartella `.partial` e rilanciare **una** volta; se fallisce ancora, registrare e fermarsi.

### Passo 5 — Rapporti, commit, push del branch

Scrivere i due rapporti Markdown (struttura: cosa è stato fatto, tabella dei numeri, differenze, ambiguità e ostacoli, tempi, versioni). Poi:
```bash
git add docs/reports/2026-09-XX-e02-socio-*
git status --short            # atteso: solo i file di §3
git commit -m "docs: E02 partner tasks S1 (mask audit) and S2 (independent pooling of pherc0814-46527)"
git push -u origin e02-socio
```
Consegnare a Matteo un riepilogo: numeri principali di S1 (tre righe), `tree_sha256` di S2, ostacoli incontrati.

---

## 5. Criterio di esito, deciso prima della prova

- **S1 concorde** se, per ogni segmento: `n_px_held` uguale a R02 al pixel; `annotated_regions` e `regions_mixing_held_and_training` uguali; quote `< 128` e `< 256` entro ±0,5 punti percentuali; mediana entro ±2 px. Altrimenti *discorde*: si riporta la differenza senza interpretarla; deciderà Matteo con Claude (le cause possibili: connettività delle componenti, confine degli strati, versione del dataset).
- **S2 valido** se forma e attributi coincidono e l'impronta è riportata. Il confronto con l'impronta di Kaggle lo fa Matteo: il socio non la conosce.
- `n_px_held_and_train` diverso da 0 su un segmento è un **P0** da segnalare subito: significherebbe che held-out e training si sovrappongono.

---

## 6. Verifica finale

```bash
git branch --show-current                                  # e02-socio
git log origin/e02-socio -1 --format=%s                    # il commit del passo 5
ls docs/reports/ | grep e02-socio                          # 5 file: 2 .md + 3 .json
git ls-files | grep -E '\.(zarr|tif|tar)$'                 # nessun output
```

---

## 7. Se il piano è sbagliato

1. Fermati; non improvvisare (non modificare script, non cambiare versioni, non usare altri strumenti di pooling).
2. Annota cosa hai trovato e a quale passo.
3. Committa e pusha ciò che è coerente (anche solo un rapporto con l'ostacolo).
4. Segnala a Matteo.

---

## 8. Fuori perimetro

Non fare, anche se sembra utile: run Kaggle o GPU; inferenze; pubblicare dataset; leggere `main`, i rapporti o le cartelle `runs/` di Matteo; scaricare altri segmenti; modificare `.gitignore` o gli script; commit su `main`; pull request.

---

## 9. Al termine

- [ ] S1: tre JSON e rapporto con la tabella e le differenze
- [ ] S2: rapporto con impronta, forma, attributi, tempi
- [ ] Ambiguità e ostacoli registrati, anche se risolti
- [ ] Branch `e02-socio` pushato; riepilogo consegnato a Matteo
