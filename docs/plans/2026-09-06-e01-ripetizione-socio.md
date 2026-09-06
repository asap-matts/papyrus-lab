# E01 — ripetizione indipendente di E00 da parte del socio (Mac + account Kaggle proprio)

**Scritto da:** Claude Code (writer, su incarico di Matteo) · **Esecutore previsto:** Codex, sul Mac del socio, con il socio che approva i run GPU · **Revisore dell'esito:** Claude (read-only), poi decisione di Matteo
**Data:** 2026-09-06 · **Branch PapyrusLab di lavoro:** `e01-socio` (creato da `main`) · **Base:** il commit di `main` che contiene questo piano

> Verifica prima di iniziare, dalla cartella del repository (`~/dev/papyrus-lab`), sul branch `e01-socio`:
> `git status --short` vuoto; esistono `docs/plans/2026-09-06-e01-ripetizione-socio.md`, `scripts/e01_bootstrap_mac.sh` e `kaggle/e01-r01-seed42/`.
> Se non è così, **fermati**: il repository non è aggiornato (`git pull`).

---

## 1. Obiettivo

Alla fine deve essere vero **uno** dei due esiti:

- **E01 superato:** dal solo repository, una persona diversa (il socio), con un account Kaggle diverso e un agente diverso (Codex), ottiene su w035 un esito equivalente a E00: gate A e gate B superati, AUROC entro la tolleranza del §5, orientamento corretto. Il risultato di E00 diventa **riproducibile** (gate G2 della procedura).
- **E01 non superato o interrotto, documentato:** dove e perché le istruzioni non sono bastate. Anche questo è un risultato utile: è proprio ciò che E01 misura.

Non si esegue nulla sul Mac oltre a comandi di gestione: **i notebook girano su Kaggle**, sulle GPU dell'account del socio. E01 verifica istruzioni, account e agente diversi — non hardware diverso.

---

## 2. Contesto necessario

Chi esegue non ha letto nessuna conversazione. Tutto ciò che serve è nel repository:

- [AGENTS.md](../../AGENTS.md): regole del progetto (leggerlo per primo).
- [docs/07-procedura-operativa.md](../07-procedura-operativa.md): metodo, gate, condizioni di arresto.
- [docs/08-dossier-input-e00.md](../08-dossier-input-e00.md): dati, modello, decisioni, criterio di esito.
- [docs/plans/2026-09-06-e00-controllo-noto-w035.md](2026-09-06-e00-controllo-noto-w035.md): il piano E00, con il registro di tutti i tentativi e ciò che hanno insegnato.
- `scripts/build_e00_notebooks.py`, `scripts/kaggle_e00.py`, `scripts/build_w035_label_dataset.py`: l'automazione, già collaudata su E00.

In parole semplici: **w035** è un pezzo di papiro già annotato a mano dagli organizzatori e già visto dal modello in addestramento; il modello produce un'immagine con un valore 0–255 per pixel (quanto "crede" ci sia inchiostro); si confronta con l'annotazione ufficiale con un numero, l'**AUROC** (probabilità che un pixel d'inchiostro riceva un valore più alto di un pixel di sfondo; 0,5 = caso, 1 = perfetto), e con un **test di orientamento** (la label ruotata o specchiata deve dare AUROC più bassa). Tutto questo è calcolato dai notebook: nessun giudizio a occhio decide l'esito.

### Decisioni già prese, e perché

- **Stesso codice, stesso modello, stessi parametri di E00** — è una ripetizione, non una variante. Branch `merge-ink-pipelines` di villa @ `3ea17f54a9b3d5fd1aaf73e1d2c8386dbaa9f30e`, checkpoint `step-075000` dei seed 42 e 43 (SHA-256 nel dossier), `--no-compile --gpus 0 --batch-size 1`, una sola T4 visibile. Nulla di questo va "migliorato".
- **I notebook si rigenerano con l'username Kaggle del socio** (`--user`) e con `--run-id e01-r01`: cambiano solo i nomi dei notebook e dei dataset Kaggle, che devono appartenere al suo account. Ogni costante scientifica resta identica (è nel generatore).
- **La label si ricostruisce dal bucket ufficiale con lo script del progetto**, non si copia da Matteo: lo script scarica i 5.128 file (~8 minuti, una volta sola), verifica conteggio e byte, e calcola l'hash dell'albero, che **deve** coincidere con quello congelato nel generatore (`09037f1d…1f27`). Se coincide, il socio ha esattamente la stessa label, ottenuta in modo indipendente.
- **Non si usa `uv run`** su Kaggle (deviazione dichiarata e motivata nel dossier: ambiente da 4,3 GB azzerato a ogni sessione); l'installazione con `--no-deps` aggiunge tre pacchetti, tutti dal lock. Lo stesso in E01: a parità di deviazione, la ripetizione è confrontabile.
- **Non è cieco, e va bene:** i numeri di E00 sono nel repository e il socio potrebbe leggerli. Il cieco serve quando l'esito dipende da un giudizio umano; qui l'esito è calcolato da uno script e la conoscenza del risultato atteso non può cambiare ciò che la pipeline produce. Si chiede comunque a Codex di **non aprire** `docs/reports/2026-09-06-e00-r01*` e `runs/` prima di aver completato i propri run, per non farsi guidare nella diagnosi degli errori dalle soluzioni già trovate.
- **Il socio approva ogni run GPU** (è la sua quota, ~30 ore/settimana): Codex si ferma e chiede prima di `push seed42` e `push seed43`. Il preflight non consuma quota.
- **Codex scrive solo nei percorsi assegnati** (§3) e lavora sul branch `e01-socio`; alla fine committa e pusha **il branch**, non `main`. La fusione in `main` la decide Matteo dopo la revisione dell'esito (un solo writer su `main`).
- **Se uno script non funziona su macOS, ci si ferma e si registra:** è un finding di E01 (istruzioni non sufficienti), non un problema da aggirare modificando gli script — modificarli renderebbe il confronto con E00 non a parità.
- **Tolleranze (§5) decise prima della prova.** I TIFF possono differire a livello di byte fra due esecuzioni GPU (aritmetica in virgola mobile non deterministica): non si richiede lo stesso hash del TIFF, si richiede lo stesso esito e AUROC entro tolleranza.

### Vincoli

- Nessun commit su `main`, nessun push di `main`, nessuna PR, nessun invito, nessuna submission, nessuna spesa. Commit e push **solo sul branch `e01-socio`**, al termine (o a un arresto documentato).
- Non modificare `scripts/`, `kaggle/e00-r01-*`, `docs/07`, `docs/08`, il piano E00, la scheda E00. Non toccare `main`.
- Non scaricare i TIFF di E00 (non sono in Git) e non caricare TIFF, checkpoint o label in Git (`.gitignore` li esclude; verificare con `git status` prima del commit).
- Il clone del repository va in una cartella **fuori da iCloud Drive** (per esempio `~/dev/papyrus-lab`).

---

## 3. Perimetro

### File che Codex crea o modifica (solo sul branch `e01-socio`)

| File | Cosa fare |
|---|---|
| `kaggle/e01-r01-{preflight,seed42,seed43}/` | **Già generati e committati da Matteo** con `scripts/build_e00_notebooks.py --user micheleghisa --run-id e01-r01`; Codex li verifica soltanto (passo 2), **non li rigenera e non li modifica** |
| `docs/reports/AAAA-MM-GG-e01-r01.md` | Scheda dell'esperimento compilata da `docs/templates/esperimento.md` (stessa struttura della scheda E00) |
| `docs/reports/AAAA-MM-GG-e01-r01-manifest.json` | Manifest con commit, revisioni, hash, versioni, tempi, metriche, confronto con E00 (§5), elenco delle ambiguità trovate nelle istruzioni |

Fuori da Git (cartella ignorata): `runs/E01-R01/…` con gli output scaricati (una sottocartella per versione), il dataset della label e il dataset dell'output seed42.

### File da NON toccare

| File | Perché |
|---|---|
| `scripts/*` | Se non funzionano, è un finding: fermarsi e registrare, non correggere (altrimenti il confronto con E00 non è a parità) |
| `kaggle/e00-r01-*`, `docs/reports/2026-09-06-e00-r01*` | Sono il risultato di E00, congelato |
| `docs/07`, `docs/08`, `docs/plans/2026-09-06-e00-*` | Procedura e piano congelati; correzioni solo tramite Matteo |
| `main` | Un solo writer; la fusione la decide Matteo |

---

## 4. Passi

Sul Mac, in Terminale. Le parti che richiedono **una persona** sono segnate con 👤; tutto il resto lo fa Codex.

### Passo 0 — Prerequisiti (già predisposti da Matteo; al socio restano tre login)

Stato di partenza dichiarato da Matteo il 6 settembre 2026: account Kaggle del socio `micheleghisa` con **verifica telefonica completata**; account GitHub `micheleghisa`; username già inseriti in piano, prompt e notebook; branch `e01-socio` già creato su GitHub; invito al repository inviato da Matteo.

Sul Mac, il socio apre il Terminale e incolla **una riga**, dopo aver installato `gh` se manca (`brew install gh`):

```bash
gh auth login
bash <(curl -fsSL https://raw.githubusercontent.com/asap-matts/papyrus-lab/main/scripts/e01_bootstrap_mac.sh)
```

Lo script (`scripts/e01_bootstrap_mac.sh`) è rieseguibile e si ferma dicendo cosa manca: controlla `git` e Python ≥ 3.11, installa la CLI Kaggle, clona il repository in `~/dev/papyrus-lab` (fuori da iCloud), passa al branch `e01-socio`, verifica l'autenticazione Kaggle. I passaggi 👤 che chiede, quando servono:

- 👤 `gh auth login` (GitHub.com, HTTPS, login nel browser) e accettare l'invito al repository, arrivato per e-mail o su `github.com/asap-matts/papyrus-lab/invitations`;
- 👤 `python3 -m kaggle auth login` (si apre il browser) **oppure** token da `kaggle.com/settings/api` → *Generate New Token* salvato in `~/.kaggle/access_token` (solo il token). Codex non deve mai leggere né stampare quel file.

**Fatto quando:** lo script stampa "Tutto pronto" con il commit del branch. Codex registra nel manifest le versioni di git, Python e CLI Kaggle stampate dallo script (o le rilegge con `git --version`, `python3 --version`, `python3 -m kaggle --version`).

### Passo 1 — Verifica dello stato (Codex)

```bash
cd ~/dev/papyrus-lab
git status --short --branch          # atteso: pulito, su e01-socio, allineato a origin/e01-socio
git log -1 --format='%h %s'
ls docs/plans/2026-09-06-e01-ripetizione-socio.md scripts/kaggle_e00.py
```
**Fatto quando:** il branch è `e01-socio`, pulito, e i file esistono. Annotare l'hash del commit di partenza nel manifest.

### Passo 2 — Verificare i notebook già generati (non rigenerarli)

```bash
ls kaggle/e01-r01-preflight kaggle/e01-r01-seed42 kaggle/e01-r01-seed43
python3 -c "import json;[print(json.load(open(f'kaggle/e01-r01-{m}/kernel-metadata.json'))['id']) for m in ['preflight','seed42','seed43']]"
```
**Fatto quando:** i tre `id` stampati sono `micheleghisa/papyruslab-e01-r01-preflight`, `…-seed42`, `…-seed43`. Se il repository fosse indietro (cartelle assenti), `git pull` e ripetere; non eseguire il generatore.

### Passo 3 — Costruire e pubblicare il dataset della label (una volta; ~8–10 minuti di download)

```bash
python3 scripts/build_w035_label_dataset.py --user micheleghisa --out runs/E01-R01/dataset-w035-labels
```
Atteso nelle ultime righe: `API listing: 5128 files, 737833 bytes` e **`LABEL_TREE_SHA256=09037f1d0ccc008c5f619b2a4f41a554d1abf50739fd02469a9a2fb799731f27`**.
**Fermarsi se** il conteggio o l'hash differiscono: la label a monte è cambiata o il download è corrotto; registrare e non procedere.
Poi:
```bash
python3 -m kaggle datasets create -p "$(pwd)/runs/E01-R01/dataset-w035-labels"
python3 -m kaggle datasets status micheleghisa/papyruslab-w035-labels    # ripetere finché risponde: ready
```
**Fatto quando:** lo stato è `ready`.

### Passo 4 — Preflight su Kaggle (senza GPU, senza quota)

```bash
python3 scripts/kaggle_e00.py --run-id e01-r01 push preflight
python3 scripts/kaggle_e00.py --run-id e01-r01 wait preflight      # esce 0 solo se 'complete'
python3 scripts/kaggle_e00.py --run-id e01-r01 output preflight    # scarica in runs/E01-R01/preflight/<timestamp>/ e verifica SHA256SUMS
```
**Fatto quando:** `wait` stampa `complete` e `output` stampa `differenze: 0; richiesti mancanti: nessuno`. Nel log scaricato (`runs/E01-R01/preflight/<timestamp>/e00/logs/`): `install.json` con i pacchetti aggiunti, `label_count.txt` con lo stesso `tree_sha256`, `model_build_cpu.json` con `in_chans: 17`, `tiff_lzw_test.json` con `ok: true`.
**Se il run è `error`:** `output` scarica comunque log e output parziali; leggere il log del kernel (`papyruslab-e01-r01-preflight.log`) per trovare la riga `STOP: …` o il traceback; registrare passo e causa; **non modificare gli script**; fermarsi e riportare (§7). Un preflight fallito non consuma quota GPU e può essere ripetuto dopo aver capito la causa, se la causa è esterna (rete, servizio Kaggle) e non del repository.

### Passo 5 — 👤 Approvazione del socio, poi run `seed42` (GPU)

Codex mostra al socio: cosa sta per fare, che consuma quota GPU (stima 10–15 minuti di sessione), e attende un "vai" esplicito. Poi:
```bash
python3 scripts/kaggle_e00.py --run-id e01-r01 push seed42
python3 scripts/kaggle_e00.py --run-id e01-r01 wait seed42
python3 scripts/kaggle_e00.py --run-id e01-r01 output seed42
python3 -c "import json,glob;m=json.load(open(sorted(glob.glob('runs/E01-R01/seed42/*/e00/out/metrics_seed42.json'))[-1]));print({k:m[k] for k in ['originale','rot180','flipY','flipX','orientamento_ok','gate_B','sha256_tif']})"
```
**Fatto quando:** `output` verifica tutto e `gate_B` è `superato`. Se `wait` restituisce `error`, scaricare comunque con `output`, leggere il log, registrare, fermarsi. Un retry è ammesso solo se la causa è esterna e documentata; ogni retry consuma quota e va approvato di nuovo dal socio.

### Passo 6 — Pubblicare l'output del seed 42 e 👤 approvare il run `seed43`

```bash
python3 scripts/kaggle_e00.py --run-id e01-r01 publish-seed42-out
python3 -m kaggle datasets status micheleghisa/papyruslab-e01-r01-seed42-out   # finché: ready
```
Poi, con il "vai" del socio:
```bash
python3 scripts/kaggle_e00.py --run-id e01-r01 push seed43
python3 scripts/kaggle_e00.py --run-id e01-r01 wait seed43
python3 scripts/kaggle_e00.py --run-id e01-r01 output seed43
cat runs/E01-R01/seed43/*/e00/out/compare_seeds.json
```
**Fatto quando:** `output` verifica tutto; `metrics_seed43.json` e `compare_seeds.json` esistono. Il seed 43 è informativo: non cambia il verdetto di E01.

### Passo 7 — Scheda, manifest, commit e push del branch

Codex compila `docs/reports/AAAA-MM-GG-e01-r01.md` da `docs/templates/esperimento.md` (stessa struttura della scheda E00, che ora può essere letta per confronto) e il manifest JSON, con: ambiente del Mac (versioni), username Kaggle, hash del commit di partenza, versioni Kaggle di ogni run, pacchetti aggiunti, tempi, metriche dei due seed, confronto con E00 secondo il §5, e — sezione obbligatoria — **"Ambiguità e ostacoli nelle istruzioni"**: ogni punto in cui il piano o la documentazione non erano chiari o non bastavano, anche se poi risolto. Questo elenco è il prodotto principale di E01.

Poi:
```bash
git status --short                                   # solo kaggle/e01-r01-*, docs/reports/*e01-r01*
git ls-files --others --exclude-standard | grep -E '\.(tif|pth|zarr)$' && echo "STOP: binari non ignorati" || true
git add kaggle/e01-r01-preflight kaggle/e01-r01-seed42 kaggle/e01-r01-seed43 docs/reports/*e01-r01*
git commit -m "docs: E01-R01 independent repetition of E00 (partner account)"
git push -u origin e01-socio
```
**Fatto quando:** il push del branch è riuscito. **Non** fondere in `main`, **non** aprire PR: Matteo riceve il branch, Claude revisiona la scheda in sola lettura, Matteo decide.

---

## 5. Criterio di esito, deciso prima della prova

**E01 superato** se, sull'account del socio:

1. Gate A del piano E00 superato nel run `seed42` (commit villa, hash dei checkpoint, label con `tree_sha256 = 09037f1d…1f27`, indici 6–22, `in_chans=17`, `exit_code=0`, TIFF `(5820, 5240)` uint8);
2. `gate_B = superato` e `orientamento_ok = true` per il seed 42;
3. **|AUROC_seed42(E01) − 0,99908| ≤ 0,005** — tolleranza fissata ora: la variabilità attesa fra due esecuzioni GPU dello stesso comando è molto inferiore; una differenza maggiore segnala una differenza di ambiente o di input da spiegare;
4. le tre AUROC con label trasformate sono tutte < 0,65 (in E00: 0,53–0,58).

**Informativo, non bloccante:** seed 43 (in E00: AUROC 0,99825, Spearman con il 42 = 0,917); uguaglianza degli SHA-256 dei TIFF con quelli di E00 (`a0cc3f53…3c38` e `72fabca9…c8e5`): se uguali, l'esecuzione è bit-per-bit riproducibile, un risultato più forte; se diversi, è normale e va solo registrato.

**E01 non superato** se uno dei punti 1–4 fallisce. **Interrotto** se una stop condition scatta prima del passo 5.

Formulazione ammessa in caso di successo: *"il risultato di E00 è stato riprodotto da un secondo operatore, con account e agente diversi, dalle sole istruzioni del repository"* (gate G2 della procedura). Non ammesso: qualunque affermazione sul modello o sull'inchiostro oltre quelle già ammesse per E00.

---

## 6. Verifica finale

```bash
python3 scripts/kaggle_e00.py --run-id e01-r01 output preflight   # atteso: differenze: 0
python3 scripts/kaggle_e00.py --run-id e01-r01 output seed42      # atteso: differenze: 0
git status --short                                                # atteso: vuoto dopo il commit
git log origin/e01-socio -1 --format='%h %s'                      # atteso: il commit E01
git ls-files | grep -E '\.(tif|tiff|pth|zarr)$'                   # atteso: nessun output
```

---

## 7. Se il piano è sbagliato

1. **Fermati.** Non modificare gli script, non cambiare parametri, non passare a `main` di villa, non installare `uv`, non cambiare checkpoint o step.
2. Annota passo, comando, output e causa nella sezione "Ambiguità e ostacoli" della scheda: è il risultato di E01.
3. Se l'arresto avviene dopo il passo 4, esegui comunque il passo 7 (commit e push del branch con la scheda dello stato raggiunto).
4. Riporta al socio, che riporta a Matteo. Un nuovo tentativo sarà `E01-R02` con un piano corretto.

Arresto obbligatorio: `tree_sha256` della label diverso; hash di un checkpoint diverso; `wait` diverso da `complete` (dopo la lettura del log); `output` con differenze o file mancanti; qualunque richiesta di modificare file fuori dal §3; qualunque azione che richieda spesa, invito, PR o push su `main`.

---

## 8. Fuori perimetro

- Eseguire l'inferenza sul Mac (GPU Apple) o con `uv run`; confronti di tempo fra macchine.
- Provare altri step, segmenti, `--tta-mirror`, `--direction both`, due GPU, `torch.compile`.
- Interpretare i valori del TIFF come probabilità o "leggere lettere" nell'immagine di visualizzazione.
- Correggere la documentazione del progetto: le correzioni si **propongono** nella scheda, le applica Matteo.
- Coinvolgere Francesco o terzi.

---

## 9. Al termine

- [ ] Passi 0–7 eseguiti, oppure arresto documentato al passo N
- [ ] Scheda e manifest scritti, con la sezione "Ambiguità e ostacoli nelle istruzioni"
- [ ] Branch `e01-socio` pushato; `main` intatto
- [ ] Esito comunicato a Matteo (superato / non superato / interrotto) — la revisione e la decisione seguono su `main`
