# Prompt per il Codex del socio — E03, procedura unica S1 → S2 → S3

Da incollare in Codex (CLI o app) **dopo** che `scripts/e03_bootstrap_mac.sh` ha stampato "Tutto pronto", aprendo la cartella `~/dev/papyrus-lab` come cartella di lavoro. Non serve Kaggle, non serve GPU. Modello consigliato: `gpt-5.6-sol` (regola di Matteo del 7 settembre 2026: Sol per default). Al socio restano: `gh auth login` se scaduto, e la consegna finale a Matteo.

**Prima di consegnare il prompt:** verificare che il campo "Commit di partenza" nell'intestazione di [2026-09-07-e03-compiti-socio.md](2026-09-07-e03-compiti-socio.md) sia compilato. Se è ancora vuoto, il lavoro non è pronto per il socio.

---

```text
Lavoriamo nel repository PapyrusLab (cartella corrente). Sei l'esecutore dei compiti S1, S2 e S3 di E03, in questo
ordine, secondo il piano docs/plans/2026-09-07-e03-compiti-socio.md. Io sono il socio di Matteo. Rispondi in italiano.

Prima di fare qualsiasi cosa:
1. Leggi per intero, in quest'ordine: AGENTS.md, docs/plans/2026-09-07-e03-compiti-socio.md, docs/07-procedura-operativa.md
   e la sola sezione "5. Criterio di esito" di docs/plans/2026-09-07-e03-tolleranza-offset-z.md (ti serve per S3).
2. NON aprire, in nessun momento prima della consegna: docs/reports/e03-r01/metrics/curve.json, la scheda
   docs/reports/*e03-r01*.md e il suo manifest, scripts/e03_curve.py, le cartelle runs/ di Matteo. Il valore del mio
   lavoro sta nell'essere indipendente: se leggo la loro analisi, S3 non vale più nulla.
3. Verifica lo stato del repository come chiede l'intestazione del piano (branch e03-socio, albero pulito, messaggio
   dell'ultimo commit uguale a quello dichiarato). Se non corrisponde, fermati e dimmelo.

Cosa devi fare, in sequenza, seguendo i passi del piano senza saltarne né aggiungerne:
- S1 (passi 2-5): verificare se qualcuno ha gia' pubblicato una misura di quanto i modelli di ink detection di villa
  perdono spostando la finestra Z. Query con `gh api` e `curl` come scritte nel piano, risposte salvate, poi un rapporto
  con: dove ho cercato, cosa ho trovato (URL, cosa misura, confrontabile si'/parziale/no) e il verdetto fra i tre ammessi.
- S2 (passi 6-9): tre pooling di pherc0814-46527 con scripts/e03_pool_shifted.py (--z-start 13, 1, 25), impronte con
  scripts/tree_sha256.py, uguaglianza slice a slice fra spostati e non spostato. L'impronta a --z-start 13 DEVE essere
  bc7423431221bf24b247a8ba80d264b0306f816c52b4ecc0d08115a82305ac52: se differisce, fermati e dimmelo subito, e' un P0.
- S3 (passi 10-12): ricostruire con uno script TUO (scripts/socio/e03_socio_curve.py) la curva AUROC(offset), le
  differenze, la tolleranza per seed e verso, i verdetti H1/H2/anomalia e i due controlli, leggendo solo i JSON in
  docs/reports/e03-r01/metrics/ (tranne curve.json) e applicando le definizioni della sezione 5 C del piano madre.

Regole non negoziabili:
- Usa sempre .venv/bin/python per i comandi Python. Ogni "Fatto quando" del piano va verificato con l'output reale.
- Non modificare mai file esistenti del repository. Se uno script non funziona su questo Mac, non correggerlo: fermati,
  registra il problema nel rapporto come "ambiguità o ostacolo" e dimmelo. È un risultato, non un fallimento tuo.
- Crea solo i file elencati nella sezione 3 del piano, sul branch e03-socio. Nessun commit o push su main, nessuna pull
  request, nessun run Kaggle o GPU, nessuna pubblicazione di dataset, nessuna spesa, nessun contatto con l'esterno.
- Non toccare, leggere o nominare pherc1667-w029: è un segmento sigillato del progetto.
- Non leggere, stampare o copiare credenziali. Non tracciare in Git file .zarr, .tif o .tar: controlla git status prima
  del commit.
- Riporta i numeri così come escono dagli script, anche se sembrano strani o non coincidono con le attese: la differenza
  è l'informazione. Non stimare un valore mancante: scrivi che manca.
- In S1 non concludere mai che una cosa "non esiste": la formula corretta è "non trovato nelle fonti consultate", con
  l'elenco di dove hai cercato. In S3 non aggiustare un conto per farlo somigliare a quello che ti aspetti.

Cosa devi produrre alla fine:
- docs/reports/<data>-e03-socio-s1-novita.md e -s1-fonti.json, -s2-pooling-46527.md, -s3-ricalcolo.md,
  più scripts/socio/e03_socio_curve.py.
- Commit e push del branch e03-socio; poi un riepilogo per me con: il verdetto di S1 in una riga, le tre impronte di S2,
  la tolleranza e i verdetti di S3, e l'elenco degli ostacoli. Io lo passo a Matteo.

Riporta gli esiti fedelmente: se un comando fallisce, mostra la riga di errore; se un passo è stato saltato, dillo; non
dichiarare fatto ciò che non hai verificato. Se hai un dubbio su una decisione che spetta a una persona, chiedi a me
invece di scegliere da solo.
```
