# Strumenti e setup

Proposta iniziale, non installazione completata. Inventario del 5 settembre 2026: PC Windows di Matteo, 16 GiB RAM, Intel UHD Graphics, circa 29 GiB liberi sul disco C; Git e GitHub CLI disponibili. Mac M3 Pro dichiarato dal socio: memoria, spazio, software e prestazioni ancora da verificare.

## Dove fare cosa

| Strumento / luogo | Funzione | Primo utilizzo previsto |
|---|---|---|
| Git e repository GitHub privato | Storia comune di documenti, codice e risultati piccoli | Leggere e aggiornare il progetto |
| Browser e Data Browser | Esaminare esempi e disponibilità dei dati | Comprendere l'oggetto e scegliere un campione |
| VC3D sul PC o Mac | Vedere e ricostruire superfici | Aprire un esempio e controllare un segmento |
| Kaggle | Computer remoto con GPU NVIDIA | Applicare un modello esistente a un piccolo campione |
| villa / vesuvius | Software ufficiale per i dati e i modelli | Eseguire la procedura di riferimento |
| Hugging Face | Distribuzione dei modelli | Recuperare checkpoint versionati |
| ScrollScout, eventuale | Ordinare zone promettenti su CPU | Confrontarlo con metodi più semplici |
| Discord della Challenge | Aggiornamenti e chiarimenti dagli organizzatori | Leggere regole e discussioni pertinenti |

VC3D documenta pacchetti per Windows e Apple Silicon. La procedura ufficiale dei modelli assume Linux e NVIDIA/CUDA. Per il primo percorso useremo Kaggle; farla funzionare sulla GPU Apple richiederebbe una verifica distinta di compatibilità e prestazioni. Il Mac può comunque servire per visualizzazione, codice e analisi CPU. [VC3D](https://scrollprize.org/tutorial_VC3D), [modelli](https://scrollprize.org/tutorial5).

## Ordine del setup

1. Leggere la guida introduttiva e concordare il primo esperimento.
2. Verificare gli account individuali GitHub, Kaggle e Discord. Invitare il socio al repository solo quando Matteo indica l'account corretto e richiede l'invito.
3. Sul Mac scegliere una cartella di sviluppo fuori da iCloud Drive e clonare il repository. Ogni persona mantiene la propria copia; GitHub scambia i commit.
4. Installare una release identificabile di VC3D, annotando versione e piattaforma; aprire un campione piccolo su ciascuna macchina. Registrare tempi, memoria e spazio.
5. Preparare su Kaggle un notebook privato, fissando la versione di villa e dei checkpoint. Verificare l'accesso alla GPU e salvare gli output alla fine della sessione.
6. Riprodurre un controllo noto prima di cercare testo nuovo.

Per il socio, dopo aver ricevuto accesso e dalla cartella di sviluppo scelta:

```sh
git clone https://github.com/asap-matts/papyrus-lab.git
cd papyrus-lab
git status --short --branch
git rev-parse HEAD
```

La presenza della stessa versione su GitHub non verifica automaticamente il setup del Mac: serve eseguire una prova anche lì. Per lavorare contemporaneamente, assegnare parti distinte e branch separati. Concordare un responsabile per ciascuna modifica ai file comuni.

## Limiti pratici proposti

Per la prima prova: campione con input previsto inferiore a 1 GB, al massimo 2 GB aggiuntivi locali fra download e cache, tetto di 30 minuti di sessione GPU, nessuna spesa. Sono limiti di progetto da confermare nel piano eseguibile, non prestazioni promesse. Se non bastano, registrare dove si è fermata la prova e rivedere il piano.

Kaggle documenta una quota GPU settimanale generalmente di 30 ore, dipendente dalle risorse. Leggere il contatore effettivo prima di una sessione. [Gestione GPU Kaggle](https://www.kaggle.com/docs/efficient-gpu-usage).

Il repository ignora data/, cache/, checkpoints/, runs/ e outputs/. Non salvare in Git volumi o modelli. Per trasferirli fra le macchine servirà una scelta esplicita di storage o una procedura di download ripetibile; GitHub da solo non sincronizza questi dati.
