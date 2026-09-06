# Dossier di ingresso per E00

**Stato:** ricerca tecnica preparatoria, revisionata il 6 settembre 2026 ([rapporto](reports/2026-09-06-revisione-procedura-e00.md)); non è ancora un piano eseguibile. Le decisioni segnate come *decisione di Matteo* sono prese; il resto è proposta da congelare nel piano E00.

**Rilevazione:** 5 settembre 2026; verifiche su fonti primarie e correzioni il 6 settembre 2026.

## Decisione proposta

Usare come primo controllo noto il segmento **w035 di PHerc. 0139**, nel surface volume nativo a 9,362 µm. Tre ragioni, in ordine di forza:

1. È l'**esempio lavorato del tutorial ufficiale**: [tutorial5](https://scrollprize.org/tutorial5) dice testualmente *"The worked example is w035, a PHerc. 0139 segment from the models' own training set, so you know what a good result looks like before trying an unread scroll"*. Il model card usa invece w043 nel quick start; le due fonti ufficiali indicano segmenti diversi e w035 è quello scelto dal tutorial.
2. Nel dataset ufficiale `ink_9um` esiste una **label nativa** a 9,362 µm con la stessa forma del surface volume: il confronto output/label è diretto, pixel per pixel.
3. Il livello 0 pesa 814 MiB, contro 1,296 GiB di w043.

w035 fa parte dei dati usati per addestrare `ink_9um`, e vi compare **due volte**: come `pherc0139-w035` nella famiglia `aligned-scrollprizeorg-21slices` (dal volume a 2,399 µm ridotto) e come `w035` fra i cinque segmenti nativi a 9,362 µm. Il modello ha visto la stessa area fisica in due rappresentazioni: è il caso più favorevole possibile, adatto a verificare che la catena funzioni, e non misura la capacità di trovare inchiostro mai visto. In E02, escludere w035 significherà escluderlo da entrambe le rappresentazioni.

## Input candidato

| Campo | Valore verificato (fonte: `.zattrs` e `0/.zarray` nell'open-data, 6 settembre 2026) |
|---|---|
| Rotolo | PHerc. 0139 |
| Segmento pubblico | `20260317000000-w035_2026031718` |
| Surface volume | `9.362um-1.2m-113keV-volume-20250728140407.zarr` |
| URL | `https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/20260317000000-w035_2026031718/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr` |
| Livello | `0` |
| Forma e ordine assi | `[28, 5820, 5240]`, ZYX (`note_axes_order: "ZYX (slice, row, col)"`) |
| Tipo | `uint8` |
| Chunk | `[28, 128, 128]` |
| Scala | 9,362 µm sui tre assi |
| Compressione del livello 0 | nessuna (`compressor: null`) |
| Dimensione logica del livello 0 | 853.910.400 byte, circa 814,35 MiB |

Il README del dataset delle label indica esattamente questo file come volume sorgente di w035 nel training. Nello stesso segmento esistono anche surface volume a 2,399 µm e 1,129 µm e predizioni ufficiali di ink detection a quelle due risoluzioni: **non** esiste una predizione ufficiale a 9,362 µm, quindi il riferimento di E00 è la label, non un'immagine pubblicata.

**Traffico di rete previsto.** I chunk sono `[28, 128, 128]`: la profondità non è suddivisa, quindi leggere 17 slice su 28 trasferisce comunque il chunk intero. Con copertura piena, l'inferenza legge fino a **≈814 MiB** dal livello 0, più **≈12,7 MiB** per la scansione di occupazione al livello 3 (`[28, 728, 655]`). Non è una misura: è il massimo derivato dai metadati.

Il fallback w043 (`20260112000000-w043_2026011217`, livello 0 `[28, 6120, 8120]`, circa 1,296 GiB) è anch'esso nel training set, ma soltanto nella rappresentazione a 2,399 µm ridotta: per il volume nativo sarebbe un controllo meno "noto" di w035.

## Riferimento noto

La label si trova nel bucket pubblico Hugging Face al prefisso:

```text
hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w035/
```

Misurata il 6 settembre 2026 tramite l'API del bucket: **5.128 file, 737.833 byte (0,70 MiB)**, di cui 2.564 file per `w035_inklabels.zarr` (369.430 B) e 2.564 per `w035_supervision_mask.zarr` (368.403 B). Il costo dell'acquisizione è nel numero di richieste, non nella banda. Entrambi gli array hanno livello 0 `[28, 5820, 5240]`, `uint8`, chunk `[28, 128, 128]`, compressi (blosc/zstd): **stessa forma del surface volume**. Il README del dataset conferma: *"annotations made directly on native 9.362 µm PHerc. 0139 volumes. Arrays are 28 slices deep, annotated only at Z=14"* — il nome della cartella dice `21slices`, ma gli array nativi sono a 28.

Il bucket completo misura **3,35 TiB in 11,66 milioni di file** e non deve essere sincronizzato per intero. Il comando ufficiale del tutorial, ristretto al prefisso, è:

```text
uvx --from huggingface_hub hf buckets sync \
  hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w035 \
  ./data/labels/w035
```

Prima con `--dry-run` (stampa il piano senza trasferire; documentato per entrambe le direzioni), poi senza. `hf buckets cp` **non** serve: copia un solo file quando è coinvolto un percorso locale.

Attenzione ai nomi: il README del dataset avverte che i nomi `pherc0139-wNNN` della famiglia `aligned` **non seguono la numerazione pubblica** (`pherc0139-w016` è il segmento pubblico `w029`; `pherc0139-w028` è `w044`). Per w035 il nome coincide, ma per caso. Non dedurre mai l'identità di un segmento dal numero.

La label servirà a confermare posizione e orientamento, non a proclamare generalizzazione.

## Software da congelare

Esistono **due percorsi ufficiali**, entrambi del 14 agosto 2026:

| Percorso | Dove | Pacchetto | PyTorch richiesto | Chi lo cita |
|---|---|---|---|---|
| Branch `merge-ink-pipelines` di villa, commit `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e` (ultimo, 01:18 UTC) | `ink-detection/` | `koine_machines` | `==2.10.0` | Model card di `ink_9um` |
| `main` di villa (PR #1456, 21:24 UTC), poi in evoluzione | `vesuvius/src/vesuvius/ink_detection/` | `vesuvius.ink_detection` | `>=2.12,<3` (extra `models`) | Tutorial ufficiale |

Il secondo è la fusione e rifattorizzazione del primo nel pacchetto `vesuvius`: non è "storico", è il codice corrente. I due conservano gli stessi invarianti verificati per ispezione (overlap 0,5 di default, blending Hann, TIFF LZW, stessa formula per le slice centrali, `torch.compile` attivo di default).

**Decisione di Matteo (6 settembre 2026): E00 usa il branch `merge-ink-pipelines`** al commit indicato, perché è congelato (fermo dal 14 agosto) e richiede il PyTorch 2.10.0 che Kaggle ha già; `main` richiede oggi PyTorch ≥ 2.12, assente su Kaggle. L'equivalenza fra i due codici sullo stesso checkpoint è verificata leggendo il codice (L2), non misurata: resta un rischio residuo dichiarato.

| Componente | Revisione congelata |
|---|---|
| `ScrollPrize/villa`, branch `merge-ink-pipelines` | `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e` |
| `scrollprize/ink_9um` (Hugging Face) | `7109667e2607db1b90c37c8b09cb876ea7fe7bb1` |
| Python del preflight | `3.12.13` |
| PyTorch del preflight | `2.10.0+cu128` |
| CUDA del preflight | `12.8` |

### Installazione su Kaggle

`ink-detection/pyproject.toml` richiede Python ≥ 3.11 e `torch==2.10.0`, compatibili con il preflight. Ma il comando ufficiale `uv run …` ha due conseguenze verificate nel `uv.lock` del branch:

- la dipendenza `vesuvius` è dichiarata come **percorso locale del monorepo** (`[tool.uv.sources] vesuvius = { path = "../vesuvius" }`): serve il checkout di villa (circa 0,97 GiB per intero), non basta installare un pacchetto;
- `uv run` costruisce un ambiente isolato dal lock: **195 pacchetti, circa 4,3 GiB**, di cui circa 3,8 GiB per `torch`, `triton` e quindici librerie `nvidia-*-cu12`. Non usa il PyTorch preinstallato da Kaggle, lo duplica. Su Kaggle l'ambiente si azzera a ogni sessione, quindi il download si ripeterebbe ogni volta. Le librerie grafiche (`napari`, `pyqt6`) pesano solo circa 195 MiB: non sono il problema.

**Decisione di Matteo (6 settembre 2026): su Kaggle si usa il Python di sistema** con `pip install --no-deps` del pacchetto `koine_machines` dal checkout (parziale) di villa, aggiungendo soltanto le dipendenze effettivamente mancanti, in versione registrata nel piano. Prova a GPU spenta; subito dopo verificare che `torch.__version__` sia ancora `2.10.0+cu128`. È una deviazione dal comando ufficiale e va dichiarata come tale nella scheda dell'esperimento. Sul fisso e sul Mac, dove l'ambiente persiste, `uv run` resta la scelta naturale.

Non installare mai `vesuvius[models]`: nel branch richiede `torch>=2.6,<2.9`, incompatibile con `torch==2.10.0`. Le dipendenze base di `vesuvius` non includono torch e sono sufficienti.

### Comando candidato

Il comando pubblicato in `ink-detection/configs/README.md` è `uv run python -m koine_machines.inference.infer <input.zarr> <checkpoint.pth> <output.tif> --overlap 0.5 --blend-mode hann`; i due flag rendono espliciti i default. Il comando candidato per E00 aggiunge tre scelte motivate:

```text
python -m koine_machines.inference.infer \
  <URL del surface volume> <checkpoint.pth> <output.tif> \
  --overlap 0.5 --blend-mode hann \
  --no-compile --gpus 0 --batch-size 1
```

- `--no-compile`: nel codice `torch.compile` è **attivo di default** in modalità `reduce-overhead`. Su una Tesla T4, dentro un tetto di 30 minuti, il tempo di compilazione è un rischio di budget non necessario al controllo noto. Il codice degrada senza errore se la compilazione fallisce, ma il tempo si paga comunque.
- `--gpus 0`: una sola T4. Con più GPU il codice **disattiva `torch.compile`** e usa `DataParallel` (il meccanismo di PyTorch che copia il modello su ogni scheda e divide fra loro ciascun lotto di dati, con un costo di coordinamento a ogni passo): confrontare una e due GPU cambierebbe due variabili insieme. Il multi-GPU diventa una misura di costo separata, con `--no-compile` su entrambi i lati.
- `--batch-size 1`: il tutorial usa 32 "per una GPU grande" e consiglia 4 o 1 in caso di memoria insufficiente; per il primo tentativo si parte dal minimo.

Un fatto favorevole, letto nel config del training (`aligned21_hybrid_3d2d.json`): `mixed_precision: "fp16"`. Con `--amp-dtype auto` il codice usa quindi `float16`, nativo e veloce su T4. Il rischio "bf16 su Turing" non si presenta.

## Checkpoint candidati

Per evitare di scegliere il checkpoint dopo aver visto il risultato, si usa lo stesso step finale per entrambi i seed:

| File | Dimensione | SHA-256 pubblicato (verificato via API, 6 settembre 2026) |
|---|---:|---|
| `hybrid_3d2d-seed42/step-075000.pth` | 138.360.039 byte, circa 131,95 MiB | `e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab` |
| `hybrid_3d2d-seed43/step-075000.pth` | 138.360.231 byte, circa 131,95 MiB | `2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f` |

**La dimensione identifica il seed, non lo step:** tutti e sette i checkpoint di seed42 pesano 138.360.039 byte e tutti quelli di seed43 138.360.231. L'unico discriminante è lo SHA-256, che va verificato dopo il download.

Il model card avverte che step diversi reagiscono diversamente sui segmenti. E00 non deve trasformarsi in una ricerca opportunistica: prima seed 42, poi seed 43 con gli stessi parametri per osservare la concordanza. L'unica immagine ufficiale di confronto fra i due seed su w035 è a `step-020000`, non a `step-075000`: non è un riferimento a parità e non deve indurre a cambiare step dopo aver visto l'output. Un confronto fra checkpoint diventerà un esperimento separato.

## Output e controlli attesi

Il codice scrive un TIFF `uint8`, tiled e compresso LZW (`tifffile.imwrite(..., compression="lzw")`), con la stessa forma spaziale del livello scelto: per w035 una matrice `5820 × 5240`, identica al piano della label.

**Slice.** Il checkpoint lavora su 17 slice (`patch_size: [17, 128, 128]`). Con l'intero intervallo Z il codice seleziona `(28 // 2) − (17 // 2) = 6`, cioè gli indici **6–22**, il cui centro è 14: esattamente il piano su cui è annotata la label. Il commento nel codice dichiara che il crop replica quello del training (*"surface − patch_depth // 2"*). Il default è quindi corretto per w035 per costruzione; il log (`Selected source layer indices=…`) dovrà confermarlo. Il model card avverte che i modelli sono sensibili a un offset in Z: su altri segmenti la stessa regola può non valere.

**Direzione.** Il tutorial dichiara che i render pubblicati riproducono l'orientamento in profondità delle label di training (`--flip-normals`); `--direction both` serve per superfici proprie. Per il surface volume pubblicato di w035, `--direction forward` (default) è corretto.

**Store temporanei.** Le somme di probabilità e di pesi sono due array `float32` di `5820 × 5240` (232,67 MiB in tutto) scritti come Zarr **su disco temporaneo** in una cartella creata con `tempfile.mkdtemp()` — su Linux `/tmp`, ridirigibile solo con la variabile d'ambiente `TMPDIR` — e **cancellati a fine run**. Non sono conservabili come artefatto.

Il model card spiega che, per la sola visualizzazione, le predizioni possono essere riscalate con `(p − 0,25) / 0,5`: il training usa `bce_label_smoothing: 0.5`, quindi l'uscita più confidente di "assenza di inchiostro" sta vicino a 0,25. I TIFF grezzi vanno conservati per le analisi quantitative.

## Criterio di esito proposto

E00 verifica che dati, modello e orientamento siano collegati correttamente, non l'accuratezza del modello. Il criterio è calcolabile da uno script e va **congelato nel piano prima dell'esecuzione**. Tutte le misure si calcolano solo sui pixel con `supervision_mask = 1`: una regione non annotata è sconosciuta, non negativa.

**A. Gate di identità** (tutti obbligatori; uno solo fallito = E00 fallito): commit di villa e revisione Hugging Face uguali a quelli congelati; SHA-256 dei checkpoint scaricati uguali alla tabella; il log riporta gli indici di layer 6–22; il TIFF esiste con forma `(5820, 5240)` e tipo `uint8`.

**B. Gate di collegamento dati↔modello.**

- *Separazione.* **AUROC** dei valori grezzi del TIFF, positivi = `inklabels == 1`, negativi = `supervision_mask == 1 ∧ inklabels == 0`. L'AUROC (area sotto la curva ROC) misura quanto i valori sui pixel d'inchiostro superano quelli sui pixel di sfondo, senza scegliere una soglia. Proposta: **≥ 0,90 superato**; 0,75–0,90 esito anomalo da investigare (primo sospetto: offset Z); **< 0,75 fallito**. La soglia è una proposta motivata (segmento del training set: un modello sano deve fare molto bene) e va confermata nel piano.
- *Orientamento.* Ricalcolare l'AUROC con la label ruotata di 180°, riflessa su Y e riflessa su X: **quella non trasformata deve essere strettamente la massima**. Se una trasformazione vince, l'orientamento è sbagliato e E00 fallisce, qualunque sia il valore assoluto. Un errore di assi produce comunque un'immagine plausibile all'occhio: questo test lo smaschera, l'ispezione visiva no.

**C. Stabilità** (informativo, non bloccante): ripetere con seed 43 a parametri identici; registrare la correlazione di Spearman (misura fra −1 e 1 di quanto due mappe ordinano i pixel allo stesso modo, insensibile alla scala dei valori) fra i due TIFF sui pixel con `supervision_mask = 1` e la differenza fra le AUROC. Nessuna soglia: due seed condividono architettura e dati, la concordanza non è indipendenza.

**D. Arresto immediato:** superamento dei 30 minuti di GPU; forma del TIFF diversa da `(5820, 5240)`; indici diversi da 6–22; `torch.__version__` diverso da `2.10.0+cu128` dopo l'installazione; una trasformazione della label che batte l'originale.

**E. Formulazione ammessa in caso di successo:** *"la catena dati → modello → output è collegata correttamente su un segmento del training set, con orientamento verificato"*. Livello di evidenza L3. Non è ammesso scrivere che il modello "funziona", "trova inchiostro" o "è validato".

## Budget e limiti

| Voce | Quantità | Risorsa |
|---|---:|---|
| Surface volume w035 (lettura remota, massimo) | 814 MiB | rete; disco solo se cachato |
| Due checkpoint | 264 MiB | disco |
| Store temporanei | 233 MiB | disco `/tmp`, cancellati a fine run |
| TIFF di output (non compresso; LZW riduce) | ≤ 29 MiB | disco, da conservare |
| Label w035 | 0,70 MiB, 5.128 file | disco, da conservare |
| Checkout di villa | ≈ 0,97 GiB completo; molto meno se parziale | disco |
| Ambiente `uv run` (se usato) | ≈ 4,3 GiB | disco, non su Kaggle per decisione |

**Decisione di Matteo (6 settembre 2026):** il tetto di spazio locale per la prima prova è alzato a **10 GB** come soglia di allarme, non più 2 GB. Restano: input previsto sotto 1 GiB, 30 minuti di sessione GPU per il primo tentativo, nessuna spesa. Il tempo di inferenza sulla T4 non è stimabile senza eseguire.

## Ruoli per E00

Decisione di Matteo del 6 settembre 2026, registrata come richiede la procedura:

- **Writer** delle correzioni documentali e del piano E00: Claude, nella sessione che ha svolto le due revisioni, su incarico esplicito.
- **Revisore del piano** (sola lettura) e poi **revisore dell'esito** (log, output, confronto con la label): Codex, tramite plugin. Lavoro leggero in token, coerente con il budget Codex disponibile.
- **Esecutore** del notebook Kaggle e **arbitro** dei disaccordi: Matteo.
- **Socio:** non partecipa a E00; ripete a E01 dalle sole istruzioni salvate, senza aver visto l'esito. Se lo vedesse, la ripetizione non proverebbe più che le istruzioni bastano.
- Un preflight della GTX 1060 del fisso è un'attività separata, non prerequisito di E00.

## Prerequisiti prima del piano E00

Risolti dalla revisione: acquisizione della label (misurata, comando ufficiale), allineamento label/output (stessa forma), traffico previsto (derivato dai metadati), scelta del percorso software, scelta del metodo di installazione, tetto di spazio, ruoli.

Restano da eseguire, tutti senza GPU:

1. installazione provata sul Python di Kaggle, con elenco dei pacchetti aggiunti e verifica della versione di PyTorch;
2. accesso a Internet del notebook attivo e verificato con una richiesta a costo nullo verso l'URL dello Zarr e verso Hugging Face (il preflight del 5 settembre non ha usato la rete);
3. destinazione e persistenza di TIFF, log e manifest su Kaggle, e modalità di trasferimento fuori dalla sessione;
4. criterio di esito confermato e scritto nel piano;
5. label scaricata e hash dei checkpoint verificati, prima di accendere la GPU.

## Rischi residui che il controllo noto non elimina

1. Nessuna informazione sulla generalizzazione: w035 è il caso più favorevole esistente.
2. Kaggle non garantisce lo stesso hardware in sessioni future; tempi e picchi non sono riproducibili per contratto.
3. La geometria (mesh, appiattimento, rendering) non viene esercitata: E00 parte da un render pubblicato.
4. L'offset Z è corretto per w035 per costruzione, non in generale.
5. Le label sono state trasferite sui volumi pubblici con revisione dell'offset caso per caso: il riferimento ha un margine proprio.
6. La concordanza fra seed non è indipendenza.
7. Nessuna calibrazione: i valori del TIFF non sono probabilità.
8. Gli store intermedi vengono cancellati: un'analisi che li richieda impone una nuova esecuzione.
9. L'equivalenza fra il codice del branch e quello di `main` sullo stesso checkpoint è verificata per ispezione, non misurata.
