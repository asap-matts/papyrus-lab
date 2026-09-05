# ScrollScout: che cosa prendiamo e come lo verifichiamo

**Stato: sintesi di ricerca e proposta di test.** ScrollScout è il progetto pubblico indipendente di Francesco. Il nostro team può usarlo come riferimento e collaborare secondo regole pubbliche, ma non lo considera già parte del proprio codice o una prova definitiva.

## L'idea in parole semplici

La pipeline non legge automaticamente le lettere. Prima un modello di *ink detection* produce un'immagine in cui ogni punto rappresenta quanto il modello ritiene plausibile l'inchiostro. ScrollScout prende questa immagine, divide la superficie in finestre e dà priorità alle zone che assomigliano alla scrittura: righe ripetute, orientamento coerente e tracce compatibili con tratti.

Il risultato è quindi un **ordinatore di zone da guardare**, non una trascrizione e non un certificato che il testo esista. La fase costosa rimane la ricostruzione della superficie e l'inferenza GPU; il ranking e molti controlli possono girare sulla CPU.

## Che cosa è utile nell'aggiornamento di Francesco

- Usare due seed dello stesso modello e confrontare le mappe: se indicano la stessa regione, il candidato è più interessante; se divergono, va trattato come incerto.
- Misurare la periodicità delle righe insieme allo score, invece di ordinare solo per luminosità o quantità di pixel.
- Tenere le finestre non sovrapposte nel gruppo presentato a una persona: otto copie quasi uguali non sono otto evidenze indipendenti.
- Registrare anche i risultati negativi e il costo della prova. Un negativo circoscritto è informativo se sappiamo quali segmenti, profondità, seed e checkpoint sono stati provati.

Queste sono buone euristiche operative. Non sono ancora una garanzia statistica: seed diversi possono condividere gli stessi errori, e un modello addestrato su rotoli diversi può fallire in modo sistematico su un nuovo rotolo.

## Tre precisazioni da non perdere

1. Un valore come `0,98` è uno score interno del ranking, non una probabilità del 98% che ci siano lettere. Al commit `29656e3b8455572dded5ed4a13ddfa974dac1a5e`, il README descrive ancora più segnali pesati, ma i pesi predefiniti in `scrollscout/letterness.py` fanno votare soltanto la periodicità, con un filtro sulla copertura d'inchiostro. Per replicare uno score dovremo registrare versione e parametri realmente eseguiti.
2. La finestra di 10 mm per lato copre circa 1 cm². Il premio First Letters richiede invece dieci lettere entro una singola area di 4 cm² e chiede un pacchetto di evidenze specifico. Sono due scale utili ma diverse; non bisogna scegliere una soglia del detector solo perché coincide con il regolamento.
3. `period` indica quanto è forte il segnale di periodicità nel modello di scoring. Il passo di riga espresso in millimetri è una misura separata e va controllato sul singolo rotolo; non esiste un passo universale valido per tutti i copisti.

La nota storica `validation_w035.md` (v0.3) riporta score migliori circa 0,92–0,93. Le note successive `pherc1447_predictions.md` e `results.md` riportano 0,97–0,99 sul positivo e concordanza Spearman 0,778, contro 0,163–0,370 nei tre segmenti di PHerc. 1447. Versioni e configurazioni diverse non vanno fuse in un unico confronto. Il messaggio più recente di Francesco è coerente con l'intervallo di score delle note successive; l'immagine menzionata nel messaggio non è stata ricevuta né valutata. Tutti questi risultati sono dell'autore, ancora da replicare nel nostro team.

## Il nostro test minimo, prima di cercare un rotolo nuovo

1. **Congelare una baseline:** versione di `vesuvius`, checkpoint `ink_9um`, seed, direzione, profondità, dimensione e passo delle finestre, normalizzazione e versione di ScrollScout.
2. **Controllare un positivo noto:** w035 di PHerc. 0139 è utile per capire se dati, modello e orientamento sono collegati correttamente, ma appartiene al training set di `ink_9um`; non misura la generalizzazione.
3. **Aggiungere controlli e confronti semplici:** usare predizioni sulle regioni di fondo annotate come attendibili, prodotte con la stessa pipeline del positivo, e confrontare il ranking con selezione casuale ripetuta e segnale medio. Zone senza testo rilevato ma prive di riferimento restano sconosciute. Render grezzi e rumore sintetico sono prove supplementari; confrontare solo predizioni positive con render negativi confonderebbe presenza di testo e tipo di immagine.
4. **Confrontare i seed a costo uguale:** salvare correlazione delle mappe, sovrapposizione del decile superiore e posizione del primo candidato. Non trasformare il disaccordo in una probabilità finché non avremo esempi etichettati indipendentemente.
5. **Separare sviluppo e verifica:** decidere soglie e finestra sui casi di sviluppo; lasciare segmenti o regioni fisiche intere fuori dalle scelte. Crop vicini della stessa superficie non sono test indipendenti.
6. **Solo dopo fare una piccola esplorazione:** mantenere le predizioni grezze, la geometria della superficie, i manifest e una revisione cieca di Matteo e del socio. Un candidato interessante richiede un secondo controllo, una scala fisica verificabile e, per un premio, il pacchetto richiesto dal regolamento corrente.

Per il filone ScrollScout proponiamo di misurare quanto il ranking migliori la selezione e quante regioni con scrittura debole scarti. Finestre da 10, 15 e 20 mm sono possibili varianti da confrontare sui dati di sviluppo; il protocollo e il budget vanno fissati prima della prova. La periodicità può perdere lettere isolate o poche righe: mantenere anche una quota di esame delle zone poco segnalate. Le priorità dell'intero progetto saranno confrontate con gli altri contributi nella [ricerca sulla community](06-ricerca-community.md).

Fonti: [repository pubblico ScrollScout](https://github.com/FrankTheRope/scrollscout), [validazione w035](https://github.com/FrankTheRope/scrollscout/blob/main/docs/validation_w035.md), [analisi PHerc. 1447](https://github.com/FrankTheRope/scrollscout/blob/main/docs/pherc1447_predictions.md), [tutorial ufficiale ink_9um](https://scrollprize.org/tutorial5), [premio First Letters](https://scrollprize.org/prizes).
