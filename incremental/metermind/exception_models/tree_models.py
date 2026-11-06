import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import recall_score
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from config import constants
from metermind.exception_models.baseline_model import (
    EXCEPTION_CLASSES,
    save_model,
    score_exception_model,
    split_readings,
)
from metermind.exception_models.feature_pipeline import build_feature_pipeline


def build_decision_tree_model(class_weight=None, widened=False):
    return Pipeline(
        steps=[
            ("prepare", build_feature_pipeline(widened=widened)),
            (
                "decide",
                DecisionTreeClassifier(
                    max_depth=constants.DECISION_TREE_DEPTH_LIMIT,
                    random_state=constants.MODEL_SEED,
                    class_weight=class_weight,
                ),
            ),
        ]
    )


def build_random_forest_model(class_weight=None, widened=False):
    return Pipeline(
        steps=[
            ("prepare", build_feature_pipeline(widened=widened)),
            (
                "decide",
                RandomForestClassifier(
                    n_estimators=constants.RANDOM_FOREST_TREE_COUNT,
                    max_depth=constants.RANDOM_FOREST_DEPTH_LIMIT,
                    random_state=constants.MODEL_SEED,
                    class_weight=class_weight,
                    n_jobs=1,
                ),
            ),
        ]
    )


def train_decision_tree(
    fitting_columns, fitting_classes, class_weight=None, widened=False
):
    model = build_decision_tree_model(class_weight=class_weight, widened=widened)
    model.fit(fitting_columns, fitting_classes)
    return model


def train_random_forest(
    fitting_columns, fitting_classes, class_weight=None, widened=False
):
    model = build_random_forest_model(class_weight=class_weight, widened=widened)
    model.fit(fitting_columns, fitting_classes)
    return model


def compare_class_weighting(
    fitting_columns, held_out_columns, fitting_classes, held_out_classes
):
    # Shallower than the published forest. At full depth both weightings already
    # fit the rare classes, so the weights have nothing left to lift.
    report = {}
    for label, weight in (("unweighted", None), ("balanced", "balanced")):
        model = Pipeline(
            steps=[
                ("prepare", build_feature_pipeline(widened=False)),
                (
                    "decide",
                    RandomForestClassifier(
                        n_estimators=50,
                        max_depth=8,
                        random_state=constants.MODEL_SEED,
                        class_weight=weight,
                        n_jobs=1,
                    ),
                ),
            ]
        )
        model.fit(fitting_columns, fitting_classes)
        predicted = model.predict(held_out_columns)
        recalls = recall_score(
            held_out_classes,
            predicted,
            labels=list(EXCEPTION_CLASSES),
            average=None,
            zero_division=0,
        )
        recall_by_class = {
            exception_class: float(score)
            for exception_class, score in zip(EXCEPTION_CLASSES, recalls)
        }
        report[label] = {
            "recall_by_class": recall_by_class,
            "lowest_recall": min(recall_by_class.values()),
        }
    return report


if __name__ == "__main__":
    book = pd.read_csv(constants.CLEAN_READING_BOOK_PATH)
    fitting_columns, held_out_columns, fitting_classes, held_out_classes = (
        split_readings(book)
    )
    tree = train_decision_tree(fitting_columns, fitting_classes)
    forest = train_random_forest(fitting_columns, fitting_classes)
    tree_path = save_model(tree, constants.DECISION_TREE_MODEL_PATH)
    forest_path = save_model(forest, constants.RANDOM_FOREST_MODEL_PATH)
    tree_score = score_exception_model(tree, held_out_columns, held_out_classes)
    forest_score = score_exception_model(forest, held_out_columns, held_out_classes)
    print(f"{tree_path} {tree_score['accuracy']:.4f}")
    print(f"{forest_path} {forest_score['accuracy']:.4f}")
