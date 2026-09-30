#!/usr/bin/env python3
"""
04_topicos.py — v2: modelado de tópicos (BERTopic) sobre el corpus elegible.

Mismo diseño que la v1 (pipeline/03_modelado_topicos.py): embeddings
all-MiniLM-L6-v2 sobre título + keywords + abstract, barrido UMAP (5D) × HDBSCAN
con el mismo puntaje combinado, y ajuste final de BERTopic con la mejor
combinación. Además guarda coordenadas UMAP 2D para el mapa.

Uso:
    python3 pipeline/v2/04_topicos.py embeddings   # solo embeddings (todo el corpus v2)
    python3 pipeline/v2/04_topicos.py              # barrido + ajuste final (solo elegibles)

Salidas:
    data/v2_topic_sweep_results.csv, data/v2_topic_sweep_best.json
    data/v2_bertopic_assignments.csv   paper_id, topic_id, umap_x, umap_y
    data/v2_bertopic_info.csv          Topic, Count, Name, Representation, Representative_Docs
    data/v2_bertopic_top_words.json    {topic_id: [[palabra, peso], …]}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path("data")
CACHE = Path("work/v2_embeddings_minilm.npy")
SEED = 42


def build_text(row) -> str:
    parts = [row.get(c) for c in ["Title", "Author Keywords", "Index Keywords", "Abstract"]]
    return " ".join(p for p in parts if isinstance(p, str)).strip()


def embeddings(corpus: pd.DataFrame) -> np.ndarray:
    if CACHE.exists():
        embs = np.load(CACHE)
        if len(embs) == len(corpus):
            return embs
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embs = model.encode(corpus['doc_text'].tolist(), batch_size=64,
                        show_progress_bar=False, convert_to_numpy=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.save(CACHE, embs)
    return embs


def score_combo(n_clusters: int, pct_outliers: float, sil: float) -> float:
    """Mismo puntaje que la v1: favorece ~15 clusters y pocos outliers."""
    if n_clusters < 6 or n_clusters > 40 or pct_outliers > 0.55:
        return -1.0
    n_penalty = 1 - min(abs(n_clusters - 15) / 20, 1.0)
    out_penalty = max(0, 1 - pct_outliers / 0.50)
    return sil * n_penalty * out_penalty


def sweep(embs: np.ndarray) -> dict:
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.metrics import silhouette_score
    rows = []
    for nn in [5, 10, 15]:
        reduced = UMAP(n_neighbors=nn, n_components=5, min_dist=0.0,
                       metric='cosine', random_state=SEED).fit_transform(embs)
        for mcs in [5, 7, 10, 12, 15, 20]:
            labels = HDBSCAN(min_cluster_size=mcs, metric='euclidean',
                             cluster_selection_method='eom').fit_predict(reduced)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            pct_out = float((labels == -1).mean())
            mask = labels != -1
            sil = -1.0
            if mask.sum() > 50 and n_clusters >= 2:
                sil = float(silhouette_score(reduced[mask], labels[mask],
                                             sample_size=2000, random_state=SEED))
            rows.append({'min_cluster_size': mcs, 'n_neighbors': nn, 'min_dist': 0.0,
                         'n_clusters': n_clusters, 'pct_outliers': round(pct_out, 3),
                         'silhouette': round(sil, 4),
                         'score': round(score_combo(n_clusters, pct_out, sil), 4)})
            print(f"  nn={nn:>2} mcs={mcs:>2} → clusters={n_clusters:>3} "
                  f"outliers={pct_out*100:4.1f}% sil={sil:+.3f}")
    df = pd.DataFrame(rows).sort_values('score', ascending=False)
    df.to_csv(DATA / 'v2_topic_sweep_results.csv', index=False)
    best = df.iloc[0].to_dict()
    (DATA / 'v2_topic_sweep_best.json').write_text(json.dumps(best, indent=2, default=str))
    return best


def main():
    corpus = pd.read_csv(DATA / 'v2_corpus_consolidated.csv')
    corpus['doc_text'] = corpus.apply(build_text, axis=1)
    embs = embeddings(corpus)
    print(f"[1] Embeddings: {embs.shape}")
    if len(sys.argv) > 1 and sys.argv[1] == 'embeddings':
        return

    scored = pd.read_csv(DATA / 'v2_corpus_scored.csv')      # solo elegibles
    idx = corpus.index[corpus['paper_id'].isin(scored['paper_id'])].to_numpy()
    sub, sub_embs = corpus.loc[idx].reset_index(drop=True), embs[idx]
    print(f"[2] Corpus elegible: {len(sub)} documentos")

    print("[3] Barrido UMAP × HDBSCAN")
    best = sweep(sub_embs)
    print(f"    mejor: {best}")

    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
    stop = sorted(ENGLISH_STOP_WORDS | {
        'de', 'la', 'el', 'en', 'los', 'las', 'del', 'que', 'por', 'con', 'una', 'para', 'se',
        'su', 'sus', 'al', 'lo', 'como', 'más', 'este', 'esta', 'entre', 'sobre', 'y', 'o',
        'study', 'studies', 'paper', 'article', 'research', 'chapter', 'book', 'findings',
        'results', 'analysis', 'using', 'based', 'elsevier', 'rights', 'reserved', 'author',
        'authors', 'published', 'springer', 'taylor', 'francis', 'copyright'})
    model = BERTopic(
        umap_model=UMAP(n_neighbors=int(best['n_neighbors']), n_components=5, min_dist=0.0,
                        metric='cosine', random_state=SEED),
        hdbscan_model=HDBSCAN(min_cluster_size=int(best['min_cluster_size']), metric='euclidean',
                              cluster_selection_method='eom', prediction_data=True),
        vectorizer_model=CountVectorizer(stop_words=stop, ngram_range=(1, 2), min_df=2),
        calculate_probabilities=False, verbose=False)
    topics, _ = model.fit_transform(sub['doc_text'].tolist(), sub_embs)
    info = model.get_topic_info()
    info[['Topic', 'Count', 'Name', 'Representation', 'Representative_Docs']].to_csv(
        DATA / 'v2_bertopic_info.csv', index=False)
    top_words = {str(t): [[w, float(s)] for w, s in model.get_topic(t)]
                 for t in info['Topic'] if t != -1}
    (DATA / 'v2_bertopic_top_words.json').write_text(json.dumps(top_words, indent=2, ensure_ascii=False))

    xy = UMAP(n_neighbors=15, n_components=2, min_dist=0.1, metric='cosine',
              random_state=SEED).fit_transform(sub_embs)
    pd.DataFrame({'paper_id': sub['paper_id'], 'topic_id': topics,
                  'umap_x': xy[:, 0], 'umap_y': xy[:, 1]}).to_csv(
        DATA / 'v2_bertopic_assignments.csv', index=False)
    n_t = len(info) - (1 if -1 in set(info['Topic']) else 0)
    print(f"[OK] {n_t} tópicos · {int((np.array(topics) == -1).sum())} outliers → data/v2_bertopic_*")


if __name__ == '__main__':
    main()
