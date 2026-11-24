#!/usr/bin/env python3
"""
02_preparar_lotes.py — v3: divide los registros que no reutilizan la evaluación de la v2 en lotes para cribado + RSI.

Lee data/v3_corpus_consolidated.csv (solo reutiliza_v2 = False) y escribe, un registro por línea,
work/v3_lotes/lote_XX.jsonl (Scopus y SciELO), work/v3_lotes/oa_lote_XX.jsonl (OpenAlex, que
se buscó y evaluó después) y work/v3_lotes/rs_lote_XX.jsonl (registros cuyo resumen se rescató
por DOI en OpenAlex). Cada registro lleva los mismos campos que la v1 le
pasaba al modelo (título, año, autores, keywords de autor, abstract) más el
tipo de documento y el idioma, que usa el cribado.

Uso:
    python3 pipeline/v3/02_preparar_lotes.py [--tam 40]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

DATA = Path("data")
OUT = Path("work/v3_lotes")


def _s(v, n=None):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ''
    s = str(v).strip()
    return s[:n] if n else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tam', type=int, default=40)
    args = ap.parse_args()
    df = pd.read_csv(DATA / 'v3_corpus_consolidated.csv')
    df = df[~df['reutiliza_v2'].astype(bool)]
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob('*lote_*.jsonl'):
        old.unlink()
    rs = df['resumen_fuente'].fillna('').eq('openalex_doi')
    es_oa = df['_source'].eq('openalex') & ~rs
    for prefijo, sub in [('lote', df[~es_oa & ~rs]), ('oa_lote', df[es_oa]), ('rs_lote', df[rs])]:
        n = escribir(sub, prefijo, args.tam)
        print(f'[OK] {len(sub)} registros en {n} lotes de ≤{args.tam} → {OUT}/{prefijo}_XX.jsonl')


def escribir(df: pd.DataFrame, prefijo: str, tam: int) -> int:
    n_lotes = 0
    for i in range(0, len(df), tam):
        chunk = df.iloc[i:i + tam]
        n_lotes += 1
        with (OUT / f'{prefijo}_{n_lotes:02d}.jsonl').open('w') as f:
            for _, r in chunk.iterrows():
                f.write(json.dumps({
                    'paper_id': int(r['paper_id']),
                    'title': _s(r['Title']),
                    'year': _s(r['Year']).replace('.0', ''),
                    'authors': _s(r['Authors'], 300),
                    'keywords': _s(r['Author Keywords'], 400),
                    'document_type': _s(r['Document Type']),
                    'language': _s(r['Language of Original Document']),
                    'abstract': _s(r['Abstract'], 5000),
                }, ensure_ascii=False) + '\n')
    return n_lotes


if __name__ == '__main__':
    main()
