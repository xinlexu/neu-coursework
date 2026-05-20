from pathlib import Path
import joblib
import pandas as pd
from sqlalchemy.orm import Session
from ..models_db import Prediction, Experiment
from .datasets import FEATURES

def predict_once(db: Session, data_dir: Path, experiment_id: int, x: dict):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise ValueError("experiment not found")
    model_path = data_dir.parent / "models" / f"exp_{experiment_id}.joblib"
    pipe = joblib.load(model_path)

    X = pd.DataFrame([{k: x[k] for k in FEATURES}], columns=FEATURES)
    yhat = float(pipe.predict(X)[0])

    std = float(exp.metrics.get("resid_std") or 2.0)
    band = 1.64 * std
    interval = [yhat - band, yhat + band]

    out = {"mpg": yhat, "interval": interval}
    pred = Prediction(experiment_id=experiment_id, input=x, output=out)
    db.add(pred); db.commit(); db.refresh(pred)
    return pred.id, out
