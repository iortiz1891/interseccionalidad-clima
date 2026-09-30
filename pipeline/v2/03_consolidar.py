#!/usr/bin/env python3
"""
03_consolidar.py — v2: une y valida las salidas de cribado + RSI.

Lee work/v2_salidas/lote_*.jsonl, valida cada línea contra el esquema de
prompts/v2_cribado_rsi.md y calcula el total de la RSI con la misma fórmula de
la v1 (pipeline/02_scoring_rsi.py::compute_total).

Salidas:
  data/v2_cribado.csv            todos los registros con su decisión de cribado
  data/v2_bowleg_results.csv     puntajes RSI (mismo esquema que la v1 + codificación)
  data/v2_reasoning_results.csv  razonamiento por registro
  data/v2_corpus_scored.csv      corpus elegible + puntajes + categoría
  data/v2_prisma_meta.json       se completa con el cribado y las categorías
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path
import pandas as pd

DATA = Path("data")
SALIDAS = Path("work/v2_salidas")

sys.path.insert(0, str(Path(__file__).parent))
from validar_lote import check  # noqa: E402

_spec = importlib.util.spec_from_file_location('scoring_v1', 'pipeline/02_scoring_rsi.py')
_scoring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scoring)
compute_total = _scoring.compute_total


def categoria(total: float) -> str:
    if total >= 3.5: return 'sustantivo_fuerte'
    if total >= 2.5: return 'sustantivo'
    if total >= 1.5: return 'parcial'
    if total > 0:    return 'nominal_debil'
    return 'mencion_sin_aplicacion'


def main():
    recs, errores = [], []
    for f in sorted(SALIDAS.glob('lote_*.jsonl')):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if not line.strip():
                continue
            d = json.loads(line)
            for e in check(d):
                errores.append(f'{f.name}:{n} paper_id {d.get("paper_id")}: {e}')
            recs.append(d)
    if errores:
        sys.exit('ERRORES DE ESQUEMA:\n' + '\n'.join(errores[:40]))

    corpus = pd.read_csv(DATA / 'v2_corpus_consolidated.csv')
    ids = [r['paper_id'] for r in recs]
    if '--parcial' in sys.argv:          # solo para probar el pipeline con lotes incompletos
        corpus = corpus[corpus['paper_id'].isin(ids)].copy()
    faltan = sorted(set(corpus['paper_id']) - set(ids))
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if faltan or dups:
        sys.exit(f'Faltan {len(faltan)} registros ({faltan[:10]}) · duplicados {dups[:10]}')
    print(f"[1] {len(recs)} registros válidos de {len(list(SALIDAS.glob('lote_*.jsonl')))} lotes")

    # ── Cribado ──
    cr = pd.DataFrame([{k: r.get(k) for k in
                        ['paper_id', 'elig_interseccional', 'elig_clima', 'elegible', 'motivo_exclusion']}
                       for r in recs])
    cr = corpus[['paper_id', 'Title', 'Year', 'Document Type', 'idioma', 'nivel_ancla']].merge(cr, on='paper_id')
    cr.to_csv(DATA / 'v2_cribado.csv', index=False)
    print(f"[2] Elegibles: {int(cr['elegible'].sum())} / {len(cr)}")

    # ── RSI (solo elegibles) ──
    rows, razon = [], []
    for r in recs:
        razon.append({'paper_id': r['paper_id'], 'razonamiento': r.get('razonamiento', '')})
        if not r['elegible']:
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
        })
    res = pd.DataFrame(rows)
    res.to_csv(DATA / 'v2_bowleg_results.csv', index=False)
    pd.DataFrame(razon).to_csv(DATA / 'v2_reasoning_results.csv', index=False)

    scored = corpus.merge(res, on='paper_id', how='inner')
    scored['categoria_bowleg'] = scored['bowleg_total'].apply(categoria)
    scored.to_csv(DATA / 'v2_corpus_scored.csv', index=False)
    print(f"[3] Corpus puntuado: {len(scored)} · gate {int(scored['gate_pass'].sum())} · "
          f"RSI 0: {100 * (scored['bowleg_total'] == 0).mean():.1f}%")

    # ── PRISMA ──
    meta = json.loads((DATA / 'v2_prisma_meta.json').read_text())
    no_int = ~cr['elig_interseccional']
    no_cli = ~cr['elig_clima']
    meta['cribado'] = {
        'excluidos': int((~cr['elegible']).sum()),
        'solo_no_interseccional': int((no_int & ~no_cli).sum()),
        'solo_no_climatico': int((no_cli & ~no_int).sum()),
        'ambos': int((no_int & no_cli).sum()),
        'elegibles': int(cr['elegible'].sum()),
    }
    meta['rsi'] = {
        'gate_pass': int(scored['gate_pass'].sum()),
        'categorias_n': scored['categoria_bowleg'].value_counts().to_dict(),
        'categorias_pct': (scored['categoria_bowleg'].value_counts(normalize=True) * 100).round(1).to_dict(),
        'modelo': 'claude-opus-5-5 (Claude Code) · prompts/v2_cribado_rsi.md',
    }
    (DATA / 'v2_prisma_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print("[OK] data/v2_cribado.csv · v2_bowleg_results.csv · v2_reasoning_results.csv · "
          "v2_corpus_scored.csv · v2_prisma_meta.json")


if __name__ == '__main__':
    main()
