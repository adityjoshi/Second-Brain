"""Official Week 3 Day 5 and Week 4 Day 1 cases."""


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
    """A few hundred real rows, taken straight off the book without the cleaning pass."""
    import pandas

    from config import constants

    book = pandas.read_csv(constants.READING_BOOK_TRAIN_PATH, nrows=rows * 8)
    book = book[book["consumer_category"].isin(constants.CONSUMER_CATEGORIES)]
    for number in ("sanctioned_load_kw", "cycle_days", "units_consumed"):
        book = book[pandas.to_numeric(book[number], errors="coerce").notna()]
    book = book[pandas.to_numeric(book["sanctioned_load_kw"]) > 0]
    return book.head(rows).reset_index(drop=True)


def a_clean_book(tmp_path, rows):
    """The whole cleaning pass over real rows."""
    import pandas

    from config import constants
    from metermind.data_access.cleaning_pipeline import clean_reading_book

    pandas.read_csv(constants.READING_BOOK_TRAIN_PATH).head(rows * 2).to_csv(
        tmp_path / "some.csv", index=False)
    clean_reading_book(tmp_path / "some.csv", tmp_path / "clean.csv", tmp_path / "bad.csv")
    return pandas.read_csv(tmp_path / "clean.csv").sample(rows,
                                                          random_state=constants.MODEL_SEED)


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
