# Predictor de Sismos Panamá — Documentación

PoC de investigación: pronóstico probabilístico `P(M4+ en 7 días)` por zona de Panamá.
**No es predicción determinista. Investigación, no alerta oficial.**

| Doc | Contenido |
|---|---|
| [01-objetivos](01-objetivos.md) | Por qué existe, qué queremos lograr, no-objetivos |
| [02-datos](02-datos.md) | Fuentes, volúmenes, zonas, ingesta recurrente |
| [03-metodologia](03-metodologia.md) | Etiquetas, splits, features, modelos |
| [04-decisiones](04-decisiones.md) | ADRs: cada decisión y en qué se basó |
| [05-evaluacion](05-evaluacion.md) | Todos los resultados y comparativas |
| [06-research](06-research.md) | Estado del arte abierto y referencias |
| [07-operacion](07-operacion.md) | Servidores, mini-CSEP, ética |
| [08-roadmap](08-roadmap.md) | Pendientes ordenados |

Stack: Python (LightGBM, scikit-learn, PyTorch, DuckDB/Parquet, FastAPI) + Nuxt 4 web.
Ver README raíz para quickstart.
