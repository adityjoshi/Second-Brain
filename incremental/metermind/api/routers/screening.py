import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from config import constants
from metermind.api import schemas
from metermind.api.access_control import require_signed_in
from metermind.core.entities import create_service_connection
from metermind.core.exceptions import UnsupportedCategoryError
from metermind.exception_models.baseline_model import load_model
from metermind.exception_models.champion_model import predict_with_rule
from metermind.exception_models.feature_engineering import widen_readings
from metermind.exception_models.feature_pipeline import modelling_columns

router = APIRouter(tags=["screening"])
champion_model_path = constants.CHAMPION_MODEL_PATH
operating_rule_path = constants.OPERATING_RULE_PATH
loaded_champion = {}


def load_champion_once():
    if "model" not in loaded_champion or "rule" not in loaded_champion:
        model_file = Path(champion_model_path)
        rule_file = Path(operating_rule_path)
        if not model_file.is_file() or not rule_file.is_file():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="no champion has been fitted yet, so readings cannot be screened",
            )
        model = load_model(model_file)
        rule = json.loads(rule_file.read_text(encoding="utf-8"))
        loaded_champion["model"] = model
        loaded_champion["rule"] = rule
    return loaded_champion["model"], loaded_champion["rule"]


def _request_as_record(submitted_reading):
    if hasattr(submitted_reading, "model_dump"):
        return submitted_reading.model_dump()
    return submitted_reading.dict()


def _class_labels(model):
    if hasattr(model, "classes_"):
        return [str(label) for label in model.classes_]
    return [str(label) for label in model.named_steps["decide"].classes_]


@router.post("/screening", response_model=schemas.ScreeningReply)
def screen_reading(
    submitted_reading: schemas.ScreeningRequest,
    carried=Depends(require_signed_in),
):
    record = _request_as_record(submitted_reading)
    try:
        create_service_connection(record)
    except UnsupportedCategoryError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    model, rule = load_champion_once()
    widened = widen_readings(pd.DataFrame([record]))
    columns = widened[list(modelling_columns(True))]
    decided = predict_with_rule(
        model, columns, rule["tamper_floor"], rule["fault_floor"]
    )[0]
    if decided not in constants.EXCEPTION_CLASSES:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"the champion named a class the platform does not publish: {decided}",
        )

    confidences = model.predict_proba(columns)[0]
    confidence = float(confidences[_class_labels(model).index(decided)])
    return schemas.ScreeningReply(
        account_number=submitted_reading.account_number,
        billing_period=submitted_reading.billing_period,
        exception_class=decided,
        confidence=round(confidence, constants.MEASUREMENT_DECIMAL_PLACES),
        goes_to=Path(constants.QUEUE_FILE_PATHS[decided]).name,
    )
