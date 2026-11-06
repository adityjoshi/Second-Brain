import csv
import json
from datetime import date
from pathlib import Path

import pandas as pd

from config import constants
from metermind.message_intelligence.llm_client import LanguageModelError
from metermind.retrieval.document_loader import read_manifest
from metermind.retrieval.grounded_answer import UngroundedAnswer, answer_from_chunks
from metermind.retrieval.vector_store import (
    load_embedder,
    open_tariff_store,
    search_tariff,
    search_with_filter,
)

FILTERED_ANSWER_FIELDS = ("question_id", "question", "consumer_category", "billing_period",
                          "order_in_force", "answer", "citations", "refused_because")
DEMONSTRATION_QUESTION = "What is the fixed charge on a domestic connection?"
EVALUATION_QUESTIONS_ANSWERED = 5
JOINED_BY = ";"


class NoOrderInForce(Exception):
    pass


def _as_date(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in ("none", "null", "nan"):
        return None
    return pd.to_datetime(text).date()


def _period_start(billing_period):
    year, month = str(billing_period).strip().split("-")[:2]
    return date(int(year), int(month), 1)


def _category_matches(order_category, consumer_category):
    asked = str(consumer_category).strip().lower()
    names = {asked}
    code = constants.TARIFF_CODE_BY_CATEGORY.get(asked)
    if code:
        names.update({code.lower(), code.replace("-", "").lower()})
    return str(order_category).strip().lower() in names


def order_in_force(manifest, consumer_category, billing_period):
    start = _period_start(billing_period)
    for order in manifest:
        if not _category_matches(order.get("consumer_category"), consumer_category):
            continue
        effective_from = _as_date(order.get("effective_from"))
        effective_to = _as_date(order.get("effective_to"))
        if effective_from is not None and start < effective_from:
            continue
        if effective_to is not None and start > effective_to:
            continue
        return order
    raise NoOrderInForce(
        f"no {consumer_category} order was in force in {billing_period}; answering from an "
        f"order that had ceased to have effect would be worse than not answering"
    )


def filtered_search(collection, question, embedder, consumer_category, billing_period,
                    manifest=None, result_count=constants.SEARCH_RESULT_COUNT):
    if manifest is None:
        manifest = read_manifest()
    order = order_in_force(manifest, consumer_category, billing_period)
    conditions = {"order_id": order["order_id"]}
    if order.get("consumer_category"):
        conditions["consumer_category"] = order["consumer_category"]
    return search_with_filter(collection, question, embedder, conditions, result_count)


def write_filtered_answers(questions, collection, embedder, answers_path, manifest=None,
                           cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    if manifest is None:
        manifest = read_manifest()
    rows = []
    answered = 0
    for question in questions:
        asked = question["question"]
        category = question.get("consumer_category", "")
        period = question.get("billing_period", "")
        row = {"question_id": question.get("question_id"), "question": asked,
               "consumer_category": category, "billing_period": period,
               "order_in_force": "", "answer": "", "citations": "", "refused_because": ""}
        try:
            row["order_in_force"] = order_in_force(manifest, category, period)["order_id"]
            chunks = filtered_search(collection, asked, embedder, category, period, manifest)
            grounded = answer_from_chunks(asked, chunks, cache_path)
            row["answer"] = grounded["answer"]
            row["citations"] = JOINED_BY.join(grounded["citations"])
            if grounded["answer"].strip() == constants.UNANSWERABLE_REPLY:
                row["refused_because"] = "the order in force does not answer the question"
            else:
                answered += 1
        except (NoOrderInForce, UngroundedAnswer, LanguageModelError, ValueError) as error:
            row["refused_because"] = str(error)
        rows.append(row)

    path = Path(answers_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FILTERED_ANSWER_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    return {"questions": len(rows), "answered": answered, "refused": len(rows) - answered}


def _orders_reached(results):
    return sorted({result["order_id"] for result in results})


if __name__ == "__main__":
    store = open_tariff_store()
    embedder = load_embedder()
    manifest = read_manifest()
    everywhere = search_tariff(store, DEMONSTRATION_QUESTION, embedder)
    print(f"nearest, any order at all : {_orders_reached(everywhere)}")
    narrowed = filtered_search(store, DEMONSTRATION_QUESTION, embedder, "domestic", "2024-09",
                               manifest)
    print(f"nearest, domestic 2024-09 : {_orders_reached(narrowed)}")
    try:
        filtered_search(store, DEMONSTRATION_QUESTION, embedder, "domestic", "2019-01", manifest)
    except NoOrderInForce as refusal:
        print(f"asked about 2019-01       : {refusal}")

    evaluation = json.loads(
        Path(constants.RETRIEVAL_EVALUATION_SET_PATH).read_text(encoding="utf-8")
    )
    if isinstance(evaluation, dict):
        evaluation = evaluation.get("questions", [])
    counts = write_filtered_answers(evaluation[:EVALUATION_QUESTIONS_ANSWERED], store, embedder,
                                    constants.FILTERED_ANSWERS_PATH, manifest)
    print(f"five questions, filtered  : {counts}")
