from pathlib import Path

REQUIRED = ["mpg","cylinders","displacement","horsepower","weight","acceleration","model_year","origin"]

def ensure_mpg_csv(data_dir: Path) -> Path:
    csv_path = data_dir / "auto-mpg.csv"
    if csv_path.exists():
        return csv_path
    try:
        import seaborn as sns
        import pandas as pd
        df = sns.load_dataset("mpg")
        df = df.dropna(subset=REQUIRED)
        num_cols = ["cylinders","displacement","horsepower","weight","acceleration","model_year"]
        df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
        df = df.dropna(subset=num_cols)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        return csv_path
    except Exception:
        pass
    try:
        from sklearn.datasets import fetch_openml
        import pandas as pd
        ds = fetch_openml(name="autoMpg", version=1, as_frame=True)
        df = ds.frame.copy()
        df = df.rename(columns={"model-year": "model_year"})
        df = df.dropna(subset=REQUIRED)
        num_cols = ["cylinders","displacement","horsepower","weight","acceleration","model_year"]
        df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
        df = df.dropna(subset=num_cols)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        return csv_path
    except Exception as e:
        raise RuntimeError(f"Failed to bootstrap dataset: {e}")
