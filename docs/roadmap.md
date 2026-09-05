# Roadmap e decisioni

Aggiornamento: 5 settembre 2026.

## Decisioni consolidate dal contesto

- Il team è Matteo e il suo socio; l'amico fisico lavora separatamente.
- L'obiettivo è un contributo eccellente, riproducibile e candidabile a un premio.
- La sequenza richiesta è: comprendere, definire il setup, progettare i test, implementare ed eseguire.
- Creare una cartella locale e sincronizzare un repository GitHub è autorizzato per l'avvio.
- Matteo ha richiesto anche il consolidamento e il commit/push di tutti gli aggiornamenti documentali correnti, inclusa la ricerca sui contributi pubblici oltre a Francesco.
- La verifica telefonica Kaggle è completata e confermata nel browser. Matteo fornirà le specifiche dettagliate del fisso quando lo utilizzerà; il setup Kaggle procede dal portatile.

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
| F2 — Setup minimo | Account Kaggle e telefono verificati; nessuna GPU ancora eseguita; inventario hardware parziale | Un campione visualizzato e un piccolo notebook eseguibile |
| F3 — Progettazione dei test | Prima bozza disponibile | Campioni, baseline, controlli, budget, metriche e stop definiti |
| R — Ricerca community | Prima selezione di 11 risorse, revisioni e prove proposte registrate | Soluzioni esistenti valutate prima di ogni esperimento o nuovo strumento |
| F4 — Implementazione minima | Non avviata | Script/notebook ripetibile per E00–E02 |
| F5 — Ottimizzazione | Non avviata | Confronti documentati, esiti positivi e negativi |
| F6 — Ricerca e candidatura | Non avviata | Evidenza tecnica e valutazione previste dal premio scelto |

Prima delle campagne di ottimizzazione completare F3. Il setup può comprendere prove minime di funzionamento; queste non costituiscono ancora una ricerca scientifica su rotoli nuovi.

## Prossima sessione

Seguire la [prima sessione guidata](04-prima-sessione.md), la [ricerca community](06-ricerca-community.md) e il [setup Kaggle](02-strumenti-e-setup.md#primo-accesso-a-kaggle). Il [piano di verifica di ScrollScout](05-scrollscout-e-piano-di-verifica.md) è uno dei filoni di confronto.

1. Scrivere il primo piano eseguibile sulla documentazione consolidata: campione già renderizzato, checkpoint e software esatti, output atteso, limite di tempo/spazio e criterio di arresto per E00.
2. Preparare un notebook privato inizialmente su CPU, poi verificare l'assegnazione GPU e completare il controllo noto. Il contatore Kaggle osservato mostra 00:00 su 30 ore GPU e 20 ore TPU; disponibilità dell'acceleratore e funzionamento del modello restano da provare.
3. Salvare istruzioni, parametri e risultati; predisporre la ripetizione del socio e il confronto indipendente E02 usando la ricerca già raccolta.
4. Quando disponibili, rilevare modello NVIDIA, CPU, sistema operativo e spazio libero del fisso; poi RAM e spazio del Mac. Servirà l'username GitHub del socio per un invito esplicitamente richiesto. Questi dati non bloccano i primi due passi.

Nessun acceleratore è stato attivato, né sono stati effettuati inviti, registrazione Discord, installazione VC3D o submission. Non è stato impostato un monitoraggio automatico della community: il registro verrà usato nelle sessioni di ricerca e quando arrivano nuovi aggiornamenti.

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
- Setup scientifico e test GPU non eseguiti; nessuna spesa sostenuta per calcolo, nessun collaboratore invitato.
