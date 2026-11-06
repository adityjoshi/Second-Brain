import csv
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from config import constants
from metermind.exception_models.baseline_model import load_model, split_readings
from metermind.exception_models.champion_model import predict_with_rule
from metermind.exception_models.feature_engineering import widen_readings
from metermind.exception_models.feature_pipeline import modelling_columns

EXCEPTION_REPORT_FIELDS = ("exception_class", "precision", "recall", "support")
TOTAL_ROW_LABEL = "total"


def _as_text(sequence):
    return [str(label) for label in sequence]


def per_class_scores(truth, predicted):
    truth = _as_text(truth)
    predicted = _as_text(predicted)
    precision, recall, _, support = precision_recall_fscore_support(
        truth,
        predicted,
        labels=list(constants.EXCEPTION_CLASSES),
        average=None,
        zero_division=0,
    )
    return {
        exception_class: {
            "precision": float(precision[position]),
            "recall": float(recall[position]),
            "support": int(support[position]),
        }
        for position, exception_class in enumerate(constants.EXCEPTION_CLASSES)
    }


def confusion_frame(truth, predicted):
    labels = list(constants.EXCEPTION_CLASSES)
    counts = confusion_matrix(_as_text(truth), _as_text(predicted), labels=labels)
    return pd.DataFrame(counts, index=labels, columns=labels)


def write_exception_report(truth, predicted, where):
    places = constants.MEASUREMENT_DECIMAL_PLACES
    scores = per_class_scores(truth, predicted)
    weighted_precision, weighted_recall, _, _ = precision_recall_fscore_support(
        _as_text(truth),
        _as_text(predicted),
        labels=list(constants.EXCEPTION_CLASSES),
        average="weighted",
        zero_division=0,
    )
    path = Path(where)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(EXCEPTION_REPORT_FIELDS))
        writer.writeheader()
        for exception_class, figures in scores.items():
            writer.writerow(
                {
                    "exception_class": exception_class,
                    "precision": round(figures["precision"], places),
                    "recall": round(figures["recall"], places),
                    "support": figures["support"],
                }
            )
        writer.writerow(
            {
                "exception_class": TOTAL_ROW_LABEL,
                "precision": round(float(weighted_precision), places),
                "recall": round(float(weighted_recall), places),
                "support": sum(figures["support"] for figures in scores.values()),
            }
        )
    return path


if __name__ == "__main__":
    book = widen_readings(pd.read_csv(constants.CLEAN_READING_BOOK_PATH))
    _, held_out_columns, _, held_out_classes = split_readings(
        book, columns=list(modelling_columns(True))
    )
    champion = load_model(constants.CHAMPION_MODEL_PATH)
    rule_path = Path(constants.OPERATING_RULE_PATH)
    if rule_path.is_file():
        rule = json.loads(rule_path.read_text(encoding="utf-8"))
        predicted = predict_with_rule(
            champion, held_out_columns, rule["tamper_floor"], rule["fault_floor"]
        )
    else:
        predicted = _as_text(champion.predict(held_out_columns))
    with pd.option_context("display.width", 200, "display.max_columns", 10):
        print(confusion_frame(held_out_classes, predicted))
    written = write_exception_report(
        held_out_classes, predicted, constants.EXCEPTION_REPORT_PATH
    )
    print(f"written: {written}")
