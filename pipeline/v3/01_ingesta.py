#!/usr/bin/env python3
"""
01_ingesta.py — v3: une Scopus (API), SciELO y OpenAlex (ES/PT), depura y deduplica.

Entradas:
  data/v3_scopus_raw.csv        salida de pipeline/v3/00_scopus_api.py (no se versiona)
  data/v3_scielo_export.json    export RIS de search.scielo.org, ya convertido a JSON
  data/v3_openalex_raw.csv      salida de pipeline/v3/00b_openalex.py (no se versiona)

Salidas:
  data/v3_corpus_consolidated.csv   registros que pasan a cribado, con paper_id
  data/v3_prisma_meta.json          conteos de identificación y exclusión, por fuente

Pasos:
  1. Normaliza ambas fuentes al esquema del pipeline v2.
  2. Excluye por regla: sin abstract (<100 caracteres), Erratum, Conference review.
  3. Deduplica dentro de cada fuente y entre fuentes (Scopus tiene prioridad), por DOI
     y luego por título normalizado + año + primer autor.
  4. Marca el nivel del ancla (ahora también con el vocabulario en portugués) y el idioma.
  5. Enlaza cada registro de Scopus o SciELO con su paper_id de la v2 (por EID, DOI o título), si lo tiene.
     Si además el resumen coincide con el de la v2 (similitud ≥ 0.98 sin la línea de
     copyright, que la API no trae), reutiliza_v2 = True y pipeline/v3/03_consolidar.py
     toma el cribado y la RSI de la v2: el modelo vería el mismo texto con el mismo prompt
     base. Los demás registros se evalúan de nuevo en la v3.
  6. Agrega los trabajos en español y portugués de OpenAlex (búsqueda hecha después de la de
     Scopus y SciELO): mismas reglas de exclusión, deduplicación entre sí y contra lo anterior,
     y paper_id a partir del último de Scopus + SciELO. Ninguno reutiliza la evaluación de la
     v2; se evaluaron en lotes propios (work/v3_salidas/oa_lote_*.jsonl).
  7. Rescata el resumen de los registros que su fuente trae sin resumen, buscándolo por DOI en
     OpenAlex (data/v3_resumenes_openalex.json, de pipeline/v3/00c_resumenes_openalex.py). Se
     acepta solo si (a) tiene ≥100 caracteres y ≥20 palabras sin contar el título, (b) el DOI no
     lo comparte otro registro (los capítulos con el DOI del libro reciben la descripción del
     libro) y (c) en un capítulo no empieza con «This book / Este libro / Este livro». Los
     rescatados pasan las mismas exclusiones por tipo y la misma deduplicación, reciben paper_id
     después del último de OpenAlex y se evalúan en un lote propio (work/v3_salidas/rs_lote_*.jsonl).
     La columna resumen_fuente vale «openalex_doi» en ellos.
  8. Agrega los trabajos en español o portugués que OpenAlex etiqueta con otro idioma
     (data/v3_openalex_idioma_raw.csv, de pipeline/v3/00d_openalex_idioma.py): solo los que
     el idioma detectado en el título y el inicio del resumen da como español o portugués, con
     las mismas exclusiones y la misma deduplicación que el resto de OpenAlex. Reciben paper_id
     después de los rescatados, la columna idioma_openalex guarda la etiqueta original y se
     evalúan en un lote propio (work/v3_salidas/oi_lote_*.jsonl).
"""
from __future__ import annotations
import importlib.util
import difflib
import json
import re
from pathlib import Path
import pandas as pd

DATA = Path("data")

_spec = importlib.util.spec_from_file_location('ing_v2', 'pipeline/v2/01_ingesta_scopus.py')
_v2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v2)
norm_doi, norm_title, first_author = _v2.norm_doi, _v2.norm_title, _v2.first_author
AX_EN, AX_ES = _v2.AX_EN, _v2.AX_ES

PIPELINE_COLS = _v2.PIPELINE_COLS
EXTRA_COLS = _v2.EXTRA_COLS
EXCLUDED_TYPES = {'erratum', 'conference review'}

# Ancla: las expresiones de la v2 más el vocabulario en portugués de la cadena v3.
AX_PT = (r'(?:g[eê]nero|ra[çc]a|racismo|sexo|sexualidade|classe|etnia|identidade|opress[ãa]o'
         r'|desigualdade|defici[eê]ncia|ind[ií]gena)')
RE_NUCLEO = re.compile(r'intersectional|interseccional|intersecional')
RE_AMPLIADA = re.compile(
    _v2.RE_AMPLIADA.pattern
    + rf'|\binterse[cç]+\w*\W+(?:\w+\W+){{0,4}}?{AX_PT}|\b{AX_PT}\W+(?:\w+\W+){{0,4}}?interse[cç]'
    + r'|intersecting systems of power|interlocking systems of power|overlapping oppression'
    + r'|interse[cç]+[ãa]o de opress')
RE_AFIN = re.compile(
    _v2.RE_AFIN.pattern
    + r'|opresiones (?:entrecruzadas|imbricadas)|desigualdades imbricadas|relaciones de poder entrelazadas'
    + r'|consubstancialidade|consubstantiality|coextensividade|imbrica[çc][ãa]o'
    + r'|matriz de (?:domina[çc][ãa]o|opress[ãa]o)|opress[õo]es (?:entrecruzadas|entrela[çc]adas)'
    + r'|desigualdades (?:interseccionais|entrela[çc]adas)|colonialidade d[eo] g[eê]nero'
    + r'|sistemas de (?:opress[ãa]o|domina[çc][ãa]o) entrela[çc]ados|marcadores sociais da diferen[çc]a')

# Palabras funcionales para adivinar el idioma del título original de SciELO.
_FUNC = {
    'pt': {'e', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'nas', 'nos', 'uma', 'um', 'para',
           'com', 'não', 'ao', 'à', 'às', 'pela', 'pelo', 'são', 'mulheres', 'mudanças'},
    'es': {'y', 'del', 'el', 'los', 'las', 'en', 'la', 'una', 'un', 'para', 'con', 'por',
           'desde', 'entre', 'mujeres', 'cambio'},
    'en': {'and', 'the', 'of', 'in', 'on', 'for', 'with', 'from', 'women', 'climate', 'to'},
}


def idioma_titulo(t: str, disponibles: str) -> str:
    langs = [x.strip() for x in str(disponibles or '').split(',') if x.strip()]
    if len(langs) == 1:
        return langs[0]
    w = re.findall(r'\w+', str(t).lower())
    score = {k: sum(x in v for x in w) for k, v in _FUNC.items()}
    return max(score, key=lambda k: (score[k], k == 'en'))


def nivel_ancla(row) -> str:
    tak = ' '.join(str(row.get(c, '') or '') for c in ['Title', 'Abstract', 'Author Keywords']).lower()
    if RE_NUCLEO.search(tak): return 'A_nucleo'
    if RE_AMPLIADA.search(tak): return 'A_ampliada'
    if RE_AFIN.search(tak): return 'B_afin'
    return 'solo_index_keywords'


def tipo_doc(s) -> str:
    s = '' if pd.isna(s) else str(s).strip()
    return s[:1].upper() + s[1:].lower()       # "Book Chapter" (API) → "Book chapter" (export)


def leer_scopus() -> pd.DataFrame:
    df = pd.read_csv(DATA / 'v3_scopus_raw.csv', dtype={'Year': str})
    for c in PIPELINE_COLS + EXTRA_COLS:
        if c not in df.columns:
            df[c] = ''
    df = df[PIPELINE_COLS + EXTRA_COLS].copy()
    df['Document Type'] = df['Document Type'].map(tipo_doc)
    df['_source'] = 'scopus'
    df['_scielo_id'] = ''
    return df


def leer_scielo() -> pd.DataFrame:
    recs = json.loads((DATA / 'v3_scielo_export.json').read_text())['records']
    filas = []
    for r in recs:
        lang = idioma_titulo(r.get('ti', ''), r.get('la', ''))
        filas.append({
            'Title': r.get('ti', ''), 'Year': str(r.get('py', '')), 'DOI': r.get('doi', ''),
            'Abstract': r.get('ab', ''), 'Authors': r.get('au', ''),
            'Source title': r.get('jo', '').replace('&amp;', '&'), 'Affiliations': '',
            'Language of Original Document': {'en': 'English', 'es': 'Spanish',
                                              'pt': 'Portuguese'}.get(lang, lang),
            'Document Type': 'Preprint' if r['id'].startswith('preprint') else 'Article',
            'Author Keywords': r.get('kw', ''), 'Cited by': '', 'Index Keywords': '',
            'EID': '', 'Publication Stage': '', 'Open Access': 'All Open Access',
            '_source': 'scielo', '_scielo_id': r['id'],
        })
    df = pd.DataFrame(filas)
    # Las versiones publicadas van antes que los preprints, para que la deduplicación
    # conserve la publicada.
    return df.sort_values('Document Type', key=lambda s: s.eq('Preprint')).reset_index(drop=True)


def sin_resumen(df: pd.DataFrame) -> pd.Series:
    abs_txt = df['Abstract'].fillna('').astype(str).str.strip()
    return (abs_txt.str.len() < 100) | abs_txt.str.contains(r'^\[No abstract available\]', regex=True)


def excluir(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    sin_abs = sin_resumen(df)
    tipo = df['Document Type'].str.lower().isin(EXCLUDED_TYPES) & ~sin_abs
    return df[~(sin_abs | tipo)].copy(), int(sin_abs.sum()), int(tipo.sum())


def claves(df: pd.DataFrame) -> pd.DataFrame:
    df['_doi'] = norm_doi(df['DOI'])
    df['_key'] = (df['Title'].apply(norm_title) + '|' + df['Year'].astype(str) + '|'
                  + df['Authors'].apply(first_author))
    return df


def dedup(df: pd.DataFrame) -> pd.DataFrame:
    con_doi = df[df['_doi'].str.startswith('10.')].drop_duplicates('_doi')
    sin_doi = df[~df['_doi'].str.startswith('10.')].drop_duplicates('_key')
    sin_doi = sin_doi[~sin_doi['_key'].isin(set(con_doi['_key']))]
    return pd.concat([con_doi, sin_doi]).drop_duplicates('_key')


def enlazar_v2(df: pd.DataFrame) -> pd.Series:
    v2 = claves(pd.read_csv(DATA / 'v2_corpus_consolidated.csv', dtype={'Year': str}))
    v2['_key'] = v2['_key'].str.replace(r'\.0\|', '|', regex=True)
    por_eid = dict(zip(v2['EID'].dropna(), v2['paper_id']))
    por_doi = dict(zip(v2.loc[v2['_doi'].str.startswith('10.'), '_doi'],
                       v2.loc[v2['_doi'].str.startswith('10.'), 'paper_id']))
    por_key = dict(zip(v2['_key'], v2['paper_id']))
    out = []
    for _, r in df.iterrows():
        pid = por_eid.get(r['EID']) if r['EID'] else None
        if pid is None and r['_doi'].startswith('10.'):
            pid = por_doi.get(r['_doi'])
        if pid is None:
            pid = por_key.get(r['_key'])
        out.append(pid)
    return pd.Series(out, index=df.index, dtype='Int64')


SIMILITUD_MIN = 0.98

# Tipos de OpenAlex que no son trabajos de investigación o ensayo.
TIPOS_EXCLUIDOS_OA = {'erratum', 'paratext', 'dataset', 'book review', 'retraction', 'peer review'}


def _limpio(s) -> str:
    s = re.sub(r'\s*(©|\(c\)|Copyright).*$', '', '' if pd.isna(s) else str(s), flags=re.S | re.I)
    return re.sub(r'\s+', ' ', s).strip()


def similitud_v2(df: pd.DataFrame) -> pd.Series:
    v2 = pd.read_csv(DATA / 'v2_corpus_consolidated.csv').set_index('paper_id')['Abstract']
    out = []
    for _, r in df.iterrows():
        if pd.isna(r['v2_paper_id']):
            out.append(None)
            continue
        a, b = _limpio(r['Abstract']), _limpio(v2.loc[int(r['v2_paper_id'])])
        out.append(1.0 if a == b else difflib.SequenceMatcher(None, a, b, autojunk=False).ratio())
    return pd.Series(out, index=df.index, dtype=float)


def leer_openalex() -> pd.DataFrame:
    df = pd.read_csv(DATA / 'v3_openalex_raw.csv', dtype={'Year': str})
    df['Document Type'] = df['Document Type'].fillna('').map(tipo_doc)
    df['_source'] = 'openalex'
    df['_scielo_id'] = ''
    return df


def agregar_openalex(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Agrega a df (Scopus + SciELO, ya con paper_id) los registros nuevos de OpenAlex."""
    oa = leer_openalex()
    n_oa = len(oa)
    sin_abs = sin_resumen(oa)
    tipo = oa['Document Type'].str.lower().isin(TIPOS_EXCLUIDOS_OA) & ~sin_abs
    oa = claves(oa[~(sin_abs | tipo)].copy())
    n0 = len(oa)
    oa = dedup(oa)
    dup_oa = n0 - len(oa)
    en_prev = (oa['_doi'].str.startswith('10.') & oa['_doi'].isin(set(df['_doi']))) | oa['_key'].isin(set(df['_key']))
    # Registros de Scopus o SciELO que OpenAlex también encontró (para el conteo por fuente).
    ambas = (df['_doi'].str.startswith('10.') & df['_doi'].isin(set(oa.loc[en_prev, '_doi']))) | \
        df['_key'].isin(set(oa.loc[en_prev, '_key']))
    df = df.copy()
    df.loc[ambas, '_source'] = df.loc[ambas, '_source'] + '+openalex'
    nuevos = oa[~en_prev].copy()
    print(f"[5] OpenAlex (ES/PT): {n_oa} identificados · {int(sin_abs.sum())} sin resumen · "
          f"{int(tipo.sum())} por tipo · {dup_oa} duplicados internos · {int(en_prev.sum())} ya en "
          f"Scopus o SciELO → {len(nuevos)} nuevos")

    nuevos['nivel_ancla'] = nuevos.apply(nivel_ancla, axis=1)
    lang = nuevos['Language of Original Document'].fillna('').astype(str)
    nuevos['idioma'] = ['es' if 'Spanish' in l else 'pt' if 'Portuguese' in l else
                        'en' if 'English' in l else 'otro' for l in lang]
    nuevos['v2_paper_id'] = pd.Series(pd.NA, index=nuevos.index, dtype='Int64')
    nuevos['sim_resumen_v2'] = float('nan')
    nuevos['reutiliza_v2'] = False
    nuevos['_ord'] = pd.to_numeric(nuevos['Year'], errors='coerce')
    nuevos = nuevos.sort_values(['_ord', 'Title'], ascending=[False, True]).reset_index(drop=True)
    inicio = int(df['paper_id'].max()) + 1
    nuevos.insert(0, 'paper_id', range(inicio, inicio + len(nuevos)))
    meta = {'n': n_oa, 'sin_abstract': int(sin_abs.sum()), 'tipo': int(tipo.sum()), 'dup': dup_oa,
            'ya_en_scopus_scielo': int(en_prev.sum()), 'nuevos': len(nuevos)}
    return pd.concat([df, nuevos], ignore_index=True), meta


RE_LIBRO = re.compile(r'^\s*(this book|este libro|este livro)\b', re.I)


def _palabras_sin_titulo(resumen: str, titulo: str) -> int:
    r, t = norm_title(resumen), norm_title(titulo)
    if t and t in r:
        r = r.replace(t, ' ', 1)
    return len(r.split())


def rescatar_resumenes(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Agrega los registros sin resumen en su fuente cuyo resumen se encuentra en OpenAlex por DOI."""
    p = DATA / 'v3_resumenes_openalex.json'
    if not p.exists():
        print('[6] Sin data/v3_resumenes_openalex.json: no se rescatan resúmenes')
        return df, {}
    res = json.loads(p.read_text())['resultados']
    cand = []
    for nombre, lector, tipos in [('scopus', leer_scopus, EXCLUDED_TYPES), ('scielo', leer_scielo, EXCLUDED_TYPES),
                                  ('openalex', leer_openalex, TIPOS_EXCLUIDOS_OA)]:
        x = claves(lector())
        x = x[sin_resumen(x) & ~x['Document Type'].str.lower().isin(tipos)].copy()
        cand.append(x)
    cand = pd.concat(cand, ignore_index=True)
    n_cand = len(cand)
    # (b) DOI compartido: por otro candidato o por un registro que ya está en el corpus.
    todos_doi = pd.concat([cand['_doi'], df['_doi']])
    compartido = cand['_doi'].map(todos_doi.value_counts()).fillna(0).gt(1) & \
        ~cand.duplicated('_key', keep=False)          # el mismo trabajo en dos fuentes no cuenta
    con_doi = cand['_doi'].str.startswith('10.')
    txt = cand['_doi'].map(lambda d: res.get(d, {}).get('resumen', '')).fillna('')
    largo_ok = txt.str.strip().str.len().ge(100) & \
        pd.Series([_palabras_sin_titulo(r, t) >= 20 for r, t in zip(txt, cand['Title'])], index=cand.index)
    libro = cand['Document Type'].str.lower().eq('book chapter') & txt.str.match(RE_LIBRO)
    ok = con_doi & largo_ok & ~compartido & ~libro
    resc = cand[ok].copy()
    resc['Abstract'] = txt[ok]
    resc = dedup(resc)
    ya = (resc['_doi'].isin(set(df['_doi'])) & resc['_doi'].str.startswith('10.')) | resc['_key'].isin(set(df['_key']))
    resc = resc[~ya].copy()
    meta = {'sin_resumen_en_su_fuente': n_cand, 'con_doi': int(con_doi.sum()),
            'con_resumen_en_openalex': int((con_doi & txt.str.len().gt(0)).sum()),
            'descartados_corto_o_solo_titulo': int((con_doi & txt.str.len().gt(0) & ~largo_ok).sum()),
            'descartados_doi_compartido': int((con_doi & largo_ok & compartido).sum()),
            'descartados_descripcion_del_libro': int((con_doi & largo_ok & ~compartido & libro).sum()),
            'ya_en_corpus_o_duplicados': int(ok.sum()) - len(resc),
            'rescatados': len(resc), 'por_fuente': resc['_source'].value_counts().to_dict(),
            'tipo': resc['Document Type'].value_counts().to_dict()}
    print(f"[6] Resúmenes rescatados por DOI en OpenAlex: {len(resc)} de {n_cand} sin resumen "
          f"(por fuente: {meta['por_fuente']})")
    resc['nivel_ancla'] = resc.apply(nivel_ancla, axis=1)
    lang = resc['Language of Original Document'].fillna('').astype(str)
    resc['idioma'] = ['es' if 'Spanish' in l else 'pt' if 'Portuguese' in l else
                      'en' if 'English' in l else 'otro' for l in lang]
    resc['v2_paper_id'] = pd.Series(pd.NA, index=resc.index, dtype='Int64')
    resc['sim_resumen_v2'] = float('nan')
    resc['reutiliza_v2'] = False
    resc['resumen_fuente'] = 'openalex_doi'
    resc['_ord'] = pd.to_numeric(resc['Year'], errors='coerce')
    resc = resc.sort_values(['_ord', 'Title'], ascending=[False, True]).reset_index(drop=True)
    inicio = int(df['paper_id'].max()) + 1
    resc.insert(0, 'paper_id', range(inicio, inicio + len(resc)))
    return pd.concat([df, resc], ignore_index=True), meta


def agregar_openalex_idioma(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Agrega los trabajos en español o portugués que OpenAlex etiqueta con otro idioma."""
    p = DATA / 'v3_openalex_idioma_raw.csv'
    if not p.exists():
        print('[7] Sin data/v3_openalex_idioma_raw.csv: no se agregan')
        return df, {}
    oi = pd.read_csv(p, dtype={'Year': str})
    n_id = len(oi)
    det = oi['idioma_detectado'].fillna('')
    oi = oi[det.isin(['es', 'pt'])].copy()
    n_espt = len(oi)
    oi['Language of Original Document'] = oi['idioma_detectado'].map({'es': 'Spanish', 'pt': 'Portuguese'})
    oi['Document Type'] = oi['Document Type'].fillna('').map(tipo_doc)
    oi['_source'], oi['_scielo_id'] = 'openalex', ''
    sin_abs = sin_resumen(oi)
    tipo = oi['Document Type'].str.lower().isin(TIPOS_EXCLUIDOS_OA) & ~sin_abs
    oi = dedup(claves(oi[~(sin_abs | tipo)].copy()))
    ya = (oi['_doi'].str.startswith('10.') & oi['_doi'].isin(set(df['_doi']))) | oi['_key'].isin(set(df['_key']))
    nuevos = oi[~ya].copy()
    meta = {'identificados': n_id, 'en_es_o_pt': n_espt, 'sin_abstract': int(sin_abs.sum()),
            'tipo': int(tipo.sum()), 'ya_en_corpus': int(ya.sum()), 'nuevos': len(nuevos),
            'idioma': nuevos['idioma_detectado'].value_counts().to_dict(),
            'tipo_nuevos': nuevos['Document Type'].value_counts().to_dict()}
    print(f"[7] OpenAlex con otra etiqueta de idioma: {n_id} identificados · {n_espt} en español o portugués · "
          f"{meta['sin_abstract']} sin resumen · {meta['tipo']} por tipo · {meta['ya_en_corpus']} ya en el corpus "
          f"→ {len(nuevos)} nuevos")
    nuevos['nivel_ancla'] = nuevos.apply(nivel_ancla, axis=1)
    nuevos['idioma'] = nuevos['idioma_detectado']
    nuevos['v2_paper_id'] = pd.Series(pd.NA, index=nuevos.index, dtype='Int64')
    nuevos['sim_resumen_v2'] = float('nan')
    nuevos['reutiliza_v2'] = False
    nuevos['resumen_fuente'] = ''
    nuevos['_ord'] = pd.to_numeric(nuevos['Year'], errors='coerce')
    nuevos = nuevos.sort_values(['_ord', 'Title'], ascending=[False, True]).reset_index(drop=True)
    inicio = int(df['paper_id'].max()) + 1
    nuevos.insert(0, 'paper_id', range(inicio, inicio + len(nuevos)))
    return pd.concat([df, nuevos], ignore_index=True), meta


def main():
    sc, se = leer_scopus(), leer_scielo()
    n_sc, n_se = len(sc), len(se)
    print(f"[1] Identificados: Scopus {n_sc} · SciELO {n_se}")

    sc, sc_abs, sc_tipo = excluir(sc)
    se, se_abs, se_tipo = excluir(se)
    print(f"[2] Excluidos por regla: Scopus {sc_abs} sin abstract + {sc_tipo} Erratum/Conference "
          f"review · SciELO {se_abs} sin abstract + {se_tipo} por tipo")

    sc, se = claves(sc), claves(se)
    n0_sc, n0_se = len(sc), len(se)
    sc, se = dedup(sc), dedup(se)
    dup_sc, dup_se = n0_sc - len(sc), n0_se - len(se)
    # Entre fuentes: un registro de SciELO que ya está en Scopus se descarta y el de Scopus
    # queda marcado como hallado en ambas.
    en_sc = se['_doi'].str.startswith('10.') & se['_doi'].isin(set(sc['_doi'])) | se['_key'].isin(set(sc['_key']))
    doi_ambas = set(se.loc[en_sc, '_doi']) - {''}
    key_ambas = set(se.loc[en_sc, '_key'])
    ambas = sc['_doi'].isin(doi_ambas) | sc['_key'].isin(key_ambas)
    sc.loc[ambas, '_source'] = 'scopus+scielo'
    se = se[~en_sc]
    df = pd.concat([sc, se], ignore_index=True)
    print(f"[3] Duplicados: {dup_sc} dentro de Scopus · {dup_se} dentro de SciELO · "
          f"{int(en_sc.sum())} de SciELO ya en Scopus → {len(df)}")

    df['nivel_ancla'] = df.apply(nivel_ancla, axis=1)
    lang = df['Language of Original Document'].fillna('').astype(str)
    df['idioma'] = ['es' if 'Spanish' in l else 'pt' if 'Portuguese' in l else
                    'en' if 'English' in l else 'otro' for l in lang]
    df['v2_paper_id'] = enlazar_v2(df)
    df['sim_resumen_v2'] = similitud_v2(df).round(3)
    df['reutiliza_v2'] = df['sim_resumen_v2'].ge(SIMILITUD_MIN)
    print(f"[4] Nivel del ancla: {df['nivel_ancla'].value_counts().to_dict()}")
    print(f"    Idioma: {df['idioma'].value_counts().to_dict()}")
    print(f"    Fuente: {df['_source'].value_counts().to_dict()}")
    print(f"    Enlazados con la v2: {int(df['v2_paper_id'].notna().sum())} · reutilizan su "
          f"evaluación: {int(df['reutiliza_v2'].sum())} · a evaluar en la v3: "
          f"{int((~df['reutiliza_v2']).sum())}")

    df['_ord'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.sort_values(['_ord', 'Title'], ascending=[False, True]).reset_index(drop=True)
    df.insert(0, 'paper_id', range(len(df)))
    df, oa = agregar_openalex(df)
    df, rescate = rescatar_resumenes(df)
    df, oidioma = agregar_openalex_idioma(df)
    if 'idioma_openalex' not in df:
        df['idioma_openalex'] = ''
    df['idioma_openalex'] = df['idioma_openalex'].fillna('')
    if 'resumen_fuente' not in df:
        df['resumen_fuente'] = ''
    df['resumen_fuente'] = df['resumen_fuente'].fillna('')
    out_cols = (['paper_id'] + PIPELINE_COLS + EXTRA_COLS
                + ['nivel_ancla', 'idioma', '_source', '_doi', '_scielo_id', 'v2_paper_id',
                   'sim_resumen_v2', 'reutiliza_v2', 'OpenAlex ID', 'resumen_fuente', 'idioma_openalex'])
    df[out_cols].to_csv(DATA / 'v3_corpus_consolidated.csv', index=False)

    meta = {
        # Los de OpenAlex con otra etiqueta de idioma cuentan como identificados solo si están en español
        # o portugués (equivale al filtro de idioma de la consulta principal).
        'identificados': {'scopus': n_sc, 'scielo': n_se, 'openalex': oa['n'],
                          'openalex_otra_etiqueta': oidioma.get('en_es_o_pt', 0)},
        'excluidos_regla': {'scopus': {'sin_abstract': sc_abs, 'erratum_o_conference_review': sc_tipo},
                            'scielo': {'sin_abstract': se_abs, 'tipo': se_tipo},
                            'openalex': {'sin_abstract': oa['sin_abstract'], 'tipo': oa['tipo']},
                            'openalex_otra_etiqueta': {'sin_abstract': oidioma.get('sin_abstract', 0),
                                                       'tipo': oidioma.get('tipo', 0)}},
        'duplicados': {'dentro_scopus': dup_sc, 'dentro_scielo': dup_se,
                       'scielo_ya_en_scopus': int(en_sc.sum()), 'dentro_openalex': oa['dup'],
                       'openalex_ya_en_scopus_scielo': oa['ya_en_scopus_scielo'],
                       'openalex_otra_etiqueta_ya_en_corpus': oidioma.get('ya_en_corpus', 0)},
        'a_cribado': len(df),
        'fuente': df['_source'].value_counts().to_dict(),
        'nivel_ancla': df['nivel_ancla'].value_counts().to_dict(),
        'idioma': df['idioma'].value_counts().to_dict(),
        'enlazados_v2': int(df['v2_paper_id'].notna().sum()),
        'reutilizan_evaluacion_v2': int(df['reutiliza_v2'].sum()),
        'evaluados_en_v3': int((~df['reutiliza_v2']).sum()),
        'openalex_nuevos': oa['nuevos'] + oidioma.get('nuevos', 0),
        'tipo_openalex_nuevos': df.loc[(df['_source'] == 'openalex') & df['resumen_fuente'].eq('')
                                       & df['idioma_openalex'].eq(''),
                                       'Document Type'].value_counts().to_dict(),
        'rescate_resumen': rescate,
        'openalex_otra_etiqueta_idioma': oidioma,
    }
    (DATA / 'v3_prisma_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\n[OK] data/v3_corpus_consolidated.csv ({len(df)}) + data/v3_prisma_meta.json")


if __name__ == '__main__':
    main()
