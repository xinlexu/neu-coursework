import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"


def main() -> None:
    logs = pd.read_csv(DATA_DIR / "cleaned_logs.csv", parse_dates=["timestamp"])

    session = logs.groupby(["user_id", "session_id"])

    session_sizes = session.size().rename("events_per_session")
    session_conv = session["conversion_flag"].max().rename("session_converted")

    user_sessions = session_sizes.groupby("user_id")
    avg_session_length = user_sessions.mean().rename("avg_session_length")
    num_sessions = user_sessions.size().rename("num_sessions")

    session_conv_by_user = session_conv.groupby("user_id")
    conversion_rate = (session_conv_by_user.mean()).rename("conversion_rate")

    if "duration" in logs.columns:
        session_duration = (session["duration"].sum() / 60000.0).rename("session_duration_minutes")
        avg_duration = session_duration.groupby("user_id").mean().rename("avg_duration")
    else:
        avg_duration = pd.Series(0.0, index=avg_session_length.index, name="avg_duration")

    if "event_type" in logs.columns:
        mask_search = logs["event_type"] == "SEARCH_PINS"
        search_sessions = logs[mask_search].groupby(["user_id", "session_id"]).size()
        search_sessions_per_user = search_sessions.groupby("user_id").size()
        search_frequency = (search_sessions_per_user / num_sessions).rename("search_frequency")
    else:
        search_frequency = pd.Series(0.0, index=avg_session_length.index, name="search_frequency")

    features = pd.concat(
        [avg_session_length, conversion_rate, num_sessions, avg_duration, search_frequency], axis=1
    ).reset_index()

    features = features.fillna(0.0)

    scaler = StandardScaler()
    cols = ["avg_session_length", "conversion_rate", "num_sessions", "avg_duration", "search_frequency"]
    scaled_values = scaler.fit_transform(features[cols].values)
    features[cols] = scaled_values

    DATA_DIR.mkdir(exist_ok=True)
    features.to_csv(DATA_DIR / "user_features.csv", index=False)

    MODELS_DIR.mkdir(exist_ok=True)
    with open(MODELS_DIR / "user_feature_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)


if __name__ == "__main__":
    main()
