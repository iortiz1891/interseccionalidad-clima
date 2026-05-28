#!/usr/bin/env python3
"""
30_daniel_ingest.py — Ingesta de las 2 bases de Daniel (EN + ES).

Lee daniel_en.xlsx (765) + daniel_es.xlsx (222), consolida, filtra abstract,
dedup interno, y produce data/v1_corpus_consolidated.csv con el MISMO schema
que el pipeline principal (para reusar scripts 16-29 sin cambios).

La rama Daniel reutiliza el nombre 'v1_corpus_consolidated.csv' pero vive en
su propia carpeta (Daniel_databases_project/), aislada del corpus multi-base.
"""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path
import pandas as pd

DATA = Path("data")

# Columnas que el pipeline downstream espera
PIPELINE_COLS = ['Title', 'Year', 'DOI', 'Abstract', 'Authors', 'Source title',
                 'Affiliations', 'Language of Original Document', 'Document Type',
                 'Author Keywords', 'Cited by']


def norm_doi(s):
    return (s.fillna('').astype(str).str.lower()
              .str.replace('https://doi.org/', '', regex=False).str.strip())


def norm_title(s):
    if pd.isna(s): return ''
    s = unicodedata.normalize('NFD', str(s).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', s)).strip()


def first_author(s):
    if pd.isna(s): return ''
    return str(s).split(';')[0].strip().lower()[:30]


def main():
    print("[1] Cargando xlsx de Daniel")
    en = pd.read_excel(DATA / 'daniel_en.xlsx')
    es = pd.read_excel(DATA / 'daniel_es.xlsx')
    en['_tag'] = 'daniel_en'; en['_source'] = 'scopus_daniel'
    es['_tag'] = 'daniel_es'; es['_source'] = 'scopus_daniel'
    print(f"    EN: {len(en)} | ES: {len(es)}")

    # Unir
    keep = PIPELINE_COLS + ['_tag', '_source']
    for df in (en, es):
        for c in PIPELINE_COLS:
            if c not in df.columns:
                df[c] = ''
    big = pd.concat([en[keep], es[keep]], ignore_index=True)
    print(f"[union bruto] {len(big)}")

    # Filtro abstract ≥100 chars
    big['_abs_len'] = big['Abstract'].fillna('').astype(str).str.strip().str.len()
    has_abs = big[big['_abs_len'] >= 100].copy()
    print(f"[filtro abstract ≥100] {len(has_abs)} OK | {len(big)-len(has_abs)} descartados")

    # Dedup por DOI
    has_abs['_doi'] = norm_doi(has_abs['DOI'])
    with_doi = has_abs[has_abs['_doi'].str.startswith('10.')].copy()
    without_doi = has_abs[~has_abs['_doi'].str.startswith('10.')].copy()
    n0 = len(with_doi)
    with_doi = with_doi.drop_duplicates(subset=['_doi'], keep='first')
    print(f"[dedup DOI] {len(with_doi)} únicos | {n0-len(with_doi)} dups")

    # Dedup sin DOI por título+año+autor
    without_doi['_key'] = (without_doi['Title'].apply(norm_title) + '|'
                            + without_doi['Year'].astype(str) + '|'
                            + without_doi['Authors'].apply(first_author))
    n1 = len(without_doi)
    without_doi = without_doi.drop_duplicates(subset=['_key'], keep='first')
    print(f"[dedup sin-DOI] {len(without_doi)} únicos | {n1-len(without_doi)} dups")

    # Cross-dedup
    with_doi['_key'] = (with_doi['Title'].apply(norm_title) + '|'
                         + with_doi['Year'].astype(str) + '|'
                         + with_doi['Authors'].apply(first_author))
    doi_keys = set(with_doi['_key'])
    without_doi = without_doi[~without_doi['_key'].isin(doi_keys)]

    final = pd.concat([with_doi, without_doi], ignore_index=True)
    final = final.drop(columns=['_abs_len', '_key'], errors='ignore')
    # paper_id estable
    final = final.reset_index(drop=True)

    print(f"\n=== CORPUS DANIEL CONSOLIDADO: {len(final)} papers ===")
    print(f"Por fuente:\n{final['_tag'].value_counts()}")
    print(f"\nPor idioma:\n{final['Language of Original Document'].value_counts().head(6)}")
    print(f"\nAños recientes:\n{pd.to_numeric(final['Year'],errors='coerce').dropna().astype(int).value_counts().sort_index().tail(8)}")

    out = DATA / 'v1_corpus_consolidated.csv'
    final.to_csv(out, index=False)
    print(f"\n[OK] {out} ({len(final)} papers)")


if __name__ == '__main__':
    main()
