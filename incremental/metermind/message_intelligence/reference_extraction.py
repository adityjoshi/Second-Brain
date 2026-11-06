import csv
import re
from pathlib import Path

import pandas as pd

from config import constants
from metermind.message_intelligence.text_cleaning import _as_text, _message_column


def _whole_reference(published):
    body = published.lstrip("^").rstrip("$")
    return re.compile(rf"(?<![A-Za-z0-9-]){body}(?![A-Za-z0-9-])")


ACCOUNT_NUMBER_PATTERN = _whole_reference(constants.ACCOUNT_NUMBER_PATTERN)
METER_SERIAL_PATTERN = _whole_reference(constants.METER_SERIAL_PATTERN)
COMPLAINT_REFERENCE_PATTERN = _whole_reference(constants.COMPLAINT_REFERENCE_PATTERN)
EXTRACTED_REFERENCE_FIELDS = (
    "message_id",
    "account_numbers",
    "meter_serials",
    "complaint_references",
    "unknown_accounts",
    "serials_on_another_account",
)
JOINED_BY = ";"
MESSAGE_ID_CANDIDATES = ("message_id", "complaint_reference", "id")


def _find(pattern, message):
    return sorted({found.group(0) for found in pattern.finditer(_as_text(message))})


def find_account_numbers(message):
    return _find(ACCOUNT_NUMBER_PATTERN, message)


def find_meter_serials(message):
    return _find(METER_SERIAL_PATTERN, message)


def find_complaint_references(message):
    return _find(COMPLAINT_REFERENCE_PATTERN, message)


def check_against_connection_register(accounts, serials, known_accounts, serial_owner):
    unknown_accounts = sorted({account for account in accounts if account not in known_accounts})
    quoted_accounts = set(accounts)
    on_another = []
    if quoted_accounts:
        for serial in sorted(set(serials)):
            owner = serial_owner.get(serial)
            if owner is not None and owner not in quoted_accounts:
                on_another.append(serial)
    return {"unknown_accounts": unknown_accounts, "serials_on_another_account": on_another}


def extract_and_check(messages_path, register_path, extracted_path):
    register = pd.read_csv(register_path, dtype=str)
    known_accounts = set(register["account_number"].dropna())
    serial_owner = dict(
        register.dropna(subset=["meter_serial", "account_number"])[
            ["meter_serial", "account_number"]
        ].itertuples(index=False, name=None)
    )

    corpus = pd.read_csv(messages_path)
    text_column = _message_column(corpus)
    id_column = next((name for name in MESSAGE_ID_CANDIDATES if name in corpus.columns), None)

    rows = []
    faults = 0
    for position, record in enumerate(corpus.to_dict("records")):
        message = record[text_column]
        accounts = find_account_numbers(message)
        serials = find_meter_serials(message)
        checked = check_against_connection_register(
            accounts, serials, known_accounts, serial_owner
        )
        faults += len(checked["unknown_accounts"]) + len(checked["serials_on_another_account"])
        rows.append({
            "message_id": record[id_column] if id_column else position,
            "account_numbers": JOINED_BY.join(accounts),
            "meter_serials": JOINED_BY.join(serials),
            "complaint_references": JOINED_BY.join(find_complaint_references(message)),
            "unknown_accounts": JOINED_BY.join(checked["unknown_accounts"]),
            "serials_on_another_account": JOINED_BY.join(
                checked["serials_on_another_account"]
            ),
        })

    path = Path(extracted_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(EXTRACTED_REFERENCE_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    return {"messages": len(rows), "faults": faults}


if __name__ == "__main__":
    print(extract_and_check(
        constants.COMPLAINT_MESSAGES_PATH,
        constants.CONNECTION_REGISTER_PATH,
        constants.EXTRACTED_REFERENCES_PATH,
    ))
