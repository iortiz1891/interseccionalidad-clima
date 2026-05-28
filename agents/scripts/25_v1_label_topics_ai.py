#!/usr/bin/env python3
"""
25_v1_label_topics_ai.py — Etiqueta los 84 tópicos BERTopic con GPT-4o-mini.

Para cada tópico:
- Toma top 10 palabras (c-TF-IDF de BERTopic)
- Toma 5 títulos de papers representativos del cluster
- Pide a GPT-4o-mini un label de 2-5 palabras en español

Output: data/v1_topic_ai_labels.json (mapa topic_id → label + descripción corta)
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path
import pandas as pd
import requests

DATA = Path("data")


def load_key():
    creds = Path.home() / ".config" / "openai_creds"
    for line in creds.read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("[FATAL] OPENAI_API_KEY no encontrada")


SYSTEM = """Eres un experto en análisis temático de literatura académica sobre cambio climático e interseccionalidad. Tu tarea es asignar a cada tópico un label corto y descriptivo en español.

Reglas:
- 2 a 5 palabras
- En español (sin traducir nombres propios como "Katrina", "COVID", "ESG", "India", "Patagonia")
- Específico y discriminativo (no genérico como "estudios sociales")
- Capta la unidad temática que conecta los papers
- NO uses "estudios sobre", "investigación de" — directo al concepto
- Si detectas un cluster artefactual (ruido de indexación, falsos positivos como tráfico/transporte cuando "intersection" es vial, o citas mal parseadas), márcalo con prefijo "[Artefacto]"

Devuelve SOLO JSON con esta estructura:
{
  "label": "<2-5 palabras>",
  "descripcion": "<1 oración explicando el tópico>"
}"""


def build_user_prompt(top_words: list, sample_titles: list) -> str:
    words_str = ", ".join(top_words[:10])
    titles_str = "\n".join(f"- {t[:120]}" for t in sample_titles[:5])
    return f"""Top palabras (c-TF-IDF de BERTopic):
{words_str}

Títulos representativos:
{titles_str}

Devuelve JSON con label y descripcion."""


def label_topic(api_key: str, top_words: list, sample_titles: list) -> dict:
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_user_prompt(top_words, sample_titles)},
        ],
        "max_tokens": 200,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload, timeout=30,
    )
    if not r.ok:
        return {"label": "?", "descripcion": f"error {r.status_code}"}
    try:
        content = r.json()["choices"][0]["message"]["content"]
        usage = r.json().get("usage", {})
        parsed = json.loads(content)
        parsed["_tokens"] = usage.get("total_tokens", 0)
        return parsed
    except Exception as e:
        return {"label": "?", "descripcion": f"parse error: {e}"}


def main():
    api_key = load_key()

    top_words = json.loads((DATA / 'v1_bertopic_top_words.json').read_text())
    info = pd.read_csv(DATA / 'v1_bertopic_info.csv')
    assignments = pd.read_csv(DATA / 'v1_bertopic_assignments.csv')

    print(f"[info] {len(top_words)} tópicos con top words")

    results = {}
    total_tokens = 0
    for tid_str, words_with_scores in top_words.items():
        tid = int(tid_str)
        if tid < 0: continue

        words = [w for w, _ in words_with_scores]
        sub = assignments[assignments['topic_id'] == tid]
        titles = sub['Title'].dropna().tolist()[:5]

        result = label_topic(api_key, words, titles)
        total_tokens += result.pop('_tokens', 0)
        results[str(tid)] = {
            'label': result.get('label', '?'),
            'descripcion': result.get('descripcion', ''),
            'n_papers': len(sub),
            'top_words': words[:5],
        }
        print(f"  T{tid:>3} (n={len(sub):>3}): {result.get('label','?'):<35s}  {result.get('descripcion','')[:60]}")
        time.sleep(0.1)  # rate limit polite

    # Guardar
    out = DATA / 'v1_topic_ai_labels.json'
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # Costo aproximado
    cost = total_tokens * 0.30 / 1_000_000  # mix input+output, aproximación
    print(f"\n[OK] {len(results)} tópicos etiquetados → {out}")
    print(f"     Tokens totales: {total_tokens:,}  |  Costo aprox: ~${cost:.4f}")


if __name__ == '__main__':
    main()
