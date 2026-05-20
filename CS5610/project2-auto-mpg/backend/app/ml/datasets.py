import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

FEATURES = ["cylinders","displacement","horsepower","weight","acceleration","model_year","origin"]
TARGET = "mpg"

def load_dataset(csv_path: str | Path, test_size=0.2, random_state=42):
    df = pd.read_csv(csv_path)
    df = df.replace("?", np.nan)
    df["horsepower"] = pd.to_numeric(df["horsepower"], errors="coerce")
    df = df.dropna(subset=FEATURES + [TARGET])
    X = df[FEATURES].copy()
    y = df[TARGET].astype(float).values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=random_state)
    return Xtr, Xte, ytr, yte
