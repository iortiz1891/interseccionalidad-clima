#!/usr/bin/env python3
"""
09b_mapa_estatico.py — v4: mapa temático estático (PNG) y versión alternativa en Plotly.

En la v1, estos archivos (assets/v6_fig09_topic_map*.{png,html}) los generó un paso que
no está en el repo. Este script los produce para la v4 con el mismo formato:
  assets/v4_fig09_topic_map.png               datamapplot estático, etiquetas en el perímetro
  assets/v4_fig09_topic_map_interactive.html  Plotly, página completa
  assets/v4_fig09_topic_map_embed.html        Plotly, fragmento que incrusta el dashboard
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import datamapplot
import plotly.express as px

DATA = Path("data"); ASSETS = Path("assets")


def main():
    asg = pd.read_csv(DATA / 'v4_bertopic_assignments.csv')
    final = pd.read_csv(DATA / 'v4_corpus_final.csv')[['paper_id', 'Title', 'Year', 'bowleg_total', 'categoria_bowleg']]
    labels = json.loads((DATA / 'v4_topic_ai_labels.json').read_text())
    m = asg.merge(final, on='paper_id', how='inner')
    m['label'] = [labels.get(str(int(t)), {}).get('label', 'Unlabelled') if t >= 0 else 'Unlabelled'
                  for t in m['topic_id']]
    counts = m.loc[m['topic_id'] >= 0, 'label'].value_counts()

    # ── PNG estático (datamapplot) ──
    lab_n = {l: f"{l} (n={n})" for l, n in counts.items()}
    point_labels = m['label'].map(lambda l: lab_n.get(l, 'Unlabelled')).to_numpy()
    fig, ax = datamapplot.create_plot(
        m[['umap_x', 'umap_y']].to_numpy(), point_labels,
        title="Mapa temático del corpus REVISA v4",
        title_keywords={'fontsize': 20, 'fontweight': 'bold'},
        add_glow=False, point_size=10,
        label_wrap_width=22, figsize=(16, 12), dpi=100, font_family="DejaVu Sans")
    fig.text(0.5, 0.02, f"n = {len(m):,} papers · {len(counts)} tópicos BERTopic · "
                        f"todos los clusters etiquetados (n=tamaño del tópico)",
             ha='center', fontsize=10, style='italic', color='gray')
    fig.savefig(ASSETS / 'v4_fig09_topic_map.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("  → assets/v4_fig09_topic_map.png")

    # ── Plotly (alternativo) ──
    m['Título'] = m['Title'].fillna('').str.split(r';\s*\[').str[0].str.slice(0, 110)
    m['Año'] = pd.to_numeric(m['Year'], errors='coerce').astype('Int64')
    m['RSI'] = m['bowleg_total']
    order = list(counts.index) + ['Unlabelled']
    figp = px.scatter(m, x='umap_x', y='umap_y', color='label', category_orders={'label': order},
                      hover_data={'Título': True, 'Año': True, 'RSI': True, 'label': False,
                                  'umap_x': False, 'umap_y': False},
                      width=1280, height=920)
    figp.update_traces(marker=dict(size=6, opacity=0.8, line=dict(width=0.5, color='white')))
    figp.update_layout(
        title=f"Mapa temático v4 · {len(counts)} tópicos · {len(m):,} papers",
        legend_title_text="Tópicos<br><span style='font-size:11px'>(clic para ocultar, doble clic para aislar)</span>",
        xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor='white',
        font=dict(family='Inter, system-ui, sans-serif', size=12))
    figp.write_html(ASSETS / 'v4_fig09_topic_map_interactive.html', include_plotlyjs='cdn')
    (ASSETS / 'v4_fig09_topic_map_embed.html').write_text(
        figp.to_html(full_html=False, include_plotlyjs='cdn', div_id='topicmap_v4'))
    print("  → assets/v4_fig09_topic_map_interactive.html · assets/v4_fig09_topic_map_embed.html")


if __name__ == '__main__':
    main()
