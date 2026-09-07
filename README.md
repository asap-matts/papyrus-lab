# PapyrusLab

Progetto di Matteo e del suo socio per contribuire alla Vesuvius Challenge e costruire un risultato verificabile candidabile a un premio.

**Stato:** **E00 ed E01 superati il 6 settembre 2026** — controllo noto della pipeline ufficiale `ink_9um` su w035 eseguito su Kaggle via API (AUROC 0,999 contro la label ufficiale, orientamento verificato, due seed concordanti; [scheda E00](docs/reports/2026-09-06-e00-r01.md)) e **riprodotto dal socio** dal solo repository, con account e agente diversi, con TIFF identici bit per bit ([scheda E01](docs/reports/2026-09-06-e01-r01.md)). Sono controlli di funzionamento su un segmento del training set: nessuna evidenza di generalizzazione, nessuna scoperta. **E02-R01 eseguito il 7 settembre 2026** ([scheda](docs/reports/2026-09-07-e02-r01.md)): il metro è costruito — 721.550 pixel a label ufficiale mai usati per il training, su tre segmenti di tre rotoli, con adiacenza al training misurata; la baseline ufficiale, che vale 0,99 di F1 sui pixel studiati, scende a 0,53–0,75 sui pixel nuovi di sviluppo, numeri identici a quelli pubblicati da un altro partecipante; il segmento di verifica resta sigillato fino a E05. È un metro intra-segmento, non una prova di generalizzazione fra rotoli. Gate G3 raggiunto (7 settembre 2026). **Decisione presa il 7 settembre 2026** ([documento](docs/decisions/2026-09-06-dove-investire.md)): E03 misura la **tolleranza del modello all'offset Z**, cioè quanto errore nella posizione stimata della superficie l'inchiostro sopravvive, sui pixel nuovi di sviluppo, con offset fino a ±5 slice in due tappe; scelta presa con le fonti ufficiali rilette ([intake](docs/reports/2026-09-07-intake-dove-investire.md)) e un secondo parere di Codex in cieco. **E03-R01 completato il 7 settembre 2026** ([scheda](docs/reports/2026-09-07-e03-r01.md)): 24 inferenze GPU (128 minuti) su 2 segmenti × 2 seed × 7 offset, matrice validata e ricalcolata in cieco dal socio; sui pixel held-out il modello non è piatto entro ±2 slice (6 punti su 8 fuori dalla banda di 0,02), la perdita massima rispetto alla finestra ufficiale arriva a 0,111 di AUROC, e il verso in cui migliora cambia da un segmento all'altro, così che la media fra i segmenti lo nasconde; sui pixel di training dello stesso segmento la perdita massima è 0,027. Risultato su due segmenti, con errore di offset uniforme: non dice nulla su altri rotoli né su una finestra migliore. Il seguito lo decide Matteo. Nome di lavoro provvisorio.

L'amico fisico di Matteo lavora indipendentemente: condivide informazioni e strumenti, ma non fa parte del team. ScrollScout è una risorsa esterna da valutare, non il progetto del team né una dipendenza già scelta.

## Da dove iniziare

1. [Capire il processo con parole semplici](docs/01-capire-il-processo.md).
2. [Strumenti e setup Windows / Mac / cloud](docs/02-strumenti-e-setup.md).
3. [Proposta di metodo sperimentale](docs/03-metodo-sperimentale.md).
4. [Fasi, stato e prossime decisioni](docs/roadmap.md).
5. [Fonti, premi e rettifiche](docs/fonti-e-verifiche.md).
6. [ScrollScout e piano di verifica](docs/05-scrollscout-e-piano-di-verifica.md).
7. [Ricerca sulla community e registro dei contributi](docs/06-ricerca-community.md).
8. [Procedura operativa canonica](docs/07-procedura-operativa.md).
9. [Dossier tecnico dell'input candidato E00](docs/08-dossier-input-e00.md).
10. [Dove investire le energie: regola, mappa delle opzioni, numeri di E02 e decisione](docs/decisions/2026-09-06-dove-investire.md) — decisa il 7 settembre 2026: tolleranza all'offset Z (E03); con la [nota di intake](docs/reports/2026-09-07-intake-dove-investire.md) sulle fonti ufficiali.

Per la prossima attività pratica: [prima sessione guidata](docs/04-prima-sessione.md), con un esempio ufficiale da esplorare nel browser. Disponibili anche il PC fisso di Matteo (i7-12700K, 32 GB, GTX 1060 6 GB, 681 GB liberi, WSL2; inventario rilevato) e il Mac M3 Pro del socio; la prima inferenza GPU è su Kaggle, il fisso richiede un preflight dedicato.

La prima meta — riprodurre una procedura nota e comprenderne i limiti — è raggiunta con E00 ed E01. L'obiettivo è capire l'intero processo, misurare dove si perde di più e concentrare lì il miglioramento, per un contributo utile alla community che possa meritare un premio; lo stadio su cui investire è stato scelto il 7 settembre 2026 con i numeri di E02 ([regola e decisione](docs/decisions/2026-09-06-dove-investire.md)); la candidatura a un Progress Prize (scadenza corrente 30 settembre 2026) si decide ora che l'esito di E03 è revisionato, First Letters resta la meta lunga. Vincere è l'obiettivo del progetto, non un esito garantito dal funzionamento del software.

Account Kaggle e telefono verificati. Il [preflight dell'ambiente Kaggle](docs/reports/2026-09-05-kaggle-preflight.md) ha confermato PyTorch e due Tesla T4; la sessione è stata fermata e nessuna inferenza Vesuvius è stata ancora eseguita. La [revisione del 6 settembre 2026](docs/reports/2026-09-06-revisione-procedura-e00.md) ha verificato il dossier E00 su fonti primarie e fissato le decisioni per il piano. La ricerca comprende contributi pubblici di altri partecipanti oltre agli aggiornamenti di Francesco: prima selezione di 11 risorse documentata, nessuna nuova pipeline replicata.

## Organizzazione

GitHub conserva documentazione e, in seguito, codice, configurazioni e rapporti piccoli. Scansioni, pesi dei modelli e risultati voluminosi restano fuori da Git: per riprodurli conserveremo provenienza, versione e impronte dei file.

Il repository parte privato. La licenza del futuro codice e l'eventuale pubblicazione saranno decise prima di distribuire il lavoro, tenendo conto delle licenze delle risorse e delle condizioni del premio. Non è un progetto ufficiale della Vesuvius Challenge.

Le istruzioni comuni per gli agenti sono in [AGENTS.md](AGENTS.md). Per registrare il lavoro useremo la [scheda esperimento](docs/templates/esperimento.md) e la [scheda di revisione](docs/templates/revisione.md).
