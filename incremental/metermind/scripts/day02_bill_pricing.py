import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.constants import (
    ELECTRICITY_DUTY_PERCENT_BY_CATEGORY,
    FIXED_CHARGE_INR_PER_HORSEPOWER,
    FIXED_CHARGE_INR_PER_KW_BY_CATEGORY,
    HORSEPOWER_PER_KILOWATT,
    METER_ROLLOVER_UNITS,
    SLAB_TABLE_INR_BY_CATEGORY,
    SUBSIDY_INR_PER_UNIT_BY_CATEGORY,
    SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY,
    TELESCOPIC_CATEGORIES,
)


def units_consumed(previous_reading, current_reading, physical_maximum_units):
    if current_reading >= previous_reading:
        return current_reading - previous_reading
    if previous_reading + physical_maximum_units >= METER_ROLLOVER_UNITS:
        rollover_units = current_reading + METER_ROLLOVER_UNITS - previous_reading
        if rollover_units <= physical_maximum_units:
            return rollover_units
    return 0.0


def slab_energy_charge(consumer_category, units):
    blocks = SLAB_TABLE_INR_BY_CATEGORY[consumer_category]
    if consumer_category in TELESCOPIC_CATEGORIES:
        energy_charge = 0.0
        previous_limit = 0.0
        remaining = units
        for limit, rate in blocks:
            if remaining <= 0:
                break
            slab_units = min(remaining, limit - previous_limit)
            energy_charge += slab_units * rate
            remaining -= slab_units
            previous_limit = limit
        return energy_charge
    for limit, rate in blocks:
        if units <= limit:
            return units * rate
    return units * blocks[-1][1]


def apply_fixed_charge(consumer_category, sanctioned_load_kw):
    if consumer_category == "agricultural":
        return sanctioned_load_kw * HORSEPOWER_PER_KILOWATT * FIXED_CHARGE_INR_PER_HORSEPOWER
    return sanctioned_load_kw * FIXED_CHARGE_INR_PER_KW_BY_CATEGORY[consumer_category]


def apply_electricity_duty(consumer_category, energy_charge_inr):
    return energy_charge_inr * ELECTRICITY_DUTY_PERCENT_BY_CATEGORY[consumer_category] / 100


def apply_subsidy(consumer_category, units):
    qualifying = SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY[consumer_category]
    if units <= qualifying:
        return units * SUBSIDY_INR_PER_UNIT_BY_CATEGORY[consumer_category]
    return 0.0


def net_bill_amount(consumer_category, units, sanctioned_load_kw):
    energy_charge = slab_energy_charge(consumer_category, units)
    fixed_charge = apply_fixed_charge(consumer_category, sanctioned_load_kw)
    electricity_duty = apply_electricity_duty(consumer_category, energy_charge)
    rebate = apply_subsidy(consumer_category, units)
    amount = energy_charge + fixed_charge + electricity_duty - rebate
    if amount < 0:
        amount = 0.0
    return round(amount, 2)


class MeterReading:
    def __init__(
        self,
        account_number,
        consumer_category,
        sanctioned_load_kw,
        cycle_days,
        previous_reading,
        current_reading,
    ):
        self.account_number = account_number
        self.consumer_category = consumer_category
        self.sanctioned_load_kw = sanctioned_load_kw
        self.cycle_days = cycle_days
        self.previous_reading = previous_reading
        self.current_reading = current_reading

    def price(self):
        physical_maximum_units = (
            self.sanctioned_load_kw * 24 * self.cycle_days * 1.10
        )
        used = units_consumed(
            self.previous_reading, self.current_reading, physical_maximum_units
        )
        amount = net_bill_amount(
            self.consumer_category, used, self.sanctioned_load_kw
        )
        return float(used), amount


if __name__ == "__main__":
    account_number = input().strip().upper()
    consumer_category = input().strip().lower()
    sanctioned_load_kw = float(input())
    cycle_days = int(input())
    previous_reading = float(input())
    current_reading = float(input())
    arrears_inr = float(input())
    late_payment_surcharge_percent = float(input())

    reading = MeterReading(
        account_number,
        consumer_category,
        sanctioned_load_kw,
        cycle_days,
        previous_reading,
        current_reading,
    )
    used, net = reading.price()
    energy = slab_energy_charge(consumer_category, used)
    fixed = apply_fixed_charge(consumer_category, sanctioned_load_kw)
    surcharge = arrears_inr * late_payment_surcharge_percent / 100
    payable = net + arrears_inr + surcharge

    print(f"Account number: {account_number}")
    print(f"Consumer category: {consumer_category}")
    print(f"Units consumed: {used:.1f}")
    print(f"Energy charge: {energy:.1f}")
    print(f"Fixed charge: {fixed:.1f}")
    print(f"Current demand: {net:.2f}")
    print(f"Amount payable: {payable:.2f}")
