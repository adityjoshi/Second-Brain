import functools
import pathlib
import subprocess
import sys
import time

PROJECT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT / "scripts"
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))


def run_script(script_name, values):
    """Run one of the Week 1 scripts, feeding it the values it reads from standard input."""
    finished = subprocess.run([sys.executable, str(PROJECT / "scripts" / script_name)],
                              input="\n".join(str(one) for one in values) + "\n",
                              capture_output=True, text=True, timeout=60)
    assert finished.returncode == 0, (
        f"{script_name} stopped with code {finished.returncode}: {finished.stderr.strip()}")
    return finished.stdout


def printed(output, label):
    """The value printed against a label, as text."""
    for line in output.splitlines():
        if line.startswith(label + ":"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"no line beginning '{label}:' was printed. Printed:\n{output}")


# --------------------------------------------------------------------------- WEEK 1 DAY 1

def test_week1_day1_a_domestic_cycle_is_priced_to_the_paisa():
    output = run_script("day01_bill_from_reading.py",
                        ["ACC10000123", 3, 30, 14208, 14675, 340, 2])
    for label, expected in (("Units consumed", "467.0"), ("Energy charge", "2575.7"),
                            ("Fixed charge", "150.0"), ("Electricity duty", "128.78"),
                            ("Rebate", "0.0"), ("Current demand", "2854.48")):
        assert printed(output, label) == expected, (
            f"a 467 unit domestic cycle on a 3 kW load should print {label} as {expected}, "
            f"not {printed(output, label)}")


def test_week1_day1_a_cycle_inside_the_first_block_is_priced_at_the_first_rate():
    output = run_script("day01_bill_from_reading.py",
                        ["ACC10000123", 2, 30, 1000, 1080, 0, 0])
    assert printed(output, "Units consumed") == "80.0", "eighty units should have been read"
    assert printed(output, "Energy charge") == "280.0", (
        "eighty units all sit inside the first block, so the charge is eighty at that block's "
        f"rate and nothing else, not {printed(output, 'Energy charge')}")
    assert float(printed(output, "Rebate")) > 0.0, (
        "a cycle at or under the qualifying figure earns the rebate on every unit it used")


def test_week1_day1_a_reading_that_went_backwards_is_refused():
    output = run_script("day01_bill_from_reading.py",
                        ["ACC10000123", 3, 30, 50000, 49500, 0, 0])
    refusals = [line for line in output.splitlines() if line.startswith("Rejected:")]
    assert len(refusals) == 1, (
        f"exactly one rule is broken here, so exactly one refusal should be printed, not "
        f"{len(refusals)}. Printed:\n{output}")
    assert "below the previous reading" in refusals[0], (
        f"the refusal should say the reading went backwards, not {refusals[0]!r}")
    assert output.strip().splitlines()[-1].startswith("Reading is not billable"), (
        "a cycle that breaks a rule should end by saying it is not billable")


def test_week1_day1_consumption_above_the_connected_capacity_is_refused():
    output = run_script("day01_bill_from_reading.py",
                        ["ACC10000123", 1, 30, 1000, 60000, 0, 0])
    refusals = [line for line in output.splitlines() if line.startswith("Rejected:")]
    assert any("above" in line for line in refusals), (
        f"fifty nine thousand units cannot be drawn through a 1 kW connection in thirty days, "
        f"so the capacity rule should refuse it. Printed:\n{output}")


def test_week1_day1_a_clean_cycle_carries_no_refusal_at_all():
    output = run_script("day01_bill_from_reading.py",
                        ["ACC10000123", 3, 30, 14208, 14675, 0, 0])
    refusals = [line for line in output.splitlines() if line.startswith("Rejected:")]
    assert refusals == [], f"this cycle breaks no rule, yet it printed {refusals}"
    assert output.strip().splitlines()[-1] == "Reading is billable", (
        "a cycle that breaks no rule should end by saying it is billable")
    with_arrears = run_script("day01_bill_from_reading.py",
                              ["ACC10000123", 3, 30, 14208, 14675, 500, 2])
    demand = float(printed(with_arrears, "Current demand"))
    surcharge = float(printed(with_arrears, "Late payment surcharge"))
    assert abs(surcharge - 10.0) < 0.005, (
        f"the surcharge is the published percentage of the arrears, which is two per cent of "
        f"five hundred, not {surcharge}")
    assert abs(float(printed(with_arrears, "Amount payable")) - (demand + 500 + surcharge)) \
        < 0.005, (
        "what is payable is the current demand plus the arrears plus the surcharge on them, "
        "and those three have to add up in the printed figures")


# --------------------------------------------------------------------------- WEEK 1 DAY 2

def test_week1_day2_the_rollover_is_read_as_a_rollover_and_not_as_a_mistake():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import units_consumed

    reachable_in_this_cycle = 30.0 * 24 * 30 * 1.10
    assert units_consumed(14208.0, 14675.0, reachable_in_this_cycle) == 467.0, (
        "an ordinary cycle is the difference between the two readings")
    assert units_consumed(99500.0, 300.0, reachable_in_this_cycle) == 800.0, (
        f"the meter passed its last digit and started again, so the cycle used eight hundred "
        f"units, not {units_consumed(99500.0, 300.0, reachable_in_this_cycle)}")
    assert units_consumed(50000.0, 49500.0, reachable_in_this_cycle) == 0.0, (
        "a meter halfway up its range cannot have rolled over, so nothing may be claimed")


def test_week1_day2_the_domestic_schedule_charges_each_block_at_its_own_rate():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import slab_energy_charge

    step = slab_energy_charge("domestic", 101) - slab_energy_charge("domestic", 100)
    assert abs(step - 4.90) < 0.005, (
        f"the hundred and first unit falls in the second block, so it should cost that "
        f"block's rate on its own. It cost {step:.2f}")
    assert abs(slab_energy_charge("domestic", 100) - 350.0) < 0.005, (
        f"a hundred units sit wholly inside the first block, so they cost a hundred at that "
        f"block's rate, not {slab_energy_charge('domestic', 100):.2f}")
    from day02_bill_pricing import apply_electricity_duty
    assert apply_electricity_duty("domestic", 1000.0) > apply_electricity_duty(
        "agricultural", 1000.0), (
        "the duty is a percentage of the energy charge and the schedule levies none on an "
        "agricultural connection, so the same charge cannot carry the same duty")


def test_week1_day2_the_commercial_schedule_reprices_everything_past_a_boundary():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import slab_energy_charge

    at_two_hundred = slab_energy_charge("commercial", 200)
    past_it = slab_energy_charge("commercial", 201)
    assert past_it - at_two_hundred > 100.0, (
        f"one unit past a commercial boundary reprices the whole consumption, so the charge "
        f"should jump by far more than one unit is worth. It moved by "
        f"{past_it - at_two_hundred:.2f}")
    assert abs(past_it - 201 * 8.60) < 0.005, (
        f"past the boundary every unit is charged at the higher band's rate, not just the "
        f"ones above it; got {past_it:.2f}")


def test_week1_day2_the_fixed_charge_follows_the_load_and_not_the_units():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import apply_fixed_charge

    small, large = apply_fixed_charge("domestic", 2), apply_fixed_charge("domestic", 6)
    assert large > small, "a larger sanctioned load should carry a larger fixed charge"
    assert abs(large / small - 3.0) < 0.001, (
        f"the fixed charge is levied for each kilowatt, so tripling the load should triple "
        f"it. It moved from {small} to {large}")
    assert apply_fixed_charge("agricultural", 5) != apply_fixed_charge("domestic", 5), (
        "an agricultural connection is charged by horsepower and cannot pay the same fixed "
        "charge as a domestic one on the same kilowatts")


def test_week1_day2_the_reading_object_prices_itself_the_same_way_the_functions_do():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import MeterReading, net_bill_amount

    reading = MeterReading("ACC10000123", "domestic", 3, 30, 14208, 14675)
    units, net_inr = reading.price()
    assert units == 467.0, f"the object should read the same 467 units, not {units}"
    assert abs(net_inr - net_bill_amount("domestic", units, 3)) < 0.005, (
        f"the object may hold the values, but the arithmetic stays in the functions; the "
        f"object said {net_inr:.2f} and the function said "
        f"{net_bill_amount('domestic', units, 3):.2f}")
    assert abs(net_inr - 2854.48) < 0.005, (
        f"and it should reach the same figure the same arithmetic reached on Day 1, not "
        f"{net_inr:.2f}")


# --------------------------------------------------------------------------- WEEK 1 DAY 3

def test_week1_day3_the_package_is_importable_and_carries_the_days_work():
    import importlib

    for module_name, written_here in (
            ("metermind.core.exceptions", "MeterMindError"),
            ("metermind.core.tariff_calculations", "calculate_bill_amount"),
            ("metermind.data_access.file_storage", "ReadingFileStorage")):
        reached = importlib.import_module(module_name)
        assert hasattr(reached, written_here), (
            f"{module_name} should be importable and should define {written_here}")


def test_week1_day3_every_metermind_error_shares_one_parent():
    from metermind.core import exceptions

    for name in ("UnsupportedCategoryError", "ReadingStorageError", "InvalidReadingError"):
        raised = getattr(exceptions, name)
        assert issubclass(raised, exceptions.MeterMindError), (
            f"{name} should inherit from MeterMindError so that one except clause catches "
            f"everything this platform raises")
    assert issubclass(exceptions.MeterMindError, Exception), (
        "MeterMindError should still be an ordinary exception")


def test_week1_day3_a_rollover_is_read_as_a_rollover_and_a_regression_as_nothing():
    from metermind.core.tariff_calculations import calculate_units_consumed

    reachable_in_this_cycle = 3.0 * 24 * 30 * 1.10
    assert calculate_units_consumed(14208.0, 14675.0, reachable_in_this_cycle) == 467.0, (
        "an ordinary cycle is the difference between the two readings")
    assert calculate_units_consumed(99500.0, 300.0, reachable_in_this_cycle) == 800.0, (
        "the meter passed its last digit and started again, so this cycle used eight hundred "
        "units and not a negative number")
    assert calculate_units_consumed(50000.0, 49500.0, reachable_in_this_cycle) == 0.0, (
        "a meter halfway up its range cannot have rolled over, so this reading is a mistake "
        "and no consumption may be claimed from it")


def test_week1_day3_the_package_prices_a_cycle_the_way_the_day_two_script_did():
    sys.path.insert(0, str(SCRIPTS))
    from day02_bill_pricing import net_bill_amount

    from metermind.core.tariff_calculations import calculate_bill_amount

    from_the_script = net_bill_amount("domestic", 467.0, 3.0)
    from_the_package = calculate_bill_amount("domestic", 467.0, 3.0)
    assert abs(from_the_package - from_the_script) < 0.005, (
        f"moving the arithmetic into the package must not change what a cycle costs. The "
        f"script said {from_the_script:.2f} and the package said {from_the_package:.2f}")


def test_week1_day3_the_reading_book_survives_a_round_trip_to_disk(tmp_path):
    from metermind.core.exceptions import ReadingStorageError
    from metermind.data_access.file_storage import ReadingFileStorage

    book = [{"account_number": "ACC10000123", "consumer_category": "domestic",
             "units_consumed": "467.0"},
            {"account_number": "ACC10000124", "consumer_category": "commercial",
             "units_consumed": "5120.5"}]
    storage = ReadingFileStorage(tmp_path)
    storage.save_readings_csv("book.csv", book)
    assert storage.load_readings_csv("book.csv") == book, (
        "every field should come back out of the file exactly as it went in")
    try:
        storage.load_readings_csv("nothing_here.csv")
        raise AssertionError("loading a file that is not there should have been refused")
    except ReadingStorageError:
        pass


# --------------------------------------------------------------------------- WEEK 1 DAY 4

def test_week1_day4_the_factory_returns_the_class_the_category_names():
    from metermind.core import entities
    from metermind.core.exceptions import UnsupportedCategoryError

    record = {"account_number": "ACC10000123", "consumer_category": "domestic",
              "sanctioned_load_kw": 3, "cycle_days": 30,
              "previous_reading": 14208, "current_reading": 14675}
    for category, wanted in (("domestic", entities.ServiceConnection),
                             ("commercial", entities.CommercialConnection),
                             ("agricultural", entities.AgriculturalConnection)):
        built = entities.create_service_connection(dict(record, consumer_category=category))
        assert isinstance(built, wanted), (
            f"a {category} record should be built as {wanted.__name__}, not "
            f"{type(built).__name__}")
    try:
        entities.create_service_connection(dict(record, consumer_category="industrial"))
        raise AssertionError("a category with no tariff schedule should have been refused")
    except UnsupportedCategoryError:
        pass


def test_week1_day4_the_domestic_charge_is_the_sum_of_its_blocks():
    from config import constants
    from metermind.core.entities import create_service_connection

    built = create_service_connection(
        {"account_number": "ACC10000123", "consumer_category": "domestic",
         "sanctioned_load_kw": 3, "cycle_days": 30,
         "previous_reading": 0, "current_reading": 467})
    by_hand, lower = 0.0, 0.0
    for upper, rate in constants.SLAB_TABLE_INR_BY_CATEGORY["domestic"]:
        by_hand += max(0.0, min(built.units_consumed, upper) - lower) * rate
        lower = upper
    assert abs(built.energy_charge_inr() - by_hand) < 0.005, (
        f"a domestic connection is charged block by block, which comes to {by_hand:.2f}, not "
        f"{built.energy_charge_inr():.2f}")


def test_week1_day4_one_unit_past_a_commercial_boundary_costs_more_than_one_unit():
    from config import constants
    from metermind.core.entities import create_service_connection

    record = {"account_number": "ACC10000123", "consumer_category": "commercial",
              "sanctioned_load_kw": 10, "cycle_days": 30, "previous_reading": 0}
    boundary = constants.SLAB_TABLE_INR_BY_CATEGORY["commercial"][0][0]
    at_the_boundary = create_service_connection(dict(record, current_reading=boundary))
    just_past_it = create_service_connection(dict(record, current_reading=boundary + 1))
    dearest_rate = max(rate for _, rate in constants.SLAB_TABLE_INR_BY_CATEGORY["commercial"])
    jump = just_past_it.energy_charge_inr() - at_the_boundary.energy_charge_inr()
    assert jump > dearest_rate, (
        f"crossing a boundary on a schedule that is not telescopic reprices every unit, so the "
        f"charge should jump by far more than one unit at any rate. It jumped {jump:.2f}")


def test_week1_day4_the_agricultural_subsidy_can_reach_zero_but_not_below():
    from metermind.core.entities import create_service_connection

    built = create_service_connection(
        {"account_number": "ACC10000123", "consumer_category": "agricultural",
         "sanctioned_load_kw": 5, "cycle_days": 30,
         "previous_reading": 0, "current_reading": 3000})
    assert built.subsidy_inr() > built.energy_charge_inr(), (
        "the subsidy on this cycle is larger than the energy it is set against, which is what "
        "makes the floor worth having")
    assert built.net_bill_inr() == 0.0, (
        f"a bill the subsidy more than covers is nil, not {built.net_bill_inr():.2f}, and "
        f"nothing is carried forward or refunded")


def test_week1_day4_a_connection_is_billable_exactly_when_it_has_no_refusal():
    from metermind.core.entities import create_service_connection

    record = {"account_number": "ACC10000123", "consumer_category": "domestic",
              "sanctioned_load_kw": 3, "cycle_days": 30,
              "previous_reading": 14208, "current_reading": 14675}
    clean = create_service_connection(record)
    assert clean.refusal_reasons() == [] and clean.is_billable(), (
        f"this cycle breaks no rule, yet it reported {clean.refusal_reasons()}")
    for broken in (dict(record, cycle_days=7),
                   dict(record, previous_reading=50000, current_reading=49500),
                   dict(record, current_reading=90000)):
        built = create_service_connection(broken)
        assert built.refusal_reasons(), f"{broken} should have been refused for something"
        assert not built.is_billable(), (
            "a connection with a reason against it cannot also be billable")


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
        "the timer should record how long the call took, in seconds and never negative")
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
    assert len(blocks) == len(earlier_part) == len(later_part)
    for (whole_limit, whole_rate), (earlier_limit, earlier_rate), (later_limit, _) in zip(
            blocks, earlier_part, later_part):
        assert earlier_rate == whole_rate, "proration changes the limits, never the rates"
        if whole_limit < constants.UNLIMITED_UNITS:
            assert abs(earlier_limit + later_limit - whole_limit) < 0.001, (
                f"the two parts of a split cycle should add back to the whole block limit "
                f"{whole_limit}, not {earlier_limit + later_limit}")


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
        f"whole cycle came to {whole:.2f} and the split came to {split:.2f}")


def test_week1_day5_the_loader_returns_objects_and_not_dictionaries(tmp_path):
    from metermind.core.entities import ServiceConnection
    from metermind.data_access.file_storage import ReadingFileStorage

    book = [{"account_number": "ACC10000123", "consumer_category": "domestic",
             "sanctioned_load_kw": "3", "cycle_days": "30",
             "previous_reading": "14208", "current_reading": "14675"},
            {"account_number": "ACC10000124", "consumer_category": "streetlight",
             "sanctioned_load_kw": "3", "cycle_days": "30",
             "previous_reading": "100", "current_reading": "200"}]
    storage = ReadingFileStorage(tmp_path)
    storage.save_readings_csv("book.csv", book)
    loaded = storage.load_connection_objects("book.csv")
    assert len(loaded) == 1, (
        f"the row with a category this platform has no schedule for should be left out rather "
        f"than stopping the load, so one connection should come back, not {len(loaded)}")
    assert isinstance(loaded[0], ServiceConnection), (
        f"the loader should return connections, not {type(loaded[0]).__name__}")
    assert loaded[0].units_consumed == 467.0, (
        "the connection that came back should have worked out its own units")


# --------------------------------------------------------------------------- WEEK 2 DAY 1

def test_week2_day1_the_whole_book_is_priced_without_a_loop_over_rows():
    import pandas

    from metermind.core.tariff_calculations import calculate_bill_amount, calculate_bill_amounts

    book = pandas.DataFrame({
        "consumer_category": ["domestic", "commercial", "agricultural", "domestic"],
        "units_consumed": [467.0, 467.0, 3000.0, 80.0],
        "sanctioned_load_kw": [3.0, 3.0, 5.0, 2.0]})
    together = calculate_bill_amounts(book)
    assert len(together) == len(book), "one bill should come back for every row of the book"
    for position, row in enumerate(book.itertuples()):
        one_at_a_time = calculate_bill_amount(row.consumer_category, row.units_consumed,
                                              row.sanctioned_load_kw)
        assert abs(together.iloc[position] - one_at_a_time) < 0.005, (
            f"row {position} came to {together.iloc[position]:.2f} priced together and "
            f"{one_at_a_time:.2f} priced on its own, and the two must agree")


def test_week2_day1_a_bill_the_subsidy_covers_is_nil_and_never_negative():
    import pandas

    from metermind.core.tariff_calculations import calculate_bill_amounts

    book = pandas.DataFrame({"consumer_category": ["agricultural", "agricultural"],
                             "units_consumed": [3000.0, 12000.0],
                             "sanctioned_load_kw": [5.0, 5.0]})
    assert (calculate_bill_amounts(book) >= 0.0).all(), (
        "a subsidy larger than the rest of the bill leaves nothing to pay, not a negative bill")


def test_week2_day1_every_shape_of_read_date_is_read_and_a_fifth_is_not():
    import pandas

    from metermind.data_access.cleaning_pipeline import parse_read_dates

    book = pandas.DataFrame({"read_date": ["2025-06-14", "14/06/2025", "14-Jun-2025",
                                           "14.06.2025", "not taken"]})
    read_on = parse_read_dates(book)
    assert read_on[:4].notna().all(), (
        f"all four shapes the field applications wrote should be read, not {list(read_on[:4])}")
    assert len(set(read_on[:4])) == 1, (
        "the four shapes are the same day written four ways, so they should read as one date")
    assert pandas.isna(read_on[4]), "a date in no agreed shape is a fault, not a fifth shape"


def test_week2_day1_a_row_is_refused_for_the_first_rule_it_breaks():
    import pandas

    from metermind.data_access.cleaning_pipeline import REJECTION_REASONS, first_broken_rule

    breaks_two = pandas.Series({"reading_id": "RDG1", "account_number": "", "consumer_category":
                                "streetlight", "sanctioned_load_kw": 3.0, "billing_period":
                                "2026-06", "cycle_days": 30, "previous_reading": 0.0,
                                "current_reading": 100.0, "units_consumed": 100.0,
                                "read_on": pandas.Timestamp("2026-06-14")})
    assert first_broken_rule(breaks_two) == REJECTION_REASONS[0], (
        "this row has no account number and an unknown category, and the first rule wins")
    clean = breaks_two.copy()
    clean["account_number"] = "ACC10000123"
    clean["consumer_category"] = "domestic"
    assert first_broken_rule(clean) == "", "a row that breaks no rule earns no reason"


def test_week2_day1_the_cleaner_loses_no_row_and_gives_every_refusal_a_published_reason(
        tmp_path):
    import pandas

    from config import constants
    from metermind.data_access.cleaning_pipeline import REJECTION_REASONS, clean_reading_book

    book = pandas.read_csv(constants.READING_BOOK_TRAIN_PATH)
    counted = clean_reading_book(constants.READING_BOOK_TRAIN_PATH, tmp_path / "clean.csv",
                                 tmp_path / "rejected.csv")
    assert counted["kept"] + counted["rejected"] == len(book), (
        f"{len(book)} rows went in and {counted['kept'] + counted['rejected']} came out, so "
        f"rows were lost or duplicated")
    rejected = pandas.read_csv(tmp_path / "rejected.csv")
    assert set(rejected["rejection_reason"]) <= set(REJECTION_REASONS), (
        "every reason written beside a refused row should be one of the published reasons")
    assert counted["rejected"] > 0 and counted["kept"] > counted["rejected"], (
        "the book carries faults, and far more good rows than bad ones")


# --------------------------------------------------------------------------- WEEK 2 DAY 2

def test_week2_day2_the_table_is_built_from_the_books_own_columns(tmp_path):
    import pandas

    from metermind.data_access.database_loader import READINGS_TABLE, ReadingDatabase

    book = pandas.DataFrame({"reading_id": ["RDG1", "RDG2"], "account_number":
                             ["ACC10000123", "ACC10000124"], "units_consumed": [467.0, 12.0]})
    database = ReadingDatabase(tmp_path / "book.sqlite")
    assert database.create_readings_table(book) == len(book), (
        "the loader should report having stored every row it was given")
    columns = [row[1] for row in
               database.connection.execute(f"PRAGMA table_info({READINGS_TABLE})").fetchall()]
    assert columns == list(book.columns), (
        f"the table's columns should be the book's own, in order: {list(book.columns)}, "
        f"not {columns}")


def test_week2_day2_a_reading_is_found_by_its_identifier_and_nothing_is_found_for_a_stranger(
        tmp_path):
    import pandas

    from metermind.data_access.database_loader import ReadingDatabase

    book = pandas.DataFrame({"reading_id": ["RDG1"], "account_number": ["ACC10000123"]})
    database = ReadingDatabase(tmp_path / "book.sqlite")
    database.create_readings_table(book)
    assert database.find_reading_by_identifier("RDG1")["account_number"] == "ACC10000123", (
        "the reading that was stored should come back by its identifier")
    assert database.find_reading_by_identifier("RDG9") is None, (
        "an identifier that was never stored should find nothing, not raise")


def test_week2_day2_removing_a_reading_takes_exactly_one_and_refuses_a_second_go(tmp_path):
    import pandas

    from metermind.core.exceptions import ReadingStorageError
    from metermind.data_access.database_loader import ReadingDatabase

    book = pandas.DataFrame({"reading_id": ["RDG1", "RDG2"], "account_number":
                             ["ACC10000123", "ACC10000124"]})
    database = ReadingDatabase(tmp_path / "book.sqlite")
    database.create_readings_table(book)
    assert database.delete_reading_by_identifier("RDG1") == 1, "exactly one row should go"
    assert database.find_reading_by_identifier("RDG2") is not None, "the other should remain"
    try:
        database.delete_reading_by_identifier("RDG1")
        raise AssertionError("removing a reading that is already gone should be refused")
    except ReadingStorageError:
        pass


def test_week2_day2_each_report_groups_without_repeating_a_group(tmp_path):
    import pandas

    from config import constants
    from metermind.data_access import database_reports
    from metermind.data_access.cleaning_pipeline import clean_reading_book
    from metermind.data_access.database_loader import ReadingDatabase

    pandas.read_csv(constants.READING_BOOK_TRAIN_PATH).head(4000).to_csv(
        tmp_path / "some.csv", index=False)
    clean_reading_book(tmp_path / "some.csv", tmp_path / "clean.csv", tmp_path / "bad.csv")
    clean = pandas.read_csv(tmp_path / "clean.csv")
    database = ReadingDatabase(tmp_path / "book.sqlite")
    database.create_readings_table(clean)
    for reading_report, grouped_by in (
            (database_reports.exception_rate_by_category, "consumer_category"),
            (database_reports.estimated_read_share_by_month, "billing_period"),
            (database_reports.billed_units_by_division, "division")):
        rows = reading_report(database)
        assert rows, f"{reading_report.__name__} answered with nothing at all"
        groups = [row[grouped_by] for row in rows]
        assert len(groups) == len(set(groups)), (
            f"{reading_report.__name__} repeated a {grouped_by}, so it is not grouping")
    written = database_reports.write_report_files(database, tmp_path / "reports.csv")
    assert pathlib.Path(written).is_file(), (
        f"the reports have to land somewhere a billing office can open, and {written} is not "
        f"a file")
    lines = pathlib.Path(written).read_text(encoding="utf-8").splitlines()
    headings = [one for one in lines if one and one == one.upper() and "," not in one]
    assert len(headings) == 3, (
        f"each of the three reports goes under its own heading in capitals, and this file "
        f"carries {headings}")
    assert "" in lines, "a blank line separates one report from the next"


# --------------------------------------------------------------------------- WEEK 2 DAY 3

def test_week2_day3_the_service_answers_that_it_is_up():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    answered = TestClient(build_application()).get(f"{API_PREFIX}/health")
    assert answered.status_code == 200, "the health route should answer 200"
    assert set(answered.json()) == {"service", "status"}, (
        f"the reply model settles what comes back, so it should be exactly the two fields, "
        f"not {sorted(answered.json())}")


def test_week2_day3_every_route_is_mounted_under_one_prefix():
    from metermind.api.application_factory import API_PREFIX, build_application

    paths = [route.path for route in build_application().routes
             if getattr(route, "methods", None) and not route.path.startswith("/openapi")]
    ours = [path for path in paths if path not in ("/docs", "/redoc", "/docs/oauth2-redirect")]
    assert ours, "the application should carry at least one route of its own"
    for path in ours:
        assert path.startswith(API_PREFIX), f"{path} is not mounted under {API_PREFIX}"


def test_week2_day3_two_applications_do_not_share_a_store():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import build_application

    first, second = build_application(), build_application()
    assert first is not second, (
        "the application comes from a factory, so asking twice gives two applications")
    assert TestClient(first).get("/docs").status_code == 200, "the documentation page is served"


def test_week2_day3_a_malformed_body_is_refused_before_any_handler_runs():
    from pydantic import ValidationError

    from metermind.api.schemas import ReadingSubmission

    good = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    assert ReadingSubmission(**good).account_number == "ACC10000123", (
        "a well formed body should be accepted and its identifier settled to one spelling")
    for field, wrong in (("account_number", "ACC1"), ("meter_serial", "mtr-ab-123456"),
                         ("billing_period", "2026-13")):
        try:
            ReadingSubmission(**dict(good, **{field: wrong}))
            raise AssertionError(f"{field}={wrong!r} should have been refused")
        except ValidationError:
            pass


def test_week2_day3_a_cycle_length_outside_the_permitted_range_is_refused_at_the_door():
    from pydantic import ValidationError

    from config import constants
    from metermind.api.schemas import ReadingSubmission

    good = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    for wrong in (constants.MINIMUM_CYCLE_DAYS - 1, constants.MAXIMUM_CYCLE_DAYS + 1):
        try:
            ReadingSubmission(**dict(good, cycle_days=wrong))
            raise AssertionError(f"a cycle of {wrong} days should have been refused")
        except ValidationError:
            pass
    try:
        ReadingSubmission(**dict(good, sanctioned_load_kw=0.0))
        raise AssertionError("a sanctioned load of nothing should have been refused")
    except ValidationError:
        pass


# --------------------------------------------------------------------------- WEEK 2 DAY 4

def test_week2_day4_a_reading_is_accepted_and_comes_back_priced():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    answered = client.post(f"{API_PREFIX}/readings", json=body)
    assert answered.status_code == 201, (
        f"a well formed reading should be created, not {answered.status_code}")
    assert answered.json()["net_bill_inr"] == 2854.48, (
        f"the service should reach the figure Week 1's arithmetic reached, not "
        f"{answered.json()['net_bill_inr']}")
    assert answered.json()["reading_id"], "a stored reading should be given an identifier"
    unbillable = client.post(f"{API_PREFIX}/readings",
                             json=dict(body, previous_reading=14675.0,
                                       current_reading=14208.0))
    assert unbillable.status_code == 201, (
        f"a reading the domain accepts but will not bill is still stored, not refused; got "
        f"{unbillable.status_code}")
    assert unbillable.json()["is_billable"] is False and unbillable.json()["refusal_reasons"], (
        f"it comes back saying it cannot be billed and why, got {unbillable.json()}")
    assert client.get(f"{API_PREFIX}/readings/{unbillable.json()['reading_id']}"
                      ).status_code == 200, (
        "and it can be read back afterwards, because refusing to bill is not refusing to keep")


def test_week2_day4_a_reading_nobody_can_price_is_refused_and_not_stored():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "streetlight", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    assert client.post(f"{API_PREFIX}/readings", json=body).status_code == 422, (
        "a category with no tariff schedule cannot be priced, so it cannot be filed")
    good = dict(body, consumer_category="domestic")
    stored = client.post(f"{API_PREFIX}/readings", json=good).json()["reading_id"]
    assert client.get(f"{API_PREFIX}/readings/{stored}").json()["consumer_category"] \
        == "domestic", (
        "the refused reading must not have been stored on the way to being refused, so the "
        "next reading in is the first one the book holds")


def test_week2_day4_a_reading_can_be_read_back_by_its_identifier():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000124", "meter_serial": "MTR-CD-654321",
            "consumer_category": "commercial", "billing_period": "2026-05",
            "sanctioned_load_kw": 15.0, "cycle_days": 31,
            "previous_reading": 1000.0, "current_reading": 4200.0}
    identifier = client.post(f"{API_PREFIX}/readings", json=body).json()["reading_id"]
    read_back = client.get(f"{API_PREFIX}/readings/{identifier}")
    assert read_back.status_code == 200, "the reading just stored should be readable"
    assert read_back.json()["units_consumed"] == 3200.0, (
        f"the reading should come back with the units it was sent with, not "
        f"{read_back.json()['units_consumed']}")


def test_week2_day4_an_identifier_nobody_stored_is_answered_with_not_found():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    stored = client.post(f"{API_PREFIX}/readings", json=body)
    assert stored.status_code == 201, (
        "the route has to be answering at all before its answer for a stranger means anything")
    assert client.get(
        f"{API_PREFIX}/readings/{stored.json()['reading_id']}").status_code == 200, (
        "the reading that was just stored should be readable before a stranger is asked for")
    assert client.get(f"{API_PREFIX}/readings/RDG00000000").status_code == 404, (
        "asking for a reading that is not there is a different answer from asking wrongly")


def test_week2_day4_the_store_hands_back_copies_and_not_what_it_is_keeping():
    from metermind.api.repository import InMemoryReadingRepository
    from metermind.core.exceptions import ReadingStorageError

    store = InMemoryReadingRepository()
    stored = store.add_reading({"account_number": "ACC10000123", "units_consumed": 467.0})
    stored["account_number"] = "ACC99999999"
    assert store.get_reading(stored["reading_id"])["account_number"] == "ACC10000123", (
        "changing what the store handed back must not change what the store is keeping")
    assert len(store.list_readings()) == 1, "one reading was added, so one should be listed"
    try:
        store.get_reading("RDG00000000")
        raise AssertionError("asking the store for a reading it has not got should be refused")
    except ReadingStorageError:
        pass


# --------------------------------------------------------------------------- WEEK 2 DAY 5

def test_week2_day5_both_tables_are_created_against_a_fresh_database(tmp_path):
    from sqlalchemy import inspect

    from metermind.api.orm_models import build_session_factory

    factory = build_session_factory(tmp_path / "metermind.sqlite")
    with factory() as session:
        tables = set(inspect(session.get_bind()).get_table_names())
    assert {"connections", "readings"} <= tables, (
        f"both mapped classes should have created their tables, found {sorted(tables)}")


def test_week2_day5_two_sessions_are_independent_of_each_other(tmp_path):
    from metermind.api.orm_models import ReadingRow, build_session_factory

    factory = build_session_factory(tmp_path / "metermind.sqlite")
    writing, reading = factory(), factory()
    assert writing is not reading, "a factory should give a new session each time it is asked"
    writing.add(ReadingRow(reading_id="RDG1", account_number="ACC10000123",
                           meter_serial="MTR-AB-123456", consumer_category="domestic",
                           billing_period="2026-06", sanctioned_load_kw=3.0, cycle_days=30,
                           previous_reading=14208.0, current_reading=14675.0,
                           read_type="actual"))
    writing.commit()
    assert reading.get(ReadingRow, "RDG1").account_number == "ACC10000123", (
        "what one session commits should be visible to another session")


def test_week2_day5_replacing_a_reading_prices_the_replacement_and_not_the_original():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    first = client.post(f"{API_PREFIX}/readings", json=body).json()
    replaced = client.put(f"{API_PREFIX}/readings/{first['reading_id']}",
                          json=dict(body, consumer_category="commercial"))
    assert replaced.status_code == 200, "replacing a stored reading should succeed"
    assert replaced.json()["reading_id"] == first["reading_id"], (
        "a replacement keeps the identifier it replaced")
    assert replaced.json()["net_bill_inr"] > first["net_bill_inr"], (
        f"the same units on a commercial schedule cost more than on a domestic one, so the "
        f"bill should have risen from {first['net_bill_inr']}, not stayed or fallen")


def test_week2_day5_replacing_or_removing_something_that_is_not_there_is_not_found():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    stored = client.post(f"{API_PREFIX}/readings", json=body).json()["reading_id"]
    assert client.put(f"{API_PREFIX}/readings/{stored}", json=body).status_code == 200, (
        "both routes have to be answering at all before their answer for a stranger means "
        "anything")
    assert client.put(f"{API_PREFIX}/readings/RDG00000000", json=body).status_code == 404, (
        "replacing a reading that was never stored is not found")
    assert client.delete(f"{API_PREFIX}/readings/RDG00000000").status_code == 404, (
        "removing a reading that was never stored is not found")


def test_week2_day5_a_reading_removed_once_is_gone_and_cannot_be_removed_twice():
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import API_PREFIX, build_application

    client = TestClient(build_application())
    body = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30,
            "previous_reading": 14208.0, "current_reading": 14675.0}
    identifier = client.post(f"{API_PREFIX}/readings", json=body).json()["reading_id"]
    assert client.delete(f"{API_PREFIX}/readings/{identifier}").status_code == 204, (
        "removing a stored reading succeeds and sends nothing back but the status")
    assert client.get(f"{API_PREFIX}/readings/{identifier}").status_code == 404, (
        "a reading that has been removed is no longer there to read")
    assert client.delete(f"{API_PREFIX}/readings/{identifier}").status_code == 404, (
        "removing it a second time is not found")


# --------------------------------------------------------------------------- WEEK 3 DAY 1

def test_week3_day1_the_interface_names_five_operations_and_both_stores_answer_all_five():
    from metermind.api.repository import InMemoryReadingRepository, ReadingRepository
    from metermind.api.sql_repository import SqlReadingRepository

    wanted = {"add_reading", "get_reading", "replace_reading", "list_readings", "remove_reading"}
    assert set(ReadingRepository.__abstractmethods__) == wanted, (
        f"the interface should name exactly the five operations, not "
        f"{sorted(ReadingRepository.__abstractmethods__)}")
    for store in (InMemoryReadingRepository, SqlReadingRepository):
        assert issubclass(store, ReadingRepository), f"{store.__name__} is not the interface"
        assert not store.__abstractmethods__, (
            f"{store.__name__} leaves {sorted(store.__abstractmethods__)} unimplemented")


def test_week3_day1_a_half_built_store_cannot_be_created_at_all():
    from metermind.api.repository import ReadingRepository

    class HalfBuiltRepository(ReadingRepository):
        def add_reading(self, reading):
            return reading

    try:
        HalfBuiltRepository()
        raise AssertionError("a store that implements one of five operations should not build")
    except TypeError:
        pass


def test_week3_day1_the_two_stores_answer_the_same_way_for_the_same_call(tmp_path):
    from metermind.api.repository import STORED_READING_FIELDS, InMemoryReadingRepository
    from metermind.api.sql_repository import SqlReadingRepository

    reading = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
               "consumer_category": "domestic", "billing_period": "2026-06",
               "sanctioned_load_kw": 3.0, "cycle_days": 30, "previous_reading": 14208.0,
               "current_reading": 14675.0, "read_type": "actual", "case_status": None}
    for store in (InMemoryReadingRepository(), SqlReadingRepository(tmp_path / "one.sqlite")):
        stored = store.add_reading(dict(reading, division="North", noted_by="je/1180"))
        read_back = store.get_reading(stored["reading_id"])
        assert read_back["account_number"] == "ACC10000123", (
            f"{type(store).__name__} did not give back what it was given")
        assert len(store.list_readings()) == 1, (
            f"{type(store).__name__} stored one reading and lists a different number")
        assert set(read_back) == set(STORED_READING_FIELDS), (
            f"both stores answer with exactly the published fields, so a caller cannot tell "
            f"them apart by what comes back; {type(store).__name__} answered with "
            f"{sorted(read_back)}")
    reopened = SqlReadingRepository(tmp_path / "one.sqlite")
    assert reopened.add_reading(reading)["reading_id"] not in {
        one["reading_id"] for one in reopened.list_readings()[:-1]}, (
        "the store that survives a restart has to keep numbering where the file left off; "
        "starting again from the first number collides with a reading already on it")


def test_week3_day1_both_stores_keep_the_same_fields_through_a_replacement(tmp_path):
    from metermind.api.repository import STORED_READING_FIELDS, InMemoryReadingRepository
    from metermind.api.sql_repository import SqlReadingRepository

    reading = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
               "consumer_category": "domestic", "billing_period": "2026-06",
               "sanctioned_load_kw": 3.0, "cycle_days": 30, "previous_reading": 14208.0,
               "current_reading": 14675.0, "read_type": "actual", "case_status": None}
    for store in (InMemoryReadingRepository(), SqlReadingRepository(tmp_path / "two.sqlite")):
        stored = store.add_reading(reading)
        changed = store.replace_reading(stored["reading_id"],
                                        dict(reading, consumer_category="commercial"))
        assert changed["consumer_category"] == "commercial", (
            f"{type(store).__name__} did not take the replacement")
        assert changed["reading_id"] == stored["reading_id"], (
            "a replacement keeps the identifier it replaced")
        assert set(changed) == set(STORED_READING_FIELDS), (
            f"a field the caller supplied that is not one of the stored fields is not written, "
            f"and none of the stored ones is lost; {type(store).__name__} came back with "
            f"{sorted(changed)}")
        kept_anyway = store.replace_reading(stored["reading_id"],
                                            dict(reading, division="North", junk="x"))
        assert set(kept_anyway) == set(STORED_READING_FIELDS), (
            f"the two stores must not diverge in what they keep, so neither may hold a field "
            f"the other cannot; {type(store).__name__} kept {sorted(kept_anyway)}")


def test_week3_day1_both_stores_refuse_the_same_way_for_something_that_is_not_there(tmp_path):
    from metermind.api.repository import InMemoryReadingRepository
    from metermind.api.sql_repository import SqlReadingRepository
    from metermind.core.exceptions import ReadingStorageError

    for store in (InMemoryReadingRepository(), SqlReadingRepository(tmp_path / "three.sqlite")):
        for operation in ("get_reading", "replace_reading", "remove_reading"):
            arguments = ("RDG00000000", {}) if operation == "replace_reading" \
                else ("RDG00000000",)
            try:
                getattr(store, operation)(*arguments)
                raise AssertionError(
                    f"{type(store).__name__}.{operation} did not refuse a stranger")
            except ReadingStorageError:
                pass


# --------------------------------------------------------------------------- WEEK 3 DAY 2

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


# --------------------------------------------------------------------------- WEEK 3 DAY 3

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


# --------------------------------------------------------------------------- WEEK 3 DAY 4

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


# --------------------------------------------------------------------------- WEEK 3 DAY 5


def test_week3_day5_the_preparation_survives_a_missing_number_and_a_category_it_never_saw():
    import pandas

    from metermind.exception_models.feature_pipeline import (
        MODELLING_CATEGORY_COLUMNS,
        MODELLING_NUMBER_COLUMNS,
        build_feature_pipeline,
    )

    rows = 40
    seen = pandas.DataFrame(
        {**{name: [float(one) for one in range(rows)] for name in MODELLING_NUMBER_COLUMNS},
         **{name: ["known"] * rows for name in MODELLING_CATEGORY_COLUMNS}})
    prepared = build_feature_pipeline().fit(seen)
    strange = seen.head(1).copy()
    strange.loc[:, MODELLING_NUMBER_COLUMNS[0]] = float("nan")
    strange.loc[:, MODELLING_CATEGORY_COLUMNS[0]] = "a category nobody has seen"
    answered = prepared.transform(strange)
    assert answered.shape[0] == 1, "one row in should be one row out"
    assert answered.shape[1] == prepared.transform(seen.head(1)).shape[1], (
        "an unseen category must not change how many columns come out, or the model that was "
        "fitted on the old width cannot be used at all")


def test_week3_day5_the_baseline_beats_always_saying_the_commonest_class(tmp_path):
    import pandas

    from config import constants
    from metermind.data_access.cleaning_pipeline import clean_reading_book
    from metermind.exception_models.baseline_model import (
        score_exception_model,
        split_readings,
        train_baseline_model,
    )

    pandas.read_csv(constants.READING_BOOK_TRAIN_PATH).head(12000).to_csv(
        tmp_path / "some.csv", index=False)
    clean_reading_book(tmp_path / "some.csv", tmp_path / "clean.csv", tmp_path / "bad.csv")
    book = pandas.read_csv(tmp_path / "clean.csv").sample(
        7000, random_state=constants.MODEL_SEED)
    fitting_columns, held_out_columns, fitting_classes, held_out_classes = split_readings(book)
    trained = train_baseline_model(fitting_columns, fitting_classes)
    scored = score_exception_model(trained, held_out_columns, held_out_classes)
    always_the_commonest = held_out_classes.value_counts(normalize=True).max()
    assert scored["accuracy"] > always_the_commonest + 0.10, (
        f"a model that cannot beat always naming the commonest class has learnt nothing; it "
        f"scored {scored['accuracy']:.3f} against {always_the_commonest:.3f}")
    assert set(scored["per_class"]) >= set(constants.EXCEPTION_CLASSES), (
        "the score should report every class separately, because the rare ones are the point")


def test_week3_day5_a_saved_model_reloads_and_decides_exactly_as_it_did_before(tmp_path):
    import pandas

    from config import constants
    from metermind.data_access.cleaning_pipeline import clean_reading_book
    from metermind.exception_models.baseline_model import (
        load_model,
        predict_exception,
        save_model,
        split_readings,
        train_baseline_model,
    )

    pandas.read_csv(constants.READING_BOOK_TRAIN_PATH).head(12000).to_csv(
        tmp_path / "some.csv", index=False)
    clean_reading_book(tmp_path / "some.csv", tmp_path / "clean.csv", tmp_path / "bad.csv")
    book = pandas.read_csv(tmp_path / "clean.csv").sample(
        3500, random_state=constants.MODEL_SEED)
    fitting_columns, held_out_columns, fitting_classes, _ = split_readings(book)
    trained = train_baseline_model(fitting_columns, fitting_classes)
    save_model(trained, tmp_path / "baseline.joblib")
    reloaded = load_model(tmp_path / "baseline.joblib")
    before = predict_exception(trained, held_out_columns)
    after = predict_exception(reloaded, held_out_columns)
    assert before == after, (
        "a model that decides differently after being saved and loaded cannot be served")


def a_small_book(rows=400):
    """A few hundred real rows, taken straight off the book without the cleaning pass.

    This is what a testcase that is checking PLUMBING uses - that a pipeline handles an unseen
    category, that a saved model reloads unchanged, that a search cannot settle on something
    dearer than where it started. None of those are claims about how good the model is, so none
    of them needs thirty thousand rows to make.
    """
    import pandas

    from config import constants

    book = pandas.read_csv(constants.READING_BOOK_TRAIN_PATH, nrows=rows * 8)
    book = book[book["consumer_category"].isin(constants.CONSUMER_CATEGORIES)]
    for number in ("sanctioned_load_kw", "cycle_days", "units_consumed"):
        book = book[pandas.to_numeric(book[number], errors="coerce").notna()]
    book = book[pandas.to_numeric(book["sanctioned_load_kw"]) > 0]
    return book.head(rows).reset_index(drop=True)


def a_small_widened_book(rows=400):
    from metermind.exception_models.feature_engineering import widen_readings

    return widen_readings(a_small_book(rows))


def a_clean_book(tmp_path, rows):
    """The whole cleaning pass over real rows. Only a testcase making a claim about how well a
    model reads the book should be paying for this."""
    import pandas

    from config import constants
    from metermind.data_access.cleaning_pipeline import clean_reading_book

    pandas.read_csv(constants.READING_BOOK_TRAIN_PATH).head(rows * 2).to_csv(
        tmp_path / "some.csv", index=False)
    clean_reading_book(tmp_path / "some.csv", tmp_path / "clean.csv", tmp_path / "bad.csv")
    return pandas.read_csv(tmp_path / "clean.csv").sample(rows,
                                                          random_state=constants.MODEL_SEED)


# --------------------------------------------------------------------------- WEEK 4 DAY 1

def test_week4_day1_a_model_is_built_unfitted_and_fitting_it_is_a_separate_step():
    import pandas
    from sklearn.exceptions import NotFittedError

    from metermind.exception_models.baseline_model import build_baseline_model
    from metermind.exception_models.tree_models import (
        build_decision_tree_model,
        build_random_forest_model,
    )

    for build in (build_baseline_model, build_decision_tree_model, build_random_forest_model):
        model = build()
        try:
            model.predict(pandas.DataFrame({"units_consumed": [1.0]}))
            raise AssertionError(f"{build.__name__} came back already fitted")
        except (NotFittedError, KeyError, ValueError):
            pass


def test_week4_day1_all_three_families_are_measured_on_the_same_rows():
    from metermind.exception_models.baseline_model import build_baseline_model, split_readings
    from metermind.exception_models.tree_models import (
        build_decision_tree_model,
        build_random_forest_model,
    )

    book = a_small_book()
    first = split_readings(book)
    second = split_readings(book)
    assert list(first[0].index) == list(second[0].index), (
        "the split is settled by a seed, so asking twice must give the same rows; if it does "
        "not, no two models are ever compared on the same thing")
    assert not set(first[0].index) & set(first[1].index), (
        "a row used to fit a model must not also be used to score it")
    assert len(first[0]) + len(first[1]) == len(book), (
        "every row belongs to one side of the split or the other, and none to both")
    def columns_it_prepares(model):
        return [(name, list(columns)) for name, _, columns in model["prepare"].transformers]

    prepared_by_the_baseline = columns_it_prepares(build_baseline_model("balanced"))
    for build in (build_decision_tree_model, build_random_forest_model):
        assert columns_it_prepares(build("balanced")) == prepared_by_the_baseline, (
            f"{build.__name__} prepares different columns from the baseline, so the three are "
            f"not seeing the same book even when they are handed the same rows")


def test_week4_day1_the_forest_reads_the_hardest_class_at_least_as_well_as_one_tree(tmp_path):
    from metermind.exception_models.baseline_model import split_readings
    from metermind.exception_models.tree_models import train_decision_tree, train_random_forest

    book = a_clean_book(tmp_path, 1800)
    fitting, held_out, fitting_classes, held_out_classes = split_readings(book)
    one_tree = train_decision_tree(fitting, fitting_classes, "balanced")
    many_trees = train_random_forest(fitting, fitting_classes, "balanced")
    assert many_trees.score(held_out, held_out_classes) >= \
        one_tree.score(held_out, held_out_classes) - 0.02, (
        "an ensemble of trees should not be meaningfully worse than one of the trees in it")


def test_week4_day1_weighting_the_classes_lifts_the_class_the_model_finds_hardest(tmp_path):
    from metermind.exception_models.baseline_model import split_readings
    from metermind.exception_models.tree_models import compare_class_weighting

    book = a_clean_book(tmp_path, 1800)
    fitting, held_out, fitting_classes, held_out_classes = split_readings(book)
    compared = compare_class_weighting(fitting, held_out, fitting_classes, held_out_classes)
    assert set(compared) == {"unweighted", "balanced"}, (
        f"both weightings should be reported so the difference can be seen, got "
        f"{sorted(compared)}")
    assert compared["balanced"]["lowest_recall"] > compared["unweighted"]["lowest_recall"], (
        f"weighting exists to help the class the model finds hardest; it moved from "
        f"{compared['unweighted']['lowest_recall']:.3f} to "
        f"{compared['balanced']['lowest_recall']:.3f}")


def test_week4_day1_no_model_ever_names_a_class_the_platform_does_not_publish():
    from config import constants
    from metermind.exception_models.baseline_model import split_readings
    from metermind.exception_models.tree_models import train_random_forest

    fitting, held_out, fitting_classes, _ = split_readings(a_small_book())
    decided = set(train_random_forest(fitting, fitting_classes, "balanced").predict(held_out))
    assert decided <= set(constants.EXCEPTION_CLASSES), (
        f"the model named {decided - set(constants.EXCEPTION_CLASSES)}, which no queue exists "
        f"for and no inspector would know what to do with")


# --------------------------------------------------------------------------- WEEK 4 DAY 2

def test_week4_day2_four_families_are_offered_and_every_one_comes_back_unfitted():
    from metermind.exception_models.cross_validation import every_candidate_model

    offered = every_candidate_model("balanced")
    assert len(offered) == 4, (
        f"four families should be compared, not {len(offered)}: {sorted(offered)}")
    for name, model in offered.items():
        assert hasattr(model, "fit"), f"{name} is not something that can be fitted"
        assert not hasattr(model[-1], "classes_"), f"{name} came back already fitted"


def test_week4_day2_the_folds_are_stratified_so_every_fold_carries_every_class():
    from config import constants
    from metermind.exception_models.baseline_model import split_readings
    from metermind.exception_models.cross_validation import cross_validate_models

    fitting, _, fitting_classes, _ = split_readings(a_small_book(600))
    scored = cross_validate_models(fitting, fitting_classes, folds=3)
    by_chance = 1.0 / len(constants.EXCEPTION_CLASSES)
    for name, folds in scored.items():
        assert min(folds) > by_chance, (
            f"{name} scored {min(folds):.3f} on its worst fold, against {by_chance:.3f} for "
            f"guessing; a fold that has lost a class scores at chance whatever the model is")


def test_week4_day2_the_spread_across_folds_is_never_negative_and_never_wider_than_the_range():
    from metermind.exception_models.cross_validation import fold_spread

    for folds in ([0.80, 0.82, 0.79, 0.81], [0.5], [0.9, 0.9, 0.9]):
        spread = fold_spread(folds)
        assert spread >= 0.0, f"a spread cannot be negative, got {spread} from {folds}"
        assert spread <= max(folds) - min(folds) + 1e-9, (
            f"the spread cannot be wider than the folds themselves, got {spread} from {folds}")


def test_week4_day2_the_written_file_carries_one_row_for_every_model_and_fold(tmp_path):
    import csv

    from metermind.exception_models.cross_validation import (
        CROSS_VALIDATION_FIELDS,
        write_cross_validation,
    )

    scored = {"baseline": [0.71, 0.72, 0.70], "random_forest": [0.88, 0.89, 0.88]}
    written = write_cross_validation(scored, tmp_path / "cross_validation.csv")
    with open(written, encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == list(CROSS_VALIDATION_FIELDS), (
        f"the file should open with its published columns, got {rows[0]}")
    assert len(rows) - 1 == 6, (
        f"two models on three folds is six rows, not {len(rows) - 1}")


# --------------------------------------------------------------------------- WEEK 4 DAY 3

def test_week4_day3_load_factor_is_units_over_what_the_load_could_draw():
    from config import constants
    from metermind.exception_models.feature_engineering import add_load_factor

    widened = add_load_factor(a_small_book(600))
    by_hand = widened["units_consumed"] / (widened["sanctioned_load_kw"]
                                           * constants.HOURS_IN_A_DAY * widened["cycle_days"])
    assert (widened["load_factor"] - by_hand).abs().max() < 1e-9, (
        "load factor is the consumption over what the sanctioned load could physically draw "
        "in the cycle, and nothing else")
    impossible = widened[widened["load_factor"] > 1.0]
    assert len(impossible) > 0, (
        "the book carries connections drawing more than their load allows, and those are what "
        "the column is for")


def test_week4_day3_the_ratio_to_the_average_is_one_when_the_cycle_is_the_average():
    import pandas

    from metermind.exception_models.feature_engineering import add_consumption_ratio_to_average

    book = pandas.DataFrame({"units_consumed": [400.0, 800.0, 0.0],
                             "twelve_month_average_units": [400.0, 400.0, 0.0]})
    widened = add_consumption_ratio_to_average(book)
    assert abs(widened["consumption_ratio_to_average"].iloc[0] - 1.0) < 1e-9, (
        "a cycle equal to its own average is one times the average")
    assert abs(widened["consumption_ratio_to_average"].iloc[1] - 2.0) < 1e-9, (
        "twice the average is two")
    assert widened["consumption_ratio_to_average"].notna().all(), (
        "a connection with no history must not produce a value nothing can be done with")


def test_week4_day3_widening_adds_exactly_three_columns_and_changes_no_other():
    from metermind.exception_models.feature_engineering import widen_readings
    from metermind.exception_models.feature_pipeline import DERIVED_NUMBER_COLUMNS

    narrow = a_small_book(500)
    widened = widen_readings(narrow)
    added = set(widened.columns) - set(narrow.columns)
    assert added == set(DERIVED_NUMBER_COLUMNS), (
        f"widening should add the three published columns, it added {sorted(added)}")
    for column in narrow.columns:
        assert widened[column].equals(narrow[column]), (
            f"widening changed {column}, and a derived column must never alter what it derives "
            f"from")


def test_week4_day3_the_widened_column_set_is_the_narrow_one_plus_the_three():
    from metermind.exception_models.feature_pipeline import (
        DERIVED_NUMBER_COLUMNS,
        MODELLING_COLUMNS,
        modelling_columns,
    )

    assert set(modelling_columns(False)) == set(MODELLING_COLUMNS), (
        "asked for the narrow set, the module should give the set it started with")
    assert set(modelling_columns(True)) == set(MODELLING_COLUMNS) | set(DERIVED_NUMBER_COLUMNS), (
        "asked for the widened set, it should give that plus the three derived columns and "
        "nothing else")
    assert len(set(MODELLING_COLUMNS) & set(DERIVED_NUMBER_COLUMNS)) == 0, (
        "a derived column that is already in the book is not derived")


# --------------------------------------------------------------------------- WEEK 4 DAY 4

def test_week4_day4_the_cost_matrix_is_five_by_five_with_a_zero_diagonal():
    from config import constants
    from metermind.exception_models.champion_model import COST_MATRIX

    assert set(COST_MATRIX) == set(constants.EXCEPTION_CLASSES), (
        f"the matrix should cover every class the platform publishes, got {sorted(COST_MATRIX)}")
    for truth, costs in COST_MATRIX.items():
        assert set(costs) == set(constants.EXCEPTION_CLASSES), (
            f"the row for {truth} does not cover every class it could be confused with")
        assert costs[truth] == 0.0, (
            f"getting {truth} right should cost nothing, not {costs[truth]}")


def test_week4_day4_calling_an_honest_consumer_a_thief_is_the_most_expensive_mistake():
    from metermind.exception_models.champion_model import COST_MATRIX

    every_mistake = {(truth, said): cost for truth, costs in COST_MATRIX.items()
                     for said, cost in costs.items() if truth != said}
    dearest = max(every_mistake, key=every_mistake.get)
    assert dearest == ("genuine_high_usage", "tamper_suspected"), (
        f"a wrongly raised tamper case means a penalty bill and a police complaint, so it "
        f"should be the dearest cell in the matrix; {dearest} is dearer")
    assert every_mistake[("genuine_high_usage", "tamper_suspected")] > \
        every_mistake[("tamper_suspected", "genuine_high_usage")], (
        "accusing the innocent should cost more than missing the guilty, or the matrix is not "
        "saying anything the accuracy did not already say")


def test_week4_day4_a_perfect_prediction_costs_nothing_and_any_mistake_costs_something():
    from metermind.exception_models.champion_model import expected_cost

    truth = ["genuine_high_usage", "meter_fault", "tamper_suspected"]
    assert expected_cost(truth, truth) == 0.0, "getting everything right should cost nothing"
    assert expected_cost(truth, ["tamper_suspected", "meter_fault", "tamper_suspected"]) > 0.0, (
        "a mistake that costs nothing is a mistake the matrix is not measuring")


def test_week4_day4_the_rule_the_search_settles_on_is_never_dearer_than_plain_argmax(tmp_path):
    from metermind.exception_models.baseline_model import split_readings
    from metermind.exception_models.champion_model import (
        MODELS_THAT_REPORT_CONFIDENCE,
        choose_champion,
        choose_operating_rule,
        expected_cost,
        predict_with_rule,
    )
    from metermind.exception_models.feature_pipeline import modelling_columns
    from metermind.exception_models.tree_models import build_random_forest_model

    columns = list(modelling_columns(True))
    fitting, held_out, fitting_classes, held_out_classes = split_readings(
        a_small_widened_book(600), columns)
    champion = build_random_forest_model("balanced", True)
    champion.fit(fitting, fitting_classes)
    rule = choose_operating_rule(champion, held_out, held_out_classes)
    argmax = expected_cost(held_out_classes, champion.predict(held_out))
    assert rule["expected_cost"] <= argmax + 1e-9, (
        f"the search includes the rule that does nothing, so it can never settle on something "
        f"dearer; it chose {rule['expected_cost']:.4f} against argmax at {argmax:.4f}")
    held_back = predict_with_rule(champion, held_out, 1.01, 0.0)
    assert "tamper_suspected" not in held_back, (
        "a floor no confidence can clear should stop the class being named at all, which is "
        "what makes the floor a control rather than a decoration")
    chosen, considered = choose_champion(fitting, fitting_classes, folds=2)
    assert set(considered) == set(MODELS_THAT_REPORT_CONFIDENCE), (
        f"only the families that report a confidence can carry an operating rule, so three are "
        f"compared and not four; this compared {sorted(considered)}")
    assert chosen in MODELS_THAT_REPORT_CONFIDENCE, (
        f"the champion has to be a family a floor can be applied to, and {chosen} is not one")


def test_week4_day4_a_saved_champion_and_its_rule_reach_the_same_decisions(tmp_path):
    import json

    from metermind.exception_models.baseline_model import load_model, split_readings
    from metermind.exception_models.champion_model import predict_with_rule, save_champion
    from metermind.exception_models.feature_pipeline import modelling_columns
    from metermind.exception_models.tree_models import build_random_forest_model

    columns = list(modelling_columns(True))
    fitting, held_out, fitting_classes, _ = split_readings(a_small_widened_book(400), columns)
    champion = build_random_forest_model("balanced", True)
    champion.fit(fitting, fitting_classes)
    rule = {"tamper_floor": 0.60, "fault_floor": 0.40, "expected_cost": 0.0}
    model_path, rule_path = save_champion(champion, rule, tmp_path / "champion.joblib",
                                          tmp_path / "operating_rule.json")
    reloaded = load_model(model_path)
    kept = json.loads(rule_path.read_text())
    assert kept["tamper_floor"] == rule["tamper_floor"], "the rule should survive being written"
    before = predict_with_rule(champion, held_out, rule["tamper_floor"], rule["fault_floor"])
    after = predict_with_rule(reloaded, held_out, kept["tamper_floor"], kept["fault_floor"])
    assert before == after, (
        "a champion that decides differently after being saved cannot be the thing that runs")


# --------------------------------------------------------------------------- WEEK 4 DAY 5

def test_week4_day5_there_is_one_queue_for_every_class_and_no_class_unmapped():
    from config import constants
    from metermind.exception_models.investigation_queues import QUEUE_BY_DECISION, QUEUES

    assert set(QUEUES) == set(constants.EXCEPTION_CLASSES), (
        f"every class the model can name needs somewhere to go, got {sorted(QUEUES)}")
    assert set(QUEUE_BY_DECISION) == set(QUEUES), (
        "a class with no file to be written to is a class nobody works")
    assert len(set(QUEUE_BY_DECISION.values())) == len(QUEUES), (
        f"two classes writing to one file would put two teams' work in one place: "
        f"{sorted(QUEUE_BY_DECISION.values())}")


def test_week4_day5_every_row_lands_in_exactly_one_queue():
    from metermind.exception_models.investigation_queues import sort_into_queues

    book = a_small_book(300)
    decided = ["genuine_high_usage", "tamper_suspected"] * (len(book) // 2)
    decided = (decided + ["meter_fault"] * len(book))[:len(book)]
    sorted_out = sort_into_queues(book, decided)
    landed = [one for rows in sorted_out.values() for one in rows["reading_id"]]
    assert len(landed) == len(book), (
        f"{len(book)} rows went in and {len(landed)} came out across the queues")
    assert len(set(landed)) == len(landed), (
        "a reading in two queues would be worked twice by two different teams")


def test_week4_day5_the_queue_counts_add_back_to_the_book():
    from metermind.exception_models.investigation_queues import queue_counts, sort_into_queues

    book = a_small_book(300)
    decided = ["estimated_read"] * len(book)
    counted = queue_counts(sort_into_queues(book, decided))
    assert sum(counted.values()) == len(book), (
        f"the counts should add back to {len(book)}, they add to {sum(counted.values())}")
    assert counted["estimated_read"] == len(book), (
        "every row was decided the same way, so every row should be in that one queue")
    assert all(counted[name] == 0 for name in counted if name != "estimated_read"), (
        "the other four queues should be empty rather than missing")


def test_week4_day5_five_files_are_written_and_each_one_carries_a_header(tmp_path):
    from metermind.exception_models.investigation_queues import (
        QUEUES,
        sort_into_queues,
        write_queue_files,
    )

    book = a_small_book(250)
    decided = list(QUEUES) * len(book)
    sorted_out = sort_into_queues(book, decided[:len(book)])
    written = write_queue_files(sorted_out,
                                {name: tmp_path / f"queue_{name}.csv" for name in QUEUES})
    assert len(written) == len(QUEUES), (
        f"one file for each of the {len(QUEUES)} queues, got {len(written)}")
    for name, path in written.items():
        assert path.is_file(), f"{name} was not written at all"
        assert path.read_text(encoding="utf-8").splitlines()[0].startswith("reading_id"), (
            f"{name} should open with a header row, or nobody can read it")


def test_week4_day5_the_queue_a_reading_lands_in_is_the_class_it_was_given():
    from metermind.exception_models.investigation_queues import sort_into_queues

    book = a_small_book(250)
    decided = ["tamper_suspected"] * 10 + ["genuine_high_usage"] * (len(book) - 10)
    sorted_out = sort_into_queues(book, decided)
    assert list(sorted_out["tamper_suspected"]["reading_id"]) == \
        list(book["reading_id"].head(10)), (
        "the ten readings called tamper should be the ten in the vigilance queue, in order")
    assert len(sorted_out["genuine_high_usage"]) == len(book) - 10, (
        "and everything else should be in the queue nobody works")


def a_fitted_champion(tmp_path, rows=500):
    from metermind.exception_models.baseline_model import split_readings
    from metermind.exception_models.champion_model import save_champion
    from metermind.exception_models.feature_pipeline import modelling_columns
    from metermind.exception_models.tree_models import build_random_forest_model

    book = a_small_widened_book(rows)
    columns = list(modelling_columns(True))
    fitting, held_out, fitting_classes, held_out_classes = split_readings(book, columns)
    champion = build_random_forest_model("balanced", True)
    champion.fit(fitting, fitting_classes)
    save_champion(champion, {"tamper_floor": 0.60, "fault_floor": 0.0, "expected_cost": 0.0},
                  tmp_path / "champion.joblib", tmp_path / "operating_rule.json")
    return champion, held_out, held_out_classes


def a_reading_to_screen():
    return {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30, "previous_reading": 14208.0,
            "current_reading": 14675.0, "units_consumed": 467.0,
            "twelve_month_average_units": 302.5, "same_month_last_year_units": 290.0,
            "consecutive_estimated_reads": 0, "days_since_actual_read": 0,
            "neighbourhood_average_units": 310.0, "arrears_inr": 0.0,
            "payment_defaults_last_year": 0, "seal_check_result": "intact",
            "meter_make": "Secure", "division": "North",
            "meter_install_date": "2019-04-02", "cycle_end_date": "2026-06-14"}


def a_screening_client(tmp_path):
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import build_application
    from metermind.api.routers import screening

    a_fitted_champion(tmp_path)
    screening.champion_model_path = str(tmp_path / "champion.joblib")
    screening.operating_rule_path = str(tmp_path / "operating_rule.json")
    screening.loaded_champion.clear()
    return TestClient(build_application())


# --------------------------------------------------------------------------- WEEK 5 DAY 1

def test_week5_day1_screening_needs_a_token_like_the_rest_of_the_book(tmp_path):
    from metermind.api.application_factory import API_PREFIX

    client = a_screening_client(tmp_path)
    assert client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen()).status_code == 401, (
        "deciding what is wrong with somebody's meter is not something an anonymous caller does")


def test_week5_day1_a_signed_in_call_names_a_published_class_and_where_it_goes(tmp_path):
    from config import constants
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import API_PREFIX

    client = a_screening_client(tmp_path)
    signed_in = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    answered = client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen(),
                           headers=signed_in)
    assert answered.status_code == 200, (
        f"a signed-in call should be answered, got {answered.status_code}")
    said = answered.json()
    assert said["exception_class"] in constants.EXCEPTION_CLASSES, (
        f"the service named {said['exception_class']}, which no queue exists for")
    assert 0.0 <= said["confidence"] <= 1.0, (
        f"a confidence outside nought to one means nothing, got {said['confidence']}")
    assert said["goes_to"].endswith(".csv"), (
        "the reply should say which queue the reading joins, or nobody knows who works it")


def test_week5_day1_the_champion_is_read_from_disk_once_and_not_per_request(tmp_path):
    from config import constants
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import API_PREFIX
    from metermind.api.routers import screening

    client = a_screening_client(tmp_path)
    signed_in = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen(), headers=signed_in)
    held = screening.loaded_champion.get("model")
    assert held is not None, "the first call should have loaded the champion and kept it"
    client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen(), headers=signed_in)
    assert screening.loaded_champion.get("model") is held, (
        "the second call re-read the artefact from disk, which is a file read on every request")


def test_week5_day1_a_service_with_no_champion_refuses_rather_than_guessing(tmp_path):
    from fastapi.testclient import TestClient

    from config import constants
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import API_PREFIX, build_application
    from metermind.api.routers import screening

    screening.champion_model_path = str(tmp_path / "nothing_here.joblib")
    screening.operating_rule_path = str(tmp_path / "nothing_here.json")
    screening.loaded_champion.clear()
    client = TestClient(build_application())
    signed_in = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    answered = client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen(),
                           headers=signed_in)
    assert answered.status_code == 503, (
        f"a service with no fitted champion is not available for this, and should say so "
        f"rather than answer anyway; it answered {answered.status_code}")


def test_week5_day1_a_typo_and_a_date_are_settled_at_the_door(tmp_path):
    from pydantic import ValidationError

    from metermind.api.schemas import ReadingSubmission

    good = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "COMMERICAL", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30, "previous_reading": 14208.0,
            "current_reading": 14675.0, "read_date": "14/06/2026"}
    settled = ReadingSubmission(**good)
    assert settled.consumer_category == "commercial", (
        f"a spelling the field application produced should be settled to the one the platform "
        f"uses before the model ever sees it, got {settled.consumer_category!r}")
    assert settled.read_date == "2026-06-14", (
        f"a date in any shape the field writes should come out in one shape, got "
        f"{settled.read_date!r}")
    try:
        ReadingSubmission(**dict(good, read_date="not taken"))
        raise AssertionError("a date in no shape at all should have been refused")
    except ValidationError:
        pass


# --------------------------------------------------------------------------- WEEK 5 DAY 2

def test_week5_day2_every_class_is_scored_separately_because_the_rare_ones_are_the_point(
        tmp_path):
    from config import constants
    from metermind.exception_models.exception_report import per_class_scores

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    scored = per_class_scores(held_out_classes, champion.predict(held_out))
    assert set(scored) == set(constants.EXCEPTION_CLASSES), (
        f"a class missing from the report is a class nobody is watching, got {sorted(scored)}")
    for name, one in scored.items():
        assert 0.0 <= one["precision"] <= 1.0 and 0.0 <= one["recall"] <= 1.0, (
            f"{name} reported an impossible precision or recall: {one}")


def test_week5_day2_the_supports_add_back_to_the_rows_that_were_scored(tmp_path):
    from metermind.exception_models.exception_report import per_class_scores

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    scored = per_class_scores(held_out_classes, champion.predict(held_out))
    assert sum(one["support"] for one in scored.values()) == len(held_out_classes), (
        "every row scored belongs to exactly one class, so the supports must add back to the "
        "number of rows")


def test_week5_day2_the_confusion_frame_is_five_by_five_and_totals_the_rows(tmp_path):
    from config import constants
    from metermind.exception_models.exception_report import confusion_frame

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    frame = confusion_frame(held_out_classes, champion.predict(held_out))
    assert frame.shape == (len(constants.EXCEPTION_CLASSES),
                           len(constants.EXCEPTION_CLASSES)), (
        f"the frame should be one row and one column for every class, got {frame.shape}")
    assert int(frame.to_numpy().sum()) == len(held_out_classes), (
        "every row scored lands in exactly one cell, so the frame should total the rows")


def test_week5_day2_the_written_report_carries_a_row_per_class_and_a_total(tmp_path):
    import pandas

    from config import constants
    from metermind.exception_models.exception_report import (
        EXCEPTION_REPORT_FIELDS,
        write_exception_report,
    )

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    written = write_exception_report(held_out_classes, champion.predict(held_out),
                                     tmp_path / "exception_report.csv")
    report = pandas.read_csv(written)
    assert list(report.columns) == list(EXCEPTION_REPORT_FIELDS), (
        f"the report should carry its published columns, got {list(report.columns)}")
    assert len(report) == len(constants.EXCEPTION_CLASSES) + 1, (
        f"a row for each of the five classes and one for the lot, got {len(report)}")
    assert set(constants.EXCEPTION_CLASSES) <= set(report["exception_class"]), (
        "an audit team reads this by class, so every class has to be named in it")


# --------------------------------------------------------------------------- WEEK 5 DAY 3

def test_week5_day3_every_row_of_a_softmax_adds_up_to_one():
    import numpy

    from metermind.message_intelligence.attention import softmax_rows

    for scores in (numpy.arange(12, dtype=float).reshape(3, 4),
                   numpy.zeros((2, 5)), numpy.array([[-3.0, 0.5, 2.25]])):
        weighted = softmax_rows(scores)
        assert weighted.shape == numpy.asarray(scores).shape, (
            "a softmax reweights the scores, it does not change how many there are")
        assert numpy.allclose(weighted.sum(axis=-1), 1.0), (
            f"each row should add to one, they add to {weighted.sum(axis=-1)}")
        assert (weighted > 0.0).all(), "a weight of nothing at all is not a weight"


def test_week5_day3_the_softmax_does_not_overflow_on_large_scores():
    import numpy

    from metermind.message_intelligence.attention import softmax_rows

    enormous = numpy.array([[1000.0, 1001.0, 999.0]])
    weighted = softmax_rows(enormous)
    assert numpy.isfinite(weighted).all(), (
        "exponentiating a large score without steadying it first overflows to not-a-number, "
        "and every weight downstream is lost")
    assert abs(weighted.sum() - 1.0) < 1e-9, "and it should still add to one"
    assert weighted.argmax() == 1, "the largest score should still carry the largest weight"


def test_week5_day3_the_weights_are_square_in_the_sequence_and_each_row_adds_to_one():
    import numpy

    from metermind.message_intelligence.attention import attention_weights

    sequence = numpy.arange(20, dtype=float).reshape(5, 4)
    weights = attention_weights(sequence, sequence)
    assert weights.shape == (5, 5), (
        f"five things attending to five things is a five by five weighting, got {weights.shape}")
    assert numpy.allclose(weights.sum(axis=-1), 1.0), (
        "each thing spreads all of its attention across the others, so each row adds to one")


def test_week5_day3_the_scores_are_scaled_by_the_size_of_a_key():
    import numpy

    from metermind.message_intelligence.attention import attention_weights, softmax_rows

    sequence = numpy.linspace(-1.0, 1.0, 4 * 16).reshape(4, 16)
    scaled = attention_weights(sequence, sequence)
    unscaled = softmax_rows(sequence @ sequence.T)
    assert not numpy.allclose(scaled, unscaled), (
        "without dividing by the square root of the key width the softmax saturates on long "
        "keys and attends to one thing only; the two must not come out the same")
    assert scaled.max() < unscaled.max(), (
        "scaling should spread the attention, so the largest weight should come down")


def test_week5_day3_what_comes_out_is_shaped_by_the_values_and_not_the_keys():
    import numpy

    from metermind.message_intelligence.attention import scaled_dot_product_attention

    queries = numpy.arange(12, dtype=float).reshape(3, 4)
    keys = numpy.arange(20, dtype=float).reshape(5, 4)
    values = numpy.arange(35, dtype=float).reshape(5, 7)
    answered = scaled_dot_product_attention(queries, keys, values)
    assert answered.shape == (3, 7), (
        f"three queries over values seven wide is three by seven, got {answered.shape}")


# --------------------------------------------------------------------------- WEEK 5 DAY 4

def test_week5_day4_the_quoted_reply_goes_and_the_new_message_stays():
    from metermind.message_intelligence.text_cleaning import strip_quoted_reply

    message = ("There is no supply at my premises since this morning.\n"
               "\n> On 06/03/2026 the section office wrote:\n"
               "> Your complaint has been registered.\n")
    cleaned = strip_quoted_reply(message)
    assert "no supply at my premises" in cleaned, "the consumer's own words must survive"
    assert "has been registered" not in cleaned, (
        "the reply quoted underneath is the department's words, and counting them as the "
        "consumer's teaches the classifier the department's vocabulary")


def test_week5_day4_a_greeting_and_a_sign_off_go_and_the_sentence_between_stays():
    from metermind.message_intelligence.text_cleaning import strip_greeting_and_sign_off

    message = "Dear Sir,\nThe display on my meter has gone blank.\nThanks and regards,\n"
    cleaned = strip_greeting_and_sign_off(message)
    assert "display on my meter has gone blank" in cleaned, "the complaint itself must survive"
    assert "Dear Sir" not in cleaned and "Thanks and regards" not in cleaned, (
        f"politeness is in every message and separates none of them, got {cleaned!r}")


def test_week5_day4_a_mobile_number_block_goes():
    from metermind.message_intelligence.text_cleaning import strip_signature

    message = "My meter is running fast.\nMobile: 9876543210\n"
    cleaned = strip_signature(message)
    assert "meter is running fast" in cleaned, "the complaint must survive"
    assert "9876543210" not in cleaned, (
        "a phone number is not evidence of anything a classifier should learn")


def test_week5_day4_runs_of_space_collapse_and_the_ends_are_trimmed():
    from metermind.message_intelligence.text_cleaning import normalise_whitespace

    assert normalise_whitespace("  there   is\n\n  no    supply  ") == "there is no supply", (
        "two messages that differ only in whitespace are the same message")


def test_week5_day4_the_whole_corpus_cleans_without_losing_or_emptying_a_message(tmp_path):
    import pandas

    from config import constants
    from metermind.message_intelligence.text_cleaning import clean_corpus

    pandas.read_csv(constants.COMPLAINT_MESSAGES_PATH).head(600).to_csv(
        tmp_path / "some.csv", index=False)
    counted = clean_corpus(tmp_path / "some.csv", tmp_path / "clean.csv")
    cleaned = pandas.read_csv(tmp_path / "clean.csv")
    assert counted["messages"] == len(cleaned) == 600, (
        f"six hundred messages went in and {len(cleaned)} came out")
    assert counted["shortest"] > 0, (
        "a message the cleaning empties is a message the classifier can never place, and the "
        "wrapping should never be the whole of it")
    assert "clean_text" in cleaned.columns, (
        "the cleaned text should be written beside the original, not over it")


# --------------------------------------------------------------------------- WEEK 5 DAY 5

def a_complaint_corpus(rows=1800):
    import pandas

    from config import constants
    return pandas.read_csv(constants.COMPLAINT_MESSAGES_PATH, nrows=rows)


def test_week5_day5_the_split_keeps_each_category_in_the_same_proportion():
    from metermind.message_intelligence.complaint_classifier import split_complaints

    corpus = a_complaint_corpus(1800)
    _, _, fitting_labels, held_out_labels = split_complaints(corpus, "category")
    whole = corpus["category"].value_counts(normalize=True)
    for labels, where in ((fitting_labels, "the fitting rows"),
                          (held_out_labels, "the held out rows")):
        share = labels.value_counts(normalize=True)
        for name in whole.index:
            assert abs(share[name] - whole[name]) < 0.02, (
                f"{name} is {whole[name]:.3f} of the corpus but {share[name]:.3f} of {where}")


def test_week5_day5_the_cleaning_is_inside_the_pipeline():
    from metermind.message_intelligence.complaint_classifier import (
        split_complaints,
        train_category_classifier,
    )
    from metermind.message_intelligence.text_cleaning import clean_message

    corpus = a_complaint_corpus(700)
    fitting_text, held_out_text, fitting_labels, _ = split_complaints(corpus, "category")
    model = train_category_classifier(fitting_text, fitting_labels)
    raw = held_out_text.iloc[0]
    assert model.predict([raw])[0] == model.predict([clean_message(raw)])[0], (
        "a caller should not have to know the message needs cleaning first; if the model "
        "answers differently for the raw and the cleaned form, the cleaning is outside it")


def test_week5_day5_the_category_classifier_beats_always_naming_the_commonest():
    from metermind.message_intelligence.complaint_classifier import (
        split_complaints,
        train_category_classifier,
    )

    corpus = a_complaint_corpus(1800)
    fitting_text, held_out_text, fitting_labels, held_out_labels = split_complaints(
        corpus, "category")
    model = train_category_classifier(fitting_text, fitting_labels)
    always_the_commonest = held_out_labels.value_counts(normalize=True).max()
    assert model.score(held_out_text, held_out_labels) > always_the_commonest + 0.20, (
        f"routing a complaint to the commonest queue needs no model at all; it scored "
        f"{model.score(held_out_text, held_out_labels):.3f} against {always_the_commonest:.3f}")


def test_week5_day5_the_urgency_classifier_beats_always_naming_the_commonest():
    from metermind.message_intelligence.complaint_classifier import (
        split_complaints,
        train_urgency_classifier,
    )

    corpus = a_complaint_corpus(1800)
    fitting_text, held_out_text, fitting_labels, held_out_labels = split_complaints(
        corpus, "urgency")
    model = train_urgency_classifier(fitting_text, fitting_labels)
    always_the_commonest = held_out_labels.value_counts(normalize=True).max()
    assert model.score(held_out_text, held_out_labels) > always_the_commonest + 0.15, (
        f"how fast a complaint must be answered has to be readable from what it says; it "
        f"scored {model.score(held_out_text, held_out_labels):.3f} against "
        f"{always_the_commonest:.3f}")


def test_week5_day5_a_message_is_given_one_category_and_one_urgency_from_the_published_sets():
    from config import constants
    from metermind.message_intelligence.complaint_classifier import (
        classify_message,
        split_complaints,
        train_category_classifier,
        train_urgency_classifier,
    )

    corpus = a_complaint_corpus(700)
    category_model = train_category_classifier(*split_complaints(corpus, "category")[0::2])
    urgency_model = train_urgency_classifier(*split_complaints(corpus, "urgency")[0::2])
    said = classify_message(category_model, urgency_model,
                            "There has been no power supply in our area since last evening.")
    assert set(said) == {"category", "urgency"}, (
        f"a message gets one of each and nothing else, got {sorted(said)}")
    assert said["category"] in constants.COMPLAINT_CATEGORIES, (
        f"{said['category']} is not a category any team works")
    assert said["urgency"] in constants.COMPLAINT_URGENCIES, (
        f"{said['urgency']} is not an urgency the service publishes")


# --------------------------------------------------------------------------- WEEK 6 DAY 1

def a_thread_of_sentences():
    return ("The meter was replaced on the fifteenth of last month by the area lineman. "
            "The bill that came afterwards is for eleven thousand rupees, which is four times "
            "what we normally pay. Nobody has come to check the new meter since it went in. "
            "We have already paid the previous bill in full and have the receipt. "
            "Please send somebody to read the meter again before the due date. Ok.")


def test_week6_day1_the_split_keeps_sentences_and_drops_fragments():
    from config import constants
    from metermind.message_intelligence.thread_summary import (
        SHORTEST_SENTENCE_CHARACTERS,
        split_sentences,
    )

    sentences = split_sentences(a_thread_of_sentences())
    assert len(sentences) == 5, (
        f"six sentence endings with one fragment among them should leave five usable "
        f"sentences, got {len(sentences)}: {sentences}")
    assert all(len(one) >= SHORTEST_SENTENCE_CHARACTERS for one in sentences), (
        f"every sentence kept must reach {SHORTEST_SENTENCE_CHARACTERS} characters, and "
        f"{[one for one in sentences if len(one) < SHORTEST_SENTENCE_CHARACTERS]} does not")
    assert constants.SUMMARY_SENTENCE_COUNT < len(sentences), (
        "the thread must hold more sentences than a summary keeps, or nothing is being chosen")


def test_week6_day1_the_matrix_has_one_row_for_every_sentence():
    from metermind.message_intelligence.thread_summary import sentence_matrix, split_sentences

    sentences = split_sentences(a_thread_of_sentences())
    counted = sentence_matrix(sentences)
    assert counted.shape[0] == len(sentences), (
        f"{len(sentences)} sentences should become {len(sentences)} rows, got "
        f"{counted.shape[0]}")
    assert counted.shape[1] > 0, "a sentence turned into no numbers at all cannot be compared"
    assert counted.ndim == 2, f"the matrix should have two dimensions, not {counted.ndim}"


def test_week6_day1_every_sentence_is_given_one_finite_score():
    import numpy

    from metermind.message_intelligence.thread_summary import score_sentences, split_sentences

    sentences = split_sentences(a_thread_of_sentences())
    scores = score_sentences(sentences)
    assert scores.shape == (len(sentences),), (
        f"one score for each of the {len(sentences)} sentences, got shape {scores.shape}")
    assert bool(numpy.isfinite(scores).all()), (
        f"a sentence scored to infinity or to nothing cannot be ranked: {scores}")


def test_week6_day1_nothing_in_the_summary_was_invented(tmp_path):
    import csv

    from config import constants
    from metermind.message_intelligence.thread_summary import (
        split_sentences,
        summarise_thread,
        write_thread_summaries,
    )

    thread = a_thread_of_sentences()
    summary = summarise_thread(thread)
    kept = split_sentences(summary)
    assert len(kept) == constants.SUMMARY_SENTENCE_COUNT, (
        f"a summary keeps {constants.SUMMARY_SENTENCE_COUNT} sentences, this one kept "
        f"{len(kept)}")
    for one in kept:
        assert one in thread, (
            f"an extractive summary may only return sentences the thread already holds, and "
            f"{one!r} is not one of them")
    out_of_order = ("There is no supply in our street since yesterday evening and nobody has "
                    "come. The transformer near the school has been humming and smoking since "
                    "the morning. Our whole street has been without supply since the evening "
                    "and nobody has come. Kindly acknowledge this message at your earliest "
                    "convenience please.")
    said_in = split_sentences(out_of_order)
    came_back = [said_in.index(one)
                 for one in split_sentences(summarise_thread(out_of_order))]
    assert came_back == sorted(came_back), (
        f"the sentences chosen are the highest scoring, but they come back in the order the "
        f"thread said them; a summary that reorders a conversation misreports it, and this one "
        f"came back as {came_back}")
    threads_path = tmp_path / "message_threads.csv"
    with threads_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("thread_id", "turn_number", "message_text"))
        for turn, sentence in enumerate(split_sentences(thread), start=1):
            writer.writerow(("THR000001", turn, sentence))
    summaries_path = tmp_path / "thread_summaries.csv"
    counted = write_thread_summaries(str(threads_path), str(summaries_path))
    rows = list(csv.DictReader(summaries_path.open(encoding="utf-8")))
    assert len(rows) == 1 == counted["threads"], (
        f"one thread went in, so one summary row comes out, got {len(rows)} and {counted}")
    for one in split_sentences(rows[0]["summary"]):
        assert one in thread, (
            f"the written summary is held to the same rule as the returned one, and {one!r} "
            f"is not in the thread")


def test_week6_day1_a_thread_with_nothing_to_summarise_is_refused():
    from metermind.message_intelligence.thread_summary import UnreadableThread, summarise_thread

    for nothing_usable in ("", "Ok. Yes. No.", "   "):
        try:
            summarise_thread(nothing_usable)
            raise AssertionError(
                f"{nothing_usable!r} holds no sentence worth summarising and should have been "
                f"refused rather than answered")
        except UnreadableThread:
            pass


# --------------------------------------------------------------------------- WEEK 6 DAY 2

def a_seeded_cache(tmp_path, prompt, answer, name="llm_cache.json"):
    """A cache file holding one answer, keyed exactly as ask_model keys it."""
    import json
    import os

    from config import constants
    from metermind.message_intelligence.llm_client import cache_key

    model_name = os.environ.get("GEMINI_MODEL", "").strip() or constants.DEFAULT_LANGUAGE_MODEL
    path = tmp_path / name
    path.write_text(json.dumps({cache_key(model_name, prompt): answer}), encoding="utf-8")
    return str(path)


def without_a_key(work):
    """Run work with GEMINI_API_KEY emptied, so no testcase can reach a live model by accident."""
    import os

    was = os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = ""
        return work()
    finally:
        if was is None:
            del os.environ["GEMINI_API_KEY"]
        else:
            os.environ["GEMINI_API_KEY"] = was


def test_week6_day2_the_settings_come_from_the_environment_and_a_missing_key_is_refused():
    import os

    from config import constants
    from metermind.message_intelligence.llm_client import LanguageModelError, load_settings

    was = os.environ.get("GEMINI_API_KEY"), os.environ.get("GEMINI_MODEL")
    try:
        os.environ["GEMINI_API_KEY"] = "a-key-that-is-not-real"
        os.environ["GEMINI_MODEL"] = "gemini-from-the-environment"
        settings = load_settings()
        assert settings["api_key"] == "a-key-that-is-not-real", (
            "the key must be read from the environment and never written in the source")
        assert settings["model_name"] == "gemini-from-the-environment", (
            f"the model named in the environment should win, got {settings['model_name']}")
        os.environ["GEMINI_MODEL"] = ""
        assert load_settings()["model_name"] == constants.DEFAULT_LANGUAGE_MODEL, (
            "with no model named, the published default is the one used")
        os.environ["GEMINI_API_KEY"] = ""
        try:
            load_settings()
            raise AssertionError("a missing key should be refused, not worked around")
        except LanguageModelError:
            pass
    finally:
        for name, value in zip(("GEMINI_API_KEY", "GEMINI_MODEL"), was):
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def test_week6_day2_the_key_is_the_same_for_one_prompt_and_different_for_another():
    from metermind.message_intelligence.llm_client import cache_key

    first = cache_key("gemini-2.0-flash", "What is the fixed charge for LT-1?")
    again = cache_key("gemini-2.0-flash", "What is the fixed charge for LT-1?")
    other = cache_key("gemini-2.0-flash", "What is the fixed charge for LT-2?")
    changed = cache_key("gemini-1.5-flash", "What is the fixed charge for LT-1?")
    assert first == again, "the same model and the same prompt must give the same key"
    assert first != other, "two different prompts must not share one cached answer"
    assert first != changed, (
        "two models answer differently, so the model has to be part of the key")
    assert len(first) == 64, f"a sha256 key is 64 characters, this one is {len(first)}"


def test_week6_day2_a_call_that_fails_is_raised_and_never_answered_with_a_default(tmp_path):
    from metermind.message_intelligence.llm_client import LanguageModelError, ask_model

    cache_path = str(tmp_path / "empty_cache.json")

    def ask_with_no_key():
        try:
            ask_model("A prompt nothing has answered yet.", cache_path)
        except LanguageModelError as refused:
            return str(refused)
        raise AssertionError(
            "with no key and nothing cached there is no answer to give, and a made up one "
            "would be worse than none")

    said = without_a_key(ask_with_no_key)
    assert "GEMINI_API_KEY" in said, (
        f"the failure should say what is missing, and this one says {said!r}")


def test_week6_day2_what_was_written_to_the_cache_is_what_is_read_back(tmp_path):
    from metermind.message_intelligence.llm_client import (
        LanguageModelError,
        cache_key,
        read_answer,
        read_cache,
        write_cache,
    )

    cache_path = str(tmp_path / "written_cache.json")
    assert read_cache(cache_path) == {}, "a cache that does not exist yet holds nothing"
    key = cache_key("gemini-2.0-flash", "Read the tone of this complaint.")
    said = '```json\n{"tone": "angry", "reason": "third reminder"}\n```'
    write_cache({key: said}, cache_path)
    assert read_cache(cache_path)[key] == said, (
        "the answer read back has to be the answer written, character for character")
    assert read_answer(said, ("tone", "reason")) == {"tone": "angry",
                                                     "reason": "third reminder"}, (
        "a fenced JSON answer should be read back as the object it holds")
    try:
        read_answer(said, ("tone", "reason", "confidence"))
        raise AssertionError(
            "an answer missing a wanted key has to raise naming what is missing; a caller "
            "handed half an answer then has to guess about the other half")
    except LanguageModelError as refused:
        assert "confidence" in str(refused), (
            f"the refusal has to name the key that was missing, and this one said {refused}")
    half_written = tmp_path / "half_written.json"
    half_written.write_text('{"a3f0": "the answer that was being writ', encoding="utf-8")
    try:
        read_cache(str(half_written))
        raise AssertionError(
            "a cache that cannot be read raises rather than being treated as empty; quietly "
            "discarding it means every question is paid for again and nobody finds out")
    except LanguageModelError:
        pass


# --------------------------------------------------------------------------- WEEK 6 DAY 3

def test_week6_day3_all_three_kinds_of_reference_are_found_in_one_message():
    from metermind.message_intelligence.reference_extraction import (
        find_account_numbers,
        find_complaint_references,
        find_meter_serials,
    )

    message = ("Against account ACC10004512 and also ACC10004512, the meter MTR-NS-004411 was "
               "changed. My earlier complaint CMP2400318 is still open, and meter "
               "MTR-SO-119002 is the old one.")
    assert find_account_numbers(message) == ["ACC10004512"], (
        "an account quoted twice is one account, not two")
    assert find_meter_serials(message) == ["MTR-NS-004411", "MTR-SO-119002"], (
        f"both serials should be found, got {find_meter_serials(message)}")
    assert find_complaint_references(message) == ["CMP2400318"], (
        f"the complaint reference should be found, got {find_complaint_references(message)}")


def test_week6_day3_an_account_the_register_has_never_heard_of_is_marked():
    from metermind.message_intelligence.reference_extraction import (
        check_against_connection_register,
    )

    checked = check_against_connection_register(
        ["ACC10000001", "ACC99999999"], [], {"ACC10000001", "ACC10000002"}, {})
    assert checked["unknown_accounts"] == ["ACC99999999"], (
        f"the account that is not in the register is the one to mark, got "
        f"{checked['unknown_accounts']}")
    assert checked["serials_on_another_account"] == [], (
        "no serial was quoted, so none can sit against another account")


def test_week6_day3_a_serial_standing_against_another_account_is_the_worse_fault():
    from metermind.message_intelligence.reference_extraction import (
        check_against_connection_register,
    )

    known = {"ACC10000001", "ACC10000002"}
    owner = {"MTR-NS-000111": "ACC10000002", "MTR-NS-000222": "ACC10000001"}
    checked = check_against_connection_register(
        ["ACC10000001"], ["MTR-NS-000111", "MTR-NS-000222"], known, owner)
    assert checked["unknown_accounts"] == [], "the account quoted is in the register"
    assert checked["serials_on_another_account"] == ["MTR-NS-000111"], (
        f"the serial the register puts against a different account is the one that matters, "
        f"got {checked['serials_on_another_account']}")


def test_week6_day3_a_message_quoting_nothing_returns_empty_lists():
    from metermind.message_intelligence.reference_extraction import (
        check_against_connection_register,
        find_account_numbers,
        find_complaint_references,
        find_meter_serials,
    )

    message = "There has been no supply in our street since yesterday evening. Please help."
    for found in (find_account_numbers(message), find_meter_serials(message),
                  find_complaint_references(message)):
        assert found == [], f"nothing was quoted, so nothing should be found, got {found}"
    checked = check_against_connection_register([], [], {"ACC10000001"}, {})
    assert checked == {"unknown_accounts": [], "serials_on_another_account": []}, (
        f"a message quoting nothing has no fault to report, got {checked}")


def test_week6_day3_one_row_is_written_for_every_message_with_the_columns_named(tmp_path):
    import csv

    from config import constants
    from metermind.message_intelligence.reference_extraction import (
        EXTRACTED_REFERENCE_FIELDS,
        extract_and_check,
    )

    messages_path = tmp_path / "messages.csv"
    register_path = tmp_path / "register.csv"
    with messages_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("message_id", "message_text"))
        writer.writerow(("MSG000001", "Account ACC10000001 meter MTR-NS-000111 is running fast"))
        writer.writerow(("MSG000002", "No supply since yesterday in our lane"))
        writer.writerow(("MSG000003", "Account ACC70000000 has been billed twice"))
    with register_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("account_number", "meter_serial"))
        writer.writerow(("ACC10000001", "MTR-NS-000111"))
        writer.writerow(("ACC10000002", "MTR-NS-000222"))
    extracted_path = tmp_path / "extracted.csv"
    counted = extract_and_check(str(messages_path), str(register_path), str(extracted_path))
    assert counted["messages"] == 3, f"three messages went in, {counted['messages']} counted"
    rows = list(csv.DictReader(extracted_path.open(encoding="utf-8")))
    assert len(rows) == 3, f"one row for every message, got {len(rows)}"
    assert tuple(rows[0]) == EXTRACTED_REFERENCE_FIELDS, (
        f"the columns should be {EXTRACTED_REFERENCE_FIELDS}, got {tuple(rows[0])}")
    assert rows[2]["unknown_accounts"] == "ACC70000000", (
        f"the account that is not in the register should be marked on its own row, got "
        f"{rows[2]['unknown_accounts']!r}")
    assert constants.EXTRACTED_REFERENCES_PATH.endswith(".csv"), (
        "the published path for this file is a csv")


# --------------------------------------------------------------------------- WEEK 6 DAY 4

class AlwaysSaysPriority:
    """Stands in for the Week 5 Day 5 urgency classifier, so the day's wiring is what is tried."""

    def __init__(self, urgency="priority"):
        self.urgency = urgency

    def predict(self, messages):
        return [self.urgency for one in messages]


def test_week6_day4_one_result_comes_back_for_every_message_even_when_one_fails(tmp_path):
    from metermind.message_intelligence.batch_pipeline import run_batch

    messages = [{"message_id": "MSG000001", "units": 120}, {"message_id": "MSG000002"},
                {"message_id": "MSG000003", "units": 40}]

    def double_the_units(one):
        return one["units"] * 2

    handled = run_batch(messages, double_the_units, str(tmp_path / "failures.csv"))
    assert len(handled) == len(messages), (
        f"{len(messages)} messages went in, so {len(messages)} results come out, got "
        f"{len(handled)}; a batch that stops at the first bad message loses the rest")
    assert [handled[0], handled[2]] == [240, 80], (
        f"the messages that could be handled should carry their own answers, got {handled}")


def test_week6_day4_a_message_that_failed_carries_its_own_reason(tmp_path):
    import csv

    from metermind.message_intelligence.batch_pipeline import MessageFailure, run_batch

    failures_path = tmp_path / "failures.csv"

    def refuse_the_second(one):
        if one["message_id"] == "MSG000002":
            raise ValueError("the reading is missing")
        return one["message_id"]

    handled = run_batch([{"message_id": "MSG000001"}, {"message_id": "MSG000002"}],
                        refuse_the_second, str(failures_path))
    assert isinstance(handled[1], MessageFailure), (
        f"a message that could not be handled comes back as a MessageFailure, got "
        f"{type(handled[1]).__name__}")
    assert handled[1].message_id == "MSG000002", (
        f"the failure has to say which message it was, got {handled[1].message_id!r}")
    assert "the reading is missing" in handled[1].reason, (
        f"and why it failed, got {handled[1].reason!r}")
    written = list(csv.DictReader(failures_path.open(encoding="utf-8")))
    assert [one["message_id"] for one in written] == ["MSG000002"], (
        f"only the failures are written down, got {written}")


def test_week6_day4_the_prompt_the_model_sees_carries_the_message(tmp_path):
    from metermind.message_intelligence.escalation import TONE_PROMPT, read_tone

    message_text = "This is the third time I am writing and nobody has come."
    assert "{message_text}" in TONE_PROMPT, (
        "the prompt has to have a place for the message, or every message asks the same thing")
    rendered = TONE_PROMPT.format(message_text=message_text)
    assert message_text in rendered, "the rendered prompt has to hold the message it is about"
    cache_path = a_seeded_cache(tmp_path, rendered,
                                '{"tone": "angry", "reason": "third time I am writing"}')
    read = without_a_key(lambda: read_tone(message_text, cache_path))
    assert read["tone"] == "angry", (
        f"the seeded answer is keyed on the rendered prompt, so reading it back proves the "
        f"message reached the model; got {read}")
    assert read["reason"], "the tone read has to come with the words that showed it"


def test_week6_day4_the_decision_moves_when_any_one_of_the_three_signals_moves(tmp_path):
    import datetime

    from config import constants
    from metermind.message_intelligence.escalation import (
        TONE_PROMPT,
        complaint_age_days,
        decide_escalation,
        escalate_one_message,
    )

    said = "This is the third time I am writing about this and nobody has come."
    message = {"message_id": "MSG000001", "received_date": "2026-01-01", "message_text": said}
    prompt = TONE_PROMPT.format(message_text=said)
    calm = a_seeded_cache(tmp_path, prompt, '{"tone": "calm", "reason": "asked politely"}',
                          "calm_cache.json")
    angry = a_seeded_cache(tmp_path, prompt, '{"tone": "angry", "reason": "third time"}',
                           "angry_cache.json")
    long_after = datetime.date(2026, 1, 1) + datetime.timedelta(
        days=constants.COMPLAINT_AGE_ESCALATION_DAYS + 9)
    same_week = datetime.date(2026, 1, 4)

    def decided(today, urgency, cache_path):
        return without_a_key(lambda: escalate_one_message(
            message, AlwaysSaysPriority(urgency), today, cache_path))

    waiting_only = decided(long_after, "routine", calm)
    assert waiting_only["escalate"] is False, (
        f"one signal is not enough when {constants.ESCALATION_SIGNALS_NEEDED} are needed, got "
        f"{waiting_only}")
    assert decided(long_after, "emergency", calm)["escalate"] is True, (
        "the urgency the classifier gave is a signal in its own right, and with the wait it "
        "makes two")
    assert decided(long_after, "routine", angry)["escalate"] is True, (
        "the tone the model read is a signal in its own right, and with the wait it makes two")
    assert decided(same_week, "emergency", calm)["escalate"] is False, (
        "the same urgency on a complaint received this week is one signal, not two; if the age "
        "changes nothing then only two of the three readings are being consulted")
    assert (waiting_only["age_days"], waiting_only["urgency"], waiting_only["tone"]) == (
        constants.COMPLAINT_AGE_ESCALATION_DAYS + 9, "routine", "calm"), (
        f"all three readings should come back beside the decision, got {waiting_only}")
    assert complaint_age_days("2026-01-01", datetime.date(2026, 1, 22)) == 21, (
        "the age of a complaint is counted in whole days from the day it was received")
    assert decide_escalation(0, "emergency", "angry")["signals"] == ["urgency", "tone"], (
        "the decision names the signals it found and no others")


def test_week6_day4_the_three_signals_are_written_beside_the_decision(tmp_path):
    import csv
    import datetime

    from metermind.message_intelligence.escalation import (
        ESCALATION_FIELDS,
        TONE_PROMPT,
        write_escalations,
    )
    from metermind.message_intelligence.llm_client import LanguageModelError

    messages = [{"message_id": "MSG000001", "received_date": "2026-01-01",
                 "message_text": "This is the third time I am writing and nobody has come."},
                {"message_id": "MSG000002", "received_date": "2026-01-01",
                 "message_text": "Nothing has been cached for this one."}]
    cache_path = a_seeded_cache(
        tmp_path, TONE_PROMPT.format(message_text=messages[0]["message_text"]),
        '{"tone": "angry", "reason": "third time"}')
    escalations_path = tmp_path / "escalations.csv"
    counted = without_a_key(lambda: write_escalations(
        messages, AlwaysSaysPriority(), str(escalations_path),
        today=datetime.date(2026, 2, 1), cache_path=cache_path))
    assert (counted["decided"], counted["failed"]) == (1, 1), (
        f"one message had an answer and one did not, got {counted}")
    rows = list(csv.DictReader(escalations_path.open(encoding="utf-8")))
    assert tuple(rows[0]) == ESCALATION_FIELDS, (
        f"the columns should be {ESCALATION_FIELDS}, got {tuple(rows[0])}")
    assert (rows[0]["age_days"], rows[0]["urgency"], rows[0]["tone"]) == ("31", "priority",
                                                                         "angry"), (
        f"all three signals belong on the row beside the decision, got {rows[0]}")
    assert rows[0]["escalate"] == "True" and "tone" in rows[0]["signals"], (
        f"two signals were present, so the row should escalate and name them, got {rows[0]}")
    assert LanguageModelError.__module__.endswith("llm_client"), (
        "the failure a batch records is the one the model client raises")


# --------------------------------------------------------------------------- WEEK 6 DAY 5

def test_week6_day5_every_order_in_the_folder_gives_up_its_text():
    import pathlib

    from config import constants
    from metermind.retrieval.document_loader import UnreadableOrder, read_pdf_text

    orders = sorted(pathlib.Path(constants.TARIFF_ORDERS_DIRECTORY).glob("*.pdf"))
    assert len(orders) == 12, f"twelve orders were published, the folder holds {len(orders)}"
    for one in orders:
        text = read_pdf_text(str(one))
        assert len(text) > 1000, (
            f"{one.name} came back with {len(text)} characters, which is not an order")
        assert "TARIFF ORDER" in text, f"{one.name} does not read like a tariff order"
    try:
        read_pdf_text("data/tariff_orders/an_order_that_was_never_issued.pdf")
        raise AssertionError("an order that is not there should be refused, not returned empty")
    except UnreadableOrder:
        pass


def test_week6_day5_the_manifest_decides_what_is_loaded_and_nothing_else_is():
    from metermind.retrieval.document_loader import load_tariff_orders, read_manifest

    manifest = read_manifest()
    orders = load_tariff_orders()
    assert len(orders) == len(manifest), (
        f"the manifest names {len(manifest)} orders and {len(orders)} were loaded; a file in "
        f"the folder that the manifest does not name has no dates and cannot be filtered")
    assert [one["order_id"] for one in orders] == [one["order_id"] for one in manifest], (
        "the orders should come back in the order the manifest names them")
    for one in orders:
        assert one["effective_from"] < one["effective_to"], (
            f"{one['order_id']} is in force from {one['effective_from']} to "
            f"{one['effective_to']}, which is backwards")


def test_week6_day5_the_pieces_keep_to_the_size_and_carry_the_overlap():
    from metermind.retrieval.chunking import split_into_chunks

    text = "".join(f"sentence number {number} of the order. " for number in range(200))
    pieces = split_into_chunks(text, size=300, overlap=60)
    assert all(len(one) <= 300 for one in pieces), (
        f"no piece may be longer than the size asked for, longest is "
        f"{max(len(one) for one in pieces)}")
    assert len(pieces) > 1, "text far longer than the size should have been cut up"
    assert text[300 - 60:300] in (pieces[0][-60:] + pieces[1][:60]), (
        "the last characters of one piece have to reappear at the start of the next, or a "
        "sentence cut in half is lost to both")
    try:
        split_into_chunks(text, size=100, overlap=100)
        raise AssertionError("an overlap as wide as the chunk never moves forward")
    except ValueError:
        pass


def test_week6_day5_a_piece_remembers_which_order_it_came_out_of():
    from config import constants
    from metermind.retrieval.chunking import chunk_metadata

    order = {"order_id": "FY2024-25-LT1", "title": "Retail Supply Tariff Order FY2024-25",
             "consumer_category": "domestic", "effective_from": "2024-04-01",
             "effective_to": "2025-03-31", "sections": ["ENERGY CHARGE", "FIXED CHARGE"]}
    entry = chunk_metadata(order, "3. ENERGY CHARGE The energy charge shall be levied", 7)
    for field in constants.STORED_CHUNK_FIELDS:
        assert field in entry, (
            f"{field} is published as a field every stored piece carries, and this one has "
            f"{sorted(entry)}")
    assert (entry["order_id"], entry["consumer_category"]) == ("FY2024-25-LT1", "domestic"), (
        f"the piece has to say which order and which category it belongs to, got {entry}")
    assert (entry["effective_from"], entry["effective_to"]) == ("2024-04-01", "2025-03-31"), (
        "both dates travel with the piece; a piece that has forgotten when it applied is "
        "worse than no piece at all")
    assert entry["section"] == "ENERGY CHARGE", (
        f"the piece names the section it opens in, got {entry['section']!r}")


def test_week6_day5_the_file_is_written_and_no_two_pieces_share_an_identifier(tmp_path):
    import json

    from metermind.retrieval.chunking import write_chunks
    from metermind.retrieval.document_loader import load_tariff_orders

    chunks_path = tmp_path / "tariff_chunks.json"
    orders = load_tariff_orders()
    counted = write_chunks(orders, str(chunks_path))
    assert counted["orders"] == len(orders), (
        f"every order should have been cut up, got {counted}")
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    assert len(chunks) == counted["chunks"] > len(orders), (
        f"an order longer than one chunk becomes several, got {counted}")
    assert len({one["chunk_id"] for one in chunks}) == len(chunks), (
        "two pieces sharing an identifier cannot both be cited")
    assert counted["without_a_section"] == 0, (
        f"{counted['without_a_section']} pieces do not know which section they are in")
    assert {one["order_id"] for one in chunks} == {one["order_id"] for one in orders}, (
        "every order should be represented among the pieces, and no other")


# --------------------------------------------------------------------------- WEEK 7 DAY 1

@functools.lru_cache(maxsize=1)
def the_embedder():
    """Loaded once for the whole suite; every Week 7 testcase borrows the same reader."""
    from metermind.retrieval.vector_store import load_embedder

    return load_embedder()


def a_small_tariff_store(tmp_path, orders=2):
    """Real orders, cut and stored, so a search has something true to find."""
    from metermind.retrieval.chunking import write_chunks
    from metermind.retrieval.document_loader import load_tariff_orders
    from metermind.retrieval.vector_store import build_tariff_store

    chunks_path = tmp_path / "chunks.json"
    write_chunks(load_tariff_orders()[:orders], str(chunks_path))
    store_directory = str(tmp_path / "tariff_store")
    return build_tariff_store(str(chunks_path), store_directory, the_embedder()), store_directory


@functools.lru_cache(maxsize=4)
def a_shared_tariff_store(orders=2):
    """The same store, built once and read by several testcases; none of them writes to it."""
    import tempfile

    folder = pathlib.Path(tempfile.mkdtemp())
    collection, store_directory = a_small_tariff_store(folder, orders)
    return collection, store_directory, str(folder / "chunks.json")


def test_week7_day1_the_distance_measure_is_stated_and_not_left_to_the_default():
    from config import constants
    from metermind.retrieval.vector_store import STORE_SETTINGS

    assert "hnsw:space" in STORE_SETTINGS, (
        f"the collection has to declare the space it measures distance in, got {STORE_SETTINGS}")
    assert STORE_SETTINGS["hnsw:space"] == constants.VECTOR_DISTANCE_MEASURE, (
        f"the published measure is {constants.VECTOR_DISTANCE_MEASURE} and the store is built "
        f"with {STORE_SETTINGS['hnsw:space']}; a store built on one measure and searched as "
        f"though it were another returns plausible nonsense")


def test_week7_day1_one_record_is_stored_for_every_chunk():
    import json

    collection, _, chunks_path = a_shared_tariff_store()
    chunks = json.loads(pathlib.Path(chunks_path).read_text(encoding="utf-8"))
    assert collection.count() == len(chunks), (
        f"{len(chunks)} chunks went in and {collection.count()} records came out")
    stored = collection.get()
    assert set(stored["ids"]) == {one["chunk_id"] for one in chunks}, (
        "every chunk should be stored under its own identifier and no other")
    assert stored["metadatas"][0]["order_id"], (
        "a stored record with no order id cannot be filtered or cited later")
    from metermind.retrieval.vector_store import TariffStoreMissing, open_tariff_store

    opened = open_tariff_store(a_shared_tariff_store()[1])
    assert opened.count() == len(chunks), (
        f"opening a store must not rebuild it; re-embedding every piece on every open would "
        f"make the assistant of Week 8 unusable, and this came back with {opened.count()}")
    try:
        open_tariff_store(str(pathlib.Path(chunks_path).parent / "no-store-was-built-here"))
        raise AssertionError("a store that is not there has to be named, not invented")
    except TariffStoreMissing:
        pass


def test_week7_day1_what_comes_back_is_ordered_closest_first():
    from metermind.retrieval.vector_store import SEARCH_RESULT_FIELDS, search_tariff

    collection = a_shared_tariff_store()[0]
    found = search_tariff(collection, "what is the fixed charge for each kilowatt of "
                                      "sanctioned load", the_embedder(), result_count=5)
    assert len(found) == 5, f"five results were asked for, {len(found)} came back"
    distances = [one["distance"] for one in found]
    assert distances == sorted(distances), (
        f"the nearest chunk has to be the first one read, and these are ordered {distances}")
    assert set(found[0]) == set(SEARCH_RESULT_FIELDS), (
        f"a result should carry {SEARCH_RESULT_FIELDS}, got {sorted(found[0])}")


def test_week7_day1_a_chunk_is_found_by_its_own_words():
    from metermind.retrieval.vector_store import search_tariff

    collection = a_shared_tariff_store()[0]
    stored = collection.get()
    position = len(stored["ids"]) // 2
    asked = " ".join(stored["documents"][position].split()[8:40])
    found = search_tariff(collection, asked, the_embedder(), result_count=3)
    assert stored["ids"][position] in [one["chunk_id"] for one in found], (
        f"a query taken straight out of a chunk should retrieve that chunk; asked with "
        f"{asked[:60]!r} and got {[one['chunk_id'] for one in found]} instead of "
        f"{stored['ids'][position]}")


# --------------------------------------------------------------------------- WEEK 7 DAY 2

def three_extracts():
    return [{"chunk_id": "FY2026-27-LT1-002", "text": "The energy charge for the first block "
                                                      "shall be Rs. 3.50 for each unit.",
             "order_id": "FY2026-27-LT1", "section": "ENERGY CHARGE",
             "effective_from": "2026-04-01", "effective_to": "2027-03-31"},
            {"chunk_id": "FY2026-27-LT1-003", "text": "A fixed charge of Rs. 50.00 for each "
                                                      "kilowatt of sanctioned load is levied.",
             "order_id": "FY2026-27-LT1", "section": "FIXED CHARGE",
             "effective_from": "2026-04-01", "effective_to": "2027-03-31"},
            {"chunk_id": "FY2024-25-LT1-002", "text": "The energy charge for the first block "
                                                      "shall be Rs. 3.20 for each unit.",
             "order_id": "FY2024-25-LT1", "section": "ENERGY CHARGE",
             "effective_from": "2024-04-01", "effective_to": "2025-03-31"}]


def test_week7_day2_the_prompt_carries_every_extract_it_was_handed_and_no_other():
    from config import constants
    from metermind.retrieval.grounded_answer import CITATION_PATTERN, build_answer_prompt

    chunks = three_extracts()
    prompt = build_answer_prompt("What is the rate for the first block?", chunks)
    for one in chunks:
        assert one["chunk_id"] in prompt, (
            f"{one['chunk_id']} was handed over and its identifier is not in the prompt")
        assert one["text"] in prompt, (
            f"the words of {one['chunk_id']} were handed over and are not in the prompt")
    assert set(CITATION_PATTERN.findall(prompt)) == {one["chunk_id"] for one in chunks}, (
        f"the prompt must offer exactly the extracts retrieved and no other identifier, got "
        f"{sorted(set(CITATION_PATTERN.findall(prompt)))}")
    assert "What is the rate for the first block?" in prompt, "the question itself is missing"
    assert constants.UNANSWERABLE_REPLY in prompt, (
        "the model has to be told what to answer when the extracts do not answer the question")


def test_week7_day2_an_answer_whose_citations_all_resolve_is_accepted():
    from metermind.retrieval.grounded_answer import check_citations

    chunks = three_extracts()
    cited = check_citations("The rate is Rs. 3.50 [FY2026-27-LT1-002], and the fixed charge is "
                            "Rs. 50.00 [FY2026-27-LT1-003].", chunks)
    assert cited == ["FY2026-27-LT1-002", "FY2026-27-LT1-003"], (
        f"both citations resolve and both should come back, got {cited}")
    assert check_citations("NOT IN THE ORDER", chunks) == [], (
        "an answer that cites nothing is grounded in nothing, which is honest and allowed")


def test_week7_day2_a_citation_nobody_handed_over_is_refused():
    from metermind.retrieval.grounded_answer import UngroundedAnswer, check_citations

    chunks = three_extracts()
    try:
        check_citations("The rate is Rs. 3.50 [FY2026-27-LT1-002] and the duty is five percent "
                        "[FY2026-27-LT1-009].", chunks)
        raise AssertionError(
            "an answer citing an extract that was never retrieved should be refused; a citation "
            "that cannot be resolved is how a wrong answer gets to look sourced")
    except UngroundedAnswer as refused:
        assert "FY2026-27-LT1-009" in str(refused), (
            f"the refusal should name the citation that does not resolve, got {refused}")


def test_week7_day2_nothing_retrieved_means_no_answer_at_all(tmp_path):
    from metermind.retrieval.grounded_answer import (
        UngroundedAnswer,
        answer_from_chunks,
        build_answer_prompt,
    )

    for refusing in (lambda: build_answer_prompt("What is the rate?", []),
                     lambda: without_a_key(lambda: answer_from_chunks(
                         "What is the rate?", [], str(tmp_path / "cache.json")))):
        try:
            refusing()
            raise AssertionError(
                "with nothing retrieved there is nothing to be grounded in, so the only honest "
                "outcome is a refusal - answering here would be answering from memory")
        except UngroundedAnswer:
            pass


def test_week7_day2_one_row_is_written_for_every_question_with_what_it_stands_on(tmp_path):
    import csv

    from metermind.retrieval.grounded_answer import (
        ANSWER_FIELDS,
        build_answer_prompt,
        write_answers,
    )
    from metermind.retrieval.vector_store import search_tariff

    collection = a_shared_tariff_store()[0]
    asked = [{"question_id": "RQ0001", "question": "What is the fixed charge for each kilowatt?"},
             {"question_id": "RQ0002", "question": "How long is a billing cycle?"}]
    chunks = search_tariff(collection, asked[0]["question"], the_embedder())
    cache_path = a_seeded_cache(
        tmp_path, build_answer_prompt(asked[0]["question"], chunks),
        '{"answer": "The fixed charge is stated in [%s].", "citations": ["%s"]}'
        % (chunks[0]["chunk_id"], chunks[0]["chunk_id"]))
    answers_path = tmp_path / "tariff_answers.csv"
    counted = without_a_key(lambda: write_answers(asked, collection, the_embedder(),
                                                  str(answers_path), cache_path))
    assert counted == {"questions": 2, "answered": 1, "refused": 1}, (
        f"one question had an answer to read and one did not, got {counted}")
    rows = list(csv.DictReader(answers_path.open(encoding="utf-8")))
    assert len(rows) == 2, f"one row for every question asked, got {len(rows)}"
    assert tuple(rows[0]) == ANSWER_FIELDS, (
        f"the columns should be {ANSWER_FIELDS}, got {tuple(rows[0])}")
    assert rows[0]["citations"] == chunks[0]["chunk_id"], (
        f"the row should carry what the answer cited, got {rows[0]['citations']!r}")
    assert rows[0]["chunks_handed_over"].split(";") == [one["chunk_id"] for one in chunks], (
        "the row should also carry every extract the model was shown, so an answer can be "
        "argued with afterwards")


# --------------------------------------------------------------------------- WEEK 7 DAY 3

def test_week7_day3_the_order_returned_is_the_one_whose_window_holds_the_period():
    from metermind.retrieval.document_loader import read_manifest
    from metermind.retrieval.filtered_search import NoOrderInForce, order_in_force

    manifest = read_manifest()
    order = order_in_force(manifest, "domestic", "2024-09")
    assert order["consumer_category"] == "domestic", (
        f"a domestic question must be answered from a domestic order, got "
        f"{order['consumer_category']}")
    assert order["effective_from"] <= "2024-09-01" <= order["effective_to"], (
        f"{order['order_id']} is in force {order['effective_from']} to {order['effective_to']}, "
        f"which does not hold 2024-09")
    try:
        order_in_force(manifest, "domestic", "2019-01")
        raise AssertionError(
            "no order was in force in 2019, and answering from one that was not is worse than "
            "not answering")
    except NoOrderInForce:
        pass


def test_week7_day3_the_same_question_in_two_periods_reaches_two_different_orders():
    from metermind.retrieval.document_loader import read_manifest
    from metermind.retrieval.filtered_search import order_in_force

    manifest = read_manifest()
    reached = [order_in_force(manifest, "domestic", period)["order_id"]
               for period in ("2024-09", "2025-06", "2025-11", "2026-06")]
    assert len(set(reached)) == len(reached), (
        f"four billing periods spanning four orders should reach four different orders, got "
        f"{reached}; if two periods share an order the schedule has stopped changing and the "
        f"whole filter is pointless")
    early, late = order_in_force(manifest, "domestic", "2025-06"), order_in_force(
        manifest, "domestic", "2025-11")
    assert early["effective_to"] < late["effective_from"], (
        f"{early['order_id']} should have ceased before {late['order_id']} took effect, and "
        f"the windows read {early['effective_to']} then {late['effective_from']}")


def test_week7_day3_no_chunk_comes_back_from_another_consumer_category():
    from metermind.retrieval.document_loader import read_manifest
    from metermind.retrieval.filtered_search import filtered_search

    collection = a_shared_tariff_store(6)[0]
    manifest = read_manifest()
    for category in ("domestic", "commercial", "agricultural"):
        found = filtered_search(collection, "how is the fixed charge levied", the_embedder(),
                                category, "2024-09", manifest)
        assert {one["consumer_category"] for one in found} == {category}, (
            f"a {category} connection is billed under its own schedule, and these extracts "
            f"came from {sorted({one['consumer_category'] for one in found})}")


def test_week7_day3_without_the_filter_an_out_of_force_extract_does_come_back(tmp_path):
    import csv

    from metermind.retrieval.document_loader import read_manifest
    from metermind.retrieval.filtered_search import (
        FILTERED_ANSWER_FIELDS,
        filtered_search,
        order_in_force,
        write_filtered_answers,
    )
    from metermind.retrieval.vector_store import search_tariff

    collection = a_shared_tariff_store(6)[0]
    manifest = read_manifest()
    asked = "what is the rate for the first hundred units"
    in_force = order_in_force(manifest, "domestic", "2024-09")["order_id"]
    unfiltered = {one["order_id"] for one in search_tariff(collection, asked, the_embedder())}
    filtered = {one["order_id"] for one in filtered_search(collection, asked, the_embedder(),
                                                           "domestic", "2024-09", manifest)}
    assert unfiltered - {in_force}, (
        f"the same search without the filter should reach orders that were not in force, and "
        f"it reached only {unfiltered}; if it cannot go wrong the filter is not doing work")
    assert filtered == {in_force}, f"with the filter, only {in_force}, got {filtered}"
    answers_path = tmp_path / "filtered_answers.csv"
    counted = without_a_key(lambda: write_filtered_answers(
        [{"question_id": "RQ0001", "question": asked, "consumer_category": "domestic",
          "billing_period": "2024-09"}], collection, the_embedder(), str(answers_path),
        manifest, str(tmp_path / "empty_cache.json")))
    assert counted["questions"] == 1, f"one question was asked, got {counted}"
    rows = list(csv.DictReader(answers_path.open(encoding="utf-8")))
    assert tuple(rows[0]) == FILTERED_ANSWER_FIELDS, (
        f"the columns should be {FILTERED_ANSWER_FIELDS}, got {tuple(rows[0])}")
    assert rows[0]["order_in_force"] == in_force, (
        f"every answer has to say which order it was answered out of, got "
        f"{rows[0]['order_in_force']!r}")


# --------------------------------------------------------------------------- WEEK 7 DAY 4

def tools_pointed_at_what_this_run_built(tmp_path):
    """The four tools read paths the module publishes; a test settles them, as W5 D1 does."""
    import csv

    from config import constants
    from metermind.assistant import tools
    from metermind.data_access.database_loader import ReadingDatabase
    from metermind.exception_models.feature_pipeline import modelling_columns

    book = a_small_widened_book(600)
    wanted = ["reading_id"] + [one for one in list(modelling_columns(False))
                               + ["meter_install_date", "cycle_end_date"]
                               if one in book.columns]
    database_path = tmp_path / "readings.sqlite"
    ReadingDatabase(database_path).create_readings_table(book[wanted])
    a_fitted_champion(tmp_path, 600)
    report_path = tmp_path / "exception_report.csv"
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("exception_class", "precision", "recall", "support"))
        for one in constants.EXCEPTION_CLASSES:
            writer.writerow((one, 0.9, 0.9, 100))
    tools.readings_database_path = str(database_path)
    tools.champion_model_path = str(tmp_path / "champion.joblib")
    tools.operating_rule_path = str(tmp_path / "operating_rule.json")
    tools.exception_report_path = str(report_path)
    tools.tariff_store_directory = a_shared_tariff_store(6)[1]
    tools.opened_resources.clear()
    return book["reading_id"].iloc[0]


def test_week7_day4_there_are_four_tools_and_each_one_says_what_it_is_for():
    from metermind.assistant.tools import READING_TOOLS

    named = [one.name for one in READING_TOOLS]
    assert named == ["look_up_reading", "calculate_bill", "predict_reading_exception",
                     "search_tariff_order"], (
        f"the assistant is offered exactly these four tools and no others, got {named}")
    for one in READING_TOOLS:
        assert len(one.description) > 60, (
            f"{one.name} has a {len(one.description)} character description; the description is "
            f"the only thing telling the model when to reach for this tool and when not to")
        assert one.args_schema is not None, (
            f"{one.name} takes arguments and must declare their shape, or the model is free to "
            f"invent them")


def test_week7_day4_a_malformed_argument_is_refused_before_the_tool_body_runs():
    from pydantic import ValidationError

    from metermind.assistant.tools import calculate_bill, search_tariff_order

    for asked, wrong in ((calculate_bill, {"consumer_category": "industrial",
                                           "units_consumed": 100, "sanctioned_load_kw": 3}),
                         (calculate_bill, {"consumer_category": "domestic",
                                           "units_consumed": -5, "sanctioned_load_kw": 3}),
                         (search_tariff_order, {"question": "what is the rate",
                                                "consumer_category": "domestic",
                                                "billing_period": "September"})):
        try:
            asked.invoke(wrong)
            raise AssertionError(
                f"{asked.name} accepted {wrong}; an argument the schema cannot accept has to be "
                f"refused at the door, because by the time the body has run something has "
                f"already been read, fitted or searched")
        except ValidationError:
            pass


def test_week7_day4_an_unknown_reading_comes_back_as_a_named_failure(tmp_path):
    from metermind.assistant.tools import look_up_reading
    from metermind.core.exceptions import MeterMindError, ToolError

    tools_pointed_at_what_this_run_built(tmp_path)
    try:
        look_up_reading.invoke({"reading_identifier": "RDG00000000"})
        raise AssertionError(
            "a reading nobody has heard of must come back as that; an empty answer would be "
            "read as nothing being wrong with it")
    except ToolError as refused:
        assert "RDG00000000" in str(refused), (
            f"the failure should name the reading that was not found, got {refused}")
        assert isinstance(refused, MeterMindError), (
            "a tool failure belongs in the project's own exception family")


def test_week7_day4_the_bill_is_week_ones_and_the_class_carries_its_precision(tmp_path):
    from config import constants
    from metermind.assistant.tools import calculate_bill, predict_reading_exception
    from metermind.core.tariff_calculations import calculate_bill_amount

    reading_identifier = tools_pointed_at_what_this_run_built(tmp_path)
    said = calculate_bill.invoke({"consumer_category": "domestic", "units_consumed": 467,
                                  "sanctioned_load_kw": 3})
    assert said["current_demand_inr"] == round(calculate_bill_amount("domestic", 467, 3),
                                               constants.CURRENCY_DECIMAL_PLACES), (
        f"the tool must not do its own arithmetic; it should return what Week 1 returns, and "
        f"it returned {said}")
    decided = predict_reading_exception.invoke({"reading_identifier": reading_identifier})
    assert decided["exception_class"] in constants.EXCEPTION_CLASSES, (
        f"{decided['exception_class']} is not a class anybody works")
    assert decided["precision"] == 0.9, (
        f"the class has to come back with how often it is right, read out of the report Week 5 "
        f"Day 2 wrote, got {decided['precision']}")


# --------------------------------------------------------------------------- WEEK 7 DAY 5

def classifiers_pointed_at_what_this_run_fitted(tmp_path):
    """The triage node reads two published paths; a test fits small models and settles them."""
    import joblib

    from metermind.assistant import nodes
    from metermind.message_intelligence.complaint_classifier import (
        split_complaints,
        train_category_classifier,
        train_urgency_classifier,
    )

    corpus = a_complaint_corpus(700)
    for column, train, name in (("category", train_category_classifier, "category.joblib"),
                                ("urgency", train_urgency_classifier, "urgency.joblib")):
        fitting_text, _, fitting_labels, _ = split_complaints(corpus, column)
        joblib.dump(train(fitting_text, fitting_labels), tmp_path / name)
    nodes.category_model_path = str(tmp_path / "category.joblib")
    nodes.urgency_model_path = str(tmp_path / "urgency.joblib")
    nodes.loaded_classifiers.clear()


def test_week7_day5_the_state_declares_every_channel_and_exactly_two_accumulate():
    import typing

    from metermind.assistant.state import ACCUMULATING_CHANNELS, AssistantState

    declared = typing.get_type_hints(AssistantState, include_extras=True)
    for channel in ("question", "category", "urgency", "answer", "refusal", "finished",
                    "steps", "tool_calls"):
        assert channel in declared, (
            f"{channel} is written by a later day and is not declared on the state; a channel "
            f"nobody declared is a value that quietly disappears between nodes")
    accumulating = [name for name, kind in declared.items()
                    if getattr(kind, "__metadata__", None)]
    assert sorted(accumulating) == sorted(ACCUMULATING_CHANNELS), (
        f"exactly {sorted(ACCUMULATING_CHANNELS)} should add to what is already there and every "
        f"other channel should replace it, got {sorted(accumulating)}")


def test_week7_day5_a_new_state_starts_empty_with_the_question_set():
    from metermind.assistant.state import ACCUMULATING_CHANNELS, new_assistant_state

    started = new_assistant_state("Why is my bill for June three times the usual amount?")
    assert started["question"] == "Why is my bill for June three times the usual amount?", (
        "the question is the one thing a new run is given")
    for channel in ACCUMULATING_CHANNELS:
        assert started[channel] == [], (
            f"{channel} accumulates, so it has to start empty; anything already in it would be "
            f"read as work this run had done")
    assert started["finished"] is False, "a run that starts finished never does anything"
    assert started["answer"] == "" and started["refusal"] == "", (
        f"a new run has neither answered nor refused, got {started}")


def test_week7_day5_triage_names_a_category_the_classifier_publishes(tmp_path):
    from config import constants
    from metermind.assistant.nodes import triage_the_question
    from metermind.assistant.state import new_assistant_state

    classifiers_pointed_at_what_this_run_fitted(tmp_path)
    read = triage_the_question(new_assistant_state(
        "My bill for June is three times what I usually pay and nobody has visited."))
    assert read["category"] in constants.COMPLAINT_CATEGORIES, (
        f"{read['category']} is not a category any team works")
    assert read["steps"] == ["triage"], (
        f"every node has to say it ran, so a finished run can be read back, got {read}")


def test_week7_day5_triage_names_an_urgency_the_service_publishes(tmp_path):
    from config import constants
    from metermind.assistant.nodes import triage_the_question
    from metermind.assistant.state import new_assistant_state

    classifiers_pointed_at_what_this_run_fitted(tmp_path)
    for asked in ("There has been no supply in our street since last evening.",
                  "Please tell me the rate for the first hundred units."):
        read = triage_the_question(new_assistant_state(asked))
        assert read["urgency"] in constants.COMPLAINT_URGENCIES, (
            f"{read['urgency']} is not an urgency the service publishes")
        assert not read.get("finished"), (
            f"a question worth answering should not stop the run, got {read}")


def test_week7_day5_a_question_it_will_not_take_carries_a_reason_and_stops(tmp_path):
    from metermind.assistant.nodes import triage_the_question
    from metermind.assistant.state import new_assistant_state

    classifiers_pointed_at_what_this_run_fitted(tmp_path)
    for nothing_to_work_with in ("", "   ", "\n\t "):
        read = triage_the_question(new_assistant_state(nothing_to_work_with))
        assert read.get("finished") is True, (
            f"{nothing_to_work_with!r} gives the assistant nothing to act on, and a run that "
            f"carries on regardless will answer a question nobody asked; got {read}")
        assert read.get("refusal"), (
            f"a refusal has to say why, or the person is told no and nothing else, got {read}")
        assert not read.get("category"), (
            f"nothing was classified, so nothing should be claimed about it, got {read}")


# --------------------------------------------------------------------------- WEEK 8 DAY 1

def a_planned_state(tmp_path, question, plan, reason="the tools answer the question"):
    """A state that has been triaged, and a cache holding the plan the model would have sent."""
    import json

    from config import constants
    from metermind.assistant.agents import PLANNER_PROMPT, TOOL_CATALOGUE, build_agent_prompt
    from metermind.assistant.state import new_assistant_state

    state = new_assistant_state(question, "domestic", "2024-09")
    state["category"], state["urgency"] = "high_bill", "routine"
    prompt = build_agent_prompt(PLANNER_PROMPT, {
        "catalogue": json.dumps(TOOL_CATALOGUE, indent=2),
        "rounds": constants.ASSISTANT_TOOL_ROUNDS, "question": state["question"],
        "category": state["category"], "urgency": state["urgency"],
        "consumer_category": state["consumer_category"],
        "billing_period": state["billing_period"]})
    cache_path = a_seeded_cache(tmp_path, prompt,
                                json.dumps({"plan": plan, "reason": reason}), "planner.json")
    return state, cache_path


def test_week8_day1_the_catalogue_names_exactly_the_tools_the_assistant_holds():
    from metermind.assistant.agents import TOOL_CATALOGUE
    from metermind.assistant.tools import READING_TOOLS

    assert set(TOOL_CATALOGUE) == {one.name for one in READING_TOOLS}, (
        f"the catalogue the model is shown must be the tools that actually exist; it names "
        f"{sorted(TOOL_CATALOGUE)} and the assistant holds "
        f"{sorted(one.name for one in READING_TOOLS)}")
    for one in READING_TOOLS:
        assert TOOL_CATALOGUE[one.name]["does"] == one.description, (
            f"{one.name} is described to the model differently from how it describes itself; "
            f"two descriptions of one tool is one description too many")
        assert set(TOOL_CATALOGUE[one.name]["arguments"]) == set(one.args_schema.model_fields), (
            f"{one.name} is offered to the model taking "
            f"{sorted(TOOL_CATALOGUE[one.name]['arguments'])} and actually takes "
            f"{sorted(one.args_schema.model_fields)}; a planner told the wrong argument names "
            f"calls the tool with the wrong argument names, and every call comes back empty")


def test_week8_day1_a_prompt_with_a_placeholder_left_in_it_is_refused():
    from metermind.assistant.agents import (
        PLANNER_PROMPT,
        RESOLVER_PROMPT,
        build_agent_prompt,
    )
    from metermind.message_intelligence.llm_client import LanguageModelError

    filled = build_agent_prompt("answer {question} for a {consumer_category} connection",
                                {"question": "why is my bill high",
                                 "consumer_category": "domestic"})
    assert "{" not in filled, f"every placeholder should have been filled, got {filled!r}"
    for template in (PLANNER_PROMPT, RESOLVER_PROMPT):
        try:
            build_agent_prompt(template, {"question": "why is my bill high"})
            raise AssertionError(
                "a template sent to the model with a placeholder still in it asks a question "
                "nobody wrote, and should be refused rather than sent")
        except LanguageModelError:
            pass


def test_week8_day1_the_planner_is_offered_the_catalogue_and_nothing_else(tmp_path):
    from metermind.assistant.agents import TOOL_CATALOGUE, plan_tools
    from metermind.message_intelligence.llm_client import LanguageModelError

    plan = [{"tool": "search_tariff_order",
             "arguments": {"question": "what is the rate", "consumer_category": "domestic",
                           "billing_period": "2024-09"}}]
    state, cache_path = a_planned_state(tmp_path, "What is the rate for the first block?", plan)
    read = without_a_key(lambda: plan_tools(state, cache_path))
    assert [one["tool"] for one in read["plan"]] == ["search_tariff_order"], (
        f"the plan read back should be the plan that was sent, got {read['plan']}")
    assert set(one["tool"] for one in read["plan"]) <= set(TOOL_CATALOGUE), (
        "a planned step naming something outside the catalogue has nothing to run")
    assert read["steps"] == ["plan"], f"the planner has to say it ran, got {read}"
    broken, broken_cache = a_planned_state(tmp_path, "What is the rate for the first block?",
                                           "look up the reading and see")
    try:
        without_a_key(lambda: plan_tools(broken, broken_cache))
        raise AssertionError(
            "a plan that is a sentence rather than a list of steps cannot be run, and guessing "
            "what it meant is how an agent does something nobody asked for")
    except LanguageModelError:
        pass


def test_week8_day1_the_tools_run_are_the_tools_the_plan_named_in_that_order(tmp_path):
    from metermind.assistant.nodes import run_tools

    reading_identifier = tools_pointed_at_what_this_run_built(tmp_path)
    plan = [{"tool": "calculate_bill", "arguments": {"consumer_category": "domestic",
                                                     "units_consumed": 467,
                                                     "sanctioned_load_kw": 3}},
            {"tool": "look_up_reading", "arguments": {"reading_identifier": reading_identifier}},
            {"tool": "predict_reading_exception",
             "arguments": {"reading_identifier": reading_identifier}}]
    ran = run_tools({"plan": plan})
    assert [one["tool"] for one in ran["tool_calls"]] == [one["tool"] for one in plan], (
        f"the plan named {[one['tool'] for one in plan]} in that order and the node ran "
        f"{[one['tool'] for one in ran['tool_calls']]}")
    assert all("result" in one for one in ran["tool_calls"]), (
        f"every planned step should have carried something back, got {ran['tool_calls']}")
    assert ran["tool_calls"][0]["result"]["current_demand_inr"] > 0, (
        "the first step's result should be the bill the first step asked for")
    assert ran["steps"] == ["tools"], f"the node has to say it ran, got {ran}"


def test_week8_day1_a_plan_naming_a_tool_that_does_not_exist_is_never_run(tmp_path):
    from metermind.assistant.nodes import run_tools

    tools_pointed_at_what_this_run_built(tmp_path)
    ran = run_tools({"plan": [{"tool": "calculate_bill",
                               "arguments": {"consumer_category": "domestic",
                                             "units_consumed": 467, "sanctioned_load_kw": 3}},
                              {"tool": "issue_a_refund", "arguments": {}}]})
    assert ran.get("finished") is True, (
        f"a plan naming a tool nobody wrote cannot be carried out, and the run has to stop; "
        f"got {ran}")
    assert "issue_a_refund" in ran.get("refusal", ""), (
        f"the refusal should name the tool that does not exist, got {ran}")
    assert not ran.get("tool_calls"), (
        f"nothing may be run from a plan that cannot be carried out - not even the steps that "
        f"would have worked, because a half-run plan is a half-answered question; got {ran}")


# --------------------------------------------------------------------------- WEEK 8 DAY 2

def test_week8_day2_the_graph_registers_exactly_the_seven_nodes():
    from metermind.assistant.graph import ASSISTANT_NODES, build_assistant_graph

    named = [name for name, _ in ASSISTANT_NODES]
    assert named == ["triage", "plan", "tools", "draft", "critique", "gate", "respond"], (
        f"the flow runs triage, plan, tools, draft, critique, gate, respond, and the graph "
        f"declares {named}")
    registered = set(build_assistant_graph().compile().get_graph().nodes)
    assert registered - {"__start__", "__end__"} == set(named), (
        f"every declared node has to be wired in and nothing else may be; the compiled graph "
        f"holds {sorted(registered)}")


def test_week8_day2_a_run_that_has_stopped_is_routed_to_the_end():
    from langgraph.graph import END
    from metermind.assistant.graph import CARRY_ON, still_going, worth_answering

    for route in (worth_answering, still_going):
        assert route({"question": "why is my bill high"}) == CARRY_ON, (
            f"{route.__name__} should let an ordinary run carry on")
        assert route({"finished": True}) == END, (
            f"{route.__name__} should send a finished run to the end; a node that runs after "
            f"the run has stopped answers a question that was already refused")
        assert route({"refusal": "there is not enough here to work with"}) == END, (
            f"{route.__name__} should send a refused run to the end, whatever else is on the "
            f"state")


def test_week8_day2_the_gate_holds_what_the_run_established_and_nothing_else():
    from config import constants
    from metermind.assistant.nodes import approval_gate

    ordinary = {"draft": "Your bill for June is Rs. 2854.48 for 467 units.",
                "tool_calls": [{"tool": "calculate_bill",
                                "result": {"current_demand_inr": 2854.48}}]}
    carried = approval_gate(ordinary)
    assert not carried.get("held"), (
        f"an ordinary answer must not wait for a person; holding everything is the same as "
        f"holding nothing; got {carried}")
    assert carried["steps"] == ["gate"], f"the gate still has to say it ran, got {carried}"
    for held_class in constants.HELD_EXCEPTION_CLASSES:
        stopped = approval_gate(dict(ordinary, tool_calls=[
            {"tool": "predict_reading_exception",
             "result": {"exception_class": held_class, "precision": 0.9}}]))
        assert stopped.get("held"), (
            f"a reading the model read as {held_class} carries a legal consequence for the "
            f"consumer and must not be put to them without a person confirming it; got "
            f"{stopped}")
        assert held_class in stopped["held"], (
            f"the hold has to name what tripped it, got {stopped['held']!r}")
        assert stopped["answer"] == constants.HELD_FOR_A_PERSON_REPLY, (
            f"the consumer still gets told what is happening, got {stopped['answer']!r}")
    vetoed = approval_gate(dict(ordinary, veto="the draft quotes a rate no tool returned"))
    assert vetoed.get("held") == "the draft quotes a rate no tool returned", (
        f"a draft the critic objected to waits for a person rather than being dropped in "
        f"silence, got {vetoed}")
    assert approval_gate({"draft": "  ", "tool_calls": []}).get("held"), (
        "there is nothing to send, and sending nothing without saying so is worse than waiting")
    assert set(constants.HELD_EXCEPTION_CLASSES) < set(constants.EXCEPTION_CLASSES), (
        f"the classes held for a person are some of the five, not all of them, or every reading "
        f"would wait; got {constants.HELD_EXCEPTION_CLASSES}")


def test_week8_day2_the_critic_may_only_object_and_never_answers(tmp_path):
    import json

    from metermind.assistant.agents import CRITIC_PROMPT, build_agent_prompt, critique_draft

    state = {"question": "What is the rate for the first block?",
             "draft": "The rate is Rs. 9.99 for each unit.", "tool_calls": []}
    prompt = build_agent_prompt(CRITIC_PROMPT, {
        "question": state["question"], "draft": state["draft"],
        "tool_calls": json.dumps(state["tool_calls"], indent=2, default=str)})
    vetoed = a_seeded_cache(tmp_path, prompt, json.dumps(
        {"veto": True, "reason": "the tools returned no rate at all",
         "answer": "The rate is Rs. 3.20.", "draft": "The rate is Rs. 3.20."}), "critic.json")
    read = without_a_key(lambda: critique_draft(state, vetoed))
    assert "answer" not in read and "draft" not in read, (
        f"the critic checks and objects; the moment it writes the answer there is nobody left "
        f"to check it, and this one returned {sorted(read)}")
    assert read["veto"] == "the tools returned no rate at all", (
        f"an objection has to say what is wrong, got {read['veto']!r}")
    assert not read.get("answer") and not read.get("finished"), (
        f"the critic neither answers nor ends the run; it objects, and the gate puts the "
        f"objection in front of a person; got {read}")
    passed = a_seeded_cache(tmp_path, prompt, json.dumps(
        {"veto": False, "reason": "every figure in the draft came from a tool"}), "passed.json")
    read = without_a_key(lambda: critique_draft(state, passed))
    assert read["veto"] == "" and not read.get("finished"), (
        f"with nothing to object to the run should carry on, got {read}")


def test_week8_day2_the_retry_waits_longer_each_time_and_then_gives_up(tmp_path):
    from config import constants
    from metermind.message_intelligence.llm_client import (
        LanguageModelError,
        ask_model_with_retry,
    )

    from metermind.message_intelligence.llm_client import ModelNotConfigured

    half_written = tmp_path / "half_written_cache.json"
    half_written.write_text('{"a3f0": "the answer that was being writ', encoding="utf-8")
    waits = []
    try:
        without_a_key(lambda: ask_model_with_retry("Read the tone.", str(half_written),
                                                   attempts=3, pause_seconds=0.05, waits=waits))
        raise AssertionError(
            "three attempts on a cache that cannot be read still has no answer, and inventing "
            "one at the end would be worse than the failure")
    except LanguageModelError:
        pass
    assert len(waits) == 2, (
        f"three attempts means waiting twice between them, and it waited {len(waits)} times")
    assert waits[1] > waits[0], (
        f"a second failure means the far end is busier, not less busy, so each wait has to be "
        f"longer than the one before; got {waits}")
    watched, took = [], time.monotonic()
    try:
        without_a_key(lambda: ask_model_with_retry("Read the tone.", str(half_written),
                                                   attempts=3, pause_seconds=5.0, waits=watched))
    except LanguageModelError:
        pass
    assert watched and time.monotonic() - took < 1.0, (
        f"where a list is supplied the waits are recorded in it and NOT taken, so a suite can "
        f"check the backoff without anybody waiting for it; this recorded {watched} and still "
        f"took {time.monotonic() - took:.1f} seconds")
    nothing_cached, no_waiting = str(tmp_path / "nothing_cached.json"), []
    try:
        without_a_key(lambda: ask_model_with_retry("Read the tone.", nothing_cached, attempts=3,
                                                   pause_seconds=0.05, waits=no_waiting))
        raise AssertionError("with no key there is no answer to be had")
    except ModelNotConfigured:
        pass
    assert no_waiting == [], (
        f"waiting cannot supply a key that was never set, so a failure of configuration is "
        f"raised at once rather than three times over; got {no_waiting}")
    assert constants.MODEL_RETRY_ATTEMPTS >= 2 and constants.MODEL_RETRY_SECONDS > 0, (
        "the published retry figures have to describe a retry that actually waits")


# --------------------------------------------------------------------------- WEEK 8 DAY 3

def an_assistant_with_every_answer_seeded(tmp_path, draft, veto=False, reply=None):
    """Walks the flow once by hand to learn each prompt, and seeds the cache with every reply."""
    import json
    import os

    from config import constants
    from metermind.assistant import agents
    from metermind.assistant.agents import (
        CRITIC_PROMPT,
        PLANNER_PROMPT,
        RESOLVER_PROMPT,
        RESPONDER_PROMPT,
        TOOL_CATALOGUE,
        build_agent_prompt,
    )
    from metermind.assistant.nodes import run_tools, triage_the_question
    from metermind.assistant.state import new_assistant_state
    from metermind.message_intelligence.llm_client import cache_key

    tools_pointed_at_what_this_run_built(tmp_path)
    classifiers_pointed_at_what_this_run_fitted(tmp_path)
    state = new_assistant_state("Why is my bill for June so high?", "domestic", "2024-09")
    state.update(triage_the_question(state))
    plan = [{"tool": "calculate_bill", "arguments": {"consumer_category": "domestic",
                                                     "units_consumed": 467,
                                                     "sanctioned_load_kw": 3}}]
    seeded = {build_agent_prompt(PLANNER_PROMPT, {
        "catalogue": json.dumps(TOOL_CATALOGUE, indent=2),
        "rounds": constants.ASSISTANT_TOOL_ROUNDS, "question": state["question"],
        "category": state["category"], "urgency": state["urgency"],
        "consumer_category": state["consumer_category"],
        "billing_period": state["billing_period"]}): {"plan": plan,
                                                       "reason": "the bill was asked about"}}
    state["plan"] = plan
    state.update(run_tools(state))
    told = json.dumps(state["tool_calls"], indent=2, default=str)
    seeded[build_agent_prompt(RESOLVER_PROMPT, {"question": state["question"],
                                                "tool_calls": told})] = {
        "draft": draft, "reason": "the figure came from the billing tool"}
    seeded[build_agent_prompt(CRITIC_PROMPT, {"question": state["question"], "draft": draft,
                                              "tool_calls": told})] = {
        "veto": veto, "reason": "every figure in the draft came from a tool"}
    seeded[build_agent_prompt(RESPONDER_PROMPT, {"question": state["question"],
                                                 "draft": draft})] = {
        "reply": reply or draft, "reason": "said the same thing in plainer words"}
    model_name = os.environ.get("GEMINI_MODEL", "").strip() or constants.DEFAULT_LANGUAGE_MODEL
    cache_path = tmp_path / "assistant_cache.json"
    cache_path.write_text(json.dumps({cache_key(model_name, prompt): json.dumps(answer)
                                      for prompt, answer in seeded.items()}), encoding="utf-8")
    agents.language_model_cache_path = str(cache_path)
    return state["question"]


def test_week8_day3_a_held_run_is_picked_up_again_on_the_same_thread(tmp_path):
    from metermind.assistant.workflow import open_saved_graph, run_assistant

    question = an_assistant_with_every_answer_seeded(
        tmp_path, "Your June bill is Rs. 2854.48 for 467 units.", veto=True)
    graph = open_saved_graph(str(tmp_path / "threads.sqlite"))
    held = without_a_key(lambda: run_assistant(question, "thread-one", "domestic", "2024-09",
                                               graph))
    assert held["held"], f"the critic objected, so a person has to see it, got {held}"
    settled = {"configurable": {"thread_id": "thread-one"}}
    assert graph.get_state(settled).next == ("respond",), (
        f"a held run waits at the last node rather than disappearing, and this one is at "
        f"{graph.get_state(settled).next}")
    assert (tmp_path / "threads.sqlite").is_file(), (
        "the run has to be written down somewhere, or nobody can pick it up later")
    carried_on = without_a_key(lambda: run_assistant(question, "thread-two", "domestic",
                                                     "2024-09", graph))
    assert not carried_on["held"] or carried_on["thread_id"] == "thread-two", (
        "a second question runs on its own thread and does not disturb the first")
    assert graph.get_state(settled).next == ("respond",), (
        "the first thread is still waiting where it was left")


def test_week8_day3_the_consumers_answer_and_the_inspectors_reason_come_back_together(tmp_path):
    from metermind.assistant.workflow import (
        ASSISTANT_OUTCOME_FIELDS,
        open_saved_graph,
        run_assistant,
    )

    question = an_assistant_with_every_answer_seeded(
        tmp_path, "Your June bill is Rs. 2854.48 for 467 units on a 3 kW connection.")
    graph = open_saved_graph(str(tmp_path / "threads.sqlite"))
    outcome = without_a_key(lambda: run_assistant(question, "thread-three", "domestic",
                                                  "2024-09", graph))
    assert set(outcome) == set(ASSISTANT_OUTCOME_FIELDS), (
        f"a run comes back as {ASSISTANT_OUTCOME_FIELDS}, got {sorted(outcome)}")
    assert "2854.48" in outcome["answer"], (
        f"the consumer gets the answer the responder wrote, got {outcome['answer']!r}")
    assert outcome["category"] and outcome["urgency"], (
        f"an inspector reading this needs to know what it was read as, got {outcome}")
    assert outcome["tools_called"] == ["calculate_bill"], (
        f"and which tools it stands on, got {outcome['tools_called']}")
    assert outcome["steps"] == ["triage", "plan", "tools", "draft", "critique", "gate",
                               "respond"], (
        f"every node it went through, in order, got {outcome['steps']}")


def test_week8_day3_a_held_thread_is_released_and_an_unknown_one_is_not_found(tmp_path):
    from fastapi.testclient import TestClient

    from config import constants
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import build_application
    from metermind.api.routers import assistant

    question = an_assistant_with_every_answer_seeded(
        tmp_path, "Your June bill is Rs. 2854.48 for 467 units.", veto=True,
        reply="An inspector has looked at this and the figure is right.")
    assistant.assistant_threads_path = str(tmp_path / "threads.sqlite")
    assistant.opened_graph.clear()
    client = TestClient(build_application())
    consumer = {"Authorization": f"Bearer {issue_token('acc/1', constants.CONSUMER_ROLE)}"}
    inspector = {"Authorization": f"Bearer {issue_token('je/1180', constants.INSPECTOR_ROLE)}"}
    asked = client.post("/api/v1/assistant/questions",
                        json={"question": question, "consumer_category": "domestic",
                              "billing_period": "2024-09", "thread_id": "thread-held"},
                        headers=consumer)
    assert asked.status_code == 200, f"a signed-in consumer may ask; got {asked.text[:200]}"
    assert asked.json()["held"], f"this run should have been held, got {asked.json()}"
    assert asked.json()["answer"] == constants.HELD_FOR_A_PERSON_REPLY, (
        "the consumer is told a person is looking at it, not left with nothing")
    released = client.post("/api/v1/assistant/threads/thread-held/release", headers=inspector)
    assert released.status_code == 200, f"the inspector may release it, got {released.text[:200]}"
    assert "inspector has looked" in released.json()["answer"], (
        f"once released the run finishes and the reply goes out, got {released.json()}")
    missing = client.post("/api/v1/assistant/threads/thread-nobody-started/release",
                          headers=inspector)
    assert missing.status_code == 404, (
        f"a thread nobody started cannot be released, got {missing.status_code}")


