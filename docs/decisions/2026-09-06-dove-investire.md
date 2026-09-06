# Dove investire le energie: stato della decisione al 6 settembre 2026

**Tipo:** decisione durevole con motivazione (prevista da [docs/07 §Artefatti](../07-procedura-operativa.md)).
**Stato: decisione rinviata, di proposito, a dopo E02.** Questo documento fissa l'obiettivo, la regola con cui si deciderà, e la mappa delle opzioni con ciò che oggi si sa di ciascuna, così che nessuno le confonda per scelte già fatte.

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
| **Segmentazione e superficie** (seguire il foglio giusto dentro il rotolo) | Un errore qui rende inutile tutto ciò che segue; è il lavoro umano più costoso della Challenge | Alto: VC3D, apprendimento, molto tempo umano; terreno già presidiato da strumenti pubblici (R06–R08 nel [registro](../06-ricerca-community.md)) | L1: la community lo indica da anni come limite principale. **Da verificare (L0):** la posizione della pagina ufficiale *Open Problems* — non ancora riletta a questo scopo |
| **Rendering e profondità di campionamento** (quali slice attorno alla superficie stimata) | Il model card dichiara i modelli "quite sensitive" a un offset in Z; una superficie stimata con un errore di una o due slice può degradare la predizione | Basso-medio: strumenti già in mano (E00), misurabile con il metro di E02 | L0 (model card); L2 dal codice: crop centrale fisso. Nessuna misura nostra della perdita in funzione dell'offset |
| **Modello di inchiostro** | Gli organizzatori scrivono che i modelli sono *"far from optimized"* | Alto: servono dati puliti (E02), quota GPU (30 h/settimana per account), e si compete con molti team attrezzati | L0 (model card). Differenziazione difficile |
| **Ranking e verifica** (dove guardare, come evitare falsi allarmi) | Poco lavoro pubblico rigoroso; l'unico tentativo noto al team è ScrollScout di Francesco ([nota](../05-scrollscout-e-piano-di-verifica.md)) | Basso: quasi solo CPU; si misura bene (Recall@K, confronti con selezione casuale) | L1 per ScrollScout; nessuna replica nostra. La carenza di rigore altrui è un'opportunità di contributo *metodologico* |
| **Il metro stesso** (valutazione con separazione training/test dimostrata) | Senza, nessun miglioramento è credibile; nella community le valutazioni rigorose sono rare | Basso-medio: è il lavoro di E02 comunque necessario | L1: contributi di valutazione (R02, R04) esistono e sono stati apprezzati |

## Due considerazioni di realismo

1. **First Letters** (dieci lettere leggibili in 4 cm² su un volume eleggibile) dipende soprattutto dalla segmentazione ed è la strada più lunga e più affollata. Non è esclusa: è la meta finale, da raggiungere dopo aver costruito credibilità e strumenti.
2. **Progress Prizes** premiano contributi verificabili e utili. Un metro rigoroso, uno studio di robustezza all'offset Z, un protocollo di ranking con controlli sono candidature credibili, e sono anche il modo di guadagnarsi la competenza per la strada lunga. Le condizioni e le scadenze correnti vanno rilette sul sito prima di ogni candidatura ([fonti](../fonti-e-verifiche.md)).

## Cosa NON è deciso

- Quale stadio ottimizzare per primo (si decide con i numeri di E02).
- Quale premio candidare e quale rotolo esplorare (dopo G3, come da procedura).
- Se addestrare un modello proprio (solo se il metro mostra che il modello è il collo di bottiglia *e* il costo è sostenibile).

## Aggiornamenti

- 2026-09-06 — documento creato dopo E00 ed E01, su richiesta di Matteo di rendere esplicito che la scelta è rinviata e con quale regola verrà presa.
