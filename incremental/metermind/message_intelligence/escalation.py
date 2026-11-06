import csv
from datetime import date
from pathlib import Path

import joblib
import pandas as pd

from config import constants
from metermind.message_intelligence.batch_pipeline import MessageFailure, run_batch
from metermind.message_intelligence.llm_client import (
    LanguageModelError,
    ask_model,
    read_answer,
)
from metermind.message_intelligence.text_cleaning import MESSAGE_COLUMN_CANDIDATES

TONE_PROMPT = (
    "You read complaints sent to an electricity distribution company.\n"
    "Say how the complaint below reads. Answer with exactly one of these tones: "
    f"{', '.join(constants.TONE_READINGS)}.\n"
    "Give as your reason a short phrase quoted word for word from the complaint that shows "
    "the tone.\n"
    'Answer with JSON only, in the form {{"tone": "<one of the tones>", '
    '"reason": "<phrase from the complaint>"}}.\n\n'
    "Complaint:\n{message_text}"
)
ESCALATION_FIELDS = ("message_id", "age_days", "urgency", "tone", "escalate", "signals")
WAITING_SIGNAL = "waiting too long"
URGENCY_SIGNAL = "urgency"
TONE_SIGNAL = "tone"
RECEIVED_DATE_CANDIDATES = ("received_date", "received_on", "received_at", "date_received")
JOINED_BY = ";"


def complaint_age_days(received_date, today=None):
    if today is None:
        today = date.today()
    received = pd.to_datetime(str(received_date)).date()
    return int((pd.Timestamp(today).date() - received).days)


def decide_escalation(age_days, urgency, tone):
    signals = []
    if age_days > constants.COMPLAINT_AGE_ESCALATION_DAYS:
        signals.append(WAITING_SIGNAL)
    if urgency in constants.ESCALATING_URGENCIES:
        signals.append(URGENCY_SIGNAL)
    if tone in constants.ESCALATING_TONES:
        signals.append(TONE_SIGNAL)
    return {
        "escalate": len(signals) >= constants.ESCALATION_SIGNALS_NEEDED,
        "signals": signals,
    }


def read_tone(message_text, cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    prompt = TONE_PROMPT.format(message_text=str(message_text))
    answer = read_answer(ask_model(prompt, cache_path), constants.TONE_REPLY_KEYS)
    tone = str(answer["tone"]).strip().lower()
    if tone not in constants.TONE_READINGS:
        raise LanguageModelError(f"the model read the tone as {answer['tone']!r}, "
                                 f"which is not one the platform publishes")
    return {"tone": tone, "reason": str(answer["reason"])}


def _first_field(message, candidates):
    for candidate in candidates:
        if candidate in message:
            return message[candidate]
    raise KeyError(f"the complaint carries none of {candidates}")


def escalate_one_message(message, urgency_model, today=None,
                         cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    text = _first_field(message, MESSAGE_COLUMN_CANDIDATES)
    age_days = complaint_age_days(_first_field(message, RECEIVED_DATE_CANDIDATES), today)
    urgency = str(urgency_model.predict([text])[0])
    tone = read_tone(text, cache_path)["tone"]
    decided = decide_escalation(age_days, urgency, tone)
    return {
        "message_id": message.get("message_id"),
        "age_days": age_days,
        "urgency": urgency,
        "tone": tone,
        "escalate": decided["escalate"],
        "signals": decided["signals"],
    }


def write_escalations(messages, urgency_model, escalations_path, today=None,
                      cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    messages = list(messages)
    results = run_batch(
        messages,
        lambda message: escalate_one_message(message, urgency_model, today, cache_path),
    )
    decided = [result for result in results if not isinstance(result, MessageFailure)]

    path = Path(escalations_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ESCALATION_FIELDS))
        writer.writeheader()
        for row in decided:
            writer.writerow(dict(row, signals=JOINED_BY.join(row["signals"])))
    return {
        "decided": len(decided),
        "failed": len(results) - len(decided),
        "escalated": sum(1 for row in decided if row["escalate"]),
    }


if __name__ == "__main__":
    sample = pd.read_csv(
        constants.COMPLAINT_MESSAGES_PATH, nrows=constants.ESCALATION_SAMPLE_MESSAGES
    ).to_dict("records")
    urgency_model = joblib.load(constants.COMPLAINT_URGENCY_MODEL_PATH)
    print(write_escalations(sample, urgency_model, constants.ESCALATIONS_PATH))
