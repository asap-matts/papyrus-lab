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
| F2 — Setup minimo | **Completata il 6 settembre 2026**: E00-R01 (Matteo, G1) ed E01-R01 (socio, G2): pipeline ufficiale su Kaggle (una T4) su w035, AUROC 0,999 contro la label con orientamento corretto, riprodotta da un secondo operatore con TIFF **identici bit per bit** | Un campione noto visualizzato e inferenza minima verificata |
| F3 — Progettazione dei test | Procedura revisionata e corretta; E00 ed E01 eseguiti. **Prossimo: E02** — congelare dati di sviluppo e verifica, baseline e metriche (gestione: Matteo dai suoi PC; compiti puntuali al socio) | Campioni, baseline, controlli, budget, metriche e stop definiti |
| R — Ricerca community | Prima selezione di 11 risorse, revisioni e prove proposte registrate | Soluzioni esistenti valutate prima di ogni esperimento o nuovo strumento |
| F4 — Implementazione minima | Non avviata | Script/notebook ripetibile per E00–E02 |
| F5 — Ottimizzazione | Non avviata | Confronti documentati, esiti positivi e negativi |
| F6 — Ricerca e candidatura | Non avviata | Evidenza tecnica e valutazione previste dal premio scelto |

Prima delle campagne di ottimizzazione completare F3. Il setup può comprendere prove minime di funzionamento; queste non costituiscono ancora una ricerca scientifica su rotoli nuovi.

## Prossima sessione

La [procedura operativa canonica](07-procedura-operativa.md) è stata revisionata in due giri read-only il 6 settembre 2026 ([rapporto](reports/2026-09-06-revisione-procedura-e00.md)): 23 finding, nessun P0, correzioni accettate e integrate. Il [dossier E00](08-dossier-input-e00.md) è stato verificato su fonti primarie e contiene le decisioni prese, il comando candidato e il criterio di esito proposto. Il [piano di verifica di ScrollScout](05-scrollscout-e-piano-di-verifica.md) resta uno dei filoni di confronto.

1. **E00-R01 eseguito e superato il 6 settembre 2026** ([scheda](reports/2026-09-06-e00-r01.md), [manifest](reports/2026-09-06-e00-r01-manifest.json), [piano](plans/2026-09-06-e00-controllo-noto-w035.md)): esecuzione automatizzata via API Kaggle (`scripts/kaggle_e00.py`), tre run generati da `scripts/build_e00_notebooks.py`; ~62 minuti di quota GPU in tutto, di cui due tentativi persi su dipendenze pigre poi coperte dal preflight. Revisione dell'esito da parte di Codex in sola lettura.
2. **E01-R01 eseguito e superato il 6 settembre 2026** dal socio (`micheleghisa`) con Codex ([scheda](reports/2026-09-06-e01-r01.md), [piano](plans/2026-09-06-e01-ripetizione-socio.md)): stesse metriche e TIFF identici bit per bit a E00, 11 minuti di quota GPU, otto ostacoli di avvio su Mac registrati e integrati nello script di bootstrap. Branch fuso in `main` dopo revisione read-only. **G2 raggiunto.**
3. **E02 (prossimo)**: costruire il metro — inventario del training set di `ink_9um` con la mappatura corretta dei nomi, candidati puliti con label affidabile, divisione sviluppo/verifica per segmento o rotolo, baseline congelata (la procedura di E00), metriche per segmento, manifest revisionato prima di qualunque confronto. La sostanza è nei sei punti di [docs/03 §Costruire il confronto](03-metodo-sperimentale.md); usare R02–R05 del registro community; attenzione alle due trappole del dataset `ink_9um` (doppia rappresentazione, nomi non allineati). Il piano E02 va scritto sul commit corrente e revisionato prima dell'esecuzione. Gestione: Matteo dal portatile (bastano Git, Python e il token Kaggle: il lavoro è lettura, metadati e CPU; le inferenze restano su Kaggle); al socio compiti puntuali. **La scelta di dove investire è rinviata a dopo E02, con la regola scritta in [docs/decisions/2026-09-06-dove-investire.md](decisions/2026-09-06-dove-investire.md).**
4. Attività separate, non bloccanti: preflight della GTX 1060 del fisso; aggiornamento del registro community; inventario del Mac del socio (Python di sistema 3.9, Homebrew presente).

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
