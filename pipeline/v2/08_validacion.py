#!/usr/bin/env python3
"""
08_validacion.py — v2: herramienta de validación humana de la RSI.
Copia adaptada de pipeline/11_validacion.py con los datos de la v2.

Genera una interfaz HTML amigable para que Daniel codifique a ciegas una
submuestra del corpus (gate + criterios I–VI + integración) sin ver el puntaje
del LLM. Al terminar, calcula la concordancia humano–LLM (κ de Cohen) y permite
exportar los códigos en CSV/JSON. Persistencia en localStorage (pausa/reanuda).

Outputs:
  data/v2_validation_sample.json     muestra estratificada (~50 papers) + scores LLM ocultos
  site/validacion.html       interfaz de codificación (tab independiente)
"""
from __future__ import annotations
import json
import math
import pandas as pd
from pathlib import Path

DATA = Path("data"); DASHBOARD = Path("site/v2")

N_PER_CAT = 10           # papers por categoría (estratificado)
SEED = 42

CAT_ORDER = ['mencion_sin_aplicacion', 'nominal_debil', 'parcial', 'sustantivo', 'sustantivo_fuerte']

# Criterios con su pregunta diagnóstica (alineados al prompt RSI v3)
CRITERIA = [
    {"key": "gate", "label": "Criterio de entrada (gate)",
     "q": "¿El trabajo articula dos o más ejes de diferenciación social como relacionados entre sí —no solo mencionados por separado?",
     "opts": [["No", 0], ["Sí", 1]]},
    {"key": "I", "label": "I · Identidades entrelazadas",
     "q": "¿Trata ≥2 ejes como mutuamente constitutivos, no como suma aditiva?",
     "opts": [["No", 0], ["Parcial", 0.5], ["Sí", 1]]},
    {"key": "II", "label": "II · Poder estructural",
     "q": "¿Articula estructuras (racismo, patriarcado, colonialismo) y no rasgos individuales?",
     "opts": [["No", 0], ["Parcial", 0.5], ["Sí", 1]]},
    {"key": "III", "label": "III · Contexto situado",
     "q": "¿Sitúa los hallazgos en una historia/geografía/política específicas?",
     "opts": [["No", 0], ["Parcial", 0.5], ["Sí", 1]]},
    {"key": "IV", "label": "IV · Método no aditivo",
     "q": "¿Traduce la interseccionalidad en el diseño metodológico (muestreo, codificación, interacciones)?",
     "opts": [["No", 0], ["Parcial", 0.5], ["Sí", 1]]},
    {"key": "V", "label": "V · Praxis y justicia",
     "q": "¿Conecta el análisis con praxis, justicia o transformación social?",
     "opts": [["No", 0], ["Parcial", 0.5], ["Sí", 1]]},
    {"key": "VI", "label": "VI · Agencia y resistencia",
     "q": "¿Reconoce agencia, resistencia o estrategias de los propios sujetos?",
     "opts": [["No", 0], ["Parcial", 0.5], ["Sí", 1]]},
    {"key": "integracion", "label": "Factor de integración",
     "q": "¿Los ejes se analizan de forma articulada a lo largo del trabajo (no en secciones separadas)?",
     "opts": [["No", 0], ["Parcial", 0.5], ["Sí", 1]]},
]


def _s(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ''
    return str(x).strip()


def main():
    print("[1] Cargando corpus + resultados RSI v3")
    f = pd.read_csv(DATA / 'v2_corpus_final.csv')
    res = pd.read_csv(DATA / 'v2_bowleg_results.csv')
    cols = ['paper_id', 'bowleg_I', 'bowleg_II', 'bowleg_III', 'bowleg_IV',
            'rsi_V', 'rsi_VI', 'gate_pass', 'integracion', 'bowleg_total']
    cols = [c for c in cols if c in res.columns]
    dup = [c for c in cols if c != 'paper_id' and c in f.columns]
    f = f.drop(columns=dup).merge(res[cols], on='paper_id', how='left')

    print("[2] Muestra estratificada por categoría")
    parts = []
    for cat in CAT_ORDER:
        sub = f[f['categoria_bowleg'] == cat]
        n = min(N_PER_CAT, len(sub))
        if n > 0:
            parts.append(sub.sample(n=n, random_state=SEED))
    sample = pd.concat(parts)
    # mezclar para que las categorías queden intercaladas (mismo seed → reproducible)
    sample = sample.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    print(f"    muestra: {len(sample)} papers ({N_PER_CAT}/categoría, seed={SEED})")

    def lang(x):
        x = _s(x).lower()
        if 'span' in x: return 'ES'
        if 'port' in x: return 'PT'
        if 'eng' in x: return 'EN'
        return ''

    items = []
    for _, r in sample.iterrows():
        def num(c):
            v = r.get(c)
            return None if (v is None or (isinstance(v, float) and pd.isna(v))) else float(v)
        gate = r.get('gate_pass')
        gate_v = 1 if (str(gate).strip().lower() in ('true', '1', '1.0')) else 0
        items.append({
            "paper_id": _s(r.get('paper_id')),
            "title": _s(r.get('Title')),
            "authors": _s(r.get('Authors')),
            "source": _s(r.get('Source title')),
            "year": _s(r.get('Year')).replace('.0', ''),
            "lang": lang(r.get('Language of Original Document')),
            "doi": _s(r.get('DOI')),
            "abstract": _s(r.get('Abstract')),
            # puntajes LLM (ocultos en la UI hasta el "reveal" de concordancia)
            "llm": {
                "gate": gate_v, "I": num('bowleg_I'), "II": num('bowleg_II'),
                "III": num('bowleg_III'), "IV": num('bowleg_IV'),
                "V": num('rsi_V'), "VI": num('rsi_VI'),
                "integracion": num('integracion'), "total": num('bowleg_total'),
            }
        })

    out = {"meta": {"n": len(items), "n_per_cat": N_PER_CAT, "seed": SEED}, "items": items}
    (DATA / 'v2_validation_sample.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"    → data/v2_validation_sample.json")

    print(f"[3] Generando interfaz {DASHBOARD / 'validacion.html'}")
    html = HTML_TEMPLATE
    html = html.replace('__SAMPLE_JSON__', json.dumps(out, ensure_ascii=False))
    html = html.replace('__CRITERIA_JSON__', json.dumps(CRITERIA, ensure_ascii=False))
    (DASHBOARD / 'validacion.html').write_text(html)
    print(f"    → {DASHBOARD / 'validacion.html'} ({len(html):,} chars)")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Validación humana de la RSI · v2</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root { --accent:#1a73e8; --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --bg:#f3f4f6; }
  * { box-sizing:border-box; }
  body { font-family:'Inter',system-ui,sans-serif; margin:0; background:var(--bg); color:var(--ink); line-height:1.55; }
  .wrap { max-width:860px; margin:0 auto; padding:0 20px 80px; }
  .top { position:sticky; top:0; z-index:50; background:#0f172a; color:#fff; padding:14px 20px;
    box-shadow:0 2px 8px rgba(0,0,0,.15); }
  .top .inner { max-width:860px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; gap:12px; }
  .top h1 { font-size:16px; margin:0; font-weight:700; }
  .top a { color:#93c5fd; font-size:12.5px; text-decoration:none; }
  .top a:hover { text-decoration:underline; }
  .progress-wrap { background:#1e293b; height:6px; }
  .progress-bar { background:#3b82f6; height:6px; width:0%; transition:width .2s; }
  .intro { background:#fff; border:1px solid var(--line); border-radius:10px; padding:16px 20px; margin:18px 0; font-size:13px; }
  .intro summary { cursor:pointer; font-weight:600; color:var(--accent); }
  .intro ul { margin:8px 0 0; padding-left:20px; }
  .card { background:#fff; border:1px solid var(--line); border-radius:12px; padding:20px 22px; margin:16px 0;
    box-shadow:0 1px 3px rgba(0,0,0,.06); }
  .pid { font-size:11px; color:var(--muted); letter-spacing:.3px; }
  .ptitle { font-size:16px; font-weight:700; margin:4px 0 6px; line-height:1.35; }
  .pmeta { font-size:12px; color:var(--muted); margin-bottom:10px; }
  .pill { display:inline-block; padding:1px 7px; border-radius:8px; font-size:10px; font-weight:700; margin-left:6px; }
  .pill.ES { background:#ffebee; color:#d32f2f; } .pill.PT { background:#e3f2fd; color:#1976d2; }
  .pill.EN { background:#f5f5f5; color:#616161; }
  .abstract { font-size:13px; color:#374151; background:#f9fafb; border:1px solid var(--line);
    border-radius:8px; padding:12px 14px; max-height:230px; overflow-y:auto; margin-bottom:6px; white-space:pre-wrap; }
  .doi { font-size:12px; }
  .crit { border-top:1px solid var(--line); padding:13px 0 4px; }
  .crit-label { font-size:13.5px; font-weight:700; }
  .crit-q { font-size:12px; color:var(--muted); margin:2px 0 8px; }
  .seg { display:inline-flex; gap:0; border:1px solid #cbd5e1; border-radius:8px; overflow:hidden; }
  .seg button { border:none; background:#fff; padding:7px 18px; font-size:13px; cursor:pointer;
    font-family:inherit; color:#475569; border-right:1px solid #e2e8f0; transition:all .1s; }
  .seg button:last-child { border-right:none; }
  .seg button:hover { background:#f1f5f9; }
  .seg button.sel-no { background:#eef0f2; color:#374151; font-weight:700; box-shadow:inset 0 0 0 2px #9ca3af; }
  .seg button.sel-mid { background:#ffe9cc; color:#b45309; font-weight:700; box-shadow:inset 0 0 0 2px #f59e0b; }
  .seg button.sel-yes { background:#d1fae5; color:#065f46; font-weight:700; box-shadow:inset 0 0 0 2px #10b981; }
  .nota { width:100%; margin-top:6px; font-family:inherit; font-size:12.5px; padding:8px 10px;
    border:1px solid var(--line); border-radius:8px; resize:vertical; min-height:42px; }
  .gate-no-note { font-size:12px; color:#b45309; background:#fffbeb; border:1px solid #fde68a;
    border-radius:8px; padding:8px 12px; margin-top:8px; display:none; }
  .nav { display:flex; justify-content:space-between; align-items:center; margin:18px 0; gap:10px; }
  .btn { background:var(--accent); color:#fff; border:none; padding:10px 20px; border-radius:8px;
    font-size:14px; font-weight:600; cursor:pointer; font-family:inherit; }
  .btn:hover { background:#1557b0; } .btn:disabled { background:#cbd5e1; cursor:not-allowed; }
  .btn.ghost { background:#fff; color:var(--ink); border:1px solid #cbd5e1; }
  .btn.ghost:hover { background:#f8fafc; }
  .status { text-align:center; font-size:12.5px; color:var(--muted); }
  .status b { color:#059669; }
  .tools { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin-top:14px; }
  .btn.sm { padding:8px 14px; font-size:12.5px; }
  .reveal { background:#fff; border:1px solid var(--line); border-radius:12px; padding:18px 22px; margin:16px 0; display:none; }
  .reveal h2 { font-size:16px; margin:0 0 10px; }
  .kappa-big { font-size:34px; font-weight:800; color:var(--accent); }
  .ktable { border-collapse:collapse; width:100%; font-size:12.5px; margin-top:10px; }
  .ktable th, .ktable td { border:1px solid var(--line); padding:6px 9px; text-align:center; }
  .ktable th { background:#f8fafc; }
  .agree-hi { color:#059669; font-weight:700; } .agree-lo { color:#dc2626; font-weight:700; }
  .done-flag { color:#059669; font-weight:700; }
</style>
</head>
<body>
<div class="top">
  <div class="inner">
    <h1>Validación humana de la RSI · v2</h1>
    <a href="index.html">← Volver al dashboard</a>
  </div>
</div>
<div class="progress-wrap"><div class="progress-bar" id="pbar"></div></div>

<div class="wrap">
  <details class="intro">
    <summary>¿Cómo funciona? (leer una vez)</summary>
    <ul>
      <li>Vas a leer el <b>resumen</b> de cada trabajo y codificar tú mismo la rúbrica, <b>sin ver el puntaje del modelo</b> (codificación a ciegas).</li>
      <li>Primero el <b>criterio de entrada (gate)</b>; si es «No», el trabajo no aplica interseccionalidad de forma relacional y su puntaje es 0 (igual puedes anotar los demás criterios si quieres).</li>
      <li>Para cada criterio elige <b>No / Parcial / Sí</b>. Hay una pregunta guía bajo cada uno.</li>
      <li>Tu avance se guarda solo en este navegador. Puedes <b>cerrar y reanudar</b>.</li>
      <li>Al terminar, pulsa <b>«Ver concordancia con el LLM»</b> para el κ de Cohen, y <b>exporta el CSV</b> para enviarlo.</li>
    </ul>
  </details>

  <div class="status" id="topstatus"></div>

  <div class="card" id="card"><!-- render dinámico --></div>

  <div class="nav">
    <button class="btn ghost" id="prev">← Anterior</button>
    <div class="status" id="counter"></div>
    <button class="btn" id="next">Siguiente →</button>
  </div>

  <div class="status" id="savedinfo"></div>

  <div class="tools">
    <button class="btn sm" id="kappaBtn">Ver concordancia con el LLM (κ)</button>
    <button class="btn sm ghost" id="csvBtn">Exportar CSV</button>
    <button class="btn sm ghost" id="jsonBtn">Exportar JSON</button>
    <button class="btn sm ghost" id="resetBtn">Borrar mis códigos</button>
  </div>

  <div class="reveal" id="reveal"></div>
</div>

<script>
const DATA = __SAMPLE_JSON__;
const CRITERIA = __CRITERIA_JSON__;
const ITEMS = DATA.items;
const LSKEY = 'revisa_validacion_v1';
let idx = 0;
let codes = {};
try { codes = JSON.parse(localStorage.getItem(LSKEY) || '{}'); } catch(e) { codes = {}; }

function save() { localStorage.setItem(LSKEY, JSON.stringify(codes)); }
function curId() { return ITEMS[idx].paper_id; }
function getCode() { return codes[curId()] || {}; }

function isComplete(c) {
  if (c.gate === undefined || c.gate === null) return false;
  if (c.gate === 0) return true;            // gate=No → total 0, suficiente
  return ['I','II','III','IV','V','VI','integracion'].every(k => c[k] !== undefined && c[k] !== null);
}
function nCompleted() { return ITEMS.filter(it => isComplete(codes[it.paper_id] || {})).length; }

function humanTotal(c) {
  if (c.gate !== 1) return 0;
  const crits = ['I','II','III','IV','V','VI'].map(k => c[k]);
  if (crits.some(x => x === undefined || x === null)) return null;
  const sum = crits.reduce((a,b)=>a+b, 0);
  const integ = (c.integracion == null) ? 0 : c.integracion;
  return Math.round(((sum/6*4)*(0.5+0.5*integ))*2)/2;
}
function categoria(v) {
  if (v == null) return null;
  if (v === 0) return 'mención';
  if (v < 1.5) return 'nominal';
  if (v < 2.5) return 'parcial';
  if (v < 3.5) return 'sustantiva';
  return 'sustantiva fuerte';
}
const CATS = ['mención','nominal','parcial','sustantiva','sustantiva fuerte'];

function segClass(optVal) {
  if (optVal === 0) return 'sel-no';
  if (optVal === 1) return 'sel-yes';
  return 'sel-mid';
}

function render() {
  const it = ITEMS[idx];
  const c = getCode();
  let credits = '';
  CRITERIA.forEach(cr => {
    // si gate=No, los criterios quedan deshabilitados visualmente (opcionales)
    const disabled = (cr.key !== 'gate' && c.gate === 0);
    let btns = '';
    cr.opts.forEach(([lbl, val]) => {
      const sel = (c[cr.key] === val) ? segClass(val) : '';
      btns += `<button class="${sel}" ${disabled?'style="opacity:.5"':''} onclick="setVal('${cr.key}',${val})">${lbl}</button>`;
    });
    credits += `<div class="crit">
      <div class="crit-label">${cr.label}</div>
      <div class="crit-q">${cr.q}</div>
      <div class="seg">${btns}</div>
    </div>`;
  });
  const langPill = it.lang ? `<span class="pill ${it.lang}">${it.lang}</span>` : '';
  const doi = it.doi ? `<a class="doi" href="${it.doi.startsWith('http')?it.doi:'https://doi.org/'+it.doi}" target="_blank">abrir DOI ↗</a>` : '';
  document.getElementById('card').innerHTML = `
    <div class="pid">Paper ${idx+1} de ${ITEMS.length} · id ${it.paper_id} ${isComplete(c)?'· <span class="done-flag">✓ codificado</span>':''}</div>
    <div class="ptitle">${it.title}${langPill}</div>
    <div class="pmeta">${it.authors || '(sin autores)'} · ${it.source || '—'} · ${it.year || '—'} ${doi?'· '+doi:''}</div>
    <div class="abstract">${it.abstract || '(sin resumen)'}</div>
    ${credits}
    <div class="gate-no-note" id="gatenote">Marcaste <b>gate = No</b>: el trabajo no articula ejes de forma relacional, así que su RSI es 0. Puedes pasar al siguiente o anotar los criterios igualmente.</div>
    <textarea class="nota" id="nota" placeholder="Nota opcional (por qué dudaste, evidencia que viste...)">${c.nota || ''}</textarea>
  `;
  document.getElementById('gatenote').style.display = (c.gate === 0) ? 'block' : 'none';
  document.getElementById('nota').addEventListener('input', e => {
    const cc = getCode(); cc.nota = e.target.value; codes[curId()] = cc; save();
  });
  document.getElementById('prev').disabled = (idx === 0);
  document.getElementById('next').disabled = (idx === ITEMS.length-1);
  document.getElementById('counter').textContent = `${idx+1} / ${ITEMS.length}`;
  const done = nCompleted();
  document.getElementById('topstatus').innerHTML = `Codificados: <b>${done}</b> de ${ITEMS.length}`;
  document.getElementById('pbar').style.width = (100*done/ITEMS.length) + '%';
  document.getElementById('savedinfo').textContent = 'Tu avance se guarda automáticamente en este navegador.';
}

function setVal(key, val) {
  const c = getCode();
  c[key] = (c[key] === val) ? null : val;   // re-click deselecciona
  codes[curId()] = c; save(); render();
}
function go(d) { idx = Math.max(0, Math.min(ITEMS.length-1, idx+d)); render(); window.scrollTo({top:0,behavior:'smooth'}); }

// ── Concordancia humano–LLM ──
function cohenKappa(humanCats, llmCats) {
  const n = humanCats.length;
  if (n === 0) return null;
  let agree = 0;
  const hCount = {}, lCount = {};
  CATS.forEach(k => { hCount[k]=0; lCount[k]=0; });
  for (let i=0;i<n;i++) {
    if (humanCats[i] === llmCats[i]) agree++;
    hCount[humanCats[i]]++; lCount[llmCats[i]]++;
  }
  const po = agree/n;
  let pe = 0;
  CATS.forEach(k => { pe += (hCount[k]/n)*(lCount[k]/n); });
  const kappa = (pe === 1) ? 1 : (po - pe)/(1 - pe);
  return { kappa, po, n };
}
function kappaLabel(k) {
  if (k < 0) return 'pobre'; if (k < 0.2) return 'leve'; if (k < 0.4) return 'aceptable';
  if (k < 0.6) return 'moderada'; if (k < 0.8) return 'sustancial'; return 'casi perfecta';
}

function showKappa() {
  const coded = ITEMS.filter(it => isComplete(codes[it.paper_id] || {}));
  const rev = document.getElementById('reveal');
  if (coded.length < 2) {
    rev.style.display='block';
    rev.innerHTML = '<h2>Concordancia humano–LLM</h2><p>Codifica al menos 2 trabajos para calcular el κ.</p>';
    rev.scrollIntoView({behavior:'smooth'}); return;
  }
  const hCats=[], lCats=[];
  // acuerdo por criterio
  const critKeys = ['gate','I','II','III','IV','V','VI','integracion'];
  const critAgree = {}; critKeys.forEach(k => critAgree[k] = {match:0, tot:0});
  coded.forEach(it => {
    const c = codes[it.paper_id];
    const ht = humanTotal(c), lt = it.llm.total;
    hCats.push(categoria(ht)); lCats.push(categoria(lt));
    critKeys.forEach(k => {
      const hv = (k==='gate') ? c.gate : c[k];
      const lv = it.llm[k];
      if (hv != null && lv != null) { critAgree[k].tot++; if (hv === lv) critAgree[k].match++; }
    });
  });
  const r = cohenKappa(hCats, lCats);
  let rows = '';
  critKeys.forEach(k => {
    const a = critAgree[k];
    const pct = a.tot ? Math.round(100*a.match/a.tot) : null;
    const lbl = (k==='gate')?'Gate':(k==='integracion'?'Integración':k);
    rows += `<tr><td>${lbl}</td><td>${a.tot}</td><td class="${pct>=70?'agree-hi':(pct!=null&&pct<50?'agree-lo':'')}">${pct==null?'—':pct+'%'}</td></tr>`;
  });
  rev.style.display='block';
  rev.innerHTML = `
    <h2>Concordancia humano–LLM (n=${r.n} codificados)</h2>
    <div style="display:flex;gap:24px;align-items:baseline;flex-wrap:wrap">
      <div><div class="kappa-big">κ = ${r.kappa.toFixed(2)}</div>
        <div style="font-size:12px;color:#6b7280">concordancia ${kappaLabel(r.kappa)} (categoría RSI, 5 niveles)</div></div>
      <div><div style="font-size:22px;font-weight:700">${Math.round(100*r.po)}%</div>
        <div style="font-size:12px;color:#6b7280">acuerdo exacto de categoría</div></div>
    </div>
    <h3 style="font-size:13px;margin:16px 0 4px">Acuerdo exacto por criterio</h3>
    <table class="ktable"><thead><tr><th>Criterio</th><th>n comparados</th><th>% acuerdo</th></tr></thead>
      <tbody>${rows}</tbody></table>
    <p style="font-size:11.5px;color:#9ca3af;margin-top:10px">κ de Cohen sin ponderar sobre las 5 categorías de RSI. Muestra estratificada (${DATA.meta.n_per_cat}/categoría) — interpretar como validación de la discriminación del instrumento, no como prevalencia poblacional.</p>
  `;
  rev.scrollIntoView({behavior:'smooth'});
}

// ── Export ──
function download(name, content, type) {
  const blob = new Blob([content], {type});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  URL.revokeObjectURL(a.href);
}
function exportCSV() {
  const cols = ['paper_id','title','human_gate','human_I','human_II','human_III','human_IV','human_V','human_VI','human_integracion','human_total','human_categoria','llm_total','llm_categoria','confianza','nota'];
  const esc = s => '"' + String(s==null?'':s).replace(/"/g,'""').replace(/\n/g,' ') + '"';
  let out = cols.join(',') + '\n';
  ITEMS.forEach(it => {
    const c = codes[it.paper_id] || {};
    if (!isComplete(c)) return;
    const ht = humanTotal(c);
    const row = [it.paper_id, it.title, c.gate, c.I, c.II, c.III, c.IV, c.V, c.VI, c.integracion,
      ht, categoria(ht), it.llm.total, categoria(it.llm.total), c.conf||'', c.nota||''];
    out += row.map(esc).join(',') + '\n';
  });
  download('validacion_RSI_v2_codigos.csv', out, 'text/csv');
}
function exportJSON() {
  const payload = { meta: DATA.meta, generado: new Date().toISOString(), codigos: codes };
  download('validacion_RSI_v2_codigos.json', JSON.stringify(payload, null, 2), 'application/json');
}

document.getElementById('prev').onclick = () => go(-1);
document.getElementById('next').onclick = () => go(1);
document.getElementById('kappaBtn').onclick = showKappa;
document.getElementById('csvBtn').onclick = exportCSV;
document.getElementById('jsonBtn').onclick = exportJSON;
document.getElementById('resetBtn').onclick = () => {
  if (confirm('¿Borrar todos tus códigos guardados en este navegador?')) {
    codes = {}; save(); document.getElementById('reveal').style.display='none'; render();
  }
};
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'TEXTAREA') return;
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
