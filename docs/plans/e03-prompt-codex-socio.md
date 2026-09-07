# Prompt per il Codex del socio — E03, procedura unica S1 → S2 → S3

Questo file contiene **tutto** ciò che Matteo deve mandare al socio: le tre righe di istruzioni per la persona e, sotto, il blocco da incollare in Codex. Codex esegue l'intera procedura da solo, dalla preparazione dell'ambiente alla consegna: il socio non lancia comandi. L'unica azione che può toccare al socio è un login GitHub nel browser, se Codex glielo chiede.

**Prima di consegnare:** verificare che l'intestazione di [2026-09-07-e03-compiti-socio.md](2026-09-07-e03-compiti-socio.md) riporti il commit di partenza e che il branch `e03-socio` sul remoto abbia quel commit in testa (fatto il 7 settembre 2026).

---

## Istruzioni per il socio (da mandare insieme al blocco)

1. Apri Codex. Come modello scegli **GPT-5.6 Sol**. Come cartella di lavoro apri `~/dev/papyrus-lab` (quella di E02); se non esiste più, apri la tua cartella home: Codex la ricreerà.
2. Incolla per intero il blocco di testo qui sotto e invia. Codex farà tutto da solo, anche i download e i calcoli; può servire qualche ora e più di un turno. Se si ferma dicendo cosa ha fatto e cosa manca, scrivigli **continua**.
3. Se Codex ti chiede di fare il login su GitHub, apri il Terminale, scrivi `gh auth login`, scegli GitHub.com, HTTPS, login nel browser, completa nel browser, poi torna su Codex e scrivi **continua**. È l'unica cosa che potrebbe chiederti.
4. Alla fine Codex stampa un blocco che comincia con `RIEPILOGO E03 SOCIO`. Copialo e mandalo a Matteo così com'è. Se Codex si ferma per qualunque altro motivo, manda a Matteo quello che ha scritto, senza provare a sistemare.

---

## Blocco da incollare in Codex

```text
Sei l'esecutore dei compiti S1, S2 e S3 di E03 per PapyrusLab, un progetto di ricerca sulla Vesuvius Challenge.
Lavori per il socio di Matteo, che non e' tecnico e non eseguira' alcun comando: fai tutto tu, dalla preparazione
dell'ambiente alla consegna, chiedendogli qualcosa soltanto se davvero non puoi fare altrimenti (vedi FASE 0).
Rispondi in italiano. Procedi in autonomia, passo dopo passo, senza chiedere conferme intermedie.

===================================================================================================
FASE 0 — PREPARAZIONE DELL'AMBIENTE (la fai tu; unica eccezione: il login GitHub nel browser)
===================================================================================================
0.1 Se la cartella ~/dev/papyrus-lab/.git NON esiste:
    - esegui `gh auth status`. Se dice che non sei autenticato, FERMATI e scrivi al socio, testualmente:
        "Apri il Terminale e scrivi: gh auth login  (GitHub.com, HTTPS, login nel browser). Quando hai finito, scrivimi: continua"
      Quando il socio scrive "continua", riesegui `gh auth status` e prosegui solo se autenticato.
    - poi esegui: `gh repo clone asap-matts/papyrus-lab ~/dev/papyrus-lab`
0.2 Esegui:  `bash ~/dev/papyrus-lab/scripts/e03_bootstrap_mac.sh`
    Lo script mette il repository sul branch e03-socio al commit giusto, controlla Python e crea l'ambiente .venv.
    Leggi il suo output:
    - se stampa una riga "DA FARE" con `gh auth login`: fai come al punto 0.1, poi rilancia lo script;
    - se stampa una riga "DA FARE" con `brew install python@3.12`: esegui tu `brew install python@3.12`, poi rilancia;
    - se stampa una riga "STOP": fermati, riporta al socio il testo esatto della riga e digli di mandarlo a Matteo.
      Non aggirare lo stop.
    - se stampa "Tutto pronto": prosegui.
0.3 Da qui in avanti lavora dentro ~/dev/papyrus-lab. Verifica e stampa:
      git branch --show-current      -> deve essere e03-socio
      git status --short             -> deve essere vuoto
      git log -1 --format=%s         -> deve coincidere con il messaggio scritto nella riga "Commit di partenza"
                                        del file docs/plans/2026-09-07-e03-compiti-socio.md
    Se una delle tre non coincide, fermati e riporta.

===================================================================================================
FASE 1 — LETTURA (prima di qualunque comando dei compiti)
===================================================================================================
Leggi per intero, in quest'ordine:
  1. AGENTS.md
  2. docs/plans/2026-09-07-e03-compiti-socio.md     <- e' il tuo piano: contiene i comandi esatti di ogni passo
  3. docs/07-procedura-operativa.md
  4. SOLO la sezione "5. Criterio di esito, deciso prima della prova" di docs/plans/2026-09-07-e03-tolleranza-offset-z.md
     (ti serve per S3: contiene le definizioni di Delta, tolleranza, H1, H2, regola di anomalia e controlli)

NON aprire, in nessun momento prima della consegna:
  - docs/reports/e03-r01/metrics/curve.json
  - qualunque file docs/reports/*e03-r01*.md o *e03-r01*manifest*
  - scripts/e03_curve.py
  - le cartelle runs/ diverse da runs/E03-SOCIO
  - il resto di docs/plans/2026-09-07-e03-tolleranza-offset-z.md oltre alla sezione 5
Il valore del tuo lavoro sta nell'essere indipendente: se leggi l'analisi del team, il compito S3 non vale piu' nulla.
Non toccare, leggere o nominare pherc1667-w029: e' un segmento sigillato del progetto.

===================================================================================================
FASE 2 — ESECUZIONE, NELL'ORDINE S1 -> S2 -> S3 (piano, passi 1-12)
===================================================================================================
Segui i passi del piano docs/plans/2026-09-07-e03-compiti-socio.md nell'ordine, usando i comandi che contiene,
senza saltarne ne' aggiungerne. Usa sempre .venv/bin/python per i comandi Python. Ogni "Fatto quando" del piano
va verificato con l'output reale del comando, non presunto. In sintesi:

  Passo 1 (verifica dello stato): come al punto 0.3, piu' `.venv/bin/python -m pytest tests/ -q`.
          Registra macOS, Python, git, gh per i rapporti.

  S1 — VERIFICA DI NOVITA' (passi 2-5, circa 2-3 ore, solo rete)
       Domanda: qualcuno ha gia' pubblicato una misura di quanto i modelli di ink detection di villa (in particolare
       ink_9um) perdono quando si sposta la finestra Z / le slice in profondita', su dati con etichette tenute fuori
       dal training?
       Esegui le query con `gh api` e `curl` esattamente come scritte nel piano, salvando le risposte in
       runs/E03-SOCIO/s1/. Se una query non risponde (limite di frequenza, 403, endpoint cambiato), NON insistere
       oltre due tentativi: registrala come ostacolo e prosegui con le altre. Poi scrivi il rapporto S1 e il JSON
       delle fonti come descritto al passo 5: per ogni fonte pertinente URL, data o revisione, cosa misura, e se e'
       confrontabile con una curva AUROC(offset) su pixel held-out (si' / parziale / no). Il verdetto deve essere una
       di tre formule: "trovato equivalente", "trovato lavoro parziale", "non trovato nelle fonti consultate".
       Non scrivere mai che una cosa "non esiste": puoi dire solo che non l'hai trovata, e dove hai cercato.

  S2 — POOLING SPOSTATO INDIPENDENTE (passi 6-9, circa 1 ora, 1,6 GB di rete)
       Tre pooling di pherc0814-46527 con scripts/e03_pool_shifted.py (--z-start 13, poi 1, poi 25), impronte con
       scripts/tree_sha256.py, uguaglianza slice a slice fra spostati e non spostato (script del passo 8).
       L'impronta a --z-start 13 DEVE essere esattamente:
           bc7423431221bf24b247a8ba80d264b0306f816c52b4ecc0d08115a82305ac52
       Se differisce, FERMATI dopo aver scritto il rapporto S2 con l'impronta ottenuta: e' un P0 da segnalare subito.
       Se la rete si interrompe (ServerDisconnectedError, 5xx), cancella la cartella .partial e rilancia quel
       pooling: fino a tre tentativi, poi registra e prosegui. Non modificare lo script.
       Il pooling di pherc0139-w016 e' FACOLTATIVO: fallo solo se hai gia' finito tutto il resto e la rete regge
       (5,6 GB per ciascuno dei due pooling).

  S3 — RICALCOLO IN CIECO DELLA CURVA (passi 10-12, circa 1-2 ore, CPU)
       Scrivi uno script TUO, scripts/socio/e03_socio_curve.py (cartella nuova), che legge SOLO i JSON in
       docs/reports/e03-r01/metrics/ elencati al passo 10 del piano (mai curve.json) e ricostruisce, applicando
       alla lettera le definizioni della sezione 5 C del piano madre:
         1. la tabella AUROC held-out per offset k in {-5,-3,-2,0,+2,+3,+5} e per le quattro combinazioni
            (segmento x seed), e la stessa tabella per la F1 alla soglia 91;
         2. le differenze Delta rispetto all'offset zero DELLO STESSO seed, e la loro media sui due segmenti;
         3. la tolleranza per seed e per verso (regola: primo |k| fra 2, 3, 5 con perdita media <= -0,05), scrivendo
            "nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati" quando non c'e';
            riporta la tolleranza anche per singolo segmento;
         4. H1: tutte le |Delta| a +-2 sono <= 0,02? quali no e di quanto;
         5. H2: la perdita media cresce passando da +-2 a +-3 a +-5, per seed e verso? dove si' e dove no;
         6. regola di anomalia: esiste un k diverso da 0 con Delta >= +0,02 su TUTTE e quattro le combinazioni?
         7. i due controlli: media dei seed (file *_seedmean.json) contro ciascuno dei due seed a offset 0, e media
            delle finestre -2/+2 (file *_zmean_m2p2.json) contro l'offset 0 dello stesso seed: "aiuta" solo se
            migliora su entrambi i segmenti senza peggiorare oltre 0,01 su nessuno.
       Lo script deve essere deterministico e non usare la rete. Scrivi poi il rapporto S3 con le tabelle, i verdetti
       e una sezione "ambiguita'": ogni punto in cui la regola ti e' sembrata interpretabile in piu' modi (pareggi,
       valori mancanti, arrotondamenti, segni) e la scelta che hai fatto. Quella sezione e' la parte piu' utile.
       Se un file manca, scrivilo: non stimare mai un valore.

===================================================================================================
FASE 3 — CONSEGNA (piano, passo 13)
===================================================================================================
3.1 `git status --short` deve mostrare SOLO i file nuovi elencati nella sezione 3 del piano (i tre rapporti .md,
    il JSON delle fonti di S1, scripts/socio/e03_socio_curve.py). Se compare qualunque altro file, non committarlo:
    capisci perche' esiste e, se lo hai creato tu per sbaglio, rimuovilo.
3.2 Verifica che nessun file .zarr, .tif o .tar sia tracciato: `git ls-files | grep -E '\.(zarr|tif|tar)$'` deve
    non stampare nulla.
3.3 Committa e pusha come scritto al passo 13 del piano (branch e03-socio; nessun commit su main, nessuna PR).
3.4 Stampa, come ULTIMO messaggio, un blocco in questo formato esatto, compilato con i tuoi risultati:

RIEPILOGO E03 SOCIO — <data e ora>
S1 verdetto: <trovato equivalente | trovato lavoro parziale | non trovato nelle fonti consultate> — <una riga di motivo>
S1 fonti pertinenti trovate: <numero>; query non riuscite (ostacoli): <numero>
S2 impronte 0814: z13=<sha256> (attesa bc7423431221bf24…) | z1=<sha256> | z25=<sha256>
S2 uguaglianza slice a slice: <OK per -3 e +3 | DIFFERENZA in ...>
S3 tolleranza per seed e verso: seed42 -:<..> +:<..> | seed43 -:<..> +:<..>
S3 H1: <rispettata | violata su N combinazioni> | H2: <...> | anomalia: <attivata su k=.. | non attivata>
S3 controlli: media dei seed <aiuta | non aiuta> | media -2/+2 <aiuta | non aiuta>
S3 ambiguita' registrate: <numero>
Commit: <sha breve> "<messaggio>" — push su origin/e03-socio: <si' | no>
Ostacoli complessivi: <elenco in una riga, oppure "nessuno">
File consegnati: <elenco>

===================================================================================================
REGOLE NON NEGOZIABILI
===================================================================================================
- Non modificare mai file esistenti del repository. Se uno script non funziona su questo Mac, NON correggerlo:
  fermati su quel passo, registra il problema nel rapporto come "ambiguita' o ostacolo" (con la riga di errore
  esatta) e prosegui con il passo successivo se e' indipendente. Un ostacolo documentato e' un risultato valido.
- Crea solo i file elencati nella sezione 3 del piano, sul branch e03-socio. Nessun commit o push su main,
  nessuna pull request, nessun run Kaggle o GPU, nessuna pubblicazione di dataset, nessuna spesa, nessun contatto
  con l'esterno (niente issue, niente messaggi ad altri).
- Non leggere, stampare o copiare credenziali o token.
- Riporta i numeri cosi' come escono dagli script, anche se sembrano strani o non coincidono con le attese: la
  differenza e' l'informazione. Non aggiustare un conto per farlo somigliare a cio' che ti aspetti.
- Se hai un dubbio su una decisione che spetta a una persona, scrivilo nel rapporto nella sezione "ambiguita'" e
  prendi la scelta piu' conservativa, invece di fermarti: il socio non puo' deciderla, la decidera' Matteo leggendo.
- Se devi interrompere per limiti di sessione o di tempo, stampa prima uno stato chiaro: quali passi sono conclusi,
  quale e' in corso, quali file esistono gia'. Il socio ti scrivera' "continua" e tu riprenderai da li', senza
  rifare cio' che e' gia' fatto e verificato.

Riporta gli esiti fedelmente: se un comando fallisce, mostra la riga di errore; se un passo e' stato saltato,
dillo; non dichiarare fatto cio' che non hai verificato.
```
