import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

from config import constants
from metermind.message_intelligence.text_cleaning import _message_column, clean_messages

FITTING_ROUNDS_LIMIT = 2000
CATEGORY_COLUMN_CANDIDATES = ("category", "complaint_category")
URGENCY_COLUMN_CANDIDATES = ("urgency", "complaint_urgency")


def build_text_pipeline():
    return Pipeline(
        steps=[
            ("clean", FunctionTransformer(clean_messages, validate=False)),
            (
                "weigh",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=constants.TEXT_MINIMUM_DOCUMENT_COUNT,
                    max_features=constants.TEXT_MAXIMUM_FEATURES,
                    sublinear_tf=True,
                ),
            ),
            (
                "decide",
                LogisticRegression(
                    max_iter=FITTING_ROUNDS_LIMIT,
                    random_state=constants.MODEL_SEED,
                ),
            ),
        ]
    )


def split_complaints(corpus, label_column):
    return train_test_split(
        corpus[_message_column(corpus)],
        corpus[label_column],
        test_size=constants.HELD_OUT_SHARE,
        random_state=constants.MODEL_SEED,
        stratify=corpus[label_column],
    )


def train_category_classifier(fitting_text, fitting_labels):
    model = build_text_pipeline()
    model.fit(fitting_text, fitting_labels)
    return model


def train_urgency_classifier(fitting_text, fitting_labels):
    model = build_text_pipeline()
    model.fit(fitting_text, fitting_labels)
    return model


def classify_message(category_model, urgency_model, message):
    category = str(category_model.predict([message])[0])
    urgency = str(urgency_model.predict([message])[0])
    if category not in constants.COMPLAINT_CATEGORIES:
        raise ValueError(f"the category model named an unpublished category: {category}")
    if urgency not in constants.COMPLAINT_URGENCIES:
        raise ValueError(f"the urgency model named an unpublished urgency: {urgency}")
    return {"category": category, "urgency": urgency}


def _label_column(corpus, candidates):
    for candidate in candidates:
        if candidate in corpus.columns:
            return candidate
    raise KeyError(f"the corpus carries none of {candidates}")


if __name__ == "__main__":
    corpus = pd.read_csv(constants.COMPLAINT_MESSAGES_PATH)
    places = constants.MEASUREMENT_DECIMAL_PLACES
    scores = {}
    for name, candidates, trainer, model_path in (
        ("category", CATEGORY_COLUMN_CANDIDATES, train_category_classifier,
         constants.COMPLAINT_CATEGORY_MODEL_PATH),
        ("urgency", URGENCY_COLUMN_CANDIDATES, train_urgency_classifier,
         constants.COMPLAINT_URGENCY_MODEL_PATH),
    ):
        fitting_text, held_out_text, fitting_labels, held_out_labels = split_complaints(
            corpus, _label_column(corpus, candidates)
        )
        model = trainer(fitting_text, fitting_labels)
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)
        scores[name] = round(float(model.score(held_out_text, held_out_labels)), places)

    scores_path = Path(constants.COMPLAINT_SCORES_PATH)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
    print(scores)
