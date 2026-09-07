# PapyrusLab — istruzioni di progetto

Fonte comune per Codex e Claude Code. Leggere prima README.md e docs/roadmap.md.

## Intento e fase

Il team è Matteo e il suo socio (Mac M3 Pro). L'amico fisico è un interlocutore esterno indipendente. Non assegnargli ruoli, quote o obblighi. Non presumere che Matteo abbia già VC3D o competenze di segmentazione.

Fase attuale: **E02-R01 eseguito il 7 settembre 2026** (docs/reports/2026-09-07-e02-r01.md, manifest e piano con emendamento A1): metro intra-segmento congelato sulle tre maschere di validazione ufficiali di `ink_9um` (sviluppo `pherc0139-w016` e `pherc0814-46527`; verifica `pherc1667-w029` **sigillata**: i suoi pixel held-out non si leggono prima di E05), baseline E00 misurata per segmento con `scripts/e02_metrics.py` (soglia congelata 91 in configs/e02/baseline.json), gate G3 raggiunto (decisione di Matteo del 7 settembre 2026). E00-R01 ed E01-R01 superati il 6 settembre 2026 (docs/reports/2026-09-06-e00-r01.md, docs/reports/2026-09-06-e01-r01.md): G1 e G2 superati, livello di evidenza L3, riproducibilità bit per bit su un secondo account; nessuna generalizzazione dimostrata. Esecuzione automatizzata via API Kaggle (scripts/kaggle_e00.py, notebook generati da scripts/build_e00_notebooks.py, label da dataset Kaggle privato con hash verificato; scripts/e01_bootstrap_mac.sh per l'avvio su Mac). Il socio (GitHub e Kaggle `micheleghisa`, collaboratore del repository) lavora su branch dedicati con Codex; la fusione in main la decide Matteo. **Stadio deciso da Matteo il 7 settembre 2026** (docs/decisions/2026-09-06-dove-investire.md, sezione "Decisione", dopo la nota di intake sulle fonti ufficiali e un secondo parere di Codex in cieco): rendering e profondità, misurati come **tolleranza all'offset Z** sui pixel held-out di sviluppo (w016, 0814), seed 42 e 43, offset fino a ±5 slice in due tappe, più controlli a costo zero sui TIFF conservati; il risultato è la curva AUROC(offset), non una finestra migliore. **Piano E03 congelato il 7 settembre 2026** (docs/plans/2026-09-07-e03-tolleranza-offset-z.md, con docs/plans/2026-09-07-e03-compiti-socio.md e docs/plans/e03-prompt-codex-socio.md): dodici passi, revisione Codex R1 chiusa con 7 finding accettati. Prossimo passo: passi 0–5 (script, test, generatore, pilota) e revisione R2 sul codice; **nessun run GPU prima di R2 e del "vai" di Matteo, uno per run**. Il socio esegue una procedura unica S1 → S2 → S3 dopo il passo 10, sul commit dichiarato nell'intestazione del suo piano. Modelli Codex: `gpt-5.6-sol` per default, `gpt-6-astra` solo per compiti molto complessi e su decisione di Matteo. Progress Prizes: scadenza corrente 30 settembre 2026; la candidatura si decide solo con l'esito revisionato; i Terms and Conditions chiedono l'apertura del codice per accettare il premio, non alla submission. I livelli di evidenza si chiamano L0–L5, gli esperimenti E00–E06. Matteo ha autorizzato (6 settembre 2026) commit e push senza richiesta puntuale per il lavoro in corso; restano su approvazione esplicita i run GPU, gli inviti, le spese e le submission. L'avvio documentale non autorizza implicitamente campagne GPU, training, spese o submission. Il bootstrap e la prima sincronizzazione GitHub sono stati richiesti esplicitamente nella conversazione del 5 settembre 2026.

## Metodo

- Spiegazioni e documentazione in italiano accessibile. Definire un termine tecnico al primo uso.
- Separare fatti ufficiali, risultati esterni, ipotesi del team e misure replicate.
- Non presentare una scelta proposta come approvata.
- Un solo writer per cartella. Il socio usa un clone proprio; agenti paralleli richiedono isolamento e incarichi espliciti.
- Claude e Codex non hanno ruoli permanenti in PapyrusLab. Scegliere per ogni attività chi organizza, esegue o revisiona in base a contesto, importanza, indipendenza utile e budget disponibile; registrare la scelta nel piano o nella revisione.
- Non leggere contenuti di .env, token o credenziali. Non pubblicare segreti o conversazioni private.
- Commit, push, merge, PR e deploy richiedono richiesta esplicita; l'autorizzazione al bootstrap non vale per tutte le modifiche future.
- Operazioni distruttive solo con conferma. Conservare risultati negativi e spiegare gli esperimenti interrotti.
- Usare percorsi relativi alla radice del repository nel codice e nelle configurazioni. Tenere il clone fuori da OneDrive/iCloud o altre cartelle sincronizzate.
- Codice futuro e messaggi di commit in inglese; commit con prefissi docs:, chore:, feat:, fix: o test:. Branch di lavoro brevi e descrittivi, derivati da main.

## Fonti e validazione

Il sito ufficiale decide regole e volumi eleggibili: ricontrollarlo prima di selezionare un obiettivo o inviare risultati. Non trasformare automaticamente consigli esterni in requisiti ufficiali.

La ricerca sui contributi pubblici degli altri partecipanti è parte del progetto, oltre agli aggiornamenti di Francesco. Prima di fissare esperimenti o sviluppare strumenti, consultare docs/06-ricerca-community.md e aggiornare fonti, revisioni, limiti e prova minima proposta. Non trattare una risorsa individuata come una dipendenza adottata o un risultato replicato. Cercare anche correzioni già integrate a monte.

w035 appartiene al training set di ink_9um, in due rappresentazioni (2,4 µm ridotta e nativa 9,362 µm): è un controllo di funzionamento, non una misura indipendente di generalizzazione. I nomi dei segmenti nel dataset delle label non seguono la numerazione pubblica: non dedurre identità dal numero. Due seed dello stesso modello possono condividere errori. Un punteggio ScrollScout non è una probabilità di avere trovato testo.

Non usare generazione di immagini, completamento linguistico o ritocchi che inventino tratti per produrre evidenza di inchiostro. Conservare gli output originali; registrare separatamente trasformazioni per la sola visualizzazione.

## Verifiche e piani

Per ora il repository contiene solo documenti: verificare link relativi, git diff --check, file tracciati e assenza di file voluminosi/riservati. Non esistono ancora build o test scientifici da dichiarare superati.

La procedura canonica è `docs/07-procedura-operativa.md`. I futuri piani eseguibili andranno in docs/plans/AAAA-MM-GG-argomento.md con commit di partenza, perimetro, ordine, controlli e condizione di arresto. Verificare il commit prima di eseguirli e fermarsi se il piano non corrisponde allo stato reale. docs/roadmap.md e docs/03-metodo-sperimentale.md sono proposte di percorso, non contratti di implementazione già approvati.
