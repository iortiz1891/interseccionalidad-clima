#!/usr/bin/env python3
"""
validar_lote.py — Valida la salida de un lote de cribado + RSI (v2).

Uso:
    python3 pipeline/v2/validar_lote.py <salida.jsonl> <entrada.jsonl>

Comprueba que cada paper_id de la entrada aparezca exactamente una vez en la
salida y que cada línea cumpla el esquema de prompts/v2_cribado_rsi.md.
Sale con código 1 si hay errores (y los lista).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

CRITS = ['rsi_I', 'rsi_II', 'rsi_III', 'rsi_IV', 'rsi_V', 'rsi_VI']
LEVELS = {0, 0.5, 1}
TIPOS = {'empirico_cuantitativo', 'empirico_cualitativo', 'empirico_mixto',
         'conceptual_teorico', 'revision', 'otro'}
AMENAZAS = {'cambio_climatico_general', 'ciclon_huracan_tormenta', 'inundacion', 'sequia',
            'calor_extremo', 'incendio_forestal', 'nivel_mar_costas', 'glaciares_criosfera',
            'desastres_multiples', 'mitigacion_transicion', 'otro'}
CONF = {'high', 'medium', 'low'}


def check(d: dict) -> list[str]:
    e = []
    for k in ('elig_interseccional', 'elig_clima', 'elegible'):
        if not isinstance(d.get(k), bool):
            e.append(f'{k} no es booleano')
    if isinstance(d.get('elig_interseccional'), bool) and isinstance(d.get('elig_clima'), bool):
        if d.get('elegible') != (d['elig_interseccional'] and d['elig_clima']):
            e.append('elegible != elig_interseccional AND elig_clima')
    if not isinstance(d.get('razonamiento'), str) or not d['razonamiento'].strip():
        e.append('falta razonamiento')
    if d.get('confidence') not in CONF:
        e.append('confidence inválido')

    if d.get('elegible') is False:
        if not d.get('motivo_exclusion'):
            e.append('no elegible sin motivo_exclusion')
        for k in CRITS + ['gate_pass', 'integracion', 'tipo_estudio']:
            if d.get(k) is not None:
                e.append(f'no elegible pero {k} no es null')
        return e

    if d.get('tipo_estudio') not in TIPOS:
        e.append(f"tipo_estudio inválido: {d.get('tipo_estudio')}")
    am = d.get('amenaza')
    if not isinstance(am, list) or not am or not set(am) <= AMENAZAS:
        e.append(f'amenaza inválida: {am}')
    if not isinstance(d.get('lugar_estudio'), list) or not d['lugar_estudio']:
        e.append('lugar_estudio debe ser lista no vacía')
    if not isinstance(d.get('gate_pass'), bool):
        e.append('gate_pass no es booleano')
    for k in CRITS + ['integracion']:
        if d.get(k) not in LEVELS:
            e.append(f'{k} fuera de 0/0.5/1: {d.get(k)}')
    if d.get('gate_pass') is False:
        if any(d.get(k) not in (0, None) for k in CRITS + ['integracion']):
            e.append('gate_pass=false con criterios distintos de 0')
    if not d.get('gate_evidence'):
        e.append('falta gate_evidence')
    return e


def main(out_path: str, in_path: str) -> int:
    ids_in = [json.loads(l)['paper_id'] for l in Path(in_path).read_text().splitlines() if l.strip()]
    seen, errors = {}, []
    for n, line in enumerate(Path(out_path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError as ex:
            errors.append(f'línea {n}: JSON inválido ({ex})')
            continue
        pid = d.get('paper_id')
        seen[pid] = seen.get(pid, 0) + 1
        for msg in check(d):
            errors.append(f'paper_id {pid}: {msg}')
    faltan = [i for i in ids_in if i not in seen]
    extra = [i for i in seen if i not in set(ids_in)]
    dup = [i for i, c in seen.items() if c > 1]
    if faltan: errors.append(f'faltan {len(faltan)} paper_id: {faltan[:20]}')
    if extra: errors.append(f'paper_id que no están en la entrada: {extra[:20]}')
    if dup: errors.append(f'paper_id duplicados: {dup[:20]}')
    if errors:
        print(f'ERRORES ({len(errors)}):')
        print('\n'.join(errors[:60]))
        return 1
    print(f'OK: {len(seen)} registros válidos')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
