#!/usr/bin/env python3
"""
00d_openalex_idioma.py — v3: trabajos en español o portugués que OpenAlex etiqueta con otro idioma.

La consulta de pipeline/v3/00b_openalex.py filtra por language:es|pt, y OpenAlex asigna el idioma
a partir del título (y a veces se equivoca). Así quedó fuera, por ejemplo, un artículo en español
sobre los huracanes Otis y John en Acapulco desde una perspectiva de género interseccional,
etiquetado como inglés.

Este script corre la misma consulta (mismos bloques y años), pero:
  · el bloque interseccional se limita a los términos en español y portugués de
    data/v3_query_openalex.json (desde «interseccional» hasta el final): un trabajo en inglés
    que solo dice «intersectional» lo cubre Scopus;
  · el filtro de idioma es el contrario: language:!es,language:!pt.
Después estima el idioma real con las palabras funcionales del título y del inicio del resumen
(español, portugués, inglés o catalán). pipeline/v3/01_ingesta.py incorpora solo los que
resultan en español o portugués, con las mismas reglas que el resto de OpenAlex.

Salidas:
  data/v3_openalex_idioma_raw.csv    un registro por trabajo, con idioma_openalex e idioma_detectado (no se
                                     versiona, como data/v3_openalex_raw.csv)
  data/v3_openalex_idioma_meta.json  fecha, consulta, conteos

Uso (desde la raíz del repo):
  python3 pipeline/v3/00d_openalex_idioma.py [--reclasificar]
  --reclasificar: no consulta OpenAlex; recalcula idioma_detectado sobre el CSV ya descargado.
"""
from __future__ import annotations
import importlib.util
import json
import sys
import re
import time
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

DATA = Path('data')

_spec = importlib.util.spec_from_file_location('oa_v3', 'pipeline/v3/00b_openalex.py')
oa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oa)

# Palabras funcionales frecuentes y propias de cada idioma (las compartidas, como «de» o «a», no cuentan).
FUNC = {
    'es': {'el', 'los', 'las', 'del', 'y', 'una', 'por', 'con', 'que', 'se', 'su', 'sus', 'como',
           'entre', 'desde', 'sobre', 'esta', 'este', 'también', 'mujeres', 'cambio'},
    'pt': {'os', 'da', 'do', 'das', 'dos', 'e', 'uma', 'com', 'não', 'ao', 'aos', 'pela', 'pelo',
           'na', 'no', 'nas', 'nos', 'em', 'são', 'também', 'mulheres', 'mudanças'},
    'en': {'the', 'and', 'of', 'in', 'on', 'with', 'from', 'that', 'this', 'is', 'are', 'for',
           'women', 'climate', 'to'},
    'ca': {'els', 'les', 'dels', 'amb', 'i', 'per', 'què', 'aquest', 'aquesta', 'són', 'dones',
           'canvi', 'pel', 'als'},
}


def idioma_detectado(texto: str) -> str:
    w = re.findall(r"[a-záéíóúàèòçãõâêôüñï]+", texto.lower())
    c = Counter(w)
    score = {k: sum(c[x] for x in v) for k, v in FUNC.items()}
    if not any(score.values()):
        return ''
    return max(score, key=score.get)


def detectar(df: pd.DataFrame) -> pd.Series:
    # Título + inicio del resumen: varios resúmenes son bilingües (p. ej. inglés y, al final, portugués).
    return pd.Series([idioma_detectado(f"{t} {str(a)[:400]}") for t, a in
                      zip(df['Title'].fillna(''), df['Abstract'].fillna(''))], index=df.index)


def guardar(df: pd.DataFrame, meta: dict):
    df = df.sort_values(['idioma_detectado', 'Year', 'Title'])
    df.to_csv(DATA / 'v3_openalex_idioma_raw.csv', index=False)
    det = df['idioma_detectado'].value_counts().to_dict()
    print(f'[2] Idioma detectado: {det} · etiqueta de OpenAlex: {df["idioma_openalex"].value_counts().to_dict()}')
    meta.update({'identificados': len(df), 'idioma_openalex': df['idioma_openalex'].value_counts().to_dict(),
                 'idioma_detectado': det})
    (DATA / 'v3_openalex_idioma_meta.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    print('[OK] data/v3_openalex_idioma_raw.csv + data/v3_openalex_idioma_meta.json')


def main():
    if '--reclasificar' in sys.argv:
        df = pd.read_csv(DATA / 'v3_openalex_idioma_raw.csv', dtype={'Year': str})
        df['idioma_detectado'] = detectar(df)
        guardar(df, json.loads((DATA / 'v3_openalex_idioma_meta.json').read_text()))
        return
    q = json.loads((DATA / 'v3_query_openalex.json').read_text())
    inter = q['interseccional'][q['interseccional'].index('interseccional'):]
    por_id, consultas = {}, 0
    for a in oa.trozos(inter, oa.TAM_INTER):
        for b in oa.trozos(q['clima'], oa.TAM_CLIMA):
            f = (f"title_and_abstract.search:{'|'.join(a)},title_and_abstract.search:{'|'.join(b)},"
                 f"language:!es,language:!pt,publication_year:>{q['anio_minimo'] - 1}")
            pagina = 1
            while True:
                d = oa.pedir({'filter': f, 'per-page': oa.POR_PAGINA, 'page': pagina, 'select': oa.CAMPOS})
                for w in d['results']:
                    por_id[w['id']] = w
                if len(d['results']) < oa.POR_PAGINA:
                    break
                pagina += 1
            consultas += 1
            time.sleep(0.5)
    print(f'[1] {consultas} consultas · {len(por_id)} trabajos únicos que OpenAlex no etiqueta como es/pt')

    df = pd.DataFrame([{**oa.fila(w), 'idioma_openalex': w.get('language') or ''} for w in por_id.values()])
    df['idioma_detectado'] = detectar(df)
    guardar(df, {'fecha': date.today().isoformat(), 'consultas': consultas,
                 'terminos_interseccionales': inter, 'filtro_idioma': 'language:!es,language:!pt'})

if __name__ == '__main__':
    main()
