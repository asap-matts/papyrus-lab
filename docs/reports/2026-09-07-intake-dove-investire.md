# Intake per la decisione "dove investire" — fonti rilette il 7 settembre 2026

**Tipo:** nota di intake (docs/07 §1), scritta prima della decisione. Contiene soltanto fatti e fonti con il loro livello di evidenza; **non** contiene proposte né valutazioni. Serve a completare la mappa delle opzioni del [documento di decisione](../decisions/2026-09-06-dove-investire.md) prima di scegliere.

Contesto: E02 è chiuso (gate G3 raggiunto il 7 settembre 2026, [scheda](2026-09-07-e02-r01.md), [manifest](2026-09-07-e02-r01-manifest.json)). Il documento di decisione segnava come "da verificare (L0)" la pagina ufficiale *Open Problems*: è stata riletta oggi, insieme alla pagina dei premi, al catalogo dei progetti della community e al model card di `ink_9um`.

## 1. Pagina ufficiale *Open Problems* (L0; aggiornata il 10 luglio 2026)

Fonte: https://scrollprize.org/2026_open_problems, letta il 7 settembre 2026. Dodici problemi aperti, in sintesi fedele:

| # | Problema | Cosa chiedono gli organizzatori | Stadio della nostra catena |
|---|---|---|---|
| 1 | Regioni compresse: la diffusione dei raggi X nelle zone dense degrada la scansione | metriche di qualità della scansione, ricette di acquisizione per rotolo | scansione (a monte di tutto) |
| 2 | Predizione di superficie e topologia: buchi, falsi positivi, fusioni fra fogli vicini | dataset con label meglio localizzate sul recto, modelli che preservino la topologia | superficie |
| 3 | Tracciamento della mesh e geometria (C++, ottimizzazione) | riparazione topologica automatica, vincoli di continuità | superficie |
| 4 | Qualità delle label di superficie ("uno dei principali colli di bottiglia dell'unwrapping") | *label snapping* sul segnale CT, *active learning* | superficie / annotazione |
| 5 | Tracciamento delle fibre | tracciamento conservativo e robusto su lunghe distanze | superficie |
| 6 | Spirale globale (*spiral fitting*) | suite di valutazione e funzioni di loss migliori, automazione delle annotazioni di *winding number* | superficie / valutazione |
| 7 | **Generalizzazione dell'ink detection** ("pseudo-labeling: bootstrapping weak signals") | "diagnosi migliori per distinguere *niente inchiostro* da *inchiostro non ancora recuperato*"; training multi-rotolo; label migliori; "diagnostica più forte". Testo: "non è sempre chiaro quale parte della pipeline limita" | modello / rendering / valutazione |
| 8 | Segmentazione 3D diretta dell'inchiostro (scansioni ad alta risoluzione, PHerc. Paris 4) | segmentazione volumetrica a livello di voxel | modello |
| 9 | Rappresentazioni auto-supervisionate (DINO 3D) | modelli senza label per voxel, raffinamento di label "fuzzy" | modello / annotazione |
| 10 | Scala dei dati e infrastruttura | pipeline cloud-native su OME-Zarr, inferenza a tile, output ispezionabili in VC3D | infrastruttura |
| 11 | Tracciamento neurale della mesh (in pausa) | — | superficie |
| 12 | **Generalizzazione fra rotoli** dell'inchiostro | training multi-rotolo, label robuste, "diagnostica più forte per capire quale componente limita" | modello / valutazione |

Le "sei modalità di contributo principali" elencate dalla pagina sono: superficie e topologia; geometria della mesh e C++; annotazione 3D e active learning; tracciamento delle fibre; valutazione dello spiral fit; deep learning 3D e inchiostro. La pagina cita il modello principale a 2,4 µm (`ink_canonical_2um`, ResNet3D-50 + decoder U-Net 2D) e i checkpoint iterativi con pseudo-label su PHerc. 1667; `ink_9um` non è nominato come modello principale. Cita anche, come "progresso recente" sul problema 12, uno sciame di agenti autonomi (marzo 2026) che avrebbe quasi raddoppiato il Dice su pseudo-label fra PHerc. 0139 (training) e PHerc. 1667 (test): risultato riportato dagli organizzatori, non replicato da noi (L1 per il numero).

## 2. Pagina ufficiale dei premi (L0)

Fonte: https://scrollprize.org/prizes, letta il 7 settembre 2026.

- **Progress Prizes:** prossima scadenza **30 settembre 2026, 23:59 Pacific**; 20.000 $ garantiti alla miglior submission del mese, più premi da 20.000 a 500 $ per altri contributi. Criteri dichiarati: rilascio open source tempestivo, uso effettivo da parte della community, miglioramenti quantitativi o qualitativi su dati reali, correzione di bug in strumenti esistenti, informazioni "insightful, actionable", documentazione eccellente. Ammesso qualunque contributo che affronti gli *Open Problems* (inclusi ink detection, surface prediction, unwrapping, miglioramenti a VC3D). Le idee pubbliche sono le issue GitHub di villa con etichetta `help wanted` / `good first issue`: al 7 settembre 2026 sono tre, tutte dell'aprile 2025: #191 predizioni di superficie e fibre in aree compresse o molto curve; #192 label 3D accurate dell'inchiostro; #193 metodi per generare label di superficie, fibre o inchiostro.
- **First Letters:** 50.000 $ per rotolo, dieci lettere leggibili in un'area di 4 cm² su uno dei 13 volumi eleggibili (PHerc0125, 0191, 0211, 0257, 0268, 0358, 0800, 0813, 0826, 1203, 1218, 1447, 1545); mesh tifxyz con parametrizzazione 2D generata programmaticamente; finestra del modello non superiore a 0,5 × 0,5 mm; nessuna sovrapposizione con i dati di training; scadenza 25 giugno 2027.
- **Titolo di PHerc. Paris 4:** 50.000 $, stesse condizioni tecniche, resta aperto finché non viene vinto.
- **Grand Prize 2027:** 1.000.000 $ complessivi, srotolamento completo di un rotolo eleggibile con il 70 % dei caratteri leggibili per colonna.
- Condizioni comuni (sezione *Terms and Conditions*, testuale): "You agree to make your method open source if you win a prize. It does not have to be open source at the time of submission, but you have to make it open source under a permissive license to accept the prize"; per i Progress Prizes la pagina dichiara di favorire submission che "are released or open-sourced early"; dataset creati sotto CC BY-NC 4.0; riproducibilità (Docker consigliato, seed fissi); nessuna pubblicazione prima dell'annuncio per i premi di scoperta. La registrazione Discord compare testualmente nella sezione del Grand Prize ("To qualify, you must have registered on the Vesuvius Challenge Discord at the time of the submission") e **non** nella sezione Progress Prizes né nei Terms and Conditions. Le submission ai Progress Prizes passano da un modulo (Submission Form) e sono valutate mensilmente.

La scadenza dei Progress Prizes riportata in [fonti e verifiche](../fonti-e-verifiche.md) (31 agosto 2026) è superata: la pagina ne indica ora una successiva.

**Modulo di submission dei Progress Prizes** (Google Form collegato dalla pagina dei premi, letto il 7 settembre 2026, intestato "September 2026 Progress Prizes"). Campi obbligatori: e-mail; nome completo; descrizione del team (individuale o gruppo, con i membri); **URL del contributo** (repository GitHub o PR, anche più d'uno); **"What is your contribution?"**, testo libero in cui indicare (1) quali dati dei rotoli sono stati usati, (2) l'impatto sulla lettura dei rotoli, (3) le novità abilitate, (4) le prove fornite; accettazione dei Terms and Conditions. Facoltativo: nome su Discord. Condizioni richiamate dal modulo: impegno ad aprire il metodo con licenza permissiva **in caso di vittoria**; trenta giorni per i dati di pagamento dopo l'annuncio; premi a discrezione di Scroll Prize, Inc. Conseguenza pratica: la candidatura richiede un URL raggiungibile dai valutatori, quindi la decisione sulla pubblicazione del repository (oggi privato) precede la submission.

## 3. Catalogo ufficiale dei progetti della community (L0 per la presenza nel catalogo, L1 per i contenuti)

Fonte: https://scrollprize.org/community_projects, letta il 7 settembre 2026. Voci pertinenti alla nostra catena, oltre a quelle già nel [registro](../06-ricerca-community.md):

- **Valutazione dell'ink detection:** "Ink detection validation harness" di khj1222 (il nostro R02) è catalogato, con la motivazione "the ink-detection tutorial trains with no held-out data"; "Ink detection model resolution analysis" (Kirchhoff et al.); "Kaggle top model analysis" (Chesler).
- **Inferenza e varianti a pesi fissi:** "Scroll-specific augmentations" (pscamillo: Squeeze, Decohesion+Warp, Ring, Streak; TTA e benchmark di ablazione); "Fast/low-memory GP ink detection".
- **Qualità dei dati e QA geometrica:** scroll-data-audit (R04), vesuvius-repro (R05), tifxyz-repair, TIFXYZ Doctor (QA deterministica con benchmark su 709 patch verificate da umani), spiralcheck (valutazione held-out di spiral fit, matrice di difetti piantati), Herculaneum Scroll Tools (QA di consistenza CT delle predizioni m7), qa_holescan (perdita di z-slice), "Phantom contamination audit" (16,9 % di chunk fantasma), "Surface geometry failure diagnostic" (analisi stratificata dei fallimenti con 200 patch di riferimento).
- **Ranking e ricerca visiva:** Scroll Sleuth (ricerca visiva dell'inchiostro con più modalità di visualizzazione); nessuna voce di *ranking* di finestre con protocollo di valutazione. ScrollScout (R11) non compare nel catalogo alla data di lettura.
- **Modelli:** volumetric ink detection (Chesler, Johnson), ScrollMAE, DINO non supervisionato, Vesuvius AutoResearch (R09), Inkalyzer (XAI), pretraining su rotoli.
- **Label:** ink labels di Scroll 1, 4, 5 (Bodill, Repushko, Johnson), Ink Generator e visualizzazione delle feature (Stewart).

## 4. Model card di `ink_9um` (L0), citazioni testuali

Fonte: https://huggingface.co/scrollprize/ink_9um, riletta il 7 settembre 2026 (revisione usata in E00–E02: `7109667e…`).

- Sezione *Models*: "the z window jitters over 17 of the 21 slices so the models don't lock onto one exact depth"; "Different steps behave a bit differently on different segments, so it's worth trying a few".
- Sezione *Tips*: "If a checkpoint is not responding well on your data, it might just be a z layer offset; the models can be quite sensitive to it"; "picking a different z window (--layer-start/--layer-end) can help. Averaging predictions over a few nearby z windows also works as a simple ensemble"; "Training on jittered 17-of-21 windows makes the models handle small offsets reasonably well, but larger ones can still throw them off".
- Sezione *Train it yourself*: "These models are _far_ from optimized. Better augmentation, longer training, other architectures, ensembling, and more data are all open directions".

Conseguenza fattuale per un eventuale test sull'offset Z: la finestra di 17 slice dentro le 21 può spostarsi di al massimo ±2 slice con `--layer-start/--layer-end`, ed è esattamente l'intervallo su cui il training ha fatto *jitter*; offset maggiori richiedono di rifare il pooling dal livello 2 del volume a 2,4 µm con un `source_z_slice` diverso (109 piani disponibili, 13–96 usati; una slice poolata = 4 piani sorgente). Il model card suggerisce anche la media di predizioni su finestre Z vicine come ensemble.

## 5. Fatti derivati dal manifest E02 utili alla scelta (L3, calcolati oggi dai numeri già pubblicati)

- Superficie fisica dei pixel held-out (pixel di 9,596 µm di lato, 92,08 µm² ciascuno): w016 178.146 px = 16,4 mm²; 0814 161.051 px = 14,8 mm²; w029 382.353 px = 35,2 mm². Totale 66,4 mm² = 0,66 cm², di cui 31,2 mm² di sviluppo. Una finestra ScrollScout da 10 mm di lato è 1 cm²; l'area di First Letters è 4 cm².
- Lo strato `<64` di 0814 contiene 60 pixel d'inchiostro su 35.799 (frazione 0,0017): l'AUROC di quello strato (0,996 seed 42, 0,999 seed 43) poggia su pochissimi positivi.
- Mediana del punteggio TIFF sui pixel d'inchiostro, seed 42: w016 held 108 contro train 201; 0814 held 155 contro train 199. Seed 43: w016 held 164; 0814 held 167.
- Regioni di w016 (seed 42 / seed 43): regione 1 AUROC 0,824 / 0,952; regione 2 AUROC 0,723 / 0,914.
- Differenza fra seed sugli held-out: w016 ΔAUROC +0,162, Spearman 0,637; 0814 ΔAUROC −0,012, Spearman 0,864.
- I TIFF dei seed 42 e 43 dei due segmenti di sviluppo sono conservati in locale con hash: un confronto fra le loro medie non richiede GPU.
- Costi misurati in E02: inferenza 46–48 s (0814), 315–353 s (w016), 446–455 s (w029) su una T4; sessioni da 2 min 30 s a 10 min 18 s; pooling 6–38 s su Kaggle CPU; quota 30 h/settimana per account.

## 6. Mappa ampliata delle opzioni, con ciò che il metro E02 può variare

Tabella fattuale: dice se lo stadio è misurabile con il metro attuale, non se conviene.

| Opzione | Fonte ufficiale che la indica | Il metro E02 può misurarla? |
|---|---|---|
| Qualità della scansione, acquisizione | Open Problem 1 | no (dati fissi) |
| Superficie: predizione, mesh, label snapping, fibre, spirale | Open Problems 2–6, 11; issue #191, #193 | no: le label vivono nelle coordinate delle superfici ufficiali |
| Rendering: finestra Z (±2 con le opzioni; oltre con nuovo pooling), media su finestre Z vicine, direzione, TTA | model card *Tips*; catalogo (augmentations/TTA) | sì, a pesi fissi |
| Modello a pesi fissi: seed, step (14 checkpoint), ensemble, calibrazione dei punteggi | model card *Models*; R02 docs/14 | sì |
| Modello con training: fine-tuning, pseudo-label, multi-rotolo, 3D, DINO | Open Problems 7, 8, 9, 12; model card *Train it yourself* | sì per la misura, ma il training è fuori dal metro |
| Diagnostica: "quale componente limita", "niente inchiostro vs non ancora recuperato" | Open Problems 7 e 12 (testuale) | è ciò che il metro produce, per costruzione |
| Valutazione e label: benchmark, held-out, audit | catalogo (validation harness = R02, resolution analysis); issue #192 | è E02 |
| Ranking e verifica umana di zone | nessun problema aperto dedicato; catalogo: Scroll Sleuth | limitato: 0,31 cm² held-out di sviluppo |
| Infrastruttura cloud-native, output ispezionabili | Open Problem 10 | non pertinente al metro |
| Scoperta su volume eleggibile (First Letters, titolo) | pagina premi | no: nessuna label sui volumi eleggibili |

## Aggiornamenti

- 2026-09-07 — nota creata prima della decisione; fonti ufficiali rilette; nessuna proposta contenuta.
