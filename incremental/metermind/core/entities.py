from config.constants import (
    CONSUMER_CATEGORIES,
    SLAB_TABLE_INR_BY_CATEGORY,
    ELECTRICITY_DUTY_PERCENT_BY_CATEGORY,
    FIXED_CHARGE_INR_PER_KW_BY_CATEGORY,
    FIXED_CHARGE_INR_PER_HORSEPOWER,
    HORSEPOWER_PER_KILOWATT,
    SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY,
    SUBSIDY_INR_PER_UNIT_BY_CATEGORY,
    HOURS_IN_A_DAY,
    CAPACITY_ALLOWANCE_FACTOR,
    MINIMUM_CYCLE_DAYS,
    MAXIMUM_CYCLE_DAYS,
)
from metermind.core.exceptions import UnsupportedCategoryError
from metermind.core.tariff_calculations import calculate_units_consumed


class ServiceConnection:
    def __init__(
        self,
        account_number,
        consumer_category,
        sanctioned_load_kw,
        cycle_days,
        previous_reading,
        current_reading,
    ):
        if consumer_category not in CONSUMER_CATEGORIES:
            raise UnsupportedCategoryError(consumer_category)

        self.account_number = account_number
        self.consumer_category = consumer_category
        self.sanctioned_load_kw = sanctioned_load_kw
        self.cycle_days = cycle_days
        self.previous_reading = previous_reading
        self.current_reading = current_reading

        self.physical_maximum_units = (
            sanctioned_load_kw
            * HOURS_IN_A_DAY
            * cycle_days
            * CAPACITY_ALLOWANCE_FACTOR
        )
        self.units_consumed = calculate_units_consumed(
            previous_reading, current_reading, self.physical_maximum_units
        )

    def applicable_slab_table(self):
        return SLAB_TABLE_INR_BY_CATEGORY[self.consumer_category]

    def energy_charge_inr(self):
        energy_charge = 0.0
        previous_limit = 0.0
        for upper, rate in self.applicable_slab_table():
            slab_units = max(
                0.0, min(self.units_consumed, upper) - previous_limit
            )
            energy_charge += slab_units * rate
            previous_limit = upper
        return energy_charge

    def fixed_charge_inr(self):
        return (
            self.sanctioned_load_kw
            * FIXED_CHARGE_INR_PER_KW_BY_CATEGORY[self.consumer_category]
        )

    def electricity_duty_inr(self):
        return self.energy_charge_inr() * (
            ELECTRICITY_DUTY_PERCENT_BY_CATEGORY[self.consumer_category] / 100
        )

    def subsidy_inr(self):
        qualifying = SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY[self.consumer_category]
        if self.units_consumed <= qualifying:
            return (
                self.units_consumed
                * SUBSIDY_INR_PER_UNIT_BY_CATEGORY[self.consumer_category]
            )
        return 0.0

    def net_bill_inr(self):
        amount = (
            self.energy_charge_inr()
            + self.electricity_duty_inr()
            + self.fixed_charge_inr()
            - self.subsidy_inr()
        )
        return max(0.0, amount)

    def refusal_reasons(self):
        reasons = []
        if (
            self.current_reading < self.previous_reading
            and self.units_consumed == 0.0
        ):
            reasons.append(
                "the current reading is below the previous reading with no rollover"
            )
        if self.units_consumed > self.physical_maximum_units:
            reasons.append(
                "consumption is above what the sanctioned load could physically draw"
            )
        if not MINIMUM_CYCLE_DAYS <= self.cycle_days <= MAXIMUM_CYCLE_DAYS:
            reasons.append(
                "the billing cycle length is outside the permitted range"
            )
        return reasons

    def is_billable(self):
        return self.refusal_reasons() == []


class CommercialConnection(ServiceConnection):
    def energy_charge_inr(self):
        for upper, rate in self.applicable_slab_table():
            if self.units_consumed <= upper:
                return self.units_consumed * rate
        return 0.0


class AgriculturalConnection(ServiceConnection):
    def fixed_charge_inr(self):
        return (
            self.sanctioned_load_kw
            * HORSEPOWER_PER_KILOWATT
            * FIXED_CHARGE_INR_PER_HORSEPOWER
        )

    def subsidy_inr(self):
        return (
            self.units_consumed
            * SUBSIDY_INR_PER_UNIT_BY_CATEGORY[self.consumer_category]
        )


def create_service_connection(record):
    category = str(record["consumer_category"]).strip().lower()
    classes = {
        "domestic": ServiceConnection,
        "commercial": CommercialConnection,
        "agricultural": AgriculturalConnection,
    }
    if category not in classes:
        raise UnsupportedCategoryError(category)

    return classes[category](
        str(record["account_number"]).strip().upper(),
        category,
        float(record["sanctioned_load_kw"]),
        int(float(record["cycle_days"])),
        float(record["previous_reading"]),
        float(record["current_reading"]),
    )


if __name__ == "__main__":
    base = {
        "account_number": "ACC10000123",
        "sanctioned_load_kw": 3,
        "cycle_days": 30,
        "previous_reading": 0,
        "current_reading": 467,
    }
    for category in ("domestic", "commercial", "agricultural"):
        connection = create_service_connection(
            dict(base, consumer_category=category)
        )
        print(
            f"{category:<13}{connection.units_consumed:.0f} units on a "
            f"{connection.sanctioned_load_kw:g} kW connection -> "
            f"Rs. {connection.net_bill_inr()}"
        )
    print(
        "an agricultural cycle costs nothing because the rebate of Rs. 2.6 a unit "
        "is larger than the tariff of Rs. 2.25 a unit, and a bill is never negative"
    )
