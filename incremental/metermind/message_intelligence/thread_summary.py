import csv
import re
import string
from pathlib import Path

import numpy as np
import pandas as pd

from config import constants
from metermind.message_intelligence.attention import attention_weights
from metermind.message_intelligence.text_cleaning import _message_column, clean_message

SENTENCE_END_PATTERN = re.compile(r"(?<=[.!?])\s+")
SHORTEST_SENTENCE_CHARACTERS = 25

THREAD_COLUMN_CANDIDATES = ("thread_id", "thread", "conversation_id")
TURN_COLUMN_CANDIDATES = ("turn_number", "turn", "turn_index", "position", "sent_at")
THREAD_SUMMARY_FIELDS = ("thread_id", "turns", "summary", "not_summarised_because")


class UnreadableThread(Exception):
    pass


def split_sentences(thread_text):
    sentences = []
    for fragment in SENTENCE_END_PATTERN.split(str(thread_text)):
        settled = " ".join(fragment.split())
        if len(settled) >= SHORTEST_SENTENCE_CHARACTERS:
            sentences.append(settled)
    return sentences


def _words(sentence):
    settled = (word.lower().strip(string.punctuation) for word in sentence.split())
    return [word for word in settled if word]


def sentence_matrix(sentences):
    worded = [_words(sentence) for sentence in sentences]
    vocabulary = sorted({word for words in worded for word in words})
    position = {word: column for column, word in enumerate(vocabulary)}
    matrix = np.zeros((len(sentences), len(vocabulary)), dtype=float)
    for row, words in enumerate(worded):
        for word in words:
            matrix[row, position[word]] += 1.0
    return matrix


def score_sentences(sentences):
    if len(sentences) < 2:
        raise UnreadableThread(
            "a thread needs at least two sentences for one to be compared with another"
        )
    matrix = sentence_matrix(sentences)
    weights = attention_weights(matrix, matrix)
    # How much attention each sentence draws from the others, not from itself.
    return weights.sum(axis=0) - np.diag(weights)


def summarise_thread(thread_text, sentence_count=None):
    if sentence_count is None:
        sentence_count = constants.SUMMARY_SENTENCE_COUNT
    sentences = split_sentences(thread_text)
    if not sentences:
        raise UnreadableThread(
            f"the thread carries no sentence of {SHORTEST_SENTENCE_CHARACTERS} "
            f"characters or more"
        )
    if len(sentences) <= sentence_count:
        return " ".join(sentences)
    scores = score_sentences(sentences)
    strongest = np.argsort(-scores, kind="stable")[:sentence_count]
    return " ".join(sentences[position] for position in sorted(strongest))


def _first_present(frame, candidates):
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    return None


def write_thread_summaries(threads_path, summaries_path):
    turns = pd.read_csv(threads_path)
    thread_column = _first_present(turns, THREAD_COLUMN_CANDIDATES)
    turn_column = _first_present(turns, TURN_COLUMN_CANDIDATES)
    text_column = _message_column(turns)

    rows = []
    summarised = 0
    for thread_id, thread_turns in turns.groupby(thread_column, sort=True):
        if turn_column is not None:
            thread_turns = thread_turns.sort_values(turn_column, kind="stable")
        thread_text = " ".join(clean_message(turn) for turn in thread_turns[text_column])
        row = {"thread_id": thread_id, "turns": int(len(thread_turns)),
               "summary": "", "not_summarised_because": ""}
        try:
            row["summary"] = summarise_thread(thread_text)
            summarised += 1
        except UnreadableThread as error:
            row["not_summarised_because"] = str(error)
        rows.append(row)

    path = Path(summaries_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(THREAD_SUMMARY_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    return {
        "threads": len(rows),
        "summarised": summarised,
        "not summarised": len(rows) - summarised,
    }


if __name__ == "__main__":
    counts = write_thread_summaries(
        constants.MESSAGE_THREADS_PATH, constants.THREAD_SUMMARIES_PATH
    )
    print(f"written: {counts}")
