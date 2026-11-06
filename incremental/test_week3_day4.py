"""Official Week 3 Day 4 cases."""

def test_week3_day4_signing_up_stores_a_hash_and_never_the_password():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application
    from metermind.api.routers.user_accounts import accounts

    client = TestClient(build_application())
    wanted = {"account_number": "ACC10000123", "email_address": "consumer.one@example.in",
              "password": "a-password-nobody-should-store"}
    made = client.post(f"{API_PREFIX}/accounts", json=wanted)
    assert made.status_code == 201, (
        f"a well formed sign-up should be created, got {made.status_code}")
    assert "password" not in made.json(), "the reply should never carry the password back"
    held = accounts["ACC10000123"]
    assert wanted["password"] not in held["hashed_password"], (
        "what is stored must not contain the password it was made from")
    assert client.post(f"{API_PREFIX}/accounts", json=wanted).status_code == 409, (
        "one account number cannot have two sign-ins")


def test_week3_day4_logging_in_returns_a_token_for_the_right_password_only():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    client.post(f"{API_PREFIX}/accounts", json={"account_number": "ACC10000124",
                                                "email_address": "two@example.in",
                                                "password": "the-right-password"})
    wrong = client.post(f"{API_PREFIX}/accounts/login",
                        json={"account_number": "ACC10000124", "password": "the-wrong-one"})
    assert wrong.status_code == 401, (
        f"the wrong password should not sign in, got {wrong.status_code}")
    right = client.post(f"{API_PREFIX}/accounts/login",
                        json={"account_number": "ACC10000124", "password": "the-right-password"})
    assert right.status_code == 200, "the right password should sign in"
    assert right.json()["access_token"], "signing in should hand back a token"


def test_week3_day4_the_book_needs_a_token_but_the_meter_reader_does_not():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000125", "meter_serial": "MTR-AB-123457",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    assert client.post(f"{API_PREFIX}/readings", json=body).status_code == 201, (
        "sending a reading in is a field operation, and a meter reader carries no token")
    assert client.get(f"{API_PREFIX}/readings").status_code == 401, (
        "reading the whole book is not a field operation and should need a token")
    assert client.get(f"{API_PREFIX}/health").status_code == 200, (
        "the health route stays open, or nothing can check the service is up")


def test_week3_day4_the_listing_can_be_narrowed_to_one_category_and_one_read_type():
    from fastapi.testclient import TestClient

    from config import constants
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    signed_in = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    body = {"account_number": "ACC10000126", "meter_serial": "MTR-AB-123458",
            "billing_period": "2026-06", "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    for category, read_type in (("domestic", "actual"), ("domestic", "estimated"),
                                ("commercial", "actual")):
        client.post(f"{API_PREFIX}/readings",
                    json=dict(body, consumer_category=category, read_type=read_type))
    everything = client.get(f"{API_PREFIX}/readings", headers=signed_in).json()
    narrowed = client.get(f"{API_PREFIX}/readings?consumer_category=commercial",
                          headers=signed_in).json()
    assert everything["total"] == 3, f"three readings went in, {everything['total']} listed"
    assert narrowed["total"] == 1, (
        f"one of the three is commercial, so the filter should leave one, not "
        f"{narrowed['total']}")
    by_read_type = client.get(f"{API_PREFIX}/readings?read_type=estimated",
                              headers=signed_in).json()
    assert by_read_type["total"] == 1, (
        f"each published filter has to narrow on a field a stored reading actually carries; "
        f"one of the three was estimated and this left {by_read_type['total']}")
    both = client.get(f"{API_PREFIX}/readings?consumer_category=domestic&read_type=estimated",
                      headers=signed_in).json()
    assert both["total"] == 1, (
        f"two filters given are both applied, and only one reading is domestic and estimated; "
        f"got {both['total']}")


def test_week3_day4_two_pages_are_disjoint_and_together_are_the_whole_book():
    from fastapi.testclient import TestClient

    from config import constants
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    signed_in = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    body = {"account_number": "ACC10000127", "meter_serial": "MTR-AB-123459",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    for _ in range(5):
        client.post(f"{API_PREFIX}/readings", json=body)
    first = client.get(f"{API_PREFIX}/readings?page=1&page_size=3", headers=signed_in).json()
    second = client.get(f"{API_PREFIX}/readings?page=2&page_size=3", headers=signed_in).json()
    on_first = {one["reading_id"] for one in first["readings"]}
    on_second = {one["reading_id"] for one in second["readings"]}
    assert not on_first & on_second, (
        f"a reading on two pages would be counted twice; {on_first & on_second} is on both")
    assert len(on_first | on_second) == first["total"] == 5, (
        f"the pages together should be the whole book of {first['total']}")
