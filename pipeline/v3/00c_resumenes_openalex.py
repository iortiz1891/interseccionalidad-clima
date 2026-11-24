#!/usr/bin/env python3
"""
00c_resumenes_openalex.py — v3: busca en OpenAlex, por DOI, el resumen de los registros que
llegan sin resumen de su fuente (Scopus, SciELO u OpenAlex ES/PT).

Scopus no trae resumen para muchas notas, editoriales y capítulos de libro que sí lo tienen en
OpenAlex (en cualquier idioma). Este script solo guarda lo que OpenAlex devuelve; las reglas
para aceptar un resumen rescatado están en pipeline/v3/01_ingesta.py (rescatar_resumenes).

Entradas: las mismas de 01_ingesta.py (data/v3_scopus_raw.csv, data/v3_scielo_export.json,
          data/v3_openalex_raw.csv).
Salida:   data/v3_resumenes_openalex.json  {fecha, buscados, resultados: {doi: {...}}}
          (OpenAlex publica sus datos con licencia CC0, así que se versiona).

Uso (desde la raíz del repo):
  python3 pipeline/v3/00c_resumenes_openalex.py
"""
from __future__ import annotations
import importlib.util
import json
import time
from datetime import date
from pathlib import Path

DATA = Path('data')


def _modulo(nombre: str, ruta: str):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


oa = _modulo('oa_v3', 'pipeline/v3/00b_openalex.py')
ing = _modulo('ing_v3', 'pipeline/v3/01_ingesta.py')


def main():
    dois = set()
    for df in (ing.leer_scopus(), ing.leer_scielo(), ing.leer_openalex()):
        df = ing.claves(df)
        sin = ing.sin_resumen(df)
        dois |= {d for d in df.loc[sin, '_doi'] if d.startswith('10.')}
    dois = sorted(dois)
    print(f'[1] {len(dois)} DOI de registros sin resumen en su fuente')

    res = {}
    for i in range(0, len(dois), 40):
        lote = dois[i:i + 40]
        r = oa.pedir({'filter': 'doi:' + '|'.join(lote), 'per-page': 50,
                      'select': 'id,doi,type,language,abstract_inverted_index'})
        for w in r['results']:
            d = (w.get('doi') or '').replace('https://doi.org/', '').lower()
            txt = oa.resumen(w.get('abstract_inverted_index'))
            res[d] = {'openalex_id': w['id'].rsplit('/', 1)[-1], 'tipo': w.get('type'),
                      'idioma': w.get('language'), 'palabras': len(txt.split()), 'resumen': txt}
        time.sleep(1)
    con = sum(v['palabras'] > 0 for v in res.values())
    print(f'[2] {len(res)} encontrados en OpenAlex · {con} con algún resumen')

    out = {'fecha': date.today().isoformat(), 'buscados': len(dois), 'encontrados': len(res),
           'resultados': dict(sorted(res.items()))}
    (DATA / 'v3_resumenes_openalex.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print('[OK] data/v3_resumenes_openalex.json')


if __name__ == '__main__':
    main()
