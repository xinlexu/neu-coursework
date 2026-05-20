import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .deps import get_db, init_db
from .schemas import TrainRequest, TrainResponse, PredictRequest, PredictResponse
from .ml.trainer import train_once
from .ml.predict import predict_once
from .data_bootstrap import ensure_mpg_csv
from .models_db import Experiment, Prediction

app = FastAPI(title="Auto MPG API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_PATH = DATA_DIR / "auto-mpg.csv"

@app.on_event("startup")
def on_startup():
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set")
    init_db()
    ensure_mpg_csv(DATA_DIR)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/train", response_model=TrainResponse)
def train(req: TrainRequest, db: Session = Depends(get_db)):
    exp_id, metrics = train_once(db, CSV_PATH, req.model_type, req.params)
    return {"experiment_id": exp_id, "metrics": metrics}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    try:
        pred_id, out = predict_once(db, DATA_DIR, req.experiment_id, req.input)
        return {"prediction_id": pred_id, "output": out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/experiments")
def list_experiments(db: Session = Depends(get_db)):
    rows = db.query(Experiment).order_by(Experiment.id.desc()).all()
    return [{"id": r.id, "model_type": r.model_type, "params": r.params, "metrics": r.metrics, "created_at": r.created_at.isoformat()} for r in rows]

@app.get("/experiments/{exp_id}")
def get_experiment(exp_id: int, db: Session = Depends(get_db)):
    r = db.query(Experiment).filter(Experiment.id == exp_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": r.id, "model_type": r.model_type, "params": r.params, "metrics": r.metrics, "created_at": r.created_at.isoformat()}

@app.get("/predictions")
def list_predictions(experiment_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Prediction).order_by(Prediction.id.desc())
    if experiment_id is not None:
        q = q.filter(Prediction.experiment_id == experiment_id)
    rows = q.all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "experiment_id": r.experiment_id,
            "input": r.input,
            "output": r.output,
            "created_at": r.created_at.isoformat()
        })
    return out
