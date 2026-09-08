# E04 — Contratto d'uso dell'allineamento locale della profondità

**Stato:** scritto prima del congelamento del [piano E04](plans/2026-09-08-e04-allineamento-locale-profondita.md), letto in R1.

**Due modalità, separate di proposito.**

| | **Operativa** (questo documento, §"Sequenza operativa") | **Sperimentale** (piano E04 §4) |
|---|---|---|
| Su che cosa | un segmento **nuovo**, senza label | i due segmenti di sviluppo, con label |
| Guardia | `--mode new-segment` passato a **ogni** comando: il caricatore rifiuta qualunque percorso di label prima di aprire, leggere o elencare alcunché; nomi di segmento arbitrari ammessi | `--mode dev` (predefinito): ammette solo i due segmenti di sviluppo e le due impronte della lista bianca |
| Uscite | `out/e04/<segmento>/` | `docs/reports/e04-r01/` (JSON piccoli) e `runs/E04-R01/` (TIFF e mappe) |
| Passi in più | nessuno | scelta di τ, mappe e località, inviluppo e cross-fit, diagnostici, sensibilità, `validate-reports`, manifest |

I comandi delle due modalità stanno in un unico elenco già scritto, [`configs/e04/commands.json`](../configs/e04/commands.json) (schema 1.1: 95 voci `dev` compreso lo staging, 8 voci `new_segment`, varianti di griglia e di robustezza, artefatti attesi per ogni report con la coppia mosaico/dominio): il piano, questo contratto e `tests/test_e04_smoke.py` lo leggono, e un test fallisce se divergono.

**La modalità non è un preflight: è una proprietà di ogni processo.** `--mode new-segment` è obbligatorio su ogni comando della sequenza operativa; con quella modalità il caricatore comune (`scripts/e04_io.py`) rifiuta con errore qualunque percorso che contenga label, maschere di validazione o supervisione, **prima** di aprirlo. I sottocomandi che esistono solo per la valutazione (`base --labels`, `inventory --analytic`, `evaluate`) sono rifiutati in modalità operativa. `tests/test_e04_mode.py` esegue la sequenza operativa in una cartella che contiene label-esca e verifica strumentalmente (patch di `open`, `os.stat`, `glob`) che nessuna di esse venga toccata.

Se E04 conclude che lo stimatore non funziona, questo documento resta come specifica di ciò che è stato provato, con l'esito scritto in fondo.

## Che cosa fa

Stima, per mattonelle di 64 × 64 px del surface volume a 21 fette (livello 2, ≈ 9,6 µm per fetta e per pixel), di quante fette il foglio di papiro è spostato rispetto al profilo tipico del segmento, **senza label**. Usa la stima per comporre una predizione d'inchiostro a partire da inferenze `ink_9um` fatte a offset uniformi diversi. Corregge solo la **componente locale**: la mediana degli spostamenti del segmento è zero per costruzione, perché senza label uno spostamento uniforme non è stimabile con questa caratteristica.

## Input

| Input | Formato | Note |
|---|---|---|
| Surface volume pooled a 21 fette | zarr `uint8` `(21, H, W)`, formato `level2-zmean4-21slice-v1` di villa | lo stesso che si dà a `ink_9um` |
| Predizioni uniformi | TIFF `uint8` `(H, W)`, una per k ∈ {−5, −3, −2, 0, +2, +3, +5}, per seed | da `villa infer --layer-start/--layer-end` (|k| ≤ 2) o dal pooling spostato di `scripts/e03_pool_shifted.py` (|k| ≥ 3) |
| `configs/e04/grid.json` | JSON congelato | tutte le costanti: griglia, buffer, τ o `estimator_disabled`, calibrazione, seed |
| Cartella dei sette TIFF | `--preds <dir>` con i file `pred_s<seed>_k<k>.tif` (k in `m5,m3,m2,0,p2,p3,p5`) | l'elenco atteso è in `configs/e04/commands.json`; un file mancante ferma il comando |
| Label (solo per valutare) | cartella nella lista bianca di `scripts/e03_metrics.py` | non serve per stimare né per comporre |

**Costo della modalità compatibile**, l'unica di E04: sette inferenze uniformi per seed, circa 7 × una inferenza normale (per w016, ≈ 35 minuti di GPU Kaggle per seed). La **modalità efficiente** (una sola inferenza con le 17 fette scelte per patch dalla mappa) è lavoro successivo e prima di essere proposta deve superare il test di equivalenza: una mappa costante k deve produrre bit a bit l'output dell'inferenza uniforme a k.

## Output

| File | Formato | Contenuto |
|---|---|---|
| `offsets_T_<segmento>.json` | JSON | per mattonella: L\*, k̂, confidenza, astensione e motivo; mediana degli L\*; `schema_version` |
| `offset_map.tif` | TIFF `int8` `(H, W)` | k̂ per pixel, in **fette** (positivo = foglio a indici più alti, il modello guarda più in profondità); in µm = fette × 9,596 |
| `confidence_map.tif` | TIFF `uint8` `(H, W)` | prominenza del picco di correlazione, 0–255 |
| `abstention_mask.tif` | TIFF `uint8` `(H, W)` | 1 = astensione: lì il mosaico usa k = 0 |
| `coverage.json` | JSON | copertura, frazione di astensioni per motivo, distribuzione dei k̂, entropia della mappa |
| `mosaic_<segmento>_s<seed>_T.tif` | TIFF `uint8` `(H, W)` | predizione composta, **sulla scala dei punteggi di k = 0** (calibrazione senza label) |
| `manifest.json` | JSON | impronte SHA-256 di volume, TIFF di ingresso e di uscita, versioni degli script, `grid.json` usato, comandi risolti, tempi, costo |

La mappa di offset è **diagnostica**: dice dove il profilo del foglio si scosta dal tipico, non dove c'è inchiostro. Non va mostrata come evidenza di testo.

## Sequenza operativa (segmento nuovo, senza label)

Shell: Git Bash o qualunque shell POSIX; su PowerShell sostituire `$VAR` con `$env:VAR` o scrivere i percorsi per esteso. Un comando per riga, nessuna continuazione di riga. Sostituire i tre percorsi in cima.

```sh
PY=./.venv/Scripts/python.exe
SEG=<nome-segmento>
SEED=42
VOL=<percorso>/${SEG}_pooled.zarr
PREDS=<percorso>/preds_${SEG}          # 7 file: pred_s42_k{m5,m3,m2,0,p2,p3,p5}.tif
OUT=out/e04/${SEG}

$PY scripts/e04_tiles.py base --mode new-segment --seg $SEG --grid configs/e04/grid.json --volume $VOL --preds $PREDS --out $OUT/base.json
$PY scripts/e04_tiles.py inventory --mode new-segment --seg $SEG --grid configs/e04/grid.json --volume $VOL --out $OUT/tiles.json
$PY scripts/e04_calibrate.py --mode new-segment --seg $SEG --grid configs/e04/grid.json --volume $VOL --preds $PREDS --seed $SEED --out $OUT/cal_s${SEED}.json --out-tifs $OUT/cal_s${SEED}/
$PY scripts/e04_features.py profiles --mode new-segment --seg $SEG --grid configs/e04/grid.json --volume $VOL --out $OUT/profiles.json
$PY scripts/e04_features.py estimate --mode new-segment --seg $SEG --grid configs/e04/grid.json --grid-variant g64_o0 --profiles $OUT/profiles.json --out $OUT/offsets_T_${SEG}.json --maps $OUT/maps/
$PY scripts/e04_mosaic.py equivalence --mode new-segment --seg $SEG --grid configs/e04/grid.json --grid-variant g64_o0 --preds $OUT/cal_s${SEED}/ --seed $SEED
$PY scripts/e04_mosaic.py compose --mode new-segment --seg $SEG --grid configs/e04/grid.json --grid-variant g64_o0 --map $OUT/offsets_T_${SEG}.json --preds $OUT/cal_s${SEED}/ --calibration $OUT/cal_s${SEED}.json --seed $SEED --out $OUT/mosaic_${SEG}_s${SEED}_T.tif
$PY scripts/e04_manifest.py --mode new-segment --seg $SEG --grid configs/e04/grid.json --out $OUT/manifest.json
```

`e04_calibrate.py` scrive sia il JSON delle mappe di calibrazione sia i **sette TIFF calibrati** in `--out-tifs`; `compose` legge quelli e verifica che il JSON di calibrazione corrisponda alle loro impronte. I nomi dei file prodotti sono esattamente quelli della tabella degli output.

**Smoke test end-to-end preregistrato** (`tests/test_e04_smoke.py`): estrae i comandi **letteralmente** da questo blocco e dalla sequenza sperimentale del piano §4 tramite `configs/e04/commands.json`, li esegue su un fixture sintetico di 8 × 8 mattonelle prodotto da `scripts/e04_synth.py --fixture`, verifica che ogni artefatto della tabella degli output esista e sia leggibile e che l'equivalenza valga. `tests/test_e04_mode.py` ripete la sequenza in una cartella con label-esca e verifica strumentalmente (patch di `open`, `os.stat`, `glob`) che nessuna venga toccata.

## Limiti dichiarati

- Provato su due segmenti di sviluppo, due seed, sette offset campionati: nessuna affermazione su altri rotoli.
- Corregge solo spostamenti **locali** rispetto alla mediana del segmento. Lo spostamento uniforme resta a carico dell'utente: E03 ha mostrato che può valere fino a 0,11 di AUROC e che il verso cambia da segmento a segmento.
- Compositore a mattonelle dure, senza fusione ai bordi; offset intermedi (±1, ±4) non misurati.
- Dove il profilo è piatto, multimodale o con picco al bordo, lo stimatore si astiene: la percentuale di astensione è parte dell'output. Se `grid.json` porta `estimator_disabled: true`, lo strumento si astiene ovunque e il mosaico coincide con la finestra ufficiale.
- Le regioni annotate disponibili in E04 sono piccole (tre regioni che intersecano 47 celle da 128 px) e su dati osservazionali nessun nullo per traslazione è difendibile come test esatto: la valutazione di E04 è **descrittiva e preregistrata**, senza p-value nei criteri e senza intervalli che sostengano da soli una conclusione. Questa procedura è proposta come **candidato**, non come metodo validato.
- Se il segmento non produce abbastanza mattonelle valide non piatte (meno di 16), lo stimatore va in **astensione totale** (`no_template`) e il mosaico coincide con la finestra ufficiale.

## Esito

*Da compilare al passo 7 di E04: quale delle tre conclusioni di §1 del piano si è realizzata, con i numeri.*
