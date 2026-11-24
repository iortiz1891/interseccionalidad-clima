# Interseccionalidad y Cambio Climático

### ¿Aplicación sustantiva o invocación nominal?

Una revisión sistemática que mide **en qué medida la investigación sobre cambio climático aplica la interseccionalidad de forma sustantiva, y en qué medida solo la menciona.** Tiene tres versiones:

- **v1** (mayo 2026): **971 registros** recuperados por las cadenas originales (inglés y español), puntuados sin cribado de elegibilidad.
- **v2** (septiembre 2026): **1,696 registros** de una cadena bilingüe más estricta; un cribado previo deja **1,016 trabajos elegibles** que invocan la interseccionalidad en sentido social y tienen un objeto climático.
- **v3** (noviembre 2026): cadenas trilingües (inglés, español y portugués) en **Scopus y SciELO**, con un bloque climático más amplio, más los trabajos en **español y portugués de OpenAlex** (tesis, capítulos de libro, revistas regionales): **2,291 registros** a cribado y **1,221 trabajos elegibles**. Los registros que ya estaban en la v2 con el mismo resumen conservan su evaluación; se evaluaron los 605 nuevos (158 de Scopus y SciELO, 429 de OpenAlex y 18 cuyo resumen se rescató de OpenAlex por DOI). Redalyc se revisó como verificación de cobertura y no aporta registros nuevos ([docs/cadenas_busqueda.md §8.5](docs/cadenas_busqueda.md)).

🔗 **Dashboard interactivo:** https://iortiz1891.github.io/interseccionalidad-clima/

---

## La pregunta

La interseccionalidad —formulada por Crenshaw (1989) para examinar cómo género, clase, raza, etnicidad y territorio operan de forma entrelazada— se volvió un marco de referencia para estudiar la desigualdad ante el clima. Pero su amplia difusión trajo un riesgo que la propia literatura crítica diagnosticó: su invocación **nominal**, como gesto de actualización teórica, sin que el análisis empírico opere con sus principios.

Este proyecto traduce esa crítica —hasta ahora ejercida caso por caso— en una **variable medible** aplicada a todo un corpus.

## El instrumento: Rúbrica de Sustantividad Interseccional (RSI)

La RSI sintetiza la teoría interseccional (Crenshaw, Collins, McCall, Hancock, Bowleg, Collins & Bilge) en un criterio de entrada más seis criterios graduados:

- **Criterio de entrada (gate):** ¿articula dos o más ejes como *relacionados entre sí*, no solo mencionados por separado?
- **I.** Identidades entrelazadas · **II.** Poder estructural · **III.** Contexto situado · **IV.** Método no aditivo · **V.** Praxis y justicia · **VI.** Agencia y resistencia
- **Factor de integración:** ¿se analizan los ejes de forma articulada o en secciones separadas?

La rúbrica se aplica a escala de corpus con un modelo de lenguaje (GPT-4.1 en la v1, Claude en la v2 y la v3), registrando **evidencia textual por criterio** para hacer auditable cada puntaje. El modelo solo asigna los criterios; el total lo calcula el pipeline: `(Σ criterios / 6 × 4) × (0.5 + 0.5 × integración)`, redondeado a múltiplos de 0.5 con los empates hacia arriba y un mínimo de 0.5 si el trabajo pasa el gate. Los puntajes son **provisionales** hasta completar la validación humana (incluida como herramienta en el dashboard).

## Hallazgos principales

- **Adopción ≠ aplicación.** En la v2, el 43.8 % de los trabajos elegibles invoca el marco sin articular ejes de diferenciación (no pasa el gate) y solo el 16 % alcanza aplicación sustantiva (RSI ≥ 2.5). En la v1 las cifras son 57.5 % y 25.7 %, pero ese corpus no tuvo cribado (ver *Advertencias*).
- **La v3 confirma la v2.** Con la búsqueda ampliada a SciELO, OpenAlex y el portugués, las cifras casi no se mueven: 45.5 % no pasa el gate y 15.0 % alcanza aplicación sustantiva.
- **El eslabón débil es el método.** Entre los trabajos que pasan el gate, el criterio metodológico (IV) es el menos cumplido (22 % en la v2, 34 % en la v1): el campo *teoriza* la interseccionalidad mejor de lo que la *opera*.
- **El rigor es de nicho.** La sustantividad no se distribuye al azar: se concentra en vecindarios temáticos concretos (desastres situados, conocimientos indígenas, género y agricultura), visibles en el mapa temático.

## Advertencias metodológicas

- **La v1 no tuvo cribado de elegibilidad.** La cadena en inglés usa `intersection*`, que también recupera frases como «at the intersection of climate and health»; la cadena en español busca en todos los campos (`ALL`), referencias incluidas. Solo cerca de un tercio de los 971 registros menciona *intersectional/interseccional* en el título, el resumen o las palabras clave, y la mayoría de los 219 registros en español no trata el clima. Las proporciones de la v1 incluyen esos registros.
- **La v1 y la v2 no se comparan directamente.** Entre una y otra cambian el corpus, el modelo (gpt-4.1 vía Batch API → Claude en sesiones de Claude Code) y las reglas del gate y de los criterios I y IV (`prompts/v2_cribado_rsi.md`, reglas 3 y 4).
- **La v2 no es reproducible al pie de la letra.** El cribado y la RSI se aplicaron por lotes de 70 registros en sesiones de Claude Code; las reglas comunes se fijaron tras el lote piloto y se aplicaron también a los registros ya escritos; las salidas crudas (`work/`) no se versionan.
- **La v2 casi no tiene trabajos en español.** La cadena bilingüe devolvió 19 registros en español (12 tras la ingesta, 6 elegibles), frente a 219 en la v1. Falta ejecutar las cadenas de Web of Science / SciELO (`docs/cadenas_busqueda.md` §3.2).
- **La v3 reutiliza la evaluación de la v2.** 1,686 de los 2,291 registros ya estaban en la v2 con el mismo resumen (similitud ≥ 0.98 sin la línea de copyright) y conservan su cribado y su RSI; los 605 nuevos (158 de Scopus y SciELO, 429 de OpenAlex, 18 rescatados) se evaluaron con `prompts/v3_cribado_rsi.md`, que es el prompt de la v2 con vocabulario en portugués. La columna `origen_evaluacion` dice de dónde viene cada evaluación.
- **El portugués y el español siguen siendo minoritarios.** La v3 tiene 73 trabajos elegibles en español y 75 en portugués, frente a 1,073 en inglés. Sin OpenAlex serían 17 y 7; pero la búsqueda de OpenAlex es menos fina (sin comodines ni proximidad, lematización en inglés, idioma asignado por el título) y muchos de los nuevos son tesis y capítulos de libro.
- **Redondeo corregido (noviembre 2026).** Hasta entonces el total usaba `round()` de Python, que manda los empates al número par (2.5 → 2 pero 1.5 → 2) y bajaba de categoría a 44 trabajos de la v1 y 114 de la v2. Los totales se recalcularon con `pipeline/recalcular_totales.py`, sin volver a llamar al modelo; las muestras de validación se conservaron.

## El dashboard

El dashboard tiene tres pestañas:

- **v1 · corpus original** (mayo 2026): las 971 publicaciones de las cadenas de búsqueda originales.
- **v2 · búsqueda ampliada** (septiembre 2026, [site/v2/](site/v2/index.html)): una cadena bilingüe nueva en Scopus ([docs/cadenas_busqueda.md §3](docs/cadenas_busqueda.md)). Agrega un cribado de elegibilidad antes de la RSI y se construye solo con esos datos, sin reutilizar registros ni puntajes de la v1.
- **v3 · Scopus + SciELO + OpenAlex** (noviembre 2026, [site/v3/](site/v3/index.html)): cadenas trilingües en Scopus (por la API) y SciELO ([docs/cadenas_busqueda.md §7](docs/cadenas_busqueda.md)), más los trabajos en español y portugués que OpenAlex recupera con las mismas cadenas (§8). Misma rúbrica, mismo modelo y mismas reglas que la v2; tiene su propia herramienta de validación y su lista del corpus.


Una sola página que recorre el marco, el corpus, los hallazgos y el método. Incluye:

- **Mapa temático interactivo** (33 tópicos): se puede colorear por tópico, por nivel RSI del trabajo o por RSI medio del vecindario; resaltar el sub-corpus de la tesis; y, al hacer clic en un punto, ver la **justificación del modelo por cada criterio**.
- **Figuras explicativas** (perfil por criterio, embudo del gate, ranking de tópicos, asimetría por idioma…).
- **Herramienta de validación**, en la pestaña v2 ([site/v2/validacion.html](site/v2/validacion.html)): un evaluador repite a ciegas los pasos del LLM sobre una muestra de 140 trabajos (20 bloques de 7, con registros incluidos y excluidos de todos los niveles). Los pasos son inclusión, gate, criterios I–VI e integración, con las mismas definiciones y reglas del prompt. La página calcula el puntaje RSI con la fórmula del pipeline y la concordancia del cribado, el gate, cada criterio y la categoría RSI (κ de Cohen, κ ponderado, IC bootstrap). Las respuestas del LLM no están en la página: se cargan solo al pedir la concordancia.
- **Lista completa del corpus**, en la pestaña v2 ([site/v2/corpus.html](site/v2/corpus.html)): los 1,696 registros cribados con la decisión del LLM, el puntaje RSI, los criterios, la evidencia y el tópico. Tiene búsqueda, filtros compartibles por URL y descarga en CSV.

## Arquitectura del repositorio

Separación clara entre el **sitio publicado**, los **datos**, el **pipeline** y la **documentación**:

```
.
├── index.html              # redirección a site/ (entrada de GitHub Pages)
├── site/                   # SITIO PUBLICADO (autocontenido)
│   ├── index.html          #   · dashboard principal
│   ├── mapa.html           #   · mapa temático interactivo
│   ├── validacion.html     #   · herramienta de validación humana
│   ├── v2/                 #   · pestaña v2 (index, mapa, validación y lista del corpus de la búsqueda ampliada)
│   └── v3/                 #   · pestaña v3 (Scopus + SciELO + OpenAlex ES/PT)
├── data/                   # datos procesados (corpus, puntajes, tópicos, estadísticas)
├── assets/                 # figuras y mapas estáticos
├── prompts/                # prompts del modelo (Rúbrica de Sustantividad Interseccional)
├── pipeline/               # scripts de reproducción, en orden lógico (01 → 12)
│   ├── v2/                 #   · pipeline de la búsqueda ampliada (01 → 13)
│   └── v3/                 #   · pipeline de la v3 (00 → 13)
├── docs/                   # fundamentación teórica de la RSI
├── requirements.txt
└── LICENSE
```

El **pipeline** está numerado según el flujo real de datos:

| # | Script | Qué hace |
|---|--------|----------|
| 01 | `ingesta_corpus.py` | Consolida las bases Scopus (EN + ES) en el corpus de trabajo |
| 02 | `scoring_rsi.py` | Aplica la rúbrica RSI con el modelo de lenguaje (Batch API) y define la fórmula del total |
| — | `recalcular_totales.py` | Recalcula totales y categorías (v1 y v2) desde los criterios guardados, sin llamar al modelo |
| 03 | `modelado_topicos.py` | BERTopic + optimización de hiperparámetros |
| 04 | `etiquetado_topicos.py` | Etiqueta los tópicos con un modelo de lenguaje |
| 05 | `analisis_cruzados.py` | Cruces RSI × tópico / idioma / país |
| 06 | `estadisticas.py` | Estadística descriptiva del corpus |
| 07 | `figuras.py` | Figuras base (distribución, PRISMA, temporal…) |
| 08 | `figuras_explicativas.py` | Figuras del método (perfil por criterio, embudo…) |
| 09 | `insights_topicos.py` | Estadísticas por tópico + ranking de sustantividad |
| 10 | `mapa_interactivo.py` | Mapa temático interactivo (`site/mapa.html`) |
| 11 | `validacion.py` | Herramienta de validación humana (`site/validacion.html`) |
| 12 | `dashboard.py` | Ensambla el dashboard final (`site/index.html`) |

## Ver el dashboard

- **En línea:** https://iortiz1891.github.io/interseccionalidad-clima/
- **En local:** desde la raíz del repo, `python3 -m http.server 8001` y abre `http://localhost:8001/site/`.

## Reproducir

Los datos procesados están incluidos, así que el dashboard se regenera **sin re-correr el modelo de lenguaje**. Desde la raíz del repo:

```bash
pip install -r requirements.txt

python3 pipeline/07_figuras.py               # figuras base
python3 pipeline/08_figuras_explicativas.py  # figuras del método
python3 pipeline/09_insights_topicos.py      # stats por tópico + ranking
python3 pipeline/10_mapa_interactivo.py      # mapa temático → site/mapa.html
python3 pipeline/11_validacion.py            # validación → site/validacion.html
python3 pipeline/12_dashboard.py             # dashboard → site/index.html
```

Para la v2 o la v3, cambia `pipeline/` por `pipeline/v2/` o `pipeline/v3/` y corre `05`, `06`, `07`, `08`, `09`, `09b`, `10`, `11`, `12` y `13`. Si cambia la fórmula del total, corre antes `python3 pipeline/recalcular_totales.py`. Los pasos `11` conservan la muestra de validación ya sorteada (con `--remuestrear` se sortea otra).

La cadena completa desde las bases Scopus crudas (`01` ingesta → `02` scoring con la API de OpenAI → `03` BERTopic → `04` etiquetado → `05`/`06` análisis) requiere las bases crudas (`.xlsx`), que **no se incluyen** por términos de redistribución, y una clave de API de OpenAI (`OPENAI_API_KEY`) para el scoring.

### Pipeline v2 (búsqueda ampliada)

La pestaña v2 es una **réplica de la v1 con la búsqueda nueva**. Los pasos 05–12 son copias de los scripts de la v1 que cambian solo las rutas de datos (`data/v2_*`, `assets/v2_*`, `site/v2/`) y los textos que en la v1 tenían cifras escritas a mano.

| # | Script | Qué hace |
|---|--------|----------|
| 01 | `v2/01_ingesta_scopus.py` | Ingesta del export de Scopus, exclusiones por regla, deduplicación y nivel del ancla |
| 02 | `v2/02_preparar_lotes.py` | Divide el corpus en lotes para el cribado y la RSI |
| — | `v2/validar_lote.py` | Valida cada lote contra el esquema de `prompts/v2_cribado_rsi.md` |
| 03 | `v2/03_consolidar.py` | Une los lotes, aplica la reevaluación del gate y calcula la RSI con la misma fórmula de la v1 |
| 04 | `v2/04_topicos.py` · `04b_etiquetas.py` | BERTopic sobre los elegibles y etiquetas de los tópicos |
| 05–12 | `v2/05_analisis_cruzados.py` … `v2/12_dashboard.py` | Réplica de los pasos 05–12 de la v1 |
| 09b | `v2/09b_mapa_estatico.py` | Mapa temático estático y versión Plotly (equivalente al paso de la v1 que no está en el repo) |
| 11 | `v2/11_validacion.py` | Validación humana: muestra por bloques, inclusión + RSI, concordancia (`site/v2/validacion.html` + `validacion_llm.js`) |
| 13 | `v2/13_lista_corpus.py` | Lista completa del corpus con búsqueda y filtros (`site/v2/corpus.html`) |

El cribado, la codificación y la RSI de la v2 los aplicó Claude (claude-opus-5-5) con `prompts/v2_cribado_rsi.md`, en lotes independientes. El export crudo de Scopus (`data/v2_scopus_raw.csv`) no se versiona.

### Pipeline v3 (Scopus + SciELO + OpenAlex)

La v3 replica la v2 con las cadenas nuevas. Los pasos 05–13 son copias de los de la v2 con rutas `data/v3_*`, `assets/v3_*` y `site/v3/`; cambian el PRISMA (tres fuentes) y los textos sobre la búsqueda, el idioma y el origen de cada evaluación. Los tópicos (paso 04) usan un modelo de embeddings multilingüe.

| # | Script | Qué hace |
|---|--------|----------|
| 00 | `v3/00_scopus_api.py` | Corre la cadena de `data/v3_query_scopus.txt` en la Scopus Search API (vista COMPLETE). La cadena no cabe en una petición: parte el bloque climático en grupos unidos por OR y une los resultados por EID |
| 00b | `v3/00b_openalex.py` | Corre `data/v3_query_openalex.json` en la API de OpenAlex (`title_and_abstract.search`, idioma `es\|pt`). Parte los bloques en grupos, corre todas las combinaciones y une por ID de OpenAlex; reconstruye el resumen del índice invertido |
| 00c | `v3/00c_resumenes_openalex.py` | Busca por DOI en OpenAlex el resumen de los registros que llegan sin resumen de su fuente (`data/v3_resumenes_openalex.json`) |
| 01 | `v3/01_ingesta.py` | Une Scopus y SciELO (`data/v3_scielo_export.json`), excluye por regla, deduplica, marca el ancla y el idioma, y enlaza cada registro con la v2. Después agrega OpenAlex: mismas exclusiones, deduplicación contra Scopus y SciELO, y `paper_id` a partir del último de esas dos fuentes. Por último rescata los resúmenes de OpenAlex que cumplen las reglas (≥20 palabras además del título, DOI no compartido, no es la descripción del libro) |
| 02 | `v3/02_preparar_lotes.py` | Lotes de 40 con los registros que no reutilizan la evaluación de la v2 (`lote_XX` para Scopus y SciELO, `oa_lote_XX` para OpenAlex, `rs_lote_XX` para los resúmenes rescatados) |
| 03 | `v3/03_consolidar.py` | Une la evaluación reutilizada de la v2 con la nueva (`work/v3_salidas/`, versionada) y calcula la RSI |
| 04 | `v3/04_topicos.py` · `04b_etiquetas.py` | BERTopic con `paraphrase-multilingual-MiniLM-L12-v2` (con el modelo solo en inglés, los trabajos en español y portugués se agrupan por idioma) y etiquetas manuales de los tópicos |
| 05–13 | `v3/05_analisis_cruzados.py` … `v3/13_lista_corpus.py` | Réplica de los pasos de la v2 |

Para el paso 00 hace falta una clave de la API de Elsevier (`SCOPUS_API_KEY`, y `SCOPUS_INSTTOKEN` fuera de la red institucional), como variable de entorno o en `~/.config/scopus_creds`. La respuesta cruda (`data/v3_scopus_raw.csv`, `work/v3_scopus_api/`) no se versiona. El export de SciELO se descargó de search.scielo.org en formato RIS. El paso 00b no necesita clave: la consulta cabe en el presupuesto diario gratuito de OpenAlex. Con una clave (gratuita, en openalex.org) se puede guardar como `OPENALEX_API_KEY` en el entorno o en `~/.config/openalex_creds`. La respuesta cruda de OpenAlex (`data/v3_openalex_raw.csv`, `work/v3_openalex/`) tampoco se versiona.

## Créditos

Revisión sistemática y curaduría del corpus: **Daniel** · Implementación técnica y análisis: **Ivan Ortiz** · 2026.

## Licencia

El código se publica bajo licencia MIT. Los metadatos bibliográficos provienen de Scopus (Elsevier); su reutilización está sujeta a los términos correspondientes.
