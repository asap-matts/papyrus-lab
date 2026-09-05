# Roadmap e decisioni

Aggiornamento: 5 settembre 2026.

## Decisioni consolidate dal contesto

- Il team è Matteo e il suo socio; l'amico fisico lavora separatamente.
- L'obiettivo è un contributo eccellente, riproducibile e candidabile a un premio.
- La sequenza richiesta è: comprendere, definire il setup, progettare i test, implementare ed eseguire.
- Creare una cartella locale e sincronizzare un repository GitHub è autorizzato per l'avvio.
- Matteo ha richiesto anche il consolidamento e il commit/push di tutti gli aggiornamenti documentali correnti, inclusa la ricerca sui contributi pubblici oltre a Francesco.
- La verifica telefonica Kaggle è completata e confermata nel browser. Un preflight privato ha verificato due Tesla T4 e CUDA tramite PyTorch, poi la sessione è stata fermata. Matteo fornirà le specifiche dettagliate del fisso quando lo utilizzerà.

## Impostazioni iniziali modificabili

- Nome provvisorio PapyrusLab; repository privato papyrus-lab nell'account GitHub di Matteo.
- Documentazione prima del codice; nessun framework di training o servizio a pagamento scelto.
- Mac/Windows per analisi e visualizzazione; prima inferenza proposta su Kaggle. Fisso con NVIDIA da circa 6 GB, 32 GB RAM e NVMe da 1 TB per preparazione dati e successivo confronto di inferenza ridotta. Specifiche dichiarate, non rilevate direttamente.
- First Letters e Progress Prizes sono opzioni da confrontare. Nessun rotolo bersaglio scelto.

## Fasi

| Fase | Stato | Risultato atteso |
|---|---|---|
| F0 — Avvio | Completata e verificata | Repository privato e primo commit locale/remoto coincidenti |
| F1 — Comprensione | In corso; prima sessione guidata preparata | Entrambi distinguono scansione, mesh, render, previsione e prova |
| F2 — Setup minimo | Notebook Kaggle privato eseguito su due Tesla T4; pipeline e campione non ancora provati; inventario hardware parziale | Un campione noto visualizzato e inferenza minima verificata |
| F3 — Progettazione dei test | Procedura operativa canonica in bozza; revisione e piano E00 mancanti | Campioni, baseline, controlli, budget, metriche e stop definiti |
| R — Ricerca community | Prima selezione di 11 risorse, revisioni e prove proposte registrate | Soluzioni esistenti valutate prima di ogni esperimento o nuovo strumento |
| F4 — Implementazione minima | Non avviata | Script/notebook ripetibile per E00–E02 |
| F5 — Ottimizzazione | Non avviata | Confronti documentati, esiti positivi e negativi |
| F6 — Ricerca e candidatura | Non avviata | Evidenza tecnica e valutazione previste dal premio scelto |

Prima delle campagne di ottimizzazione completare F3. Il setup può comprendere prove minime di funzionamento; queste non costituiscono ancora una ricerca scientifica su rotoli nuovi.

## Prossima sessione

La [procedura operativa canonica](07-procedura-operativa.md) traduce il metodo scientifico in gate, artefatti, criteri di arresto e combinazioni possibili fra due agenti, senza assegnare ruoli permanenti. Sottoporla a revisione incrociata read-only, consolidare i finding accettati e pubblicarla su un commit pulito. Il [piano di verifica di ScrollScout](05-scrollscout-e-piano-di-verifica.md) resta uno dei filoni di confronto.

1. Revisionare il [dossier E00](08-dossier-input-e00.md), che propone w035 e congela le revisioni candidate; risolvere acquisizione della sola label e installazione minima. Dopo la revisione della procedura, scrivere il primo piano eseguibile sul nuovo commit di base.
2. Usare il notebook privato già collaudato per completare il controllo noto. Il [preflight](reports/2026-09-05-kaggle-preflight.md) ha verificato due Tesla T4, PyTorch e CUDA; disponibilità dell'acceleratore non equivale ancora al funzionamento del modello Vesuvius.
3. Salvare istruzioni, parametri e risultati; predisporre la ripetizione del socio e il confronto indipendente E02 usando la ricerca già raccolta.
4. Quando disponibili, rilevare modello NVIDIA, CPU, sistema operativo e spazio libero del fisso; poi RAM e spazio del Mac. Servirà l'username GitHub del socio per un invito esplicitamente richiesto. Questi dati non bloccano i primi due passi.

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
