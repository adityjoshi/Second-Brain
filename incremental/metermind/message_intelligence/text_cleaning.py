import re
from pathlib import Path

import pandas as pd

from config import constants

QUOTED_REPLY_PATTERN = re.compile(
    r"^[ \t]*(?:>"
    r"|On\s.*\bwrote:[ \t]*$"
    r"|-{2,}\s*(?:Original|Forwarded)\s+Message\s*-{2,}"
    r"|Begin\s+forwarded\s+message"
    r"|(?:From|Sent|To|Subject):\s)",
    re.IGNORECASE | re.MULTILINE,
)

GREETING_PATTERN = re.compile(
    r"^[ \t]*(?:"
    r"(?i:dear|respected|hello|hi|hey|greetings|sir|madam|good\s+(?:morning|afternoon|evening|day))"
    r"(?:\s+(?:(?i:sir|madam|sir/madam|sir\s+or\s+madam|team|all|there|officer|engineer|ji"
    r"|concerned|support|customer\s+care)|[A-Z][A-Za-z.'/-]*))*"
    r"|(?i:to\s+whom\s+it\s+may\s+concern)"
    r")[ \t]*[,!:.]?[ \t]*$",
    re.MULTILINE,
)

SIGN_OFF_PATTERN = re.compile(
    r"^[ \t]*(?:regards|best\s+regards|kind\s+regards|warm\s+regards|with\s+regards"
    r"|thanks|thank\s+you|thanks\s+(?:and|&)\s+regards|many\s+thanks"
    r"|sincerely|yours\s+(?:sincerely|faithfully|truly)|cheers)"
    r"(?:\s+(?:in\s+advance|again|so\s+much))?[ \t]*[,!.]?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

SIGNATURE_PATTERN = re.compile(
    r"^[ \t]*(?:"
    r"(?:(?:ph|phone|mob|mobile|tel|cell|contact(?:\s+no\.?)?|whatsapp)\s*[.:#-]*\s*)?"
    r"\+?\d[\d \t()-]{7,}\d"
    r"|(?:staff|emp(?:loyee)?|officer)\s*(?:id|no\.?|code|number)?\s*[.:#-]*\s*[A-Z]*-?\d+"
    r"|(?:STF|EMP)-?\d+"
    r")[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

COMPLAINT_REFERENCE_PATTERN = re.compile(
    r"[(\[]?\s*(?:(?:complaint\s*)?(?:ref(?:erence)?|no|number|id)\.?\s*[:#-]?\s*)?"
    r"\bCMP\d{7}\b\s*[)\]]?",
    re.IGNORECASE,
)

WHITESPACE_PATTERN = re.compile(r"\s+")

MESSAGE_COLUMN_CANDIDATES = (
    "message_text",
    "message",
    "raw_message",
    "complaint_text",
    "text",
    "body",
    "complaint",
)
CLEAN_TEXT_COLUMN = "clean_text"


def strip_quoted_reply(message):
    found = QUOTED_REPLY_PATTERN.search(message)
    if found is None:
        return message
    kept = message[: found.start()]
    if kept.strip():
        return kept
    # The quotation opened the message; keep the unquoted lines rather than nothing.
    unquoted = [
        line for line in message.splitlines()
        if not QUOTED_REPLY_PATTERN.match(line)
    ]
    return "\n".join(unquoted)


def strip_greeting_and_sign_off(message):
    without_greeting = GREETING_PATTERN.sub("", message)
    return SIGN_OFF_PATTERN.sub("", without_greeting)


def strip_signature(message):
    return SIGNATURE_PATTERN.sub("", message)


def normalise_whitespace(message):
    return WHITESPACE_PATTERN.sub(" ", message).strip()


def _as_text(message):
    if message is None:
        return ""
    try:
        if pd.isna(message):
            return ""
    except (TypeError, ValueError):
        pass
    return str(message)


def clean_message(message):
    text = _as_text(message)
    cleaned = strip_quoted_reply(text)
    cleaned = strip_greeting_and_sign_off(cleaned)
    cleaned = strip_signature(cleaned)
    cleaned = COMPLAINT_REFERENCE_PATTERN.sub(" ", cleaned)
    cleaned = normalise_whitespace(cleaned)
    if cleaned:
        return cleaned
    # A cleaning that empties a message has removed the complaint itself.
    fallback = normalise_whitespace(COMPLAINT_REFERENCE_PATTERN.sub(" ", text))
    return fallback or normalise_whitespace(text)


def clean_messages(messages):
    return [clean_message(message) for message in messages]


def _message_column(corpus):
    for candidate in MESSAGE_COLUMN_CANDIDATES:
        if candidate in corpus.columns:
            return candidate
    text_columns = [
        column for column in corpus.columns
        if corpus[column].dtype == object and column != CLEAN_TEXT_COLUMN
    ]
    return max(
        text_columns,
        key=lambda column: corpus[column].astype(str).str.len().mean(),
    )


def clean_corpus(messages_path, clean_path):
    corpus = pd.read_csv(messages_path)
    source = _message_column(corpus)
    corpus[CLEAN_TEXT_COLUMN] = clean_messages(corpus[source])
    path = Path(clean_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    corpus.to_csv(path, index=False)
    lengths = corpus[CLEAN_TEXT_COLUMN].str.len()
    return {
        "messages": int(len(corpus)),
        "shortest": int(lengths.min()) if len(corpus) else 0,
    }


if __name__ == "__main__":
    print(clean_corpus(constants.COMPLAINT_MESSAGES_PATH, constants.CLEAN_COMPLAINTS_PATH))
