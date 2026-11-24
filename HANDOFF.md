# HANDOFF — Interseccionalidad y Cambio Climático

**Última actualización:** 2026-11-24
**Repo:** https://github.com/iortiz1891/interseccionalidad-clima
**Dashboard en vivo:** https://iortiz1891.github.io/interseccionalidad-clima/

---

## 1. Lo esencial en 30 segundos

- **Qué es:** revisión sistemática que mide, con una rúbrica (RSI) aplicada por LLM, en qué medida la investigación sobre cambio climático **aplica** interseccionalidad vs. solo la **menciona**.
- **Corpus v1:** 971 registros Scopus (752 EN + 219 ES, mayo 2026) consolidados por Daniel, **sin cribado de elegibilidad**.
- **Corpus v2:** 1,696 registros de la cadena bilingüe (30-09-2026); el cribado deja 1,016 elegibles. Solo 12 registros en español.
- **Corpus v3:** cadenas trilingües en Scopus (API) y SciELO (24-11-2026): 1,844 registros a cribado, 1,088 elegibles (17 en español, 7 en portugués). 1,686 registros conservan la evaluación de la v2; los 158 nuevos se evaluaron con `prompts/v3_cribado_rsi.md`.
- **Corpus v4:** el de la v3 más OpenAlex en español y portugués (24-11-2026): 2,273 registros a cribado, 1,212 elegibles (73 en español, 75 en portugués). Los 1,844 de la v3 conservan su evaluación; los 429 nuevos de OpenAlex se evaluaron con el mismo prompt.
- **Instrumento:** Rúbrica de Sustantividad Interseccional (RSI) — gate + 6 criterios graduados + factor de integración. Fundamentada en Crenshaw, Collins, Hancock, McCall, Bowleg.
- **Scoring vigente:** v1 con `gpt-4.1` vía Batch API de OpenAI (`prompts/bowleg_eval_v3.md` + `reasoning_v3.md`); v2 con Claude (claude-opus-5-5) en sesiones de Claude Code (`prompts/v2_cribado_rsi.md`). **Provisional** — pendiente validación humana con κ de Cohen.
- **Resultado principal (v2):** 43.8% de los elegibles no pasa el gate (RSI=0); 16% alcanza RSI ≥ 2.5. El eslabón débil es el criterio IV (método no aditivo). En la v1: 57.5% y 25.7%, sobre un corpus sin cribar.
- **Fórmula del total (desde 2026-11-24):** empates hacia arriba y mínimo 0.5 si pasa el gate (antes, `round()` de Python mandaba los empates al par). Ver `pipeline/recalcular_totales.py`.

**Dos entregables esperados:**
1. **Manuscrito Íconos (FLACSO Ecuador)** — sobre el campo general.
2. **Tesis de Daniel** — ciclones × CC × interseccionalidad × México costero (sub-corpus de 97 papers; se dispersa en 25 tópicos, no forma cluster propio).

---

## 2. Arquitectura: repo publicado vs. working directory local

### 2.1 Repo publicado (fuente de verdad, limpio)

```
iortiz1891/interseccionalidad-clima
├── site/                    ← dashboard (publicado por GitHub Pages)
│   ├── index.html           ·  pestaña v1
│   ├── mapa.html            ·  mapa temático interactivo v1
│   ├── validacion.html      ·  validación v1 (ya no se enlaza desde el dashboard)
│   └── v2/                  ·  pestaña v2: index, mapa, validacion (+ validacion_llm.js), corpus
├── data/                    ← CSV/JSON con prefijo v1_* y v2_*
├── pipeline/                ← 01→12 de la v1 + recalcular_totales.py
│   └── v2/                  ·  01→13 de la v2
├── prompts/                 ← bowleg_eval_v3.md, reasoning_v3.md, v2_cribado_rsi.md
├── docs/                    ← rubrica_RSI_fundamentacion.md, cadenas_busqueda.md
└── assets/                  ← figuras v6_* (v1) y v2_*
```

### 2.2 Working directory local (historia completa, no publicado)

```
<Google Drive>/My Drive/Daniel_LiteratureReview_May2026/
├── Daniel_databases_project/        ← mirror local con historia completa (NO es git)
│   ├── agents/scripts/              ·  36 scripts (01-34 + variantes), incluye iteraciones
│   ├── data/                        ·  mismos v1_* + xlsx crudos de Daniel + logs
│   ├── docs/
│   ├── dashboard/
│   └── assets/
├── Daniel Data/                     ← bases Scopus originales (xlsx)
│   ├── scopus (17)_En.xlsx          ·  765 registros, inglés
│   └── BD_2026_Scopus_Spanish.xlsx  ·  222 registros, español
├── outputs/                         ← artefactos vivos de sesiones previas
└── _manuscrito_no_servido/          ← drafts manuscrito Íconos
```

**Drift conocido:** el repo tiene los 12 scripts limpios y renombrados; el local tiene 36 scripts con historia iterativa. Si tocas pipeline, hazlo en el repo y re-sincroniza manualmente al local si lo necesitas.

---

## 3. Historial de sesiones

### 2026-11-24 — rama `feat/v4-openalex` (sobre `feat/v3-busqueda-revisada`)

- Nueva pestaña **v4** = corpus v3 + trabajos en español y portugués de OpenAlex. Pipeline en `pipeline/v4/` (00 → 13), datos `data/v4_*`, figuras `assets/v4_*`, sitio `site/v4/`; las pestañas v1–v3 enlazan a la v4.
- OpenAlex por la API (`00_openalex.py`, sin clave): las cadenas v3 traducidas a filtros `title_and_abstract.search` con términos unidos por `|` (`data/v4_query_openalex.json`); 8 consultas, 470 trabajos únicos. Tras exclusiones y deduplicación contra la v3 quedan 429 nuevos (107 tesis, 45 capítulos).
- Los 429 se evaluaron en 11 lotes de 40 con subagentes de Claude Code (`prompts/v3_cribado_rsi.md`); salidas versionadas en `work/v4_salidas/`. Mucho ruido de búsqueda (OpenAlex lematiza *intersectional* → *intersection*): 124 elegibles.
- Resultado: 1,212 elegibles; 45.3 % no pasa el gate y 15.0 % es sustantivo (v3: 44.3 % y 15.6 %). Los nuevos de OpenAlex pasan menos el gate (46 % frente a 56 % de los evaluados en la v2).

### 2026-11-24 — rama `feat/v3-busqueda-revisada` (sobre `fix/redondeo-rsi-y-textos`)

- Nueva pestaña **v3** con las cadenas revisadas (Scopus + SciELO, EN/ES/PT). Pipeline en `pipeline/v3/` (00 → 13), datos `data/v3_*`, figuras `assets/v3_*`, sitio `site/v3/`; las pestañas de v1 y v2 enlazan a la v3.
- Scopus por la API (`00_scopus_api.py`): la cadena se parte en grupos del bloque climático porque no cabe en una petición; 1,882 registros únicos. SciELO: export RIS (34).
- Se reutiliza el cribado y la RSI de la v2 cuando el registro y su resumen coinciden (1,686). Los 158 nuevos se evaluaron en 4 lotes de 40 con subagentes de Claude Code; las salidas quedan versionadas en `work/v3_salidas/`.
- Resultado: 1,088 elegibles; 44.3 % no pasa el gate y 15.6 % es sustantivo (v2: 43.8 % y 16.0 %). 15 tópicos BERTopic con etiquetas manuales (`data/v3_topic_labels_manual.json`).

### 2026-11-24 — rama `fix/redondeo-rsi-y-textos`

- `compute_total` deja de usar `round()` de Python (empates al par): ahora redondea los empates hacia arriba y da un mínimo de 0.5 a todo trabajo que pasa el gate. Cambian 44 totales de la v1 y 114 de la v2; se recalcularon con `pipeline/recalcular_totales.py` y se regeneró todo (05–12 v1, 05–13 v2).
- La herramienta de validación (v1 y v2) usa la misma fórmula y **conserva la muestra ya sorteada** (`--remuestrear` para sortear otra).
- Ejemplo B del prompt: decía «parcial (~1.5–2)» pero la fórmula da 1.0 (nominal); se corrigió el rótulo y se dejó la errata en el frontmatter.
- Textos: advertencias sobre la v1 sin cribado, la comparabilidad v1/v2 y la reproducibilidad de la v2; versiones fijas de deck.gl y apache-arrow en los mapas.

### 2026-09-28

| # | Commit | Qué cambió |
|---|---|---|
| 1 | `e7f851a` | **Nuevo:** `docs/cadenas_busqueda.md` — documenta las cadenas Scopus v1 ejecutadas por Daniel + propone v2 potenciada (v2a recomendada / v2b exploratoria / v2c sub-corpus tesis) |
| 2 | `a3f9e7d` | Actualiza `pipeline/12_dashboard.py` — añade entrada "Cadenas de búsqueda" al sidebar + sección "2b · Estrategia de búsqueda" entre PRISMA y Distribución RSI |
| 3 | `ec20324` | Actualiza `site/index.html` desplegado con el mismo contenido (para que GitHub Pages lo muestre sin regenerar) |

**Novedad clave:** las cadenas de búsqueda ya están documentadas y visibles. Antes no estaban en ninguna parte del repo (vivían solo en el script local `Daniel_databases_project/agents/scripts/01_search.py`).

---

## 4. Estado del corpus y scoring

### Flujo PRISMA real

```
Scopus EN (xlsx manual)   752  ─┐
Scopus ES (xlsx manual)   219  ─┤→ 971 (filtro abstract ≥100 chars: −13; dedup DOI+título: −3)
Bruto                     987  ─┘
```

### Distribución RSI (provisional, fórmula corregida el 2026-11-24)

| Categoría | v1 · gpt-4.1 (971, sin cribado) | v2 · Claude (1,016 elegibles) |
|---|---:|---:|
| Mención sin aplicación (0) | 57.5% · 558 | 43.8% · 445 |
| Nominal/débil (0.5–1.0) | 4.1% · 40 | 8.9% · 90 |
| Parcial (1.5–2.0) | 12.8% · 124 | 31.3% · 318 |
| Sustantiva (2.5–3.0) | 6.6% · 64 | 10.1% · 103 |
| Sustantiva fuerte (3.5–4.0) | 19.1% · 185 | 5.9% · 60 |

Las dos columnas no se comparan directamente: cambian el corpus, el modelo y las reglas del gate.

### Hallazgos actuales

1. **Adopción ≠ aplicación.** Mayoría nominal.
2. **Eslabón débil = método (IV).** Entre papers que pasan el gate, solo 34% operacionaliza. 70%+ cumplen poder estructural (II) y praxis (V).
3. **La sustantividad es de nicho.** Se concentra en desastres situados, conocimientos indígenas, género × agricultura. BERTopic con 33 tópicos.

---

## 5. Pendientes priorizados

### Alta prioridad

1. **Validación humana de la v2** — codificar la muestra de `site/v2/validacion.html` (140 trabajos en 20 bloques; al menos 10 bloques) y calcular κ de Cohen frente al LLM.
2. **Cobertura en español** — la v2 solo tiene 12 registros en español. Ejecutar las cadenas de Web of Science / SciELO (`docs/cadenas_busqueda.md` §3.2) antes del manuscrito Íconos y de la tesis.
3. **Decidir qué hacer con la v1** — no tuvo cribado: solo ~1/3 menciona *intersectional/interseccional* y la mayoría de los registros en español no trata el clima. Opciones: cribarla con el Paso 0 de `prompts/v2_cribado_rsi.md` o reportar solo la v2.
4. **Reproducibilidad de la v2** — versionar las salidas crudas de `work/v2_salidas` y `work/v2_reevaluacion`, o rehacer el scoring con un script por API. Revisar también que la reevaluación del gate (regla 3 corregida) solo se aplicó a los 421 que no pasaban; la regla nueva también añade restricciones que podrían afectar a los que sí pasaban.
5. *(Nota histórica: una versión anterior de este archivo hablaba de GPT-4o-mini con κ = 0.038 frente a Sonnet; el scoring vigente de la v1 es gpt-4.1.)*

6. **Revisar casos dudosos de los lotes nuevos de la v3** — los evaluadores marcaron gates límite (v3 paper_id 143, 237, 278, 385, 412, 803, 1103, 1397) y climas incidentales (18, 123, 1611, 1697, 1805). El registro 295 tiene una inconsistencia en el resumen (cita el EACOP, un oleoducto de África oriental, en un caso del Delta del Níger): conviene verificarlo.

7. **Revisar casos dudosos de los lotes de OpenAlex (v4)** — gates límite que pasaron: 1866, 1876, 1901, 1917 (resumen truncado o solo afiliación; gate por el título), 1997, 2049, 2082, 2093, 2109, 2150, 2184. Gates que no pasaron y podrían pasar: 1883, 1971, 2116, 2166. Clima discutible: 1855/1896, 1939, 1947, 1951, 1958, 1974, 1983, 2101, 2115, 2144, 2173, 2175, 2205, 2211. Capítulos que comparten el resumen del libro (movilidad humana y PNA: 1948, 1957, 1969, 1972, 1973, 1988, 2001, 2007, 2008, 2018, 2033, 2035; empleo de las mujeres y transición: 2042–2076): el título decide, conviene leerlos con el texto completo. 2201 y 2203 son el mismo trabajo (artículo y tesis). Unificar cómo se codifican los deslizamientos y las lluvias intensas (hoy «otro»).

### Media prioridad

6. **Expansión multi-base** — OpenAlex (ES/PT) y SciELO ya están en la v4; Redalyc se verificó y no aporta registros nuevos (`docs/cadenas_busqueda.md` §8.4). Faltan: toolkit fetcher para PubMed, CrossRef, DOAJ + bases manuales (WoS, Latindex, Redalyc, Dialnet, CLACSO, LILACS). Script base: `Daniel_databases_project/agents/scripts/14_scopus_fetcher.py` (solo Scopus API, extender).
7. **Documentar el drift local↔repo** — decidir si fusionar `agents/scripts/` histórico al repo o archivarlo.

### Baja prioridad

8. Convertir `Daniel_databases_project/` en un clon git del repo (actualmente no lo es).
9. Automatizar la regeneración del dashboard cuando cambian los datos (hoy requiere correr `12_dashboard.py` localmente a mano).
10. El mapa incrustado en los dashboards v2, v3 y v4 deja en la consola un `deck.gl: assertion failed` al cargar (el mapa se dibuja igual; `mapa.html` por separado no lo da).

---

## 6. Cómo correr el pipeline

### Prerrequisitos

- Python 3.10+
- `pip install -r requirements.txt`
- Para re-scoring: `OPENAI_API_KEY` con acceso a la Batch API.
- Para búsquedas en Scopus API: credenciales institucionales (Elsevier API key + institutional token). Alternativa: usar la plataforma web de Scopus manualmente, como hizo Daniel.

### Regenerar el dashboard sin re-correr el LLM (rápido)

```bash
pip install -r requirements.txt
python3 pipeline/07_figuras.py
python3 pipeline/08_figuras_explicativas.py
python3 pipeline/09_insights_topicos.py
python3 pipeline/10_mapa_interactivo.py
python3 pipeline/11_validacion.py
python3 pipeline/12_dashboard.py
```

### Cadena completa (requiere bases crudas + API)

Los `.xlsx` de Scopus no se publican por términos de redistribución; están en `Daniel Data/` en el working directory local. Para reproducir desde cero:

```bash
# ingesta → scoring → topics → cruces → stats → figuras → mapa → validación → dashboard
for n in 01 02 03 04 05 06 07 08 09 10 11 12; do
  python3 pipeline/${n}_*.py
done
```

### Servir el dashboard localmente

```bash
python3 -m http.server 8001
# abrir http://localhost:8001/site/
```

---

## 7. Credenciales / secretos (NO están en el repo)

| Para qué | Variable | Fuente |
|---|---|---|
| Scoring RSI con GPT-4.1 (Batch API) | `OPENAI_API_KEY` | OpenAI dashboard |
| Scopus API (expansión opcional) | API key + inst. token | Elsevier/Scopus (institucional) |

Ninguna va al repo. Para una sesión nueva: pedirlas al usuario (Ivan Ortiz, `@iortiz1891` en GitHub) o leer de su entorno local.

---

## 8. Decisiones de diseño sedimentadas (no re-litigar sin razón)

1. **La rúbrica evalúa operacionalización, no fidelidad teórica regional.** Un paper puede ser sustantivo con vocabulario diverso (ES/EN/portugués, varias tradiciones) sin citar a Crenshaw.
2. **La selección teórica va al scoring, no al filtro de búsqueda.** Las cadenas Scopus son incluyentes por diseño; la rúbrica descarta.
3. **Idioma del proyecto:** español mexicano, tuteo. No voseo rioplatense.
4. **Dos entregables, un solo pipeline:** manuscrito Íconos (campo general) + tesis Daniel (sub-corpus ciclones × México). No bifurcar el pipeline.
5. **Scoring con LLM es provisional hasta validación humana.** La herramienta `validacion.html` existe para esto; faltan los pases.
6. **El dashboard es autocontenido en `site/`.** No depende de servicios externos (ni CDN de datos, ni backend). Todo embebido como base64 o archivos en `data/`.

---

## 9. Puntos de contacto

- **Autoría:** curaduría del corpus → Daniel · implementación técnica → Ivan Ortiz (`@iortiz1891` en GitHub).
- **Repositorio:** [iortiz1891/interseccionalidad-clima](https://github.com/iortiz1891/interseccionalidad-clima)
- **Dashboard:** https://iortiz1891.github.io/interseccionalidad-clima/
- **Documento canónico de la rúbrica:** [`docs/rubrica_RSI_fundamentacion.md`](docs/rubrica_RSI_fundamentacion.md)
- **Documento canónico de cadenas de búsqueda:** [`docs/cadenas_busqueda.md`](docs/cadenas_busqueda.md)

---

## 10. Para una sesión Claude nueva (misma usuario)

Las memorias persistentes están en:
`~/.claude/projects/<carpeta del proyecto en Google Drive>/memory/`

Archivos clave: `MEMORY.md` (índice), `project_revisa_rama_daniel.md`, `project_revisa_methodology.md`, `project_revisa_pending.md`, `feedback_espanol_mexicano.md`, `feedback_no_direccional.md`.

El working directory local está en Google Drive (sincronizado) — una sesión nueva en otra máquina necesita que Google Drive esté montado y sincronizado.
