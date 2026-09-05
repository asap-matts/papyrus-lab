# Roadmap e decisioni

Aggiornamento: 5 settembre 2026.

## Decisioni consolidate dal contesto

- Il team è Matteo e il suo socio; l'amico fisico lavora separatamente.
- L'obiettivo è un contributo eccellente, riproducibile e candidabile a un premio.
- La sequenza richiesta è: comprendere, definire il setup, progettare i test, implementare ed eseguire.
- Creare una cartella locale e sincronizzare un repository GitHub è autorizzato per l'avvio.

## Impostazioni iniziali modificabili

- Nome provvisorio PapyrusLab; repository privato papyrus-lab nell'account GitHub di Matteo.
- Documentazione prima del codice; nessun framework di training o servizio a pagamento scelto.
- Mac/Windows per analisi e visualizzazione; GPU NVIDIA remota per la procedura iniziale dei modelli.
- First Letters e Progress Prizes sono opzioni da confrontare. Nessun rotolo bersaglio scelto.

## Fasi

| Fase | Stato | Risultato atteso |
|---|---|---|
| F0 — Avvio | Completata e verificata | Repository privato e primo commit locale/remoto coincidenti |
| F1 — Comprensione | Da affrontare insieme | Entrambi distinguono scansione, mesh, render, previsione e prova |
| F2 — Setup minimo | Proposto | Un campione visualizzato e un piccolo notebook eseguibile |
| F3 — Progettazione dei test | Prima bozza disponibile | Campioni, baseline, controlli, budget, metriche e stop definiti |
| F4 — Implementazione minima | Non avviata | Script/notebook ripetibile per E00–E02 |
| F5 — Ottimizzazione | Non avviata | Confronti documentati, esiti positivi e negativi |
| F6 — Ricerca e candidatura | Non avviata | Evidenza tecnica e valutazione previste dal premio scelto |

Prima delle campagne di ottimizzazione completare F3. Il setup può comprendere prove minime di funzionamento; queste non costituiscono ancora una ricerca scientifica su rotoli nuovi.

## Prossima sessione

Partire da docs/01-capire-il-processo.md e discutere un esempio concreto. Successivamente raccogliere RAM e spazio del Mac, disponibilità degli account e tempo settimanale del team. Servirà l'username GitHub del socio per un invito esplicitamente richiesto.

Poi scrivere il primo piano eseguibile con commit di partenza, campione esatto e limite di risorse. Nessun invito, registrazione Discord, installazione VC3D, utilizzo Kaggle o submission è stato effettuato durante l'avvio.

## Verifica dell'avvio

- Repository creato: [asap-matts/papyrus-lab](https://github.com/asap-matts/papyrus-lab), privato, branch predefinito main.
- Primo commit pubblicato: ea7fe140dc3531fca66721608d4772deece715fe. Verificato identico con git rev-parse HEAD e git ls-remote origin refs/heads/main.
- Collegamenti Markdown locali: tutti risolti; git diff --cached --check: superato.
- Git ignore: verificato per esempi di dati, checkpoint, file .env, ambiente Python e output.
- Primo commit: 11 file di documentazione e configurazione Git, nessun dataset o modello.
- Albero di lavoro pulito dopo il primo push. Questo verbale viene pubblicato in un successivo commit documentale, la cui sincronizzazione è verificata nella sessione di avvio.
- Setup scientifico e test GPU non eseguiti; nessuna spesa sostenuta per calcolo, nessun collaboratore invitato.
