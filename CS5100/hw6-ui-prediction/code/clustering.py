import pickle
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"


def choose_k(X: np.ndarray, candidate_k: List[int]) -> int:
    best_k = None
    best_score = -1.0
    for k in candidate_k:
        model = KMeans(n_clusters=k, n_init=10, max_iter=300, random_state=42)
        labels = model.fit_predict(X)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(X, labels)
        if score > best_score:
            best_score = score
            best_k = k
    if best_k is None:
        best_k = 2
    return best_k


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    MODELS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(DATA_DIR / "user_features.csv")
    feature_cols = ["avg_session_length", "conversion_rate", "num_sessions", "avg_duration", "search_frequency"]
    X = df[feature_cols].values

    candidate_k = [3, 4, 5]
    best_k = choose_k(X, candidate_k)

    model = KMeans(n_clusters=best_k, n_init=10, max_iter=300, random_state=42)
    labels = model.fit_predict(X)
    df["persona_label"] = labels

    cluster_sizes = df["persona_label"].value_counts().sort_index()
    if (cluster_sizes < 50).any():
        model_small = KMeans(n_clusters=2, n_init=10, max_iter=300, random_state=42)
        labels_small = model_small.fit_predict(X)
        cluster_sizes_small = pd.Series(labels_small).value_counts()
        if (cluster_sizes_small >= 50).all():
            model = model_small
            labels = labels_small
            df["persona_label"] = labels
            best_k = 2

    with open(MODELS_DIR / "kmeans_model.pkl", "wb") as f:
        pickle.dump(model, f)

    df.to_csv(DATA_DIR / "user_personas.csv", index=False)

    means = df.groupby("persona_label")[feature_cols].mean()
    with open(MODELS_DIR / "user_feature_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    means_raw = scaler.inverse_transform(means.values)
    means_raw_df = pd.DataFrame(means_raw, columns=feature_cols, index=means.index)

    lines = [f"Optimal K: {best_k}"]
    lines.append("Cluster sizes:")
    for cluster_id, size in cluster_sizes.sort_index().items():
        lines.append(f"Cluster {cluster_id}: {size} users")
    lines.append("")
    lines.append("Cluster means (original scale):")
    for cluster_id, row in means_raw_df.iterrows():
        lines.append(f"Cluster {cluster_id}:")
        for col in feature_cols:
            lines.append(f"  {col}: {row[col]:.4f}")
        lines.append("")

    with open(RESULTS_DIR / "cluster_analysis.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X)

    plt.figure()
    scatter = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, s=5)
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.title("User personas (PCA projection)")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "cluster_visualization.png")
    plt.close()


if __name__ == "__main__":
    main()
