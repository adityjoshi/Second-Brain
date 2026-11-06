from pathlib import Path
from time import monotonic, time

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import constants

REQUEST_LOG_FIELDS = (
    "received_at",
    "method",
    "path",
    "status_code",
    "duration_ms",
)


class RequestLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, application, log_path=constants.REQUEST_LOG_PATH):
        super().__init__(application)
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    async def dispatch(self, request: Request, call_next):
        started = monotonic()
        received_at = time()
        response = await call_next(request)
        duration_ms = round((monotonic() - started) * 1000, 3)
        values = {
            "received_at": received_at,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
        line = "|".join(str(values[field]) for field in REQUEST_LOG_FIELDS)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return response


class FixedWindowRateLimiter(BaseHTTPMiddleware):
    def __init__(
        self,
        application,
        allowed=constants.REQUESTS_ALLOWED_PER_WINDOW,
        window_seconds=constants.RATE_LIMIT_WINDOW_SECONDS,
    ):
        super().__init__(application)
        self.allowed = allowed
        self.window_seconds = window_seconds
        self._windows = {}

    def _caller_key(self, request: Request):
        if request.client is None:
            return "unknown"
        return request.client.host

    def _window_index(self):
        return int(time()) // self.window_seconds

    async def dispatch(self, request: Request, call_next):
        caller = self._caller_key(request)
        window = self._window_index()
        state = self._windows.get(caller)
        if state is None or state[0] != window:
            state = (window, 0)
        count = state[1] + 1
        self._windows[caller] = (window, count)
        if count > self.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "too many requests in this window"},
            )
        return await call_next(request)


def add_cross_origin_policy(application):
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(constants.ALLOWED_ORIGINS),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    return application


if __name__ == "__main__":
    print(f"fields written for every request: {REQUEST_LOG_FIELDS}")
    print(
        f"{constants.REQUESTS_ALLOWED_PER_WINDOW} requests are allowed in each "
        f"{constants.RATE_LIMIT_WINDOW_SECONDS} second window"
    )
    print(f"origins the browser may call from: {constants.ALLOWED_ORIGINS}")
