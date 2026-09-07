# Ricerca sui contributi della community

Avviata il 5 settembre 2026 su richiesta di Matteo. È parte del lavoro di PapyrusLab: cercare, valutare e adattare contributi pubblici degli altri partecipanti, insieme agli aggiornamenti di Francesco. Questo registro contiene una prima selezione mirata, non una ricognizione esaustiva né risultati replicati.

## Come useremo la ricerca

Prima di fissare un esperimento, controllare le novità pertinenti su sito ufficiale, repository, release, issue e PR, modelli Hugging Face e resoconti degli autori. I punti di partenza sono [Community Projects](https://scrollprize.org/community_projects), [Open Problems](https://scrollprize.org/2026_open_problems) e [premi](https://scrollprize.org/prizes). Le discussioni Discord possono offrire contesto quando disponibili, ma in questa ricognizione non sono state consultate. Questa è una procedura durante le sessioni di lavoro; non è stato configurato un monitoraggio automatico.

Per ogni idea promettente registrare:

- Fonte primaria, autore, data di consultazione e revisione esatta; distinguere vecchi risultati e aggiornamenti.
- Problema risolto e risultato dichiarato; cosa è stato effettivamente ispezionato o replicato da noi.
- Dati, riferimenti, regioni escluse dal training, hardware, dipendenze e licenze di codice, pesi e dati separatamente.
- Utilità per il prossimo esperimento, costo d'integrazione e una piccola prova capace anche di smentire il beneficio.
- Decisione motivata: approfondire, provare, adottare, rinviare o scartare. Un bug già corretto a monte va riconosciuto come tale.

Gli aggiornamenti di Francesco seguiranno lo stesso metodo. Consolidare informazioni tecniche pertinenti e attribuite; conservare il collegamento alle pubblicazioni senza riversare conversazioni private in Git. Il riuso di codice avverrà dopo aver letto la licenza del componente, mantenendo le attribuzioni richieste.

## Prima selezione e prossime prove

Le revisioni della tabella successiva sono state risolte attraverso l'API GitHub. Qui abbiamo letto documentazione pubblica e, per ScrollScout, ispezionato anche parte del codice di scoring. Nessuna delle pipeline elencate è stata eseguita in questa ricognizione. La presenza nel catalogo ufficiale è un segnale di pertinenza, non una nostra certificazione.

| ID | Risorsa e contributo documentato | Utilità proposta e prova minima |
|---|---|---|
| R01 | [ScrollPrize/villa](https://github.com/ScrollPrize/villa): base ufficiale, con VC3D e `vesuvius`. | Priorità immediata: fissare ambiente e modello del controllo E00 usando il tutorial corrente. |
| R02 | [khj1222/vesuvius-challenge](https://github.com/khj1222/vesuvius-challenge): strumenti di valutazione che riservano intere regioni annotate, confrontano checkpoint e registrano risultati per regione; scorecard dei checkpoint `ink_9um` sulle tre maschere ufficiali (docs/14) e audit dell'adiacenza held-out/training (docs/17). | **Adottato in E02 in forma adattata** (licenza MIT, revisione `13920ba`): sweep di soglia dagli istogrammi e strati di distanza in `scripts/e02_metrics.py`; i numeri di docs/14 e docs/17 usati come replica esterna del metro ([scheda E02](reports/2026-09-07-e02-r01.md)): held-out identici alla terza cifra su 0814 e w016; geometria identica su 0814 e w029, diversa su w016 (differenza nel dataset o nella copia di R02, non nel calcolo). La variabilità fra seed misurata dall'autore (0,22 di F1 su w016) è stata osservata anche da noi. DRD e pseudo-F-measure non adottati. |
| R03 | [Schurkai/vesuvius-catalog](https://github.com/Schurkai/vesuvius-catalog): catalogo interrogabile e accesso a livelli OME-Zarr. | Priorità alta per scegliere input: confrontare URL, risoluzione e disponibilità di un campione con il catalogo ufficiale; valutare l'utilità rispetto a `vesuvius` già necessario. |
| R04 | [Bullo27/scroll-data-audit](https://github.com/Bullo27/scroll-data-audit): confronta descrizioni del catalogo, array e scale; include controlli campionati delle piramidi. | Prima di inferire: verificare dimensioni, assi e scala del nostro input. Distinguere errore dei dati, errore di metadati e problema transitorio di rete. |
| R05 | [TAUIL-Abd-Elilah/vesuvius-repro](https://github.com/TAUIL-Abd-Elilah/vesuvius-repro): riproduzione regionale di predizioni di superficie m7; documenta il ruolo delle trasformazioni in inferenza (TTA). | Per il protocollo: registrare anche TTA e impostazioni di fusione. La somiglianza con un output pubblicato prova riproducibilità su quella regione, non correttezza della superficie né lettura dell'inchiostro. Il README corregge una precedente conclusione negativa e riferisce una correzione della provenienza a monte. |
| R06 | [joe-carr-data/windcheck](https://github.com/joe-carr-data/windcheck): trova autointersezioni nelle superfici tifxyz e documenta derivati ripuliti. | Per E03: primo confronto in modalità solo rapporto su una mesh. L'autore precisa che il beneficio sull'inchiostro non è ancora misurato; anche una mesh senza autointersezioni può seguire il foglio sbagliato. |
| R07 | [spencerdavis-tx/vesuvius-automesh](https://github.com/spencerdavis-tx/vesuvius-automesh): crescita automatica con controlli di qualità, documentata su Scroll 3 usando CPU di un Mac Apple Silicon. | Interessante per il socio: misurare area utile, errori e tempo su un piccolo caso. La prova pubblicata non dimostra prestazioni sul suo M3 Pro o sui rotoli eleggibili; usa predizioni di superficie già disponibili. |
| R08 | [Hob3rMallow/scrollfiesta_public](https://github.com/Hob3rMallow/scrollfiesta_public): costruzione di mesh e srotolamento a partire da predizioni di superficie; percorso CPU e accelerazione opzionale. | Alternativa geometrica per E03, dopo la baseline. Valutare continuità e distorsione di un piccolo risultato, formati e costo della compilazione. Il README distingue la geometria dalla produzione/riparazione delle predizioni in ingresso. |
| R09 | [mojomast/vesuvius-autoresearch](https://github.com/mojomast/vesuvius-autoresearch): gestione di esperimenti, provenienza e criteri per accettare risultati; demo con dati sintetici. | Consultare per registri e confronti a budget fissato. Valutare dopo E00–E02: una demo sintetica funzionante non prova miglioramenti sui papiri, e automazione non elimina la necessità di controlli indipendenti. |
| R10 | [younader/Vesuvius-Grandprize-Winner](https://github.com/younader/Vesuvius-Grandprize-Winner): soluzione del premio 2023, con iterazioni di pulizia/espansione delle etichette e più architetture. | Riferimento storico per il metodo. Il README dichiara il repository archiviato e rimanda a villa per lo sviluppo: non prenderlo come setup attuale predefinito. |
| R11 | [FrankTheRope/scrollscout](https://github.com/FrankTheRope/scrollscout): selezione delle finestre e confronto delle predizioni. | Prove E04 e limiti nella [nota dedicata](05-scrollscout-e-piano-di-verifica.md). La priorità relativa va confrontata con accesso dati, geometria e validazione. |
| R12 | [nerln/vesuvius-ladder](https://github.com/nerln/vesuvius-ladder) e [villa #1547](https://github.com/ScrollPrize/villa/issues/1547) (2026-08-20): i segmenti pubblici PHerc0139 w045 e w046 tracciano lo stesso foglio (81,5 % di vertici identici). | Consultato per E02 (L1): w046 escluso dai candidati "estranei al training" perché fisicamente coincide con w045, che è nel training. Non replicato. Da rileggere se si sceglieranno segmenti di PHerc0139 in E06. |

## Revisioni consultate

Snapshot del 5 settembre 2026. Il commit identifica lo stato da ritrovare per la revisione; non indica una dipendenza già installata o approvata. Prima di una prova fissare anche eventuali sottocomponenti e checkpoint. I README possono descrivere risultati prodotti con commit precedenti: rintracciare il manifest dell'esperimento.

| ID | Commit GitHub |
|---|---|
| R01 | `23adee047dea06526151d3a152a7d85de8da478b` |
| R02 | `13920bad47e2bee4f2a21e748ae3f338093d64a4` |
| R03 | `f59f0c1121260e02ed4ed6eb34532a7f92e6ac01` |
| R04 | `d94bcdbbc696df3896e52acc27453c4e29617926` |
| R05 | `6b757b9e6f9efe2d0f808671cad89c5ad95882a3` |
| R06 | `a615e7485d5db7295f269d2a6dca0788157aaab7` |
| R07 | `09482fa6acfd4d93235c40c3a90c408e614c06f4` |
| R08 | `5d957e9c21529580cc43eda8bf980fef02486b36` |
| R09 | `0cb1d4fe0a8820ffdb8146b0d3086a64a3493e29` |
| R10 | `0efba1b508a334dbce048326ff0ecf88e75d929c` |
| R11 | `29656e3b8455572dded5ed4a13ddfa974dac1a5e` |
| R12 | issue villa #1547 letta il 6 settembre 2026 (aperta); repository non fissato a un commit |

Le licenze complete non sono state revisionate per l'integrazione. In particolare GitHub restituisce `NOASSERTION` per R04 e R08: è un limite della classificazione automatica, non una conclusione sull'assenza o sul contenuto della licenza.

## Decisioni per il prossimo ciclo

1. Preparare E00 con un campione già renderizzato e il modello ufficiale. Il fisso e VC3D non sono prerequisiti della prova Kaggle.
2. Usare R02–R05 per affinare il registro degli input e la futura verifica indipendente. La prima inferenza serve a capire e verificare la procedura.
3. Confrontare poi il costo dei problemi osservati: input errato, superficie difettosa, modello poco sensibile o ranking poco utile. Approfondire R06–R11 in funzione dei risultati, senza adottare tutta la lista.
4. Prima di proporre un nuovo strumento da candidare a un Progress Prize, cercare soluzioni equivalenti e correzioni già integrate. La candidatura dovrà dimostrare il vantaggio rispetto agli strumenti pertinenti, con dati reali e misure ripetibili.

**Aggiornamento del 7 settembre 2026 (E02).** R02 è la prima risorsa della lista adottata in forma adattata e usata come replica esterna; R04 è stato consultato per il metodo di verifica dei metadati (non adottato: i controlli necessari sono nel nostro script di inventario). Due issue di villa registrate: #1547 (duplicato w045/w046, R12) e #1231 (le maschere di validazione mancano sui segmenti pubblicati; #1638 di R02 chiusa da pmh47 con la lettura "intra-segmento" che il nostro metro adotta). Lezione operativa da R02 docs/13 confermata: un download che supera il controllo di dimensione può contenere chunk illeggibili; la verifica va fatta decomprimendo.

Da approfondire dopo questa prima selezione: resoconti della gara Surface Detection collegati da Open Problems, metodi volumetrici di ink detection e analisi della risoluzione presenti nel catalogo ufficiale. Le condizioni del premio corrente hanno precedenza sulle descrizioni storiche nei repository.
