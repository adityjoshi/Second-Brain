import json
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator

from config import constants
from metermind.core.exceptions import ToolError
from metermind.core.tariff_calculations import calculate_bill_amount

readings_database_path = constants.READINGS_DATABASE_PATH
champion_model_path = constants.CHAMPION_MODEL_PATH
operating_rule_path = constants.OPERATING_RULE_PATH
exception_report_path = constants.EXCEPTION_REPORT_PATH
tariff_store_directory = constants.TARIFF_STORE_DIRECTORY

opened_resources = {}


def _refuse_unpublished_category(given):
    settled = str(given).strip().lower()
    if settled not in constants.CONSUMER_CATEGORIES:
        raise ValueError(
            f"{given!r} is not a category the company bills; use one of "
            f"{', '.join(constants.CONSUMER_CATEGORIES)}"
        )
    return settled


class ReadingRequest(BaseModel):
    reading_identifier: str = Field(
        description="The identifier of one reading on file, such as RDG00000123."
    )


class BillRequest(BaseModel):
    consumer_category: str = Field(
        description="Whose schedule prices the cycle: domestic, commercial or agricultural."
    )
    units_consumed: float = Field(
        ge=0, description="The units the meter recorded in the cycle, not below zero."
    )
    sanctioned_load_kw: float = Field(
        gt=0, description="The connected load on file in kilowatts, above zero."
    )

    @field_validator("consumer_category")
    @classmethod
    def a_category_that_is_billed(cls, given):
        return _refuse_unpublished_category(given)


class TariffRequest(BaseModel):
    question: str = Field(description="What to answer out of the tariff order, in words.")
    consumer_category: str = Field(
        description="Whose schedule is asked about: domestic, commercial or agricultural."
    )
    billing_period: str = Field(
        pattern=constants.BILLING_PERIOD_PATTERN,
        description="The billing cycle asked about, as a year and a month such as 2026-06.",
    )

    @field_validator("consumer_category")
    @classmethod
    def a_category_with_a_schedule(cls, given):
        return _refuse_unpublished_category(given)


def _opened(name, opener):
    if name not in opened_resources:
        opened_resources[name] = opener()
    return opened_resources[name]


def _open_database():
    from metermind.data_access.database_loader import ReadingDatabase

    if not Path(readings_database_path).is_file():
        raise ToolError(f"no readings database at {readings_database_path}")
    return ReadingDatabase(readings_database_path)


def _open_champion():
    from metermind.exception_models.baseline_model import load_model

    if not Path(champion_model_path).is_file():
        raise ToolError(f"no champion has been fitted at {champion_model_path}")
    return load_model(champion_model_path)


def _open_rule():
    if not Path(operating_rule_path).is_file():
        raise ToolError(f"no operating rule at {operating_rule_path}")
    return json.loads(Path(operating_rule_path).read_text(encoding="utf-8"))


def _open_report():
    if not Path(exception_report_path).is_file():
        raise ToolError(f"no exception report at {exception_report_path}")
    report = pd.read_csv(exception_report_path)
    return dict(zip(report["exception_class"].astype(str), report["precision"].astype(float)))


def _open_store():
    from metermind.retrieval.vector_store import TariffStoreMissing, open_tariff_store

    try:
        return open_tariff_store(tariff_store_directory)
    except TariffStoreMissing as error:
        raise ToolError(str(error)) from error


def _open_embedder():
    from metermind.retrieval.vector_store import load_embedder

    return load_embedder()


@tool(args_schema=ReadingRequest)
def look_up_reading(reading_identifier):
    """Look up one meter reading on file by its identifier and return everything recorded
    against that billing cycle: the account, the meter, the readings, the units and the
    exception class on file. Use it whenever a question is about a particular reading."""
    database = _opened("database", _open_database)
    reading = database.find_reading_by_identifier(reading_identifier)
    if reading is None:
        raise ToolError(f"no reading is stored against {reading_identifier}")
    return reading


@tool(args_schema=BillRequest)
def calculate_bill(consumer_category, units_consumed, sanctioned_load_kw):
    """Price one billing cycle under the published schedule for its consumer category,
    from the units consumed and the sanctioned load. It says nothing about whether the
    reading behind the units is trustworthy; it only prices the units it is given."""
    amount = calculate_bill_amount(consumer_category, units_consumed, sanctioned_load_kw)
    return {
        "consumer_category": consumer_category,
        "units_consumed": units_consumed,
        "sanctioned_load_kw": sanctioned_load_kw,
        "current_demand_inr": round(float(amount), constants.CURRENCY_DECIMAL_PLACES),
    }


def _reading_as_frame(reading):
    from metermind.exception_models.feature_pipeline import (
        DERIVED_NUMBER_COLUMNS,
        MODELLING_NUMBER_COLUMNS,
    )

    frame = pd.DataFrame([reading])
    for column in MODELLING_NUMBER_COLUMNS + DERIVED_NUMBER_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


@tool(args_schema=ReadingRequest)
def predict_reading_exception(reading_identifier):
    """Say which of the five exception classes one reading on file belongs to, under the
    champion model and its operating rule, together with how often that class is right
    when the champion names it (its measured precision). Report the precision alongside
    the class, especially before suggesting a meter may have been tampered with."""
    from metermind.exception_models.champion_model import predict_with_rule
    from metermind.exception_models.feature_engineering import widen_readings
    from metermind.exception_models.feature_pipeline import modelling_columns

    reading = look_up_reading.invoke({"reading_identifier": reading_identifier})
    champion = _opened("champion", _open_champion)
    rule = _opened("rule", _open_rule)
    precisions = _opened("report", _open_report)

    widened = widen_readings(_reading_as_frame(reading))
    for column in modelling_columns(True):
        if column not in widened.columns:
            widened[column] = None
    decided = predict_with_rule(
        champion, widened[list(modelling_columns(True))],
        rule["tamper_floor"], rule["fault_floor"],
    )[0]
    if decided not in precisions:
        raise ToolError(f"the exception report carries no precision for {decided}")
    return {
        "reading_identifier": reading_identifier,
        "reading": reading,
        "exception_class": decided,
        "precision": precisions[decided],
    }


@tool(args_schema=TariffRequest)
def search_tariff_order(question, consumer_category, billing_period):
    """Return what the tariff order actually in force for that consumer category and
    billing period says about the question. Never answer a tariff question from memory:
    the same question has different answers in different periods, and only the order in
    force for the period asked about is reached."""
    from metermind.retrieval.filtered_search import NoOrderInForce, filtered_search

    store = _opened("store", _open_store)
    embedder = _opened("embedder", _open_embedder)
    try:
        return filtered_search(store, question, embedder, consumer_category, billing_period)
    except NoOrderInForce as error:
        raise ToolError(str(error)) from error


READING_TOOLS = [look_up_reading, calculate_bill, predict_reading_exception,
                 search_tariff_order]


if __name__ == "__main__":
    for one in READING_TOOLS:
        print(f"{one.name:<26} {sorted(one.args)}")
