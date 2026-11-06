from config import constants
from metermind.api.orm_models import ReadingRow, build_session_factory
from metermind.api.repository import (
    STORED_READING_FIELDS,
    ReadingRepository,
    _as_stored_reading,
)
from metermind.core.exceptions import ReadingStorageError


class SqlReadingRepository(ReadingRepository):
    def __init__(self, database_path=constants.READINGS_DATABASE_PATH):
        self._session_factory = build_session_factory(database_path)
        self._next_number = self._highest_reading_number() + 1

    def _highest_reading_number(self):
        session = self._session_factory()
        try:
            highest = 40000000
            for (reading_id,) in session.query(ReadingRow.reading_id).all():
                if not reading_id or not str(reading_id).startswith("RDG"):
                    continue
                try:
                    highest = max(highest, int(str(reading_id)[3:]))
                except ValueError:
                    continue
            return highest
        finally:
            session.close()

    def _allocate_reading_id(self):
        reading_id = f"RDG{self._next_number:08d}"
        self._next_number += 1
        return reading_id

    def _row_as_stored(self, row):
        return {field: getattr(row, field) for field in STORED_READING_FIELDS}

    def add_reading(self, reading):
        stored = _as_stored_reading(reading, self._allocate_reading_id())
        session = self._session_factory()
        try:
            session.add(ReadingRow(**stored))
            session.commit()
            return dict(stored)
        finally:
            session.close()

    def get_reading(self, reading_identifier):
        session = self._session_factory()
        try:
            row = session.get(ReadingRow, reading_identifier)
            if row is None:
                raise ReadingStorageError(reading_identifier)
            return self._row_as_stored(row)
        finally:
            session.close()

    def replace_reading(self, reading_identifier, reading):
        session = self._session_factory()
        try:
            row = session.get(ReadingRow, reading_identifier)
            if row is None:
                raise ReadingStorageError(reading_identifier)
            stored = _as_stored_reading(reading, reading_identifier)
            for field in STORED_READING_FIELDS:
                if field == "reading_id":
                    continue
                setattr(row, field, stored[field])
            session.commit()
            return self._row_as_stored(row)
        finally:
            session.close()

    def list_readings(self):
        session = self._session_factory()
        try:
            rows = (
                session.query(ReadingRow)
                .order_by(ReadingRow.reading_id.asc())
                .all()
            )
            return [self._row_as_stored(row) for row in rows]
        finally:
            session.close()

    def remove_reading(self, reading_identifier):
        session = self._session_factory()
        try:
            row = session.get(ReadingRow, reading_identifier)
            if row is None:
                raise ReadingStorageError(reading_identifier)
            session.delete(row)
            session.commit()
        finally:
            session.close()
