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
- **Herramienta de validación** ([dashboard/v6_validacion.html](dashboard/v6_validacion.html)): interfaz para codificar a ciegas una submuestra y calcular la concordancia humano–modelo (κ de Cohen).

## Estructura del repositorio

```
.
├── index.html                 # redirige al dashboard (entrada de GitHub Pages)
├── dashboard/
│   ├── v6_dashboard.html       # dashboard principal (autocontenido)
│   ├── v6_datamap_interactive.html
│   └── v6_validacion.html      # herramienta de validación humana
├── data/                       # datos procesados (corpus, puntajes, tópicos, stats)
├── assets/                     # figuras y mapas
├── agents/
│   ├── prompts/                # prompts de la RSI (v3)
│   └── scripts/                # pipeline de análisis
└── docs/
    └── rubrica_RSI_fundamentacion.md   # fundamentación teórica de la RSI
```

## Ver el dashboard

- **En línea:** https://iortiz1891.github.io/interseccionalidad-clima/
- **En local:** desde la raíz del repo, `python3 -m http.server 8001` y abre `http://localhost:8001/dashboard/v6_dashboard.html`.

## Reproducir

Los datos procesados están incluidos, así que el dashboard se regenera sin re-correr el modelo de lenguaje:

```bash
pip install -r requirements.txt
# desde la raíz del repo:
python3 agents/scripts/20_v1_figures.py          # figuras base
python3 agents/scripts/32_v1_paper_figures.py    # figuras explicativas A–F
python3 agents/scripts/33_v1_topic_insights.py   # stats por tópico + ranking
python3 agents/scripts/28_v1_datamapplot_enhanced.py  # mapa temático interactivo
python3 agents/scripts/34_v1_validation_tool.py  # herramienta de validación
python3 agents/scripts/21_v1_dashboard.py        # dashboard final
```

La cadena completa desde las bases Scopus crudas (ingest → scoring RSI con la API de OpenAI → BERTopic → etiquetado) está documentada en los scripts `30`, `31`, `25` y `27`. Las bases crudas (`.xlsx`) no se incluyen por términos de redistribución.

## Créditos

Revisión sistemática y curaduría del corpus: **Daniel** · Implementación técnica y análisis: **Ivan Ortiz** · 2026.

## Licencia

El código se publica bajo licencia MIT. Los metadatos bibliográficos provienen de Scopus (Elsevier); su reutilización está sujeta a los términos correspondientes.
