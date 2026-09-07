# Secondo parere indipendente di Codex — "dove investire le energie" (7 settembre 2026)

**Tipo:** parere in cieco, sola lettura, richiesto da Matteo prima della decisione ([regola](../decisions/2026-09-06-dove-investire.md)).
**Canale:** plugin `codex@openai-codex` 1.0.6, comando `task` del runtime (`sandbox: read-only`, nessun `--write`, nessun accesso di rete), modello `gpt-6-astra` ed effort `high` passati esplicitamente al lancio; Codex ha dichiarato "GPT-6" e di non vedere l'effort. Lancio 11:06:49 UTC, durata 6 min 10 s (job `task-mtr4yhac-ijxtze`, sessione Codex `01a07b8c-c94b-7f42-9eb4-483d464b5462`).
**Cosa ha ricevuto:** l'elenco dei 14 file da leggere (AGENTS, README, roadmap, documento di decisione, [nota di intake](2026-09-07-intake-dove-investire.md) con le fonti ufficiali, scheda e manifest E02, piano E02 §2/§5/§11, docs/07, 03, 06, 05, 08, `configs/e02/baseline.json`) e la richiesta di una proposta motivata in otto sezioni. **Non** ha visto la proposta di Claude, scritta dopo.
**Come è stato usato:** confrontato con la proposta di Claude in sessione; accordi e disaccordi sono riassunti nella sezione "Decisione" del documento di decisione. È un parere, non una decisione.

Il testo che segue è l'output di Codex, riportato integralmente. Unica modifica: tre collegamenti con percorso assoluto locale resi relativi.

---

**Investirei in una diagnosi controllata dell’inferenza a pesi fissi: distinguere l’effetto della profondità da quello del modello scelto.** Prima userei le predizioni già conservate, poi un piccolo confronto Z × seed. Non avvierei ancora training, segmentazione o ranking. È una proposta: la decisione resta a Matteo.

**1. Lettura dei numeri di E02**

Uso **L0** per le fonti ufficiali riportate nei documenti, **L1** per risultati esterni, **L2** per ispezioni, **L3** per misure del team. Le mie interpretazioni sono indicate come **inferenze**. Un futuro confronto controllato può produrre L4; la verifica della configurazione congelata su dati esclusi dalle scelte, L5.

La **F1** combina precisione — quanti pixel segnalati sono corretti — e richiamo — quanti pixel d’inchiostro vengono recuperati. L’**AUROC** misura quanto il modello assegna punteggi maggiori all’inchiostro rispetto allo sfondo, senza scegliere una soglia. Un **seed** determina le scelte casuali dell’addestramento: qui identifica due modelli già addestrati, non due ripetizioni casuali dell’inferenza.

Questi sono i confronti L3 più utili, tutti alla stessa soglia congelata, 91:

| Segmento | Seed | F1 training | F1 sviluppo | AUROC sviluppo |
|---|---:|---:|---:|---:|
| w016 | 42 | 0,938 | 0,526 | 0,774 |
| w016 | 43 | 0,935 | 0,748 | 0,936 |
| 0814 | 42 | 0,975 | 0,748 | 0,874 |
| 0814 | 43 | 0,970 | 0,740 | 0,863 |

**Il fenomeno misurato è una perdita sui pixel esclusi dalla supervisione, non una ripartizione delle perdite fra stadi.** Con seed 42, il divario di F1 è circa 0,412 su w016 e 0,227 su 0814. Non possiamo attribuirlo interamente né al modello né alla geometria. La regola del documento di decisione non è quindi ancora soddisfatta nella sua parte “misurare stadio per stadio”. [Manifest E02](2026-09-07-e02-r01-manifest.json)

La lettura per stadio è questa:

- **Superficie e segmentazione**, cioè ricostruire quale foglio seguire nel volume: E02 non le varia. L0 identifica problemi importanti di geometria e annotazione della superficie; nessuna misura del team ne quantifica il contributo agli errori osservati. **Inferenza:** non possiamo chiamarle né responsabili né assolte.
- **Rendering e profondità Z**, cioè trasformare la superficie in un volume di sezioni da presentare al modello: input, orientamento e preparazione sono controllati, ma non è stata misurata una risposta alle variazioni Z. L0 segnala sensibilità agli spostamenti. Tuttavia, ±2 sezioni è proprio l’intervallo già variato durante l’addestramento: un test lì misura robustezza locale, non tutti i possibili errori di superficie.
- **Modello a pesi fissi**, senza nuovo addestramento: è lo stadio con il più forte effetto direttamente osservato cambiando una componente. A input identico, seed 43 guadagna **0,222 di F1 e 0,162 di AUROC su w016**, mentre su 0814 perde circa 0,008 e 0,012. Il vantaggio su w016 appare in entrambe le regioni: F1 0,567→0,798 e 0,492→0,708. **Inferenza:** l’input contiene segnale recuperabile che il seed 42 sfrutta peggio; non segue che tutta la perdita dipenda dal modello.
- **Modello con training**, cioè aggiornamento dei pesi tramite esempi: nessuna prova E02 misura il beneficio di riaddestrare. L0 indica questa direzione come aperta, ma non dimostra che convenga al team.
- **Ranking e verifica**, cioè ordinare le zone da esaminare e controllarle umanamente: E02 misura pixel, non lettere leggibili né tempo risparmiato. Lo sviluppo copre complessivamente **0,31 cm²**, meno di una sola finestra ScrollScout da 1 cm². Non basta per una valutazione convincente del ranking a quella scala.
- **Il metro:** funziona per confronti intra-segmento, ma non è una verifica su rotoli sconosciuti al modello. I pixel sono esclusi dalla supervisione; erano però casi di validazione durante l’addestramento ufficiale. Non equivalgono a dati mai consultati nell’intero sviluppo dei modelli.

Due dettagli impediscono letture troppo semplici degli strati di distanza:

1. Su 0814, l’AUROC quasi perfetta entro 64 pixel riguarda appena **60 positivi**; a soglia 91 la F1 è circa **0,24**. Non è un’isola di recupero quasi perfetto dell’inchiostro.
2. Su w016, seed 43 migliora molto il recupero ma nello strato senza inchiostro oltre 256 pixel produce **800 falsi positivi contro 327**, su 1.576 pixel. Il miglioramento complessivo non elimina tutti i peggioramenti locali.

La sola soglia, invece, lascia poco margine: sul seed 42 passare da 91 alla migliore soglia per segmento aggiunge circa **0,005 di F1**. **Inferenza:** una semplice ricalibrazione globale dei punteggi non spiega il grande divario osservato.

**La mappa iniziale era incompleta; l’intake la amplia utilmente.** Aggiungerei esplicitamente, come dimensioni trasversali, la qualità/allineamento delle annotazioni e la trasferibilità delle conclusioni da `ink_9um` al modello principale a 2,4 µm. Non manca, nei materiali letti, un altro stadio chiaramente prioritario. L’assenza di una voce nel catalogo non dimostra comunque l’assenza di lavoro pubblico. [Intake, §§1–6](2026-09-07-intake-dove-investire.md)

**2. Proposta**

Propongo questa combinazione ordinata:

1. **Controllo senza nuova inferenza:** media dei punteggi dei seed 42 e 43 già conservati.
2. **E03:** confronto della profondità sugli stessi due seed, per separare un effetto Z ripetibile da un vantaggio specifico del modello.
3. **E04, solo se serve:** confronto limitato con uno step precedente di addestramento; niente ricerca su tutti i 14 checkpoint.

Un **ensemble** è una combinazione di predizioni, qui una media a pesi uguali. Non sappiamo ancora se la media dei seed migliori: le metriche aggregate non consentono di ricostruirne il risultato.

La motivazione numerica è che il cambio di modello recupera già circa 0,22 di F1 su w016, mentre la perdita recuperabile intervenendo su Z è ancora sconosciuta. La diagnostica serve a misurare quest’ultima con poche inferenze e con un’alternativa concreta a pari costo.

**Non sceglierei oggi “il rendering è il collo di bottiglia”.** Sceglierei di risolvere questa incertezza prima di impegnare settimane. È coerente con gli Open Problems 7 e 12, che chiedono proprio di capire quale componente limiti il recupero. [Regola di decisione](../decisions/2026-09-06-dove-investire.md)

**3. Prova minima di E03**

**Domanda:** una combinazione fissa di due finestre Z migliora il recupero su entrambi i modelli, e vale più di spendere lo stesso calcolo sui due seed?

**Dati e impostazioni.** Solo `pherc0139-w016` e `pherc0814-46527`, con input, annotazioni e maschere congelati in E02. Valutazione sui pixel `held`, esclusi dalla supervisione; `train` soltanto come controllo. Stesse versioni, direzione e parametri di E02. Seed **42 e 43**, entrambi allo step **75000**, cioè allo stesso punto dell’addestramento. Nessun accesso ai dati di verifica di w029.

| Configurazione | Finestre, estremi inclusi | Nuove inferenze |
|---|---|---:|
| Centrale, già disponibile | 2–18 | 0 |
| Spostamento −2 | 0–16 | 4: due segmenti × due seed |
| Spostamento +2 | 4–20 | 4: due segmenti × due seed |

Sono **otto nuove inferenze**. Da questi output si costruiscono due tipi di media:

- **Media Z per ciascun seed:** metà predizione −2 e metà +2.
- **Media dei seed al centro:** metà seed 42 e metà seed 43, usando gli output E02.

Entrambe richiedono due passaggi del modello per segmento nell’uso futuro. Le medie vanno calcolate sui TIFF grezzi conservando i mezzi punti, senza riscalare o arrotondare prima della valutazione. Il codice di valutazione delle medie richiede un piccolo adattamento separato; E02 resta congelato.

**Metrica primaria:** AUROC per segmento, mantenendo la scelta di E02. Per ogni combinazione segmento/seed si calcola:

> differenza = AUROC della media Z − AUROC della finestra centrale dello stesso seed.

L’indicatore riassuntivo è la media delle **quattro differenze**, con uguale peso ai due segmenti e ai due seed. Restano visibili tutti e quattro i risultati.

**Criterio preregistrato proposto per approfondire Z:**

- guadagno medio di AUROC **almeno 0,02**;
- guadagno medio **almeno 0,01 per ciascun segmento e per ciascun seed**;
- nessuna delle quattro combinazioni peggiora di oltre **0,01**;
- F1 a soglia 91, mediata sui seed, non peggiora di oltre **0,01 in nessun segmento**;
- nello strato di w016 senza inchiostro, la frazione di falsi positivi non aumenta di oltre **5 punti percentuali per seed**.

Queste soglie sono **mie proposte di utilità pratica**, non livelli di significatività statistica o requisiti ufficiali.

Per preferire una media Z alla media dei seed a pari costo, richiederei inoltre, per entrambi i seed, almeno **0,01 di AUROC media aggiuntiva sui due segmenti**, senza perdere oltre 0,01 su uno dei due. Se Z supera il primo criterio ma non questo confronto, abbiamo trovato una sensibilità utile da documentare, senza dimostrare che sia il miglior investimento operativo.

**Variabilità fra seed.** Lo 0,22 osservato non è una deviazione standard e non è una soglia che ogni miglioramento debba superare. Confrontare ogni variante con il proprio seed elimina il confronto ingannevole “variante seed 43 contro baseline seed 42”. Due seed restano insufficienti per stimare la variabilità di tutti i possibili addestramenti. Ripetere l’inferenza deterministica non aggiungerebbe seed indipendenti.

**Numero di confronti.** Una sola ipotesi primaria: la media Z simmetrica migliora rispetto al centro in modo coerente. Gli otto confronti dei singoli spostamenti con il centro e le letture per strato/regione sono diagnostici: non si sceglie a posteriori la finestra vincente e non la si presenta come risultato confermato. La media dei seed è un controllo operativo aggiuntivo già dichiarato. Tutti i risultati si pubblicano; nessuna ricerca di soglie, pesi o finestre specifiche per segmento.

Non ricaverei intervalli di confidenza trattando centinaia di migliaia di pixel vicini come prove indipendenti. La conferma resta E05, dopo il congelamento della scelta.

**Costo stimato, non misurato:**

- **24–27 minuti di inferenza T4**, estrapolati dai tempi E02;
- **45–70 minuti di quota GPU**, includendo avvio e installazione; tetto proposto **90 minuti**;
- **10–16 ore umane complessive** per piano, adattamenti, controlli, lettura e rapporto;
- strumenti: estensione minima del generatore dei run, media dei TIFF, tabella delle differenze per seed/segmento e riuso delle metriche esistenti. Nessuna nuova interfaccia.

Download e preparazione prima della GPU; lanci sequenziali con controllo del risultato precedente. Non rifarei le inferenze centrali di E02.

**E04 eventuale:** un solo checkpoint precedente documentato come disponibile, per esempio step **20000**, su entrambi i seed e sulla finestra centrale. Quattro inferenze, circa 12–14 minuti netti. Sarebbe un confronto sull’effetto della durata dell’addestramento, non una ricerca del migliore fra 14 checkpoint. Lo step andrebbe fissato prima dei nuovi risultati.

**4. Rischi**

- **Trovare rumore:** ridotto con una trasformazione primaria fissa, confronti entro seed e nessuna selezione del massimo. Rimangono solo due segmenti.
- **Sovra-adattarsi allo sviluppo:** niente finestre, soglie o pesi diversi per w016 e 0814; nessuna concatenazione di tentativi suggeriti dai risultati locali. Anche un esito positivo rimane intra-segmento.
- **Scambiare robustezza locale per diagnosi completa:** ±2 è nell’intervallo di addestramento. Un esito negativo non esclude spostamenti maggiori, errori locali della superficie o cambi di foglio.
- **Sprecare quota:** riuso degli output centrali, limite di otto nuove inferenze, arresto su errori tecnici; nessun lancio duplicato o ricerca automatica di combinazioni.
- **Ottimizzare la metrica senza migliorare l’utilità:** conservare F1, falsi positivi e risultati regionali. Un’AUROC migliore non dimostra lettere più leggibili.
- **Studiare un modello meno centrale per la community:** L0 indica il modello a 2,4 µm come principale. Il contributo deve dichiarare il proprio ambito e rendere la procedura trasferibile; non assumere che i risultati `ink_9um` valgano anche lì.

**5. Alternative scartate e perché**

“Scartate” significa escluse dal prossimo investimento, non inutili in assoluto.

| Alternativa | Motivo |
|---|---|
| Nuova segmentazione, riparazione della superficie, fibre o spirale | Alto ingresso umano; E02 non misura direttamente il beneficio di cambiare geometria. Esistono già strumenti e valutazioni pubbliche pertinenti. |
| Scansione/acquisizione | Nessuna possibilità del team, nel perimetro attuale, di variare l’acquisizione. |
| Offset ampi con nuova preparazione del volume | Più complessità e necessità di verificare il riferimento geometrico delle annotazioni. Da riaprire se emerge un indizio concreto, non automaticamente dopo un test locale negativo. |
| Inversione della profondità e molte trasformazioni dell’input | L’orientamento ufficiale è documentato; manca una perdita misurata che le renda prioritarie. Aumenterebbero subito i confronti. |
| Sola calibrazione globale dei punteggi | Il margine tra F1 a 91 e migliore F1 del seed 42 è circa 0,005. Non affronta il divario principale. |
| Ricerca su tutti i checkpoint | R02 ha già pubblicato il confronto. Alto rischio di scegliere il caso fortunato sui due segmenti e contributo incrementale debole. |
| Nuovo training, pseudo-label e modelli 3D | Le pseudo-label sono annotazioni generate da un modello: possono perpetuarne gli errori. Non abbiamo ancora una diagnosi né un costo di training misurato. |
| Ranking/ScrollScout | Il riferimento disponibile è troppo piccolo alla scala delle finestre; manca una misura del tempo umano perso nell’ordinamento attuale. |
| Ampliare il metro come progetto autonomo | E02 è sufficiente per questa decisione e deriva già da R02. Nuove annotazioni indipendenti potrebbero avere valore, ma sono un altro incarico. |
| Infrastruttura cloud e accelerazione | Non risolvono la perdita di qualità osservata. Il carico minimo proposto sta ampiamente nella quota. |
| Ricerca immediata First Letters | Nessun risultato attuale riguarda un volume eleggibile o dimostra lettere leggibili. Richiederebbe E05/E06 e ulteriori competenze. |

**6. Cosa candidare a un Progress Prize**

Candiderei, **solo se produce un’informazione nuova e utilizzabile**, un contributo del tipo:

> Diagnosi riproducibile dell’interazione fra profondità e modello: quando conviene spendere due inferenze su finestre Z diverse e quando su due seed.

Il valore dovrebbe stare in risultati su dati reali, confronti a pari costo, limiti espliciti e istruzioni che consentano a un altro partecipante di prendere una decisione diversa grazie al lavoro.

L0, come riportato nell’intake, premia rilascio aperto tempestivo, uso effettivo nella community, miglioramenti quantitativi o qualitativi, correzioni di errori e informazioni concretamente utilizzabili, oltre alla documentazione. La scadenza riportata è **30 settembre 2026, 23:59 Pacific**. Un risultato negativo circoscritto può essere utile; “non migliora qui” da solo è una candidatura debole. [Intake, §2](2026-09-07-intake-dove-investire.md)

**Non candiderei come novità:**

- la riproduzione della pipeline;
- la costruzione del metro e la riscoperta del divario training/validazione;
- lo 0,22 fra seed;
- una nuova tabella dei checkpoint;
- la semplice idea di mediare finestre Z, già suggerita dal model card.

R02 ha già strumenti di valutazione, confronto dei checkpoint, audit dell’adiacenza e osservazioni sui seed; E02 ne adatta componenti e replica numeri. Va attribuito esplicitamente. Il catalogo contiene anche analisi della risoluzione, trasformazioni in inferenza e numerosi strumenti di controllo geometrico: non possiamo dichiarare il campo libero. [Registro community, R02](../06-ricerca-community.md)

Il pacchetto dovrebbe comprendere codice con attribuzioni e licenza compatibile, configurazioni, impronte degli artefatti, risultati completi, costo e una breve guida alle decisioni. Un uso documentato da parte di un esterno rafforzerebbe la candidatura; non è qualcosa che oggi possiamo dichiarare.

Per le condizioni riportate nell’intake: licenza permissiva per il codice, CC BY-NC 4.0 per dataset creati, registrazione Discord alla candidatura e riproducibilità. Non confondere il rilascio tempestivo richiesto ai contributi tecnici con la riservatezza prima dell’annuncio dei premi di scoperta.

**7. La condizione che mi farebbe cambiare idea**

- **Z supera i criteri su entrambi i seed e batte la media dei seed a pari costo:** investirei in profondità/rendering in E04.
- **Z non supera i criteri, mentre la media dei seed offre un beneficio concreto:** darei priorità alla combinazione dei modelli e a un solo confronto con uno step precedente.
- **Una finestra aiuta soltanto seed 42 su w016:** lo leggerei come effetto specifico modello–segmento. Non giustifica una campagna sul rendering.
- **Né Z né la media aiutano, e uno step precedente non migliora:** interromperei l’ottimizzazione di `ink_9um` su questi due segmenti. Riaprirei la scelta verso qualità delle annotazioni o valutazione del modello principale a 2,4 µm, dopo una verifica mirata di compatibilità e costo.

Anche un miglioramento locale di F1 pari a 0,22 non basterebbe, da solo, a scegliere un filone se peggiorasse l’altro segmento o i controlli negativi.

**8. Dichiarazione finale**

Sono **Codex, basato su GPT-6**. L’identificativo preciso della variante e il parametro **effort**, cioè il livello di elaborazione configurato per questa sessione, non mi sono esposti in modo verificabile. Non li deduco dalla configurazione delle precedenti revisioni E02.

Ho letto, nell’ordine richiesto:

1. `AGENTS.md`
2. `README.md`
3. `docs/roadmap.md`
4. `docs/decisions/2026-09-06-dove-investire.md`
5. `docs/reports/2026-09-07-intake-dove-investire.md`
6. `docs/reports/2026-09-07-e02-r01.md`
7. `docs/reports/2026-09-07-e02-r01-manifest.json`: sezioni richieste e `metrics_local` dei sei run `infer-*`. Gli strati e le regioni sono presenti per gli insiemi di sviluppo; per `train` non sono riportati.
8. `docs/plans/2026-09-06-e02-costruire-il-metro.md`: §§2, 5 e 11.
9. `docs/07-procedura-operativa.md`
10. `docs/03-metodo-sperimentale.md`
11. `docs/06-ricerca-community.md`
12. `docs/05-scrollscout-e-piano-di-verifica.md`
13. `docs/08-dossier-input-e00.md`, integralmente.
14. `configs/e02/baseline.json`

Ho eseguito soltanto letture di file e selezione delle sezioni JSON. Nessuna modifica, rete, esecuzione scientifica, lettura di immagini o accesso ai pixel sigillati; nessuna ricerca della proposta dell’altro agente o di memoria precedente.

I documenti autorizzati contengono anche valori aggregati esterni di R02 relativi a w029: li ho incontrati nel testo, ma **non li ho usati per scegliere varianti o criteri**.

Sono inferenze mie: la priorità proposta, l’interpretazione causale limitata del cambio di seed, il ridotto interesse della sola calibrazione, la valutazione delle alternative e del potenziale premio. Sono proposte mie le soglie, i confronti e gli arresti; sono estrapolazioni i costi GPU e stime i tempi umani. Non ho misurato il risultato di alcuna media o variante, né verificato direttamente il codice esterno o l’assenza di contributi equivalenti oltre alle fonti riportate nei file.

Codex session ID: 01a07b8c-c94b-7f42-9eb4-483d464b5462
Resume in Codex: codex resume 01a07b8c-c94b-7f42-9eb4-483d464b5462
