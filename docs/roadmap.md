# Roadmap e decisioni

Aggiornamento: 6 settembre 2026.

## Decisioni consolidate dal contesto

- Il team è Matteo e il suo socio; l'amico fisico lavora separatamente.
- L'obiettivo è un contributo eccellente, riproducibile e candidabile a un premio.
- La sequenza richiesta è: comprendere, definire il setup, progettare i test, implementare ed eseguire.
- Creare una cartella locale e sincronizzare un repository GitHub è autorizzato per l'avvio.
- Matteo ha richiesto anche il consolidamento e il commit/push di tutti gli aggiornamenti documentali correnti, inclusa la ricerca sui contributi pubblici oltre a Francesco.
- La verifica telefonica Kaggle è completata e confermata nel browser. Un preflight privato ha verificato due Tesla T4 e CUDA tramite PyTorch, poi la sessione è stata fermata. Le specifiche del fisso sono state rilevate il 6 settembre 2026 (vedi [strumenti e setup](02-strumenti-e-setup.md)).
- Decisioni del 6 settembre 2026, dopo la revisione: E00 usa il branch congelato `merge-ink-pipelines`; su Kaggle si installa sul Python di sistema senza `uv run`; il tetto di spazio locale sale a 10 GB; Claude è writer di correzioni e piano, Codex revisore in sola lettura, Matteo esecutore e arbitro, il socio entra a E01.

## Impostazioni iniziali modificabili

- Nome provvisorio PapyrusLab; repository privato papyrus-lab nell'account GitHub di Matteo.
- Documentazione prima del codice; nessun framework di training o servizio a pagamento scelto.
- Mac/Windows per analisi e visualizzazione; prima inferenza su Kaggle. Fisso (i7-12700K, 32 GB, GTX 1060 6 GB, NVMe 1 TB con 681 GB liberi, WSL2) per scrittura, preparazione dati e controlli CPU; l'inferenza sul fisso richiede un preflight dedicato per la GPU Pascal.
- First Letters e Progress Prizes sono opzioni da confrontare. Nessun rotolo bersaglio scelto.

## Fasi

| Fase | Stato | Risultato atteso |
|---|---|---|
| F0 — Avvio | Completata e verificata | Repository privato e primo commit locale/remoto coincidenti |
| F1 — Comprensione | In corso; prima sessione guidata preparata | Entrambi distinguono scansione, mesh, render, previsione e prova |
| F2 — Setup minimo | Notebook Kaggle privato eseguito su due Tesla T4; inventario del fisso rilevato; pipeline e campione non ancora provati | Un campione noto visualizzato e inferenza minima verificata |
| F3 — Progettazione dei test | Procedura revisionata e corretta il 6 settembre 2026; dossier E00 verificato su fonti primarie; piano E00 da scrivere sul commit corrente | Campioni, baseline, controlli, budget, metriche e stop definiti |
| R — Ricerca community | Prima selezione di 11 risorse, revisioni e prove proposte registrate | Soluzioni esistenti valutate prima di ogni esperimento o nuovo strumento |
| F4 — Implementazione minima | Non avviata | Script/notebook ripetibile per E00–E02 |
| F5 — Ottimizzazione | Non avviata | Confronti documentati, esiti positivi e negativi |
| F6 — Ricerca e candidatura | Non avviata | Evidenza tecnica e valutazione previste dal premio scelto |

Prima delle campagne di ottimizzazione completare F3. Il setup può comprendere prove minime di funzionamento; queste non costituiscono ancora una ricerca scientifica su rotoli nuovi.

## Prossima sessione

La [procedura operativa canonica](07-procedura-operativa.md) è stata revisionata in due giri read-only il 6 settembre 2026 ([rapporto](reports/2026-09-06-revisione-procedura-e00.md)): 23 finding, nessun P0, correzioni accettate e integrate. Il [dossier E00](08-dossier-input-e00.md) è stato verificato su fonti primarie e contiene le decisioni prese, il comando candidato e il criterio di esito proposto. Il [piano di verifica di ScrollScout](05-scrollscout-e-piano-di-verifica.md) resta uno dei filoni di confronto.

1. Commit documentale delle correzioni eseguito (`d430456`). Sul quel commit è scritto il [piano E00](plans/2026-09-06-e00-controllo-noto-w035.md) con prerequisiti, criterio di esito e comando congelati; revisione read-only del piano da parte di Codex, poi commit del piano su richiesta.
2. Prerequisiti senza GPU: installazione sul Python di Kaggle provata, Internet del notebook verificato, label scaricata, hash dei checkpoint controllati, destinazione degli output decisa.
3. E00 su una Tesla T4 con il notebook privato; il [preflight](reports/2026-09-05-kaggle-preflight.md) ha verificato l'acceleratore, non il modello.
4. Salvare istruzioni, parametri e risultati; predisporre la ripetizione del socio (E01) e il confronto E02. Servono ancora RAM e spazio del Mac e l'username GitHub del socio per un invito esplicitamente richiesto. Un preflight della GTX 1060 del fisso è un'attività separata.

L'acceleratore Kaggle è stato attivato soltanto per il preflight e poi fermato. Non sono stati effettuati inviti, registrazione Discord, installazione VC3D o submission. Non è stato impostato un monitoraggio automatico della community: il registro verrà usato nelle sessioni di ricerca e quando arrivano nuovi aggiornamenti.

## Consolidamento documentale del 5 settembre 2026

Inclusi inventario dichiarato del fisso, stato Kaggle verificato, guida della prima sessione, analisi ScrollScout con rettifiche di versioni e controlli, ricerca community con 11 risorse e collegamenti al metodo sperimentale. Le fonti canoniche sono README per l'indice, questo documento per lo stato, strumenti-e-setup per l'inventario e il registro community per i contributi esterni. La richiesta corrente autorizza commit e push di questo insieme; non cambia la regola delle future richieste esplicite.

La pubblicazione viene verificata nella sessione confrontando HEAD con main remoto e controllando l'albero di lavoro. I risultati scientifici rimangono da produrre: la verifica documentale non equivale a test GPU o a una replica delle pipeline esterne.

## Verifica dell'avvio

- Repository creato: [asap-matts/papyrus-lab](https://github.com/asap-matts/papyrus-lab), privato, branch predefinito main.
- Commit di bootstrap pubblicato: c5e388dd3e21731fb15d93a636398f5347b520d7. Verificato identico con git rev-parse HEAD e git ls-remote origin refs/heads/main prima delle modifiche documentali correnti.
- Collegamenti Markdown locali: tutti risolti; git diff --cached --check: superato.
- Git ignore: verificato per esempi di dati, checkpoint, file .env, ambiente Python e output.
- Primo commit: 11 file di documentazione e configurazione Git, nessun dataset o modello.
- Albero di lavoro pulito dopo il primo push. Questo verbale viene pubblicato in un successivo commit documentale, la cui sincronizzazione è verificata nella sessione di avvio.
- Setup scientifico ed E00 non eseguiti. Il successivo preflight tecnico GPU è documentato separatamente; nessuna spesa sostenuta per calcolo, nessun collaboratore invitato.
