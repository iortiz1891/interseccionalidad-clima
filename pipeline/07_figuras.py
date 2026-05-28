#!/usr/bin/env python3
"""
20_v1_figures.py — Fase 5: figuras para manuscrito v6.

Outputs en assets/:
  v6_fig01_prisma.png         flujo PRISMA (Scopus EN + ES)
  v6_fig02_bowleg_distribution.png  distribución de la RSI
  v6_fig03_years.png          papers por año
  v6_fig04_topics_x_bowleg.png  tópicos × RSI estratificado
  v6_fig05_lang_x_bowleg.png  asimetría EN/ES/PT
  v6_fig06_country_x_bowleg.png  top 15 países
  v6_fig07_year_x_bowleg.png  tendencia temporal del rigor
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import json

DATA = Path("data")
ASSETS = Path("assets")
ASSETS.mkdir(exist_ok=True)

plt.rcParams.update({
    'figure.dpi': 100,
    'savefig.dpi': 200,
    'font.size': 10,
    'font.family': 'sans-serif',
})

PROVISIONAL_NOTE = "Scoring RSI v3 (gpt-4.1) · provisional hasta validación humana"


# ─────────────────────────────────
# Fig 01 — PRISMA v6
# ─────────────────────────────────
def fig01_prisma():
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(0, 10); ax.set_ylim(0, 14); ax.axis('off')

    def box(x, y, w, h, txt, color='#e8f0fe', fontsize=9):
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1", linewidth=1.2,
            facecolor=color, edgecolor='#1a73e8'
        )
        ax.add_patch(rect)
        ax.text(x+w/2, y+h/2, txt, ha='center', va='center', fontsize=fontsize)

    def arrow(x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle='->', lw=1.5, color='#5f6368'))

    # Cargar metadata real de la rama Daniel
    import json as _json
    meta = _json.loads((DATA / 'daniel_prisma_meta.json').read_text())
    fuentes = meta['fuentes']
    f_items = list(fuentes.items())
    bruto = meta['bruto']; sin_abs = meta['sin_abstract']; dups = meta['dups']; final = meta['final']
    cats = meta['categorias_pct']

    # Identificación — solo las 2 bases de Daniel
    box(0.5, 12.5, 9, 1, f"IDENTIFICACIÓN — bases construidas por Daniel ({len(f_items)} fuentes Scopus)", color='#fff3e0')
    box(2.0, 10.5, 2.6, 1.5, f"{f_items[0][0]}\nn={f_items[0][1]}")
    box(5.4, 10.5, 2.6, 1.5, f"{f_items[1][0]}\nn={f_items[1][1]}")

    # Bruto
    box(3, 9, 4, 0.7, f"Total identificado: {bruto} papers", color='#e8f5e9')
    arrow(5, 10.4, 5, 9.7)

    # Filtro abstract
    box(3, 7.5, 4, 1, f"Filtro abstract ≥100 chars\n−{sin_abs} sin abstract usable", color='#fff9c4')
    arrow(5, 9, 5, 8.5)

    # Dedup
    box(3, 6, 4, 1, f"Dedup DOI + título\n−{dups} duplicados", color='#fff9c4')
    arrow(5, 7.5, 5, 7)

    # Corpus consolidado
    box(2, 4, 6, 1.5, f"CORPUS DANIEL CONSOLIDADO\nn = {final} papers", color='#c8e6c9', fontsize=11)
    arrow(5, 6, 5, 5.5)

    # RSI scoring
    box(2, 2, 6, 1.5, f"Scoring RSI v3 (gpt-4.1)\n{final} papers · sin exclusión (gate + 6 criterios)", color='#bbdefb')
    arrow(5, 4, 5, 3.5)

    # Categorías
    cat_order = [('mencion_sin_aplicacion','mención sin aplicación'), ('nominal_debil','nominal/débil'),
                 ('parcial','parcial'), ('sustantivo','sustantivo'), ('sustantivo_fuerte','sustantivo fuerte')]
    cat_str = " · ".join(f"{cats.get(k,0)}% {lbl}" for k, lbl in cat_order)
    box(0.5, 0.3, 9, 1.3, f"Categorías RSI (provisional):\n{cat_str}", color='#e1bee7', fontsize=9)

    ax.set_title("PRISMA — Rama Daniel · interseccionalidad × cambio climático",
                  fontsize=13, fontweight='bold', pad=10)
    ax.text(0.5, -0.5, PROVISIONAL_NOTE, transform=ax.transAxes,
             ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout()
    plt.savefig(ASSETS / 'v6_fig01_prisma.png', bbox_inches='tight')
    plt.close()
    print("[fig 01] PRISMA")


# ─────────────────────────────────
# Fig 02 — Distribución RSI
# ─────────────────────────────────
def fig02_bowleg_dist():
    """Distribución RSI del corpus Daniel (autocontenida, sin comparación externa)."""
    scored = pd.read_csv(DATA / 'v1_corpus_scored.csv')
    levels = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    counts = [(scored['bowleg_total'] == l).sum() for l in levels]
    pct = [100*c/len(scored) for c in counts]

    # Color por categoría
    def col(l):
        if l >= 3.5: return '#1b5e20'
        if l >= 2.5: return '#66bb6a'
        if l >= 1.5: return '#ffa726'
        if l > 0:    return '#ef5350'
        return '#8d6e63'
    colors = [col(l) for l in levels]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.bar([str(l) for l in levels], pct, color=colors, edgecolor='white', linewidth=0.6)
    for b, p in zip(bars, pct):
        if p > 0:
            ax.text(b.get_x()+b.get_width()/2, p+0.5, f'{p:.1f}%', ha='center', fontsize=8)
    ax.set_xlabel('Puntaje RSI (0 = mención sin aplicación · 4 = sustantiva fuerte)')
    ax.set_ylabel('% del corpus')
    ax.set_title(f'Distribución RSI — corpus Daniel (n={len(scored)})')
    ax.axvline(4.5, color='gray', linestyle='--', alpha=0.5)
    ax.text(4.5, max(pct)*0.9, 'umbral sustantivo\n(≥2.5) →', ha='right', fontsize=8, color='gray')
    ax.grid(axis='y', alpha=0.3)
    fig.text(0.5, 0.01, PROVISIONAL_NOTE, ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(ASSETS / 'v6_fig02_bowleg_distribution.png', bbox_inches='tight')
    plt.close()
    print("[fig 02] Distribución RSI (Daniel)")


# ─────────────────────────────────
# Fig 03 — Papers por año
# ─────────────────────────────────
def fig03_years():
    df = pd.read_csv(DATA / 'v1_corpus_scored.csv')
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    by_year = df['Year'].value_counts().sort_index()
    by_year = by_year[(by_year.index >= 2000) & (by_year.index <= 2026)]

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(by_year.index, by_year.values, color='#1976d2', alpha=0.85)
    ax.set_xlabel('Año')
    ax.set_ylabel('Papers')
    ax.set_title(f'Producción anual — corpus Daniel (n={len(df):,})')
    ax.grid(axis='y', alpha=0.3)
    # Anotar 2026 si parcial
    (ax.text(2026, by_year.loc[2026.0] + 30, '(parcial)',
             ha='center', fontsize=8, color='gray') if 2026.0 in by_year.index else None)
    plt.tight_layout()
    plt.savefig(ASSETS / 'v6_fig03_years.png', bbox_inches='tight')
    plt.close()
    print("[fig 03] Years")


# ─────────────────────────────────
# Fig 04 — Topics × Bowleg estratificado
# ─────────────────────────────────
def fig04_topics_x_bowleg():
    tb = pd.read_csv(DATA / 'v1_topics_x_bowleg.csv')
    # Filtrar outliers y top 25 tópicos por tamaño
    tb = tb[tb['topic_id_clean'] >= 0].copy()
    tb = tb.head(25)
    # Etiqueta corta
    tb['short_label'] = tb['topic_name'].fillna('').str.split('_').str[1:4].str.join('/').str[:35]
    tb = tb.sort_values('pct_substantive', ascending=True)

    fig, ax = plt.subplots(figsize=(12, 10))
    colors = plt.cm.RdYlGn(tb['pct_substantive']/100)
    bars = ax.barh(range(len(tb)), tb['pct_substantive'], color=colors,
                    edgecolor='black', linewidth=0.5)
    ax.set_yticks(range(len(tb)))
    ax.set_yticklabels([f"T{int(t['topic_id_clean'])}: {t['short_label']} (n={int(t['n_papers'])})"
                         for _, t in tb.iterrows()], fontsize=8)
    ax.set_xlabel('% papers con interseccionalidad sustantiva (RSI ≥ 2.5)')
    ax.set_title('Topics × sustantividad interseccional (top 25 tópicos del corpus v1)')
    ax.axvline(50, color='gray', linestyle='--', alpha=0.5)
    for i, v in enumerate(tb['pct_substantive']):
        ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=7)
    ax.set_xlim(0, 100)
    ax.grid(axis='x', alpha=0.3)
    fig.text(0.5, 0.01, PROVISIONAL_NOTE, ha='center', fontsize=8,
              style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(ASSETS / 'v6_fig04_topics_x_bowleg.png', bbox_inches='tight')
    plt.close()
    print("[fig 04] Topics × Bowleg")


# ─────────────────────────────────
# Fig 05 — Idioma × Bowleg
# ─────────────────────────────────
def fig05_lang_x_bowleg():
    lb = pd.read_csv(DATA / 'v1_lang_x_bowleg.csv')
    lb.rename(columns={lb.columns[0]: 'lang'}, inplace=True)
    lb = lb[lb['n'] >= 30].copy()
    # Renombrar Unknown
    lb['lang_display'] = lb['lang'].replace({'Unknown':'Sin etiqueta (OpenAlex EN)'})

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    # Panel 1: % sustantivo
    ax = axes[0]
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(lb)))
    ax.bar(range(len(lb)), lb['pct_substantive'], color=colors)
    ax.set_xticks(range(len(lb)))
    ax.set_xticklabels(lb['lang_display'], rotation=20, ha='right')
    ax.set_ylabel('% sustantivo (RSI ≥ 2.5)')
    ax.set_title('Sustantividad por idioma del documento')
    for i, (v, n) in enumerate(zip(lb['pct_substantive'], lb['n'])):
        ax.text(i, v + 1, f'{v:.0f}%\n(n={int(n)})', ha='center', fontsize=8)
    ax.grid(axis='y', alpha=0.3)

    # Panel 2: bowleg medio
    ax = axes[1]
    ax.bar(range(len(lb)), lb['bowleg_mean'], color=colors)
    ax.set_xticks(range(len(lb)))
    ax.set_xticklabels(lb['lang_display'], rotation=20, ha='right')
    ax.set_ylabel('RSI media')
    ax.set_title('RSI promedio por idioma')
    ax.axhline(2.5, color='red', linestyle='--', alpha=0.5, label='umbral sustantivo')
    for i, v in enumerate(lb['bowleg_mean']):
        ax.text(i, v + 0.05, f'{v:.2f}', ha='center', fontsize=8)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    fig.suptitle('Asimetría EN/ES/PT en sustantividad interseccional', fontsize=12, fontweight='bold')
    fig.text(0.5, 0.01, PROVISIONAL_NOTE, ha='center', fontsize=8,
              style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(ASSETS / 'v6_fig05_lang_x_bowleg.png', bbox_inches='tight')
    plt.close()
    print("[fig 05] Idioma × Bowleg")


# ─────────────────────────────────
# Fig 06 — País × Bowleg
# ─────────────────────────────────
def fig06_country_x_bowleg():
    cb = pd.read_csv(DATA / 'v1_country_x_bowleg.csv')
    cb = cb.head(15).sort_values('pct_substantive')
    fig, ax = plt.subplots(figsize=(11, 7))
    colors = plt.cm.RdYlGn(cb['pct_substantive']/100)
    ax.barh(range(len(cb)), cb['pct_substantive'], color=colors, edgecolor='black', linewidth=0.5)
    ax.set_yticks(range(len(cb)))
    ax.set_yticklabels([f"{c['country']} (n={int(c['n'])})" for _, c in cb.iterrows()])
    ax.set_xlabel('% sustantivo (RSI ≥ 2.5)')
    ax.set_title('Sustantividad por país (top 15 por volumen de papers)')
    ax.axvline(50, color='gray', linestyle='--', alpha=0.5)
    for i, v in enumerate(cb['pct_substantive']):
        ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=8)
    ax.grid(axis='x', alpha=0.3)
    fig.text(0.5, 0.01, PROVISIONAL_NOTE, ha='center', fontsize=8,
              style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(ASSETS / 'v6_fig06_country_x_bowleg.png', bbox_inches='tight')
    plt.close()
    print("[fig 06] País × Bowleg")


# ─────────────────────────────────
# Fig 07 — Año × Bowleg
# ─────────────────────────────────
def fig07_year_trend():
    yb = pd.read_csv(DATA / 'v1_year_x_bowleg.csv')
    yb = yb[(yb['Year'] >= 2010) & (yb['n'] >= 20)].copy()
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax2 = ax1.twinx()
    ax1.bar(yb['Year'], yb['n'], color='#1976d2', alpha=0.45, label='n papers')
    ax2.plot(yb['Year'], yb['pct_substantive'], 'o-', color='#d32f2f', linewidth=2,
              markersize=7, label='% sustantivo')
    ax1.set_xlabel('Año')
    ax1.set_ylabel('Número de papers', color='#1976d2')
    ax2.set_ylabel('% sustantivo (RSI ≥ 2.5)', color='#d32f2f')
    ax1.set_title('Tendencia temporal: volumen y rigor del campo')
    ax1.grid(axis='y', alpha=0.3)
    fig.text(0.5, 0.01, PROVISIONAL_NOTE, ha='center', fontsize=8,
              style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(ASSETS / 'v6_fig07_year_trend.png', bbox_inches='tight')
    plt.close()
    print("[fig 07] Year trend")


if __name__ == '__main__':
    fig01_prisma()
    fig02_bowleg_dist()
    fig03_years()
    fig04_topics_x_bowleg()
    fig05_lang_x_bowleg()
    fig06_country_x_bowleg()
    fig07_year_trend()
    print("\n[OK] 7 figuras guardadas en assets/v6_*.png")
