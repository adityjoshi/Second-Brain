from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from config import constants
from metermind.api import schemas
from metermind.api.access_control import (
    record_audit_entry,
    require_inspector,
    require_signed_in,
)
from metermind.api.case_transitions import move_case_status
from metermind.api.repository import InMemoryReadingRepository
from metermind.core.entities import create_service_connection
from metermind.core.exceptions import (
    MeterMindError,
    ReadingStorageError,
    UnsupportedCategoryError,
)

router = APIRouter(tags=["readings"])
reading_repository = InMemoryReadingRepository()


def price_reading(stored_reading):
    connection = create_service_connection(
        {
            "account_number": stored_reading["account_number"],
            "consumer_category": stored_reading["consumer_category"],
            "sanctioned_load_kw": stored_reading["sanctioned_load_kw"],
            "cycle_days": stored_reading["cycle_days"],
            "previous_reading": stored_reading["previous_reading"],
            "current_reading": stored_reading["current_reading"],
        }
    )
    return schemas.ReadingReply(
        reading_id=stored_reading["reading_id"],
        account_number=stored_reading["account_number"],
        consumer_category=connection.consumer_category,
        units_consumed=round(connection.units_consumed, 1),
        energy_charge_inr=round(connection.energy_charge_inr(), 2),
        fixed_charge_inr=round(connection.fixed_charge_inr(), 2),
        net_bill_inr=round(connection.net_bill_inr(), 2),
        is_billable=connection.is_billable(),
        refusal_reasons=list(connection.refusal_reasons()),
    )


def _submission_as_record(submitted_reading: schemas.ReadingSubmission):
    if hasattr(submitted_reading, "model_dump"):
        return submitted_reading.model_dump()
    return submitted_reading.dict()


@router.post(
    "/readings",
    response_model=schemas.ReadingReply,
    status_code=status.HTTP_201_CREATED,
)
def submit_reading(submitted_reading: schemas.ReadingSubmission):
    record = _submission_as_record(submitted_reading)
    try:
        create_service_connection(record)
    except UnsupportedCategoryError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    stored = reading_repository.add_reading(record)
    return price_reading(stored)


@router.get("/readings", response_model=schemas.PagedReadings)
def list_readings(
    consumer_category: str = Query(default=None),
    read_type: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    carried=Depends(require_signed_in),
):
    matched = reading_repository.list_readings()
    if consumer_category is not None:
        matched = [
            reading
            for reading in matched
            if reading.get("consumer_category") == consumer_category
        ]
    if read_type is not None:
        matched = [
            reading for reading in matched if reading.get("read_type") == read_type
        ]
    total = len(matched)
    start = (page - 1) * page_size
    page_rows = matched[start : start + page_size]
    return schemas.PagedReadings(
        readings=[price_reading(reading) for reading in page_rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/readings/{reading_identifier}", response_model=schemas.ReadingReply)
def read_reading(reading_identifier: str):
    try:
        stored = reading_repository.get_reading(reading_identifier)
    except ReadingStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return price_reading(stored)


@router.put("/readings/{reading_identifier}", response_model=schemas.ReadingReply)
def replace_reading(
    reading_identifier: str, submitted_reading: schemas.ReadingSubmission
):
    record = _submission_as_record(submitted_reading)
    try:
        create_service_connection(record)
    except UnsupportedCategoryError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    try:
        stored = reading_repository.replace_reading(reading_identifier, record)
    except ReadingStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return price_reading(stored)


@router.delete("/readings/{reading_identifier}", status_code=status.HTTP_204_NO_CONTENT)
def remove_reading(reading_identifier: str):
    try:
        reading_repository.remove_reading(reading_identifier)
    except ReadingStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/readings/{reading_identifier}/status",
    response_model=schemas.CaseStatusReply,
)
def change_case_status(
    reading_identifier: str,
    wanted: schemas.CaseStatusRequest,
    carried=Depends(require_inspector),
):
    try:
        stored = reading_repository.get_reading(reading_identifier)
    except ReadingStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    from_status = stored.get("case_status") or constants.INITIAL_CASE_STATUS
    try:
        to_status = move_case_status(from_status, wanted.wanted_status)
    except MeterMindError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    stored["case_status"] = to_status
    reading_repository.replace_reading(reading_identifier, stored)
    record_audit_entry(
        wanted.noted_by,
        carried.get("role"),
        reading_identifier,
        from_status,
        to_status,
    )
    return schemas.CaseStatusReply(
        reading_id=reading_identifier,
        from_status=from_status,
        to_status=to_status,
        recorded_by=wanted.noted_by,
    )
