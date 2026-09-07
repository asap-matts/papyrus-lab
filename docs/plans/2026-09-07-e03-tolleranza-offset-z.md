# E03 — tolleranza di `ink_9um` all'offset Z: curva AUROC(offset) sui pixel held-out di sviluppo

**Scritto da:** Claude Code (writer, su incarico di Matteo) · **Esecutore previsto:** Claude Code dal portatile di Matteo (script, test, metriche, CPU) e via API Kaggle (pooling CPU e inferenze T4), con un "vai" di Matteo per ogni run GPU · **Revisori (R1 piano, R2 codice, R3 esito):** Codex, sola lettura, plugin `codex@openai-codex`, modello `gpt-5.6-sol`, effort `high` (decisione di Matteo del 7 settembre 2026: Sol anche per R1) · **Socio:** compiti indipendenti S1–S3 su branch `e03-socio` (§9), eseguiti con Codex sul Mac
**Data:** 2026-09-07 · **Branch PapyrusLab:** `main` · **Commit di partenza:** `b581271` · **Branch villa:** `merge-ink-pipelines` @ `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e` (invariato da E00)
**Stato:** bozza in revisione R1; il piano si congela in un commit dedicato `docs: freeze E03 plan (R01)` dopo la classificazione dei finding.

> Verifica prima di iniziare, dalla cartella del repository: `git status --short` deve essere vuoto e `git log -1 --format=%s` deve restituire esattamente `docs: freeze E03 plan (R01)`. Se una delle due condizioni non vale, **fermati**: stai leggendo un piano non congelato o uno stato diverso.

---

## 1. Obiettivo

Alla fine deve essere vero **uno** dei due esiti:

- **E03 completato:** esistono nel repository una scheda e un manifest revisionati, e i tre rapporti indipendenti del socio integrati, che riportano, per i due segmenti di sviluppo (`pherc0139-w016`, `pherc0814-46527`) e per i due modelli (seed 42 e 43, step 75000), la **curva AUROC(offset)** sui pixel held-out per offset di {−5, −3, −2, 0, +2, +3, +5} slice, con i valori per strato di distanza e per regione, la F1 alla soglia congelata τ\* = 91, la concordanza di Spearman con la finestra centrale, la **tolleranza** stimata per seed e per verso secondo la definizione di §5, e i due **controlli a costo zero** (media dei seed, media delle finestre −2/+2) confrontati con la finestra centrale dello stesso seed. Nessun numero è stato usato per scegliere una finestra; il segmento di verifica `pherc1667-w029` non è stato toccato.
- **E03 interrotto, documentato:** log, output parziali e causa dell'arresto conservati e scritti nella scheda, con la prossima prova proposta.

E03 non decide nulla da solo: fornisce i numeri con cui Matteo applica le condizioni di ripensamento scritte nel [documento di decisione](../decisions/2026-09-06-dove-investire.md).

---

## 2. Contesto necessario

Chi esegue non ha letto la conversazione da cui nasce questo piano. La procedura che governa il lavoro è [docs/07](../07-procedura-operativa.md); la decisione che questo piano attua è nella sezione "Decisione" del [documento di decisione](../decisions/2026-09-06-dove-investire.md); i fatti ufficiali sono nella [nota di intake](../reports/2026-09-07-intake-dove-investire.md). La baseline è il metro di E02 ([piano](2026-09-06-e02-costruire-il-metro.md), [scheda](../reports/2026-09-07-e02-r01.md), [manifest](../reports/2026-09-07-e02-r01-manifest.json)); i termini *surface volume*, *label*, *supervision mask*, *validation mask*, *held-out*, *pooling*, *checkpoint*, *seed* sono definiti lì e in [docs/01](../01-capire-il-processo.md).

Termini nuovi di questo piano. Il **surface volume allineato** dei nostri segmenti è una pila di **21 slice** (fette) ottenuta dal volume a 2,399 µm prendendo 84 piani centrali (indici 13–96 dei 109 disponibili) e facendo la media di 4 piani per slice: ogni slice vale 4 × 2,399 = **9,596 µm**. Il modello guarda **17 slice**: con la finestra di default sceglie gli indici **2–18**, il cui centro (10) è il piano su cui sono annotate le label (`annotation_center_channel: 10`). Un **offset Z di k slice** significa far guardare al modello la finestra centrata su 10 + k invece che su 10, tenendo ferma la label: imita l'errore di chi stima la superficie del foglio k slice (≈ 9,6·k µm) troppo in alto o in basso. La **curva di tolleranza** è l'AUROC sui pixel held-out in funzione di k; la **tolleranza** è il più piccolo |k| campionato al quale la perdita media supera la soglia di §5. Un **offset uniforme** sposta tutte le colonne del segmento della stessa quantità: è un'approssimazione dell'errore reale di superficie, che è locale e ondulato, e va dichiarata come tale.

### 2.1 Fatti verificati (7 settembre 2026)

| Fatto | Fonte | Livello |
|---|---|---|
| Il training di `ink_9um` fa *jitter* della finestra di 17 slice dentro le 21: "makes the models handle small offsets reasonably well, but larger ones can still throw them off"; il model card suggerisce anche la media di predizioni su finestre Z vicine come ensemble | model card, sezioni *Models* e *Tips* ([intake §4](../reports/2026-09-07-intake-dove-investire.md)) | L0 |
| `infer.py` accetta `--layer-start S --layer-end E` e usa gli indici `[S, E)` (estremo superiore escluso); se sono più di 17 ne ritaglia i 17 centrali; scrive nel log `Selected source layer indices=[...]` | `ink-detection/koine_machines/inference/infer.py` @ `3ea17f5`, righe 359–380 e 1655–1672 | L2 |
| Lo script di pooling ufficiale `prepare_9um_isotropic_input.py` non ha alcun parametro per spostare la finestra sorgente: `centered_slice(109, 84)` dà sempre `[13, 97)`; media in `float32`, `np.rint`, `uint8`; chunk `(21, 128, 128)`, Blosc zstd livello 5 con bitshuffle; attributi `format`, `source`, `source_level`, `source_shape_zyx`, `source_z_slice`, `z_pool`. SHA-256 dello script `3afff4f2…` (identico a quello registrato in E02) | `ink-detection/scripts/prepare_9um_isotropic_input.py` @ `3ea17f5` (113 righe) | L2 |
| Gli input poolati ufficiali dei due segmenti di sviluppo esistono come dataset Kaggle privati con impronta verificata su tre macchine (0814) e attributi verificati (w016): `papyruslab-e02-input-46527` (`bc742343…`), `papyruslab-e02-input-w016` (`7c0c7006…`); le label sono in `papyruslab-e02-r01-labels` | `configs/e02/datasets.json`, scheda E02 | L3 |
| I TIFF di E02 dei due segmenti di sviluppo, seed 42 e 43, sono sul portatile in `runs/E02-R01/infer-*/…/e02/out/` con SHA-256 nel manifest (`6d026507…`, `cc2002cc…`, `7208daca…`, `975d56f4…`) | manifest E02, `runs/` locale | L3 |
| Baseline sui pixel held-out (seed 42 / 43): w016 AUROC 0,774 / 0,936, 0814 0,874 / 0,863; costi: sessione GPU 2 min 30 s–3 min 25 s per 0814, 8 min 30 s–9 min 19 s per w016; pooling su Kaggle CPU 6 s (0814) e 38 s (w016) | scheda E02 | L3 |

### 2.2 La matrice degli offset

Il centro della finestra ufficiale è il piano sorgente 55 (13 + 8·4 + 34). Ogni riga sotto è verificata aritmeticamente e va asserita dal codice (passo 1).

| Offset k (slice) | Input poolato | Finestra sorgente del pooling `source_z_slice` | Argomenti di `infer.py` | Indici attesi nel log | Piani sorgente visti dal modello | Centro | µm |
|---:|---|---|---|---|---|---:|---:|
| −5 | spostato −3 | `[1, 85)` | `--layer-start 0 --layer-end 17` | 0…16 | `[1, 69)` | 35 | −48,0 |
| −3 | spostato −3 | `[1, 85)` | nessuno (default 2–18) | 2…18 | `[9, 77)` | 43 | −28,8 |
| −2 | ufficiale | `[13, 97)` | `--layer-start 0 --layer-end 17` | 0…16 | `[13, 81)` | 47 | −19,2 |
| 0 | ufficiale | `[13, 97)` | nessuno | 2…18 | `[21, 89)` | 55 | 0 |
| +2 | ufficiale | `[13, 97)` | `--layer-start 4 --layer-end 21` | 4…20 | `[29, 97)` | 63 | +19,2 |
| +3 | spostato +3 | `[25, 109)` | nessuno | 2…18 | `[33, 101)` | 67 | +28,8 |
| +5 | spostato +3 | `[25, 109)` | `--layer-start 4 --layer-end 21` | 4…20 | `[41, 109)` | 75 | +48,0 |

Lo spostamento del pooling è limitato a ±3 slice (12 piani) dai 109 piani disponibili (`[1, 85)` e `[25, 109)` sono gli estremi che restano dentro `[0, 109)`); combinando pooling spostato e finestra spostata nella stessa direzione si arriva a ±5. Gli offset ±1 e ±4 non si misurano (decisione di Matteo: sei offset, due tappe).

### Decisioni già prese, e perché

- **Stadio e disegno sono decisi da Matteo (7 settembre 2026) e non si riaprono in E03** — offset {−5, −3, −2, +2, +3, +5}, due segmenti di sviluppo, seed 42 e 43, due tappe, due controlli a costo zero, risultato = curva e tolleranza. Motivazioni nel documento di decisione. Chi esegue non aggiunge offset, seed, step, direzioni o TTA "per completezza".
- **Tappa 1 = ±2 sugli input ufficiali (8 inferenze), poi gate, poi tappa 2 = ±3 e ±5 (16 inferenze)** — ±2 è l'intervallo del jitter di training, quindi la parte in cui ci si aspetta una curva piatta; farla per prima costa un'ora di GPU e collauda l'intera catena E03 (argomenti di finestra, controlli del log, metriche) prima dei pooling spostati. Se la tappa 1 mostra un problema tecnico, ci si ferma avendo speso poco.
- **Pooling spostato con uno script nostro (`scripts/e03_pool_shifted.py`) che riproduce byte per byte quello ufficiale, non con una modifica di villa** — il codice di villa è congelato (E00–E02) e non si modifica; lo script ufficiale non ha il parametro. La riproduzione è **dimostrata**, non presunta: a spostamento zero lo script deve produrre per 0814 esattamente l'albero zarr con impronta `bc742343…`, e per ogni input spostato ogni slice deve coincidere esattamente con la slice corrispondente dell'input ufficiale (stessi piani sorgente, stessa aritmetica). Senza queste due uguaglianze non si spende GPU sugli input spostati.
- **I piani sorgente nuovi (1–12 e 97–108) hanno un'identità congelata prima del pooling spostato** (revisione R1, finding 2) — l'impronta `bc742343…` e l'uguaglianza slice a slice provano soltanto i piani 13–96, cioè le 18 slice condivise; le tre slice nuove di ogni input spostato vengono dai piani ai bordi, che nessun artefatto congelato copre. Un aggiornamento o una corruzione limitata a quei piani passerebbe ogni controllo e verrebbe poi "consacrata" dall'impronta del nuovo output. Poiché al livello 2 i chunk sono `[109, 128, 128]` (tutta la profondità in un chunk: leggere 84 piani ne trasferisce comunque 109), il manifest di sorgente si calcola **senza traffico aggiuntivo** durante il primo pooling: passo 2b.
- **Ogni variante si confronta con la finestra centrale dello stesso seed, mai fra seed** — il seed 43 batte il 42 di 0,22 di F1 su w016 a input identico: un confronto incrociato attribuirebbe all'offset ciò che è del modello (scheda E02; decisione).
- **Ogni punto della curva porta con sé la propria identità, e la curva rifiuta una matrice incompleta o ambigua** (revisione R1, finding 3) — i report di `e02_metrics` non registrano seed e offset: un file rinominato `zm3` invece di `zp3`, o una copia, invertirebbe un verso senza che nulla se ne accorga, e il ricalcolo in cieco del socio ripeterebbe lo stesso errore perché parte dagli stessi file. Ogni report di E03 contiene quindi un blocco `e03_point` con `segment`, `seed`, `k` (intero con segno), `sha256_pred`, `input_tree_sha256`, `source_z_slice`, `layer_indices` (letti dal log del run) e `run_id`; `e03_curve.py` pretende **esattamente** il prodotto 2 segmenti × 2 seed × 7 offset, chiavi uniche, coerenza fra nome del file e contenuto, e coerenza fra `k`, `source_z_slice` e `layer_indices` secondo `configs/e03/offsets.json`. Qualunque scostamento è un arresto, non un avviso.
- **Il sigillo di w029 è protetto dal contenuto, non dal nome** (revisione R1, finding 4) — il caricatore di E02 deriva l'identità del segmento dal nome della cartella: una cartella, un collegamento o un report rinominato potrebbe far aprire la maschera di validazione sigillata, e il solo accesso ai suoi pixel violerebbe il sigillo. In E03, prima di aprire qualunque `validation_mask`, si verifica che la cartella delle label appartenga a una **lista bianca** di due voci con l'impronta congelata: `pherc0139-w016` → `a62d3e0e…`, `pherc0814-46527` → `56592368…`; qualunque altra cartella, o un'impronta diversa, ferma lo script prima della lettura. La verifica finale ispeziona il **contenuto** dei report (campo `e03_point.segment` e impronte), non soltanto i nomi dei file.
- **Metrica primaria AUROC per segmento e per seed; nessuna selezione dell'offset "migliore"** — con quattro combinazioni seed × segmento e sei offset se ne troverebbe sempre uno vincente per caso. Il risultato è la curva intera, pubblicata per tutte e quattro le combinazioni; la tolleranza è una lettura della curva con una regola fissata prima (§5), non una scelta.
- **Un offset diverso da zero che vince ovunque è un segnale di allarme, non un risultato da adottare** — significherebbe che il piano annotato non coincide con il centro reale del segnale (label o pooling disallineati): si ferma tutto e si indaga (§7).
- **I controlli a costo zero si calcolano sui TIFF grezzi conservando i mezzi punti** — la media di due `uint8` produce mezzi interi; arrotondare prima della valutazione cambierebbe l'ordinamento dei pixel. Lo script `scripts/e03_metrics.py` lavora sulla **somma** (`uint16`, 0–510) e riporta le soglie in unità di media (t/2); la soglia congelata τ\* = 91 sulla media corrisponde a `somma ≥ 182`. `scripts/e02_metrics.py` resta congelato alla versione 1.2 e viene importato **solo** per le funzioni indipendenti dal numero di livelli (`auroc`, `load_masks`, `centre_plane`, `read_prediction`, `strata`, `regions`, `annotated_regions`, `trivial_floor`).
- **Sweep, `best_f1` e `at_threshold` a 511 livelli sono riscritti in E03, non importati** (revisione R1, finding 1) — gli helper congelati di E02 sono legati a 256 livelli: `sweep` ha `assert pos.shape == (256,)` e `at_threshold` fa `np.clip(int(t), 0, 255)`, quindi con un ottimo oltre 255 riporterebbe la soglia chiesta ma le statistiche dell'indice 255. Verificato con un controesempio eseguito il 7 settembre 2026: `at_threshold(sw, 300)` restituisce `threshold: 255` con i conteggi di 255. Il caso è reale, non teorico: sui pixel di training di w016 la soglia E02 di best-F1 è 135, che sulla somma corrisponde a 269. E03 definisce quindi `sweep_n(pos_hist, neg_hist, levels)`, `best_f1_n(sw)` e `at_threshold_n(sw, t)` senza alcun troncamento, con la stessa regola dei pareggi (soglia più bassa fra i massimi) e la stessa formula di F1 in un solo quoziente.
- **Il gate di orientamento (regola M3 di E02, trasformate dentro il bounding box) è bloccante solo per |k| = 2, cioè sugli input ufficiali; per |k| ∈ {3, 5} è registrato, non bloccante** — l'orientamento verifica l'allineamento XY dell'input, che gli offset Z non toccano. Per gli input spostati l'allineamento XY è **dimostrato** dall'uguaglianza esatta, slice per slice, con l'input ufficiale (passo 8): una prova più forte del gate. Inoltre, con il segnale degradato dall'offset, l'originale potrebbe non battere più strettamente le trasformate anche con input corretto: a ±3 e ±5 un orientamento non superato è un **risultato** (segnale perso), non un errore, e va scritto nella scheda.
- **Le misure sui pixel di training si registrano come curva secondaria** — mostrano quanto rapidamente il modello perde anche i pixel memorizzati: è informativo, ma non è la metrica della decisione.
- **Un solo run GPU per volta, con download e metriche prima del successivo** — la deviazione 7 di E02 (run avviati in parallelo prima dei controlli) non si ripete. Ordine: prima 0814 (3 minuti a run), poi w016 (9 minuti), dentro ogni tappa.
- **Baseline identica a E02** — villa `3ea17f5`, `ink_9um` @ `7109667…`, checkpoint `hybrid_3d2d-seed42/step-075000.pth` (`e635558a…`) e `seed43/step-075000.pth` (`2aeaa85a…`), `--overlap 0.5 --blend-mode hann --no-compile --gpus 0 --batch-size 1`, direzione `forward`, installazione `--no-deps` sul Python di sistema di Kaggle. Cambia **solo** la finestra Z (argomenti e/o input spostato). Le inferenze a offset 0 non si rifanno: i TIFF di E02 sono il punto zero della curva.
- **Le condizioni di ripensamento le applica Matteo, dopo la scheda** — il piano produce numeri e li confronta con le regole di §5; le conseguenze (E04, riapertura dello stadio) sono nel documento di decisione e non si anticipano nella scheda.
- **Progress Prize:** si lavora come se la scadenza fosse il 30 settembre 2026, ma la candidatura si decide dopo la revisione R3; nessuna scorciatoia sulla revisione. La novità della curva va **verificata** dal socio (S1) prima di essere rivendicata: l'assenza dal catalogo non dimostra l'assenza di lavoro pubblico (revisione Codex della decisione, finding 2).
- **Tre revisioni Codex, come in E02, tutte con `gpt-5.6-sol`, effort `high`** — R1 sul piano (questo documento, prima del congelamento), R2 sul codice (prima di qualunque run GPU), R3 sull'esito (prima del consolidamento). Regola di Matteo del 7 settembre 2026: Sol per default, Astra solo per compiti che richiedono ragionamento molto avanzato; per E03 Matteo ha scelto Sol anche per R1. Tutte in sola lettura; il modello si passa esplicitamente al runtime (`--model`), perché il default della configurazione utente resta Astra.

### Vincoli

- Niente dati, checkpoint, TIFF, zarr o tar in Git (`.gitignore` li copre). In Git vanno: script, test, configurazioni piccole, notebook generati senza output, scheda, manifest e i **JSON delle metriche per run** (piccoli, servono al socio per S3).
- Non modificare il codice di villa, gli script e i notebook di E00–E02, `scripts/e02_metrics.py`, `configs/e02/*`, `docs/07`, la sezione "Decisione" del documento di decisione (si aggiorna solo "Aggiornamenti").
- `pherc1667-w029`: nessun run, nessuna lettura, nessun pooling. Il generatore rifiuta il segmento.
- Tetti: **4 ore di quota GPU** complessive per E03 (stima 2,4 h), 30 minuti di inferenza per run (timeout interno), 60 minuti di sessione GPU; 4 ore per run CPU di pooling; 15 GB su Kaggle, 5 GB sul portatile (gli input spostati di w016 non si scaricano in locale: ≈ 0,7 GB ciascuno, si verificano su Kaggle); nessuna spesa. Al superamento di un tetto ci si ferma.
- Ogni cella di notebook che può fermare il run lo fa con un'asserzione che dice dove e perché.
- Un solo writer per cartella: Claude scrive su `main`, il socio solo sui percorsi di §9 nel branch `e03-socio`.

---

## 3. Perimetro

### File da creare o modificare

| File | Cosa fare |
|---|---|
| `docs/plans/2026-09-07-e03-tolleranza-offset-z.md` | Questo piano; congelato dopo R1 |
| `docs/plans/2026-09-07-e03-compiti-socio.md`, `docs/plans/e03-prompt-codex-socio.md`, `scripts/e03_bootstrap_mac.sh` | Piano eseguibile per il socio (procedura unica S1 → S2 → S3), prompt per il suo Codex e script di avvio sul Mac; scritti insieme a questo piano, con il campo "Commit di partenza" compilato al passo 10 |
| `configs/e03/offsets.json` | La matrice di §2.2: per ogni offset, spostamento del pooling, `source_z_slice`, argomenti di `infer.py`, indici attesi, centro, µm |
| `configs/e03/datasets.json` | Dataset Kaggle di E03: input spostati (`papyruslab-e03-input-<short>-zm3` / `-zp3`) con impronte; riferimenti ai dataset E02 riusati (label, input ufficiali) |
| `scripts/e03_pool_shifted.py` | Pooling ufficiale riprodotto con parametro `--z-start` (default 13 = ufficiale); attributi identici a spostamento zero; a spostamento ≠ 0 aggiunge `e03_z_shift_slices` e `format` con suffisso `+zshift`; `--source-manifest` / `--verify-source-manifest` per l'identità dei 109 piani sorgente (passo 2b) |
| `configs/e03/source_manifest.json` | Impronte per tile dei blocchi sorgente a profondità piena dei due segmenti di sviluppo (passo 2b) |
| `tests/test_e03_pool_shifted.py` | Aritmetica della finestra, uguaglianza con la formula ufficiale su array sintetici, uguaglianza slice a slice fra spostato e non spostato, rifiuto di spostamenti fuori intervallo, manifest deterministico e rifiuto di una sorgente alterata **dentro e fuori** l'intervallo 13–96 |
| `scripts/e03_metrics.py` | Metriche su medie di due TIFF (somma `uint16`, sweep a 511 livelli, soglie in unità di media) e Spearman fra due TIFF sui pixel held-out; importa da `e02_metrics` |
| `tests/test_e03_metrics.py` | La media di un TIFF con se stesso riproduce il report E02 (AUROC, best-F1, F1 a 91) al decimale; casi sintetici |
| `scripts/e03_curve.py` | Dai JSON delle metriche: **validazione della matrice** (esattamente 2 segmenti × 2 seed × 7 offset, chiavi uniche, `e03_point` coerente con nome del file, con `configs/e03/offsets.json` e con le impronte), poi tabella AUROC(offset), Δ rispetto allo zero, tolleranza per seed e verso (§5), controlli; output JSON + tabella Markdown. Una matrice incompleta, duplicata o incoerente è un errore, non un avviso |
| `tests/test_e03_curve.py` | Tolleranza su curve sintetiche (piatta, decrescente, asimmetrica, anomala); **rifiuto** di un punto mancante, di un duplicato, di un file il cui `e03_point.k` non corrisponde al nome, e di un segno invertito (`zm3` con `k = +3`) |
| `scripts/build_e03_notebooks.py` | Generatore dei notebook `prep-<short>-z<m3\|p3>` (CPU) e `infer-<short>-s<seed>-z<m5\|m3\|m2\|p2\|p3\|p5>` (T4); **importa** le celle di `build_e02_notebooks.py` e aggiunge finestra Z, indici attesi, input spostati, pooling inlineato |
| `scripts/kaggle_e03.py` | Pilota: `push`, `status`, `wait`, `output`, `publish-input <short> <zm3\|zp3>`, `budget` (minuti GPU consumati dai run scaricati); rifiuta `push` senza hash e senza esito verificato del run precedente |
| `kaggle/e03-r01-*/` | Notebook generati e `kernel-metadata.json` — **non modificare a mano** |
| `docs/reports/2026-09-XX-e03-r01.md`, `docs/reports/2026-09-XX-e03-r01-manifest.json` | Scheda (da `docs/templates/esperimento.md`) e manifest |
| `docs/reports/e03-r01/metrics/*.json` | Report `e02_metrics` (run) ed `e03_metrics` (controlli) per ogni TIFF, più `curve.json`: piccoli, committati per S3. **Nomi congelati** (servono al ricalcolo in cieco del socio): `<seg>_s<seed>_z<k>.json` con `k` in `m5, m3, m2, 0, p2, p3, p5` (28 file: 4 punti zero + 24 run); `<seg>_s<seed>_z<k>_spearman_z0.json` (24); `<seg>_seedmean.json` (2) e `<seg>_seedmean_spearman.json` (2); `<seg>_s<seed>_zmean_m2p2.json` (4); `curve.json` (1). Totale 61 |
| `docs/roadmap.md`, `README.md`, `AGENTS.md`, `docs/decisions/2026-09-06-dove-investire.md` (solo "Aggiornamenti"), `docs/06-ricerca-community.md` (se S1 trova fonti) | Consolidamento finale |

Fuori da Git: `runs/E03-R01/<run>/<timestamp>/` sul portatile; su Kaggle `WORK=/kaggle/working/e03` e `HEAVY=/tmp/e03`; dataset Kaggle privati `matteopontesilli/papyruslab-e03-input-<short>-<zm3|zp3>`.

### File da NON toccare

| File | Perché |
|---|---|
| Codice di villa | Congelato: la riproducibilità dipende dal commit dichiarato |
| `scripts/build_e02_notebooks.py`, `scripts/kaggle_e02.py`, `scripts/e02_metrics.py`, `scripts/e02_manifest.py`, `kaggle/e02-r01-*`, `configs/e02/*` | Artefatti congelati di E02: E03 li importa o li legge, non li cambia |
| `docs/07-procedura-operativa.md`, sezione "Decisione" del documento di decisione | Congelati; una correzione è un commit separato con motivazione |
| Qualunque cosa riguardi `pherc1667-w029` | Sigillato fino a E05 |
| `.gitignore` | Copre già tutto |

---

## 4. Passi

### Come si esegue

Passi 0–5 locali (portatile, CPU); passi 6–12 con l'API Kaggle tramite `scripts/kaggle_e03.py`, stesso schema di E02 (notebook generati, asserzioni, output scaricati per versione e verificati con `SHA256SUMS`). **Fanno fede questo piano congelato e `configs/e03/offsets.json`, non il generatore** (revisione R1, finding 7): il generatore ha autorità soltanto sull'espansione meccanica già verificata (nomi dei file, sostituzione dei segnaposto, ordine delle celle). Qualunque divergenza *semantica* fra generatore e piano — finestra Z, indici attesi, comandi, gate, insiemi di pixel — è un arresto e richiede una nuova revisione del piano, non un adeguamento silenzioso del testo. ID del run: `E03-R01`; un tentativo fallito per causa tecnica conserva l'ID con numero di tentativo crescente (massimo due tentativi per run, poi stop); una modifica scientifica crea `E03-R02` con piano corretto.

| Run Kaggle | Acceleratore | Cosa fa | Quanti |
|---|---|---|---:|
| `infer-<short>-s<seed>-z<m2\|p2>` | T4 | inferenza sull'input ufficiale con finestra spostata | 8 (tappa 1) |
| `prep-<short>-z<m3\|p3>` | nessuno | pooling spostato con lo script E03 inlineato, verifica slice a slice contro l'input ufficiale montato, tar + hash | 4 |
| `infer-<short>-s<seed>-z<m3\|p3>` | T4 | inferenza sull'input spostato, finestra di default | 8 (tappa 2) |
| `infer-<short>-s<seed>-z<m5\|p5>` | T4 | inferenza sull'input spostato, finestra spostata nello stesso verso | 8 (tappa 2) |

Sul portatile, Git Bash, dalla cartella del repository (`.venv` già creato in E02):

```bash
./.venv/Scripts/python.exe -m pytest tests/test_e03_*.py -q                          # passi 1-4
./.venv/Scripts/python.exe scripts/e03_pool_shifted.py "<SRC_0814>" runs/E03-R01/local-input/pherc0814-46527_z0.zarr --level 2 --workers 4      # identita' (passo 2)
./.venv/Scripts/python.exe scripts/tree_sha256.py runs/E03-R01/local-input/pherc0814-46527_z0.zarr                                            # atteso: bc742343...
./.venv/Scripts/python.exe scripts/build_e03_notebooks.py                                # passo 5
# --- R2 Codex sul diff, poi STOP: "vai" di Matteo per ogni run GPU ---
./.venv/Scripts/python.exe scripts/kaggle_e03.py push infer-46527-s42-zm2; ... wait; ... output    # passo 6, un run per volta
./.venv/Scripts/python.exe scripts/e02_metrics.py --pred <tif> --labels data/labels/aligned-scrollprizeorg-21slices/pherc0814-46527 --threshold 91 --out docs/reports/e03-r01/metrics/pherc0814-46527_s42_zm2.json
```

### Passo 0 — Base verificata

**Cosa:** commit congelato, ambiente, TIFF di E02, autenticazione Kaggle.
**Come:** `git status --short` vuoto e messaggio dell'ultimo commit = `docs: freeze E03 plan (R01)`; `.venv` importa `numpy, zarr, tifffile, scipy`; i quattro TIFF di E02 dei segmenti di sviluppo esistono in `runs/E02-R01/` e i loro SHA-256 coincidono con il manifest E02 (`6d026507…` 0814 s42, `cc2002cc…` 0814 s43, `7208daca…` w016 s42, `975d56f4…` w016 s43); le label locali dei due segmenti hanno tree-SHA-256 `56592368…` e `a62d3e0e…`; `kaggle kernels list --mine --page-size 3` risponde (token rigenerato da Matteo, come annotato nella roadmap). Registrare `pip freeze` in `runs/E03-R01/env/`.
**Fatto quando:** tutte le impronte coincidono.
**Fermarsi se:** un TIFF manca o ha impronta diversa (ricalcolare dal dataset Kaggle `papyruslab-e02-<short>-seed42-out` per il seed 42; per il seed 43 dal download del run `infer-<short>-seed43`); il commit non coincide; Kaggle non autentica.

### Passo 1 — La matrice degli offset come dato, con test

**Cosa:** `configs/e03/offsets.json` e le funzioni che ne derivano gli argomenti, asserite.
**Come:** il JSON elenca, per `k in [-5, -3, -2, 0, 2, 3, 5]`: `pool_shift_slices` (−3, 0, +3), `source_z_slice` (`[1, 85]`, `[13, 97]`, `[25, 109]`), `layer_start`/`layer_end` (`null` per default), `expected_indices` (lista di 17 interi), `source_planes_seen` (`[a, b)`), `centre_plane`, `micrometres` (k × 9,596). Test in `tests/test_e03_pool_shifted.py`:

```python
def test_offset_matrix_is_consistent():
    for row in OFFSETS:
        z0, z1 = row["source_z_slice"]; assert z1 - z0 == 84 and 0 <= z0 and z1 <= 109
        s = 2 if row["layer_start"] is None else row["layer_start"]
        idx = list(range(s, s + 17)); assert idx == row["expected_indices"] and 0 <= idx[0] and idx[-1] <= 20
        seen = [z0 + 4 * idx[0], z0 + 4 * (idx[-1] + 1)]; assert seen == row["source_planes_seen"]
        assert (seen[0] + seen[1]) // 2 == 55 + 4 * row["k"] == row["centre_plane"]
        assert abs(row["micrometres"] - row["k"] * 9.596) < 1e-9
```

**Fatto quando:** il test passa e la tabella stampata dallo script coincide con §2.2 riga per riga.
**Fermarsi se:** una riga non coincide: correggere il piano prima di continuare.

### Passo 2 — Pooling spostato: riproduzione dimostrata dell'ufficiale

**Cosa:** `scripts/e03_pool_shifted.py`, copia funzionale di `prepare_9um_isotropic_input.py` @ `3ea17f5` con `--z-start N` (default 13), stessi `TILE`, `CHUNK_XY`, compressore, `fill_value`, ordine delle operazioni (`float32`, `mean(axis=1)`, `np.rint`, `uint8`), stessi attributi e stesso ordine delle chiavi a spostamento zero; con spostamento ≠ 0 aggiunge `"e03_z_shift_slices": ±3` e `"format": "level2-zmean4-21slice-v1+zshift"`. Rifiuta `z_start` fuori da `[0, 25]`. Attribuzione nel file: derivato dallo script di villa (licenza del repository villa da riportare nell'intestazione).
**Test (prima del codice):** su un array sintetico `(109, 40, 40)` casuale: (a) a `z_start=13` l'output è uguale a `np.rint(src[13:97].reshape(21,4,40,40).astype(np.float32).mean(1)).astype(np.uint8)`; (b) per `z_start=1`: `out_m3[3:21] == out_0[0:18]` esattamente, e per `z_start=25`: `out_p3[0:18] == out_0[3:21]`; (c) gli attributi a spostamento zero sono esattamente il dizionario ufficiale (chiavi e ordine); (d) `z_start=26` e `z_start=-1` alzano `ValueError`.
**Verifica di identità sui dati reali (CPU locale, ≈ 3 minuti, 0,8 GB di rete):** lo script a spostamento zero su 0814 produce un albero zarr con `tree_sha256 == bc7423431221bf24b247a8ba80d264b0306f816c52b4ecc0d08115a82305ac52` (l'impronta ufficiale, identica su Kaggle, portatile e Mac in E02). Poi `--z-start 1` e `--z-start 25` su 0814 in locale: uguaglianza slice a slice con `runs/E02-R01/local-input/pherc0814-46527_pooled.zarr` (già presente) e impronte annotate in `runs/E03-R01/local-input/*.json`. I dataset Kaggle per la tappa 2 verranno comunque prodotti su Kaggle (passo 8), non caricati dal portatile: il confronto locale/Kaggle delle impronte è un secondo controllo di identità fra piattaforme.
**Fatto quando:** test verdi; impronta a spostamento zero identica; uguaglianza slice a slice vera per ±3.
**Fermarsi se:** l'impronta a spostamento zero differisce (lo script non riproduce l'ufficiale: **non** procedere con input spostati); una slice differisce.

### Passo 2b — Identità congelata dei piani sorgente (revisione R1, finding 2)

**Cosa:** un manifest di contenuto della sorgente che copre **tutti i 109 piani**, non solo i 13–96 usati dal pooling ufficiale, per entrambi i segmenti di sviluppo.
**Come:** `scripts/e03_pool_shifted.py --source-manifest <file.json>` calcola, mentre legge, per ogni tile `512 × 512` lo SHA-256 del blocco sorgente a **profondità piena** (`source[:, y0:y1, x0:x1]`, `uint8`, ordine C) e scrive `{segment, url, level, shape, tile, tiles: {"y0_x0": sha256, …}, tree_sha256_of_manifest, generated_at}`. Poiché al livello 2 il chunk è `[109, 128, 128]`, leggere la profondità piena **non aggiunge traffico**: i chunk sono già interamente trasferiti dal pooling. Il manifest si produce durante la **prima** esecuzione a `--z-start 13` di ciascun segmento (in locale per 0814 al passo 2, su Kaggle per w016 al passo 8) e si congela in `configs/e03/source_manifest.json`. Da quel momento **ogni** pooling successivo dello stesso segmento passa `--verify-source-manifest configs/e03/source_manifest.json` e si ferma alla prima differenza, indicando tile e piani coinvolti.
**Test** (`tests/test_e03_pool_shifted.py`): il manifest di un array sintetico è deterministico; modificare un solo piano fuori da 13–96 (per esempio il piano 5 o il 100) fa fallire la verifica; modificare un piano dentro 13–96 pure; un manifest di un altro segmento viene rifiutato per `shape`/`url`.
**Fatto quando:** `configs/e03/source_manifest.json` contiene i due segmenti; i tre pooling locali di 0814 (0, −3, +3) passano la verifica; il manifest è citato nel manifest finale di E03 accanto alle impronte degli input prodotti.
**Fermarsi se:** la verifica fallisce su un qualunque tile: la sorgente a monte è cambiata o corrotta ai bordi. Nessun run GPU sugli input spostati.

### Passo 3 — Metriche sulle medie e Spearman, con test

**Cosa:** `scripts/e03_metrics.py`:

```text
python scripts/e03_metrics.py --average A.tif B.tif --labels SEGMENT_DIR --out REPORT.json [--sets held,train] [--threshold-mean 91] [--edges 0 64 128 256] [--patch 128]
python scripts/e03_metrics.py --spearman A.tif B.tif --labels SEGMENT_DIR --out REPORT.json [--sets held]
```

Importa da `scripts/e02_metrics.py` (versione 1.2, invariata) soltanto le funzioni indipendenti dal numero di livelli: `auroc`, `load_masks`, `centre_plane`, `read_prediction`, `strata`, `regions`, `annotated_regions`, `trivial_floor`. **Non** importa `sweep`, `best_f1`, `at_threshold` (revisione R1, finding 1): definisce `sweep_n(pos_hist, neg_hist, levels)`, `best_f1_n(sw)` e `at_threshold_n(sw, t)` senza troncamenti, con la stessa regola dei pareggi e la stessa formula di F1. Riporta ogni soglia anche in unità di media (`t/2`); `--threshold-mean 91` valuta `somma >= 182`. Il report ha la stessa struttura del report E02 (`sets` → `held`/`train` con `strata` e `regions`) più `inputs` (percorsi e SHA-256 dei due TIFF), `levels: 511` e `combination: "mean_of_two"`, e il blocco `e03_point` (§2 decisioni). Con `--spearman` calcola la correlazione di Spearman fra i due TIFF sui pixel dell'insieme richiesto (stessa definizione della cella di E00/E02: rank medio sui pareggi). **Lista bianca dei segmenti**: prima di aprire qualunque maschera, la cartella delle label deve essere una delle due di sviluppo con l'impronta congelata (§2 decisioni); ogni altro caso è `ValueError` e uscita 3.
**Test:** (a) `--average X.tif X.tif` riproduce AUROC, best-F1 e F1 a 91 del report `e02_metrics` sullo stesso TIFF, con la soglia riscalata (somma `2t`) e i conteggi identici (test su array sintetici scritti come TIFF `uint8`, e controllo sui dati reali al passo 4); (b) **ottimo oltre 255**: un istogramma il cui massimo di F1 cade a somma 300 deve dare `best_f1_n().threshold == 300` con i conteggi di 300 (con gli helper di E02 la stessa chiamata restituisce le statistiche di 255: controesempio eseguito il 7 settembre 2026); (c) media di due array costanti; (d) `--threshold-mean 91` ↔ somma 182; (e) Spearman di un TIFF con se stesso = 1, con la sua inversione (255 − x) = −1; (f) determinismo del JSON; (g) una cartella di label fuori dalla lista bianca, o con impronta diversa, viene rifiutata **prima** di qualunque lettura di maschera.
**Fatto quando:** test verdi.

### Passo 4 — Controllo a costo zero n. 1: media dei seed (nessuna GPU)

**Cosa:** per w016 e 0814, `e03_metrics.py --average <s42.tif> <s43.tif> --threshold-mean 91` sui TIFF di E02, più `--spearman` fra s42 e s43 sui pixel held-out (atteso: 0,637 su w016 e 0,864 su 0814, come nel manifest E02: è la verifica sui dati reali della funzione). Rieseguire anche `e02_metrics.py --threshold 91` sui quattro TIFF a offset 0 in `docs/reports/e03-r01/metrics/` (sono il punto zero della curva; devono coincidere al decimale con i report E02).
**Fatto quando:** sei JSON in `docs/reports/e03-r01/metrics/` (4 punti zero + 2 medie) e i punti zero coincidono con E02.
**Fermarsi se:** un punto zero differisce da E02 (ambiente cambiato).

### Passo 5 — Generatore, pilota, revisione R2

**Cosa:** `scripts/build_e03_notebooks.py`, `scripts/kaggle_e03.py`, `configs/e03/datasets.json`; poi `python scripts/build_e03_notebooks.py` genera `kaggle/e03-r01-*` (12 cartelle per la tappa 1 e i prep; le cartelle degli `infer` di tappa 2 si generano quando gli hash degli input spostati esistono: il generatore rifiuta costanti `null`, come in E02).
**Come:** il generatore importa `build_e02_notebooks` e ne riusa le celle (ambiente, rete, checkout parziale di villa, installazione `--no-deps`, checkpoint con hash, label con verifica per file e tree-SHA-256, guardia dell'input montato, costruzione del modello su CPU, persistenza, verdetto) sostituendo i placeholder; celle **nuove o modificate**:

- **costanti**: `K` (offset), `LAYER_ARGS` (stringa vuota oppure `--layer-start S --layer-end E`), `EXPECTED_INDICES`, `INPUT_TREE_SHA256` (ufficiale o spostato), `TIF_NAME = f"{SEG}_seed{SEED}_step075000_z{K:+d}.tif"`;
- **inferenza**: la cella di E02 con `$LAYER_ARGS` aggiunto al comando e il nome del TIFF con l'offset;
- **controllo del log**: `assert f"Selected source layer indices={EXPECTED_INDICES}" in log`, `in_chans=17`, device 0, riga `Wrote`; GPU singola misurata come in E02;
- **metriche minime**: `e02_metrics` inlineato (base64, come E02) con `--threshold 91`, `--sets held,train`; gate `shape_ok`; `orientamento_ok` bloccante se `abs(K) == 2`, altrimenti registrato (§2 decisioni); `disjoint_check == 0`;
- **percorsi**: le celle importate da E02 contengono `/kaggle/working/e02`, `/tmp/e02` e `e02_guard.json`; il generatore E03 li sostituisce testualmente con `e03`, e un test verifica che nei notebook generati la stringa `e02` compaia soltanto nei nomi dei dataset E02 riusati (`papyruslab-e02-*`) e nel nome dello script inlineato `e02_metrics`;
- **prep spostato** (run CPU): `scripts/e03_pool_shifted.py` inlineato, con `--verify-source-manifest` (per w016 il manifest si **produce** nel primo run a `--z-start 13` e si verifica nei due spostati); dopo il pooling, la cella monta l'input **ufficiale** dello stesso segmento (dataset E02) e asserisce l'uguaglianza slice a slice (`np.array_equal` su blocchi di 512 × 512 per non saturare la RAM) fra spostato e ufficiale sulle 18 slice condivise, poi attributi (`source_z_slice` atteso, `e03_z_shift_slices`), forma uguale alla label, tar deterministico + hash; nessuna GPU;
- **guardia iniziale** (run GPU): input montato con tree-SHA-256 uguale alla costante; **lista bianca dei segmenti** con impronta congelata delle label (§2 decisioni), verificata prima di aprire qualunque maschera: non è il nome a decidere, ma l'impronta; ogni cartella che non è una delle due di sviluppo ferma il run.

Il pilota `scripts/kaggle_e03.py` riusa le funzioni di `kaggle_e02.py` importandole dove sono generiche (`run`, `dataset_status`, `create_or_version`) e ridefinisce modi, cartelle (`runs/E03-R01/`), `publish-input <short> <zm3|zp3>` e la regola di sequenza: `push` di un `infer-*` è rifiutato se il run GPU precedente della stessa tappa non è stato scaricato con `differenze: 0` e gate superati (ordine fisso in `configs/e03/offsets.json`: tappa 1 = 0814 s42 −2, 0814 s42 +2, 0814 s43 −2, 0814 s43 +2, w016 idem; tappa 2 = ±3 poi ±5 con lo stesso schema). `budget` somma le durate di sessione di **tutte** le versioni scaricate, comprese quelle fallite (in E02 anche gli output dei tentativi falliti sono stati scaricati per versione), più le voci inserite a mano in `configs/e03/datasets.json` per versioni non scaricabili. La regola è una **prenotazione**, non un consuntivo (revisione R1, finding 5): il `push` è rifiutato quando `consumato + 60` (il massimo che quel run può occupare, cioè il limite di sessione passato a `kaggle kernels push -t 3600`) supera i 240 minuti; con 239 minuti consumati, quindi, non parte più nulla. Test del confine a 239 minuti fra i test del pilota.
**R2 Codex** (`adversarial-review`, sola lettura) sul diff completo dal commit di congelamento, con focus: sigillo di w029, identità degli input spostati, argomenti di finestra e indici attesi, metriche sulle medie, sequenza e budget del pilota. Finding classificati nel piano (§10). **Nessun run GPU prima della chiusura di R2.**
**Fatto quando:** `python scripts/build_e03_notebooks.py` rigenera senza diff; `python -m pytest tests/ -q` verde (E02 + E03); R2 chiusa.

### Passo 6 — Tappa 1: ±2 sugli input ufficiali (GPU, 8 run, un "vai" per run)

**Cosa:** nell'ordine del passo 5. Dopo ogni run: `output` (SHA256SUMS, `differenze: 0`), poi in locale `e02_metrics.py --threshold 91` sul TIFF con le label locali → `docs/reports/e03-r01/metrics/<seg>_s<seed>_z<k>.json`, confronto con il JSON della cella Kaggle (AUROC uguale al decimale), `e03_metrics.py --spearman` con il TIFF a offset 0 dello stesso seed.
**Fatto quando:** 8 TIFF con gate A e B superati, 8 report locali, 8 Spearman.
**Fermarsi se:** un gate fallisce; un run supera 30 minuti di inferenza; il pilota rifiuta il push; il budget supera i 240 minuti; uno script legge w029.

### Passo 7 — Gate fra le tappe e controllo a costo zero n. 2

**Cosa:** `e03_metrics.py --average <z-2.tif> <z+2.tif>` per seed e segmento (4 medie); `e03_curve.py` sulla tappa 1: tabella AUROC(k) per k ∈ {−2, 0, +2}, Δ rispetto allo zero, lettura di H1 (§5). Scrivere il rapporto intermedio nella scheda (sezione "Tappa 1") e sottoporlo a Matteo per il "vai" alla tappa 2. Se H1 è violata (perdita > 0,02 già a ±2 su una combinazione) **non** si ferma la tappa 2: è un risultato che rende la curva ancora più interessante; si ferma solo per i motivi di §7.
**Fatto quando:** rapporto intermedio scritto e "vai" di Matteo ricevuto (o stop registrato).

### Passo 8 — Pooling spostato su Kaggle (CPU, 4 run, da annunciare)

**Cosa:** `prep-46527-zm3`, `prep-46527-zp3`, `prep-w016-zm3`, `prep-w016-zp3` (letture S3: 0,8 GB × 2 e 5,6 GB × 2; tempi attesi 6–40 s di pooling più il download dell'ufficiale per il confronto). Poi `publish-input <short> <zm3|zp3>` → dataset `papyruslab-e03-input-<short>-<zm3|zp3>`; le impronte finiscono in `configs/e03/datasets.json` e il generatore produce i notebook della tappa 2. Per 0814 le impronte di Kaggle devono coincidere con quelle calcolate in locale al passo 2 (e con quelle del socio, S2, quando arrivano).
**Fatto quando:** 4 dataset `ready`, impronte scritte, uguaglianza slice a slice asserita nei log dei quattro run, impronte di 0814 identiche fra Kaggle e portatile.
**Fermarsi se:** l'asserzione slice a slice fallisce; impronte diverse fra piattaforme per 0814 (l'aritmetica non è deterministica: dichiarare e fermarsi).

### Passo 9 — Tappa 2: ±3 e ±5 (GPU, 16 run, un "vai" per run)

Come il passo 6, ordine: ±3 (0814 s42 −3, +3; s43 −3, +3; w016 idem), poi ±5 nello stesso schema. Per |k| = 5 l'orientamento è registrato, non bloccante. Spearman di ogni TIFF con lo zero del suo seed. Budget controllato dal pilota.
**Fatto quando:** 16 TIFF con gate A superati (gate B dove bloccante), 16 report locali, 16 Spearman; totale 24 nuovi TIFF conservati in `runs/E03-R01/` con SHA-256.

### Passo 10 — Curva e commit dei JSON, poi **stop**

**Cosa:** `e03_curve.py` su tutti i JSON: prima la **validazione della matrice** (2 × 2 × 7, chiavi uniche, `e03_point` coerente con nomi, `offsets.json` e impronte), poi `docs/reports/e03-r01/metrics/curve.json` e la tabella Markdown (per seed e segmento: AUROC held e train, best-F1, F1 a 91, Spearman, per strato; Δ rispetto allo zero; tolleranza per seed e verso secondo §5; i due controlli; lettura di H1, H2 e della regola di anomalia). Commit dei JSON delle metriche **e di `curve.json`** con un messaggio dichiarato (per esempio `docs: E03 per-run metrics and curve (24 runs)`).
**Fatto quando:** il commit esiste ed è pushato; il suo sha breve e il messaggio esatto sono scritti nell'intestazione di `docs/plans/2026-09-07-e03-compiti-socio.md` (campo "Commit di partenza", oggi `DA COMPILARE`), e quel piano più il prompt sono pronti da consegnare.
**Poi ci si ferma:** la scheda e la revisione R3 si scrivono **dopo** il rientro del socio (passo 11), così il suo ricalcolo è davvero in cieco e le sue eventuali differenze entrano nella scheda invece di correggerla a posteriori.

### Passo 11 — Procedura unica del socio (S1 → S2 → S3) e integrazione

**Cosa:** Matteo consegna al socio `docs/plans/2026-09-07-e03-compiti-socio.md` (con il commit compilato) e il prompt `docs/plans/e03-prompt-codex-socio.md`; il socio esegue in sequenza S1 (verifica di novità), S2 (pooling spostati sul Mac, impronte) e S3 (ricalcolo in cieco di curva e tolleranza), consegna con un push del branch `e03-socio`. Claude legge i tre rapporti in sola lettura e li confronta con i nostri numeri: verdetto di novità, impronte contro quelle di Kaggle e del portatile, tabella di S3 contro `curve.json` (differenze e ambiguità segnalate). Matteo decide la fusione.
**Fatto quando:** i tre rapporti esistono sul branch, il confronto è scritto, ogni differenza è spiegata o dichiarata aperta.
**Fermarsi se:** l'impronta a spostamento zero del socio differisce (P0: l'aritmetica non è deterministica fra piattaforme) o la sua curva non coincide con la nostra entro l'arrotondamento dei JSON.

### Passo 12 — Scheda, manifest, R3, consolidamento

**Cosa:** scheda da `docs/templates/esperimento.md` (curva, letture di §5 C, esito di S1–S3 del socio, limiti, deviazioni) e manifest (commit, hash dei checkpoint, delle label, dei sei input, dei 28 TIFF, `source_manifest`, comandi risolti, versioni Kaggle, tempi, picchi di memoria, quota GPU consumata per run e totale). R3 Codex (`adversarial-review`, modello `gpt-5.6-sol`, focus: "la curva e la tolleranza sono lette con la regola preregistrata? qualche numero è stato usato per scegliere? il sigillo di w029 è intatto? le formulazioni eccedono le evidenze?"); finding classificati; correzioni; consolidamento di roadmap, README, AGENTS, "Aggiornamenti" del documento di decisione, registro community (fonti trovate da S1). Commit e push del lavoro verificato. Le condizioni di ripensamento le applica Matteo nella sessione successiva.

---

## 5. Criterio di esito, deciso prima della prova

Tutte le misure sui pixel del piano annotato (`shape[0] // 2 = 10`); `held` = `validation_mask == 1`; `train` = `supervision_mask == 1`; mai mescolati; solo `pherc0139-w016` e `pherc0814-46527`.

**A. Identità** (per ogni run GPU, tutti, altrimenti il run è fallito): commit villa `3ea17f5…`; revisione HF `7109667…`; SHA-256 dei checkpoint (`e635558a…9cab`, `2aeaa85a…b28f`); cartella delle label nella **lista bianca** con tree-SHA-256 congelato (`a62d3e0e…` per w016, `56592368…` per 0814), verificata prima di aprire qualunque maschera; input montato con tree-SHA-256 uguale alla costante del generatore (ufficiale per |k| = 2, spostato per |k| ∈ {3, 5}); `torch.__version__` invariato (`2.10.0+cu128`); log con `Selected source layer indices=` uguale alla lista attesa per k (§2.2) e `in_chans=17`; `exit_code=0`; TIFF `uint8` con forma uguale a `label.shape[1:]`; report con `e03_point` completo e coerente. Per ogni run CPU di pooling: **manifest di sorgente** verificato (passo 2b, tutti i 109 piani), uguaglianza slice a slice con l'input ufficiale sulle 18 slice condivise, `source_z_slice` atteso, forma uguale alla label.

**B. Validità del punto della curva:** `disjoint_check == 0`; `orientamento_ok` vero su `train` per |k| = 2 (bloccante), registrato per |k| ∈ {3, 5} (l'allineamento XY degli input spostati è provato dall'uguaglianza slice a slice, criterio A); metriche della cella Kaggle e dello script locale uguali al decimale; punti zero (E02) riprodotti al decimale. **Validità della matrice** (prima di qualunque lettura della curva): esattamente 2 segmenti × 2 seed × 7 offset, chiavi uniche, `e03_point` coerente con il nome del file, con `configs/e03/offsets.json` e con le impronte di TIFF e input. Un punto mancante, duplicato o incoerente ferma l'analisi.

**C. Letture preregistrate** (nessuna soglia sul "successo": sono regole di lettura, non criteri di accettazione):

- **Curva:** per ogni seed s e segmento g, `AUROC_held(s, g, k)` per k ∈ {−5, −3, −2, 0, +2, +3, +5}; `Δ(s, g, k) = AUROC(s, g, k) − AUROC(s, g, 0)`; `Δ̄(s, k)` = media di Δ sui due segmenti (pesi uguali).
- **Tolleranza per seed e verso:** `T⁻(s)` = il più piccolo |k| fra {2, 3, 5} con k < 0 tale che `Δ̄(s, k) ≤ −0,05`; analogamente `T⁺(s)` per k > 0. Se nessun k campionato soddisfa la condizione, si scrive "nessun decadimento di 0,05 rilevato fino a 5 slice (48 µm) agli offset campionati", **non** "tollera 48 µm". Si riporta anche il valore di `Δ̄(s, ±5)` e la tolleranza per singolo segmento.
- **H1 (piatta entro ±2):** `|Δ(s, g, ±2)| ≤ 0,02` per tutte e quattro le combinazioni (s, g). Se violata, si scrive quale combinazione e di quanto: è un'osservazione contro l'attesa del jitter, non un fallimento.
- **H2 (decade oltre ±2):** `Δ̄(s, ±3) < Δ̄(s, ±2)` e `Δ̄(s, ±5) < Δ̄(s, ±3)` per ciascun seed e verso; si riporta dove vale e dove no. Un'asimmetria fra i versi (per esempio perdita più rapida verso il verso del recto) si riporta come tale.
- **Regola di anomalia:** se esiste k ≠ 0 con `Δ(s, g, k) ≥ +0,02` per **tutte e quattro** le combinazioni (s, g), il piano annotato potrebbe non coincidere con il centro del segnale: **stop** (§7), nessuna adozione dell'offset, indagine su label e pooling prima di qualunque altro run.
- **Controlli a costo zero** (dal documento di decisione): una media "aiuta" se la sua AUROC held supera quella della finestra centrale dello stesso seed su **entrambi** i segmenti senza peggiorare di oltre 0,01 su nessuno; si riporta per la media dei seed (confronto con ciascuno dei due seed) e per la media −2/+2 (confronto con lo zero dello stesso seed).
- **Secondarie, sempre riportate:** best-F1 e F1 a 91 (precision, recall) per set; AUROC per strato di distanza (`<64`, `64–128`, `128–256`, `≥256`) e per regione; Spearman con lo zero dello stesso seed su `held`; curva su `train`; per la media, soglia in unità di media.

Le soglie 0,05, 0,02 e 0,01 sono scelte di utilità pratica fissate prima della prova, non livelli di significatività: due segmenti e due seed non permettono intervalli di confidenza onesti, e i pixel vicini non sono osservazioni indipendenti. La conferma di qualunque scelta futura resta E05.

**D. Formulazione ammessa in caso di completamento:** *"Sui pixel held-out di sviluppo di due segmenti (w016, 0814), i due modelli `ink_9um` (seed 42 e 43, step 75000) mostrano, per offset uniformi della finestra Z di k slice (9,6·k µm), la curva AUROC(k) riportata; con la regola preregistrata la tolleranza per seed risulta T⁻/T⁺ (oppure: nessun decadimento di 0,05 rilevato agli offset campionati); la media dei seed e la media delle finestre −2/+2 hanno l'effetto riportato; l'errore simulato è uniforme e non rappresenta errori locali della superficie, normali sbagliate o cambi di foglio"*. **Non ammesso:** "il rendering è/non è il collo di bottiglia", "superfici con errore sotto X µm sono sicure", "la finestra ottimale è k", qualunque affermazione su rotoli non misurati, su lettere leggibili, su E05 o su w029.

---

## 6. Verifica finale

Esecuzione completata quando, nell'ordine, sul portatile:

```bash
./.venv/Scripts/python.exe -m pytest tests/ -q                                       # atteso: tutti passati (E02 + E03)
./.venv/Scripts/python.exe scripts/build_e03_notebooks.py; git status --short kaggle/   # atteso: nessun output
./.venv/Scripts/python.exe scripts/kaggle_e03.py budget                              # atteso: <= 240 minuti, 24 run infer + 4 prep scaricati con differenze 0
./.venv/Scripts/python.exe scripts/e03_curve.py --validate-only                      # atteso: matrice 2x2x7 completa, chiavi uniche, e03_point coerenti
ls docs/reports/e03-r01/metrics/ | wc -l                                             # atteso: 4 zero + 24 run + 2 medie seed + 2 spearman s42/s43 + 4 medie Z + 24 spearman run/zero + curve.json = 61
./.venv/Scripts/python.exe - <<'PY'                                                  # sigillo, verificato sul CONTENUTO dei report (R1, finding 4)
import json, pathlib
ok = {"pherc0139-w016", "pherc0814-46527"}
for p in pathlib.Path("docs/reports/e03-r01/metrics").glob("*.json"):
    d = json.loads(p.read_text(encoding="utf-8"))
    segs = {d.get("segment")} | {pt.get("segment") for pt in [d.get("e03_point", {})]} - {None}
    assert segs <= ok, f"STOP: {p.name} riporta segmenti {segs}"
print("sigillo: nessun report fuori dai due segmenti di sviluppo")
PY
git ls-files | grep -E '\.(tif|tiff|pth|zarr|tar)$'                                  # atteso: nessun output
git status --short                                                                   # atteso: solo i file di §3
```

E03 completato quando, in più, i criteri A e B di §5 valgono per i 24 run e i 4 prep, la scheda riporta tutte le letture di §5 C, i tre rapporti del socio sono integrati (passo 11) e la revisione R3 è chiusa con finding classificati.

---

## 7. Se il piano è sbagliato

1. **Fermati.** Non improvvisare: non aggiungere offset, seed, step, `--direction both`, `--tta-mirror`; non scegliere una finestra; non modificare villa né gli script di E02; non rilanciare dopo un timeout senza registrare; non toccare w029.
2. Annota cosa hai trovato e a quale passo.
3. Conserva log e output parziali; esegui i passi di persistenza per quanto esiste.
4. Spegni la GPU. Segnala a Matteo. Il piano si corregge in un nuovo commit; un nuovo tentativo scientifico è `E03-R02`.

Arresto obbligatorio: impronta a spostamento zero diversa da `bc742343…` (passo 2); manifest di sorgente non verificato (passo 2b); uguaglianza slice a slice falsa; matrice della curva incompleta, duplicata o incoerente; una cartella di label fuori dalla lista bianca; hash di label, input o checkpoint diverso; `torch` che cambia versione; indici di layer diversi dagli attesi; `in_chans ≠ 17`; `exit_code ≠ 0` o timeout; `orientamento_ok` falso con |k| = 2; `held ∧ train ≠ ∅`; regola di anomalia di §5 C soddisfatta; budget oltre 240 minuti di GPU o oltre i tetti di spazio; due tentativi falliti sullo stesso run; qualunque lettura o run su w029; due writer sugli stessi percorsi; serve una spesa, un invito o un'azione esterna.

---

## 8. Fuori perimetro

Anche se sembrano utili o ovvie, **non** fare in questo lavoro:

- offset ±1, ±4, oltre ±5; finestre asimmetriche; medie di più di due predizioni; `--tta-mirror`; `--direction both`; altri step o checkpoint (E04); pesi diversi da ½ nelle medie;
- scegliere "la finestra migliore" o proporre di adottarla;
- rifare le inferenze a offset 0 (i TIFF di E02 sono il punto zero);
- qualunque run, pooling, lettura o metrica su `pherc1667-w029`;
- ri-addestrare, fine-tuning, pseudo-label; misurare il cross-scroll;
- correggere o "migliorare" `prepare_9um_isotropic_input.py` di villa (lo script E03 lo riproduce, non lo sostituisce);
- candidare a un Progress Prize, pubblicare il repository, decidere la licenza, registrarsi su Discord, coinvolgere Francesco o segnalare a monte: decisioni di Matteo, dopo R3;
- interpretare la curva come giudizio sul collo di bottiglia: le condizioni di ripensamento sono nel documento di decisione e le applica Matteo.

Se ne emergono altre: **annotarle, non farle.**

---

## 9. Divisione del lavoro

### Persone e agenti

| Chi | Ruolo in E03 | Cosa fa concretamente | Tempo stimato |
|---|---|---|---|
| **Matteo** | Responsabile, arbitro, esecutore delle azioni che richiedono una persona | **Prima del passo 0:** rigenera il token API Kaggle (quello attuale è passato in chat il 6 settembre 2026: va revocato e sostituito, senza mostrarlo) e rifà `kaggle auth login`; verifica il commit di congelamento; un "vai" per ciascuno dei 24 run GPU (si possono dare a gruppi dentro una sessione, ma i run partono uno alla volta); "vai" alla tappa 2 dopo il rapporto intermedio; decide sui finding di R1–R3 in caso di disaccordo fra writer e revisore; **consegna al socio** piano e prompt dopo il passo 10; legge la scheda e applica le condizioni di ripensamento; decide la fusione di `e03-socio` | 5 sessioni brevi (1: congelamento e R2; 2: tappa 1, ≈ 1 h di parete; 3: prep + tappa 2, ≈ 2,5 h di parete; 4: curva, commit e consegna al socio; 5: integrazione, scheda e consolidamento) |
| **Claude Code** (con Matteo) | Writer ed esecutore su `main` | Script, test, generatore, pilota, run, metriche, curva, confronto con i rapporti del socio, scheda, manifest, consolidamento; classifica i finding di Codex | le stesse 5 sessioni |
| **Codex** (con Matteo) | Revisore in sola lettura | R1 piano, R2 codice, R3 esito; due giri al massimo per revisione | 3 × (3–6 minuti) |
| **Socio** (con Codex, Mac) | Verificatore indipendente su `e03-socio` | S1, S2, S3 sotto; non vede i numeri di Matteo prima di consegnare | S1 2–3 h, S2 1 h, S3 1–2 h, distribuite nelle due settimane |

Il lavoro del socio è progettato per essere **indipendente e parallelo**: nessun compito richiede la quota GPU di Matteo, i suoi dataset privati o l'accesso ai suoi `runs/`; ogni compito produce una verifica che Matteo e Claude non possono darsi da soli.

### Compiti del socio (branch `e03-socio`; percorsi posseduti: `docs/reports/2026-09-XX-e03-socio-*` e `runs/`, ignorata)

Tutti e tre i compiti si eseguono **dopo il passo 10**, in un'unica sessione, nell'ordine S1 → S2 → S3, sul commit dichiarato nell'intestazione del piano del socio.

| ID | Compito | Perché è utile | Costo |
|---|---|---|---|
| **S1 — Verifica di novità** | Ricerca documentata di lavori pubblici che abbiano già misurato la sensibilità di `ink_9um` (o dei modelli ink di villa) all'offset Z o alla finestra di slice: ricerca di codice, issue e repository su GitHub con `gh api`, model card e discussioni su Hugging Face, pagine scrollprize.org, repository R01–R12 del registro; per ogni fonte: URL, revisione o data, cosa misura, se è confrontabile con la nostra curva. Verdetto: "trovato un equivalente / trovato lavoro parziale / non trovato", con la lista di dove si è cercato | La decisione rivendica una novità "non individuata nelle fonti consultate"; la revisione Codex ha chiesto di verificarla prima di una candidatura. È una ricerca che deve farla chi **non** ha scritto la decisione | 2–3 h, solo rete |
| **S2 — Pooling spostato indipendente** | Sul Mac, con `scripts/e03_pool_shifted.py`: 0814 a `--z-start 13` (impronta attesa `bc742343…`: verifica che lo script riproduce l'ufficiale anche sul Mac), poi `--z-start 1` e `--z-start 25`, con verifica del manifest di sorgente (passo 2b) e uguaglianza slice a slice fra spostati e non spostato. Facoltativo: w016 (5,6 GB per pooling) | Terza misura indipendente delle impronte (Kaggle, portatile, Mac). **Verifica a posteriori**, per decisione di Matteo: l'identità prima delle inferenze è già garantita dal manifest di sorgente e dall'uguaglianza slice a slice su Kaggle. Se un'impronta differisce, è una deviazione da scrivere nella scheda e la tappa 2 va ripetuta con la causa chiarita | 1 h, 1,6 GB di rete (0814), +11 GB opzionali (w016) |
| **S3 — Ricalcolo in cieco della curva e della tolleranza** | Dai soli JSON committati in `docs/reports/e03-r01/metrics/` (esclusa `curve.json`), con uno script **proprio** (non `scripts/e03_curve.py`), ricostruire la tabella AUROC(k) per seed e segmento, Δ, tolleranza per seed e verso e i due controlli secondo §5 C, **senza leggere la scheda né `curve.json`**; consegnare tabelle, verdetti su H1, H2 e regola di anomalia, e le ambiguità incontrate | Verifica indipendente dell'analisi (non dei dati): un errore di lettura della regola preregistrata o di segno negli offset verrebbe scoperto da chi non l'ha scritta | 1–2 h, CPU |
| S4 — *opzionale, solo su decisione di Matteo* | Ripetizione di un run della tappa 1 (`infer-46527-s42-zm2`) nell'account Kaggle del socio con dataset propri: TIFF atteso identico bit per bit | Riproducibilità cross-account di un run E03 (E01 l'ha mostrata per E00). Richiede la pubblicazione di due dataset privati nel suo namespace e ≈ 3 minuti della sua quota | 1–2 h di setup, 3 min GPU |

**Decisione di Matteo (7 settembre 2026): S1, S2 e S3 si eseguono in un'unica procedura consecutiva, dopo il commit dei JSON delle metriche (passo 10), non in tre momenti separati.** È più semplice da consegnare e da eseguire per il socio. Conseguenza dichiarata: S2 diventa una verifica **a posteriori** dell'identità degli input spostati fra piattaforme (Kaggle, portatile, Mac), non un controllo prima dei run GPU; l'identità prima della GPU resta garantita su Kaggle dall'uguaglianza slice a slice con l'input ufficiale (passo 8) e sul portatile dal passo 2. Se S2 trovasse un'impronta diversa, la scheda lo registra come deviazione e la tappa 2 andrebbe ripetuta con la causa chiarita. Il commit di partenza del socio è quello che contiene i JSON delle metriche; da lì il socio **non** legge la scheda, `curve.json` né i documenti canonici aggiornati finché non consegna S3.

Regole per il socio: nessun commit su `main`, nessuna pull request, nessun run GPU senza il "vai" di Matteo (S4), non leggere `runs/` di Matteo né la scheda prima di consegnare; uno script che non funziona sul Mac si registra come ostacolo, non si corregge. Il piano eseguibile dettagliato per il socio (una sola procedura S1 → S2 → S3: comandi, criteri di esito, formato dei rapporti) è `docs/plans/2026-09-07-e03-compiti-socio.md`, con il prompt per il suo Codex in `docs/plans/e03-prompt-codex-socio.md`, entrambi scritti al passo 2 sulla struttura di quelli di E02 e rifiniti al passo 10 con il commit di partenza effettivo.

### Calendario indicativo (non vincolante)

| Quando | Cosa |
|---|---|
| 7–8 settembre | R1, correzioni, congelamento; piano e prompt del socio pronti (commit di partenza ancora da compilare) |
| 9–11 settembre | passi 1–5 (script, test, manifest di sorgente, generatore, pilota), R2 |
| 12–14 settembre | tappa 1 (passo 6), gate e controllo a costo zero (passo 7) |
| 15–18 settembre | pooling spostati (passo 8), tappa 2 (passo 9) |
| 19–20 settembre | curva e commit dei JSON (passo 10); consegna al socio |
| 20–22 settembre | il socio esegue S1 → S2 → S3 in un'unica procedura; Claude confronta e integra (passo 11) |
| 22–23 settembre | scheda, manifest, R3, consolidamento, fusione di `e03-socio` (passo 12) |
| entro il 30 settembre | decisione di Matteo su candidatura, licenza e pubblicazione: fuori da questo piano |

---

## 10. Revisioni Codex e congelamento

- **R1 — piano** (prima del congelamento): `adversarial-review` sull'albero di lavoro con focus: "trova ciò che renderebbe la curva non valida o non riproducibile: aritmetica degli offset e degli indici, identità degli input spostati, confronti fra seed, selezione a posteriori, sigillo di w029, budget, divisione del lavoro". Finding classificati sotto; piano congelato in `docs: freeze E03 plan (R01)`.
- **R1 — piano**: modello `gpt-5.6-sol` (vedi sotto per i tentativi).
- **R2 — codice** (prima dei run GPU, modello `gpt-5.6-sol`): sul diff dal congelamento: `e03_pool_shifted.py`, `e03_metrics.py`, `e03_curve.py`, generatore, pilota, test, configurazioni. **Eseguita il 7 settembre 2026**, esito sotto.
- **R3 — esito** (prima del consolidamento, modello `gpt-5.6-sol`): scheda, manifest, `curve.json`, JSON delle metriche.
- I compiti del socio con Codex (S1–S3) usano `gpt-5.6-sol`, salvo diversa indicazione di Matteo.

Per ogni revisione registrare: canale, modello ed effort dichiarati, durata, finding per severità, accettati/rifiutati/differiti, correzioni materiali.

### Revisione R1 (7 settembre 2026)

- **Tentativo 1 (11:49 UTC), non completato:** `adversarial-review` sull'albero di lavoro, modello `gpt-6-astra`; Codex ha letto il piano, dichiarato che "la tabella degli offset è aritmeticamente coerente" e poi il turno è fallito per **limite di utilizzo dell'account Codex** ("You've hit your usage limit … try again at 4:05 PM"): nessun finding prodotto (job `review-mtr6h7i9-jvjc4e`, 2 min 20 s). Il canale non è stato sostituito.
- **Autorevisione del writer nell'attesa**, correzioni integrate nel testo prima del tentativo 2: gate di orientamento bloccante solo per |k| = 2; sostituzione dei percorsi `e02` → `e03` nelle celle importate, con test; budget del pilota che conta anche le versioni fallite; conteggio dei file di metriche corretto; rigenerazione del token Kaggle come prerequisito esplicito di Matteo.
- **Tentativo 2 (12:49–13:01 UTC), completato:** stesso comando, modello **`gpt-5.6-sol`** (decisione di Matteo del 7 settembre 2026: Sol per default, anche per R1), sola lettura, 12 min 34 s, job `review-mtr8m8fk-gd5xre`, sessione Codex `01a07bea-8d52-7e52-b8c1-4253a3bf97c1`. **Verdetto: NO-SHIP** — "l'aritmetica degli offset è coerente, ma il piano può produrre metriche errate sulle medie, una curva con punti mal attribuiti e input spostati non pienamente riproducibili; sigillo, budget e sequenza del socio non sono ancora fail-closed". **7 finding: 4 P1, 3 P2. Accettati 7**, rifiutati 0, differiti 0.

| # | Sev. | Finding (sintesi) | Esito | Correzione |
|---|---|---|---|---|
| 1 | P1 | Lo sweep a 511 livelli importava `best_f1`/`at_threshold` da `e02_metrics`, che troncano l'indice a 255 (`np.clip(int(t), 0, 255)`) e assertano `shape == (256,)`: best-F1, precision e recall delle medie sarebbero stati internamente incoerenti quando l'ottimo cade oltre 255 (caso reale: la soglia 135 di w016/train corrisponde a 269 sulla somma) | accettato | E03 definisce `sweep_n`, `best_f1_n`, `at_threshold_n` senza troncamenti; test con ottimo a 300 e test `X+X` con soglia riscalata e conteggi identici. **Controesempio riprodotto da Claude prima di accettare:** `at_threshold(sw, 300)` restituisce `threshold: 255` con le statistiche di 255 |
| 2 | P1 | I piani sorgente 1–12 e 97–108, che alimentano le tre slice nuove degli input ±3/±5, non avevano identità congelata: l'impronta `bc742343…` e l'uguaglianza slice a slice coprono solo i piani 13–96; una corruzione ai bordi sarebbe passata e poi "consacrata" dal nuovo hash | accettato | **Passo 2b**: manifest di contenuto per tile a profondità piena (109 piani), prodotto durante il primo pooling e verificato da ogni pooling successivo; nessun traffico aggiuntivo perché il chunk al livello 2 è `[109, 128, 128]`; test con alterazione dentro e fuori 13–96 |
| 3 | P1 | La curva si sarebbe costruita da "tutti i JSON" senza pretendere che ogni report autentichi `(segmento, seed, k)`: un rinomino `zm`/`zp` o una copia avrebbe invertito un verso, e il ricalcolo in cieco del socio avrebbe ripetuto lo stesso errore | accettato | Blocco `e03_point` in ogni report (segmento, seed, k, hash del TIFF e dell'input, `source_z_slice`, indici di layer, run) e validazione in `e03_curve.py`: esattamente 2 × 2 × 7, chiavi uniche, coerenza con nome, `offsets.json` e impronte; test per punto mancante, duplicato e segno invertito |
| 4 | P1 | Il sigillo di w029 era protetto dal solo nome, ma il caricatore di E02 deriva l'identità dal nome della cartella: una cartella o un collegamento rinominato avrebbe aperto la maschera sigillata, e il solo accesso viola il sigillo | accettato | Lista bianca dei due segmenti di sviluppo con tree-SHA-256 congelato, verificata **prima** di aprire qualunque maschera, nello script e nella guardia dei notebook; verifica finale sul contenuto dei report, non sui nomi dei file |
| 5 | P2 | Il tetto GPU era un consuntivo: con 239 minuti consumati il `push` era ancora ammesso e un run può occuparne 60 | accettato | Prenotazione: `push` rifiutato quando `consumato + 60 > 240`; test del confine a 239 minuti |
| 6 | P2 | La tabella dei compiti del socio e il calendario contraddicevano la decisione della procedura unica; il passo 10 accorpava commit, lavoro del socio, scheda, R3 e consolidamento senza uno stop | accettato | Tabella e calendario allineati; passo 10 diviso in **10** (curva, commit dei JSON, consegna, stop), **11** (procedura unica del socio e integrazione), **12** (scheda, manifest, R3, consolidamento) |
| 7 | P2 | La clausola "fa fede il generatore" permetteva al codice scritto dopo il congelamento di cambiare il comando eseguito senza correggere la preregistrazione | accettato | Piano congelato e `offsets.json` sono autoritativi; il generatore ha autorità solo sull'espansione meccanica; ogni divergenza semantica è un arresto con revisione del piano |

Nessun secondo giro di R1: le correzioni sono di piano, non di codice, e saranno esercitate dai test e dalla revisione R2 sul codice che le implementa.

### Revisione R2 (codice, 7 settembre 2026)

- **Canale:** plugin `codex@openai-codex`, `adversarial-review --base 9e7f1d0`, modello **`gpt-5.6-sol`**, sola lettura, 12 min 5 s (job `review-mtrayrfi-zg6cgc`, sessione `01a07c26-bad0-7d11-8793-fb55b3670956`). Codex non ha potuto eseguire la suite (nel suo sandbox in sola lettura manca una cartella temporanea scrivibile): i test sono stati eseguiti da Claude, 84 superati.
- **Verdetto: NO-SHIP.** **6 finding: 2 P0, 3 P1, 1 P2. Accettati 6**, rifiutati 0, differiti 0. Il primo avrebbe fermato ogni run al primo controllo.

| # | Sev. | Finding (sintesi) | Esito | Correzione |
|---|---|---|---|---|
| 1 | P0 | Ogni notebook montava `papyruslab-e02-r01-labels`, che contiene **anche `pherc1667-w029`**: l'artefatto sigillato sarebbe entrato nel perimetro del run, e la guardia generata (che cerca il sigillato fra i mount) avrebbe fatto fallire **tutti** i run. Il test controllava solo lo slug, quindi passava | accettato | Nuovo dataset `papyruslab-e03-r01-labels` con i **soli due segmenti di sviluppo**, ricostruito dalle copie locali verificate: i tar risultano **identici byte per byte** a quelli di E02 (`tree_sha256` e `tar_sha256` uguali per entrambi i segmenti). `configs/e03/datasets.json` aggiornato, comando `publish-labels` nel pilota, due test nuovi |
| 2 | P0 | `check_labels_allowed` decideva sul nome e poi calcolava l'impronta dell'intera cartella: e `tree_sha256` **legge ogni file**, quindi una copia del segmento sigillato rinominata con un nome ammesso sarebbe stata letta prima del rifiuto | accettato | Prima si decide con i soli **metadati**: nome nella lista bianca, nessun collegamento, nessuna voce diversa dai tre array attesi, nessun percorso che nomini il sigillato; solo dopo si calcola l'impronta. Stessa sequenza nella cella dei notebook. Test che intercetta `Path.read_bytes` e verifica che **nessun byte** venga letto prima del rifiuto |
| 3 | P1 | La curva accettava qualunque `input_tree_sha256` purché non vuoto: 28 report costruiti da un input sbagliato ma con finestre giuste avrebbero prodotto una curva falsa | accettato | Ogni punto è confrontato con `configs/e03/datasets.json`: tipo di input previsto per quel `k` e impronta esatta; verificate anche impronta delle label, seed, soglia congelata 91, `run_id`, gate quando presenti e presenza delle letture secondarie |
| 4 | P1 | `latest_download` considerava valido qualunque download con `SHA256SUMS`, anche uno che aveva **fallito** la verifica: poteva sbloccare il run successivo | accettato | `output()` scrive `VERIFIED.json` **solo** dopo zero differenze e zero file mancanti; `latest_download` richiede quel marcatore |
| 5 | P1 | Sequenza e budget aggirabili: un secondo `push` prima del download non prenotava i 60 minuti già in volo, e un predecessore non generato veniva saltato | accettato | Registro persistente delle prenotazioni scritto **prima** del push e contato nel consumo; il modo corrente non deve risultare già in volo né concluso e non scaricato; un predecessore mancante è un errore, non un salto |
| 6 | P2 | `curve.json` ometteva letture secondarie che il piano §5 C richiede sempre | accettato | Aggiunte best-F1, metriche alla soglia congelata, AUROC per strato e per regione, Spearman contro lo zero e fra i seed; la validazione rifiuta un report che non le contenga |

Nessun secondo giro: le correzioni sono locali, coperte da 84 test (nove nuovi, scritti sui controesempi dei finding) e verificate sui dati reali (lista bianca sulle due cartelle di label vere, dataset montati dai notebook rigenerati).

---

## 11. Emendamenti dopo il congelamento

Il piano è stato congelato il 7 settembre 2026 (`docs: freeze E03 plan (R01)`, commit `9e7f1d0`). Ciò che segue è stato scoperto eseguendo i passi 0–5 e corretto con un commit dedicato, come chiede [docs/07 §2](../07-procedura-operativa.md): nessuna correzione silenziosa. Nessuno di questi emendamenti tocca il disegno scientifico (offset, segmenti, seed, metriche, regole di lettura).

### A1 — i report per run passano da `scripts/e03_metrics.py --run`

- **Cosa è successo.** Il piano (passo 6) prescriveva di produrre i report locali con `scripts/e02_metrics.py --threshold 91`. Ma la revisione R1, finding 3, richiede che ogni report porti il blocco `e03_point` con segmento, seed, offset, impronte e finestra: `e02_metrics.py` è congelato e non può produrlo.
- **Correzione.** `scripts/e03_metrics.py --run` **avvolge** `e02_metrics.build_report()` (importato, non modificato) e vi aggiunge `e03_point`, dopo aver verificato che indici di layer e finestra sorgente siano quelli attesi per quel `k`. I numeri restano quelli di E02: i quattro punti a offset zero, ricalcolati così il 7 settembre 2026, riproducono la scheda E02 **esattamente** (differenza 0 su AUROC, best-F1 e F1 a τ\* = 91, held e train, per entrambi i segmenti e i due seed).
- **Conseguenza.** I comandi dei passi 4, 6 e 9 usano `e03_metrics.py --run` invece di `e02_metrics.py`.

### A2 — un quinto run CPU, `prep-w016-z13`, per il manifest di sorgente

- **Cosa è successo.** Il passo 2b (introdotto da R1, finding 2) vuole un manifest di identità dei 109 piani sorgente prodotto "durante il primo pooling a `--z-start 13` di ciascun segmento". Per `pherc0814-46527` quel pooling si fa in locale (passo 2), ma per `pherc0139-w016` in E03 non era previsto alcun pooling ufficiale: l'input ufficiale arriva dal dataset di E02. Senza quel run, il manifest di w016 non esisterebbe e i due pooling spostati non avrebbero nulla da verificare.
- **Correzione.** Si aggiunge il run CPU `prep-w016-z13`, che produce il manifest e **riproduce l'input ufficiale**: la sua impronta deve coincidere con quella congelata di E02 (`7c0c7006…`), altrimenti si ferma tutto. È quindi anche una replica indipendente dell'input di E02 su una nuova sessione Kaggle. I run CPU passano da 4 a 5; nessun costo GPU.
- **Conseguenza.** Il pilota ha il comando `publish-manifest`, che scrive il manifest di w016 in `configs/e03/source_manifest.json` dopo aver verificato quell'uguaglianza. Il generatore rifiuta i notebook `prep-*-z{m3,p3}` finché il manifest del segmento non esiste.

### A3 — perimetro: un file di test e due comandi del pilota in più

- `tests/test_e03_generator.py` (non elencato in §3): verifica che i notebook generati non scrivano nelle cartelle di E02, che nessun segnaposto resti irrisolto, che ogni notebook porti la propria finestra Z e il proprio input, che monti solo i dataset che gli servono, che la guardia della lista bianca preceda ogni lettura di maschera e che la prenotazione del budget rifiuti al confine.
- `scripts/kaggle_e03.py` ha, oltre ai comandi previsti, `publish-manifest` (A2) e `budget`.
- `configs/e03/source_manifest.json` è dichiarato in §3 come artefatto del passo 2b.

### A4 — il pooling locale ha richiesto due ripetizioni per disconnessione S3

- **Cosa è successo.** Sul portatile, i tre pooling di `pherc0814-46527` hanno incontrato `aiohttp ServerDisconnectedError: Server disconnected` (lo stesso errore che R02 aveva osservato e che il piano E02 prevedeva): un tentativo perso per `--z-start 13`, uno per `1`, uno per `25`.
- **Correzione.** Nessuna modifica al codice: lo script resta una riproduzione fedele di quello ufficiale, che non ha ritentativi. Si è **ripetuto il run**, come prescrive la procedura di E02, fino a tre tentativi. Tempi effettivi: 102 s, 95 s, 95 s; 0,8 GB letti per pooling.
- **Esito.** `--z-start 13` produce l'albero con impronta **`bc7423431221bf24b247a8ba80d264b0306f816c52b4ecc0d08115a82305ac52`**, identica a quella ufficiale di E02: lo script riproduce il pooling di villa byte per byte. Gli input spostati hanno impronte `f73364dc…` (−3) e `8406e615…` (+3); le 18 slice condivise coincidono esattamente con l'input ufficiale e le tre slice nuove differiscono, come atteso.

### A9, A10, A11 — tre difetti del generatore trovati dai run GPU (7 settembre 2026)

Tutti e tre hanno la stessa forma: una cella scriveva o cercava un nome diverso da quello che un'altra cella si aspettava, oppure usava qualcosa che in quel punto del notebook non esisteva ancora. Tutti e tre sono stati fermati dalle guardie prima di spendere inferenza; costo complessivo **4,7 minuti** di quota. Per ciascuno esiste ora un test che lo avrebbe intercettato.

- **A9 — `import zarr` nella guardia dell'input** (`infer-46527-s42-zm2` v1, 36 s). La guardia gira prima della cella di installazione, apposta, e importava una libreria non ancora presente. Ora legge `.zattrs` e `0/.zarray` come JSON. Test: nessuna cella prima dell'installazione importa librerie di terze parti.
- **A10 — segnaposto adiacenti** (`infer-46527-s42-zm2` v2, 3,2 min: l'inferenza è girata, il TIFF è stato scritto, ma non persistito). `__SEED____TAG__` perdeva il separatore: il log si chiamava `infer_seed42zm2.log` e la cella dei controlli cercava `infer_seed42_zm2.log`. I nomi dei file ora si calcolano in Python e arrivano alla cella come segnaposto unici. Test: la cella bash e le celle Python concordano sui nomi.
- **A11 — nome dell'input derivato dall'offset** (`infer-46527-s42-zm5` v1, 51 s). Gli offset ±5 usano l'input spostato di ±3 con la finestra spostata di ±2; la guardia cercava `…_pooled_zm5.zarr`. Il nome dello store ora segue il pooling (`INPUT_NAME`), non l'offset. Test: la corrispondenza offset → input per tutti i 24 run.
- **Registro del budget.** Un run fallito dopo pochi secondi costava l'intera prenotazione di 60 minuti: `output` ora chiude la prenotazione con la durata misurata (da `run_info.txt`, o dall'ultimo istante del log del kernel se il run non ha raggiunto la persistenza). Quota reale consumata dai 24 run più i 3 tentativi falliti: **128,2 minuti** su 240.

### A8 — il manifest del dataset delle label deve avere l'elenco per file (7 settembre 2026)

- **Cosa è successo.** Il run `prep-w016-z13` **tentativo 2** è arrivato fino alla cella delle label (checkout, installazione e mount corretti) e si è fermato con `KeyError: 'files'`: la cella riusata da E02 verifica il dataset **file per file** contro `manifest['segments'][<seg>]['files']`, e il manifest che avevo costruito aveva solo i totali.
- **Correzione.** Il dataset viene ora costruito da `scripts/build_e03_label_dataset.py` (nuovo, perimetro esteso come in A3), che riusa le funzioni congelate di `scripts/build_label_dataset.py`, scrive lo **stesso schema** di E02 (elenco di `{path, size, sha256}` per ogni file) e si ferma se le impronte non coincidono con quelle congelate o se il segmento sigillato compare. Un test verifica che il manifest costruito soddisfi ciò che la cella riusata pretende.
- **Verifica.** Manifest ripubblicato: 10.800 file elencati, 0 percorsi del segmento sigillato; i tar restano identici byte per byte a quelli di E02.
- **Costo.** Una seconda sessione CPU persa, nessuna quota GPU.

### A7 — `null` invece di `None` nelle costanti dei notebook CPU (7 settembre 2026)

- **Cosa è successo.** Il run `prep-w016-z13` **tentativo 1** è fallito alla prima cella: `EXPECTED_INDICES = null`, `NameError: name 'null' is not defined`. Il generatore scriveva le costanti con `json.dumps`, che per un valore assente produce `null`: valido in JSON, inesistente in Python. Nei run `infer-*` la costante non è mai nulla, quindi il difetto colpiva solo i run CPU, dove gli indici non servono.
- **Correzione.** Il generatore scrive `None` quando il valore è assente. Due test nuovi, che il difetto avrebbe fatto fallire: uno **compila** ogni cella Python di ogni notebook generato, l'altro **esegue** la cella delle costanti da sola e verifica che definisca tutti i nomi usati dalle celle successive.
- **Costo.** Una sessione CPU persa, nessuna quota GPU. Il run è stato ripetuto con lo stesso ID come tentativo 2, secondo la procedura.

### A6 — due difetti del pilota scoperti pubblicando il dataset delle label (7 settembre 2026)

- **Titolo troppo lungo.** Kaggle rifiuta un titolo oltre i 50 caratteri ("The dataset title must be between 6 and 50 characters"). I titoli dei dataset di E03 sono stati accorciati: `PapyrusLab E03-R01 labels (dev segments)` e `PapyrusLab E03-R01 input <tag> <segmento breve>`.
- **Esito dedotto dal testo.** `create_or_version` deduceva il successo cercando la parola "error" nell'output: il messaggio sopra non la contiene, quindi il pilota ha **dichiarato riuscita una pubblicazione fallita**. Ora l'esito si verifica interrogando lo stato del dataset dopo la chiamata, e la pubblicazione fallisce rumorosamente se non risulta `ready`.
- **403 transitorio.** Subito dopo un caricamento l'API risponde `403 Forbidden` allo stato per qualche secondo (già osservato in E01; qui due volte, poi `ready`). `dataset_status` ritenta fino a quattro volte a distanza di dieci secondi prima di dichiarare un errore.
- **Esito.** Dataset `papyruslab-e03-r01-labels` pubblicato e verificato: `ready`, con i soli due segmenti di sviluppo e **zero file** del segmento sigillato (controllato sull'elenco dei file pubblicati).

### A5 — dataset delle label proprio di E03 (dalla revisione R2, finding 1)

- **Cosa è successo.** Il piano riusava il dataset delle label di E02. Quello contiene anche `pherc1667-w029`: montarlo avrebbe portato l'artefatto sigillato dentro il perimetro di ogni notebook e, per via della guardia stessa, avrebbe fatto fallire ogni run.
- **Correzione.** `runs/E03-R01/dataset-labels/` contiene i tar dei **soli** due segmenti di sviluppo, ricostruiti dalle copie locali verificate con le funzioni congelate di `scripts/build_label_dataset.py`; i due tar risultano identici byte per byte a quelli di E02 (`tar_sha256` `32d3842a…` e `27f3e6ae…`). Si pubblica come `papyruslab-e03-r01-labels` con `python scripts/kaggle_e03.py publish-labels`, che rifiuta se il manifest non coincide con le impronte congelate.
- **Conseguenza.** Un passo in più prima dei run (pubblicazione del dataset delle label), da fare con il token Kaggle rigenerato.

---

## 12. Al termine

- [ ] Passi 0–12 eseguiti, **oppure** stop documentato al passo N con causa
- [ ] Criteri A e B di §5 verificati per 24 run e 4 prep (manifest di sorgente, lista bianca, matrice completa compresi); letture di §5 C compilate nella scheda
- [ ] Scheda, manifest, `configs/e03/*.json`, `docs/reports/e03-r01/metrics/*.json` scritti; output in `runs/E03-R01/` con `differenze: 0`
- [ ] Revisioni R1–R3 registrate con finding classificati; S1–S3 del socio consegnati e fusi (decisione di Matteo)
- [ ] Documenti canonici aggiornati; commit e push del lavoro verificato
- [ ] Fuori perimetro emersi: annotati; condizioni di ripensamento: **a Matteo**
