import pickle
from pathlib import Path
from typing import Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"


def load_split(name: str):
    with open(DATA_DIR / f"{name}.pkl", "rb") as f:
        data = pickle.load(f)
    return data["X"], data["y"], data["timestamps"]


def build_transition_table(last_screens: np.ndarray, targets: np.ndarray) -> Dict[int, Dict[int, int]]:
    table: Dict[int, Dict[int, int]] = {}
    for cur, nxt in zip(last_screens, targets):
        cur = int(cur)
        nxt = int(nxt)
        if cur not in table:
            table[cur] = {}
        table[cur][nxt] = table[cur].get(nxt, 0) + 1
    return table


def get_global_ranking(targets: np.ndarray) -> List[int]:
    counts: Dict[int, int] = {}
    for nxt in targets:
        nxt = int(nxt)
        counts[nxt] = counts.get(nxt, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [k for k, _ in ranked]


def predict_topk(table: Dict[int, Dict[int, int]], global_rank: List[int], current: int, k: int) -> List[int]:
    if current in table:
        items = sorted(table[current].items(), key=lambda x: x[1], reverse=True)
        ordered = [j for j, _ in items]
    else:
        ordered = global_rank
    if len(ordered) < k:
        ordered = ordered + global_rank
    return ordered[:k]


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)

    X_train, y_train, _ = load_split("train")
    X_test, y_test, _ = load_split("test")

    last_train = X_train[:, -1, 0].astype(int)
    last_test = X_test[:, -1, 0].astype(int)

    table = build_transition_table(last_train, y_train)
    global_rank = get_global_ranking(y_train)

    top1_correct = 0
    top3_correct = 0

    for cur, true in zip(last_test, y_test):
        preds = predict_topk(table, global_rank, int(cur), k=3)
        if preds[0] == int(true):
            top1_correct += 1
        if int(true) in preds:
            top3_correct += 1

    n = len(y_test)
    acc1 = top1_correct / n if n > 0 else 0.0
    acc3 = top3_correct / n if n > 0 else 0.0

    lines = [
        f"Baseline most-frequent-next-screen results:",
        f"Test size: {n}",
        f"Top-1 accuracy: {acc1:.4f}",
        f"Top-3 accuracy: {acc3:.4f}",
    ]
    text = "\n".join(lines)
    print(text)

    with open(RESULTS_DIR / "baseline_results.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
