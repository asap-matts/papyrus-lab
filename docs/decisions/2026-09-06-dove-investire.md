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

La scelta dello stadio si prende nella prossima sessione, con questi numeri, secondo la regola sopra.

## Aggiornamenti

- 2026-09-06 — documento creato dopo E00 ed E01, su richiesta di Matteo di rendere esplicito che la scelta è rinviata e con quale regola verrà presa.
- 2026-09-07 — aggiunti i numeri di E02 (gate G3 raggiunto); la scelta resta da prendere, con i numeri, nella sessione successiva.
