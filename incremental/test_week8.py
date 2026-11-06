"""Official Week 8 cases, with local stand-ins for the shared helpers."""
import json
import time

from config import constants
from test_week6_week7 import a_seeded_cache, without_a_key


class _Always:
    def __init__(self, label):
        self.label = label

    def predict(self, rows):
        return [self.label for _ in rows]


def classifiers_pointed_at_what_this_run_fitted(tmp_path):
    import joblib

    from metermind.assistant import nodes

    category_path = tmp_path / "category.joblib"
    urgency_path = tmp_path / "urgency.joblib"
    joblib.dump(_Always("high_bill"), category_path)
    joblib.dump(_Always("routine"), urgency_path)
    nodes.category_model_path = str(category_path)
    nodes.urgency_model_path = str(urgency_path)
    nodes.loaded_classifiers.clear()


def tools_pointed_at_what_this_run_built(tmp_path):
    import pandas as pd

    from metermind.assistant import tools
    from metermind.data_access.database_loader import ReadingDatabase
    from metermind.exception_models.baseline_model import build_baseline_model, save_model
    from metermind.exception_models.feature_engineering import widen_readings
    from metermind.exception_models.feature_pipeline import modelling_columns

    book = pd.read_csv(constants.READING_BOOK_TRAIN_PATH, nrows=800)
    book = book[book["consumer_category"].isin(list(constants.CONSUMER_CATEGORIES))]
    book = book.reset_index(drop=True)
    database_path = tmp_path / "readings.sqlite"
    ReadingDatabase(database_path).create_readings_table(book)

    widened = widen_readings(book)
    columns = list(modelling_columns(True))
    for column in columns:
        if column not in widened.columns:
            widened[column] = None
    model = build_baseline_model(widened=True)
    model.fit(widened[columns], widened["exception_class"].astype(str))
    model_path = tmp_path / "champion.joblib"
    save_model(model, model_path)
    rule_path = tmp_path / "operating_rule.json"
    rule_path.write_text(json.dumps({"tamper_floor": 0, "fault_floor": 0}), encoding="utf-8")
    report_path = tmp_path / "exception_report.csv"
    pd.DataFrame({
        "exception_class": list(constants.EXCEPTION_CLASSES),
        "precision": [0.9] * len(constants.EXCEPTION_CLASSES),
    }).to_csv(report_path, index=False)

    tools.readings_database_path = str(database_path)
    tools.champion_model_path = str(model_path)
    tools.operating_rule_path = str(rule_path)
    tools.exception_report_path = str(report_path)
    tools.opened_resources.clear()
    return str(book.iloc[0]["reading_id"])


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
