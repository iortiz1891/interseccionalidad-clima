#!/usr/bin/env python3
"""
01_ingesta_scopus.py — v2: ingesta del export de Scopus (cadena bilingüe v2).

Lee data/v2_scopus_raw.csv (export CSV de Scopus; no se versiona) y produce:
  data/v2_corpus_consolidated.csv   registros que pasan a cribado, con paper_id
  data/v2_prisma_meta.json          conteos de identificación y exclusión por regla

Pasos:
  1. Normaliza columnas al esquema del pipeline v1 (+ Index Keywords, EID).
  2. Excluye por regla: sin abstract (<100 caracteres), Erratum, Conference review.
  3. Deduplica por DOI y luego por título normalizado + año + primer autor.
  4. Marca el nivel del ancla por el que entró cada registro (A núcleo, A ampliada,
     B afín, solo index keywords).

La v2 se construye solo con el export de la búsqueda ampliada: no usa datos de la v1.
"""
from __future__ import annotations
import json
import re
import unicodedata
from pathlib import Path
import pandas as pd

DATA = Path("data")
RAW = DATA / 'v2_scopus_raw.csv'

PIPELINE_COLS = ['Title', 'Year', 'DOI', 'Abstract', 'Authors', 'Source title',
                 'Affiliations', 'Language of Original Document', 'Document Type',
                 'Author Keywords', 'Cited by']
EXTRA_COLS = ['Index Keywords', 'EID', 'Publication Stage', 'Open Access']
EXCLUDED_TYPES = {'Erratum', 'Conference review'}

# Ancla (aproximación por regex de la cadena Scopus v2)
AX_EN = r'(?:gender|race|racial|racism|sex|sexism|sexuality|class|classes|ethnic\w*|identit\w*|oppression\w*|disabilit\w*|indigen\w*|caste)'
AX_ES = r'(?:g[eé]nero|raza|racismo|sexo|sexualidad\w*|clase|[eé]tnic\w*|identidad\w*|opresi\w*|discapacidad\w*|ind[ií]gena\w*)'
RE_NUCLEO = re.compile(r'intersectional|interseccional')
RE_AMPLIADA = re.compile(
    r'intersecting (?:inequalit|identit|oppression)'
    rf'|\bintersection\w*\W+(?:\w+\W+){{0,4}}?{AX_EN}\b|\b{AX_EN}\W+(?:\w+\W+){{0,4}}?intersection'
    rf'|\bintersecci\w*\W+(?:\w+\W+){{0,4}}?{AX_ES}|\b{AX_ES}\W+(?:\w+\W+){{0,4}}?intersecci')
RE_AFIN = re.compile(
    r'matrix of domination|multiple jeopardy|kyriarch|coloniality of gender|simultaneity of oppression'
    r'|entangled inequalit|multiple marginali|interlocking\W+(?:\w+\W+){0,3}?(?:oppression|inequalit|domination)'
    r'|matriz de (?:dominaci|opresi)|colonialidad de(?:l)? g[eé]nero|entronque patriarcal|consustancialidad'
    r'|desigualdades entrelazadas|imbricaci|entrelazad\w*\W+(?:\w+\W+){0,3}?(?:opresi|dominaci)')


def norm_doi(s: pd.Series) -> pd.Series:
    return (s.fillna('').astype(str).str.lower().str.strip()
             .str.replace(r'^https?://(dx\.)?doi\.org/', '', regex=True))


def english_title(t) -> str:
    """Scopus pone el título original entre corchetes: 'English; [Original]'."""
    t = '' if pd.isna(t) else str(t)
    return re.split(r';?\s*\[', t, maxsplit=1)[0].strip()


def norm_title(t) -> str:
    s = unicodedata.normalize('NFD', english_title(t).lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', s)).strip()


def first_author(s) -> str:
    if pd.isna(s): return ''
    return re.split(r'[;,]', str(s))[0].strip().lower()[:30]


def nivel_ancla(row) -> str:
    tak = ' '.join(str(row.get(c, '') or '') for c in ['Title', 'Abstract', 'Author Keywords']).lower()
    if RE_NUCLEO.search(tak): return 'A_nucleo'
    if RE_AMPLIADA.search(tak): return 'A_ampliada'
    if RE_AFIN.search(tak): return 'B_afin'
    return 'solo_index_keywords'


def main():
    raw = pd.read_csv(RAW, encoding='utf-8-sig')
    raw.columns = [c.strip() for c in raw.columns]
    n_raw = len(raw)
    print(f"[1] Export Scopus: {n_raw} registros")
    for c in PIPELINE_COLS + EXTRA_COLS:
        if c not in raw.columns:
            raw[c] = ''
    df = raw[PIPELINE_COLS + EXTRA_COLS].copy()

    # ── Exclusión por regla ──
    abs_txt = df['Abstract'].fillna('').astype(str).str.strip()
    sin_abs = (abs_txt.str.len() < 100) | abs_txt.str.contains(r'^\[No abstract available\]', regex=True)
    tipo_excl = df['Document Type'].isin(EXCLUDED_TYPES)
    excl = pd.DataFrame({'sin_abstract': sin_abs, 'tipo_excluido': tipo_excl & ~sin_abs})
    df = df[~(sin_abs | tipo_excl)].copy()
    print(f"[2] Excluidos por regla: {int(sin_abs.sum())} sin abstract, "
          f"{int(excl['tipo_excluido'].sum())} Erratum/Conference review → quedan {len(df)}")

    # ── Deduplicación ──
    df['_doi'] = norm_doi(df['DOI'])
    df['_key'] = (df['Title'].apply(norm_title) + '|' + df['Year'].astype(str) + '|'
                  + df['Authors'].apply(first_author))
    n0 = len(df)
    con_doi = df[df['_doi'].str.startswith('10.')].drop_duplicates('_doi')
    sin_doi = df[~df['_doi'].str.startswith('10.')].drop_duplicates('_key')
    sin_doi = sin_doi[~sin_doi['_key'].isin(set(con_doi['_key']))]
    df = pd.concat([con_doi, sin_doi]).drop_duplicates('_key')
    n_dups = n0 - len(df)
    print(f"[3] Duplicados eliminados: {n_dups} → {len(df)}")

    # ── Nivel del ancla ──
    df['nivel_ancla'] = df.apply(nivel_ancla, axis=1)
    print(f"[4] Nivel del ancla:\n{df['nivel_ancla'].value_counts().to_string()}")

    # ── Idioma normalizado ──
    lang = df['Language of Original Document'].fillna('').astype(str)
    df['idioma'] = [('es' if 'Spanish' in l else 'en' if 'English' in l else 'otro') for l in lang]

    df = df.sort_values(['Year', 'Title'], ascending=[False, True]).reset_index(drop=True)
    df.insert(0, 'paper_id', range(len(df)))
    df['_source'] = 'scopus_v2'
    out_cols = ['paper_id'] + PIPELINE_COLS + EXTRA_COLS + ['nivel_ancla', 'idioma', '_source', '_doi']
    df[out_cols].to_csv(DATA / 'v2_corpus_consolidated.csv', index=False)

    meta = {
        'identificados_scopus': n_raw,
        'excluidos_regla': {'sin_abstract': int(sin_abs.sum()),
                            'erratum_o_conference_review': int(excl['tipo_excluido'].sum())},
        'duplicados': n_dups,
        'a_cribado': len(df),
        'nivel_ancla': df['nivel_ancla'].value_counts().to_dict(),
        'idioma': df['idioma'].value_counts().to_dict(),
    }
    (DATA / 'v2_prisma_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\n[OK] data/v2_corpus_consolidated.csv ({len(df)}) + data/v2_prisma_meta.json")


if __name__ == '__main__':
    main()
