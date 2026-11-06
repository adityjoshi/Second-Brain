import csv
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import constants

AUDIT_TRAIL_FIELDS = (
    "recorded_at",
    "actor",
    "role",
    "reading_id",
    "from_status",
    "to_status",
)

bearer_scheme = HTTPBearer(auto_error=False)


def read_signing_secret():
    named = os.environ.get(constants.TOKEN_SECRET_ENVIRONMENT_NAME)
    if named:
        return named
    return constants.DEVELOPMENT_SECRET


def issue_token(subject, role):
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=constants.TOKEN_VALID_MINUTES
    )
    payload = {"sub": subject, "role": role, "exp": expires}
    return jwt.encode(payload, read_signing_secret(), algorithm="HS256")


def read_token(token):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="the token could not be read",
        )
    try:
        return jwt.decode(token, read_signing_secret(), algorithms=["HS256"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="the token could not be read",
        )


def require_inspector(
    carried: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = None if carried is None else carried.credentials
    payload = read_token(token)
    if payload.get("role") != constants.INSPECTOR_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"role {constants.INSPECTOR_ROLE} is required",
        )
    return payload


def require_signed_in(
    carried: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = None if carried is None else carried.credentials
    return read_token(token)


def record_audit_entry(
    actor,
    role,
    reading_identifier,
    from_status,
    to_status,
    trail_path=constants.AUDIT_TRAIL_PATH,
):
    path = Path(trail_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    row = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "role": role,
        "reading_id": reading_identifier,
        "from_status": from_status,
        "to_status": to_status,
    }
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(AUDIT_TRAIL_FIELDS))
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return path


if __name__ == "__main__":
    token = issue_token("je/1180", constants.INSPECTOR_ROLE)
    print(f"issued: {token}")
    print(f"reads back as: {read_token(token)}")
