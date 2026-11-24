#!/usr/bin/env python3
"""
00_scopus_api.py — v3: ejecuta la cadena de data/v3_query_scopus.txt en la Scopus Search API.

Credenciales (nunca van al repo), como variables de entorno o como líneas NOMBRE=valor
en ~/.config/scopus_creds:
  SCOPUS_API_KEY       obligatoria (https://dev.elsevier.com)
  SCOPUS_INSTTOKEN     opcional; hace falta fuera de la red institucional para la vista
                       COMPLETE, que es la que trae resúmenes y palabras clave.

La API no acepta LIMIT-TO: el bloque de idiomas de la cadena web se sustituye por
LANGUAGE(...) y la cadena se corre una vez por idioma. Así cada registro sabe en qué
idioma(s) lo indexa Scopus (la vista de búsqueda no trae ese campo).

La cadena completa codificada en la URL pasa de 9 KB y la API responde 413. Por eso el
bloque climático (el segundo TITLE-ABS-KEY) se parte en grupos de términos unidos por OR:
  bloque_interseccional AND TITLE-ABS-KEY ( grupo_i ) AND PUBYEAR > 1988 AND LANGUAGE(x)
La unión de los grupos equivale a la cadena original (A AND (B1 OR B2) = (A AND B1) OR
(A AND B2)); los registros se unen por EID. Si un grupo sigue siendo demasiado largo, el
grupo se parte en dos y se reintenta.

Salidas:
  data/v3_scopus_raw.csv        mismas columnas que el export CSV de Scopus (no se versiona)
  data/v3_search_meta.json      fecha, cadena enviada y totales por idioma
  work/v3_scopus_api/*.json     respuestas crudas de la API (no se versionan)

Uso (desde la raíz del repo):
  export SCOPUS_API_KEY=...          # y, si hace falta, SCOPUS_INSTTOKEN=...
  python3 pipeline/v3/00_scopus_api.py
  python3 pipeline/v3/00_scopus_api.py --solo-contar   # solo totales, sin descargar
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

API = 'https://api.elsevier.com/content/search/scopus'
DATA = Path('data')
WORK = Path('work/v3_scopus_api')
IDIOMAS = {'English': 'english', 'Spanish': 'spanish', 'Portuguese': 'portuguese'}
POR_PAGINA = 25            # máximo de la vista COMPLETE
LIMITE_URL = 3400          # caracteres de la consulta ya codificada (a ~3,500 la API ya rechaza algunas)


class ConsultaLarga(Exception):
    """La API rechazó la consulta por longitud (413/414, o 400 'Request header is too large')."""


def cadena_api() -> str:
    """Cadena web → cadena de la API: quita el bloque LIMIT-TO y normaliza espacios."""
    t = (DATA / 'v3_query_scopus.txt').read_text()
    t = re.split(r'\bAND\s*\(\s*LIMIT-TO', t)[0]
    return re.sub(r'\s+', ' ', t).strip()


def _cierre(s: str, i: int) -> int:
    """Índice del paréntesis que cierra el que está en s[i], ignorando lo que va entre comillas."""
    prof, comillas = 0, False
    for k in range(i, len(s)):
        c = s[k]
        if c == '"':
            comillas = not comillas
        elif not comillas and c == '(':
            prof += 1
        elif not comillas and c == ')':
            prof -= 1
            if prof == 0:
                return k
    raise ValueError('paréntesis sin cerrar')


def _ors(s: str) -> list[str]:
    """Parte s en sus términos unidos por OR en el nivel superior."""
    partes, prof, comillas, ini = [], 0, False, 0
    k = 0
    while k < len(s):
        c = s[k]
        if c == '"':
            comillas = not comillas
        elif not comillas and c == '(':
            prof += 1
        elif not comillas and c == ')':
            prof -= 1
        elif not comillas and prof == 0 and s.startswith(' OR ', k):
            partes.append(s[ini:k].strip())
            ini = k + 4
            k += 3
        k += 1
    partes.append(s[ini:].strip())
    return [p for p in partes if p]


def partir_cadena(base: str) -> tuple[str, list[str], str]:
    """(bloque interseccional, términos del bloque climático, resto: AND PUBYEAR...)."""
    i = base.index('AND TITLE-ABS-KEY (', 1)
    a = base[:i].strip()
    j = base.index('(', i)
    k = _cierre(base, j)
    return a, _ors(base[j + 1:k]), base[k + 1:].strip()


def _largo(q: str) -> int:
    return len(urlencode({'query': q}))


def grupos(a: str, terminos: list[str], cola: str, limite: int) -> list[list[str]]:
    """Agrupa los términos del bloque climático para que cada consulta quepa en `limite`."""
    sufijo = ' AND LANGUAGE(portuguese)'   # el idioma más largo
    out, actual = [], []
    for t in terminos:
        prueba = actual + [t]
        q = f'{a} AND TITLE-ABS-KEY ( {" OR ".join(prueba)} ) {cola}{sufijo}'
        if actual and _largo(q) > limite:
            out.append(actual)
            actual = [t]
        else:
            actual = prueba
    if actual:
        out.append(actual)
    return out


def consulta(a: str, grupo: list[str], cola: str, idioma: str) -> str:
    return f'{a} AND TITLE-ABS-KEY ( {" OR ".join(grupo)} ) {cola} AND LANGUAGE({idioma})'


def _credencial(nombre: str) -> str:
    """Variable de entorno o, si no existe, línea NOMBRE=valor de ~/.config/scopus_creds."""
    v = os.environ.get(nombre, '').strip()
    p = Path.home() / '.config' / 'scopus_creds'
    if not v and p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(nombre + '='):
                v = line.split('=', 1)[1].strip()
    return v


def cabeceras() -> dict:
    key = _credencial('SCOPUS_API_KEY')
    if not key:
        sys.exit('[FATAL] Falta SCOPUS_API_KEY (variable de entorno o ~/.config/scopus_creds).')
    h = {'X-ELS-APIKey': key, 'Accept': 'application/json'}
    tok = _credencial('SCOPUS_INSTTOKEN')
    if tok:
        h['X-ELS-Insttoken'] = tok
    return h


def pedir(params: dict, h: dict) -> dict:
    """GET con reintentos; ConsultaLarga si el servidor rechaza la URL por longitud."""
    for intento in range(5):
        r = requests.get(API, params=params, headers=h, timeout=90)
        if r.status_code in (413, 414) or (r.status_code == 400 and 'too large' in r.text):
            raise ConsultaLarga(r.status_code)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (intento + 1))
            continue
        if r.status_code in (401, 403):
            sys.exit(f'[FATAL] {r.status_code}: la API rechazó la clave o la vista COMPLETE. '
                     'La vista COMPLETE exige acceso institucional (red de la universidad o '
                     f'SCOPUS_INSTTOKEN). Respuesta: {r.text[:300]}')
        if r.status_code != 200:
            sys.exit(f'[FATAL] {r.status_code}: {r.text[:500]}')
        return r.json()
    sys.exit('[FATAL] La API siguió respondiendo 429/5xx después de 5 intentos.')


def total(q: str, h: dict) -> int:
    d = pedir({'query': q, 'count': 1, 'view': 'STANDARD'}, h)
    return int(d['search-results'].get('opensearch:totalResults', 0))


def descargar(q: str, etiqueta: str, h: dict) -> list[dict]:
    WORK.mkdir(parents=True, exist_ok=True)
    cursor, entradas, pagina = '*', [], 0
    while True:
        d = pedir({'query': q, 'count': POR_PAGINA, 'view': 'COMPLETE', 'cursor': cursor}, h)
        sr = d['search-results']
        (WORK / f'{etiqueta}_{pagina:04d}.json').write_text(json.dumps(d, ensure_ascii=False))
        lote = [e for e in sr.get('entry', []) if 'error' not in e]
        entradas += lote
        n_tot = int(sr.get('opensearch:totalResults', 0))
        print(f'    {etiqueta}: {len(entradas)}/{n_tot}', end='\r')
        siguiente = (sr.get('cursor') or {}).get('@next')
        if not lote or not siguiente or siguiente == cursor or len(entradas) >= n_tot:
            break
        cursor, pagina = siguiente, pagina + 1
        time.sleep(0.2)
    print()
    return entradas


def fila(e: dict) -> dict:
    autores = '; '.join(a.get('authname', '') for a in (e.get('author') or []))
    afil = '; '.join(', '.join(x for x in (a.get('affilname'), a.get('affiliation-city'),
                                            a.get('affiliation-country')) if x)
                     for a in (e.get('affiliation') or []))
    kw = (e.get('authkeywords') or '').replace(' | ', '; ')
    return {
        'Title': e.get('dc:title', ''),
        'Year': (e.get('prism:coverDate') or '')[:4],
        'DOI': e.get('prism:doi', ''),
        'Abstract': e.get('dc:description', '') or '',
        'Authors': autores or e.get('dc:creator', ''),
        'Source title': e.get('prism:publicationName', ''),
        'Affiliations': afil,
        'Document Type': e.get('subtypeDescription', ''),
        'Author Keywords': kw,
        'Cited by': e.get('citedby-count', ''),
        'Index Keywords': '',
        'EID': e.get('eid', ''),
        'Publication Stage': '',
        'Open Access': 'All Open Access' if str(e.get('openaccess', '0')) == '1' else '',
    }


def correr(a, terminos, cola, h, accion):
    """Aplica accion(q, etiqueta) a cada grupo × idioma. Si la API rechaza un grupo por
    largo, ese grupo se parte en dos y se reintenta."""
    pendientes = grupos(a, terminos, cola, LIMITE_URL)
    hechos, out = [], []
    while pendientes:
        g = pendientes.pop(0)
        gi = len(hechos)
        try:
            res = [(n, gi, accion(consulta(a, g, cola, kw), f'{kw}_g{gi:02d}'))
                   for n, kw in IDIOMAS.items()]
        except ConsultaLarga as e:
            if len(g) == 1:
                sys.exit(f'[FATAL] Ni con un solo término cabe la consulta: {g[0]}')
            print(f'    {e.args[0]}: grupo de {len(g)} términos demasiado largo; lo parto en dos')
            m = len(g) // 2
            pendientes[:0] = [g[:m], g[m:]]
            continue
        hechos.append(g)
        out += res
    return hechos, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo-contar', action='store_true')
    args = ap.parse_args()
    h = cabeceras()
    base = cadena_api()
    a, terminos, cola = partir_cadena(base)
    print(f'[1] Cadena: {len(base):,} caracteres · bloque climático: {len(terminos)} términos · '
          f'resto: "{cola}"')

    gs, conteos = correr(a, terminos, cola, h, lambda q, et: total(q, h))
    print(f'[2] {len(gs)} grupos de términos climáticos')
    totales = {n: sum(c for nn, _, c in conteos if nn == n) for n in IDIOMAS}
    for gi, g in enumerate(gs):
        print(f'    g{gi:02d} ({len(g):3d} términos): ' +
              ' · '.join(f'{n} {c}' for n, ggi, c in conteos if ggi == gi))
    print(f'    Suma por idioma (con repetidos entre grupos): {totales}')
    if args.solo_contar:
        return

    por_eid: dict[str, dict] = {}
    idiomas: dict[str, set[str]] = {}
    shutil.rmtree(WORK, ignore_errors=True)   # sin páginas de corridas o grupos anteriores
    gs_desc, lotes = correr(a, terminos, cola, h, lambda q, et: descargar(q, et, h))
    for nombre, _, entradas in lotes:
        for e in entradas:
            eid = e.get('eid')
            por_eid.setdefault(eid, e)
            idiomas.setdefault(eid, set()).add(nombre)

    filas = []
    for eid, e in por_eid.items():
        f = fila(e)
        f['Language of Original Document'] = '; '.join(n for n in IDIOMAS if n in idiomas[eid])
        filas.append(f)
    df = pd.DataFrame(filas)
    df.to_csv(DATA / 'v3_scopus_raw.csv', index=False)
    sin_abs = int((df['Abstract'].fillna('').str.len() < 100).sum())
    print(f'[3] {len(df)} registros únicos → data/v3_scopus_raw.csv ({sin_abs} sin resumen)')
    if len(df) and sin_abs / len(df) > 0.5:
        print('    AVISO: más de la mitad no trae resumen. Probablemente la clave no tiene acceso '
              'a la vista COMPLETE desde esta red; prueba con SCOPUS_INSTTOKEN o desde la red '
              'institucional.')

    unicos_idioma = {n: sum(1 for s in idiomas.values() if n in s) for n in IDIOMAS}
    meta = {'fecha': date.today().isoformat(), 'fuente': 'Scopus Search API (vista COMPLETE)',
            'cadena_web': 'data/v3_query_scopus.txt', 'cadena_api': base,
            'idioma_por_consulta': 'AND LANGUAGE(english|spanish|portuguese), una consulta por idioma',
            # La descarga (vista COMPLETE + cursor) alarga la petición: ahí la API rechaza
            # grupos que en el conteo sí pasaban y se parten de nuevo.
            'particion': {'limite_caracteres': LIMITE_URL,
                          'grupos_conteo': len(gs), 'grupos_descarga': len(gs_desc),
                          'terminos_por_grupo_descarga': [len(g) for g in gs_desc]},
            'suma_por_idioma_con_repetidos': totales, 'unicos_por_idioma': unicos_idioma,
            'registros_unicos': len(df), 'sin_resumen': sin_abs}
    (DATA / 'v3_search_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print('[OK] data/v3_search_meta.json')


if __name__ == '__main__':
    main()
