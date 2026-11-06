from pathlib import Path

from sqlalchemy import Boolean, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import constants

Base = declarative_base()


class ConnectionRow(Base):
    __tablename__ = "connections"

    account_number = Column(String, primary_key=True)
    consumer_name = Column(String, nullable=False)
    consumer_category = Column(String, nullable=False)
    tariff_code = Column(String, nullable=False)
    sanctioned_load_kw = Column(Float, nullable=False)
    meter_serial = Column(String, nullable=False, unique=True)
    division = Column(String, nullable=False)
    subdivision = Column(String, nullable=False)


class ReadingRow(Base):
    __tablename__ = "readings"

    reading_id = Column(String, primary_key=True)
    account_number = Column(String, nullable=False, index=True)
    meter_serial = Column(String, nullable=False)
    consumer_category = Column(String, nullable=False)
    billing_period = Column(String, nullable=False, index=True)
    sanctioned_load_kw = Column(Float, nullable=False)
    cycle_days = Column(Integer, nullable=False)
    previous_reading = Column(Float, nullable=False)
    current_reading = Column(Float, nullable=False)
    read_type = Column(String, nullable=False, default="actual")
    case_status = Column(String, nullable=True)
    is_billable = Column(Boolean, nullable=True)


def build_session_factory(database_path):
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


if __name__ == "__main__":
    factory = build_session_factory(constants.ORM_DATABASE_PATH)
    session = factory()
    try:
        names = sorted(Base.metadata.tables.keys())
        print(f"tables: {names}")
    finally:
        session.close()
