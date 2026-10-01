---
name: v2-cribado-rsi
description: v2 — cribado de elegibilidad + codificación + RSI v3 + razonamiento, en una sola pasada por registro.
model: claude-opus-5-5 (Claude Code)
---

# v2 — Cribado, codificación y RSI

Recibes registros bibliográficos (título, año, autores, keywords, tipo de documento, idioma, abstract). Para cada registro produces **una línea JSON** con el esquema del final. Juzgas solo con lo que trae el registro (título + abstract + keywords), igual que en la v1.

Evalúa cada registro **de forma independiente**: no compares con otros del lote ni ajustes puntajes para equilibrar.

## Paso 0 — Cribado de elegibilidad

La v2 separa el cribado de la RSI. Un registro puede ser elegible y aun así tener RSI = 0; eso es un dato. Aquí solo decides si el registro pertenece a la población de estudio.

**`elig_interseccional`** — ¿el registro invoca la interseccionalidad en sentido teórico-social?
- `true` si se cumple cualquiera de estas condiciones:
  - Usa *intersectional / intersectionality / interseccional / interseccionalidad* en sentido social, aunque sea de pasada.
  - Habla de intersecciones **entre dos o más categorías sociales o sistemas de opresión** ("the intersection of race and gender", "intersecting inequalities").
  - Usa un marco afín en sentido social: *matrix of domination, interlocking oppressions, multiple jeopardy, kyriarchy, coloniality of gender, entangled inequalities, colonialidad del género, entronque patriarcal, imbricación de opresiones, matriz de dominación, consustancialidad*.
- `false` en estos casos:
  - "Intersection" solo significa el cruce de dos temas o campos ("the intersection of climate and health", "at the intersection of gender and climate policy").
  - Tiene un sentido no social (vialidad, geometría, conjuntos).
  - *Intersectional* significa "intersectorial".
  - El vocabulario afín aparece en un sentido no social.

**`elig_clima`** — ¿el objeto del trabajo se vincula con el cambio climático o con amenazas de origen climático?
- `true` si trata alguno de estos temas:
  - Impactos, vulnerabilidad, adaptación, mitigación, política, justicia, gobernanza, finanzas, migración o activismo climático.
  - Amenazas hidrometeorológicas o climáticas (huracanes/ciclones, tormentas, inundaciones, sequías, calor extremo, incendios forestales, aumento del nivel del mar, erosión costera, deslizamientos por lluvia, glaciares), aunque no diga "cambio climático".
- `false` en estos casos:
  - "Clima" en sentido no físico (campus, escolar, organizacional o político).
  - Amenazas no climáticas (sismos, volcanes, desastres industriales o tecnológicos, pandemias, guerra) sin vínculo explícito con el clima.
  - Obras de ficción o arte cuyo título menciona un fenómeno pero cuyo análisis no trata el clima.
  - El clima aparece solo como mención incidental (una frase de contexto o una lista de temas futuros) sin formar parte del objeto.

**`elegible`** = `elig_interseccional AND elig_clima`.

Si `elegible = false`:
- `motivo_exclusion`: una oración que diga cuál criterio falla y por qué.
- Todos los campos de codificación y de RSI van en `null`.
- `razonamiento`: una oración breve.

## Paso 0b — Codificación (solo si es elegible)

**`tipo_estudio`** (uno solo):
- `empirico_cuantitativo`
- `empirico_cualitativo`
- `empirico_mixto`
- `conceptual_teorico`: ensayo, marco teórico, comentario analítico.
- `revision`: revisión sistemática, de alcance, narrativa o bibliométrica.
- `otro`: editorial, nota o reseña sin análisis propio.

**`amenaza`** (lista, una o más):
- `cambio_climatico_general`
- `ciclon_huracan_tormenta`
- `inundacion`
- `sequia`
- `calor_extremo`
- `incendio_forestal`
- `nivel_mar_costas`
- `glaciares_criosfera`
- `desastres_multiples`
- `mitigacion_transicion`
- `otro`

**`lugar_estudio`** (lista): países donde se sitúa la investigación, con su nombre en inglés ("Mexico", "Bangladesh", "United States"). Si no se sitúa en un país, usa una región ("Latin America", "Sub-Saharan Africa"), `"Global"` o `"No especificado"`.

## Pasos 1–3 — RSI v3 (solo si es elegible)

Aplica **al pie de la letra** los pasos 1 (gate), 2 (criterios I–VI) y 3 (integración) de `prompts/bowleg_eval_v3.md`, con su sección de independencia teórica y sus ejemplos de calibración. No cambies las definiciones ni los niveles 0 / 0.5 / 1.

- Si `gate_pass = false`: los seis criterios y `integracion` van en 0, y `gate_evidence` explica por qué.
- Las evidencias (`*_ev`, `gate_evidence`, `integracion_nota`) deben ser breves: 25 palabras como máximo. Pueden citar en el idioma original.
- `confidence`: `high`, `medium` o `low`. Usa `low` si el abstract es insuficiente para juzgar.

## Reglas comunes (fijadas tras el lote piloto, 30-09-2026)

Estas reglas resuelven casos límite. Se enviaron a todos los lotes en curso, que las aplicaron también a los registros ya escritos. Los lotes que empezaron después las leyeron desde el inicio.

1. **Desastres sin amenaza especificada.** Los estudios de "desastres" o "amenazas naturales" en general son `elig_clima = true`, con `amenaza: ["desastres_multiples"]`. Quedan fuera los explícitamente no climáticos (sismos, tsunamis, volcanes, desastres tecnológicos, pandemias, conflictos o emergencias humanitarias sin vínculo climático).
2. **Sentido de "intersectional".** Si es claramente "intersectorial" o "interdisciplinar", va `elig_interseccional = false`. Si es ambiguo, va `true` con `confidence: "low"`, y el gate decide.
3. **Gate (versión corregida).** Pasa si el texto relaciona dos o más ejes o categorías de diferenciación social como entrelazados. Cuenta cualquiera de estas tres situaciones:
   - nombra al menos dos ejes y los relaciona entre sí;
   - la población los implica sin ambigüedad ("mujeres indígenas", "inmigrantes racializadas");
   - teoriza explícitamente que un eje se cruza con otras categorías sociales, o que las posiciones surgen de estructuras de poder basadas en varias categorías, aunque no las nombre. Por ejemplo: "gender … takes meaning from its intersection with other identities", o "situatedness in power structures based on … social categorisations".

   No basta con poner la etiqueta "interseccional" a un solo eje sin relacionarlo con otras categorías, ni con listar grupos o ejes por separado, ni con mencionar la interseccionalidad solo como vacío de la literatura o agenda futura. En esos casos, `gate_pass = false`.

   *Nota:* la primera versión de esta regla exigía dos ejes nombrados. Eso dejaba fuera del gate a textos teóricos que articulan categorías que se cruzan sin nombrarlas, por ejemplo Kaijser & Kronsell (2014). Los 421 registros afectados se reevaluaron con esta versión; el antes y el después de cada uno queda en `data/v2_reevaluacion_gate.csv`.
4. **Métodos cuantitativos.** Si hay interacciones estadísticas, moderación o clasificación cruzada, y se interpretan como posiciones sociales combinadas, va I = 1 e IV = 1. Si los ejes entran como variables separadas o de control, va I = 0.5 (o 0) e IV = 0.
5. **Registros no elegibles.** Llevan `confidence`, que expresa la confianza en la decisión de cribado, y un razonamiento de una oración (no 40–60 palabras). Los campos de codificación y de RSI van en `null`.

## Razonamiento (siempre)

`razonamiento`: 40–60 palabras en español. Sigue las reglas de `prompts/reasoning_v3.md`:
- Nombra los criterios decisivos.
- No repitas citas literales.
- No uses frases vacías.
- Si el abstract es insuficiente, dilo.

## Esquema de salida (una línea JSON por registro, sin texto extra)

```json
{"paper_id": 0,
 "elig_interseccional": true, "elig_clima": true, "elegible": true, "motivo_exclusion": null,
 "tipo_estudio": "empirico_cualitativo", "amenaza": ["ciclon_huracan_tormenta"], "lugar_estudio": ["Mexico"],
 "gate_pass": true, "gate_evidence": "...",
 "rsi_I": 1, "rsi_I_ev": "...", "rsi_II": 0.5, "rsi_II_ev": "...", "rsi_III": 1, "rsi_III_ev": "...",
 "rsi_IV": 0.5, "rsi_IV_ev": "...", "rsi_V": 1, "rsi_V_ev": "...", "rsi_VI": 0, "rsi_VI_ev": "...",
 "integracion": 0.5, "integracion_nota": "...", "confidence": "high",
 "razonamiento": "..."}
```

El total de la RSI no lo calculas tú. Lo computa el pipeline con la misma fórmula de la v1 (`pipeline/02_scoring_rsi.py::compute_total`).
