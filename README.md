# Energy Consumption Insights API

This task exposes a simple FastAPI endpoint that accepts a small energy bill payload and
returns a predicted consumption value for the next month.

The API takes two inputs:

- `consumption_per_day`
- `month_of_bill`

It loads a serialized model artifact from the local `artifacts/` folder, makes a prediction,
and returns both the predicted kWh value and a short interpretation message.

## Files in this folder

- `main.py` - FastAPI application
- `artifacts/energy_consumption_model.joblib` - local model artifact used by the API

## Requirements

Install the required packages:

```bash
pip install fastapi uvicorn joblib pandas scikit-learn
```

## How to run the API

From this folder, run:

```bash
python -m uvicorn main:app --reload
```

Once the server starts, the API will be available at:

- `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

## Endpoints

### Health check

```http
GET /health
```

This confirms the API is running and whether the model artifact loaded successfully.

### Prediction endpoint

```http
POST /predict_consumption
```

#### Example request body

```json
{
  "consumption_per_day": 28.5,
  "month_of_bill": 6
}
```

#### Example curl command

```bash
curl -X POST "http://127.0.0.1:8000/predict_consumption" ^
  -H "Content-Type: application/json" ^
  -d "{\"consumption_per_day\": 28.5, \"month_of_bill\": 6}"
```

#### Example response

```json
{
  "predicted_consumption_kwh": 892.37,
  "month_of_bill": 6,
  "predicted_for_month": "July",
  "message": "Predicted consumption for July is 892.37 kWh, which looks higher than the current daily-use pace."
}
```

## Invalid input example

If the request body is invalid, FastAPI returns a `422` response.

Example bad request:

```json
{
  "consumption_per_day": -5,
  "month_of_bill": 13
}
```

Example error response:

```json
{
  "error": "Invalid request payload.",
  "details": [
    {
      "type": "greater_than",
      "loc": ["body", "consumption_per_day"],
      "msg": "Input should be greater than 0",
      "input": -5,
      "ctx": {"gt": 0.0}
    }
  ],
  "example": {
    "consumption_per_day": 28.5,
    "month_of_bill": 6
  }
}
```

## Notes

- The API expects `month_of_bill` to be a number from `1` to `12`.
- `consumption_per_day` should be a positive number.
- The prediction uses the packaged model artifact stored in the `artifacts` directory.
