# E02 — costruire il metro: inventario, candidati, divisione, baseline congelata, metriche

**Scritto da:** Claude Code (writer, su incarico di Matteo) · **Esecutore previsto:** Claude Code dal portatile di Matteo (lettura, metadati, CPU) e via API Kaggle (inferenze), con i "vai" di Matteo · **Revisore del piano:** Codex, sola lettura, tramite plugin `codex@openai-codex`, modello `gpt-6-astra`, effort `high` · **Revisore dell'esito:** Codex, sola lettura · **Socio:** compiti puntuali su branch `e02-socio` (§9), da confermare
**Data:** 2026-09-06 · **Branch PapyrusLab:** `main` · **Commit di partenza:** `6130881` · **Branch villa:** `merge-ink-pipelines` @ `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e` (invariato da E00)

> Verifica prima di iniziare, dalla cartella del repository: `git status --short` deve essere vuoto e `git log -1 --format=%s` deve restituire esattamente `docs: freeze E02 plan (R01)`. Se una delle due condizioni non vale, **fermati**: stai leggendo un piano non congelato o uno stato diverso.

---

## 1. Obiettivo

Alla fine deve essere vero **uno** dei due esiti:

- **E02 superato (metro congelato):** esiste nel repository un manifest revisionato che fissa (a) l'inventario completo del training set di `ink_9um` con i nomi mappati sui segmenti pubblici, (b) un insieme di pixel con label ufficiale **mai usati per addestrare i checkpoint rilasciati**, divisi per segmento in *sviluppo* e *verifica*, (c) la baseline congelata (la procedura di E00), (d) metriche per segmento definite e calcolate da uno script deterministico, (e) la prima lettura del metro: i numeri della baseline sui segmenti di sviluppo e sui pixel di training di tutti e tre, con i limiti dichiarati; i pixel held-out del segmento di verifica restano sigillati fino a E05. Gate G3 proposto a Matteo.
- **E02 non superato o interrotto, documentato:** log, output parziali, misure e causa dell'arresto conservati e scritti nella scheda.

Livello di evidenza raggiungibile: **L3** (replica operativa) per i numeri della baseline, con un confronto informativo contro i numeri pubblicati da R02 (L1). E02 **non** decide dove investire, non confronta varianti, non addestra: la scelta si prende dopo, con questi numeri, secondo [docs/decisions/2026-09-06-dove-investire.md](../decisions/2026-09-06-dove-investire.md).

---

## 2. Contesto necessario

La procedura che governa il lavoro è [docs/07](../07-procedura-operativa.md). La baseline è la procedura di E00 ([piano](2026-09-06-e00-controllo-noto-w035.md), [scheda](../reports/2026-09-06-e00-r01.md)), riprodotta bit per bit dal socio in E01. I termini *surface volume*, *label*, *supervision mask*, *checkpoint* sono definiti nel piano E00 §2 e in [docs/01](../01-capire-il-processo.md).

Un **held-out** (in italiano: "tenuto fuori") è un insieme di pixel annotati che chi ha addestrato il modello ha escluso di proposito dal training, per potervi misurare il modello. Una **validation mask** è il file che dice quali pixel sono held-out. Il **pooling** è la riduzione di un volume a risoluzione più bassa facendo la media di blocchi di pixel vicini. Una **rappresentazione** è un modo di presentare lo stesso segmento fisico al modello: `ink_9um` ne usa due (volume 2,4 µm ridotto a ~9,6 µm; volume nativo 9,362 µm).

### 2.1 Intake: fonti verificate il 6 settembre 2026

| Fonte | Revisione | Cosa dice (livello) | Rischio principale |
|---|---|---|---|
| README del dataset `ink_9um` (bucket HF `scrollprize/datasets`, `ink_9um/README.md`, 10.739 byte) | letto il 6 settembre 2026 | Tabella ufficiale label → segmento pubblico e volume sorgente, per tutte e 29 le rappresentazioni; le tre `_validation_mask` sono "the online-validation cases the released checkpoints report metrics on" (L0) | Il README avverte che i nomi `pherc0139-wNNN` non seguono la numerazione pubblica |
| Model card `scrollprize/ink_9um` | `7109667e2607db1b90c37c8b09cb876ea7fe7bb1` | Training su 24 segmenti allineati (9 PHerc0139, 6 PHerc1667, 8 PHercParis4, 1 PHerc0814) + 5 nativi PHerc0139; sensibilità all'offset Z; nessun numero di prestazione (L0) | — |
| villa `ink-detection/configs/aligned21_fixed_scroll_prior.json` | `3ea17f5` | Contratto delle 29 rappresentazioni con `physical_segment_key`: "duplicate public/native representations share one physical-segment budget" (L2) | Le chiavi fisiche usano i nomi delle label, non i pubblici: vedi trappola 3 in §2.2 |
| villa `ink-detection/scripts/prepare_9um_isotropic_input.py` | `3ea17f5` | Pooling ufficiale: livello 2 del volume 2,4 µm, 84 piani Z centrali, media 4× → 21 slice (L2) | Lettura remota di interi chunk `[109,128,128]` non compressi |
| villa `ink-detection/koine_machines/inference/infer.py` | `3ea17f5` | Opzioni `--mask-path`, `--layer-start/--layer-end`, `--tta-mirror`, `--no-compile`; finestra di default `depth//2 − 17//2` (L2) | Per 21 slice la finestra è 2–18, centro 10 |
| Bucket `ink_9um/labels` (API, paginata) | 381 pagine, 380.992 file, 33.362.621 byte | 29 cartelle, 3 con `_validation_mask` (pherc0139-w016, pherc0814-46527, pherc1667-w029) (L0, misurato) | Le label allineate sono a un solo livello (`0`); le native a sei |
| Metadati S3 dei tre volumi 2,4 µm dei segmenti con maschera | `.zattrs`, `0/.zarray`, `2/.zarray` | 109 slice, chunk `[109,128,128]`, livello 2 a 9,596 µm con forma uguale alla label (L0, misurato) | Volume letto dal livello 2: 5,6 / 0,8 / 8,3 GB (limite superiore) |
| R02 `khj1222/vesuvius-challenge` docs/09, 13, 14, 15, 17 e `tools/eval_validation.py`, `tools/audit_holdout_masks.py` (MIT) | `13920bad47e2bee4f2a21e748ae3f338093d64a4` | Scorecard dei 14 checkpoint sui tre held-out (best-F1 0,74–0,77 contro 0,98+ sui pixel di training); audit delle maschere: tagliano regioni annotate, su w016 nessun sottoinsieme senza adiacenza; w029 l'unico con separazione reale; villa #1638 chiuso da pmh47: "validation mask is disjoint from the supervision mask", i numeri vanno letti come intra-segmento (L1) | Numeri di un altro autore, su Windows/RTX 5090, batch size della scorecard non dichiarato: replicabili ma non nostri |
| villa #1547 (aperta, 2026-08-20) | letta il 6 settembre 2026 | I segmenti pubblici PHerc0139 w045 e w046 tracciano lo stesso foglio (81,5 % di vertici identici) (L1) | w046 **non** è un candidato "estraneo": è fisicamente w045, che è nel training |
| villa #1231 (aperta) | letta il 6 settembre 2026 | I segmenti pubblicati non hanno `_validation_mask`; risposta ufficiale assente (L1) | — |
| Open-data S3 `PHerc0139/segments/` | 38 cartelle il 6 settembre 2026 | 29 segmenti pubblici di PHerc0139 non sono nel training, tutti con volume nativo 9,362 µm, **nessuno con label** (L0) | Senza label non entrano nel metro |
| Kaggle (ricerca web, L1, da verificare nel preflight) | — | sessione CPU ≤ 12 h, GPU ≤ 9 h, 30 h/settimana di GPU per account, `/kaggle/working` ≤ 20 GB | Le quote cambiano; i mount dei dataset differiscono fra sessioni CPU e GPU (misurato in E00) |

La ricerca si ferma qui: l'informazione basta a scegliere la prova più piccola. Fonti **non** consultate e rinviate: il vecchio server dati (Scroll 1, label a 7,91 µm, accesso registrato), la pagina *Open Problems* per la scelta dello stadio (serve dopo E02, non ora).

### 2.2 Inventario del training set di `ink_9um` (L0 + L2, verificato il 6 settembre 2026)

29 rappresentazioni, **24 segmenti fisici**, 4 rotoli. Le cinque rappresentazioni native riguardano segmenti che sono nel training anche nella forma allineata: nessun segmento fisico "in più".

| Segmento pubblico (S3) | Rotolo | Label allineata (`aligned-scrollprizeorg-21slices`) | Label nativa (`native9-…`) | `_validation_mask` | Note |
|---|---|---|---|---|---|
| `20250108000004-w029_2025010827` | PHerc0139 | `pherc0139-w016` | — | **sì** | trappola 1: il nome dice w016, il pubblico è w029 |
| `20250108000005-w030_2025010818` | PHerc0139 | `pherc0139-w017` | — | no | |
| `20260115000000-w044_2026011522` | PHerc0139 | `pherc0139-w028` | `w044` | no | trappola 2 e 3: doppia rappresentazione; nel contratto le chiavi fisiche sono `0139:w028` e `0139:w044`, quindi **non** condividono il budget dichiarato |
| `20260126000000-w045_2026012619` | PHerc0139 | `pherc0139-w029` | — | no | villa #1547: stesso foglio del pubblico w046 |
| `20260317000000-w035_2026031718` | PHerc0139 | `pherc0139-w035` | `w035` | no | doppia; controllo E00/E01 |
| `20260302000000-w039_2026030210` | PHerc0139 | `pherc0139-w039` | `w039` | no | doppia |
| `20250831000000-w040_2025083102` | PHerc0139 | `pherc0139-w040` | `w040` | no | doppia |
| `20260108000000-w041_2026010816` | PHerc0139 | `pherc0139-w041` | `w041` | no | doppia |
| `20260112000000-w043_2026011217` | PHerc0139 | `pherc0139-w043` | — | no | quick start del model card |
| `20260226000000-46527_2um_try2` | PHerc0814 | `pherc0814-46527` | — | **sì** | una sola regione annotata |
| `20240304141531-w013_…_flatboi` | PHerc1667 | `pherc1667-w013` | — | no | |
| `20240304144031-w018_…_flatboi` | PHerc1667 | `pherc1667-w018` | — | no | |
| `20240304161941-w023_…_flatboi` | PHerc1667 | `pherc1667-w023` | — | no | |
| `20251208130119-w028_…_flatboi` | PHerc1667 | `pherc1667-w028` | — | no | |
| `20251212185248-w029_…_flatboi` | PHerc1667 | `pherc1667-w029` | — | **sì** | otto regioni annotate |
| `20251223230000-w031_…_flatboi` | PHerc1667 | `pherc1667-w031` | — | no | |
| `20231016151002` | PHercParis4 | `phercparis4-w00` | — | no | |
| `20230702185753` | PHercParis4 | `phercparis4-w01` | — | no | |
| `20231031143852` | PHercParis4 | `phercparis4-w02` | — | no | |
| `20231106155351` | PHercParis4 | `phercparis4-w03` | — | no | |
| `20231012184424` | PHercParis4 | `phercparis4-w05` | — | no | |
| `20231210121321` | PHercParis4 | `phercparis4-w06` | — | no | |
| `20231007101619` | PHercParis4 | `phercparis4-w07` | — | no | |
| `20230929220926` | PHercParis4 | `phercparis4-w09` | — | no | |

Le tre trappole, da scrivere nel manifest: (1) nomi non allineati alla numerazione pubblica (w016→w029, w017→w030, w028→w044, w029→w045); (2) stesso segmento fisico in due rappresentazioni (w035, w039, w040, w041, w044); (3) il contratto di villa condivide il budget per quattro coppie ma **non** per `pherc0139-w028`/`w044`, che è la stessa area fisica: è una nostra lettura del codice (L2), da segnalare a monte solo se Matteo lo decide, non un fatto che cambia il metro.

### 2.3 Dove stanno i pixel mai visti dal training

Per i checkpoint rilasciati, gli **unici** pixel con label ufficiale e mai usati come supervisione sono quelli delle tre `_validation_mask`: il dataset li dichiara disgiunti dalla `supervision_mask` (confermato da pmh47 in villa #1638) e sono gli "online-validation cases" del training. Tutto il resto è training, oppure è senza label. Non esiste, con fonte anonima e a ~9 µm, un segmento con label fuori dai quattro rotoli del training: **il metro di E02 è intra-segmento e intra-rotolo**, e va chiamato così. Il cross-scroll (fra rotoli diversi) richiederebbe un nuovo training (come i LOSO di R02) o label esterne: fuori perimetro.

Limite noto e misurato da altri (L1, da rimisurare da noi): le tre maschere tagliano regioni annotate; su w016 il 99,1 % dei pixel held-out sta a meno di due patch dal pixel di training più vicino e il resto non ha inchiostro (la patch di training è di **128 px sulla scala delle label**, `patch_size: [17, 128, 128]` nel config di villa; "entro una patch" significa distanza euclidea **< 128 px**, "entro due" **< 256 px**, confine escluso, stessa regola di R02); su 0814 l'unica regione è divisa internamente; w029 è l'unico con una quota di pixel lontani. Un modello che ha addestrato "accanto" guadagna di più sui pixel vicini (+0,14 F1 su w016, +0,07 su w029). Per questo le metriche vanno riportate **per strato di distanza** dal pixel di training più vicino, e i numeri su w016 e 0814 sono letture ottimistiche.

### Decisioni già prese, e perché

- **Il metro usa le tre `_validation_mask` ufficiali, non maschere generate da noi** — una maschera nuova su un segmento di training non "dis-addestra" un checkpoint già rilasciato: i pixel restano di training. Le maschere di R02 (`make_validation_mask.py`) servono a chi riaddestra; noi non riaddestriamo in E02.
- **Divisione per segmento: verifica = `pherc1667-w029`; sviluppo = `pherc0139-w016` + `pherc0814-46527`; controllo operativo = pixel di supervisione degli stessi tre segmenti + w035 nativo (E00)** — w029 ha la separazione reale migliore, il maggior numero di pixel held-out (≈382 k) e otto regioni; è di un rotolo diverso dagli altri due. Si sacrifica il caso migliore alla verifica finale perché la verifica è l'unica cosa che non si può rifare. Scartata la divisione per regione dentro w029: regioni dello stesso foglio sono correlate, e docs/03 preferisce segmento o rotolo. Il set di verifica non si usa per nessuna scelta fino a E05.
- **Su w029 E02 esegue l'inferenza ma non legge i pixel held-out** (revisione R1, finding 1) — servono i controlli di identità e di orientamento sui pixel di *training* di w029 per sapere che l'input poolato è corretto prima di sigillarlo; ma calcolare l'AUROC held-out di w029 già in E02 renderebbe disponibile il numero di verifica prima delle scelte di E03/E04, e la verifica smetterebbe di essere esclusa dalle scelte. Il TIFF di w029 viene conservato con hash; le sue metriche held-out si calcolano per la prima volta in E05, con lo stesso script congelato. Il confronto con R02 sui pixel held-out riguarda quindi solo w016 e 0814; sui pixel di training riguarda tutti e tre.
- **Baseline = E00, senza modifiche**: villa `3ea17f5`, `ink_9um` @ `7109667…`, `hybrid_3d2d-seed42/step-075000.pth` (primario) e `seed43/step-075000.pth` (informativo), `--overlap 0.5 --blend-mode hann --no-compile --gpus 0 --batch-size 1`, direzione `forward`, finestra Z di default, autocast fp16, installazione su Python di sistema con `--no-deps` — è la procedura verificata (L3) e riprodotta (G2); cambiare anche un solo parametro trasformerebbe il metro in un esperimento. Lo step resta 75000 per costruzione, anche se R02 mostra che su held-out altri step fanno meglio: scegliere lo step sui dati di verifica sarebbe esattamente l'errore che il metro deve impedire. Il confronto fra step è materia di E04.
- **Input dei tre segmenti allineati = pooling ufficiale `prepare_9um_isotropic_input.py` al commit `3ea17f5`, livello 2, workers 4** — è il percorso dichiarato dal model card per i volumi 2,4 µm; le label allineate dichiarano (`.zattrs`) `source_surface_volume_level: 2`, `source_z_slice: [13, 97]`, `z_pool: 21 complete means of 4 source planes`, e lo script sceglie esattamente i piani 13–96 di 109 (`ceil((109−84)/2) = 13`). Si esegue su Kaggle in sessione **senza acceleratore**, si conserva il risultato come dataset Kaggle privato (un tar per segmento, con hash) e i run GPU lo montano: il pooling costa rete e CPU, non GPU, e lo stesso input servirà a E03/E04. R02 ha osservato disconnessioni S3 con 24 connessioni: 4 workers, con ripetizione del run in caso di errore.
- **Finestra Z attesa per gli input a 21 slice: indici 2–18** — `(21 // 2) − (17 // 2) = 2`; il centro è 10, il piano su cui la label allineata è annotata (`annotation_center_channel: 10`). Per w035 nativo restano 6–22. Se il log mostra altro, fermarsi.
- **Metrica primaria per segmento: AUROC sui pixel held-out; secondarie: best-F1 con soglia libera (per confronto con R02) e F1 alla soglia congelata sui dati di sviluppo; sempre per strato di distanza e per regione** — l'AUROC non dipende dalla soglia e non premia la calibrazione; best-F1 è ciò che R02 pubblica ed è l'unico confronto esterno disponibile; la soglia congelata su sviluppo e applicata a verifica è il numero onesto per l'uso futuro. Le definizioni sono in §5 e nel codice di `scripts/e02_metrics.py`; DRD e pseudo-F-measure di R02 non si adottano (richiedono `opencv-contrib` e non aggiungono informazione decisiva).
- **Il confronto con i numeri di R02 è un controllo del metro, non un giudizio sul modello** — stessa pipeline, stesso branch, stessi input: un disaccordo grande segnalerebbe un errore nostro (pooling, orientamento, versione), non una scoperta. Tolleranza preregistrata in §5.
- **Tre revisioni Codex, pesanti e mirate, nessuna di routine** — (R1) il piano, prima dell'esecuzione; (R2) inventario, script delle metriche e test, prima di spendere GPU; (R3) manifest e scheda, prima del congelamento. Modello `gpt-6-astra`, effort `high` (configurazione utente di Codex verificata il 6 settembre 2026); `/codex:adversarial-review` con testo di focus per R1 e R3, `/codex:review` per R2. Le revisioni sono in sola lettura per costruzione del plugin.
- **Il socio lavora in parallelo solo su compiti che non toccano piano, manifest e metriche** (§9) — un solo writer per cartella; il branch `e02-socio` possiede soltanto i file elencati lì; la fusione la decide Matteo.
- **Nessun run GPU, invito, spesa o submission senza il "vai" di Matteo, uno per run** — come stabilito. Commit e push del lavoro verificato sono autorizzati senza richiesta puntuale (6 settembre 2026).
- **Le decisioni di E02 non includono la scelta dello stadio su cui investire** — come scritto nel documento di decisione: prima i numeri, poi la scelta.

### Vincoli

- Niente dati, checkpoint, TIFF, zarr o tar in Git: solo script, configurazioni piccole, scheda, manifest e notebook generati senza output. `.gitignore` copre già `data/`, `runs/`, `*.zarr/`, `*.tif`, `*.pth`, `.venv/`.
- Non modificare il codice di villa né i notebook di E00/E01 (artefatti congelati). Se serve una modifica a villa, fermarsi.
- Ogni cella di notebook che può fermare il run lo fa con un'asserzione che dice dove e perché.
- Tetto di spazio: 15 GB su Kaggle (misurato su `WORK` + `HEAVY`), 5 GB sul portatile (29 GiB liberi rilevati il 5 settembre 2026). Tetto GPU: 30 minuti per inferenza (timeout interno), 60 minuti di sessione. Tetto CPU Kaggle per il pooling: 4 ore di sessione per segmento. Nessuna spesa.
- Le richieste anonime a Hugging Face sono limitate (HTTP 429 osservato in E00/E01): download delle label con 4 thread e attesa crescente.
- Sul portatile il lavoro è CPU: nessuna inferenza locale.

---

## 3. Perimetro

### File da creare o modificare (nel repository)

| File | Cosa fare |
|---|---|
| `docs/plans/2026-09-06-e02-costruire-il-metro.md` | Questo piano; dopo la revisione R1, congelato in un commit dedicato |
| `requirements-cpu.txt` | Dipendenze CPU del portatile, versioni fissate (§4 passo 0) |
| `scripts/e02_inventory.py` | Inventario da tre fonti primarie con controlli incrociati → `configs/e02/ink9um_inventory.json` |
| `scripts/e02_metrics.py` | Metriche congelate (AUROC, orientamento, sweep di soglia, strati di distanza, regioni), CLI deterministica |
| `tests/test_e02_metrics.py` | Test unitari su array sintetici |
| `scripts/build_label_dataset.py` | Generalizzazione di `build_w035_label_dataset.py` a un elenco di segmenti → dataset Kaggle privato `papyruslab-e02-labels` |
| `scripts/build_e02_notebooks.py` | Generatore dei notebook `prep-<seg>` (CPU) e `infer-<seg>-seed<NN>` (T4) |
| `scripts/kaggle_e02.py` | Pilota: `push`, `status`, `wait`, `output`, `publish-input <seg>` (dataset dell'input poolato) |
| `kaggle/e02-r01-*/` | Notebook generati e `kernel-metadata.json` — **non modificare a mano** |
| `configs/e02/ink9um_inventory.json` | Inventario generato (piccolo) |
| `configs/e02/split.json` | Ruoli dei segmenti e dei pixel, con motivazioni |
| `configs/e02/baseline.json` | Baseline congelata: commit, revisioni, hash, comando, finestra Z per famiglia |
| `docs/reports/2026-09-XX-e02-r01.md`, `docs/reports/2026-09-XX-e02-r01-manifest.json` | Scheda dell'esperimento e manifest |
| `docs/roadmap.md`, `README.md`, `AGENTS.md`, `docs/06-ricerca-community.md` | Consolidamento finale (stato, R02 adottato per la valutazione, esito) |

Fuori da Git: `runs/E02-R01/<run>/<timestamp>/` sul portatile; su Kaggle `WORK=/kaggle/working/e02` (persistito) e `HEAVY=/tmp/e02` (non persistito); dataset Kaggle privati `matteopontesilli/papyruslab-e02-labels` e `matteopontesilli/papyruslab-e02-input-<seg>`.

### File da NON toccare

| File | Perché |
|---|---|
| `docs/07-procedura-operativa.md`, `docs/08-dossier-input-e00.md`, `docs/decisions/2026-09-06-dove-investire.md` | Congelati; una correzione è un commit separato con motivazione |
| `scripts/build_e00_notebooks.py`, `scripts/kaggle_e00.py`, `scripts/build_w035_label_dataset.py`, `kaggle/e00-r01-*`, `kaggle/e01-r01-*` | Artefatti congelati di E00/E01: la riproducibilità dipende dal loro stato |
| Codice di villa | Qualsiasi modifica renderebbe il risultato non riproducibile dal commit dichiarato |
| `.gitignore` | Copre già tutto ciò che serve |

---

## 4. Passi

### Come si esegue

I passi 0–3 sono locali (portatile, CPU) e non toccano Kaggle. I passi 4–8 usano l'API Kaggle tramite `scripts/kaggle_e02.py`, con lo stesso schema di E00: notebook generati, ogni condizione di arresto come asserzione, output scaricati in cartelle per versione e verificati con `SHA256SUMS`. **Dove un frammento qui sotto e il generatore differiscono, fa fede il generatore.** ID del run: `E02-R01`; un tentativo fallito per causa tecnica conserva l'ID con numero di tentativo crescente; una modifica scientifica crea `E02-R02` con piano corretto.

| Run Kaggle | Acceleratore | Cosa fa | Timeout piattaforma |
|---|---|---|---|
| `prep-46527`, `prep-w016`, `prep-w029` | nessuno | installa, verifica la label montata, esegue il pooling ufficiale dal livello 2 via URL, verifica forma e attributi, tar + hash, persiste | 14.400 s |
| `infer-<seg>-seed42` ×3 | T4 (allocazione doppia, uso singolo) | verifica subito label e input poolato montati (hash), altrimenti si ferma; installa, verifica hash dei checkpoint, inferenza, controlli sul log, metriche minime (w029: solo pixel di training), persiste TIFF + metriche | 3.600 s |
| `infer-<seg>-seed43` ×3 | T4 | idem con seed 43, solo se il seed 42 dello stesso segmento ha superato i gate | 3.600 s |

Sul portatile, PowerShell, dalla cartella del repository:

```powershell
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements-cpu.txt
python scripts/e02_inventory.py --out configs/e02/ink9um_inventory.json        # passo 1
python -m pytest tests/test_e02_metrics.py -q                                   # passo 3
python scripts/build_label_dataset.py --run-id e02-r01 --segments aligned-scrollprizeorg-21slices/pherc0814-46527 aligned-scrollprizeorg-21slices/pherc0139-w016 aligned-scrollprizeorg-21slices/pherc1667-w029   # passo 4
kaggle datasets create -p runs\E02-R01\dataset-labels                           # passo 4 (prima volta)
python scripts/build_e02_notebooks.py                                           # passo 5: rigenera kaggle/e02-r01-*
python scripts/kaggle_e02.py push   prep-46527; python scripts/kaggle_e02.py wait prep-46527; python scripts/kaggle_e02.py output prep-46527
python scripts/kaggle_e02.py publish-input 46527                                # dataset dell'input poolato
# … idem per w016 e w029 (passo 6)
# --- STOP: "vai" di Matteo per ogni run GPU ---
python scripts/kaggle_e02.py push   infer-46527-seed42; … wait; … output        # passo 7, poi w016, w029
python scripts/e02_metrics.py --pred runs\E02-R01\infer-46527-seed42\<ts>\e02\out\pherc0814-46527_seed42_step075000.tif --labels data\labels\aligned-scrollprizeorg-21slices\pherc0814-46527 --out runs\E02-R01\metrics\pherc0814-46527_seed42.json
```

### Passo 0 — Base verificata e ambiente del portatile

**Cosa:** verificare il commit, creare l'ambiente CPU, autenticare Kaggle.
**Come:** `git status --short` vuoto; `git rev-parse --short HEAD` = commit congelato (§10). Creare `requirements-cpu.txt` con versioni fissate e coerenti con il lock di villa dove il pacchetto coincide:

```text
numpy==2.2.6          # versione già presente sul portatile; sotto la 2.3 come il lock di villa
zarr==2.18.7          # API Zarr v2, come su Kaggle in E00
numcodecs==0.15.1     # come su Kaggle in E00
imagecodecs==2026.3.6 # come su Kaggle in E00 (dipendenza pigra di tifffile per LZW)
tifffile==2026.8.23   # ultima su PyPI il 6 settembre 2026
scipy==1.18.1         # ultima su PyPI il 6 settembre 2026
fsspec==2026.7.0      # versione già presente sul portatile
aiohttp==3.14.3       # ultima su PyPI il 6 settembre 2026
requests==2.34.2      # ultima su PyPI il 6 settembre 2026
pytest==9.1.1         # ultima su PyPI il 6 settembre 2026
kaggle==2.2.4         # stessa CLI usata in E01
```

Tutte le versioni esistono su PyPI e **l'installazione è stata verificata il 6 settembre 2026** su Python 3.12.10 (`.venv`, tutte le versioni fissate importabili, CLI Kaggle 2.2.4). Se in futuro `pip` non riuscisse a installarne una (per esempio una ruota Windows mancante), **fermarsi**: conservare il log del tentativo e `pip freeze`, correggere `requirements-cpu.txt` in una nuova revisione del piano, verificare l'installazione e solo allora proseguire. Non si prosegue con un ambiente diverso dal file congelato (revisione R1, finding 8). Poi `kaggle auth login` (**Matteo**, apre il browser); verifica `kaggle kernels list --mine --page-size 3` (codice 0; "Not found" con codice 0 significa nessun kernel, non errore: osservato in E01). Registrare `python --version` e `pip freeze` in `runs/E02-R01/env/`.
**Fatto quando:** l'ambiente importa `numpy, zarr, tifffile, scipy`; il comando Kaggle risponde; `git status` è pulito a parte `requirements-cpu.txt` e `.venv/` (ignorata).
**Fermarsi se:** il commit non coincide; Kaggle non autentica.

### Passo 1 — Inventario da tre fonti, con controlli incrociati

**Cosa:** generare `configs/e02/ink9um_inventory.json` da (a) il README del dataset, (b) il contratto di villa, (c) l'elenco del bucket, più i metadati S3 di ogni volume sorgente; fermarsi a ogni disaccordo.
**Dove:** `scripts/e02_inventory.py`.
**Come:** lo script scarica il README (`https://huggingface.co/buckets/scrollprize/datasets/resolve/ink_9um/README.md`) e ne registra lo SHA-256; scarica `aligned21_fixed_scroll_prior.json` da `raw.githubusercontent.com/ScrollPrize/villa/3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e/ink-detection/configs/…` e ne registra lo SHA-256; elenca `ink_9um/labels` con l'API paginata (`Link: rel="next"`, come in `build_w035_label_dataset.py`); per ogni volume sorgente legge `.zattrs`, `0/.zarray` e, per gli allineati, `2/.zarray`; per ogni label legge `<seg>_inklabels.zarr/0/.zarray` e `.zattrs`. Controlli, tutti come asserzioni:

```python
assert set(readme_aligned) == set(contract_aligned) == set(bucket_aligned), "nomi allineati diversi fra README, contratto e bucket"
assert set(readme_native) == set(contract_native) == set(bucket_native)
assert len(readme_aligned) == 24 and len(readme_native) == 5
public_of = {**{k: v.public_segment for k, v in readme_aligned.items()}, **{k: v.public_segment for k, v in readme_native.items()}}
physical = set(public_of.values()); assert len(physical) == 24, f"segmenti fisici: {len(physical)}"
dual = {p for p in physical if sum(1 for k in public_of if public_of[k] == p) == 2}
assert dual == {"20260317000000-w035_2026031718", "20260302000000-w039_2026030210", "20250831000000-w040_2025083102", "20260108000000-w041_2026010816", "20260115000000-w044_2026011522"}
assert {s for s in bucket_aligned if "validation_mask" in bucket_aligned[s].arrays} == {"pherc0139-w016", "pherc0814-46527", "pherc1667-w029"}
for s, lab in labels.items():                      # forma label == forma del livello sorgente
    src = volumes[s]; lvl = "2" if s in readme_aligned else "0"
    assert lab.shape[1:] == src.levels[lvl].shape[1:], f"{s}: label {lab.shape} vs volume livello {lvl} {src.levels[lvl].shape}"
    assert lab.shape[0] == (21 if s in readme_aligned else 28)
# finding L2 registrato, non asserito: chiavi fisiche del contratto
contract_keys = {r["segment"]: r["physical_segment_key"] for r in contract["representations"]}
inventory["contract_physical_key_mismatch"] = [p for p in dual if len({contract_keys[k] for k in public_of if public_of[k] == p}) > 1]   # atteso: ['20260115000000-w044_2026011522']
```

Il JSON contiene, per rappresentazione: nome label, famiglia, rotolo, segmento pubblico, URL del volume, livello usato, forma per livello, chunk, scala, conteggio file e byte della label, array presenti, `annotation_center_channel`, `source_z_slice`, chiave fisica del contratto; più le sezioni `physical_segments` (24), `dual_representations` (5), `validation_mask_segments` (3), `known_physical_duplicates_outside_training` (`w046` ↔ `w045`, fonte villa #1547), `sources` (URL, revisione, SHA-256, data). Lo script stampa anche la tabella Markdown di §2.2 e la confronta riga per riga con quella scritta qui: una differenza ferma il run (o corregge il piano prima dell'esecuzione).
**Fatto quando:** il JSON esiste, tutte le asserzioni passano, la tabella coincide con §2.2, `python scripts/e02_inventory.py --check configs/e02/ink9um_inventory.json` rigenera un file identico (byte per byte, con `sources.date` esclusa dal confronto).
**Fermarsi se:** un'asserzione fallisce: il dataset a monte è cambiato o il piano è sbagliato; correggere il piano in un nuovo commit prima di continuare.

### Passo 2 — Divisione e label locali

**Cosa:** scrivere `configs/e02/split.json` e scaricare le tre label in locale.
**Come:** `split.json`:

```json
{
  "verifica":   {"segments": ["pherc1667-w029"], "pixels": "validation_mask == 1 al piano Z=10", "uso": "nessuno prima di E05"},
  "sviluppo":   {"segments": ["pherc0139-w016", "pherc0814-46527"], "pixels": "validation_mask == 1 al piano Z=10", "uso": "scelte di E03/E04, soglia congelata"},
  "controllo_operativo": {"segments": ["pherc0139-w016", "pherc0814-46527", "pherc1667-w029", "w035 (nativo, E00)"], "pixels": "supervision_mask == 1", "uso": "riferimento di memorizzazione, mai come misura di generalizzazione"},
  "training_non_misurato": "le altre 25 rappresentazioni",
  "cross_scroll": "non disponibile: nessuna label ufficiale anonima fuori dai quattro rotoli a ~9 µm",
  "esclusioni": {"20260325000000-w046_20260325": "stesso foglio del pubblico w045 (villa #1547)"},
  "motivazioni": "vedi docs/plans/2026-09-06-e02-costruire-il-metro.md §2 Decisioni"
}
```

`configs/e02/baseline.json` fissa la baseline, copiando le costanti da `scripts/build_e00_notebooks.py`:

```json
{
  "villa_commit": "3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e",
  "ink_9um_revision": "7109667e2607db1b90c37c8b09cb876ea7fe7bb1",
  "checkpoints": {"seed42": {"path": "hybrid_3d2d-seed42/step-075000.pth", "bytes": 138360039, "sha256": "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"},
                  "seed43": {"path": "hybrid_3d2d-seed43/step-075000.pth", "bytes": 138360231, "sha256": "2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f"}},
  "primary_seed": 42,
  "infer_args": ["--overlap", "0.5", "--blend-mode", "hann", "--no-compile", "--gpus", "0", "--batch-size", "1"],
  "direction": "forward",
  "layer_window": {"aligned_21": [2, 18], "native_28": [6, 22]},
  "input_prep_aligned": {"script": "ink-detection/scripts/prepare_9um_isotropic_input.py", "level": 2, "source_z_slice": [13, 97], "output_slices": 21, "workers": 4},
  "install": "python di sistema Kaggle, pip --no-deps, pacchetti aggiunti dal lock di villa",
  "threshold_dev": null,
  "threshold_dev_note": "argmax F1 sull'unione dei pixel held-out di pherc0139-w016 e pherc0814-46527, seed 42: compilato al passo 7, mai ricalcolato su pherc1667-w029"
}
```

Le label: **in questo passo si scrive** `scripts/build_label_dataset.py` (generalizzazione dello script di E00: elenco di segmenti `<famiglia>/<seg>`, elenco dall'API paginata del bucket, download con 4 thread e attesa crescente sui 429, verifica per file, un tar deterministico per segmento, `manifest.json` con elenco API, dimensioni, SHA-256 per file, tree-SHA-256 e tar-SHA-256, `dataset-metadata.json` per Kaggle). Comando: `python scripts/build_label_dataset.py --run-id e02-r01 --segments aligned-scrollprizeorg-21slices/pherc0814-46527 aligned-scrollprizeorg-21slices/pherc0139-w016 aligned-scrollprizeorg-21slices/pherc1667-w029`; scarica in `runs/E02-R01/dataset-labels-stage/labels/<famiglia>/<seg>/`, prepara `runs/E02-R01/dataset-labels/` e copia gli alberi in `data/labels/<famiglia>/<seg>/` (ignorata). Conteggi attesi dall'elenco del 6 settembre 2026: `pherc0814-46527` 1.386 file / 118.869 byte; `pherc0139-w016` 9.414 / 746.565; `pherc1667-w029` 13.959 / 1.108.191. La pubblicazione su Kaggle è il passo 4 (revisione R1, finding 5).
**Fatto quando:** i tre alberi locali hanno esattamente quei conteggi; `manifest.json` riporta tree-SHA-256 (definizione di `build_w035_label_dataset.py`) e tar-SHA-256 dei tre segmenti; `split.json` e `baseline.json` sono scritti.
**Fermarsi se:** conteggi o byte differiscono anche di uno: il dataset a monte è cambiato dopo la misura.

### Passo 3 — Script delle metriche, con test prima del codice

**Cosa:** `scripts/e02_metrics.py`, CLI deterministica, e `tests/test_e02_metrics.py` scritto **prima**.
**Interfaccia:**

```text
python scripts/e02_metrics.py --pred PRED.tif --labels SEGMENT_DIR --out REPORT.json [--sets held,train] [--threshold N] [--edges 0 64 128 256] [--patch 128]
python scripts/e02_metrics.py --geometry --labels SEGMENT_DIR --out GEOMETRY.json [--edges …] [--patch 128]   # solo strati e regioni, senza predizione (compito S1)
```

`--sets` (default `held,train`) elenca gli insiemi di pixel da misurare: per `pherc1667-w029` in E02 si passa **`--sets train`** e lo script non legge la `validation_mask` (finding 1 di R1). `--patch 128` è la patch di training sulla scala delle label; gli strati usano la distanza euclidea al pixel di training più vicino con confine escluso (`d < 128`, `d < 256`).

`SEGMENT_DIR` contiene `<seg>_inklabels.zarr`, `<seg>_supervision_mask.zarr` e, se esiste, `<seg>_validation_mask.zarr`; il piano annotato è `shape[0] // 2` (10 per 21 slice, 14 per 28: stessa regola del trainer e di R02). Funzioni (nomi congelati, usati anche nei notebook):

- `auroc(scores, pos, valid)` — la funzione di E00 (rank medio sui pareggi), invariata.
- `sweep(pos_hist, neg_hist)` — precision/recall/F1 a ogni soglia 0–255 dai due istogrammi (adattata da `tools/eval_validation.py` di R02, MIT, con attribuzione nel file); un pixel è "predetto inchiostro" quando `score >= t`. `best_f1(sweep)` restituisce la **soglia più bassa** fra quelle che massimizzano F1 (`np.argmax` sul vettore, che prende il primo massimo): regola dei pareggi congelata, usata anche per `threshold_dev` (finding 3 di R1). `at_threshold(sweep, t)`.
- `trivial_floor(p) = 2p / (1 + p)` — F1 del classificatore "tutto inchiostro" con frazione d'inchiostro `p`.
- `orientation(pred, ink, valid)` — le quattro AUROC (originale, rot180, flipY, flipX) e `orientamento_ok`, con una differenza rispetto a E00 (revisione R1, secondo giro): E00 indicizzava la predizione con la **maschera trasformata**, che può cadere su coordinate fuori dalla supervisione, held-out comprese; in E02 ogni variante si calcola sull'**intersezione** `valid ∧ T(valid)` con positivi `T(ink) ∧ valid ∧ T(valid)`, così lo script legge la predizione soltanto sulle coordinate della maschera di training originale. Un'intersezione vuota o con una sola classe dà `NaN` e la variante è "non confrontabile"; `orientamento_ok` richiede l'originale strettamente maggiore di ogni variante confrontabile e almeno una variante confrontabile, altrimenti il gate è "non valutabile" e il run si ferma. Per l'originale `valid ∧ valid = valid`: l'AUROC di E00 resta riproducibile al decimale.
- `strata(held, supervision, edges, patch)` — distanza euclidea (`scipy.ndimage.distance_transform_edt(~supervision)`) e maschere per strato `<64, 64–128, 128–256, ≥256`, quota entro una e due patch (adattata da `tools/audit_holdout_masks.py` di R02).
- `regions(held)` — componenti connesse (`scipy.ndimage.label`) con conteggi, densità d'inchiostro e bbox.
- `report(...)` — un solo JSON con: `sets` (`held`, `train`) → `n_px, n_ink, ink_fraction, trivial_floor, auroc, best_f1 {f1, threshold, precision, recall}, at_threshold {...}` (se `--threshold`), `orientation` (calcolata su `train`: più pixel, è un gate di identità), `strata` (per `held`: px, densità, AUROC, best-F1, quota), `regions` (per `held`), `disjoint_check: n_px(held ∧ train)` (atteso 0), `sha256_pred`, `shape`, `dtype`, `version` dello script.

Test minimi (array 64×64 sintetici, senza rete):

```python
def test_auroc_perfect_and_random():
    scores = np.zeros((8, 8), np.uint8); scores[:, 4:] = 255
    ink = np.zeros((8, 8), bool); ink[:, 4:] = True
    valid = np.ones((8, 8), bool)
    assert auroc(scores, ink, valid) == 1.0
    assert auroc(np.full((8, 8), 7, np.uint8), ink, valid) == 0.5      # tutti pareggi → 0,5

def test_best_f1_threshold_and_floor():
    pos = np.bincount([200, 210, 220], minlength=256); neg = np.bincount([10, 20, 30], minlength=256)
    s = sweep(pos, neg); b = best_f1(s)
    assert b["f1"] == 1.0 and b["threshold"] == 31          # F1 = 1 per ogni t in 31..200: si congela la piu' bassa
    assert at_threshold(s, 200)["f1"] == 1.0 and at_threshold(s, 201)["recall"] < 1.0
    assert abs(trivial_floor(0.5) - 2 / 3) < 1e-12

def test_strata_partition_held_pixels():
    sup = np.zeros((64, 64), bool); sup[:, :8] = True
    held = np.zeros((64, 64), bool); held[:, 16:] = True
    st = strata(held, sup, edges=[0, 8, 16, 32], patch=8)
    assert sum(int(m.sum()) for _, m in st["masks"]) == int(held.sum())
    assert st["within_patch"] == 0.0                                   # tutti a ≥ 8 px

def test_orientation_detects_flip():
    # inchiostro solo nel quadrante in alto a sinistra: ogni trasformazione lo sposta altrove
    pred = np.zeros((16, 16), np.uint8); pred[:8, :8] = 255
    ink = np.zeros((16, 16), bool); ink[:8, :8] = True
    o = orientation(pred, ink, np.ones((16, 16), bool))
    # trasformata: i 64 positivi hanno score 0; fra i 192 negativi, 128 hanno score 0 (pareggio, 0,5) e 64 hanno 255
    # -> AUROC = 128 * 0,5 / 192 = 1/3, non 0 (verificato da Codex in R1 con la funzione di E00)
    assert o["originale"] == 1.0
    for k in ("flipY", "flipX", "rot180"):
        assert abs(o[k] - 1 / 3) < 1e-9
    assert o["orientamento_ok"]
    # simmetria in X: flipX pareggia l'originale, quindi "strettamente massima" deve fallire
    pred2 = np.zeros((16, 16), np.uint8); pred2[:8] = 255
    ink2 = np.zeros((16, 16), bool); ink2[:8] = True
    assert not orientation(pred2, ink2, np.ones((16, 16), bool))["orientamento_ok"]

def test_held_out_pixels_are_never_read():
    # maschera di training a sinistra, held-out a destra, disgiunte: cambiare SOLO le predizioni held-out
    # non deve cambiare nessuna metrica ne' il gate quando si misura l'insieme 'train' (R1, secondo giro)
    rng = np.random.default_rng(0)
    train = np.zeros((32, 32), bool); train[:, :12] = True
    held = np.zeros((32, 32), bool); held[:, 20:] = True
    ink = np.zeros((32, 32), bool); ink[4:12, 2:8] = True; ink[10:20, 22:30] = True
    pred = rng.integers(0, 256, (32, 32)).astype(np.uint8); pred[ink] = 240
    pred2 = pred.copy(); pred2[held] = rng.integers(0, 256, int(held.sum())).astype(np.uint8)
    a, b = orientation(pred, ink, train), orientation(pred2, ink, train)
    assert a == b
    assert auroc(pred, ink & train, train) == auroc(pred2, ink & train, train)
    assert (train & held).sum() == 0

def test_report_is_deterministic(tmp_path):
    # due chiamate sullo stesso input producono JSON identici (esclusa la chiave 'generated_at')
```

**Fatto quando:** i test falliscono prima dell'implementazione (import assente), passano dopo; `python scripts/e02_metrics.py` su E00 (se il TIFF di w035 è disponibile sul fisso) riproduce l'AUROC originale `0,9990785918` al decimale (le tre trasformate hanno in E02 una definizione diversa, sull'intersezione delle maschere, e non sono confrontabili con i valori di E00) — altrimenti questo controllo si esegue sul primo TIFF di E02 confrontando la cella minima del notebook con lo script locale.
**Fermarsi se:** una funzione non è deterministica; l'AUROC di E00 non è riprodotta.

### Passo 4 — Dataset Kaggle delle label

**Cosa:** pubblicare la cartella `runs/E02-R01/dataset-labels/` preparata al passo 2 come dataset privato `matteopontesilli/papyruslab-e02-labels` (`kaggle datasets create -p …` la prima volta, `kaggle datasets version` poi) e verificarne lo stato. Kaggle estrae i tar al caricamento: i notebook cercano `**/<seg>/<seg>_inklabels.zarr/0/.zarray` in modo ricorsivo sotto `/kaggle/input` (lezione di E00: il mount cambia fra sessioni CPU e GPU) e verificano file per file contro `manifest.json`, poi il tree-SHA-256.
**Fatto quando:** `kaggle datasets status matteopontesilli/papyruslab-e02-labels` risponde `ready` (ripetere dopo un `403` transitorio, osservato in E01); tar-SHA-256 e tree-SHA-256 dei tre segmenti sono copiati in `scripts/build_e02_notebooks.py` come costanti.

### Passo 5 — Generatore dei notebook e pilota; primo run CPU su 0814

**Cosa:** `scripts/build_e02_notebooks.py` e `scripts/kaggle_e02.py`, poi il run `prep-46527` (il segmento più piccolo: 0,8 GB da leggere) che vale anche da preflight.
**Come:** il generatore riusa, copiandole, le celle di E00 per ambiente (`env.sh`, guardia dello spazio a 15 GB, versioni, rete), checkout parziale di villa al commit congelato (`ink-detection` e `vesuvius`), installazione `--no-deps` con gli stessi controlli (nel run CPU: torch `2.10.0+cpu`; nei run GPU `2.10.0+cu128`), download e hash dei checkpoint (solo nei run GPU). Celle nuove:

- **label**: ricerca ricorsiva del dataset, verifica per file e tree-SHA-256; ripiego al download diretto con 4 thread (come E00) se non montato.
- **prep** (solo run CPU): `python $HEAVY/villa/ink-detection/scripts/prepare_9um_isotropic_input.py "$SRC_URL" $HEAVY/input/<seg>_pooled.zarr --level 2 --workers 4 2>&1 | tee $WORK/logs/prep_<seg>.log` con `timeout 12600`; poi in Python:

```python
g = zarr.open(f"{HEAVY}/input/{SEG}_pooled.zarr", mode="r"); a = g["0"]
lab = zarr.open(f"{HEAVY}/labels/{SEG}/{SEG}_inklabels.zarr", mode="r")["0"]
assert tuple(a.shape) == tuple(lab.shape), f"STOP: input poolato {a.shape} vs label {lab.shape}"
assert g.attrs["source_z_slice"] == [13, 97] and g.attrs["source_level"] == "2" and a.dtype == np.uint8, g.attrs
assert g.attrs["source_shape_zyx"][0] == 109, "STOP: volume sorgente con profondità diversa da 109"
blk = a[:, a.shape[1]//2 - 64 : a.shape[1]//2 + 64, a.shape[2]//2 - 64 : a.shape[2]//2 + 64]
assert blk.max() > 0, "STOP: blocco centrale vuoto"
# tar deterministico (mtime 0, ordinamento) + SHA-256 + tree-SHA-256 dell'albero zarr (stessa definizione delle label)
```

  Il tar va in `$WORK/out/<seg>_pooled.tar` (w029: ≈1,6 GB non compresso, blosc lo riduce); `SHA256SUMS` finale. Un errore S3 (`ServerDisconnectedError`, 5xx) dopo i tentativi interni fa fallire il run: si ripete il run intero (stesso ID, tentativo +1), non si aggiungono ritentativi ad hoc nel codice di villa.
- **infer** (run GPU): la cella di E00 con `SRC` = percorso locale dell'input poolato montato (o `$ZARR` nativo per w035 se mai rieseguito), `CUDA_VISIBLE_DEVICES=0`, campionamento della memoria di entrambe le GPU, `timeout -s INT -k 30 1800`. Controllo del log: `Selected source layer indices=[2, …, 18]` per input a 21 slice, `in_chans=17`, `Using CUDA device 0`, `Wrote …`. **Nessun pooling in sessione GPU** (finding 6 di R1): la prima cella del run cerca l'input poolato sotto `/kaggle/input`, ne verifica il tree-SHA-256 contro la costante del generatore e, se manca o differisce, ferma il run prima di qualunque installazione; il pilota rifiuta il `push` di un `infer-*` se il dataset `papyruslab-e02-input-<seg>` non risulta `ready` o se la costante di hash non è stata scritta nel generatore. Un input mancante si ripara con il percorso CPU (`prep-*`), mai dentro una sessione GPU.
- **metriche minime** (run GPU): la cella importa il testo di `scripts/e02_metrics.py` inlineato dal generatore (il repository è privato: Kaggle non può scaricarlo) ed esegue `report()` con `--sets held,train` per w016 e 0814 e **`--sets train` per w029**; gate: `shape_ok`, `orientamento_ok` su `train`, `disjoint_check == 0` (calcolato dalle sole maschere, senza leggere la predizione sui pixel held-out); salva `metrics_<seg>_seed<NN>.json`. Il verdetto (`error` se un gate fallisce) è nell'ultima cella, dopo la persistenza.
- **guardia del seed 43**: come E00, richiede l'esito del seed 42 dello stesso segmento montato come dataset o kernel source, con SHA-256 del TIFF verificato.

Il pilota `scripts/kaggle_e02.py` deriva i modi dal generatore, usa `-t 14400` per i run `prep-*` e `-t 3600` per gli `infer-*`, scarica in `runs/E02-R01/<run>/<timestamp>/`, verifica `SHA256SUMS` e gli output richiesti, con `publish-input <seg>` pubblica `<seg>_pooled.tar` + manifest come dataset `matteopontesilli/papyruslab-e02-input-<seg>` (crea, oppure nuova versione se esiste) e, prima di ogni `push infer-*`, controlla che i dataset delle label e dell'input del segmento siano `ready` e che il generatore contenga i loro hash; per `infer-*-seed43` richiede anche l'esito verificato del seed 42 dello stesso segmento (come il pilota di E00).
**Fatto quando:** `python scripts/build_e02_notebooks.py` rigenera `kaggle/e02-r01-*` senza diff; `prep-46527` termina `complete`, `output` dà `differenze: 0`, `<seg>_pooled.tar` ha la forma attesa `(21, 2130, 3455)`; `publish-input 46527` → `ready`.
**Fermarsi se:** forma diversa dalla label; attributi diversi da quelli attesi; tar oltre 5 GB; il run supera 4 ore.

### Passo 6 — Pooling di w016 e w029 (CPU)

Come il passo 5 per `prep-w016` (atteso `(21, 7020, 7220)`, ≈5,6 GB letti) e `prep-w029` (atteso `(21, 9500, 7830)`, ≈8,3 GB letti). Registrare tempi di lettura e dimensione dei tar. Sono run senza GPU: non richiedono un "vai" puntuale, ma vanno annunciati prima del lancio.
**Fatto quando:** i tre dataset `papyruslab-e02-input-<seg>` sono `ready`, con hash nel generatore.

### Passo 7 — Baseline seed 42 sui tre segmenti (GPU, un "vai" per run)

Ordine: `infer-46527-seed42` (≈1 minuto di inferenza stimato dal costo di E00, 32 blocchi/s), poi `infer-w016-seed42` (≈5–6 minuti), poi `infer-w029-seed42` (≈8–9 minuti). Dopo ogni run: `output`, poi in locale `scripts/e02_metrics.py` sul TIFF scaricato con le label locali (`--sets held,train` per w016 e 0814, **`--sets train` per w029**), e confronto con il JSON delle metriche minime prodotto su Kaggle (AUROC uguale al decimale: stesso codice, stesso input). Poi il **controllo di replica esterna** (§5 C): best-F1 contro R02 docs/14 (seed 42, step 75k) sui pixel held-out di `pherc0139-w016` (0,531) e `pherc0814-46527` (0,753), e sui pixel di training di tutti e tre (0,984 / 0,989 / 0,986). Il valore held-out di w029 pubblicato da R02 (0,658) **non** viene confrontato in E02: resta per E05. Infine `threshold_dev` (§5 D) viene calcolata dai soli held-out di sviluppo e scritta in `baseline.json`. Il TIFF di w029 viene conservato in `runs/E02-R01/` con SHA-256 nel manifest e non viene letto sui pixel held-out da nessuno script fino a E05.
**Fatto quando:** tre TIFF con `gate_A` e `gate_B` superati; tre report locali (w029 solo `train`); la tabella di §5 D compilata; `threshold_dev` scritta.
**Fermarsi se:** un gate fallisce; il disaccordo con R02 supera 0,10 su un confronto ammesso (§5 C); un run supera 30 minuti di inferenza; uno script o una persona legge i pixel held-out di w029.

### Passo 8 — Seed 43 (informativo, GPU, un "vai" per run)

Stessi tre run con seed 43, solo dopo il passo 7. Registrare Spearman, ΔAUROC e Δbest-F1 fra i seed sui pixel held-out di w016 e 0814 e sui pixel di training di tutti e tre; su w029 **solo** pixel di training. Nessuna soglia: la concordanza non è indipendenza. Se la quota o il tempo mancano, il passo 8 si può rinviare senza invalidare E02: va scritto nella scheda come "non eseguito".

### Passo 9 — Manifest, scheda, revisione R3, consolidamento

Scrivere `docs/reports/2026-09-XX-e02-r01-manifest.json` (commit PapyrusLab, commit villa, revisione HF, hash dei checkpoint, hash dei tre tar di label e dei tre tar di input, SHA-256 dei TIFF, comandi risolti, versioni Kaggle dei run, tempi, picchi di memoria, spazio, quota GPU consumata, tolleranze e confronti R02) e la scheda da `docs/templates/esperimento.md`, con la tabella per segmento (held / train / strati / regioni), i limiti (intra-segmento, adiacenza), la decisione proposta (promuovere a G3 / ripetere / modificare) e ciò che smentirebbe la conclusione. Consegnare a Codex (R3, `/codex:adversarial-review` con focus: "il manifest fissa davvero tutto ciò che serve a rifare e a non barare? quali pixel potrebbero essere training senza che ce ne accorgiamo?"). Classificare i finding (accettato / rifiutato / differito, con motivo); un secondo giro solo per correzioni materiali. Poi aggiornare `docs/roadmap.md` (F3 → E02 eseguito, G3 proposto/raggiunto), `README.md` (stato), `AGENTS.md` (riga della fase), `docs/06-ricerca-community.md` (R02: strumenti di valutazione **adottati** in forma adattata, licenza MIT, revisione `13920ba`; R04 consultato, non adottato; villa #1547 e #1231 registrati). Commit e push del lavoro verificato.

---

## 5. Criterio di esito, deciso prima della prova

Tutte le misure sui pixel del piano annotato (`shape[0] // 2`); `held` = `validation_mask == 1`; `train` = `supervision_mask == 1`; mai mescolati.

**A. Identità** (tutti, altrimenti il run è fallito): commit villa `3ea17f5…`; revisione HF `7109667…`; SHA-256 dei checkpoint (`e635558a…9cab`, `2aeaa85a…b28f`); label con conteggi, byte e tree-SHA-256 uguali al passo 2; input poolato con tree-SHA-256 uguale a quello del run `prep-*` corrispondente; `torch.__version__` invariato dopo l'installazione; log con indici **2–18** e `in_chans=17`; `exit_code=0`; TIFF `uint8` con forma uguale a `label.shape[1:]`.

**B. Metro valido** (tutti, altrimenti E02 non superato):
- M1 inventario: tutte le asserzioni del passo 1 passano; la tabella generata coincide con §2.2.
- M2 dati: per ciascuno dei tre segmenti `n_px(held ∧ train) = 0`, `n_px(held) > 0`, forma label = forma input, `source_z_slice = [13, 97]`, `annotation_center_channel = 10`.
- M3 orientamento: su `train`, l'AUROC con la label originale è strettamente maggiore di ogni variante confrontabile (calcolate sull'intersezione fra maschera di training originale e trasformata, così nessuna coordinata held-out viene letta), per ogni segmento e seed; almeno una variante deve essere confrontabile. Se una trasformata vince, l'input poolato è disallineato: E02 fallito, qualunque sia il valore.
- M4 determinismo: `scripts/e02_metrics.py` eseguito due volte sullo stesso TIFF produce JSON identici (esclusa `generated_at`); i test unitari passano; la cella Kaggle e lo script locale danno la stessa AUROC al decimale.
- M5 separazione dichiarata: il manifest riporta per ogni segmento (w029 compreso: è geometria delle maschere, non una lettura della predizione) la quota di pixel held-out a distanza < 128 px e < 256 px dal training più vicino e, per i segmenti di sviluppo, i numeri per strato.
- M6 sigillo: nessun file di metriche di E02 contiene valori calcolati sui pixel held-out di w029; il TIFF di w029 ha SHA-256 registrato nel manifest.

**C. Replica esterna** (controllo del metro, seed 42, step 75000, best-F1): cinque confronti ammessi — `held` di w016 e 0814, `train` di w016, 0814 e w029. |nostro − R02| ≤ 0,03 su tutti e cinque → *concordante*; fra 0,03 e 0,10 → *anomalo*: E02 sospeso finché la causa (pooling, versione, blending, TIFF) non è trovata e scritta; > 0,10 → *fallito*. Il confronto è informativo sul valore del modello e vincolante sulla validità del metro: due esecuzioni della stessa pipeline sugli stessi input devono coincidere. Il sesto valore di R02 (`held` di w029, 0,658) si confronta in E05.

**D. Prima lettura del metro** (risultato, nessuna soglia): per seed, w016 e 0814 su `held` e `train`, w029 solo su `train`: AUROC, best-F1 (soglia più bassa fra i massimi), F1 alla soglia congelata τ\*, precision, recall, floor banale; per i `held` di sviluppo anche per strato e per regione. τ\* = soglia più bassa che massimizza F1 sull'unione dei pixel held-out di sviluppo (w016 + 0814, seed 42, comparatore `score >= t`); viene scritta in `baseline.json` (campo `threshold_dev`) al passo 7 e vale per E03/E04; **non** si ricalcola su w029.

**E. Formulazione ammessa in caso di successo:** *"Esiste un metro intra-segmento su tre segmenti di tre rotoli, con N pixel mai usati per la supervisione dei checkpoint rilasciati, adiacenza al training misurata e dichiarata; la baseline congelata misura X sui segmenti di sviluppo; il segmento di verifica è preparato, controllato sui pixel di training e sigillato"*. Non ammesso: "il modello generalizza", "benchmark indipendente", "cross-scroll", "il modello funziona", e qualunque numero held-out di w029.

---

## 6. Verifica finale

Esecuzione completata quando, nell'ordine, sul portatile:

```powershell
python scripts/e02_inventory.py --check configs/e02/ink9um_inventory.json       # atteso: identico
python -m pytest tests/test_e02_metrics.py -q                                     # atteso: tutti passati
python scripts/build_e02_notebooks.py; git status --short kaggle/                 # atteso: nessun output
python scripts/kaggle_e02.py output infer-46527-seed42                            # atteso: "differenze: 0" (idem w016, w029)
Get-ChildItem runs\E02-R01\metrics\*.json | Measure-Object                        # atteso: ≥ 3 file (seed 42): w016 e 0814 con held+train, w029 solo train
Select-String -Path runs\E02-R01\metrics\pherc1667-w029_*.json -Pattern '"held"'  # atteso: nessun output (sigillo M6)
git ls-files | Select-String -Pattern '\.(tif|tiff|pth|zarr|tar)$'                # atteso: nessun output
git status --short                                                                # atteso: solo i file di §3
```

E02 superato quando, in più, i criteri A–C di §5 sono soddisfatti per i tre segmenti e la revisione R3 è chiusa con finding classificati.

---

## 7. Se il piano è sbagliato

1. **Fermati.** Non improvvisare: non cambiare step o seed "per vedere", non generare maschere proprie, non passare a `main` di villa, non modificare `prepare_9um_isotropic_input.py`, non allargare la finestra Z, non rilanciare dopo un timeout.
2. Annota cosa hai trovato e a quale passo.
3. Conserva log e output parziali; esegui comunque i passi di persistenza per quanto esiste.
4. Spegni la GPU. Segnala. Il piano viene corretto in un nuovo commit; un nuovo tentativo scientifico è `E02-R02`.

Arresto obbligatorio: un'asserzione dell'inventario; conteggi delle label diversi; una versione di `requirements-cpu.txt` non installabile; `torch` che cambia versione; hash diverso; input poolato non montato o con hash diverso in un run GPU; forma dell'input poolato diversa dalla label; `held ∧ train ≠ ∅`; orientamento fallito; indici diversi da 2–18 (o 6–22 per il nativo); `exit_code ≠ 0` o timeout; disaccordo con R02 > 0,10 su un confronto ammesso; lettura dei pixel held-out di w029 prima di E05; spazio oltre 15 GB su Kaggle o 5 GB sul portatile; due writer sugli stessi percorsi; serve una spesa, un invito o un'azione esterna.

---

## 8. Fuori perimetro

Anche se sembrano utili o ovvie, **non** fare in questo lavoro:

- confrontare step, finestre Z, `--tta-mirror`, `--direction both`, due GPU, `torch.compile`; scegliere lo step "migliore";
- generare maschere di validazione nostre sui 26 segmenti senza maschera (utile solo se si riaddestra);
- riaddestrare o fare fine-tuning; misurare il cross-scroll;
- usare le predizioni ufficiali pubblicate (`ink-detection/` su S3) come riferimento: sono output di modelli, non label;
- calcolare DRD o pseudo-F-measure;
- decidere lo stadio su cui investire, il premio o il rotolo;
- coinvolgere Francesco; inviare segnalazioni a monte (villa #1547, chiavi del contratto) senza decisione di Matteo;
- installare ScrollScout, VC3D o `vesuvius[models]`.

Se ne emergono altre: **annotarle, non farle.**

---

## 9. Compiti del socio (branch `e02-socio`, da confermare da Matteo)

Percorsi posseduti dal socio: `docs/reports/2026-09-XX-e02-socio-*.md` e `runs/` (ignorata). Nessun altro file. Fusione in `main` decisa da Matteo dopo revisione read-only.

| ID | Compito | Perché è utile | Costo |
|---|---|---|---|
| S1 | **Audit geometrico indipendente delle tre maschere** sul Mac: scaricare le tre label dal bucket (stesso script del passo 2), eseguire `scripts/e02_metrics.py --geometry --patch 128` (solo strati e regioni, senza predizione) e confrontare con la tabella di R02 docs/17 (w016: 3 regioni, 175.222 px held-out, 58,6 % a distanza < 128 px dal training; 0814: 1 regione, 161.051 px, 45,0 %; w029: 8 regioni, 382.353 px, 23,2 %) e con i numeri di Matteo | Replica (L3) di un risultato esterno (L1) da parte di un secondo operatore su un'altra macchina; se i numeri divergono, il metro ha un problema prima di spendere GPU. È geometria delle maschere: non legge predizioni, quindi non viola il sigillo di w029 | CPU, ≈5 MB di rete, meno di un'ora |
| S2 | **Pooling indipendente di `pherc0814-46527`** sul Mac con `uv run` dal checkout di villa al commit congelato: `prepare_9um_isotropic_input.py <URL> pooled.zarr --level 2 --workers 4`; tree-SHA-256 dell'albero zarr e confronto con quello del run Kaggle `prep-46527` | Verifica che l'input del metro sia identico fra piattaforme (media e arrotondamento in `float32`): se differisce, va dichiarata una tolleranza | CPU, ≈0,8 GB di rete, ≈1 GB di disco |
| S3 | **Differito** (revisione R1, finding 7): un run GPU nell'account del socio richiederebbe label, input poolato ed esito del seed 42 pubblicati come dataset privati nel suo namespace, cioè un piccolo piano a sé. Si attiva solo se la quota di Matteo non basta (stima E02: meno di un'ora su 30 settimanali) | — | — |

S1 e S2 possono partire appena il passo 3 è committato. Il socio non vede i numeri della baseline prima di consegnare S1 e S2.

---

## 10. Revisioni Codex e congelamento

- **R1 — piano** (prima dell'esecuzione): `/codex:adversarial-review --wait` sul file di questo piano non ancora committato, con focus: "trova ciò che renderebbe il metro non valido o non riproducibile: pixel di training scambiati per held-out, offset Z, nomi dei segmenti, ordine dei passi, condizioni di arresto mancanti, budget". Finding classificati nel piano stesso (sezione *Revisione R1*, sotto) e piano congelato in un commit `docs: freeze E02 plan (R01)`.
- **R2 — codice** (prima dei run GPU): `/codex:review --wait` sul diff di `scripts/e02_inventory.py`, `scripts/e02_metrics.py`, `tests/test_e02_metrics.py`, `scripts/build_e02_notebooks.py`.
- **R3 — esito** (prima del congelamento del manifest): §4 passo 9.

Per ogni revisione registrare: modello ed effort effettivi riportati dal plugin, durata, finding per severità, accettati/rifiutati/differiti, correzioni materiali. Consumo: variazione dell'usage meter in punti percentuali, se visibile; mai "token".

### Revisione R1 (6 settembre 2026)

- **Canale:** plugin `codex@openai-codex` 1.0.6, comando `adversarial-review` sull'albero di lavoro (piano + `requirements-cpu.txt`), sola lettura; CLI Codex 0.153.4, login ChatGPT. Modello ed effort: `gpt-6-astra` / `high` dalla configurazione utente; Codex ha dichiarato "GPT-6" e di aver caricato `AGENTS.md`, `docs/07`, `docs/03` e `claude-orchestra-codex.md`. Durata ≈ 5 minuti (20:53:19–20:58:42 UTC, dal log del job). Nessun accesso di rete dal sandbox (le fonti GitHub congelate non erano raggiungibili da Codex: verificate da Claude).
- **Verdetto Codex:** piano da correggere prima dell'esecuzione. **8 finding: 2 P1, 6 P2. Accettati 8** (uno con modifica), rifiutati 0, differiti 0.

| # | Sev. | Finding (sintesi) | Esito | Correzione |
|---|---|---|---|---|
| 1 | P1 | Il passo 7 leggeva i pixel held-out di w029, il set riservato a E05 | accettato | w029: inferenza eseguita, controlli su identità e pixel di training, TIFF sigillato con hash; metriche held-out rinviate a E05; §1, §2 decisioni, passi 5, 7, 8, §5 B–E, §6, §7 |
| 2 | P1 | Il test di orientamento attendeva 0 dove l'AUROC di E00 dà 1/3 (pareggi) | accettato | test corretto con tolleranza su 1/3; asserzioni su originale e `orientamento_ok` conservate |
| 3 | P2 | Soglia di best-F1 non univoca in caso di pareggio | accettato | comparatore `score >= t` e regola "soglia più bassa fra i massimi" congelati; test sul valore esatto (31); stessa regola per `threshold_dev` |
| 4 | P2 | "Patch" indicava due distanze diverse (128 vs 64 px) | accettato | patch = 128 px sulla scala delle label, strati `< 128` e `< 256`, confine escluso; §2.3, passo 3, §5 B, S1 allineati |
| 5 | P2 | Il passo 2 usava uno script introdotto al passo 4 | accettato | `build_label_dataset.py` scritto e verificato al passo 2; il passo 4 pubblica soltanto |
| 6 | P2 | Ripiego di pooling dentro la sessione GPU, con timeout superiore alla sessione | accettato | nessun pooling in sessione GPU; input e hash verificati come prerequisito del `push`; arresto immediato se il mount manca |
| 7 | P2 | S3 nell'account del socio senza i dataset privati necessari | accettato con modifica | S3 differito: richiede un piano a sé; si attiva solo se la quota non basta |
| 8 | P2 | Ripiego d'installazione che lascia `requirements-cpu.txt` diverso dall'ambiente | accettato | arresto e nuova revisione del file; installazione già verificata il 6 settembre 2026 |

- **Secondo giro (verifica di chiusura, 21:04–21:06 UTC, ≈2 minuti, stesso canale):** F2–F8 **chiusi**; F1 **riaperto** con un'osservazione nuova e corretta: il test di orientamento di E00 indicizza la predizione con la maschera *trasformata*, che può cadere su coordinate held-out; Codex lo ha dimostrato con un controesempio sintetico (modificando solo predizioni held-out, `flipX` passava da 0,5 a 1). **Accettato:** in E02 ogni variante usa l'intersezione fra maschera di training originale e trasformata (passo 3, M3), con il test `test_held_out_pixels_are_never_read`. Claude ha rieseguito il controesempio con la funzione AUROC di E00: con la regola E00 le AUROC trasformate cambiano al variare dei soli pixel held-out; con la regola E02 restano identiche. Nessun nuovo finding P0–P1. Terzo giro non eseguito: la correzione è una definizione in una funzione, verificata con il test sintetico sopra.
- **Commit di congelamento:** `docs: freeze E02 plan (R01)` (verifica nell'intestazione del piano).

---

## 11. Al termine

- [ ] Esecuzione completata: passi 0–9 eseguiti, **oppure** stop documentato al passo N con causa
- [ ] Criteri A–C di §5 verificati per i tre segmenti; §5 D compilato
- [ ] Scheda, manifest, `configs/e02/*.json` scritti; output in `runs/E02-R01/` con `differenze: 0`
- [ ] Revisioni R1–R3 registrate con finding classificati
- [ ] Documenti canonici aggiornati; commit e push del lavoro verificato
- [ ] Fuori perimetro emersi: annotati; segnalazioni a monte: solo su decisione di Matteo
