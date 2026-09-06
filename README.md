# PapyrusLab

Progetto di Matteo e del suo socio per contribuire alla Vesuvius Challenge e costruire un risultato verificabile candidabile a un premio.

**Stato:** **E00 superato il 6 settembre 2026** — controllo noto della pipeline ufficiale `ink_9um` su w035, eseguito su Kaggle via API, AUROC 0,999 contro la label ufficiale con orientamento verificato, due seed concordanti ([scheda](docs/reports/2026-09-06-e00-r01.md)). È un controllo di funzionamento su un segmento del training set: nessuna evidenza di generalizzazione, nessuna scoperta. Prossimo: E01 (ripetizione del socio). Nome di lavoro provvisorio.

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

Per la prossima attività pratica: [prima sessione guidata](docs/04-prima-sessione.md), con un esempio ufficiale da esplorare nel browser. Disponibili anche il PC fisso di Matteo (i7-12700K, 32 GB, GTX 1060 6 GB, 681 GB liberi, WSL2; inventario rilevato) e il Mac M3 Pro del socio; la prima inferenza GPU è su Kaggle, il fisso richiede un preflight dedicato.

La prima meta è riprodurre una procedura nota e comprenderne i limiti. La scelta fra First Letters e Progress Prizes resta da consolidare. Vincere è l'obiettivo del progetto, non un esito garantito dal funzionamento del software.

Account Kaggle e telefono verificati. Il [preflight dell'ambiente Kaggle](docs/reports/2026-09-05-kaggle-preflight.md) ha confermato PyTorch e due Tesla T4; la sessione è stata fermata e nessuna inferenza Vesuvius è stata ancora eseguita. La [revisione del 6 settembre 2026](docs/reports/2026-09-06-revisione-procedura-e00.md) ha verificato il dossier E00 su fonti primarie e fissato le decisioni per il piano. La ricerca comprende contributi pubblici di altri partecipanti oltre agli aggiornamenti di Francesco: prima selezione di 11 risorse documentata, nessuna nuova pipeline replicata.

## Organizzazione

GitHub conserva documentazione e, in seguito, codice, configurazioni e rapporti piccoli. Scansioni, pesi dei modelli e risultati voluminosi restano fuori da Git: per riprodurli conserveremo provenienza, versione e impronte dei file.

Il repository parte privato. La licenza del futuro codice e l'eventuale pubblicazione saranno decise prima di distribuire il lavoro, tenendo conto delle licenze delle risorse e delle condizioni del premio. Non è un progetto ufficiale della Vesuvius Challenge.

Le istruzioni comuni per gli agenti sono in [AGENTS.md](AGENTS.md). Per registrare il lavoro useremo la [scheda esperimento](docs/templates/esperimento.md) e la [scheda di revisione](docs/templates/revisione.md).
