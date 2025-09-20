## STRESS TESTING SCRIPT FOR FASTAPI APP USING LOCUST

from locust import HttpUser, task, between

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

class PredictionUser(HttpUser):
    wait_time = between(1, 3)

    @task(30)  # higher weight for valid predictions
    def predict_required(self):
        self.client.post("/predict_only_required",
                         json=valid_input_required)

    @task(30)
    def predict_unseen(self):
        self.client.post("/predict_unseen",
                         json=valid_input_unseen)

    # --- Reload model endpoint (optional, less frequent) ---
    @task(1)
    def reload_model(self):
        self.client.post("/reload_model")
