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

## 3. Expansión multi-base (pendiente)

Las mismas cadenas potenciadas se pueden portar a otras bases con ajustes de sintaxis. Ver `project_revisa_pending.md` para el toolkit fetcher previsto.

| Base | Campo equivalente | Nota |
|---|---|---|
| Web of Science | `TS=` (Topic) | Sintaxis casi idéntica; `AND / OR / NEAR` |
| OpenAlex (API) | `abstract.search` + `title.search` | Sin operadores anidados nativos → dividir en varios queries |
| SciELO | Web: `ti,ab,kw:` | Cobertura fuerte de literatura iberoamericana |
| PubMed | `[Title/Abstract]` + MeSH | Solo salud/epidemiología; útil para eje "health disparities" |
| Redalyc / Latindex / CLACSO / Dialnet | Interfaz web | Ejecutar por bloques (una búsqueda por eje climático) por límites de sintaxis |

---

## 4. Registro de ejecución

Cada corrida debe registrar en `data/search_log.csv`:

- Fecha (UTC)
- Base y plataforma (Scopus web, Scopus API, WoS, OpenAlex, …)
- Versión de la cadena (v1, v2a, v2c, …)
- Idioma / filtros aplicados
- N de resultados brutos
- Ruta del archivo exportado
- Notas (excepciones, timeouts, límites de export)

---

## 5. Referencias sobre construcción de queries

- Booth, A., Sutton, A., Papaioannou, D. (2016). *Systematic Approaches to a Successful Literature Review*. Sage. — Cap. 5 (search strategy).
- PRISMA-S (2021). *Reporting guideline for search strategies in systematic reviews*.
- Bramer, W. M. et al. (2018). Optimal database combinations for literature searches in systematic reviews. *Systematic Reviews*, 7(1).
