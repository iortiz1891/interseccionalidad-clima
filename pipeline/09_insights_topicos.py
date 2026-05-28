#!/usr/bin/env python3
"""
33_v1_topic_insights.py — Insights derivados del mapa temático (RSI v3).

Genera:
  data/v1_topic_stats.json            radiografía por tópico (RSI, gate%, idioma, n, n_tesis)
  assets/v6_figH_topic_ranking.png    ranking de tópicos por RSI medio (barras horizontales)

La idea: la sustantividad (RSI) no se distribuye al azar en el mapa; se concentra
en ciertos vecindarios temáticos. Este script cuantifica esa concentración y ubica
el sub-corpus de la tesis de Daniel (97 papers) dentro de la estructura temática.
"""
from __future__ import annotations
import json
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path("data"); ASSETS = Path("assets")
plt.rcParams.update({'figure.dpi': 100, 'savefig.dpi': 200, 'font.size': 10,
                     'font.family': 'sans-serif'})
NOTE = "RSI v3 (gpt-4.1) · provisional hasta validación humana"


def rsi_color(v):
    """Paleta secuencial por nivel de sustantividad (idéntica al overlay del mapa)."""
    if v is None or (isinstance(v, float) and np.isnan(v)) or v <= 0:
        return '#bdbdbd'
    if v < 1.5:  return '#ffd166'
    if v < 2.5:  return '#f39c35'
    if v < 3.5:  return '#52b788'
    return '#1b6b3a'


def norm_t(s):
    if pd.isna(s): return ''
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', str(s).lower())).strip()


def lang_code(x):
    x = str(x).lower()
    if 'span' in x: return 'ES'
    if 'port' in x: return 'PT'
    if 'eng' in x:  return 'EN'
    return '?'


def main():
    print("[1] Cargando datos")
    f = pd.read_csv(DATA / 'v1_corpus_final.csv')
    labels = json.loads((DATA / 'v1_topic_ai_labels.json').read_text())
    f['bowleg_total'] = pd.to_numeric(f['bowleg_total'], errors='coerce')
    f['lg'] = f['Language of Original Document'].apply(lang_code)

    # Marcar papers del sub-corpus de la tesis (por título normalizado)
    sc = pd.read_csv(DATA / 'v1_daniel_subcorpus.csv')
    sc_titles = set(sc['Title'].apply(norm_t)) - {''}
    f['_t'] = f['Title'].apply(norm_t)
    f['is_tesis'] = f['_t'].isin(sc_titles)

    f = f[f['topic_id'] >= 0].copy()

    def lab(t):
        s = labels.get(str(int(t)))
        return (s['label'].replace('[Artefacto] ', '') if s and s.get('label')
                else f'Tópico {int(t)}')

    print("[2] Computando stats por tópico")
    rows = []
    for tid, g in f.groupby('topic_id'):
        n = len(g)
        rsi = float(g['bowleg_total'].mean())
        rows.append({
            'topic_id': int(tid),
            'label': lab(tid),
            'n': int(n),
            'rsi_mean': round(rsi, 2),
            'gate_pct': round(float((g['bowleg_total'] > 0).mean()) * 100, 0),
            'sust_pct': round(float((g['bowleg_total'] >= 2.5).mean()) * 100, 0),
            'es_pct': round(float((g['lg'] == 'ES').mean()) * 100, 0),
            'en_pct': round(float((g['lg'] == 'EN').mean()) * 100, 0),
            'pt_pct': round(float((g['lg'] == 'PT').mean()) * 100, 0),
            'n_tesis': int(g['is_tesis'].sum()),
        })
    stats = sorted(rows, key=lambda r: -r['rsi_mean'])

    out = {
        'topics': stats,
        'meta': {
            'n_topics': len(stats),
            'n_papers': int(len(f)),
            'rsi_min': min(r['rsi_mean'] for r in stats),
            'rsi_max': max(r['rsi_mean'] for r in stats),
            'n_tesis_total': int(f['is_tesis'].sum()),
            'n_topics_con_tesis': int(sum(1 for r in stats if r['n_tesis'] > 0)),
        }
    }
    (DATA / 'v1_topic_stats.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"    → data/v1_topic_stats.json ({len(stats)} tópicos, "
          f"RSI {out['meta']['rsi_min']:.2f}–{out['meta']['rsi_max']:.2f}, "
          f"tesis dispersa en {out['meta']['n_topics_con_tesis']} tópicos)")

    print("[3] Figura H · ranking de tópicos por RSI medio")
    ds = stats[::-1]  # ascendente para barh (menor abajo→arriba invertido)
    labels_short = [(r['label'][:40] + '…') if len(r['label']) > 40 else r['label'] for r in ds]
    vals = [r['rsi_mean'] for r in ds]
    cols = [rsi_color(v) for v in vals]
    ns = [r['n'] for r in ds]

    fig, ax = plt.subplots(figsize=(11, 11))
    y = np.arange(len(ds))
    ax.barh(y, vals, color=cols, edgecolor='white', linewidth=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([f"T{r['topic_id']} · {l}" for r, l in zip(ds, labels_short)], fontsize=8)
    ax.set_xlim(0, 4.2)
    ax.set_xlabel('RSI medio del tópico (0 = solo mención · 4 = sustantiva fuerte)')
    ax.axvline(2.5, color='#888', ls='--', lw=0.9)
    ax.text(2.52, len(ds) - 0.5, 'umbral sustantivo (2.5)', fontsize=8, color='#666', va='top')
    for i, (v, nn) in enumerate(zip(vals, ns)):
        ax.text(v + 0.05, i, f'{v:.2f}  (n={nn})', va='center', fontsize=7.5, color='#333')

    # leyenda de niveles
    from matplotlib.patches import Patch
    leg = [Patch(facecolor='#bdbdbd', label='Mención (0)'),
           Patch(facecolor='#ffd166', label='Nominal (<1.5)'),
           Patch(facecolor='#f39c35', label='Parcial (1.5–2.5)'),
           Patch(facecolor='#52b788', label='Sustantiva (2.5–3.5)'),
           Patch(facecolor='#1b6b3a', label='Sustantiva fuerte (≥3.5)')]
    ax.legend(handles=leg, loc='lower right', fontsize=8, frameon=True)
    ax.set_title('La sustantividad se concentra: ranking de tópicos por RSI medio',
                 fontsize=13, fontweight='bold', pad=12)
    fig.text(0.5, 0.005, NOTE, ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.02, 1, 0.98])
    plt.savefig(ASSETS / 'v6_figH_topic_ranking.png', bbox_inches='tight'); plt.close()
    print("    → assets/v6_figH_topic_ranking.png")


if __name__ == '__main__':
    main()
