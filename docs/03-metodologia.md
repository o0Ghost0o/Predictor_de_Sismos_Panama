# 03 · Metodología

## Etiqueta y split
- Etiqueta: `1` si hay M≥4.0 en la zona en (D, D+7]. Modelos M5+/M6+ análogos.
- Split **temporal** (nunca shuffle): train <2009-09-27 · val <2018-04-04 · test ≥2018-04-04.
- Features día D usan datos ≤D; sin leakage por construcción (auditado en 07).

## Features (14 base + 5 técnicas + 1 ETAS)
Sísmicas: `n, n7, n30, maxmag7, logE7, mean_depth, days_since_m4`.
Técnicas (idea RSI): `rsi_n14, rsi_E14` (Wilder), `vol_n30`, `roc_E30`, `benioff_since_m4`
(deformación acumulada desde último M4+).
Clima: medias + anomalías 30d de t2m, humedad, presión, lluvia.
Híbrida: `etas_rate` (tasa ETAS 7d ajustada solo en train).

## Modelos (`src/models/`)
| Modelo | Archivo | Nota |
|---|---|---|
| LightGBM 300 árboles, lr 0.05, class_weight balanced | `train.py` | Producción (14 feats validados) |
| LSTM 2 capas / Transformer-encoder (ventanas 30d) | `sequence.py` | Experiments, no superan baseline |
| ETAS temporal por zona (μ,K ajustados; c=0.01,p=1.1,α=1 fijos) | `etas.py` | Baseline físico |
| Stacking LR / cascada / LR portero / umbrales × zona | `multipass.py`, `multipass2.py` | Multipass, sin ganancia |
| Dial réplicas 24h/1h | `aftershock.py` | Segundo evaluador en producción |

Escala común 3–6 por umbrales calibrados (4: p4≥0.5 · 5: p5≥0.35 · 6: p6≥0.30).
Bandas M7–M10 por extrapolación Gutenberg-Richter (p7≈p6/10, b=1), etiquetadas GR,
visibles solo si ≥1% (por pedido: bajo 1% se ocultan en toda la app).

## Curva diaria (7 pronósticos individuales)
Modelos `d1..d7` (evento M4+ el día exacto D+k, `models/daily_7x.pkl`).
Test: D+1 0.063 (base 0.016) → D+5 0.038 → D+7 0.046: decaimiento de hazard.
El semanal concentra su skill en D+1/D+2; en día-D quieto PR-AUC 0.21 vs 0.45 con actividad.
