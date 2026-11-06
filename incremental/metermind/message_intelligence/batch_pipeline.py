import csv
from pathlib import Path

from config import constants

BATCH_FAILURE_FIELDS = ("message_id", "reason")


class MessageFailure(Exception):
    def __init__(self, message_id, reason):
        self.message_id = message_id
        self.reason = reason
        super().__init__(f"{message_id} failed: {reason}")


def _message_id(message, position):
    if isinstance(message, dict) and message.get("message_id") is not None:
        return str(message["message_id"])
    return f"position {position}"


def run_batch(messages, handle_one, failures_path=constants.BATCH_FAILURES_PATH):
    results = []
    for position, message in enumerate(messages):
        try:
            results.append(handle_one(message))
        except MessageFailure as failure:
            results.append(failure)
        except Exception as error:
            results.append(MessageFailure(_message_id(message, position), str(error)))

    path = Path(failures_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BATCH_FAILURE_FIELDS))
        writer.writeheader()
        for result in results:
            if isinstance(result, MessageFailure):
                writer.writerow({"message_id": result.message_id, "reason": result.reason})
    return results


if __name__ == "__main__":
    messages = [{"message_id": "MSG000001", "units": 120}, {"message_id": "MSG000002"}]
    for result in run_batch(messages, lambda message: message["units"] * 2):
        if isinstance(result, MessageFailure):
            print(f"{result.message_id} failed, and the batch carried on: {result.reason}")
        else:
            print(f"handled and returned: {result}")
    print(f"what failed is written to: {constants.BATCH_FAILURES_PATH}")
