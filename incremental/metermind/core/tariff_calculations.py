from config.constants import (
    SLAB_TABLE_INR_BY_CATEGORY,
    FIXED_CHARGE_INR_PER_KW_BY_CATEGORY,
    FIXED_CHARGE_INR_PER_HORSEPOWER,
    HORSEPOWER_PER_KILOWATT,
    ELECTRICITY_DUTY_PERCENT_BY_CATEGORY,
    SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY,
    SUBSIDY_INR_PER_UNIT_BY_CATEGORY,
    UNLIMITED_UNITS,
    METER_ROLLOVER_UNITS,
    CONSUMER_CATEGORIES,
    TELESCOPIC_CATEGORIES,
)
import numpy as np
import pandas as pd

def calculate_units_consumed(

    previous_reading,

    current_reading,

    physical_maximum_units,

):

    if current_reading >= previous_reading:

        return current_reading - previous_reading

    if previous_reading + physical_maximum_units < METER_ROLLOVER_UNITS:

        return 0.0

    rollover_units = (

        current_reading

        + METER_ROLLOVER_UNITS

        - previous_reading

    )

    if rollover_units <= physical_maximum_units:

        return rollover_units

    return 0.0

# 
def calculate_slab_energy_charge(consumer_category, units, blocks=None):
    if blocks is None:
        blocks = SLAB_TABLE_INR_BY_CATEGORY[consumer_category]

    if consumer_category not in TELESCOPIC_CATEGORIES:
        for limit, rate in blocks:
            if limit is None or units <= limit:
                return units * rate
        return units * blocks[-1][1]

    energy_charge = 0.0
    remaining_units = units
    previous_limit = 0
    for limit, rate in blocks:
        if remaining_units <= 0:
            break
        if limit is None:
            slab_units = remaining_units
        else:
            slab_units = min(remaining_units, limit - previous_limit)
        energy_charge += slab_units * rate
        remaining_units -= slab_units
        if limit is not None:
            previous_limit = limit
    return energy_charge


def apply_fixed_charge(consumer_category, sanctioned_load_kw):
    if consumer_category == "agricultural":
        return (
            sanctioned_load_kw
            * HORSEPOWER_PER_KILOWATT
            * FIXED_CHARGE_INR_PER_HORSEPOWER
        )
    return sanctioned_load_kw * FIXED_CHARGE_INR_PER_KW_BY_CATEGORY[consumer_category]


def apply_electricity_duty(consumer_category, energy_charge):
    return energy_charge * ELECTRICITY_DUTY_PERCENT_BY_CATEGORY[consumer_category] / 100


def apply_subsidy(consumer_category, units):
    qualifying_units = SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY[consumer_category]
    rebate_per_unit = SUBSIDY_INR_PER_UNIT_BY_CATEGORY[consumer_category]
    if qualifying_units is None:
        return 0.0
    if units <= qualifying_units:
        return units * rebate_per_unit
    return 0.0


def calculate_bill_amount(consumer_category, units, sanctioned_load_kw):
    energy_charge = calculate_slab_energy_charge(consumer_category, units)
    fixed_charge = apply_fixed_charge(consumer_category, sanctioned_load_kw)
    electricity_duty = apply_electricity_duty(consumer_category, energy_charge)
    rebate = apply_subsidy(consumer_category, units)
    amount = energy_charge + fixed_charge + electricity_duty - rebate
    if amount < 0:
        amount = 0.0
    return amount


def calculate_prorated_slab_limits(blocks, day_share):
    result = []
    for limit, rate in blocks:
        if limit is None or limit >= UNLIMITED_UNITS:
            result.append((limit, rate))
        else:
            result.append((limit * day_share, rate))
    return result


def calculate_prorated_energy_charge(
    consumer_category,
    units,
    total_cycle_days,
    days_before_change,
    old_blocks,
    new_blocks,
):
    days_after_change = total_cycle_days - days_before_change
    old_share = days_before_change / total_cycle_days
    new_share = days_after_change / total_cycle_days
    old_charge = calculate_slab_energy_charge(
        consumer_category,
        units * old_share,
        calculate_prorated_slab_limits(old_blocks, old_share),
    )
    new_charge = calculate_slab_energy_charge(
        consumer_category,
        units * new_share,
        calculate_prorated_slab_limits(new_blocks, new_share),
    )
    return old_charge + new_charge


def calculate_bill_amounts(book):
    """Price every row of a reading book without looping over rows."""
   

    category = book["consumer_category"].astype(str).str.strip().str.lower()
    units = book["units_consumed"].astype(float)
    load = book["sanctioned_load_kw"].astype(float)

    domestic = category == "domestic"
    commercial = category == "commercial"
    agricultural = category == "agricultural"

    energy = pd.Series(0.0, index=book.index)
    fixed = pd.Series(0.0, index=book.index)
    duty = pd.Series(0.0, index=book.index)
    rebate = pd.Series(0.0, index=book.index)

    # Domestic — telescopic slabs from constants
    d0, r0 = SLAB_TABLE_INR_BY_CATEGORY["domestic"][0]
    d1, r1 = SLAB_TABLE_INR_BY_CATEGORY["domestic"][1]
    d2, r2 = SLAB_TABLE_INR_BY_CATEGORY["domestic"][2]
    _, r3 = SLAB_TABLE_INR_BY_CATEGORY["domestic"][3]
    u = units[domestic]
    energy.loc[domestic] = (
        np.minimum(u, d0) * r0
        + np.clip(u - d0, 0, d1 - d0) * r1
        + np.clip(u - d1, 0, d2 - d1) * r2
        + np.maximum(u - d2, 0) * r3
    )
    fixed.loc[domestic] = load[domestic] * FIXED_CHARGE_INR_PER_KW_BY_CATEGORY["domestic"]
    duty.loc[domestic] = (
        energy[domestic] * ELECTRICITY_DUTY_PERCENT_BY_CATEGORY["domestic"] / 100
    )
    q = SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY["domestic"]
    sr = SUBSIDY_INR_PER_UNIT_BY_CATEGORY["domestic"]
    rebate.loc[domestic] = np.where(u <= q, u * sr, 0.0)

    # Commercial — non-telescopic
    c0, cr0 = SLAB_TABLE_INR_BY_CATEGORY["commercial"][0]
    c1, cr1 = SLAB_TABLE_INR_BY_CATEGORY["commercial"][1]
    _, cr2 = SLAB_TABLE_INR_BY_CATEGORY["commercial"][2]
    u = units[commercial]
    energy.loc[commercial] = np.where(
        u <= c0,
        u * cr0,
        np.where(u <= c1, u * cr1, u * cr2),
    )
    fixed.loc[commercial] = (
        load[commercial] * FIXED_CHARGE_INR_PER_KW_BY_CATEGORY["commercial"]
    )
    duty.loc[commercial] = (
        energy[commercial] * ELECTRICITY_DUTY_PERCENT_BY_CATEGORY["commercial"] / 100
    )
    q = SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY["commercial"]
    sr = SUBSIDY_INR_PER_UNIT_BY_CATEGORY["commercial"]
    rebate.loc[commercial] = np.where(u <= q, u * sr, 0.0)

    # Agricultural — single rate, horsepower fixed charge, always-on rebate up to qualify
    _, ar = SLAB_TABLE_INR_BY_CATEGORY["agricultural"][0]
    u = units[agricultural]
    energy.loc[agricultural] = u * ar
    fixed.loc[agricultural] = (
        load[agricultural] * HORSEPOWER_PER_KILOWATT * FIXED_CHARGE_INR_PER_HORSEPOWER
    )
    duty.loc[agricultural] = (
        energy[agricultural]
        * ELECTRICITY_DUTY_PERCENT_BY_CATEGORY["agricultural"]
        / 100
    )
    q = SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY["agricultural"]
    sr = SUBSIDY_INR_PER_UNIT_BY_CATEGORY["agricultural"]
    rebate.loc[agricultural] = np.where(u <= q, u * sr, 0.0)

    net = (energy + fixed + duty - rebate).clip(lower=0.0)
    net.name = "net_bill_inr"
    return net
