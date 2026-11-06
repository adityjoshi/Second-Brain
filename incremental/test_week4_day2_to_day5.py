"""Official Week 4 Day 2–5 cases."""


def a_small_book(rows=400):
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
