#!/usr/bin/env python3
"""
11_validacion.py — v2: validación humana que repite, sobre una muestra, lo que hizo el LLM.

El codificador sigue los mismos pasos del prompt de la v2 (prompts/v2_cribado_rsi.md),
con las mismas definiciones, reglas y ejemplos, y sin ver las respuestas del LLM:
  Paso 0  inclusión: ¿interseccionalidad en sentido social? ¿objeto climático?
  Paso 1  gate
  Paso 2  criterios I–VI (0 / 0.5 / 1)
  Paso 3  integración (0 / 0.5 / 1)
La página calcula el puntaje RSI con la fórmula del pipeline
(pipeline/02_scoring_rsi.py::compute_total) y, al pedirlo, la concordancia humano–LLM:
cribado, gate, criterios y categoría RSI (κ de Cohen, κ ponderado, IC bootstrap).

Muestra: 20 bloques de 7 trabajos (140). Cada bloque trae 2 registros que el LLM excluyó
(1 por no invocar la interseccionalidad, 1 por objeto no climático) y 1 de cada categoría
RSI, en orden aleatorio dentro del bloque. Cualquier número de bloques completos es una
muestra balanceada, y la posición no delata el estrato. Quedan fuera del marco muestral
los casos ejemplares que el dashboard muestra con su puntaje y el trabajo retractado.

Las respuestas del LLM no van en la página de codificación: van en
site/v2/validacion_llm.js, que la página carga solo al pedir la concordancia.

Salidas:
  data/v2_validation_sample.json   muestra + respuestas del LLM + tamaño de cada estrato
  site/v2/validacion.html          interfaz de codificación
  site/v2/validacion_llm.js        respuestas del LLM (se cargan al revelar)
"""
from __future__ import annotations
import hashlib
import json
import random
import pandas as pd
from pathlib import Path

DATA = Path("data"); DASHBOARD = Path("site/v2")

N_BLOQUES = 20           # 20 bloques × 7 estratos = 140 trabajos
SEED = 42

# Estrato → (descripción, filtro sobre el cribado del LLM)
ESTRATOS = [
    ('excl_interseccional', 'Excluido por el LLM: no invoca la interseccionalidad en sentido social'),
    ('excl_clima',          'Excluido por el LLM: invoca la interseccionalidad, pero el objeto no es climático'),
    ('mencion_sin_aplicacion', 'Elegible · RSI 0 (mención sin aplicación)'),
    ('nominal_debil',       'Elegible · RSI 0.5–1 (nominal)'),
    ('parcial',             'Elegible · RSI 1.5–2 (parcial)'),
    ('sustantivo',          'Elegible · RSI 2.5–3 (sustantiva)'),
    ('sustantivo_fuerte',   'Elegible · RSI 3.5–4 (sustantiva fuerte)'),
]

# ── Instrumento: el mismo texto que siguió el LLM (prompts/v2_cribado_rsi.md + bowleg_eval_v3.md) ──
PASO0 = [
    {"key": "ei", "label": "A · ¿Invoca la interseccionalidad en sentido teórico-social?",
     "si": ["Usa <i>intersectional / intersectionality / interseccional / interseccionalidad</i> en sentido social, aunque sea de pasada.",
            "Habla de intersecciones entre dos o más categorías sociales o sistemas de opresión («the intersection of race and gender», «intersecting inequalities»).",
            "Usa un marco afín en sentido social: <i>matrix of domination, interlocking oppressions, multiple jeopardy, kyriarchy, coloniality of gender, entangled inequalities, colonialidad del género, entronque patriarcal, imbricación de opresiones, matriz de dominación, consustancialidad</i>."],
     "no": ["«Intersection» solo significa el cruce de dos temas o campos («the intersection of climate and health», «at the intersection of gender and climate policy»).",
            "Tiene un sentido no social (vialidad, geometría, conjuntos), o <i>intersectional</i> significa «intersectorial».",
            "El vocabulario afín aparece en un sentido no social."]},
    {"key": "ec", "label": "B · ¿El objeto del trabajo se vincula con el cambio climático o con amenazas de origen climático?",
     "si": ["Impactos, vulnerabilidad, adaptación, mitigación, política, justicia, gobernanza, finanzas, migración o activismo climático.",
            "Amenazas hidrometeorológicas o climáticas (huracanes, ciclones, tormentas, inundaciones, sequías, calor extremo, incendios forestales, aumento del nivel del mar, erosión costera, deslizamientos por lluvia, glaciares), aunque no diga «cambio climático».",
            "Estudios de «desastres» o «amenazas naturales» en general (regla 1)."],
     "no": ["«Clima» en sentido no físico (campus, escolar, organizacional, político).",
            "Amenazas no climáticas (sismos, tsunamis, volcanes, desastres industriales o tecnológicos, pandemias, guerra) sin vínculo explícito con el clima.",
            "Obras de ficción o arte cuyo título menciona un fenómeno, pero cuyo análisis no trata el clima.",
            "El clima aparece solo como mención incidental (una frase de contexto o una lista de temas futuros)."]},
]

GATE = {"key": "gate", "label": "Gate · criterio de entrada",
        "q": "¿El trabajo articula <b>dos o más ejes de diferenciación social</b> (género, raza, clase, etnia, indigeneidad, edad, estatus migratorio, capacidad, sexualidad…) como <b>relacionados entre sí</b>, no solo mencionados por separado?",
        "si": ["Nombra al menos dos ejes y los relaciona entre sí.",
               "La población los implica sin ambigüedad («mujeres indígenas», «inmigrantes racializadas»).",
               "Teoriza explícitamente que un eje se cruza con otras categorías sociales, o que las posiciones surgen de estructuras de poder basadas en varias categorías, aunque no las nombre."],
        "no": ["Pone la etiqueta «interseccional» a un solo eje sin relacionarlo con otras categorías.",
               "Lista grupos o ejes por separado.",
               "Menciona la interseccionalidad solo como vacío de la literatura o agenda futura."]}

CRITERIOS = [
    {"key": "I", "label": "I · Identidades entrelazadas",
     "q": "¿Trata ≥2 ejes como mutuamente constitutivos (no aditivos)?",
     "niveles": [["1", "analiza cómo los ejes se co-construyen («ser mujer indígena no es mujer + indígena, es una posición específica»)"],
                 ["0.5", "menciona varios ejes pero los trata por separado o solo en la discusión"],
                 ["0", "un solo eje, o ejes sueltos sin relación"]]},
    {"key": "II", "label": "II · Poder estructural",
     "q": "¿Articula estructuras (racismo, patriarcado, colonialismo, capitalismo, capacitismo) y mecanismos, no rasgos individuales o culturales?",
     "niveles": [["1", "mecanismos estructurales explícitos + marco crítico"],
                 ["0.5", "nombra estructuras sin teorizar mecanismos"],
                 ["0", "atribuye a individuos o a la cultura, o no teoriza"]]},
    {"key": "III", "label": "III · Contexto sociohistórico situado",
     "q": "¿Sitúa los hallazgos en una historia, geografía y política específicas? ¿Reconoce que la interseccionalidad opera de forma situada?",
     "niveles": [["1", "contexto detallado + reconoce la no universalidad"],
                 ["0.5", "contexto superficial"],
                 ["0", "generalizaciones descontextualizadas"]]},
    {"key": "IV", "label": "IV · Método no aditivo",
     "q": "¿El diseño empírico capta interacciones (muestreo intencional de subgrupos interseccionales, codificación cruzada, interacciones en modelos)?",
     "niveles": [["1", "método que opera las intersecciones"],
                 ["0.5", "subgrupos descriptivos sin análisis interaccional"],
                 ["0", "variables paralelas; o solo teórico, sin operacionalización empírica"]],
     "nota": "Regla 4: en métodos cuantitativos, interacciones, moderación o clasificación cruzada interpretadas como posiciones sociales combinadas → I = 1 e IV = 1; ejes como variables separadas o de control → I = 0.5 (o 0) e IV = 0."},
    {"key": "V", "label": "V · Praxis y orientación a la justicia",
     "q": "¿Se orienta a transformar desigualdades (no solo a describirlas)? ¿Conecta el análisis con justicia social, política o ambiental?",
     "niveles": [["1", "orientación explícita a la transformación o la justicia, recomendaciones, crítica situada"],
                 ["0.5", "menciona implicaciones de justicia sin desarrollarlas"],
                 ["0", "puramente descriptivo, sin dimensión crítica o transformadora"]]},
    {"key": "VI", "label": "VI · Agencia y resistencia",
     "q": "¿Reconoce a los sujetos como agentes (estrategias, resistencia, conocimiento propio) y no solo como víctimas pasivas?",
     "niveles": [["1", "documenta agencia, resistencia, saberes o estrategias de los sujetos"],
                 ["0.5", "menciona la agencia marginalmente"],
                 ["0", "sujetos representados solo como víctimas u objetos"]]},
]

INTEGRACION = {"key": "integracion", "label": "Integración",
               "q": "¿Los elementos anteriores se <b>articulan en un análisis coherente</b>, o están <b>yuxtapuestos</b> (presentes pero sin conectarse)?",
               "niveles": [["1", "los criterios se integran (el poder estructural explica las identidades entrelazadas, que se analizan con el método, en su contexto…)"],
                           ["0.5", "integración parcial"],
                           ["0", "elementos yuxtapuestos sin articulación"]]}

REGLAS = [
    "<b>Juzga solo con lo que trae el registro</b>: título, resumen y palabras clave, lo mismo que vio el LLM. El DOI sirve para identificar el trabajo, no para leerlo completo.",
    "<b>Independencia teórica.</b> Evalúa la operacionalización del concepto, no la fidelidad a una autoría o región. Un trabajo puede puntuar alto con vocabulario diverso («colonialidad de género», «compounded vulnerability», «interlocking systems of oppression») sin citar a Crenshaw, Bowleg, Collins ni Lugones.",
    "<b>Regla 1 · Desastres.</b> Los estudios de «desastres» o «amenazas naturales» en general cuentan como climáticos. Quedan fuera los explícitamente no climáticos (sismos, tsunamis, volcanes, desastres tecnológicos, pandemias, conflictos sin vínculo climático).",
    "<b>Regla 2 · «Intersectional».</b> Si claramente significa «intersectorial» o «interdisciplinar», la respuesta A es No. Si es ambiguo, responde Sí (con confianza baja) y deja que el gate decida.",
    "<b>Regla 3 · Gate.</b> Pasa si el texto relaciona dos o más ejes como entrelazados: los nombra y los relaciona; la población los implica («mujeres indígenas»); o teoriza que un eje se cruza con otras categorías aunque no las nombre. No basta la etiqueta «interseccional» sobre un solo eje, una lista de grupos por separado, ni mencionar la interseccionalidad como agenda futura.",
    "<b>Regla 4 · Métodos cuantitativos.</b> Interacciones, moderación o clasificación cruzada interpretadas como posiciones combinadas → I = 1 e IV = 1. Ejes como variables separadas o de control → I = 0.5 (o 0) e IV = 0.",
    "<b>Cada trabajo por separado.</b> No compares con otros ni ajustes puntajes para equilibrar.",
]

EJEMPLOS = [
    "<b>A · gate = No (mención sin aplicación).</b> «Usamos un enfoque interseccional para revisar la literatura bibliométrica sobre energía y clima…», pero el resto solo cuenta trabajos por año y país. No articula ejes relacionados → RSI 0.",
    "<b>B · parcial (RSI ≈ 1.5–2).</b> Estudio cuantitativo que mide vulnerabilidad climática por género y por nivel socioeconómico en regresiones separadas, en un país. Gate = Sí; I = 0.5 (ejes aditivos), II = 0.5, III = 0.5, IV = 0 (sin interacciones), V = 0.5, VI = 0, integración = 0.5.",
    "<b>C · sustantiva fuerte (RSI ≈ 3.5–4).</b> Etnografía de mujeres indígenas en una costa específica; analiza cómo colonialidad, género y clase se co-constituyen en la exposición a ciclones; muestreo intencional; documenta estrategias de resistencia comunitaria; orientada a la justicia climática. Todo = 1.",
]

INSTRUMENTO = {"paso0": PASO0, "gate": GATE, "criterios": CRITERIOS, "integracion": INTEGRACION,
               "reglas": REGLAS, "ejemplos": EJEMPLOS}


def _s(x, n=None):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ''
    s = str(x).strip()
    return s[:n] if n else s


def _num(x):
    return None if (x is None or (isinstance(x, float) and pd.isna(x))) else float(x)


def _bool(x):
    return str(x).strip().lower() in ('true', '1', '1.0')


def _lang(x):
    x = _s(x).lower()
    if 'span' in x: return 'ES'
    if 'port' in x: return 'PT'
    if 'eng' in x: return 'EN'
    return ''


def _json_script(obj) -> str:
    """JSON seguro dentro de <script>: evita que un '</' de los datos cierre la etiqueta."""
    return json.dumps(obj, ensure_ascii=False).replace('</', '<\\/')


def main():
    print("[1] Cargando cribado, corpus y resultados RSI de la v2")
    cons = pd.read_csv(DATA / 'v2_corpus_consolidated.csv')
    cr = pd.read_csv(DATA / 'v2_cribado.csv')
    fin = pd.read_csv(DATA / 'v2_corpus_final.csv')
    razon = pd.read_csv(DATA / 'v2_reasoning_results.csv').set_index('paper_id')['razonamiento']
    casos = json.loads((DATA / 'v2_casos_ejemplares.json').read_text())

    for c in ['elig_interseccional', 'elig_clima', 'elegible', 'retractado']:
        cr[c] = cr[c].map(_bool)

    # Marco muestral: todo lo cribado, menos el retractado y los casos que el dashboard
    # ya muestra con su puntaje (el codificador los habría visto).
    titulos_casos = {c['titulo'] for c in casos}
    vistos = set(cons.loc[cons['Title'].fillna('').str.slice(0, 160).isin(titulos_casos), 'paper_id'])
    marco = cr[~cr['retractado'] & ~cr['paper_id'].isin(vistos)].merge(
        fin[['paper_id', 'categoria_bowleg']], on='paper_id', how='left')
    print(f"    marco: {len(marco)} registros (fuera: {int(cr['retractado'].sum())} retractado, "
          f"{len(vistos)} casos ejemplares del dashboard)")

    def estrato(r):
        if not r['elegible']:
            return 'excl_interseccional' if not r['elig_interseccional'] else 'excl_clima'
        return r['categoria_bowleg']
    marco['estrato'] = marco.apply(estrato, axis=1)
    poblacion = cr[~cr['retractado']].merge(fin[['paper_id', 'categoria_bowleg']], on='paper_id', how='left')
    poblacion['estrato'] = poblacion.apply(estrato, axis=1)
    n_pob = poblacion['estrato'].value_counts().to_dict()

    print(f"[2] Muestra: {N_BLOQUES} bloques × {len(ESTRATOS)} estratos (seed={SEED})")
    por_estrato = {}
    for key, _ in ESTRATOS:
        sub = marco[marco['estrato'] == key]
        if len(sub) < N_BLOQUES:
            raise SystemExit(f'El estrato {key} tiene {len(sub)} registros (< {N_BLOQUES})')
        por_estrato[key] = list(sub.sample(n=N_BLOQUES, random_state=SEED)['paper_id'])
    rng = random.Random(SEED)
    orden = []                          # (bloque, paper_id, estrato)
    for b in range(N_BLOQUES):
        bloque = [(por_estrato[k][b], k) for k, _ in ESTRATOS]
        rng.shuffle(bloque)
        orden += [(b + 1, pid, k) for pid, k in bloque]

    cons_i = cons.set_index('paper_id')
    cr_i = cr.set_index('paper_id')
    fin_i = fin.set_index('paper_id')
    items, llm = [], {}
    for pos, (bloque, pid, key) in enumerate(orden, 1):
        b = cons_i.loc[pid]
        items.append({
            "pos": pos, "bloque": bloque, "paper_id": str(pid),
            "title": _s(b.get('Title')), "authors": _s(b.get('Authors'), 300),
            "year": _s(b.get('Year')).replace('.0', ''), "source": _s(b.get('Source title')),
            "doc_type": _s(b.get('Document Type')), "lang": _lang(b.get('Language of Original Document')),
            "keywords": _s(b.get('Author Keywords'), 400), "doi": _s(b.get('DOI')),
            "abstract": _s(b.get('Abstract'), 5000),
        })
        c = cr_i.loc[pid]
        e = {"estrato": key, "ei": bool(c['elig_interseccional']), "ec": bool(c['elig_clima']),
             "elegible": bool(c['elegible']), "motivo": _s(c.get('motivo_exclusion')) or None,
             "confidence": _s(c.get('confidence')), "razonamiento": _s(razon.get(pid))}
        if e['elegible']:
            f = fin_i.loc[pid]
            e.update({
                "gate": 1 if _bool(f['gate_pass']) else 0,
                "I": _num(f['bowleg_I']), "II": _num(f['bowleg_II']), "III": _num(f['bowleg_III']),
                "IV": _num(f['bowleg_IV']), "V": _num(f['rsi_V']), "VI": _num(f['rsi_VI']),
                "integracion": _num(f['integracion']), "total": _num(f['bowleg_total']),
                "categoria": f['categoria_bowleg'], "tipo_estudio": _s(f.get('tipo_estudio')),
                "ev": {"gate": _s(f.get('gate_evidence')), "I": _s(f.get('bowleg_I_evidence')),
                       "II": _s(f.get('bowleg_II_evidence')), "III": _s(f.get('bowleg_III_evidence')),
                       "IV": _s(f.get('bowleg_IV_evidence')), "V": _s(f.get('rsi_V_evidence')),
                       "VI": _s(f.get('rsi_VI_evidence')), "integracion": _s(f.get('integracion_nota'))},
            })
        else:
            e["categoria"] = 'excluido'
        llm[str(pid)] = e

    llm_meta = {"estratos": [{"key": k, "desc": d, "N": int(n_pob.get(k, 0)), "n": N_BLOQUES} for k, d in ESTRATOS],
                "N_total": int(sum(n_pob.values()))}
    llm_payload = {"meta": llm_meta, "by_id": llm}
    version = hashlib.sha1(json.dumps(llm_payload, sort_keys=True).encode()).hexdigest()[:10]
    meta = {"n": len(items), "bloques": N_BLOQUES, "por_bloque": len(ESTRATOS), "seed": SEED,
            "version": version, "corpus_cribado": int(len(cr)),
            "fuente": "Scopus · búsqueda ampliada v2 (30-09-2026)"}

    full = {"meta": {**meta, **llm_meta},
            "items": [{**it, "llm": llm[it['paper_id']]} for it in items]}
    (DATA / 'v2_validation_sample.json').write_text(json.dumps(full, ensure_ascii=False, indent=2))
    print(f"    → data/v2_validation_sample.json ({len(items)} trabajos)")

    (DASHBOARD / 'validacion_llm.js').write_text(
        "// Respuestas del LLM para la muestra de validación (las carga validacion.html al revelar).\n"
        f"window.LLM_V2 = {json.dumps(llm_payload, ensure_ascii=False)};\n")
    print(f"    → {DASHBOARD / 'validacion_llm.js'}")

    html = (HTML_TEMPLATE
            .replace('__SAMPLE_JSON__', _json_script({"meta": meta, "items": items}))
            .replace('__INSTRUMENTO_JSON__', _json_script(INSTRUMENTO))
            .replace('__N__', str(len(items)))
            .replace('__BLOQUES__', str(N_BLOQUES))
            .replace('__POR_BLOQUE__', str(len(ESTRATOS))))
    (DASHBOARD / 'validacion.html').write_text(html)
    print(f"[3] → {DASHBOARD / 'validacion.html'} ({len(html):,} caracteres)")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Validación humana · REVISA v2</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root { --accent:#1a73e8; --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --bg:#f3f4f6; }
  * { box-sizing:border-box; }
  body { font-family:'Inter',system-ui,sans-serif; margin:0; background:var(--bg); color:var(--ink); line-height:1.55; }
  .wrap { max-width:880px; margin:0 auto; padding:0 16px 80px; }
  .top { position:sticky; top:0; z-index:50; background:#0f172a; color:#fff; padding:12px 16px;
    box-shadow:0 2px 8px rgba(0,0,0,.15); }
  .top .inner { max-width:880px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .top h1 { font-size:15.5px; margin:0; font-weight:700; }
  .top h1 span { font-size:11px; font-weight:700; background:#1d4ed8; padding:2px 7px; border-radius:6px; margin-left:6px; vertical-align:2px; }
  .toplinks { display:flex; gap:14px; flex-wrap:wrap; }
  .top a { color:#93c5fd; font-size:12.5px; text-decoration:none; }
  .top a:hover { text-decoration:underline; }
  .progress-wrap { background:#1e293b; height:6px; }
  .progress-bar { background:#3b82f6; height:6px; width:0%; transition:width .2s; }
  .intro { background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 18px; margin:16px 0 10px; font-size:13px; }
  .intro summary { cursor:pointer; font-weight:600; color:var(--accent); }
  .intro ul { margin:8px 0 4px; padding-left:20px; }
  .intro li { margin:3px 0; }
  .intro + .intro { margin-top:0; }
  .setup { display:flex; flex-wrap:wrap; gap:10px 22px; align-items:center; font-size:12.5px; color:var(--muted); margin:8px 2px 4px; }
  .setup input[type=text] { font-family:inherit; font-size:12.5px; padding:5px 8px; border:1px solid #cbd5e1; border-radius:6px; width:190px; }
  .setup label { display:flex; gap:6px; align-items:center; cursor:pointer; }
  .card { background:#fff; border:1px solid var(--line); border-radius:12px; padding:18px 20px; margin:12px 0;
    box-shadow:0 1px 3px rgba(0,0,0,.06); }
  .pid { font-size:11px; color:var(--muted); letter-spacing:.3px; }
  .ptitle { font-size:16px; font-weight:700; margin:4px 0 6px; line-height:1.35; }
  .pmeta { font-size:12px; color:var(--muted); margin-bottom:6px; }
  .kw { font-size:12px; color:#4b5563; margin-bottom:8px; }
  .pill { display:inline-block; padding:1px 7px; border-radius:8px; font-size:10px; font-weight:700; margin-left:6px; vertical-align:2px; }
  .pill.ES { background:#ffebee; color:#b71c1c; } .pill.PT { background:#e3f2fd; color:#0d47a1; }
  .pill.EN { background:#f1f5f9; color:#475569; }
  .abstract { font-size:13px; color:#374151; background:#f9fafb; border:1px solid var(--line);
    border-radius:8px; padding:12px 14px; max-height:260px; overflow-y:auto; margin-bottom:4px; white-space:pre-wrap; }
  .doi { font-size:12px; }
  .seen-note { font-size:12px; color:#7c2d12; background:#fff7ed; border:1px solid #fed7aa; border-radius:8px; padding:7px 11px; margin:8px 0; }
  .step { border-top:2px solid #e2e8f0; margin-top:14px; padding-top:10px; }
  .step-h { font-size:11px; font-weight:800; letter-spacing:1px; text-transform:uppercase; color:#1d4ed8; }
  .step.off { opacity:.42; }
  .step.off .seg button { cursor:not-allowed; }
  .crit { padding:9px 0 3px; }
  .crit + .crit { border-top:1px dashed var(--line); }
  .crit-label { font-size:13.5px; font-weight:700; }
  .crit-q { font-size:12.5px; color:#4b5563; margin:2px 0 7px; }
  .levels { font-size:11.5px; color:var(--muted); margin:2px 0 8px; padding-left:0; list-style:none; }
  .levels li { margin:1px 0; }
  .levels b { display:inline-block; min-width:30px; color:#374151; }
  .levels .yes b { color:#065f46; } .levels .no b { color:#991b1b; }
  .crit-nota { font-size:11.5px; color:#92400e; background:#fffbeb; border-radius:6px; padding:5px 9px; margin:0 0 8px; }
  .hide-levels .levels, .hide-levels .crit-nota { display:none; }
  .seg { display:inline-flex; flex-wrap:wrap; border:1px solid #cbd5e1; border-radius:8px; overflow:hidden; }
  .seg button { border:none; background:#fff; padding:7px 16px; font-size:13px; cursor:pointer;
    font-family:inherit; color:#475569; border-right:1px solid #e2e8f0; transition:background .1s; }
  .seg button:last-child { border-right:none; }
  .seg button:hover:not(:disabled) { background:#f1f5f9; }
  .seg button.sel-no { background:#fee2e2; color:#991b1b; font-weight:700; box-shadow:inset 0 0 0 2px #f87171; }
  .seg button.sel-mid { background:#ffedd5; color:#9a3412; font-weight:700; box-shadow:inset 0 0 0 2px #fb923c; }
  .seg button.sel-yes { background:#d1fae5; color:#065f46; font-weight:700; box-shadow:inset 0 0 0 2px #10b981; }
  .seg button.sel-neutral { background:#e0e7ff; color:#3730a3; font-weight:700; box-shadow:inset 0 0 0 2px #818cf8; }
  .verdict { font-size:12.5px; border-radius:8px; padding:8px 12px; margin-top:10px; }
  .verdict.no { color:#7f1d1d; background:#fef2f2; border:1px solid #fecaca; }
  .verdict.yes { color:#065f46; background:#ecfdf5; border:1px solid #a7f3d0; }
  .score { margin-top:14px; background:#0f172a; color:#e2e8f0; border-radius:10px; padding:12px 16px; font-size:12.5px; }
  .score .big { font-size:20px; font-weight:800; color:#fff; }
  .cat { display:inline-block; margin-left:8px; font-size:12px; font-weight:700; padding:2px 9px; border-radius:7px; vertical-align:3px; }
  .score .formula { color:#94a3b8; margin-top:4px; font-variant-numeric:tabular-nums; }
  .extra { display:flex; flex-wrap:wrap; gap:8px 18px; align-items:center; margin-top:12px; font-size:12.5px; color:var(--muted); }
  .extra .seg button { padding:5px 12px; font-size:12px; }
  .nota { width:100%; margin-top:8px; font-family:inherit; font-size:12.5px; padding:8px 10px;
    border:1px solid var(--line); border-radius:8px; resize:vertical; min-height:42px; }
  .nav { display:flex; justify-content:space-between; align-items:center; margin:14px 0; gap:10px; flex-wrap:wrap; }
  .btn { background:var(--accent); color:#fff; border:none; padding:10px 18px; border-radius:8px;
    font-size:14px; font-weight:600; cursor:pointer; font-family:inherit; }
  .btn:hover { background:#1557b0; } .btn:disabled { background:#cbd5e1; cursor:not-allowed; }
  .btn.ghost { background:#fff; color:var(--ink); border:1px solid #cbd5e1; }
  .btn.ghost:hover { background:#f8fafc; }
  .btn.sm { padding:8px 13px; font-size:12.5px; }
  .status { text-align:center; font-size:12.5px; color:var(--muted); }
  .status b { color:#059669; }
  .tools { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin-top:12px; }
  .reveal { background:#fff; border:1px solid var(--line); border-radius:12px; padding:18px 20px; margin:16px 0; display:none; }
  .reveal h2 { font-size:17px; margin:0 0 4px; }
  .reveal h3 { font-size:13.5px; margin:20px 0 6px; }
  .reveal .sub { font-size:12px; color:var(--muted); margin:0 0 6px; }
  .kpis { display:flex; flex-wrap:wrap; gap:12px; margin:10px 0 4px; }
  .kpi { flex:1 1 150px; border:1px solid var(--line); border-radius:10px; padding:10px 12px; }
  .kpi .v { font-size:24px; font-weight:800; color:var(--accent); font-variant-numeric:tabular-nums; }
  .kpi .l { font-size:11.5px; color:var(--muted); line-height:1.35; }
  .tablewrap { overflow-x:auto; }
  .ktable { border-collapse:collapse; width:100%; font-size:12.5px; margin-top:6px; font-variant-numeric:tabular-nums; }
  .ktable th, .ktable td { border:1px solid var(--line); padding:6px 8px; text-align:center; }
  .ktable th { background:#f8fafc; font-weight:600; }
  .ktable td:first-child, .ktable th:first-child { text-align:left; }
  .ktable td.diag { background:#ecfdf5; font-weight:700; }
  .ktable td.zero { color:#cbd5e1; }
  .agree-hi { color:#047857; font-weight:700; } .agree-lo { color:#b91c1c; font-weight:700; }
  .done-flag { color:#059669; font-weight:700; }
  .fine { font-size:11.5px; color:#6b7280; margin-top:10px; }
  .dis { border:1px solid var(--line); border-radius:10px; padding:10px 14px; margin:8px 0; font-size:12.5px; }
  .dis .t { font-weight:700; font-size:13px; }
  .dis .row { margin:3px 0; font-variant-numeric:tabular-nums; }
  .dis .who { display:inline-block; min-width:44px; font-weight:700; color:#374151; }
  .dis .diff { background:#fee2e2; border-radius:4px; padding:0 3px; }
  .dis details { margin-top:4px; } .dis summary { cursor:pointer; color:var(--accent); }
  .dis .ev { margin:3px 0 0 12px; color:#4b5563; }
  .linkbtn { background:none; border:none; color:var(--accent); cursor:pointer; padding:0; font-family:inherit; font-size:12.5px; }
  @media (max-width:600px) { .seg button { padding:7px 11px; } .card { padding:14px; } }
</style>
</head>
<body>
<div class="top">
  <div class="inner">
    <h1>Validación humana · cribado + RSI<span>v2</span></h1>
    <div class="toplinks">
      <a href="corpus.html">☰ Lista completa del corpus</a>
      <a href="index.html">← Volver al dashboard</a>
    </div>
  </div>
</div>
<div class="progress-wrap"><div class="progress-bar" id="pbar"></div></div>

<div class="wrap">
  <details class="intro" id="introHow">
    <summary>¿Cómo funciona? (leer una vez)</summary>
    <ul>
      <li>Repites, sobre una muestra, <b>los mismos pasos que siguió el LLM</b> con cada registro: <b>Paso 0</b> inclusión (¿pertenece al corpus?), <b>Paso 1</b> gate, <b>Paso 2</b> criterios I–VI y <b>Paso 3</b> integración. Las definiciones, reglas y ejemplos son los del prompt (<code>prompts/v2_cribado_rsi.md</code>).</li>
      <li>Cada criterio vale <b>0, 0.5 o 1</b>. La página calcula tu <b>puntaje RSI</b> con la misma fórmula del pipeline: <b>(Σ criterios / 6 × 4) × (0.5 + 0.5 × integración)</b>, redondeado a 0.5. Gate = No → 0.</li>
      <li><b>A ciegas:</b> esta página no contiene las respuestas del LLM. Se cargan solo cuando pides la concordancia. No revises la <a href="corpus.html">lista completa del corpus</a> antes de codificar: ahí sí se ven.</li>
      <li><b>Muestra:</b> __N__ trabajos en __BLOQUES__ bloques de __POR_BLOQUE__. Cada bloque trae registros que el LLM incluyó y excluyó, de todos los niveles de la RSI, en orden aleatorio. Si te detienes al final de un bloque, la muestra sigue balanceada. Recomendado: al menos 10 bloques.</li>
      <li>Tu avance se guarda en este navegador. Descarga un <b>respaldo</b> para continuar en otro equipo (botón «Importar respaldo»).</li>
    </ul>
  </details>
  <details class="intro">
    <summary>Reglas para casos límite y ejemplos de calibración (los mismos que recibió el LLM)</summary>
    <ul id="reglas"></ul>
    <div style="font-weight:600;margin-top:8px">Ejemplos de calibración</div>
    <ul id="ejemplos"></ul>
  </details>

  <div class="setup">
    <label>Codificador/a: <input type="text" id="coder" placeholder="tu nombre o iniciales"></label>
    <label><input type="checkbox" id="showLevels"> mostrar la definición de cada nivel</label>
  </div>

  <div class="status" id="topstatus"></div>
  <div class="card" id="card"></div>

  <div class="nav">
    <button class="btn ghost" id="prev">← Anterior</button>
    <div class="status" id="counter"></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn ghost" id="nextTodo" title="Salta al siguiente trabajo sin terminar">Siguiente pendiente</button>
      <button class="btn" id="next">Siguiente →</button>
    </div>
  </div>

  <div class="tools">
    <button class="btn sm" id="kappaBtn">Ver concordancia con el LLM</button>
    <button class="btn sm ghost" id="csvBtn">Exportar mis códigos (CSV)</button>
    <button class="btn sm ghost" id="jsonBtn">Descargar respaldo</button>
    <button class="btn sm ghost" id="importBtn">Importar respaldo</button>
    <button class="btn sm ghost" id="resetBtn">Borrar mis códigos</button>
    <input type="file" id="importFile" accept="application/json,.json" style="display:none">
  </div>
  <div class="status" id="savedinfo" style="margin-top:8px"></div>

  <div class="reveal" id="reveal"></div>
</div>

<script>
const DATA = __SAMPLE_JSON__;
const INS = __INSTRUMENTO_JSON__;
const ITEMS = DATA.items;
const POS = Object.fromEntries(ITEMS.map((it, i) => [it.paper_id, i]));
const LSKEY = 'revisa_v2_validacion';
const K6 = ['I','II','III','IV','V','VI'];
const CATS = ['mencion_sin_aplicacion','nominal_debil','parcial','sustantivo','sustantivo_fuerte'];
const CATS6 = ['excluido'].concat(CATS);
const CAT_LABEL = { excluido:'Excluido', mencion_sin_aplicacion:'Mención (0)', nominal_debil:'Nominal (0.5–1)',
  parcial:'Parcial (1.5–2)', sustantivo:'Sustantiva (2.5–3)', sustantivo_fuerte:'Sustantiva fuerte (3.5–4)' };
const CAT_COLOR = { excluido:['#e5e7eb','#374151'], mencion_sin_aplicacion:['#8d6e63','#fff'], nominal_debil:['#ef5350','#fff'],
  parcial:['#ffa726','#1f2937'], sustantivo:['#66bb6a','#1f2937'], sustantivo_fuerte:['#1b5e20','#fff'] };
const CONF = [['alta','high'],['media','medium'],['baja','low']];
const CONF_ES = { high:'alta', medium:'media', low:'baja' };

let store = { coder:'', codes:{}, seen:{}, showLevels:true, idx:0 };
try {
  const s = JSON.parse(localStorage.getItem(LSKEY) || 'null');
  if (s && s.codes) store = Object.assign(store, s);
} catch (e) {}
let idx = Math.max(0, Math.min(store.idx || 0, ITEMS.length - 1));
let saveOk = true;
function save() {
  store.idx = idx;
  try { localStorage.setItem(LSKEY, JSON.stringify(store)); saveOk = true; } catch (e) { saveOk = false; }
}

const esc = s => String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const has = v => v !== undefined && v !== null;
const fmt = (v, d=1) => (v == null || isNaN(v)) ? '—' : Number(v).toLocaleString('en-US', {minimumFractionDigits:d, maximumFractionDigits:d});
const pct = v => (v == null || isNaN(v)) ? '—' : Math.round(100 * v) + '%';
function curId() { return ITEMS[idx].paper_id; }
function code(pid) { return store.codes[pid] || {}; }

// ── Lógica del instrumento (idéntica al pipeline) ──
function elegible(c) {
  if (!has(c.ei) || !has(c.ec)) return null;
  return (c.ei === 1 && c.ec === 1) ? 1 : 0;
}
function isComplete(c) {
  const e = elegible(c);
  if (e === null) return false;
  if (e === 0) return true;
  if (!has(c.gate)) return false;
  if (c.gate === 0) return true;
  return K6.every(k => has(c[k])) && has(c.integracion);
}
function faltan(c) {
  const e = elegible(c), out = [];
  if (!has(c.ei)) out.push('A'); if (!has(c.ec)) out.push('B');
  if (e !== 1) return out;
  if (!has(c.gate)) { out.push('gate'); return out; }
  if (c.gate === 0) return out;
  K6.forEach(k => { if (!has(c[k])) out.push(k); });
  if (!has(c.integracion)) out.push('integración');
  return out;
}
// round() de Python redondea los empates al par (0.5 → 0; 2.5 → 2): se replica para que
// el total humano y el del LLM salgan de exactamente la misma fórmula.
function roundHalfEven(x) {
  const f = Math.floor(x), d = x - f;
  if (d > 0.5) return f + 1;
  if (d < 0.5) return f;
  return (f % 2 === 0) ? f : f + 1;
}
function rsiTotal(c) {            // = pipeline/02_scoring_rsi.py::compute_total
  if (c.gate !== 1) return 0;
  let core = 0; for (const k of K6) core += c[k];
  const norm = core / 6.0 * 4.0;
  const factor = 0.5 + 0.5 * c.integracion;
  return roundHalfEven(norm * factor * 2) / 2;
}
function categoria(t) {
  if (t >= 3.5) return 'sustantivo_fuerte';
  if (t >= 2.5) return 'sustantivo';
  if (t >= 1.5) return 'parcial';
  if (t > 0) return 'nominal_debil';
  return 'mencion_sin_aplicacion';
}
function humanResult(c) {
  if (!isComplete(c)) return null;
  if (elegible(c) === 0) return { cat:'excluido', total:null };
  const t = rsiTotal(c);
  return { cat: categoria(t), total: t };
}
function catPill(cat) {
  const [bg, fg] = CAT_COLOR[cat] || ['#e5e7eb', '#374151'];
  return `<span class="cat" style="background:${bg};color:${fg}">${CAT_LABEL[cat] || cat}</span>`;
}

// ── Render ──
function seg(key, opts, val, off, kind) {
  return '<div class="seg" role="group">' + opts.map(([lbl, v]) => {
    let cls = '';
    if (val === v) cls = kind === 'conf' ? 'sel-neutral' : (v === 0 ? 'sel-no' : (v === 1 ? 'sel-yes' : 'sel-mid'));
    const arg = typeof v === 'string' ? `'${v}'` : v;
    return `<button type="button" class="${cls}" aria-pressed="${val === v}" ${off ? 'disabled' : ''} onclick="setVal('${key}', ${arg})">${lbl}</button>`;
  }).join('') + '</div>';
}
const OPT2 = [['No', 0], ['Sí', 1]];
const OPT3 = [['No · 0', 0], ['Parcial · 0.5', 0.5], ['Sí · 1', 1]];

function siNo(list, cls, head) {
  return `<ul class="levels"><li class="${cls}"><b>${head}</b></li>` + list.map(t => `<li class="${cls}">· ${t}</li>`).join('') + '</ul>';
}
function niveles(cr) {
  return '<ul class="levels">' + cr.niveles.map(([n, t]) => `<li><b>${n}</b>${t}</li>`).join('') + '</ul>' +
    (cr.nota ? `<div class="crit-nota">${cr.nota}</div>` : '');
}

function render() {
  const it = ITEMS[idx], c = code(it.paper_id), e = elegible(c);
  const off1 = e !== 1, off2 = off1 || c.gate !== 1;
  const seen = !!store.seen[it.paper_id];

  let p0 = INS.paso0.map(q => `<div class="crit">
      <div class="crit-label">${q.label}</div>
      ${siNo(q.si, 'yes', 'Sí si…')}${siNo(q.no, 'no', 'No si…')}
      ${seg(q.key, OPT2, c[q.key], false)}
    </div>`).join('');
  if (e === 0) p0 += `<div class="verdict no"><b>No elegible:</b> el registro queda fuera del corpus y no se puntúa la RSI (igual que hace el LLM). Puedes pasar al siguiente.</div>`;
  if (e === 1) p0 += `<div class="verdict yes"><b>Elegible:</b> continúa con el gate.</div>`;

  const g = INS.gate;
  let p1 = `<div class="crit"><div class="crit-label">${g.label}</div><div class="crit-q">${g.q}</div>
      ${siNo(g.si, 'yes', 'Pasa si…')}${siNo(g.no, 'no', 'No pasa si…')}
      ${seg('gate', OPT2, c.gate, off1)}</div>`;
  if (!off1 && c.gate === 0) p1 += `<div class="verdict no"><b>Gate = No:</b> el trabajo no articula ejes de forma relacional; su RSI es 0 y no se puntúan los criterios.</div>`;

  const p2 = INS.criterios.map(cr => `<div class="crit">
      <div class="crit-label">${cr.label}</div><div class="crit-q">${cr.q}</div>
      ${niveles(cr)}${seg(cr.key, OPT3, c[cr.key], off2)}</div>`).join('');
  const ig = INS.integracion;
  const p3 = `<div class="crit"><div class="crit-label">${ig.label}</div><div class="crit-q">${ig.q}</div>
      ${niveles(ig)}${seg('integracion', OPT3, c.integracion, off2)}</div>`;

  // Panel de puntaje
  let score;
  const falt = faltan(c);
  if (e === 0) score = `<div class="big">No elegible</div><div class="formula">Fuera del corpus · sin RSI</div>`;
  else if (e === 1 && c.gate === 0) score = `<div class="big">RSI = 0 ${catPill('mencion_sin_aplicacion')}</div><div class="formula">Gate = No → 0</div>`;
  else if (isComplete(c)) {
    const core = K6.reduce((a, k) => a + c[k], 0), norm = core / 6 * 4, fac = 0.5 + 0.5 * c.integracion, t = rsiTotal(c);
    score = `<div class="big">RSI = ${fmt(t)} ${catPill(categoria(t))}</div>
      <div class="formula">Σ criterios = ${fmt(core)} → ${fmt(core)} / 6 × 4 = ${fmt(norm, 2)} · × (0.5 + 0.5 × ${fmt(c.integracion)}) = ${fmt(norm * fac, 2)} → redondeado a 0.5: <b style="color:#fff">${fmt(t)}</b></div>`;
  } else score = `<div class="big" style="font-size:15px">Tu puntaje aparecerá al completar los pasos</div><div class="formula">Falta: ${falt.join(', ')}</div>`;

  const lang = it.lang ? `<span class="pill ${it.lang}">${it.lang}</span>` : '';
  const doiUrl = it.doi ? (it.doi.startsWith('http') ? it.doi : 'https://doi.org/' + it.doi) : '';
  const doi = doiUrl ? ` · <a class="doi" href="${esc(doiUrl)}" target="_blank" rel="noopener">DOI ↗</a>` : '';
  const done = isComplete(c);

  document.getElementById('card').className = 'card' + (store.showLevels ? '' : ' hide-levels');
  document.getElementById('card').innerHTML = `
    <div class="pid">Trabajo ${idx + 1} de ${ITEMS.length} · bloque ${it.bloque} · id ${esc(it.paper_id)} ${done ? '· <span class="done-flag">✓ codificado</span>' : ''}</div>
    <div class="ptitle">${esc(it.title)}${lang}</div>
    <div class="pmeta">${esc(it.authors) || '(sin autores)'} · ${esc(it.year) || '—'} · ${esc(it.doc_type) || '—'} · ${esc(it.source) || '—'}${doi}</div>
    ${it.keywords ? `<div class="kw"><b>Palabras clave:</b> ${esc(it.keywords)}</div>` : ''}
    <div class="abstract">${esc(it.abstract) || '(sin resumen)'}</div>
    ${seen ? '<div class="seen-note">Ya viste la respuesta del LLM para este trabajo. Si cambias tu código, la exportación lo marcará como «editado tras ver al LLM».</div>' : ''}
    <div class="step"><div class="step-h">Paso 0 · Inclusión: ¿pertenece al corpus?</div>${p0}</div>
    <div class="step ${off1 ? 'off' : ''}"><div class="step-h">Paso 1 · Gate</div>${p1}</div>
    <div class="step ${off2 ? 'off' : ''}"><div class="step-h">Paso 2 · Criterios (0 / 0.5 / 1)</div>${p2}</div>
    <div class="step ${off2 ? 'off' : ''}"><div class="step-h">Paso 3 · Integración</div>${p3}</div>
    <div class="score">${score}</div>
    <div class="extra">Tu confianza (opcional): ${seg('conf', CONF, c.conf, false, 'conf')}</div>
    <textarea class="nota" id="nota" placeholder="Nota opcional: por qué dudaste, qué evidencia viste…">${esc(c.nota || '')}</textarea>
  `;
  document.getElementById('nota').addEventListener('input', ev => {
    const cc = Object.assign({}, code(curId())); cc.nota = ev.target.value; store.codes[curId()] = cc; save(); savedInfo();
  });
  document.getElementById('prev').disabled = (idx === 0);
  document.getElementById('next').disabled = (idx === ITEMS.length - 1);
  document.getElementById('counter').textContent = `${idx + 1} / ${ITEMS.length}`;
  const nDone = ITEMS.filter(x => isComplete(code(x.paper_id))).length;
  const nBlocks = DATA.meta.bloques;
  let full = 0;
  for (let b = 1; b <= nBlocks; b++) if (ITEMS.filter(x => x.bloque === b).every(x => isComplete(code(x.paper_id)))) full++;
  document.getElementById('topstatus').innerHTML = `Codificados: <b>${nDone}</b> de ${ITEMS.length} · bloques completos: <b>${full}</b> de ${nBlocks}`;
  document.getElementById('pbar').style.width = (100 * nDone / ITEMS.length) + '%';
  savedInfo();
}
function savedInfo() {
  document.getElementById('savedinfo').textContent = saveOk
    ? 'Tu avance se guarda automáticamente en este navegador.'
    : 'Este navegador no permite guardar el avance: descarga un respaldo antes de cerrar la página.';
}

function setVal(key, val) {
  const pid = curId(), c = Object.assign({}, code(pid));
  // los pasos bloqueados no se pueden marcar
  const e = elegible(c);
  if (key === 'gate' && e !== 1) return;
  if ((K6.includes(key) || key === 'integracion') && (e !== 1 || c.gate !== 1)) return;
  c[key] = (c[key] === val) ? null : val;     // volver a pulsar deselecciona
  c.t = new Date().toISOString();
  if (store.seen[pid] && key !== 'conf') c.tras_ver = true;
  store.codes[pid] = c; save(); render();
}
function go(d) { idx = Math.max(0, Math.min(ITEMS.length - 1, idx + d)); save(); render(); window.scrollTo({top:0, behavior:'smooth'}); }
function goTo(i) { idx = i; save(); render(); window.scrollTo({top:0, behavior:'smooth'}); }
function nextTodo() {
  for (let s = 1; s <= ITEMS.length; s++) {
    const i = (idx + s) % ITEMS.length;
    if (!isComplete(code(ITEMS[i].paper_id))) return goTo(i);
  }
  alert('¡Codificaste toda la muestra!');
}

// ── Concordancia ──
function loadLLM() {
  return new Promise((resolve, reject) => {
    if (window.LLM_V2) return resolve(window.LLM_V2);
    const s = document.createElement('script');
    s.src = 'validacion_llm.js?v=' + DATA.meta.version;
    s.onload = () => window.LLM_V2 ? resolve(window.LLM_V2) : reject(new Error('archivo vacío'));
    s.onerror = () => reject(new Error('no se pudo cargar validacion_llm.js'));
    document.head.appendChild(s);
  });
}
function weight(i, j, k, scheme) {
  if (scheme === 'quadratic') return Math.pow((i - j) / (k - 1), 2);
  if (scheme === 'linear') return Math.abs(i - j) / (k - 1);
  return i === j ? 0 : 1;
}
function kappa(pairs, cats, scheme) {
  const k = cats.length, n = pairs.length;
  if (n < 2) return null;
  const ix = new Map(cats.map((c, i) => [c, i]));
  const O = cats.map(() => new Array(k).fill(0));
  for (const [h, l] of pairs) O[ix.get(h)][ix.get(l)] += 1;
  const r = O.map(row => row.reduce((a, b) => a + b, 0));
  const col = cats.map((_, j) => O.reduce((a, row) => a + row[j], 0));
  let num = 0, den = 0;
  for (let i = 0; i < k; i++) for (let j = 0; j < k; j++) {
    const w = weight(i, j, k, scheme);
    num += w * O[i][j] / n;
    den += w * r[i] * col[j] / (n * n);
  }
  return den === 0 ? null : 1 - num / den;
}
function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function bootCI(pairs, cats, scheme, B = 1000) {
  if (pairs.length < 10) return null;
  const rnd = mulberry32(42), vals = [];
  for (let b = 0; b < B; b++) {
    const s = [];
    for (let i = 0; i < pairs.length; i++) s.push(pairs[Math.floor(rnd() * pairs.length)]);
    const v = kappa(s, cats, scheme);
    if (v !== null && isFinite(v)) vals.push(v);
  }
  if (vals.length < B / 2) return null;
  vals.sort((a, b) => a - b);
  return [vals[Math.floor(0.025 * (vals.length - 1))], vals[Math.ceil(0.975 * (vals.length - 1))]];
}
function stats(pairs, cats, scheme, withCI = true) {
  const n = pairs.length;
  if (!n) return { n: 0 };
  const po = pairs.filter(([h, l]) => h === l).length / n;
  return { n, po, k: kappa(pairs, cats, scheme), ci: withCI ? bootCI(pairs, cats, scheme) : null };
}
function kLabel(k) {
  if (k == null) return '';
  if (k < 0) return 'pobre'; if (k <= 0.20) return 'leve'; if (k <= 0.40) return 'aceptable';
  if (k <= 0.60) return 'moderada'; if (k <= 0.80) return 'sustancial'; return 'casi perfecta';
}
function kTxt(s) {
  if (!s || s.k == null) return '—';
  const ci = s.ci ? ` <span style="color:#6b7280;font-weight:400">[${fmt(s.ci[0], 2)}; ${fmt(s.ci[1], 2)}]</span>` : '';
  return `${fmt(s.k, 2)}${ci}`;
}
function pctCls(p) { return p == null ? '' : (p >= 0.8 ? 'agree-hi' : (p < 0.6 ? 'agree-lo' : '')); }

function comparisons(L) {
  const coded = ITEMS.filter(it => isComplete(code(it.paper_id)));
  return coded.map(it => {
    const c = code(it.paper_id), l = L.by_id[it.paper_id], h = humanResult(c);
    return { it, c, l, h, he: elegible(c), le: l.elegible ? 1 : 0 };
  });
}

let LLM = null;
async function showKappa() {
  const rev = document.getElementById('reveal');
  rev.style.display = 'block';
  try { LLM = await loadLLM(); }
  catch (e) { rev.innerHTML = `<h2>Concordancia humano–LLM</h2><p>No se pudieron cargar las respuestas del LLM (${esc(e.message)}). Abre la página desde el sitio publicado o desde un servidor local.</p>`; return; }
  const C = comparisons(LLM);
  if (C.length < 2) {
    rev.innerHTML = '<h2>Concordancia humano–LLM</h2><p>Codifica al menos 2 trabajos para calcular la concordancia.</p>';
    rev.scrollIntoView({behavior:'smooth'}); return;
  }
  // Paso 0
  const sEl = stats(C.map(x => [x.he, x.le]), [0, 1], 'none');
  const sEi = stats(C.map(x => [x.c.ei, x.l.ei ? 1 : 0]), [0, 1], 'none');
  const sEc = stats(C.map(x => [x.c.ec, x.l.ec ? 1 : 0]), [0, 1], 'none');
  const t2 = [[0, 0], [0, 0]];
  C.forEach(x => { t2[1 - x.he][1 - x.le] += 1; });
  // Paso 1 y categoría (ambos elegibles)
  const B = C.filter(x => x.he === 1 && x.le === 1);
  const sGate = stats(B.map(x => [x.c.gate, x.l.gate]), [0, 1], 'none');
  const catPairs = B.map(x => [x.h.cat, x.l.categoria]);
  const sCatQ = stats(catPairs, CATS, 'quadratic');
  const sCatN = stats(catPairs, CATS, 'none', false);
  const adj = B.length ? B.filter(x => Math.abs(CATS.indexOf(x.h.cat) - CATS.indexOf(x.l.categoria)) <= 1).length / B.length : null;
  const mae = B.length ? B.reduce((a, x) => a + Math.abs(x.h.total - x.l.total), 0) / B.length : null;
  const bias = B.length ? B.reduce((a, x) => a + (x.h.total - x.l.total), 0) / B.length : null;
  // Pasos 2–3 (ambos con gate = Sí)
  const G = B.filter(x => x.c.gate === 1 && x.l.gate === 1);
  let critRows = '';
  K6.concat(['integracion']).forEach(k => {
    const pr = G.map(x => [x.c[k], x.l[k]]);
    const s = stats(pr, [0, 0.5, 1], 'linear', false);
    const near = pr.length ? pr.filter(([h, l]) => Math.abs(h - l) <= 0.5).length / pr.length : null;
    const mean = pr.length ? pr.reduce((a, [h, l]) => a + (h - l), 0) / pr.length : null;
    critRows += `<tr><td>${k === 'integracion' ? 'Integración' : k}</td><td>${s.n || 0}</td>
      <td class="${pctCls(s.po)}">${pct(s.po)}</td><td>${pct(near)}</td><td>${s.k == null ? '—' : fmt(s.k, 2)}</td>
      <td>${mean == null ? '—' : (mean > 0 ? '+' : '') + fmt(mean, 2)}</td></tr>`;
  });
  // Matriz 6 × 6 y acuerdo ponderado por estrato
  const M = CATS6.map(() => new Array(6).fill(0));
  C.forEach(x => { M[CATS6.indexOf(x.h.cat)][CATS6.indexOf(x.l.categoria)] += 1; });
  let mat = '<tr><th>Tú ↓ · LLM →</th>' + CATS6.map(c => `<th>${CAT_LABEL[c].replace(/ \(.*\)/, '')}</th>`).join('') + '<th>Total</th></tr>';
  M.forEach((row, i) => {
    mat += `<tr><td><b>${CAT_LABEL[CATS6[i]]}</b></td>` + row.map((v, j) =>
      `<td class="${i === j ? 'diag' : (v === 0 ? 'zero' : '')}">${v}</td>`).join('') + `<td>${row.reduce((a, b) => a + b, 0)}</td></tr>`;
  });
  const est = LLM.meta.estratos;
  let wsum = 0, wagree = 0, used = 0;
  est.forEach(s => {
    const xs = C.filter(x => x.l.estrato === s.key);
    if (!xs.length) return;
    used++; wsum += s.N;
    wagree += s.N * xs.filter(x => x.h.cat === x.l.categoria).length / xs.length;
  });
  const wAgree = wsum ? wagree / wsum : null;

  rev.innerHTML = `
    <h2>Concordancia humano–LLM</h2>
    <p class="sub">${C.length} trabajos codificados${store.coder ? ' por ' + esc(store.coder) : ''} · κ de Cohen con IC 95 % bootstrap (1,000 remuestreos) entre corchetes.</p>

    <h3>Resultado final (los 6 desenlaces: excluido + 5 categorías RSI)</h3>
    <div class="kpis">
      <div class="kpi"><div class="v">${pct(C.filter(x => x.h.cat === x.l.categoria).length / C.length)}</div><div class="l">acuerdo exacto en la muestra (${C.length})</div></div>
      <div class="kpi"><div class="v">${pct(wAgree)}</div><div class="l">acuerdo estimado sobre el corpus completo, ponderando cada estrato por su tamaño (${used} de ${est.length} estratos con datos)</div></div>
    </div>
    <div class="tablewrap"><table class="ktable">${mat}</table></div>

    <h3>Paso 0 · Inclusión</h3>
    <div class="tablewrap"><table class="ktable">
      <tr><th>Decisión</th><th>n</th><th>% acuerdo</th><th>κ [IC 95 %]</th></tr>
      <tr><td><b>Elegible</b> (A y B)</td><td>${sEl.n}</td><td class="${pctCls(sEl.po)}">${pct(sEl.po)}</td><td>${kTxt(sEl)} ${kLabel(sEl.k)}</td></tr>
      <tr><td>A · interseccionalidad en sentido social</td><td>${sEi.n}</td><td class="${pctCls(sEi.po)}">${pct(sEi.po)}</td><td>${kTxt(sEi)}</td></tr>
      <tr><td>B · objeto climático</td><td>${sEc.n}</td><td class="${pctCls(sEc.po)}">${pct(sEc.po)}</td><td>${kTxt(sEc)}</td></tr>
    </table></div>
    <p class="fine">Tabla 2 × 2 de elegibilidad — tú Sí y LLM Sí: <b>${t2[0][0]}</b> · tú Sí y LLM No: <b>${t2[0][1]}</b> · tú No y LLM Sí: <b>${t2[1][0]}</b> · tú No y LLM No: <b>${t2[1][1]}</b>.</p>

    <h3>Paso 1 · Gate <span style="font-weight:400;color:#6b7280">(trabajos que ambos consideran elegibles)</span></h3>
    <div class="tablewrap"><table class="ktable">
      <tr><th>Decisión</th><th>n</th><th>% acuerdo</th><th>κ [IC 95 %]</th></tr>
      <tr><td>Gate</td><td>${sGate.n || 0}</td><td class="${pctCls(sGate.po)}">${pct(sGate.po)}</td><td>${kTxt(sGate)} ${kLabel(sGate.k)}</td></tr>
    </table></div>

    <h3>Puntaje RSI <span style="font-weight:400;color:#6b7280">(trabajos que ambos consideran elegibles)</span></h3>
    <div class="kpis">
      <div class="kpi"><div class="v">${sCatQ.k == null ? '—' : fmt(sCatQ.k, 2)}</div><div class="l">κ ponderado cuadrático de la categoría (5 niveles) ${sCatQ.ci ? '[' + fmt(sCatQ.ci[0], 2) + '; ' + fmt(sCatQ.ci[1], 2) + ']' : ''} · ${kLabel(sCatQ.k)}</div></div>
      <div class="kpi"><div class="v">${sCatN.k == null ? '—' : fmt(sCatN.k, 2)}</div><div class="l">κ sin ponderar de la categoría</div></div>
      <div class="kpi"><div class="v">${pct(sCatQ.po)}</div><div class="l">misma categoría · ${pct(adj)} a ±1 categoría</div></div>
      <div class="kpi"><div class="v">${mae == null ? '—' : fmt(mae, 2)}</div><div class="l">diferencia media absoluta del total (escala 0–4) · sesgo humano − LLM: ${bias == null ? '—' : (bias > 0 ? '+' : '') + fmt(bias, 2)}</div></div>
    </div>

    <h3>Pasos 2–3 · Criterios <span style="font-weight:400;color:#6b7280">(trabajos con gate = Sí para ambos)</span></h3>
    <div class="tablewrap"><table class="ktable">
      <tr><th>Criterio</th><th>n</th><th>% exacto</th><th>% a ±0.5</th><th>κ ponderado lineal</th><th>media humano − LLM</th></tr>
      ${critRows}
    </table></div>

    <p class="fine">Escala de Landis y Koch (1977): ≤ 0.20 leve · 0.21–0.40 aceptable · 0.41–0.60 moderada · 0.61–0.80 sustancial · > 0.80 casi perfecta.
    La muestra está estratificada por la decisión del LLM (sobrerrepresenta las categorías altas y los excluidos), así que el κ mide la capacidad del instrumento de discriminar entre niveles. El «acuerdo estimado sobre el corpus completo» corrige esa sobrerrepresentación con el tamaño de cada estrato. Un sesgo positivo indica que tú puntúas más alto que el LLM.</p>

    <div class="tools">
      <button class="btn sm" onclick="showDisagreements(true)">Revisar desacuerdos trabajo a trabajo</button>
      <button class="btn sm ghost" onclick="showDisagreements(false)">Ver todos los codificados</button>
      <button class="btn sm ghost" onclick="exportComparison()">Exportar comparación humano–LLM (CSV)</button>
    </div>
    <p class="fine" style="text-align:center">La revisión muestra las respuestas, la evidencia y el razonamiento del LLM. Los trabajos que veas quedan marcados: si después cambias su código, la exportación lo indicará.</p>
    <div id="dislist"></div>
  `;
  rev.scrollIntoView({behavior:'smooth'});
}

function summary(x, who) {
  const src = who === 'h' ? x.c : x.l;
  const e = who === 'h' ? x.he : x.le, r = who === 'h' ? x.h : { cat: x.l.categoria, total: x.l.total };
  const ei = who === 'h' ? x.c.ei : (x.l.ei ? 1 : 0), ec = who === 'h' ? x.c.ec : (x.l.ec ? 1 : 0);
  const other = who === 'h' ? x.l : x.c;
  const d = (a, b) => (a !== b) ? ' class="diff"' : '';
  const oEi = who === 'h' ? (x.l.ei ? 1 : 0) : x.c.ei, oEc = who === 'h' ? (x.l.ec ? 1 : 0) : x.c.ec;
  let s = `<span${d(ei, oEi)}>A ${ei ? 'Sí' : 'No'}</span> · <span${d(ec, oEc)}>B ${ec ? 'Sí' : 'No'}</span>`;
  if (e === 1) {
    const bothE = x.he === 1 && x.le === 1;
    s += ` · <span${bothE ? d(src.gate, other.gate) : ''}>gate ${src.gate ? 'Sí' : 'No'}</span>`;
    if (src.gate === 1) {
      const bothG = bothE && x.c.gate === 1 && x.l.gate === 1;
      s += ' · ' + K6.concat(['integracion']).map(k =>
        `<span${bothG ? d(src[k], other[k]) : ''}>${k === 'integracion' ? 'int' : k} ${fmt(src[k])}</span>`).join(' ');
    }
    s += ` → <b>RSI ${fmt(r.total)}</b>`;
  }
  return s + ' ' + catPill(r.cat);
}
function showDisagreements(onlyDis) {
  const C = comparisons(LLM);
  const xs = onlyDis ? C.filter(x => x.h.cat !== x.l.categoria || x.he !== x.le ||
                                     (x.he === 1 && x.le === 1 && x.c.gate !== x.l.gate)) : C;
  const now = new Date().toISOString();
  xs.forEach(x => { if (!store.seen[x.it.paper_id]) store.seen[x.it.paper_id] = now; });
  save();
  const ev = x => {
    if (!x.l.elegible) return `<div class="ev"><b>Motivo de exclusión:</b> ${esc(x.l.motivo)}</div>`;
    const lab = { gate:'Gate', integracion:'Integración' };
    return ['gate'].concat(K6, ['integracion']).map(k => x.l.ev && x.l.ev[k]
      ? `<div class="ev"><b>${lab[k] || k}:</b> ${esc(x.l.ev[k])}</div>` : '').join('');
  };
  document.getElementById('dislist').innerHTML =
    `<h3>${onlyDis ? 'Desacuerdos' : 'Todos los codificados'} (${xs.length})</h3>` +
    (xs.length ? xs.map(x => `<div class="dis">
      <div class="t">#${x.it.pos} · ${esc(x.it.title)}</div>
      <div class="row"><span class="who">Tú</span> ${summary(x, 'h')}${x.c.tras_ver ? ' <i style="color:#9a3412">(editado tras ver al LLM)</i>' : ''}</div>
      <div class="row"><span class="who">LLM</span> ${summary(x, 'l')} <span style="color:#6b7280">· confianza ${CONF_ES[x.l.confidence] || esc(x.l.confidence || '—')}</span></div>
      ${x.c.nota ? `<div class="row"><span class="who">Nota</span> ${esc(x.c.nota)}</div>` : ''}
      <details><summary>Razonamiento y evidencia del LLM</summary>
        <div class="ev">${esc(x.l.razonamiento)}</div>${ev(x)}</details>
      <div class="row"><button class="linkbtn" onclick="goTo(${POS[x.it.paper_id]})">Ir a este trabajo ↑</button></div>
    </div>`).join('') : '<p class="sub">No hay desacuerdos en los trabajos codificados.</p>');
  document.getElementById('dislist').scrollIntoView({behavior:'smooth'});
}

// ── Exportación ──
function download(name, content, type) {
  const blob = new Blob([content], {type});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
const csvEsc = s => '"' + String(s == null ? '' : s).replace(/"/g, '""').replace(/\r?\n/g, ' ') + '"';
function humanRow(it) {
  const c = code(it.paper_id), e = elegible(c), h = humanResult(c);
  const rsi = k => (e === 1 && c.gate === 1) ? c[k] : '';
  return [store.coder, it.pos, it.bloque, it.paper_id, it.title, c.ei, c.ec, e, e === 1 ? c.gate : '',
    ...K6.map(rsi), rsi('integracion'), h ? (h.total == null ? '' : h.total) : '', h ? h.cat : '',
    c.conf || '', c.nota || '', c.tras_ver ? 1 : 0, c.t || ''];
}
const HUMAN_COLS = ['codificador','pos','bloque','paper_id','titulo','h_interseccional','h_clima','h_elegible','h_gate',
  'h_I','h_II','h_III','h_IV','h_V','h_VI','h_integracion','h_total','h_categoria','h_confianza','h_nota',
  'editado_tras_ver_llm','fecha'];
function exportCSV() {
  let out = '﻿' + HUMAN_COLS.join(',') + '\n';
  ITEMS.forEach(it => { if (isComplete(code(it.paper_id))) out += humanRow(it).map(csvEsc).join(',') + '\n'; });
  download('validacion_v2_mis_codigos.csv', out, 'text/csv;charset=utf-8');
}
function exportComparison() {
  const cols = HUMAN_COLS.concat(['llm_estrato','llm_interseccional','llm_clima','llm_elegible','llm_gate',
    'llm_I','llm_II','llm_III','llm_IV','llm_V','llm_VI','llm_integracion','llm_total','llm_categoria','llm_confianza',
    'acuerdo_elegible','acuerdo_categoria']);
  let out = '﻿' + cols.join(',') + '\n';
  comparisons(LLM).forEach(x => {
    const l = x.l, b = v => v ? 1 : 0;
    out += humanRow(x.it).concat([l.estrato, b(l.ei), b(l.ec), b(l.elegible), l.elegible ? l.gate : '',
      ...K6.map(k => l.elegible ? l[k] : ''), l.elegible ? l.integracion : '', l.elegible ? l.total : '', l.categoria,
      l.confidence, b(x.he === x.le), b(x.h.cat === l.categoria)]).map(csvEsc).join(',') + '\n';
  });
  download('validacion_v2_comparacion_humano_llm.csv', out, 'text/csv;charset=utf-8');
}
function exportJSON() {
  const payload = { herramienta:'REVISA v2 · validación humana', version: DATA.meta.version,
    generado: new Date().toISOString(), coder: store.coder, codes: store.codes, seen: store.seen };
  download('validacion_v2_respaldo.json', JSON.stringify(payload, null, 2), 'application/json');
}
function importJSON(file) {
  const rd = new FileReader();
  rd.onload = () => {
    try {
      const p = JSON.parse(rd.result);
      if (!p.codes) throw new Error('el archivo no tiene códigos');
      if (!confirm(`Importar ${Object.keys(p.codes).length} códigos${p.coder ? ' de ' + p.coder : ''}? Reemplazan los de este navegador.`)) return;
      store.codes = p.codes; store.seen = p.seen || {}; if (p.coder) store.coder = p.coder;
      document.getElementById('coder').value = store.coder || '';
      save(); render();
    } catch (e) { alert('No se pudo importar: ' + e.message); }
  };
  rd.readAsText(file);
}

// ── Arranque ──
document.getElementById('reglas').innerHTML = INS.reglas.map(r => `<li>${r}</li>`).join('');
document.getElementById('ejemplos').innerHTML = INS.ejemplos.map(r => `<li>${r}</li>`).join('');
const coderEl = document.getElementById('coder');
coderEl.value = store.coder || '';
coderEl.addEventListener('input', e => { store.coder = e.target.value.trim(); save(); });
const lvEl = document.getElementById('showLevels');
lvEl.checked = store.showLevels !== false;
lvEl.addEventListener('change', e => { store.showLevels = e.target.checked; save(); render(); });
if (!Object.keys(store.codes).length) document.getElementById('introHow').open = true;
document.getElementById('prev').onclick = () => go(-1);
document.getElementById('next').onclick = () => go(1);
document.getElementById('nextTodo').onclick = nextTodo;
document.getElementById('kappaBtn').onclick = showKappa;
document.getElementById('csvBtn').onclick = exportCSV;
document.getElementById('jsonBtn').onclick = exportJSON;
document.getElementById('importBtn').onclick = () => document.getElementById('importFile').click();
document.getElementById('importFile').onchange = e => { if (e.target.files[0]) importJSON(e.target.files[0]); e.target.value = ''; };
document.getElementById('resetBtn').onclick = () => {
  if (confirm('¿Borrar todos tus códigos guardados en este navegador? Descarga antes un respaldo si quieres conservarlos.')) {
    store.codes = {}; store.seen = {}; save();
    document.getElementById('reveal').style.display = 'none'; render();
  }
};
document.addEventListener('keydown', e => {
  if (['TEXTAREA', 'INPUT'].includes(e.target.tagName)) return;
  if (e.key === 'ArrowRight') go(1);
  if (e.key === 'ArrowLeft') go(-1);
});
render();
</script>
</body>
</html>
"""


if __name__ == '__main__':
    main()
