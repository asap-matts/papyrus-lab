# Capire il processo

Immagina una lunga striscia di carta scritta, arrotolata molto stretta, schiacciata e resa fragilissima dal calore. Possiamo studiarne l'interno con una scansione. Il nostro lavoro consiste nel trasformare quelle misure in una pagina sulla quale una persona possa leggere.

## 1. Guardare dentro

La tomografia, spesso abbreviata CT, ricostruisce l'oggetto in tre dimensioni usando raggi X. Un voxel è il corrispondente tridimensionale di un pixel: un piccolo elemento del volume misurato. Le scansioni sono già messe a disposizione dagli organizzatori.

Il calcolo deve recuperare sia la forma del foglio sia il segnale dell'inchiostro. Sono due difficoltà diverse; entrambe limitano il risultato. [Spiegazione tecnica ufficiale](https://scrollprize.org/2026_open_problems).

## 2. Seguire il foglio giusto

Pensa al bordo di un tappeto arrotolato visto di lato. È facile seguirlo dove i giri sono separati; dove sono schiacciati insieme, si rischia di passare al giro vicino.

**Segmentazione** significa ricostruire la superficie di una porzione di foglio. **Segmento** è quella porzione. **Mesh** è la rete di punti che ne descrive forma e collegamenti. Il formato **tifxyz** conserva la corrispondenza fra punti della pagina digitale e posizioni nell'oggetto scansionato.

La mesh deve seguire davvero lo stesso foglio. Se un'immagine è brutta, il problema può trovarsi qui, prima del modello che cerca inchiostro.

## 3. Distendere e campionare

**Appiattire** significa assegnare una posizione sulla pagina digitale a ciascun punto della superficie curva. **Rendering** significa estrarre dalla scansione i valori corrispondenti a quella superficie.

Un **surface volume** è una piccola pila di immagini campionate anche un po' sopra e sotto la superficie ricostruita. Serve perché la posizione stimata può essere leggermente imprecisa. È diverso dall'immagine finale sulla quale cercheremo le lettere.

VC3D è il programma che permette di vedere la scansione, costruire e controllare queste superfici. [Guida ufficiale VC3D](https://scrollprize.org/tutorial_VC3D).

## 4. Far emergere l'inchiostro

Il **modello** è un programma che ha imparato associazioni fra piccoli dettagli della scansione e presenza di inchiostro. **Addestramento** è il processo con cui impara; **inferenza** è usarlo su un dato. Possiamo iniziare con un modello già addestrato, ink_9um.

Un **checkpoint** è una versione salvata del modello; il **seed** controlla le scelte casuali di un'esecuzione. Confrontare versioni diverse aiuta a capire quanto il risultato dipenda dalle singole scelte.

L'output è una mappa dell'inchiostro previsto, che deve essere esaminata criticamente. [Tutorial di ink detection](https://scrollprize.org/tutorial5).

## 5. Decidere se crederci

Un **falso positivo** è una macchia interpretata come scrittura. Un **falso negativo** è scrittura che il procedimento non riesce a mostrare. Un output vuoto non dimostra che il papiro fosse bianco.

Per questo prima proviamo un caso noto, poi misuriamo su casi indipendenti. La concordanza fra due modelli è un indizio: possono anche sbagliare entrambi nello stesso modo.

**ScrollScout** ordina le zone da guardare secondo quanto la loro struttura somiglia a righe di scrittura. È proposto come strumento di selezione, non come certificatore di lettere. Le sue soglie devono essere verificate nel nostro protocollo. [Repository esterno](https://github.com/FrankTheRope/scrollscout).

## Che cosa significa ottimizzare

Vogliamo rendere più probabile trovare un risultato reale con il tempo e le risorse disponibili. Una modifica utile può ridurre il tempo per preparare una superficie, recuperare più tratti veri, diminuire i falsi allarmi o permettere al socio di ripetere una prova. Misureremo queste cose separatamente: un programma più veloce può produrre risultati peggiori.

Il primo successo del team sarà spiegare e ripetere un caso noto. Successivamente costruiremo un confronto che possa anche dimostrare che una nostra idea non migliora nulla.
