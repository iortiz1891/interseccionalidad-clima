#!/usr/bin/env python3
"""
18_v1_descriptive_stats.py — Fase 2: estadísticos descriptivos del corpus v1.

Output:
  - data/v1_corpus_stats.json — métricas resumidas
  - data/v1_corpus_stats_report.md — reporte humano-leíble
  - data/v1_daniel_subcorpus.csv — subconjunto temático para tesis de Daniel
"""
from __future__ import annotations
import pandas as pd
import json
import re
from pathlib import Path
from collections import Counter

DATA = Path("data")


def safe_dict_top(s: pd.Series, n: int = 20) -> dict:
    return {str(k): int(v) for k, v in s.head(n).items()}


def main():
    df = pd.read_csv(DATA / 'v1_corpus_scored.csv')
    n = len(df)
    print(f"=== Corpus v1: {n} papers ===\n")

    stats = {'n_total': n}

    # ─────────────────────────────────
    # Por año
    # ─────────────────────────────────
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    year_dist = df['Year'].dropna().astype(int).value_counts().sort_index()
    print("=== Por año (últimos 12) ===")
    print(year_dist.tail(12))
    stats['year_distribution'] = {int(k): int(v) for k, v in year_dist.items()}

    # ─────────────────────────────────
    # Por idioma
    # ─────────────────────────────────
    lang_dist = df['Language of Original Document'].fillna('Unknown').value_counts()
    print("\n=== Por idioma (top 8) ===")
    print(lang_dist.head(8))
    stats['language_distribution'] = safe_dict_top(lang_dist, 15)

    # ─────────────────────────────────
    # Por fuente
    # ─────────────────────────────────
    src_dist = df['_tag'].value_counts()
    base_dist = df['_source'].value_counts()
    print("\n=== Por tag de fuente ===")
    print(src_dist)
    print("\n=== Por base ===")
    print(base_dist)
    stats['source_distribution'] = safe_dict_top(src_dist)
    stats['base_distribution'] = safe_dict_top(base_dist)

    # ─────────────────────────────────
    # Por país (parseado de Affiliations)
    # ─────────────────────────────────
    affs = df['Affiliations'].fillna('').astype(str)
    # Extraer último elemento separado por coma (país suele venir al final)
    countries = []
    for aff_str in affs:
        for aff in aff_str.split(';'):
            parts = [p.strip() for p in aff.split(',') if p.strip()]
            if parts:
                countries.append(parts[-1])
    country_counter = Counter(countries)
    # Filtrar entradas vacías / cortas
    country_counter = {k: v for k, v in country_counter.items() if len(k) >= 3}
    country_top = dict(sorted(country_counter.items(), key=lambda x: -x[1])[:25])
    print("\n=== Top 15 países ===")
    for k, v in list(country_top.items())[:15]:
        print(f"  {k:35s} {v}")
    stats['top_countries'] = country_top

    # ─────────────────────────────────
    # Bowleg distribution
    # ─────────────────────────────────
    bw_dist = df['bowleg_total'].value_counts().sort_index()
    print("\n=== Distribución bowleg_total ===")
    print(bw_dist)
    stats['bowleg_distribution'] = {float(k): int(v) for k, v in bw_dist.items()}

    cat_dist = df['categoria_bowleg'].value_counts()
    print("\n=== Categorías Bowleg ===")
    for c, n_c in cat_dist.items():
        print(f"  {c:25s} {n_c:>5} ({100*n_c/n:>5.1f}%)")
    stats['category_distribution'] = {k: int(v) for k, v in cat_dist.items()}
    stats['category_percentages'] = {k: round(100*v/n, 2) for k, v in cat_dist.items()}

    # ─────────────────────────────────
    # Confidence
    # ─────────────────────────────────
    conf_dist = df['confidence'].value_counts()
    print("\n=== Confidence ===")
    print(conf_dist)
    stats['confidence_distribution'] = safe_dict_top(conf_dist)

    # ─────────────────────────────────
    # Sub-corpus tesis de Daniel
    # ─────────────────────────────────
    # Filtros temáticos: México + ciclones tropicales / huracanes
    title_abs = (df['Title'].fillna('').astype(str) + ' ' +
                  df['Abstract'].fillna('').astype(str)).str.lower()
    is_mexico = title_abs.str.contains(r'\bmexic|méxic|veracruz|yucat|quintana roo|oaxaca|chiapas|guerrero|tabasco|sinaloa', regex=True)
    is_cyclonic = title_abs.str.contains(r'\bcyclone|hurricane|hurac[aá]n|cicl[oó]n|tropical storm|tormenta tropical|typhoon|tif[oó]n', regex=True)
    is_coastal = title_abs.str.contains(r'\bcoast|costa|costera|costero|coastal|marin|maritim', regex=True)
    is_indigenous = title_abs.str.contains(r'\bind[íi]gen|nativ|originari', regex=True)
    is_women = title_abs.str.contains(r'\bwomen|mujer|female|gender|g[eé]nero', regex=True)

    print(f"\n=== Sub-corpus para tesis de Daniel (foco temático) ===")
    print(f"  México:           {is_mexico.sum()}")
    print(f"  Ciclones/huracanes: {is_cyclonic.sum()}")
    print(f"  Costero:          {is_coastal.sum()}")
    print(f"  Indígena:         {is_indigenous.sum()}")
    print(f"  Mujeres/género:   {is_women.sum()}")
    print(f"  México + ciclones: {(is_mexico & is_cyclonic).sum()}")
    print(f"  México + ciclones + (indígena|mujeres): {(is_mexico & is_cyclonic & (is_indigenous|is_women)).sum()}")
    print(f"  Latinoamérica costera + ciclones: {(is_coastal & is_cyclonic).sum()}")

    stats['daniel_subcorpus'] = {
        'mexico': int(is_mexico.sum()),
        'cyclonic_events': int(is_cyclonic.sum()),
        'coastal': int(is_coastal.sum()),
        'indigenous': int(is_indigenous.sum()),
        'gender_women': int(is_women.sum()),
        'mexico_AND_cyclonic': int((is_mexico & is_cyclonic).sum()),
        'mexico_cyclonic_gender_or_indigenous': int((is_mexico & is_cyclonic & (is_indigenous|is_women)).sum()),
        'coastal_AND_cyclonic': int((is_coastal & is_cyclonic).sum()),
    }

    # Guardar sub-corpus Daniel: papers con al menos 2 de los 4 ejes
    daniel_score = (is_mexico.astype(int) + is_cyclonic.astype(int)
                     + is_coastal.astype(int) + is_indigenous.astype(int)
                     + is_women.astype(int))
    df['_daniel_score'] = daniel_score
    daniel_relevant = df[df['_daniel_score'] >= 2].copy()
    print(f"\n  Papers con ≥2 ejes Daniel: {len(daniel_relevant)}")
    print(f"     Bowleg medio: {daniel_relevant['bowleg_total'].mean():.2f}")
    print(f"     Bowleg ≥2.5: {(daniel_relevant['bowleg_total'] >= 2.5).sum()}")
    daniel_relevant.to_csv(DATA / 'v1_daniel_subcorpus.csv', index=False)
    stats['daniel_subcorpus']['relevant_ge2_axes'] = int(len(daniel_relevant))
    stats['daniel_subcorpus']['relevant_bowleg_mean'] = float(daniel_relevant['bowleg_total'].mean())
    stats['daniel_subcorpus']['relevant_substantive'] = int((daniel_relevant['bowleg_total'] >= 2.5).sum())

    # (La comparación con el corpus original se eliminó: esta rama usa
    #  únicamente las 2 bases de Daniel y es autocontenida.)

    # Save
    (DATA / 'v1_corpus_stats.json').write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"\n[OK] stats → data/v1_corpus_stats.json")

    # ─────────────────────────────────
    # Reporte md
    # ─────────────────────────────────
    report = [
        f"# Corpus v1 — Estadísticos descriptivos",
        f"",
        f"**Fecha:** 2026-05-15 | **N:** {n} papers | **Scoring:** GPT-4o-mini (provisional)",
        f"",
        f"## Distribución por categoría Bowleg",
        f"",
        "| Categoría | n | % |",
        "|---|---|---|",
    ]
    for cat, n_c in cat_dist.items():
        report.append(f"| {cat} | {n_c:,} | {100*n_c/n:.1f}% |")
    report.append("")
    report.append(f"**Nota:** los puntajes RSI son provisionales hasta completar la validación humana sobre una submuestra (κ de Cohen humano–modelo).")
    report.append("")
    report.append("## Idiomas")
    report.append("")
    for lang, n_l in lang_dist.head(8).items():
        report.append(f"- **{lang}:** {n_l}")
    report.append("")
    report.append("## Top 10 países (afiliaciones)")
    report.append("")
    for k, v in list(country_top.items())[:10]:
        report.append(f"- {k}: {v}")
    report.append("")
    report.append("## Sub-corpus tesis Daniel")
    report.append("")
    report.append(f"- México: {is_mexico.sum()}")
    report.append(f"- Ciclones/huracanes: {is_cyclonic.sum()}")
    report.append(f"- México + ciclones: {(is_mexico & is_cyclonic).sum()}")
    report.append(f"- Papers con ≥2 ejes (mexico/ciclones/costero/indígena/género): {len(daniel_relevant)}")
    report.append(f"- De esos, bowleg ≥ 2.5: {(daniel_relevant['bowleg_total'] >= 2.5).sum()}")
    (DATA / 'v1_corpus_stats_report.md').write_text('\n'.join(report))
    print(f"[OK] reporte → data/v1_corpus_stats_report.md")


if __name__ == '__main__':
    main()
