# Dove investire le energie: regola, mappa delle opzioni e decisione (6–7 settembre 2026)

**Tipo:** decisione durevole con motivazione (prevista da [docs/07 §Artefatti](../07-procedura-operativa.md)).
**Stato: decisa il 7 settembre 2026** (sezione "Decisione", in fondo): rendering e profondità, misurati come tolleranza all'offset Z. Le sezioni precedenti sono state scritte il 6 settembre 2026, quando la scelta era rinviata di proposito a dopo E02, e restano come registro della regola e delle ipotesi di partenza; la sezione "Completamento della mappa" registra ciò che le fonti ufficiali hanno aggiunto il 7 settembre.

## L'obiettivo, come lo ha ribadito Matteo

L'obiettivo ideale è vincere un premio della Vesuvius Challenge e contribuire davvero alla lettura dei papiri. La via per arrivarci non è scommettere su un'idea, ma **capire l'intero processo, misurare dove si perde di più, e concentrare lì il lavoro di miglioramento** — producendo un contributo utile a noi e alla community, che possa anche meritare un premio. Un contributo tecnico verificabile è un risultato in sé, e i Progress Prizes mensili premiano esattamente questo.

## La regola con cui si deciderà

In una catena di stadi, migliorare uno stadio che non è il più debole non si vede nel risultato finale. Il punto debole non si indovina ragionando: **si misura**. Perciò:

1. **E02** costruisce il metro (dati di sviluppo e di verifica dimostrabilmente estranei al training, baseline congelata, metriche per segmento).
2. Con il metro si misura la **baseline stadio per stadio**: quanto si perde nella superficie, quanto nel rendering e nella profondità, quanto nel modello, quanto nel ranking.
3. **Solo allora** si sceglie dove investire: dove la perdita misurata è maggiore *e* il costo d'ingresso è alla nostra portata. La scelta viene scritta qui, con i numeri che l'hanno motivata, e diventa il tema di E03/E04.

Ciò che segue sono **ipotesi** da mettere alla prova, non conclusioni.

## Mappa degli stadi e ciò che oggi si sa

| Stadio | Perché potrebbe essere il collo di bottiglia | Costo d'ingresso per il team | Cosa si sa già (con livello di evidenza) |
|---|---|---|---|
| **Segmentazione e superficie** (seguire il foglio giusto dentro il rotolo) | Un errore qui rende inutile tutto ciò che segue; è il lavoro umano più costoso della Challenge | Alto: VC3D, apprendimento, molto tempo umano; terreno già presidiato da strumenti pubblici (R06–R08 nel [registro](../06-ricerca-community.md)) | L1: la community lo indica da anni come limite principale. **Verificato il 7 settembre 2026 (L0):** la pagina ufficiale *Open Problems* dedica alla superficie sei dei dodici problemi (2–6, 11); vedi "Completamento della mappa" |
| **Rendering e profondità di campionamento** (quali slice attorno alla superficie stimata) | Il model card dichiara i modelli "quite sensitive" a un offset in Z; una superficie stimata con un errore di una o due slice può degradare la predizione | Basso-medio: strumenti già in mano (E00), misurabile con il metro di E02 | L0 (model card); L2 dal codice: crop centrale fisso. Nessuna misura nostra della perdita in funzione dell'offset |
| **Modello di inchiostro** | Gli organizzatori scrivono che i modelli sono *"far from optimized"* | Alto: servono dati puliti (E02), quota GPU (30 h/settimana per account), e si compete con molti team attrezzati | L0 (model card). Differenziazione difficile |
| **Ranking e verifica** (dove guardare, come evitare falsi allarmi) | Poco lavoro pubblico rigoroso; l'unico tentativo noto al team è ScrollScout di Francesco ([nota](../05-scrollscout-e-piano-di-verifica.md)) | Basso: quasi solo CPU; si misura bene (Recall@K, confronti con selezione casuale) | L1 per ScrollScout; nessuna replica nostra. La carenza di rigore altrui è un'opportunità di contributo *metodologico* |
| **Il metro stesso** (valutazione con separazione training/test dimostrata) | Senza, nessun miglioramento è credibile; nella community le valutazioni rigorose sono rare | Basso-medio: è il lavoro di E02 comunque necessario | L1: contributi di valutazione (R02, R04) esistono e sono stati apprezzati |

## Due considerazioni di realismo

1. **First Letters** (dieci lettere leggibili in 4 cm² su un volume eleggibile) dipende soprattutto dalla segmentazione ed è la strada più lunga e più affollata. Non è esclusa: è la meta finale, da raggiungere dopo aver costruito credibilità e strumenti.
2. **Progress Prizes** premiano contributi verificabili e utili. Un metro rigoroso, uno studio di robustezza all'offset Z, un protocollo di ranking con controlli sono candidature credibili, e sono anche il modo di guadagnarsi la competenza per la strada lunga. Le condizioni e le scadenze correnti vanno rilette sul sito prima di ogni candidatura ([fonti](../fonti-e-verifiche.md)).

## Cosa NON era deciso al 6 settembre 2026 (superato: vedi "Cosa resta NON deciso" in fondo)

- Quale stadio ottimizzare per primo (si decide con i numeri di E02). → **Deciso il 7 settembre 2026.**
- Quale premio candidare e quale rotolo esplorare (dopo G3, come da procedura). → Premio: si lavora per un Progress Prize, candidatura da decidere con l'esito di E03; rotolo: ancora aperto.
- Se addestrare un modello proprio (solo se il metro mostra che il modello è il collo di bottiglia *e* il costo è sostenibile). → Ancora no.

## I numeri di E02 (7 settembre 2026), da cui partirà la scelta

Il metro esiste ([scheda E02](../reports/2026-09-07-e02-r01.md), gate G3 raggiunto). È intra-segmento: pixel con label ufficiale mai usati per la supervisione, dentro fogli che il modello ha studiato altrove, con adiacenza al training misurata. Baseline ufficiale `ink_9um`, seed 42, step 75000:

| Segmento (ruolo) | Pixel nuovi | AUROC | best-F1 | F1 a τ\* = 91 | F1 sui pixel studiati | entro 128 px dal training |
|---|---:|---:|---:|---:|---:|---:|
| PHerc0139 w016 (sviluppo) | 178.146 | 0,774 | 0,531 | 0,526 | 0,952 | 59 % |
| PHerc0814 46527 (sviluppo) | 161.051 | 0,874 | 0,753 | 0,748 | 0,989 | 45 % |
| PHerc1667 w029 (verifica) | 382.353 | sigillato | sigillato | sigillato | 0,986 | 23 % |

Letture utili alla scelta, senza anticiparla:

- **La perdita fra pixel studiati e pixel nuovi è la più grande della catena misurata finora:** da 0,95–0,99 a 0,53–0,75 di F1. È il fenomeno che il metro rende visibile; non dice ancora *quale stadio* lo produca.
- **Seed e segmento pesano molto:** sul w016 il seed 43 dà 0,751 contro 0,531 del seed 42 sugli stessi pixel nuovi; su 0814 i due seed sono vicini (0,740 e 0,753). Prima di attribuire un miglioramento a una modifica, la variabilità fra seed va messa nel conto (R02 aveva osservato lo stesso, 0,22 di F1).
- **L'adiacenza al training conta ma non spiega tutto:** su w016 i pixel a meno di 64 px dal training vanno meglio (AUROC 0,82) di quelli più lontani (0,69–0,74); su 0814 l'andamento non è monotono (0,996 → 0,898 → 0,805 → 0,930).
- **Il rendering e la profondità restano lo stadio più misurabile a basso costo:** la finestra Z è fissa (2–18 su 21 slice) e il model card dichiara i modelli sensibili all'offset; ora esiste il metro per misurarlo (E03), sui soli segmenti di sviluppo.
- **Il modello:** i 14 checkpoint pubblici e la media fra seed sono confrontabili a costo zero di training (E04); un training nostro resta fuori portata finché il metro non mostra che è lì la perdita e che vale il costo.

La scelta dello stadio è stata presa il 7 settembre 2026, con questi numeri, secondo la regola sopra: vedi la sezione seguente.

## Completamento della mappa (7 settembre 2026)

Prima di scegliere sono state rilette le fonti ufficiali che la mappa segnava come "da verificare (L0)": la pagina *Open Problems* (aggiornata il 10 luglio 2026), la pagina dei premi, il catalogo dei progetti della community e il model card di `ink_9um`. I fatti sono nella [nota di intake](../reports/2026-09-07-intake-dove-investire.md); qui ciò che cambia nella mappa:

- **La diagnostica è un problema aperto ufficiale.** Gli Open Problems 7 e 12 chiedono testualmente "diagnostica più forte per capire quale componente limita" e strumenti per distinguere *niente inchiostro* da *inchiostro non ancora recuperato*. La regola di questo documento ("misurare dove si perde") rientra in una categoria che gli organizzatori dichiarano di volere.
- **Tre dimensioni mancavano:** la qualità delle annotazioni (di superficie e d'inchiostro: Open Problem 4, issue villa #192 e #193), la trasferibilità dei risultati da `ink_9um` al modello principale a 2,4 µm (`ink_canonical_2um`, quello che gli organizzatori indicano come principale) e l'acquisizione della scansione (Open Problem 1). Le prime due vanno tenute nella mappa come dimensioni trasversali; la terza è fuori dalla portata del team. Codex, consultato in cieco, ha segnalato le stesse due lacune.
- **Il metro è piccolo in superficie:** i 721.550 pixel held-out coprono 0,66 cm² (0,31 cm² di sviluppo), contro finestre di ranking da 1 cm² e i 4 cm² di First Letters. Questo esclude oggi una valutazione credibile del ranking, e va ricordato per ogni prova che ragiona in finestre.
- **Il model card cambia il disegno di un test sull'offset Z (L0):** il training ha fatto *jitter* della finestra di 17 slice dentro le 21 ("makes the models handle small offsets reasonably well, but larger ones can still throw them off"). Quindi ±2 slice, l'intervallo raggiungibile con le opzioni `--layer-start/--layer-end`, è ciò che il modello è stato costruito per tollerare; l'informazione nuova sta oltre ±2, dove si arriva rifacendo il pooling con una finestra sorgente spostata. Il model card suggerisce anche la media di predizioni su finestre Z vicine come ensemble semplice.
- **Scadenza corrente dei Progress Prizes: 30 settembre 2026** (pagina premi, letta il 7 settembre 2026); criteri dichiarati: rilascio open source tempestivo, uso effettivo dalla community, miglioramenti quantitativi o qualitativi su dati reali, informazioni "insightful, actionable", documentazione.

## Decisione (7 settembre 2026)

**Stadio scelto: rendering e profondità di campionamento, misurato come *tolleranza all'offset Z* sui pixel held-out di sviluppo.** Decisione di Matteo del 7 settembre 2026, dopo la lettura dei numeri di E02, la rilettura delle fonti ufficiali e due proposte indipendenti confrontate in sessione: quella di Codex, formulata in cieco e conservata integralmente ([testo](../reports/2026-09-07-secondo-parere-codex-dove-investire.md)), e quella di Claude, scritta dopo. Il confronto è riassunto in fondo a questa sezione.

Definizioni. Il **surface volume** è la pila di 21 fette (slice) di scansione, spesse 9,6 µm ciascuna, attorno alla superficie stimata del foglio; il modello ne guarda 17 (oggi gli indici 2–18, centrati sul piano 10 dove sono annotate le label). L'**offset Z** è uno spostamento di quella finestra di un numero intero di slice; imita l'errore di chi stima la superficie un po' troppo in alto o in basso. La **tolleranza** è lo spostamento oltre il quale il riconoscimento dell'inchiostro sui pixel nuovi peggiora in modo apprezzabile. La domanda di E03 è: *quanto errore di posizione della superficie tollera `ink_9um` prima di perdere inchiostro sui pixel mai visti?*

### I numeri che hanno motivato la scelta

1. **Il metro non attribuisce ancora la perdita a uno stadio.** Il salto da 0,95–0,99 (pixel di training) a 0,53–0,75 di F1 (pixel held-out) è il divario di memorizzazione, non la ripartizione della perdita lungo la catena: per applicare la regola bisogna *variare* uno stadio a parità di tutto il resto. Con il metro attuale si possono variare solo il rendering (finestra Z, direzione, TTA) e il modello a pesi fissi (seed, step, ensemble); superficie e ranking no (le label vivono nelle coordinate delle superfici ufficiali; il ranking non ha abbastanza superficie held-out).
2. **Fra i due stadi variabili, il modello a pesi fissi è già stato pubblicato da R02** (scorecard dei 14 checkpoint sui tre held-out, docs/14; effetto del seed osservato). Il nostro contributo lì sarebbe incrementale. **Non abbiamo individuato una curva di tolleranza all'offset Z** per `ink_9um` nelle fonti consultate (catalogo ufficiale della community, registro R01–R12, model card, letti il 7 settembre 2026): il model card la evoca senza numeri. L'assenza dal catalogo non dimostra l'assenza di lavoro pubblico: la novità va verificata prima di rivendicarla in una candidatura.
3. **L'effetto del seed fissa il rumore di fondo:** su w016 il seed 43 dà F1 0,751 contro 0,531 del seed 42 sugli stessi pixel (ΔAUROC +0,162, Spearman 0,637), su 0814 i due seed coincidono (0,740 e 0,753). Ogni variante va confrontata **con il proprio seed**, mai "variante seed 43 contro baseline seed 42".
4. **La curva serve a due problemi aperti insieme:** dice a chi lavora sulla superficie (Open Problems 2–4) quanto deve essere precisa la superficie perché l'inchiostro sopravviva, e a chi lavora sull'inchiostro (7, 12) quanto pesa, da solo, un errore *uniforme* di posizione della finestra Z. Non misura errori locali della superficie, normali sbagliate o cambi di foglio: su quelli la curva non dice nulla, né in un senso né nell'altro.
5. **Il costo è alla nostra portata:** generatore dei notebook, pilota Kaggle, script delle metriche congelato e script di pooling ufficiale esistono; inferenze da 46 s (0814) a 353 s (w016) su una T4; pooling 6–38 s su CPU Kaggle; quota 30 h/settimana.

### Le cinque decisioni di dettaglio

1. **Ampiezza degli offset: fino a ±5 slice (≈ 48 µm), in due tappe.** Tappa 1: offset ±2 con `--layer-start/--layer-end` sugli input poolati esistenti (finestre 0–16 e 4–20), su w016 e 0814, seed 42 e 43: 8 inferenze. Gate fra le tappe (identità, orientamento sui pixel di training, metriche). Tappa 2: offset ±3 con quattro nuovi pooling (finestra sorgente spostata di 12 piani: `source_z_slice` [1, 85] e [25, 109]) e ±5 combinando pooling spostato e finestra spostata nella stessa direzione: 16 inferenze. Totale 24 inferenze nuove più lo zero già in mano. Scartata l'opzione "solo ±2" (proposta di Codex): è l'intervallo su cui il training ha fatto jitter, quindi la parte meno informativa; resta come prima tappa.
2. **Il risultato è la curva, non una finestra migliore.** Per ogni seed e segmento si riporta AUROC(offset); la tolleranza è il primo offset al quale l'AUROC media sui due segmenti perde almeno 0,05 rispetto allo zero. Nessuna scelta di "offset vincente": con quattro combinazioni seed × segmento se ne troverebbe sempre uno per caso. Se un offset diverso da zero risultasse migliore su entrambi i seed e su entrambi i segmenti, sarebbe un segnale di disallineamento delle label, da indagare e non da adottare.
3. **Due controlli a costo zero GPU dentro E03,** calcolati sui TIFF già conservati: media dei seed 42 e 43 (finestra centrale) e media delle finestre −2/+2 per seed (l'ensemble suggerito dal model card), confrontate con la finestra centrale dello stesso seed. Rispondono alla domanda operativa di Codex: a pari costo conviene mediare due finestre o due seed?
4. **Progress Prize:** si lavora come se la scadenza fosse il 30 settembre 2026, ma la candidatura si decide solo dopo la revisione dell'esito, e nessuna scorciatoia sulla revisione per fare in tempo. Candidabile, se la curva è informativa: "tolleranza di `ink_9um` all'offset di superficie, misurata su pixel held-out con seed e strati dichiarati, più il metro riproducibile", con attribuzione esplicita a R02. Non candidabili: la replica della pipeline, il metro da solo, l'effetto del seed, la semplice idea di mediare finestre Z. Condizioni ufficiali (pagina dei premi, sezione *Terms and Conditions*, riletta il 7 settembre 2026): il codice **non** deve essere open source al momento della submission, ma va rilasciato con licenza permissiva per **accettare** il premio; il rilascio anticipato è favorito nella valutazione dei Progress Prizes; la registrazione Discord è richiesta testualmente nella sezione del Grand Prize e non compare nei requisiti dei Progress Prizes. Licenza e pubblicazione del repository restano decisioni separate di Matteo, da prendere con il risultato in mano.
5. **Dopo E03:** E04 confronta il modello a pesi fissi (ensemble, pochi step prefissati) solo se E03 lo giustifica; training proprio, segmentazione e ranking restano fuori. Il socio avrà compiti indipendenti definiti nel piano E03 (per esempio i pooling spostati sul Mac, con confronto delle impronte).

### Prova minima di E03, da congelare nel piano

- **Dati:** pixel held-out di `pherc0139-w016` e `pherc0814-46527`; pixel di training solo come controllo di identità e orientamento; `pherc1667-w029` sigillato, nessun run.
- **Baseline:** identica a E02 (villa `3ea17f5`, `ink_9um` @ `7109667…`, seed 42 e 43 allo step 75000, stessi parametri, finestra centrale 2–18).
- **Varianti:** offset in slice {−5, −3, −2, +2, +3, +5}; segno negativo = finestra spostata verso indici minori. Nessun'altra variante (direzione, TTA, step) in E03.
- **Metrica primaria:** AUROC sui pixel held-out, per segmento e per seed. **Secondarie:** best-F1, F1 alla soglia congelata τ\* = 91, valori per strato di distanza e per regione, Spearman fra ogni variante e la finestra centrale dello stesso seed.
- **Ipotesi preregistrata:** la curva è piatta entro ±2 (come atteso dal jitter del training) e decade oltre; il numero consegnato è la tolleranza per seed, con l'eventuale asimmetria fra i due versi. Criterio di lettura per i controlli: una media (di seed o di finestre) "aiuta" solo se migliora l'AUROC su entrambi i segmenti senza peggiorare di oltre 0,01 su nessuno dei due.
- **Ordine:** tappa 1 → gate → tappa 2; run in sequenza, uno per volta, con download e metriche prima del run successivo (la deviazione 7 di E02 non si ripete); un "vai" di Matteo per run.
- **Budget proposto:** 2,5–3,5 ore di quota GPU (tetto 4 ore), 4 run CPU di pooling, 2–3 sessioni umane; nessuna spesa.
- **Revisioni Codex:** piano prima dell'esecuzione; esito prima del consolidamento.

### Alternative scartate e perché

| Alternativa | Perché non ora |
|---|---|
| Superficie e segmentazione (VC3D, mesh, fibre, spirale) | Il metro non può misurarla: le label vivono nelle coordinate delle superfici ufficiali; costo d'ingresso di settimane; terreno presidiato da strumenti pubblici (R06–R08, gara Surface Detection). Resta la strada obbligata per First Letters, dopo |
| Modello a pesi fissi come stadio primario (14 checkpoint, ensemble) | R02 ha già pubblicato la scorecard; con 14 candidati e due segmenti si trova sempre "il migliore" e il vantaggio si sgonfia sul segmento sigillato. Entra come controllo gratuito in E03 e come E04 |
| Training proprio, pseudo-label, modelli 3D, DINO | Nessuna diagnosi che dica che la perdita è lì; T4 e 30 h/settimana; i pochi pixel held-out diventerebbero l'unico segnale di selezione |
| Ranking e verifica (ScrollScout) | 0,31 cm² held-out di sviluppo contro finestre da 1 cm²: nessuna valutazione credibile possibile oggi; si riapre dopo E06 su un volume eleggibile |
| Il metro come progetto a sé | E02 basta per questa decisione; il valore aggiunto rispetto a R02 è la replica, gli strati, la soglia congelata e il sigillo: infrastruttura, non candidatura |
| Calibrazione globale dei punteggi | Fra F1 a τ\* = 91 e best-F1 del seed 42 c'è 0,005: non è lì il divario |
| Solo ±2 slice (proposta di Codex) | È l'intervallo del jitter di training: misura ciò che il modello è stato costruito per tollerare. Resta come tappa 1 |
| Acquisizione, infrastruttura cloud, First Letters immediato | Fuori dalla portata del team, o senza label sui volumi eleggibili |

### Cosa ci farebbe cambiare idea

- **Curva piatta fino a ±5 su entrambi i seed:** nessun decadimento rilevato agli offset uniformi campionati sui due segmenti di sviluppo. Non assolve il rendering in generale (errori locali, normali sbagliate e cambi di foglio non sono stati variati), ma dice che insistere sugli offset uniformi non paga. Passo operativo, non attribuzione causale: si passa a E04 (modello a pesi fissi) e la scelta dello stadio si riapre verso la qualità delle annotazioni o la valutazione del modello a 2,4 µm, dopo una verifica di compatibilità e costo.
- **Curva che decade solo per il seed 42:** sensibilità all'offset dipendente dal seed, cioè un'interazione fra modello e offset, non una causa "solo del modello". Passo operativo: priorità al confronto fra modelli a pesi fissi (E04), tenendo l'offset come fattore.
- **Un offset diverso da zero migliore ovunque:** possibile disallineamento delle label; fermarsi e indagare prima di qualunque altro run.
- **Costo oltre il tetto o fallimenti tecnici ripetuti:** arresto registrato come risultato, con causa e prossima prova proposta.

### Le due proposte a confronto

| | Codex (in cieco) | Claude |
|---|---|---|
| Stadio | Inferenza a pesi fissi: separare l'effetto della profondità da quello del modello | Rendering e profondità come misura di tolleranza all'offset Z |
| Intervallo Z | Solo ±2 (8 inferenze) | ±2, ±3, ±5 (24 inferenze, 4 pooling CPU) |
| Domanda primaria | A pari costo, conviene mediare due finestre Z o due seed? | Quanto offset tollera il modello prima di perdere inchiostro? |
| Costo | 45–70 min GPU | 2,5–3,5 h GPU |
| Progress Prize | "Quando spendere due inferenze su Z e quando su due seed" | "Tolleranza all'offset di superficie + metro riproducibile" |

Accordi: stadio di partenza (variare l'inferenza a pesi fissi, non il training); niente segmentazione, training o ranking ora; confronti sempre entro lo stesso seed; media dei seed come primo controllo gratuito; R02 da attribuire; il metro e l'effetto del seed non sono candidature; riapertura della scelta se non si rileva decadimento agli offset campionati; nessuna lettura di w029. Disaccordo: l'ampiezza degli offset; Matteo ha scelto l'intervallo ampio in due tappe, che contiene per intero la proposta di Codex come prima tappa.

### Revisione Codex della decisione scritta (7 settembre 2026)

Canale: plugin `codex@openai-codex` 1.0.6, `adversarial-review` sull'albero di lavoro, sola lettura, modello `gpt-6-astra` (job `review-mtr5t041-gzsfw0`, 3 min 6 s). Verdetto: "da correggere prima del consolidamento: tre affermazioni eccedono le evidenze; numeri E02, intervalli di pooling e conteggio delle 24 inferenze coerenti; la scelta dello stadio resta ferma". Tre finding, **tutti accettati** e corretti nel testo sopra:

| # | Sev. | Finding (sintesi) | Correzione |
|---|---|---|---|
| 1 | P1 | "Cosa ci farebbe cambiare idea" traeva conclusioni causali che il disegno non identifica: una curva piatta agli offset uniformi non assolve il rendering per ogni errore di superficie; un decadimento sul solo seed 42 è un'interazione modello–offset, non una causa "del modello" | riformulate come osservazioni ("nessun decadimento rilevato agli offset uniformi campionati", "sensibilità dipendente dal seed") con passi operativi distinti dalle attribuzioni causali; allineato il punto 4 dei "numeri" |
| 2 | P2 | "Nessuno ha pubblicato" era sostenuto solo dalla consultazione del catalogo; ripetuto nella roadmap come motivo dell'investimento | sostituito con "non abbiamo individuato ... nelle fonti consultate", novità da verificare prima della candidatura; roadmap allineata |
| 3 | P2 | La candidatura era subordinata a codice già open source e a registrazione Discord; i Terms and Conditions ufficiali richiedono l'apertura per *accettare* il premio, non alla submission, e Discord compare solo nella sezione Grand Prize | verificato alla fonte (citazioni testuali nell'[intake](../reports/2026-09-07-intake-dove-investire.md) §2) e corretto qui, nell'intake e in [fonti e verifiche](../fonti-e-verifiche.md) |

Nessun secondo giro: le correzioni sono di formulazione e verificabili a vista.

## Cosa resta NON deciso

- La licenza del codice e la pubblicazione del repository (necessarie per accettare un premio, non per candidarsi).
- Se e quando candidare a un Progress Prize: solo con l'esito di E03 revisionato.
- Quale rotolo eleggibile esplorare in E06.
- Se addestrare un modello proprio: no, finché il metro non mostra che la perdita è lì e che il costo è sostenibile.

## Aggiornamenti

- 2026-09-06 — documento creato dopo E00 ed E01, su richiesta di Matteo di rendere esplicito che la scelta è rinviata e con quale regola verrà presa.
- 2026-09-07 — aggiunti i numeri di E02 (gate G3 raggiunto); la scelta resta da prendere, con i numeri, nella sessione successiva.
- 2026-09-07 (sessione successiva) — fonti ufficiali rilette ([intake](../reports/2026-09-07-intake-dove-investire.md)); secondo parere di Codex in cieco ([testo](../reports/2026-09-07-secondo-parere-codex-dove-investire.md)); **decisione di Matteo:** rendering e profondità, misurati come tolleranza all'offset Z fino a ±5 slice in due tappe; cinque decisioni di dettaglio, prova minima, alternative scartate e condizioni di ripensamento scritte sopra. La sezione "Cosa NON è deciso" precedente è sostituita da "Cosa resta NON deciso".
- 2026-09-07 (sera) — **E03-R01 completato e revisionato** ([scheda](../reports/2026-09-07-e03-r01.md), [manifest](../reports/2026-09-07-e03-r01-manifest.json), R3 nel [piano §10](../plans/2026-09-07-e03-tolleranza-offset-z.md)). Il caso realizzato non è nessuno dei tre previsti in "Cosa ci farebbe cambiare idea": la curva non è piatta (perdita fino a 0,111 di AUROC held-out rispetto alla finestra ufficiale), il decadimento non riguarda un solo seed, e nessun offset è migliore ovunque (regola di anomalia non attivata). È un quarto caso: **sensibilità forte, dipendente dal segmento e dal verso, sui due segmenti misurati** (PHerc0814 favorisce gli offset positivi in tutti i confronti campionati; w016 quelli negativi con il seed 42 e il centro con il seed 43); la tolleranza definita come media sui segmenti non lo rileva. Nessuna condizione scatta da sola: **l'applicazione delle condizioni di ripensamento, il seguito (E04 come deciso oppure ridefinito) e la candidatura restano decisioni di Matteo**, non prese in questo aggiornamento. Le opzioni non approvate sono elencate nella scheda, sezione "Decisione successiva".
