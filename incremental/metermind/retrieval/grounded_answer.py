import csv
import json
import re
from pathlib import Path

from config import constants
from metermind.message_intelligence.llm_client import (
    LanguageModelError,
    ask_model,
    read_answer,
)
from metermind.retrieval.vector_store import open_tariff_store, load_embedder, search_tariff

CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9._-]*-\d+)\]")
ANSWER_FIELDS = ("question_id", "question", "answer", "citations", "chunks_handed_over",
                 "refused_because")
ANSWER_TEMPLATE = (
    "You answer questions about electricity tariff orders.\n"
    "Use ONLY the extracts below. Do not use anything you know from elsewhere.\n"
    "Cite every extract you rely on by writing its identifier inside square brackets in your "
    "answer, and list the same identifiers under citations. "
    "Never cite an identifier that is not among the extracts.\n"
    f"If the extracts do not answer the question, answer exactly "
    f"\"{constants.UNANSWERABLE_REPLY}\" with no citations.\n"
    'Answer with JSON only, in the form {"answer": "<answer>", '
    '"citations": ["<identifier>", ...]}.\n\n'
    "Question: <<question>>\n\n"
    "Extracts:\n<<extracts>>"
)
EVALUATION_QUESTIONS_ANSWERED = 5
JOINED_BY = ";"


class UngroundedAnswer(Exception):
    pass


def check_citations(answer_text, chunks):
    handed_over = {chunk["chunk_id"] for chunk in chunks}
    cited = set(CITATION_PATTERN.findall(str(answer_text)))
    invented = sorted(cited - handed_over)
    if invented:
        raise UngroundedAnswer(
            f"the answer cites {', '.join(invented)}, which was never handed over"
        )
    return sorted(cited)


def _describe_extract(chunk):
    return (
        f"[{chunk['chunk_id']}] order {chunk.get('order_id', '')}, "
        f"section {chunk.get('section', '') or 'none'}, "
        f"in force {chunk.get('effective_from', '') or 'unknown'} to "
        f"{chunk.get('effective_to', '') or 'open'}\n{chunk['text']}"
    )


def build_answer_prompt(question, chunks):
    if not chunks:
        raise UngroundedAnswer("nothing was retrieved, so there is nothing to answer from")
    extracts = "\n\n".join(_describe_extract(chunk) for chunk in chunks)
    return (ANSWER_TEMPLATE
            .replace("<<question>>", str(question))
            .replace("<<extracts>>", extracts))


def answer_from_chunks(question, chunks, cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    said = ask_model(build_answer_prompt(question, chunks), cache_path)
    answer_key, citations_key = constants.GROUNDED_ANSWER_KEYS
    parsed = read_answer(said, constants.GROUNDED_ANSWER_KEYS)
    answer = str(parsed[answer_key])
    listed = parsed[citations_key] or []
    if isinstance(listed, str):
        listed = [listed]
    in_text = check_citations(answer, chunks)
    in_field = check_citations(" ".join(f"[{str(one).strip('[]')}]" for one in listed), chunks)
    return {"answer": answer, "citations": sorted(set(in_text) | set(in_field))}


def write_answers(questions, collection, embedder, answers_path,
                  cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    rows = []
    answered = 0
    for question in questions:
        asked = question["question"]
        row = {"question_id": question.get("question_id"), "question": asked,
               "answer": "", "citations": "", "chunks_handed_over": "",
               "refused_because": ""}
        try:
            chunks = search_tariff(collection, asked, embedder)
            row["chunks_handed_over"] = JOINED_BY.join(chunk["chunk_id"] for chunk in chunks)
            grounded = answer_from_chunks(asked, chunks, cache_path)
            row["answer"] = grounded["answer"]
            row["citations"] = JOINED_BY.join(grounded["citations"])
            if grounded["answer"].strip() == constants.UNANSWERABLE_REPLY:
                row["refused_because"] = "the extracts do not answer the question"
            else:
                answered += 1
        except (UngroundedAnswer, LanguageModelError) as error:
            row["refused_because"] = str(error)
        rows.append(row)

    path = Path(answers_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ANSWER_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    return {"questions": len(rows), "answered": answered, "refused": len(rows) - answered}


if __name__ == "__main__":
    evaluation = json.loads(
        Path(constants.RETRIEVAL_EVALUATION_SET_PATH).read_text(encoding="utf-8")
    )
    if isinstance(evaluation, dict):
        evaluation = evaluation.get("questions", [])
    print(write_answers(
        evaluation[:EVALUATION_QUESTIONS_ANSWERED],
        open_tariff_store(),
        load_embedder(),
        constants.TARIFF_ANSWERS_PATH,
    ))
