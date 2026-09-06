# Prompt per il Codex del socio — E01

Da incollare in Codex (CLI o app) **dopo** aver aperto la cartella del repository clonato (`~/dev/papyrus-lab`) come cartella di lavoro. Sostituire `<USERNAME_KAGGLE>` con il proprio username Kaggle. Prima di incollarlo, avere completato da soli i tre punti 👤 del passo 0 del piano: verifica telefonica Kaggle, invito GitHub accettato, autenticazione `kaggle` (`kaggle auth login` oppure token in `~/.kaggle/access_token`).

---

```text
Lavoriamo nel repository PapyrusLab (cartella corrente). Sei l'esecutore dell'esperimento E01 secondo il piano
docs/plans/2026-09-06-e01-ripetizione-socio.md. Io sono il socio di Matteo: approvo i run GPU e ti riporto ciò che vedo nel browser se serve.

Prima di fare qualsiasi cosa:
1. Leggi per intero AGENTS.md, poi docs/plans/2026-09-06-e01-ripetizione-socio.md, poi docs/07-procedura-operativa.md e docs/08-dossier-input-e00.md. Non aprire docs/reports/2026-09-06-e00-r01.md, il relativo manifest né la cartella runs/ finché non hai completato i tuoi run: il piano spiega perché.
2. Verifica lo stato del repository come richiesto nell'intestazione del piano; se non corrisponde, fermati e dimmelo.

Regole non negoziabili:
- Segui i passi del piano nell'ordine, senza saltarne né aggiungerne. Ogni "Fatto quando" deve essere verificato con l'output reale del comando, non presunto.
- Non modificare mai i file in scripts/, kaggle/e00-r01-*, docs/07, docs/08, docs/plans/2026-09-06-e00-*, docs/reports/2026-09-06-e00-r01*. Se uno script non funziona su questo Mac, non correggerlo: fermati, registra il problema nella scheda come "ambiguità o ostacolo" e dimmelo. È un risultato dell'esperimento.
- Lavora sul branch e01-socio. Nessun commit o push su main, nessuna pull request, nessun invito, nessuna spesa, nessuna submission. Commit e push del solo branch e01-socio al passo 7, o a un arresto documentato dopo il passo 4.
- Prima di ogni comando che consuma la mia quota GPU (`push seed42`, `push seed43`, e ogni loro ripetizione) fermati, dimmi cosa stai per fare e quanto costa, e aspetta il mio "vai" esplicito. Il preflight non consuma quota e puoi lanciarlo da solo.
- Non leggere, stampare o copiare ~/.kaggle/access_token, ~/.kaggle/kaggle.json né altre credenziali. Verifica l'autenticazione solo con `kaggle kernels list --mine --page-size 3`.
- Non scaricare né tracciare in Git file .tif, .pth o .zarr; controlla `git status` prima del commit.
- Il mio username Kaggle è <USERNAME_KAGGLE>: usalo dove il piano scrive <USERNAME_KAGGLE_SOCIO>.

Cosa devi produrre alla fine:
- docs/reports/<data>-e01-r01.md compilata dal template docs/templates/esperimento.md (stessa struttura della scheda E00, che potrai leggere solo a quel punto per il confronto), con la sezione obbligatoria "Ambiguità e ostacoli nelle istruzioni": ogni punto in cui piano o documentazione non erano chiari o sufficienti, anche se poi risolto.
- docs/reports/<data>-e01-r01-manifest.json con commit, versioni, hash, tempi, metriche dei due seed e il confronto con E00 secondo il §5 del piano.
- Commit e push del branch e01-socio; poi un riepilogo per me con: esito (superato / non superato / interrotto), i numeri principali (AUROC dei due seed, orientamento, tempi), quota GPU usata, e l'elenco delle ambiguità trovate. Io lo passo a Matteo.

Riporta gli esiti fedelmente: se un run fallisce, mostra la riga di errore del log; se un passo è stato saltato, dillo; non dichiarare superato ciò che non hai verificato. Se hai dubbi su una decisione che spetta a una persona, chiedi a me invece di scegliere da solo.
```
