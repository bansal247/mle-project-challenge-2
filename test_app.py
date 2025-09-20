import pytest
from fastapi.testclient import TestClient
from app import app

valid_input_unseen = {
    "data": {
        "bedrooms": 4,
        "bathrooms": 1,
        "sqft_living": 1680,
        "sqft_lot": 5043,
        "floors": 1.5,
        "waterfront": 0,
        "view": 0,
        "condition": 4,
        "grade": 6,
        "sqft_above": 1680,
        "sqft_basement": 0,
        "yr_built": 1911,
        "yr_renovated": 0,
        "zipcode": 98118,
        "lat": 47.5354,
        "long": -122.273,
        "sqft_living15": 1560,
        "sqft_lot15": 5765
    }
}

valid_input_required = {
    "data": {
        "bedrooms": 4,
        "bathrooms": 1,
        "sqft_living": 1680,
        "sqft_lot": 5043,
        "floors": 1.5,
        "sqft_above": 1680,
        "sqft_basement": 0,
        "zipcode": 98118
    }
}

invalid_input_missing = {
    "data": {
        "zipcode": 98118  # missing required features
    }
}

invalid_input_extra = {
    "data": {
        "zipcode": 98118,
        "extra_feature": 123
    }
}

invalid_zipcode = {
    "data": {
        "bedrooms": 4,
        "bathrooms": 1,
        "sqft_living": 1680,
        "sqft_lot": 5043,
        "floors": 1.5,
        "sqft_above": 1680,
        "sqft_basement": 0,
        "zipcode": 0  # invalid zipcode
    }
}

# --- Parametrized tests ---
@pytest.mark.parametrize("endpoint, input_data, expected_status", [
    ("/predict_only_required", valid_input_required, 200),
    ("/predict_unseen", valid_input_unseen, 200),
    ("/predict_only_required", invalid_input_missing, 400),
    ("/predict_only_required", invalid_input_extra, 400),
    ("/predict_only_required", invalid_zipcode, 400),
])
def test_predictions(endpoint, input_data, expected_status):
    with TestClient(app) as client:
        response = client.post(endpoint, json=input_data)

        assert response.status_code == expected_status
        if expected_status == 200:
            data = response.json()
            assert "prediction" in data
            assert "metadata" in data
            assert "model_version" in data["metadata"]
            assert "prediction_time_ms" in data["metadata"]
            assert "prediction_id" in data["metadata"]

# --- Test reload_model endpoint ---
def test_reload_model():
    with TestClient(app) as client:
        response = client.post("/reload_model")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
