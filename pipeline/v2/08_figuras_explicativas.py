#!/usr/bin/env python3
"""
08_figuras_explicativas.py — v2: réplica de pipeline/08_figuras_explicativas.py con la búsqueda ampliada.

Genera:
  A  assets/v2_figA_criterios.png       perfil por criterio I-VI (barras apiladas)
  B  assets/v2_figB_embudo.png          embudo del gate (invocan→articulan→sustantivo→fuerte)
  D  assets/v2_figD_cooc.png            matriz de correlación entre criterios
  E  assets/v2_figE_integracion.png     distribución del factor de integración
  F  assets/v2_figF_violin.png          distribución RSI por idioma (violín)
  + data/v2_casos_ejemplares.json       casos para la tabla C (anchoring cualitativo)
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path("data"); ASSETS = Path("assets")
plt.rcParams.update({'figure.dpi': 100, 'savefig.dpi': 200, 'font.size': 10,
                     'font.family': 'sans-serif'})
NOTE = "RSI v3 (Claude · claude-opus-5-5) · provisional hasta validación humana"

CRITS = [('bowleg_I', 'I · Identidades\nentrelazadas'),
         ('bowleg_II', 'II · Poder\nestructural'),
         ('bowleg_III', 'III · Contexto\nsituado'),
         ('bowleg_IV', 'IV · Método\nno aditivo'),
         ('rsi_V', 'V · Praxis\ny justicia'),
         ('rsi_VI', 'VI · Agencia\ny resistencia')]


def load():
    df = pd.read_csv(DATA / 'v2_corpus_scored.csv')
    res = pd.read_csv(DATA / 'v2_bowleg_results.csv')
    # asegurar columnas v3 en df (merge si faltan)
    for c in ['rsi_V','rsi_VI','gate_pass','integracion']:
        if c not in df.columns and c in res.columns:
            df = df.merge(res[['paper_id', c]], on='paper_id', how='left')
    return df, res


# ── A · Perfil por criterio ──
def figA(df):
    gate = df[df['gate_pass'] == True]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True)
    for ax, subset, title in [
        (axes[0], df, f'Corpus completo (n={len(df)})'),
        (axes[1], gate, f'Solo papers que pasan el gate (n={len(gate)})')]:
        labels = [l for _, l in CRITS]
        p0 = [100*(subset[c] == 0).sum()/len(subset) for c, _ in CRITS]
        p5 = [100*(subset[c] == 0.5).sum()/len(subset) for c, _ in CRITS]
        p1 = [100*(subset[c] == 1).sum()/len(subset) for c, _ in CRITS]
        y = np.arange(len(labels))
        ax.barh(y, p0, color='#e57373', label='No (0)')
        ax.barh(y, p5, left=p0, color='#ffb74d', label='Parcial (0.5)')
        ax.barh(y, p1, left=[a+b for a,b in zip(p0,p5)], color='#66bb6a', label='Cumple (1)')
        ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, 100); ax.set_xlabel('% de papers')
        ax.set_title(title, fontsize=11)
        ax.invert_yaxis()
        # anotar % cumple
        for i, v in enumerate(p1):
            ax.text(99, i, f'{v:.0f}% cumple', va='center', ha='right', fontsize=8, color='#1b5e20')
    handles, labels_ = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels_, loc='lower center', ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle('Perfil de cumplimiento por criterio de la RSI', fontsize=13, fontweight='bold')
    fig.text(0.5, 0.005, NOTE, ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.savefig(ASSETS / 'v2_figA_criterios.png', bbox_inches='tight'); plt.close()
    print("[A] perfil por criterio")


# ── B · Embudo del gate ──
def figB(df):
    n = len(df)
    gate = (df['gate_pass'] == True).sum()
    sust = (df['bowleg_total'] >= 2.5).sum()
    fuerte = (df['bowleg_total'] >= 3.5).sum()
    stages = [('Invocan interseccionalidad\n(corpus)', n),
              ('Articulan ≥2 ejes\n(pasan el gate)', gate),
              ('Aplicación sustantiva\n(RSI ≥ 2.5)', sust),
              ('Sustantiva fuerte\n(RSI ≥ 3.5)', fuerte)]
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#90caf9', '#64b5f6', '#66bb6a', '#1b5e20']
    maxw = n
    for i, (lbl, val) in enumerate(stages):
        w = val / maxw
        ax.barh(i, w, height=0.62, color=colors[i], edgecolor='white')
        ax.text(w/2, i, f'{val}  ({100*val/n:.0f}%)', va='center', ha='center',
                fontsize=11, fontweight='bold', color='white' if i==3 else '#1a1a1a')
        ax.text(-0.02, i, lbl, va='center', ha='right', fontsize=9.5)
    ax.set_xlim(0, 1); ax.set_ylim(-0.5, 3.5); ax.invert_yaxis()
    ax.axis('off')
    ax.set_title('Embudo de sustantividad interseccional', fontsize=13, fontweight='bold', pad=15)
    fig.text(0.5, 0.01, NOTE, ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout()
    plt.savefig(ASSETS / 'v2_figB_embudo.png', bbox_inches='tight'); plt.close()
    print("[B] embudo del gate")


# ── D · Matriz de correlación entre criterios ──
def figD(df):
    gate = df[df['gate_pass'] == True]
    cols = [c for c, _ in CRITS]
    short = ['I', 'II', 'III', 'IV', 'V', 'VI']
    corr = gate[cols].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(6)); ax.set_yticks(range(6))
    ax.set_xticklabels(short); ax.set_yticklabels(short)
    for i in range(6):
        for j in range(6):
            ax.text(j, i, f'{corr.iloc[i,j]:.2f}', ha='center', va='center',
                    fontsize=9, color='white' if abs(corr.iloc[i,j])>0.5 else '#333')
    plt.colorbar(im, ax=ax, shrink=0.8, label='correlación de Pearson')
    ax.set_title('Co-ocurrencia de criterios (papers que pasan el gate)',
                 fontsize=12, fontweight='bold')
    fig.text(0.5, 0.01, NOTE, ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(ASSETS / 'v2_figD_cooc.png', bbox_inches='tight'); plt.close()
    print("[D] co-ocurrencia")


# ── E · Distribución del factor de integración ──
def figE(df):
    gate = df[df['gate_pass'] == True]
    vals = [0.0, 0.5, 1.0]
    labels = ['Yuxtapuestos\n(0)', 'Integración\nparcial (0.5)', 'Articulados\n(1)']
    counts = [(gate['integracion'] == v).sum() for v in vals]
    pct = [100*c/len(gate) for c in counts]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars = ax.bar(labels, pct, color=['#e57373', '#ffb74d', '#66bb6a'], edgecolor='white')
    for b, c, p in zip(bars, counts, pct):
        ax.text(b.get_x()+b.get_width()/2, p+1, f'{c}\n({p:.0f}%)', ha='center', fontsize=10)
    ax.set_ylabel('% de papers que pasan el gate')
    ax.set_title('¿Los criterios se articulan o se yuxtaponen?\nFactor de integración (n papers con gate)',
                 fontsize=12, fontweight='bold')
    ax.set_ylim(0, max(pct)*1.2)
    fig.text(0.5, 0.01, NOTE, ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(ASSETS / 'v2_figE_integracion.png', bbox_inches='tight'); plt.close()
    print("[E] integración")


# ── F · Violín de RSI por idioma ──
def figF(df):
    lang_col = 'Language of Original Document'
    groups, labels = [], []
    for lang in ['English', 'Spanish']:
        sub = df[df[lang_col] == lang]['bowleg_total'].dropna()
        if len(sub) >= 10:
            groups.append(sub.values); labels.append(f'{lang}\n(n={len(sub)})')
    fig, ax = plt.subplots(figsize=(8, 5.5))
    parts = ax.violinplot(groups, showmeans=True, showextrema=True)
    for pc in parts['bodies']:
        pc.set_facecolor('#64b5f6'); pc.set_alpha(0.6)
    ax.set_xticks(range(1, len(labels)+1)); ax.set_xticklabels(labels)
    ax.set_ylabel('Puntaje RSI (0–4)')
    ax.axhline(2.5, color='red', ls='--', alpha=0.5, label='umbral sustantivo (2.5)')
    ax.set_title('Distribución del puntaje RSI por idioma', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8)
    fig.text(0.5, 0.01, NOTE, ha='center', fontsize=8, style='italic', color='gray')
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(ASSETS / 'v2_figF_violin.png', bbox_inches='tight'); plt.close()
    print("[F] violín por idioma")


# ── C · Casos ejemplares (datos para tabla HTML) ──
def casos(df, res):
    m = df.merge(res[['paper_id','bowleg_I_evidence','bowleg_II_evidence','bowleg_III_evidence',
                       'bowleg_IV_evidence','rsi_V_evidence','rsi_VI_evidence','gate_evidence']],
                 on='paper_id', how='left')
    def pick(cond, n=1):
        sub = m[cond].sort_values('bowleg_total', ascending=False)
        return sub.head(n)
    casos = []
    # sustantivo fuerte
    for _, r in pick(m['bowleg_total'] >= 3.5, 2).iterrows():
        casos.append(_caso(r, 'Sustantiva fuerte'))
    # parcial
    for _, r in pick((m['bowleg_total'] >= 1.5) & (m['bowleg_total'] < 2.5), 1).iterrows():
        casos.append(_caso(r, 'Parcial'))
    # nominal / gate fail
    for _, r in m[m['bowleg_total'] == 0].head(2).iterrows():
        casos.append(_caso(r, 'Mención sin aplicación'))
    (DATA / 'v2_casos_ejemplares.json').write_text(json.dumps(casos, indent=2, ensure_ascii=False))
    print(f"[C] {len(casos)} casos ejemplares → data/v2_casos_ejemplares.json")


def _caso(r, cat):
    def ev(c):
        v = r.get(c);
        return '' if (v is None or (isinstance(v,float) and pd.isna(v))) else str(v)[:200]
    return {
        'titulo': str(r.get('Title',''))[:160],
        'year': str(r.get('Year','')),
        'categoria': cat,
        'rsi_total': float(r.get('bowleg_total', 0)),
        'gate': bool(r.get('gate_pass', False)),
        'scores': {'I': r.get('bowleg_I'), 'II': r.get('bowleg_II'), 'III': r.get('bowleg_III'),
                   'IV': r.get('bowleg_IV'), 'V': r.get('rsi_V'), 'VI': r.get('rsi_VI')},
        'evidencias': {'I': ev('bowleg_I_evidence'), 'II': ev('bowleg_II_evidence'),
                       'III': ev('bowleg_III_evidence'), 'IV': ev('bowleg_IV_evidence'),
                       'V': ev('rsi_V_evidence'), 'VI': ev('rsi_VI_evidence')},
        'gate_evidence': ev('gate_evidence'),
    }


if __name__ == '__main__':
    df, res = load()
    figA(df); figB(df); figD(df); figE(df); figF(df); casos(df, res)
    print("\n[OK] Figuras A,B,D,E,F + casos C generados")
