import re
from pathlib import Path

import pandas as pd

from config import constants

REJECTION_REASONS = (
    "a required field is empty",
    "the read date could not be read",
    "the billing period is not a year and a month",
    "the consumer category has no tariff schedule",
    "the sanctioned load is not above zero",
    "the billing cycle length is outside the permitted range",
    "the current reading is below the previous reading",
    "the consumption could not be drawn by any load on file",
)

REQUIRED_FIELDS = (
    "account_number",
    "consumer_category",
    "sanctioned_load_kw",
    "cycle_days",
    "previous_reading",
    "current_reading",
    "read_date",
    "billing_period",
    "meter_serial",
)

READ_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%d.%m.%Y")

_ENGLISH_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_read_dates(book):
    result = pd.Series(pd.NaT, index=book.index, dtype="datetime64[ns]")
    if "read_date" not in book.columns:
        return result

    text = book["read_date"].astype(str).str.strip()
    text = text.where(~book["read_date"].isna(), "")

    # Try each published format; never re-parse rows already read.
    mask = result.isna()
    result = result.mask(
        mask, pd.to_datetime(text.where(mask), format="%Y-%m-%d", errors="coerce")
    )

    mask = result.isna()
    result = result.mask(
        mask, pd.to_datetime(text.where(mask), format="%d/%m/%Y", errors="coerce")
    )

    mask = result.isna()
    parts = text.where(mask).str.extract(
        r"^(\d{1,2})-([A-Za-z]{3})-(\d{4})$"
    )
    month = parts[1].str.lower().map(_ENGLISH_MONTHS)
    iso = (
        parts[2]
        + "-"
        + month.map(lambda m: f"{int(m):02d}" if pd.notna(m) else pd.NA)
        + "-"
        + parts[0].map(lambda d: f"{int(d):02d}" if pd.notna(d) else pd.NA)
    )
    result = result.mask(mask, pd.to_datetime(iso, format="%Y-%m-%d", errors="coerce"))

    mask = result.isna()
    result = result.mask(
        mask, pd.to_datetime(text.where(mask), format="%d.%m.%Y", errors="coerce")
    )

    return result.astype("datetime64[ns]")


def first_broken_rule(row):
    for field in REQUIRED_FIELDS:
        if field not in row.index:
            continue
        value = row[field]
        if pd.isna(value) or str(value).strip() == "":
            return REJECTION_REASONS[0]

    if "read_on" not in row.index or pd.isna(row["read_on"]):
        return REJECTION_REASONS[1]

    if re.fullmatch(
        constants.BILLING_PERIOD_PATTERN, str(row["billing_period"]).strip()
    ) is None:
        return REJECTION_REASONS[2]

    if str(row["consumer_category"]).strip().lower() not in constants.CONSUMER_CATEGORIES:
        return REJECTION_REASONS[3]

    if not (float(row["sanctioned_load_kw"]) > 0):
        return REJECTION_REASONS[4]

    cycle_days = float(row["cycle_days"])
    if not constants.MINIMUM_CYCLE_DAYS <= cycle_days <= constants.MAXIMUM_CYCLE_DAYS:
        return REJECTION_REASONS[5]

    previous_reading = float(row["previous_reading"])
    current_reading = float(row["current_reading"])
    sanctioned_load_kw = float(row["sanctioned_load_kw"])
    physical_max = (
        sanctioned_load_kw
        * constants.HOURS_IN_A_DAY
        * cycle_days
        * constants.IMPLAUSIBLE_CAPACITY_FACTOR
    )

    if current_reading < previous_reading:
        if previous_reading + physical_max < constants.METER_ROLLOVER_UNITS:
            return REJECTION_REASONS[6]
        units = constants.METER_ROLLOVER_UNITS - previous_reading + current_reading
    else:
        units = current_reading - previous_reading

    if units > physical_max:
        return REJECTION_REASONS[7]

    return ""


def clean_reading_book(book_path, clean_path, rejected_path):
    book = pd.read_csv(book_path)

    text_cols = {
        "reading_id",
        "account_number",
        "consumer_category",
        "tariff_code",
        "read_date",
        "billing_period",
        "meter_serial",
        "read_type",
        "seal_check_result",
        "meter_make",
        "division",
        "subdivision",
        "exception_class",
        "connection_date",
        "meter_install_date",
        "cycle_start_date",
        "cycle_end_date",
        "last_inspection_date",
    }
    for col in book.columns:
        if col not in text_cols:
            book[col] = pd.to_numeric(book[col], errors="coerce")

    book = book.copy()
    book["read_on"] = parse_read_dates(book)
    book["rejection_reason"] = book.apply(first_broken_rule, axis=1)

    kept = book.loc[book["rejection_reason"] == ""].drop(
        columns=["rejection_reason", "read_on"], errors="ignore"
    )
    rejected = book.loc[book["rejection_reason"] != ""].drop(
        columns=["read_on"], errors="ignore"
    )

    Path(clean_path).parent.mkdir(parents=True, exist_ok=True)
    Path(rejected_path).parent.mkdir(parents=True, exist_ok=True)
    kept.to_csv(clean_path, index=False)
    rejected.to_csv(rejected_path, index=False)

    return {"kept": int(len(kept)), "rejected": int(len(rejected))}
