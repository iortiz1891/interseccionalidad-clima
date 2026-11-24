#!/usr/bin/env python3
"""
03_consolidar.py — v3: une la evaluación reutilizada de la v2 con la nueva de la v3.

Para cada registro de data/v3_corpus_consolidated.csv:
  · reutiliza_v2 = True  → cribado, codificación, RSI y razonamiento se toman de
    data/v2_cribado.csv, data/v2_bowleg_results.csv y data/v2_reasoning_results.csv
    (ya incluyen la reevaluación del gate de la v2).
  · reutiliza_v2 = False → se leen de work/v3_salidas/lote_*.jsonl (Scopus y SciELO) y
    work/v3_salidas/oa_lote_*.jsonl (OpenAlex) y work/v3_salidas/rs_lote_*.jsonl (resumen
    rescatado por DOI en OpenAlex), evaluados con prompts/v3_cribado_rsi.md y
    validados contra el esquema de pipeline/v2/validar_lote.py.

El total de la RSI se recalcula siempre con pipeline/02_scoring_rsi.py::compute_total.
La columna origen_evaluacion (v2 | v3) dice de dónde viene cada evaluación.

Salidas:
  data/v3_cribado.csv            todos los registros con su decisión de cribado
  data/v3_bowleg_results.csv     puntajes RSI (mismo esquema que la v2)
  data/v3_reasoning_results.csv  razonamiento por registro
  data/v3_corpus_scored.csv      corpus elegible + puntajes + categoría
  data/v3_prisma_meta.json       se completa con el cribado y las categorías
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path
import pandas as pd

DATA = Path("data")
SALIDAS = Path("work/v3_salidas")

sys.path.insert(0, str(Path(__file__).parent.parent / 'v2'))
from validar_lote import check  # noqa: E402

_spec = importlib.util.spec_from_file_location('scoring_v1', 'pipeline/02_scoring_rsi.py')
_scoring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scoring)
compute_total = _scoring.compute_total
categoria = _scoring.categoria

CRIT = ['I', 'II', 'III', 'IV', 'V', 'VI']


def _txt(v) -> str:
    return '' if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)


def _lista(v) -> list[str]:
    return [x.strip() for x in _txt(v).split(';') if x.strip()]


def registros_v2(corpus: pd.DataFrame) -> list[dict]:
    """Reconstruye, en el esquema del prompt, la evaluación v2 de los registros reutilizados."""
    cr = pd.read_csv(DATA / 'v2_cribado.csv').set_index('paper_id')
    res = pd.read_csv(DATA / 'v2_bowleg_results.csv').set_index('paper_id')
    raz = pd.read_csv(DATA / 'v2_reasoning_results.csv').set_index('paper_id')['razonamiento']
    out = []
    for _, r in corpus[corpus['reutiliza_v2']].iterrows():
        p2 = int(r['v2_paper_id'])
        c = cr.loc[p2]
        d = {'paper_id': int(r['paper_id']), 'v2_paper_id': p2,
             'elig_interseccional': bool(c['elig_interseccional']), 'elig_clima': bool(c['elig_clima']),
             'elegible': bool(c['elegible']), 'motivo_exclusion': c['motivo_exclusion'] if not c['elegible'] else None,
             'confidence': c['confidence'], 'razonamiento': _txt(raz.get(p2))}
        if c['elegible']:
            s = res.loc[p2]
            for k in CRIT:
                col = f'bowleg_{k}' if k in ('I', 'II', 'III', 'IV') else f'rsi_{k}'
                d[f'rsi_{k}'] = float(s[col])
                d[f'rsi_{k}_ev'] = _txt(s[f'{col}_evidence'])
            d.update({'gate_pass': bool(s['gate_pass']), 'gate_evidence': _txt(s['gate_evidence']),
                      'integracion': float(s['integracion']), 'integracion_nota': _txt(s['integracion_nota']),
                      'confidence': s['confidence'], 'tipo_estudio': s['tipo_estudio'],
                      'amenaza': _lista(s['amenaza']), 'lugar_estudio': _lista(s['lugar_estudio'])})
            if compute_total(d) != float(s['bowleg_total']):
                sys.exit(f'v2 paper_id {p2}: el total recalculado no coincide con el de la v2')
        d['origen_evaluacion'] = 'v2'
        out.append(d)
    return out


def registros_v3() -> list[dict]:
    recs, errores = [], []
    for f in (sorted(SALIDAS.glob('lote_*.jsonl')) + sorted(SALIDAS.glob('oa_lote_*.jsonl'))
              + sorted(SALIDAS.glob('rs_lote_*.jsonl'))):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if not line.strip():
                continue
            d = json.loads(line)
            for e in check(d):
                errores.append(f'{f.name}:{n} paper_id {d.get("paper_id")}: {e}')
            d['origen_evaluacion'] = 'v3'
            recs.append(d)
    if errores:
        sys.exit('ERRORES DE ESQUEMA:\n' + '\n'.join(errores[:40]))
    return recs


def main():
    corpus = pd.read_csv(DATA / 'v3_corpus_consolidated.csv')
    corpus['reutiliza_v2'] = corpus['reutiliza_v2'].astype(bool)
    rv2, rv3 = registros_v2(corpus), registros_v3()
    recs = rv2 + rv3
    ids = [r['paper_id'] for r in recs]
    nuevos = set(corpus.loc[~corpus['reutiliza_v2'], 'paper_id'])
    faltan = sorted(set(corpus['paper_id']) - set(ids))
    sobran = sorted({r['paper_id'] for r in rv3} - nuevos)
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if '--parcial' in sys.argv:          # solo para probar el pipeline con lotes incompletos
        corpus = corpus[corpus['paper_id'].isin(ids)].copy()
        faltan = []
    if faltan or sobran or dups:
        sys.exit(f'Faltan {len(faltan)} ({faltan[:10]}) · fuera de los lotes {sobran[:10]} · '
                 f'duplicados {dups[:10]}')
    print(f"[1] {len(rv2)} evaluaciones reutilizadas de la v2 + {len(rv3)} nuevas de la v3")

    # ── Cribado ──
    cr = pd.DataFrame([{k: r.get(k) for k in
                        ['paper_id', 'elig_interseccional', 'elig_clima', 'elegible', 'motivo_exclusion',
                         'confidence', 'origen_evaluacion']}
                       for r in recs])
    cr = corpus[['paper_id', 'Title', 'Year', 'Document Type', 'idioma', 'nivel_ancla', '_source']].merge(
        cr, on='paper_id')
    retract = cr['Title'].fillna('').str.match(r'\s*RETRACTED', case=False)
    cr['retractado'] = retract
    cr.loc[retract, 'elegible'] = False
    cr.loc[retract, 'motivo_exclusion'] = 'Trabajo retractado (excluido por regla).'
    retract_ids = set(cr.loc[retract, 'paper_id'])
    cr = cr.sort_values('paper_id')
    cr.to_csv(DATA / 'v3_cribado.csv', index=False)
    print(f"[2] Elegibles: {int(cr['elegible'].sum())} / {len(cr)}")

    # ── RSI (solo elegibles) ──
    rows, razon = [], []
    for r in recs:
        razon.append({'paper_id': r['paper_id'], 'razonamiento': r.get('razonamiento', ''),
                      'origen_evaluacion': r['origen_evaluacion']})
        if not r['elegible'] or r['paper_id'] in retract_ids:
            continue
        rows.append({
            'paper_id': r['paper_id'],
            'bowleg_I': r['rsi_I'], 'bowleg_I_evidence': r.get('rsi_I_ev', ''),
            'bowleg_II': r['rsi_II'], 'bowleg_II_evidence': r.get('rsi_II_ev', ''),
            'bowleg_III': r['rsi_III'], 'bowleg_III_evidence': r.get('rsi_III_ev', ''),
            'bowleg_IV': r['rsi_IV'], 'bowleg_IV_evidence': r.get('rsi_IV_ev', ''),
            'bowleg_total': compute_total(r),
            'confidence': r.get('confidence', 'medium'), 'confidence_note': '',
            'rsi_V': r['rsi_V'], 'rsi_V_evidence': r.get('rsi_V_ev', ''),
            'rsi_VI': r['rsi_VI'], 'rsi_VI_evidence': r.get('rsi_VI_ev', ''),
            'gate_pass': r['gate_pass'], 'gate_evidence': r.get('gate_evidence', ''),
            'integracion': r['integracion'], 'integracion_nota': r.get('integracion_nota', ''),
            'tipo_estudio': r['tipo_estudio'],
            'amenaza': '; '.join(r['amenaza']),
            'lugar_estudio': '; '.join(r['lugar_estudio']),
            'origen_evaluacion': r['origen_evaluacion'],
        })
    res = pd.DataFrame(rows).sort_values('paper_id')
    res.to_csv(DATA / 'v3_bowleg_results.csv', index=False)
    pd.DataFrame(razon).sort_values('paper_id').to_csv(DATA / 'v3_reasoning_results.csv', index=False)

    scored = corpus.merge(res, on='paper_id', how='inner')
    scored['categoria_bowleg'] = scored['bowleg_total'].apply(categoria)
    scored['_tag'] = 'v3_' + scored['idioma']      # equivalente al _tag de la v1
    scored.to_csv(DATA / 'v3_corpus_scored.csv', index=False)
    print(f"[3] Corpus puntuado: {len(scored)} · gate {int(scored['gate_pass'].sum())} · "
          f"RSI 0: {100 * (scored['bowleg_total'] == 0).mean():.1f}%")

    # ── PRISMA ──
    meta = json.loads((DATA / 'v3_prisma_meta.json').read_text())
    no_int = ~cr['elig_interseccional'].astype(bool) & ~cr['retractado']
    no_cli = ~cr['elig_clima'].astype(bool) & ~cr['retractado']
    meta['cribado'] = {
        'excluidos': int((~cr['elegible'].astype(bool)).sum()),
        'retractados': int(cr['retractado'].sum()),
        'solo_no_interseccional': int((no_int & ~no_cli).sum()),
        'solo_no_climatico': int((no_cli & ~no_int).sum()),
        'ambos': int((no_int & no_cli).sum()),
        'elegibles': int(cr['elegible'].sum()),
        'elegibles_por_origen': cr[cr['elegible'].astype(bool)]['origen_evaluacion'].value_counts().to_dict(),
    }
    meta['rsi'] = {
        'gate_pass': int(scored['gate_pass'].sum()),
        'categorias_n': scored['categoria_bowleg'].value_counts().to_dict(),
        'categorias_pct': (scored['categoria_bowleg'].value_counts(normalize=True) * 100).round(1).to_dict(),
        'modelo': ('claude-opus-5-5 (Claude Code) · prompts/v2_cribado_rsi.md (reutilizados de la v2) '
                   '+ prompts/v3_cribado_rsi.md (nuevos de Scopus, SciELO y OpenAlex)'),
    }
    (DATA / 'v3_prisma_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print("[OK] data/v3_cribado.csv · v3_bowleg_results.csv · v3_reasoning_results.csv · "
          "v3_corpus_scored.csv · v3_prisma_meta.json")


if __name__ == '__main__':
    main()
