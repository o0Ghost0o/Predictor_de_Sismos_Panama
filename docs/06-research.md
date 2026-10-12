# 06 · Research y fuentes

Verificación: todos los enlaces resuelven (oct-2026). Si alguno muere, buscar por DOI.

## Experimentos prospectivos (el estándar que imitamos)
- [CSEP Testing Center](https://cseptesting.org) y [publicaciones](https://cseptesting.org/publications)
- [pyCSEP](https://github.com/cseptesting/pycsep) — toolkit abierto (SRL 2022, [doi](https://doi.org/10.1785/0220220033)); [docs](https://docs.cseptesting.org)
- [floatCSEP](https://doi.org/10.21105/joss.09408) — orquestación reproducible de experimentos (JOSS 2026)
- [Benchmark 10 años California](https://doi.org/10.1038/s41597-025-05766-3) (*Sci Data* 2025) — dataset Zenodo + pyCSEP
- [Modelos operacionales vs década observada](https://doi.org/10.1038/s41467-026-76243-7) (*Nat Comm* 2026) — evidencia de que ETAS bien calibrado sostiene skill decadal
- [Prácticas actuales y futuro](https://doi.org/10.1029/2023RG000823) (Mizrahi et al., *Rev Geophys* 2024) — review de referencia
- [Década de Italia](https://doi.org/10.1785/0220230247) (SRL 2024) — ejemplo de experimento decadal

## ML vs física
- [RECAST](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023GL103909) (Dascher-Cousineau et al., GRL 2023) — deep learning que iguala ETAS con >10⁴ eventos
- [EarthquakeNPP](https://openreview.net/pdf?id=dIcNAg6ZuZ) (TMLR 2026) — benchmark procesos puntuales neuronales
- [SafeNet](https://www.nature.com/articles/s41598-025-93877-7) (*Sci Rep* 2025) — fusión multimodal P(M≥m) anual
- [Mármara 2026](https://eartharxiv.org/repository/view/13850) (EarthArXiv) — ML no suma ranking sobre ETAS; foreshock 36min + ~220 falsas
- [Catálogos DL de alta resolución](https://doi.org/10.1029/2022JB025202) (Mancini et al., JGR 2022) — beneficios y límites actuales

## Datos que usamos
- [USGS FDSN Event API](https://earthquake.usgs.gov/fdsnws/event/1/) — catálogo (ver `src/ingest/api_usgs.py`)
- [Open-Meteo](https://open-meteo.com/) — archivo + pronóstico (ver `src/ingest/weather.py`)
- IGC-UPA — catálogo local M2+ (**pendiente integrar**)
- NGL ([lista global](https://geodesy.unr.edu/NGLStationPages/GlobalStationList), [portal](https://geodesy.unr.edu/PlugNPlayPortal.php)) —
  COCONet en Panamá: CN20 (Bocas, viva hasta ago-2026), VLCN (Chiriquí, muerta 2018),
  CN28 (Central, muerta 2023), CN33 (Azuero, muerta 2018), CN34 (Darién, muerta 2017).
  Cobertura útil en test: **12%** → features GNSS sin señal. La red local necesita mantenimiento.

Conceptos: ETAS (Ogata 1988), Omori, Gutenberg-Richter/b-value (futuro), Benioff/AMR, Molchan (futuro).
