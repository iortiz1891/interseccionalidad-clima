#!/usr/bin/env python3
"""
27_v1_topic_optimization.py — Sweep en grid sobre params UMAP+HDBSCAN.

Para cada combinación:
- Corre UMAP (5D)
- Corre HDBSCAN
- Computa: n_clusters, % outliers, silhouette score (sobre asignados)
- Computa score combinado y reporta tabla

Output:
  data/v1_topic_sweep_results.csv
  data/v1_topic_sweep_best.json
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.metrics import silhouette_score

DATA = Path("data")


def build_text(row) -> str:
    parts = []
    for col in ["Title", "Author Keywords", "Index Keywords", "Abstract"]:
        v = row.get(col)
        if isinstance(v, str):
            parts.append(v)
    return " ".join(parts).strip()


def score_combo(n_clusters: int, pct_outliers: float, sil: float) -> float:
    """Score combinado (ajustado a corpus chico ~971): acepta 6-30 clusters."""
    if n_clusters < 6 or n_clusters > 40 or pct_outliers > 0.55:
        return -1.0
    # Sweet spot: ~12-20 clusters para corpus de ~1000 papers
    n_penalty = 1 - min(abs(n_clusters - 15) / 20, 1.0)
    out_penalty = max(0, 1 - pct_outliers / 0.50)
    return sil * n_penalty * out_penalty


def main():
    print("[1] Cargando corpus + computando embeddings")
    corpus = pd.read_csv(DATA / 'v1_corpus_consolidated.csv').dropna(subset=['Title']).reset_index(drop=True)
    corpus['doc_text'] = corpus.apply(build_text, axis=1)
    corpus = corpus[corpus['doc_text'].str.len() > 50].reset_index(drop=True)

    cache = DATA / 'v1_embeddings_minilm.npy'
    if cache.exists():
        embs = np.load(cache)
        print(f"    Cached embeddings: {embs.shape}")
    else:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embs = model.encode(corpus['doc_text'].tolist(),
                             batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        np.save(cache, embs)
        print(f"    Computed + cached: {embs.shape} → {cache}")

    # ─── Grid ───
    min_cluster_sizes = [5, 7, 10, 12, 15, 20]
    n_neighbors_list = [5, 10, 15]
    min_dist_list = [0.0]
    total = len(min_cluster_sizes) * len(n_neighbors_list) * len(min_dist_list)
    print(f"\n[2] Sweep: {total} combinaciones")

    rows = []
    t0 = time.time()
    i = 0
    # Cache UMAP por (n_neighbors, min_dist) ya que es lo más caro
    umap_cache = {}
    for nn in n_neighbors_list:
        for md in min_dist_list:
            key = (nn, md)
            t_umap = time.time()
            reducer = UMAP(n_neighbors=nn, n_components=5, min_dist=md,
                            metric='cosine', random_state=42)
            reduced = reducer.fit_transform(embs)
            umap_cache[key] = reduced
            print(f"    UMAP cached for nn={nn}, md={md}  ({time.time()-t_umap:.1f}s)")

    for nn in n_neighbors_list:
        for md in min_dist_list:
            reduced = umap_cache[(nn, md)]
            for mcs in min_cluster_sizes:
                i += 1
                t_hdb = time.time()
                clusterer = HDBSCAN(min_cluster_size=mcs, metric='euclidean',
                                     cluster_selection_method='eom')
                labels = clusterer.fit_predict(reduced)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                n_outliers = int((labels == -1).sum())
                pct_outliers = n_outliers / len(labels)
                mask = labels != -1
                if mask.sum() > 50 and n_clusters >= 2:
                    try:
                        sil = float(silhouette_score(reduced[mask], labels[mask], sample_size=2000, random_state=42))
                    except Exception:
                        sil = -1.0
                else:
                    sil = -1.0
                score = score_combo(n_clusters, pct_outliers, sil)
                # Tamaño promedio y mediana de clusters
                if n_clusters >= 1:
                    sizes = pd.Series(labels[mask]).value_counts().tolist()
                    median_size = float(np.median(sizes))
                    max_size = int(np.max(sizes))
                else:
                    median_size = 0; max_size = 0
                rows.append({
                    'min_cluster_size': mcs, 'n_neighbors': nn, 'min_dist': md,
                    'n_clusters': n_clusters, 'n_outliers': n_outliers,
                    'pct_outliers': round(pct_outliers, 3),
                    'silhouette': round(sil, 4),
                    'median_cluster_size': median_size,
                    'max_cluster_size': max_size,
                    'score': round(score, 4),
                })
                print(f"  [{i:>2}/{total}] mcs={mcs:>2} nn={nn:>2} md={md} → "
                      f"clusters={n_clusters:>3} outliers={pct_outliers*100:>4.1f}% "
                      f"sil={sil:>+.3f} score={score:>+.4f}  ({time.time()-t_hdb:.1f}s)")

    print(f"\n[3] Total: {time.time()-t0:.0f}s")

    df = pd.DataFrame(rows).sort_values('score', ascending=False)
    out_csv = DATA / 'v1_topic_sweep_results.csv'
    df.to_csv(out_csv, index=False)
    print(f"\n[OK] Tabla → {out_csv}")
    print("\n=== TOP 10 combinaciones por score ===")
    print(df.head(10).to_string(index=False))

    best = df.iloc[0].to_dict()
    print("\n=== MEJOR COMBINACIÓN ===")
    print(json.dumps(best, indent=2, default=str))

    (DATA / 'v1_topic_sweep_best.json').write_text(json.dumps(best, indent=2, default=str))
    print(f"\n[OK] Best params → data/v1_topic_sweep_best.json")


if __name__ == '__main__':
    main()
