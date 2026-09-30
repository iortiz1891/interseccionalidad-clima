#!/usr/bin/env python3
"""
09_dashboard.py — v2: pestaña "v2 · búsqueda ampliada" del dashboard (site/v2/index.html).

Se construye solo con los datos de la búsqueda ampliada (data/v2_*). No reutiliza
registros ni puntajes de la v1; del dashboard v1 conserva únicamente el diseño y el
texto teórico que no depende de datos (criterios de la RSI, genealogía, referencias).
"""
from __future__ import annotations
import base64
import html as _html
import json
from pathlib import Path
import pandas as pd

DATA = Path("data")
ASSETS = Path("assets")
OUT = Path("site/v2")

CAT_ORDER = ['sustantivo_fuerte', 'sustantivo', 'parcial', 'nominal_debil', 'mencion_sin_aplicacion']
CAT_LABELS = {'sustantivo_fuerte': 'Sustantiva fuerte (3.5–4.0)', 'sustantivo': 'Sustantiva (2.5–3.0)',
              'parcial': 'Parcial (1.5–2.0)', 'nominal_debil': 'Nominal/débil (0.5–1.0)',
              'mencion_sin_aplicacion': 'Mención sin aplicación (0)'}
CAT_COLOR = {'mencion_sin_aplicacion': '#c9c8c3', 'nominal_debil': '#86b6ef', 'parcial': '#5598e7',
             'sustantivo': '#256abf', 'sustantivo_fuerte': '#104281'}
TIPO_LABEL = {'empirico_cuantitativo': 'Empírico cuantitativo', 'empirico_cualitativo': 'Empírico cualitativo',
              'empirico_mixto': 'Empírico mixto', 'conceptual_teorico': 'Conceptual / teórico',
              'revision': 'Revisión', 'otro': 'Otro (editorial, nota…)'}
AMENAZA_LABEL = {'cambio_climatico_general': 'Cambio climático (general)',
                 'ciclon_huracan_tormenta': 'Ciclones, huracanes, tormentas', 'inundacion': 'Inundaciones',
                 'sequia': 'Sequías', 'calor_extremo': 'Calor extremo', 'incendio_forestal': 'Incendios forestales',
                 'nivel_mar_costas': 'Nivel del mar y costas', 'glaciares_criosfera': 'Glaciares y criósfera',
                 'desastres_multiples': 'Desastres (varios)', 'mitigacion_transicion': 'Mitigación y transición',
                 'otro': 'Otro'}
ANCLA_LABEL = {'A_nucleo': 'A · núcleo (intersectional / interseccional)',
               'A_ampliada': 'A · ampliada ("intersection of race and gender", "intersecting …")',
               'B_afin': 'B · vocabulario afín (matrix of domination, colonialidad del género…)',
               'solo_index_keywords': 'Solo en keywords indexadas'}

CSS = """
  :root { --accent: #2563eb; --accent-dark: #1e40af; --ink: #1f2937; --muted: #6b7280;
    --line: #e5e7eb; --bg: #f8fafc; --card: #ffffff; }
  * { box-sizing: border-box; }
  body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0;
    color: var(--ink); background: var(--bg); line-height: 1.65; }
  .main p, .main li { font-size: 13.5px; }
  .layout { display: flex; align-items: flex-start; }
  .sidebar { position: sticky; top: 0; height: 100vh; width: 248px; flex-shrink: 0;
    background: #0f172a; color: #cbd5e1; overflow-y: auto; padding: 22px 0; }
  .sidebar-brand { font-size: 18px; font-weight: 800; color: #fff; padding: 0 22px 18px;
    letter-spacing: 0.5px; border-bottom: 1px solid #1e293b; margin-bottom: 10px; }
  .sidebar-brand span { display: block; font-size: 11px; font-weight: 500; color: #64748b;
    letter-spacing: 1.5px; text-transform: uppercase; margin-top: 3px; }
  .sidebar-nav { display: flex; flex-direction: column; }
  .nav-group { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px;
    color: #475569; padding: 16px 22px 5px; }
  .sidebar-nav a { color: #cbd5e1; text-decoration: none; font-size: 13.5px; padding: 7px 22px;
    border-left: 3px solid transparent; transition: all .12s; }
  .sidebar-nav a:hover { background: #1e293b; color: #fff; }
  .sidebar-nav a.active { background: #1e293b; color: #fff; border-left-color: var(--accent); font-weight: 600; }
  .sidebar-nav a.nav-tool { margin: 6px 14px 0; background: #1d4ed8; color: #fff; border-radius: 7px;
    font-weight: 600; text-align: center; border-left: none; padding: 9px 12px; }
  .main { flex: 1; max-width: 980px; margin: 0 auto; padding: 0 40px 80px; min-width: 0; }
  .version-tabs { display: flex; gap: 6px; padding-top: 18px; border-bottom: 1px solid var(--line); }
  .version-tabs a { padding: 8px 16px; border: 1px solid var(--line); border-bottom: none;
    border-radius: 8px 8px 0 0; text-decoration: none; color: var(--muted); font-size: 13px;
    font-weight: 600; background: #f1f5f9; margin-bottom: -1px; }
  .version-tabs a span { font-weight: 400; font-size: 11.5px; margin-left: 6px; }
  .version-tabs a.active { background: var(--bg); color: var(--ink); border-bottom: 1px solid var(--bg); }
  .topbar { padding: 30px 0 18px; border-bottom: 1px solid var(--line); margin-bottom: 8px; }
  .topbar h1 { font-size: 23px; font-weight: 800; margin: 0 0 6px; }
  .topbar p { color: var(--muted); font-size: 14px; margin: 0; }
  h2 { font-size: 18px; font-weight: 700; margin: 44px 0 14px; scroll-margin-top: 20px;
    padding-bottom: 8px; border-bottom: 2px solid var(--line); }
  h3 { font-size: 15px; color: #374151; margin-top: 24px; }
  .caveat { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px 18px; margin: 18px 0;
    font-size: 13.5px; border-radius: 0 8px 8px 0; }
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin: 18px 0; }
  .stat { background: var(--card); border: 1px solid var(--line); padding: 18px 14px; border-radius: 12px;
    text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
  .stat-num { font-size: 25px; font-weight: 800; color: var(--accent); line-height: 1; }
  .stat-lbl { font-size: 12px; color: var(--muted); margin-top: 8px; }
  .data-table { border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 13px; background: var(--card);
    border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
  .data-table th { background: #f1f5f9; color: #334155; padding: 10px; text-align: left; font-weight: 600;
    border-bottom: 2px solid var(--line); }
  .data-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
  .data-table tr:hover { background: #f8fafc; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  pre.code-block { background: #0f172a; color: #e2e8f0; padding: 18px; border-radius: 10px; overflow-x: auto;
    font-size: 12px; line-height: 1.6; font-family: 'SF Mono', Menlo, monospace; white-space: pre-wrap;
    word-wrap: break-word; max-height: 460px; }
  pre.query { background: #f8fafc; color: #0f172a; border: 1px solid var(--line); max-height: none; }
  .theory-block { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 20px 24px;
    margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
  .flow-diagram { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 18px; margin: 16px 0;
    font-family: 'SF Mono', Menlo, monospace; font-size: 12.5px; text-align: center; }
  img { max-width: 100%; border: 1px solid var(--line); border-radius: 10px; margin: 10px 0; background: #fff; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
  details { background: var(--card); border: 1px solid var(--line); padding: 14px 18px; border-radius: 10px; margin: 14px 0; }
  details summary { font-weight: 600; cursor: pointer; color: var(--accent-dark); }
  .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
  .badge-prov { background: #fef3c7; color: #b45309; }
  .doc-link { display: inline-block; background: var(--accent); color: #fff !important; padding: 9px 16px;
    border-radius: 8px; text-decoration: none; margin: 6px 6px 6px 0; font-size: 13px; font-weight: 500; }
  .daniel-box { background: #faf5ff; border-left: 4px solid #9333ea; padding: 18px; border-radius: 0 10px 10px 0; margin: 18px 0; }
  .insight { background: #f0f7f4; border-left: 4px solid #10b981; padding: 14px 18px; margin: 16px 0;
    border-radius: 0 8px 8px 0; font-size: 13.5px; line-height: 1.6; }
  .insight .lbl { display: block; font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: #059669; margin-bottom: 6px; }
  .chip { display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 12px; margin: 2px 3px 2px 0; color: #fff; }
  a { color: var(--accent); }
  @media (max-width: 860px) { .sidebar { display: none; } .main { padding: 0 16px 60px; } .grid-2 { grid-template-columns: 1fr; } }
"""

SCROLL_JS = """
<script>
(function() {
  const links = Array.from(document.querySelectorAll('.sidebar-nav a[href^="#"]'));
  const map = {};
  links.forEach(a => { const id = a.getAttribute('href').slice(1); if (document.getElementById(id)) map[id] = a; });
  const ids = Object.keys(map);
  function onScroll() {
    let current = ids[0];
    for (const id of ids) { const el = document.getElementById(id); if (el && el.getBoundingClientRect().top <= 120) current = id; }
    links.forEach(a => a.classList.remove('active'));
    if (map[current]) map[current].classList.add('active');
  }
  document.addEventListener('scroll', onScroll, { passive: true });
  links.forEach(a => a.addEventListener('click', e => {
    const el = document.getElementById(a.getAttribute('href').slice(1));
    if (el) { e.preventDefault(); el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  }));
  onScroll();
})();
</script>
"""

CRITERIOS_TABLA = """
<table class="data-table" style="margin-top:4px;">
  <tr><th>Criterio</th><th>Pregunta diagnóstica</th><th>Ejemplo de aplicación sustantiva</th></tr>
  <tr><td><b>Gate — criterio de entrada</b></td><td>¿Articula dos o más ejes de diferenciación social como relacionados entre sí, no solo mencionados por separado?</td><td style="font-style:italic;color:#555">Si no los articula, el total es 0 (mención sin aplicación).</td></tr>
  <tr><td><b>I — Identidades entrelazadas</b><br><span style="font-size:11px;color:#888">Crenshaw 1989; Bowleg 2012</span></td><td>¿Trata ≥2 ejes como mutuamente constitutivos, no aditivos?</td><td style="font-style:italic;color:#555">"Ser mujer indígena ante el huracán no es 'mujer' + 'indígena': es una posición distinta."</td></tr>
  <tr><td><b>II — Poder estructural</b><br><span style="font-size:11px;color:#888">Collins 2000; Crenshaw 1991</span></td><td>¿Articula estructuras (racismo, patriarcado, colonialismo) y mecanismos, no rasgos individuales?</td><td style="font-style:italic;color:#555">La exposición se explica por despojo territorial, no por "falta de preparación".</td></tr>
  <tr><td><b>III — Contexto situado</b><br><span style="font-size:11px;color:#888">McCall 2005</span></td><td>¿Sitúa los hallazgos en historia, geografía y política específicas?</td><td style="font-style:italic;color:#555">Una costa, un huracán y una reforma agraria concretos.</td></tr>
  <tr><td><b>IV — Método no aditivo</b><br><span style="font-size:11px;color:#888">Hancock 2007; Else-Quest &amp; Hyde 2016</span></td><td>¿El diseño empírico capta interacciones (muestreo intencional, codificación cruzada, términos de interacción)?</td><td style="font-style:italic;color:#555">Muestreo de "mujeres indígenas pescadoras" como categoría combinada.</td></tr>
  <tr><td><b>V — Praxis y justicia</b><br><span style="font-size:11px;color:#888">Collins &amp; Bilge 2016</span></td><td>¿Se orienta a transformar desigualdades, no solo a describirlas?</td><td style="font-style:italic;color:#555">Recomendaciones de adaptación construidas con y para las comunidades.</td></tr>
  <tr><td><b>VI — Agencia y resistencia</b><br><span style="font-size:11px;color:#888">Collins 2000; feminismos del Sur</span></td><td>¿Reconoce a los sujetos como agentes, no solo como víctimas?</td><td style="font-style:italic;color:#555">Documenta estrategias y saberes propios frente al ciclón.</td></tr>
  <tr><td><b>Factor de integración</b></td><td>¿Los criterios se articulan en un análisis coherente o se yuxtaponen?</td><td style="font-style:italic;color:#555">Ajusta el total: la interseccionalidad es, ante todo, integración.</td></tr>
</table>
"""

GENEALOGIA = """
<div class="theory-block">
  <p style="margin-top:0;">La RSI no surge de un autor único, sino de cinco décadas de teoría feminista crítica. Cada criterio responde a un aporte específico:</p>
  <p><b>Crenshaw (1989, 1991) — el origen.</b> Acuña "interseccionalidad" para mostrar que las mujeres negras quedan en un punto ciego de marcos de eje único. Las opresiones no se suman, se <em>co-constituyen</em>. → <b>Criterio I</b>.</p>
  <p><b>Collins (2000) — la matriz de dominación.</b> Teoriza el poder como sistema interconectado (estructural, disciplinario, hegemónico, interpersonal). → <b>Criterio II</b>.</p>
  <p><b>McCall (2005) — la complejidad.</b> Enfoques anti-, intra- e intercategóricos; la interseccionalidad opera de forma <em>situada</em>. → <b>Criterio III</b>.</p>
  <p><b>Hancock (2007) — el paradigma de investigación.</b> La interseccionalidad es también un <em>método</em>: exige diseños que capten interacciones. → <b>Criterio IV</b>.</p>
  <p><b>Bowleg (2012) — la operacionalización empírica.</b> Denuncia el uso aditivo y propone cómo aplicar el marco sin traicionarlo. → <b>Criterios I y IV</b>.</p>
  <p><b>Collins &amp; Bilge (2016) — la praxis.</b> Herramienta crítica orientada a la justicia social. → <b>Criterio V</b>. De esa tradición y de los feminismos del Sur viene reconocer la <em>agencia</em> de los sujetos. → <b>Criterio VI</b>.</p>
  <p style="margin-bottom:0;"><b>La crítica al uso nominal</b> (Davis 2008, "buzzword"; Carbado et al. 2013, "citar sin movilizar") justifica <em>medir</em> la sustantividad.</p>
</div>
"""

REFERENCIAS = """
<ol style="font-size:13px;line-height:1.7;">
  <li>Crenshaw, K. (1989). Demarginalizing the Intersection of Race and Sex. <i>University of Chicago Legal Forum</i>, 1989(1), 139–167. <a href="https://chicagounbound.uchicago.edu/uclf/vol1989/iss1/8/" target="_blank">[texto]</a></li>
  <li>Crenshaw, K. (1991). Mapping the Margins. <i>Stanford Law Review</i>, 43(6), 1241–1299. <a href="https://doi.org/10.2307/1229039" target="_blank">[DOI]</a></li>
  <li>Collins, P. H. (2000). <i>Black Feminist Thought</i> (2ª ed.). Routledge.</li>
  <li>McCall, L. (2005). The Complexity of Intersectionality. <i>Signs</i>, 30(3), 1771–1800. <a href="https://doi.org/10.1086/426800" target="_blank">[DOI]</a></li>
  <li>Hancock, A.-M. (2007). When Multiplication Doesn't Equal Quick Addition. <i>Perspectives on Politics</i>, 5(1), 63–79. <a href="https://doi.org/10.1017/S1537592707070065" target="_blank">[DOI]</a></li>
  <li>Davis, K. (2008). Intersectionality as Buzzword. <i>Feminist Theory</i>, 9(1), 67–85. <a href="https://doi.org/10.1177/1464700108086364" target="_blank">[DOI]</a></li>
  <li>Bowleg, L. (2012). The Problem with the Phrase Women and Minorities. <i>American Journal of Public Health</i>, 102(7), 1267–1273. <a href="https://doi.org/10.2105/AJPH.2012.300750" target="_blank">[DOI]</a></li>
  <li>Carbado, D. W., Crenshaw, K. W., Mays, V. M., &amp; Tomlinson, B. (2013). Intersectionality: Mapping the Movements of a Theory. <i>Du Bois Review</i>, 10(2), 303–312. <a href="https://doi.org/10.1017/S1742058X13000349" target="_blank">[DOI]</a></li>
  <li>Else-Quest, N. M., &amp; Hyde, J. S. (2016). Intersectionality in Quantitative Psychological Research: II. <i>Psychology of Women Quarterly</i>, 40(3), 319–336. <a href="https://doi.org/10.1177/0361684316647953" target="_blank">[DOI]</a></li>
  <li>Collins, P. H., &amp; Bilge, S. (2016). <i>Intersectionality</i>. Polity Press.</li>
  <li>Rethlefsen, M. L., et al. (2021). PRISMA-S: an extension to the PRISMA Statement for Reporting Literature Searches in Systematic Reviews. <i>Systematic Reviews</i>, 10, 39. <a href="https://doi.org/10.1186/s13643-020-01542-z" target="_blank">[DOI]</a></li>
</ol>
"""


def img(name: str) -> str:
    p = ASSETS / f'v2_{name}.png'
    return f'<img src="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}" alt="{name}">'


def insight(body: str, label: str = 'Lectura del dato') -> str:
    return f'<div class="insight"><span class="lbl">{label}</span>{body}</div>'


def esc(x) -> str:
    return _html.escape('' if x is None or (isinstance(x, float) and pd.isna(x)) else str(x))


def table(df: pd.DataFrame, cols: list[tuple[str, str]], max_rows: int = 30) -> str:
    head = ''.join(f'<th>{lbl}</th>' for _, lbl in cols)
    rows = []
    for _, r in df.head(max_rows).iterrows():
        cells = []
        for c, _ in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append(f'<td class="num">{v:,.1f}</td>' if abs(v) >= 10 or c.startswith('pct') else f'<td class="num">{v:.2f}</td>')
            elif isinstance(v, (int,)) or (hasattr(v, 'dtype') and 'int' in str(getattr(v, 'dtype', ''))):
                cells.append(f'<td class="num">{int(v):,}</td>')
            else:
                cells.append(f'<td>{esc(v)}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    return f'<table class="data-table"><tr>{head}</tr>{"".join(rows)}</table>'


def load_prompt(path: str) -> str:
    t = Path(path).read_text()
    if t.startswith('---'):
        parts = t.split('---', 2)
        if len(parts) >= 3: t = parts[2].strip()
    return _html.escape(t)


def doi_link(d) -> str:
    d = '' if d is None or (isinstance(d, float) and pd.isna(d)) else str(d).strip()
    if not d: return '<span style="color:#bbb;font-size:11px">sin DOI</span>'
    return f'<a href="https://doi.org/{esc(d)}" target="_blank" style="font-size:11px">abrir ↗</a>'


def rsi_badge(v: float) -> str:
    cat = ('sustantivo_fuerte' if v >= 3.5 else 'sustantivo' if v >= 2.5 else 'parcial' if v >= 1.5
           else 'nominal_debil' if v > 0 else 'mencion_sin_aplicacion')
    fg = '#1f2937' if cat in ('mencion_sin_aplicacion', 'nominal_debil') else '#fff'
    return (f'<span style="background:{CAT_COLOR[cat]};color:{fg};padding:1px 7px;border-radius:9px;'
            f'font-size:11px;font-weight:600">{v:.1f}</span>')


def main():
    meta = json.loads((DATA / 'v2_prisma_meta.json').read_text())
    smeta = json.loads((DATA / 'v2_search_meta.json').read_text())
    stats = json.loads((DATA / 'v2_corpus_stats.json').read_text())
    tstats = json.loads((DATA / 'v2_topic_stats.json').read_text())
    f = pd.read_csv(DATA / 'v2_corpus_final.csv')
    cr = pd.read_csv(DATA / 'v2_cribado.csv')
    tb = pd.read_csv(DATA / 'v2_topics_x_bowleg.csv')
    lb = pd.read_csv(DATA / 'v2_lang_x_bowleg.csv')
    cb = pd.read_csv(DATA / 'v2_country_x_bowleg.csv')
    ab = pd.read_csv(DATA / 'v2_affil_x_bowleg.csv')
    tipo = pd.read_csv(DATA / 'v2_tipo_x_bowleg.csv')
    am = pd.read_csv(DATA / 'v2_amenaza_x_bowleg.csv')
    yb = pd.read_csv(DATA / 'v2_year_x_bowleg.csv')
    sub = pd.read_csv(DATA / 'v2_daniel_subcorpus.csv').sort_values('bowleg_total', ascending=False)
    casos = json.loads((DATA / 'v2_casos_ejemplares.json').read_text())
    query = (DATA / 'v2_query_scopus.txt').read_text().strip()

    n = len(f)
    gp = f[f['gate_pass'] == True]
    pct = lambda s: 100 * s.mean()
    p_gate_fail = pct(f['bowleg_total'] == 0)
    p_sust = pct(f['bowleg_total'] >= 2.5)
    p_fuerte = pct(f['bowleg_total'] >= 3.5)
    p_iv = pct(gp['bowleg_IV'] == 1)
    crit_pct = stats['criterios_cumple_gate_pct']
    emp = gp[gp['tipo_estudio'].str.startswith('empirico')]
    p_iv_emp = pct(emp['bowleg_IV'] == 1) if len(emp) else 0
    cat_n = f['categoria_bowleg'].value_counts()
    cr_meta = meta['cribado']
    excl_rate_by_anchor = cr.groupby('nivel_ancla')['elegible'].agg(['size', 'mean'])

    ts = tstats['topics']
    top_sust = [t for t in ts if t['n'] >= 15][:4]
    low_sust = sorted([t for t in ts if t['n'] >= 15], key=lambda t: t['rsi_mean'])[:3]
    yb_c = yb[(yb['Year'] >= 2016) & (yb['n'] >= 20)]
    trend_first, trend_last = (yb_c.iloc[0], yb_c.iloc[-2] if len(yb_c) > 2 else yb_c.iloc[-1]) if len(yb_c) else (None, None)
    ds = stats['daniel_subcorpus']
    en = lb[lb['idioma'] == 'en'].iloc[0] if (lb['idioma'] == 'en').any() else None
    es = lb[lb['idioma'] == 'es'].iloc[0] if (lb['idioma'] == 'es').any() else None
    lugares = cb[~cb['country'].isin(['Global', 'No especificado'])]
    lug15 = lugares[lugares['n'] >= 15].sort_values('pct_substantive', ascending=False)

    # ── Bloques ──
    sidebar = """
    <aside class="sidebar">
      <div class="sidebar-brand">Interseccionalidad<span>y cambio climático · v2</span></div>
      <nav class="sidebar-nav">
        <div class="nav-group">Búsqueda</div>
        <a href="#busqueda">Cadena de búsqueda</a>
        <a href="#prisma">Flujo PRISMA</a>
        <a href="#cribado">Cribado</a>
        <div class="nav-group">Marco</div>
        <a href="#rsi">Qué es la RSI</a>
        <a href="#teoria">Genealogía teórica</a>
        <a href="#prompts">Cómo se aplica</a>
        <div class="nav-group">Hallazgos</div>
        <a href="#nums">Números clave</a>
        <a href="#bowleg">Distribución RSI</a>
        <a href="#anatomia">Anatomía de la RSI</a>
        <a href="#metodo">Método por tipo de estudio</a>
        <a href="#anual">Producción anual</a>
        <a href="#topics">Tópicos</a>
        <a href="#topicmap">Mapa interactivo</a>
        <a href="#amenazas">Amenazas</a>
        <a href="#lang">Idiomas</a>
        <a href="#paises">Geografía</a>
        <a href="#temporal">Tendencia temporal</a>
        <div class="nav-group">Método</div>
        <a href="#casos">Casos ejemplares</a>
        <a href="#valid">Validación</a>
        <a href="#daniel">Sub-corpus tesis</a>
        <div class="nav-group">Cierre</div>
        <a href="#sintesis">Síntesis</a>
        <a href="#docs">Documentos</a>
        <a href="#refs">Referencias</a>
        <div class="nav-group">Herramientas</div>
        <a href="validacion.html" class="nav-tool">✓ Validar la rúbrica</a>
      </nav>
    </aside>"""

    anchor_rows = ''.join(
        f"<tr><td>{ANCLA_LABEL.get(k, k)}</td><td class='num'>{int(r['size']):,}</td>"
        f"<td class='num'>{100 * r['mean']:.0f}%</td></tr>"
        for k, r in excl_rate_by_anchor.sort_values('size', ascending=False).iterrows())
    excl = cr[~cr['elegible']].copy()
    ejemplos = excl.sample(min(10, len(excl)), random_state=7) if len(excl) else excl
    ejemplos_rows = ''.join(
        f"<tr><td style='font-size:12.5px'>{esc(str(r['Title'])[:120])}</td>"
        f"<td style='font-size:12px;color:#555'>{esc(r['motivo_exclusion'])}</td></tr>"
        for _, r in ejemplos.iterrows())
    dt_elig = cr.groupby('Document Type')['elegible'].agg(['size', 'mean']).sort_values('size', ascending=False)
    dt_rows = ''.join(f"<tr><td>{esc(k)}</td><td class='num'>{int(r['size']):,}</td><td class='num'>{100 * r['mean']:.0f}%</td></tr>"
                      for k, r in dt_elig.iterrows())

    casos_html = ''
    for c in casos:
        sc = " · ".join(f"{k}={'—' if v is None else (int(v) if float(v).is_integer() else v)}" for k, v in c['scores'].items())
        evs = ''.join(f"<li><b>{k}:</b> <i>{esc(v)}</i></li>" for k, v in c['evidencias'].items() if v)
        block = (f"<ul style='margin:6px 0 0;padding-left:18px;font-size:12px;'>{evs}</ul>" if evs
                 else f"<p style='font-size:12px;color:#666;margin:6px 0 0'>{esc(c['gate_evidence'])}</p>")
        casos_html += (f"<div style='border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0;background:var(--card)'>"
                       f"<div style='display:flex;justify-content:space-between;gap:10px;align-items:start'>"
                       f"<div style='font-weight:600;font-size:13.5px'>{esc(c['titulo'])}</div>{rsi_badge(c['rsi_total'])}</div>"
                       f"<div style='font-size:11px;color:#6b7280;margin-top:3px'>{esc(c['year'])} · {esc(c['categoria'])} · {sc}</div>{block}</div>")

    ficha_rows = ''.join(
        f"<tr><td style='font-size:11px;color:#888'>T{t['topic_id']}</td><td style='font-size:12px'>{esc(t['label'])}</td>"
        f"<td class='num'>{t['n']}</td><td class='num'>{rsi_badge(t['rsi_mean'])}</td><td class='num'>{t['gate_pct']:.0f}%</td>"
        f"<td class='num'>{t['sust_pct']:.0f}%</td><td class='num'>{t['es_pct']:.0f}%</td>"
        f"<td class='num'>{t['n_tesis'] or ''}</td></tr>" for t in ts)
    ficha = ("<table class='data-table' style='font-size:12px'><tr><th>#</th><th>Tópico</th><th>n</th><th>RSI media</th>"
             f"<th>% gate</th><th>% sust.</th><th>% ES</th><th>Tesis</th></tr>{ficha_rows}</table>")

    sub_rows = ''.join(
        f"<tr><td>{rsi_badge(float(r['bowleg_total']))}</td><td style='font-size:12.5px'>{esc(str(r['Title'])[:130])}</td>"
        f"<td style='font-size:11px;color:#6b7280'>{'' if pd.isna(r['Year']) else int(r['Year'])} · {esc(str(r['idioma']).upper())}</td>"
        f"<td>{doi_link(r['DOI'])}</td></tr>" for _, r in sub.iterrows())

    tipo_t = tipo.copy()
    tipo_t['tipo'] = tipo_t['tipo_estudio'].map(TIPO_LABEL)
    am_t = am.copy(); am_t['amenaza_lbl'] = am_t['amenaza'].map(AMENAZA_LABEL)
    lb_t = lb.copy(); lb_t['idioma_lbl'] = lb_t['idioma'].map({'en': 'Inglés', 'es': 'Español'})

    tl = ", ".join(f"<i>{esc(t['label'])}</i> ({t['rsi_mean']:.2f})" for t in top_sust)
    ll = ", ".join(f"<i>{esc(t['label'])}</i> ({t['rsi_mean']:.2f})" for t in low_sust)
    trend_txt = ''
    if trend_first is not None:
        trend_txt = (f"Entre {int(trend_first['Year'])} y {int(trend_last['Year'])} el volumen pasa de "
                     f"{int(trend_first['n'])} a {int(trend_last['n'])} trabajos por año, mientras la proporción sustantiva "
                     f"va de {trend_first['pct_substantive']:.0f}% a {trend_last['pct_substantive']:.0f}%.")
    lang_txt = ''
    if en is not None and es is not None:
        lang_txt = (f"Los trabajos en inglés ({int(en['n'])}) tienen {en['pct_substantive']:.0f}% de aplicación sustantiva; "
                    f"los escritos en español son solo {int(es['n'])} ({es['pct_substantive']:.0f}%). ")
    lug_txt = ''
    if len(lug15):
        best, worst = lug15.iloc[0], lug15.iloc[-1]
        lug_txt = (f"Entre los lugares con ≥ 15 trabajos, el rango va de <b>{esc(best['country'])}</b> "
                   f"({best['pct_substantive']:.0f}% sustantivo) a <b>{esc(worst['country'])}</b> ({worst['pct_substantive']:.0f}%). ")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Interseccionalidad y Cambio Climático · v2</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
{sidebar}
<div class="main">

<nav class="version-tabs" aria-label="Versión del corpus">
  <a href="../index.html">v1 · corpus original<span>mayo 2026</span></a>
  <a href="index.html" class="active">v2 · búsqueda ampliada<span>{n:,} trabajos · septiembre 2026</span></a>
</nav>

<div class="topbar">
  <h1>Interseccionalidad y Cambio Climático · v2</h1>
  <p>Búsqueda ampliada en Scopus ({smeta['fecha_busqueda']}) · {meta['identificados_scopus']:,} registros identificados · {n:,} trabajos elegibles medidos con la Rúbrica de Sustantividad Interseccional · <span class="badge badge-prov">scoring provisional</span></p>
</div>

<div class="caveat">
  <strong>Cómo leer esta pestaña.</strong> La v2 se construye <b>solo con la búsqueda ampliada</b>: no reutiliza registros ni puntajes de la v1.
  Antes de la RSI hay un <b>cribado de elegibilidad</b> que separa lo que no es del tema (p. ej. "intersection" en sentido vial o genérico, "clima" escolar) de lo que invoca el marco sin aplicarlo.
  Los puntajes los asignó <b>Claude (claude-opus-5-5)</b> con el prompt versionado <code>prompts/v2_cribado_rsi.md</code> y la misma rúbrica RSI v3; son <b>provisionales</b> hasta la validación humana (§ Validación).
</div>

<div style="background:#f0f7f4;border:1px solid #c4e0c4;border-radius:12px;padding:18px 22px;margin:18px 0;">
  <div style="font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#059669;margin-bottom:10px;">En síntesis</div>
  <ul style="margin:0;padding-left:20px;line-height:1.7;font-size:13.5px;">
    <li><b>Búsqueda.</b> {meta['identificados_scopus']:,} registros en Scopus con una cadena bilingüe; tras reglas, deduplicación y cribado quedan <b>{n:,} trabajos elegibles</b> ({100 * n / meta['a_cribado']:.0f}% de los cribados).</li>
    <li><b>Adopción y aplicación.</b> Entre los elegibles, el <b>{p_gate_fail:.0f}%</b> invoca el marco sin articular ejes (RSI = 0); el <b>{p_sust:.0f}%</b> alcanza aplicación sustantiva (RSI ≥ 2.5) y el <b>{p_fuerte:.0f}%</b> sustantiva fuerte.</li>
    <li><b>El eslabón débil es el método.</b> Entre los que pasan el gate, solo el <b>{p_iv:.0f}%</b> cumple el criterio IV (método no aditivo); en estudios empíricos, el <b>{p_iv_emp:.0f}%</b>.</li>
    <li><b>El rigor se concentra.</b> Los tópicos con mayor RSI media: {tl}.</li>
    <li><b>Para la tesis.</b> {ds['relevant_ge2_axes']} trabajos combinan ≥ 2 ejes temáticos de la tesis (RSI media {ds['relevant_bowleg_mean']:.2f}); solo {ds['mexico_AND_cyclonic']} cruzan México y ciclones.</li>
  </ul>
</div>

<h2 id="busqueda">1 · Cadena de búsqueda</h2>
<p><b>Base:</b> {smeta['base']} · <b>plataforma:</b> {esc(smeta['plataforma'])} · <b>fecha:</b> {smeta['fecha_busqueda']} · <b>límites:</b> {esc(smeta['limites'])}.
Una sola cadena bilingüe: en Scopus los trabajos en español suelen traer el abstract solo en inglés, así que se buscan términos en ambos idiomas. El ancla exige la interseccionalidad en sentido teórico; el bloque climático es amplio; no hay bloque de ejes sociales (excluiría justo los usos nominales que se quieren medir).</p>
<pre class="code-block query">{esc(query)}</pre>
<div class="grid-2">
  <div>
    <h3 style="margin-top:6px">Resultados por parte del ancla</h3>
    <table class="data-table">
      <tr><th>Parte del ancla</th><th>Registros</th></tr>
      <tr><td>Solo <code>intersectional*</code> / <code>interseccional*</code></td><td class="num">{smeta['desglose_ancla']['nucleo_intersectional_interseccional']:,}</td></tr>
      <tr><td>Además, frases como "intersection of race and gender" (<code>W/4</code>) o "intersecting …"</td><td class="num">{smeta['desglose_ancla']['ampliada_W4_intersecting']:,}</td></tr>
      <tr><td>Solo vocabulario afín</td><td class="num">{smeta['desglose_ancla']['solo_vocabulario_afin']:,}</td></tr>
      <tr><td><b>Total</b></td><td class="num"><b>{smeta['resultados']:,}</b></td></tr>
    </table>
  </div>
  <div>
    <h3 style="margin-top:6px">Tipos de documento (Scopus)</h3>
    <table class="data-table">
      <tr><th>Tipo</th><th>Registros</th></tr>
      {''.join(f"<tr><td>{esc(k)}</td><td class='num'>{v:,}</td></tr>" for k, v in smeta['tipo_documento_facetas'].items())}
    </table>
  </div>
</div>
<p style="font-size:12.5px;color:#6b7280">Idioma en Scopus: {smeta['idioma_facetas']['English']:,} en inglés y {smeta['idioma_facetas']['Spanish']} en español ({esc(smeta['idioma_facetas']['nota'])}). Versiones para Web of Science y SciELO Citation Index en <a href="../../docs/cadenas_busqueda.md">docs/cadenas_busqueda.md</a>.</p>

<h2 id="prisma">2 · Flujo PRISMA</h2>
{img('fig01_prisma')}

<h2 id="cribado">2b · Cribado de elegibilidad</h2>
<p>Cada registro se evaluó con dos preguntas antes de la RSI: <b>¿invoca la interseccionalidad en sentido social?</b> (no "intersection" vial o como simple cruce de temas) y <b>¿su objeto es climático?</b> (no "clima" escolar u organizacional, ni desastres no climáticos). Se excluyeron <b>{cr_meta['excluidos']:,}</b> de {meta['a_cribado']:,}: {cr_meta['solo_no_interseccional']} por no invocar el marco, {cr_meta['solo_no_climatico']} por no ser climáticos y {cr_meta['ambos']} por ambas razones.</p>
<div class="grid-2">
  <div>
    <h3 style="margin-top:6px">Elegibilidad según la parte del ancla</h3>
    <table class="data-table"><tr><th>Entró por</th><th>n</th><th>% elegible</th></tr>{anchor_rows}</table>
  </div>
  <div>
    <h3 style="margin-top:6px">Elegibilidad según el tipo de documento</h3>
    <table class="data-table"><tr><th>Tipo</th><th>n</th><th>% elegible</th></tr>{dt_rows}</table>
  </div>
</div>
<details>
<summary>Diez exclusiones al azar, con su motivo</summary>
<table class="data-table"><tr><th>Título</th><th>Motivo</th></tr>{ejemplos_rows}</table>
</details>

<h2 id="rsi">3 · ¿Qué es la Rúbrica de Sustantividad Interseccional (RSI)?</h2>
<div class="theory-block">
  <p style="margin-top:0;"><b>Pregunta.</b> ¿En qué medida la investigación sobre cambio climático aplica la interseccionalidad de forma sustantiva, y en qué medida solo la menciona? La RSI traduce la crítica al uso nominal (Davis 2008; Bowleg 2012; Carbado et al. 2013) en una variable medible a escala de corpus.</p>
  <p><b>Procedimiento.</b> Primero un criterio de entrada (gate); si se supera, seis criterios (0 / 0.5 / 1) y un factor de integración. El total se normaliza a 0–4. En la v2 la RSI se aplica solo a los trabajos elegibles del cribado.</p>
  {CRITERIOS_TABLA}
  <p style="margin-bottom:6px;"><b>Interpretación del total:</b></p>
  <div>{''.join(f'<span class="chip" style="background:{CAT_COLOR[c]};color:{"#1f2937" if c in ("mencion_sin_aplicacion", "nominal_debil") else "#fff"}">{CAT_LABELS[c]}</span>' for c in CAT_ORDER)}</div>
  <p style="font-size:13px;color:#555;margin-bottom:0"><b>Independencia teórica:</b> la RSI evalúa la operacionalización del concepto, no la fidelidad a una autoría o región. Fundamentación completa: <a href="../../docs/rubrica_RSI_fundamentacion.md">rubrica_RSI_fundamentacion.md</a>.</p>
</div>

<h2 id="teoria">3b · Genealogía teórica de la interseccionalidad</h2>
{GENEALOGIA}

<h2 id="prompts">3c · Cómo se aplica (prompts)</h2>
<div class="flow-diagram">
  [Título + abstract + keywords + tipo de documento + idioma]<br>↓<br>
  <b>Cribado</b> → ¿invoca la interseccionalidad? · ¿objeto climático? · (si no: excluido con motivo)<br>↓<br>
  <b>Codificación</b> → tipo de estudio · amenaza · lugar del estudio<br>↓<br>
  <b>RSI v3</b> → gate + 6 criterios + integración + evidencia por criterio<br>↓<br>
  <b>Razonamiento</b> (~50 palabras) → JSON por registro, validado contra el esquema
</div>
<p>Una sola pasada por registro, aplicada por Claude (claude-opus-5-5) en lotes de 68, cada uno de forma independiente y sin acceso a la v1. Los pasos 1–3 aplican al pie de la letra la rúbrica <code>prompts/bowleg_eval_v3.md</code>.</p>
<details><summary><b>Prompt v2 — cribado, codificación y RSI</b> (prompts/v2_cribado_rsi.md)</summary><pre class="code-block">{load_prompt('prompts/v2_cribado_rsi.md')}</pre></details>
<details><summary><b>Rúbrica RSI v3</b> (prompts/bowleg_eval_v3.md)</summary><pre class="code-block">{load_prompt('prompts/bowleg_eval_v3.md')}</pre></details>
<details><summary><b>Reglas del razonamiento</b> (prompts/reasoning_v3.md)</summary><pre class="code-block">{load_prompt('prompts/reasoning_v3.md')}</pre></details>

<h2 id="nums">4 · Números clave</h2>
<div class="stat-grid">
  <div class="stat"><div class="stat-num">{meta['identificados_scopus']:,}</div><div class="stat-lbl">Registros identificados</div></div>
  <div class="stat"><div class="stat-num">{n:,}</div><div class="stat-lbl">Trabajos elegibles</div></div>
  <div class="stat"><div class="stat-num">{len(gp):,}</div><div class="stat-lbl">Pasan el gate</div></div>
  <div class="stat"><div class="stat-num">{int((f['bowleg_total'] >= 2.5).sum()):,}</div><div class="stat-lbl">RSI ≥ 2.5 (sustantiva)</div></div>
  <div class="stat"><div class="stat-num">{p_gate_fail:.0f}%</div><div class="stat-lbl">Mención sin aplicación (0)</div></div>
  <div class="stat"><div class="stat-num">{p_iv:.0f}%</div><div class="stat-lbl">Cumplen el criterio IV (con gate)</div></div>
</div>
<table class="data-table"><tr><th>Categoría RSI</th><th>n</th><th>%</th></tr>
{''.join(f"<tr><td>{CAT_LABELS[c]}</td><td class='num'>{int(cat_n.get(c, 0)):,}</td><td class='num'>{100 * cat_n.get(c, 0) / n:.1f}%</td></tr>" for c in CAT_ORDER)}
</table>

<h2 id="bowleg">5 · Distribución RSI</h2>
{img('fig02_distribucion')}
{insight(f"Entre los {n:,} trabajos elegibles, el <b>{p_gate_fail:.0f}%</b> no supera el criterio de entrada: invoca la interseccionalidad sin articular ejes de diferenciación relacionados. El <b>{p_sust:.0f}%</b> alcanza aplicación sustantiva (RSI ≥ 2.5). Como el cribado ya retiró lo que no era del tema, estas proporciones describen el uso del marco dentro de la literatura que efectivamente lo invoca.")}

<h2 id="anatomia">6 · Anatomía de la sustantividad</h2>
<h3>El embudo: de la mención a la aplicación</h3>
{img('figB_embudo')}
<h3>Perfil por criterio</h3>
{img('figA_criterios')}
{insight("Entre los trabajos que pasan el gate: " + ", ".join(f"{k.replace('bowleg_', '').replace('rsi_', '')} {v:.0f}%" for k, v in crit_pct.items()) + f" cumplen plenamente cada criterio (I a VI). El <b>criterio IV (método no aditivo)</b> es el más bajo ({crit_pct['bowleg_IV']:.0f}%): el campo teoriza la interseccionalidad mejor de lo que la opera en el diseño empírico.")}
<h3>¿Se articulan los criterios o se yuxtaponen?</h3>
<div class="grid-2">{img('figE_integracion')}{img('figD_coocurrencia')}</div>

<h2 id="metodo">6b · El método, según el tipo de estudio</h2>
<p>El criterio IV pregunta por el diseño empírico, así que no aplica igual a revisiones o ensayos conceptuales. La v2 codifica el tipo de estudio para separar ese efecto.</p>
{img('figG_metodo_por_tipo')}
{table(tipo_t, [('tipo', 'Tipo de estudio'), ('n', 'n'), ('bowleg_mean', 'RSI media'), ('pct_substantive', '% sustantivo'), ('n_gate', 'Pasan el gate'), ('pct_IV_cumple_gate', '% IV (con gate)')])}
{insight(f"Aun restringido a estudios empíricos, solo el <b>{p_iv_emp:.0f}%</b> de los que pasan el gate opera las intersecciones en el método. El eslabón débil no es un artefacto de incluir revisiones o ensayos.")}

<h2 id="anual">7 · Producción anual</h2>
{img('fig03_anios')}

<h2 id="topics">8 · Tópicos × RSI</h2>
{img('fig04_topicos')}
{insight(f"La sustantividad no se reparte de forma homogénea. Los tópicos (≥ 15 trabajos) con mayor RSI media son {tl}; los de menor, {ll}.")}

<h2 id="topicmap">8b · Mapa temático interactivo</h2>
<p>Los controles del panel (arriba a la derecha) colorean el mismo mapa por tópico, por nivel RSI del trabajo o por RSI media del vecindario, y permiten resaltar el sub-corpus de la tesis. <b>Hover</b> = metadata · <b>click</b> = panel con la justificación por criterio.</p>
<div style="width:100%;height:920px;margin:16px 0;border:1px solid #ddd;border-radius:6px;overflow:hidden;">
  <iframe src="mapa.html" width="100%" height="100%" style="border:none;" title="Mapa temático v2"></iframe>
</div>
<p style="font-size:12px;color:#666;"><a href="mapa.html" target="_blank">Abrir el mapa en pantalla completa</a></p>
<h3>Ranking de tópicos por RSI media</h3>
{img('figH_ranking_topicos')}
<details><summary><b>Radiografía por tópico</b> (RSI, % gate, % sustantivo, % en español, trabajos de la tesis)</summary>
<div style="overflow-x:auto;margin-top:10px">{ficha}</div></details>

<h2 id="amenazas">9 · Tipo de amenaza</h2>
{img('figI_amenazas')}
{table(am_t, [('amenaza_lbl', 'Amenaza'), ('n', 'n'), ('bowleg_mean', 'RSI media'), ('pct_substantive', '% sustantivo')])}
<p style="font-size:12px;color:#6b7280">Un trabajo puede tratar varias amenazas; por eso la suma supera el total.</p>

<h2 id="lang">10 · Idioma del documento</h2>
<div class="grid-2">{img('fig05_idioma')}{img('figF_idioma_puntos')}</div>
{table(lb_t, [('idioma_lbl', 'Idioma'), ('n', 'n'), ('bowleg_mean', 'RSI media'), ('pct_substantive', '% sustantivo')])}
{insight(lang_txt + "Con tan pocos trabajos en español en Scopus, la comparación por idioma no es concluyente: hace falta sumar bases con mejor cobertura iberoamericana (SciELO, Redalyc).")}

<h2 id="paises">11 · Geografía del rigor</h2>
<p>La v2 usa el <b>lugar donde se sitúa el estudio</b> (codificado en el cribado), no solo la afiliación de los autores.</p>
{img('fig06_lugares')}
{insight(lug_txt + "El rigor no sigue de forma simple al volumen de producción.")}
<details><summary>Tabla por lugar del estudio (25 con más trabajos)</summary>
{table(cb, [('country', 'Lugar'), ('n', 'n'), ('bowleg_mean', 'RSI media'), ('pct_substantive', '% sustantivo')], 25)}</details>
<details><summary>Tabla por país de afiliación (una vez por trabajo)</summary>
{table(ab, [('country', 'País'), ('n', 'n'), ('bowleg_mean', 'RSI media'), ('pct_substantive', '% sustantivo')], 25)}</details>

<h2 id="temporal">12 · Tendencia temporal</h2>
{img('fig07_tendencia')}
{insight(trend_txt + " El último año está incompleto.")}

<h2 id="casos">13 · Casos ejemplares</h2>
<p>Trabajos elegidos al azar dentro de cada nivel (entre los de confianza alta), con la evidencia textual que respalda cada criterio.</p>
{casos_html}

<h2 id="valid">14 · Validación</h2>
<div class="theory-block">
  <p style="margin-top:0;">La RSI de la v2 la aplicó <b>Claude (claude-opus-5-5)</b>, con el prompt versionado y la evidencia textual por criterio guardada para cada registro. Es un modelo distinto al usado en la v1, así que los valores no son directamente comparables entre pestañas.</p>
  <p style="margin-bottom:0;"><b>Pendiente:</b> codificación humana a ciegas de una submuestra estratificada para estimar la concordancia humano–modelo (κ). La herramienta está en <a href="validacion.html">validacion.html</a>. Hasta entonces, los puntajes son provisionales.</p>
</div>

<h2 id="daniel">15 · Sub-corpus de la tesis</h2>
<div class="daniel-box"><b>Tema de la tesis:</b> ciclones tropicales × cambio climático × interseccionalidad (género × clase × territorio) × medios de vida de mujeres y comunidades indígenas en costas de México. Se marcan los trabajos elegibles que combinan ≥ 2 de estos ejes en título o abstract.</div>
<div class="stat-grid">
  <div class="stat"><div class="stat-num">{ds['mexico_AND_cyclonic']}</div><div class="stat-lbl">México + ciclones</div></div>
  <div class="stat"><div class="stat-num">{ds['mexico_cyclonic_gender_or_indigenous']}</div><div class="stat-lbl">México + ciclones + género/indígena</div></div>
  <div class="stat"><div class="stat-num">{ds['coastal_AND_cyclonic']}</div><div class="stat-lbl">Costero + ciclones</div></div>
  <div class="stat"><div class="stat-num">{ds['relevant_ge2_axes']}</div><div class="stat-lbl">Sub-corpus (≥ 2 ejes)</div></div>
  <div class="stat"><div class="stat-num">{ds['relevant_substantive']}</div><div class="stat-lbl">De esos, RSI ≥ 2.5</div></div>
  <div class="stat"><div class="stat-num">{ds['relevant_bowleg_mean']:.2f}</div><div class="stat-lbl">RSI media del sub-corpus</div></div>
</div>
<table class="data-table"><tr><th>Eje temático</th><th>Trabajos</th></tr>
  <tr><td>México</td><td class="num">{ds['mexico']}</td></tr><tr><td>Ciclones / huracanes</td><td class="num">{ds['cyclonic']}</td></tr>
  <tr><td>Costero</td><td class="num">{ds['coastal']}</td></tr><tr><td>Indígena</td><td class="num">{ds['indigenous']}</td></tr>
  <tr><td>Mujeres / género</td><td class="num">{ds['gender_women']}</td></tr></table>
<details><summary>Listado del sub-corpus ({ds['relevant_ge2_axes']} trabajos, por RSI)</summary>
<table class="data-table"><tr><th>RSI</th><th>Título</th><th>Año · idioma</th><th>Acceso</th></tr>{sub_rows}</table></details>

<h2 id="sintesis">16 · Síntesis</h2>
<div class="theory-block">
  <p style="margin-top:0;"><b>Una búsqueda más limpia.</b> La cadena bilingüe con ancla teórica recupera {meta['identificados_scopus']:,} registros; el cribado deja {n:,} trabajos que efectivamente invocan la interseccionalidad en investigación climática.</p>
  <p><b>Adopción y aplicación.</b> Dentro de esa literatura, el {p_gate_fail:.0f}% no articula ejes (mención sin aplicación) y el {p_sust:.0f}% aplica el marco de forma sustantiva.</p>
  <p><b>El método sigue siendo el eslabón débil.</b> Solo el {p_iv:.0f}% de los que pasan el gate operan las intersecciones en el diseño (el {p_iv_emp:.0f}% entre los empíricos).</p>
  <p style="margin-bottom:0;"><b>Límites.</b> Puntajes provisionales (modelo de lenguaje, validación humana pendiente, evaluación sobre abstracts); una sola base; muy poca literatura en español indexada en Scopus.</p>
</div>

<h2 id="docs">17 · Documentos</h2>
<p>
  <a class="doc-link" href="../../docs/cadenas_busqueda.md">📋 Cadenas de búsqueda</a>
  <a class="doc-link" href="../../prompts/v2_cribado_rsi.md">⚙ Prompt v2</a>
  <a class="doc-link" href="../../data/v2_corpus_scored.csv">📊 Corpus elegible + puntajes (CSV)</a>
  <a class="doc-link" href="../../data/v2_cribado.csv">📊 Cribado completo (CSV)</a>
  <a class="doc-link" href="../../data/v2_daniel_subcorpus.csv">📊 Sub-corpus tesis (CSV)</a>
</p>

<h2 id="refs">18 · Referencias</h2>
{REFERENCIAS}

<p style="text-align:center;color:#9ca3af;font-size:12px;margin-top:56px;padding-top:20px;border-top:1px solid var(--line);">
Interseccionalidad y Cambio Climático · v2 · búsqueda ampliada · 2026</p>
</div>
</div>
{SCROLL_JS}
</body>
</html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(html)
    print(f"[OK] dashboard v2 → {OUT / 'index.html'} ({(OUT / 'index.html').stat().st_size / 1e6:.1f} MB)")


if __name__ == '__main__':
    main()
