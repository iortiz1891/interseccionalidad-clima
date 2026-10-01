#!/usr/bin/env python3
"""
13_lista_corpus.py — v2: lista completa del corpus, con búsqueda y filtros.

Una fila por cada registro cribado de la búsqueda ampliada (elegibles y excluidos), con
la decisión de cribado del LLM y, si es elegible, el puntaje RSI, los criterios, la
evidencia, la codificación (tipo de estudio, amenaza, lugar) y el tópico. Cada fila se
despliega para ver el resumen y el razonamiento del modelo. El filtro vigente se guarda
en la URL (#...), así que una vista filtrada se puede compartir con un enlace.

Entradas: data/v2_corpus_consolidated.csv · v2_cribado.csv · v2_corpus_final.csv ·
          v2_reasoning_results.csv · v2_topic_ai_labels.json · v2_prisma_meta.json
Salida:   site/v2/corpus.html
"""
from __future__ import annotations
import json
import pandas as pd
from pathlib import Path

DATA = Path("data"); DASHBOARD = Path("site/v2")
REPO = "https://github.com/iortiz1891/interseccionalidad-clima/blob/main"

TIPO_LABEL = {
    'empirico_cualitativo': 'Empírico cualitativo', 'empirico_cuantitativo': 'Empírico cuantitativo',
    'empirico_mixto': 'Empírico mixto', 'conceptual_teorico': 'Conceptual o teórico',
    'revision': 'Revisión', 'otro': 'Otro (editorial, nota, reseña)',
}
AMENAZA_LABEL = {
    'cambio_climatico_general': 'Cambio climático (general)', 'ciclon_huracan_tormenta': 'Ciclones, huracanes y tormentas',
    'inundacion': 'Inundaciones', 'sequia': 'Sequías', 'calor_extremo': 'Calor extremo',
    'incendio_forestal': 'Incendios forestales', 'nivel_mar_costas': 'Nivel del mar y costas',
    'glaciares_criosfera': 'Glaciares y criosfera', 'desastres_multiples': 'Desastres (múltiples o sin especificar)',
    'mitigacion_transicion': 'Mitigación y transición', 'otro': 'Otra',
}
CAT_KEYS = ['sustantivo_fuerte', 'sustantivo', 'parcial', 'nominal_debil', 'mencion_sin_aplicacion']


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


def main():
    cons = pd.read_csv(DATA / 'v2_corpus_consolidated.csv')
    cr = pd.read_csv(DATA / 'v2_cribado.csv')
    fin = pd.read_csv(DATA / 'v2_corpus_final.csv')
    razon = pd.read_csv(DATA / 'v2_reasoning_results.csv').set_index('paper_id')['razonamiento']
    labels = json.loads((DATA / 'v2_topic_ai_labels.json').read_text())
    meta = json.loads((DATA / 'v2_prisma_meta.json').read_text())
    for c in ['elig_interseccional', 'elig_clima', 'elegible', 'retractado']:
        cr[c] = cr[c].map(_bool)

    cr_i, fin_i = cr.set_index('paper_id'), fin.set_index('paper_id')
    recs = []
    for _, b in cons.iterrows():
        pid = int(b['paper_id'])
        c = cr_i.loc[pid]
        if c['retractado']:
            x = 're'
        elif c['elegible']:
            x = ''
        elif not c['elig_interseccional'] and not c['elig_clima']:
            x = 'am'
        elif not c['elig_interseccional']:
            x = 'ni'
        else:
            x = 'nc'
        cited = _num(b.get('Cited by'))
        r = {"id": pid, "t": _s(b['Title']), "y": int(b['Year']) if not pd.isna(b['Year']) else None,
             "a": _s(b.get('Authors'), 300), "s": _s(b.get('Source title')), "d": _s(b.get('DOI')),
             "l": _lang(b.get('Language of Original Document')), "dt": _s(b.get('Document Type')),
             "kw": _s(b.get('Author Keywords'), 400), "ab": _s(b.get('Abstract')),
             "ci": int(cited) if cited is not None else 0,
             "e": 1 if x == '' else 0, "x": x, "m": _s(c.get('motivo_exclusion')),
             "c": _s(c.get('confidence')), "rz": _s(razon.get(pid))}
        if x == '':
            f = fin_i.loc[pid]
            tid = f.get('topic_id_clean')
            tid = int(tid) if tid is not None and not pd.isna(tid) else None
            r.update({
                "r": _num(f['bowleg_total']), "k": f['categoria_bowleg'], "g": 1 if _bool(f['gate_pass']) else 0,
                "v": [_num(f[k]) for k in ['bowleg_I', 'bowleg_II', 'bowleg_III', 'bowleg_IV', 'rsi_V', 'rsi_VI', 'integracion']],
                "te": _s(f.get('tipo_estudio')), "am": _s(f.get('amenaza')), "lu": _s(f.get('lugar_estudio')),
                "tp": tid,
                "ev": [_s(f.get(k)) for k in ['gate_evidence', 'bowleg_I_evidence', 'bowleg_II_evidence',
                                               'bowleg_III_evidence', 'bowleg_IV_evidence', 'rsi_V_evidence',
                                               'rsi_VI_evidence', 'integracion_nota']],
            })
        recs.append(r)

    # Opciones de los filtros, con su conteo sobre el total
    el = [r for r in recs if r['e']]
    topics = {str(k): v['label'] for k, v in labels.items() if str(k) != '-1'}
    opts = {
        "estado": [["eleg", f"Elegibles ({len(el):,})"],
                   ["excl", f"Excluidos, todos ({len(recs) - len(el):,})"],
                   ["ni", f"Excluidos · no interseccional ({sum(r['x'] == 'ni' for r in recs)})"],
                   ["nc", f"Excluidos · no climático ({sum(r['x'] == 'nc' for r in recs)})"],
                   ["am", f"Excluidos · ninguno de los dos ({sum(r['x'] == 'am' for r in recs)})"],
                   ["re", f"Retractado ({sum(r['x'] == 're' for r in recs)})"]],
        "cat": [[k, f"{lbl} ({sum(r.get('k') == k for r in el)})"] for k, lbl in [
            ('sustantivo_fuerte', 'Sustantiva fuerte · 3.5–4'), ('sustantivo', 'Sustantiva · 2.5–3'),
            ('parcial', 'Parcial · 1.5–2'), ('nominal_debil', 'Nominal · 0.5–1'),
            ('mencion_sin_aplicacion', 'Mención sin aplicación · 0')]],
        "tp": sorted([[k, f"{v} ({sum(r.get('tp') == int(k) for r in el)})"] for k, v in topics.items()],
                     key=lambda o: o[1]) + [["-1", f"Sin tópico asignado ({sum(r.get('tp') == -1 for r in el)})"]],
        "te": [[k, f"{v} ({sum(r.get('te') == k for r in el)})"] for k, v in TIPO_LABEL.items()],
        "am": [[k, f"{v} ({sum(k in (r.get('am') or '').split('; ') for r in el)})"] for k, v in AMENAZA_LABEL.items()],
        "l": [[k, f"{k} ({sum(r['l'] == k for r in recs)})"] for k in ['EN', 'ES', 'PT'] if any(r['l'] == k for r in recs)],
    }
    years = [r['y'] for r in recs if r['y']]
    info = {"n": len(recs), "eleg": len(el), "excl": len(recs) - len(el),
            "ymin": min(years), "ymax": max(years),
            "fecha": meta.get('fecha_busqueda', '30-09-2026'),
            "topics": topics, "tipo": TIPO_LABEL, "amenaza": AMENAZA_LABEL, "opts": opts, "repo": REPO}

    payload = json.dumps(recs, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = (HTML_TEMPLATE
            .replace('__CORPUS_JSON__', payload)
            .replace('__INFO_JSON__', json.dumps(info, ensure_ascii=False).replace('</', '<\\/'))
            .replace('__N__', f"{len(recs):,}")
            .replace('__ELEG__', f"{len(el):,}")
            .replace('__EXCL__', f"{len(recs) - len(el):,}"))
    (DASHBOARD / 'corpus.html').write_text(html)
    print(f"→ {DASHBOARD / 'corpus.html'}: {len(recs)} registros ({len(el)} elegibles) · {len(html) / 1e6:.1f} MB")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lista del corpus · REVISA v2</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root { --accent:#1a73e8; --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --bg:#f3f4f6; }
  * { box-sizing:border-box; }
  body { font-family:'Inter',system-ui,sans-serif; margin:0; background:var(--bg); color:var(--ink); line-height:1.5; }
  .top { position:sticky; top:0; z-index:50; background:#0f172a; color:#fff; padding:12px 16px; box-shadow:0 2px 8px rgba(0,0,0,.15); }
  .top .inner { max-width:1200px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .top h1 { font-size:15.5px; margin:0; font-weight:700; }
  .top h1 span { font-size:11px; font-weight:700; background:#1d4ed8; padding:2px 7px; border-radius:6px; margin-left:6px; vertical-align:2px; }
  .toplinks { display:flex; gap:14px; flex-wrap:wrap; }
  .top a { color:#93c5fd; font-size:12.5px; text-decoration:none; }
  .top a:hover { text-decoration:underline; }
  .wrap { max-width:1200px; margin:0 auto; padding:0 16px 60px; }
  .lead { font-size:13.5px; color:#374151; margin:16px 2px 6px; max-width:900px; }
  .warn { font-size:12.5px; color:#7c2d12; background:#fff7ed; border:1px solid #fed7aa; border-radius:8px; padding:8px 12px; margin:8px 0 12px; max-width:900px; }
  .warn a { color:#9a3412; }
  .chips { display:flex; gap:8px; flex-wrap:wrap; margin:6px 0 12px; }
  .chip { background:#fff; border:1px solid var(--line); border-radius:999px; padding:4px 12px; font-size:12.5px; cursor:pointer; font-family:inherit; color:var(--ink); }
  .chip b { font-variant-numeric:tabular-nums; }
  .chip.on { background:#1d4ed8; border-color:#1d4ed8; color:#fff; }
  .filters { background:#fff; border:1px solid var(--line); border-radius:12px; padding:12px 14px; display:grid;
    grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:10px 14px; }
  .filters label { display:flex; flex-direction:column; gap:3px; font-size:11px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }
  .filters input, .filters select { font-family:inherit; font-size:13px; padding:6px 8px; border:1px solid #cbd5e1; border-radius:7px; background:#fff; color:var(--ink); text-transform:none; letter-spacing:0; font-weight:400; width:100%; }
  .filters .q { grid-column:1 / -1; }
  .filters .years { display:flex; gap:6px; }
  .bar { display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin:12px 2px 8px; font-size:13px; color:var(--muted); }
  .bar b { color:var(--ink); font-variant-numeric:tabular-nums; }
  .bar .right { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  .bar select { font-family:inherit; font-size:12.5px; padding:5px 8px; border:1px solid #cbd5e1; border-radius:7px; }
  .btn { background:var(--accent); color:#fff; border:none; padding:7px 13px; border-radius:7px; font-size:12.5px; font-weight:600; cursor:pointer; font-family:inherit; }
  .btn:hover { background:#1557b0; }
  .btn.ghost { background:#fff; color:var(--ink); border:1px solid #cbd5e1; }
  .btn.ghost:hover { background:#f8fafc; }
  .btn:disabled { opacity:.45; cursor:not-allowed; }
  .tablecard { background:#fff; border:1px solid var(--line); border-radius:12px; overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:13px; }
  th { text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.5px; color:var(--muted); font-weight:700;
    padding:9px 10px; border-bottom:1px solid var(--line); background:#f8fafc; white-space:nowrap; }
  td { padding:9px 10px; border-bottom:1px solid #f1f5f9; vertical-align:top; }
  tr.row { cursor:pointer; }
  tr.row:hover td { background:#f8fafc; }
  tr.row.open td { background:#eff6ff; }
  .id { color:#9ca3af; font-size:11px; font-variant-numeric:tabular-nums; }
  .tt { font-weight:600; line-height:1.35; }
  .meta { font-size:11.5px; color:var(--muted); margin-top:2px; }
  .pill { display:inline-block; padding:1px 8px; border-radius:7px; font-size:11px; font-weight:700; white-space:nowrap; }
  .lang { display:inline-block; padding:0 6px; border-radius:6px; font-size:10px; font-weight:700; margin-left:4px; background:#f1f5f9; color:#475569; }
  .lang.ES { background:#ffebee; color:#b71c1c; }
  .st-e { background:#dcfce7; color:#166534; } .st-x { background:#f3f4f6; color:#4b5563; }
  .rsi { font-size:16px; font-weight:800; font-variant-numeric:tabular-nums; }
  .glyphs { display:flex; gap:3px; align-items:center; white-space:nowrap; }
  .gl { width:15px; height:15px; border-radius:3px; border:1.5px solid #1d4ed8; display:inline-block; position:relative; }
  .gl.v1 { background:#1d4ed8; }
  .gl.v05 { background:linear-gradient(90deg, #1d4ed8 50%, transparent 50%); }
  .gl.gate { border-color:#6b7280; }
  .gl.gate.v1 { background:#6b7280; }
  .gllab { font-size:9.5px; color:#9ca3af; display:flex; gap:3px; margin-top:2px; }
  .gllab span { width:15px; text-align:center; }
  .gfail { font-size:11.5px; color:#991b1b; }
  .topic { font-size:12px; color:#374151; max-width:200px; }
  tr.detail td { background:#fbfdff; padding:4px 14px 16px; border-bottom:1px solid var(--line); }
  .dgrid { display:grid; grid-template-columns:minmax(0, 3fr) minmax(0, 2fr); gap:16px; }
  .dbox h4 { font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:var(--muted); margin:10px 0 4px; }
  .abs { font-size:12.5px; color:#374151; white-space:pre-wrap; max-height:280px; overflow-y:auto; background:#fff; border:1px solid var(--line); border-radius:8px; padding:10px 12px; }
  .rz { font-size:12.5px; background:#f8fafc; border-left:3px solid #1d4ed8; padding:8px 11px; border-radius:0 8px 8px 0; }
  .evt { border-collapse:collapse; width:100%; font-size:12px; }
  .evt td { border-bottom:1px solid #f1f5f9; padding:4px 6px; vertical-align:top; }
  .evt td:first-child { font-weight:700; white-space:nowrap; color:#374151; }
  .evt td:nth-child(2) { font-variant-numeric:tabular-nums; white-space:nowrap; }
  .kv { font-size:12.5px; margin:3px 0; } .kv b { color:#374151; }
  .pager { display:flex; justify-content:center; gap:6px; margin:14px 0; flex-wrap:wrap; align-items:center; font-size:13px; color:var(--muted); }
  .pager button { min-width:34px; }
  .pager button.cur { background:#1d4ed8; color:#fff; border-color:#1d4ed8; }
  .empty { padding:30px; text-align:center; color:var(--muted); }
  .foot { font-size:12px; color:var(--muted); margin-top:16px; }
  .foot a { color:var(--accent); }
  @media (max-width:820px) { .c-crit, .c-topic { display:none; } .dgrid { grid-template-columns:1fr; } }
</style>
</head>
<body>
<div class="top">
  <div class="inner">
    <h1>Lista completa del corpus<span>v2</span></h1>
    <div class="toplinks">
      <a href="validacion.html">✓ Validación humana</a>
      <a href="index.html">← Volver al dashboard</a>
    </div>
  </div>
</div>
<div class="wrap">
  <p class="lead">Los <b>__N__ registros cribados</b> de la búsqueda ampliada en Scopus: <b>__ELEG__ elegibles</b> y <b>__EXCL__ excluidos</b>. Cada fila trae la decisión de cribado del LLM y, si el trabajo es elegible, su puntaje RSI, los criterios y el tópico. Haz clic en una fila para ver el resumen, el razonamiento del modelo y la evidencia de cada criterio.</p>
  <div class="warn"><b>Antes de la validación humana:</b> esta lista muestra las respuestas del LLM. Si vas a codificar la <a href="validacion.html">muestra de validación</a>, hazlo antes de revisarla, para que la codificación sea a ciegas.</div>

  <div class="chips" id="chips"></div>
  <div class="filters" id="filters">
    <label class="q">Buscar en título, autores, palabras clave, fuente y resumen
      <input type="search" id="f-q" placeholder="p. ej. Mexico, hurricane, indigenous women, Bangladesh…"></label>
    <label>Estado <select id="f-estado"><option value="">Todos</option></select></label>
    <label>Categoría RSI <select id="f-cat"><option value="">Todas</option></select></label>
    <label>Tópico <select id="f-tp"><option value="">Todos</option></select></label>
    <label>Tipo de estudio <select id="f-te"><option value="">Todos</option></select></label>
    <label>Amenaza <select id="f-am"><option value="">Todas</option></select></label>
    <label>Idioma <select id="f-l"><option value="">Todos</option></select></label>
    <label>Años <span class="years"><input type="number" id="f-y1" aria-label="desde"><input type="number" id="f-y2" aria-label="hasta"></span></label>
  </div>

  <div class="bar">
    <div id="count"></div>
    <div class="right">
      <select id="f-sort" aria-label="Ordenar">
        <option value="y_desc">Año: recientes primero</option>
        <option value="y_asc">Año: antiguos primero</option>
        <option value="r_desc">RSI: mayor primero</option>
        <option value="r_asc">RSI: menor primero</option>
        <option value="ci_desc">Más citados primero</option>
        <option value="t_asc">Título A–Z</option>
      </select>
      <button class="btn ghost" id="clear">Limpiar filtros</button>
      <button class="btn" id="csv">Descargar CSV (filtro actual)</button>
    </div>
  </div>

  <div class="tablecard">
    <table>
      <thead><tr><th>#</th><th>Trabajo</th><th>Estado</th><th>RSI</th><th class="c-crit">Gate · criterios</th><th class="c-topic">Tópico</th></tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
  <div class="pager" id="pager"></div>
  <p class="foot" id="foot"></p>
</div>

<script>
const CORPUS = __CORPUS_JSON__;
const INFO = __INFO_JSON__;
const PER = 50;
const CAT_LABEL = { sustantivo_fuerte:'Sustantiva fuerte', sustantivo:'Sustantiva', parcial:'Parcial',
  nominal_debil:'Nominal', mencion_sin_aplicacion:'Mención' };
const CAT_COLOR = { mencion_sin_aplicacion:['#8d6e63','#fff'], nominal_debil:['#ef5350','#fff'],
  parcial:['#ffa726','#1f2937'], sustantivo:['#66bb6a','#1f2937'], sustantivo_fuerte:['#1b5e20','#fff'] };
const EXCL_LABEL = { ni:'no interseccional', nc:'no climático', am:'ni interseccional ni climático', re:'retractado' };
const CRIT = ['I','II','III','IV','V','VI','Int'];
const EV_LABEL = ['Gate','I · Identidades entrelazadas','II · Poder estructural','III · Contexto situado',
  'IV · Método no aditivo','V · Praxis y justicia','VI · Agencia y resistencia','Integración'];
const CONF = { high:'alta', medium:'media', low:'baja' };

const esc = s => String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const norm = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const fmt = v => (v == null) ? '—' : Number(v).toLocaleString('en-US', {minimumFractionDigits:1, maximumFractionDigits:1});
CORPUS.forEach(r => { r._h = norm([r.t, r.a, r.kw, r.s, r.ab].join(' · ')); });

const F = { q:'', estado:'', cat:'', tp:'', te:'', am:'', l:'', y1:'', y2:'', sort:'y_desc', p:1 };
const DEFAULTS = Object.assign({}, F);
const open = new Set();

function fillSelect(id, opts) {
  const el = document.getElementById(id);
  opts.forEach(([v, l]) => { const o = document.createElement('option'); o.value = v; o.textContent = l; el.appendChild(o); });
}
fillSelect('f-estado', INFO.opts.estado);
fillSelect('f-cat', INFO.opts.cat);
fillSelect('f-tp', INFO.opts.tp);
fillSelect('f-te', INFO.opts.te);
fillSelect('f-am', INFO.opts.am);
fillSelect('f-l', INFO.opts.l);
document.getElementById('f-y1').placeholder = INFO.ymin;
document.getElementById('f-y2').placeholder = INFO.ymax;

// Atajos: los cinco niveles de la RSI y los excluidos
const CHIPS = [['', '', `Todos <b>${INFO.n.toLocaleString('en-US')}</b>`], ['estado', 'eleg', `Elegibles <b>${INFO.eleg.toLocaleString('en-US')}</b>`],
  ['estado', 'excl', `Excluidos <b>${INFO.excl.toLocaleString('en-US')}</b>`]].concat(
  INFO.opts.cat.map(([k, l]) => ['cat', k, l.replace(/ · [^(]*/, ' ').replace(/\((\d+)\)/, '<b>$1</b>')]));
function renderChips() {
  document.getElementById('chips').innerHTML = CHIPS.map(([f, v, l], i) => {
    const on = f === '' ? (!F.estado && !F.cat) : (F[f] === v && (f === 'cat' ? true : !F.cat));
    return `<button class="chip ${on ? 'on' : ''}" onclick="chip(${i})">${l}</button>`;
  }).join('');
}
function chip(i) {
  const [f, v] = CHIPS[i];
  F.estado = ''; F.cat = '';
  if (f) F[f] = v;
  F.p = 1; syncInputs(); update();
}

function matches(r) {
  if (F.q) { const words = norm(F.q).split(/\s+/).filter(Boolean); if (!words.every(w => r._h.includes(w))) return false; }
  if (F.estado === 'eleg' && !r.e) return false;
  if (F.estado === 'excl' && r.e) return false;
  if (['ni','nc','am','re'].includes(F.estado) && r.x !== F.estado) return false;
  if (F.cat && r.k !== F.cat) return false;
  if (F.tp !== '' && String(r.tp) !== F.tp) return false;
  if (F.te && r.te !== F.te) return false;
  if (F.am && !(r.am || '').split('; ').includes(F.am)) return false;
  if (F.l && r.l !== F.l) return false;
  if (F.y1 && (!r.y || r.y < +F.y1)) return false;
  if (F.y2 && (!r.y || r.y > +F.y2)) return false;
  return true;
}
function sorted(rows) {
  const s = F.sort, rv = r => r.r == null ? -1 : r.r;
  const cmp = {
    y_desc: (a, b) => (b.y || 0) - (a.y || 0) || a.t.localeCompare(b.t),
    y_asc: (a, b) => (a.y || 0) - (b.y || 0) || a.t.localeCompare(b.t),
    r_desc: (a, b) => rv(b) - rv(a) || (b.y || 0) - (a.y || 0),
    r_asc: (a, b) => rv(a) - rv(b) || (b.y || 0) - (a.y || 0),
    ci_desc: (a, b) => (b.ci || 0) - (a.ci || 0),
    t_asc: (a, b) => a.t.localeCompare(b.t, 'es'),
  }[s] || ((a, b) => 0);
  return rows.slice().sort(cmp);
}
let current = [];

function authorsShort(a) {
  const xs = String(a || '').split(';').map(s => s.trim()).filter(Boolean);
  return xs.length > 3 ? xs.slice(0, 3).join('; ') + ' et al.' : xs.join('; ');
}
function glyphs(r) {
  if (!r.e) return '<span class="meta">—</span>';
  if (!r.g) return '<span class="gfail">gate ✗ · RSI 0</span>';
  const g = (v, extra='') => `<span class="gl ${extra} ${v === 1 ? 'v1' : (v === 0.5 ? 'v05' : '')}"></span>`;
  return `<div class="glyphs" title="Gate ✓ · ${CRIT.map((c, i) => c + ' = ' + fmt(r.v[i])).join(' · ')}">${g(1, 'gate')}${r.v.map(v => g(v)).join('')}</div>
    <div class="gllab"><span>G</span>${CRIT.map(c => `<span>${c === 'Int' ? 'In' : c}</span>`).join('')}</div>`;
}
function estado(r) {
  return r.e ? '<span class="pill st-e">Elegible</span>' : `<span class="pill st-x">Excluido</span><div class="meta">${EXCL_LABEL[r.x] || ''}</div>`;
}
function rsiCell(r) {
  if (!r.e) return '<span class="meta">—</span>';
  const [bg, fg] = CAT_COLOR[r.k] || ['#eee', '#333'];
  return `<div class="rsi">${fmt(r.r)}</div><span class="pill" style="background:${bg};color:${fg}">${CAT_LABEL[r.k] || ''}</span>`;
}
function detail(r) {
  const doi = r.d ? `<a href="https://doi.org/${esc(r.d)}" target="_blank" rel="noopener">${esc(r.d)} ↗</a>` : '—';
  let right = `<h4>Razonamiento del LLM</h4><div class="rz">${esc(r.rz) || '—'}</div>`;
  if (!r.e) right += `<h4>Motivo de exclusión</h4><div class="kv">${esc(r.m) || '—'}</div>`;
  else {
    const vals = [r.g ? 'Sí' : 'No'].concat(r.v.map(v => fmt(v)));
    right += `<h4>Evidencia por criterio · RSI ${fmt(r.r)}</h4><table class="evt">` +
      EV_LABEL.map((l, i) => `<tr><td>${l}</td><td>${vals[i]}</td><td>${esc(r.ev[i]) || '<span class="meta">—</span>'}</td></tr>`).join('') + '</table>';
    right += `<h4>Codificación</h4>
      <div class="kv"><b>Tipo de estudio:</b> ${esc(INFO.tipo[r.te] || r.te || '—')}</div>
      <div class="kv"><b>Amenaza:</b> ${esc((r.am || '').split('; ').filter(Boolean).map(a => INFO.amenaza[a] || a).join(' · ') || '—')}</div>
      <div class="kv"><b>Lugar:</b> ${esc(r.lu || '—')}</div>
      <div class="kv"><b>Tópico:</b> ${esc(r.tp == null ? '—' : (r.tp === -1 ? 'Sin tópico asignado' : INFO.topics[r.tp] || r.tp))}</div>`;
  }
  right += `<div class="kv" style="margin-top:8px"><b>Confianza del LLM:</b> ${CONF[r.c] || r.c || '—'}</div>`;
  return `<div class="dgrid">
    <div class="dbox"><h4>Resumen</h4><div class="abs">${esc(r.ab) || '—'}</div>
      ${r.kw ? `<h4>Palabras clave</h4><div class="kv">${esc(r.kw)}</div>` : ''}
      <h4>Referencia</h4><div class="kv">${esc(String(r.a || '').replace(/\.$/, ''))}. ${r.y || ''}. ${esc(r.s)} · ${esc(r.dt)} · citas en Scopus: ${r.ci}</div>
      <div class="kv"><b>DOI:</b> ${doi}</div></div>
    <div class="dbox">${right}</div></div>`;
}

function update(pushHash = true) {
  current = sorted(CORPUS.filter(matches));
  const pages = Math.max(1, Math.ceil(current.length / PER));
  F.p = Math.min(Math.max(1, F.p), pages);
  const a = (F.p - 1) * PER, rows = current.slice(a, a + PER);
  document.getElementById('count').innerHTML = current.length
    ? `Mostrando <b>${(a + 1).toLocaleString('en-US')}–${(a + rows.length).toLocaleString('en-US')}</b> de <b>${current.length.toLocaleString('en-US')}</b> registros`
    : 'Ningún registro coincide con el filtro.';
  document.getElementById('tbody').innerHTML = rows.length ? rows.map(r => {
    const isOpen = open.has(r.id);
    const tp = r.tp == null ? '' : (r.tp === -1 ? '<span class="meta">sin tópico</span>' : esc(INFO.topics[r.tp] || ''));
    return `<tr class="row ${isOpen ? 'open' : ''}" onclick="toggle(${r.id})">
      <td class="id">${r.id}</td>
      <td><div class="tt">${esc(r.t)}${r.l && r.l !== 'EN' ? `<span class="lang ${r.l}">${r.l}</span>` : ''}</div>
        <div class="meta">${esc(authorsShort(r.a))} · ${r.y || '—'} · ${esc(r.s)} · ${esc(r.dt)}</div></td>
      <td>${estado(r)}</td><td>${rsiCell(r)}</td><td class="c-crit">${glyphs(r)}</td><td class="c-topic topic">${tp}</td></tr>` +
      (isOpen ? `<tr class="detail"><td colspan="6">${detail(r)}</td></tr>` : '');
  }).join('') : '<tr><td colspan="6" class="empty">Sin resultados. Prueba con menos filtros.</td></tr>';
  // Paginación compacta
  const btn = (p, l, cur=false, dis=false) => `<button class="btn ghost ${cur ? 'cur' : ''}" ${dis ? 'disabled' : ''} onclick="page(${p})">${l}</button>`;
  let pg = btn(F.p - 1, '←', false, F.p === 1);
  const set = new Set([1, pages, F.p - 1, F.p, F.p + 1].filter(p => p >= 1 && p <= pages));
  let last = 0;
  [...set].sort((x, y) => x - y).forEach(p => { if (p - last > 1) pg += '<span>…</span>'; pg += btn(p, p, p === F.p); last = p; });
  pg += btn(F.p + 1, '→', false, F.p === pages);
  document.getElementById('pager').innerHTML = pages > 1 ? pg : '';
  renderChips();
  if (pushHash) writeHash();
}
function toggle(id) { open.has(id) ? open.delete(id) : open.add(id); update(false); }
function page(p) { F.p = p; update(); document.querySelector('.tablecard').scrollIntoView({behavior:'smooth'}); }

// Filtros ↔ URL
const IDS = ['q','estado','cat','tp','te','am','l','y1','y2','sort'];
function syncInputs() { IDS.forEach(k => { document.getElementById('f-' + k).value = F[k]; }); }
function writeHash() {
  const p = new URLSearchParams();
  Object.keys(F).forEach(k => { if (String(F[k]) !== String(DEFAULTS[k])) p.set(k, F[k]); });
  const h = p.toString();
  history.replaceState(null, '', h ? '#' + h : location.pathname + location.search);
}
function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  Object.assign(F, DEFAULTS);
  Object.keys(F).forEach(k => { if (p.has(k)) F[k] = k === 'p' ? (+p.get(k) || 1) : p.get(k); });
}
let timer = null;
IDS.forEach(k => {
  const el = document.getElementById('f-' + k);
  el.addEventListener(k === 'q' ? 'input' : 'change', () => {
    F[k] = el.value.trim(); F.p = 1;
    if (k === 'q') { clearTimeout(timer); timer = setTimeout(update, 160); } else update();
  });
});
document.getElementById('clear').onclick = () => { Object.assign(F, DEFAULTS); open.clear(); syncInputs(); update(); };
window.addEventListener('hashchange', () => { readHash(); syncInputs(); update(false); });

// CSV del filtro vigente
document.getElementById('csv').onclick = () => {
  const cols = ['paper_id','titulo','anio','autores','fuente','doi','idioma','tipo_documento','citas_scopus','elegible','motivo_exclusion',
    'confianza_llm','rsi_total','categoria','gate','I','II','III','IV','V','VI','integracion','tipo_estudio','amenaza','lugar','topico','razonamiento_llm'];
  const q = s => '"' + String(s == null ? '' : s).replace(/"/g, '""').replace(/\r?\n/g, ' ') + '"';
  let out = '﻿' + cols.join(',') + '\n';
  current.forEach(r => {
    const v = r.v || [];
    out += [r.id, r.t, r.y, r.a, r.s, r.d, r.l, r.dt, r.ci, r.e, r.m, r.c, r.e ? r.r : '', r.e ? r.k : '', r.e ? r.g : '',
      ...(r.e ? v : ['', '', '', '', '', '', '']), r.te || '', r.am || '', r.lu || '',
      r.tp == null ? '' : (r.tp === -1 ? 'sin tópico' : INFO.topics[r.tp] || ''), r.rz].map(q).join(',') + '\n';
  });
  const blob = new Blob([out], {type:'text/csv;charset=utf-8'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'corpus_v2_filtrado.csv';
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
};

document.getElementById('foot').innerHTML = `Búsqueda en Scopus del ${esc(INFO.fecha)}. Cribado y RSI: Claude (claude-opus-5-5) con el prompt <a href="${INFO.repo}/prompts/v2_cribado_rsi.md" target="_blank" rel="noopener">v2_cribado_rsi.md</a>. ` +
  `Datos completos en <a href="${INFO.repo}/data/v2_cribado.csv" target="_blank" rel="noopener">data/v2_cribado.csv</a> (cribado) y <a href="${INFO.repo}/data/v2_corpus_final.csv" target="_blank" rel="noopener">data/v2_corpus_final.csv</a> (RSI y tópicos).`;
readHash(); syncInputs(); update(false);
</script>
</body>
</html>
"""


if __name__ == '__main__':
    main()
