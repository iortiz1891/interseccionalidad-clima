#!/usr/bin/env python3
"""
00b_openalex.py — v3 (segunda fuente abierta): corre la búsqueda de data/v3_query_openalex.json en la API de OpenAlex,
solo para trabajos en español y portugués.

OpenAlex limita las búsquedas con más de 5 operadores booleanos, así que no se usa
AND/OR en el texto: cada bloque va como un filtro con valores separados por «|» (OR) y
los filtros se separan por comas (AND):

  title_and_abstract.search:<interseccional_i>,title_and_abstract.search:<clima_j>,
  language:es|pt,publication_year:>1988

Los bloques se parten en grupos (OpenAlex limita los valores por filtro) y se corren
todas las combinaciones; los registros se unen por ID de OpenAlex. Si la API rechaza un
grupo, se parte en dos y se reintenta.

Clave opcional (gratuita, https://openalex.org/settings/api): OPENALEX_API_KEY como
variable de entorno o línea OPENALEX_API_KEY=... en ~/.config/openalex_creds. Sin clave,
la API comparte un presupuesto diario pequeño por red; esta búsqueda cabe en él.

Salidas:
  data/v3_openalex_raw.csv      un registro por trabajo (no se versiona)
  data/v3_openalex_meta.json    fecha, consultas, totales
  work/v3_openalex/*.json       respuestas crudas (no se versionan)

Uso (desde la raíz del repo):
  python3 pipeline/v3/00b_openalex.py [--solo-contar]
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

API = 'https://api.openalex.org/works'
DATA = Path('data')
WORK = Path('work/v3_openalex')
POR_PAGINA = 200
TAM_INTER = 30
TAM_CLIMA = 45
CAMPOS = ('id,doi,title,display_name,publication_year,language,type,authorships,'
          'primary_location,abstract_inverted_index,keywords,cited_by_count,open_access')


class Rechazo(Exception):
    pass


def _clave() -> str:
    v = os.environ.get('OPENALEX_API_KEY', '').strip()
    p = Path.home() / '.config' / 'openalex_creds'
    if not v and p.exists():
        for line in p.read_text().splitlines():
            if line.startswith('OPENALEX_API_KEY='):
                v = line.split('=', 1)[1].strip()
    return v


def pedir(params: dict) -> dict:
    k = _clave()
    if k:
        params = {**params, 'api_key': k}
    for intento in range(5):
        r = requests.get(API, params=params, headers={'User-Agent': 'revisa-pipeline'}, timeout=90)
        if r.status_code == 429 and 'operators' not in r.text and 'budget' not in r.text.lower():
            time.sleep(5 * (intento + 1))
            continue
        if r.status_code >= 500:
            time.sleep(5 * (intento + 1))
            continue
        if r.status_code in (400, 403, 413, 414):
            raise Rechazo(f'{r.status_code}: {r.text[:200]}')
        if r.status_code != 200:
            sys.exit(f'[FATAL] {r.status_code}: {r.text[:400]}')
        return r.json()
    sys.exit('[FATAL] OpenAlex siguió respondiendo 429/5xx después de 5 intentos '
             '(¿se agotó el presupuesto diario sin clave?).')


def filtro(inter: list[str], clima: list[str], q: dict) -> str:
    return (f"title_and_abstract.search:{'|'.join(inter)},"
            f"title_and_abstract.search:{'|'.join(clima)},"
            f"language:{'|'.join(q['idiomas'])},publication_year:>{q['anio_minimo'] - 1}")


def trozos(xs: list, n: int) -> list[list]:
    return [xs[i:i + n] for i in range(0, len(xs), n)]


def contar(f: str) -> int:
    return int(pedir({'filter': f, 'per-page': 1, 'select': 'id'})['meta']['count'])


def descargar(f: str, etiqueta: str) -> list[dict]:
    """Paginación simple (page=): sin clave, OpenAlex no permite cursor, y cada consulta
    trae muy por debajo del tope de 10,000 resultados de la paginación simple."""
    out, pagina = [], 1
    while True:
        d = pedir({'filter': f, 'per-page': POR_PAGINA, 'page': pagina, 'select': CAMPOS})
        (WORK / f'{etiqueta}_{pagina:03d}.json').write_text(json.dumps(d, ensure_ascii=False))
        out += d['results']
        n = int(d['meta']['count'])
        if n > 10_000:
            sys.exit(f'[FATAL] {etiqueta}: {n} resultados; la paginación simple llega a 10,000.')
        if not d['results'] or len(out) >= n:
            return out
        pagina += 1


def correr(q: dict, accion):
    """Aplica accion(filtro, etiqueta) a cada combinación de grupos; parte los grupos rechazados."""
    pend = [(a, b) for a in trozos(q['interseccional'], TAM_INTER) for b in trozos(q['clima'], TAM_CLIMA)]
    hechos, k = [], 0
    while pend:
        a, b = pend.pop(0)
        try:
            res = accion(filtro(a, b, q), f'c{k:02d}')
        except Rechazo as e:
            if len(a) == 1 and len(b) == 1:
                sys.exit(f'[FATAL] Ni con un término por bloque la acepta: {a} {b} ({e})')
            print(f'    {e} → parto el grupo ({len(a)}×{len(b)} términos)')
            if len(a) >= len(b):
                m = len(a) // 2
                pend[:0] = [(a[:m], b), (a[m:], b)]
            else:
                m = len(b) // 2
                pend[:0] = [(a, b[:m]), (a, b[m:])]
            continue
        hechos.append((len(a), len(b), res))
        k += 1
    return hechos


def resumen(inv: dict | None) -> str:
    if not inv:
        return ''
    pos = {}
    for w, ps in inv.items():
        for p in ps:
            pos[p] = w
    return ' '.join(pos[i] for i in sorted(pos))


def fila(w: dict) -> dict:
    au = w.get('authorships') or []
    autores = '; '.join((a.get('author') or {}).get('display_name', '') for a in au)
    afil = '; '.join(sorted({', '.join(x for x in (i.get('display_name'), i.get('country_code')) if x)
                             for a in au for i in (a.get('institutions') or [])}))
    src = ((w.get('primary_location') or {}).get('source') or {}).get('display_name', '')
    kw = '; '.join(k.get('display_name', '') for k in (w.get('keywords') or []))
    lang = {'es': 'Spanish', 'pt': 'Portuguese', 'en': 'English'}.get(w.get('language'), w.get('language') or '')
    return {
        'Title': w.get('title') or w.get('display_name') or '',
        'Year': w.get('publication_year') or '',
        'DOI': (w.get('doi') or '').replace('https://doi.org/', ''),
        'Abstract': resumen(w.get('abstract_inverted_index')),
        'Authors': autores, 'Source title': src, 'Affiliations': afil,
        'Language of Original Document': lang,
        'Document Type': (w.get('type') or '').replace('-', ' '),
        'Author Keywords': '',                 # OpenAlex no trae las palabras clave de autor
        'Index Keywords': kw,                  # palabras clave asignadas por OpenAlex
        'Cited by': w.get('cited_by_count', ''),
        'EID': '', 'OpenAlex ID': w.get('id', '').replace('https://openalex.org/', ''),
        'Publication Stage': '',
        'Open Access': 'All Open Access' if (w.get('open_access') or {}).get('is_oa') else '',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo-contar', action='store_true')
    args = ap.parse_args()
    q = json.loads((DATA / 'v3_query_openalex.json').read_text())
    print(f"[1] {len(q['interseccional'])} términos interseccionales × {len(q['clima'])} climáticos · "
          f"idiomas {q['idiomas']} · clave: {'sí' if _clave() else 'no'}")

    conteos = correr(q, lambda f, et: contar(f))
    print(f"[2] {len(conteos)} consultas · suma de conteos (con repetidos): {sum(c for _, _, c in conteos)}")
    if args.solo_contar:
        return

    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    lotes = correr(q, descargar)
    por_id = {}
    for _, _, ws in lotes:
        for w in ws:
            por_id.setdefault(w['id'], w)
    df = pd.DataFrame([fila(w) for w in por_id.values()])
    df.to_csv(DATA / 'v3_openalex_raw.csv', index=False)
    sin_abs = int((df['Abstract'].str.len() < 100).sum())
    print(f"[3] {len(df)} registros únicos → data/v3_openalex_raw.csv ({sin_abs} sin resumen) · "
          f"idioma: {df['Language of Original Document'].value_counts().to_dict()}")
    meta = {'fecha': date.today().isoformat(), 'fuente': 'OpenAlex API (works)',
            'consulta': 'data/v3_query_openalex.json', 'consultas': len(lotes),
            'terminos_por_consulta': [[a, b] for a, b, _ in lotes],
            'suma_conteos_con_repetidos': sum(len(ws) for _, _, ws in lotes),
            'registros_unicos': len(df), 'sin_resumen': sin_abs,
            'idioma': df['Language of Original Document'].value_counts().to_dict(),
            'tipo': df['Document Type'].value_counts().to_dict()}
    (DATA / 'v3_openalex_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print('[OK] data/v3_openalex_meta.json')


if __name__ == '__main__':
    main()
