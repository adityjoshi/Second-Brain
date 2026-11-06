"""Official Week 5 cases, with local stand-ins for the shared helpers."""
import pathlib
import random
import tempfile

from config import constants

if not pathlib.Path(constants.COMPLAINT_MESSAGES_PATH).is_file():
    # Local-only stand-in for the real corpus, which is not on this machine.
    import pandas

    random.seed(7)
    topics = {
        "high_bill": ["my bill is far too high this month", "charged for units I never used",
                      "the amount on the bill doubled"],
        "no_supply": ["there is no power supply", "electricity has been cut in our street",
                      "outage since last evening"],
        "meter_problem": ["the meter display is blank", "my meter is running fast",
                          "meter seal looks broken"],
        "connection_request": ["I need a new connection", "please enhance my sanctioned load",
                               "apply for a fresh service connection"],
        "payment_issue": ["payment was deducted but not credited", "online payment failed",
                          "receipt not generated after paying"],
    }
    urgencies = {"routine": ["please look into it when convenient"],
                 "priority": ["please resolve this soon"],
                 "emergency": ["wires are sparking and it is dangerous"]}
    rows = []
    for number in range(2000):
        category = random.choice(list(topics))
        urgency = random.choices(list(urgencies), weights=[6, 3, 1])[0]
        rows.append({
            "complaint_reference": f"CMP{number:07d}",
            "message_text": (f"Dear Sir,\n{random.choice(topics[category])}. "
                             f"{random.choice(urgencies[urgency])}. Ref CMP{number:07d}\n"
                             f"Regards,\nMobile: 98765{number:05d}"),
            "category": category,
            "urgency": urgency,
        })
    synthetic = pathlib.Path(tempfile.mkdtemp()) / "complaint_messages.csv"
    pandas.DataFrame(rows).to_csv(synthetic, index=False)
    constants.COMPLAINT_MESSAGES_PATH = str(synthetic)


def a_reading_to_screen():
    return {"account_number": "ACC10000123", "meter_serial": "MTR-NS-004411",
            "consumer_category": "domestic", "billing_period": "2026-06",
            "sanctioned_load_kw": 5, "cycle_days": 30, "previous_reading": 14208,
            "current_reading": 14675, "read_type": "actual", "read_date": "2026-07-01",
            "units_consumed": 467.0, "twelve_month_average_units": 180.0,
            "same_month_last_year_units": 195.0, "consecutive_estimated_reads": 0,
            "days_since_actual_read": 30, "neighbourhood_average_units": 210.0,
            "arrears_inr": 0.0, "payment_defaults_last_year": 0,
            "seal_check_result": "intact", "meter_make": "Genus", "division": "North",
            "meter_install_date": "2024-08-14", "cycle_end_date": "2026-06-30"}


def a_fitted_champion(tmp_path):
    import pandas

    from metermind.exception_models.baseline_model import split_readings
    from metermind.exception_models.feature_engineering import widen_readings
    from metermind.exception_models.feature_pipeline import modelling_columns
    from metermind.exception_models.tree_models import build_random_forest_model

    book = pandas.read_csv(constants.READING_BOOK_TRAIN_PATH, nrows=2000)
    book = book[book["consumer_category"].isin(constants.CONSUMER_CATEGORIES)]
    book = widen_readings(book.head(600).reset_index(drop=True))
    fitting, held_out, fitting_classes, held_out_classes = split_readings(
        book, list(modelling_columns(True)))
    champion = build_random_forest_model("balanced", True)
    champion.fit(fitting, fitting_classes)
    return champion, held_out, held_out_classes


def a_screening_client(tmp_path):
    from fastapi.testclient import TestClient

    from metermind.api.application_factory import build_application
    from metermind.api.routers import screening
    from metermind.exception_models.champion_model import save_champion

    champion, _, _ = a_fitted_champion(tmp_path)
    model_path, rule_path = save_champion(
        champion, {"tamper_floor": 0.6, "fault_floor": 0.4, "expected_cost": 0.0},
        tmp_path / "champion.joblib", tmp_path / "operating_rule.json")
    screening.champion_model_path = str(model_path)
    screening.operating_rule_path = str(rule_path)
    screening.loaded_champion.clear()
    return TestClient(build_application())


def test_week5_day1_screening_needs_a_token_like_the_rest_of_the_book(tmp_path):
    from metermind.api.application_factory import API_PREFIX

    client = a_screening_client(tmp_path)
    assert client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen()).status_code == 401


def test_week5_day1_a_signed_in_call_names_a_published_class_and_where_it_goes(tmp_path):
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import API_PREFIX

    client = a_screening_client(tmp_path)
    signed_in = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    answered = client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen(),
                           headers=signed_in)
    assert answered.status_code == 200, answered.text
    said = answered.json()
    assert said["exception_class"] in constants.EXCEPTION_CLASSES
    assert 0.0 <= said["confidence"] <= 1.0
    assert said["goes_to"].endswith(".csv")


def test_week5_day1_the_champion_is_read_from_disk_once_and_not_per_request(tmp_path):
    from metermind.api.access_control import issue_token
    from metermind.api.application_factory import API_PREFIX
    from metermind.api.routers import screening

    client = a_screening_client(tmp_path)
    signed_in = {"Authorization": f"Bearer {issue_token('me', constants.CONSUMER_ROLE)}"}
    client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen(), headers=signed_in)
    held = screening.loaded_champion.get("model")
    assert held is not None
    client.post(f"{API_PREFIX}/screening", json=a_reading_to_screen(), headers=signed_in)
    assert screening.loaded_champion.get("model") is held


def test_week5_day1_a_service_with_no_champion_refuses_rather_than_guessing(tmp_path):
    from fastapi.testclient import TestClient

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
    assert answered.status_code == 503


def test_week5_day1_a_typo_and_a_date_are_settled_at_the_door(tmp_path):
    from pydantic import ValidationError

    from metermind.api.schemas import ReadingSubmission

    good = {"account_number": "ACC10000123", "meter_serial": "MTR-AB-123456",
            "consumer_category": "COMMERICAL", "billing_period": "2026-06",
            "sanctioned_load_kw": 3.0, "cycle_days": 30, "previous_reading": 14208.0,
            "current_reading": 14675.0, "read_date": "14/06/2026"}
    settled = ReadingSubmission(**good)
    assert settled.consumer_category == "commercial"
    assert settled.read_date == "2026-06-14"
    try:
        ReadingSubmission(**dict(good, read_date="not taken"))
        raise AssertionError("a date in no shape at all should have been refused")
    except ValidationError:
        pass


def test_week5_day2_every_class_is_scored_separately_because_the_rare_ones_are_the_point(
        tmp_path):
    from metermind.exception_models.exception_report import per_class_scores

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    scored = per_class_scores(held_out_classes, champion.predict(held_out))
    assert set(scored) == set(constants.EXCEPTION_CLASSES)
    for one in scored.values():
        assert 0.0 <= one["precision"] <= 1.0 and 0.0 <= one["recall"] <= 1.0


def test_week5_day2_the_supports_add_back_to_the_rows_that_were_scored(tmp_path):
    from metermind.exception_models.exception_report import per_class_scores

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    scored = per_class_scores(held_out_classes, champion.predict(held_out))
    assert sum(one["support"] for one in scored.values()) == len(held_out_classes)


def test_week5_day2_the_confusion_frame_is_five_by_five_and_totals_the_rows(tmp_path):
    from metermind.exception_models.exception_report import confusion_frame

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    frame = confusion_frame(held_out_classes, champion.predict(held_out))
    assert frame.shape == (5, 5)
    assert int(frame.to_numpy().sum()) == len(held_out_classes)


def test_week5_day2_the_written_report_carries_a_row_per_class_and_a_total(tmp_path):
    import pandas

    from metermind.exception_models.exception_report import (
        EXCEPTION_REPORT_FIELDS,
        write_exception_report,
    )

    champion, held_out, held_out_classes = a_fitted_champion(tmp_path)
    written = write_exception_report(held_out_classes, champion.predict(held_out),
                                     tmp_path / "exception_report.csv")
    report = pandas.read_csv(written)
    assert list(report.columns) == list(EXCEPTION_REPORT_FIELDS)
    assert len(report) == len(constants.EXCEPTION_CLASSES) + 1
    assert set(constants.EXCEPTION_CLASSES) <= set(report["exception_class"])


def test_week5_day3_every_row_of_a_softmax_adds_up_to_one():
    import numpy

    from metermind.message_intelligence.attention import softmax_rows

    for scores in (numpy.arange(12, dtype=float).reshape(3, 4),
                   numpy.zeros((2, 5)), numpy.array([[-3.0, 0.5, 2.25]])):
        weighted = softmax_rows(scores)
        assert weighted.shape == numpy.asarray(scores).shape
        assert numpy.allclose(weighted.sum(axis=-1), 1.0)
        assert (weighted > 0.0).all()


def test_week5_day3_the_softmax_does_not_overflow_on_large_scores():
    import numpy

    from metermind.message_intelligence.attention import softmax_rows

    weighted = softmax_rows(numpy.array([[1000.0, 1001.0, 999.0]]))
    assert numpy.isfinite(weighted).all()
    assert abs(weighted.sum() - 1.0) < 1e-9
    assert weighted.argmax() == 1


def test_week5_day3_the_weights_are_square_in_the_sequence_and_each_row_adds_to_one():
    import numpy

    from metermind.message_intelligence.attention import attention_weights

    sequence = numpy.arange(20, dtype=float).reshape(5, 4)
    weights = attention_weights(sequence, sequence)
    assert weights.shape == (5, 5)
    assert numpy.allclose(weights.sum(axis=-1), 1.0)


def test_week5_day3_the_scores_are_scaled_by_the_size_of_a_key():
    import numpy

    from metermind.message_intelligence.attention import attention_weights, softmax_rows

    sequence = numpy.linspace(-1.0, 1.0, 4 * 16).reshape(4, 16)
    scaled = attention_weights(sequence, sequence)
    unscaled = softmax_rows(sequence @ sequence.T)
    assert not numpy.allclose(scaled, unscaled)
    assert scaled.max() < unscaled.max()


def test_week5_day3_what_comes_out_is_shaped_by_the_values_and_not_the_keys():
    import numpy

    from metermind.message_intelligence.attention import scaled_dot_product_attention

    queries = numpy.arange(12, dtype=float).reshape(3, 4)
    keys = numpy.arange(20, dtype=float).reshape(5, 4)
    values = numpy.arange(35, dtype=float).reshape(5, 7)
    assert scaled_dot_product_attention(queries, keys, values).shape == (3, 7)


def test_week5_day4_the_quoted_reply_goes_and_the_new_message_stays():
    from metermind.message_intelligence.text_cleaning import strip_quoted_reply

    message = ("There is no supply at my premises since this morning.\n"
               "\n> On 06/03/2026 the section office wrote:\n"
               "> Your complaint has been registered.\n")
    cleaned = strip_quoted_reply(message)
    assert "no supply at my premises" in cleaned
    assert "has been registered" not in cleaned


def test_week5_day4_a_greeting_and_a_sign_off_go_and_the_sentence_between_stays():
    from metermind.message_intelligence.text_cleaning import strip_greeting_and_sign_off

    message = "Dear Sir,\nThe display on my meter has gone blank.\nThanks and regards,\n"
    cleaned = strip_greeting_and_sign_off(message)
    assert "display on my meter has gone blank" in cleaned
    assert "Dear Sir" not in cleaned and "Thanks and regards" not in cleaned, cleaned


def test_week5_day4_a_mobile_number_block_goes():
    from metermind.message_intelligence.text_cleaning import strip_signature

    cleaned = strip_signature("My meter is running fast.\nMobile: 9876543210\n")
    assert "meter is running fast" in cleaned
    assert "9876543210" not in cleaned


def test_week5_day4_runs_of_space_collapse_and_the_ends_are_trimmed():
    from metermind.message_intelligence.text_cleaning import normalise_whitespace

    assert normalise_whitespace("  there   is\n\n  no    supply  ") == "there is no supply"


def test_week5_day4_the_whole_corpus_cleans_without_losing_or_emptying_a_message(tmp_path):
    import pandas

    from metermind.message_intelligence.text_cleaning import clean_corpus

    pandas.read_csv(constants.COMPLAINT_MESSAGES_PATH).head(600).to_csv(
        tmp_path / "some.csv", index=False)
    counted = clean_corpus(tmp_path / "some.csv", tmp_path / "clean.csv")
    cleaned = pandas.read_csv(tmp_path / "clean.csv")
    assert counted["messages"] == len(cleaned) == 600
    assert counted["shortest"] > 0
    assert "clean_text" in cleaned.columns


def a_complaint_corpus(rows=1800):
    import pandas

    return pandas.read_csv(constants.COMPLAINT_MESSAGES_PATH, nrows=rows)


def test_week5_day5_the_split_keeps_each_category_in_the_same_proportion():
    from metermind.message_intelligence.complaint_classifier import split_complaints

    corpus = a_complaint_corpus(1800)
    _, _, fitting_labels, held_out_labels = split_complaints(corpus, "category")
    whole = corpus["category"].value_counts(normalize=True)
    for labels in (fitting_labels, held_out_labels):
        share = labels.value_counts(normalize=True)
        for name in whole.index:
            assert abs(share[name] - whole[name]) < 0.02


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
    assert model.predict([raw])[0] == model.predict([clean_message(raw)])[0]


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
    assert model.score(held_out_text, held_out_labels) > always_the_commonest + 0.20


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
    assert model.score(held_out_text, held_out_labels) > always_the_commonest + 0.15


def test_week5_day5_a_message_is_given_one_category_and_one_urgency_from_the_published_sets():
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
    assert set(said) == {"category", "urgency"}
    assert said["category"] in constants.COMPLAINT_CATEGORIES
    assert said["urgency"] in constants.COMPLAINT_URGENCIES
