UNLIMITED_UNITS = 1000000
METER_CEILING_UNITS = 100000
HORSEPOWER_PER_KILOWATT = 1.34102
FIXED_CHARGE_PER_HORSEPOWER_INR = 22.0

SLAB_RATES_INR = {
    "domestic": ((100, 3.50), (200, 4.90), (400, 6.30), (UNLIMITED_UNITS, 7.10)),
    "commercial": ((200, 7.40), (500, 8.60), (UNLIMITED_UNITS, 9.80)),
    "agricultural": ((UNLIMITED_UNITS, 2.25),),
}
TELESCOPIC_CATEGORIES = ("domestic", "agricultural")
FIXED_CHARGE_PER_KW_INR = {"domestic": 50.0, "commercial": 145.0}
ELECTRICITY_DUTY_PERCENT = {"domestic": 5.0, "commercial": 9.0, "agricultural": 0.0}
REBATE_PER_UNIT_INR = {"domestic": 1.50, "commercial": 0.0, "agricultural": 2.60}
REBATE_QUALIFYING_UNITS = {"domestic": 100, "commercial": 0, "agricultural": UNLIMITED_UNITS}


def units_consumed(previous_reading, current_reading, physical_maximum_units):
    if current_reading >= previous_reading:
        return current_reading - previous_reading
    if previous_reading + physical_maximum_units >= METER_CEILING_UNITS:
        rollover_units = current_reading + METER_CEILING_UNITS - previous_reading
        if rollover_units <= physical_maximum_units:
            return rollover_units
    return 0.0


def slab_energy_charge(consumer_category, units):
    blocks = SLAB_RATES_INR[consumer_category]
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
        return sanctioned_load_kw * HORSEPOWER_PER_KILOWATT * FIXED_CHARGE_PER_HORSEPOWER_INR
    return sanctioned_load_kw * FIXED_CHARGE_PER_KW_INR[consumer_category]


def apply_electricity_duty(consumer_category, energy_charge_inr):
    return energy_charge_inr * ELECTRICITY_DUTY_PERCENT[consumer_category] / 100


def apply_subsidy(consumer_category, units):
    qualifying = REBATE_QUALIFYING_UNITS[consumer_category]
    if units <= qualifying:
        return units * REBATE_PER_UNIT_INR[consumer_category]
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
