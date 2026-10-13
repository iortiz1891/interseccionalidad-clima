# HANDOFF — Interseccionalidad y Cambio Climático

**Última actualización:** 2026-10-13
**Repo:** https://github.com/iortiz1891/interseccionalidad-clima
**Dashboard en vivo:** https://iortiz1891.github.io/interseccionalidad-clima/

---

## 1. Lo esencial en 30 segundos

- **Qué es:** revisión sistemática que mide, con una rúbrica (RSI) aplicada por LLM, en qué medida la investigación sobre cambio climático **aplica** interseccionalidad vs. solo la **menciona**.
- **Corpus:** 971 papers Scopus (752 EN + 219 ES, mayo 2026) consolidados por Daniel.
- **Instrumento:** Rúbrica de Sustantividad Interseccional (RSI) — gate + 6 criterios graduados + factor de integración. Fundamentada en Crenshaw, Collins, Hancock, McCall, Bowleg.
- **Scoring vigente:** `gpt-4.1` vía Batch API de OpenAI, prompts en `prompts/bowleg_eval_v3.md` + `reasoning_v3.md`. **Provisional** — pendiente validación humana con κ de Cohen.
- **Resultado principal:** 57.5% invoca el marco sin articularlo (RSI=0); 19% sustantiva fuerte. El eslabón débil es el criterio IV (método no aditivo).

**Dos entregables esperados:**
1. **Manuscrito Íconos (FLACSO Ecuador)** — sobre el campo general.
2. **Tesis de Daniel** — ciclones × CC × interseccionalidad × México costero (sub-corpus de 97 papers; se dispersa en 25 tópicos, no forma cluster propio).

---

## 2. Arquitectura: repo publicado vs. working directory local

### 2.1 Repo publicado (fuente de verdad, limpio)

```
iortiz1891/interseccionalidad-clima
├── site/                    ← dashboard autocontenido (publicado por GitHub Pages)
│   ├── index.html           ·  dashboard principal (~3 MB)
│   ├── mapa.html            ·  mapa temático interactivo
│   └── validacion.html      ·  herramienta de validación humana (κ de Cohen)
├── data/                    ← 21 CSV/JSON con prefijo v1_* + daniel_prisma_meta.json
├── pipeline/                ← 12 scripts numerados 01→12 (orden lógico)
├── prompts/                 ← bowleg_eval_v3.md, reasoning_v3.md
├── docs/                    ← rubrica_RSI_fundamentacion.md, cadenas_busqueda.md
└── assets/                  ← 16 figuras v6_*
```

### 2.2 Working directory local (historia completa, no publicado)

```
~/Library/CloudStorage/GoogleDrive-iortiz1891@gmail.com/My Drive/Daniel_LiteratureReview_May2026/
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

## 3. Lo que se hizo en esta sesión (2026-09-28)

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

### Distribución RSI (gpt-4.1, provisional)

| Categoría | % | n |
|---|---:|---:|
| Mención sin aplicación (0) | 57.5% | 558 |
| Nominal/débil (0.5–1.0) | 6.6% | 64 |
| Parcial (1.5–2.0) | 12.4% | 120 |
| Sustantiva (2.5–3.0) | 4.5% | 44 |
| Sustantiva fuerte (3.5–4.0) | 19.1% | 185 |

### Hallazgos actuales

1. **Adopción ≠ aplicación.** Mayoría nominal.
2. **Eslabón débil = método (IV).** Entre papers que pasan el gate, solo 34% operacionaliza. 70%+ cumplen poder estructural (II) y praxis (V).
3. **La sustantividad es de nicho.** Se concentra en desastres situados, conocimientos indígenas, género × agricultura. BERTopic con 33 tópicos.

---

## 5. Pendientes priorizados

### Alta prioridad

1. **Ejecutar v2a Scopus y comparar hits vs v1** — ver `docs/cadenas_busqueda.md` §2.2. Esperado: amplía peligros climáticos (inundación, sequía, ola de calor) y ejes (discapacidad, LGBT, edad, casta, indigeneidad). Registrar en `data/search_log.csv`.
2. **Validación humana** — codificar submuestra con la herramienta `site/validacion.html` y calcular κ de Cohen vs scoring del LLM. La submuestra ya está en `data/v1_validation_sample.json`.
3. **Refinamiento con Sonnet antes de Íconos** — ver [`project_revisa_v1_scoring.md`](memory). Decisión de 2026-05-15 fue usar GPT-4o-mini pese a κ=0.038 vs Sonnet; antes del manuscrito definitivo re-correr con Sonnet o modelo equivalente.

### Media prioridad

4. **Expansión multi-base** — toolkit fetcher para OpenAlex, SciELO, PubMed, CrossRef, DOAJ + bases manuales (WoS, Latindex, Redalyc, Dialnet, CLACSO, LILACS). Script base: `Daniel_databases_project/agents/scripts/14_scopus_fetcher.py` (solo Scopus API, extender).
5. **Documentar el drift local↔repo** — decidir si fusionar `agents/scripts/` histórico al repo o archivarlo.

### Baja prioridad

6. Convertir `Daniel_databases_project/` en un clon git del repo (actualmente no lo es).
7. Automatizar la regeneración del dashboard cuando cambian los datos (hoy requiere correr `12_dashboard.py` localmente a mano).

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

Ninguna va al repo. Para una sesión nueva: pedirlas al usuario (Ivan, `iortiz1891@gmail.com`) o leer de su entorno local.

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

- **Autoría:** curaduría del corpus → Daniel · implementación técnica → Ivan Ortiz (`iortiz1891@gmail.com`).
- **Repositorio:** [iortiz1891/interseccionalidad-clima](https://github.com/iortiz1891/interseccionalidad-clima)
- **Dashboard:** https://iortiz1891.github.io/interseccionalidad-clima/
- **Documento canónico de la rúbrica:** [`docs/rubrica_RSI_fundamentacion.md`](docs/rubrica_RSI_fundamentacion.md)
- **Documento canónico de cadenas de búsqueda:** [`docs/cadenas_busqueda.md`](docs/cadenas_busqueda.md)

---

## 10. Para una sesión Claude nueva (misma usuario)

Las memorias persistentes están en:
`~/.claude/projects/-Users-ivanmini-Library-CloudStorage-GoogleDrive-iortiz1891-gmail-com-My-Drive-Daniel-LiteratureReview-May2026/memory/`

Archivos clave: `MEMORY.md` (índice), `project_revisa_rama_daniel.md`, `project_revisa_methodology.md`, `project_revisa_pending.md`, `feedback_espanol_mexicano.md`, `feedback_no_direccional.md`.

El working directory local está en Google Drive (sincronizado) — una sesión nueva en otra máquina necesita que Google Drive esté montado y sincronizado.
