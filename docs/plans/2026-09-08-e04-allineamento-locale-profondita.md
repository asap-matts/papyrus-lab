# E04 — Dall'avviso allo strumento: allineamento locale della profondità senza label

**Scritto da:** Claude Code · **Esecutore previsto:** Claude Code (writer), Codex (revisore), socio (riproduzione in cieco)
**Data:** 2026-09-08 · **Branch:** `main` (socio su `e04-socio`) · **Commit di partenza:** *da compilare al congelamento*
**Stato:** bozza v0, in discussione con Codex. Nessun passo eseguito.

> Verifica prima di iniziare: `git rev-parse --short HEAD` deve restituire il commit sopra. Se non corrisponde, **fermati**.

---

## 1. Obiettivo

Alla fine deve essere vero, con criteri scritti qui prima di misurare: (a) sappiamo se l'offset di profondità che rende meglio **varia dentro un segmento**, mattonella per mattonella, o è uniforme; (b) sappiamo **quanto AUROC si guadagnerebbe al massimo** scegliendo l'offset per mattonella con le label (oracolo), e quanto di quel guadagno è reale e non rumore; (c) sappiamo se uno **stimatore senza label** recupera una frazione dichiarata di quel guadagno su un segmento mai usato per tararlo; (d) sappiamo se una **predizione a mosaico** costruita con lo stimatore batte la finestra ufficiale sui pixel held-out, con il criterio prefissato. Tutto questo con **zero minuti GPU** nella prima versione: le 28 predizioni ai 7 offset esistono già.

Se (c) e (d) sono vere, E04 consegna uno strumento riproducibile applicabile alla pipeline di villa. Se sono false, E04 consegna il tetto (b) e una misura onesta del perché: entrambi gli esiti si scrivono nella scheda.

---

## 2. Contesto necessario

### 2.1 Fatti verificati (E03-R01, 7 settembre 2026)

- Modello `ink_9um` (villa `3ea17f5…`, checkpoint seed 42 `e635558a…` e seed 43 `2aeaa85a…`, step 75000). Input: 21 fette pooled (media di 4 piani su 109, 9,596 µm per fetta); il modello vede 17 fette, di norma indici 2–18.
- Predizioni disponibili in locale, verificate per impronta nel [manifest E03](../reports/2026-09-07-e03-r01-manifest.json): per ciascun segmento di sviluppo (`pherc0139-w016`, `pherc0814-46527`) e seed (42, 43), un TIFF `uint8` per offset k ∈ {−5, −3, −2, 0, +2, +3, +5}; 28 TIFF in tutto (i 4 a k = 0 sono di E02). Percorsi in `runs/E02-R01/…` e `runs/E03-R01/infer-*/…/e03/out/*.tif` (cartella `runs/` ignorata da git, impronte nel manifest).
- Label held-out (`validation_mask == 1`, piano 10): w016 178 146 px in **due regioni** (bbox `[4944:5425, 3655:3955]` e `[4955:5322, 1803:2131]`); 0814 161 051 px in **una regione** (`[1624:2035, 258:817]`). Pixel di training (`supervision_mask`) separati; `pherc1667-w029` **sigillato** fino a E05.
- Curva E03: perdita massima held-out rispetto a k = 0 pari a 0,111; 0814 favorisce k > 0 con entrambi i seed; w016 favorisce k < 0 con il seed 42 e k = 0 con il seed 43; sui pixel di training la perdita massima è 0,027. Nessun controllo a costo zero (media dei seed, media −2/+2) aiuta.
- Volumi a 21 fette in locale: 0814 ufficiale (`runs/E03-R01/local-input/pherc0814-46527_z13.zarr`, impronta `bc742343…`) e spostati z1/z25. **w016 non è in locale** (≈ 11 GB; disco libero 27 GB): il dataset Kaggle `papyruslab-e02-input-w016` lo contiene.
- Strumenti: `scripts/e02_metrics.py` (`auroc`, `strata`, `regions`, `load_masks`), `scripts/e03_metrics.py` (`check_labels_allowed`, `build_run_report`), `scripts/e03_curve.py`, `scripts/e03_pool_shifted.py`, pilota `scripts/kaggle_e03.py` (prenotazioni GPU, pubblicazione dataset fail-closed), `scripts/tree_sha256.py`.

### 2.2 L'idea, in una riga per gradino

1. **Località.** L'errore di profondità della superficie tracciata è plausibilmente a macchie, non uniforme. Se l'offset migliore cambia da mattonella a mattonella in modo spazialmente coerente, lo spostamento uniforme di E03 sottostima il problema.
2. **Oracolo.** Scegliere per ogni mattonella l'offset migliore *con le label* dà il tetto di qualunque correzione. Scegliere con il seed 42 e valutare con il seed 43 (e viceversa) dice quanto di quel tetto è reale e quanto è rumore di selezione.
3. **Stimatore senza label.** Su un rotolo non letto le label non ci sono. Candidati: il profilo di luminosità lungo le fette (dove sta il foglio), la confidenza del modello per offset. Si tara su un segmento e si prova sull'altro.
4. **Mosaico.** Una predizione composta dalle 7 predizioni esistenti, scegliendo per mattonella l'offset dello stimatore. Se batte la finestra ufficiale sui pixel held-out con il criterio prefissato, è uno strumento.

### Decisioni già prese, e perché

- **Zero GPU nella prima versione** — tutto si calcola dalle 28 predizioni e dai volumi esistenti. Gli offset intermedi (±1, ±4) si misurano solo dopo, e solo se il mosaico funziona (passo 5b, gate). Motivo: la domanda "vale la pena" si risponde gratis; spendere GPU prima sarebbe scegliere con i numeri.
- **Mattonelle da 64 px (≈ 0,6 mm) allineate alla griglia dell'immagine, con griglia da 128 px come lettura secondaria** — 64 px dà decine di mattonelle per segmento (necessarie per parlare di "mappa"); 128 px ne dà una dozzina ma con AUROC più stabile. Nessuna delle due si sceglie guardando i risultati: si riportano entrambe, la primaria decide.
- **Idoneità di una mattonella preregistrata: ≥ 100 pixel held-out d'inchiostro e ≥ 100 di sfondo** — sotto, l'AUROC per mattonella è troppo rumorosa. Le mattonelle non idonee restano nel mosaico con k = 0 (la finestra ufficiale) e contano nella valutazione complessiva: lo strumento deve valere anche dove non sa scegliere.
- **Oracolo incrociato fra seed come stima del rumore di selezione** — scegliere e valutare sullo stesso seed gonfia il guadagno (chi sceglie il massimo fra 7 numeri rumorosi vince sempre qualcosa). Il seed gemello è un replicato indipendente del modello, non dei dati: la stima è ottimista ma è la migliore disponibile senza GPU, e viene dichiarata come tale.
- **Taratura incrociata fra segmenti per lo stimatore** — qualunque parametro dello stimatore si fissa su un segmento e si valuta sull'altro (due pieghe); si riportano solo le pieghe di test. I pixel di training non servono a tarare: il modello li ha memorizzati e la curva lì è quasi piatta.
- **Le regole di lettura (§5) sono scritte prima di calcolare** e i risultati si riportano per segmento e per seed, mai solo in media: lezione di E03.
- **Nessun training, nessuna modifica al modello, nessun ranking, nessuna lettura di w029** — come deciso nel [documento di decisione](../decisions/2026-09-06-dove-investire.md).
- **Punteggi del mosaico presi grezzi dai TIFF** — le 7 predizioni potrebbero avere calibrazioni diverse (un offset "sicuro" ovunque); il mosaico grezzo è la versione che un utente applicherebbe. Una variante con normalizzazione per mattonella è lettura secondaria, non primaria.

### Vincoli

- Pixel held-out mai usati per tarare nulla, salvo nella piega di test dove si misurano soltanto.
- Un writer per cartella; il socio lavora su `e04-socio` e possiede `docs/reports/2026-09-XX-e04-socio-*` e `runs/`.
- Run CPU su Kaggle da annunciare a Matteo; run GPU (solo passo 5b) con il suo "vai" per run e prenotazione nel registro.
- Congelamento di ciò che entra nella candidatura Progress Prize: **21 settembre 2026**.

---

## 3. Perimetro

### File da creare o modificare

| File | Cosa fare |
|---|---|
| `configs/e04/tiles.json` | inventario delle mattonelle idonee per segmento e griglia (passo 1) |
| `configs/e04/estimators.json` | definizione degli stimatori e dei loro parametri liberi, con la piega in cui si tarano (passo 4) |
| `scripts/e04_tiles.py` | griglia, idoneità, AUROC per mattonella e offset, mappe, statistica di località, oracolo e oracolo incrociato |
| `scripts/e04_features.py` | caratteristiche senza label per mattonella: profilo di luminosità dal volume a 21 fette, confidenza del modello per offset |
| `scripts/e04_mosaic.py` | costruzione del TIFF a mosaico da 7 TIFF + una mappa di offset; valutazione con `e03_metrics` |
| `scripts/build_e04_notebooks.py`, `scripts/kaggle_e04.py` | un notebook CPU per le caratteristiche di w016 su Kaggle (passo 4); riuso del pilota E03 |
| `tests/test_e04_*.py` | test su dati sintetici: griglia, idoneità, oracolo, mosaico, stimatori, controlli nulli |
| `docs/reports/e04-r01/` | JSON per mattonella, mappe, tabelle; scheda `docs/reports/2026-09-XX-e04-r01.md`; manifest |
| `docs/plans/2026-09-08-e04-compiti-socio.md`, `docs/plans/e04-prompt-codex-socio.md` | procedura unica S1 → S2 → S3 del socio |

### File da NON toccare

| File | Perché |
|---|---|
| `docs/reports/e03-r01/**`, `docs/reports/2026-09-07-e03-r01*.md/json` | esito congelato di E03: E04 lo legge, non lo modifica |
| `scripts/e03_*.py`, `configs/e03/*` | strumenti congelati; E04 li importa. Una modifica lì richiede un emendamento e i test di E03 |
| `pherc1667-w029` (qualunque percorso o dataset) | sigillato fino a E05 |

---

## 4. Passi

### Passo 0 — Base verificata

**Cosa:** verificare commit, test verdi (`pytest tests -q`), impronte dei 28 TIFF uguali a quelle del manifest E03, whitelist delle label superata. **Fatto quando:** un report `docs/reports/e04-r01/base.json` elenca i 28 TIFF con impronta e la conferma della whitelist.

### Passo 1 — Inventario delle mattonelle (zero GPU)

**Cosa:** per ogni segmento e per le griglie 64 e 128 px (origine (0,0) dell'immagine), contare per mattonella i pixel held-out d'inchiostro e di sfondo, i pixel di training, la regione di appartenenza. Applicare l'idoneità (≥ 100 e ≥ 100). **Output:** `configs/e04/tiles.json`. **Fatto quando:** il file esiste, i test passano, e la scheda riporta il numero di mattonelle idonee per segmento e griglia **prima** di qualunque AUROC.

### Passo 2 — Mappe dell'offset migliore e statistica di località (zero GPU)

**Cosa:** per ogni mattonella idonea, segmento, seed e offset: AUROC held-out (stesso codice di E02/E03 sui pixel della mattonella). Per mattonella: offset migliore k*, escursione (max − min), Δ(k) rispetto a k = 0. **Statistica di località (HA):** concordanza fra mattonelle adiacenti (frazione di coppie di vicini con lo stesso k*, o con |k*₁ − k*₂| ≤ 1 sulla scala campionata) confrontata con la distribuzione ottenuta permutando casualmente i k* fra le mattonelle 1 000 volte. **Output:** `docs/reports/e04-r01/tiles_<seg>_s<seed>_g<grid>.json`, mappe in testo (una cifra per mattonella) nella scheda.

### Passo 3 — Oracolo e oracolo incrociato (zero GPU)

**Cosa:** mosaico oracolo: per mattonella idonea il TIFF dell'offset k* scelto con le label **dello stesso seed**; mattonelle non idonee a k = 0. AUROC sull'intero insieme held-out del segmento. **Oracolo incrociato:** k* scelto con il seed 42, mosaico valutato con il seed 43, e viceversa. Guadagni G_oracolo e G_incrociato rispetto a k = 0 e rispetto al miglior offset uniforme del segmento. Intervalli con bootstrap sulle mattonelle (1 000 ricampionamenti). **Gate G_A (§5):** se G_incrociato < 0,02 su entrambi i segmenti, i passi 4–5 si eseguono comunque ma il piano dichiara già che lo strumento non può superare il criterio; la scheda registra il tetto come risultato.

### Passo 4 — Stimatori senza label (CPU; un run Kaggle per w016, da annunciare)

**Cosa:** caratteristiche per mattonella che non usano label:
- **P (profilo):** dal volume a 21 fette, luminosità media per fetta nella mattonella; posizione del picco z_p (con interpolazione parabolica sui tre punti attorno al massimo); stimatore k̂_P = offset campionato più vicino a (z_p − z_rif), con z_rif parametro libero tarato nella piega di taratura (atteso ≈ 10).
- **C (confidenza):** per offset, dal TIFF di quel offset nella mattonella: frazione di pixel con punteggio ≥ 128 più frazione ≤ 32 (quanto il modello "si sbilancia"); k̂_C = offset che massimizza la statistica. Parametri: le due soglie, tarate nella piega di taratura tra poche alternative elencate in `estimators.json`.
- **Controlli nulli:** k̂ casuale (200 estrazioni, media e 95° percentile), k̂ = miglior offset uniforme dell'altro segmento, k̂ = 0.
Per w016 il profilo P richiede il volume: notebook CPU Kaggle su `papyruslab-e02-input-w016` che scrive un solo JSON di profili per mattonella (poche centinaia di KB), scaricato e verificato per impronta. **Taratura incrociata:** piega A = taratura su 0814, prova su w016; piega B = il contrario. Si riportano solo le prove.

### Passo 5 — Mosaico con stimatore e verdetto (zero GPU)

**Cosa:** `e04_mosaic.py` costruisce il TIFF a mosaico per ogni (segmento di prova, seed, stimatore) e lo valuta con `e03_metrics` (AUROC, F1 alla soglia 91, strati, regioni). Confronti preregistrati (§5, HC e HD). **Fatto quando:** i JSON e la tabella sono nella scheda con tutte le celle, comprese le negative.

### Passo 5b — Offset intermedi (GPU, solo se HD è vera; un "vai" per run)

**Cosa:** se il mosaico supera HD, misurare k ∈ {−4, −1, +1, +4} sui due segmenti e due seed (16 run, ≈ 90 min GPU) per vedere se un passo più fine aggiunge guadagno. Altrimenti il passo non si esegue e la scheda lo dice.

### Passo 6 — Procedura unica del socio (branch `e04-socio`)

S1: pubblicazione delle 28 predizioni in un dataset Kaggle privato (impronte nel manifest) e **ricalcolo in cieco** di mappe e oracolo con codice proprio; S2: verifica di novità su "allineamento locale della profondità / per-tile z offset / depth alignment" nelle fonti pubbliche; S3: ricalcolo in cieco della valutazione degli stimatori nelle pieghe di prova. Confronto al passo 7 con lo stesso rigore del manifest E03 (confronto cella per cella, fail-closed).

### Passo 7 — Scheda, manifest, R3, consolidamento, congelamento per la candidatura

Scheda da `docs/templates/esperimento.md`; manifest con impronte di TIFF, mosaici, JSON, versioni; R3 Codex sull'esito; roadmap, README, AGENTS, documento di decisione aggiornati; pacchetto per la candidatura (testo del modulo, link, immagini) congelato il 21 settembre.

---

## 5. Criterio di esito, deciso prima della prova

Tutte le misure sui pixel held-out del piano 10; `held` = `validation_mask == 1`; mai mescolati con `train`. Per segmento e per seed, mai solo in media.

- **HA (località):** la mappa dei k* è "locale" se la concordanza fra vicini supera il 95° percentile delle 1 000 permutazioni, per almeno 3 delle 4 combinazioni segmento × seed sulla griglia 64. Altrimenti "non distinguibile dal rumore".
- **HB (tetto):** G_incrociato ≥ 0,02 su entrambi i segmenti per almeno un seed ⇒ "c'è un guadagno reale da recuperare". Se G_oracolo è grande ma G_incrociato piccolo ⇒ "il tetto è rumore di selezione", e lo si scrive così.
- **HC (stimatore):** nella piega di prova, il mosaico dello stimatore recupera ≥ 50 % di G_incrociato e supera k = 0 di ≥ 0,02 AUROC, per entrambi i seed. Controllo obbligatorio: deve superare anche il 95° percentile del controllo casuale e il controllo "offset uniforme dell'altro segmento".
- **HD (strumento):** HC vera in **entrambe** le pieghe (cioè su entrambi i segmenti di prova), senza peggiorare nessuna regione held-out di più di 0,01 e senza peggiorare l'F1 alla soglia 91 di più di 0,01.
- **Anomalie:** stimatore che sceglie lo stesso k in > 90 % delle mattonelle (degenerato: equivale a un offset uniforme, va detto); k* delle mattonelle tutti uguali fra i seed ma opposti fra segmenti (già noto da E03, non è nuovo); mattonelle idonee < 12 per segmento sulla griglia 64 (la griglia primaria passa a 128 e la scheda lo dichiara).
- **Ciò che nessun numero può dire qui:** la causa (superficie, modello, o entrambi); il comportamento su altri rotoli; l'effetto di offset intermedi non misurati (fino al passo 5b).

---

## 6. Verifica finale

```
./.venv/Scripts/python.exe -m pytest tests -q                         # atteso: tutti verdi
./.venv/Scripts/python.exe scripts/e04_tiles.py --validate            # atteso: 28 TIFF autenticati, mattonelle idonee contate
./.venv/Scripts/python.exe scripts/e04_mosaic.py --validate-reports   # atteso: tutte le celle di §5 presenti
./.venv/Scripts/python.exe scripts/e04_manifest.py --out docs/reports/2026-09-XX-e04-r01-manifest.json   # atteso: fail-closed, socio confrontato
```

Inoltre: nessun file cita `pherc1667-w029`; `git status` pulito; il diff tocca solo i file del §3.

---

## 7. Se il piano è sbagliato

Fermarsi, annotare, committare il coerente, segnalare. In particolare: se le mattonelle idonee sono troppo poche anche a 128 px, o se i volumi non sono raggiungibili, il piano si emenda (§11), non si aggira.

---

## 8. Fuori perimetro

Training o fine-tuning; modifica dei pesi o dell'architettura; ranking di zone; lettura di w029; offset intermedi prima di HD; stimatori basati sulla periodicità dei tratti (R13) e qualunque stimatore che usi label; applicazione a segmenti non letti (E06); modifiche a `scripts/e03_*`.

---

## 9. Divisione del lavoro

- **Matteo:** approva il piano congelato; annuncia/autorizza il run CPU Kaggle; "vai" per ogni run GPU del passo 5b; decide pubblicazione, licenza, candidatura, fusione di `e04-socio`.
- **Claude Code (writer):** passi 0–5, 7; scheda e manifest.
- **Codex (revisore, `gpt-5.6-sol`):** co-progettazione di questa bozza (giro di ricerca, sola lettura); R1 sul piano; R2 sul codice prima dei calcoli sui pixel held-out; R3 sull'esito.
- **Socio (`e04-socio`, Codex):** S1 → S2 → S3 in una procedura unica, dopo il passo 5.

### Calendario indicativo

8–9 settembre: piano congelato (R1). 9–11: passi 0–3 (R2 prima del passo 2). 11–14: passi 4–5. 14–17: socio. 17–21: passo 7 e congelamento per la candidatura. 22–30: 5b se HD, testo della candidatura, invio entro il 30.

---

## 10. Revisioni Codex e congelamento

*Da compilare: giro di co-progettazione (task read-only), R1 (adversarial-review).*

---

## 11. Emendamenti dopo il congelamento

*Nessuno.*

---

## 12. Al termine

- [ ] Tutti i passi eseguiti e verificati, o fermati con motivo scritto
- [ ] §5 letto come scritto, esiti negativi compresi
- [ ] Scheda, manifest, R3, consolidamento
- [ ] Commit e push del lavoro verificato; nessuna candidatura inviata dagli agenti
