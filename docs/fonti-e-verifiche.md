# Fonti e verifiche

Consultazione: 5 settembre 2026. Sono appunti di avvio; verificare regole e disponibilità prima di una decisione operativa. I collegamenti sono fonti, non prove di esperimenti eseguiti dal team.

## Fonti primarie

- [Regolamento e premi](https://scrollprize.org/prizes).
- [Introduzione interattiva ufficiale](https://scrollprize.org/get_started).
- [Problemi aperti](https://scrollprize.org/2026_open_problems).
- [VC3D](https://scrollprize.org/tutorial_VC3D) e [release](https://github.com/ScrollPrize/villa/releases).
- [Ink detection](https://scrollprize.org/tutorial5).
- [Catalogo dati](https://scrollprize.org/data_browser).
- [Codice villa](https://github.com/ScrollPrize/villa).
- [Catalogo ufficiale dei contributi della community](https://scrollprize.org/community_projects); prima selezione e revisioni nel [registro di ricerca](06-ricerca-community.md).
- [Checkpoint ink_9um](https://huggingface.co/scrollprize/ink_9um).
- [Kaggle Notebooks](https://www.kaggle.com/docs/notebooks) e [quota GPU](https://www.kaggle.com/docs/efficient-gpu-usage).

## Premi: orientamento, non regolamento completo

First Letters: 50.000 USD per rotolo, massimo dieci premi, per dieci lettere leggibili all'interno di una singola area di 4 cm² su un volume eleggibile. Grand Prize: montepremi di un milione USD per srotolamento completo, con requisiti molto più estesi. Titolo di PHerc. Paris 4: 50.000 USD. Questi premi indicano il 25 giugno 2027 come scadenza. Progress Prizes: contributi utili valutati mensilmente, con 20.000 USD al migliore e ulteriori premi discrezionali.

La pagina dei Progress Prizes mostra ancora il 31 agosto 2026 come prossima scadenza: è già trascorsa. Chiedere agli organizzatori la scadenza corrente. La clausola Discord è esplicita nella sezione Grand Prize; verificare l'applicazione alle altre categorie. Per i premi di scoperta è previsto di attendere l'annuncio prima di rendere pubblica la scoperta. Codice e materiali dovranno rispettare le condizioni di apertura e le licenze applicabili. [Fonte](https://scrollprize.org/prizes).

## Correzioni alla spiegazione iniziale

1. **Il team:** Matteo e il socio. Non dedurre dal messaggio inoltrato che Matteo abbia già compilato VC3D o sappia crescere segmenti.
2. **w035:** il tutorial lo identifica come parte del training set di ink_9um. Un risultato riuscito verifica la catena operativa, non la capacità su dati nuovi. [Fonte](https://scrollprize.org/tutorial5).
3. **Area:** 20 × 20 mm è un esempio di 4 cm². Una mesh da 5–6 cm² è una proposta pratica per avere margine, non un requisito ufficiale. Dal testo non discende automaticamente che un segmento più piccolo sia escluso, se le lettere soddisfano il criterio; per casi limite chiedere una conferma agli organizzatori.
4. **Concordanza:** 0,78 riportato dall'amico è una correlazione dei punteggi, non una probabilità del 78% di testo reale.
5. **Profondità:** gli intervalli 0–16, 7–23 e 14–30 descritti nel repository esterno si sovrappongono. Non sono tre campioni indipendenti. Mancato recupero a quegli offset non esclude ogni possibile errore di superficie.

## Risorse esterne e limiti

[ScrollScout](https://github.com/FrankTheRope/scrollscout) e [nota PHerc. 1447](https://github.com/FrankTheRope/scrollscout/blob/main/docs/pherc1447_predictions.md) sono contributi indipendenti. Trattare prestazioni, soglie e novità delle analisi come dichiarazioni degli autori finché replicate.

Nella conversazione preliminare è stato esaminato il commit d9be23361e159962394a76591aa543850c4a1d75. Il tentativo locale di test non è stato completato: prima mancavano il pacchetto e scipy, poi l'installazione isolata delle dipendenze è stata interrotta. Errori riportati: `ModuleNotFoundError: No module named 'scrollscout'`, quindi `No module named 'scipy'`; la verifica finale dell'ambiente isolato segnalava anche numpy e pytest mancanti. Questi sono problemi dell'ambiente di prova, non un fallimento scientifico del metodo. Non importiamo quel checkout nel progetto né dichiariamo i test superati.

Le affermazioni private dell'amico su analisi non ancora pubblicate restano informazioni da chiarire con lui; non si presumono priorità, esclusività o diritto di pubblicazione.

Nel consolidamento del 5 settembre è stato controllato anche ScrollScout al commit `29656e3b8455572dded5ed4a13ddfa974dac1a5e`: README e pesi predefiniti del codice non coincidono completamente. La [nota ScrollScout](05-scrollscout-e-piano-di-verifica.md) distingue versioni, score e controlli corretti. È una revisione documentale e parziale del codice, senza una nuova esecuzione dei test esterni.
