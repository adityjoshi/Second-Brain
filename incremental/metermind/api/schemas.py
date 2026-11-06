from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from config.constants import (
    CONSUMER_CATEGORY_CORRECTIONS,
    MINIMUM_CYCLE_DAYS,
    MAXIMUM_CYCLE_DAYS,
    METER_ROLLOVER_UNITS,
)
from metermind.core.validators import (
    validate_account_number,
    validate_meter_serial,
    validate_billing_period,
)


READ_DATE_SHAPES = ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%d.%m.%Y")
PLATFORM_DATE_SHAPE = "%Y-%m-%d"


class HealthReply(BaseModel):
    service: str
    status: str


class ReadingSubmission(BaseModel):
    account_number: str
    meter_serial: str
    consumer_category: str
    billing_period: str
    sanctioned_load_kw: float = Field(gt=0, le=500)
    cycle_days: int = Field(ge=MINIMUM_CYCLE_DAYS, le=MAXIMUM_CYCLE_DAYS)
    previous_reading: float = Field(ge=0, lt=METER_ROLLOVER_UNITS)
    current_reading: float = Field(ge=0, lt=METER_ROLLOVER_UNITS)
    read_type: str = "actual"
    read_date: Optional[str] = None

    @field_validator("consumer_category")
    @classmethod
    def spelling_is_settled_at_the_door(cls, given):
        settled = str(given).strip().lower()
        return CONSUMER_CATEGORY_CORRECTIONS.get(settled, settled)

    @field_validator("read_date")
    @classmethod
    def date_is_readable(cls, given):
        if given is None:
            return None
        text = str(given).strip()
        for shape in READ_DATE_SHAPES:
            try:
                return datetime.strptime(text, shape).strftime(PLATFORM_DATE_SHAPE)
            except ValueError:
                continue
        raise ValueError(
            "read date must be written as 2026-07-01, 01/07/2026, 01-Jul-2026 "
            "or 01.07.2026"
        )

    @field_validator("account_number")
    @classmethod
    def account_number_is_well_formed(cls, given):
        text = str(given).strip()
        if not validate_account_number(text):
            raise ValueError(
                "account number must look like ACC followed by eight digits"
            )
        return text.upper()

    @field_validator("meter_serial")
    @classmethod
    def meter_serial_is_well_formed(cls, given):
        text = str(given).strip()
        if not validate_meter_serial(text):
            raise ValueError(
                "meter serial must look like MTR-XX-123456 with capital letters"
            )
        return text.upper()

    @field_validator("billing_period")
    @classmethod
    def billing_period_is_well_formed(cls, given):
        text = str(given).strip()
        if not validate_billing_period(text):
            raise ValueError(
                "billing period must be a year and a month, such as 2026-06"
            )
        return text


class ReadingReply(BaseModel):
    reading_id: str
    account_number: str
    consumer_category: str
    units_consumed: float
    energy_charge_inr: float
    fixed_charge_inr: float
    net_bill_inr: float
    is_billable: bool
    refusal_reasons: List[str]


class CaseStatusRequest(BaseModel):
    wanted_status: str
    noted_by: str


class CaseStatusReply(BaseModel):
    reading_id: str
    from_status: str
    to_status: str
    recorded_by: str


class PagedReadings(BaseModel):
    readings: List[ReadingReply]
    page: int
    page_size: int
    total: int


class ScreeningRequest(ReadingSubmission):
    units_consumed: float
    twelve_month_average_units: float
    same_month_last_year_units: float
    consecutive_estimated_reads: int
    days_since_actual_read: int
    neighbourhood_average_units: float
    arrears_inr: float
    payment_defaults_last_year: int
    seal_check_result: str
    meter_make: str
    division: str
    meter_install_date: str
    cycle_end_date: str


class ScreeningReply(BaseModel):
    account_number: str
    billing_period: str
    exception_class: str
    confidence: float
    goes_to: str
