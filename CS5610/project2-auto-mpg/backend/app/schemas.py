from typing import Dict, Any, Literal
from pydantic import BaseModel

ModelType = Literal["linear", "random_forest"]

class TrainRequest(BaseModel):
    model_type: ModelType
    params: Dict[str, Any] = {}

class TrainResponse(BaseModel):
    experiment_id: int
    metrics: Dict[str, float]

class PredictRequest(BaseModel):
    experiment_id: int
    input: Dict[str, float]

class PredictResponse(BaseModel):
    prediction_id: int
    output: Dict[str, float | list]
