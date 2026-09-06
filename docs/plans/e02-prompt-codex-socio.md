# Prompt per il Codex del socio — E02, compiti S1 e S2

Da incollare in Codex (CLI o app) **dopo** che `scripts/e02_bootstrap_mac.sh` ha stampato "Tutto pronto", aprendo la cartella `~/dev/papyrus-lab` come cartella di lavoro. Non serve Kaggle. Al socio restano: `gh auth login` se scaduto, e la consegna finale a Matteo.

---

```text
Lavoriamo nel repository PapyrusLab (cartella corrente). Sei l'esecutore dei compiti S1 e S2 di E02 secondo il piano
docs/plans/2026-09-06-e02-compiti-socio.md. Io sono il socio di Matteo.

Prima di fare qualsiasi cosa:
1. Leggi per intero AGENTS.md, poi docs/plans/2026-09-06-e02-compiti-socio.md, poi docs/07-procedura-operativa.md. Non aprire
   docs/reports/*e02*, docs/plans/2026-09-06-e02-costruire-il-metro.md oltre alla sezione 9, né alcuna cartella runs/ diversa da
   runs/E02-SOCIO e runs/villa: i miei risultati valgono perché sono indipendenti da quelli di Matteo.
2. Verifica lo stato del repository come richiesto nell'intestazione del piano (branch e02-socio, stato pulito, messaggio del
   commit); se non corrisponde, fermati e dimmelo.

Regole non negoziabili:
- Usa sempre .venv/bin/python per i comandi Python. Segui i passi del piano nell'ordine, senza saltarne né aggiungerne. Ogni
  "Fatto quando" va verificato con l'output reale del comando.
- Non modificare mai file esistenti del repository. Se uno script non funziona su questo Mac, non correggerlo: fermati,
  registra il problema nel rapporto come "ambiguità o ostacolo" e dimmelo. È un risultato.
- Crea solo i file elencati nella sezione 3 del piano, sul branch e02-socio. Nessun commit o push su main, nessuna pull request,
  nessun run Kaggle, nessuna pubblicazione di dataset, nessuna spesa.
- Non leggere, stampare o copiare credenziali. Non tracciare in Git file .zarr, .tif o .tar: controlla git status prima del commit.
- Riporta i numeri così come escono dagli script, anche se non coincidono con quelli di R02: la differenza è l'informazione.

Cosa devi produrre alla fine:
- docs/reports/<data>-e02-socio-s1-audit-maschere.md con la tabella (nostri numeri accanto a quelli di R02 e differenze), i tre
  JSON di geometria, docs/reports/<data>-e02-socio-s2-pooling-46527.md con impronta, forma, attributi, tempi.
- Commit e push del branch e02-socio; poi un riepilogo per me con: i numeri principali di S1, l'impronta di S2, gli ostacoli.
  Io lo passo a Matteo.

Riporta gli esiti fedelmente: se un comando fallisce, mostra la riga di errore; se un passo è stato saltato, dillo; non dichiarare
fatto ciò che non hai verificato. Se hai dubbi su una decisione che spetta a una persona, chiedi a me invece di scegliere da solo.
```
