#!/usr/bin/env python3
"""
06_figuras.py — v2: figuras del dashboard (equivalentes a 07, 08 y 09 de la v1).

Paleta: rampa ordinal de un solo tono (azul) para los niveles de la RSI, con gris
neutro para "mención sin aplicación"; azul/naranja para comparaciones de dos
series. La tendencia temporal va en dos paneles (sin doble eje).

Salidas en assets/v2_*.png, data/v2_topic_stats.json y data/v2_casos_ejemplares.json.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

DATA = Path("data")
ASSETS = Path("assets")
NOTE = "RSI v3 aplicada por Claude (claude-opus-5-5) · provisional hasta validación humana"

INK, INK2, GRID = '#1f2937', '#52514e', '#e5e7eb'
NEUTRAL = '#c9c8c3'                                     # mención sin aplicación / "no cumple"
RAMP = ['#86b6ef', '#5598e7', '#256abf', '#104281']     # nominal → parcial → sustantiva → fuerte
SERIES = ['#2a78d6', '#eb6834', '#1baf7a']
CAT_ORDER = ['mencion_sin_aplicacion', 'nominal_debil', 'parcial', 'sustantivo', 'sustantivo_fuerte']
CAT_LABEL = {'mencion_sin_aplicacion': 'Mención sin aplicación (0)', 'nominal_debil': 'Nominal/débil (0.5–1)',
             'parcial': 'Parcial (1.5–2)', 'sustantivo': 'Sustantiva (2.5–3)',
             'sustantivo_fuerte': 'Sustantiva fuerte (3.5–4)'}
CAT_COLOR = dict(zip(CAT_ORDER, [NEUTRAL] + RAMP))
CRITS = [('bowleg_I', 'I · Identidades entrelazadas'), ('bowleg_II', 'II · Poder estructural'),
         ('bowleg_III', 'III · Contexto situado'), ('bowleg_IV', 'IV · Método no aditivo'),
         ('rsi_V', 'V · Praxis y justicia'), ('rsi_VI', 'VI · Agencia y resistencia')]
TIPO_LABEL = {'empirico_cuantitativo': 'Empírico cuantitativo', 'empirico_cualitativo': 'Empírico cualitativo',
              'empirico_mixto': 'Empírico mixto', 'conceptual_teorico': 'Conceptual / teórico',
              'revision': 'Revisión', 'otro': 'Otro (editorial, nota…)'}
AMENAZA_LABEL = {'cambio_climatico_general': 'Cambio climático (general)',
                 'ciclon_huracan_tormenta': 'Ciclones, huracanes, tormentas', 'inundacion': 'Inundaciones',
                 'sequia': 'Sequías', 'calor_extremo': 'Calor extremo', 'incendio_forestal': 'Incendios forestales',
                 'nivel_mar_costas': 'Nivel del mar y costas', 'glaciares_criosfera': 'Glaciares y criósfera',
                 'desastres_multiples': 'Desastres (varios)', 'mitigacion_transicion': 'Mitigación y transición',
                 'otro': 'Otro'}

plt.rcParams.update({'figure.dpi': 100, 'savefig.dpi': 200, 'font.size': 10, 'font.family': 'sans-serif',
                     'text.color': INK, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.edgecolor': GRID, 'axes.spines.top': False, 'axes.spines.right': False})


def rsi_cat(v: float) -> str:
    if v >= 3.5: return 'sustantivo_fuerte'
    if v >= 2.5: return 'sustantivo'
    if v >= 1.5: return 'parcial'
    if v > 0: return 'nominal_debil'
    return 'mencion_sin_aplicacion'


def save(fig, name: str):
    fig.text(0.5, 0.005, NOTE, ha='center', fontsize=7.5, style='italic', color=INK2)
    fig.savefig(ASSETS / f'v2_{name}.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  → assets/v2_{name}.png")


def hgrid(ax, axis='y'):
    ax.grid(axis=axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


# ── 01 · PRISMA ──
def fig01_prisma(meta):
    fig, ax = plt.subplots(figsize=(10, 11.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 13.2); ax.axis('off')

    def box(x, y, w, h, txt, fc='#eef4fc', ec='#256abf', fs=9.5, bold=False):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                             lw=1.1, facecolor=fc, edgecolor=ec))
        ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center', fontsize=fs,
                fontweight='bold' if bold else 'normal', color=INK)

    def arrow(x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='->', lw=1.3, color=INK2))

    ex, cr, rs = meta['excluidos_regla'], meta['cribado'], meta['rsi']
    box(1.5, 11.6, 5, 1.1, f"IDENTIFICACIÓN\nScopus · cadena bilingüe v2 · 30-09-2026\nn = {meta['identificados_scopus']:,}",
        fc='#fff4e5', ec='#eb6834', bold=True)
    box(7.0, 10.2, 2.8, 1.3, f"Excluidos por regla\n−{ex['sin_abstract']} sin abstract\n−{ex['erratum_o_conference_review']} erratum / conf. review",
        fc='#f5f5f4', ec=NEUTRAL, fs=8.5)
    box(1.5, 9.6, 5, 0.9, f"Tras reglas y deduplicación (−{meta['duplicados']} duplicados)\nn = {meta['a_cribado']:,}")
    arrow(4, 11.6, 4, 10.5); arrow(6.5, 12.1, 7.0, 10.9)
    box(1.5, 7.6, 5, 1.2, f"CRIBADO DE ELEGIBILIDAD\n¿invoca la interseccionalidad en sentido social?\n¿su objeto es climático?", bold=False)
    arrow(4, 9.6, 4, 8.8)
    box(7.0, 6.9, 2.8, 2.2, f"Excluidos\nn = {cr['excluidos']}\n\n{cr['solo_no_interseccional']} no interseccional\n"
        f"{cr['solo_no_climatico']} no climático\n{cr['ambos']} ninguno de los dos",
        fc='#f5f5f4', ec=NEUTRAL, fs=8.5)
    arrow(6.5, 8.2, 7.0, 8.0)
    box(1.5, 5.4, 5, 1.2, f"CORPUS ELEGIBLE\nn = {cr['elegibles']:,}", fc='#dbe9fb', bold=True, fs=11)
    arrow(4, 7.6, 4, 6.6)
    box(1.5, 3.4, 5, 1.2, f"RSI v3 (gate + 6 criterios + integración)\n{rs['gate_pass']:,} pasan el gate "
        f"({100 * rs['gate_pass'] / cr['elegibles']:.0f}%)")
    arrow(4, 5.4, 4, 4.6)
    cats = rs['categorias_pct']
    txt = "  ·  ".join(f"{cats.get(k, 0):.0f}% {CAT_LABEL[k].split(' (')[0].lower()}" for k in CAT_ORDER)
    box(0.3, 1.4, 9.4, 1.2, f"Categorías RSI (provisional)\n{txt}", fc='#f8fafc', ec=GRID, fs=8.5)
    arrow(4, 3.4, 4, 2.6)
    ax.set_title("Flujo PRISMA · v2 (búsqueda ampliada)", fontsize=13, fontweight='bold', pad=6)
    save(fig, 'fig01_prisma')


# ── 02 · Distribución RSI ──
def fig02_dist(df):
    levels = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    pct = [100 * (df['bowleg_total'] == l).mean() for l in levels]
    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar([str(l) for l in levels], pct, color=[CAT_COLOR[rsi_cat(l)] for l in levels],
                  edgecolor='white', linewidth=2, width=0.72)
    for b, p in zip(bars, pct):
        if p > 0:
            ax.text(b.get_x() + b.get_width() / 2, p + 0.6, f'{p:.1f}%', ha='center', fontsize=8.5, color=INK)
    ax.set_xlabel('Puntaje RSI (0 = mención sin aplicación · 4 = sustantiva fuerte)')
    ax.set_ylabel('% del corpus elegible')
    ax.set_title(f'Distribución de la RSI · v2 (n = {len(df):,})', fontweight='bold')
    handles = [mpatches.Patch(color=CAT_COLOR[k], label=CAT_LABEL[k]) for k in CAT_ORDER]
    ax.legend(handles=handles, fontsize=8, frameon=False, loc='upper center', ncol=3)
    ax.set_ylim(0, max(pct) * 1.25)
    hgrid(ax)
    save(fig, 'fig02_distribucion')


# ── 03 · Producción anual ──
def fig03_years(df):
    y = pd.to_numeric(df['Year'], errors='coerce').dropna().astype(int).value_counts().sort_index()
    y = y[y.index >= 2000]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.bar(y.index, y.values, color=SERIES[0], edgecolor='white', linewidth=1.5, width=0.8)
    for yr in (y.index.max(),):
        ax.text(yr, y.loc[yr] + max(y) * 0.02, '(parcial)', ha='center', fontsize=8, color=INK2)
    ax.set_xlabel('Año'); ax.set_ylabel('Trabajos elegibles')
    ax.set_title(f'Producción anual · v2 (n = {len(df):,})', fontweight='bold')
    hgrid(ax)
    save(fig, 'fig03_anios')


# ── 04 · Tópicos × % sustantivo ──
def fig04_topics(tb):
    t = tb[tb['topic_id'] >= 0].sort_values('n', ascending=False).head(25).sort_values('pct_substantive')
    fig, ax = plt.subplots(figsize=(11.5, 9.5))
    ax.barh(range(len(t)), t['pct_substantive'], color=SERIES[0], edgecolor='white', linewidth=1.5, height=0.72)
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels([f"T{int(r.topic_id)} · {r.topic_label[:48]} (n={int(r.n)})" for r in t.itertuples()], fontsize=8)
    for i, v in enumerate(t['pct_substantive']):
        ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=7.5, color=INK)
    ax.set_xlim(0, 100); ax.set_xlabel('% con aplicación sustantiva (RSI ≥ 2.5)')
    ax.set_title('Tópicos × sustantividad (25 tópicos más grandes)', fontweight='bold')
    hgrid(ax, 'x')
    save(fig, 'fig04_topicos')


# ── 05 · Idioma ──
def fig05_lang(lb):
    lb = lb.reset_index().rename(columns={lb.index.name or 'index': 'idioma'})
    lb['lbl'] = lb['idioma'].map({'en': 'Inglés', 'es': 'Español'}).fillna(lb['idioma'])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, col, ttl, fmt in [(axes[0], 'pct_substantive', '% sustantivo (RSI ≥ 2.5)', '{:.0f}%'),
                              (axes[1], 'bowleg_mean', 'RSI media', '{:.2f}')]:
        ax.bar(lb['lbl'], lb[col], color=SERIES[:len(lb)], edgecolor='white', linewidth=2, width=0.55)
        for i, (v, n) in enumerate(zip(lb[col], lb['n'])):
            ax.text(i, v * 1.02 + (0.02 if col == 'bowleg_mean' else 0.5), fmt.format(v) + f'\n(n={int(n)})',
                    ha='center', fontsize=8.5)
        ax.set_title(ttl, fontsize=10.5); hgrid(ax)
        ax.set_ylim(0, lb[col].max() * 1.3)
    fig.suptitle('Sustantividad por idioma del documento', fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    save(fig, 'fig05_idioma')


# ── 06 · Lugar del estudio ──
def fig06_lugares(cb):
    c = cb[~cb.index.isin(['Global', 'No especificado'])].head(15).sort_values('pct_substantive')
    fig, ax = plt.subplots(figsize=(11, 6.8))
    ax.barh(range(len(c)), c['pct_substantive'], color=SERIES[0], edgecolor='white', linewidth=1.5, height=0.7)
    ax.set_yticks(range(len(c)))
    ax.set_yticklabels([f"{k} (n={int(r.n)})" for k, r in c.iterrows()], fontsize=9)
    for i, v in enumerate(c['pct_substantive']):
        ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=8)
    ax.set_xlim(0, 100); ax.set_xlabel('% sustantivo (RSI ≥ 2.5)')
    ax.set_title('Sustantividad por lugar del estudio (15 lugares con más trabajos)', fontweight='bold')
    hgrid(ax, 'x')
    save(fig, 'fig06_lugares')


# ── 07 · Tendencia temporal (dos paneles, sin doble eje) ──
def fig07_trend(yb):
    y = yb[(yb.index >= 2010)]
    y = y[y['n'] >= 10]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.8), sharex=True, gridspec_kw={'height_ratios': [1, 1]})
    a1.bar(y.index, y['n'], color=SERIES[0], edgecolor='white', linewidth=1.5, width=0.8)
    a1.set_ylabel('Trabajos'); a1.set_title('Volumen anual', fontsize=10.5, loc='left'); hgrid(a1)
    a2.plot(y.index, y['pct_substantive'], '-o', color=SERIES[0], lw=2, ms=6, mec='white', mew=1.5)
    for x, v in zip(y.index, y['pct_substantive']):
        a2.text(x, v + 2.5, f'{v:.0f}%', ha='center', fontsize=7.5)
    a2.set_ylim(0, 100); a2.set_ylabel('% sustantivo (RSI ≥ 2.5)')
    a2.set_title('Proporción con aplicación sustantiva', fontsize=10.5, loc='left'); hgrid(a2)
    a2.set_xlabel('Año (años con ≥ 10 trabajos; el último es parcial)')
    fig.suptitle('Tendencia temporal: volumen y rigor', fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    save(fig, 'fig07_tendencia')


# ── A · Perfil por criterio ──
def figA(df):
    gate = df[df['gate_pass'] == True]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), sharey=True)
    for ax, sub, ttl in [(axes[0], df, f'Corpus elegible (n = {len(df):,})'),
                         (axes[1], gate, f'Solo los que pasan el gate (n = {len(gate):,})')]:
        p0 = [100 * (sub[c] == 0).mean() for c, _ in CRITS]
        p5 = [100 * (sub[c] == 0.5).mean() for c, _ in CRITS]
        p1 = [100 * (sub[c] == 1).mean() for c, _ in CRITS]
        yy = np.arange(len(CRITS))
        ax.barh(yy, p0, color=NEUTRAL, edgecolor='white', linewidth=2, label='No (0)')
        ax.barh(yy, p5, left=p0, color=RAMP[0], edgecolor='white', linewidth=2, label='Parcial (0.5)')
        ax.barh(yy, p1, left=np.add(p0, p5), color=RAMP[2], edgecolor='white', linewidth=2, label='Cumple (1)')
        for i, v in enumerate(p1):
            ax.text(99, i, f'{v:.0f}% cumple', va='center', ha='right', fontsize=8.5, color='white', fontweight='bold')
        ax.set_yticks(yy); ax.set_yticklabels([l for _, l in CRITS], fontsize=9)
        ax.set_xlim(0, 100); ax.set_xlabel('% de trabajos'); ax.set_title(ttl, fontsize=10.5)
        ax.invert_yaxis()
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.02))
    fig.suptitle('Perfil de cumplimiento por criterio de la RSI', fontweight='bold')
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    save(fig, 'figA_criterios')


# ── B · Embudo ──
def figB(df):
    n = len(df)
    stages = [('Corpus elegible', n, NEUTRAL), ('Pasan el gate', int((df['gate_pass'] == True).sum()), RAMP[0]),
              ('Sustantiva (RSI ≥ 2.5)', int((df['bowleg_total'] >= 2.5).sum()), RAMP[2]),
              ('Sustantiva fuerte (RSI ≥ 3.5)', int((df['bowleg_total'] >= 3.5).sum()), RAMP[3])]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for i, (lbl, v, c) in enumerate(stages):
        ax.barh(i, v / n, color=c, height=0.62, edgecolor='white')
        ax.text(v / n + 0.01, i, f'{v:,}  ({100 * v / n:.0f}%)', va='center', fontsize=10.5, fontweight='bold')
        ax.text(-0.01, i, lbl, va='center', ha='right', fontsize=9.5)
    ax.set_xlim(0, 1.18); ax.invert_yaxis(); ax.axis('off')
    ax.set_title('Embudo de sustantividad interseccional · v2', fontweight='bold')
    save(fig, 'figB_embudo')


# ── D · Correlación entre criterios ──
def figD(df):
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('div', ['#d03b3b', '#f0efec', '#2a78d6'])
    gate = df[df['gate_pass'] == True]
    corr = gate[[c for c, _ in CRITS]].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1)
    short = ['I', 'II', 'III', 'IV', 'V', 'VI']
    ax.set_xticks(range(6)); ax.set_yticks(range(6)); ax.set_xticklabels(short); ax.set_yticklabels(short)
    for i in range(6):
        for j in range(6):
            ax.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center', fontsize=9,
                    color='white' if abs(corr.iloc[i, j]) > 0.6 else INK)
    plt.colorbar(im, ax=ax, shrink=0.8, label='correlación de Pearson')
    ax.set_title('Co-ocurrencia de criterios (trabajos que pasan el gate)', fontweight='bold', fontsize=11)
    save(fig, 'figD_coocurrencia')


# ── E · Integración ──
def figE(df):
    gate = df[df['gate_pass'] == True]
    vals, lbls = [0.0, 0.5, 1.0], ['Yuxtapuestos (0)', 'Integración parcial (0.5)', 'Articulados (1)']
    cnt = [int((gate['integracion'] == v).sum()) for v in vals]
    pct = [100 * c / len(gate) for c in cnt]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(lbls, pct, color=[NEUTRAL, RAMP[0], RAMP[2]], edgecolor='white', linewidth=2, width=0.6)
    for b, c, p in zip(bars, cnt, pct):
        ax.text(b.get_x() + b.get_width() / 2, p + 1, f'{c:,} ({p:.0f}%)', ha='center', fontsize=10)
    ax.set_ylabel('% de los que pasan el gate'); ax.set_ylim(0, max(pct) * 1.2); hgrid(ax)
    ax.set_title('¿Los criterios se articulan o se yuxtaponen? (factor de integración)', fontweight='bold', fontsize=11)
    save(fig, 'figE_integracion')


# ── F · RSI por idioma (puntos, porque el grupo en español es pequeño) ──
def figF(df):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    rng = np.random.default_rng(42)
    for i, (code, lbl) in enumerate([('en', 'Inglés'), ('es', 'Español')]):
        v = df.loc[df['idioma'] == code, 'bowleg_total'].dropna()
        if v.empty: continue
        ax.scatter(i + rng.uniform(-0.18, 0.18, len(v)), v + rng.uniform(-0.12, 0.12, len(v)),
                   s=9, color=SERIES[i], alpha=0.35, edgecolors='none')
        ax.plot([i - 0.28, i + 0.28], [v.mean()] * 2, color=INK, lw=2)
        ax.text(i + 0.3, v.mean(), f'media {v.mean():.2f}\n(n={len(v)})', va='center', fontsize=8.5)
    ax.set_xticks([0, 1]); ax.set_xticklabels(['Inglés', 'Español']); ax.set_xlim(-0.6, 1.9)
    ax.set_ylabel('Puntaje RSI (0–4)'); ax.axhline(2.5, color=INK2, ls='--', lw=0.9)
    ax.text(1.85, 2.55, 'umbral sustantivo', ha='right', fontsize=8, color=INK2)
    ax.set_title('Distribución de la RSI por idioma', fontweight='bold'); hgrid(ax)
    save(fig, 'figF_idioma_puntos')


# ── G · Criterio IV por tipo de estudio ──
def figG(tipo):
    t = tipo[tipo['n_gate'] > 0].sort_values('pct_IV_cumple_gate')
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.barh(range(len(t)), t['pct_IV_cumple_gate'], color=SERIES[0], edgecolor='white', linewidth=1.5, height=0.65)
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels([f"{TIPO_LABEL.get(k, k)} (n={int(r.n_gate)})" for k, r in t.iterrows()], fontsize=9)
    for i, v in enumerate(t['pct_IV_cumple_gate']):
        ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=8.5)
    ax.set_xlim(0, 100); ax.set_xlabel('% que cumple el criterio IV (método no aditivo) entre los que pasan el gate')
    ax.set_title('El método, según el tipo de estudio', fontweight='bold'); hgrid(ax, 'x')
    save(fig, 'figG_metodo_por_tipo')


# ── H · Ranking de tópicos por RSI media ──
def figH(stats):
    ds = stats[::-1]
    fig, ax = plt.subplots(figsize=(11, max(6, 0.36 * len(ds) + 1.5)))
    yy = np.arange(len(ds))
    ax.barh(yy, [r['rsi_mean'] for r in ds], color=[CAT_COLOR[rsi_cat(r['rsi_mean'])] for r in ds],
            edgecolor='white', linewidth=1.5, height=0.72)
    ax.set_yticks(yy)
    ax.set_yticklabels([f"T{r['topic_id']} · {r['label'][:46]}" for r in ds], fontsize=8)
    for i, r in enumerate(ds):
        ax.text(r['rsi_mean'] + 0.04, i, f"{r['rsi_mean']:.2f}  (n={r['n']})", va='center', fontsize=7.5)
    ax.set_xlim(0, 4.3); ax.axvline(2.5, color=INK2, ls='--', lw=0.9)
    ax.set_xlabel('RSI media del tópico (0 = solo mención · 4 = sustantiva fuerte)')
    handles = [mpatches.Patch(color=CAT_COLOR[k], label=CAT_LABEL[k]) for k in CAT_ORDER]
    ax.legend(handles=handles, loc='lower right', fontsize=8, frameon=True)
    ax.set_title('Ranking de tópicos por RSI media · v2', fontweight='bold'); hgrid(ax, 'x')
    save(fig, 'figH_ranking_topicos')


# ── I · Amenaza × % sustantivo ──
def figI(am):
    a = am[am['n'] >= 10].sort_values('pct_substantive')
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.barh(range(len(a)), a['pct_substantive'], color=SERIES[0], edgecolor='white', linewidth=1.5, height=0.65)
    ax.set_yticks(range(len(a)))
    ax.set_yticklabels([f"{AMENAZA_LABEL.get(k, k)} (n={int(r.n)})" for k, r in a.iterrows()], fontsize=9)
    for i, v in enumerate(a['pct_substantive']):
        ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=8.5)
    ax.set_xlim(0, 100); ax.set_xlabel('% sustantivo (RSI ≥ 2.5)')
    ax.set_title('Sustantividad por tipo de amenaza (≥ 10 trabajos)', fontweight='bold'); hgrid(ax, 'x')
    save(fig, 'figI_amenazas')


def topic_stats(f, sub_ids):
    f = f[f['topic_id'] >= 0]
    rows = []
    for tid, g in f.groupby('topic_id'):
        rows.append({'topic_id': int(tid), 'label': g['topic_label'].iloc[0], 'n': int(len(g)),
                     'rsi_mean': round(float(g['bowleg_total'].mean()), 2),
                     'gate_pct': round(float((g['gate_pass'] == True).mean()) * 100, 0),
                     'sust_pct': round(float((g['bowleg_total'] >= 2.5).mean()) * 100, 0),
                     'es_pct': round(float((g['idioma'] == 'es').mean()) * 100, 0),
                     'en_pct': round(float((g['idioma'] == 'en').mean()) * 100, 0), 'pt_pct': 0.0,
                     'n_tesis': int(g['paper_id'].isin(sub_ids).sum())})
    stats = sorted(rows, key=lambda r: -r['rsi_mean'])
    out = {'topics': stats, 'meta': {
        'n_topics': len(stats), 'n_papers': int(len(f)),
        'rsi_min': min(r['rsi_mean'] for r in stats), 'rsi_max': max(r['rsi_mean'] for r in stats),
        'n_tesis_total': int(f['paper_id'].isin(sub_ids).sum()),
        'n_topics_con_tesis': int(sum(1 for r in stats if r['n_tesis'] > 0))}}
    (DATA / 'v2_topic_stats.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return stats


def casos(df):
    def ev(r, c):
        v = r.get(c)
        return '' if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)[:200]

    def caso(r, cat):
        return {'titulo': str(r['Title'])[:160], 'year': str(int(r['Year'])) if pd.notna(r['Year']) else '',
                'categoria': cat, 'rsi_total': float(r['bowleg_total']), 'gate': bool(r['gate_pass']),
                'scores': {k: (None if pd.isna(r[c]) else float(r[c])) for k, c in
                           zip(['I', 'II', 'III', 'IV', 'V', 'VI'], [c for c, _ in CRITS])},
                'evidencias': {k: ev(r, c) for k, c in
                               zip(['I', 'II', 'III', 'IV', 'V', 'VI'],
                                   ['bowleg_I_evidence', 'bowleg_II_evidence', 'bowleg_III_evidence',
                                    'bowleg_IV_evidence', 'rsi_V_evidence', 'rsi_VI_evidence'])},
                'gate_evidence': ev(r, 'gate_evidence')}
    hi = df[df['confidence'] == 'high']
    out = [caso(r, 'Sustantiva fuerte') for _, r in hi[hi['bowleg_total'] == 4].sample(2, random_state=42).iterrows()]
    out += [caso(r, 'Parcial') for _, r in hi[hi['bowleg_total'].between(1.5, 2.0)].sample(1, random_state=42).iterrows()]
    out += [caso(r, 'Mención sin aplicación') for _, r in hi[hi['bowleg_total'] == 0].sample(2, random_state=42).iterrows()]
    (DATA / 'v2_casos_ejemplares.json').write_text(json.dumps(out, indent=2, ensure_ascii=False))


def main():
    meta = json.loads((DATA / 'v2_prisma_meta.json').read_text())
    f = pd.read_csv(DATA / 'v2_corpus_final.csv')
    tb = pd.read_csv(DATA / 'v2_topics_x_bowleg.csv')
    lb = pd.read_csv(DATA / 'v2_lang_x_bowleg.csv', index_col=0)
    yb = pd.read_csv(DATA / 'v2_year_x_bowleg.csv', index_col=0)
    cb = pd.read_csv(DATA / 'v2_country_x_bowleg.csv', index_col=0)
    tipo = pd.read_csv(DATA / 'v2_tipo_x_bowleg.csv', index_col=0)
    am = pd.read_csv(DATA / 'v2_amenaza_x_bowleg.csv', index_col=0)
    sub_ids = set(pd.read_csv(DATA / 'v2_daniel_subcorpus.csv')['paper_id'])
    print("[figuras v2]")
    fig01_prisma(meta); fig02_dist(f); fig03_years(f); fig04_topics(tb); fig05_lang(lb)
    fig06_lugares(cb); fig07_trend(yb); figA(f); figB(f); figD(f); figE(f); figF(f); figG(tipo)
    figH(topic_stats(f, sub_ids)); figI(am); casos(f)
    print("[OK] figuras + data/v2_topic_stats.json + data/v2_casos_ejemplares.json")


if __name__ == '__main__':
    main()
