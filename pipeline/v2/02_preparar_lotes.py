#!/usr/bin/env python3
"""
02_preparar_lotes.py — v2: divide el corpus en lotes para cribado + RSI.

Lee data/v2_corpus_consolidated.csv y escribe work/v2_lotes/lote_XX.jsonl
(un registro por línea). Cada registro lleva los mismos campos que la v1 le
pasaba al modelo (título, año, autores, keywords de autor, abstract) más el
tipo de documento y el idioma, que usa el cribado.

Uso:
    python3 pipeline/v2/02_preparar_lotes.py [--tam 70]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

DATA = Path("data")
OUT = Path("work/v2_lotes")


def _s(v, n=None):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ''
    s = str(v).strip()
    return s[:n] if n else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tam', type=int, default=70)
    args = ap.parse_args()
    df = pd.read_csv(DATA / 'v2_corpus_consolidated.csv')
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob('lote_*.jsonl'):
        old.unlink()
    n_lotes = 0
    for i in range(0, len(df), args.tam):
        chunk = df.iloc[i:i + args.tam]
        n_lotes += 1
        with (OUT / f'lote_{n_lotes:02d}.jsonl').open('w') as f:
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
    print(f'[OK] {len(df)} registros en {n_lotes} lotes de ≤{args.tam} → {OUT}/')


if __name__ == '__main__':
    main()
