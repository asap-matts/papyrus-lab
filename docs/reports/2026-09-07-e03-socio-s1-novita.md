# E03 socio S1 — verifica indipendente di novità

**Data della ricerca:** 7 settembre 2026  
**Esecutore:** Codex sul Mac del socio  
**Domanda:** è già pubblicata una misura della perdita dei modelli di *ink detection* di villa, in particolare `ink_9um`, al variare dell'offset Z, valutata con AUROC su etichette tenute fuori dall'addestramento?

## Dove ho cercato

Ho eseguito le sei query GitHub Code Search prescritte:

```text
layer-start repo:ScrollPrize/villa
z_window repo:ScrollPrize/villa
layer_start repo:ScrollPrize/villa
"z offset" ink detection vesuvius
"layer-start" vesuvius ink
"z window" ink_9um
```

Ho eseguito le cinque query GitHub Issues/PR prescritte:

```text
repo:ScrollPrize/villa z offset ink
repo:ScrollPrize/villa layer-start
repo:ScrollPrize/villa validation ink_9um
ink_9um z window
vesuvius ink detection z offset sensitivity
```

Ho inoltre eseguito la query repository `vesuvius ink detection evaluation`, letto la model card `ink_9um`, interrogato le discussioni Hugging Face, controllato le pagine ufficiali `community_projects`, `2026_open_problems` e `tutorial5`, e cercato `z offset` e `layer-start` nei 12 repository GitHub estratti dal registro community. I comandi, i conteggi e gli URL sono registrati nel JSON associato; le risposte testuali originali sono in `runs/E03-SOCIO/s1/` e non sono versionate.

La ricerca è limitata a fonti pubbliche indicizzate, in inglese, raggiungibili il 7 settembre 2026. Non ho consultato Discord, conversazioni private, repository non pubblici o materiale non indicizzato.

## Cosa ho trovato

| Fonte | Data o revisione verificata | Cosa misura | Confrontabile con una curva AUROC(offset) su pixel held-out? |
|---|---|---|---|
| [Model card ufficiale `ink_9um`](https://huggingface.co/scrollprize/ink_9um/blob/main/README.md) | accesso 2026-09-07 | Dichiara che il modello può essere sensibile all'offset Z, che il jitter rende tollerabili piccoli offset e che offset maggiori possono compromettere la risposta; suggerisce anche la media di finestre vicine. Non pubblica una curva o valori numerici. | **parziale** — formula l'ipotesi e le contromisure, ma non misura AUROC per offset. |
| [Tutorial 5 ufficiale](https://scrollprize.org/tutorial5) | accesso 2026-09-07 | Consiglia di spostare `--layer-start`/`--layer-end` o mediare finestre quando il modello vede una profondità diversa da quella attesa. | **parziale** — indicazione operativa senza etichette, protocollo comparativo o numeri. |
| [`inkalign`](https://github.com/hilalitvak/inkalign/tree/c11177a645148b13c29e26bedbd443fc61d7505d) | revisione `c11177a645148b13c29e26bedbd443fc61d7505d`; README: sviluppo agosto 2026, run dichiarato 25 agosto 2026 | Esegue inferenza `ink_9um` su più finestre e orientamenti; sul ROI w025 pubblica come migliore l'offset −4 usando un punteggio senza etichette basato sulla struttura periodica dei tratti (`line_score`). | **parziale** — è uno sweep Z reale dello stesso modello, ma non usa etichette held-out né AUROC e cerca la finestra migliore su un singolo ROI. |
| [`measure-before-you-hunt`, Investigation B](https://github.com/flummoxjr/measure-before-you-hunt/blob/e508085cdfe51e9f65018d2ce3e71119f142d304/hunt/depth_offset_plan.md) | revisione `e508085cdfe51e9f65018d2ce3e71119f142d304`; documento datato 2026-08-17 | Pubblica una curva AUC per offset da −6 a +5 del checkpoint `ink_9um` seed 42 sul controllo w035, inclusi AUC forward/reverse e perdita rispetto allo zero. | **parziale** — è la misura numerica più vicina, ma w035 è un segmento di training del modello e quindi non valuta pixel tenuti fuori dall'addestramento; usa un solo seed e un solo segmento. |

La ricerca ha trovato anche [`gp13-ink-detectability`](https://github.com/flummoxjr/gp13-ink-detectability/blob/e08d88fec673f2885a8d13e8efbe76cab0b95d52/hunt/depth_offset_plan.md). Alla revisione `e08d88fec673f2885a8d13e8efbe76cab0b95d52` il file `hunt/depth_offset_plan.md` ha lo stesso SHA-256 (`532a70d409d2a148a7cbaf3ed1539ffbbbff0a56999b13283e2bba3281d860ef`) del file in `measure-before-you-hunt`: è quindi una copia dello stesso risultato, non una seconda misura indipendente.

Gli altri risultati di GitHub Code Search riguardano opzioni di inferenza, configurazioni, test, trasferimento di etichette o termini omonimi; i risultati Issues/PR riguardano in prevalenza rendering, metadati, streaming e validazione. Nessuno di quelli raggiunti pubblica la combinazione richiesta: curva AUROC(offset), modello `ink_9um` e pixel con etichette tenuti fuori dall'addestramento.

## Verdetto

**trovato lavoro parziale**

La confidenza è moderata: ho trovato sia uno sweep Z del modello senza ground truth sia una curva AUC(offset) su un controllo appartenente al training, ma non una curva equivalente su pixel held-out nelle fonti consultate. La conclusione è circoscritta alle query e alle fonti sopra elencate; non afferma che un lavoro equivalente non esista.

## Ambiguità e ostacoli

- GitHub Code Search ha restituito `HTTP 403` per 10 query del registro community al primo tentativo. Il secondo e ultimo tentativo è riuscito per tutte; l'ostacolo non lascia query irrisolte.
- L'apertura automatica di quattro pagine GitHub già individuate ha restituito `Cache miss`. Ho recuperato gli stessi file tramite gli URL raw alle revisioni già restituite dalle query, senza ampliare le query.
- `Hob3rMallow/scrollfiesta_public` ha restituito 2060 occorrenze per `z offset` e `ScrollPrize/villa` 622: la stringa non era abbastanza selettiva. Ho considerato pertinenti solo i risultati con un legame esplicito fra finestra Z e modello di ink detection.
- La pagina ufficiale e la model card usano formulazioni qualitative; le classifico come “parziale”, non come misura.
- Per “held-out” ho richiesto che i pixel valutati non fossero stati usati per addestrare il checkpoint. Una maschera o un ritaglio distinto dentro un segmento di training non soddisfa da solo questa condizione.

