# E03 socio S3 — ricalcolo in cieco della curva

**Data:** 7 settembre 2026  
**Esecutore:** Codex sul Mac del socio  
**Script indipendente:** `scripts/socio/e03_socio_curve.py`  
**Output deterministico:** `runs/E03-SOCIO/s3/e03_socio_curve.json`, SHA-256 `88bc95f825fb697faabadf13ca3ef354791166dd1cfe11e241d53f20c2d09ad8`

Il calcolo ha letto i 28 report individuali `<segmento>_s<seed>_z<k>.json` e i sei report dei controlli. Non ha letto `curve.json`, lo script di analisi del team, la scheda E03 o il manifest. Tutti i file e i campi richiesti erano presenti; nessun valore è stato stimato.

## AUROC held-out

| offset | w016/s42 | w016/s43 | 0814/s42 | 0814/s43 |
|---:|---:|---:|---:|---:|
| −5 | 0,813722 | 0,880307 | 0,822721 | 0,752079 |
| −3 | 0,830457 | 0,879065 | 0,817208 | 0,817250 |
| −2 | 0,827533 | 0,921149 | 0,806517 | 0,822982 |
| 0 | 0,774009 | 0,936449 | 0,874325 | 0,862635 |
| +2 | 0,729609 | 0,910403 | 0,896097 | 0,876457 |
| +3 | 0,713225 | 0,896580 | 0,903762 | 0,878726 |
| +5 | 0,731502 | 0,852075 | 0,892620 | 0,909990 |

## F1 held-out alla soglia 91

| offset | w016/s42 | w016/s43 | 0814/s42 | 0814/s43 |
|---:|---:|---:|---:|---:|
| −5 | 0,582537 | 0,634675 | 0,694364 | 0,619437 |
| −3 | 0,588170 | 0,658862 | 0,695324 | 0,689178 |
| −2 | 0,604058 | 0,720419 | 0,690343 | 0,698373 |
| 0 | 0,525874 | 0,748193 | 0,748131 | 0,739901 |
| +2 | 0,475431 | 0,722057 | 0,769759 | 0,734576 |
| +3 | 0,462763 | 0,697192 | 0,795661 | 0,739231 |
| +5 | 0,472387 | 0,621841 | 0,759776 | 0,775073 |

## Differenze AUROC rispetto allo zero dello stesso seed

`Δ(s,g,k) = AUROC(s,g,k) − AUROC(s,g,0)`.

| offset | w016/s42 | w016/s43 | 0814/s42 | 0814/s43 |
|---:|---:|---:|---:|---:|
| −5 | +0,039713 | −0,056142 | −0,051604 | −0,110557 |
| −3 | +0,056448 | −0,057384 | −0,057117 | −0,045385 |
| −2 | +0,053524 | −0,015299 | −0,067808 | −0,039653 |
| 0 | 0,000000 | 0,000000 | 0,000000 | 0,000000 |
| +2 | −0,044401 | −0,026046 | +0,021771 | +0,013821 |
| +3 | −0,060784 | −0,039868 | +0,029437 | +0,016090 |
| +5 | −0,042507 | −0,084374 | +0,018295 | +0,047355 |

Media di Δ sui due segmenti, con pesi uguali:

| seed | −5 | −3 | −2 | 0 | +2 | +3 | +5 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | −0,005946 | −0,000335 | −0,007142 | 0,000000 | −0,011315 | −0,015674 | −0,012106 |
| 43 | −0,083349 | −0,051385 | −0,027476 | 0,000000 | −0,006112 | −0,011889 | −0,018510 |

In particolare, a ±5: seed 42 `Δ̄(−5)=−0,005946`, `Δ̄(+5)=−0,012106`; seed 43 `Δ̄(−5)=−0,083349`, `Δ̄(+5)=−0,018510`.

## Tolleranza preregistrata

| aggregazione | seed | verso − | verso + |
|---|---:|---|---|
| media dei due segmenti | 42 | nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati | nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati |
| media dei due segmenti | 43 | 3 slice | nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati |
| w016 | 42 | nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati | 3 slice |
| w016 | 43 | 3 slice | 5 slice |
| 0814 | 42 | 2 slice | nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati |
| 0814 | 43 | 5 slice | nessun decadimento di 0,05 rilevato fino a 5 slice agli offset campionati |

La tabella riporta il primo modulo campionato fra 2, 3 e 5 per cui la perdita raggiunge almeno 0,05; non afferma che un valore intermedio non campionato sia tollerato.

## H1 — piatta entro ±2

**Violata su 6 coppie combinazione-offset su 8.** Violazioni di `|Δ| ≤ 0,02`:

| combinazione | offset | Δ | oltre il limite di 0,02 |
|---|---:|---:|---:|
| w016/s42 | −2 | +0,053524 | 0,033524 |
| 0814/s42 | −2 | −0,067808 | 0,047808 |
| 0814/s43 | −2 | −0,039653 | 0,019653 |
| w016/s42 | +2 | −0,044401 | 0,024401 |
| w016/s43 | +2 | −0,026046 | 0,006046 |
| 0814/s42 | +2 | +0,021771 | 0,001771 |

Le due coppie entro il limite sono w016/s43 a −2 (`Δ=−0,015299`) e 0814/s43 a +2 (`Δ=+0,013821`).

## H2 — decadimento oltre ±2

| seed | verso | Δ̄ a 2 | Δ̄ a 3 | Δ̄ a 5 | 3 < 2 | 5 < 3 | H2 nel verso |
|---:|---|---:|---:|---:|---|---|---|
| 42 | − | −0,007142 | −0,000335 | −0,005946 | no | sì | **no** |
| 42 | + | −0,011315 | −0,015674 | −0,012106 | sì | no | **no** |
| 43 | − | −0,027476 | −0,051385 | −0,083349 | sì | sì | **sì** |
| 43 | + | −0,006112 | −0,011889 | −0,018510 | sì | sì | **sì** |

H2 vale in entrambi i versi per seed 43 e non vale in nessuno dei due versi per seed 42. La risposta dipende quindi dal seed; non c'è un unico andamento monotono condiviso.

## Regola di anomalia

**Non attivata.** Nessun offset diverso da zero ha `Δ ≥ +0,02` in tutte e quattro le combinazioni segmento/seed.

## Controlli a costo zero

### Media dei seed

| riferimento a offset 0 | Δ w016 | Δ 0814 | aiuta? |
|---|---:|---:|---|
| seed 42 | +0,138992 | +0,014194 | sì |
| seed 43 | −0,023447 | +0,025884 | no |

**Verdetto complessivo: non aiuta.** La media supera seed 42 su entrambi i segmenti, ma rispetto a seed 43 peggiora w016 di 0,023447, oltre il margine 0,01.

### Media delle finestre −2/+2

| seed | Δ w016 | Δ 0814 | aiuta? |
|---:|---:|---:|---|
| 42 | +0,027108 | −0,002204 | no |
| 43 | −0,013080 | +0,003465 | no |

**Verdetto complessivo: non aiuta.** Per seed 42 non migliora entrambi i segmenti; per seed 43 peggiora w016 di 0,013080, oltre il margine 0,01.

## Ambiguità e scelte conservative

1. Per la tolleranza ho applicato la frontiera inclusiva `Δ ≤ −0,05` esattamente come preregistrata.
2. Per H1 ho applicato la frontiera inclusiva `|Δ| ≤ 0,02`: soltanto valori strettamente superiori in modulo sono violazioni.
3. Per H2 ho applicato confronti stretti; un pareggio non soddisferebbe il decadimento monotono.
4. Per l'anomalia ho applicato la frontiera inclusiva `Δ ≥ +0,02`.
5. Nei controlli ho interpretato “supera su entrambi i segmenti” come miglioramento stretto; un pareggio non è un miglioramento.
6. Per la media dei seed ho confrontato la media separatamente con entrambi i seed a offset zero e richiesto che entrambi i confronti aiutassero per il verdetto complessivo. Per la media −2/+2 ho richiesto l'esito positivo per entrambi i seed.
7. Le decisioni usano tutta la precisione dei JSON; l'arrotondamento a sei decimali serve solo alla visualizzazione.
8. In presenza di una curva non monotona, la tolleranza resta il primo modulo **campionato** che raggiunge la soglia, senza interpolazione.
9. Il conteggio H1 è espresso in coppie combinazione-offset: le quattro combinazioni segmento/seed sono valutate sia a −2 sia a +2.
10. Un file o campo mancante avrebbe fermato lo script con un errore, senza stima. In questa esecuzione non ne mancava nessuno.

## Ostacolo operativo

Il primo comando di cattura dello stdout ha restituito `tee: runs/E03-SOCIO/s3/stdout.txt: No such file or directory`: `tee` ha aperto il percorso prima che lo script creasse la cartella. Lo script aveva comunque prodotto il JSON. Il comando è stato ripetuto senza `tee` ed è terminato con codice 0. Due esecuzioni consecutive hanno prodotto lo stesso SHA-256 dell'output (`88bc95f8…ad8`), verificandone il determinismo.

