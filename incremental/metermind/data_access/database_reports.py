from pathlib import Path

from config import constants
from metermind.data_access.database_loader import READINGS_TABLE

_HELD_EXCEPTION_CLASSES_SQL = ", ".join(
    f"'{exception_class}'" for exception_class in constants.HELD_EXCEPTION_CLASSES
)

# The clean book already carries exception_class / read_type / division. There is no
# is_exception column — every kept row is counted, and “needs a look” / “estimated”
# are shares within each group.

EXCEPTION_RATE_QUERY = f"""
SELECT
    consumer_category,
    COUNT(*) AS flagged_cycles,
    ROUND(
        AVG(
            CASE
                WHEN LOWER(exception_class) IN ({_HELD_EXCEPTION_CLASSES_SQL}) THEN 1.0
                ELSE 0.0
            END
        ),
        4
    ) AS share_needing_look
FROM {READINGS_TABLE}
GROUP BY consumer_category
ORDER BY share_needing_look DESC, consumer_category ASC
"""

ESTIMATED_READ_QUERY = f"""
SELECT
    billing_period,
    COUNT(*) AS flagged_cycles,
    ROUND(
        AVG(
            CASE
                WHEN LOWER(read_type) = 'estimated' THEN 1.0
                ELSE 0.0
            END
        ),
        4
    ) AS estimated_share
FROM {READINGS_TABLE}
GROUP BY billing_period
ORDER BY billing_period ASC
"""

BILLED_UNITS_QUERY = f"""
SELECT
    division,
    COUNT(*) AS flagged_cycles,
    ROUND(SUM(CAST(units_consumed AS REAL)), 4) AS billed_units
FROM {READINGS_TABLE}
GROUP BY division
ORDER BY billed_units DESC, division ASC
"""


def exception_rate_by_category(database):
    cursor = database.connection.execute(EXCEPTION_RATE_QUERY)
    return [dict(row) for row in cursor.fetchall()]


def estimated_read_share_by_month(database):
    cursor = database.connection.execute(ESTIMATED_READ_QUERY)
    return [dict(row) for row in cursor.fetchall()]


def billed_units_by_division(database):
    cursor = database.connection.execute(BILLED_UNITS_QUERY)
    return [dict(row) for row in cursor.fetchall()]


def write_report_files(database, report_path):
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    sections = (
        ("EXCEPTION RATE BY CATEGORY", exception_rate_by_category(database)),
        ("ESTIMATED READ SHARE BY MONTH", estimated_read_share_by_month(database)),
        ("BILLED UNITS BY DIVISION", billed_units_by_division(database)),
    )

    lines = []
    for heading, rows in sections:
        lines.append(heading)
        if rows:
            columns = list(rows[0].keys())
            lines.append(",".join(columns))
            for row in rows:
                lines.append(",".join(str(row[column]) for column in columns))
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


if __name__ == "__main__":
    from metermind.data_access.database_loader import ReadingDatabase

    database = ReadingDatabase(constants.READINGS_DATABASE_PATH)
    written = write_report_files(database, constants.READING_REPORTS_PATH)
    print(f"written: {written}")
