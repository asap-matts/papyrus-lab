# Dossier di ingresso per E00

**Stato:** ricerca tecnica preparatoria; non è ancora un piano eseguibile

**Rilevazione:** 5 settembre 2026

## Decisione proposta

Usare come primo controllo noto il segmento **w035 di PHerc. 0139**, nel surface volume nativo a 9,362 µm. È più adatto del w043 mostrato nel quick start ufficiale perché il livello 0 di w035 resta sotto il limite iniziale di 1 GiB e nel dataset ufficiale `ink_9um` esiste una label nativa corrispondente.

Questa è una proposta da congelare soltanto nel futuro piano E00. w035 fa parte dei dati usati per addestrare `ink_9um`: è quindi adatto a verificare che la catena funzioni, ma non misura la capacità di trovare inchiostro mai visto.

## Input candidato

| Campo | Valore verificato |
|---|---|
| Rotolo | PHerc. 0139 |
| Segmento pubblico | `20260317000000-w035_2026031718` |
| Surface volume | `9.362um-1.2m-113keV-volume-20250728140407.zarr` |
| URL | `https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0139/segments/20260317000000-w035_2026031718/surface-volumes/9.362um-1.2m-113keV-volume-20250728140407.zarr` |
| Livello | `0` |
| Forma e ordine assi | `[28, 5820, 5240]`, ZYX |
| Tipo | `uint8` |
| Chunk | `[28, 128, 128]` |
| Scala | 9,362 µm sui tre assi |
| Compressione del livello 0 | nessuna |
| Dimensione logica del livello 0 | 853.910.400 byte, circa 814,35 MiB |

Forma, assi, scala e tipo sono stati letti direttamente dai metadati `.zattrs` e `0/.zarray` nell'open-data pubblico. La dimensione logica è il prodotto della forma per un byte; non è una misura del traffico effettivo di una lettura remota a chunk.

Il [model card ufficiale di ink_9um](https://huggingface.co/scrollprize/ink_9um) usa w043 nel quick start. w043 resta il fallback più aderente all'esempio pubblicato, ma il suo livello 0 è `[28, 6120, 8120]`, circa 1,296 GiB, e supera il limite prudenziale iniziale. Il [dataset ufficiale delle label](https://huggingface.co/buckets/scrollprize/datasets/tree/ink_9um) elenca invece w035 fra i cinque segmenti PHerc. 0139 nativi a 9,362 µm.

## Riferimento noto

La label proposta si trova nel bucket pubblico al prefisso:

```text
hf://buckets/scrollprize/datasets/ink_9um/labels/native9-scrollprizeorg-21slices/w035/
```

Il dossier del dataset dichiara `w035_inklabels.zarr` e `w035_supervision_mask.zarr`; l'annotazione è sul piano Z=14 di un array profondo 28 slice. L'acquisizione va limitata a questo prefisso e preceduta da una lista o da un dry run: il bucket completo misura terabyte e non deve essere sincronizzato. Hugging Face documenta `hf buckets list`, `hf buckets cp` e `hf buckets sync --dry-run` per operare su un prefisso.

Prima di E00 occorre ancora verificare dimensioni, file esatti e trasferimento previsto della sola label. La label servirà a confermare posizione e orientamento, non a proclamare generalizzazione.

## Software da congelare

Il model card rimanda al branch `merge-ink-pipelines` di villa, non al branch `main`. Le revisioni osservate sono:

| Componente | Revisione candidata |
|---|---|
| `ScrollPrize/villa`, branch `merge-ink-pipelines` | `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e` |
| `scrollprize/ink_9um` | `7109667e2607db1b90c37c8b09cb876ea7fe7bb1` |
| Python del preflight | `3.12.13` |
| PyTorch del preflight | `2.10.0+cu128` |
| CUDA del preflight | `12.8` |

La dipendenza dichiarata da `ink-detection/pyproject.toml` richiede Python almeno 3.11 e PyTorch 2.10.0, compatibili con il preflight osservato. Questo non verifica ancora l'installazione delle altre dipendenze.

Il comando di riferimento esposto dal branch è:

```text
uv run python -m koine_machines.inference.infer \
  <input.zarr> <checkpoint.pth> <output.tif> \
  --overlap 0.5 --blend-mode hann
```

Il metodo di installazione su Kaggle resta da provare senza GPU e poi da fissare nel piano. Non copiare alla cieca il comando storico `python -m vesuvius.ink_detection...`: il pacchetto e l'entry point correnti indicati dal model card sono `koine_machines` nel branch citato.

## Checkpoint candidati

Per evitare di scegliere il checkpoint dopo aver visto il risultato, la proposta iniziale è usare lo stesso step finale per entrambi i seed:

| File | Dimensione | SHA-256 pubblicato |
|---|---:|---|
| `hybrid_3d2d-seed42/step-075000.pth` | 138.360.039 byte, circa 131,95 MiB | `e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab` |
| `hybrid_3d2d-seed43/step-075000.pth` | 138.360.231 byte, circa 131,95 MiB | `2aeaa85a35ef28d7bc7bf3e848c4a6a91385e9132710927fdba41133c4ecb28f` |

Il model card avverte che step diversi reagiscono diversamente sui segmenti. E00 non deve trasformarsi in una ricerca opportunistica: prima seed 42 per il funzionamento minimo, poi seed 43 con gli stessi parametri per osservare la concordanza. Un eventuale confronto fra checkpoint diventerà un esperimento separato.

## Output e controlli attesi

Il codice candidato scrive un TIFF `uint8`, tiled e compresso LZW, con la stessa forma spaziale del livello scelto. Per w035 ci aspettiamo quindi una matrice `5820 × 5240`. Con il checkpoint a 17 slice e l'intero intervallo Z, il codice corrente dovrebbe selezionare le slice centrali 6–22; il log reale dovrà confermarlo.

E00 sarà superato soltanto se sono conservati e controllati:

1. log completo con revisione, comando, GPU, layer, patch, stride e numero di blocchi;
2. hash e dimensione dei due checkpoint scaricati;
3. TIFF grezzo senza riscalatura usato per le misure;
4. immagine di sola visualizzazione con trasformazione dichiarata;
5. confronto di posizione e orientamento con label e maschera;
6. esito del secondo seed, senza interpretare la concordanza come indipendenza completa.

Il model card spiega che, per la sola visualizzazione, le predizioni possono essere riscalate con `(p - 0,25) / 0,5`, mentre i TIFF grezzi vanno conservati per le analisi quantitative.

## Budget preliminare e punti aperti

- Due checkpoint richiedono circa 264 MiB complessivi.
- L'inferenza usa store temporanei in `float32`; dal codice risultano almeno due matrici spaziali, circa 233 MiB logici complessivi per w035, oltre a cache, modello e output.
- Tetto proposto: 30 minuti di sessione GPU per il primo tentativo; arresto immediato se input, layer o dipendenze non corrispondono.
- Non è ancora misurato quanto del surface volume remoto verrà trasferito né il tempo di inferenza sulle due T4.
- Va deciso se utilizzare entrambe le T4 con `--gpus 0,1` o iniziare con una sola; la decisione deve basarsi su una stima o una prova minima, non sull'assunzione che due GPU dimezzino il tempo.
- Occorre verificare il percorso più leggero per installare `koine_machines` su Kaggle senza portare dipendenze grafiche inutili.

Questi punti aperti impediscono di trattare questo dossier come comando autorizzato. Dopo revisione e commit della procedura, diventeranno prerequisiti verificabili nel piano E00.
