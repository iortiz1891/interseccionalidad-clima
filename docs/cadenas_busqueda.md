# Cadenas de búsqueda

**Objetivo:** documentar de forma auditable qué se buscó, dónde y con qué límites, y proponer una versión potenciada que amplíe la cobertura sin diluir el objeto de estudio.

**Alcance del proyecto:** el corpus debe recuperar la literatura que **invoca la interseccionalidad** en relación con el **cambio climático o eventos climáticos extremos**, en un espacio amplio de **ejes de diferenciación social y vulnerabilidad**. Sobre ese corpus se aplica después la Rúbrica de Sustantividad Interseccional (RSI), que distingue aplicación sustantiva de invocación nominal.

**Estrategia:** dejar la selección teórica al scoring RSI (no al filtro de búsqueda). La búsqueda debe ser **incluyente**: mejor recuperar de más y descartar con la rúbrica que descartar en la query.

---

## 1. Versión ejecutada (v1 — mayo 2026)

**Fuente:** Scopus, plataforma web (exportado como `.xlsx`).
**Filtros comunes:** solo `LIMIT-TO(LANGUAGE, …)`. Sin filtro de años ni de tipo de documento.

### 1.1 Cadena EN — `scopus_en` → **752 registros**

```
( TITLE-ABS-KEY ( "intersection*" )
  AND TITLE-ABS-KEY ( "climate change*" OR "hurricane*" OR "storm"
                      OR "extreme weather events" OR "cyclone" )
  AND TITLE-ABS-KEY ( "justice" OR "gender" OR "race" OR "ethnicity"
                      OR "socioeconomic status" OR "health disparities"
                      OR "governance" OR "power" OR "agency"
                      OR "identity" OR "institution" OR "vulnerab*"
                      OR "adapt*" ) )
AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

### 1.2 Cadena ES — `scopus_es` → **219 registros**

```
( ALL ( "interseccio*" )
  AND ALL ( "cambio clim*" OR "hurac*" OR "torment*" OR "evento clim*"
            OR "ciclo*" )
  AND ALL ( "vulnerab*" OR "adapta*" OR "resilien*" OR "justicia"
            OR "poder" OR "instituci*" OR "gobernanza" OR "agenci*"
            OR "identida*" OR "genero" OR "raza" OR "racia*" OR "etnic*"
            OR "nivel soci*" OR "disparidad*" ) )
AND ( LIMIT-TO ( LANGUAGE , "Spanish" ) )
```

**Total consolidado tras filtro `abstract ≥ 100 caracteres` y dedup por DOI/título:** 971 papers (`daniel_prisma_meta.json`).

### 1.3 Diagnóstico de v1

| # | Problema | Efecto |
|---|---|---|
| a | EN usa `TITLE-ABS-KEY` (título + abstract + keywords), ES usa `ALL` (además: afiliaciones, referencias, texto indexado) | Precisión/cobertura **asimétrica** entre idiomas |
| b | `ciclo*` en ES captura *ciclón* pero también *ciclo hidrológico*, *ciclo económico*, *ciclo del carbono* | Falsos positivos en ES |
| c | Peligros climáticos limitados a huracán/tormenta/ciclón + "extreme weather events" | Deja fuera **inundación**, **sequía**, **ola de calor**, **incendio forestal**, **aumento del nivel del mar**, **desplazamiento climático** |
| d | Ejes de diferenciación incompletos: sin **discapacidad**, **sexualidad**, **edad/generación**, **casta**, **indigeneidad**, **colonialidad**, **clase** explícita | Sub-recupera literatura sobre grupos históricamente sub-representados |
| e | Ancla teórica solo por raíz `intersection*` / `interseccio*` | Deja fuera papers que operan con **sistemas entrelazados**, **matriz de dominación**, **múltiples marginalidades**, **colonialidad de género** sin nombrar interseccionalidad |
| f | Sin filtro temporal ni recorte por tipo de documento | Aceptable, pero conviene registrarlo explícitamente |

---

## 2. Propuesta potenciada (v2)

Se ofrecen **tres variantes** con propósitos distintos. La v2a es la recomendada como sucesora comparable de la v1; la v2b es exploratoria; la v2c está afinada al sub-corpus de la tesis de Daniel.

### 2.1 Principios de diseño

1. **Simetría entre idiomas.** Ambas cadenas usan `TITLE-ABS-KEY`. Para español se acepta que Scopus indexa menos abstracts en ese idioma; a cambio, se compensa con vocabulario más amplio.
2. **Ancla interseccional preservada.** Un paper entra si **invoca** interseccionalidad o un sinónimo teórico documentado en la literatura crítica (Bowleg, Collins, Hancock, McCall, Lugones). Se evita ensanchar hacia todo el campo de "género + clima" o "justicia ambiental" sin marco.
3. **Peligros climáticos completos.** Se cubren los eventos que la literatura sobre desastres y clima reconoce: huracanes/ciclones/tifones, tormentas, inundaciones, sequías, olas de calor, incendios forestales, aumento del nivel del mar, erosión costera y desplazamiento climático.
4. **Ejes de diferenciación ampliados.** Se añaden discapacidad, sexualidad/orientación sexual, edad/generación, casta, indigeneidad, colonialidad, migración y clase.
5. **`ciclo*` fijado a `ciclón*` / `cyclone*`** para eliminar falsos positivos.
6. **Documentabilidad.** Cada ejecución registra fecha, base, plataforma, límites y n de hits.

### 2.2 v2a — Cadena EN potenciada (recomendada)

```
( TITLE-ABS-KEY ( "intersection*"
                   OR "interlocking oppression*" OR "interlocking system*"
                   OR "matrix of domination" OR "multiple marginalization*"
                   OR "co-constitutive" OR "coloniality of gender" )
  AND TITLE-ABS-KEY ( "climate change" OR "climate crisis" OR "climate variability"
                       OR "climate justice" OR "climate adapt*" OR "climate vulnerab*"
                       OR "climate displac*" OR "climate migrat*"
                       OR "hurricane*" OR "cyclone*" OR "typhoon*"
                       OR "storm surge" OR "extreme weather" OR "extreme heat"
                       OR "heat wave" OR "heatwave"
                       OR "flood*" OR "drought*" OR "wildfire*" OR "bushfire*"
                       OR "sea level rise" OR "sea-level rise" OR "coastal erosion" )
  AND TITLE-ABS-KEY ( "gender" OR "wom*n" OR "feminis*"
                       OR "race" OR "racial" OR "ethnic*" OR "indigen*"
                       OR "class" OR "caste" OR "socioeconomic*"
                       OR "sexuality" OR "sexual orientation" OR "LGBT*" OR "queer"
                       OR "disabilit*" OR "age" OR "generation*" OR "elder*" OR "youth"
                       OR "migrant*" OR "refugee*" OR "displaced"
                       OR "colonial*" OR "postcolonial" OR "decolon*"
                       OR "power" OR "inequality" OR "inequalit*" OR "justice"
                       OR "vulnerab*" OR "marginali*" OR "identit*" OR "agency" ) )
AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

### 2.3 v2a — Cadena ES potenciada (recomendada)

```
( TITLE-ABS-KEY ( "interseccio*"
                   OR "sistemas entrelazados" OR "opresiones entrelazadas"
                   OR "matriz de dominación" OR "múltiples marginalidades"
                   OR "colonialidad de género" OR "colonialidad del género" )
  AND TITLE-ABS-KEY ( "cambio climático" OR "crisis climática" OR "variabilidad climática"
                       OR "justicia climática" OR "adaptación climática"
                       OR "vulnerabilidad climática" OR "desplazamiento climático"
                       OR "migración climática"
                       OR "huracán*" OR "huracanes" OR "ciclón*" OR "tifón*"
                       OR "marejada" OR "evento* climático* extremo*"
                       OR "ola de calor" OR "olas de calor"
                       OR "inundación*" OR "inundaciones"
                       OR "sequía*" OR "incendio* forestal*"
                       OR "aumento del nivel del mar" OR "erosión costera" )
  AND TITLE-ABS-KEY ( "género" OR "mujer*" OR "feminis*"
                       OR "raza" OR "racial*" OR "etnic*" OR "indígena*"
                       OR "clase" OR "casta" OR "socioeconómic*"
                       OR "sexualidad" OR "orientación sexual" OR "LGBT*" OR "cuir"
                       OR "discapacidad*" OR "edad" OR "generacion*" OR "juventud*"
                       OR "adultos mayores" OR "personas mayores"
                       OR "migrante*" OR "refugiad*" OR "desplazad*"
                       OR "colonial*" OR "poscolonial" OR "decolonial*" OR "descolonial*"
                       OR "poder" OR "desigualdad*" OR "justicia"
                       OR "vulnerab*" OR "marginali*" OR "identidad*" OR "agencia" ) )
AND ( LIMIT-TO ( LANGUAGE , "Spanish" ) )
```

**Cambios respecto a v1:**
- ES pasa de `ALL` a `TITLE-ABS-KEY` → simetría con EN.
- `ciclo*` → `ciclón*` (elimina falsos positivos).
- Se añaden peligros faltantes: inundación, sequía, ola de calor, incendio forestal, aumento del nivel del mar, marejada, erosión costera, desplazamiento/migración climática.
- Se añaden ejes: discapacidad, sexualidad/orientación sexual/LGBT/cuir, edad/generación, casta, indigeneidad, colonialidad, migración/desplazamiento.
- Se añaden sinónimos teóricos al ancla interseccional.

### 2.4 v2b — Cadena exploratoria (sin ancla léxica de interseccionalidad)

Uso: **auditar** qué queda fuera de v2a. Recupera literatura que opera con marcos afines (multi-axis, compounded vulnerability, entrelazamiento) sin nombrar interseccionalidad. Requiere post-filtro con la rúbrica.

**No se pega aquí completa** para evitar que se use por defecto. Se genera reemplazando el primer bloque de v2a por:

```
TITLE-ABS-KEY ( "compounded vulnerab*" OR "multiple vulnerab*"
                 OR "intersecting inequalit*" OR "co-produced inequalit*"
                 OR "structural inequalit*" AND "gender" AND "race" )
```

y añadiendo un post-filtro que exija **≥ 2 ejes distintos** en título/abstract.

### 2.5 v2c — Sub-corpus tesis Daniel (ciclones × costera × LatAm)

**Uso:** aislar el sub-corpus temático de la tesis. Se aplica como sub-consulta *dentro* del corpus v2a (no como reemplazo).

```
AND TITLE-ABS-KEY ( "cyclone*" OR "hurricane*" OR "typhoon*"
                     OR "storm surge" OR "coastal flood*"
                     OR "coastal erosion" OR "sea level rise"
                     OR "ciclón*" OR "huracán*" OR "marejada"
                     OR "costa*" OR "coast*" OR "costero*" OR "coastal" )
AND TITLE-ABS-KEY ( "Mexico" OR "México" OR "Latin America" OR "América Latina"
                     OR "Caribbean" OR "Caribe" OR "Mesoamerica" OR "Mesoamérica"
                     OR "Gulf of Mexico" OR "Golfo de México"
                     OR "Yucatán" OR "Yucatan" OR "Veracruz" OR "Guerrero"
                     OR "Quintana Roo" OR "Tabasco" OR "Oaxaca" OR "Chiapas" )
```

---

## 3. v2 ejecutada (30 de septiembre de 2026) — cadena bilingüe

Sustituye a las propuestas v2a/v2b/v2c de la sección 2. Resuelve dos problemas que esas propuestas no resolvían:

- **La raíz `intersection*` atrapa la palabra común**: cruces viales o frases como "at the intersection of climate and health". La v2 exige *intersectional* / *interseccional*, o bien "intersection" a ≤ 4 palabras de un eje social (`W/4`).
- **Los trabajos en español casi siempre tienen el abstract solo en inglés.** Por eso una cadena con términos solo en español, limitada a `TITLE-ABS-KEY`, dependería del título. La v2 usa una única cadena con términos en inglés y en español.

Decisiones de diseño:

- **Sin bloque de ejes sociales.** Con el ancla estricta, ese bloque solo excluiría los trabajos que invocan el marco sin nombrar ejes, que son justo los usos nominales que se quieren medir.
- **Bloque climático amplio.** Incluye desastres, mitigación enmarcada en clima, calor, glaciares, etc. Lo que no es climático se descarta en el cribado, con motivo.
- **Límites:** desde 1989 (Crenshaw), inglés y español, todos los tipos de documento.

### 3.1 Scopus (ejecutada)

```
TITLE-ABS-KEY (
  "intersectional*" OR "interseccional*"
  OR "intersecting inequalit*" OR "intersecting identit*" OR "intersecting oppression*"
  OR ( intersection* W/4 ( gender OR race OR racial OR racism OR sex OR sexism
       OR sexuality OR class OR ethnic* OR identit* OR oppression* OR disabilit*
       OR indigen* OR caste ) )
  OR ( intersecci* W/4 ( género OR genero OR raza OR racismo OR sexo OR sexualidad*
       OR clase OR étnic* OR etnic* OR identidad* OR opresi* OR discapacidad*
       OR indígena* OR indigena* ) )
  OR "matrix of domination" OR "multiple jeopardy" OR kyriarch*
  OR "coloniality of gender" OR "simultaneity of oppression*"
  OR "entangled inequalit*" OR "multiple marginali*"
  OR ( interlocking W/3 ( oppression* OR inequalit* OR domination ) )
  OR "matriz de dominación" OR "matriz de opresión"
  OR "colonialidad del género" OR "colonialidad de género"
  OR "entronque patriarcal" OR consustancialidad OR "desigualdades entrelazadas"
  OR ( imbricaci* W/3 ( opresi* OR dominaci* OR género OR raza OR clase ) )
  OR ( entrelazad* W/3 ( opresi* OR dominaci* ) )
)
AND TITLE-ABS-KEY (
  "climate change*" OR "changing climate*" OR "global warming"
  OR "global environmental change" OR "climate crisis" OR "climate emergenc*"
  OR "climate variab*" OR "climate justice" OR "climate adapt*"
  OR "climate vulnerab*" OR "climate risk*" OR "climate resilien*"
  OR "climate polic*" OR "climate action" OR "climate governance"
  OR "climate mitigation" OR "climate finance" OR "climate migra*"
  OR "climate mobilit*" OR "climate displace*" OR "climate impact*"
  OR "climate hazard*" OR "climate extreme*" OR "climate shock*"
  OR "climate-induced" OR "climate-related" OR "climate security"
  OR "climate politic*" OR "climate activis*" OR "climate anxiety"
  OR "extreme weather" OR "extreme event*" OR "extreme heat" OR "heat stress"
  OR heatwave* OR "heat wave*" OR "heat-related" OR "urban heat"
  OR hurricane* OR cyclone* OR typhoon* OR storm* OR flood* OR drought*
  OR wildfire* OR bushfire* OR "forest fire*" OR "sea level*" OR "sea-level*"
  OR "coastal erosion" OR monsoon* OR "el niño" OR "el nino" OR desertification
  OR glacier* OR permafrost OR landslide* OR "cold wave*" OR hydrometeorolog*
  OR disaster* OR "natural hazard*"
  OR "cambio* clim*" OR "crisis clim*" OR "emergencia clim*"
  OR "variabilidad clim*" OR "calentamiento global" OR "justicia clim*"
  OR "adaptación clim*" OR "vulnerabilidad clim*" OR "riesgo* clim*"
  OR "política* clim*" OR "acción clim*" OR "gobernanza clim*"
  OR "migraci* clim*" OR "desplaza* clim*" OR "movilidad clim*"
  OR "evento* clim*" OR "evento* extremo*" OR "fenómeno* extremo*"
  OR hidrometeorol* OR hurac* OR ciclón* OR ciclon* OR tifón* OR tifon*
  OR tormenta* OR marejada* OR inundaci* OR sequía* OR sequia*
  OR "ola* de calor" OR "estrés térmico" OR "incendio* forestal*"
  OR "nivel del mar" OR "erosión costera" OR desertificaci* OR glaciar*
  OR "deslizamiento* de tierra*" OR desastre* OR "amenaza* natural*"
)
AND PUBYEAR > 1988
AND ( LIMIT-TO ( LANGUAGE , "English" ) OR LIMIT-TO ( LANGUAGE , "Spanish" ) )
```

### 3.2 Web of Science Core Collection / SciELO Citation Index (pendiente de ejecutar)

Misma lógica con la sintaxis de WoS. Al marcar el nivel del ancla, los registros que solo coinciden por KeyWords Plus se tratan como invocación por cita: KeyWords Plus se genera de los títulos de las referencias.

```
TS=(
  "intersectional*" OR "interseccional*"
  OR "intersecting inequalit*" OR "intersecting identit*" OR "intersecting oppression*"
  OR (intersection* NEAR/4 (gender OR race OR racial OR racism OR sex OR sexism
      OR sexuality OR class OR ethnic* OR identit* OR oppression* OR disabilit*
      OR indigen* OR caste))
  OR (intersecci* NEAR/4 (género OR genero OR raza OR racismo OR sexo OR sexualidad*
      OR clase OR étnic* OR etnic* OR identidad* OR opresi* OR discapacidad*
      OR indígena* OR indigena*))
  OR "matrix of domination" OR "multiple jeopardy" OR kyriarch*
  OR "coloniality of gender" OR "simultaneity of oppression*"
  OR "entangled inequalit*" OR "multiple marginali*"
  OR (interlocking NEAR/3 (oppression* OR inequalit* OR domination))
  OR "matriz de dominación" OR "matriz de opresión"
  OR "colonialidad del género" OR "colonialidad de género"
  OR "entronque patriarcal" OR consustancialidad OR "desigualdades entrelazadas"
  OR (imbricaci* NEAR/3 (opresi* OR dominaci* OR género OR raza OR clase))
  OR (entrelazad* NEAR/3 (opresi* OR dominaci*))
)
AND TS=(
  "climate change*" OR "changing climate*" OR "global warming"
  OR "global environmental change" OR "climate crisis" OR "climate emergenc*"
  OR "climate variab*" OR "climate justice" OR "climate adapt*"
  OR "climate vulnerab*" OR "climate risk*" OR "climate resilien*"
  OR "climate polic*" OR "climate action" OR "climate governance"
  OR "climate mitigation" OR "climate finance" OR "climate migra*"
  OR "climate mobilit*" OR "climate displace*" OR "climate impact*"
  OR "climate hazard*" OR "climate extreme*" OR "climate shock*"
  OR "climate-induced" OR "climate-related" OR "climate security"
  OR "climate politic*" OR "climate activis*" OR "climate anxiety"
  OR "extreme weather" OR "extreme event*" OR "extreme heat" OR "heat stress"
  OR heatwave* OR "heat wave*" OR "heat-related" OR "urban heat"
  OR hurricane* OR cyclone* OR typhoon* OR storm* OR flood* OR drought*
  OR wildfire* OR bushfire* OR "forest fire*" OR "sea level*" OR "sea-level*"
  OR "coastal erosion" OR monsoon* OR "el niño" OR "el nino" OR desertification
  OR glacier* OR permafrost OR landslide* OR "cold wave*" OR hydrometeorolog*
  OR disaster* OR "natural hazard*"
  OR "cambio* clim*" OR "crisis clim*" OR "emergencia clim*"
  OR "variabilidad clim*" OR "calentamiento global" OR "justicia clim*"
  OR "adaptación clim*" OR "vulnerabilidad clim*" OR "riesgo* clim*"
  OR "política* clim*" OR "acción clim*" OR "gobernanza clim*"
  OR "migraci* clim*" OR "desplaza* clim*" OR "movilidad clim*"
  OR "evento* clim*" OR "evento* extremo*" OR "fenómeno* extremo*"
  OR hidrometeorol* OR hurac* OR ciclón* OR ciclon* OR tifón* OR tifon*
  OR tormenta* OR marejada* OR inundaci* OR sequía* OR sequia*
  OR "ola* de calor" OR "estrés térmico" OR "incendio* forestal*"
  OR "nivel del mar" OR "erosión costera" OR desertificaci* OR glaciar*
  OR "deslizamiento* de tierra*" OR desastre* OR "amenaza* natural*"
)
AND PY=(1989-2026)
AND LA=(English OR Spanish)
```

### 3.3 Opcional: invocación solo por cita (Scopus)

Trabajos climáticos que citan literatura interseccional sin nombrarla en título, abstract ni keywords. Su RSI requiere texto completo.

```
REFTITLE ( "intersectional*" OR "interseccional*"
           OR "demarginalizing the intersection" OR "black feminist thought" )
AND TITLE-ABS-KEY (
  "climate change*" OR "changing climate*" OR "global warming"
  OR "global environmental change" OR "climate crisis" OR "climate emergenc*"
  OR "climate variab*" OR "climate justice" OR "climate adapt*"
  OR "climate vulnerab*" OR "climate risk*" OR "climate resilien*"
  OR "climate polic*" OR "climate action" OR "climate governance"
  OR "climate mitigation" OR "climate finance" OR "climate migra*"
  OR "climate mobilit*" OR "climate displace*" OR "climate impact*"
  OR "climate hazard*" OR "climate extreme*" OR "climate shock*"
  OR "climate-induced" OR "climate-related" OR "climate security"
  OR "climate politic*" OR "climate activis*" OR "climate anxiety"
  OR "extreme weather" OR "extreme event*" OR "extreme heat" OR "heat stress"
  OR heatwave* OR "heat wave*" OR "heat-related" OR "urban heat"
  OR hurricane* OR cyclone* OR typhoon* OR storm* OR flood* OR drought*
  OR wildfire* OR bushfire* OR "forest fire*" OR "sea level*" OR "sea-level*"
  OR "coastal erosion" OR monsoon* OR "el niño" OR "el nino" OR desertification
  OR glacier* OR permafrost OR landslide* OR "cold wave*" OR hydrometeorolog*
  OR disaster* OR "natural hazard*"
  OR "cambio* clim*" OR "crisis clim*" OR "emergencia clim*"
  OR "variabilidad clim*" OR "calentamiento global" OR "justicia clim*"
  OR "adaptación clim*" OR "vulnerabilidad clim*" OR "riesgo* clim*"
  OR "política* clim*" OR "acción clim*" OR "gobernanza clim*"
  OR "migraci* clim*" OR "desplaza* clim*" OR "movilidad clim*"
  OR "evento* clim*" OR "evento* extremo*" OR "fenómeno* extremo*"
  OR hidrometeorol* OR hurac* OR ciclón* OR ciclon* OR tifón* OR tifon*
  OR tormenta* OR marejada* OR inundaci* OR sequía* OR sequia*
  OR "ola* de calor" OR "estrés térmico" OR "incendio* forestal*"
  OR "nivel del mar" OR "erosión costera" OR desertificaci* OR glaciar*
  OR "deslizamiento* de tierra*" OR desastre* OR "amenaza* natural*"
)
AND PUBYEAR > 1988
AND ( LIMIT-TO ( LANGUAGE , "English" ) OR LIMIT-TO ( LANGUAGE , "Spanish" ) )
```

### 3.4 Resultados de la ejecución en Scopus

| | Registros |
|---|---|
| Total (30-09-2026) | **1,751** |
| Solo `intersectional*` / `interseccional*` | 1,449 |
| + frases con `W/4` o "intersecting …" | 287 |
| Solo vocabulario afín | 15 |
| Idioma | 1,739 inglés · 19 español (7 en ambos) |
| Tipo | 1,038 artículos · 331 capítulos · 138 reviews · 114 libros · 45 notas · 37 editoriales · 32 ponencias · 8 short surveys · 5 erratas · 3 conference reviews |

El export (CSV con información de citación, bibliográfica, abstract y keywords, sin truncar) se guarda como `data/v2_scopus_raw.csv`. No se versiona, por los términos de Scopus. El flujo de exclusiones está en `data/v2_prisma_meta.json` y el cribado registro a registro en `data/v2_cribado.csv`.

---

## 4. Expansión multi-base (pendiente; SciELO se ejecutó en la v3, §7, y OpenAlex en la v4, §8)

Las mismas cadenas potenciadas se pueden portar a otras bases con ajustes de sintaxis. Ver `project_revisa_pending.md` para el toolkit fetcher previsto.

| Base | Campo equivalente | Nota |
|---|---|---|
| Web of Science | `TS=` (Topic) | Sintaxis casi idéntica; `AND / OR / NEAR` |
| OpenAlex (API) | `abstract.search` + `title.search` | Sin operadores anidados nativos → dividir en varios queries |
| SciELO | Web: `ti,ab,kw:` | Cobertura fuerte de literatura iberoamericana |
| PubMed | `[Title/Abstract]` + MeSH | Solo salud/epidemiología; útil para eje "health disparities" |
| Redalyc / Latindex / CLACSO / Dialnet | Interfaz web | Ejecutar por bloques (una búsqueda por eje climático) por límites de sintaxis |

---

## 5. Registro de ejecución

Cada corrida se registra en `data/search_log.csv`:

- Fecha (UTC)
- Base y plataforma (Scopus web, Scopus API, WoS, OpenAlex, …)
- Versión de la cadena (v1, v2a, v2c, …)
- Idioma / filtros aplicados
- N de resultados brutos
- Ruta del archivo exportado
- Notas (excepciones, timeouts, límites de export)

---

## 7. v3 ejecutada (24 de noviembre de 2026) — Scopus + SciELO

Cadenas revisadas: trilingües (inglés, español y portugués), con un bloque interseccional que agrega vocabulario en portugués (*intersecionalidade, consubstancialidade, marcadores sociais da diferença*…) y un bloque climático más amplio (desastres, migración y movilidad, transición, salud y calor, términos en portugués). Están tal como se ejecutaron en `data/v3_query_scopus.txt` y `data/v3_query_scielo.txt`. A la cadena de Scopus se le agregó un paréntesis que faltaba para cerrar el primer `TITLE-ABS-KEY`.

### 7.1 Scopus (API)

`pipeline/v3/00_scopus_api.py` corre la cadena en la Scopus Search API, vista COMPLETE (trae resumen y palabras clave):

- La API no acepta `LIMIT-TO`: los idiomas se piden con `AND LANGUAGE(english|spanish|portuguese)`, una consulta por idioma, para saber en qué idioma indexa Scopus cada registro.
- La cadena codificada pasa de 9 KB y la API responde 413. Por eso el bloque climático se parte en grupos de términos unidos por OR, con consultas de hasta ~3,400 caracteres codificados: `bloque_interseccional AND TITLE-ABS-KEY(grupo_i) AND PUBYEAR > 1988 AND LANGUAGE(x)`. La unión de los grupos equivale a la cadena original. Si la API rechaza un grupo por largo (413, o 400 «Request header is too large»), ese grupo se parte en dos. La descarga terminó con 22 grupos.
- Resultado: **1,882 registros únicos** (1,865 en inglés, 21 en español, 9 en portugués); 46 sin resumen. Dos corridas dieron los mismos 1,882 EID. Metadatos en `data/v3_search_meta.json`.

### 7.2 SciELO

La cadena se corrió en search.scielo.org y se exportó en RIS (todas las referencias): **34 registros**, que quedan en `data/v3_scielo_export.json`. Cuando un registro trae resúmenes en varios idiomas, se conserva el que tiene más palabras funcionales en inglés.

### 7.3 Ingesta (`pipeline/v3/01_ingesta.py`)

| Paso | Scopus | SciELO |
|---|---|---|
| Identificados | 1,882 | 34 |
| Sin resumen (<100 caracteres) | −46 | −1 |
| Erratum / Conference review | −8 | 0 |
| Duplicados dentro de la fuente | −5 | −5 |
| Ya en Scopus | — | −7 |
| **A cribado** | **1,823** | **21** |

Total a cribado: **1,844**. De ellos, 1,695 están en la v2 (por EID, DOI o título) y 1,686 tienen el mismo resumen (similitud ≥ 0.98 sin la línea de copyright): conservan la evaluación de la v2. Los 158 restantes se evaluaron con `prompts/v3_cribado_rsi.md`. El cribado deja **1,088 elegibles** (1,010 con evaluación de la v2, 78 nuevos).

---

## 8. v4 ejecutada (24 de noviembre de 2026) — + OpenAlex en español y portugués

La v4 conserva el corpus de la v3 (Scopus + SciELO) y le suma los trabajos en **español y portugués** que OpenAlex recupera con las mismas cadenas. El objetivo es cubrir literatura iberoamericana que no indexan Scopus ni SciELO (tesis, capítulos de libro, revistas regionales).

### 8.1 Consulta (`data/v4_query_openalex.json`)

OpenAlex no tiene el lenguaje de consulta de Scopus, así que las cadenas v3 se tradujeron a sus filtros:

```
filter=title_and_abstract.search:<términos interseccionales separados por |>,
       title_and_abstract.search:<términos climáticos separados por |>,
       language:es|pt,publication_year:>1988
```

- Cada bloque es un filtro de `title_and_abstract.search` con valores separados por `|` (OR); los filtros se unen con comas (AND). No se usa `AND`/`OR` en el texto porque OpenAlex limita las búsquedas con más de 5 operadores booleanos.
- **Sin comodines ni proximidad.** Los términos con `*` se escriben con sus variantes en español y portugués (*interseccional, interseccionales, intersecional, intersecionais…*); las expresiones con `W/n` se omiten (las formas *interseccional\** las cubren casi siempre). Quedan 57 términos interseccionales y 177 climáticos.
- **Lematización en inglés.** OpenAlex lematiza: *intersectional* también recupera *intersection*. Eso trae ruido (cruces de calles, intersección de capas en SIG, «la intersección entre dos temas») que el cribado retira.
- **Idioma por el título.** OpenAlex asigna el idioma del trabajo según el título; hay registros en español o portugués con resumen en inglés, y algunos en inglés marcados como español o portugués.
- Solo español y portugués: lo que OpenAlex tiene en inglés ya lo cubre Scopus, con su búsqueda más fina.

### 8.2 Descarga (`pipeline/v4/00_openalex.py`)

Los bloques se parten en grupos (hasta 30 términos interseccionales × 45 climáticos) y se corren todas las combinaciones: **8 consultas**, 776 resultados con repetidos, **470 trabajos únicos** (272 en portugués, 198 en español), unidos por ID de OpenAlex. El resumen se reconstruye a partir del índice invertido de OpenAlex. Sin clave de API cabe en el presupuesto diario gratuito; la paginación es simple (`page=`), porque el cursor exige clave. Metadatos en `data/v4_openalex_meta.json`.

Tipos de documento: 242 artículos, 107 tesis, 53 capítulos de libro, 20 libros, 14 ponencias, 14 editoriales, 8 informes y otros.

### 8.3 Ingesta (`pipeline/v4/01_ingesta.py`)

| Paso | OpenAlex |
|---|---|
| Identificados | 470 |
| Sin resumen (<100 caracteres) | −13 |
| Tipos que no son trabajos (paratext, dataset, book review) | −3 |
| Duplicados dentro de OpenAlex | −1 |
| Ya en la v3 (por DOI o título + año + primer autor) | −24 |
| **Nuevos a cribado** | **429** (251 en portugués, 178 en español) |

Los 1,844 registros de la v3 conservan su paper_id y su evaluación; los 24 que OpenAlex también encontró quedan marcados en `_source` (`…+openalex`). Total a cribado: **2,273**. Los 429 nuevos se evaluaron con el mismo prompt de la v3 (`prompts/v3_cribado_rsi.md`). El cribado deja **1,212 elegibles** (1,088 de la v3 y 124 nuevos de OpenAlex: 56 en español y 68 en portugués). La mayoría de los nuevos que se excluyen son ruido de la lematización (*intersection* en sentido vial, cartográfico o de cruce de temas) o trabajos interseccionales sin objeto climático.

---

## 6. Referencias sobre construcción de queries

- Booth, A., Sutton, A., Papaioannou, D. (2016). *Systematic Approaches to a Successful Literature Review*. Sage. — Cap. 5 (search strategy).
- PRISMA-S (2021). *Reporting guideline for search strategies in systematic reviews*.
- Bramer, W. M. et al. (2018). Optimal database combinations for literature searches in systematic reviews. *Systematic Reviews*, 7(1).
