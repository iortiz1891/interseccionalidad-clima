#!/usr/bin/env python3
"""
03_consolidar.py — v4: une la evaluación de la v3 con la de los registros nuevos de OpenAlex.

  · reutiliza_v3 = True  → cribado, codificación, RSI y razonamiento de data/v3_cribado.csv,
    data/v3_bowleg_results.csv y data/v3_reasoning_results.csv (mismo paper_id). Conservan su
    origen_evaluacion (v2 o v3).
  · reutiliza_v3 = False → work/v4_salidas/lote_*.jsonl (prompts/v3_cribado_rsi.md),
    validados con pipeline/v2/validar_lote.py; origen_evaluacion = v4.

Salidas: data/v4_cribado.csv · v4_bowleg_results.csv · v4_reasoning_results.csv ·
         v4_corpus_scored.csv · v4_prisma_meta.json (se completa)
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path
import pandas as pd

DATA = Path("data")
SALIDAS = Path("work/v4_salidas")

sys.path.insert(0, str(Path(__file__).parent.parent / 'v2'))
from validar_lote import check  # noqa: E402

_spec = importlib.util.spec_from_file_location('scoring_v1', 'pipeline/02_scoring_rsi.py')
_scoring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scoring)
compute_total = _scoring.compute_total
categoria = _scoring.categoria


def fila_res(r: dict) -> dict:
    return {
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
        'tipo_estudio': r['tipo_estudio'], 'amenaza': '; '.join(r['amenaza']),
        'lugar_estudio': '; '.join(r['lugar_estudio']), 'origen_evaluacion': 'v4',
    }


def main():
    corpus = pd.read_csv(DATA / 'v4_corpus_consolidated.csv')
    corpus['reutiliza_v3'] = corpus['reutiliza_v3'].astype(bool)
    viejos = set(corpus.loc[corpus['reutiliza_v3'], 'paper_id'])
    nuevos = set(corpus.loc[~corpus['reutiliza_v3'], 'paper_id'])

    cr3 = pd.read_csv(DATA / 'v3_cribado.csv')
    res3 = pd.read_csv(DATA / 'v3_bowleg_results.csv')
    raz3 = pd.read_csv(DATA / 'v3_reasoning_results.csv')
    if set(cr3['paper_id']) != viejos:
        sys.exit('El corpus v4 no contiene exactamente los registros de la v3.')

    recs, errores = [], []
    for f in sorted(SALIDAS.glob('lote_*.jsonl')):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if line.strip():
                d = json.loads(line)
                errores += [f'{f.name}:{n} paper_id {d.get("paper_id")}: {e}' for e in check(d)]
                recs.append(d)
    if errores:
        sys.exit('ERRORES DE ESQUEMA:\n' + '\n'.join(errores[:40]))
    ids = [r['paper_id'] for r in recs]
    if '--parcial' not in sys.argv:
        faltan, sobran = sorted(nuevos - set(ids)), sorted(set(ids) - nuevos)
        dups = sorted({i for i in ids if ids.count(i) > 1})
        if faltan or sobran or dups:
            sys.exit(f'Faltan {len(faltan)} ({faltan[:10]}) · sobran {sobran[:10]} · duplicados {dups[:10]}')
    else:
        corpus = corpus[corpus['reutiliza_v3'] | corpus['paper_id'].isin(ids)].copy()
    print(f"[1] {len(cr3)} evaluaciones de la v3 + {len(recs)} nuevas de OpenAlex")

    # ── Cribado ──
    base = corpus[['paper_id', 'Title', 'Year', 'Document Type', 'idioma', 'nivel_ancla', '_source']]
    cr_old = base.merge(cr3[['paper_id', 'elig_interseccional', 'elig_clima', 'elegible', 'motivo_exclusion',
                             'confidence', 'origen_evaluacion', 'retractado']], on='paper_id')
    cr_new = base.merge(pd.DataFrame([{k: r.get(k) for k in ['paper_id', 'elig_interseccional', 'elig_clima',
                                                              'elegible', 'motivo_exclusion', 'confidence']}
                                      for r in recs]), on='paper_id')
    cr_new['origen_evaluacion'] = 'v4'
    cr_new['retractado'] = cr_new['Title'].fillna('').str.match(r'\s*RETRACTED', case=False)
    cr_new.loc[cr_new['retractado'], 'elegible'] = False
    cr_new.loc[cr_new['retractado'], 'motivo_exclusion'] = 'Trabajo retractado (excluido por regla).'
    cr = pd.concat([cr_old, cr_new], ignore_index=True).sort_values('paper_id')
    cr.to_csv(DATA / 'v4_cribado.csv', index=False)
    print(f"[2] Elegibles: {int(cr['elegible'].sum())} / {len(cr)} "
          f"(nuevos: {int(cr_new['elegible'].sum())} / {len(cr_new)})")

    # ── RSI ──
    retract = set(cr_new.loc[cr_new['retractado'], 'paper_id'])
    res_new = pd.DataFrame([fila_res(r) for r in recs if r['elegible'] and r['paper_id'] not in retract])
    res = pd.concat([res3, res_new], ignore_index=True).sort_values('paper_id')
    res.to_csv(DATA / 'v4_bowleg_results.csv', index=False)
    raz_new = pd.DataFrame([{'paper_id': r['paper_id'], 'razonamiento': r.get('razonamiento', ''),
                             'origen_evaluacion': 'v4'} for r in recs])
    pd.concat([raz3, raz_new], ignore_index=True).sort_values('paper_id').to_csv(
        DATA / 'v4_reasoning_results.csv', index=False)

    scored = corpus.merge(res, on='paper_id', how='inner')
    scored['categoria_bowleg'] = scored['bowleg_total'].apply(categoria)
    scored['_tag'] = 'v4_' + scored['idioma']
    scored.to_csv(DATA / 'v4_corpus_scored.csv', index=False)
    print(f"[3] Corpus puntuado: {len(scored)} · gate {int(scored['gate_pass'].astype(str).str.lower().eq('true').sum())} · "
          f"RSI 0: {100 * (scored['bowleg_total'] == 0).mean():.1f}%")

    meta = json.loads((DATA / 'v4_prisma_meta.json').read_text())
    elig = cr['elegible'].astype(bool)
    no_int = ~cr['elig_interseccional'].astype(bool) & ~cr['retractado'].astype(bool)
    no_cli = ~cr['elig_clima'].astype(bool) & ~cr['retractado'].astype(bool)
    meta['cribado'] = {
        'excluidos': int((~elig).sum()), 'retractados': int(cr['retractado'].astype(bool).sum()),
        'solo_no_interseccional': int((no_int & ~no_cli).sum()),
        'solo_no_climatico': int((no_cli & ~no_int).sum()), 'ambos': int((no_int & no_cli).sum()),
        'elegibles': int(elig.sum()),
        'elegibles_por_origen': cr[elig]['origen_evaluacion'].value_counts().to_dict(),
    }
    meta['rsi'] = {
        'gate_pass': int(scored['gate_pass'].astype(str).str.lower().eq('true').sum()),
        'categorias_n': scored['categoria_bowleg'].value_counts().to_dict(),
        'categorias_pct': (scored['categoria_bowleg'].value_counts(normalize=True) * 100).round(1).to_dict(),
        'modelo': ('claude-opus-5-5 (Claude Code) · evaluación de la v3 (prompts v2/v3) + '
                   'prompts/v3_cribado_rsi.md para los registros de OpenAlex'),
    }
    (DATA / 'v4_prisma_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print("[OK] data/v4_cribado.csv · v4_bowleg_results.csv · v4_reasoning_results.csv · "
          "v4_corpus_scored.csv · v4_prisma_meta.json")


if __name__ == '__main__':
    main()
