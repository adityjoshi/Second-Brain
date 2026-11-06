import sqlite3
from pathlib import Path

import pandas as pd

from config import constants

READINGS_TABLE = "readings"


class ReadingDatabase:
    def __init__(self, database_path):
        self.database_path = str(database_path)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row

    def create_readings_table(self, book):
        frame = book.copy()
        self.connection.execute(f"DROP TABLE IF EXISTS {READINGS_TABLE}")

        column_defs = []
        for name in frame.columns:
            if name == "reading_id":
                column_defs.append("reading_id TEXT PRIMARY KEY")
            else:
                column_defs.append(f'"{name}" TEXT')

        self.connection.execute(
            f"CREATE TABLE {READINGS_TABLE} ({', '.join(column_defs)})"
        )

        placeholders = ", ".join(["?"] * len(frame.columns))
        quoted = ", ".join(f'"{c}"' for c in frame.columns)
        insert_sql = (
            f"INSERT INTO {READINGS_TABLE} ({quoted}) VALUES ({placeholders})"
        )

        rows = [
            tuple("" if pd.isna(value) else str(value) for value in record)
            for record in frame.itertuples(index=False, name=None)
        ]
        self.connection.executemany(insert_sql, rows)
        self.connection.commit()
        return len(rows)

    def find_reading_by_identifier(self, reading_identifier):
        cursor = self.connection.execute(
            f"SELECT * FROM {READINGS_TABLE} WHERE reading_id = ?",
            (reading_identifier,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def delete_reading_by_identifier(self, reading_identifier):
        from metermind.core.exceptions import ReadingStorageError

        cursor = self.connection.execute(
            f"DELETE FROM {READINGS_TABLE} WHERE reading_id = ?",
            (reading_identifier,),
        )
        self.connection.commit()
        if cursor.rowcount == 0:
            raise ReadingStorageError(reading_identifier)
        return cursor.rowcount


if __name__ == "__main__":
    database = ReadingDatabase(constants.READINGS_DATABASE_PATH)
    book = pd.read_csv(constants.CLEAN_READING_BOOK_PATH)
    stored = database.create_readings_table(book)
    print(f"stored: {stored}")
