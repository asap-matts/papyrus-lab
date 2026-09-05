# Strumenti e setup

Proposta iniziale, non installazione completata. Inventario del 5 settembre 2026: PC Windows di Matteo, 16 GiB RAM, Intel UHD Graphics, circa 29 GiB liberi sul disco C; Git e GitHub CLI disponibili. Mac M3 Pro dichiarato dal socio: memoria, spazio, software e prestazioni ancora da verificare.

Matteo dispone anche di un PC fisso, dichiarato con 32 GB di RAM, GPU NVIDIA da circa 6 GB di memoria video, CPU probabilmente Intel i7 multicore e SSD NVMe da 1 TB. Modelli esatti, sistema operativo e spazio effettivamente libero non sono ancora verificati. La capacità nominale del disco non equivale allo spazio disponibile. Non è stato configurato alcun accesso remoto.

Account Kaggle e verifica telefonica completati da Matteo: il 5 settembre 2026 il browser mostra Phone verification: Verified e consumo 00:00 su 30 ore GPU e 20 ore TPU. L'assegnazione effettiva di una GPU e il funzionamento di PyTorch restano da provare nel primo notebook. Prima prova dei modelli proposta su Kaggle; il fisso è candidato alla preparazione e conservazione dei dati. I circa 6 GB di VRAM potrebbero consentire inferenze ridotte, da misurare dopo il primo riferimento riuscito. Matteo fornirà l'inventario quando userà il fisso; questo non blocca la preparazione su Kaggle dal portatile.

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

VC3D documenta pacchetti per Windows e Apple Silicon. La procedura ufficiale dei modelli assume Linux e NVIDIA/CUDA. Kaggle è un'opzione iniziale; il fisso può diventare la macchina principale per i modelli se la GPU è compatibile e supera la prova. [VC3D](https://scrollprize.org/tutorial_VC3D), [modelli](https://scrollprize.org/tutorial5).

La GPU Apple può accelerare software predisposto tramite Metal/MPS, ma questo non dimostra che la specifica pipeline Vesuvius sia compatibile senza adattamenti. Visualizzazione, codice e analisi locale restano utilizzi previsti per il Mac. [Supporto PyTorch su Mac](https://developer.apple.com/metal/pytorch/).

## CPU, RAM e GPU in parole semplici

- La **CPU** è il processore generale: prepara dati, esegue analisi e molte operazioni geometriche. Un buon processore può aiutare anche mentre la GPU lavora, rifornendola di dati.
- La **RAM** è lo spazio di lavoro della macchina. I 32 GB del fisso aiutano a gestire dati più grandi rispetto al portatile, ma non consentono di caricare un intero volume di molti terabyte.
- La **GPU** esegue rapidamente molti calcoli simili, come quelli dei modelli neurali. Con una scheda dedicata ha una propria memoria, detta **VRAM**: i 32 GB di RAM del PC non sono 32 GB di VRAM.
- Sul Mac Apple Silicon CPU e GPU condividono memoria; capacità totale e compatibilità software vanno valutate insieme. Non equiparare automaticamente memoria unificata e VRAM NVIDIA per stimare se una prova funzionerà.

## Proposta di distribuzione del lavoro

| Risorsa | Impiego iniziale | Decisione ancora da verificare |
|---|---|---|
| Portatile attuale | Documenti, codice, esame di immagini e piccoli campioni | Prestazioni di VC3D su un campione |
| Fisso 32 GB, NVIDIA circa 6 GB, NVMe 1 TB | Preparazione dati, geometria e conservazione dei dati; possibile inferenza ridotta | Modelli esatti, driver, spazio libero e tempo per campione |
| Mac M3 Pro | Visualizzazione, controllo indipendente e analisi | Memoria, spazio e prestazioni reali |
| Kaggle GPU | Prima inferenza del modello, poi confronto con il fisso | Telefono verificato; assegnazione GPU e funzionamento ancora da provare |

Le macchine non sommano automaticamente potenza o memoria. Distribuiremo inizialmente prove indipendenti, ciascuna con input, configurazione e risultati identificabili. Una coda di lavori remoti e un server condiviso potranno essere utili dopo aver stabilizzato una singola esecuzione.

## Come scegliere fra fisso e Kaggle

Prima identificare la GPU del fisso: Gestione attività → Prestazioni → GPU su Windows. Annotare nome e capacità totale della memoria dedicata; per CPU annotare nome, core e processori logici. Se NVIDIA e nvidia-smi è già disponibile, il comando seguente legge modello, memoria totale e driver senza installare software:

```sh
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

Il successo di questo comando non certifica la compatibilità della libreria ML: occorre poi verificare che PyTorch veda la GPU e completare il campione.

Confronto proposto: stesso campione, checkpoint e configurazione sul fisso e su Kaggle. Misurare tempo di preparazione, tempo di inferenza, picco di memoria e qualità dell'output; distinguere il primo avvio dalle ripetizioni con i dati già scaricati. Se serve un batch più piccolo per una macchina, registrare la differenza. L'obiettivo è scegliere dove lavorare con meno attese e risultati equivalenti, senza presumere che il cloud sia più veloce.

Il fisso evita le quote di sessione di Kaggle, ma occupa la macchina e consuma energia. Kaggle evita acquisti hardware, ma ha quote, disponibilità variabile e richiede di salvare gli artefatti delle sessioni. Non è necessario acquistare componenti prima della prova.

## Ordine del setup

1. Leggere la guida introduttiva e concordare il primo esperimento.
2. Account Kaggle di Matteo verificato. Restano gli account del socio e Discord; invitare il socio al repository quando Matteo indica l'account corretto e richiede l'invito.
3. Sul Mac scegliere una cartella di sviluppo fuori da iCloud Drive e clonare il repository. Ogni persona mantiene la propria copia; GitHub scambia i commit.
4. Preparare la prima inferenza su Kaggle con un campione già renderizzato; fissare versione di villa e checkpoint, verificare l'accesso alla GPU e salvare gli output. Riprodurre un controllo noto prima di cercare testo nuovo. Questo passaggio può iniziare senza aspettare il clone del socio o VC3D.
5. Installare in seguito una release identificabile di VC3D per il lavoro sulle superfici, annotando versione e piattaforma; aprire un campione piccolo. Registrare tempi, memoria e spazio.
6. Successivamente ripetere il campione sul fisso con un carico compatibile con i circa 6 GB dichiarati. Per Windows la guida ufficiale suggerisce WSL2 per questa pipeline; l'installazione andrà verificata sul fisso.

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

## Primo accesso a Kaggle

1. Aprire il [sito Kaggle](https://www.kaggle.com/). L'account e il login sono già stati verificati nella sessione del 5 settembre 2026.
2. Verifica telefonica già completata personalmente da Matteo e confermata nell'interfaccia. Non riportare password o codici SMS nei documenti del progetto.
3. Aprire un nuovo notebook Python da Code / New Notebook. Un notebook è una pagina con blocchi di codice eseguibili su un computer remoto. Verificare che resti privato.
4. Lasciare inizialmente Accelerator su None: prima controllare quali GPU sono disponibili e la quota assegnata, poi preparare la prova. L'attivazione GPU avverrà quando saremo pronti a eseguirla.

La verifica telefonica è conclusa. La distinta verifica d'identità Persona non è stata avviata: la pagina la collega alle competizioni che la richiedono. L'accesso GPU effettivo verrà verificato nel notebook. Nessuna sessione GPU è stata avviata durante il consolidamento documentale.
