# Proposta di metodo sperimentale

**Stato: bozza di progettazione.** Serve a discutere come misureremo il progresso prima di scrivere automazioni o lanciare una ricerca estesa. I budget, il dataset e le soglie finali richiedono ancora una scelta del team.

## Tre tipi di prove

| Prova | Domanda | Limite |
|---|---|---|
| Controllo di funzionamento su w035 | Abbiamo collegato correttamente dati e modello? | w035 è nel training set di ink_9um: non prova che il modello funzioni su casi nuovi |
| Confronto su dati con riferimento indipendente | Una modifica migliora rispetto alla procedura iniziale? | Occorre verificare la provenienza delle etichette e l'assenza di sovrapposizioni |
| Esplorazione di un rotolo non letto | Emergono candidati da verificare? | Non conosciamo il testo vero: non possiamo dichiarare accuratezza o assenza d'inchiostro |

La distinzione relativa a w035 è dichiarata nel [tutorial ufficiale](https://scrollprize.org/tutorial5). Non usare semplicemente un nuovo nome di file come prova di indipendenza: due mesh possono rappresentare la stessa area fisica.

## Costruire il confronto prima di ottimizzare

Prima di fissare la baseline consultare il [registro della community](06-ricerca-community.md): valutazione per regioni, integrità dei dati, riproducibilità e controlli geometrici possono riusare contributi esistenti. Collegare ogni idea candidata all'ID della fonte e alla prova che ne misurerà il vantaggio.

1. Identificare un piccolo gruppo di esempi con annotazioni attendibili e registrarne origine, scala e regioni fisiche. Una zona senza annotazioni può essere sconosciuta, non necessariamente priva di inchiostro.
2. Distinguere dati di sviluppo e dati finali di verifica. Conservare separatamente regioni realmente escluse dal training di tutti i checkpoint valutati, controllando i manifest ufficiali. Se non riusciamo a dimostrarlo, chiamare la prova controllo operativo e non benchmark indipendente.
3. Evitare che crop vicini, scansioni dello stesso tratto o patch sovrapposte finiscano in gruppi diversi. Preferire divisioni per segmento o rotolo e verificare le coordinate; per il training prevedere anche distanza fra regioni rispetto al campo osservato dal modello.
4. Salvare la procedura iniziale di riferimento, detta baseline: versioni, input, normalizzazione, scale fisiche, direzione e profondità, modello, seed e parametri.
5. Definire una sola domanda per esperimento. Esempio: cambiare la profondità campionata aumenta i tratti corretti mantenendo lo stesso budget? Confrontare A e B sugli stessi casi, mantenendo costanti le altre impostazioni.
6. Scegliere le impostazioni sui dati di sviluppo e congelarle prima della verifica finale. Ogni modifica suggerita dal test finale richiede un nuovo test indipendente.

## Che cosa misurare

- **Qualità della superficie:** continuità del foglio nelle sezioni, salti di strato osservati, distorsione e area valida. Una scatola rettangolare piena di buchi non corrisponde ad altrettanta superficie utile.
- **Recupero dell'inchiostro:** precisione (quanti punti segnalati sono corretti) e richiamo (quanti punti veri recuperiamo), soltanto dove il riferimento è affidabile. Riportare i risultati per segmento, non solo una media globale.
- **Utilità della selezione:** a parità di numero di finestre guardate, quanti casi utili si trovano? Confrontare ScrollScout con selezione casuale ripetuta e un ordinamento semplice per segnale medio; evitare finestre quasi identiche contate più volte.
- **Falsi allarmi:** controlli sintetici e zone di fondo verificate. Rumore e strisce artificiali sono controlli supplementari, non sostituiscono papiri reali.
- **Risorse:** minuti umani, tempo totale, tempo della sessione GPU, memoria massima, spazio e GB scaricati. Distinguere esecuzione iniziale e ripetizione con cache già presente.
- **Ripetibilità:** il socio ripete dai file e dalle istruzioni salvate. Definire la tolleranza numerica se hardware diversi non producono file identici.

La leggibilità delle lettere richiede una valutazione distinta dalle metriche dei pixel. Su pochi casi presentare numeri grezzi e limiti, senza trasformarli in stime affidabili per tutta la biblioteca.

## Ordine degli esperimenti proposto

| ID | Esperimento | Condizione per proseguire |
|---|---|---|
| E00 | Piccolo campione noto, ambiente e output salvati | Output coerente col riferimento, provenienza e tempi registrati |
| E01 | Ripetizione di E00 da parte del socio | Istruzioni sufficienti e differenze spiegate |
| E02 | Congelare campioni, riferimenti e separazione sviluppo/test | Nessuna indipendenza presunta; limiti espliciti |
| E03 | Qualità della mesh e confronto di pochi offset/direzioni | Evidenza utile sui dati di sviluppo, costo entro budget |
| E04 | Valutare il beneficio di seed/checkpoint multipli e del ranking | Confronto con baseline a uguale costo, anche se l'esito è negativo |
| E05 | Valutazione finale della configurazione scelta | Risultati su dati lasciati fuori dalle scelte |
| E06 | Piccola ricerca su un volume eleggibile scelto | Candidati tracciabili, controlli di geometria e revisione indipendente |

Non lanciare subito il prodotto di tutte le combinazioni: molti tentativi aumentano anche la probabilità di trovare rumore apparentemente convincente. Selezionare una variabile per volta nelle prime prove e registrare anche le esecuzioni scartate.

## Un candidato non è ancora una scoperta

Conservare dati originali e posizione, ricostruire di nuovo il risultato, verificare geometria, scala e stabilità. Chiedere al secondo membro del team un esame senza anticipare quali lettere ci si aspetta. Due seed condividono architettura e dati: cercare, dove possibile, riscontri con errori differenti.

Per la submission ricontrollare il regolamento corrente e predisporre il pacchetto richiesto. Non usare un modello linguistico per completare tratti mancanti e poi presentare quel completamento come segnale misurato. Le immagini di visualizzazione devono restare distinguibili dalle predizioni originali.

Ogni esecuzione avrà una [scheda](templates/esperimento.md). Nessuna riga della tabella sopra è già completata.
