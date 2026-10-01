#!/usr/bin/env python3
"""
04b_etiquetas.py — v2: etiquetas legibles de los tópicos.

Si existe data/v2_topic_labels_manual.json ({topic_id: "etiqueta"}), usa esas
etiquetas (redactadas leyendo palabras clave y títulos representativos). Si no,
arma una etiqueta provisional con las tres palabras de mayor peso c-TF-IDF.

Salida: data/v2_topic_ai_labels.json  {topic_id: {label, n_papers, top_words}}
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

DATA = Path("data")


def main():
    info = pd.read_csv(DATA / 'v2_bertopic_info.csv')
    words = json.loads((DATA / 'v2_bertopic_top_words.json').read_text())
    manual_p = DATA / 'v2_topic_labels_manual.json'
    manual = json.loads(manual_p.read_text()) if manual_p.exists() else {}
    out = {}
    for _, r in info[info['Topic'] >= 0].iterrows():
        tid = str(int(r['Topic']))
        top = [w for w, _ in words.get(tid, [])][:8]
        label = manual.get(tid) or ' · '.join(top[:3])
        out[tid] = {'label': label, 'n_papers': int(r['Count']), 'top_words': top[:5]}
    (DATA / 'v2_topic_ai_labels.json').write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"[OK] {len(out)} etiquetas ({'manuales' if manual else 'provisionales'}) → data/v2_topic_ai_labels.json")


if __name__ == '__main__':
    main()
