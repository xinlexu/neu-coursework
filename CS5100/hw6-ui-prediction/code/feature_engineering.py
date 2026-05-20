import pickle
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

SEQ_LEN = 10


def fit_safe_label_encoder(values: pd.Series) -> Dict[str, Any]:
    le = LabelEncoder()
    values_str = values.astype(str)
    le.fit(values_str)
    classes = list(le.classes_)
    mapping = {v: i for i, v in enumerate(classes)}
    unknown_index = len(classes)
    encoder = {
        "label_encoder": le,
        "class_to_index": mapping,
        "unknown_index": unknown_index,
    }
    return encoder


def encode_with_unknown(encoder: Dict[str, Any], values: np.ndarray) -> np.ndarray:
    mapping = encoder["class_to_index"]
    unknown_index = encoder["unknown_index"]
    encoded = np.fromiter((mapping.get(str(v), unknown_index) for v in values), dtype=np.int64)
    return encoded


def build_sequences(df: pd.DataFrame, screen_enc: Dict[str, Any], event_enc: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    df = df.sort_values(["user_id", "session_id", "timestamp"])
    sequences = []
    targets = []
    timestamps = []

    grouped = df.groupby(["user_id", "session_id"], sort=False)
    for (_, _), group in grouped:
        screens = group["screen_name"].astype(str).values
        events = group["event_type"].astype(str).values
        times = group["timestamp"].values

        if len(group) <= SEQ_LEN:
            continue

        screen_ids = encode_with_unknown(screen_enc, screens)
        event_ids = encode_with_unknown(event_enc, events)

        for start in range(0, len(group) - SEQ_LEN):
            end = start + SEQ_LEN
            seq_s = screen_ids[start:end]
            seq_e = event_ids[start:end]
            target = screen_ids[end]
            ts = times[end - 1]

            seq = np.stack([seq_s, seq_e], axis=1)
            sequences.append(seq)
            targets.append(target)
            timestamps.append(ts)

    X = np.stack(sequences, axis=0)
    y = np.asarray(targets, dtype=np.int64)
    t = np.asarray(timestamps)
    return X, y, t


def chronological_split(X: np.ndarray, y: np.ndarray, t: np.ndarray):
    order = np.argsort(t)
    X = X[order]
    y = y[order]
    t = t[order]

    n = len(y)
    train_end = int(0.7 * n)
    val_end = int(0.85 * n)

    splits = {}
    splits["train"] = {"X": X[:train_end], "y": y[:train_end], "timestamps": t[:train_end]}
    splits["val"] = {"X": X[train_end:val_end], "y": y[train_end:val_end], "timestamps": t[train_end:val_end]}
    splits["test"] = {"X": X[val_end:], "y": y[val_end:], "timestamps": t[val_end:]}
    return splits


def main() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    logs = pd.read_csv(DATA_DIR / "cleaned_logs.csv", parse_dates=["timestamp"])

    screen_enc = fit_safe_label_encoder(logs["screen_name"])
    event_enc = fit_safe_label_encoder(logs["event_type"])
    element_enc = fit_safe_label_encoder(logs["element_id"].fillna("none"))

    with open(MODELS_DIR / "screen_encoder.pkl", "wb") as f:
        pickle.dump(screen_enc, f)
    with open(MODELS_DIR / "event_encoder.pkl", "wb") as f:
        pickle.dump(event_enc, f)
    with open(MODELS_DIR / "element_encoder.pkl", "wb") as f:
        pickle.dump(element_enc, f)

    X, y, t = build_sequences(logs, screen_enc, event_enc)
    splits = chronological_split(X, y, t)

    for name, data in splits.items():
        with open(DATA_DIR / f"{name}.pkl", "wb") as f:
            pickle.dump(data, f)

    info_lines = [
        f"Total sequences: {len(y)}",
        f"Train: {len(splits['train']['y'])}",
        f"Val: {len(splits['val']['y'])}",
        f"Test: {len(splits['test']['y'])}",
        f"Sequence length N: {SEQ_LEN}",
    ]
    text = "\n".join(info_lines)
    print(text)
    with open(RESULTS_DIR / "feature_engineering_log.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
