# PapyrusLab — istruzioni di progetto

Fonte comune per Codex e Claude Code. Leggere prima README.md e docs/roadmap.md.

## Intento e fase

Il team è Matteo e il suo socio (Mac M3 Pro). L'amico fisico è un interlocutore esterno indipendente. Non assegnargli ruoli, quote o obblighi. Non presumere che Matteo abbia già VC3D o competenze di segmentazione.

Fase attuale: comprensione, setup da progettare e metodo sperimentale da discutere. L'avvio documentale non autorizza implicitamente campagne GPU, training, spese o submission. Il bootstrap e la prima sincronizzazione GitHub sono stati richiesti esplicitamente nella conversazione del 5 settembre 2026.

## Metodo

- Spiegazioni e documentazione in italiano accessibile. Definire un termine tecnico al primo uso.
- Separare fatti ufficiali, risultati esterni, ipotesi del team e misure replicate.
- Non presentare una scelta proposta come approvata.
- Un solo writer per cartella. Il socio usa un clone proprio; agenti paralleli richiedono isolamento e incarichi espliciti.
- Non leggere contenuti di .env, token o credenziali. Non pubblicare segreti o conversazioni private.
- Commit, push, merge, PR e deploy richiedono richiesta esplicita; l'autorizzazione al bootstrap non vale per tutte le modifiche future.
- Operazioni distruttive solo con conferma. Conservare risultati negativi e spiegare gli esperimenti interrotti.
- Usare percorsi relativi alla radice del repository nel codice e nelle configurazioni. Tenere il clone fuori da OneDrive/iCloud o altre cartelle sincronizzate.
- Codice futuro e messaggi di commit in inglese; commit con prefissi docs:, chore:, feat:, fix: o test:. Branch di lavoro brevi e descrittivi, derivati da main.

## Fonti e validazione

Il sito ufficiale decide regole e volumi eleggibili: ricontrollarlo prima di selezionare un obiettivo o inviare risultati. Non trasformare automaticamente consigli esterni in requisiti ufficiali.

La ricerca sui contributi pubblici degli altri partecipanti è parte del progetto, oltre agli aggiornamenti di Francesco. Prima di fissare esperimenti o sviluppare strumenti, consultare docs/06-ricerca-community.md e aggiornare fonti, revisioni, limiti e prova minima proposta. Non trattare una risorsa individuata come una dipendenza adottata o un risultato replicato. Cercare anche correzioni già integrate a monte.

w035 appartiene al training set di ink_9um: è un controllo di funzionamento, non una misura indipendente di generalizzazione. Due seed dello stesso modello possono condividere errori. Un punteggio ScrollScout non è una probabilità di avere trovato testo.

Non usare generazione di immagini, completamento linguistico o ritocchi che inventino tratti per produrre evidenza di inchiostro. Conservare gli output originali; registrare separatamente trasformazioni per la sola visualizzazione.

## Verifiche e piani

Per ora il repository contiene solo documenti: verificare link relativi, git diff --check, file tracciati e assenza di file voluminosi/riservati. Non esistono ancora build o test scientifici da dichiarare superati.

I futuri piani eseguibili andranno in docs/plans/AAAA-MM-GG-argomento.md con commit di partenza, perimetro, ordine, controlli e condizione di arresto. Verificare il commit prima di eseguirli e fermarsi se il piano non corrisponde allo stato reale. docs/roadmap.md e docs/03-metodo-sperimentale.md sono proposte di percorso, non contratti di implementazione già approvati.
