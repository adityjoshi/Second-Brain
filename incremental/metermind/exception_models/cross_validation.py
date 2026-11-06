import csv
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from config import constants
from metermind.exception_models.baseline_model import build_baseline_model, split_readings
from metermind.exception_models.feature_pipeline import build_feature_pipeline
from metermind.exception_models.tree_models import (
    build_decision_tree_model,
    build_random_forest_model,
)

CROSS_VALIDATION_FIELDS = ("model", "fold", "accuracy")


def build_support_vector_model(class_weight=None, widened=False):
    try:
        decide = LinearSVC(
            C=constants.SUPPORT_VECTOR_REGULARISATION,
            random_state=constants.MODEL_SEED,
            class_weight=class_weight,
            dual=False,
            max_iter=10000,
        )
    except TypeError:
        decide = LinearSVC(
            C=constants.SUPPORT_VECTOR_REGULARISATION,
            random_state=constants.MODEL_SEED,
            class_weight=class_weight,
            max_iter=10000,
        )
    return Pipeline(
        steps=[
            ("prepare", build_feature_pipeline(widened=widened)),
            ("decide", decide),
        ]
    )


def every_candidate_model(class_weight=None, widened=False):
    return {
        "baseline": build_baseline_model(class_weight=class_weight, widened=widened),
        "decision_tree": build_decision_tree_model(
            class_weight=class_weight, widened=widened
        ),
        "random_forest": build_random_forest_model(
            class_weight=class_weight, widened=widened
        ),
        "support_vector": build_support_vector_model(
            class_weight=class_weight, widened=widened
        ),
    }


def cross_validate_models(
    fitting_columns, fitting_classes, folds=None, widened=False, names=None
):
    if folds is None:
        folds = constants.CROSS_VALIDATION_FOLDS
    splitter = StratifiedKFold(
        n_splits=folds,
        shuffle=True,
        random_state=constants.MODEL_SEED,
    )
    candidates = every_candidate_model(widened=widened)
    if names is not None:
        candidates = {name: candidates[name] for name in names}
    scored = {}
    for name, model in candidates.items():
        scores = cross_val_score(
            model,
            fitting_columns,
            fitting_classes,
            cv=splitter,
            n_jobs=1,
        )
        scored[name] = [float(score) for score in scores]
    return scored


def fold_spread(fold_scores):
    if not fold_scores:
        return 0.0
    return float(max(fold_scores) - min(fold_scores))


def write_cross_validation(scored, where):
    path = Path(where)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CROSS_VALIDATION_FIELDS))
        writer.writeheader()
        for model_name, scores in scored.items():
            for fold_number, accuracy in enumerate(scores, start=1):
                writer.writerow(
                    {
                        "model": model_name,
                        "fold": fold_number,
                        "accuracy": accuracy,
                    }
                )
    return path


if __name__ == "__main__":
    book = pd.read_csv(constants.CLEAN_READING_BOOK_PATH)
    fitting_columns, _, fitting_classes, _ = split_readings(book)
    scored = cross_validate_models(fitting_columns, fitting_classes)
    write_cross_validation(scored, constants.CROSS_VALIDATION_PATH)
    for name, scores in scored.items():
        print(
            f"{name:16} mean {float(np.mean(scores)):.4f}  "
            f"spread {fold_spread(scores):.4f}"
        )
