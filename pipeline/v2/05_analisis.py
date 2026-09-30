#!/usr/bin/env python3
"""
05_analisis.py — v2: cruces y estadística descriptiva del corpus elegible.

Equivale a pipeline/05_analisis_cruzados.py + 06_estadisticas.py de la v1, con
dos cambios: une tópicos por paper_id (no por título) y usa el lugar del estudio
codificado en el cribado además de las afiliaciones.

Salidas (data/):
  v2_corpus_final.csv        corpus elegible + puntajes + tópico
  v2_topics_x_bowleg.csv     tópico × RSI
  v2_lang_x_bowleg.csv       idioma × RSI
  v2_year_x_bowleg.csv       año × RSI
  v2_country_x_bowleg.csv    país (lugar del estudio) × RSI
  v2_affil_x_bowleg.csv      país (afiliación, una vez por paper) × RSI
  v2_tipo_x_bowleg.csv       tipo de estudio × RSI y criterio IV
  v2_amenaza_x_bowleg.csv    amenaza × RSI
  v2_ancla_x_bowleg.csv      nivel del ancla × RSI
  v2_daniel_subcorpus.csv    sub-corpus temático de la tesis
  v2_corpus_stats.json       métricas resumidas
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

DATA = Path("data")
CRITS = ['bowleg_I', 'bowleg_II', 'bowleg_III', 'bowleg_IV', 'rsi_V', 'rsi_VI']


def agg(g: pd.DataFrame) -> pd.Series:
    t = g['bowleg_total']
    return pd.Series({
        'n': len(g),
        'bowleg_mean': round(t.mean(), 2),
        'pct_gate_fail': round(100 * (t == 0).mean(), 1),
        'pct_substantive': round(100 * (t >= 2.5).mean(), 1),
        'pct_strong': round(100 * (t >= 3.5).mean(), 1),
    })


def explode_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    e = df.assign(_v=df[col].fillna('').str.split(r'\s*;\s*')).explode('_v')
    return e[e['_v'].str.len() > 0]


def main():
    scored = pd.read_csv(DATA / 'v2_corpus_scored.csv')
    asg = pd.read_csv(DATA / 'v2_bertopic_assignments.csv')
    info = pd.read_csv(DATA / 'v2_bertopic_info.csv')
    labels = json.loads((DATA / 'v2_topic_ai_labels.json').read_text())

    f = scored.merge(asg, on='paper_id', how='left')
    f['topic_id'] = f['topic_id'].fillna(-1).astype(int)
    f['topic_name'] = f['topic_id'].map(info.set_index('Topic')['Name'])
    f['topic_label'] = f['topic_id'].map(lambda t: labels.get(str(t), {}).get('label', 'Sin tópico (outliers)'))
    f['Year'] = pd.to_numeric(f['Year'], errors='coerce')
    print(f"[1] Corpus elegible: {len(f)} · con tópico: {int((f['topic_id'] >= 0).sum())}")

    # ── Cruces ──
    tb = f.groupby('topic_id').apply(agg).reset_index()
    tb['topic_label'] = tb['topic_id'].map(lambda t: labels.get(str(t), {}).get('label', 'Sin tópico'))
    tb.sort_values('n', ascending=False).to_csv(DATA / 'v2_topics_x_bowleg.csv', index=False)

    f.groupby('idioma').apply(agg).to_csv(DATA / 'v2_lang_x_bowleg.csv')
    f.dropna(subset=['Year']).groupby(f['Year'].dropna().astype(int)).apply(agg).to_csv(
        DATA / 'v2_year_x_bowleg.csv')

    loc = explode_col(f, 'lugar_estudio')
    cb = loc.groupby('_v').apply(agg).sort_values('n', ascending=False)
    cb.index.name = 'country'
    cb.to_csv(DATA / 'v2_country_x_bowleg.csv')

    rows = []
    for _, r in f.iterrows():
        aff = r.get('Affiliations')
        if not isinstance(aff, str): continue
        paises = {a.split(',')[-1].strip() for a in aff.split(';') if a.strip()}
        rows += [{'country': p, 'bowleg_total': r['bowleg_total']} for p in paises if 3 <= len(p) <= 50]
    ab = pd.DataFrame(rows).groupby('country').apply(agg).sort_values('n', ascending=False)
    ab.to_csv(DATA / 'v2_affil_x_bowleg.csv')

    gp = f[f['gate_pass'] == True]
    tipo = f.groupby('tipo_estudio').apply(agg)
    tipo['n_gate'] = gp.groupby('tipo_estudio').size()
    tipo['pct_IV_cumple_gate'] = (100 * gp.groupby('tipo_estudio')['bowleg_IV'].apply(lambda s: (s == 1).mean())).round(1)
    tipo.fillna(0).to_csv(DATA / 'v2_tipo_x_bowleg.csv')

    explode_col(f, 'amenaza').groupby('_v').apply(agg).sort_values('n', ascending=False).rename_axis(
        'amenaza').to_csv(DATA / 'v2_amenaza_x_bowleg.csv')
    f.groupby('nivel_ancla').apply(agg).to_csv(DATA / 'v2_ancla_x_bowleg.csv')

    out_cols = [c for c in f.columns if not c.startswith('_')]
    f[out_cols].to_csv(DATA / 'v2_corpus_final.csv', index=False)

    # ── Sub-corpus de la tesis (México × ciclones × costas × indígenas × género) ──
    ta = (f['Title'].fillna('') + ' ' + f['Abstract'].fillna('')).str.lower()
    ejes = {
        'mexico': r'\b(?:mexic\w*|méxic\w*|veracruz|yucat[aá]n|quintana roo|oaxaca|chiapas|tabasco|sinaloa|acapulco)\b'
                  r'|guerrero state|state of guerrero|estado de guerrero',
        'cyclonic': r'\b(?:cyclon\w*|hurricane\w*|hurac[aá]n\w*|cicl[oó]n\w*|typhoon\w*|tif[oó]n\w*)'
                    r'|\btropical storm|\btormentas? tropical',
        'coastal': r'\b(?:coast\w*|costas?|coster[oa]s?|marine|marin[oa]s?|maritim\w*|littoral|litoral)\b',
        'indigenous': r'\b(?:indigen\w*|ind[ií]gena\w*|aboriginal|first nations?|originari[oa]s?)\b'
                      r'|\bnative (?:american|people|communit|nation)',
        'gender_women': r'\b(?:women|woman|mujer\w*|female|gender\w*|g[eé]nero)\b',
    }
    flags = pd.DataFrame({k: ta.str.contains(v, regex=True) for k, v in ejes.items()})
    f['_daniel_score'] = flags.sum(axis=1)
    sub = f[f['_daniel_score'] >= 2].copy()
    sub.to_csv(DATA / 'v2_daniel_subcorpus.csv', index=False)

    # ── Estadística descriptiva ──
    n = len(f)
    stats = {
        'n_total': n,
        'year_distribution': {int(k): int(v) for k, v in f['Year'].dropna().astype(int).value_counts().sort_index().items()},
        'language_distribution': f['idioma'].value_counts().to_dict(),
        'doctype_distribution': f['Document Type'].value_counts().to_dict(),
        'tipo_estudio_distribution': f['tipo_estudio'].value_counts().to_dict(),
        'ancla_distribution': f['nivel_ancla'].value_counts().to_dict(),
        'bowleg_distribution': {str(k): int(v) for k, v in f['bowleg_total'].value_counts().sort_index().items()},
        'category_distribution': f['categoria_bowleg'].value_counts().to_dict(),
        'category_percentages': (f['categoria_bowleg'].value_counts(normalize=True) * 100).round(2).to_dict(),
        'confidence_distribution': f['confidence'].value_counts().to_dict(),
        'n_gate': len(gp),
        'criterios_cumple_gate_pct': {c: round(100 * (gp[c] == 1).mean(), 1) for c in CRITS},
        'top_lugares': cb['n'].head(25).astype(int).to_dict(),
        'daniel_subcorpus': {
            **{k: int(v.sum()) for k, v in flags.items()},
            'mexico_AND_cyclonic': int((flags['mexico'] & flags['cyclonic']).sum()),
            'mexico_cyclonic_gender_or_indigenous': int(
                (flags['mexico'] & flags['cyclonic'] & (flags['indigenous'] | flags['gender_women'])).sum()),
            'coastal_AND_cyclonic': int((flags['coastal'] & flags['cyclonic']).sum()),
            'relevant_ge2_axes': len(sub),
            'relevant_bowleg_mean': round(float(sub['bowleg_total'].mean()), 2) if len(sub) else 0,
            'relevant_substantive': int((sub['bowleg_total'] >= 2.5).sum()),
        },
    }
    (DATA / 'v2_corpus_stats.json').write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"[OK] cruces + data/v2_corpus_stats.json · sub-corpus tesis: {len(sub)}")


if __name__ == '__main__':
    main()
