# 04 · Decisiones (ADR)

1. **Solo Panamá, no global.** El clima y la tectónica locales se diluyen en modelos mundiales.
2. **M4+ / 7 días / 5 zonas.** Balance clases–datos: M5+ tiene 315 eventos, M6+ 61, M7+ 5 (in-entrenable).
3. **LightGBM en producción; profundos fuera.** LSTM 0.150 / Transformer 0.154 vs LGBM 0.241:
   con 1,622 eventos (<10⁴ que pide la literatura) los árboles ganan. Coherente con RECAST/Mármara.
4. **No RL.** RL optimiza acciones con recompensa; esto es predicción supervisada.
   RL solo tendría sentido futuro para la *política de avisos*, no el pronóstico.
5. **ETAS como baseline obligatorio (2 params).** MLE de 5 diverge en catálogos ralos
   (K→10²⁰⁰, dos veces; causa raíz: signo /(p-1) en la integral + ridge μ→0/K→∞).
   Fijar c,p,α a literatura estabiliza. Resultado: ETAS ROC 0.791 > todo ML.
6. **RSI se probó y resta (0.241→0.224).** Se usa (top-6 importancia) pero oscila sobre
   93% de días en cero. Hipótesis correcta, datos insuficientes → justifica IGC-UPA.
7. **Multipass no corrige.** Stack 0.245 (+0.004), cascada misma precisión 18%,
   LR portero 13% (peor). Errores correlacionados: mismo input, mismo fallo.
8. **Escala 3–6, no 4–10.** Sin ejemplos M7+ no se emiten niveles 7–10. Honestidad > completitud.
9. **Dual-mode.** Vigilia 7d siempre + dial ETAS 24h/1h tras M6+ (PR-AUC 0.232 en secuencia vs 0.044 en calma).
10. **Experimentos no tocan producción.** Bundle `lgbm_full.pkl` (14 feats) solo se reemplaza con mejora validada.
11. **Lecciones de infra.** torch+LightGBM en un proceso = segfault (libomp vs libgomp):
    fases separadas por proceso + imports perezosos. 8GB RAM obligan batches ≤512 y tensores chicos.
13. **USGS hace backfill: resync obligatorio.** Oct-2026: 20 eventos ene–sep 2026 entraron
    semanas tarde; el loop 3h jamás los ve. Actor `resync_catalog` (re-pull 2025→hoy,
    dedupe por id, auto-cada-30d). Gap de 9 meses sesgaba `days_since_m4` y etiquetas.
14. **IGC-UPA integrado como feed live.** 175 eventos/semana M1.7+, 39 sub-M4, +136 netos tras dedupe.
    Sin archivo público: solo sirve al presente; archivarlo a diario construye el catálogo denso
    que RSI/profundos necesitan. Nota: Azuero pre-7.7 pasó de p=0.02 a p=0.99 con foreshocks IGC —
    la densidad local sí mueve la aguja.
15. **Wayback rescata lo irrecuperable (parcial).** 3 snapshots IGC → 32 eventos (ene 0→15,
    con enjambre 19-ene M4.5). Métricas sin cambio: 32 filas no mueven 103k. Queda hueco:
    sub-M4 feb–sep 2026 no existe en ningún archivo público.
16. **Contexto regional crudo resta.** Anillo 4–12N/86–76W (2,595 eventos vecinos) como
    `reg_n30/reg_max7/reg_d5` a 3° del centroide: 0.2256→0.2103 aunque `reg_d5` queda
    feature #1 (sobreajuste a secuencias regionales). El contexto de placas vecinas debe
    entrar como física (ETAS regional, strain), no como conteos crudos. Clima sigue local.
17. **Calibración isotónica obligatoria.** LightGBM con class_weight sale sobreconfiado:
    M6 p≥0.5 → realidad 0% (173 casos); M5 p≥0.5 → 5%; M4 p≥0.5 → 19%.
    IsotonicRegression en val: Brier M4 0.21→0.07, M5 0.06→0.01, M6 0.007→0.002.
    Chiriquí 5-oct pasó de M6 10.3% a 2.3% (consistente con ETAS ~1%).
    Umbral operativo: top-10% semanas por zona (el 0.5 fijo muere con probs honestas).
12. **GNSS cableado, red muerta.** NGL entrega series por zona (velocidad 30d + salto residual),
    pero 4/5 estaciones COCONet Panamá murieron 2017–2023 → cobertura test 12% → PR-AUC idéntico
    (0.2241/0.7465 con y sin GNSS, features sin uso). Método validado, dato ausente.
    Pedir IGC-UPA y mantenimiento de estaciones es ahora evidencia, no suposición.
