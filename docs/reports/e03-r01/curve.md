# E03 — curva della tolleranza all'offset Z

Generata da `e03_curve/1.0` il 2026-09-07T19:11:10+00:00. Regola preregistrata: perdita media di 0.05 di AUROC (piano sezione 5 C).

## AUROC sui pixel held-out

| k (slice) | µm | pherc0139-w016 s42 | pherc0139-w016 s43 | pherc0814-46527 s42 | pherc0814-46527 s43 |
|---|---|---|---|---|---|
| -5 | -48.0 | 0.8137 | 0.8803 | 0.8227 | 0.7521 |
| -3 | -28.8 | 0.8305 | 0.8791 | 0.8172 | 0.8172 |
| -2 | -19.2 | 0.8275 | 0.9211 | 0.8065 | 0.8230 |
| +0 | +0.0 | 0.7740 | 0.9364 | 0.8743 | 0.8626 |
| +2 | +19.2 | 0.7296 | 0.9104 | 0.8961 | 0.8765 |
| +3 | +28.8 | 0.7132 | 0.8966 | 0.9038 | 0.8787 |
| +5 | +48.0 | 0.7315 | 0.8521 | 0.8926 | 0.9100 |

## Differenza rispetto all'offset zero dello stesso seed

| k | Δ̄ seed 42 | Δ̄ seed 43 |
|---|---|---|
| -5 | -0.0059 | -0.0833 |
| -3 | -0.0003 | -0.0514 |
| -2 | -0.0071 | -0.0275 |
| +0 | +0.0000 | +0.0000 |
| +2 | -0.0113 | -0.0061 |
| +3 | -0.0157 | -0.0119 |
| +5 | -0.0121 | -0.0185 |

## Tolleranza

- **seed 42** — verso negativo: nessun decadimento di 0,05 rilevato fino a 5 slice (48 µm) agli offset campionati; verso positivo: nessun decadimento di 0,05 rilevato fino a 5 slice (48 µm) agli offset campionati; Δ̄ a ±5: -0.0059 / -0.0121
- **seed 43** — verso negativo: 3 slice (28.8 µm); verso positivo: nessun decadimento di 0,05 rilevato fino a 5 slice (48 µm) agli offset campionati; Δ̄ a ±5: -0.0833 / -0.0185

- **H1** (piatta entro ±2, banda 0.02): violata — pherc0139-w016 s42 k-2: +0.0535, pherc0139-w016 s42 k+2: -0.0444, pherc0814-46527 s42 k-2: -0.0678, pherc0814-46527 s42 k+2: +0.0218, pherc0139-w016 s43 k+2: -0.0260, pherc0814-46527 s43 k-2: -0.0397
- **H2** (decade oltre ±2): non ovunque
- **Regola di anomalia**: non attivata
- **Media dei seed**: non aiuta (differenza peggiore -0.0234)
- **Media delle finestre −2/+2**: non aiuta (differenza peggiore -0.0131)

> Sui pixel held-out di sviluppo dei due segmenti, i due modelli mostrano la curva AUROC(k) riportata per offset uniformi della finestra Z. L'errore simulato e' uniforme e non rappresenta errori locali della superficie, normali sbagliate o cambi di foglio.

