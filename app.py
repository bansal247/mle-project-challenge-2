import json
import pickle
import threading
from pathlib import Path
from typing import Tuple, Dict, Any
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic import BaseModel, model_validator
import pandas as pd

app = FastAPI(title="House Price Prediction Service")

MODEL_DIR = Path("model")
MODEL_PATH = MODEL_DIR / "model.pkl"
ALL_FEATURES_PATH = MODEL_DIR / "all_features.json"
DEMOGRAPHICS_PATH = Path("data/zipcode_demographics.csv")

model_lock = threading.Lock()
model, all_features, demographics = None, None, None

class PredictionInput(BaseModel):
    data: Dict[str, Any]

    @model_validator(mode="before")
    def validate_data(cls, values):
        """Ensure `data` is a JSON object."""
        data = values.get("data")
        if not isinstance(data, dict):
            raise ValueError("`data` must be a JSON object")
        return values


def validate_input_features(input_data: Dict[str, Any], expected_features: list):
    """Ensure request JSON matches expected features."""
    missing = [f for f in expected_features if f not in input_data]
    extra = [f for f in input_data if f not in expected_features]

    if missing:
        raise ValueError(f"Missing features: {missing}")
    if extra:
        raise ValueError(f"Unexpected features: {extra}")

def load_model():
    """Load and return trained ML model."""
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def load_features():
    """Load and return list of model features from JSON file."""
    with open(ALL_FEATURES_PATH, "r") as f:
        return json.load(f)

def load_demographics():
    """Load and return demographics data."""
    return pd.read_csv(DEMOGRAPHICS_PATH, dtype={'zipcode': str})

def load_all() -> Tuple:
    with model_lock:
        model = load_model()
        features = load_features()
        demographics = load_demographics()
    return model, features, demographics
            
def get_model_version() -> str:
    """Return a string representing the current model version."""
    return MODEL_PATH.stat().st_mtime_ns.__str__()

def build_metadata(start_time: float) -> dict:
    """Build metadata for a prediction response."""
    return { ## Can add confidence score
        "model_version": get_model_version(),
        "model_type": type(model).__name__,
        "prediction_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prediction_id": str(uuid.uuid4())
    }


@app.on_event("startup")
def startup_event():
    global model, all_features, demographics
    try:
        model, all_features, demographics = load_all()
    except Exception as e:
        model = None
        all_features = None
        demographics = None
        raise HTTPException(status_code=500, detail=str(e))

def make_prediction(input_data: dict, feature_set: list):
    global model, all_features

    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    if all_features is None:
        raise HTTPException(status_code=500, detail="Model features not loaded")

    # Validate input features
    validate_input_features(input_data, feature_set)

    # Create DataFrame
    input_df = pd.DataFrame([input_data], columns=all_features['model_required_features'])
    input_df['zipcode'] = input_df['zipcode'].astype(int).astype(str)

    if demographics[demographics['zipcode'] == input_df['zipcode'].astype(int).astype(str).values[0]].shape[0]==0:
        raise HTTPException(status_code=400, detail=f"Zipcode {input_df['zipcode'].values[0]} not found in demographics data")    
    
    # Merge with demographics
    merged_df = input_df.merge(demographics, how="left", on="zipcode").drop(columns="zipcode")

    # Predict
    prediction = model.predict(merged_df)[0]
    return prediction

@app.post("/predict_unseen")
def predict_unseen(input_data: PredictionInput):
    global all_features
    start_time = time.time()
    try:
        prediction = make_prediction(input_data.data, all_features['future_unseen_features'])
        metadata = build_metadata(start_time)
        return {
            "prediction": prediction,
            "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict_only_required")
def predict_required(input_data: PredictionInput):
    global all_features
    start_time = time.time()
    try:
        prediction = make_prediction(input_data.data, all_features['model_required_features'])
        metadata = build_metadata(start_time)
        return {
            "prediction": prediction,
            "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reload_model")
def reload_model():
    global model, all_features, demographics
    try:
        previous_model = model
        previous_features = all_features
        previous_demographics = demographics
        model, all_features, demographics = load_all()
        return {"status": "success", "message": "Model reloaded"}
    except Exception as e:
        model = previous_model
        all_features = previous_features
        demographics = previous_demographics
        raise HTTPException(status_code=500, detail=str(e)+" | Model reload failed, previous model retained")