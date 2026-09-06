# Strumenti e setup

Proposta iniziale, non installazione completata. Inventario del 5 settembre 2026 del portatile di Matteo: Windows, 16 GiB RAM, Intel UHD Graphics, circa 29 GiB liberi sul disco C; Git e GitHub CLI disponibili. Mac M3 Pro dichiarato dal socio: memoria, spazio, software e prestazioni ancora da verificare.

Inventario del **PC fisso** di Matteo, rilevato direttamente il 6 settembre 2026 (non più dichiarato):

| Componente | Rilevato |
|---|---|
| Sistema | Windows 11 Pro 26200, con **WSL2 e Ubuntu già installati** |
| CPU | Intel Core i7-12700K, 12 core / 20 thread |
| RAM | 31,7 GiB |
| GPU | NVIDIA GeForce **GTX 1060 6 GB** (6.144 MiB), driver 581.57, compute capability 6.1 (architettura Pascal, 2016) |
| Disco | Samsung 980 PRO NVMe 1 TB, **681 GB liberi** |

Il fisso è oggi la macchina migliore del team per scrivere, per i controlli su CPU (leggere la label, verificare gli hash, confrontare output e label) e per conservare i dati. Per l'inferenza GPU va trattato con cautela: la GTX 1060 non ha unità dedicate al calcolo in mezza precisione (il modello lavora in fp16, che su Pascal è lento), e CUDA 12.8 classifica Pascal come deprecato; non è certo che le build recenti di PyTorch la supportino. Serve un preflight dedicato, come per Kaggle, prima di inserirla in un piano. WSL2 permette invece di eseguire la pipeline ufficiale in ambiente Linux senza adattamenti. Nessun accesso remoto configurato.

Account Kaggle e verifica telefonica completati da Matteo: il 5 settembre 2026 il browser ha mostrato Phone verification: Verified e consumo iniziale 00:00 su 30 ore GPU e 20 ore TPU. Il successivo [preflight Kaggle](reports/2026-09-05-kaggle-preflight.md) ha assegnato due Tesla T4 da 14,56 GiB rilevati ciascuna e PyTorch 2.10.0 ha riconosciuto CUDA 12.8. La sessione è stata fermata subito dopo la prova. Prima inferenza dei modelli ancora da eseguire su Kaggle; il fisso è la macchina per preparazione, controlli CPU e conservazione dei dati. I 6 GB di VRAM della GTX 1060 potrebbero bastare a un'inferenza con batch ridotto, ma compatibilità e velocità vanno misurate in un preflight dedicato, dopo il primo riferimento riuscito su Kaggle.

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
| Fisso: i7-12700K, 32 GB, GTX 1060 6 GB, NVMe 1 TB (681 GB liberi), WSL2 | Scrittura, preparazione dati, geometria, controlli CPU e conservazione; eventuale inferenza ridotta | Preflight GPU dedicato: supporto Pascal nelle build PyTorch correnti e tempo per campione |
| Mac M3 Pro | Visualizzazione, controllo indipendente e analisi | Memoria, spazio e prestazioni reali |
| Kaggle GPU | Prima inferenza del modello, poi confronto con il fisso | Preflight riuscito su due Tesla T4; compatibilità della pipeline e inferenza ancora da provare |

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
4. Preparare la prima inferenza su Kaggle con un campione già renderizzato; l'accesso GPU è verificato, ma occorre ancora fissare versione di villa e checkpoint e salvare gli output. Riprodurre un controllo noto prima di cercare testo nuovo. Questo passaggio può iniziare senza aspettare il clone del socio o VC3D.
5. Installare in seguito una release identificabile di VC3D per il lavoro sulle superfici, annotando versione e piattaforma; aprire un campione piccolo. Registrare tempi, memoria e spazio.
6. Successivamente, dopo un preflight che verifichi che PyTorch riconosca la GTX 1060, ripetere il campione sul fisso con un carico compatibile con 6 GB di VRAM. WSL2 con Ubuntu è già presente: la pipeline ufficiale, pensata per Linux, può girarci senza adattamenti Windows; lì `uv run` è la scelta naturale perché l'ambiente persiste.

Per il socio, dopo aver ricevuto accesso e dalla cartella di sviluppo scelta:

```sh
git clone https://github.com/asap-matts/papyrus-lab.git
cd papyrus-lab
git status --short --branch
git rev-parse HEAD
```

La presenza della stessa versione su GitHub non verifica automaticamente il setup del Mac: serve eseguire una prova anche lì. Per lavorare contemporaneamente, assegnare parti distinte e branch separati. Concordare un responsabile per ciascuna modifica ai file comuni.

## Limiti pratici proposti

Per la prima prova: campione con input previsto inferiore a 1 GiB, tetto di 30 minuti di sessione GPU, nessuna spesa. Il limite di spazio locale, inizialmente 2 GB, è stato alzato a **10 GB** per decisione di Matteo del 6 settembre 2026: la revisione ha misurato che il solo ambiente costruito da `uv run` dalla ricetta ufficiale pesa circa 4,3 GiB (di cui 3,8 GiB per PyTorch e le librerie CUDA), e il checkout completo di villa circa 0,97 GiB. Su Kaggle si evita comunque `uv run` (vedi [dossier E00](08-dossier-input-e00.md)) perché l'ambiente si azzera a ogni sessione e il download si ripeterebbe. Sono limiti di progetto da confermare nel piano eseguibile, non prestazioni promesse. Se non bastano, registrare dove si è fermata la prova e rivedere il piano.

Kaggle documenta una quota GPU settimanale generalmente di 30 ore, dipendente dalle risorse. Leggere il contatore effettivo prima di una sessione. [Gestione GPU Kaggle](https://www.kaggle.com/docs/efficient-gpu-usage).

Il repository ignora data/, cache/, checkpoints/, runs/ e outputs/. Non salvare in Git volumi o modelli. Per trasferirli fra le macchine servirà una scelta esplicita di storage o una procedura di download ripetibile; GitHub da solo non sincronizza questi dati.

## Primo accesso a Kaggle

1. Aprire il [sito Kaggle](https://www.kaggle.com/). L'account e il login sono già stati verificati nella sessione del 5 settembre 2026.
2. Verifica telefonica già completata personalmente da Matteo e confermata nell'interfaccia. Non riportare password o codici SMS nei documenti del progetto.
3. È stato creato il notebook Python privato `papyruslab-e00-preflight`. Un notebook è una pagina con blocchi di codice eseguibili su un computer remoto.
4. Nel preflight è stato selezionato `GPU T4 x2`, PyTorch ha rilevato entrambe le GPU e la sessione è stata poi arrestata. La configurazione può restare selezionata senza consumare quota quando la sessione è spenta; controllare comunque il contatore e lo stato prima di ogni esecuzione.

La verifica telefonica è conclusa. La distinta verifica d'identità Persona non è stata avviata: la pagina la collega alle competizioni che la richiedono. L'accesso GPU effettivo è verificato nel solo preflight; la pipeline Vesuvius non lo è. Risultati e limiti sono nel [rapporto dedicato](reports/2026-09-05-kaggle-preflight.md).
