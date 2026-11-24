#!/usr/bin/env python3
"""
recalcular_totales.py — recalcula el total de la RSI y su categoría a partir de los
criterios ya guardados, sin volver a llamar al modelo.

Se usa cuando cambia la fórmula de pipeline/02_scoring_rsi.py::compute_total. En
noviembre de 2026 la fórmula dejó de usar round() de Python, que redondeaba los empates
al número par (0.5 → 0, 2.5 → 2, pero 1.5 → 2), y pasó a redondear los empates hacia
arriba, con un mínimo de 0.5 para todo trabajo que pasa el gate.

Actualiza, para la v1 y la v2:
  data/{v}_bowleg_results.csv   bowleg_total
  data/{v}_corpus_scored.csv    bowleg_total y categoria_bowleg
  data/daniel_prisma_meta.json  categorias_pct (v1)
  data/v2_prisma_meta.json      bloque rsi (v2)

Los CSV se leen y escriben como texto para no tocar ninguna otra columna. Después hay
que regenerar los pasos 05–12 de la v1 y 05–13 de la v2 (ver README).

Uso:
    python3 pipeline/recalcular_totales.py
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import pandas as pd

DATA = Path("data")

_spec = importlib.util.spec_from_file_location('scoring', 'pipeline/02_scoring_rsi.py')
_scoring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scoring)
compute_total = _scoring.compute_total
categoria = _scoring.categoria

CRIT = {'rsi_I': 'bowleg_I', 'rsi_II': 'bowleg_II', 'rsi_III': 'bowleg_III',
        'rsi_IV': 'bowleg_IV', 'rsi_V': 'rsi_V', 'rsi_VI': 'rsi_VI'}


def _leer(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _num(s: str) -> float:
    return float(s) if s.strip() else 0.0


def recalcular(v: str) -> pd.Series:
    res_path = DATA / f'{v}_bowleg_results.csv'
    res = _leer(res_path)
    nuevos = []
    for _, r in res.iterrows():
        d = {k: _num(r[c]) for k, c in CRIT.items()}
        d['gate_pass'] = r['gate_pass']
        d['integracion'] = _num(r['integracion'])
        nuevos.append(compute_total(d))
    antes = res['bowleg_total'].astype(float)
    total = pd.Series(nuevos, index=res.index)
    res['bowleg_total'] = total.map(repr)
    res.to_csv(res_path, index=False)

    cambia = antes != total
    print(f"[{v}] {int(cambia.sum())} de {len(res)} totales cambian")
    trans = (pd.DataFrame({'antes': antes[cambia], 'despues': total[cambia]})
             .value_counts().sort_index())
    for (a, b), n in trans.items():
        print(f"      {a} → {b}: {n}")

    por_id = dict(zip(res['paper_id'], total))
    sc_path = DATA / f'{v}_corpus_scored.csv'
    sc = _leer(sc_path)
    faltan = set(sc['paper_id']) - set(por_id)
    if faltan:
        raise SystemExit(f'{sc_path}: {len(faltan)} paper_id sin resultado RSI')
    cat_antes = sc['categoria_bowleg'].copy()
    t = sc['paper_id'].map(por_id)
    sc['bowleg_total'] = t.map(repr)
    sc['categoria_bowleg'] = t.map(categoria)
    sc.to_csv(sc_path, index=False)
    print(f"      categorías que cambian: {int((cat_antes != sc['categoria_bowleg']).sum())}")
    return sc['categoria_bowleg']


def main():
    cats_v1 = recalcular('v1')
    meta_path = DATA / 'daniel_prisma_meta.json'
    meta = json.loads(meta_path.read_text())
    meta['categorias_pct'] = (cats_v1.value_counts(normalize=True) * 100).round(1).to_dict()
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    cats_v2 = recalcular('v2')
    meta_path = DATA / 'v2_prisma_meta.json'
    meta = json.loads(meta_path.read_text())
    res = _leer(DATA / 'v2_bowleg_results.csv')
    meta['rsi']['gate_pass'] = int(res['gate_pass'].str.lower().eq('true').sum())
    meta['rsi']['categorias_n'] = cats_v2.value_counts().to_dict()
    meta['rsi']['categorias_pct'] = (cats_v2.value_counts(normalize=True) * 100).round(1).to_dict()
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    for v, c in (('v1', cats_v1), ('v2', cats_v2)):
        pct = (c.value_counts(normalize=True) * 100).round(1)
        print(f"[{v}] " + ' · '.join(f"{k} {pct.get(k, 0)}%" for k in
              ['mencion_sin_aplicacion', 'nominal_debil', 'parcial', 'sustantivo', 'sustantivo_fuerte']))
    print("[OK] Ahora regenera los pasos 05–12 (v1) y 05–13 (v2).")


if __name__ == '__main__':
    main()
