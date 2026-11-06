import abc
import copy

from metermind.core.exceptions import ReadingStorageError

STORED_READING_FIELDS = (
    "reading_id",
    "account_number",
    "meter_serial",
    "consumer_category",
    "billing_period",
    "sanctioned_load_kw",
    "cycle_days",
    "previous_reading",
    "current_reading",
    "read_type",
    "case_status",
)


def _as_stored_reading(reading, reading_identifier=None):
    stored = {}
    for field in STORED_READING_FIELDS:
        if field == "reading_id":
            stored[field] = reading_identifier
        elif field in reading:
            stored[field] = reading[field]
        elif field == "read_type":
            stored[field] = "actual"
        else:
            stored[field] = None
    return stored


class ReadingRepository(abc.ABC):
    @abc.abstractmethod
    def add_reading(self, reading):
        raise NotImplementedError

    @abc.abstractmethod
    def get_reading(self, reading_identifier):
        raise NotImplementedError

    @abc.abstractmethod
    def replace_reading(self, reading_identifier, reading):
        raise NotImplementedError

    @abc.abstractmethod
    def list_readings(self):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_reading(self, reading_identifier):
        raise NotImplementedError


class InMemoryReadingRepository(ReadingRepository):
    def __init__(self):
        self._readings = {}
        self._next_number = 40000001

    def add_reading(self, reading):
        reading_id = f"RDG{self._next_number:08d}"
        self._next_number += 1
        stored = _as_stored_reading(reading, reading_id)
        self._readings[reading_id] = stored
        return copy.deepcopy(stored)

    def get_reading(self, reading_identifier):
        if reading_identifier not in self._readings:
            raise ReadingStorageError(reading_identifier)
        return copy.deepcopy(self._readings[reading_identifier])

    def list_readings(self):
        return [
            copy.deepcopy(self._readings[reading_id])
            for reading_id in sorted(self._readings)
        ]

    def replace_reading(self, reading_identifier, reading):
        if reading_identifier not in self._readings:
            raise ReadingStorageError(reading_identifier)
        stored = _as_stored_reading(reading, reading_identifier)
        self._readings[reading_identifier] = stored
        return copy.deepcopy(stored)

    def remove_reading(self, reading_identifier):
        if reading_identifier not in self._readings:
            raise ReadingStorageError(reading_identifier)
        del self._readings[reading_identifier]
