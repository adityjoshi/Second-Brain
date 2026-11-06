"""Official Week 3 Day 2–3 cases (paste from harness)."""

def test_week3_day2_the_factory_returns_the_store_it_was_asked_for(tmp_path):
    from metermind.api.application_factory import choose_reading_repository
    from metermind.api.repository import InMemoryReadingRepository
    from metermind.api.sql_repository import SqlReadingRepository

    assert isinstance(choose_reading_repository(""), InMemoryReadingRepository), (
        "given no database to open, the factory should return the in-memory store")
    assert isinstance(choose_reading_repository(tmp_path / "chosen.sqlite"),
                      SqlReadingRepository), (
        "given a database to open, the factory should return the SQL store instead")


def test_week3_day2_every_request_is_written_down_with_its_fields_in_order(tmp_path):
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application
    from metermind.api.middleware import REQUEST_LOG_FIELDS, RequestLogMiddleware

    log_path = tmp_path / "requests.log"
    application = build_application()
    application.user_middleware = [one for one in application.user_middleware
                                   if one.cls is not RequestLogMiddleware]
    application.add_middleware(RequestLogMiddleware, log_path=log_path)
    application.middleware_stack = application.build_middleware_stack()
    TestClient(application).get(f"{API_PREFIX}/health")
    written = [line for line in log_path.read_text().splitlines() if line.strip()]
    assert len(written) == 1, f"one request should write one line, not {len(written)}"
    assert len(written[0].split("|")) == len(REQUEST_LOG_FIELDS), (
        f"the line should carry the {len(REQUEST_LOG_FIELDS)} published fields, "
        f"got {written[0]!r}")
    assert "/health" in written[0], "the line should say which path was asked for"


def test_week3_day2_calls_past_the_limit_in_one_window_are_refused():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application
    from metermind.api.middleware import FixedWindowRateLimiter

    application = build_application()
    application.user_middleware = [one for one in application.user_middleware
                                   if one.cls is not FixedWindowRateLimiter]
    application.add_middleware(FixedWindowRateLimiter, allowed=3, window_seconds=3600)
    application.middleware_stack = application.build_middleware_stack()
    client = TestClient(application)
    allowed = [client.get(f"{API_PREFIX}/health").status_code for _ in range(3)]
    assert allowed == [200, 200, 200], f"the first three should be allowed, got {allowed}"
    assert client.get(f"{API_PREFIX}/health").status_code == 429, (
        "the call past the limit should be refused, and refused as too many requests")


def test_week3_day2_a_stored_password_is_not_the_password():
    from metermind.api.password_hashing import hash_password, verify_password

    kept = hash_password("a-password-nobody-should-store")
    assert "a-password-nobody-should-store" not in kept, (
        "the stored value must not contain the password it was made from")
    assert verify_password("a-password-nobody-should-store", kept), "the right one should pass"
    assert not verify_password("something-else", kept), "any other one should not"
    assert not verify_password("anything at all", "this-was-never-a-hash"), (
        "a stored value that is not a hash answers False rather than raising; a sign-in route "
        "must be able to answer a bad attempt, not fall over on it")


def test_week3_day3_the_ladder_names_five_states_and_three_of_them_are_the_end():
    from config import constants
    from metermind.api.case_transitions import ALLOWED_TRANSITIONS

    assert len(ALLOWED_TRANSITIONS) == 6, (
        f"the ladder should publish every state a case can be in, got "
        f"{sorted(ALLOWED_TRANSITIONS)}")
    assert constants.INITIAL_CASE_STATUS in ALLOWED_TRANSITIONS, (
        "a case starts somewhere, and that somewhere should be on the ladder")
    ends = [state for state, moves in ALLOWED_TRANSITIONS.items() if not moves]
    assert len(ends) == 3, (
        f"three states should be the end of the road with nothing after them, got {ends}")


def test_week3_day3_a_re_visit_may_send_an_inspected_case_back_to_be_assigned_again():
    from metermind.api.case_transitions import move_case_status

    assert move_case_status("inspected", "assigned") == "assigned", (
        "an inspection that settles nothing has to be able to order another visit")
    assert move_case_status("inspected", "regularised") == "regularised", (
        "and an inspection that settles it has to be able to close it")


def test_week3_day3_a_move_the_ladder_does_not_publish_is_refused():
    from metermind.api.case_transitions import move_case_status
    from metermind.core.exceptions import MeterMindError

    for from_status, wanted in (("raised", "regularised"), ("regularised", "assigned"),
                                ("closed_no_fault", "inspected"), ("assigned", "billed_back")):
        try:
            move_case_status(from_status, wanted)
            raise AssertionError(f"{from_status} to {wanted} is not on the ladder and passed")
        except MeterMindError:
            pass


def test_week3_day3_a_token_carries_a_role_and_one_signed_elsewhere_is_refused():
    import os

    from fastapi import HTTPException

    from config import constants
    from metermind.api.access_control import issue_token, read_signing_secret, read_token

    carried = read_token(issue_token("je/1180", constants.INSPECTOR_ROLE))
    assert carried["sub"] == "je/1180", "the token should carry who it was issued to"
    assert carried["role"] == constants.INSPECTOR_ROLE, "and what they are allowed to do"
    was = os.environ.get(constants.TOKEN_SECRET_ENVIRONMENT_NAME)
    somewhere_else = "a-different-secret-entirely-and-long-enough"
    try:
        os.environ[constants.TOKEN_SECRET_ENVIRONMENT_NAME] = somewhere_else
        assert read_signing_secret() == somewhere_else, (
            "the signing secret should be read from the environment, not fixed in the code")
        try:
            read_token(issue_token("je/1180", constants.INSPECTOR_ROLE) + "x")
            raise AssertionError("a token that does not verify should have been refused")
        except HTTPException:
            pass
    finally:
        if was is None:
            del os.environ[constants.TOKEN_SECRET_ENVIRONMENT_NAME]
        else:
            os.environ[constants.TOKEN_SECRET_ENVIRONMENT_NAME] = was


def test_week3_day3_only_an_inspector_moves_a_case_and_every_move_is_written_down(tmp_path):
    from fastapi.testclient import TestClient

    from config import constants
    from metermind.api import routers
    from metermind.api.access_control import AUDIT_TRAIL_FIELDS, issue_token
    from metermind.api.application_factory import API_PREFIX, build_application

    trail = tmp_path / "audit_trail.csv"
    routers.readings.record_audit_entry.__defaults__ = (str(trail),)
    client = TestClient(build_application())
    body = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    identifier = client.post(f"{API_PREFIX}/readings", json=body).json()["reading_id"]
    where = f"{API_PREFIX}/readings/{identifier}/status"
    wanted = {"wanted_status": "assigned", "noted_by": "je/1180"}
    assert client.patch(where, json=wanted).status_code == 401, "no token, no move"
    consumer = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    assert client.patch(where, json=wanted, headers=consumer).status_code == 403, (
        "a consumer holds a valid token and still may not move a case")
    inspector = {"Authorization": f"Bearer {issue_token('je/1180', constants.INSPECTOR_ROLE)}"}
    moved = client.patch(where, json=wanted, headers=inspector)
    assert moved.status_code == 200 and moved.json()["to_status"] == "assigned", (
        f"an inspector should be able to move it, got {moved.status_code}")
    assert client.patch(where, json={"wanted_status": "regularised", "noted_by": "je/1180"},
                        headers=inspector).status_code == 409, (
        "a move the ladder does not publish should be refused, and the case left where it was")
    rows = [line for line in trail.read_text().splitlines() if line.strip()]
    assert rows[0].split(",") == list(AUDIT_TRAIL_FIELDS), (
        f"the trail should open with its published columns, got {rows[0]!r}")
    assert len(rows) == 2, f"one accepted move should write one row, got {len(rows) - 1}"
    assert "je/1180" in rows[1] and "raised" in rows[1] and "assigned" in rows[1], (
        f"the row should say who moved it and between which two states, got {rows[1]!r}")
