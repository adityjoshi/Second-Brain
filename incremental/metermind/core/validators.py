import re

from config.constants import (
    ACCOUNT_NUMBER_PATTERN,
    METER_SERIAL_PATTERN,
    BILLING_PERIOD_PATTERN,
    EMAIL_ADDRESS_PATTERN,
)


def _as_text(value):
    if not isinstance(value, str):
        return None
    return value.strip()


def validate_account_number(account_number):
    text = _as_text(account_number)
    if text is None:
        return False
    return bool(re.fullmatch(ACCOUNT_NUMBER_PATTERN, text))


def validate_meter_serial(meter_serial):
    text = _as_text(meter_serial)
    if text is None:
        return False
    return bool(re.fullmatch(METER_SERIAL_PATTERN, text))


def validate_billing_period(billing_period):
    text = _as_text(billing_period)
    if text is None:
        return False
    return bool(re.fullmatch(BILLING_PERIOD_PATTERN, text))


def validate_email_address(email_address):
    text = _as_text(email_address)
    if text is None:
        return False
    return bool(re.fullmatch(EMAIL_ADDRESS_PATTERN, text.lower()))


if __name__ == "__main__":
    print(
        f"account number ACC10000123    well formed: "
        f"{validate_account_number('ACC10000123')}"
    )
    print(
        f"account number ACC1           well formed: "
        f"{validate_account_number('ACC1')}"
    )
    print(
        f"billing period 2026-06        well formed: "
        f"{validate_billing_period('2026-06')}"
    )
    print(
        f"billing period 2026-13        well formed: "
        f"{validate_billing_period('2026-13')}"
    )
