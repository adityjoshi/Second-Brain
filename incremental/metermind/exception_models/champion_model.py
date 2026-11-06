import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import constants
from metermind.exception_models.baseline_model import save_model, split_readings
from metermind.exception_models.cross_validation import (
    cross_validate_models,
    every_candidate_model,
)
from metermind.exception_models.feature_engineering import widen_readings
from metermind.exception_models.feature_pipeline import (
    DERIVED_NUMBER_COLUMNS,
    modelling_columns,
)

COST_MATRIX = {
    "genuine_high_usage": {
        "genuine_high_usage": 0.0,
        "estimated_read": 1.0,
        "meter_fault": 1.5,
        "tamper_suspected": 25.0,
        "tariff_mismatch": 2.0,
    },
    "estimated_read": {
        "genuine_high_usage": 1.0,
        "estimated_read": 0.0,
        "meter_fault": 1.0,
        "tamper_suspected": 3.0,
        "tariff_mismatch": 1.0,
    },
    "meter_fault": {
        "genuine_high_usage": 1.5,
        "estimated_read": 1.0,
        "meter_fault": 0.0,
        "tamper_suspected": 4.0,
        "tariff_mismatch": 1.5,
    },
    "tamper_suspected": {
        "genuine_high_usage": 4.0,
        "estimated_read": 2.0,
        "meter_fault": 2.0,
        "tamper_suspected": 0.0,
        "tariff_mismatch": 2.0,
    },
    "tariff_mismatch": {
        "genuine_high_usage": 2.0,
        "estimated_read": 1.0,
        "meter_fault": 1.5,
        "tamper_suspected": 5.0,
        "tariff_mismatch": 0.0,
    },
}

TAMPER_FLOORS = (0.0, 0.4, 0.5, 0.6, 0.7, 0.8)
FAULT_FLOORS = (0.0, 0.4, 0.5, 0.6, 0.7, 0.8)

MODELS_THAT_REPORT_CONFIDENCE = ("baseline", "decision_tree", "random_forest")


def choose_champion(fitting_columns, fitting_classes, folds=None):
    widened = set(DERIVED_NUMBER_COLUMNS).issubset(set(fitting_columns.columns))
    # Only the families that can carry an operating rule are scored for the champion.
    scored = cross_validate_models(
        fitting_columns,
        fitting_classes,
        folds=folds,
        widened=widened,
        names=MODELS_THAT_REPORT_CONFIDENCE,
    )
    means = {
        name: float(np.mean(scored[name]))
        for name in MODELS_THAT_REPORT_CONFIDENCE
    }
    winner = max(means, key=means.get)
    return winner, means


def expected_cost(truth, predicted):
    truth = list(truth)
    predicted = list(predicted)
    if len(truth) != len(predicted):
        raise ValueError("truth and predicted must be the same length")
    if not truth:
        return 0.0
    total = 0.0
    for true_class, predicted_class in zip(truth, predicted):
        total += COST_MATRIX[str(true_class)][str(predicted_class)]
    return float(total / len(truth))


def _class_labels(model):
    if hasattr(model, "classes_"):
        return [str(label) for label in model.classes_]
    return [str(label) for label in model.named_steps["decide"].classes_]


def predict_with_rule(model, columns, tamper_floor, fault_floor):
    floors = {
        "tamper_suspected": float(tamper_floor),
        "meter_fault": float(fault_floor),
    }
    # Floors of zero must reproduce the model's unaided answer exactly.
    unaided = [str(label) for label in model.predict(columns)]
    if floors["tamper_suspected"] <= 0.0 and floors["meter_fault"] <= 0.0:
        return unaided

    probabilities = model.predict_proba(columns)
    class_labels = _class_labels(model)
    decisions = []
    for row in probabilities:
        ranked = list(np.argsort(row)[::-1])
        leading_index = ranked[0]
        chosen = class_labels[leading_index]
        if chosen in floors and row[leading_index] < floors[chosen]:
            chosen = class_labels[ranked[1]]
        decisions.append(str(chosen))
    return decisions


def choose_operating_rule(model, held_out_columns, held_out_classes):
    best = None
    for tamper_floor in TAMPER_FLOORS:
        for fault_floor in FAULT_FLOORS:
            predicted = predict_with_rule(
                model, held_out_columns, tamper_floor, fault_floor
            )
            cost = expected_cost(held_out_classes, predicted)
            candidate = {
                "tamper_floor": float(tamper_floor),
                "fault_floor": float(fault_floor),
                "expected_cost": float(cost),
            }
            if best is None or candidate["expected_cost"] < best["expected_cost"]:
                best = candidate
    return best


def save_champion(model, rule, model_path, rule_path):
    places = constants.MEASUREMENT_DECIMAL_PLACES
    written_model = save_model(model, model_path)
    rounded_rule = {
        "tamper_floor": round(float(rule["tamper_floor"]), places),
        "fault_floor": round(float(rule["fault_floor"]), places),
        "expected_cost": round(float(rule["expected_cost"]), places),
    }
    path = Path(rule_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rounded_rule, indent=2), encoding="utf-8")
    return written_model, path


if __name__ == "__main__":
    book = widen_readings(pd.read_csv(constants.CLEAN_READING_BOOK_PATH))
    fitting_columns, held_out_columns, fitting_classes, held_out_classes = (
        split_readings(book, columns=list(modelling_columns(True)))
    )
    chosen_name, means = choose_champion(fitting_columns, fitting_classes)
    print(
        "only the families that report a confidence can carry an operating rule, "
        "so the support vector\nis not considered:"
    )
    print(f"chosen: {chosen_name} {means}")

    model = every_candidate_model(widened=True)[chosen_name]
    model.fit(fitting_columns, fitting_classes)
    unaided = expected_cost(held_out_classes, model.predict(held_out_columns))
    print(f"argmax cost: {unaided:.4f}")
    rule = choose_operating_rule(model, held_out_columns, held_out_classes)
    save_champion(
        model, rule, constants.CHAMPION_MODEL_PATH, constants.OPERATING_RULE_PATH
    )
    print(f"rule: {rule}")
