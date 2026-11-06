from pathlib import Path
import csv

from metermind.core.exceptions import ReadingStorageError


class ReadingFileStorage:
    def __init__(self, directory):
        self.directory = Path(directory)

    def save_readings_csv(self, file_name, readings):
        if not readings:
            raise ReadingStorageError("no readings to write")
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            path = self.directory / file_name
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(readings[0].keys()))
                writer.writeheader()
                writer.writerows(readings)
            return path
        except ReadingStorageError:
            raise
        except Exception as error:
            raise ReadingStorageError(str(error)) from error

    def load_readings_csv(self, file_name):
        path = self.directory / file_name
        try:
            with path.open(newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except Exception as error:
            raise ReadingStorageError(str(path)) from error

    def load_connection_objects(self, file_name):
        from metermind.core.entities import create_service_connection

        rows = self.load_readings_csv(file_name)
        connections = []
        for row in rows:
            try:
                connections.append(create_service_connection(row))
            except Exception:
                continue
        return connections


if __name__ == "__main__":
    from config import constants

    storage = ReadingFileStorage(Path(constants.DATA_DIRECTORY))
    loaded = storage.load_connection_objects(
        Path(constants.READING_BOOK_PREDICT_PATH).name
    )
    print(f"connections loaded: {len(loaded)}")
