from typing import Tuple, Dict, Any
from pathlib import Path
import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sqlalchemy.orm import Session
from ..models_db import Experiment
from .datasets import load_dataset

def build_pipeline(model_type: str, params: Dict[str, Any]) -> Pipeline:
    numeric = ["cylinders","displacement","horsepower","weight","acceleration","model_year"]
    categorical = ["origin"]
    pre = ColumnTransformer([
        ("num", StandardScaler(), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)
    ])
    model = LinearRegression(**params) if model_type == "linear" else RandomForestRegressor(random_state=42, **params)
    return Pipeline([("pre", pre), ("est", model)])

def train_once(db: Session, csv_path: Path, model_type: str, params: Dict[str, Any]) -> Tuple[int, Dict[str, float]]:
    Xtr, Xte, ytr, yte = load_dataset(csv_path)
    pipe = build_pipeline(model_type, params)
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    resid = yte - pred
    resid_std = float(np.std(resid, ddof=1))  # validation residual std

    metrics = {
        "mse": float(mean_squared_error(yte, pred)),
        "mae": float(mean_absolute_error(yte, pred)),
        "r2":  float(r2_score(yte, pred)),
        "resid_std": resid_std
    }
    exp = Experiment(model_type=model_type, params=params, metrics=metrics)
    db.add(exp); db.commit(); db.refresh(exp)

    models_dir = csv_path.parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, models_dir / f"exp_{exp.id}.joblib")
    return exp.id, metrics
