# E03 — compiti del socio: una procedura unica S1 → S2 → S3 (Mac, CPU)

**Scritto da:** Claude Code (writer, su incarico di Matteo) · **Esecutore previsto:** Codex del socio, sul Mac M3 Pro, cartella `~/dev/papyrus-lab`, modello `gpt-5.6-sol` · **Revisore:** Claude Code in sola lettura, poi decisione di fusione di Matteo
**Data:** 2026-09-07 · **Branch:** `e03-socio`
**Commit di partenza:** `DA COMPILARE`

> Questa riga si compila al passo 10 del piano madre, con il commit che contiene i JSON delle metriche di E03, nel formato letto da `scripts/e03_bootstrap_mac.sh`: due asterischi, `Commit di partenza:`, due asterischi, lo sha breve fra apici inversi, un trattino lungo, il messaggio esatto del commit. Finché resta `DA COMPILARE`, lo script di avvio si ferma e il piano non va consegnato.
**Piano madre:** [E03 — tolleranza all'offset Z](2026-09-07-e03-tolleranza-offset-z.md), §9
**Prompt da incollare in Codex:** [e03-prompt-codex-socio.md](e03-prompt-codex-socio.md)

> **Questo documento non va consegnato finché il campo "Commit di partenza" qui sopra non è compilato.** Prima di iniziare: `git branch --show-current` deve stampare `e03-socio`, `git status --short` deve essere vuoto e `git log -1 --format=%s` deve restituire il messaggio dichiarato sopra. Altrimenti **fermati** e chiedi a Matteo.

---

## 1. Obiettivo

Alla fine devono esistere sul branch `e03-socio`, e solo lì, tre rapporti scritti **senza aver letto la scheda di E03, `curve.json` né i documenti canonici aggiornati dopo il commit di partenza**:

- **S1 — verifica di novità:** una ricerca documentata che dica se qualcuno ha già pubblicato una misura di quanto i modelli di ink detection di villa (in particolare `ink_9um`) perdono quando si sposta la finestra Z, con la lista di dove si è cercato e il verdetto *trovato equivalente / trovato lavoro parziale / non trovato*.
- **S2 — pooling spostato indipendente:** le impronte (SHA-256 dell'albero di file) degli input poolati di `pherc0814-46527` a spostamento 0, −3 e +3 slice, calcolate sul Mac, con l'uguaglianza slice a slice fra spostati e non spostato verificata localmente.
- **S3 — ricalcolo in cieco:** la tabella AUROC(offset) per segmento e seed, le differenze rispetto allo zero, la tolleranza per seed e verso e i due controlli, ricostruiti dai soli JSON delle metriche con uno script **tuo**, senza vedere la nostra analisi.

Se un passo non si può eseguire, un rapporto che dice dove e perché è un risultato valido.

---

## 2. Contesto necessario

Chi esegue non ha visto la conversazione da cui nasce questo piano. Serve sapere questo, e basta.

Il team sta studiando il modello ufficiale di *ink detection* `ink_9um` della Vesuvius Challenge: un programma che, guardando una pila di sezioni di scansione attorno alla superficie stimata di un foglio di papiro, dice dove c'è inchiostro. In E02 il team ha costruito un **metro**: 721.550 pixel con etichetta ufficiale mai usati per addestrare il modello, su tre segmenti; due servono allo sviluppo (`pherc0139-w016`, `pherc0814-46527`), il terzo (`pherc1667-w029`) è **sigillato** e non si tocca fino a E05.

In E03 il team misura la **tolleranza all'offset Z**. La pila di sezioni ha **21 slice** da 9,596 µm; il modello ne guarda **17**, per default gli indici 2–18, il cui centro (10) è il piano su cui sono annotate le etichette. Un **offset di k slice** fa guardare al modello la finestra centrata su 10 + k tenendo ferme le etichette: imita l'errore di chi stima la superficie ~9,6·k µm troppo in alto o in basso. Sono stati misurati k ∈ {−5, −3, −2, 0, +2, +3, +5} su due segmenti e due modelli (seed 42 e 43): 24 nuove inferenze più i quattro punti a offset zero già esistenti da E02. Il risultato atteso è la **curva** AUROC(k), non "la finestra migliore".

Per arrivare a |k| = 3 e 5 non bastano le opzioni del programma di inferenza (`--layer-start/--layer-end`, che coprono ±2): serve rifare il **pooling**, cioè la riduzione del volume da 2,399 µm a ~9,6 µm che prende 84 piani centrali dei 109 disponibili e ne fa la media a gruppi di 4. Lo script ufficiale di villa prende sempre i piani `[13, 97)`; il team ha scritto `scripts/e03_pool_shifted.py`, che lo riproduce con un parametro `--z-start` per prendere `[1, 85)` (−3 slice) o `[25, 109)` (+3 slice). **S2 verifica che quello script produca esattamente gli stessi byte anche su un'altra macchina.**

Due numeri che servono per capire i compiti:

- L'impronta ufficiale dell'input poolato di `pherc0814-46527` a spostamento zero è `bc7423431221bf24b247a8ba80d264b0306f816c52b4ecc0d08115a82305ac52`. In E02 è risultata identica su Kaggle, sul portatile di Matteo e su questo Mac.
- Sui pixel held-out, il seed 43 batte il seed 42 di 0,22 di F1 su w016 e i due seed sono quasi pari su 0814: per questo ogni confronto va fatto **entro lo stesso seed**, mai fra seed diversi.

### Perché questi tre compiti, e perché li fai tu

- **S1** serve perché il documento di decisione del team afferma che una curva del genere non è stata individuata nelle fonti consultate, e una revisione indipendente ha chiesto di verificarlo prima di rivendicarlo in una candidatura a premio. Chi ha scritto quell'affermazione non è la persona giusta per verificarla.
- **S2** è la terza misura indipendente delle impronte (Kaggle, portatile Windows, Mac): se coincidono, l'input della seconda tappa è identico fra piattaforme; se no, l'aritmetica non è deterministica e va dichiarato.
- **S3** verifica **l'analisi**, non i dati: se il team avesse sbagliato un segno negli offset o una regola di lettura, se ne accorgerebbe solo chi rifà i conti senza vedere il risultato atteso.

### Decisioni già prese, e perché

- **Una sola procedura consecutiva, dopo il commit dei JSON** (decisione di Matteo del 7 settembre 2026) — è più semplice da consegnare ed eseguire. Conseguenza: S2 è una verifica *a posteriori*; l'identità degli input spostati prima delle inferenze è già stata provata altrove (su Kaggle l'uguaglianza slice a slice con l'input ufficiale, sul portatile l'impronta a spostamento zero).
- **Ambiente `.venv` da `requirements-cpu.txt`, non `uv run`** — stesse versioni fissate del portatile di Matteo e di Kaggle: il confronto delle impronte non deve dipendere dalle librerie.
- **Solo `pherc0814-46527` in S2 (0,8 GB di rete)**; `pherc0139-w016` (5,6 GB) è facoltativo e va fatto solo se rete e tempo abbondano.
- **S3 con uno script tuo, non con `scripts/e03_curve.py`** — usare il nostro strumento riprodurrebbe anche un nostro eventuale errore. Puoi leggere i JSON, non il nostro codice di analisi.
- **Non si legge `curve.json`, la scheda `docs/reports/*e03-r01*.md`, né i documenti canonici aggiornati** finché i tre rapporti non sono committati: è ciò che rende S3 "in cieco".
- **Niente Kaggle, niente GPU, nessuna spesa** — tutti e tre i compiti sono lavoro locale di CPU e rete.

### Vincoli

- Solo il branch `e03-socio`; nessun commit su `main`, nessuna pull request, nessuna fusione.
- Nessun file `.zarr/`, `.tif`, `.tar` in Git (già ignorati): controllare `git status` prima del commit.
- Non modificare file esistenti del repository. Se uno script non funziona su questo Mac, **non correggerlo**: registra l'ostacolo nel rapporto. È un risultato.
- Non leggere, stampare o copiare credenziali. Non toccare nulla che riguardi `pherc1667-w029`.
- Spazio: ~1 GB per S2 su 0814 (+11 GB se si fa anche w016); S1 e S3 sono trascurabili.
- Percorsi relativi alla radice del repository; usare `.venv/bin/python` per ogni comando Python.

---

## 3. Perimetro

### File che Codex crea (solo sul branch `e03-socio`)

| File | Cosa contiene |
|---|---|
| `docs/reports/2026-09-XX-e03-socio-s1-novita.md` | Tabella delle fonti consultate (URL, revisione o data, cosa misura, confrontabile sì/no), query eseguite, verdetto, ambiguità |
| `docs/reports/2026-09-XX-e03-socio-s1-fonti.json` | Le risposte grezze salvate dalle query (elenco di URL e conteggi), per rendere la ricerca ripetibile |
| `docs/reports/2026-09-XX-e03-socio-s2-pooling-46527.md` | Comandi, attributi, forme, `tree_sha256` a spostamento 0/−3/+3, esito dell'uguaglianza slice a slice, tempi, ostacoli |
| `docs/reports/2026-09-XX-e03-socio-s3-ricalcolo.md` | Tabella AUROC(k) per segmento e seed, Δ rispetto allo zero, tolleranza per seed e verso, i due controlli, verdetto su H1/H2/anomalia, differenze rispetto a quanto atteso |
| `scripts/socio/e03_socio_curve.py` | Lo script **tuo** di S3 (cartella dedicata: non tocca `scripts/` del team) |

`XX` = giorno di esecuzione. Fuori da Git: `runs/E03-SOCIO/…`, `runs/villa/`, `data/`.

### File da NON toccare, e da NON leggere prima della consegna

| File | Perché |
|---|---|
| `docs/reports/e03-r01/metrics/curve.json` | È la nostra analisi: leggerla annullerebbe il valore di S3 |
| `docs/reports/2026-09-XX-e03-r01.md` e il suo manifest | La scheda dell'esperimento: idem |
| `scripts/e03_curve.py` | Il nostro codice di analisi: S3 deve essere una ricostruzione indipendente |
| Tutto il resto del repository | Un solo writer per cartella: Matteo e Claude scrivono su `main` |
| Qualunque cosa riguardi `pherc1667-w029` | Segmento sigillato fino a E05 |

Si **possono** leggere: `AGENTS.md`, questo piano, `docs/07-procedura-operativa.md`, il piano madre §5 (le regole di lettura che S3 deve applicare), `scripts/e03_pool_shifted.py` e i JSON in `docs/reports/e03-r01/metrics/` **tranne** `curve.json`.

---

## 4. Passi

### Passo 0 — Avvio (persona: il socio)

```bash
gh auth status || gh auth login
bash ~/dev/papyrus-lab/scripts/e03_bootstrap_mac.sh     # repository, branch e03-socio, Python >= 3.11, .venv
```
**Fatto quando:** lo script stampa "Tutto pronto". Poi apri Codex nella cartella `~/dev/papyrus-lab` e incolla il prompt di [e03-prompt-codex-socio.md](e03-prompt-codex-socio.md).

### Passo 1 — Verifica dello stato (Codex)

```bash
cd ~/dev/papyrus-lab && git branch --show-current && git status --short && git log -1 --format=%s
.venv/bin/python -m pytest tests/ -q
```
**Fatto quando:** branch `e03-socio`, stato vuoto, messaggio uguale a quello dichiarato nell'intestazione, test tutti superati. Registrare `sw_vers`, `.venv/bin/python --version`, `git --version`, `gh --version` per i rapporti.
**Fermarsi se:** il messaggio del commit non coincide (stai leggendo un piano scritto su un altro stato).

---

### S1 — Verifica di novità (~2–3 ore, solo rete)

**Domanda a cui rispondere:** esiste già, pubblicato da qualcuno, un lavoro che misura quanto un modello di ink detection di villa perde al variare della finestra Z o dell'offset in profondità, su dati con etichette tenute fuori dal training?

Non serve un browser: tutte le query si fanno con `gh api` e `curl`, e le risposte si salvano. Se una query non funziona (limite di frequenza, endpoint cambiato, autenticazione), **registrala come ostacolo** e prosegui con le altre.

#### Passo 2 — Query su GitHub

```bash
mkdir -p runs/E03-SOCIO/s1
# codice: opzioni e parole chiave della finestra Z nei repository della Challenge
for q in "layer-start repo:ScrollPrize/villa" "z_window repo:ScrollPrize/villa" "layer_start repo:ScrollPrize/villa" \
         "\"z offset\" ink detection vesuvius" "\"layer-start\" vesuvius ink" "\"z window\" ink_9um"; do
  echo "== $q"; gh api -X GET search/code -f q="$q" -f per_page=30 \
    --jq '.total_count as $n | "total=\($n)", (.items[]? | "\(.repository.full_name)  \(.path)  \(.html_url)")' \
    | tee -a runs/E03-SOCIO/s1/github_code.txt || echo "OSTACOLO su: $q" | tee -a runs/E03-SOCIO/s1/github_code.txt
  sleep 5
done
# issue, PR e discussioni
for q in "repo:ScrollPrize/villa z offset ink" "repo:ScrollPrize/villa layer-start" "repo:ScrollPrize/villa validation ink_9um" \
         "ink_9um z window" "vesuvius ink detection z offset sensitivity"; do
  echo "== $q"; gh api -X GET search/issues -f q="$q" -f per_page=30 \
    --jq '.total_count as $n | "total=\($n)", (.items[]? | "\(.html_url)  [\(.state)] \(.title)")' \
    | tee -a runs/E03-SOCIO/s1/github_issues.txt || echo "OSTACOLO su: $q" | tee -a runs/E03-SOCIO/s1/github_issues.txt
  sleep 5
done
# repository che citano la finestra Z nel README (ricerca per repository, non per codice)
gh api -X GET search/repositories -f q="vesuvius ink detection evaluation" -f per_page=30 \
  --jq '.items[]? | "\(.full_name)  \(.html_url)  \(.description // "")"' | tee runs/E03-SOCIO/s1/github_repos.txt
```

#### Passo 3 — Model card, discussioni Hugging Face, sito ufficiale

```bash
curl -sL https://huggingface.co/scrollprize/ink_9um/raw/main/README.md -o runs/E03-SOCIO/s1/ink_9um_README.md
grep -n -i -E "z |layer|offset|window|jitter|ensemble|average" runs/E03-SOCIO/s1/ink_9um_README.md | tee runs/E03-SOCIO/s1/ink_9um_hits.txt
curl -sL "https://huggingface.co/api/models/scrollprize/ink_9um/discussions" -o runs/E03-SOCIO/s1/hf_discussions.json
.venv/bin/python -c "import json;d=json.load(open('runs/E03-SOCIO/s1/hf_discussions.json'));print(len(d.get('discussions',d) if isinstance(d,dict) else d));[print(x.get('num'),x.get('title')) for x in (d.get('discussions',d) if isinstance(d,dict) else d)]" | tee runs/E03-SOCIO/s1/hf_discussions.txt
for u in https://scrollprize.org/community_projects https://scrollprize.org/2026_open_problems https://scrollprize.org/tutorial5; do
  f="runs/E03-SOCIO/s1/$(basename $u).html"; curl -sL "$u" -o "$f"
  echo "== $u"; grep -o -i -E ".{80}(z.?offset|z.?window|layer.start|depth sensitivity).{80}" "$f" | tee -a runs/E03-SOCIO/s1/site_hits.txt
done
```

#### Passo 4 — I repository del registro community

Per ciascuno dei repository R02–R11 elencati in `docs/06-ricerca-community.md` (tabella "Prima selezione"), cerca nel solo repository le parole chiave della finestra Z:

```bash
while read -r repo; do
  echo "== $repo"; gh api -X GET search/code -f q="z offset repo:$repo" -f per_page=10 --jq '.total_count' || echo OSTACOLO
  gh api -X GET search/code -f q="layer-start repo:$repo" -f per_page=10 --jq '.total_count' || echo OSTACOLO
  sleep 5
done < <(grep -o -E 'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+' docs/06-ricerca-community.md | sed 's#https://github.com/##' | sort -u) \
  | tee runs/E03-SOCIO/s1/registry_hits.txt
```

#### Passo 5 — Rapporto S1

Scrivi `docs/reports/2026-09-XX-e03-socio-s1-novita.md` con:

1. **Dove ho cercato:** l'elenco delle query eseguite (copiabile), le fonti raggiunte e quelle non raggiunte (ostacoli).
2. **Cosa ho trovato:** una riga per ogni risultato pertinente, con URL, data o revisione, **cosa misura esattamente** e una colonna *confrontabile con una curva AUROC(offset) su pixel held-out?* (sì / parziale / no, con una riga di motivo). Il model card ufficiale va incluso: dichiara la sensibilità **senza numeri**, quindi è "parziale".
3. **Verdetto:** *trovato equivalente* (qualcuno ha già pubblicato la stessa misura), *trovato lavoro parziale* (esistono affermazioni o misure vicine, ma non la curva), *non trovato*, con una frase che dice quanto sei sicuro e cosa non hai potuto controllare (per esempio: Discord non consultato, ricerca limitata all'inglese).
4. Salva le risposte grezze in `docs/reports/2026-09-XX-e03-socio-s1-fonti.json` (un oggetto con: query, data UTC, conteggi, elenco di URL).

**Fatto quando:** il rapporto esiste, ogni affermazione ha un URL, il verdetto è motivato. **Non** dichiarare "non esiste": la formulazione corretta è "non trovato nelle fonti consultate, elencate sopra".

---

### S2 — Pooling spostato indipendente (~1 ora, 1,6 GB di rete)

#### Passo 6 — Preparazione

```bash
mkdir -p runs/E03-SOCIO/input
shasum -a 256 scripts/e03_pool_shifted.py | tee runs/E03-SOCIO/input/script_sha256.txt
SRC="https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0814/segments/20260226000000-46527_2um_try2/surface-volumes/2.399um-0.22m-78keV-volume-20260309142202.zarr"
```

#### Passo 7 — Tre pooling e le loro impronte

```bash
for Z in 13 1 25; do
  OUT="runs/E03-SOCIO/input/pherc0814-46527_z${Z}.zarr"
  echo "== z-start $Z"; time .venv/bin/python scripts/e03_pool_shifted.py "$SRC" "$OUT" --level 2 --workers 4 --z-start $Z
  .venv/bin/python scripts/tree_sha256.py "$OUT" | tee -a runs/E03-SOCIO/input/impronte.txt
done
```

Atteso: per `--z-start 13` l'impronta deve essere **esattamente** `bc7423431221bf24b247a8ba80d264b0306f816c52b4ecc0d08115a82305ac52`. Se differisce, **fermati**: lo script non riproduce il pooling ufficiale su questo Mac, ed è un risultato importante da riportare subito.

#### Passo 8 — Uguaglianza slice a slice e attributi

```bash
.venv/bin/python - <<'EOF' | tee runs/E03-SOCIO/input/slice_check.txt
import json, numpy as np, zarr
base = "runs/E03-SOCIO/input/pherc0814-46527_z%d.zarr"
a0 = zarr.open(base % 13, mode="r")["0"]
for z, shift, lo0, lo_s in ((1, -3, 0, 3), (25, +3, 3, 0)):
    g = zarr.open(base % z, mode="r"); a = g["0"]
    print("z-start", z, "shape", a.shape, "attrs", json.dumps(dict(g.attrs)))
    assert tuple(a.shape) == (21, 2130, 3455), "STOP: forma diversa dalla label"
    ok = True
    for y in range(0, a.shape[1], 512):                      # a blocchi, per non saturare la RAM
        y1 = min(a.shape[1], y + 512)
        blk_s = a[lo_s:lo_s + 18, y:y1, :]
        blk_0 = a0[lo0:lo0 + 18, y:y1, :]
        if not np.array_equal(blk_s, blk_0):
            ok = False; print("DIFFERENZA nel blocco y", y, y1); break
    print("uguaglianza slice a slice con lo spostamento 0:", ok)
EOF
du -sh runs/E03-SOCIO/input/*.zarr
```

Le 18 slice condivise sono: per −3, le slice 3..20 dello spostato coincidono con le 0..17 dell'ufficiale; per +3, le 0..17 dello spostato coincidono con le 3..20 dell'ufficiale.

#### Passo 9 — Rapporto S2

`docs/reports/2026-09-XX-e03-socio-s2-pooling-46527.md`: comando eseguito e SHA-256 dello script, per ciascuno dei tre pooling forma, attributi (`format`, `source_z_slice`, `e03_z_shift_slices`), `tree_sha256`, tempo e dimensione su disco; esito dell'uguaglianza slice a slice; versioni (macOS, Python, zarr, numcodecs, numpy); ostacoli. **Non** confrontare con le impronte di Matteo: non le hai, il confronto lo fa lui.

*Facoltativo, solo se rete e spazio abbondano:* ripeti i passi 7–8 per `pherc0139-w016` (URL nel piano madre §2.1, forma attesa `(21, 7020, 7220)`, ~5,6 GB per pooling) e aggiungi una sezione al rapporto.

---

### S3 — Ricalcolo in cieco della curva (~1–2 ore, CPU)

#### Passo 10 — Leggere le regole, non i risultati

Leggi **solo** la sezione 5 C del piano madre ([2026-09-07-e03-tolleranza-offset-z.md](2026-09-07-e03-tolleranza-offset-z.md)): contiene le definizioni di Δ, tolleranza, H1, H2, regola di anomalia e criterio dei controlli. Non aprire `curve.json`, la scheda `docs/reports/2026-09-XX-e03-r01.md`, il manifest, `scripts/e03_curve.py`.

I file da leggere sono in `docs/reports/e03-r01/metrics/`, con nomi congelati:

| Nome | Cosa contiene |
|---|---|
| `<seg>_s<seed>_z<k>.json` (28) | report per un TIFF: `sets.held.auroc`, `sets.held.best_f1`, `sets.held.at_threshold`, `strata`, `regions`, e lo stesso per `train`. `k` ∈ `m5, m3, m2, 0, p2, p3, p5` (`m` = meno, `p` = più) |
| `<seg>_s<seed>_z<k>_spearman_z0.json` (24) | concordanza fra quella variante e l'offset zero dello stesso seed |
| `<seg>_seedmean.json` (2), `<seg>_seedmean_spearman.json` (2) | media dei due seed e loro concordanza |
| `<seg>_s<seed>_zmean_m2p2.json` (4) | media delle finestre −2 e +2 dello stesso seed |

I segmenti sono `pherc0139-w016` e `pherc0814-46527`; i seed 42 e 43.

#### Passo 11 — Il tuo script

Scrivi `scripts/socio/e03_socio_curve.py` (tuo, non copiato dal nostro) che legge quei JSON e produce:

1. **Tabella della curva:** righe = offset k in ordine da −5 a +5; colonne = le quattro combinazioni (segmento, seed); valori = AUROC held-out, e in una seconda tabella F1 alla soglia 91.
2. **Differenze:** `Δ(s, g, k) = AUROC(s, g, k) − AUROC(s, g, 0)` e `Δ̄(s, k)` = media di Δ sui due segmenti con pesi uguali.
3. **Tolleranza:** `T⁻(s)` = il più piccolo |k| fra {2, 3, 5} con k < 0 tale che `Δ̄(s, k) ≤ −0,05`; analogo `T⁺(s)`. Se nessun k campionato soddisfa la condizione, scrivi "nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati", **non** "tollera 48 µm".
4. **H1:** `|Δ(s, g, ±2)| ≤ 0,02` per tutte e quattro le combinazioni? Indica quali la violano e di quanto.
5. **H2:** `Δ̄(s, ±3) < Δ̄(s, ±2)` e `Δ̄(s, ±5) < Δ̄(s, ±3)`, per ciascun seed e verso: dove vale e dove no.
6. **Regola di anomalia:** esiste k ≠ 0 con `Δ(s, g, k) ≥ +0,02` per tutte e quattro le combinazioni? (Se sì, è un allarme da segnalare subito a Matteo.)
7. **Controlli:** per la media dei seed e per la media −2/+2, l'AUROC held supera quella del riferimento (rispettivamente ciascuno dei due seed a offset zero, e l'offset zero dello stesso seed) su **entrambi** i segmenti senza peggiorare oltre 0,01 su nessuno?

Lo script stampa le tabelle e scrive un JSON in `runs/E03-SOCIO/s3/`. Deve essere deterministico e non usare rete.

#### Passo 12 — Rapporto S3

`docs/reports/2026-09-XX-e03-socio-s3-ricalcolo.md` con: le due tabelle, le differenze, la tolleranza per seed e verso, i verdetti su H1, H2 e anomalia, l'esito dei due controlli, e una sezione "ambiguità": ogni punto in cui la regola di §5 C ti è sembrata interpretabile in più modi (per esempio pareggi, valori mancanti, arrotondamenti) con la scelta che hai fatto. Quella sezione è la parte più utile del compito.

**Fatto quando:** il rapporto contiene numeri per tutte e quattro le combinazioni e i verdetti sono motivati. Se un file manca, dillo: non stimare il valore.

---

### Passo 13 — Consegna

```bash
git add docs/reports/2026-09-XX-e03-socio-* scripts/socio/e03_socio_curve.py
git status --short                 # atteso: solo i file di §3
git commit -m "docs: E03 partner tasks S1 (novelty check), S2 (independent shifted pooling), S3 (blind curve recomputation)"
git push -u origin e03-socio
```

Poi consegna al socio un riepilogo per Matteo: verdetto di S1 in una riga, le tre impronte di S2, la tolleranza e i verdetti di S3, l'elenco degli ostacoli.

---

## 5. Criterio di esito, deciso prima della prova

- **S1 valido** se il rapporto elenca le query eseguite e, per ogni fonte pertinente, URL e giudizio di confrontabilità; il verdetto è una delle tre formule ammesse; nessuna affermazione di inesistenza assoluta.
- **S2 concorde** se l'impronta a `--z-start 13` è esattamente `bc742343…` e l'uguaglianza slice a slice vale per entrambi gli spostamenti. Se l'impronta differisce: **P0**, segnalare subito a Matteo prima di proseguire con S3.
- **S3 concorde** se le tabelle sono complete per le quattro combinazioni e i verdetti su H1, H2, anomalia e controlli sono espressi. Il confronto con la nostra analisi lo fa Claude: tu non lo puoi fare, e non devi.
- Un ostacolo documentato (una query che non risponde, un download che si interrompe) **non** invalida il compito: va scritto.

---

## 6. Verifica finale

```bash
git branch --show-current                          # e03-socio
git log origin/e03-socio -1 --format=%s            # il commit del passo 13
ls docs/reports/ | grep e03-socio                  # 4 file: 3 .md + 1 .json
git ls-files | grep -E '\.(zarr|tif|tar)$'         # nessun output
git status --short                                 # vuoto
```

---

## 7. Se il piano è sbagliato

1. **Fermati.** Non improvvisare: non correggere gli script del team, non cambiare versioni, non usare altri strumenti di pooling, non aprire i file vietati "solo per controllare".
2. Annota cosa hai trovato e a quale passo ti sei fermato.
3. Committa e pusha ciò che è coerente e verificato (anche solo un rapporto con l'ostacolo).
4. Segnala al socio, che avvisa Matteo.

---

## 8. Fuori perimetro

Non fare, anche se sembra utile: run Kaggle o GPU; inferenze; pubblicare dataset; leggere `runs/` di Matteo, la scheda di E03, `curve.json` o `scripts/e03_curve.py` prima della consegna; scaricare altri segmenti oltre a 0814 (e w016 se facoltativo); toccare `pherc1667-w029`; modificare `.gitignore`, `scripts/` del team o qualunque file esistente; commit su `main`; pull request; contattare gli organizzatori o pubblicare qualcosa.

---

## 9. Al termine

- [ ] S1: rapporto con query, fonti, verdetto; JSON delle risposte grezze
- [ ] S2: tre impronte, uguaglianza slice a slice, attributi, tempi
- [ ] S3: script proprio, due tabelle, tolleranza, H1/H2/anomalia, controlli, ambiguità
- [ ] Ostacoli registrati, anche se risolti
- [ ] Branch `e03-socio` pushato; riepilogo consegnato a Matteo
