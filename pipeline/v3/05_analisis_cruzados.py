#!/usr/bin/env python3
"""
05_analisis_cruzados.py — v3: réplica de pipeline/v2/05_analisis_cruzados.py con el corpus v3 (Scopus + SciELO + OpenAlex ES/PT).

Única diferencia de código: une los tópicos por paper_id (la v1 unía por título normalizado).

Outputs:
  - data/v3_topics_x_bowleg.csv      Topics × Bowleg
  - data/v3_lang_x_bowleg.csv         Idioma × Bowleg
  - data/v3_year_x_bowleg.csv         Año × Bowleg
  - data/v3_country_x_bowleg.csv      País × Bowleg
  - data/v3_corpus_final.csv          Master: corpus + scores + topics
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import re
from pathlib import Path
from collections import Counter

DATA = Path("data")


# Nombres en español para tablas y figuras (los que no estén aquí se muestran en inglés)
PAISES_ES = {
    'United States': 'Estados Unidos', 'United Kingdom': 'Reino Unido', 'Australia': 'Australia',
    'Canada': 'Canadá', 'India': 'India', 'Germany': 'Alemania', 'South Africa': 'Sudáfrica',
    'Sweden': 'Suecia', 'Spain': 'España', 'Netherlands': 'Países Bajos', 'Italy': 'Italia',
    'Kenya': 'Kenia', 'Norway': 'Noruega', 'Austria': 'Austria', 'Bangladesh': 'Bangladés',
    'Brazil': 'Brasil', 'Switzerland': 'Suiza', 'Indonesia': 'Indonesia', 'Ghana': 'Ghana',
    'New Zealand': 'Nueva Zelanda', 'Portugal': 'Portugal', 'Nigeria': 'Nigeria', 'Denmark': 'Dinamarca',
    'Finland': 'Finlandia', 'Ireland': 'Irlanda', 'Nepal': 'Nepal', 'Japan': 'Japón',
    'Zimbabwe': 'Zimbabue', 'Belgium': 'Bélgica', 'Mexico': 'México', 'Chile': 'Chile',
    'Turkey': 'Turquía', 'France': 'Francia', 'Thailand': 'Tailandia', 'Viet Nam': 'Vietnam',
    'China': 'China', 'Colombia': 'Colombia', 'Ethiopia': 'Etiopía', 'Uganda': 'Uganda',
    'Malaysia': 'Malasia', 'Pakistan': 'Pakistán', 'Philippines': 'Filipinas', 'Tanzania': 'Tanzania',
    'Czech Republic': 'Chequia', 'Peru': 'Perú', 'Singapore': 'Singapur', 'Senegal': 'Senegal',
    'Puerto Rico': 'Puerto Rico', 'South Korea': 'Corea del Sur', 'Argentina': 'Argentina',
    'Ecuador': 'Ecuador', 'Costa Rica': 'Costa Rica', 'Cuba': 'Cuba', 'Uruguay': 'Uruguay',
    'Jamaica': 'Jamaica', 'Bahamas': 'Bahamas', 'Trinidad and Tobago': 'Trinidad y Tobago',
}


def main():
    scored = pd.read_csv(DATA / 'v3_corpus_scored.csv')
    topics = pd.read_csv(DATA / 'v3_bertopic_assignments.csv')
    topic_info = pd.read_csv(DATA / 'v3_bertopic_info.csv')

    print(f"Scored:  {len(scored)} | Topics: {len(topics)} | Topic info: {len(topic_info)} topics únicos")

    # ─────────────────────────────────
    # Merge corpus_scored + topic assignments (por paper_id)
    # ─────────────────────────────────
    merged = scored.merge(topics[['paper_id', 'topic_id', 'umap_x', 'umap_y']], on='paper_id', how='left')
    n_with_topic = merged['topic_id'].notna().sum()
    print(f"Papers con topic asignado: {n_with_topic} / {len(scored)}")

    # Adjuntar nombre del tópico
    topic_names = topic_info.set_index('Topic')['Name'].to_dict()
    merged['topic_name'] = merged['topic_id'].map(topic_names)
    merged['topic_id_clean'] = merged['topic_id'].fillna(-99).astype(int)

    # ─────────────────────────────────
    # Cruce 1: Topics × Bowleg
    # ─────────────────────────────────
    print("\n=== Topics × Bowleg ===")
    cross = merged.groupby('topic_id_clean').agg(
        n_papers=('Title', 'count'),
        bowleg_mean=('bowleg_total', 'mean'),
        bowleg_median=('bowleg_total', 'median'),
        n_substantive=('bowleg_total', lambda s: (s >= 2.5).sum()),
        n_nominal=('bowleg_total', lambda s: (s <= 1.0).sum()),
    ).reset_index()
    cross['pct_substantive'] = (100 * cross['n_substantive'] / cross['n_papers']).round(1)
    cross['pct_nominal'] = (100 * cross['n_nominal'] / cross['n_papers']).round(1)

    # Adjuntar nombre + top words
    cross['topic_name'] = cross['topic_id_clean'].map(topic_names)
    cross = cross.sort_values('n_papers', ascending=False)
    cross.to_csv(DATA / 'v3_topics_x_bowleg.csv', index=False)
    print(cross.head(20).to_string(index=False))

    # ─────────────────────────────────
    # Cruce 2: Idioma × Bowleg
    # ─────────────────────────────────
    print("\n=== Idioma × Bowleg ===")
    # Idioma normalizado de la ingesta (en/es/pt), no el campo crudo de cada base, que mezcla
    # valores como «English; Spanish».
    idioma = merged['idioma'].map({'en': 'Inglés', 'es': 'Español', 'pt': 'Portugués'}).fillna('Otro').rename('idioma')
    by_lang = merged.groupby(idioma).agg(
        n=('Title', 'count'),
        bowleg_mean=('bowleg_total', 'mean'),
        n_substantive=('bowleg_total', lambda s: (s >= 2.5).sum()),
        n_parcial=('bowleg_total', lambda s: ((s >= 1.5) & (s < 2.5)).sum()),
        n_nominal=('bowleg_total', lambda s: (s < 1.5).sum()),
        pct_gate=('bowleg_total', lambda s: round(100 * (s > 0).mean(), 1)),
    ).round(2)
    by_lang['pct_substantive'] = (100 * by_lang['n_substantive'] / by_lang['n']).round(1)
    by_lang = by_lang.sort_values('n', ascending=False)
    by_lang.to_csv(DATA / 'v3_lang_x_bowleg.csv')
    print(by_lang.head(10))

    # ─────────────────────────────────
    # Cruce 3: Año × Bowleg
    # ─────────────────────────────────
    print("\n=== Año × Bowleg ===")
    merged['Year'] = pd.to_numeric(merged['Year'], errors='coerce')
    by_year = merged.dropna(subset=['Year']).groupby(merged['Year'].astype(int)).agg(
        n=('Title', 'count'),
        bowleg_mean=('bowleg_total', 'mean'),
        n_substantive=('bowleg_total', lambda s: (s >= 2.5).sum()),
    ).round(2)
    by_year['pct_substantive'] = (100 * by_year['n_substantive'] / by_year['n']).round(1)
    by_year.to_csv(DATA / 'v3_year_x_bowleg.csv')
    print(by_year.tail(12))

    # ─────────────────────────────────
    # Cruce 4: País × Bowleg (parseando affiliations)
    # ─────────────────────────────────
    print("\n=== País × Bowleg (top 15) ===")
    # OpenAlex escribe el país de la afiliación como código ISO de dos letras («…, BR»);
    # Scopus, con su nombre en inglés. Se unifican al nombre en inglés.
    ISO2 = {'BR': 'Brazil', 'AR': 'Argentina', 'ES': 'Spain', 'MX': 'Mexico', 'CL': 'Chile',
            'EC': 'Ecuador', 'US': 'United States', 'FR': 'France', 'UG': 'Uganda', 'CO': 'Colombia',
            'CU': 'Cuba', 'BS': 'Bahamas', 'JM': 'Jamaica', 'TT': 'Trinidad and Tobago', 'SE': 'Sweden',
            'PT': 'Portugal', 'PE': 'Peru', 'UY': 'Uruguay', 'VE': 'Venezuela', 'BO': 'Bolivia',
            'PY': 'Paraguay', 'CR': 'Costa Rica', 'GT': 'Guatemala', 'GB': 'United Kingdom',
            'DE': 'Germany', 'CA': 'Canada', 'IT': 'Italy', 'NL': 'Netherlands', 'AO': 'Angola',
            'MZ': 'Mozambique'}
    paper_countries = []
    for idx, row in merged.iterrows():
        aff_str = row.get('Affiliations', '') or ''
        if not isinstance(aff_str, str): continue
        countries = set()
        for aff in aff_str.split(';'):
            parts = [p.strip() for p in aff.split(',') if p.strip()]
            if parts:
                last = ISO2.get(parts[-1], parts[-1])
                if 3 <= len(last) <= 50:
                    countries.add(last)
        for c in countries:
            paper_countries.append({
                'country': c,
                'bowleg_total': row.get('bowleg_total'),
                'paper_id': row.get('paper_id', idx),
            })

    pc_df = pd.DataFrame(paper_countries)
    by_country = pc_df.groupby('country').agg(
        n=('paper_id', 'count'),
        bowleg_mean=('bowleg_total', 'mean'),
        n_substantive=('bowleg_total', lambda s: (s >= 2.5).sum()),
    ).round(2)
    by_country['pct_substantive'] = (100 * by_country['n_substantive'] / by_country['n']).round(1)
    by_country = by_country.sort_values('n', ascending=False)
    by_country.insert(0, 'pais', [PAISES_ES.get(c, c) for c in by_country.index])
    by_country.to_csv(DATA / 'v3_country_x_bowleg.csv')
    print(by_country.head(15).to_string())

    # ─────────────────────────────────
    # Master final
    # ─────────────────────────────────
    out_cols = [c for c in merged.columns if not c.startswith('_')]
    merged[out_cols].to_csv(DATA / 'v3_corpus_final.csv', index=False)
    print(f"\n[OK] master final → data/v3_corpus_final.csv ({len(merged)} papers, {len(out_cols)} cols)")


if __name__ == '__main__':
    main()
