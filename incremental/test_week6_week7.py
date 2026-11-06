"""Official Week 6-7 cases that run without the real data files (threads, orders, manifest)."""
import datetime


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
    assert len(sentences) == 5, sentences
    assert all(len(one) >= SHORTEST_SENTENCE_CHARACTERS for one in sentences)
    assert constants.SUMMARY_SENTENCE_COUNT < len(sentences)


def test_week6_day1_the_matrix_has_one_row_for_every_sentence():
    from metermind.message_intelligence.thread_summary import sentence_matrix, split_sentences

    sentences = split_sentences(a_thread_of_sentences())
    counted = sentence_matrix(sentences)
    assert counted.shape[0] == len(sentences)
    assert counted.shape[1] > 0
    assert counted.ndim == 2


def test_week6_day1_every_sentence_is_given_one_finite_score():
    import numpy

    from metermind.message_intelligence.thread_summary import score_sentences, split_sentences

    sentences = split_sentences(a_thread_of_sentences())
    scores = score_sentences(sentences)
    assert scores.shape == (len(sentences),)
    assert bool(numpy.isfinite(scores).all())


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
    assert len(kept) == constants.SUMMARY_SENTENCE_COUNT
    for one in kept:
        assert one in thread
    out_of_order = ("There is no supply in our street since yesterday evening and nobody has "
                    "come. The transformer near the school has been humming and smoking since "
                    "the morning. Our whole street has been without supply since the evening "
                    "and nobody has come. Kindly acknowledge this message at your earliest "
                    "convenience please.")
    said_in = split_sentences(out_of_order)
    came_back = [said_in.index(one)
                 for one in split_sentences(summarise_thread(out_of_order))]
    assert came_back == sorted(came_back)
    threads_path = tmp_path / "message_threads.csv"
    with threads_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("thread_id", "turn_number", "message_text"))
        for turn, sentence in enumerate(split_sentences(thread), start=1):
            writer.writerow(("THR000001", turn, sentence))
    summaries_path = tmp_path / "thread_summaries.csv"
    counted = write_thread_summaries(str(threads_path), str(summaries_path))
    rows = list(csv.DictReader(summaries_path.open(encoding="utf-8")))
    assert len(rows) == 1 == counted["threads"]
    for one in split_sentences(rows[0]["summary"]):
        assert one in thread


def test_week6_day1_a_thread_with_nothing_to_summarise_is_refused():
    from metermind.message_intelligence.thread_summary import UnreadableThread, summarise_thread

    for nothing_usable in ("", "Ok. Yes. No.", "   "):
        try:
            summarise_thread(nothing_usable)
            raise AssertionError(nothing_usable)
        except UnreadableThread:
            pass


def a_seeded_cache(tmp_path, prompt, answer, name="llm_cache.json"):
    import json
    import os

    from config import constants
    from metermind.message_intelligence.llm_client import cache_key

    model_name = os.environ.get("GEMINI_MODEL", "").strip() or constants.DEFAULT_LANGUAGE_MODEL
    path = tmp_path / name
    path.write_text(json.dumps({cache_key(model_name, prompt): answer}), encoding="utf-8")
    return str(path)


def without_a_key(work):
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
        assert settings["api_key"] == "a-key-that-is-not-real"
        assert settings["model_name"] == "gemini-from-the-environment"
        os.environ["GEMINI_MODEL"] = ""
        assert load_settings()["model_name"] == constants.DEFAULT_LANGUAGE_MODEL
        os.environ["GEMINI_API_KEY"] = ""
        try:
            load_settings()
            raise AssertionError("a missing key should be refused")
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
    assert first == cache_key("gemini-2.0-flash", "What is the fixed charge for LT-1?")
    assert first != cache_key("gemini-2.0-flash", "What is the fixed charge for LT-2?")
    assert first != cache_key("gemini-1.5-flash", "What is the fixed charge for LT-1?")
    assert len(first) == 64


def test_week6_day2_a_call_that_fails_is_raised_and_never_answered_with_a_default(tmp_path):
    from metermind.message_intelligence.llm_client import LanguageModelError, ask_model

    cache_path = str(tmp_path / "empty_cache.json")

    def ask_with_no_key():
        try:
            ask_model("A prompt nothing has answered yet.", cache_path)
        except LanguageModelError as refused:
            return str(refused)
        raise AssertionError("answered with no key")

    assert "GEMINI_API_KEY" in without_a_key(ask_with_no_key)


def test_week6_day2_what_was_written_to_the_cache_is_what_is_read_back(tmp_path):
    from metermind.message_intelligence.llm_client import (
        LanguageModelError,
        cache_key,
        read_answer,
        read_cache,
        write_cache,
    )

    cache_path = str(tmp_path / "written_cache.json")
    assert read_cache(cache_path) == {}
    key = cache_key("gemini-2.0-flash", "Read the tone of this complaint.")
    said = '```json\n{"tone": "angry", "reason": "third reminder"}\n```'
    write_cache({key: said}, cache_path)
    assert read_cache(cache_path)[key] == said
    assert read_answer(said, ("tone", "reason")) == {"tone": "angry", "reason": "third reminder"}
    try:
        read_answer(said, ("tone", "reason", "confidence"))
        raise AssertionError("half answer accepted")
    except LanguageModelError as refused:
        assert "confidence" in str(refused)
    half_written = tmp_path / "half_written.json"
    half_written.write_text('{"a3f0": "the answer that was being writ', encoding="utf-8")
    try:
        read_cache(str(half_written))
        raise AssertionError("half-written cache accepted")
    except LanguageModelError:
        pass


def test_week6_day3_all_three_kinds_of_reference_are_found_in_one_message():
    from metermind.message_intelligence.reference_extraction import (
        find_account_numbers,
        find_complaint_references,
        find_meter_serials,
    )

    message = ("Against account ACC10004512 and also ACC10004512, the meter MTR-NS-004411 was "
               "changed. My earlier complaint CMP2400318 is still open, and meter "
               "MTR-SO-119002 is the old one.")
    assert find_account_numbers(message) == ["ACC10004512"]
    assert find_meter_serials(message) == ["MTR-NS-004411", "MTR-SO-119002"]
    assert find_complaint_references(message) == ["CMP2400318"]


def test_week6_day3_an_account_the_register_has_never_heard_of_is_marked():
    from metermind.message_intelligence.reference_extraction import (
        check_against_connection_register,
    )

    checked = check_against_connection_register(
        ["ACC10000001", "ACC99999999"], [], {"ACC10000001", "ACC10000002"}, {})
    assert checked["unknown_accounts"] == ["ACC99999999"]
    assert checked["serials_on_another_account"] == []


def test_week6_day3_a_serial_standing_against_another_account_is_the_worse_fault():
    from metermind.message_intelligence.reference_extraction import (
        check_against_connection_register,
    )

    known = {"ACC10000001", "ACC10000002"}
    owner = {"MTR-NS-000111": "ACC10000002", "MTR-NS-000222": "ACC10000001"}
    checked = check_against_connection_register(
        ["ACC10000001"], ["MTR-NS-000111", "MTR-NS-000222"], known, owner)
    assert checked["unknown_accounts"] == []
    assert checked["serials_on_another_account"] == ["MTR-NS-000111"]


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
        assert found == []
    checked = check_against_connection_register([], [], {"ACC10000001"}, {})
    assert checked == {"unknown_accounts": [], "serials_on_another_account": []}


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
    assert counted["messages"] == 3
    rows = list(csv.DictReader(extracted_path.open(encoding="utf-8")))
    assert len(rows) == 3
    assert tuple(rows[0]) == EXTRACTED_REFERENCE_FIELDS
    assert rows[2]["unknown_accounts"] == "ACC70000000"
    assert constants.EXTRACTED_REFERENCES_PATH.endswith(".csv")


class AlwaysSaysPriority:
    def __init__(self, urgency="priority"):
        self.urgency = urgency

    def predict(self, messages):
        return [self.urgency for one in messages]


def test_week6_day4_one_result_comes_back_for_every_message_even_when_one_fails(tmp_path):
    from metermind.message_intelligence.batch_pipeline import run_batch

    messages = [{"message_id": "MSG000001", "units": 120}, {"message_id": "MSG000002"},
                {"message_id": "MSG000003", "units": 40}]
    handled = run_batch(messages, lambda one: one["units"] * 2, str(tmp_path / "failures.csv"))
    assert len(handled) == len(messages)
    assert [handled[0], handled[2]] == [240, 80]


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
    assert isinstance(handled[1], MessageFailure)
    assert handled[1].message_id == "MSG000002"
    assert "the reading is missing" in handled[1].reason
    written = list(csv.DictReader(failures_path.open(encoding="utf-8")))
    assert [one["message_id"] for one in written] == ["MSG000002"]


def test_week6_day4_the_prompt_the_model_sees_carries_the_message(tmp_path):
    from metermind.message_intelligence.escalation import TONE_PROMPT, read_tone

    message_text = "This is the third time I am writing and nobody has come."
    assert "{message_text}" in TONE_PROMPT
    rendered = TONE_PROMPT.format(message_text=message_text)
    assert message_text in rendered
    cache_path = a_seeded_cache(tmp_path, rendered,
                                '{"tone": "angry", "reason": "third time I am writing"}')
    read = without_a_key(lambda: read_tone(message_text, cache_path))
    assert read["tone"] == "angry"
    assert read["reason"]


def test_week6_day4_the_decision_moves_when_any_one_of_the_three_signals_moves(tmp_path):
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
    assert waiting_only["escalate"] is False
    assert decided(long_after, "emergency", calm)["escalate"] is True
    assert decided(long_after, "routine", angry)["escalate"] is True
    assert decided(same_week, "emergency", calm)["escalate"] is False
    assert (waiting_only["age_days"], waiting_only["urgency"], waiting_only["tone"]) == (
        constants.COMPLAINT_AGE_ESCALATION_DAYS + 9, "routine", "calm")
    assert complaint_age_days("2026-01-01", datetime.date(2026, 1, 22)) == 21
    assert decide_escalation(0, "emergency", "angry")["signals"] == ["urgency", "tone"]


def test_week6_day4_the_three_signals_are_written_beside_the_decision(tmp_path):
    import csv

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
    assert (counted["decided"], counted["failed"]) == (1, 1), counted
    rows = list(csv.DictReader(escalations_path.open(encoding="utf-8")))
    assert tuple(rows[0]) == ESCALATION_FIELDS
    assert (rows[0]["age_days"], rows[0]["urgency"], rows[0]["tone"]) == ("31", "priority",
                                                                         "angry")
    assert rows[0]["escalate"] == "True" and "tone" in rows[0]["signals"]
    assert LanguageModelError.__module__.endswith("llm_client")


def test_week6_day5_the_pieces_keep_to_the_size_and_carry_the_overlap():
    from metermind.retrieval.chunking import split_into_chunks

    text = "".join(f"sentence number {number} of the order. " for number in range(200))
    pieces = split_into_chunks(text, size=300, overlap=60)
    assert all(len(one) <= 300 for one in pieces)
    assert len(pieces) > 1
    assert text[300 - 60:300] in (pieces[0][-60:] + pieces[1][:60])
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
        assert field in entry
    assert (entry["order_id"], entry["consumer_category"]) == ("FY2024-25-LT1", "domestic")
    assert (entry["effective_from"], entry["effective_to"]) == ("2024-04-01", "2025-03-31")
    assert entry["section"] == "ENERGY CHARGE"


def test_week7_day1_the_distance_measure_is_stated_and_not_left_to_the_default():
    from config import constants
    from metermind.retrieval.vector_store import STORE_SETTINGS

    assert STORE_SETTINGS["hnsw:space"] == constants.VECTOR_DISTANCE_MEASURE


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
        assert one["chunk_id"] in prompt
        assert one["text"] in prompt
    assert set(CITATION_PATTERN.findall(prompt)) == {one["chunk_id"] for one in chunks}, (
        sorted(set(CITATION_PATTERN.findall(prompt))))
    assert "What is the rate for the first block?" in prompt
    assert constants.UNANSWERABLE_REPLY in prompt


def test_week7_day2_an_answer_whose_citations_all_resolve_is_accepted():
    from metermind.retrieval.grounded_answer import check_citations

    chunks = three_extracts()
    cited = check_citations("The rate is Rs. 3.50 [FY2026-27-LT1-002], and the fixed charge is "
                            "Rs. 50.00 [FY2026-27-LT1-003].", chunks)
    assert cited == ["FY2026-27-LT1-002", "FY2026-27-LT1-003"]
    assert check_citations("NOT IN THE ORDER", chunks) == []


def test_week7_day2_a_citation_nobody_handed_over_is_refused():
    from metermind.retrieval.grounded_answer import UngroundedAnswer, check_citations

    try:
        check_citations("The rate is Rs. 3.50 [FY2026-27-LT1-002] and the duty is five percent "
                        "[FY2026-27-LT1-009].", three_extracts())
        raise AssertionError("invented citation accepted")
    except UngroundedAnswer as refused:
        assert "FY2026-27-LT1-009" in str(refused)


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
            raise AssertionError("answered from nothing")
        except UngroundedAnswer:
            pass


def test_week7_day4_there_are_four_tools_and_each_one_says_what_it_is_for():
    from metermind.assistant.tools import READING_TOOLS

    assert [one.name for one in READING_TOOLS] == [
        "look_up_reading", "calculate_bill", "predict_reading_exception", "search_tariff_order"]
    for one in READING_TOOLS:
        assert len(one.description) > 60
        assert one.args_schema is not None


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
            raise AssertionError(f"{asked.name} accepted {wrong}")
        except ValidationError:
            pass


def test_week7_day4_the_bill_is_week_ones():
    from config import constants
    from metermind.assistant.tools import calculate_bill
    from metermind.core.tariff_calculations import calculate_bill_amount

    said = calculate_bill.invoke({"consumer_category": "domestic", "units_consumed": 467,
                                  "sanctioned_load_kw": 3})
    assert said["current_demand_inr"] == round(calculate_bill_amount("domestic", 467, 3),
                                               constants.CURRENCY_DECIMAL_PLACES)


def test_week7_day5_the_state_declares_every_channel_and_exactly_two_accumulate():
    import typing

    from metermind.assistant.state import ACCUMULATING_CHANNELS, AssistantState

    declared = typing.get_type_hints(AssistantState, include_extras=True)
    for channel in ("question", "category", "urgency", "answer", "refusal", "finished",
                    "steps", "tool_calls"):
        assert channel in declared
    accumulating = [name for name, kind in declared.items()
                    if getattr(kind, "__metadata__", None)]
    assert sorted(accumulating) == sorted(ACCUMULATING_CHANNELS)


def test_week7_day5_a_new_state_starts_empty_with_the_question_set():
    from metermind.assistant.state import ACCUMULATING_CHANNELS, new_assistant_state

    started = new_assistant_state("Why is my bill for June three times the usual amount?")
    assert started["question"] == "Why is my bill for June three times the usual amount?"
    for channel in ACCUMULATING_CHANNELS:
        assert started[channel] == []
    assert started["finished"] is False
    assert started["answer"] == "" and started["refusal"] == ""
