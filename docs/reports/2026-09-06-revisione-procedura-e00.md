# Revisione della procedura operativa e del dossier E00

Stato: completata.

## Contratto

- ID revisione e ID esperimento: REV-2026-09-06-01; oggetto: `docs/07-procedura-operativa.md` e `docs/08-dossier-input-e00.md` (nessun esperimento eseguito).
- Data, revisore, agente e modello: 6 settembre 2026; Claude Code. Primo giro con Opus 5; secondo giro dopo cambio di modello a Fable 5.1 nella stessa sessione, dichiarato come verifica di chiusura e non come parere indipendente.
- Ruolo: read-only. Il ruolo di writer è stato assegnato da Matteo solo dopo la consegna dei due giri, per integrare i finding accettati.
- Commit di base, branch o worktree: `e37b04b42e1c034579769110446403d4efccbef3`, `main`, clone in `C:\dev\papyrus-lab` (repository assente sul fisso, clonato per la revisione).
- File e artefatti inclusi: AGENTS.md, README.md, docs/roadmap.md, docs/01–08, docs/fonti-e-verifiche.md, docs/reports/2026-09-05-kaggle-preflight.md, docs/templates/*.
- Non-goal e tool ammessi: nessuna modifica ai file, nessun download di dataset o checkpoint, nessuna GPU, nessuna installazione. Ammessi: lettura di metadati pubblici (S3, API Hugging Face, API GitHub), lettura del codice di villa alle revisioni citate, documentazione ufficiale.
- Budget, massimo giri e condizione di arresto: due giri; arresto alla consegna.

## Manifest ricevuto

- Piano congelato: non esiste ancora; oggetto della revisione sono la procedura e il dossier preparatorio.
- Configurazione e comando: comando candidato del dossier (`koine_machines.inference.infer … --overlap 0.5 --blend-mode hann`).
- Log e output originali: nessuno (nessuna esecuzione).
- Hash e provenienza degli input: dichiarati nel dossier e verificati (vedi tabella).
- Risultato dichiarato dall'esecutore: dossier "pronto a diventare piano dopo revisione".
- Informazioni nascoste per mantenere la valutazione in cieco: non applicabile.

## Verifiche su fonti primarie

| Affermazione del dossier | Esito | Fonte |
|---|---|---|
| w035 è un controllo noto appropriato e nel training set di `ink_9um` | Confermata | tutorial5 (*"a PHerc. 0139 segment from the models' own training set"*); README dataset `ink_9um` |
| URL, forma `[28, 5820, 5240]`, ZYX, `uint8`, chunk `[28,128,128]`, scala 9,362 µm, nessuna compressione, 853.910.400 B | Confermate | `.zattrs`, `0/.zarray` nell'open-data |
| w043 `[28, 6120, 8120]`, nel quick start del model card | Confermate | `.zarray` w043; model card |
| Label al prefisso `native9-scrollprizeorg-21slices/w035/`, due array, Z=14 su 28 slice | Confermate; misurata: 5.128 file, 737.833 B | API bucket; README dataset |
| Bucket completo di dimensione terabyte | Confermata: 3,35 TiB, 11,66 M file | API bucket |
| `hf buckets cp` per un prefisso | Parzialmente smentita: `cp` copia un solo file verso locale; serve `sync` | Doc CLI `huggingface_hub` |
| villa `merge-ink-pipelines` @ `3ea17f54…`; HF `ink_9um` @ `7109667e…` | Confermate (HEAD attuali) | API GitHub, API HF |
| Python ≥ 3.11, torch 2.10.0; entry point `koine_machines`; comando con `--overlap 0.5 --blend-mode hann` | Confermate | `pyproject.toml`, `configs/README.md` |
| "Comando storico `vesuvius.ink_detection`" | Smentita: è il percorso corrente su `main` e nel tutorial | villa `main` (PR #1456), tutorial5 |
| Checkpoint: dimensioni e SHA-256 | Confermate esattamente | API HF (`lfs.oid`) |
| TIFF `uint8` tiled LZW, `5820 × 5240`; slice centrali 6–22 con 17 slice | Confermate | `infer.py`; `aligned21_hybrid_3d2d.json` (`patch_size [17,128,128]`) |
| ≈233 MiB store `float32`; ≈264 MiB checkpoint | Confermate nel valore; gli store sono disco temporaneo cancellato a fine run | `infer.py` |
| `--gpus 0,1` possibile | Confermata con riserva: disattiva `torch.compile` | `infer.py` |
| Traffico e tempo di inferenza | Non determinati nel dossier; traffico ora derivato dai metadati (≈814 MiB + ≈12,7 MiB), tempo non verificabile senza eseguire | — |

Non riverificato da fonte primaria in questa sessione: la documentazione Kaggle (pagine non estraibili); le affermazioni Kaggle del repository restano L2 del 5 settembre.

## Finding

Severità: P0 rende invalido o pericoloso il metodo; P1 può invalidare E00 o la sua riproducibilità; P2 ambiguità o debito metodologico concreto; P3 editoriale. Esito del coordinatore (Matteo, 6 settembre 2026) nell'ultima colonna.

| ID | Sev. | File | Affermazione | Correzione minima | Esito |
|---|---|---|---|---|---|
| F1 | P1 | docs/07 gate | E05 non è richiesto da nessun gate: si passa da G4 a G5 senza verifica su dati esclusi dalle decisioni | Aggiungere E05 alla riga G5 | accept |
| F2 | P1 | docs/08 | Nessun criterio di esito per E00, solo artefatti da conservare; viola docs/07 §2 | Criterio AUROC + test di orientamento, da congelare nel piano | accept |
| F3-bis | P1 | docs/08 | `uv run` costruisce un ambiente da 4,3 GiB (3,8 GiB torch+CUDA) ignorando il PyTorch di Kaggle; `vesuvius` è dipendenza di percorso del monorepo; `vesuvius[models]` confligge (`torch<2.9`) | Python di sistema + `pip --no-deps`, checkout parziale, verifica versione torch, mai `[models]` | accept (decisione 1) |
| F4 | P1 | docs/08 | `torch.compile` attivo di default (`reduce-overhead`); il comando non lo disattiva | `--no-compile` nel primo tentativo | accept |
| F5 | P2 | docs/08 | I 233 MiB sono Zarr su disco in `tempfile.mkdtemp()`, cancellati a fine run; risorsa non dichiarata | Dichiarare risorsa e non conservabilità | accept |
| F6 | P2 | docs/08 | 1 vs 2 T4 non è a parità: multi-GPU disattiva `torch.compile` e usa `DataParallel` | Una T4 per E00; multi-GPU come misura separata | accept |
| F7 | P2 | docs/08 | `hf buckets cp` non scarica directory; la label sono 5.128 file | Usare `hf buckets sync` | accept |
| F8 | P2 | docs/07 | Collisione E0–E5 (evidenze) / E00–E06 (esperimenti) | Rinominare i livelli L0–L5 | accept |
| F9 | P2 | docs/08 | Le dimensioni identificano il seed, non lo step (sette checkpoint per seed con byte identici) | Nota: solo lo SHA-256 discrimina | accept |
| F10 | P2 | docs/07 | "Writer o coordinatore" usato ma non definito; nessun arbitro dei disaccordi | Definire il writer; arbitra Matteo | accept |
| F11 | P2 | docs/02 | Budget di 2 GB non copre il checkout di villa né `uv run` | Alzato a 10 GB come soglia di allarme | accept modificato (decisione 2) |
| F12 | P2 | preflight, docs/02 | Accesso a Internet del notebook Kaggle mai menzionato né esercitato | Controllo di rete nel preflight | accept |
| F13 | P3 | docs/08 | La motivazione di w035 omette che è l'esempio lavorato del tutorial | Citare il tutorial | accept |
| F14 | P3 | docs/08 | Legame Z=14 (label) ↔ centro di 6–22 non esplicitato | Una frase | accept |
| F15 | P3 | docs/02, 08 | "1 GB" e "1 GiB" per lo stesso limite | Uniformare a GiB | accept |
| F16 | P3 | docs/08 | w035 è nel training in due rappresentazioni | Registrarlo; vincolo per E02 | accept |
| F17 | P3 | docs/03 | I nomi `pherc0139-wNNN` non seguono la numerazione pubblica | Annotare la regola | accept |
| F18 | P1 | docs/08 | Due percorsi ufficiali (branch/`koine_machines` vs `main`/`vesuvius.ink_detection`); il dossier chiama "storico" quello corrente. La scelta del branch regge (congelato, torch 2.10 = Kaggle; `main` richiede ≥ 2.12) | Registrare la scelta come tale con motivazione | accept (decisione 3) |
| F19 | P2 | docs/07 | La staffetta non ha una consegna definita nel repository; il metodo globale è fuori dal repo e il socio non lo ha | Cinque righe o una scheda `consegna.md` | defer a prima di E01 |
| F20 | P2 | docs/07 | Termini tecnici senza definizione nel repository (manifest, worktree, staffetta, Recall@K, stdout, hash, preregistrazione) | Glossario | accept |
| F21 | P3 | docs/08 | Il confronto ufficiale fra seed su w035 è a `step-020000`, non `075000` | Annotarlo | accept |
| F22 | P3 | docs/08 | I render pubblicati hanno orientamento allineato alle label (`--flip-normals`): `forward` è corretto | Scriverlo nel piano | accept |
| F23 | P3 | docs/08 | Il tutorial fornisce il comando ufficiale `hf buckets sync` | Adottarlo ristretto al prefisso | accept |

Nessun finding rifiutato. Nessun P0.

## Decisioni del coordinatore

1. Installazione su Kaggle: Python di sistema, `pip install --no-deps`, dipendenze mancanti registrate, prova a GPU spenta, verifica di `torch.__version__`.
2. Tetto di spazio locale: 10 GB come soglia di allarme (il socio conferma la stessa disponibilità).
3. Codice: branch `merge-ink-pipelines` @ `3ea17f54…`, con motivazione corretta.
4. Ruoli: Claude writer di correzioni e piano; Codex revisore del piano e dell'esito in sola lettura (budget Codex limitato al momento); Matteo esecutore e arbitro; socio a E01.

## Chiusura

- Giri eseguiti e durata: due, stessa sessione; il secondo è verifica di chiusura (non indipendente).
- Correzioni materiali accettate: tutte tranne F19 (differita). Integrate dal writer in docs/07, docs/08, docs/02, docs/03, docs/04, AGENTS.md, README.md, docs/roadmap.md.
- Controlli saltati o impossibili: documentazione Kaggle non estraibile; tempo di inferenza non misurabile senza eseguire; equivalenza fra codice del branch e di `main` verificata per ispezione e non per esecuzione; discrepanza minore non risolta fra "25 segmenti fisici" del tutorial e i 24 contati dalle tabelle del dataset.
- Esito: approvato con correzioni, integrate.
- Questioni aperte e responsabile del passo successivo: piano E00 sul commit che contiene queste correzioni (writer: Claude); revisione del piano (Codex); prerequisiti senza GPU (Matteo con il writer).
- Commit o pubblicazione effettuati, oppure assenti: nessun commit al momento della chiusura; il commit documentale avverrà su richiesta esplicita di Matteo.
