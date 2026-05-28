# Interseccionalidad y Cambio Climático

### ¿Aplicación sustantiva o invocación nominal?

Una revisión sistemática que mide **en qué medida la investigación sobre cambio climático aplica la interseccionalidad de forma sustantiva, y en qué medida solo la menciona.** El análisis cubre **971 trabajos** indexados en Scopus (inglés y español) que invocan explícitamente la interseccionalidad en torno al clima o a eventos extremos.

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

La rúbrica se aplica a escala de corpus con un modelo de lenguaje de gran escala (GPT-4.1), registrando **evidencia textual por criterio** para hacer auditable cada puntaje. El procedimiento es transparente y versionado; los puntajes son **provisionales** hasta completar la validación humana (incluida como herramienta en el dashboard).

## Hallazgos principales

- **Adopción ≠ aplicación.** El 57.5 % del corpus invoca el marco sin articular ejes de diferenciación; solo una minoría alcanza aplicación sustantiva.
- **El eslabón débil es el método.** Entre los trabajos que sí aplican el marco, el criterio metodológico (IV) es el menos cumplido: el campo *teoriza* la interseccionalidad mejor de lo que la *opera*.
- **El rigor es de nicho.** La sustantividad no se distribuye al azar: se concentra en vecindarios temáticos concretos (desastres situados, conocimientos indígenas, género y agricultura), visibles en el mapa temático.

## El dashboard

Una sola página que recorre el marco, el corpus, los hallazgos y el método. Incluye:

- **Mapa temático interactivo** (33 tópicos): se puede colorear por tópico, por nivel RSI del trabajo o por RSI medio del vecindario; resaltar el sub-corpus de la tesis; y, al hacer clic en un punto, ver la **justificación del modelo por cada criterio**.
- **Figuras explicativas** (perfil por criterio, embudo del gate, ranking de tópicos, asimetría por idioma…).
- **Herramienta de validación** ([site/validacion.html](site/validacion.html)): interfaz para codificar a ciegas una submuestra y calcular la concordancia humano–modelo (κ de Cohen).

## Arquitectura del repositorio

Separación clara entre el **sitio publicado**, los **datos**, el **pipeline** y la **documentación**:

```
.
├── index.html              # redirección a site/ (entrada de GitHub Pages)
├── site/                   # SITIO PUBLICADO (autocontenido)
│   ├── index.html          #   · dashboard principal
│   ├── mapa.html           #   · mapa temático interactivo
│   └── validacion.html     #   · herramienta de validación humana
├── data/                   # datos procesados (corpus, puntajes, tópicos, estadísticas)
├── assets/                 # figuras y mapas estáticos
├── prompts/                # prompts del modelo (Rúbrica de Sustantividad Interseccional)
├── pipeline/               # scripts de reproducción, en orden lógico (01 → 12)
├── docs/                   # fundamentación teórica de la RSI
├── requirements.txt
└── LICENSE
```

El **pipeline** está numerado según el flujo real de datos:

| # | Script | Qué hace |
|---|--------|----------|
| 01 | `ingesta_corpus.py` | Consolida las bases Scopus (EN + ES) en el corpus de trabajo |
| 02 | `scoring_rsi.py` | Aplica la rúbrica RSI con el modelo de lenguaje (Batch API) |
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

La cadena completa desde las bases Scopus crudas (`01` ingesta → `02` scoring con la API de OpenAI → `03` BERTopic → `04` etiquetado → `05`/`06` análisis) requiere las bases crudas (`.xlsx`), que **no se incluyen** por términos de redistribución, y una clave de API de OpenAI para el scoring.

## Créditos

Revisión sistemática y curaduría del corpus: **Daniel** · Implementación técnica y análisis: **Ivan Ortiz** · 2026.

## Licencia

El código se publica bajo licencia MIT. Los metadatos bibliográficos provienen de Scopus (Elsevier); su reutilización está sujeta a los términos correspondientes.
