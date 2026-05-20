import random
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import torch

from train_lstm import LSTMNextScreen, load_encoder  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"


def encode_with_unknown(encoder: Dict[str, Any], values: List[str]) -> np.ndarray:
    mapping = encoder["class_to_index"]
    unknown_index = encoder["unknown_index"]
    encoded = np.fromiter((mapping.get(str(v), unknown_index) for v in values), dtype=np.int64)
    return encoded


def decode_screen(encoder: Dict[str, Any], idx: int) -> str:
    le = encoder["label_encoder"]
    classes = le.classes_
    if 0 <= idx < len(classes):
        return str(le.inverse_transform([idx])[0])
    return "UNKNOWN_SCREEN"


def build_screen_index(logs: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    groups: Dict[str, pd.DataFrame] = {}
    for name, g in logs.groupby("screen_name"):
        groups[str(name)] = g
    return groups


def main() -> None:
    logs = pd.read_csv(DATA_DIR / "cleaned_logs.csv", parse_dates=["timestamp"])
    personas = pd.read_csv(DATA_DIR / "user_personas.csv")

    checkpoint = torch.load(MODELS_DIR / "model_lstm.pth", map_location="cpu")
    config = checkpoint["config"]
    num_screens = config["num_screens"]
    num_events = config["num_events"]
    seq_len = config["seq_len"]

    screen_enc = load_encoder(MODELS_DIR / "screen_encoder.pkl")
    event_enc = load_encoder(MODELS_DIR / "event_encoder.pkl")

    model = LSTMNextScreen(
        num_screens=num_screens,
        num_events=num_events,
        embedding_dim=config["embedding_dim"],
        hidden_dim=config["hidden_dim"],
        num_layers=config["num_layers"],
        dropout=config["dropout"],
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    screen_index = build_screen_index(logs)
    user_groups = {uid: g for uid, g in logs.groupby("user_id")}

    synthetic_rows = []

    rng = np.random.default_rng(42)
    epsilon = 0.1
    max_steps = 15

    for persona_id in sorted(personas["persona_label"].unique()):
        sub = personas[personas["persona_label"] == persona_id]
        if sub.empty:
            continue
        n_users = min(100, len(sub))
        sampled_users = sub.sample(n=n_users, random_state=42)["user_id"].tolist()

        for user_id in sampled_users:
            if user_id not in user_groups:
                continue
            user_log = user_groups[user_id].sort_values("timestamp")
            sessions = list(user_log.groupby("session_id"))
            random.shuffle(sessions)
            start_session = None
            for _, g in sessions:
                if len(g) >= seq_len and g["conversion_flag"].sum() == 0:
                    start_session = g.sort_values("timestamp")
                    break
            if start_session is None:
                continue

            start_seq = start_session.head(seq_len).copy()
            base_ts = start_seq["timestamp"].min()
            session_id = f"sim_p{persona_id}_u{user_id}_1"

            history_screens = start_seq["screen_name"].astype(str).tolist()
            history_events = start_seq["event_type"].astype(str).tolist()

            last_ts = base_ts
            for _, row in start_seq.iterrows():
                new_row = row.copy()
                new_row["session_id"] = session_id
                new_row["timestamp"] = last_ts
                synthetic_rows.append(new_row)

            for _ in range(max_steps):
                screen_ids = encode_with_unknown(screen_enc, history_screens)
                event_ids = encode_with_unknown(event_enc, history_events)

                screens_t = torch.from_numpy(screen_ids).long().unsqueeze(0)
                events_t = torch.from_numpy(event_ids).long().unsqueeze(0)

                with torch.no_grad():
                    logits = model(screens_t, events_t)
                    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

                if rng.random() < epsilon:
                    next_screen_id = int(rng.integers(0, num_screens))
                else:
                    next_screen_id = int(np.argmax(probs))

                next_screen_name = decode_screen(screen_enc, next_screen_id)

                if next_screen_name in screen_index:
                    candidates = screen_index[next_screen_name]
                    base_event = candidates.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
                else:
                    base_event = logs.sample(n=1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]

                last_ts = last_ts + pd.Timedelta(seconds=int(base_event.get("duration", 1000) / 1000.0))
                new_row = base_event.copy()
                new_row["session_id"] = session_id
                new_row["user_id"] = user_id
                new_row["screen_name"] = next_screen_name
                new_row["timestamp"] = last_ts

                synthetic_rows.append(new_row)

                history_screens = history_screens[1:] + [next_screen_name]
                history_events = history_events[1:] + [str(new_row["event_type"])]

                if "conversion_flag" in new_row and int(new_row["conversion_flag"]) == 1:
                    break

    synthetic = pd.DataFrame(synthetic_rows)
    synthetic.to_csv(DATA_DIR / "synthetic_logs.csv", index=False)


if __name__ == "__main__":
    main()
