account_number = input().strip().upper()
sanctioned_load_kw = float(input())
cycle_days = int(input())
previous_reading = float(input())
current_reading = float(input())
arrears_inr = float(input())
late_payment_surcharge_percent = float(input())

reasons = []

physical_max = sanctioned_load_kw * 24 * cycle_days * 1.10

if cycle_days < 26:
    reasons.append("cycle_days  is below the minimum of 26")
if cycle_days > 36:
    reasons.append("cycle_days is above the maximum of 36")

if current_reading >= previous_reading:
    units_consumed = current_reading - previous_reading
else:
    if previous_reading + physical_max >= 100000:
        rollover_units = current_reading + 100000 - previous_reading
        if rollover_units <= physical_max:
            units_consumed = rollover_units
        else:
            reasons.append(
                "rollover units are above the physical maximum for this load"
            )
            units_consumed = 0.0
    else:
        reasons.append("reading is below the previous reading")
        units_consumed = 0.0

if units_consumed > physical_max:
    reasons.append("consumption is above connected capacity")

if len(reasons) == 0:
    if units_consumed <= 100:
        energy_charge = units_consumed * 3.5
    elif units_consumed <= 200:
        energy_charge = 100 * 3.5 + (units_consumed - 100) * 4.9
    elif units_consumed <= 400:
        energy_charge = 100 * 3.5 + 100 * 4.9 + (units_consumed - 200) * 6.30
    else:
        energy_charge = (
            100 * 3.5 + 100 * 4.9 + 200 * 6.30 + (units_consumed - 400) * 7.10
        )
    fixed_charge = sanctioned_load_kw * 50.0
    electricity_duty = energy_charge * 5.0 / 100
    rebate = units_consumed * 1.5 if units_consumed <= 100 else 0.0
    current_demand = energy_charge + fixed_charge + electricity_duty - rebate
    if current_demand < 0:
        current_demand = 0.0
    surcharge = arrears_inr * late_payment_surcharge_percent / 100
    amount_payable = current_demand + arrears_inr + surcharge
else:
    energy_charge = 0.0
    fixed_charge = sanctioned_load_kw * 50.0
    electricity_duty = 0.0
    rebate = 0.0
    current_demand = fixed_charge
    surcharge = 0.0
    amount_payable = current_demand

print(f"Account number: {account_number}")
print(f"Units consumed: {units_consumed:.1f}")
print(f"Energy charge: {energy_charge:.1f}")
print(f"Fixed charge: {fixed_charge:.1f}")
print(f"Electricity duty: {electricity_duty:.2f}")
print(f"Rebate: {rebate:.1f}")
print(f"Current demand: {current_demand:.2f}")
print(f"Late payment surcharge: {surcharge:.1f}")
print(f"Amount payable: {amount_payable:.2f}")

if len(reasons) == 0:
    print("Reading is billable")
else:
    for reason in reasons:
        print(f"Rejected: {reason}")
    print(f"Reading is not billable: {len(reasons)} reasons")
