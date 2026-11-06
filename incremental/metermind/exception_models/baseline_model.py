import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config import constants
from metermind.exception_models.feature_pipeline import (
    EXCEPTION_COLUMN,
    build_feature_pipeline,
    modelling_columns,
)

EXCEPTION_CLASSES = constants.EXCEPTION_CLASSES
FITTING_ROUNDS_LIMIT = 2000


def build_baseline_model(class_weight=None, widened=False):
    return Pipeline(
        steps=[
            ("prepare", build_feature_pipeline(widened=widened)),
            (
                "decide",
                LogisticRegression(
                    max_iter=FITTING_ROUNDS_LIMIT,
                    random_state=constants.MODEL_SEED,
                    class_weight=class_weight,
                ),
            ),
        ]
    )


def split_readings(book, columns=None):
    if columns is None:
        columns = modelling_columns(False)
    features = book[list(columns)]
    classes = book[EXCEPTION_COLUMN]
    return train_test_split(
        features,
        classes,
        test_size=constants.HELD_OUT_SHARE,
        random_state=constants.MODEL_SEED,
        stratify=classes,
    )


def train_baseline_model(fitting_columns, fitting_classes, class_weight=None, widened=False):
    model = build_baseline_model(class_weight=class_weight, widened=widened)
    model.fit(fitting_columns, fitting_classes)
    return model


def score_exception_model(model, held_out_columns, held_out_classes):
    predicted = model.predict(held_out_columns)
    accuracy = float(accuracy_score(held_out_classes, predicted))
    per_class = classification_report(
        held_out_classes,
        predicted,
        labels=list(EXCEPTION_CLASSES),
        output_dict=True,
        zero_division=0,
    )
    return {"accuracy": accuracy, "per_class": per_class}


def save_model(model, model_path):
    path = Path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(model_path):
    return joblib.load(model_path)


def predict_exception(model, readings):
    columns = []
    for _, _, chosen in model.named_steps["prepare"].transformers:
        columns.extend(list(chosen))
    predicted = model.predict(readings[list(columns)])
    return [str(label) for label in predicted]


if __name__ == "__main__":
    book = pd.read_csv(constants.CLEAN_READING_BOOK_PATH)
    fitting_columns, held_out_columns, fitting_classes, held_out_classes = (
        split_readings(book)
    )
    model = train_baseline_model(fitting_columns, fitting_classes)
    scores = score_exception_model(model, held_out_columns, held_out_classes)
    save_model(model, constants.BASELINE_MODEL_PATH)
    scores_path = Path(constants.BASELINE_SCORES_PATH)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
    print(f"accuracy: {scores['accuracy']:.4f}")
