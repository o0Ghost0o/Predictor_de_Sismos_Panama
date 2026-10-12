<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Área de estudio</h1>
      <p class="text-sm text-slate-400">Hipótesis, experimentos y su veredicto — lo que funcionó y lo que no.</p>
    </div>

    <div class="card p-5 text-sm leading-relaxed text-slate-300">
      <h2 class="mb-2 font-semibold text-slate-100">1 · Clima y sismos</h2>
      <p>Hipótesis: temperatura/humedad/presión aportan señal. Ablación: sísmico solo PR-AUC 0.20 →
      +clima 0.24. El clima suma un poco; la señal principal es sísmica. Auditoría de leakage:
      features ≤ día D, etiqueta (D, D+7] — sin fuga; clima pronóstico ≡ archivo en fechas pasadas (RMSE 0).</p>
    </div>

    <div class="card p-5 text-sm leading-relaxed text-slate-300">
      <h2 class="mb-2 font-semibold text-slate-100">2 · RSI / volatilidad / Benioff acumulado</h2>
      <p>RSI(14) sobre tasa y energía + volatilidad 30d + deformación de Benioff desde el último M4+.
      El modelo los usa (top-6 importancia) pero test baja 0.241 → 0.224: con 93% de días en cero,
      el RSI oscila sobre ruido. Equivale al AMR (accelerating moment release) de la literatura —
      necesita catálogo denso (M2+) para brillar.</p>
    </div>

    <div class="card p-5 text-sm leading-relaxed text-slate-300">
      <h2 class="mb-2 font-semibold text-slate-100">3 · ETAS: la física manda</h2>
      <p>ETAS temporal por zona (μ, K ajustados; p=1.1, c=0.01, α=1.0 fijos): test PR-AUC 0.237,
      <strong>ROC 0.791</strong> — mejor ranking que cualquier ML probado. El MLE completo diverge
      con 42–628 eventos (ridge μ→0/K→∞ por un signo en la integral, ya corregido): los catálogos
      ralos piden parametrización parsimoniosa. Coherente con Mármara 2026 y RECAST (&gt;10⁴ eventos para batir ETAS).</p>
    </div>

    <div class="card p-5 text-sm leading-relaxed text-slate-300">
      <h2 class="mb-2 font-semibold text-slate-100">4 · Multipass / correctores de error</h2>
      <p>Stacking LGBM+LSTM+Transformer (0.245, +0.004), cascada AND (misma precisión 18%),
      LR portero de fallos (13%, peor), umbrales por zona (recorta 56% falsas pero pierde mitad de aciertos).
      Ningún segundo modelo sobre los mismos 14 features corrige al primero: errores correlacionados.</p>
    </div>

    <div class="card p-5 text-sm leading-relaxed text-slate-300">
      <h2 class="mb-2 font-semibold text-slate-100">6 · Segundo evaluador: dial de réplicas 24h/1h</h2>
      <p>ETAS a horizonte corto como evaluador independiente, activo tras M6+.
      Hindcast test: PR-AUC 0.040 global (base 1.5%), pero <strong>0.232 en días de
      secuencia</strong> (≤14d tras M5.5+, base 9.2%) vs 0.044 en calma. Hoy: Azuero 88.7%/24h, 30%/1h.
      El modo dual queda validado: vigilia 7d siempre + dial cuando tiembla.</p>
    </div>

    <div class="card p-5 text-sm leading-relaxed text-slate-300">
      <h2 class="mb-2 font-semibold text-slate-100">5 · Referencias abiertas (verificadas oct-2026)</h2>
      <ul class="list-disc space-y-1 pl-5">
        <li><a class="underline" href="https://cseptesting.org" target="_blank">CSEP</a> — experimentos prospectivos ·
          <a class="underline" href="https://github.com/cseptesting/pycsep" target="_blank">pyCSEP</a> ·
          <a class="underline" href="https://doi.org/10.21105/joss.09408" target="_blank">floatCSEP</a> ·
          <a class="underline" href="https://doi.org/10.1038/s41597-025-05766-3" target="_blank">benchmark California</a></li>
        <li>ETAS (Ogata 1988) — baseline obligatorio · <a class="underline" href="https://doi.org/10.1038/s41467-026-76243-7" target="_blank">validez decadal 2026</a></li>
        <li><a class="underline" href="https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023GL103909" target="_blank">RECAST</a> ·
          <a class="underline" href="https://openreview.net/pdf?id=dIcNAg6ZuZ" target="_blank">EarthquakeNPP</a> ·
          <a class="underline" href="https://www.nature.com/articles/s41598-025-93877-7" target="_blank">SafeNet</a> ·
          <a class="underline" href="https://eartharxiv.org/repository/view/13850" target="_blank">Mármara 2026</a></li>
        <li><a class="underline" href="https://doi.org/10.1029/2023RG000823" target="_blank">Review Mizrahi et al. 2024</a> ·
          <a class="underline" href="https://doi.org/10.1029/2022JB025202" target="_blank">catálogos DL alta resolución</a></li>
        <li>Catálogos: <a class="underline" href="https://earthquake.usgs.gov/fdsnws/event/1/" target="_blank">USGS FDSN</a> ·
          <a class="underline" href="https://open-meteo.com/" target="_blank">Open-Meteo</a> · IGC-UPA (pendiente)</li>
      </ul>
      <p class="mt-2 text-xs text-slate-500">Detalle con DOIs en <NuxtLink class="underline" to="/docs/06-research">docs/06-research</NuxtLink>.</p>
    </div>
  </div>
</template>
