#!/usr/bin/env python3
"""
12_dashboard.py — v3: réplica de pipeline/v2/12_dashboard.py con el corpus v3
(Scopus + SciELO con las cadenas trilingües, más OpenAlex en español y portugués).

Genera site/v3/index.html con la misma estructura, figuras y textos que la v2. Cambian los datos
(data/v3_*), la sección de estrategia de búsqueda (tres fuentes), el PRISMA y los textos sobre
idioma y sobre el origen de cada evaluación (v2 o v3).
"""
from __future__ import annotations
import pandas as pd
import json
import base64
from pathlib import Path

DATA = Path("data")
ASSETS = Path("assets")
DASHBOARD = Path("site/v3")
DASHBOARD.mkdir(exist_ok=True)


def img_b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def df_to_html_table(df: pd.DataFrame, max_rows: int = 20, cols: dict | None = None) -> str:
    """Tabla HTML; `cols` = {columna: encabezado en español} elige y renombra columnas."""
    if cols:
        df = df[list(cols)].rename(columns=cols)
    return df.head(max_rows).to_html(index=False, classes='data-table', float_format='%.2f', border=0)


COLS_TOPICO = {'topic_id_clean': '#', 'tópico': 'Tópico', 'n_papers': 'n',
               'bowleg_mean': 'RSI medio', 'pct_substantive': '% sustantivo'}
COLS_IDIOMA = {'idioma': 'Idioma', 'n': 'n', 'bowleg_mean': 'RSI medio', 'pct_gate': '% pasa el gate',
               'n_substantive': 'Sustantivos (≥ 2.5)', 'n_parcial': 'Parciales (1.5–2.0)',
               'n_nominal': 'Nominales o mención (≤ 1.0)', 'pct_substantive': '% sustantivo'}
COLS_PAIS = {'pais': 'País', 'n': 'n', 'bowleg_mean': 'RSI medio', 'n_substantive': 'Sustantivos (≥ 2.5)',
             'pct_substantive': '% sustantivo'}


CAT_LABELS = {
    'sustantivo_fuerte': 'Sustantiva fuerte (3.5–4.0)',
    'sustantivo': 'Sustantiva (2.5–3.0)',
    'parcial': 'Parcial (1.5–2.0)',
    'nominal_debil': 'Nominal/débil (0.5–1.0)',
    'mencion_sin_aplicacion': 'Mención sin aplicación (0)',
}


def main():
    stats = json.loads((DATA / 'v3_corpus_stats.json').read_text())
    scored = pd.read_csv(DATA / 'v3_corpus_scored.csv')
    topics_bw = pd.read_csv(DATA / 'v3_topics_x_bowleg.csv')
    lang_bw = pd.read_csv(DATA / 'v3_lang_x_bowleg.csv')
    country_bw = pd.read_csv(DATA / 'v3_country_x_bowleg.csv')

    # Inline images
    figs = {f"fig{n:02d}": img_b64(ASSETS / f"v3_fig{n:02d}_{name}.png")
            for n, name in [
                (1, 'prisma'), (2, 'bowleg_distribution'), (3, 'years'),
                (4, 'topics_x_bowleg'), (5, 'lang_x_bowleg'),
                (6, 'country_x_bowleg'), (7, 'year_trend'),
            ]}
    # Topic map estático (PNG) + interactivo (HTML embed)
    figs['fig09'] = img_b64(ASSETS / 'v3_fig09_topic_map.png')
    topic_map_embed = (ASSETS / 'v3_fig09_topic_map_embed.html').read_text()
    # Figuras explicativas del paper (A,B,D,E,F) + H (ranking de tópicos por RSI)
    for k, fn in [('figA','v3_figA_criterios.png'), ('figB','v3_figB_embudo.png'),
                  ('figD','v3_figD_cooc.png'), ('figE','v3_figE_integracion.png'),
                  ('figF','v3_figF_violin.png'), ('figH','v3_figH_topic_ranking.png')]:
        p = ASSETS / fn
        if p.exists(): figs[k] = img_b64(p)

    # Stats por tópico (radiografía: RSI, gate%, idioma, n, n_tesis) — del script 33
    topic_stats = {}
    if (DATA / 'v3_topic_stats.json').exists():
        topic_stats = json.loads((DATA / 'v3_topic_stats.json').read_text())
    # Casos ejemplares (tabla C)
    casos = json.loads((DATA / 'v3_casos_ejemplares.json').read_text()) if (DATA / 'v3_casos_ejemplares.json').exists() else []
    def _casos_html():
        rows = []
        for c in casos:
            sc = c['scores']
            sc_str = " · ".join(f"{k}={('—' if sc.get(k) is None else sc[k])}" for k in ['I','II','III','IV','V','VI'])
            evs = c['evidencias']
            ev_items = "".join(f"<li><b>{k}:</b> <i>{evs.get(k,'')}</i></li>" for k in ['I','II','III','IV','V','VI'] if evs.get(k))
            badge_color = {'Sustantiva fuerte':'#1b5e20','Parcial':'#ef6c00','Mención sin aplicación':'#5d4037'}.get(c['categoria'],'#555')
            ev_block = f"<ul style='margin:6px 0 0;padding-left:18px;font-size:12px;'>{ev_items}</ul>" if ev_items else f"<p style='font-size:12px;color:#888;margin:6px 0 0'>{c.get('gate_evidence','')}</p>"
            rows.append(
                f"<div style='border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0;background:var(--card)'>"
                f"<div style='display:flex;justify-content:space-between;align-items:start;gap:10px'>"
                f"<div style='font-weight:600;font-size:13.5px'>{c['titulo']}</div>"
                f"<span style='background:{badge_color};color:white;padding:3px 10px;border-radius:11px;font-size:11px;white-space:nowrap'>RSI {c['rsi_total']:.1f} · {c['categoria']}</span></div>"
                f"<div style='font-size:11px;color:#888;margin-top:3px'>{c['year']} · scores {sc_str}</div>"
                f"{ev_block}</div>")
        return "".join(rows)
    casos_html = _casos_html()

    # ── Radiografía por tópico (RSI, gate%, idioma, n, tesis) ──
    def _rsi_cell_color(v):
        if v is None or v <= 0: return '#bdbdbd'
        if v < 1.5:  return '#ffd166'
        if v < 2.5:  return '#f39c35'
        if v < 3.5:  return '#52b788'
        return '#1b6b3a'

    def _topic_ficha_html():
        if not topic_stats.get('topics'): return "<p>(stats por tópico no disponibles)</p>"
        rows = []
        for t in topic_stats['topics']:
            rsi = t['rsi_mean']; col = _rsi_cell_color(rsi)
            txtcol = '#fff' if (rsi == 0 or rsi >= 1.5) else '#5a4a00'
            # mini-barras de idioma
            def bar(pct, c):
                return (f"<span style='display:inline-block;height:9px;width:{max(pct*0.5,0):.0f}px;"
                        f"background:{c};vertical-align:middle;border-radius:2px;'></span>")
            lang_cell = (f"{bar(t['es_pct'],'#d32f2f')}{bar(t['en_pct'],'#9e9e9e')}{bar(t['pt_pct'],'#1976d2')}"
                         f"<span style='font-size:10px;color:#888;margin-left:5px'>ES {t['es_pct']:.0f}·PT {t['pt_pct']:.0f}·EN {t['en_pct']:.0f}</span>")
            tesis_cell = (f"<b style='color:#9c27b0'>{t['n_tesis']}</b>" if t['n_tesis'] > 0
                          else "<span style='color:#ccc'>0</span>")
            rows.append(
                f"<tr>"
                f"<td style='font-size:11px;color:#888'>T{t['topic_id']}</td>"
                f"<td style='font-size:12px'>{t['label']}</td>"
                f"<td style='text-align:center'>{t['n']}</td>"
                f"<td style='text-align:center'><span style='background:{col};color:{txtcol};"
                f"padding:2px 8px;border-radius:9px;font-size:11px;font-weight:600'>{rsi:.2f}</span></td>"
                f"<td style='text-align:center;font-size:11px'>{t['gate_pct']:.0f}%</td>"
                f"<td style='text-align:center;font-size:11px'>{t['sust_pct']:.0f}%</td>"
                f"<td style='white-space:nowrap'>{lang_cell}</td>"
                f"<td style='text-align:center'>{tesis_cell}</td>"
                f"</tr>")
        return (
            "<table class='data-table' style='font-size:12px'>"
            "<thead><tr>"
            "<th>#</th><th>Tópico</th><th>n</th><th>RSI medio</th>"
            "<th>% gate</th><th>% sust.</th><th>Idioma</th><th>Tesis</th>"
            "</tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")
    topic_ficha_html = _topic_ficha_html()

    # ── "Lectura del mapa": narrativa con los 4 hallazgos (datos reales) ──
    def _lectura_mapa_html():
        ts = topic_stats.get('topics', [])
        meta = topic_stats.get('meta', {})
        if not ts: return ""
        _ord = sorted([t for t in ts if t['n'] >= 10], key=lambda t: -t['rsi_mean'])
        top_names = ", ".join(f"<i>{t['label']}</i> ({t['rsi_mean']:.2f})" for t in _ord[:3])
        cero_names = ", ".join(f"<i>{t['label']}</i> ({t['rsi_mean']:.2f})" for t in _ord[-3:][::-1])
        # idioma: tópicos sustantivos anglófonos vs grandes hispanos nominales
        es_grandes = sorted([t for t in ts if t['n'] >= 20], key=lambda x: -x['es_pct'])[:2]
        es_txt = ", ".join(f"<i>{t['label']}</i> ({t['es_pct']:.0f}% ES, RSI {t['rsi_mean']:.2f})" for t in es_grandes)
        # tesis
        tesis_sorted = sorted([t for t in ts if t['n_tesis'] > 0], key=lambda x: -x['n_tesis'])[:4]
        tesis_txt = ", ".join(f"<i>{t['label']}</i> ({t['n_tesis']})" for t in tesis_sorted)
        n_disp = meta.get('n_topics_con_tesis', 0)
        return f"""
<div class="theory-block" style="border-left:4px solid #1a73e8">
  <h3 style="margin-top:0">Lo que revela el mapa</h3>
  <p style="font-size:13px;color:#555;margin-top:0">
    <b>Encuadre.</b> El universo no es «la literatura sobre cambio climático», sino la literatura que
    <b>invoca explícitamente la interseccionalidad</b> en torno al cambio climático o a eventos extremos
    (las búsquedas de la v3 exigen <code>intersectional*</code> / <code>interseccional*</code> / <code>intersecional*</code> —o frases como «intersection of race and gender»— junto a un término climático, y un cribado posterior excluye lo no pertinente). Por eso los
    hallazgos se leen <i>dentro</i> de ese corpus autoseleccionado por mención —lo que vuelve más
    contundente que aun así la mayoría no opere el concepto.
  </p>
  <ol style="font-size:13.5px;line-height:1.6;padding-left:20px">
    <li><b>La sustantividad se concentra topográficamente.</b> El RSI medio por tópico va de
      <b>{meta.get('rsi_min',0):.2f}</b> a <b>{meta.get('rsi_max',0):.2f}</b>: no se reparte al azar.
      Los vecindarios con mayor RSI medio son {top_names}. En el otro extremo están {cero_names}
      (tópicos de al menos 10 trabajos).</li>
    <li><b>Sin «trampas léxicas».</b> En la v3, el cribado ya retiró los registros donde «intersection»
      coincidía por otra razón (vialidad, cruce de temas): los tópicos de RSI baja reúnen trabajos pertinentes
      con un uso más nominal del marco.</li>
    <li><b>Idioma.</b> Aun sumando SciELO y OpenAlex en español y portugués, la literatura elegible sigue siendo
      sobre todo en inglés ({int((scored['idioma'] == 'es').sum())} en español y {int((scored['idioma'] == 'pt').sum())} en portugués). Los trabajos iberoamericanos ya tienen presencia
      en el mapa, pero una comparación por tradición lingüística todavía pide fuentes regionales (LILACS, La Referencia); Redalyc ya se verificó y no aporta registros nuevos.</li>
    <li><b>El nicho de la tesis no existe como cluster.</b> Los {stats.get('daniel_subcorpus', {}).get('relevant_ge2_axes', 0)} papers del sub-corpus de Daniel ({meta.get('n_tesis_total', 0)} con tópico asignado)
      (México × ciclones × interseccionalidad costera) se <b>dispersan en {n_disp} tópicos</b>
      —sobre todo {tesis_txt}—: el campo no tiene un vecindario propio para ese cruce. Esa fragmentación
      <b>es</b> el vacío que justifica la tesis. (Usa el botón «Resaltar sub-corpus de la tesis» en el mapa.)</li>
  </ol>
</div>"""
    lectura_mapa_html = _lectura_mapa_html()

    # ── Tabla de documentos del sub-corpus de Daniel (con links DOI) ──
    def _subcorpus_docs_html():
        p = DATA / 'v3_daniel_subcorpus.csv'
        if not p.exists(): return "<p>(sub-corpus no disponible)</p>"
        sub = pd.read_csv(p).sort_values('bowleg_total', ascending=False)
        def doi_link(d):
            d = '' if (d is None or (isinstance(d, float) and pd.isna(d))) else str(d).strip()
            if not d or d.lower() == 'nan': return '<span style="color:#bbb;font-size:11px">sin DOI</span>'
            url = d if d.startswith('http') else f'https://doi.org/{d}'
            return f'<a href="{url}" target="_blank" style="font-size:11px">abrir ↗</a>'
        def badge(v):
            if v >= 3.5: c = '#1b5e20'
            elif v >= 2.5: c = '#66bb6a'
            elif v >= 1.5: c = '#ffa726'
            else: c = '#bdbdbd'
            return f'<span style="background:{c};color:white;padding:1px 7px;border-radius:9px;font-size:11px;font-weight:600">{v:.1f}</span>'
        rows = []
        for _, r in sub.iterrows():
            try: yr = str(int(float(r.get('Year'))))
            except Exception: yr = '—'
            lang = str(r.get('idioma') or '').upper() or '—'
            rows.append(
                f"<tr><td>{badge(float(r.get('bowleg_total',0)))}</td>"
                f"<td style='font-size:12.5px'>{str(r.get('Title',''))[:130]}</td>"
                f"<td style='font-size:11px;color:#888'>{yr} · {lang}</td>"
                f"<td>{doi_link(r.get('DOI'))}</td></tr>")
        return ("<table class='data-table'><tr><th>RSI</th><th>Título</th><th>Año·Idioma</th><th>Acceso</th></tr>"
                + "".join(rows) + "</table>")
    subcorpus_docs_html = _subcorpus_docs_html()

    # Cargar prompts para sección de transparencia metodológica
    import html as _html
    def _load_prompt(path):
        p = Path(path)
        if not p.exists(): return '(prompt no encontrado)'
        txt = p.read_text()
        # quitar frontmatter
        if txt.startswith('---'):
            parts = txt.split('---', 2)
            if len(parts) >= 3: txt = parts[2].strip()
        return _html.escape(txt)
    prompt_scoring = _load_prompt('prompts/bowleg_eval_v3.md')
    prompt_reasoning = _load_prompt('prompts/reasoning_v3.md')
    prompt_v3 = _load_prompt('prompts/v3_cribado_rsi.md')

    # Top 20 tópicos sustantivos
    _labels = {t['topic_id']: t['label'] for t in topic_stats.get('topics', [])}
    topics_bw['tópico'] = [_labels.get(int(t), str(n).split('_', 1)[-1])
                           for t, n in zip(topics_bw['topic_id_clean'], topics_bw['topic_name'])]
    topics_substantive = topics_bw[topics_bw['topic_id_clean'] >= 0].nlargest(15, 'pct_substantive')
    topics_artifact = topics_bw[(topics_bw['topic_id_clean'] >= 0)].nsmallest(10, 'bowleg_mean')

    cat_dist = scored['categoria_bowleg'].value_counts()
    cat_pct = (cat_dist / len(scored) * 100).round(1)

    # ── Métricas para las cajas de inferencia ("Lectura del dato") ──
    n_tot = len(scored)
    pct_gate_fail = round(100 * (scored['bowleg_total'] == 0).sum() / n_tot)
    pct_sust = round(100 * (scored['bowleg_total'] >= 2.5).sum() / n_tot)
    # % que cumple el criterio IV (método) entre los que pasan el gate
    try:
        _gp = scored[scored['gate_pass'] == True] if 'gate_pass' in scored.columns else scored[scored['bowleg_total'] > 0]
        pct_metodo_gate = round(100 * (_gp['bowleg_IV'] == 1).sum() / max(len(_gp), 1))
        n_gate = len(_gp)
    except Exception:
        pct_metodo_gate, n_gate = 0, 0
    # Topics
    _t = topics_bw[topics_bw['topic_id_clean'] >= 0]
    _t = _t[_t['n_papers'] >= 15]
    top3 = list(_t.nlargest(3, 'pct_substantive')['tópico'])
    art3 = list(_t.nsmallest(3, 'bowleg_mean')['tópico'])
    # Idioma
    lang_col = lang_bw.columns[0]
    lr = {str(r[lang_col]): r for _, r in lang_bw.iterrows()}
    en_p, es_p, pt_p = (lr[k]['pct_substantive'] if k in lr else None for k in ('Inglés', 'Español', 'Portugués'))
    # Países
    cb = country_bw[country_bw['n'] >= 15].sort_values('pct_substantive', ascending=False)
    pais_top = cb.head(1).iloc[0] if len(cb) else None
    # Sub-corpus Daniel
    ds = stats.get('daniel_subcorpus', {})

    _gpc = (lambda c: round(100 * (_gp[c] == 1).mean()) if len(_gp) else 0)
    c_I, c_II, c_III, c_IV, c_V, c_VI = (_gpc(c) for c in ['bowleg_I', 'bowleg_II', 'bowleg_III', 'bowleg_IV', 'rsi_V', 'rsi_VI'])
    _emp = _gp[_gp['tipo_estudio'].astype(str).str.startswith('empirico')]
    c_IV_emp = round(100 * (_emp['bowleg_IV'] == 1).mean()) if len(_emp) else 0
    tesis_mayoria = ('la mayoría de los trabajos la invocan' if pct_gate_fail > 50
                     else f'una parte sustancial de los trabajos ({pct_gate_fail}%) la invoca')
    n_es = int((scored['idioma'] == 'es').sum())
    n_en = int((scored['idioma'] == 'en').sum())
    n_pt = int((scored['idioma'] == 'pt').sum())
    n_reut = int((scored['origen_evaluacion'] == 'v2').sum())       # evaluación tomada de la v2
    n_oa = int((scored['_source'] == 'openalex').sum())              # elegibles que solo trajo OpenAlex
    _cr = pd.read_csv(DATA / 'v3_cribado.csv')
    reg_origen = _cr['origen_evaluacion'].value_counts().to_dict()
    oameta = json.loads((DATA / 'v3_openalex_meta.json').read_text())
    rdmeta = json.loads((DATA / 'v3_redalyc_meta.json').read_text())
    oaq = json.loads((DATA / 'v3_query_openalex.json').read_text())
    query_oa = _html.escape(
        'filter=title_and_abstract.search:' + '|'.join(oaq['interseccional']) +
        ',\n       title_and_abstract.search:' + '|'.join(oaq['clima']) +
        f",\n       language:{'|'.join(oaq['idiomas'])},publication_year:>{oaq['anio_minimo'] - 1}")
    _new = scored[scored['_source'] == 'openalex']
    n_oa_es, n_oa_pt = int((_new['idioma'] == 'es').sum()), int((_new['idioma'] == 'pt').sum())
    rsi_media_corpus = float(scored['bowleg_total'].mean())
    _ts = [t for t in topic_stats.get('topics', []) if t['n'] >= 15]
    top_topicos_txt = ', '.join(t['label'] for t in sorted(_ts, key=lambda t: -t['rsi_mean'])[:3]) or 'tópicos concretos'
    _mx = ds.get('mexico_AND_cyclonic', 0)
    tesis_cruce_txt = ('no aparece ningún trabajo que cruce México y ciclones' if _mx == 0
                       else 'solo un trabajo cruza México y ciclones' if _mx == 1
                       else f'solo {_mx} trabajos cruzan México y ciclones')
    query_scopus = _html.escape((DATA / 'v3_query_scopus.txt').read_text().strip())
    query_scielo = _html.escape((DATA / 'v3_query_scielo.txt').read_text().strip())
    smeta = json.loads((DATA / 'v3_search_meta.json').read_text())
    smeta['fecha_busqueda'] = smeta['fecha']
    pmeta = json.loads((DATA / 'v3_prisma_meta.json').read_text())
    oimeta = pmeta.get('openalex_otra_etiqueta_idioma', {}) or {}          # ES/PT con otra etiqueta en OpenAlex
    oiraw = json.loads((DATA / 'v3_openalex_idioma_meta.json').read_text()) if (DATA / 'v3_openalex_idioma_meta.json').exists() else {}
    n_oa_principal = pmeta['openalex_nuevos'] - oimeta.get('nuevos', 0)
    vmeta = json.loads((DATA / 'v3_validation_sample.json').read_text())['meta']

    def insight(label, body):
        return f'<div class="insight"><span class="lbl">{label}</span>{body}</div>'

    ins_bowleg = insight("Lectura del dato",
        f"El <b>{pct_gate_fail}%</b> del corpus no supera el criterio de entrada: invoca la "
        f"interseccionalidad sin articular ejes de diferenciación relacionados. Solo el <b>{pct_sust}%</b> "
        f"alcanza aplicación sustantiva (RSI ≥ 2.5). La forma <b>bimodal</b> sugiere que la "
        f"interseccionalidad, cuando se aplica, tiende a aplicarse con cierta profundidad —pero ese "
        f"caso es minoritario. El patrón es consistente con la hipótesis de un uso predominantemente "
        f"nominal del marco en el campo.")

    ins_topics = insight("Lectura del dato",
        f"La sustantividad <b>no se distribuye de forma homogénea entre temas</b>. Se concentra en tópicos "
        f"anclados en poblaciones y territorios concretos (p. ej. {', '.join(top3[:3])}), donde el contexto "
        f"situado y las identidades entrelazadas emergen naturalmente. En cambio, "
        f"{', '.join(art3[:3])} tienen la menor RSI media (tópicos de al menos 15 trabajos): tratan la desigualdad de forma más genérica "
        f"(el cribado de la v3 ya retiró los falsos positivos de la búsqueda). La interseccionalidad sustantiva "
        f"parece requerir un <b>anclaje empírico situado</b>.")

    ins_topicmap = insight("Lectura del dato",
        "La proximidad espacial agrupa trabajos que comparten vocabulario y enfoque. Los clústeres "
        "densos centrales tienden a ser literatura genérica; los clústeres periféricos bien definidos "
        "—desastres concretos, pueblos indígenas, género y agricultura— son los que concentran "
        "aplicación sustantiva. El mapa permite, así, <b>localizar visualmente dónde el campo es más "
        "riguroso</b> y dónde solo nominal.")

    ins_lang = insight("Lectura del dato",
        f"En la v3 hay <b>{n_es}</b> trabajos elegibles en español y <b>{n_pt}</b> en portugués, frente a {n_en:,} "
        f"en inglés. OpenAlex aportó {n_oa_es} en español y {n_oa_pt} en portugués que no estaban en Scopus ni en SciELO "
        f"(muchos son tesis y capítulos de libro). La aplicación sustantiva es más frecuente en inglés "
        f"(<b>{en_p:.0f}%</b>) que en portugués ({pt_p:.0f}%) y en español ({es_p:.0f}%), y el español también "
        f"pasa menos el gate ({lr['Español']['pct_gate']:.0f}% frente a {lr['Inglés']['pct_gate']:.0f}% en inglés). "
        f"La comparación <b>sigue siendo exploratoria</b>: hay pocos trabajos en español y portugués, muchos son tesis y "
        f"capítulos (con resúmenes de otro formato), OpenAlex asigna el idioma por el título y su cobertura de "
        f"repositorios iberoamericanos es parcial.")

    _pais_txt = (f"<b>{pais_top['pais']}</b> ({pais_top['pct_substantive']:.0f}% sustantivo, n={int(pais_top['n'])}) "
                 if pais_top is not None else "")
    ins_anatomia = insight("Lectura del dato",
        f"El hallazgo más relevante está en el panel derecho (solo papers que pasan el gate): el <b>Criterio IV — método "
        f"no aditivo</b> es el eslabón débil. Mientras el poder estructural (II) llega al {c_II}% y la praxis (V) al {c_V}%, "
        f"solo el <b>{c_IV}%</b> operacionaliza metodológicamente las intersecciones ({c_IV_emp}% entre los estudios empíricos). "
        f"Es decir: el campo <b>teoriza</b> la interseccionalidad mejor de lo que la <b>opera empíricamente</b>. "
        f"La agencia (VI) llega al {c_VI}%. El uso no es solo nominal vs sustantivo: incluso en los trabajos sustantivos, "
        f"la traducción del marco en diseño metodológico es la asignatura pendiente.")

    ins_paises = insight("Lectura del dato",
        f"El rigor en la aplicación del marco {('encabezado por ' + _pais_txt) if _pais_txt else ''}"
        f"no se correlaciona de forma simple con el volumen de producción: países con muchos trabajos "
        f"no necesariamente lideran en sustantividad. Esto sugiere que la aplicación rigurosa depende "
        f"más de <b>tradiciones disciplinares y comunidades de investigación específicas</b> que del "
        f"volumen nacional de publicación.")

    ins_temporal = insight("Lectura del dato",
        "La producción crece de forma sostenida, pero la proporción de aplicación sustantiva "
        "<b>no aumenta de manera clara con el tiempo</b>: el campo se expande en volumen sin que la "
        "calidad de la aplicación interseccional mejore proporcionalmente. La difusión del término "
        "parece haber corrido más rápido que la consolidación de su uso analítico.")

    ins_daniel = insight("Lectura del dato",
        f"El nicho temático específico de la tesis —ciclones tropicales × México × género/indigeneidad— "
        f"es <b>muy reducido</b>: {tesis_cruce_txt}. Sin embargo, el sub-corpus ampliado (≥2 ejes temáticos, n={ds.get('relevant_ge2_axes','?')}) "
        f"tiene una RSI media de <b>{ds.get('relevant_bowleg_mean',0):.1f}</b>, "
        f"{'muy por encima' if ds.get('relevant_bowleg_mean', 0) > 1.3 * rsi_media_corpus else 'por encima'} del "
        f"promedio del corpus ({rsi_media_corpus:.2f}): los trabajos que combinan estos ejes <b>tienden a ser de los más "
        f"sustantivos</b>. Hay, por tanto, un vacío de literatura específica que la tesis puede ocupar, "
        f"apoyándose en un núcleo metodológicamente sólido.")

    # Sidebar de navegación agrupado
    sidebar = """
    <aside class="sidebar">
      <div class="sidebar-brand">Interseccionalidad<span>y cambio climático</span></div>
      <nav class="sidebar-nav">
        <div class="nav-group">Marco</div>
        <a href="#rsi">Qué es la RSI</a>
        <a href="#teoria">Genealogía teórica</a>
        <a href="#prompts">Aplicación con IA</a>
        <div class="nav-group">Corpus</div>
        <a href="#nums">Números clave</a>
        <a href="#prisma">Flujo PRISMA</a>
        <a href="#busqueda">Cadenas de búsqueda</a>
        <div class="nav-group">Hallazgos</div>
        <a href="#bowleg">Distribución RSI</a>
        <a href="#anatomia">Anatomía de la RSI</a>
        <a href="#topics">Tópicos</a>
        <a href="#topicmap">Mapa interactivo</a>
        <a href="#lang">Idiomas</a>
        <a href="#paises">Geografía</a>
        <a href="#temporal">Tendencia temporal</a>
        <div class="nav-group">Método</div>
        <a href="#casos">Casos ejemplares</a>
        <a href="#valid">Validación</a>
        <a href="#daniel">Sub-corpus Daniel</a>
        <div class="nav-group">Cierre</div>
        <a href="#sintesis">Síntesis y discusión</a>
        <a href="#docs">Documentos</a>
        <a href="#refs">Referencias</a>
        <div class="nav-group">Herramientas</div>
        <a href="validacion.html" class="nav-tool">✓ Validar la rúbrica</a>
        <a href="corpus.html" class="nav-tool nav-tool-alt">☰ Lista completa del corpus</a>
      </nav>
    </aside>
    """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Interseccionalidad y Cambio Climático · v3 · Rúbrica de Sustantividad Interseccional</title>
<style>
  :root {{
    --accent: #2563eb; --accent-dark: #1e40af; --ink: #1f2937; --muted: #6b7280;
    --line: #e5e7eb; --bg: #f8fafc; --card: #ffffff;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    margin: 0; color: var(--ink); background: var(--bg); line-height: 1.65; }}
  /* Prosa narrativa: registro compacto (≈ "En síntesis"). Los bloques con
     font-size inline conservan su tamaño; solo afecta a la prosa sin estilar. */
  .main p, .main li {{ font-size: 13.5px; }}

  /* Layout 2 columnas */
  .layout {{ display: flex; align-items: flex-start; }}
  .sidebar {{ position: sticky; top: 0; height: 100vh; width: 248px; flex-shrink: 0;
    background: #0f172a; color: #cbd5e1; overflow-y: auto; padding: 22px 0; }}
  .sidebar-brand {{ font-size: 18px; font-weight: 800; color: #fff; padding: 0 22px 18px;
    letter-spacing: 0.5px; border-bottom: 1px solid #1e293b; margin-bottom: 10px; }}
  .sidebar-brand span {{ display: block; font-size: 11px; font-weight: 500; color: #64748b;
    letter-spacing: 1.5px; text-transform: uppercase; margin-top: 3px; }}
  .sidebar-nav {{ display: flex; flex-direction: column; }}
  .nav-group {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px;
    color: #475569; padding: 16px 22px 5px; }}
  .sidebar-nav a {{ color: #cbd5e1; text-decoration: none; font-size: 13.5px; padding: 7px 22px;
    border-left: 3px solid transparent; transition: all .12s; }}
  .sidebar-nav a:hover {{ background: #1e293b; color: #fff; }}
  .sidebar-nav a.active {{ background: #1e293b; color: #fff; border-left-color: var(--accent); font-weight: 600; }}
  .sidebar-nav a.nav-tool {{ margin: 6px 14px 0; background: #1d4ed8; color: #fff; border-radius: 7px;
    font-weight: 600; text-align: center; border-left: none; padding: 9px 12px; }}
  .sidebar-nav a.nav-tool:hover {{ background: #2563eb; }}
  .sidebar-nav a.nav-tool-alt {{ background: #334155; }}
  .sidebar-nav a.nav-tool-alt:hover {{ background: #475569; }}

  .main {{ flex: 1; max-width: 980px; margin: 0 auto; padding: 0 40px 80px; min-width: 0; }}
  .topbar {{ padding: 30px 0 18px; border-bottom: 1px solid var(--line); margin-bottom: 8px; }}
  .topbar h1 {{ font-size: 23px; font-weight: 800; color: var(--ink); margin: 0 0 6px; }}
  .topbar p {{ color: var(--muted); font-size: 14px; margin: 0; }}

  h2 {{ font-size: 18px; font-weight: 700; color: var(--ink); margin: 44px 0 14px;
    scroll-margin-top: 20px; padding-bottom: 8px; border-bottom: 2px solid var(--line); }}
  h3 {{ font-size: 15px; color: #374151; margin-top: 24px; }}

  .caveat {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px 18px;
    margin: 18px 0; font-size: 13.5px; border-radius: 0 8px 8px 0; }}
  .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin: 18px 0; }}
  .stat {{ background: var(--card); border: 1px solid var(--line); padding: 18px 14px;
    border-radius: 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.04); }}
  .stat-num {{ font-size: 25px; font-weight: 800; color: var(--accent); line-height: 1; }}
  .stat-lbl {{ font-size: 12px; color: var(--muted); margin-top: 8px; }}
  .data-table {{ border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 13px;
    background: var(--card); border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.04); }}
  .data-table th {{ background: #f1f5f9; color: #334155; padding: 10px; text-align: left; font-weight: 600;
    border-bottom: 2px solid var(--line); }}
  .data-table td {{ padding: 8px 10px; border-bottom: 1px solid #f1f5f9; }}
  .data-table tr:hover {{ background: #f8fafc; }}
  pre.code-block {{ background: #0f172a; color: #e2e8f0; padding: 18px; border-radius: 10px;
    overflow-x: auto; font-size: 12px; line-height: 1.6; font-family: 'SF Mono', Menlo, monospace;
    white-space: pre-wrap; word-wrap: break-word; max-height: 460px; }}
  .theory-block {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: 20px 24px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,.04); }}
  .flow-diagram {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 18px;
    margin: 16px 0; font-family: 'SF Mono', Menlo, monospace; font-size: 12.5px; text-align: center; }}
  img {{ max-width: 100%; border: 1px solid var(--line); border-radius: 10px; margin: 10px 0; }}
  details {{ background: var(--card); border: 1px solid var(--line); padding: 14px 18px;
    border-radius: 10px; margin: 14px 0; }}
  details summary {{ font-weight: 600; cursor: pointer; color: var(--accent-dark); }}
  .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }}
  .badge-prov {{ background: #fef3c7; color: #b45309; }}
  .doc-link {{ display: inline-block; background: var(--accent); color: #fff !important; padding: 9px 16px;
    border-radius: 8px; text-decoration: none; margin: 6px 6px 6px 0; font-size: 13px; font-weight: 500; }}
  .doc-link:hover {{ background: var(--accent-dark); }}
  .daniel-box {{ background: #faf5ff; border-left: 4px solid #9333ea; padding: 18px;
    border-radius: 0 10px 10px 0; margin: 18px 0; }}
  .insight {{ background: #f0f7f4; border-left: 4px solid #10b981; padding: 14px 18px;
    margin: 16px 0; border-radius: 0 8px 8px 0; font-size: 13.5px; line-height: 1.6; }}
  .insight .lbl {{ display: block; font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: #059669; margin-bottom: 6px; }}
  a {{ color: var(--accent); }}
  /* Pestañas de versión (v1 / v2 / v3) */
  .version-tabs {{ display: flex; gap: 6px; padding-top: 18px; border-bottom: 1px solid var(--line); }}
  .version-tabs a {{ padding: 8px 16px; border: 1px solid var(--line); border-bottom: none;
    border-radius: 8px 8px 0 0; text-decoration: none; color: var(--muted); font-size: 13px;
    font-weight: 600; background: #f1f5f9; margin-bottom: -1px; }}
  .version-tabs a span {{ font-weight: 400; font-size: 11.5px; margin-left: 6px; }}
  .version-tabs a.active {{ background: var(--bg); color: var(--ink); border-bottom: 1px solid var(--bg); }}
  @media (max-width: 860px) {{
    .sidebar {{ display: none; }} .main {{ padding: 0 20px 60px; }}
  }}
</style>
</head>
<body>
<div class="layout">
{sidebar}
<div class="main">

<nav class="version-tabs" aria-label="Versión del corpus">
  <a href="../index.html">v1 · corpus original<span>mayo 2026</span></a>
  <a href="../v2/index.html">v2 · búsqueda ampliada<span>septiembre 2026</span></a>
  <a href="index.html" class="active">v3 · Scopus + SciELO + OpenAlex<span>{n_tot:,} trabajos · noviembre 2026</span></a>
</nav>

<div class="topbar">
  <h1>Interseccionalidad y Cambio Climático</h1>
  <p>¿Aplicación sustantiva o invocación nominal? · {n_tot:,} trabajos elegibles (Scopus + SciELO + OpenAlex ES/PT · búsqueda del {smeta['fecha_busqueda']}) medidos con la Rúbrica de Sustantividad Interseccional · <span class="badge badge-prov">scoring provisional</span></p>
</div>

<div class="caveat">
  <strong>⚠ Nota:</strong> los puntajes RSI fueron generados con un modelo de lenguaje (<strong>Claude · claude-opus-5-5</strong>), después de un cribado de elegibilidad.
  Son <strong>provisionales</strong> hasta completar la validación humana sobre una submuestra (ver §10).
  El procedimiento es transparente y auditable: prompt versionado y evidencia textual por criterio.<br>
  <strong>Comparación con la v2:</strong> misma rúbrica, mismo modelo y mismas reglas. Cambia la búsqueda: cadenas con
  vocabulario en portugués y un bloque climático más amplio, en Scopus y SciELO, más los trabajos en español y portugués que
  OpenAlex encuentra con las mismas cadenas. {n_reut:,} de los {n_tot:,} trabajos elegibles conservan la evaluación que
  recibieron en la v2 (mismo resumen); el resto se evaluó en la v3 ({n_oa} de ellos solo están en OpenAlex).
  Con la v1 cambian además el modelo (gpt-4.1 → Claude) y las reglas del gate y de los criterios I y IV.
</div>

<div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);color:white;border-radius:12px;padding:22px 26px;margin:20px 0;">
  <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;opacity:.8;margin-bottom:8px;">Tesis</div>
  <p style="font-size:16.5px;line-height:1.55;margin:0;font-weight:500;">
    En los estudios sobre cambio climático, la interseccionalidad funciona como un <strong>significante ampliamente adoptado pero débilmente operacionalizado</strong>: {tesis_mayoria} sin articular ejes de diferenciación, y aun quienes lo hacen rara vez la traducen en diseño metodológico. La aplicación rigurosa <strong>no es una propiedad del campo, sino un fenómeno de nicho.</strong>
  </p>
</div>

<div style="background:#f0f7f4;border:1px solid #c4e0c4;border-radius:12px;padding:18px 22px;margin:18px 0;">
  <div style="font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#059669;margin-bottom:10px;">En síntesis</div>
  <ul style="margin:0;padding-left:20px;line-height:1.7;font-size:13.5px;">
    <li><b>Pregunta.</b> ¿En qué medida el campo aplica la interseccionalidad de forma sustantiva y en qué medida solo la menciona?</li>
    <li><b>Instrumento.</b> Rúbrica de Sustantividad Interseccional (RSI): un criterio de entrada + 6 criterios + factor de integración, aplicada con un modelo de lenguaje a los {n_tot} trabajos del corpus.</li>
    <li><b>Adopción ≠ aplicación.</b> El <b>{pct_gate_fail}%</b> invoca el marco sin articular ejes de diferenciación; solo el <b>{pct_sust}%</b> alcanza aplicación sustantiva.</li>
    <li><b>El eslabón débil es el método.</b> Entre los trabajos que sí aplican el marco, solo el <b>{pct_metodo_gate}%</b> lo traduce en diseño metodológico (criterio IV): el campo teoriza mejor de lo que opera.</li>
    <li><b>El rigor es de nicho.</b> La sustantividad se concentra en comunidades temáticas concretas (p. ej. {top_topicos_txt}), no se distribuye de forma pareja.</li>
    <li><b>Para la tesis.</b> En el corpus v3 {tesis_cruce_txt}; los {ds.get('relevant_ge2_axes', 0)} trabajos que combinan ≥ 2 ejes de la tesis tienen una RSI media de {ds.get('relevant_bowleg_mean', 0):.2f}, frente a {rsi_media_corpus:.2f} del corpus: un vacío temático con piso metodológico.</li>
  </ul>
</div>

<h2 id="rsi">0 · ¿Qué es la Rúbrica de Sustantividad Interseccional (RSI)?</h2>

<div style="background:#f3f6fc;border:1px solid #c7d6f0;border-radius:8px;padding:18px 22px;margin:16px 0;line-height:1.7;">
  <p style="margin-top:0;"><strong>Planteamiento.</strong> El cambio climático y sus eventos extremos no producen efectos homogéneos: la exposición, la capacidad de respuesta y la agencia se distribuyen de manera desigual según posiciones sociales que operan de forma simultánea —género, clase, raza, etnicidad, territorio. La interseccionalidad, formulada por Crenshaw (1989), constituye el marco analítico de referencia para examinar esta desigualdad como producto de sistemas de poder entrelazados, y no como la mera suma de vulnerabilidades aisladas.</p>

  <p><strong>El problema.</strong> La amplia difusión del concepto trajo consigo un riesgo que la propia literatura crítica ha diagnosticado: su invocación <strong>nominal</strong>: el término se cita como gesto de actualización teórica sin que el análisis empírico opere con sus principios. Davis (2008) lo caracterizó como <em>buzzword</em>; Bowleg (2012) denunció el uso aditivo que traiciona su lógica relacional; Carbado et al. (2013) señalaron los trabajos que lo citan sin movilizarlo analíticamente.</p>

  <p><strong>Pregunta e instrumento.</strong> De allí la pregunta que organiza este trabajo: <em>¿en qué medida el campo aplica la interseccionalidad de forma sustantiva, y en qué medida solo la menciona?</em> Para responderla a escala de corpus, esta investigación propone la <strong>Rúbrica de Sustantividad Interseccional (RSI)</strong>, que traduce la crítica —hasta ahora ejercida caso por caso— en una variable medible. En la v3, un cribado de elegibilidad previo descarta lo que no es del tema (por ejemplo «intersection» en sentido vial o «clima» escolar); sobre el corpus elegible, la <em>distribución</em> de los puntajes constituye el hallazgo central.</p>

  <p style="margin-bottom:6px;"><strong>Procedimiento.</strong> La RSI aplica primero un <b>criterio de entrada (gate)</b>: solo si el trabajo articula dos o más ejes de diferenciación social como <em>relacionados entre sí</em> —y no meramente mencionados por separado— se procede a evaluar los seis criterios. Esto evita que un trabajo acumule puntaje por contexto o método sin tratar realmente las identidades entrelazadas.</p>
  <table class="data-table" style="margin-top:4px;">
    <tr><th>Criterio</th><th>Pregunta diagnóstica</th><th>Señales textuales que el modelo busca</th><th>Ejemplo de aplicación sustantiva</th></tr>
    <tr>
      <td><b>I — Identidades entrelazadas</b><br><span style="font-size:11px;color:#888">Crenshaw 1989; Bowleg 2012</span></td>
      <td>¿Trata ≥2 ejes como mutuamente constitutivos, no aditivos?</td>
      <td style="font-size:12px;color:#444"><b>Sí:</b> "co-constituyen", "mutuamente", "simultaneidad", "no aditivo", "interlocking", categorías <em>combinadas</em> ("mujeres indígenas mayores"). <b>No:</b> ejes unidos por "y" sin relación; variables de control independientes.</td>
      <td style="font-style:italic;color:#555">"Ser mujer indígena ante el huracán no es 'mujer' + 'indígena': es una posición distinta a la de una mujer mestiza urbana."</td>
    </tr>
    <tr>
      <td><b>II — Poder estructural</b><br><span style="font-size:11px;color:#888">Collins 2000; Crenshaw 1991</span></td>
      <td>¿Articula estructuras (racismo, patriarcado, colonialismo) y no rasgos individuales?</td>
      <td style="font-size:12px;color:#444"><b>Sí:</b> "racismo/patriarcado/colonialismo estructural", "colonialidad", "despojo", "racialización", mecanismos nombrados (redlining, racismo ambiental). <b>No:</b> "factores culturales", "diferencias individuales", "conductas".</td>
      <td style="font-style:italic;color:#555">"La mayor exposición no se debe a 'falta de preparación' sino al despojo territorial colonial que empujó a estas comunidades a zonas de riesgo."</td>
    </tr>
    <tr>
      <td><b>III — Contexto situado</b><br><span style="font-size:11px;color:#888">McCall 2005</span></td>
      <td>¿Sitúa los hallazgos en historia/geografía/política específicas?</td>
      <td style="font-size:12px;color:#444"><b>Sí:</b> lugar geográfico concreto, periodo histórico, políticas locales nombradas, "en el contexto de [evento/región]", reconoce no-universalidad. <b>No:</b> "las mujeres" en abstracto; generalizaciones globales sin anclaje.</td>
      <td style="font-style:italic;color:#555">"En la costa de Oaxaca, tras el huracán de 1997 y la reforma agraria de…, las relaciones de género se reconfiguraron de modo específico."</td>
    </tr>
    <tr>
      <td><b>IV — Método no aditivo</b><br><span style="font-size:11px;color:#888">Hancock 2007; Else-Quest & Hyde 2016</span></td>
      <td>¿El diseño empírico capta interacciones (muestreo, codificación cruzada)?</td>
      <td style="font-size:12px;color:#444"><b>Sí:</b> "muestreo intencional", "término de interacción X×Y", "codificación cruzada", subgrupos definidos por intersección, análisis cualitativo de identidades entrelazadas. <b>No:</b> "variables independientes", "controlamos por", regresión sin interacciones; solo revisión teórica.</td>
      <td style="font-style:italic;color:#555">Muestreo intencional de "mujeres indígenas pescadoras" como categoría combinada; codificación que cruza ejes en lugar de analizarlos por separado.</td>
    </tr>
    <tr>
      <td><b>V — Praxis y justicia</b><br><span style="font-size:11px;color:#888">Collins & Bilge 2016</span></td>
      <td>¿Se orienta a transformar desigualdades, no solo a describirlas?</td>
      <td style="font-size:12px;color:#444"><b>Sí:</b> "justicia climática/social", "transformación", "recomendaciones de política", "empoderamiento", "implicaciones para la acción", investigación participativa. <b>No:</b> estudio puramente descriptivo, sin dimensión normativa o de cambio.</td>
      <td style="font-style:italic;color:#555">El estudio deriva recomendaciones de política de adaptación con y para las comunidades, no solo describe su vulnerabilidad.</td>
    </tr>
    <tr>
      <td><b>VI — Agencia y resistencia</b><br><span style="font-size:11px;color:#888">Collins 2000; feminismos del Sur</span></td>
      <td>¿Reconoce a los sujetos como agentes, no solo como víctimas pasivas?</td>
      <td style="font-size:12px;color:#444"><b>Sí:</b> "estrategias de", "resistencia", "agencia", "saberes/conocimiento local", "respuestas comunitarias", "adaptación liderada por". <b>No:</b> sujetos solo como "víctimas/afectados"; enfoque exclusivo en pérdidas y daño.</td>
      <td style="font-style:italic;color:#555">Documenta las estrategias y saberes propios de las mujeres para anticipar y enfrentar el ciclón, no solo sus pérdidas.</td>
    </tr>
  </table>
  <p style="font-size:11.5px;color:#888;margin-top:6px;">Las "señales" son <em>orientativas</em>: el modelo evalúa el sentido del texto, no coincidencias literales. Se incluyen para transparencia sobre qué indica el cumplimiento de cada criterio. La fuente teórica de cada criterio aparece bajo su nombre.</p>
  <p style="font-size:13px;color:#555;margin-top:4px;">Un <b>factor de integración</b> ajusta el total según si los criterios se <em>articulan</em> en un análisis coherente o se yuxtaponen: la interseccionalidad es, ante todo, integración. El puntaje se normaliza a una escala 0–4 para su interpretación.</p>

  <p style="margin-bottom:6px;"><strong>Interpretación del total:</strong></p>
  <div style="font-size:13px;">
    <span style="background:#c8e6c9;color:#1b5e20;padding:2px 9px;border-radius:10px;">3.5–4.0 sustantiva fuerte</span>
    <span style="background:#dcedc8;color:#33691e;padding:2px 9px;border-radius:10px;">2.5–3.0 sustantiva</span>
    <span style="background:#ffe0b2;color:#ef6c00;padding:2px 9px;border-radius:10px;">1.5–2.0 parcial</span>
    <span style="background:#ffccbc;color:#bf360c;padding:2px 9px;border-radius:10px;">0.5–1.0 nominal/débil</span>
    <span style="background:#d7ccc8;color:#5d4037;padding:2px 9px;border-radius:10px;">0 mención sin aplicación</span>
  </div>

  <p style="font-size:13px;color:#555;"><strong>Independencia teórica:</strong> la RSI evalúa la <em>operacionalización del concepto</em>, no la fidelidad a una autoría o región. Un paper puede puntuar alto con vocabulario diverso ("colonialidad de género", "compounded vulnerability"…) sin citar a ninguna autora canónica.</p>

  <p style="font-size:13px;color:#999;margin-bottom:0;">Fundamentación completa con referencias: <a href="../../docs/rubrica_RSI_fundamentacion.md">rubrica_RSI_fundamentacion.md</a>. Limitaciones reconocidas: validación humana pendiente · confiabilidad inter-modelo sensible al modelo · scoring basado en abstract · los seis criterios pesan lo mismo (el total es su suma, escalada por el factor de integración).</p>
</div>

<h2 id="teoria">0b · Genealogía teórica de la interseccionalidad</h2>
<div class="theory-block">
  <p style="margin-top:0;">La RSI no surge de un autor único, sino de cinco décadas de teoría feminista crítica. Cada criterio responde a un aporte específico:</p>

  <p><b>Crenshaw (1989, 1991) — el origen.</b> Acuña "interseccionalidad" para mostrar que las mujeres negras quedan en un punto ciego de marcos de eje único (feminismo blanco / antirracismo masculino). Su tesis: las opresiones no se suman, se <em>co-constituyen</em>. → Fundamenta el <b>Criterio I</b>.</p>

  <p><b>Collins (2000) — la matriz de dominación.</b> En <em>Black Feminist Thought</em>, teoriza el poder como sistema interconectado (dominio estructural, disciplinario, hegemónico, interpersonal). La desigualdad no es individual sino estructural. → Fundamenta el <b>Criterio II</b>.</p>

  <p><b>McCall (2005) — la complejidad.</b> Distingue enfoques anti-, intra- e intercategóricos, y subraya que la interseccionalidad opera de forma <em>situada</em>: no hay una experiencia universal de "la mujer". → Fundamenta el <b>Criterio III</b>.</p>

  <p><b>Hancock (2007) — el paradigma de investigación.</b> "When multiplication doesn't equal quick addition": la interseccionalidad no es solo un <em>contenido</em> (qué se estudia) sino un <em>método</em> (cómo). Exige diseños que capten interacciones, no variables paralelas. → Fundamenta el <b>Criterio IV</b>.</p>

  <p><b>Bowleg (2012) — la operacionalización empírica.</b> "The problem with the phrase women and minorities": denuncia el uso aditivo en investigación y propone cómo aplicar el marco sin traicionarlo. → Atraviesa los <b>Criterios I y IV</b>.</p>

  <p><b>Collins & Bilge (2016) — la praxis.</b> La interseccionalidad no es solo una herramienta analítica sino también una <em>praxis crítica</em> orientada a la justicia social: el conocimiento se vincula con la transformación de las desigualdades. → Fundamenta el <b>Criterio V</b>. De la misma tradición —y de los feminismos del Sur— proviene la exigencia de reconocer la <em>agencia</em> de los sujetos (sus estrategias, saberes y resistencia) y no representarlos solo como víctimas. → Fundamenta el <b>Criterio VI</b>.</p>

  <p style="margin-bottom:0;"><b>La crítica al uso nominal</b> (Davis 2008, "buzzword"; Carbado et al. 2013, "citar sin movilizar") es lo que justifica <em>medir</em> la sustantividad: si el campo usa el marco de adorno, hay que poder demostrarlo con datos. Eso es exactamente lo que produce la RSI.</p>
</div>

<h2 id="prompts">0c · Cómo aplica la RSI el modelo de lenguaje (prompts)</h2>
<p>En la v3, la RSI la aplicó un agente LLM (Claude · claude-opus-5-5) en una sola pasada por registro, que incluye cribado, codificación, RSI y razonamiento. Por <strong>transparencia metodológica</strong>, estos son los prompts exactos:</p>

<div class="flow-diagram">
  [Título + Abstract + Keywords + tipo de documento + idioma]<br>
  ↓<br>
  <b>Cribado</b> → ¿invoca la interseccionalidad en sentido social? · ¿objeto climático? (si no: excluido con motivo)<br>
  ↓<br>
  <b>Scoring RSI v3</b> (prompt RSI) → gate + 6 criterios (I–VI) + integración + evidencia por criterio<br>
  ↓<br>
  <b>Razonamiento</b> → explicación de ~50 palabras del porqué del score<br>
  ↓<br>
  [JSON estructurado por paper, validado contra el esquema]
</div>

<details open>
<summary><b>Prompt v3 — Cribado, codificación y RSI</b> (prompts/v3_cribado_rsi.md)</summary>
<pre class="code-block">{prompt_v3}</pre>
</details>

<details>
<summary><b>Prompt RSI v3</b> (prompts/bowleg_eval_v3.md)</summary>
<pre class="code-block">{prompt_scoring}</pre>
</details>

<details>
<summary><b>Reglas del razonamiento</b> (prompts/reasoning_v3.md)</summary>
<pre class="code-block">{prompt_reasoning}</pre>
</details>

<details>
<summary><b>Ejemplo de salida JSON</b> (un paper con score 3.5)</summary>
<pre class="code-block">{{
  "bowleg_I": 1, "bowleg_I_evidence": "centres Indigenous, eco-feminist, intersectional/critical race...",
  "bowleg_II": 1, "bowleg_III": 1, "bowleg_IV": 0.5,
  "bowleg_total": 3.5, "confidence": "high",
  "razonamiento": "El paper aborda la interseccionalidad al integrar identidades entrelazadas
                   y poder estructural en el contexto de la educación en trabajo social..."
}}</pre>
</details>

<p style="font-size:13px;color:#666;">Nota sobre <strong>independencia teórica</strong>: el prompt instruye explícitamente al modelo a evaluar la <em>operacionalización del concepto</em>, no la fidelidad a una autoría o región — un paper puede puntuar alto sin citar a Crenshaw/Bowleg/Collins, usando vocabulario alternativo.</p>

<h2 id="nums">1 · Números clave</h2>
<div class="stat-grid">
  <div class="stat"><div class="stat-num">{len(scored):,}</div><div class="stat-lbl">Papers (corpus v3 elegible)</div></div>
  <div class="stat"><div class="stat-num">{sum(pmeta['identificados'].values()):,}</div><div class="stat-lbl">Registros identificados (Scopus + SciELO + OpenAlex)</div></div>
  <div class="stat"><div class="stat-num">{int((scored['bowleg_total'] >= 2.5).sum()):,}</div><div class="stat-lbl">RSI ≥ 2.5 (sustantivo)</div></div>
  <div class="stat"><div class="stat-num">{int((scored['bowleg_total'] <= 1.0).sum()):,}</div><div class="stat-lbl">RSI ≤ 1.0 (nominal/mención)</div></div>
  <div class="stat"><div class="stat-num">{cat_pct.get('sustantivo_fuerte', 0):.0f}%</div><div class="stat-lbl">Sustantiva fuerte (≥3.5)</div></div>
  <div class="stat"><div class="stat-num">{cat_pct.get('mencion_sin_aplicacion', 0):.0f}%</div><div class="stat-lbl">Mención sin aplicación (=0)</div></div>
</div>

<h3>Categorías RSI</h3>
<table class="data-table">
<tr><th>Categoría</th><th>n</th><th>%</th></tr>
{''.join(f'<tr><td>{CAT_LABELS.get(c,c)}</td><td>{int(cat_dist[c]):,}</td><td>{cat_pct[c]:.1f}%</td></tr>' for c in ['sustantivo_fuerte','sustantivo','parcial','nominal_debil','mencion_sin_aplicacion'] if c in cat_dist.index)}
</table>

<h2 id="prisma">2 · Flujo PRISMA</h2>
<img src="{figs['fig01']}" alt="PRISMA v3">

<h2 id="busqueda">2b · Estrategia de búsqueda</h2>
<p>La v3 reúne tres fuentes, todas consultadas el {smeta['fecha_busqueda']} con las mismas cadenas trilingües (inglés, español y portugués):</p>
<ul style="font-size:13.5px;line-height:1.6">
  <li><b>Scopus</b>, por la API de búsqueda (vista COMPLETE), con <code>PUBYEAR &gt; 1988</code> e idioma inglés, español o portugués.
  La cadena completa no cabe en una sola petición, así que el bloque climático se parte en {smeta['particion']['grupos_descarga']} grupos de
  términos unidos por OR; la unión de las consultas equivale a la cadena original. {smeta['registros_unicos']:,} registros únicos.</li>
  <li><b>SciELO</b> (search.scielo.org), con su propia cadena: {pmeta['identificados']['scielo']} registros; {pmeta['duplicados']['scielo_ya_en_scopus']} ya estaban en Scopus.</li>
  <li><b>OpenAlex</b>, por su API, solo para trabajos que OpenAlex clasifica en <b>español o portugués</b>: {pmeta['identificados']['openalex']} registros
  únicos ({oameta['consultas']} consultas). {pmeta['duplicados']['openalex_ya_en_scopus_scielo']} ya estaban en Scopus o SciELO y
  {n_oa_principal} son nuevos ({pmeta['tipo_openalex_nuevos'].get('Dissertation', 0)} tesis, {pmeta['tipo_openalex_nuevos'].get('Book chapter', 0)} capítulos de libro,
  {pmeta['tipo_openalex_nuevos'].get('Article', 0)} artículos). La consulta traduce las cadenas a los filtros de OpenAlex: cada bloque es una lista de términos
  separados por «|» (OR) que se busca en título y resumen. Tiene tres límites: OpenAlex <b>no acepta comodines ni proximidad</b>
  (las variantes en español y portugués se escriben completas y las expresiones con <code>W/n</code> se omiten), <b>lematiza en inglés</b>
  (por eso trae ruido como «intersection», que el cribado retira) y asigna el <b>idioma por el título</b>, a veces mal.
  Por eso la misma consulta se corrió también, solo con los términos interseccionales en español y portugués, sobre los trabajos que
  OpenAlex <i>no</i> etiqueta como español o portugués: de {oiraw.get('identificados', 0)} resultados, {oimeta.get('en_es_o_pt', 0)} están en español
  o portugués según el título y el inicio del resumen (casi todos los demás, en catalán) y {oimeta.get('nuevos', 0)} son nuevos; entre ellos, un
  artículo sobre los huracanes Otis y John en Acapulco desde una perspectiva de género interseccional, etiquetado como inglés
  (<code>pipeline/v3/00d_openalex_idioma.py</code>).</li>
  <li><b>Redalyc</b>, como verificación de cobertura: no tiene API ni exportación y su buscador busca en el texto completo, así que la cadena de SciELO
  se corrió en redalyc.org y se recorrieron los resultados en el navegador ({rdmeta['registros_unicos']:,} artículos únicos). Solo
  {rdmeta['con_ambos_bloques_en_titulo_resumen_o_palabras_clave']} tienen ambos bloques en el título, el resumen o las palabras clave, y los
  {rdmeta['con_ambos_bloques_en_titulo_resumen_o_palabras_clave']} ya estaban por las otras fuentes: <b>no aporta registros nuevos</b>
  (<code>data/v3_redalyc_meta.json</code>).</li>
</ul>
<p><b>Resúmenes rescatados.</b> {pmeta['rescate_resumen']['sin_resumen_en_su_fuente']} registros llegan sin resumen de su fuente (sobre todo notas, editoriales y
capítulos de libro de Scopus). Para los que tienen DOI se buscó el resumen en OpenAlex, en cualquier idioma, y se aceptó solo si tiene al menos
20 palabras además del título, si el DOI no lo comparte otro registro (los capítulos con el DOI del libro reciben la descripción del libro) y si,
en un capítulo, no describe el libro entero. Así se rescataron <b>{pmeta['rescate_resumen']['rescatados']}</b>, que se evaluaron con el mismo prompt;
los demás quedan excluidos por falta de resumen (<code>data/v3_resumenes_openalex.json</code>).</p>
<p>Como en la v2, la selección no se delega solo al scoring: un <b>cribado de elegibilidad</b> separa antes lo que no es del tema (§2).</p>

<details><summary>Cadena de Scopus</summary>
<pre style="background:#f8fafc;border:1px solid var(--line);border-radius:6px;padding:12px;font-size:11.5px;line-height:1.5;overflow-x:auto;white-space:pre-wrap;"><code>{query_scopus}</code></pre>
</details>
<details><summary>Cadena de SciELO</summary>
<pre style="background:#f8fafc;border:1px solid var(--line);border-radius:6px;padding:12px;font-size:11.5px;line-height:1.5;overflow-x:auto;white-space:pre-wrap;"><code>{query_scielo}</code></pre>
</details>
<details><summary>Consulta de OpenAlex (data/v3_query_openalex.json)</summary>
<pre style="background:#f8fafc;border:1px solid var(--line);border-radius:6px;padding:12px;font-size:11.5px;line-height:1.5;overflow-x:auto;white-space:pre-wrap;"><code>{query_oa}</code></pre>
<p style="font-size:12px;color:#555;">Los bloques se parten en grupos de hasta {max(a for a, _ in oameta['terminos_por_consulta'])} y {max(b for _, b in oameta['terminos_por_consulta'])} términos y se corren todas las combinaciones; los registros se unen por ID de OpenAlex.</p>
</details>

<table class="data-table" style="margin-top:8px;">
<tr><th>Parte del ancla (registros que pasan a cribado)</th><th>Registros</th></tr>
<tr><td>Solo <code>intersectional*</code> / <code>interseccional*</code> / <code>intersecional*</code></td><td>{pmeta['nivel_ancla'].get('A_nucleo', 0):,}</td></tr>
<tr><td>Además, frases como «intersection of race and gender» (<code>W/4</code>), «interseção de opressões» o «intersecting …»</td><td>{pmeta['nivel_ancla'].get('A_ampliada', 0):,}</td></tr>
<tr><td>Solo vocabulario afín</td><td>{pmeta['nivel_ancla'].get('B_afin', 0):,}</td></tr>
<tr><td>Ninguno en título, resumen o palabras clave de autor (en Scopus entraron por las palabras clave indexadas; en OpenAlex, por lematización, p. ej. «intersection»)</td><td>{pmeta['nivel_ancla'].get('solo_index_keywords', 0):,}</td></tr>
<tr><td><b>Total</b></td><td><b>{pmeta['a_cribado']:,}</b></td></tr>
</table>

<p style="margin-top:16px;">
  <a class="doc-link" href="../../docs/cadenas_busqueda.md">📋 Documento completo: cadenas de búsqueda (v1–v3)</a>
</p>

<h2 id="bowleg">3 · Distribución RSI</h2>
<img src="{figs['fig02']}" alt="Distribución RSI">
{ins_bowleg}

<h2 id="anatomia">3b · Anatomía de la sustantividad</h2>
<p>¿Qué hay <em>dentro</em> del puntaje? Estas figuras descomponen la RSI para mostrar dónde el campo aplica el marco y dónde falla.</p>

<h3>El embudo: de la mención a la aplicación</h3>
<img src="{figs['figB']}" alt="Embudo del gate">

<h3>Perfil por criterio</h3>
<img src="{figs['figA']}" alt="Perfil por criterio">
{ins_anatomia}

<h3>¿Se articulan los criterios o se yuxtaponen?</h3>
<div class="grid-2">
  <img src="{figs['figE']}" alt="Integración">
  <img src="{figs['figD']}" alt="Co-ocurrencia de criterios">
</div>
{insight("Lectura del dato", "El factor de integración (izq.) muestra cuántos trabajos articulan los criterios en un análisis coherente frente a los que los presentan yuxtapuestos. La matriz de co-ocurrencia (der.) revela qué criterios tienden a aparecer juntos: correlaciones altas indican que ciertas dimensiones se mueven en bloque (p. ej. poder estructural y contexto situado), mientras que el método (IV) suele estar más desacoplado del resto —se puede teorizar sin operacionalizar.")}

<h2>4 · Producción anual</h2>
<img src="{figs['fig03']}" alt="Papers por año">

<h2 id="topics">5 · Tópicos × RSI</h2>
<p style="font-size:13px;color:#555;">Los tópicos se calculan con BERTopic, como en las versiones anteriores, pero con un modelo de embeddings
multilingüe (<code>paraphrase-multilingual-MiniLM-L12-v2</code>): con el modelo solo en inglés de la v1 y la v2, los trabajos en español y
portugués formaban un bloque aparte por idioma y no por tema. Por eso los tópicos de la v3 no se comparan uno a uno con los de la v2.</p>
<img src="{figs['fig04']}" alt="Topics × Bowleg">

<h3>Los 15 tópicos con mayor % de trabajos sustantivos</h3>
{df_to_html_table(topics_substantive, 15, COLS_TOPICO)}

<details>
<summary>Tópicos con menor sustantividad media</summary>
{df_to_html_table(topics_artifact, 10, COLS_TOPICO)}
<p style="font-size: 12px; color: #888;">En la v3, el cribado ya excluyó los falsos positivos de la búsqueda: estos tópicos reúnen trabajos pertinentes con un uso más nominal del marco.</p>
</details>
{ins_topics}

<h2 id="topicmap">5b · Mapa temático interactivo</h2>
<p>
  El mapa no es solo ilustrativo: permite <b>leer la sustantividad como geografía</b>. Los controles del
  panel (arriba a la derecha) habilitan tres lecturas del mismo layout —los clústeres no cambian, solo el color—:
</p>
<ul style="font-size:13px;line-height:1.6">
  <li><b>Colorear por tópico</b> — color original por cluster (estructura temática).</li>
  <li><b>Colorear por nivel RSI del paper</b> — cada punto según su propia sustantividad (gris=mención → verde oscuro=sustantiva fuerte).</li>
  <li><b>Colorear por RSI medio del tópico</b> — pinta cada <i>vecindario</i> por su sustantividad media: revela de un vistazo qué regiones del campo operan el marco y cuáles solo lo mencionan.</li>
  <li><b>Resaltar sub-corpus de la tesis ({ds.get('relevant_ge2_axes', 0)})</b> — ilumina los papers de la tesis de Daniel (contorno morado) y atenúa el resto, para ver su dispersión.</li>
</ul>
<p style="font-size:13px;background:#f8f9fa;padding:10px 14px;border-radius:6px;">
  <strong>Contorno por idioma:</strong>
  <span style="color:#d32f2f;font-weight:bold">● rojo</span> = español ·
  <span style="color:#1976d2;font-weight:bold">● azul</span> = portugués ·
  <span style="color:#9e9e9e;font-weight:bold">● gris</span> = inglés ·
  <strong>Hover</strong> = metadata · <strong>Click</strong> = panel persistente (links DOI).
</p>

<div style="width:100%;height:920px;margin:16px 0;border:1px solid #ddd;border-radius:6px;overflow:hidden;">
  <iframe src="mapa.html" width="100%" height="100%" style="border:none;"></iframe>
</div>

<p style="font-size:12px;color:#666;">
  <strong>Otras versiones:</strong>
  <a href="mapa.html" target="_blank">datamapplot standalone (full screen)</a> ·
  <a href="../../assets/v3_fig09_topic_map_interactive.html" target="_blank">Plotly alternativo</a> ·
  <a href="../../assets/v3_fig09_topic_map.png" target="_blank">PNG estático</a>
</p>

{lectura_mapa_html}

<h3>Ranking de tópicos por sustantividad media (figura H)</h3>
<p style="font-size:13px;color:#555">Cada barra es un tópico; el color codifica el nivel de RSI medio. La línea punteada marca el umbral sustantivo (2.5). Hace explícita la concentración que se ve en el mapa.</p>
<img src="{figs['figH']}" alt="Ranking de tópicos por RSI medio" style="max-width:100%">

<details style="margin-top:16px">
<summary><b>Radiografía completa por tópico</b> (RSI, % gate, % sustantivo, idioma, papers de la tesis)</summary>
<div style="overflow-x:auto;margin-top:10px">
{topic_ficha_html}
</div>
<p style="font-size:11px;color:#888">% gate = papers que superan el criterio de entrada. % sust. = RSI ≥ 2.5. Idioma: barras proporcionales ES (rojo) / EN (gris) / PT (azul). Tesis = papers del sub-corpus de Daniel que caen en ese tópico.</p>
</details>

<details style="margin-top:12px;">
<summary>Mapa alternativo en Plotly (perímetro con etiquetas)</summary>
<div style="width:100%;overflow-x:auto;margin:16px 0;border:1px solid #ddd;border-radius:6px;background:white;">
{topic_map_embed}
</div>
</details>

<h2 id="lang">6 · Idioma del documento</h2>
<div class="grid-2">
  <img src="{figs['fig05']}" alt="RSI por idioma">
  <img src="{figs['figF']}" alt="Violín RSI por idioma">
</div>
{df_to_html_table(lang_bw, 6, COLS_IDIOMA)}
{ins_lang}

<h2 id="paises">7 · Geografía del rigor</h2>
<p style="font-size:13px;color:#555;">País de afiliación de los autores, según Scopus y OpenAlex (SciELO no trae afiliaciones). Un trabajo cuenta una vez por cada país de sus autores.</p>
<img src="{figs['fig06']}" alt="Country × Bowleg">

<details>
<summary>Tabla por país (25 países con más trabajos)</summary>
{df_to_html_table(country_bw, 25, COLS_PAIS)}
</details>
{ins_paises}

<h2 id="temporal">8 · Tendencia temporal</h2>
<img src="{figs['fig07']}" alt="Year trend">
{ins_temporal}

<h2 id="casos">9 · Casos ejemplares</h2>
<p>Para ilustrar qué <em>ve</em> el instrumento en cada nivel, se muestran trabajos representativos con la evidencia textual que el modelo citó por criterio. Permite al lector juzgar la rúbrica frente al texto real.</p>
{casos_html}

<h2 id="valid">10 · Notas de validación</h2>
<div class="theory-block">
  <p style="margin-top:0;">El cribado y el scoring RSI de la v3 los aplicó <strong>Claude (claude-opus-5-5)</strong>, con un prompt versionado que aplica la rúbrica RSI v3 al pie de la letra. {n_reut:,} trabajos elegibles conservan la evaluación de la v2, que ya incluye la corrección de la regla del gate (<code>data/v2_reevaluacion_gate.csv</code>); los {reg_origen.get('v3', 0)} registros nuevos (de Scopus, SciELO y OpenAlex) se evaluaron con <code>prompts/v3_cribado_rsi.md</code>, en lotes de 40 registros. El procedimiento es transparente y auditable: el prompt está versionado y cada puntaje incluye evidencia textual por criterio. No es reproducible al pie de la letra: el modelo se aplicó en sesiones de Claude Code.</p>
  <p><strong>Validación pendiente.</strong> Para consolidar la rúbrica como instrumento, resta una <strong>validación humana</strong>. Un evaluador experto repite a ciegas, sobre una muestra, los mismos pasos que siguió el modelo, con las mismas definiciones y reglas: <b>inclusión</b> (¿invoca la interseccionalidad en sentido social? ¿el objeto es climático?), <b>gate</b>, <b>criterios I–VI</b> e <b>integración</b>. La muestra tiene {vmeta["n"]} trabajos en {vmeta["bloques"]} bloques de {vmeta["por_bloque"]}: cada bloque trae 2 registros que el modelo excluyó y 1 de cada categoría RSI. La herramienta calcula la concordancia del cribado, del gate, de cada criterio y de la categoría RSI (κ de Cohen, κ ponderado e IC bootstrap), y estima el acuerdo para el corpus completo. Hasta entonces, los puntajes deben interpretarse como provisionales.</p>
  <p style="margin-bottom:0;"><a href="validacion.html"><b>✓ Abrir la herramienta de validación</b></a> · <a href="corpus.html"><b>☰ Ver la lista completa del corpus</b></a> ({pmeta["a_cribado"]:,} registros cribados, con las respuestas del modelo; conviene revisarla después de codificar la muestra).</p>
</div>

<h2 id="daniel">11 · Sub-corpus tesis de Daniel</h2>

<div class="daniel-box">
  <strong>Tema de la tesis:</strong> ciclones tropicales × cambio climático × interseccionalidad
  (género × clase × territorio) × medios de vida en mujeres y comunidades indígenas en zonas
  costeras de México. El corpus completo es estado del arte; este sub-corpus es el nicho temático.
</div>

<div class="stat-grid">
  <div class="stat"><div class="stat-num">{stats['daniel_subcorpus']['mexico_AND_cyclonic']}</div><div class="stat-lbl">México + ciclones</div></div>
  <div class="stat"><div class="stat-num">{stats['daniel_subcorpus']['mexico_cyclonic_gender_or_indigenous']}</div><div class="stat-lbl">México + ciclones + género/indígena</div></div>
  <div class="stat"><div class="stat-num">{stats['daniel_subcorpus']['coastal_AND_cyclonic']}</div><div class="stat-lbl">Costero + ciclones</div></div>
  <div class="stat"><div class="stat-num">{stats['daniel_subcorpus']['relevant_ge2_axes']}</div><div class="stat-lbl">Sub-corpus relevante (≥2 ejes)</div></div>
  <div class="stat"><div class="stat-num">{stats['daniel_subcorpus']['relevant_substantive']}</div><div class="stat-lbl">De esos, RSI ≥ 2.5</div></div>
  <div class="stat"><div class="stat-num">{stats['daniel_subcorpus']['relevant_bowleg_mean']:.2f}</div><div class="stat-lbl">RSI media del sub-corpus</div></div>
</div>

<table class="data-table">
<tr><th>Filtro temático</th><th>n papers</th></tr>
<tr><td>México (en abstract/título)</td><td>{stats['daniel_subcorpus']['mexico']}</td></tr>
<tr><td>Ciclones tropicales / huracanes</td><td>{stats['daniel_subcorpus']['cyclonic_events']}</td></tr>
<tr><td>Costero / coastal</td><td>{stats['daniel_subcorpus']['coastal']}</td></tr>
<tr><td>Indígena</td><td>{stats['daniel_subcorpus']['indigenous']}</td></tr>
<tr><td>Mujeres / género</td><td>{stats['daniel_subcorpus']['gender_women']}</td></tr>
</table>
<p style="font-size:13px;background:#f8f9fa;padding:10px 14px;border-radius:6px;">
  <b>Cómo leer el cruce México × ciclones.</b> El corpus reúne solo trabajos que <b>nombran</b> la interseccionalidad (o un marco afín)
  y tratan el clima; los filtros de esta sección buscan México y ciclones en su título y resumen. En la búsqueda principal (Scopus, SciELO y
  OpenAlex en español y portugués), antes de cualquier filtro, lo único con México y huracanes eran tres estudios de la novela <i>Temporada de huracanes</i> y uno sobre Katrina en la
  costa del Golfo de México, todos excluidos en el cribado. La literatura mexicana sobre huracanes, género y pueblos indígenas existe —en una
  consulta exploratoria en OpenAlex (24-11-2026), unos 250 trabajos cruzan México, huracanes y género, mujeres o indígenas—, pero casi
  nunca nombra la interseccionalidad: solo 12 de ellos usan ese vocabulario, y de esos solo uno trata ese cruce (Otis y John en Acapulco,
  que OpenAlex etiquetaba como inglés y se incorporó con la búsqueda de §2b). Que el nicho no use el marco es, en sí, un resultado para la tesis.
</p>
{ins_daniel}

<h3>Documentos del sub-corpus (acceso directo)</h3>
<p style="font-size:13px;">Los {ds.get('relevant_ge2_axes', 0)} trabajos con ≥2 ejes temáticos relevantes para la tesis, ordenados por puntaje RSI. Cada uno enlaza a su DOI para consulta directa.</p>
<details open>
<summary>Ver listado completo ({stats['daniel_subcorpus'].get('relevant_ge2_axes','?')} trabajos · {stats['daniel_subcorpus'].get('relevant_substantive','?')} sustantivos)</summary>
{subcorpus_docs_html}
</details>
<p style="font-size:12px;color:#666;">Exportado a <code>data/v3_daniel_subcorpus.csv</code> para análisis fino.</p>

<h2 id="sintesis">12 · Síntesis y discusión</h2>
<div class="theory-block">
  <p style="margin-top:0;"><b>Una adopción que no es aplicación.</b> El embudo (§3b) muestra el primer hallazgo: de los {n_tot} trabajos que invocan la interseccionalidad, solo {n_gate} articulan dos o más ejes de diferenciación como relacionados, y apenas una fracción de ellos alcanza aplicación sustantiva. La amplia circulación del término no se corresponde con su uso analítico: predomina la mención.</p>

  <p><b>Cuando se aplica, se teoriza más de lo que se opera.</b> El perfil por criterio (§3b) precisa <em>dónde</em> falla la aplicación. Entre los trabajos que pasan el criterio de entrada, el poder estructural llega al {c_II}% y el contexto situado al {c_III}%, pero el <b>método no aditivo (criterio IV) se queda en {pct_metodo_gate}%</b>. La interseccionalidad se invoca como marco interpretativo, pero rara vez se traduce en decisiones de diseño —muestreo, codificación, modelos con interacciones—. Es el eslabón débil del campo.</p>

  <p><b>El rigor es de nicho, no del campo.</b> El análisis temático (§5) y el mapa (§5b) muestran que la sustantividad no se reparte de forma homogénea: se concentra en comunidades de investigación ancladas en contextos concretos ({top_topicos_txt}). El paso del tiempo (§8) no modifica sustancialmente este patrón, y el idioma (§6) tampoco lo explica: los trabajos en español y portugués, ya incluidos en la v3, alcanzan aplicación sustantiva con menor frecuencia que los escritos en inglés. La aplicación rigurosa parece depender de tradiciones disciplinares específicas más que de una maduración general del campo.</p>

  <p><b>Implicaciones.</b> (1) <em>Para el campo:</em> el reto no es adoptar más la interseccionalidad —ya está ampliamente adoptada— sino operacionalizarla metodológicamente. (2) <em>Para la práctica de investigación:</em> citar a Crenshaw o Collins no basta; la sustantividad exige traducir el marco en diseño empírico. (3) <em>Para esta tesis:</em> en el corpus v3 {tesis_cruce_txt} (§11), pero los trabajos que combinan sus ejes temáticos están entre los más sustantivos del corpus. Hay, por tanto, un <b>vacío temático con un piso metodológico sólido</b>: un espacio donde la tesis puede contribuir sin partir de cero.</p>

  <p style="margin-bottom:0;"><b>Límites.</b> Los puntajes son provisionales (modelo de lenguaje, validación humana pendiente, evaluación sobre resúmenes); el criterio IV en particular puede subestimarse porque el diseño metodológico no siempre aparece en el abstract. Estas cautelas no alteran los patrones estructurales, pero sí los valores exactos.</p>
</div>

<h2 id="docs">13 · Documentos generados</h2>
<p>
  <a class="doc-link" href="../../docs/rubrica_RSI_fundamentacion.md">📋 Fundamentación RSI</a>
  <a class="doc-link" href="../../prompts/v3_cribado_rsi.md">⚙ Prompt v3</a>
  <a class="doc-link" href="../../prompts/bowleg_eval_v3.md">⚙ Prompt RSI v3</a>
  <a class="doc-link" href="../../data/v3_corpus_scored.csv">📊 Corpus + scores (CSV)</a>
  <a class="doc-link" href="../../data/v3_daniel_subcorpus.csv">📊 Sub-corpus Daniel (CSV)</a>
</p>

<details>
<summary>Detalles de procedencia</summary>
<table class="data-table">
<tr><th>Fuente</th><th>Origen</th><th>n</th></tr>
<tr><td>Scopus</td><td>Cadena v3 (data/v3_query_scopus.txt), API de búsqueda, {smeta['fecha_busqueda']}</td><td>{pmeta['identificados']['scopus']:,}</td></tr>
<tr><td>SciELO</td><td>Cadena v3 (data/v3_query_scielo.txt), export RIS de search.scielo.org, {smeta['fecha_busqueda']}</td><td>{pmeta['identificados']['scielo']:,}</td></tr>
<tr><td>OpenAlex</td><td>data/v3_query_openalex.json, API de works (español y portugués), {oameta['fecha']}</td><td>{pmeta['identificados']['openalex']:,}</td></tr>
<tr><td>OpenAlex (otra etiqueta de idioma)</td><td>Misma consulta con los términos en español y portugués, sobre trabajos no etiquetados como ES/PT (data/v3_openalex_idioma_meta.json), {oiraw.get('fecha', '')}; solo los que están en español o portugués</td><td>{pmeta['identificados'].get('openalex_otra_etiqueta', 0):,}</td></tr>
<tr><td>Redalyc</td><td>Verificación: cadena de SciELO en redalyc.org (data/v3_redalyc_meta.json), {rdmeta['fecha']}; {rdmeta['con_ambos_bloques_en_titulo_resumen_o_palabras_clave']} pertinentes, todos ya incluidos</td><td>0 nuevos</td></tr>
</table>
<p style="font-size: 12px;">
Total identificado: {sum(pmeta['identificados'].values()):,} ·
Filtro abstract ≥100 chars: −{sum(v['sin_abstract'] for v in pmeta['excluidos_regla'].values()) - pmeta['rescate_resumen']['rescatados']} ({sum(v['sin_abstract'] for v in pmeta['excluidos_regla'].values())} sin resumen en su fuente; {pmeta['rescate_resumen']['rescatados']} se rescataron con el resumen que OpenAlex tiene para su DOI) ·
Erratas, conference reviews y otros tipos: −{sum(v.get('tipo', v.get('erratum_o_conference_review', 0)) for v in pmeta['excluidos_regla'].values())} ·
Dedup DOI + título: −{sum(pmeta['duplicados'].values())} ·
Cribado de elegibilidad: −{pmeta['cribado']['excluidos']} ·
<strong>Corpus v3 elegible: {pmeta['cribado']['elegibles']:,}.</strong>
</p>
<p style="font-size: 12px;">
Cribado + scoring RSI: Claude (claude-opus-5-5); {reg_origen.get('v2', 0):,} registros con la evaluación de la v2 (<code>prompts/v2_cribado_rsi.md</code>), {reg_origen.get('v3', 0):,} evaluados en la v3 ({pmeta['openalex_nuevos']} de ellos de OpenAlex) con <code>prompts/v3_cribado_rsi.md</code>
(rúbrica <code>prompts/bowleg_eval_v3.md</code> + razonamiento <code>reasoning_v3.md</code>).
</p>
</details>

<h2 id="refs">14 · Referencias teóricas</h2>
<p style="font-size:13px;color:#555;">Fuentes que fundamentan la RSI y la crítica al uso nominal de la interseccionalidad. Los enlaces llevan al DOI o repositorio oficial.</p>
<ol style="font-size:13px;line-height:1.7;">
  <li>Crenshaw, K. (1989). Demarginalizing the Intersection of Race and Sex. <i>University of Chicago Legal Forum</i>, 1989(1), 139–167. <a href="https://chicagounbound.uchicago.edu/uclf/vol1989/iss1/8/" target="_blank">[texto]</a></li>
  <li>Crenshaw, K. (1991). Mapping the Margins. <i>Stanford Law Review</i>, 43(6), 1241–1299. <a href="https://doi.org/10.2307/1229039" target="_blank">[DOI]</a></li>
  <li>Collins, P. H. (2000). <i>Black Feminist Thought</i> (2ª ed.). Routledge. <a href="https://www.routledge.com/Black-Feminist-Thought/Collins/p/book/9780415964722" target="_blank">[editorial]</a></li>
  <li>McCall, L. (2005). The Complexity of Intersectionality. <i>Signs</i>, 30(3), 1771–1800. <a href="https://doi.org/10.1086/426800" target="_blank">[DOI]</a></li>
  <li>Hancock, A.-M. (2007). When Multiplication Doesn't Equal Quick Addition. <i>Perspectives on Politics</i>, 5(1), 63–79. <a href="https://doi.org/10.1017/S1537592707070065" target="_blank">[DOI]</a></li>
  <li>Davis, K. (2008). Intersectionality as Buzzword. <i>Feminist Theory</i>, 9(1), 67–85. <a href="https://doi.org/10.1177/1464700108086364" target="_blank">[DOI]</a></li>
  <li>Bowleg, L. (2012). The Problem with the Phrase Women and Minorities. <i>American Journal of Public Health</i>, 102(7), 1267–1273. <a href="https://doi.org/10.2105/AJPH.2012.300750" target="_blank">[DOI]</a></li>
  <li>Carbado, D. W., Crenshaw, K. W., Mays, V. M., & Tomlinson, B. (2013). Intersectionality: Mapping the Movements of a Theory. <i>Du Bois Review</i>, 10(2), 303–312. <a href="https://doi.org/10.1017/S1742058X13000349" target="_blank">[DOI]</a></li>
  <li>Else-Quest, N. M., & Hyde, J. S. (2016). Intersectionality in Quantitative Psychological Research: II. <i>Psychology of Women Quarterly</i>, 40(3), 319–336. <a href="https://doi.org/10.1177/0361684316647953" target="_blank">[DOI]</a></li>
  <li>Collins, P. H., & Bilge, S. (2016). <i>Intersectionality</i>. Polity Press. <a href="https://www.politybooks.com/bookdetail?book_slug=intersectionality-2nd-edition--9781509539680" target="_blank">[editorial]</a></li>
</ol>

<p style="text-align:center; color:#9ca3af; font-size:12px; margin-top:56px; padding-top:20px; border-top:1px solid var(--line);">
Interseccionalidad y Cambio Climático · Rúbrica de Sustantividad Interseccional (RSI) · v3 · 2026
</p>

</div><!-- /main -->
</div><!-- /layout -->

<script>
// Scroll-spy: resalta el link de la sección visible
(function() {{
  const links = Array.from(document.querySelectorAll('.sidebar-nav a'));
  const map = {{}};
  links.forEach(a => {{ const id = a.getAttribute('href').slice(1); const el = document.getElementById(id); if (el) map[id] = a; }});
  const ids = Object.keys(map);
  function onScroll() {{
    let current = ids[0];
    for (const id of ids) {{
      const el = document.getElementById(id);
      if (el && el.getBoundingClientRect().top <= 120) current = id;
    }}
    links.forEach(a => a.classList.remove('active'));
    if (map[current]) map[current].classList.add('active');
  }}
  document.addEventListener('scroll', onScroll, {{ passive: true }});
  // smooth scroll
  links.forEach(a => a.addEventListener('click', e => {{
    const id = a.getAttribute('href').slice(1); const el = document.getElementById(id);
    if (el) {{ e.preventDefault(); el.scrollIntoView({{ behavior: 'smooth', block: 'start' }}); }}
  }}));
  onScroll();
}})();
</script>

</body>
</html>
"""
    out = DASHBOARD / 'index.html'
    out.write_text(html)
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"[OK] dashboard → {out} ({size_mb:.1f} MB)")


if __name__ == '__main__':
    main()
