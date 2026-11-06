import json
from pathlib import Path

import pandas as pd

from config import constants
from metermind.exception_models.baseline_model import load_model
from metermind.exception_models.champion_model import predict_with_rule
from metermind.exception_models.feature_engineering import widen_readings
from metermind.exception_models.feature_pipeline import modelling_columns

QUEUE_BY_DECISION = dict(constants.QUEUE_FILE_PATHS)
QUEUES = tuple(QUEUE_BY_DECISION.keys())


def sort_into_queues(book, decided):
    frame = book.copy()
    frame["decided_class"] = [str(label) for label in decided]
    sorted_out = {}
    for queue_name in QUEUES:
        queue_rows = frame.loc[frame["decided_class"] == queue_name].copy()
        sorted_out[queue_name] = queue_rows.reset_index(drop=True)
    return sorted_out


def queue_counts(sorted_out):
    return {queue_name: int(len(rows)) for queue_name, rows in sorted_out.items()}


def write_queue_files(sorted_out, paths=None):
    if paths is None:
        paths = QUEUE_BY_DECISION
    written = {}
    for queue_name, rows in sorted_out.items():
        path = Path(paths[queue_name])
        path.parent.mkdir(parents=True, exist_ok=True)
        if len(rows) == 0:
            path.write_text(",".join(str(column) for column in rows.columns) + "\n",
                            encoding="utf-8")
        else:
            rows.to_csv(path, index=False)
        written[queue_name] = path
    return written


if __name__ == "__main__":
    book = pd.read_csv(constants.READING_BOOK_PREDICT_PATH)
    widened = widen_readings(book)
    model = load_model(constants.CHAMPION_MODEL_PATH)
    rule = json.loads(Path(constants.OPERATING_RULE_PATH).read_text(encoding="utf-8"))
    columns = widened[list(modelling_columns(True))]
    decided = predict_with_rule(
        model, columns, rule["tamper_floor"], rule["fault_floor"]
    )
    sorted_out = sort_into_queues(widened, decided)
    write_queue_files(sorted_out)
    print(queue_counts(sorted_out))
