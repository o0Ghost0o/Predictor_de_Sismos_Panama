# 05 · Evaluación (test 2018-2026, azar ≈0.09; batería re-corridas tras cerrar el gap + IGC)

## Modelos — P(M4+ 7d)
| Modelo | PR-AUC | ROC |
|---|---|---|
| Stack LGBM+LSTM+Trans | 0.245 | 0.756 | previo (sin re-correr; profundos no re-entrenados) |
| LGBM+clima | 0.227 | 0.725 | +0.003 con gap cerrado + IGC |
| ETAS físico | 0.240 | **0.774** | mejor ROC; Azuero post-7.7 le cuesta (ROC 0.47): tasa saturada vs ocurrencia a rachas |
| Dial ETAS-24h global | 0.029 | 0.704 | base 0.016; en secuencia 0.232 |
| LGBM+clima+RSI | 0.224 | 0.747 |
| Híbrido ETAS×LGBM | 0.220 | 0.754 |
| LGBM+GNSS (red 88% muerta) | 0.224 | 0.747 | idéntico sin GNSS: sin cobertura no hay señal |
| Transformer / LSTM | 0.154 / 0.150 | 0.655 / 0.659 |

## Backtest umbral Nivel 4+ (p≥0.5)
CHIRIQUI 779 reales: 732 aciertos / 2003 FA / 47 omitidos · DARIEN 306: 191/1733/115 ·
AZUERO 129: 13/377/116 · BOCAS 101: 2/35/99 · CENTRAL 21: 0/54/21.

## Dial 24h — P(M4+ mañana), base 1.5%
Global 0.040 / ROC 0.77 · **secuencia 0.232** (228 días, base 9.2%) · calma 0.044.
Hoy: Azuero 88.7%/24h, 30%/1h.

## Fallos documentados
- **M7.7 Azuero 2026-10-09**: modelo marcó Nivel 3 (p 0.02) el 05-oct. Causa: `days_since_m4=972`
  (quiescencia 2.7a = riesgo bajo para el modelo; falta feature de acumulación de strain).
- Pre-M7.6 Limón 1991: BOCAS 0.44/acierto parcial, probabilidad repartida.
- Clima: ablación +0.04 PR-AUC con observado; forecast ≡ archivo (RMSE 0) → lift conservado.

## Diagnóstico 9-oct-2026 Azuero (bundle actual)
Oct 1–5: p7 0.24–0.58 (elevado por clima, sin sismicidad) · Oct 6–8: p7 ~0.30, d1 ~0.07
(quietud real: n=0, dsl 65–68) · Oct 9: p7 0.99 (n=90 con el 7.7 adentro).
Ningún feature (sísmico, clima, RSI, Benioff, ETAS) vio precursor: falla bloqueada
sin expresión en superficie + red GNSS muerta + foreshocks bajo detección.

## Mini-CSEP
Primer issue 2026-10-09 (Azuero p4 0.69), cierre 2026-10-16. Log inmutable `data/forecast_log.parquet`.
