import pathlib
import subprocess
import sys

PROJECT = pathlib.Path(__file__).resolve().parent
SCRIPTS = PROJECT / "scripts"
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))


def run_script(script_name, values):
    """Run one of the Week 1 scripts, feeding it the values it reads from standard input."""
    finished = subprocess.run(
        [sys.executable, str(PROJECT / "scripts" / script_name)],
        input="\n".join(str(one) for one in values) + "\n",
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert finished.returncode == 0, (
        f"{script_name} stopped with code {finished.returncode}: {finished.stderr.strip()}"
    )
    return finished.stdout


def printed(output, label):
    """The value printed against a label, as text."""
    for line in output.splitlines():
        if line.startswith(label + ":"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"no line beginning '{label}:' was printed. Printed:\n{output}")


# --------------------------------------------------------------------------- WEEK 1 DAY 1

def test_week1_day1_a_domestic_cycle_is_priced_to_the_paisa():
    output = run_script(
        "day01_bill_from_reading.py", ["ACC10000123", 3, 30, 14208, 14675, 340, 2]
    )
    for label, expected in (
        ("Units consumed", "467.0"),
        ("Energy charge", "2575.7"),
        ("Fixed charge", "150.0"),
        ("Electricity duty", "128.78"),
        ("Rebate", "0.0"),
        ("Current demand", "2854.48"),
    ):
        assert printed(output, label) == expected, (
            f"a 467 unit domestic cycle on a 3 kW load should print {label} as {expected}, "
            f"not {printed(output, label)}"
        )


def test_week1_day1_a_cycle_inside_the_first_block_is_priced_at_the_first_rate():
    output = run_script(
        "day01_bill_from_reading.py", ["ACC10000123", 2, 30, 1000, 1080, 0, 0]
    )
    assert printed(output, "Units consumed") == "80.0", "eighty units should have been read"
    assert printed(output, "Energy charge") == "280.0", (
        "eighty units all sit inside the first block, so the charge is eighty at that block's "
        f"rate and nothing else, not {printed(output, 'Energy charge')}"
    )
    assert float(printed(output, "Rebate")) > 0.0, (
        "a cycle at or under the qualifying figure earns the rebate on every unit it used"
    )


def test_week1_day1_a_reading_that_went_backwards_is_refused():
    output = run_script(
        "day01_bill_from_reading.py", ["ACC10000123", 3, 30, 50000, 49500, 0, 0]
    )
    refusals = [line for line in output.splitlines() if line.startswith("Rejected:")]
    assert len(refusals) == 1, (
        f"exactly one rule is broken here, so exactly one refusal should be printed, not "
        f"{len(refusals)}. Printed:\n{output}"
    )
    assert "below the previous reading" in refusals[0], (
        f"the refusal should say the reading went backwards, not {refusals[0]!r}"
    )
    assert output.strip().splitlines()[-1].startswith("Reading is not billable"), (
        "a cycle that breaks a rule should end by saying it is not billable"
    )


def test_week1_day1_consumption_above_the_connected_capacity_is_refused():
    output = run_script(
        "day01_bill_from_reading.py", ["ACC10000123", 1, 30, 1000, 60000, 0, 0]
    )
    refusals = [line for line in output.splitlines() if line.startswith("Rejected:")]
    assert any("above" in line for line in refusals), (
        f"fifty nine thousand units cannot be drawn through a 1 kW connection in thirty days, "
        f"so the capacity rule should refuse it. Printed:\n{output}"
    )


def test_week1_day1_a_clean_cycle_carries_no_refusal_at_all():
    output = run_script(
        "day01_bill_from_reading.py", ["ACC10000123", 3, 30, 14208, 14675, 0, 0]
    )
    refusals = [line for line in output.splitlines() if line.startswith("Rejected:")]
    assert refusals == [], f"this cycle breaks no rule, yet it printed {refusals}"
    assert output.strip().splitlines()[-1] == "Reading is billable", (
        "a cycle that breaks no rule should end by saying it is billable"
    )
    with_arrears = run_script(
        "day01_bill_from_reading.py", ["ACC10000123", 3, 30, 14208, 14675, 500, 2]
    )
    demand = float(printed(with_arrears, "Current demand"))
    surcharge = float(printed(with_arrears, "Late payment surcharge"))
    assert abs(surcharge - 10.0) < 0.005, (
        f"the surcharge is the published percentage of the arrears, which is two per cent of "
        f"five hundred, not {surcharge}"
    )
    assert abs(float(printed(with_arrears, "Amount payable")) - (demand + 500 + surcharge)) < 0.005, (
        "what is payable is the current demand plus the arrears plus the surcharge on them, "
        "and those three have to add up in the printed figures"
    )


# --------------------------------------------------------------------------- WEEK 1 DAY 2

def test_week1_day2_the_rollover_is_read_as_a_rollover_and_not_as_a_mistake():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import units_consumed

    reachable_in_this_cycle = 30.0 * 24 * 30 * 1.10
    assert units_consumed(14208.0, 14675.0, reachable_in_this_cycle) == 467.0, (
        "an ordinary cycle is the difference between the two readings"
    )
    assert units_consumed(99500.0, 300.0, reachable_in_this_cycle) == 800.0, (
        f"the meter passed its last digit and started again, so the cycle used eight hundred "
        f"units, not {units_consumed(99500.0, 300.0, reachable_in_this_cycle)}"
    )
    assert units_consumed(50000.0, 49500.0, reachable_in_this_cycle) == 0.0, (
        "a meter halfway up its range cannot have rolled over, so nothing may be claimed"
    )


def test_week1_day2_the_domestic_schedule_charges_each_block_at_its_own_rate():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import slab_energy_charge

    step = slab_energy_charge("domestic", 101) - slab_energy_charge("domestic", 100)
    assert abs(step - 4.90) < 0.005, (
        f"the hundred and first unit falls in the second block, so it should cost that "
        f"block's rate on its own. It cost {step:.2f}"
    )
    assert abs(slab_energy_charge("domestic", 100) - 350.0) < 0.005, (
        f"a hundred units sit wholly inside the first block, so they cost a hundred at that "
        f"block's rate, not {slab_energy_charge('domestic', 100):.2f}"
    )
    from day02_bill_pricing import apply_electricity_duty

    assert apply_electricity_duty("domestic", 1000.0) > apply_electricity_duty(
        "agricultural", 1000.0
    ), (
        "the duty is a percentage of the energy charge and the schedule levies none on an "
        "agricultural connection, so the same charge cannot carry the same duty"
    )


def test_week1_day2_the_commercial_schedule_reprices_everything_past_a_boundary():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import slab_energy_charge

    at_two_hundred = slab_energy_charge("commercial", 200)
    past_it = slab_energy_charge("commercial", 201)
    assert past_it - at_two_hundred > 100.0, (
        f"one unit past a commercial boundary reprices the whole consumption, so the charge "
        f"should jump by far more than one unit is worth. It moved by "
        f"{past_it - at_two_hundred:.2f}"
    )
    assert abs(past_it - 201 * 8.60) < 0.005, (
        f"past the boundary every unit is charged at the higher band's rate, not just the "
        f"ones above it; got {past_it:.2f}"
    )


def test_week1_day2_the_fixed_charge_follows_the_load_and_not_the_units():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import apply_fixed_charge

    small, large = apply_fixed_charge("domestic", 2), apply_fixed_charge("domestic", 6)
    assert large > small, "a larger sanctioned load should carry a larger fixed charge"
    assert abs(large / small - 3.0) < 0.001, (
        f"the fixed charge is levied for each kilowatt, so tripling the load should triple "
        f"it. It moved from {small} to {large}"
    )
    assert apply_fixed_charge("agricultural", 5) != apply_fixed_charge("domestic", 5), (
        "an agricultural connection is charged by horsepower and cannot pay the same fixed "
        "charge as a domestic one on the same kilowatts"
    )


def test_week1_day2_the_reading_object_prices_itself_the_same_way_the_functions_do():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import MeterReading, net_bill_amount

    reading = MeterReading("ACC10000123", "domestic", 3, 30, 14208, 14675)
    units, net_inr = reading.price()
    assert units == 467.0, f"the object should read the same 467 units, not {units}"
    assert abs(net_inr - net_bill_amount("domestic", units, 3)) < 0.005, (
        f"the object may hold the values, but the arithmetic stays in the functions; the "
        f"object said {net_inr:.2f} and the function said "
        f"{net_bill_amount('domestic', units, 3):.2f}"
    )
    assert abs(net_inr - 2854.48) < 0.005, (
        f"and it should reach the same figure the same arithmetic reached on Day 1, not "
        f"{net_inr:.2f}"
    )


# --------------------------------------------------------------------------- WEEK 1 DAY 3

def test_week1_day3_the_package_is_importable_and_carries_the_days_work():
    import importlib

    for module_name, written_here in (
        ("metermind.core.exceptions", "MeterMindError"),
        ("metermind.core.tariff_calculations", "calculate_bill_amount"),
        ("metermind.data_access.file_storage", "ReadingFileStorage"),
    ):
        reached = importlib.import_module(module_name)
        assert hasattr(reached, written_here), (
            f"{module_name} should be importable and should define {written_here}"
        )


def test_week1_day3_every_metermind_error_shares_one_parent():
    from metermind.core import exceptions

    for name in ("UnsupportedCategoryError", "ReadingStorageError", "InvalidReadingError"):
        raised = getattr(exceptions, name)
        assert issubclass(raised, exceptions.MeterMindError), (
            f"{name} should inherit from MeterMindError so that one except clause catches "
            f"everything this platform raises"
        )
    assert issubclass(exceptions.MeterMindError, Exception), (
        "MeterMindError should still be an ordinary exception"
    )


def test_week1_day3_a_rollover_is_read_as_a_rollover_and_a_regression_as_nothing():
    from metermind.core.tariff_calculations import calculate_units_consumed

    reachable_in_this_cycle = 3.0 * 24 * 30 * 1.10
    assert calculate_units_consumed(14208.0, 14675.0, reachable_in_this_cycle) == 467.0, (
        "an ordinary cycle is the difference between the two readings"
    )
    assert calculate_units_consumed(99500.0, 300.0, reachable_in_this_cycle) == 800.0, (
        "the meter passed its last digit and started again, so this cycle used eight hundred "
        "units and not a negative number"
    )
    assert calculate_units_consumed(50000.0, 49500.0, reachable_in_this_cycle) == 0.0, (
        "a meter halfway up its range cannot have rolled over, so this reading is a mistake "
        "and no consumption may be claimed from it"
    )


def test_week1_day3_the_package_prices_a_cycle_the_way_the_day_two_script_did():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import net_bill_amount
    from metermind.core.tariff_calculations import calculate_bill_amount

    from_the_script = net_bill_amount("domestic", 467.0, 3.0)
    from_the_package = calculate_bill_amount("domestic", 467.0, 3.0)
    assert abs(from_the_package - from_the_script) < 0.005, (
        f"moving the arithmetic into the package must not change what a cycle costs. The "
        f"script said {from_the_script:.2f} and the package said {from_the_package:.2f}"
    )


def test_week1_day3_the_reading_book_survives_a_round_trip_to_disk(tmp_path):
    from metermind.core.exceptions import ReadingStorageError
    from metermind.data_access.file_storage import ReadingFileStorage

    book = [
        {
            "account_number": "ACC10000123",
            "consumer_category": "domestic",
            "units_consumed": "467.0",
        },
        {
            "account_number": "ACC10000124",
            "consumer_category": "commercial",
            "units_consumed": "5120.5",
        },
    ]
    storage = ReadingFileStorage(tmp_path)
    storage.save_readings_csv("book.csv", book)
    assert storage.load_readings_csv("book.csv") == book, (
        "every field should come back out of the file exactly as it went in"
    )
    try:
        storage.load_readings_csv("nothing_here.csv")
        raise AssertionError("loading a file that is not there should have been refused")
    except ReadingStorageError:
        pass


# --------------------------------------------------------------------------- WEEK 1 DAY 4

def test_week1_day4_the_factory_returns_the_class_the_category_names():
    from metermind.core import entities
    from metermind.core.exceptions import UnsupportedCategoryError

    record = {
        "account_number": "ACC10000123",
        "consumer_category": "domestic",
        "sanctioned_load_kw": 3,
        "cycle_days": 30,
        "previous_reading": 14208,
        "current_reading": 14675,
    }
    for category, wanted in (
        ("domestic", entities.ServiceConnection),
        ("commercial", entities.CommercialConnection),
        ("agricultural", entities.AgriculturalConnection),
    ):
        built = entities.create_service_connection(
            dict(record, consumer_category=category)
        )
        assert isinstance(built, wanted), (
            f"a {category} record should be built as {wanted.__name__}, not "
            f"{type(built).__name__}"
        )
    try:
        entities.create_service_connection(
            dict(record, consumer_category="industrial")
        )
        raise AssertionError("a category with no tariff schedule should have been refused")
    except UnsupportedCategoryError:
        pass


def test_week1_day4_the_domestic_charge_is_the_sum_of_its_blocks():
    from config import constants
    from metermind.core.entities import create_service_connection

    built = create_service_connection(
        {
            "account_number": "ACC10000123",
            "consumer_category": "domestic",
            "sanctioned_load_kw": 3,
            "cycle_days": 30,
            "previous_reading": 0,
            "current_reading": 467,
        }
    )
    by_hand, lower = 0.0, 0.0
    for upper, rate in constants.SLAB_TABLE_INR_BY_CATEGORY["domestic"]:
        by_hand += max(0.0, min(built.units_consumed, upper) - lower) * rate
        lower = upper
    assert abs(built.energy_charge_inr() - by_hand) < 0.005, (
        f"a domestic connection is charged block by block, which comes to {by_hand:.2f}, not "
        f"{built.energy_charge_inr():.2f}"
    )


def test_week1_day4_one_unit_past_a_commercial_boundary_costs_more_than_one_unit():
    from config import constants
    from metermind.core.entities import create_service_connection

    record = {
        "account_number": "ACC10000123",
        "consumer_category": "commercial",
        "sanctioned_load_kw": 10,
        "cycle_days": 30,
        "previous_reading": 0,
    }
    boundary = constants.SLAB_TABLE_INR_BY_CATEGORY["commercial"][0][0]
    at_the_boundary = create_service_connection(dict(record, current_reading=boundary))
    just_past_it = create_service_connection(
        dict(record, current_reading=boundary + 1)
    )
    dearest_rate = max(
        rate for _, rate in constants.SLAB_TABLE_INR_BY_CATEGORY["commercial"]
    )
    jump = just_past_it.energy_charge_inr() - at_the_boundary.energy_charge_inr()
    assert jump > dearest_rate, (
        f"crossing a boundary on a schedule that is not telescopic reprices every unit, so the "
        f"charge should jump by far more than one unit at any rate. It jumped {jump:.2f}"
    )


def test_week1_day4_the_agricultural_subsidy_can_reach_zero_but_not_below():
    from metermind.core.entities import create_service_connection

    built = create_service_connection(
        {
            "account_number": "ACC10000123",
            "consumer_category": "agricultural",
            "sanctioned_load_kw": 5,
            "cycle_days": 30,
            "previous_reading": 0,
            "current_reading": 3000,
        }
    )
    assert built.subsidy_inr() > built.energy_charge_inr(), (
        "the subsidy on this cycle is larger than the energy it is set against, which is what "
        "makes the floor worth having"
    )
    assert built.net_bill_inr() == 0.0, (
        f"a bill the subsidy more than covers is nil, not {built.net_bill_inr():.2f}, and "
        f"nothing is carried forward or refunded"
    )


def test_week1_day4_a_connection_is_billable_exactly_when_it_has_no_refusal():
    from metermind.core.entities import create_service_connection

    record = {
        "account_number": "ACC10000123",
        "consumer_category": "domestic",
        "sanctioned_load_kw": 3,
        "cycle_days": 30,
        "previous_reading": 14208,
        "current_reading": 14675,
    }
    clean = create_service_connection(record)
    assert clean.refusal_reasons() == [] and clean.is_billable(), (
        f"this cycle breaks no rule, yet it reported {clean.refusal_reasons()}"
    )
    for broken in (
        dict(record, cycle_days=7),
        dict(record, previous_reading=50000, current_reading=49500),
        dict(record, current_reading=90000),
    ):
        built = create_service_connection(broken)
        assert built.refusal_reasons(), f"{broken} should have been refused for something"
        assert not built.is_billable(), (
            "a connection with a reason against it cannot also be billable"
        )


# --------------------------------------------------------------------------- WEEK 1 DAY 5

def test_week1_day5_every_identifier_check_accepts_its_own_shape_and_refuses_others():
    from metermind.core import validators

    assert validators.validate_account_number("ACC10000123"), "the register's own shape passes"
    for wrong in ("ACC1000012", "ACC100001234", "acc10000123", "10000123", "ACC1000012A"):
        assert not validators.validate_account_number(wrong), f"{wrong!r} is not an account"
    assert validators.validate_meter_serial("MTR-AB-123456"), "the register's serial passes"
    assert not validators.validate_meter_serial("MTR-ab-123456"), "a serial's letters are caps"
    assert validators.validate_billing_period("2026-06"), "a real year and month passes"
    for wrong in ("2026-00", "2026-13", "2026-6", "26-06", "2026/06"):
        assert not validators.validate_billing_period(wrong), f"{wrong!r} is not a period"
    assert validators.validate_email_address("consumer.one@example.in"), "a reply could be sent"
    assert not validators.validate_email_address("consumer.one@"), "nothing could be sent here"


def test_week1_day5_the_two_wrappers_guard_and_time_without_changing_the_answer():
    from metermind.core.decorators import measure_execution_duration, reject_negative_readings
    from metermind.core.exceptions import InvalidReadingError

    @reject_negative_readings
    def units_between(previous_reading, current_reading):
        return current_reading - previous_reading

    @measure_execution_duration
    def add_up(values):
        return sum(values)

    assert units_between(14208, 14675) == 467, "the guard hands back what the function returned"
    assert add_up([1, 2, 3]) == 6, "timing a function must not change what it returns"
    assert add_up.last_duration_seconds >= 0.0, (
        "the timer should record how long the call took, in seconds and never negative"
    )
    try:
        units_between(-1, 14675)
        raise AssertionError("a negative reading should have been refused")
    except InvalidReadingError:
        pass


def test_week1_day5_the_block_limits_prorate_with_the_days():
    from config import constants
    from metermind.core.tariff_calculations import calculate_prorated_slab_limits

    blocks = constants.SLAB_TABLE_INR_BY_CATEGORY["domestic"]
    earlier_part = calculate_prorated_slab_limits(blocks, 13 / 31)
    later_part = calculate_prorated_slab_limits(blocks, 18 / 31)
    assert len(earlier_part) == len(blocks), "proration scales the blocks, it adds or drops none"
    # zip(..., strict=True) needs Python 3.10+; lengths are asserted above.
    for (whole_limit, whole_rate), (earlier_limit, earlier_rate), (later_limit, _) in zip(
        blocks, earlier_part, later_part
    ):
        assert earlier_rate == whole_rate, "proration changes the limits, never the rates"
        if whole_limit < constants.UNLIMITED_UNITS:
            assert abs(earlier_limit + later_limit - whole_limit) < 0.001, (
                f"the two parts of a split cycle should add back to the whole block limit "
                f"{whole_limit}, not {earlier_limit + later_limit}"
            )


def test_week1_day5_a_cycle_with_no_tariff_change_prorates_to_the_same_charge():
    from config import constants
    from metermind.core.tariff_calculations import (
        calculate_prorated_energy_charge,
        calculate_slab_energy_charge,
    )

    blocks = constants.SLAB_TABLE_INR_BY_CATEGORY["domestic"]
    whole = calculate_slab_energy_charge("domestic", 467.0)
    split = calculate_prorated_energy_charge("domestic", 467.0, 31, 13, blocks, blocks)
    assert abs(whole - split) < 0.005, (
        f"splitting a cycle across two identical schedules cannot change what it costs. The "
        f"whole cycle came to {whole:.2f} and the split came to {split:.2f}"
    )


def test_week1_day5_the_loader_returns_objects_and_not_dictionaries(tmp_path):
    from metermind.core.entities import ServiceConnection
    from metermind.data_access.file_storage import ReadingFileStorage

    book = [
        {
            "account_number": "ACC10000123",
            "consumer_category": "domestic",
            "sanctioned_load_kw": "3",
            "cycle_days": "30",
            "previous_reading": "14208",
            "current_reading": "14675",
        },
        {
            "account_number": "ACC10000124",
            "consumer_category": "streetlight",
            "sanctioned_load_kw": "3",
            "cycle_days": "30",
            "previous_reading": "100",
            "current_reading": "200",
        },
    ]
    storage = ReadingFileStorage(tmp_path)
    storage.save_readings_csv("book.csv", book)
    loaded = storage.load_connection_objects("book.csv")
    assert len(loaded) == 1, (
        f"the row with a category this platform has no schedule for should be left out rather "
        f"than stopping the load, so one connection should come back, not {len(loaded)}"
    )
    assert isinstance(loaded[0], ServiceConnection), (
        f"the loader should return connections, not {type(loaded[0]).__name__}"
    )
    assert loaded[0].units_consumed == 467.0, (
        "the connection that came back should have worked out its own units"
    )


# --------------------------------------------------------------------------- WEEK 2 DAY 1

def test_week2_day1_the_whole_book_is_priced_without_a_loop_over_rows():
    import pandas
    from metermind.core.tariff_calculations import calculate_bill_amount, calculate_bill_amounts

    book = pandas.DataFrame(
        {
            "consumer_category": ["domestic", "commercial", "agricultural", "domestic"],
            "units_consumed": [467.0, 467.0, 3000.0, 80.0],
            "sanctioned_load_kw": [3.0, 3.0, 5.0, 2.0],
        }
    )
    together = calculate_bill_amounts(book)
    assert len(together) == len(book), "one bill should come back for every row of the book"
    for position, row in enumerate(book.itertuples()):
        one_at_a_time = calculate_bill_amount(
            row.consumer_category, row.units_consumed, row.sanctioned_load_kw
        )
        assert abs(together.iloc[position] - one_at_a_time) < 0.005, (
            f"row {position} came to {together.iloc[position]:.2f} priced together and "
            f"{one_at_a_time:.2f} priced on its own, and the two must agree"
        )


def test_week2_day1_a_bill_the_subsidy_covers_is_nil_and_never_negative():
    import pandas
    from metermind.core.tariff_calculations import calculate_bill_amounts

    book = pandas.DataFrame(
        {
            "consumer_category": ["agricultural", "agricultural"],
            "units_consumed": [3000.0, 12000.0],
            "sanctioned_load_kw": [5.0, 5.0],
        }
    )
    assert (calculate_bill_amounts(book) >= 0.0).all(), (
        "a subsidy larger than the rest of the bill leaves nothing to pay, not a negative bill"
    )


def test_week2_day1_every_shape_of_read_date_is_read_and_a_fifth_is_not():
    import pandas
    from metermind.data_access.cleaning_pipeline import parse_read_dates

    book = pandas.DataFrame(
        {
            "read_date": [
                "2025-06-14",
                "14/06/2025",
                "14-Jun-2025",
                "14.06.2025",
                "not taken",
            ]
        }
    )
    read_on = parse_read_dates(book)
    assert read_on[:4].notna().all(), (
        f"all four shapes the field applications wrote should be read, not {list(read_on[:4])}"
    )
    assert len(set(read_on[:4])) == 1, (
        "the four shapes are the same day written four ways, so they should read as one date"
    )
    assert pandas.isna(read_on[4]), "a date in no agreed shape is a fault, not a fifth shape"


def test_week2_day1_a_row_is_refused_for_the_first_rule_it_breaks():
    import pandas
    from metermind.data_access.cleaning_pipeline import REJECTION_REASONS, first_broken_rule

    breaks_two = pandas.Series(
        {
            "reading_id": "RDG1",
            "account_number": "",
            "consumer_category": "streetlight",
            "sanctioned_load_kw": 3.0,
            "billing_period": "2026-06",
            "cycle_days": 30,
            "previous_reading": 0.0,
            "current_reading": 100.0,
            "units_consumed": 100.0,
            "read_on": pandas.Timestamp("2026-06-14"),
        }
    )
    assert first_broken_rule(breaks_two) == REJECTION_REASONS[0], (
        "this row has no account number and an unknown category, and the first rule wins"
    )
    clean = breaks_two.copy()
    clean["account_number"] = "ACC10000123"
    clean["consumer_category"] = "domestic"
    assert first_broken_rule(clean) == "", "a row that breaks no rule earns no reason"


def test_week2_day1_the_cleaner_loses_no_row_and_gives_every_refusal_a_published_reason(
    tmp_path,
):
    import pandas
    from config import constants
    from metermind.data_access.cleaning_pipeline import REJECTION_REASONS, clean_reading_book

    book = pandas.read_csv(constants.READING_BOOK_TRAIN_PATH)
    counted = clean_reading_book(
        constants.READING_BOOK_TRAIN_PATH,
        tmp_path / "clean.csv",
        tmp_path / "rejected.csv",
    )
    assert counted["kept"] + counted["rejected"] == len(book), (
        f"{len(book)} rows went in and {counted['kept'] + counted['rejected']} came out, so "
        f"rows were lost or duplicated"
    )
    rejected = pandas.read_csv(tmp_path / "rejected.csv")
    assert set(rejected["rejection_reason"]) <= set(REJECTION_REASONS), (
        "every reason written beside a refused row should be one of the published reasons"
    )
    assert counted["rejected"] > 0 and counted["kept"] > counted["rejected"], (
        "the book carries faults, and far more good rows than bad ones"
    )
