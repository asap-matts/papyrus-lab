# Prima sessione: capire un esempio prima di eseguirlo

Questa è una guida di apprendimento, non un piano eseguibile né un esperimento già svolto. Possiamo iniziare dal browser mentre raccogliamo le specifiche del fisso.

## Osservare i passaggi

Aprire la [pagina introduttiva ufficiale](https://scrollprize.org/get_started). Contiene due esercizi dimostrativi: cercare l'inchiostro e seguire una superficie. L'ordine della pagina parte dal risultato visibile e poi risale alla ricostruzione del foglio.

1. Nell'esercizio dell'inchiostro, distinguere l'immagine della superficie dalla previsione. Le aree indicate a mano servono da esempi: il programma usa quegli esempi per cercare dettagli simili altrove. Il risultato dipende anche dalla qualità degli esempi dati.
2. Nell'esercizio della superficie, osservare i giri del foglio in una sezione. Seguire un solo giro: il passaggio accidentale al vicino mescola parti differenti. Un risultato confuso può nascere da questo errore prima ancora di applicare un modello.
3. Riguardare la sequenza completa: scansione → porzione di superficie → immagine ricostruita → inchiostro previsto → verifica umana. Il sito è una dimostrazione educativa; completarla non produce un risultato candidabile al premio.

Il [tutorial w035](https://scrollprize.org/tutorial5#ink-detection-at-9-µm-pretrained-cross-scroll-models) offre un esempio della procedura reale. Se l'ancora del sito cambia, cercare nella pagina “w035”. Questo segmento è anche nel training set di ink_9um: ci serve per controllare il funzionamento, non per misurare l'efficacia su un rotolo nuovo.

## Quale sarà la nostra prima prova al computer

Useremo una porzione già preparata, così nella prima esecuzione possiamo concentrarci su input e modello. Il passaggio di costruzione della superficie verrà esercitato separatamente.

- **Riceviamo:** un piccolo volume che segue la superficie e una versione salvata del modello.
- **Eseguiamo:** il modello sul campione, su una singola GPU compatibile.
- **Otteniamo:** un'immagine dell'inchiostro previsto, insieme ai parametri e ai tempi della prova.
- **Controlliamo:** che orientamento, dimensioni e aspetto corrispondano al caso noto. Un comando terminato senza errori, da solo, non basta.

Fisso e Kaggle potranno ricevere esattamente la stessa prova. Una GPU più veloce dovrebbe ridurre l'attesa a parità di procedura, non rendere automaticamente più vera la scrittura trovata. Se gli output differiscono, bisogna prima spiegare configurazione, precisione numerica e ambiente.

## Che cosa decidiamo dopo

Con la prima ripetizione riuscita potremo separare le domande: quanto tempo costa preparare una superficie? Quanto costa passarla al modello? Quanti falsi allarmi dobbiamo guardare? Le risposte guideranno la priorità delle ottimizzazioni.

Prima di ampliare la ricerca completeremo il [metodo sperimentale](03-metodo-sperimentale.md). L'hardware verrà assegnato ai lavori che ne beneficiano, senza costruire fin dall'inizio un sistema distribuito fra tutte le macchine.

## Dati mancanti per il setup eseguibile

Il fisso è stato inventariato il 6 settembre 2026 (i7-12700K, 32 GB, GTX 1060 6 GB, 681 GB liberi, WSL2; dettagli in [strumenti e setup](02-strumenti-e-setup.md)). Restano da rilevare memoria e spazio del Mac. Account Kaggle e verifica telefonica sono completati: E00 si prepara su Kaggle; l'eventuale inferenza sul fisso richiede prima un preflight della GPU.
