# E02 socio — S1 audit indipendente delle maschere

**Data:** 2026-09-07  
**Esecutore:** Codex del socio, su Mac M3 Pro  
**Branch:** `e02-socio`  
**Commit di partenza:** `337d4a4` — `feat: E02 steps 1-3 (inventory, split, labels, metrics with tests)`

## Cosa è stato fatto

Il test preliminare `tests/test_e02_metrics.py` è terminato con `11 passed in 5.65s`. Sono state scaricate e verificate le label dei tre segmenti indicati dal piano. Per ciascun segmento è stato poi eseguito `scripts/e02_metrics.py --geometry` con patch da 128 px e bordi `0 64 128 256`.

I valori R02 sono risultati esterni, livello di evidenza L1. I valori “socio” sono misure replicate su questo Mac, livello di evidenza L3. Le differenze sono calcolate come `socio - R02`; per quote e distanze entro soglia sono espresse in punti percentuali (pp).

## Risultati

| Segmento | Misura | R02 (L1) | Socio (L3) | Differenza |
|---|---|---:|---:|---:|
| `pherc0139-w016` | Regioni annotate | 3 | 2 | -1 |
|  | Held-out (px) | 175.222 | 178.146 | +2.924 |
|  | Quota held-out | 29,5 % | 26,2548 % | -3,2452 pp |
|  | Regioni miste | 2 di 3 | 2 di 2 | 0 regioni miste; denominatore -1 |
|  | < 128 px | 58,6 % | 59,3407 % | +0,7407 pp |
|  | < 256 px | 99,1 % | 99,1153 % | +0,0153 pp |
|  | Distanza mediana | 108 px | 106,1037 px | -1,8963 px |
|  | Held-out e training sovrapposti | non riportato | 0 px | n/a |
| `pherc0814-46527` | Regioni annotate | 1 | 1 | 0 |
|  | Held-out (px) | 161.051 | 161.051 | 0 |
|  | Quota held-out | 27,3 % | 27,2947 % | -0,0053 pp |
|  | Regioni miste | 1 di 1 | 1 di 1 | 0 |
|  | < 128 px | 45,0 % | 45,0106 % | +0,0106 pp |
|  | < 256 px | 87,8 % | 87,8293 % | +0,0293 pp |
|  | Distanza mediana | 142 px | 141,9472 px | -0,0528 px |
|  | Held-out e training sovrapposti | non riportato | 0 px | n/a |
| `pherc1667-w029` | Regioni annotate | 8 | 8 | 0 |
|  | Held-out (px) | 382.353 | 382.353 | 0 |
|  | Quota held-out | 24,0 % | 23,9541 % | -0,0459 pp |
|  | Regioni miste | 1 di 8 | 1 di 8 | 0 |
|  | < 128 px | 23,2 % | 23,1616 % | -0,0384 pp |
|  | < 256 px | 45,4 % | 45,4486 % | +0,0486 pp |
|  | Distanza mediana | 283 px | 283,0000 px | 0 px |
|  | Held-out e training sovrapposti | non riportato | 0 px | n/a |

Secondo il criterio preregistrato, S1 è **discorde**: `pherc0139-w016` non coincide con R02 per numero di pixel held-out e regioni annotate; inoltre la differenza di `within_patch` è `+0,7407 pp`, oltre la tolleranza di ±0,5 pp. Non viene proposta qui una spiegazione: la decisione spetta a Matteo con il revisore.

Non è emersa sovrapposizione fra pixel held-out e training: `n_px_held_and_train=0` per tutti e tre i segmenti.

## Impronte delle label

| Segmento | File | Byte | `tree_sha256` | `tar_sha256` |
|---|---:|---:|---|---|
| `pherc0814-46527` | 1.386 | 118.869 | `5659236870d7d0408e330f05f6275bd821fc1d7bdea8c9c8f072dfd4ae8b54f0` | `32d3842a824a443e09b81414c5713a106e1010c1253a2dccf7eeb22b580e0e84` |
| `pherc0139-w016` | 9.414 | 746.565 | `a62d3e0ecfc9305758fae3bc0d74d99ecf675bcf846aa910ee4a876ee26ccfd5` | `27f3e6ae9cecccde847fe806c4ba0371a0e68b52093441e92f3eeaad87236ed9` |
| `pherc1667-w029` | 13.959 | 1.108.191 | `26cf3c17c202957f6c8c7fe1d9ded9a4d40b335d97091b012b8cd9ed92c99ee2` | `537975f217a1da24c6945955d46bd97a5b6e73bda9b0166dc60bb52f0b61c3b4` |

## Tempi e versioni

- Download e verifica: `1161 s` per `pherc0814-46527`, `3973 s` per `pherc0139-w016`, `3454 s` per `pherc1667-w029`; totale delle durate stampate dallo script `8588 s` (2 h 23 min 08 s).
- Geometria: circa 1 s, 3 s e 6 s rispettivamente, misurati dal tempo di parete della sessione.
- macOS 26.6.2, build 25G83.
- Python 3.12.14 da `.venv/bin/python`.
- Git 2.50.1 (Apple Git-155).
- `e02_metrics/1.0` nei tre JSON.

## Ambiguità e ostacoli

- Il download complessivo ha richiesto oltre due ore, molto più dei 30–60 minuti stimati nel piano. Non sono comparsi errori o retry visibili e tutti i conteggi e gli hash sono stati stampati.
- La riga sintetica dello script per `pherc1667-w029` dice `held 382353 px in 2 regions`; nel JSON `regions_held=2`, mentre la misura richiesta dal piano e confrontata con R02 è `annotated_regions=8`. La tabella usa la chiave `annotated_regions`, come prescritto.
- Le differenze di `pherc0139-w016` sono riportate senza aggiustamenti o interpretazioni.

## Artefatti

- `docs/reports/2026-09-07-e02-socio-s1-pherc0139-w016.json`
- `docs/reports/2026-09-07-e02-socio-s1-pherc0814-46527.json`
- `docs/reports/2026-09-07-e02-socio-s1-pherc1667-w029.json`

