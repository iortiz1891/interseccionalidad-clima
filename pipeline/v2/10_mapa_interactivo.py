#!/usr/bin/env python3
"""
10_mapa_interactivo.py — v2: réplica de pipeline/10_mapa_interactivo.py con la búsqueda ampliada.

Cambios de código: une por paper_id y calcula los conteos de la tesis (la v1 los tenía fijos).

Genera el datamapplot interactivo y luego post-procesa el HTML inyectando:
1. Panel de control overlay (selector de tópico, botón reset, leyenda)
2. Click-to-isolate: seleccionar cluster del dropdown → atenúa el resto
3. Outlines por idioma: rojo=ES, azul=PT, gris=EN (via Deck.gl layer manipulation)
4. Hover mejorado vía CSS de tooltip

Outputs:
  site/v2/mapa.html
  assets/v2_fig10_datamap_interactive.html  (copia)
"""
from __future__ import annotations
import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
import datamapplot

DATA = Path("data")
DASHBOARD = Path("site/v2")
ASSETS = Path("assets")


def _bowleg_badge(bw, cat):
    """Devuelve HTML badge para el score Bowleg con color según nivel."""
    if pd.isna(bw):
        return "<span style='background:#eee;color:#666;padding:1px 8px;border-radius:10px;font-size:11px;'>sin score</span>"
    bw = float(bw)
    if bw >= 3.5:   color = '#1b5e20'; bg = '#c8e6c9'; lbl = 'sustantivo fuerte'
    elif bw >= 2.5: color = '#33691e'; bg = '#dcedc8'; lbl = 'sustantivo'
    elif bw >= 1.5: color = '#ef6c00'; bg = '#ffe0b2'; lbl = 'parcial'
    elif bw > 0:    color = '#bf360c'; bg = '#ffccbc'; lbl = 'nominal/débil'
    else:           color = '#5d4037'; bg = '#d7ccc8'; lbl = 'mención sin aplicación'
    cat_str = str(cat or '').replace('_', ' ').lower() if cat else lbl
    return (f"<span style='background:{bg};color:{color};padding:2px 10px;"
            f"border-radius:11px;font-size:11px;font-weight:600;'>"
            f"RSI {bw:.1f} · {lbl}</span>")


def _lang_pill(lang):
    if not lang or pd.isna(lang): return ''
    l = str(lang).strip().lower()
    if l in ('es', 'spanish'):
        return "<span style='background:#ffebee;color:#d32f2f;padding:1px 7px;border-radius:9px;font-size:10px;font-weight:600;margin-left:6px;'>ES</span>"
    if l in ('pt', 'portuguese'):
        return "<span style='background:#e3f2fd;color:#1976d2;padding:1px 7px;border-radius:9px;font-size:10px;font-weight:600;margin-left:6px;'>PT</span>"
    if l in ('en', 'english'):
        return "<span style='background:#f5f5f5;color:#616161;padding:1px 7px;border-radius:9px;font-size:10px;font-weight:600;margin-left:6px;'>EN</span>"
    return f"<span style='color:#888;font-size:10px;margin-left:6px;'>{lang}</span>"


def _doi_link(doi_value):
    if not doi_value or pd.isna(doi_value): return ''
    d = str(doi_value).strip()
    if not d or d.lower() == 'nan': return ''
    if d.startswith('http'):
        url = d
    else:
        url = f"https://doi.org/{d}"
    return (f"<a href='{url}' target='_blank' style='color:#1a73e8;text-decoration:none;"
            f"font-size:11px;background:#e8f0fe;padding:2px 8px;border-radius:9px;"
            f"font-weight:600;display:inline-block;'>🔗 abrir DOI</a>")


def build_hover(row):
    title = str(row.get('Title', '') or '').replace('<', '&lt;').replace('>', '&gt;')
    if len(title) > 180: title = title[:180] + '…'
    authors = str(row.get('Authors', '') or '').replace('<', '&lt;').replace('>', '&gt;')
    if len(authors) > 120: authors = authors[:120] + '…'
    source = str(row.get('Source title', '') or '').replace('<', '&lt;').replace('>', '&gt;')
    if len(source) > 80: source = source[:80] + '…'
    try:
        year = int(float(row.get('Year', 0))) if pd.notna(row.get('Year')) else None
    except Exception:
        year = None
    bw = row.get('bowleg_total')
    cat = row.get('categoria_bowleg', '')
    lang = row.get('Language of Original Document', '')
    cluster = row.get('_cluster_label', '?')
    razonamiento = str(row.get('razonamiento', '') or '').replace('<', '&lt;').replace('>', '&gt;')
    doi = row.get('DOI', '')

    year_str = str(year) if year else '—'

    # HTML estructurado con jerarquía visual
    razon_block = ''
    if razonamiento and razonamiento.lower() != 'nan':
        razon_block = (
            f"<div style='font-size:11.5px;color:#333;background:#fafafa;border-left:3px solid #1a73e8;"
            f"padding:6px 10px;margin:8px 0;line-height:1.4;border-radius:4px;'>"
            f"<span style='color:#666;font-size:10px;font-weight:600;'>RAZONAMIENTO LLM</span><br>"
            f"{razonamiento}"
            f"</div>"
        )

    doi_link = _doi_link(doi)

    html = (
        f"<div style='line-height:1.45;max-width:540px;'>"
        f"<div style='font-size:13px;font-weight:600;color:#1a1a1a;margin-bottom:4px;'>"
        f"{title}{_lang_pill(lang)}"
        f"</div>"
        f"<div style='font-size:11px;color:#666;font-style:italic;margin-bottom:6px;'>"
        f"{authors or '<span style=color:#aaa>(sin autores)</span>'}"
        f"</div>"
        f"<div style='font-size:11px;color:#444;border-bottom:1px solid #eee;padding-bottom:6px;margin-bottom:6px;'>"
        f"📄 <i>{source or '—'}</i>  ·  📅 <b>{year_str}</b>"
        f"{('  ·  ' + doi_link) if doi_link else ''}"
        f"</div>"
        f"<div style='font-size:11px;margin-bottom:4px;'>"
        f"<span style='color:#888;'>Tópico:</span> "
        f"<b style='color:#1a73e8;'>{cluster}</b>"
        f"</div>"
        f"<div>{_bowleg_badge(bw, cat)}</div>"
        f"{razon_block}"
        f"</div>"
    )
    return html


def _score_chip(val, kind='crit'):
    """Chip de puntaje por criterio: 1=Sí, 0.5=Parcial, 0=No; gate=Pasa/No pasa."""
    if kind == 'gate':
        passes = (str(val).strip().lower() in ('true', '1', '1.0', 'sí', 'si'))
        c, bg, t = ('#1b5e20', '#c8e6c9', 'Pasa') if passes else ('#b71c1c', '#ffcdd2', 'No pasa')
    else:
        try:
            v = float(val)
        except Exception:
            v = None
        if v is None:        c, bg, t = ('#9e9e9e', '#eeeeee', '—')
        elif v >= 1:         c, bg, t = ('#1b5e20', '#c8e6c9', 'Sí')
        elif v >= 0.5:       c, bg, t = ('#e65100', '#ffe0b2', 'Parcial')
        else:                c, bg, t = ('#616161', '#e0e0e0', 'No')
    return (f"<span style='background:{bg};color:{c};padding:1px 7px;border-radius:8px;"
            f"font-size:10px;font-weight:700;white-space:nowrap'>{t}</span>")


def build_detail(row):
    """Versión extendida para el panel de click: hover + justificación del LLM por criterio."""
    base = build_hover(row)

    crits = [
        ('Criterio de entrada (gate)', 'gate_pass', 'gate_evidence', 'gate'),
        ('I · Identidades entrelazadas', 'bowleg_I', 'bowleg_I_evidence', 'crit'),
        ('II · Poder estructural', 'bowleg_II', 'bowleg_II_evidence', 'crit'),
        ('III · Contexto situado', 'bowleg_III', 'bowleg_III_evidence', 'crit'),
        ('IV · Método no aditivo', 'bowleg_IV', 'bowleg_IV_evidence', 'crit'),
        ('V · Praxis y justicia', 'rsi_V', 'rsi_V_evidence', 'crit'),
        ('VI · Agencia y resistencia', 'rsi_VI', 'rsi_VI_evidence', 'crit'),
        ('Factor de integración', 'integracion', 'integracion_nota', 'crit'),
    ]
    items = []
    for label, score_col, ev_col, kind in crits:
        ev = row.get(ev_col)
        ev_str = '' if ev is None else str(ev).strip()
        score_val = row.get(score_col)
        has_score = not (score_val is None or (isinstance(score_val, float) and pd.isna(score_val)))
        if (not ev_str or ev_str.lower() == 'nan') and not has_score:
            continue
        ev_html = ev_str.replace('<', '&lt;').replace('>', '&gt;') if ev_str and ev_str.lower() != 'nan' else \
            "<span style='color:#aaa'>(sin justificación)</span>"
        chip = _score_chip(score_val, kind) if has_score else ''
        items.append(
            f"<div style='margin:0 0 7px;padding:6px 8px;background:#fafafa;border-radius:5px;'>"
            f"<div style='display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:2px;'>"
            f"<span style='font-size:10.5px;font-weight:700;color:#333;'>{label}</span>{chip}</div>"
            f"<div style='font-size:11px;color:#444;line-height:1.4;'>{ev_html}</div>"
            f"</div>"
        )
    if not items:
        return base

    justif = (
        "<div style='margin-top:8px;border-top:1px solid #e0e0e0;padding-top:8px;'>"
        "<div style='font-size:10px;font-weight:700;color:#666;text-transform:uppercase;"
        "letter-spacing:0.4px;margin-bottom:6px;'>Justificación del LLM por criterio</div>"
        + "".join(items) +
        "<div style='font-size:9.5px;color:#999;font-style:italic;margin-top:2px;'>"
        "RSI v3 (Claude · claude-opus-5-5) · provisional hasta validación humana</div>"
        "</div>"
    )
    # Insertar la justificación dentro del contenedor del hover (antes del cierre </div>)
    if base.endswith("</div>"):
        return base[:-6] + justif + "</div>"
    return base + justif


def main():
    print("[1] Cargando datos (v2)")
    assignments = pd.read_csv(DATA / 'v2_bertopic_assignments.csv')
    ai_labels = json.loads((DATA / 'v2_topic_ai_labels.json').read_text())
    final = pd.read_csv(DATA / 'v2_corpus_final.csv')
    razon = pd.read_csv(DATA / 'v2_reasoning_results.csv')
    final = (final.drop(columns=['topic_id', 'umap_x', 'umap_y'], errors='ignore')
                  .merge(razon, on='paper_id', how='left'))

    def label_of(tid):
        if tid < 0: return 'Unlabelled'
        s = ai_labels.get(str(tid))
        if s and s.get('label'):
            return s['label'].replace('[Artefacto] ', '')
        return f'Topic {tid}'

    # Merge por paper_id (solo elegibles con puntaje)
    merged = assignments.merge(final, on='paper_id', how='inner')
    merged['bowleg_total'] = pd.to_numeric(merged['bowleg_total'], errors='coerce')
    merged['_cluster_label'] = merged['topic_id'].apply(label_of)

    coords = merged[['umap_x', 'umap_y']].to_numpy()
    point_labels = merged['_cluster_label'].to_numpy()
    hover_text = [build_hover(r) for _, r in merged.iterrows()]
    # Versión extendida (con justificación por criterio) para el panel de click
    detail_text = [build_detail(r) for _, r in merged.iterrows()]

    # Necesitamos cluster_id por punto para JS injection
    cluster_id_per_point = merged['topic_id'].to_numpy().astype(int)
    # Lang por punto (para outlines)
    lang_per_point = merged['Language of Original Document'].fillna('').astype(str).to_numpy()
    # RSI total por punto (para overlay de color por nivel de sustantividad)
    rsi_per_point = pd.to_numeric(merged['bowleg_total'], errors='coerce').fillna(0.0).to_numpy()
    # RSI medio del tópico al que pertenece cada punto (overlay "vecindario")
    _bt = pd.to_numeric(merged['bowleg_total'], errors='coerce')
    _topic_mean = _bt.groupby(merged['topic_id']).transform('mean')
    # los puntos sin tópico (topic_id < 0) quedan en 0 → gris
    _topic_mean = _topic_mean.where(merged['topic_id'] >= 0, 0.0).fillna(0.0)
    topic_rsi_per_point = _topic_mean.to_numpy()
    # Marcar papers del sub-corpus de la tesis de Daniel (por paper_id)
    _sc_ids = set(pd.read_csv(DATA / 'v2_daniel_subcorpus.csv')['paper_id'])
    is_tesis_per_point = merged['paper_id'].isin(_sc_ids).to_numpy()
    print(f"    sub-corpus tesis marcado: {int(is_tesis_per_point.sum())} papers en el mapa")

    print(f"    n={len(merged)} papers · {len(set(point_labels))-1} labels únicos")

    # Conteos reales para el subtítulo (dinámicos, no hardcodeados)
    n_papers = len(merged)
    n_topics = int(merged.loc[merged['topic_id'] >= 0, 'topic_id'].nunique())

    print("[2] Generando datamapplot base")
    plot = datamapplot.create_interactive_plot(
        coords,
        point_labels,
        hover_text=hover_text,
        title="Mapa temático",
        sub_title=f"{n_topics} tópicos · {n_papers} papers · etiquetas generadas con IA",
        font_family="Inter, system-ui, sans-serif",
        title_font_size=22,
        sub_title_font_size=11,
        cluster_boundary_polygons=False,
        polygon_alpha=2.5,
        color_label_text=True,
        width=1280, height=900,
        enable_search=True,
    )

    base_html_path = DASHBOARD / 'mapa.html'
    plot.save(str(base_html_path))
    html = base_html_path.read_text()
    print(f"    base HTML: {len(html):,} chars")

    # ─────────────────────────────────
    # CRITICAL: expose `datamap` to window so JS injection can access it
    # ─────────────────────────────────
    html = html.replace('const datamap = new DataMap(',
                         'window.datamap = new DataMap(', 1)
    print("    [patch] datamap expuesto a window.datamap")

    # ─────────────────────────────────
    # JS injection
    # ─────────────────────────────────
    # Datos que el JS necesita: cluster_id por punto, lang por punto
    # Los pasamos como JSON inline
    cluster_ids_json = json.dumps(cluster_id_per_point.tolist())
    detail_text_json = json.dumps(detail_text)
    lang_codes = []
    for l in lang_per_point:
        l_lower = str(l).lower()
        if 'spanish' in l_lower or l_lower == 'es':
            lang_codes.append('es')
        elif 'portuguese' in l_lower or l_lower == 'pt':
            lang_codes.append('pt')
        elif 'english' in l_lower or l_lower == 'en':
            lang_codes.append('en')
        else:
            lang_codes.append('?')
    lang_codes_json = json.dumps(lang_codes)

    # RSI total por punto (redondeado a 0.5) para el overlay de color
    rsi_values_json = json.dumps([round(float(v), 2) for v in rsi_per_point.tolist()])
    # RSI medio del tópico por punto (overlay "vecindario")
    topic_rsi_json = json.dumps([round(float(v), 2) for v in topic_rsi_per_point.tolist()])
    # Flag de sub-corpus tesis por punto (0/1)
    is_tesis_json = json.dumps([int(bool(v)) for v in is_tesis_per_point.tolist()])

    # Lista de tópicos para el dropdown
    cluster_options = []
    for tid_str, info in sorted(ai_labels.items(), key=lambda x: -x[1]['n_papers']):
        tid = int(tid_str)
        cluster_options.append({'id': tid, 'label': info['label'].replace('[Artefacto] ', ''),
                                  'n': info['n_papers']})
    cluster_options_json = json.dumps(cluster_options)

    css_addition = """
<style id="revisa-enhancements">
  /* Tooltip override (datamapplot usa .deck-tooltip) */
  .deck-tooltip {
    font-size: 12px !important;
    font-family: Inter, system-ui, sans-serif !important;
    font-weight: 400 !important;
    color: #1a1a1a !important;
    background: rgba(255, 255, 255, 0.98) !important;
    border: 1px solid #d0d7de !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
    padding: 10px 12px !important;
    max-width: 540px !important;
    backdrop-filter: blur(4px);
    z-index: 10000;
  }
  /* Panel persistente al click */
  .revisa-info-panel {
    position: fixed; bottom: 16px; left: 16px; z-index: 9998;
    background: rgba(255,255,255,0.99); border: 1px solid #1a73e8;
    border-radius: 10px; padding: 14px 16px;
    box-shadow: 0 6px 24px rgba(26, 115, 232, 0.25);
    font-family: Inter, system-ui, sans-serif; font-size: 12px;
    color: #1a1a1a;
    width: 580px; max-width: 90vw; max-height: 60vh; overflow-y: auto;
    display: none;
  }
  .revisa-info-panel.visible { display: block; animation: revisa-fade-in 0.2s ease-out; }
  @keyframes revisa-fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .revisa-info-close {
    position: absolute; top: 8px; right: 10px; cursor: pointer;
    background: #f3f4f6; color: #555; border: 1px solid #ddd;
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: bold;
  }
  .revisa-info-close:hover { background: #fee; color: #c00; }
  .revisa-info-header {
    color: #1a73e8; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.3px;
    margin-bottom: 8px; padding-right: 32px;
  }
  /* Panel de control */
  .revisa-panel {
    position: fixed; top: 16px; right: 16px; z-index: 9999;
    background: rgba(255,255,255,0.97); border: 1px solid #ccc;
    border-radius: 8px; padding: 12px 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    font-family: Inter, system-ui, sans-serif; font-size: 13px;
    min-width: 280px; max-width: 340px;
  }
  .revisa-panel h4 {
    margin: 0 0 8px 0; font-size: 13px; color: #1a73e8;
    border-bottom: 1px solid #eee; padding-bottom: 6px;
  }
  .revisa-panel select {
    width: 100%; padding: 6px; border: 1px solid #ccc; border-radius: 4px;
    font-size: 13px; margin-bottom: 8px;
  }
  .revisa-panel button {
    padding: 6px 12px; background: #1a73e8; color: white; border: none;
    border-radius: 4px; cursor: pointer; font-size: 12px;
    margin-right: 4px;
  }
  .revisa-panel button:hover { background: #185abc; }
  .revisa-panel button.secondary { background: #888; }
  .revisa-panel button.secondary:hover { background: #555; }
  .revisa-legend {
    margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;
    font-size: 11px; color: #555;
  }
  .revisa-legend .swatch {
    display: inline-block; width: 12px; height: 12px; border-radius: 50%;
    margin-right: 5px; vertical-align: middle; border: 2px solid #ccc;
  }
  .revisa-status {
    font-size: 11px; color: #888; margin-top: 6px; font-style: italic;
  }
</style>
"""

    panel_html = """
<div class="revisa-panel" id="revisa-panel">
  <h4>Controles REVISA</h4>
  <label style="display:block;font-size:11px;color:#666;margin-bottom:3px">Colorear por:</label>
  <select id="revisa-color-select">
    <option value="topic">Tópico (color original)</option>
    <option value="rsi">Nivel RSI del paper</option>
    <option value="topic_rsi">RSI medio del tópico (vecindario)</option>
  </select>
  <div class="revisa-legend" id="revisa-rsi-legend" style="display:none">
    <b>Nivel RSI (color del punto):</b><br>
    <span class="swatch" style="border-color:#fff;background:#bdbdbd"></span>Mención (gate no pasa)
    &nbsp;<span class="swatch" style="border-color:#fff;background:#ffd166"></span>Nominal / parcial<br>
    <span class="swatch" style="border-color:#fff;background:#52b788"></span>Sustantiva (≥2.5)
    &nbsp;<span class="swatch" style="border-color:#fff;background:#1b6b3a"></span>Sustantiva fuerte (≥3.5)
  </div>
  <div style="margin:8px 0">
    <button id="revisa-tesis-btn" class="secondary" style="background:#9c27b0;width:100%">
      Resaltar sub-corpus de la tesis (n=__N_TESIS__)
    </button>
  </div>
  <label style="display:block;font-size:11px;color:#666;margin:8px 0 3px">Aislar un cluster:</label>
  <select id="revisa-cluster-select">
    <option value="-1">— Mostrar todos —</option>
  </select>
  <div>
    <button id="revisa-isolate-btn">Aislar</button>
    <button id="revisa-reset-btn" class="secondary">Reset</button>
  </div>
  <div class="revisa-legend">
    <b>Contorno por idioma:</b><br>
    <span class="swatch" style="border-color:#d32f2f;background:#fff"></span>ES (español)
    &nbsp;<span class="swatch" style="border-color:#1976d2;background:#fff"></span>PT (portugués)
    &nbsp;<span class="swatch" style="border-color:#9e9e9e;background:#fff"></span>EN (inglés)
  </div>
  <div class="revisa-status" id="revisa-status">Listo</div>
  <div style="font-size:10px;color:#888;margin-top:8px;border-top:1px solid #eee;padding-top:6px">
    <b>Hover:</b> tooltip · <b>Click:</b> panel persistente (para abrir links)
  </div>
</div>

<div class="revisa-info-panel" id="revisa-info-panel">
  <div class="revisa-info-close" id="revisa-info-close" title="Cerrar (Esc)">×</div>
  <div class="revisa-info-header">📌 Paper seleccionado</div>
  <div id="revisa-info-body"></div>
</div>
"""

    panel_html = panel_html.replace('__N_TESIS__', str(int(is_tesis_per_point.sum())))

    custom_js = """
<script id="revisa-enhancements-js">
(function() {
  const CLUSTER_IDS = """ + cluster_ids_json + """;
  const LANG_CODES = """ + lang_codes_json + """;
  const RSI_VALUES = """ + rsi_values_json + """;
  const TOPIC_RSI = """ + topic_rsi_json + """;
  const IS_TESIS = """ + is_tesis_json + """;
  const N_TESIS = IS_TESIS.reduce((a,b)=>a+b, 0);
  const N_TOPICS_TESIS = new Set(CLUSTER_IDS.filter((c, i) => IS_TESIS[i] && c >= 0)).size;
  const DETAIL_TEXT = """ + detail_text_json + """;
  const TESIS_OUTLINE = [156, 39, 176, 255];  // morado para resaltar la tesis
  const CLUSTER_OPTIONS = """ + cluster_options_json + """;
  const LANG_OUTLINE = {
    es: [211, 47, 47, 255],     // rojo
    pt: [25, 118, 210, 255],    // azul
    en: [158, 158, 158, 200],   // gris
    '?': [200, 200, 200, 60]
  };
  const LANG_OUTLINE_WIDTH = { es: 0.006, pt: 0.006, en: 0.0025, '?': 0 };

  // Paleta secuencial por nivel de sustantividad RSI (0–4).
  // El layout y los clusters NO cambian: esto solo recolorea los puntos.
  function rsiColor(v) {
    if (v == null || isNaN(v) || v <= 0)   return [189, 189, 189, 235]; // mención (gate no pasa)
    if (v < 1.5)  return [255, 209, 102, 240]; // nominal
    if (v < 2.5)  return [243, 156, 53, 240];  // parcial
    if (v < 3.5)  return [82, 183, 136, 245];  // sustantiva
    return [27, 107, 58, 250];                 // sustantiva fuerte
  }
  // Modo de color actual: 'topic' (original) | 'rsi' (RSI del paper) | 'topic_rsi' (RSI medio del tópico)
  let colorMode = 'topic';
  // Resalte del sub-corpus de la tesis (atenúa el resto + outline morado)
  let highlightThesis = false;

  function populateDropdown() {
    const sel = document.getElementById('revisa-cluster-select');
    if (!sel) return;
    CLUSTER_OPTIONS.forEach(o => {
      const opt = document.createElement('option');
      opt.value = o.id;
      opt.textContent = 'T' + o.id + ': ' + o.label + ' (n=' + o.n + ')';
      sel.appendChild(opt);
    });
  }

  function setStatus(msg) {
    const s = document.getElementById('revisa-status');
    if (s) s.textContent = msg;
  }

  // Modifica el ScatterplotLayer interno de datamapplot para aplicar
  // outlines per-point (por idioma) y fade per-cluster (atenúa otros)
  function applyStyling(isolatedClusterId) {
    if (!window.datamap || !window.datamap.pointLayer) return false;
    const dm = window.datamap;
    const pl = dm.pointLayer;
    const numPoints = pl.props.data.length;
    if (numPoints !== CLUSTER_IDS.length) {
      console.warn('[REVISA] mismatch: layer has ' + numPoints + ' points, expected ' + CLUSTER_IDS.length);
    }

    // Guardar los colores originales (por tópico) la primera vez
    if (!dm._revisaOriginalColors && dm.originalColors) {
      dm._revisaOriginalColors = dm.originalColors;
    }

    // Construir arrays per-point para outline color/width
    // Por defecto: contorno por idioma. Si "resaltar tesis" está activo, los papers
    // del sub-corpus reciben contorno morado grueso (sobreescribe el de idioma).
    const lineColors = new Uint8Array(numPoints * 4);
    const lineWidths = new Float32Array(numPoints);
    for (let i = 0; i < numPoints; i++) {
      if (highlightThesis && IS_TESIS[i]) {
        lineColors[i*4]   = TESIS_OUTLINE[0];
        lineColors[i*4+1] = TESIS_OUTLINE[1];
        lineColors[i*4+2] = TESIS_OUTLINE[2];
        lineColors[i*4+3] = TESIS_OUTLINE[3];
        lineWidths[i] = 0.012;
      } else {
        const lang = LANG_CODES[i] || '?';
        const col = LANG_OUTLINE[lang] || LANG_OUTLINE['?'];
        lineColors[i*4]   = col[0];
        lineColors[i*4+1] = col[1];
        lineColors[i*4+2] = col[2];
        lineColors[i*4+3] = col[3];
        lineWidths[i] = LANG_OUTLINE_WIDTH[lang] || 0;
      }
    }

    // Construir array de fill color según el modo de color activo
    // 'topic'     → restaura los colores originales (por cluster)
    // 'rsi'       → recolorea por nivel de sustantividad del paper (layout intacto)
    // 'topic_rsi' → recolorea por RSI medio del tópico (vecindarios homogéneos)
    let fillColors = null;
    if (colorMode === 'rsi' || colorMode === 'topic_rsi') {
      const src = (colorMode === 'topic_rsi') ? TOPIC_RSI : RSI_VALUES;
      fillColors = new Uint8Array(numPoints * 4);
      for (let i = 0; i < numPoints; i++) {
        const c = rsiColor(src[i]);
        fillColors[i*4]   = c[0];
        fillColors[i*4+1] = c[1];
        fillColors[i*4+2] = c[2];
        fillColors[i*4+3] = c[3];
      }
    } else if (dm._revisaOriginalColors) {
      fillColors = dm._revisaOriginalColors;
    }

    // Construir array de selected para fade (usa el mecanismo nativo DataFilterExtension)
    // Prioridad: resaltar tesis > aislar cluster > mostrar todos
    const selected = dm.selected;  // Float32Array existente
    if (!selected) return false;
    if (highlightThesis) {
      for (let i = 0; i < numPoints; i++) {
        selected[i] = IS_TESIS[i] ? 1.0 : 0.0;
      }
    } else if (isolatedClusterId === -1) {
      selected.fill(1.0);
    } else {
      for (let i = 0; i < numPoints; i++) {
        selected[i] = (CLUSTER_IDS[i] === isolatedClusterId) ? 1.0 : 0.0;
      }
    }

    // Bump update trigger para forzar re-render
    dm.updateTriggerCounter = (dm.updateTriggerCounter || 0) + 1;

    // Reconstruir el ScatterplotLayer con outline attributes per-point + filter actualizado
    const attrOverrides = {
      getLineColor: { value: lineColors, size: 4 },
      getLineWidth: { value: lineWidths, size: 1 },
      getFilterValue: { value: selected, size: 1 },
    };
    if (fillColors) attrOverrides.getFillColor = { value: fillColors, size: 4 };
    const newAttrs = Object.assign({}, pl.props.data.attributes, attrOverrides);

    const newLayer = pl.clone({
      data: { length: numPoints, attributes: newAttrs },
      stroked: true,
      lineWidthUnits: 'common',
      lineWidthMinPixels: 1.5,
      lineWidthMaxPixels: 5,
      transitions: {},  // desactiva la transición de color de datamapplot al recolorear
      updateTriggers: {
        getLineColor: dm.updateTriggerCounter,
        getLineWidth: dm.updateTriggerCounter,
        getFilterValue: dm.updateTriggerCounter,
        getFillColor: dm.updateTriggerCounter,
      }
    });

    dm.pointLayer = newLayer;
    const idx = dm.layers.indexOf(pl);
    if (idx >= 0) dm.layers[idx] = newLayer;
    else dm.layers.push(newLayer);

    dm.deckgl.setProps({ layers: [...dm.layers] });
    return true;
  }

  let currentIsolated = -1;
  let appliedOnce = false;

  // Sobreescribir tooltipFunction para devolver {html: ...} (deck.gl renderiza HTML)
  function patchTooltipToHTML() {
    if (!window.datamap || !window.datamap.metaData || !window.datamap.metaData.hover_text) return false;
    const hoverArr = window.datamap.metaData.hover_text;
    window.datamap.tooltipFunction = ({index}) => {
      const txt = hoverArr[index];
      if (!txt) return null;
      return { html: txt };
    };
    if (window.datamap.deckgl) {
      window.datamap.deckgl.setProps({ getTooltip: window.datamap.tooltipFunction });
    }
    return true;
  }

  // Panel persistente al click sobre un punto
  // Usa la versión extendida (con justificación del LLM por criterio).
  function showInfoPanel(index) {
    if (!window.datamap || !window.datamap.metaData) return;
    const html = (DETAIL_TEXT && DETAIL_TEXT[index]) || window.datamap.metaData.hover_text[index];
    if (!html) return;
    const body = document.getElementById('revisa-info-body');
    const panel = document.getElementById('revisa-info-panel');
    if (!body || !panel) return;
    body.innerHTML = html;
    panel.classList.add('visible');
  }
  function hideInfoPanel() {
    const panel = document.getElementById('revisa-info-panel');
    if (panel) panel.classList.remove('visible');
  }

  // Inyectar onClick al ScatterplotLayer (datamapplot tiene onClickFunction=null por default)
  function patchClickHandler() {
    if (!window.datamap || !window.datamap.pointLayer) return false;
    const dm = window.datamap;
    const handler = (info) => {
      if (info && typeof info.index === 'number' && info.index >= 0) {
        showInfoPanel(info.index);
      }
    };
    dm.onClickFunction = handler;
    const newLayer = dm.pointLayer.clone({ onClick: handler, pickable: true });
    dm.pointLayer = newLayer;
    const idx = dm.layers.indexOf(dm.layers.find(l => l && l.id === 'dataPointLayer'));
    if (idx >= 0) dm.layers[idx] = newLayer;
    dm.deckgl.setProps({ layers: [...dm.layers] });
    return true;
  }

  function tryInitialApply(retries) {
    if (window.datamap && window.datamap.pointLayer && window.datamap.selected) {
      const ok = applyStyling(-1);
      const ok2 = patchTooltipToHTML();
      const ok3 = patchClickHandler();
      appliedOnce = ok;
      setStatus(
        (ok ? '✓ outlines' : '✗ outlines') + ' · ' +
        (ok2 ? '✓ tooltip HTML' : '✗ tooltip') + ' · ' +
        (ok3 ? '✓ click panel' : '✗ click')
      );
      return;
    }
    if (retries > 0) setTimeout(() => tryInitialApply(retries - 1), 400);
    else setStatus('datamap no inicializado (timeout)');
  }

  // Cerrar panel: botón × y tecla Esc
  function bindPanelClose() {
    const close = document.getElementById('revisa-info-close');
    if (close) close.onclick = hideInfoPanel;
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') hideInfoPanel();
    });
  }

  function init() {
    if (!document.getElementById('revisa-panel')) {
      setTimeout(init, 200); return;
    }
    populateDropdown();

    const colorSel = document.getElementById('revisa-color-select');
    const rsiLegend = document.getElementById('revisa-rsi-legend');
    const isRsiMode = (m) => (m === 'rsi' || m === 'topic_rsi');
    const colorLabel = { topic: 'Color: tópico (original)',
                         rsi: 'Color: nivel RSI del paper',
                         topic_rsi: 'Color: RSI medio del tópico' };
    if (colorSel) {
      colorSel.onchange = () => {
        colorMode = colorSel.value;
        if (rsiLegend) rsiLegend.style.display = isRsiMode(colorMode) ? 'block' : 'none';
        const ok = applyStyling(currentIsolated);
        setStatus(ok ? (colorLabel[colorMode] || '') : 'datamap no listo');
      };
    }

    const tesisBtn = document.getElementById('revisa-tesis-btn');
    if (tesisBtn) {
      tesisBtn.onclick = () => {
        highlightThesis = !highlightThesis;
        tesisBtn.textContent = highlightThesis
          ? 'Quitar resalte de la tesis'
          : 'Resaltar sub-corpus de la tesis (n=' + N_TESIS + ')';
        tesisBtn.style.background = highlightThesis ? '#6a1b7a' : '#9c27b0';
        const ok = applyStyling(currentIsolated);
        setStatus(ok
          ? (highlightThesis ? 'Resaltando tesis (' + N_TESIS + ' papers en ' + N_TOPICS_TESIS + ' tópicos)' : 'Resalte de tesis desactivado')
          : 'datamap no listo');
      };
    }

    document.getElementById('revisa-isolate-btn').onclick = () => {
      const sel = document.getElementById('revisa-cluster-select');
      currentIsolated = parseInt(sel.value);
      const ok = applyStyling(currentIsolated);
      setStatus(ok ? (currentIsolated < 0 ? 'Mostrando todos' : 'Aislado T' + currentIsolated) : 'datamap no listo');
    };
    document.getElementById('revisa-reset-btn').onclick = () => {
      document.getElementById('revisa-cluster-select').value = '-1';
      currentIsolated = -1;
      applyStyling(-1);
      setStatus('Reset');
    };

    bindPanelClose();
    tryInitialApply(30);  // hasta 12s esperando inicialización
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
"""

    # Inyectar antes del </head> (CSS) y antes del </body> (panel + JS)
    if '</head>' in html:
        html = html.replace('</head>', css_addition + '</head>')
    else:
        html = css_addition + html
    if '</body>' in html:
        html = html.replace('</body>', panel_html + custom_js + '</body>')
    else:
        html = html + panel_html + custom_js

    base_html_path.write_text(html)
    print(f"[OK] enhanced → {base_html_path} ({len(html):,} chars)")

    # Copia a assets
    (ASSETS / 'v2_fig10_datamap_interactive.html').write_text(html)
    print(f"[OK] copy → assets/v2_fig10_datamap_interactive.html")


if __name__ == '__main__':
    main()
