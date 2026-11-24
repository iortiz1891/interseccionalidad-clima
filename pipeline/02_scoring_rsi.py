#!/usr/bin/env python3
"""
02_scoring_rsi.py — Scoring RSI v3 vía OpenAI Batch API (gpt-4.1).

Rúbrica v3: GATE + 6 criterios (I-VI) + integración. El total se computa aquí
(no el LLM) y se normaliza a 0-4 para mantener compatibilidad con el pipeline:

  if not gate_pass: total = 0
  else:
    core = sum(rsi_I..rsi_VI)              # 0-6
    norm = core / 6 * 4                    # 0-4
    factor = 0.5 + 0.5*integracion         # 0.5 / 0.75 / 1.0
    total = floor(norm * factor * 2 + 0.5) / 2   # a múltiplos de 0.5, empates hacia arriba
    total = max(total, 0.5)                # pasar el gate nunca deja el total en 0

Hasta noviembre de 2026 el total usaba round() de Python, que redondea los empates
al número par (0.5 → 0, 2.5 → 2, pero 1.5 → 2). Eso bajaba de categoría a parte de
los trabajos de forma arbitraria. pipeline/recalcular_totales.py recalcula los
totales guardados con esta fórmula, sin volver a llamar al modelo.

Output: v1_bowleg_results.csv con columnas compatibles (bowleg_I..IV, bowleg_total,
confidence, *_evidence) + columnas nuevas (rsi_V, rsi_VI, gate_pass, integracion).

La clave se lee de la variable de entorno OPENAI_API_KEY o, si no existe, de
~/.config/openai_creds (línea OPENAI_API_KEY=...).

Uso:
    python3 pipeline/02_scoring_rsi.py full   --model gpt-4.1
    python3 pipeline/02_scoring_rsi.py submit --model gpt-4.1
    python3 pipeline/02_scoring_rsi.py fetch  <batch_id>
"""
from __future__ import annotations
import argparse, json, math, os, sys, time
from pathlib import Path
import pandas as pd
import requests

OPENAI = "https://api.openai.com/v1"
DATA = Path("data")
PROMPT = Path("prompts/bowleg_eval_v3.md")


def load_key():
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if k:
        return k
    p = Path.home() / ".config" / "openai_creds"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("[FATAL] Falta OPENAI_API_KEY (variable de entorno o ~/.config/openai_creds)")


def H(k): return {"Authorization": f"Bearer {k}"}


def system_prompt():
    t = PROMPT.read_text()
    if t.startswith("---"):
        parts = t.split("---", 2)
        if len(parts) >= 3: t = parts[2].strip()
    return t + "\n\nRecuerda: SOLO JSON, sin texto adicional."


def _safe(v, n=None):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ''
    s = str(v); return s[:n] if n else s


def build_user(row):
    return (
        f"paper_id: {int(row['paper_id'])}\n"
        f"Title: {_safe(row.get('Title'))}\n"
        f"Year: {_safe(row.get('Year'))}\n"
        f"Authors: {_safe(row.get('Authors'), 300)}\n"
        f"Keywords: {_safe(row.get('Author Keywords'), 400)}\n"
        f"Abstract:\n{_safe(row.get('Abstract'), 5000)}"
    )


def build_jsonl(path: Path, model: str, limit=None):
    df = pd.read_csv(DATA / 'v1_corpus_consolidated.csv')
    if 'paper_id' not in df.columns:
        df = df.reset_index().rename(columns={'index': 'paper_id'})
    if limit: df = df.head(limit)
    sysp = system_prompt()
    with path.open('w') as f:
        for _, row in df.iterrows():
            req = {
                "custom_id": f"paper_{int(row['paper_id'])}",
                "method": "POST", "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sysp},
                        {"role": "user", "content": build_user(row)},
                    ],
                    "max_tokens": 900, "temperature": 0,
                    "response_format": {"type": "json_object"},
                }
            }
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
    print(f"[jsonl] {len(df)} requests → {path}")
    return len(df)


def upload(p, k):
    with p.open('rb') as f:
        r = requests.post(f"{OPENAI}/files", headers=H(k),
                          files={'file': (p.name, f, 'application/jsonl')},
                          data={'purpose': 'batch'}, timeout=120)
    r.raise_for_status(); return r.json()['id']


def create_batch(fid, k):
    r = requests.post(f"{OPENAI}/batches",
                      headers={**H(k), "Content-Type": "application/json"},
                      json={"input_file_id": fid, "endpoint": "/v1/chat/completions",
                            "completion_window": "24h",
                            "metadata": {"description": "REVISA RSI v3 gpt-4.1"}}, timeout=30)
    r.raise_for_status(); return r.json()['id']


def get_batch(bid, k):
    r = requests.get(f"{OPENAI}/batches/{bid}", headers=H(k), timeout=30)
    r.raise_for_status(); return r.json()


def poll(bid, k):
    while True:
        info = get_batch(bid, k); c = info.get('request_counts', {})
        print(f"[poll {time.strftime('%H:%M:%S')}] {info['status']} {c.get('completed',0)}/{c.get('total',0)}")
        if info['status'] in ('completed','failed','expired','cancelled'): return info
        time.sleep(60)


def download(ofid, k, dest):
    r = requests.get(f"{OPENAI}/files/{ofid}/content", headers=H(k), timeout=120)
    r.raise_for_status(); dest.write_bytes(r.content)


def _es_verdadero(v) -> bool:
    """gate_pass puede venir como bool (JSON del modelo) o como texto (CSV)."""
    if isinstance(v, str):
        return v.strip().lower() in ('true', '1', '1.0')
    return bool(v) if v is not None and not (isinstance(v, float) and math.isnan(v)) else False


def compute_total(d: dict) -> float:
    if not _es_verdadero(d.get('gate_pass', False)):
        return 0.0
    crits = [d.get(f'rsi_{c}', 0) or 0 for c in ['I','II','III','IV','V','VI']]
    try:
        core = sum(float(x) for x in crits)
    except Exception:
        core = 0.0
    norm = core / 6.0 * 4.0
    integ = d.get('integracion', 0) or 0
    try: integ = float(integ)
    except Exception: integ = 0.0
    factor = 0.5 + 0.5 * integ
    # Empates hacia arriba (no round() de Python, que los manda al par). El 1e-9 protege
    # contra el error de punto flotante en los empates exactos (x.5).
    total = math.floor(norm * factor * 2 + 0.5 + 1e-9) / 2
    return max(total, 0.5)


def categoria(total: float) -> str:
    if total >= 3.5: return 'sustantivo_fuerte'
    if total >= 2.5: return 'sustantivo'
    if total >= 1.5: return 'parcial'
    if total > 0:    return 'nominal_debil'
    return 'mencion_sin_aplicacion'


def parse(raw: Path) -> pd.DataFrame:
    rows = []
    for line in raw.read_text().splitlines():
        if not line.strip(): continue
        rec = json.loads(line)
        cid = rec.get('custom_id', '')
        pid = int(cid.replace('paper_', '')) if cid.startswith('paper_') else None
        if rec.get('error'):
            rows.append({'paper_id': pid, '_error': str(rec['error'])[:200]}); continue
        body = rec.get('response', {}).get('body', {})
        try:
            d = json.loads(body['choices'][0]['message']['content'])
            total = compute_total(d)
            rows.append({
                'paper_id': pid,
                # Compatibilidad con downstream (bowleg_*)
                'bowleg_I': d.get('rsi_I'), 'bowleg_I_evidence': d.get('rsi_I_ev', ''),
                'bowleg_II': d.get('rsi_II'), 'bowleg_II_evidence': d.get('rsi_II_ev', ''),
                'bowleg_III': d.get('rsi_III'), 'bowleg_III_evidence': d.get('rsi_III_ev', ''),
                'bowleg_IV': d.get('rsi_IV'), 'bowleg_IV_evidence': d.get('rsi_IV_ev', ''),
                'bowleg_total': total,
                'confidence': d.get('confidence', 'medium'),
                'confidence_note': '',
                # Nuevos campos v3
                'rsi_V': d.get('rsi_V'), 'rsi_V_evidence': d.get('rsi_V_ev', ''),
                'rsi_VI': d.get('rsi_VI'), 'rsi_VI_evidence': d.get('rsi_VI_ev', ''),
                'gate_pass': d.get('gate_pass'), 'gate_evidence': d.get('gate_evidence', ''),
                'integracion': d.get('integracion'), 'integracion_nota': d.get('integracion_nota', ''),
                '_tokens_in': body.get('usage', {}).get('prompt_tokens', 0),
                '_tokens_out': body.get('usage', {}).get('completion_tokens', 0),
            })
        except Exception as e:
            rows.append({'paper_id': pid, '_error': f'parse: {e}'})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['submit','status','fetch','full'])
    ap.add_argument('batch_id', nargs='?')
    ap.add_argument('--model', default='gpt-4.1')
    ap.add_argument('--limit', type=int)
    args = ap.parse_args()
    k = load_key()
    jsonl = DATA / 'v1_rsi_v3_input.jsonl'
    raw = DATA / 'v1_rsi_v3_raw.jsonl'
    out = DATA / 'v1_bowleg_results.csv'   # sobrescribe la corrida anterior

    if args.action == 'submit':
        build_jsonl(jsonl, args.model, args.limit)
        bid = create_batch(upload(jsonl, k), k)
        print(f"[OK] batch: {bid}")
    elif args.action == 'status':
        print(json.dumps(get_batch(args.batch_id, k), indent=2)[:1500])
    elif args.action == 'fetch':
        info = get_batch(args.batch_id, k)
        if info['status'] != 'completed': sys.exit(f"status={info['status']}")
        download(info['output_file_id'], k, raw)
        df = parse(raw); df.to_csv(out, index=False)
        n_err = df['_error'].notna().sum() if '_error' in df.columns else 0
        print(f"[OK] {len(df)} rows → {out} ({n_err} errores)")
    elif args.action == 'full':
        n = build_jsonl(jsonl, args.model, args.limit)
        bid = create_batch(upload(jsonl, k), k)
        print(f"[OK] submitted: {bid}")
        info = poll(bid, k)
        if info['status'] != 'completed': sys.exit(f"failed: {info['status']}")
        download(info['output_file_id'], k, raw)
        df = parse(raw); df.to_csv(out, index=False)
        print(f"[OK] {len(df)} rows → {out}")


if __name__ == '__main__':
    main()
