#!/usr/bin/env python3
"""
01_ingesta.py — v4: corpus v3 + trabajos en español y portugués de OpenAlex.

Entradas:
  data/v3_corpus_consolidated.csv   corpus v3 ya depurado (Scopus + SciELO)
  data/v4_openalex_raw.csv          salida de pipeline/v4/00_openalex.py (no se versiona)

Salidas:
  data/v4_corpus_consolidated.csv   registros que pasan a cribado
  data/v4_prisma_meta.json          conteos de identificación y exclusión, por fuente

Los registros de la v3 conservan su paper_id y su evaluación (reutiliza_v3 = True). Los de
OpenAlex se depuran con las mismas reglas (sin resumen, tipos que no son trabajos), se
deduplican entre sí y contra la v3 por DOI y por título + año + primer autor, y reciben
paper_id a partir del último de la v3.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import pandas as pd

DATA = Path("data")

_spec = importlib.util.spec_from_file_location('ing_v3', 'pipeline/v3/01_ingesta.py')
_v3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v3)

# Tipos de OpenAlex que no son trabajos de investigación o ensayo.
TIPOS_EXCLUIDOS = {'erratum', 'paratext', 'dataset', 'book review', 'retraction', 'peer review'}


def leer_openalex() -> pd.DataFrame:
    df = pd.read_csv(DATA / 'v4_openalex_raw.csv', dtype={'Year': str})
    df['Document Type'] = df['Document Type'].fillna('').map(_v3.tipo_doc)
    df['_source'] = 'openalex'
    df['_scielo_id'] = ''
    return df


def main():
    v3 = pd.read_csv(DATA / 'v3_corpus_consolidated.csv', dtype={'Year': str})
    oa = leer_openalex()
    n_oa = len(oa)
    print(f"[1] Corpus v3: {len(v3)} · OpenAlex (ES/PT): {n_oa}")

    abs_txt = oa['Abstract'].fillna('').astype(str).str.strip()
    sin_abs = abs_txt.str.len() < 100
    tipo = oa['Document Type'].str.lower().isin(TIPOS_EXCLUIDOS) & ~sin_abs
    oa = oa[~(sin_abs | tipo)].copy()
    print(f"[2] OpenAlex excluidos por regla: {int(sin_abs.sum())} sin resumen, {int(tipo.sum())} por tipo "
          f"({', '.join(sorted(TIPOS_EXCLUIDOS))})")

    oa = _v3.claves(oa)
    n0 = len(oa)
    oa = _v3.dedup(oa)
    dup_oa = n0 - len(oa)
    v3k = _v3.claves(v3.copy())
    v3k['_key'] = v3k['_key'].str.replace(r'\.0\|', '|', regex=True)
    en_v3 = (oa['_doi'].str.startswith('10.') & oa['_doi'].isin(set(v3k['_doi']))) | oa['_key'].isin(set(v3k['_key']))
    # Registros de la v3 que OpenAlex también encontró (para el conteo por fuente).
    ambas = (v3k['_doi'].str.startswith('10.') & v3k['_doi'].isin(set(oa.loc[en_v3, '_doi']))) | \
        v3k['_key'].isin(set(oa.loc[en_v3, '_key']))
    nuevos = oa[~en_v3].copy()
    print(f"[3] OpenAlex: {dup_oa} duplicados internos · {int(en_v3.sum())} ya en la v3 → {len(nuevos)} nuevos")

    nuevos['nivel_ancla'] = nuevos.apply(_v3.nivel_ancla, axis=1)
    lang = nuevos['Language of Original Document'].fillna('').astype(str)
    nuevos['idioma'] = ['es' if 'Spanish' in l else 'pt' if 'Portuguese' in l else
                        'en' if 'English' in l else 'otro' for l in lang]
    nuevos['_ord'] = pd.to_numeric(nuevos['Year'], errors='coerce')
    nuevos = nuevos.sort_values(['_ord', 'Title'], ascending=[False, True]).reset_index(drop=True)
    nuevos.insert(0, 'paper_id', range(int(v3['paper_id'].max()) + 1,
                                       int(v3['paper_id'].max()) + 1 + len(nuevos)))
    nuevos['reutiliza_v3'] = False

    v3 = v3.copy()
    v3['reutiliza_v3'] = True
    v3['OpenAlex ID'] = ''
    v3.loc[ambas.values, '_source'] = v3.loc[ambas.values, '_source'] + '+openalex'

    cols = list(v3.columns.drop('reutiliza_v3')) + ['reutiliza_v3']
    for c in cols:
        if c not in nuevos.columns:
            nuevos[c] = ''
    df = pd.concat([v3[cols], nuevos[cols]], ignore_index=True)
    df.to_csv(DATA / 'v4_corpus_consolidated.csv', index=False)
    print(f"[4] Corpus v4: {len(df)} registros ({len(v3)} de la v3 + {len(nuevos)} de OpenAlex)")
    print(f"    Nuevos por idioma: {nuevos['idioma'].value_counts().to_dict()} · por tipo: "
          f"{nuevos['Document Type'].value_counts().to_dict()}")

    m3 = json.loads((DATA / 'v3_prisma_meta.json').read_text())
    meta = {
        'identificados': {**m3['identificados'], 'openalex': n_oa},
        'excluidos_regla': {**m3['excluidos_regla'],
                            'openalex': {'sin_abstract': int(sin_abs.sum()), 'tipo': int(tipo.sum())}},
        'duplicados': {**m3['duplicados'], 'dentro_openalex': dup_oa, 'openalex_ya_en_v3': int(en_v3.sum())},
        'a_cribado': len(df),
        'fuente': df['_source'].value_counts().to_dict(),
        'nivel_ancla': df['nivel_ancla'].value_counts().to_dict(),
        'idioma': df['idioma'].value_counts().to_dict(),
        'reutilizan_evaluacion_v3': int(df['reutiliza_v3'].sum()),
        'evaluados_en_v4': int((~df['reutiliza_v3'].astype(bool)).sum()),
        'tipo_nuevos': nuevos['Document Type'].value_counts().to_dict(),
    }
    (DATA / 'v4_prisma_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print("[OK] data/v4_corpus_consolidated.csv + data/v4_prisma_meta.json")


if __name__ == '__main__':
    main()
