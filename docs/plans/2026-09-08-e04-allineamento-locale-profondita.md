# E04 — Dall'avviso allo strumento: allineamento locale della profondità senza label

**Scritto da:** Claude Code · **Esecutore previsto:** Claude Code (writer), Codex (revisore), socio (riproduzione in cieco)
**Data:** 2026-09-08 · **Branch:** `main` (socio su `e04-socio`) · **Commit di partenza:** *da compilare al congelamento*
**Stato:** bozza v10, dopo co-progettazione e nove giri R1 (§10). In attesa del decimo giro R1. **Nessun passo eseguito, e nessuno si esegue senza il "vai" esplicito di Matteo** (§9), compresi i passi a costo GPU zero.

> Verifica prima di iniziare: `git rev-parse --short HEAD` deve restituire il commit sopra. Se non corrisponde, **fermati**.

---

## 1. Obiettivo

Alla fine deve essere vero, con criteri scritti qui prima di misurare: (a) sappiamo se l'offset di profondità che rende meglio **varia dentro un segmento**, mattonella per mattonella, in modo spazialmente coerente; (b) conosciamo l'**inviluppo superiore** descrittivo del guadagno ottenibile scegliendo l'offset per mattonella con le label, e una stima **cross-fitted su blocchi spaziali separati da un buffer** di quanto la mappa dei k\* si trasferisce a pixel vicini non usati per sceglierla; (c) sappiamo se **un solo stimatore senza label e senza parametri tarati sulle label** (T, §2.4), congelato prima di vedere i dati reali, produce un mosaico che batte la finestra ufficiale k = 0 su ciascuno dei due segmenti di sviluppo, e **se batte anche il miglior offset uniforme di quel segmento** scelto con le label (confronto valutativo, non disponibile a un utente); (d) esiste un [contratto d'uso](../e04-contratto-uso.md) con cui un utente applicherebbe la stessa procedura a un segmento nuovo.

T corregge per costruzione solo la **componente locale** dello spostamento (la mediana dei suoi spostamenti è zero): E04 non afferma che T sostituisca la scelta di uno spostamento uniforme.

**Limite dichiarato prima di partire: E04 non produce affermazioni inferenziali.** Due ragioni, entrambe strutturali e note prima di iniziare (§2.5): l'area annotata è minuscola (tre regioni che intersecano 47 celle del reticolo da 128 px), e su dati osservazionali di questo tipo nessun nullo per traslazione è difendibile come esatto, perché la maschera annotata e la difficoltà del modello non sono stazionarie nello spazio. **Quindi: nessun p-value entra nei criteri, nessun intervallo sostiene da solo una conclusione.**

La forza di E04 sta altrove, ed è il tipo di forza che ha reso credibile E03: criteri scritti prima di misurare; ogni condizione richiesta su **quattro combinazioni** (due segmenti × due seed) e non in media; **quattro sensibilità** preregistrate che devono concordare nel segno; **controlli nulli** riportati come diagnostica; riproduzione **in cieco** del socio; e un contratto d'uso che rende la procedura applicabile e falsificabile da terzi. È un risultato descrittivo replicato, non una stima con incertezza quantificata, e si scrive con questa etichetta ovunque. In particolare: nessuna ipotesi di §5 è decisa da un p-value, da un percentile di permutazioni o da un intervallo; ranghi, percentili e intervalli si riportano **accanto** ai risultati come diagnostica, mai come condizione. Esito massimo raggiungibile: "candidato operativo su due casi di sviluppo, per criteri descrittivi preregistrati soddisfatti su tutte e quattro le combinazioni e su tutte le letture di robustezza". Esito intermedio: "correzione locale utile ma inferiore a uno spostamento uniforme ben scelto, che senza label non è disponibile". Esito negativo: inviluppo, trasferimento e il motivo per cui T non recupera il guadagno. Tutti e tre si scrivono con lo stesso spazio. Zero minuti GPU.

---

## 2. Contesto necessario

### 2.1 Fatti verificati (E03-R01, 7 settembre 2026)

- Modello `ink_9um` (villa `3ea17f5…`, checkpoint seed 42 `e635558a…` e seed 43 `2aeaa85a…`, step 75000). Input 21 fette pooled (media di 4 piani su 109; 9,596 µm per fetta e per pixel al livello 2); il modello vede 17 fette, di norma indici 2–18.
- Predizioni in locale, autenticate nel [manifest E03](../reports/2026-09-07-e03-r01-manifest.json): per segmento (`pherc0139-w016`, `pherc0814-46527`) e seed, un TIFF `uint8` per k ∈ K = {−5, −3, −2, 0, +2, +3, +5}; 28 TIFF (i 4 a k = 0 sono di E02). `runs/` ignorata da git.
- Label held-out (`validation_mask == 1`, piano 10): w016 178 146 px in due regioni (bbox `[4944:5425, 3655:3955]` ≈ 481 × 300 px; `[4955:5322, 1803:2131]` ≈ 367 × 328 px); 0814 161 051 px in una regione (`[1624:2035, 258:817]` ≈ 411 × 559 px). Tre regioni annotate connesse: **l'unità di conclusione è il segmento**; le regioni sono unità di controllo del danno. `supervision_mask` separata; `pherc1667-w029` **sigillato** fino a E05.
- Curva E03: perdita massima held-out vs k = 0 pari a 0,111; 0814 favorisce k > 0 con entrambi i seed (seed 43 ancora in crescita a +5: massimo **censurato**); w016 favorisce k < 0 con il seed 42 e k = 0 con il seed 43. Sui pixel di training la perdita massima è 0,027.
- Volumi a 21 fette in locale: 0814 (`runs/E03-R01/local-input/pherc0814-46527_z13.zarr`, `bc742343…`) e spostati z1/z25. w016 non è in locale (≈ 11 GB; disco libero 27 GB): dataset Kaggle `papyruslab-e02-input-w016`.
- Strumenti congelati riusabili: `scripts/e02_metrics.py`, `scripts/e03_metrics.py` (`check_labels_allowed`: lista bianca per identità e impronta, `LABEL_ALLOWLIST` con le sole due impronte di sviluppo), `scripts/e03_curve.py`, `scripts/e03_pool_shifted.py`, `scripts/kaggle_e03.py`, `scripts/tree_sha256.py`.

### 2.2 L'idea, in una riga per gradino

1. **Località.** Se l'offset migliore varia per mattonella con coerenza spaziale, lo spostamento uniforme di E03 sottostima il problema.
2. **Inviluppo e trasferimento.** Scegliere per mattonella l'offset con le label dà l'inviluppo superiore, descrittivo. Scegliere su blocchi spaziali e valutare su blocchi separati da un buffer dice quanto la mappa si trasferisce.
3. **Stimatore senza label.** Il profilo di luminosità lungo le 21 fette dice dove sta il foglio in ogni mattonella; il ritardo che lo allinea al profilo mediano del segmento stima lo spostamento locale.
4. **Mosaico.** Una predizione composta dalle 7 esistenti, riportate alla scala dei punteggi di k = 0, con l'offset di T per mattonella.

### 2.3 Verifica di novità (8 settembre 2026)

Ricerca di Claude (web, tre interrogazioni su "offset map / per-tile / local z offset / depth alignment / z-alignment / sheet position" con "vesuvius", "ink detection", "surface volume", "ink_9um", "layer-start"; più l'abstract di arXiv 2606.29085, "Complete virtual unwrapping and reading of a rolled Herculaneum papyrus"). **Esito: nessuna fonte trovata che stimi o applichi un offset di profondità locale, per mattonella o per patch, all'inferenza dell'inchiostro.** Le fonti raggiunte descrivono il surface volume come pila di layer a offset fissi lungo la normale (Data Formats, tutorial 5), `--layer-start/--layer-end` uniformi e le opzioni `--overlap`/`--blend-mode` di `villa infer` (utili per la modalità efficiente futura), il tiling 256 px delle soluzioni Kaggle 2023 per la selezione dei campioni, non per l'allineamento. L'abstract dell'articolo 2026 non tratta offset, allineamento Z né sensibilità alla posizione della superficie (PDF completo non letto: compito S1 del socio). Registro community: R13 (inkalign: sweep Z con punteggio senza label su un ROI, **uniforme**), R14 (measure-before-you-hunt: curva AUC(offset) su un segmento di training, **uniforme**). Limite: Discord e repository non indicizzati non consultati; la novità è "non individuata nelle fonti consultate".

### 2.6 Le quattro varianti di robustezza sono ricostruzioni, non riletture

Ogni variante rifà davvero ciò che il suo nome dice, e i suoi input hanno impronte diverse da quelli della variante primaria; `validate-reports` **rifiuta** due report che dichiarino lo stesso mosaico. L'elenco completo dei comandi, con input e uscite per ciascuna delle quattro combinazioni segmento × seed, è in `configs/e04/commands.json` (`robustness_variants` e `artifacts_by_report`).

**Tre varianti ricompongono davvero** (mosaici con impronte diverse) e **una cambia solo il dominio di valutazione** sul mosaico primario. Ogni report è identificato dalla coppia (impronta del mosaico, impronta della maschera di valutazione); `validate-reports` **rifiuta** due report che condividano la coppia; `primary` e `inner8` condividono per costruzione l'impronta del mosaico e differiscono in quella della maschera, e il test lo verifica esplicitamente.

| Variante | Tipo | Che cosa cambia | Artefatto |
|---|---|---|---|
| `primary` | ricomposta | — | mappa su griglia 64 origine (0,0), TIFF **calibrati** |
| `raw` | ricomposta | punteggi non calibrati | stessa mappa, `compose` sui **TIFF grezzi**: mosaico diverso |
| `g128` | ricomposta | griglia 128 | **T rieseguito** su mattonelle 128 (profili, template, L\*, centraggio, astensione), nuovo `compose`: mosaico diverso |
| `o32` | ricomposta | origine (32,32) | **T rieseguito** sulla griglia traslata, nuovo `compose`: mosaico diverso |
| `inner8` | dominio di valutazione | nessuna ricomposizione | **stesso mosaico primario**, valutato sui soli pixel held-out a ≥ 8 px dal bordo della propria mattonella: misura quanto il guadagno dipenda dalle discontinuità del compositore |

In tutto: 16 mosaici (4 combinazioni × 4 varianti ricomposte) e 20 report, tutti con coppia distinta. La lettura a **blocchi mobili** resta una diagnostica del bootstrap (§2.4) e non è una variante di HD.

### 2.5 Numerosità: limiti geometrici noti e rami preregistrati

I conteggi qui sotto usano **lo stesso reticolo di §2.4** (origine globale (0, 0), celle parziali ammesse se idonee). Sono limiti **superiori**: quante celle del reticolo la bbox di ogni regione interseca. Quante di queste siano *idonee* (≥ 200 px held-out con ≥ 20 per classe) dipende dalle maschere e si conta al passo 0. Il limite **inferiore** (celle interamente dentro la bbox) è riportato per capire l'ordine di grandezza.

| Regione | Bbox | Celle 128 intersecate | Celle 128 intere | Celle 256 intersecate | Celle 256 intere |
|---|---|---|---|---|---|
| 0814, unica | `[1624:2035, 258:817]` | 20 | 12 | 6 | 2 |
| w016, regione 1 | `[4944:5425, 3655:3955]` | 15 | 6 | 6 | 1 |
| w016, regione 2 | `[4955:5322, 1803:2131]` | 12 | 4 | 4 | 1 |
| **0814** | | **20** | 12 | **6** | 2 |
| **w016** | | **27** | 10 | **10** | 2 |

Il buffer b = max(96, RF) dipende dal campo ricettivo, calcolato al passo 0: **b non è noto adesso** e con b maggiore i conteggi per piega calano.

**Rami preregistrati (si applica quello vero al passo 0; nessun criterio si emenda dopo aver letto i conteggi).**

| Conteggio osservato al passo 0 | Che cosa è dichiarabile |
|---|---|
| Segmento con ≥ 8 blocchi 128 idonei | intervalli **indicativi** per quel segmento, etichettati con il numero di unità; nessuna conclusione poggia su di essi da soli |
| Segmento con < 8 | nessun intervallo per quel segmento: sole stime puntuali |
| Regione con ≥ 8 blocchi 128 idonei | intervallo indicativo di danno per quella regione |
| Regione con < 8 | danno per regione come stima puntuale, regola descrittiva "nessuna regione peggiora più di 0,02" |
| Segmento con ≥ 8 blocchi 256 idonei | sensibilità alla scala di dipendenza **calcolata**; se il segno cambia fra 128 e 256, risultato non robusto e HC/HD non dichiarabili |
| Segmento con < 8 blocchi 256 | sensibilità **non calcolabile**: robustezza alla scala di dipendenza dichiarata **non verificata**; al suo posto la lettura a blocchi mobili 128 con passo 64, dichiarata anticonservativa |
| Piega con ≥ 2 blocchi idonei | cross-fit **descrittivo** per quel segmento (stima puntuale, nessun intervallo) |
| Piega con < 2 | cross-fit "non eseguibile"; resta l'inviluppo descrittivo |

**Aspettativa dichiarata, non un risultato:** con i limiti superiori della tabella e b ≥ 96, è probabile che la sensibilità a 256 non sia calcolabile e che il cross-fit resti descrittivo. Il piano è scritto perché **entrambi i mondi** producano una scheda leggibile: **nessuna conclusione di E04 poggia su uno strumento inferenziale**, né intervalli né ranghi, ma su soglie descrittive preregistrate verificate su quattro combinazioni e cinque letture di robustezza. Se al passo 0 i conteggi risultassero migliori del previsto, si applica il ramo corrispondente della tabella, sempre senza toccare §5.

### 2.4 Specifiche deterministiche (tutte in `configs/e04/grid.json`, congelate al congelamento del piano)

**Geometria.**
- Mattonelle primarie 64 × 64 px, origine (0, 0) dell'immagine. Sensibilità preregistrate: 128 × 128 origine (0, 0); 64 × 64 origine (32, 32).
- Maschera geometrica valida **G**: pixel con valore ≠ 0 nella fetta 10 del volume pooled ufficiale (k = 0). Uguale per tutti gli offset e i seed. Nessuna label.
- Mattonella **geometricamente valida**: ≥ 90 % dei suoi pixel in G. È l'unico requisito per entrare nel pool del template e nella copertura potenziale.
- **Idoneità analitica** (usa le label; solo per AUROC locali e mappe): ≥ 100 px held-out d'inchiostro e ≥ 100 di sfondo nella mattonella.
- **Blocchi inferenziali** 128 × 128 px, origine (0, 0), reticolo fisso; un blocco è **idoneo** se ha ≥ 200 px held-out con ≥ 20 d'inchiostro e ≥ 20 di sfondo; i blocchi parziali al bordo della regione contano se idonei. Ogni blocco appartiene a una sola regione (quella della maggioranza dei suoi pixel held-out). **k\* di un blocco** = il k che massimizza l'AUROC held-out calcolata sui pixel del blocco, con le stesse regole di margine, pareggi e censura definite per le mattonelle; è una quantità distinta dai k\* delle mattonelle che il blocco contiene.
- **Pieghe spaziali (superblocchi).** Per ciascuna regione: un solo taglio, perpendicolare al lato **più lungo** della sua bbox, alla mediana dei pixel held-out lungo quell'asse; piega A = lato di indice minore, piega B = l'altro. **Fascia esclusa** di larghezza b centrata sul taglio: i suoi pixel non entrano né in selezione né in valutazione. Così ogni pixel di B dista ≥ b da ogni pixel di A. Nessuna scacchiera: l'alternanza a blocchi non è compatibile con un buffer più largo del lato del blocco.
- **Buffer** b = max(96 px, RF) arrotondato al multiplo di 32 superiore, dove RF è il campo ricettivo in piano di `ink_9um` stimato analiticamente dal codice di villa al passo 0 (kernel, stride, profondità); se non stimabile, RF = 128.

**Gate di numerosità: la tabella normativa è quella di §2.5**, e vale in ogni caso; qui non si ripete alcuna condizione, per non crearne una seconda che possa contraddirla. Nessun conteggio, comunque vada, trasforma una lettura descrittiva in una inferenziale: gli intervalli, quando calcolabili, sono etichettati "indicativi" con il numero di unità e non sostengono da soli alcuna conclusione (§1). Un'unità sotto il gate non ha intervalli: le sue statistiche restano descrittive e ogni ipotesi che richieda un intervallo su quell'unità è **non dichiarabile**. Le regioni annotate sono piccole (§2.1: 411 × 559, 481 × 300, 367 × 328 px) e i blocchi indipendenti saranno pochi: **è previsto e ammesso che il verdetto si fermi a "risultato descrittivo"**. Il conteggio reale si fa al passo 0 e si scrive nella scheda prima di qualunque AUROC. Non è ammesso ridurre il lato del blocco o il buffer per far passare un gate.

**Bootstrap spaziale appaiato (indicativo).** Unità = blocchi idonei 128 × 128 al livello del **segmento**; per le regioni e per la scala 256 vale la tabella di §2.5. Lettura secondaria sempre riportata: blocchi mobili 128 con passo 64, dichiarata anticonservativa. Nessun intervallo, da solo, sostiene una conclusione (§1). Ricampionamento con reinserimento **stratificato per regione** (ogni regione ricampiona i propri blocchi, stesso numero). A ogni replica si ricalcolano, sugli stessi pixel ricampionati e appaiati, l'AUROC globale **e** l'F1 alla soglia 91 sia del riferimento sia della variante, e le loro differenze Δ = variante − riferimento; 2 000 repliche; seed 20260908; intervallo percentile. Guadagni: intervallo bilaterale al 95 %, si legge il **limite inferiore**. Danno: limite inferiore unilaterale al 95 %. Repliche con una classe assente sono scartate e contate; se supera l'1 %, l'intervallo è "non eseguibile" per quell'unità.

**Selezione di k\* per mattonella (con label).** k\* = argmax_k AUROC held-out della mattonella; pareggi risolti verso |k| minore, poi verso k < 0 (convenzione dichiarata, non motivata); k\* ≠ 0 solo se AUROC(k\*) − AUROC(0) ≥ 0,01 (margine), altrimenti k\* = 0; k\* = ±5 con AUROC(±5) > AUROC(±3) marcato **censurato**.

**Cross-fit spaziale (con label, valutativo).** Selezione sulla piega A, valutazione sulla piega B, poi scambio; la fascia esclusa le separa. Per ogni blocco idoneo di B, k̂ = k\* del blocco idoneo di A **più vicino** (distanza fra centri; pareggio → blocco di indice minore in ordine riga-colonna; se la regione non ha blocchi idonei in A, k̂ = 0). La valutazione usa tutti i pixel held-out dei blocchi idonei di B: la separazione ≥ b è già garantita dalla fascia. Incrocio sui seed: k\* scelto con il seed 42 e valutazione con il 43, e viceversa. Guadagno cross-fitted = media delle quattro combinazioni (A→B, B→A) × (42→43, 43→42) della Δ rispetto a k = 0; riferimento uniforme = miglior offset uniforme del segmento scelto sui soli pixel della piega di selezione. Sotto il gate di piega il trasferimento è "non eseguibile" e resta l'inviluppo descrittivo. **Test geometrico obbligatorio** (`tests/test_e04_folds.py`): su una configurazione densa sintetica il cross-fit deve produrre almeno 4 blocchi valutabili per piega; su una regione stretta deve dichiarare "non eseguibile" invece di valutare a vuoto.

**Calibrazione (senza label).** Per segmento e seed, per ogni k ≠ 0: istogrammi a 256 livelli di TIFF_k e TIFF_0 sui pixel di G; CDF con convenzione del punto medio, F(v) = (n_<v + n_=v / 2) / N; m_k(v) = il livello u di TIFF_0 che minimizza |F_0(u) − F_k(v)| (pareggio → u minore); m_k forzata monotona non decrescente (massimo cumulato); uscita `uint8`; nessuna interpolazione. Test con distribuzioni discrete degenerate e con padding a 0.

**Stimatore T (senza label; nessun parametro tarato su label).**
1. Profilo di una mattonella geometricamente valida: per z = 0…20, media dei valori del volume sui pixel della mattonella in G → p(z).
2. Normalizzazione: q(z) = (p(z) − mediana(p)) / MAD(p). Se MAD(p) = 0 → mattonella **piatta**: astensione, contata.
3. Template del segmento: mediana elemento per elemento dei q di **tutte** le mattonelle geometricamente valide non piatte. Congelato una volta calcolato (procedura monodirezionale: nessuna dipendenza dalla copertura). Se le mattonelle geometricamente valide non piatte sono **meno di 16**, si scrive `no_template: true` nel rapporto: il segmento è in **astensione totale** (k̂ = 0 ovunque, copertura 0, mosaico bit a bit uguale al TIFF calibrato di k = 0), come per `estimator_disabled`. Test dedicati: nessuna mattonella valida; tutte piatte; esattamente 15 e 16 valide.
4. Per L ∈ {−5, …, +5}: c(L) = correlazione di Pearson fra q(z + L) e template(z) sugli indici z con 0 ≤ z + L ≤ 20 (21 − |L| punti); se la varianza di uno dei due vettori è 0, c(L) = −1.
5. L\* = argmax c(L); pareggio → |L| minore → L < 0. Segno: L\* > 0 significa che il foglio della mattonella sta a indici più alti del tipico e il modello deve guardare più in profondità: k̂ ha lo stesso segno.
6. Confidenza: conf = c(L\*) − max{c(L) : |L − L\*| ≥ 2} (differenza fra il picco e il miglior valore fuori dal suo vicinato); in `confidence_map` come round(255 · max(conf, 0) / 2).
7. Astensione (k̂ = 0): conf < τ; oppure L\* = ±5 (picco al bordo, **censurato**); oppure piatta; oppure `estimator_disabled` = vero in `grid.json`, nel qual caso k̂ = 0 per **ogni** mattonella, la copertura è 0 e il mosaico coincide bit a bit con il TIFF calibrato a k = 0 (lo verifica il test di equivalenza). τ è fissato al passo 1b **solo su dati sintetici** (sotto).
8. Mappa a K: k̂ = elemento di K più vicino a L\*; pareggi (L\* = ±1 → 0; L\* = ±4 → ±3) risolti verso |k| minore.
9. **Centraggio imposto: ordine unico, senza ambiguità.** La sequenza è esattamente questa e i punti 7–8 vanno letti come sue fasi:
   1. per ogni mattonella geometricamente valida: profilo, normalizzazione, correlazione, L\* **grezzo** e confidenza (punti 1–6);
   2. **astensione**: piatta, oppure conf < τ, oppure L\* grezzo = ±5, oppure `estimator_disabled`, oppure `no_template`;
   3. se **nessuna** mattonella resta non astenuta: astensione totale del segmento, mediana non definita, k̂ = 0 ovunque, e lo si registra;
   4. altrimenti M = mediana degli L\* grezzi delle sole mattonelle non astenute (con un numero pari di valori, la media dei due centrali arrotondata al pari); L\*_c = L\* − M per ogni mattonella non astenuta; M si registra nel rapporto;
   5. **fuori dominio**: L\*_c fuori da [−5, +5] viene ritagliato all'estremo e la mattonella è marcata `saturata`, contata a parte;
   6. **quantizzazione finale** a K sui valori centrati (punto 8), con gli stessi pareggi;
   7. **test di degenerazione** (punto 10) sulla mappa dei k̂ così ottenuta.
   Dopo il punto 4 la mediana degli L\*_c è 0 per costruzione, quindi una mappa costante diventa identicamente nulla e il suo mosaico coincide **bit a bit** con il TIFF calibrato di k = 0: non può soddisfare HC1. `tests/test_e04_features.py` verifica: mediana nulla dopo il centraggio; mappa costante → mosaico ≡ k = 0; astensione totale; saturazione dopo il centraggio; **mappa bilanciata senza segnale locale** (metà −2 e metà +2 per sola posizione), che supera mediana zero e non degenerazione ma deve essere smascherata da HC2 sui dati, come dichiarato.
10. **Degenerazione, bloccante per HD:** T è "uniforme" se, sui pixel coperti, la sua mappa dopo il centraggio è costante, oppure se più del 90 % delle mattonelle coperte riceve lo stesso k̂. In quel caso HD **non è dichiarabile**, quali che siano le Δ, e la scheda lo scrive con entropia della mappa e copertura.

**Soglia τ (passo 1b), solo su dati sintetici, generatore congelato qui.** `scripts/e04_synth.py`, `numpy.random.default_rng(20260908)` (PCG64), calcoli in `float64`, uscita `uint8` con arrotondamento al pari e ritaglio a [0, 255].
- **Disposizione:** griglia di 64 × 64 mattonelle (4 096; si usano le prime 4 000 in ordine riga-colonna), ciascuna 64 × 64 px × 21 fette.
- **Campo di profondità:** d = campo gaussiano sulla griglia delle mattonelle, ottenuto filtrando `rng.standard_normal((64, 64))` con un nucleo gaussiano di deviazione standard 2 mattonelle (`scipy.ndimage.gaussian_filter`, `mode="wrap"`, nessun effetto di bordo), poi standardizzato a media 0 e deviazione standard 1,5 fette e ritagliato a [−5, +5]. Il d vero di ogni mattonella è registrato in `synth.json`.
- **Profilo:** p(z) = B + A · exp(−(z − 10 − d)² / (2 σ_z²)), z = 0…20, con A ~ U[20, 80], B ~ U[60, 110], σ_z ~ U[1,5, 3,5] estratti per mattonella nell'ordine A, B, σ_z.
- **Secondo foglio:** nelle mattonelle di indice pari (esattamente metà) si somma A₂ · exp(−(z − 10 − d − δ)² / (2 σ_z²)) con A₂ ~ U[0,3 A, 0,6 A], δ = s₂ · u, u ~ U[6, 9], s₂ = +1 se l'indice è multiplo di 4, altrimenti −1 (entrambi i lati in proporzione fissa).
- **Mattonelle senza foglio:** quelle di indice ≡ 0 (mod 10), esattamente un decimo, hanno A = 0 (solo fondo e rumore) e nessun d vero: entrano nella copertura, non nell'accuratezza.
- **Rumore:** additivo per voxel, gaussiano, deviazione standard s ~ U[8, 20] per mattonella, da `rng.standard_normal((21, 64, 64))`.
- **Fixture:** i primi 16 profili generati sono salvati in `tests/fixtures/e04_synth_head.json` e la loro impronta SHA-256 è scritta in `grid.json`: se il generatore cambia, i test falliscono.
- **Metrica:** fra le mattonelle non astenute **con foglio**, frazione con |L\* − round(d)| ≤ 1; copertura = frazione di mattonelle non astenute sul totale.
- **Scelta:** τ = il più piccolo valore della griglia {0,05, 0,10, …, 2,00} per cui accuratezza ≥ 0,90 e copertura ≥ 0,50. Se nessun valore soddisfa entrambi, si scrive `estimator_disabled: true` e `tau: null`: T si astiene ovunque per costruzione (punto 7) e il ramo strumento si chiude con "profondità non identificabile con questa caratteristica". Nessuna verifica su pixel reali: i profili reali si leggono solo dopo che `grid.json` è committato.

**Controlli nulli.** Tutti attraversano l'intera pipeline (calibrazione, composizione, AUROC, F1) e producono la Δ rispetto a k = 0.
- **(i) Distribuzione di riferimento per traslazione (diagnostica, non un test).** Statistica: **una sola** Δ globale del segmento (variante meno riferimento, su tutti i pixel held-out del segmento). Gruppo **G**: per ogni regione, tutte le traslazioni cicliche della mappa dei k̂ sul reticolo delle mattonelle dentro la bbox della regione; per un segmento con più regioni, il **prodotto cartesiano** dei gruppi regionali, applicato simultaneamente; l'identità appartiene a G. Nessun filtro dipendente dai dati: gli squilibri di copertura e di classi indotti dalle traslazioni si **riportano** (minimo, mediana, massimo della copertura sui pixel valutati), non si usano per selezionare. Enumerazione completa se |G| ≤ 100 000, altrimenti 100 000 traslazioni estratte uniformemente da G \ {identità} (seed 20260908, senza reinserimento).
  - Si riporta il **rango** della Δ osservata nella distribuzione, la frazione r = #{g : Δ(g) ≥ Δ(identità)} / |G| e la risoluzione 1/|G| (per 0814, |G| = 63 → 0,016).
  - **r non è un p-value e non entra in HC né in HD.** Sotto un nullo osservazionale l'identità non è scambiabile con le traslazioni: la maschera held-out è irregolare, la difficoltà del modello non è stazionaria, e la posizione osservata della mappa non è uniforme sul gruppo. r dice soltanto quanto la coincidenza fra mappa e guadagno sia insolita rispetto a mappe con la stessa forma altrove: è un indizio, riportato come tale, ed è ciò che il disegno di E04 permette.
- **(ii) Nullo marginale (secondario, riportato).** Permutazione dei k̂ fra le mattonelle coperte entro regione, 100 000 estrazioni (seed 20260908): preserva solo le frequenze, non l'autocorrelazione; serve a mostrare quanto il nullo spaziale sia più severo.
- **(iii)** k = 0. **(iv)** miglior offset uniforme dell'**altro** segmento (non usa le label del target, ma non è disponibile su un rotolo nuovo: si dichiara). **(v)** miglior offset uniforme del **segmento target** scelto con le label (oracolo uniforme, valutativo).
- **(vi) Controllo dei profili permutati (bloccante per HD).** Trentadue permutazioni deterministiche congelate (seed 20260908) che scambiano fra loro i **profili** delle mattonelle geometricamente valide, lasciando invariata la geometria: T viene rieseguito su ciascuna, si compone e si valuta come per la mappa vera. Una mappa determinata dalla sola posizione, o comunque indipendente dal contenuto dei profili, produce guadagni **della stessa entità** in questi controlli. Requisito preregistrato: la Δ della mappa vera deve superare la **migliore** delle 32 di almeno **0,01**, su tutte e quattro le combinazioni; altrimenti HD non è dichiarabile, quale che sia il resto. Test di equivarianza (`tests/test_e04_features.py`): permutando i profili, la mappa di T deve seguire la permutazione; se non cambia, T dipende dalle coordinate e non dai dati, e il test fallisce.
- **Test obbligatori** (`tests/test_e04_nulls.py`): (a) con enumerazione completa r = a / |G| e l'identità è contata una volta sola (il minimo su un gruppo di 63 elementi è 1/63, non 2/64); (b) il gruppo è chiuso e nessuna trasformazione viene scartata; (c) la diagnostica di copertura è riportata e non influenza r; (d) su 200 mappe lisce generate da una caratteristica indipendente dalla profondità si riporta la distribuzione di r, per documentare quanto la diagnostica sia informativa **senza** trattarla come test.

### Decisioni già prese, e perché

- **Zero GPU**; offset intermedi (±1, ±4) in un esperimento successivo (E04b) che non può riqualificare il verdetto di E04.
- **Due idoneità distinte**: analitica (con label, solo per misurare) e copertura operativa (geometrica + T non astenuto). Un utente senza label deve poter riprodurre la copertura.
- **Griglia fissa**, compositore a mattonelle dure, nessuna fusione: una mappa costante k riproduce bit a bit il TIFF (calibrato) di k. Fusione con halo = lavoro successivo.
- **Inviluppo descrittivo; trasferimento cross-fitted con buffer ≥ campo ricettivo**: la continuità dentro una patch non si chiama trasferimento.
- **Bootstrap spaziale appaiato stratificato per regione**; nessun bootstrap iid; gate per ogni unità inferenziale.
- **Calibrazione primaria per quantile matching su G**, grezzo come sensibilità; F1 alla soglia 91 solo sul calibrato.
- **Un solo stimatore (T), τ da soli sintetici, generatore congelato**; P\* (picco strutturale, z_rif = 10) e C (confidenza del modello, con esclusione dei pixel di `supervision_mask` e di un alone b) restano **diagnostici** e non entrano in HC/HD.
- **Seed = sensibilità appaiate**: una conclusione per segmento; se i seed non concordano, "dipende dal modello".
- **Novità prima del congelamento** (§2.3), socio S1 all'avvio.
- **Contratto d'uso scritto prima del congelamento** ([docs/e04-contratto-uso.md](../e04-contratto-uso.md)), da leggere in R1.
- **Nessun training, nessuna modifica al modello, nessun ranking, nessuna lettura di w029.**

### Vincoli

- Pixel held-out mai usati per tarare nulla; entrano solo nelle misure e nelle mappe analitiche. I pixel di training non si usano né per tarare né per verificare T.
- Un writer per cartella; il socio su `e04-socio`, percorsi `docs/reports/2026-09-XX-e04-socio-*` e `runs/`.
- Run CPU Kaggle da annunciare a Matteo; nessun run GPU in E04.
- Congelamento del pacchetto per la candidatura: **21 settembre 2026**. Se la scadenza impedisce revisione e manifest completi, si congela E03 e l'esito parziale di E04 senza promozione narrativa.

---

## 3. Perimetro

### File da creare o modificare

| File | Cosa fare |
|---|---|
| `configs/e04/grid.json` | tutte le costanti di §2.4 (geometria, gate, bootstrap, margine, buffer, calibrazione, T, generatore sintetico, τ dopo il passo 1b, seed); `schema_version` |
| `configs/e04/commands.json` | **fonte unica dei comandi** (già scritta, schema 1.2): 103 comandi `dev` (staging, quattro combinazioni, tre griglie, quattro varianti ricomposte più `inner8`), 8 comandi `new_segment`, artefatti attesi per ogni report con la coppia (mosaico, dominio). Piano, contratto e smoke test ne derivano; un test confronta token e ordine |
| `scripts/e04_stage.py` | staging fail-closed di volumi e predizioni con verifica delle impronte (passo 0a) |
| `configs/e04/tiles_<seg>.json` | inventario per mattonella e per blocco: validità geometrica, idoneità analitica, idoneità inferenziale, regione, conteggi |
| `scripts/e04_guard.py` | guardia eseguibile: verifica che configurazioni, notebook, report e manifest di E04 nominino solo i due segmenti di sviluppo e le due impronte di `LABEL_ALLOWLIST`; che ogni caricatore di label di E04 passi da `check_labels_allowed`; rifiuto di link, rinomine e del dataset label di E02 |
| `scripts/e04_tiles.py` | griglia, inventario, AUROC per mattonella e offset, curve Δ, k\*, località (permutazioni ristrette), inviluppo, cross-fit spaziale, bootstrap |
| `scripts/e04_calibrate.py` | quantile matching di §2.4 |
| `scripts/e04_synth.py` | generatore sintetico congelato e scelta di τ |
| `scripts/e04_features.py` | `profiles` (dal volume), `estimate` (T), diagnostici P\* e C, controlli nulli |
| `scripts/e04_mosaic.py` | `compose`, `equivalence`, `evaluate`, `validate-reports` |
| `scripts/build_e04_notebooks.py`, `scripts/kaggle_e04.py` | un notebook CPU Kaggle per i profili di w016 (e di 0814 per confronto con il locale); riuso del pilota E03 |
| `scripts/e04_manifest.py` | manifest fail-closed con confronto cella per cella dei rapporti del socio (stesso rigore di `e03_manifest.py`) |
| `tests/test_e04_*.py` | griglia, inventario, gate, equivalenza (compreso `estimator_disabled`), calibrazione (distribuzioni discrete, padding), T (piatta, multimodale, bordo, MAD = 0, segno), `test_e04_folds.py` (geometria delle pieghe: densa ≥ 4 blocchi per piega, stretta = non eseguibile), `test_e04_nulls.py` (mappa liscia indipendente dalla profondità non supera il nullo spaziale), bootstrap su casi con risposta nota, guardia (test negativi), `test_e04_smoke.py` (sequenza del contratto su fixture) |
| `tests/fixtures/e04_synth_head.json` | i primi 16 profili del generatore congelato; la sua impronta è in `grid.json` |
| `docs/e04-contratto-uso.md` | contratto d'uso (scritto; aggiornato all'esito) |
| `docs/reports/e04-r01/`, scheda, manifest | esiti |
| `docs/plans/2026-09-08-e04-compiti-socio.md`, `docs/plans/e04-prompt-codex-socio.md` | procedura del socio in due tempi |

### File da NON toccare

| File | Perché |
|---|---|
| `docs/reports/e03-r01/**`, scheda e manifest E03 | esito congelato: E04 legge, non modifica |
| `scripts/e03_*.py`, `configs/e03/*` | strumenti congelati; E04 li importa. Modifiche = emendamento + test E03 |
| qualunque percorso o dataset di `pherc1667-w029`, incluso il dataset label di E02 che lo contiene | sigillato fino a E05 |

---

## 4. Passi

Ogni comando scrive un JSON con `schema_version`, impronte degli input e parametri usati; l'artefatto di ogni passo è l'input del successivo. Percorsi relativi alla radice del repository; `PY=./.venv/Scripts/python.exe`.

### Passo 0a — Staging fail-closed di volumi e predizioni

I volumi a 21 fette e le 28 predizioni vivono fuori da git. `scripts/e04_stage.py` li materializza in `runs/E04-R01/` **verificandone le impronte** e fermandosi se una non coincide; nessun passo successivo può partire senza. Serve circa 14 GB liberi (disco: 27 GB).

```sh
PY=./.venv/Scripts/python.exe
$PY scripts/e04_stage.py volume --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --out runs/E04-R01/local-input/pherc0814-46527_z13.zarr --verify-tree-sha256 configs/e03/datasets.json
$PY scripts/e04_stage.py volume --mode dev --seg pherc0139-w016 --grid configs/e04/grid.json --out runs/E04-R01/local-input/pherc0139-w016_z13.zarr --verify-tree-sha256 configs/e03/datasets.json
$PY scripts/e04_stage.py preds --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --out runs/E04-R01/preds/pherc0814-46527 --verify-manifest docs/reports/2026-09-07-e03-r01-manifest.json
$PY scripts/e04_stage.py preds --mode dev --seg pherc0139-w016 --grid configs/e04/grid.json --out runs/E04-R01/preds/pherc0139-w016 --verify-manifest docs/reports/2026-09-07-e03-r01-manifest.json
$PY scripts/e04_stage.py labels --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --out runs/E04-R01/labels/pherc0814-46527 --verify-allowlist scripts/e03_metrics.py
$PY scripts/e04_stage.py labels --mode dev --seg pherc0139-w016 --grid configs/e04/grid.json --out runs/E04-R01/labels/pherc0139-w016 --verify-allowlist scripts/e03_metrics.py
```

`labels` copia le cartelle delle label dei **due soli segmenti di sviluppo** in `runs/E04-R01/labels/<seg>`, verificandone l'albero SHA-256 contro `LABEL_ALLOWLIST` di `scripts/e03_metrics.py`; da lì in poi **ogni comando che legge label riceve il percorso esplicito** `--labels`, e nessuno usa percorsi d'ambiente. `volume` copia da `runs/E03-R01/local-input/` quando il volume è già in locale (0814, impronta `bc742343…`) e altrimenti lo **scarica dal dataset Kaggle** `papyruslab-e02-input-w016` (≈ 11 GB), confrontando in entrambi i casi l'albero SHA-256 con `configs/e03/datasets.json`. `preds` raccoglie i sette TIFF per seed dalle cartelle di download verificate di E02/E03 e confronta ogni impronta con il manifest E03. **Fatto quando:** i quattro comandi terminano con esito positivo e scrivono `runs/E04-R01/staging.json` con le impronte.

### Passo 0b — Base verificata, campo ricettivo, preflight di numerosità

```
$PY -m pytest tests -q
$PY scripts/e04_guard.py --check                                   # guardia: solo due segmenti, lista bianca, caricatori conformi
$PY scripts/e04_tiles.py base --grid configs/e04/grid.json --out docs/reports/e04-r01/base.json
```
`base` autentica i 28 TIFF contro il manifest E03, esegue `check_labels_allowed` sulle due cartelle label, registra il campo ricettivo stimato dal codice di villa (metodo e numero, o "non stimabile" → RF = 128) e quindi b, conta blocchi idonei per segmento, regione e piega e applica i gate. I conteggi attesi sono già in §2.5: se quelli reali (dopo l'idoneità) sono **inferiori**, valgono i gate e non si rilassa nulla; se sono superiori, §2.5 si corregge con un emendamento prima di proseguire. **Fatto quando:** `base.json` esiste e la scheda riporta i conteggi e quali unità hanno intervalli.

### Passo 0c — Novita e contratto d uso

**Cosa:** verificare che §2.3 (novita) sia compilata e che [docs/e04-contratto-uso.md](../e04-contratto-uso.md) sia stato letto in R1; nessun calcolo. **Fatto quando:** il piano e congelato con entrambi presenti.

### Passo 1 — Inventario delle mattonelle (zero GPU)

```
$PY scripts/e04_tiles.py inventory --grid configs/e04/grid.json --seg pherc0814-46527 --out configs/e04/tiles_pherc0814-46527.json
$PY scripts/e04_tiles.py inventory --grid configs/e04/grid.json --seg pherc0139-w016 --out configs/e04/tiles_pherc0139-w016.json
```
Validità geometrica (da G), idoneità analitica, blocchi e pieghe A/B, regione. La scheda riporta i conteggi **prima** di qualunque AUROC.

### Passo 1b — τ su dati sintetici (zero GPU; prima di leggere qualunque profilo reale)

```
$PY scripts/e04_synth.py --grid configs/e04/grid.json --out docs/reports/e04-r01/synth.json --write-tau configs/e04/grid.json
git commit -m "feat: E04 tau frozen from synthetic data" configs/e04/grid.json docs/reports/e04-r01/synth.json
```
**Fatto quando:** τ è in `grid.json`, committato, con la tabella accuratezza/copertura per ogni valore della griglia. Da qui T non si tocca.

### Passo 2 — Mappe e località (zero GPU; **R2 del codice prima di questo passo**)

```
$PY scripts/e04_tiles.py maps --mode dev --seg <seg> --seed <42|43> --grid configs/e04/grid.json --grid-variant g64_o0 --out docs/reports/e04-r01/tiles_<seg>_s<seed>_g64_o0.json
# le due sensibilità di griglia, per ciascuna delle quattro combinazioni: --grid-variant g128_o0 e --grid-variant g64_o32 (12 invocazioni in tutto, elencate in configs/e04/commands.json)
```
Per mattonella idonea: AUROC per k, curva Δ(k), k\* con margine e censura. **Località (HA):** statistica = correlazione media fra le curve Δ di mattonelle adiacenti (4-vicinato), confrontata con 10 000 permutazioni dei k\*/curve **ristrette entro regione** (seed 20260908); concordanza fra i seed = frazione di mattonelle con k\* uguale, confrontata con la concordanza attesa permutando un seed entro regione.

### Passo 3 — Inviluppo e trasferimento cross-fitted (zero GPU; **si esegue dopo il passo 4a**, che produce i TIFF calibrati)

```
$PY scripts/e04_tiles.py envelope --grid configs/e04/grid.json --seg <seg> --seed <seed> --calibrated docs/reports/e04-r01/cal_<seg>_s<seed>.json --out docs/reports/e04-r01/envelope_<seg>_s<seed>.json
$PY scripts/e04_tiles.py crossfit --grid configs/e04/grid.json --seg <seg> --out docs/reports/e04-r01/crossfit_<seg>.json
```
Inviluppo (descrittivo) e cross-fit (§2.4) con bootstrap; entrambi anche in versione calibrata (la calibrazione, passo 4a, precede: nell'ordine reale il passo 4a si esegue prima del 3).

### Passo 4a — Calibrazione (zero GPU, senza label)

```sh
PY=./.venv/Scripts/python.exe
$PY scripts/e04_calibrate.py --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --volume runs/E03-R01/local-input/pherc0814-46527_z13.zarr --preds runs/E03-R01/preds/pherc0814-46527 --seed 42 --out docs/reports/e04-r01/cal_pherc0814-46527_s42.json --out-tifs runs/E04-R01/cal/pherc0814-46527_s42/
# le altre tre combinazioni: vedi configs/e04/commands.json (voce dev)
```
Scrive le 6 mappe m_k (256 valori ciascuna), i **sette TIFF calibrati** per combinazione e le loro impronte.

### Passo 4b — Profili e stimatore T (CPU; un run Kaggle da annunciare)

```
$PY scripts/e04_features.py profiles --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --volume runs/E03-R01/local-input/pherc0814-46527_z13.zarr --out docs/reports/e04-r01/profiles_pherc0814-46527.json
$PY scripts/build_e04_notebooks.py && $PY scripts/kaggle_e04.py push profiles-w016 && $PY scripts/kaggle_e04.py output profiles-w016   # profili di w016 (e 0814) su Kaggle CPU
$PY scripts/e04_features.py estimate --mode dev --seg <seg> --grid configs/e04/grid.json --profiles docs/reports/e04-r01/profiles_<seg>.json --out docs/reports/e04-r01/offsets_T_<seg>.json --maps runs/E04-R01/maps_<seg>/
$PY scripts/e04_features.py diagnostics --mode dev --seg <seg> --grid configs/e04/grid.json --out docs/reports/e04-r01/diag_<seg>.json   # P*, C, mediana degli L*
```
I profili di 0814 calcolati su Kaggle devono coincidere bit a bit con quelli locali (controllo del run CPU). `estimate --maps` scrive `offset_map.tif`, `confidence_map.tif`, `abstention_mask.tif` e `coverage.json` come dal [contratto d'uso](../e04-contratto-uso.md), che è l'**interfaccia canonica**: se un comando qui e nel contratto divergono, vale il contratto e questo piano si emenda.

### Passo 5 — Mosaico con T, controlli nulli, verdetto (zero GPU)

I comandi completi delle quattro combinazioni × cinque varianti sono in `configs/e04/commands.json` (voce `dev`), da cui lo smoke test li estrae letteralmente. Qui la forma, con `pherc0814-46527`, seed 42 e variante primaria:

```sh
PY=./.venv/Scripts/python.exe
$PY scripts/e04_mosaic.py equivalence --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --grid-variant g64_o0 --preds runs/E04-R01/cal/pherc0814-46527_s42/ --seed 42
$PY scripts/e04_mosaic.py compose --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --grid-variant g64_o0 --map docs/reports/e04-r01/offsets_T_pherc0814-46527_g64_o0.json --preds runs/E04-R01/cal/pherc0814-46527_s42/ --calibration docs/reports/e04-r01/cal_pherc0814-46527_s42.json --seed 42 --out runs/E04-R01/mosaic/pherc0814-46527_s42_T_primary.tif
$PY scripts/e04_mosaic.py evaluate --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --grid-variant g64_o0 --pred runs/E04-R01/mosaic/pherc0814-46527_s42_T_primary.tif --seed 42 --eval-scope full --nulls 100000 --out docs/reports/e04-r01/eval_pherc0814-46527_s42_T_primary.json
# le quattro varianti di robustezza (§2.6) ricostruiscono mappa e/o mosaico: i comandi per esteso sono in commands.json
$PY scripts/e04_mosaic.py compose --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --grid-variant g64_o0 --map docs/reports/e04-r01/offsets_T_pherc0814-46527_g64_o0.json --preds runs/E03-R01/preds/pherc0814-46527 --seed 42 --out runs/E04-R01/mosaic/pherc0814-46527_s42_T_raw.tif
$PY scripts/e04_mosaic.py evaluate --mode dev --seg pherc0814-46527 --grid configs/e04/grid.json --grid-variant g64_o0 --pred runs/E04-R01/mosaic/pherc0814-46527_s42_T_raw.tif --seed 42 --eval-scope full --out docs/reports/e04-r01/eval_pherc0814-46527_s42_T_raw.json
$PY scripts/e04_mosaic.py validate-reports --mode dev --grid configs/e04/grid.json --reports docs/reports/e04-r01/   # rifiuta due report con la stessa coppia (impronta mosaico, impronta maschera di valutazione)
```
`evaluate` produce, per segmento, seed e variante: AUROC e F1@91 del mosaico; Δ rispetto alle baseline `k0`, `uniform_oracle_target`, `uniform_other_segment`; rango nella distribuzione per traslazione e nel nullo marginale, con la loro risoluzione e la diagnostica di copertura; danno per regione; copertura, astensioni per motivo, entropia, mediana degli L\* prima e dopo il centraggio; intervalli indicativi dove il ramo di §2.5 li consente.

### Passo 6 — Socio (branch `e04-socio`), in due tempi

All'avvio: S1 verifica indipendente di novità (termini di §2.3, più il PDF completo di arXiv 2606.29085). Alla fine: S2 ricalcolo in cieco di mappe, inviluppo e cross-fit dai 28 TIFF (dataset Kaggle privato con impronte); S3 ricalcolo in cieco di calibrazione, T e valutazione del mosaico. Confronto cella per cella nel manifest.

### Passo 7 — Scheda, manifest, R3, consolidamento

```
$PY scripts/e04_manifest.py --out docs/reports/2026-09-XX-e04-r01-manifest.json
```
Scheda da `docs/templates/esperimento.md`, R3 Codex, roadmap/README/AGENTS/decisione, contratto d'uso aggiornato all'esito, pacchetto per la candidatura congelato il 21 settembre.

---

## 5. Criterio di esito, deciso prima della prova

Misure sui pixel held-out del piano 10; conclusioni **per segmento**; i due seed devono concordare, altrimenti "dipende dal modello". Δ = **metodo − riferimento**, sempre. Soglie 0,02 e 0,01 = soglie di utilità pratica (banda di E03 e rumore fra seed), non livelli di significatività. Gli intervalli, dove calcolabili, si riportano come diagnostica e non decidono nulla.

- **HA (località), per segmento: solo descrizione, nessun esito.** Si riportano, per ciascun seed: la statistica di località, il suo rango fra le permutazioni ristrette con la risoluzione, la concordanza dei k\* fra i due seed con il suo rango, la frazione di k\* censurati e la mappa testuale. **Nessuna soglia converte questi numeri in "località osservata" o "non osservata"**, e nessuna ipotesi successiva dipende da essi: la scheda descrive che cosa si vede e lascia al lettore il giudizio. HA non compare fra le condizioni di HD. Si riporta la frazione di k\* censurati.
- **HB (trasferimento), per segmento, descrittiva (§2.5, punto 4):** si riporta la stima puntuale del guadagno cross-fitted rispetto a k = 0 e al riferimento uniforme della piega di selezione, con il numero di blocchi valutabili. "Guadagno trasferibile osservato" se entrambe le stime sono ≥ 0,02 su entrambi i segmenti; **nessuna affermazione di significatività**. Sotto il gate di piega: "non eseguibile". L'inviluppo è descrittivo.
- **HC (stimatore), per segmento e per seed, sul mosaico calibrato di T.** Le baseline si citano per **nome**, non per numero; un test fail-closed (`tests/test_e04_baselines.py`) verifica che nome, identificatore e origine coincidano in ogni report.
  - **HC1** (vs finestra ufficiale, baseline `k0`): Δ ≥ 0,02. Si riportano accanto, come diagnostica e senza potere decisionale, il rango r della Δ nella distribuzione per traslazione (§2.4) con la sua risoluzione, e l'intervallo indicativo se calcolabile.
  - **HC2** (vs `uniform_oracle_target`, il miglior offset uniforme del **segmento valutato** scelto con le label), **bloccante per HD:** Δ ≥ **+0,005** come stima puntuale, cioè un vantaggio **strettamente positivo** preregistrato e non un pareggio: un pareggio è ciò che produrrebbe una mappa degenere, e non deve poter promuovere nulla. Anche qui rango e intervallo si riportano senza potere decisionale.
  - **HC3** (riportata, non bloccante) vs `uniform_other_segment`, voce (iv) di §2.4.
  - Copertura, astensioni per motivo e intervalli indicativi si riportano sempre. HC1 vera e HC2 falsa = "correzione locale utile ma inferiore a uno spostamento uniforme ben scelto".
- **HD (candidato operativo su due casi, criterio descrittivo):** T **non degenere** (§2.4, punto 10) su entrambi i segmenti; T **supera di ≥ 0,01 il migliore dei 32 controlli a profili permutati** (§2.4, voce vi) su tutte e quattro le combinazioni; HC1 e HC2 vere su **entrambi** i segmenti e **entrambi** i seed, con lo stesso algoritmo, gli stessi parametri e la stessa τ; per **ogni** regione held-out, Δ puntuale rispetto a k = 0 ≥ −0,02; F1@91 puntuale del mosaico calibrato ≥ −0,01 rispetto a k = 0; segno del guadagno invariato nelle **quattro letture di robustezza** di §2.6: le tre ricomposte (`raw`, `g128`, `o32`) e la sensibilità del dominio di valutazione (`inner8`). HD **non è** un'affermazione statistica di superiorità: è la congiunzione di condizioni preregistrate (non degenerazione, HC1 e HC2 su quattro combinazioni, danno per regione, F1, cinque letture di robustezza) su quattro combinazioni, e si scrive con questa etichetta ovunque, scheda e candidatura comprese.
- **Degenerazione:** T "uniforme" (§2.4, punto 10): si scrive, con entropia della mappa, copertura, mediana degli L\*.
- **Arresti che chiudono il ramo strumento, conservando il diagnostico:** `estimator_disabled: true` in `grid.json` (nessun τ soddisfa accuratezza e copertura sui sintetici; un τ valido pari a 1,00 **non** è un arresto e il test di equivalenza distingue i due casi); sotto il gate di segmento di §2.5; `no_template` su entrambi i segmenti; mattonelle piatte + censurate + astenute > 50 % dell'area valida di un segmento ("profondità non identificabile con questa caratteristica"); segno del guadagno che cambia fra calibrato e grezzo o con l'origine; mappe dei due seed che non condividono alcun k\* su più della metà delle mattonelle coperte; C che funziona solo includendo pixel di training.
- **Ciò che nessun numero dice qui:** la causa; il comportamento su altri rotoli; l'effetto di offset intermedi (E04b); la modalità efficiente (lavoro futuro); lo spostamento uniforme del segmento (fuori dalla portata di T).

---

## 6. Verifica finale

```
$PY -m pytest tests -q                                                                    # tutti verdi
$PY scripts/e04_guard.py --check                                                          # sigillo: guardia eseguibile, non testuale
$PY scripts/e04_tiles.py base --grid configs/e04/grid.json --out docs/reports/e04-r01/base.json   # 28 TIFF autenticati, gate
$PY scripts/e04_mosaic.py equivalence --mode dev --grid configs/e04/grid.json --all        # 28 equivalenze bit a bit, più i casi degeneri
$PY scripts/e04_mosaic.py validate-reports --grid configs/e04/grid.json --reports docs/reports/e04-r01/   # tutte le celle di §5
$PY -m pytest tests/test_e04_smoke.py -q                                                  # sequenza del contratto su fixture sintetico
$PY scripts/e04_manifest.py --out docs/reports/2026-09-XX-e04-r01-manifest.json           # fail-closed, socio confrontato
```
Inoltre: `git status` pulito; diff solo sui file del §3.

---

## 7. Se il piano è sbagliato

Fermarsi, annotare, committare il coerente, segnalare; emendare (§11), non aggirare.

---

## 8. Fuori perimetro

Training o fine-tuning; modifica dei pesi; ranking; lettura di w029; offset intermedi (E04b); fusione con halo e modalità efficiente (lavoro successivo con test di equivalenza); stimatori che usano label o soglie tarate su label o su pixel di training; applicazione a segmenti non letti (E06); modifiche a `scripts/e03_*`.

---

## 9. Divisione del lavoro

- **Matteo:** approva il piano congelato e **dà il "vai" prima che qualunque passo venga eseguito**, compresi quelli a costo GPU zero: il piano congelato non autorizza da solo l'esecuzione. Autorizza lo staging (≈ 11 GB scaricati da Kaggle) e il run CPU Kaggle; decide fusione di `e04-socio`, contenuto e invio della candidatura.
- **Claude Code (writer):** passi 0–5, 7; scheda, manifest, contratto d'uso.
- **Codex (`gpt-5.6-sol`):** co-progettazione (fatta); R1 (in corso, due giri); R2 sul codice prima del passo 2; R3 sull'esito.
- **Socio (`e04-socio`, Codex):** S1 all'avvio; S2 → S3 alla fine.

### Calendario indicativo

8–9 settembre: R1 e congelamento. 9–11: passi 0–1b, R2. 11–14: passi 2–5. 14–17: socio S2–S3. 17–21: passo 7 e congelamento per la candidatura. 22–30: testo della candidatura; invio da Matteo entro il 30.

---

## 10. Revisioni Codex e congelamento

### Giro di co-progettazione (8 settembre 2026, `task` sola lettura, `gpt-5.6-sol`, effort high, sessione `01a08060…`)

Codex ha letto la bozza v0, la scheda E03, il documento di decisione e la procedura operativa e ha restituito 12 difetti di disegno, una riformulazione dei criteri §5, tre stimatori alternativi, il contratto d'uso mancante e le condizioni di arresto. Verdetto: "buona sequenza esplorativa, non ancora congelabile come prova di uno strumento". **12 proposte, 12 accettate** (5 e 11 in forma adattata):

| # | Proposta (sintesi) | Esito | Nel piano |
|---|---|---|---|
| 1 | Idoneità analitica (con label) ≠ copertura operativa (senza label) | accettata | §2.4 geometria; passi 1, 4b, 5 |
| 2 | Oracolo = inviluppo descrittivo; trasferimento su blocchi disgiunti | accettata | §2.4 cross-fit; passo 3 |
| 3 | Bootstrap spaziale appaiato; permutazioni ristrette | accettata | §2.4; passi 2–3; §5 |
| 4 | Calibrazione monotona verso k = 0 come primaria | accettata | §2.4 calibrazione; passo 4a |
| 5 | Griglia, stride, halo, fusione, tie-break, origini, censura | adattata | griglia fissa senza fusione (equivalenza esatta), sensibilità di origine/fascia, tie-break e censura definiti |
| 6 | Un solo stimatore senza parametri supervisionati; pieghe = stress test | accettata | T, τ da sintetici |
| 7 | HA su curve Δ, seed come sensibilità appaiate | accettata | §5 HA |
| 8 | HB–HC senza "almeno un seed" né gate 50 % | accettata | §5 HB, HC |
| 9 | HD = candidato operativo su due casi; copertura, astensioni, costo, bordi | accettata | §1, §5 HD, contratto |
| 10 | Novità prima del congelamento | accettata | §2.3, socio S1 all'avvio |
| 11 | Contratto d'uso, CLI, integrazione | adattata | contratto scritto prima del congelamento; modalità efficiente rinviata con test di equivalenza |
| 12 | Offset intermedi come esperimento successivo | accettata | E04b |

### Revisione R1, primo giro (8 settembre 2026, `adversarial-review` sull'albero di lavoro, `gpt-5.6-sol`, job `review-mtshqij2-qui28o`)

Verdetto: NO-SHIP, "i 12 punti non sono tutti integrati operativamente". **9 finding (8 P1, 1 P2), accettati 9:**

| # | Sev. | Finding (sintesi) | Correzione in v2 |
|---|---|---|---|
| 1 | P1 | τ poteva essere tarata indirettamente sulle label o sui pixel di training di 0814; generatore sintetico libero | generatore congelato in §2.4 (distribuzioni, seed, numerosità, metrica, griglia di τ, regola di pareggio); nessuna verifica su pixel reali; τ committata prima di leggere i profili |
| 2 | P1 | Cross-fit A/B a scacchiera 32 px dentro la stessa mattonella non separava selezione e valutazione | pieghe = blocchi 128 interi a scacchiera, buffer b = max(96, RF) fra selezione e valutazione, fallback "non eseguibile" |
| 3 | P1 | HC poteva passare senza battere il miglior offset uniforme del segmento target | HC2 bloccante contro l'oracolo uniforme del target; §1 riformulato: T corregge solo la componente locale |
| 4 | P1 | Non-inferiorità regionale con l'estremo sbagliato dell'intervallo | Δ = metodo − riferimento; limite **inferiore** unilaterale 95 % ≥ −0,01, regioni e F1; molteplicità dichiarata |
| 5 | P1 | Bootstrap e gate non fail-closed (classi, blocchi parziali, stratificazione, seed, repliche degeneri, regioni) | §2.4 bootstrap: unità idonee con minimi per classe, stratificazione per regione, 2 000 repliche, seed, percentile, repliche scartate contate, gate per ogni unità |
| 6 | P1 | T circolare (template dalle "coperte") e senza casi degeneri | procedura monodirezionale (pool = valide geometricamente), formule, MAD = 0, correlazione per ritardo con 21 − |L| punti, pareggi, segno, prominenza, censura al bordo |
| 7 | P1 | Calibrazione senza popolazione e algoritmo congelati | maschera G deterministica, CDF a punto medio, mappa monotona, `uint8`, per segmento e seed, test su discrete e padding |
| 8 | P1 | Controllo del sigillo testuale ineseguibile | `scripts/e04_guard.py --check` e `check_labels_allowed` in ogni caricatore; test negativi; §6 aggiornato |
| 9 | P2 | Contratto d'uso circolare e comandi mancanti | contratto scritto ora ([docs/e04-contratto-uso.md](../e04-contratto-uso.md)); comandi end-to-end con argomenti e artefatti nei passi 0–7 |

### Revisione R1, secondo giro (8 settembre 2026, job `review-mtsi4jwc-odiyiw`, sessione `01a08078…`)

Verdetto: NO-SHIP. "HC2 e il verso degli intervalli sono stati corretti, ma cross-fit, fail-closed di τ, inferenza spaziale e contratto conservano difetti bloccanti." **4 finding P1, accettati 4:**

| # | Sev. | Finding (sintesi) | Correzione in v3 |
|---|---|---|---|
| 1 | P1 | Con pieghe a scacchiera ogni pixel di B dista ≤ 64 px da un blocco A, mentre b ≥ 96: il buffer svuotava la valutazione proprio nel caso denso; il k\* dei blocchi 128 non era definito | pieghe = **superblocchi**: un solo taglio per regione perpendicolare al lato più lungo, alla mediana dei pixel held-out, con fascia esclusa di larghezza b; k\* del blocco definito; gate di piega ≥ 4 blocchi; `tests/test_e04_folds.py` con caso denso e caso stretto |
| 2 | P1 | `conf` può arrivare a 2, quindi τ = 1,00 non produceva l'astensione totale dichiarata; generatore sintetico sottospecificato | `estimator_disabled: true` con `tau: null` forza k̂ = 0 ovunque (verificato dall'equivalenza); griglia di τ estesa a 2,00; generatore congelato per RNG, disposizione, covarianza (`mode="wrap"`), lati del secondo foglio, clipping, dtype, con fixture e impronta in `grid.json` |
| 3 | P1 | Il nullo preservava solo le frequenze e il bootstrap trattava blocchi adiacenti come indipendenti: una mappa liscia senza informazione sulla profondità poteva superare HC/HD; F1 non ricalcolato per replica | nullo **spaziale** primario per traslazione ciclica entro regione (preserva copertura, frequenze e autocorrelazione), marginale come secondario; unità bootstrap 128 con **sensibilità obbligatoria a 256** e verdetto "non robusto alla scala di dipendenza" se il segno cambia; AUROC e F1 ricalcolati appaiati a ogni replica; `tests/test_e04_nulls.py` con mappa liscia indipendente |
| 4 | P1 | Contratto non end-to-end e con CLI diverse da quelle del piano; output promessi non prodotti da alcun comando | [contratto](../e04-contratto-uso.md) riscritto come **interfaccia canonica** con la sequenza completa da preflight a manifest; `estimate --maps` produce mappe e `coverage.json`; comandi del piano allineati; `tests/test_e04_smoke.py` preregistrato su fixture sintetico |

### Revisione R1, terzo giro (8 settembre 2026, job `review-mtsikg7k-hkh9ks`, sessione `01a08084…`)

Verdetto: NO-SHIP. **5 finding (4 P1, 1 P2), accettati 5.** Il primo è il più importante di tutta la progettazione: un conto puramente geometrico, fatto sulle bbox già note, mostra che **l'area annotata non basta per affermazioni con intervalli**. Meglio saperlo prima di partire che dopo due settimane di calcoli.

| # | Sev. | Finding (sintesi) | Correzione in v4 |
|---|---|---|---|
| 1 | P1 | La sensibilità obbligatoria a 256 px rende HD strutturalmente non dichiarabile: le regioni contengono al massimo 2 blocchi da 256, e dopo la divisione in pieghe restano 2–3 blocchi da 128 | nuova **§2.5** con i conteggi esatti (12/6/4 blocchi da 128; 2/1/1 da 256; 3/2/0 per piega) e le cinque conseguenze accettate: nessun intervallo per regione, intervalli per segmento solo indicativi, sensibilità 256 non calcolabile e robustezza alla scala di dipendenza **non verificata**, cross-fit descrittivo, conclusione forte affidata al test di randomizzazione esatto. §1 riscritto di conseguenza |
| 2 | P1 | Il nullo ciclico non raggiungeva p < 0,01 (max 63 fasi) e non preservava copertura e classi sui pixel effettivamente valutati | test di randomizzazione **esatto** con identità inclusa, p = (1 + a) / (1 + n); supporto rettangolare comune; traslazioni ammesse solo se conservano copertura, classi e istogramma dei k entro l'1 %; risoluzione dichiarata e "non eseguibile" se peggiore di 0,05; tre test obbligatori, incluso il tasso di falsi positivi su 100 ripetizioni |
| 3 | P1 | Contratto e piano divergevano su percorsi e comandi; il contratto era per un segmento nuovo ma la guardia ammetteva solo i due segmenti di sviluppo | contratto diviso in **modalità operativa** (segmento nuovo, `e04_guard.py --new-segment` che vieta ogni apertura di label, uscite in `out/e04/<segmento>/`) e **sperimentale** (piano §4); entrambe generate da `configs/e04/commands.json`, con un test che fallisce se divergono; smoke test che esegue letteralmente entrambe le sequenze |
| 4 | P1 | Numerazione incoerente delle baseline fra §2.4 e §5: HC2 poteva essere implementata contro l'oracolo uniforme sbagliato | baseline citate per **nome** (`k0`, `uniform_oracle_target`, `uniform_other_segment`) e `tests/test_e04_baselines.py` fail-closed che verifica nome, identificatore e origine in ogni report |
| 5 | P2 | L'arresto "τ = 1,00" contraddiceva `estimator_disabled` | l'arresto è ora `estimator_disabled: true` con `tau: null`; un τ valido pari a 1,00 non è un arresto, e il test di equivalenza distingue i due casi |

### Revisione R1, quarto giro (8 settembre 2026, job `review-mtsiy3yw-iftru3`, sessione `01a0808d…`)

Verdetto: NO-SHIP. **4 finding P1, accettati 4.**

| # | Sev. | Finding (sintesi) | Correzione in v5 |
|---|---|---|---|
| 1 | P1 | §2.5 contava blocchi *interi dentro la bbox*, mentre §2.4 usa il reticolo globale con celle parziali ammesse: i conteggi veri sono 20/15/12 celle da 128 e 6/6/4 da 256; e b dipende da RF, ancora da calcolare | §2.5 riscritta con **limiti superiori** (celle intersecate) e **inferiori** (celle intere) sullo stesso reticolo di §2.4, e con **rami preregistrati**: per ogni conteggio possibile al passo 0 è già scritto che cosa diventa dichiarabile. Nessun criterio si emenda dopo aver letto i conteggi |
| 2 | P1 | Il p "esatto" contava l'identità due volte ((1 + a) / (1 + n) con l'identità già dentro a: minimo 2/64, non 1/63) e lo scarto delle traslazioni non invarianti dipendeva dalle label, rompendo l'exchangeability | enumerazione completa → p = a / |G| con l'identità contata una volta; Monte Carlo solo se |G| > 100 000, con la formula corretta per il campionamento; **nessun filtro** sulle trasformazioni, gli squilibri si riportano come diagnostica |
| 3 | P1 | Il p era definito per regione ma HC decide per segmento: con due regioni l'aggregazione era indefinita e manipolabile | statistica = **una sola Δ globale** per segmento; gruppo = **prodotto cartesiano** dei gruppi regionali applicato simultaneamente; un solo p per segmento e seed, con la sua risoluzione |
| 4 | P1 | La modalità senza label era un preflight isolato: i comandi successivi potevano aprire label; mancavano i percorsi dei sette TIFF | `--mode new-segment` obbligatorio su **ogni** comando, con rifiuto nel caricatore comune prima di qualunque I/O; sottocomandi valutativi vietati in quella modalità; `--preds <dir>` esplicita con l'elenco atteso dei sette file; `tests/test_e04_mode.py` con label-esca e verifica strumentale di `open`/`stat`/`glob` |

### Revisione R1, quinto giro (8 settembre 2026, job `review-mtsj9osw-uo6yz7`, sessione `01a08096…`)

Verdetto: NO-SHIP. **4 finding (3 P1, 1 P2), accettati 4.** Il primo cambia la natura dell'esperimento e va detto con chiarezza: **E04 non può produrre affermazioni inferenziali**, e ora lo dichiara.

| # | Sev. | Finding (sintesi) | Correzione in v6 |
|---|---|---|---|
| 1 | P1 | Il p-value non è un test esatto su dati osservazionali: l'esattezza richiede che sotto il nullo l'identità sia scambiabile con le traslazioni, e qui la maschera annotata e la difficoltà del modello non sono stazionarie. Un allineamento spurio poteva far passare HC/HD | il nullo per traslazione diventa **diagnostica**: si riporta il rango r e la risoluzione, si dichiara esplicitamente che **r non è un p-value** e non entra in HC né in HD. §1 riscritto: E04 è un risultato **descrittivo replicato**, e la sua forza sta in preregistrazione, quattro combinazioni, cinque letture di robustezza, controlli nulli riportati, riproduzione in cieco e contratto d'uso |
| 2 | P1 | §2.5 e §2.4 davano regole incompatibili sugli stessi conteggi (intervalli per regione, sensibilità 256) | §2.5 è l'**unica tabella normativa**; §2.4 e §5 non ripetono più condizioni di numerosità e vi rimandano; test parametrizzati su tutte le combinazioni dei conteggi |
| 3 | P1 | La sequenza operativa non era eseguibile (variabili, continuazioni di riga), i nomi degli artefatti non coincidevano e la calibrazione prodotta non era consumata da `compose` | comandi riscritti uno per riga, shell dichiarata, nomi uniformati alla tabella degli output; `e04_calibrate.py --out-tifs` produce i sette TIFF calibrati e `compose --preds <calibrati> --calibration <json>` li consuma verificandone le impronte; lo smoke test estrae i comandi **letteralmente** dal contratto |
| 4 | P2 | Il template di T era indefinito se tutte le mattonelle risultavano piatte | ramo `no_template` (meno di 16 mattonelle valide non piatte): astensione totale del segmento, copertura 0, mosaico bit a bit uguale a k = 0; test dedicati |

### Revisione R1, sesto giro (8 settembre 2026, job `review-mtsjlumi-ukc5pe`, sessione `01a0809e…`)

Verdetto: NO-SHIP. **3 finding P1, accettati 3.** Il terzo è il controesempio più utile di tutta la progettazione.

| # | Sev. | Finding (sintesi) | Correzione in v7 |
|---|---|---|---|
| 1 | P1 | I comandi del piano §4 non erano quelli canonici (mancava `--out-tifs`, `compose` usava un `--calibrated` indefinito) e contenevano pseudocomandi non estraibili letteralmente | passi 4a e 5 riscritti con invocazioni **complete, una per riga**, identiche al contratto; `--mode dev` esplicito; le quattro combinazioni elencate per esteso in `configs/e04/commands.json` |
| 2 | P1 | Restavano decisioni inferenziali sotto nomi descrittivi: "test esatto superato" in §1, "la conclusione forte poggia sul test" in §2.5, "gli intervalli escludono il rumore", HA decisa dal 99° percentile | rimossi tutti; HA è ora descrittiva (statistica, rango, risoluzione, e la scritta "località osservata" o "non osservata"); §1 e §5 dichiarano che nessuna ipotesi è decisa da p-value, percentili o intervalli |
| 3 | P1 | **Controesempio: una mappa costante uguale all'oracolo uniforme passava HD.** Il centraggio a mediana zero era atteso ma non imposto; la degenerazione era etichettata, non bloccante; HC2 accettava il pareggio | centraggio **imposto e testato** (si sottrae la mediana degli L\*): dopo di esso una mappa costante è identicamente nulla e il suo mosaico coincide bit a bit con k = 0, quindi non può soddisfare HC1; degenerazione (mappa costante o > 90 % dello stesso k̂) **bloccante per HD**; HC2 richiede Δ ≥ +0,005 |

### Revisione R1, settimo giro (8 settembre 2026, job `review-mtsjx6od-lyfulh`, sessione `01a080a6…`)

Verdetto: NO-SHIP. **4 finding P1, accettati 4.** Il controesempio della mappa costante è confermato chiuso.

| # | Sev. | Finding (sintesi) | Correzione in v8 |
|---|---|---|---|
| 1 | P1 | HA era ancora decisa da un percentile ("prime 1 %"), e un arresto dipendeva da "oltre il nullo" | HA non produce più alcun esito: statistiche, ranghi, risoluzione, censure e mappe si riportano e basta, e HA non compare fra le condizioni di HD; l'arresto sui seed è ora una condizione osservabile senza nullo |
| 2 | P1 | Le cinque letture di robustezza valutavano lo **stesso** mosaico: si potevano ottenere cinque JSON senza cinque misure | nuova **§2.6**: quattro varianti che **ricostruiscono** davvero (`raw` ricompone sui TIFF grezzi; `g128` e `o32` rieseguono T sulla loro griglia e ricompongono; `inner8` valuta sui soli pixel a ≥ 8 px dal bordo della mattonella); `validate-reports` rifiuta due report che dichiarino lo stesso mosaico; i blocchi mobili tornano a essere diagnostica del bootstrap |
| 3 | P1 | `configs/e04/commands.json`, dichiarato fonte canonica, non esisteva e non era nel perimetro | **scritto ora**: 91 comandi `dev` (quattro combinazioni × cinque varianti, con tutti gli input), 8 comandi `new_segment`, varianti di griglia e di robustezza, artefatti attesi per ogni report; aggiunto al perimetro; piano e contratto vi rimandano e lo smoke test ne estrae i comandi |
| 4 | P1 | L'ordine del centraggio non era univoco: eseguito alla lettera, una mappa costante di k̂ non diventava nulla | ordine unico in sette fasi (L\* grezzo e confidenza → astensione → insieme vuoto → sottrazione della mediana → saturazione → quantizzazione → degenerazione), con test su astensione totale, saturazione e **mappa bilanciata senza segnale locale** |

### Revisione R1, ottavo giro (8 settembre 2026, job `review-mtsk9h09-qqh6hb`, sessione `01a080af…`)

Verdetto: NO-SHIP. **4 finding (3 P1, 1 P2), accettati 4.** Confermato che il centraggio chiude il controesempio della mappa costante e che nessuna decisione dipende piu' da p-value, percentili o intervalli.

| # | Sev. | Finding (sintesi) | Correzione in v9 |
|---|---|---|---|
| 1 | P1 | `inner8` usava gli stessi parametri di `primary`: il compositore deterministico avrebbe prodotto lo stesso TIFF, quindi o la coppia falliva sempre o due varianti passavano con lo stesso mosaico | §2.6 riscritta: **tre** varianti ricompongono (`raw`, `g128`, `o32`) e `inner8` e' una **sensibilita' del dominio di valutazione** sul mosaico primario; ogni report e' identificato dalla coppia (impronta del mosaico, impronta della maschera di valutazione) e `validate-reports` la esige distinta. Nel registro: 16 mosaici, 20 report, 20 coppie distinte |
| 2 | P1 | La sequenza dipendeva dal volume di w016 che non esiste in locale e che nessun comando materializzava | nuovo **passo 0a** e `scripts/e04_stage.py`: `volume` copia il volume locale di 0814 o **scarica** quello di w016 dal dataset Kaggle, verificando in entrambi i casi l'albero SHA-256 contro `configs/e03/datasets.json`; `preds` raccoglie i 28 TIFF confrontandoli con il manifest E03; nessun passo puo' partire senza. Serve circa 14 GB liberi |
| 3 | P1 | Il contratto ometteva `--grid-variant g64_o0` in tre comandi presenti nel registro: lo smoke test letterale sarebbe fallito | i tre comandi allineati al registro; il test confronta **token e ordine**, senza normalizzare i default |
| 4 | P2 | Le sensibilita' di griglia del passo 2 (`maps` su g128 e o32) non erano nel registro | dodici invocazioni `maps` (due segmenti x due seed x tre griglie) materializzate con uscite distinte; il passo 2 le richiama |

### Revisione R1, nono giro (8 settembre 2026, job `review-mtskttvy-10t0ne`, sessione `01a080be…`)

Verdetto: NO-SHIP. **3 finding (2 P1, 1 P2), accettati 3.** Il secondo e' un controesempio piu' sottile di quello della mappa costante.

| # | Sev. | Finding (sintesi) | Correzione in v10 |
|---|---|---|---|
| 1 | P1 | Le label erano una dipendenza d'ambiente: nessun comando le materializzava, quindi un clone pulito si sarebbe fermato e una macchina con residui avrebbe potuto usarne di vecchie | `e04_stage.py labels` copia le label dei due soli segmenti di sviluppo in `runs/E04-R01/labels/` verificandole contro la lista bianca; ogni consumatore riceve `--labels` esplicito; test del grafo che rifiuta input non prodotti o non dichiarati |
| 2 | P1 | HC2 non smaschera necessariamente una mappa determinata dalla sola posizione: se due zone preferiscono offset opposti, una mappa posizionale batte sia lo zero sia ogni offset uniforme senza contenere informazione di profondita' | nuovo **controllo bloccante a profili permutati**: 32 permutazioni congelate che scambiano i profili fra mattonelle lasciando la geometria; T deve superare il migliore di questi di almeno 0,01 su tutte e quattro le combinazioni, altrimenti HD non e' dichiarabile; piu' un test di equivarianza che fallisce se la mappa non segue la permutazione |
| 3 | P2 | `validate-reports` era descritto come rifiuto di due report con lo stesso mosaico, ma `primary` e `inner8` lo condividono per costruzione | regola uniformata alla coppia (impronta mosaico, impronta maschera di valutazione), con test che verifica che `primary` e `inner8` abbiano lo stesso mosaico e domini distinti |

### Revisione R1, decimo giro

*Da compilare.*

---

## 11. Emendamenti dopo il congelamento

*Nessuno.*

---

## 12. Al termine

- [ ] Tutti i passi eseguiti e verificati, o fermati con motivo scritto
- [ ] §5 letto come scritto, esiti negativi compresi
- [ ] Scheda, manifest, R3, consolidamento, contratto d'uso aggiornato
- [ ] Commit e push del lavoro verificato; nessuna candidatura inviata dagli agenti
