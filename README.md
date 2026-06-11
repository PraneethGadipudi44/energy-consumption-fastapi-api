# Energy Consumption Insights API

This project exposes a simple FastAPI endpoint that returns a predicted energy consumption value based on basic bill input data.

The API accepts:

- `consumption_per_day`
- `month_of_bill`

It loads a serialized model artifact, makes a prediction for the next month, and returns both the predicted consumption and a short interpretation message.

## Files in this repository

- `main.py` — FastAPI application
- `artifacts/energy_consumption_model.joblib` — packaged model artifact used by the API
- `README.md` — instructions to run and test the service

## What the API does

The API:

- validates incoming JSON using Pydantic
- loads the model artifact on startup/use
- exposes a prediction endpoint
- returns a predicted next-month consumption value in kWh
- returns a readable message along with the prediction
- returns a validation error response for invalid input

## Endpoints

### Health check

```http
GET /health
