from metermind.api.middleware import (
    FixedWindowRateLimiter,
    RequestLogMiddleware,
    add_cross_origin_policy,
)
from metermind.api.repository import InMemoryReadingRepository
from metermind.api.routers import assistant, readings, screening, user_accounts
from metermind.api.schemas import HealthReply
from metermind.api.sql_repository import SqlReadingRepository
from config import constants
from fastapi import FastAPI

API_PREFIX = "/api/v1"
SERVICE_NAME = "metermind"


def choose_reading_repository(database_path):
    if not database_path:
        return InMemoryReadingRepository()
    return SqlReadingRepository(database_path)


def read_health():
    return HealthReply(service=SERVICE_NAME, status="up")


def build_application(database_path=""):
    application = FastAPI(title=SERVICE_NAME)
    readings.reading_repository = choose_reading_repository(database_path)
    application.add_api_route(
        f"{API_PREFIX}/health",
        read_health,
        methods=["GET"],
        response_model=HealthReply,
    )
    application.include_router(readings.router, prefix=API_PREFIX)
    application.include_router(user_accounts.router, prefix=API_PREFIX)
    application.include_router(screening.router, prefix=API_PREFIX)
    application.include_router(assistant.router, prefix=API_PREFIX)
    application.add_middleware(RequestLogMiddleware)
    application.add_middleware(FixedWindowRateLimiter)
    add_cross_origin_policy(application)
    return application


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        build_application(constants.ORM_DATABASE_PATH),
        host="127.0.0.1",
        port=8000,
    )
