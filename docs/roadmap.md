# Roadmap e decisioni

Aggiornamento: 7 settembre 2026.

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
| F3 — Progettazione dei test | **E02-R01 eseguito il 7 settembre 2026** ([scheda](reports/2026-09-07-e02-r01.md), [manifest](reports/2026-09-07-e02-r01-manifest.json), [piano](plans/2026-09-06-e02-costruire-il-metro.md)): metro intra-segmento congelato — inventario di `ink_9um` (29 rappresentazioni, 24 segmenti fisici), tre maschere ufficiali mai usate per il training (721.550 pixel), divisione sviluppo (w016, 0814) / verifica sigillata (w029, fino a E05), baseline E00 misurata per segmento e per strato di distanza, soglia congelata τ\* = 91, tre revisioni Codex. **Gate G3 raggiunto** (decisione di Matteo del 7 settembre 2026) | Campioni, baseline, controlli, budget, metriche e stop definiti |
| R — Ricerca community | Prima selezione di 11 risorse, revisioni e prove proposte registrate | Soluzioni esistenti valutate prima di ogni esperimento o nuovo strumento |
| F4 — Implementazione minima | Non avviata | Script/notebook ripetibile per E00–E02 |
| F5 — Ottimizzazione | Non avviata | Confronti documentati, esiti positivi e negativi |
| F6 — Ricerca e candidatura | Non avviata | Evidenza tecnica e valutazione previste dal premio scelto |

Prima delle campagne di ottimizzazione completare F3. Il setup può comprendere prove minime di funzionamento; queste non costituiscono ancora una ricerca scientifica su rotoli nuovi.

## Prossima sessione

La [procedura operativa canonica](07-procedura-operativa.md) è stata revisionata in due giri read-only il 6 settembre 2026 ([rapporto](reports/2026-09-06-revisione-procedura-e00.md)): 23 finding, nessun P0, correzioni accettate e integrate. Il [dossier E00](08-dossier-input-e00.md) è stato verificato su fonti primarie e contiene le decisioni prese, il comando candidato e il criterio di esito proposto. Il [piano di verifica di ScrollScout](05-scrollscout-e-piano-di-verifica.md) resta uno dei filoni di confronto.

1. **E00-R01 eseguito e superato il 6 settembre 2026** ([scheda](reports/2026-09-06-e00-r01.md), [manifest](reports/2026-09-06-e00-r01-manifest.json), [piano](plans/2026-09-06-e00-controllo-noto-w035.md)): esecuzione automatizzata via API Kaggle (`scripts/kaggle_e00.py`), tre run generati da `scripts/build_e00_notebooks.py`; ~62 minuti di quota GPU in tutto, di cui due tentativi persi su dipendenze pigre poi coperte dal preflight. Revisione dell'esito da parte di Codex in sola lettura.
2. **E01-R01 eseguito e superato il 6 settembre 2026** dal socio (`micheleghisa`) con Codex ([scheda](reports/2026-09-06-e01-r01.md), [piano](plans/2026-09-06-e01-ripetizione-socio.md)): stesse metriche e TIFF identici bit per bit a E00, 11 minuti di quota GPU, otto ostacoli di avvio su Mac registrati e integrati nello script di bootstrap. Branch fuso in `main` dopo revisione read-only. **G2 raggiunto.**
3. **E02-R01 eseguito il 7 settembre 2026** ([scheda](reports/2026-09-07-e02-r01.md), [manifest](reports/2026-09-07-e02-r01-manifest.json), [piano](plans/2026-09-06-e02-costruire-il-metro.md), con emendamento A1 e tre revisioni Codex): inventario del training set da tre fonti (29 rappresentazioni, 24 segmenti fisici, tre trappole registrate, incluso il duplicato pubblico w045/w046); gli unici pixel a label ufficiale mai usati per la supervisione sono le tre maschere di validazione (w016, 0814, w029): **il metro è intra-segmento**, con adiacenza al training misurata per strato; divisione per segmento (sviluppo w016 + 0814, verifica w029 sigillata fino a E05); input poolati identici su tre macchine; baseline E00 (seed 42) sui pixel held-out di sviluppo: AUROC 0,774 e 0,874, best-F1 0,531 e 0,753, identici alla terza cifra ai numeri pubblicati da R02; seed 43 informativo (forte effetto del seed su w016). Verifiche indipendenti del socio S1 e S2 concordanti (branch `e02-socio`). Circa 47 minuti di quota GPU, nessuna spesa. **G3 raggiunto** (decisione di Matteo del 7 settembre 2026); branch `e02-socio` fuso in `main`.
4. **Prossimo: la decisione su dove investire**, da scrivere con i numeri di E02 in [docs/decisions/2026-09-06-dove-investire.md](decisions/2026-09-06-dove-investire.md) (perdita fra pixel studiati e pixel nuovi da 0,99 a 0,53–0,75 di F1; forte dipendenza da seed e segmento; effetto dell'adiacenza misurato ma non esaustivo), poi il piano E03. Vincolo permanente: i pixel held-out di `pherc1667-w029` non si leggono prima di E05.
5. Attività separate, non bloccanti: preflight della GTX 1060 del fisso; aggiornamento del registro community; compito S3 del socio (seed 43 con la sua quota) differito, da progettare solo se la quota di Matteo non basta; rigenerare il token API Kaggle di Matteo (passato in chat il 6 settembre 2026).

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
