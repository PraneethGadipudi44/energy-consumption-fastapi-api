from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


APP_ROOT = Path(__file__).resolve().parent
MODEL_PATH = APP_ROOT / "artifacts" / "energy_consumption_model.joblib"
MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


app = FastAPI(
    title="Energy Consumption Insights API",
    description="Simple FastAPI service that predicts next-month energy consumption.",
    version="1.0.0",
)


class EnergyBillInput(BaseModel):
    consumption_per_day: float = Field(
        ...,
        gt=0,
        le=5000,
        description="Average daily energy consumption in kWh.",
    )
    month_of_bill: int = Field(
        ...,
        ge=1,
        le=12,
        description="Month number of the current bill, from 1 to 12.",
    )


class ConsumptionPrediction(BaseModel):
    predicted_consumption_kwh: float
    month_of_bill: int
    predicted_for_month: str
    message: str


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request payload.",
            "details": exc.errors(),
            "example": {
                "consumption_per_day": 28.5,
                "month_of_bill": 6,
            },
        },
    )


@lru_cache(maxsize=1)
def load_model_artifact() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {MODEL_PATH}. "
            "Make sure the artifact file is present before starting the API."
        )

    artifact = joblib.load(MODEL_PATH)
    if "model" not in artifact:
        raise ValueError("Loaded artifact is missing the 'model' entry.")
    return artifact


def next_month_name(current_month: int) -> str:
    next_month = 1 if current_month == 12 else current_month + 1
    return MONTH_NAMES[next_month]


def build_message(prediction_kwh: float, consumption_per_day: float, month_of_bill: int) -> str:
    current_month_estimate = consumption_per_day * 30.0
    if prediction_kwh >= current_month_estimate * 1.05:
        trend = "higher than the current daily-use pace"
    elif prediction_kwh <= current_month_estimate * 0.95:
        trend = "lower than the current daily-use pace"
    else:
        trend = "roughly in line with the current daily-use pace"

    return (
        f"Predicted consumption for {next_month_name(month_of_bill)} is "
        f"{prediction_kwh:.2f} kWh, which looks {trend}."
    )


@app.get("/health")
def health_check() -> dict[str, Any]:
    try:
        artifact = load_model_artifact()
        return {
            "status": "ok",
            "model_loaded": True,
            "model_type": artifact.get("model_type", "unknown"),
            "model_path": str(MODEL_PATH),
        }
    except Exception as exc:  # pragma: no cover - operational path
        return {
            "status": "error",
            "model_loaded": False,
            "error": str(exc),
        }


@app.post("/predict_consumption", response_model=ConsumptionPrediction)
def predict_consumption(payload: EnergyBillInput) -> ConsumptionPrediction:
    try:
        artifact = load_model_artifact()
        model = artifact["model"]
        features = artifact.get("features", ["consumption_per_day", "month_of_bill"])

        input_frame = pd.DataFrame(
            [
                {
                    "consumption_per_day": payload.consumption_per_day,
                    "month_of_bill": payload.month_of_bill,
                }
            ]
        )
        prediction = float(model.predict(input_frame[features])[0])
        prediction = round(max(prediction, 0.0), 2)

        return ConsumptionPrediction(
            predicted_consumption_kwh=prediction,
            month_of_bill=payload.month_of_bill,
            predicted_for_month=next_month_name(payload.month_of_bill),
            message=build_message(
                prediction_kwh=prediction,
                consumption_per_day=payload.consumption_per_day,
                month_of_bill=payload.month_of_bill,
            ),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        ) from exc
