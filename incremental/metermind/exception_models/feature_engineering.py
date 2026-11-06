import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import constants
from metermind.exception_models.feature_pipeline import modelling_columns
from metermind.exception_models.baseline_model import split_readings
from metermind.exception_models.tree_models import train_random_forest

DAYS_IN_A_YEAR = 365.25


def add_consumption_ratio_to_average(book):
    result = book.copy()
    units = pd.to_numeric(result["units_consumed"], errors="coerce")
    average = pd.to_numeric(result["twelve_month_average_units"], errors="coerce")
    ratio = units / average
    ratio = ratio.where(average.notna() & (average != 0), 1.0)
    result["consumption_ratio_to_average"] = ratio
    return result


def add_load_factor(book):
    result = book.copy()
    units = pd.to_numeric(result["units_consumed"], errors="coerce")
    load = pd.to_numeric(result["sanctioned_load_kw"], errors="coerce")
    cycle_days = pd.to_numeric(result["cycle_days"], errors="coerce")
    capacity = load * constants.HOURS_IN_A_DAY * cycle_days
    factor = units / capacity
    # Zero capacity must not become ±inf; the numeric imputer fills these later.
    factor = factor.mask(~np.isfinite(factor))
    result["load_factor"] = factor
    return result


def add_meter_age_years(book):
    result = book.copy()
    installed = pd.to_datetime(result["meter_install_date"], errors="coerce")
    ended = pd.to_datetime(result["cycle_end_date"], errors="coerce")
    span_days = (ended - installed).dt.days
    age = span_days / DAYS_IN_A_YEAR
    result["meter_age_years"] = age
    return result


def widen_readings(book):
    widened = add_consumption_ratio_to_average(book)
    widened = add_load_factor(widened)
    widened = add_meter_age_years(widened)
    return widened


def measure_feature_lift(book):
    fitting_columns, held_out_columns, fitting_classes, held_out_classes = (
        split_readings(book, columns=list(modelling_columns(False)))
    )
    narrow_model = train_random_forest(fitting_columns, fitting_classes, widened=False)
    narrow_score = float(narrow_model.score(held_out_columns, held_out_classes))

    widened = widen_readings(book)
    wide_columns = list(modelling_columns(True))
    fitting_wide = widened.loc[fitting_columns.index, wide_columns]
    held_wide = widened.loc[held_out_columns.index, wide_columns]
    wide_model = train_random_forest(fitting_wide, fitting_classes, widened=True)
    widened_score = float(wide_model.score(held_wide, held_out_classes))

    places = constants.MEASUREMENT_DECIMAL_PLACES
    narrow = round(narrow_score, places)
    widened_rounded = round(widened_score, places)
    lift = round(widened_rounded - narrow, places)
    return {"narrow": narrow, "widened": widened_rounded, "lift": lift}


if __name__ == "__main__":
    book = pd.read_csv(constants.CLEAN_READING_BOOK_PATH)
    widened = widen_readings(book)
    Path(constants.WIDENED_READINGS_PATH).parent.mkdir(parents=True, exist_ok=True)
    widened.to_csv(constants.WIDENED_READINGS_PATH, index=False)

    sample = book.sample(
        n=min(4000, len(book)), random_state=constants.MODEL_SEED
    ).reset_index(drop=True)
    figures = measure_feature_lift(sample)
    lift_path = Path(constants.FEATURE_LIFT_PATH)
    lift_path.parent.mkdir(parents=True, exist_ok=True)
    lift_path.write_text(json.dumps(figures, indent=2), encoding="utf-8")
    print(f"narrow   {figures['narrow']}")
    print(f"widened  {figures['widened']}")
    print(f"lift     {figures['lift']}")
