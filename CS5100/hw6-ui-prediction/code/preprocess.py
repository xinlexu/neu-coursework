import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"


def main() -> None:
    input_path = DATA_DIR / "train_logs.csv"
    df = pd.read_csv(input_path)

    original_rows = len(df)

    # Remove invalid sessions and users
    df = df[df["session_id"].notna()]
    df = df[df["user_id"].notna()]
    df = df[df["user_id"] >= 0]

    # Drop sessions with fewer than two events
    session_sizes = df.groupby("session_id").size()
    valid_sessions = session_sizes[session_sizes >= 2].index
    df = df[df["session_id"].isin(valid_sessions)]

    # Remove duplicate events
    df = df.drop_duplicates()

    # Remove negative durations if present
    if "duration" in df.columns:
        df["duration"] = df["duration"].fillna(0)
        df = df[df["duration"] >= 0]

    # Fill missing categorical values
    if "element_id" in df.columns:
        df["element_id"] = df["element_id"].fillna("none")
    if "content_id" in df.columns:
        df["content_id"] = df["content_id"].fillna("unknown")
    if "category" in df.columns:
        df["category"] = df["category"].fillna("unknown")

    # Parse timestamps and sort
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["user_id", "session_id", "timestamp"])

    cleaned_rows = len(df)
    removed_rows = original_rows - cleaned_rows
    removed_pct = (removed_rows / original_rows * 100.0) if original_rows > 0 else 0.0
    unique_users = df["user_id"].nunique()
    unique_sessions = df["session_id"].nunique()
    date_min = df["timestamp"].min()
    date_max = df["timestamp"].max()

    output_path = DATA_DIR / "cleaned_logs.csv"
    df.to_csv(output_path, index=False)

    RESULTS_DIR.mkdir(exist_ok=True)

    lines = [
        f"Original rows: {original_rows}",
        f"After cleaning: {cleaned_rows}",
        f"Rows removed: {removed_rows} ({removed_pct:.2f}%)",
        f"Unique users: {unique_users}",
        f"Unique sessions: {unique_sessions}",
        f"Date range: {date_min.date()} to {date_max.date()}",
    ]
    text = "\n".join(lines)
    print(text)

    with open(RESULTS_DIR / "preprocess_log.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
