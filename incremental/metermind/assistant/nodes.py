from pathlib import Path

import joblib

from config import constants
from metermind.assistant.state import new_assistant_state
from metermind.assistant.tools import READING_TOOLS
from metermind.core.exceptions import ToolError
from metermind.message_intelligence.complaint_classifier import classify_message

category_model_path = constants.COMPLAINT_CATEGORY_MODEL_PATH
urgency_model_path = constants.COMPLAINT_URGENCY_MODEL_PATH
loaded_classifiers = {}


def _load_classifiers():
    if "category" not in loaded_classifiers or "urgency" not in loaded_classifiers:
        for name, where in (("category", category_model_path),
                            ("urgency", urgency_model_path)):
            if not Path(where).is_file():
                raise ToolError(f"no {name} classifier on file at {where}")
        loaded_classifiers["category"] = joblib.load(category_model_path)
        loaded_classifiers["urgency"] = joblib.load(urgency_model_path)
    return loaded_classifiers["category"], loaded_classifiers["urgency"]


def triage_the_question(state):
    question = str(state.get("question") or "")
    if not question.strip():
        return {"refusal": "nothing was asked", "finished": True, "steps": ["triage"]}
    category_model, urgency_model = _load_classifiers()
    read = classify_message(category_model, urgency_model, question)
    return {"category": read["category"], "urgency": read["urgency"], "steps": ["triage"]}


def _tools_by_name():
    return {tool.name: tool for tool in READING_TOOLS}


def run_tools(state):
    plan = state.get("plan") or []
    if not isinstance(plan, list):
        return {
            "refusal": f"the plan came back as {plan!r}, not a list of steps",
            "finished": True,
            "steps": ["tools"],
        }
    catalogue = _tools_by_name()
    unknown = []
    for step in plan:
        name = step.get("tool") if isinstance(step, dict) else step
        if name not in catalogue:
            unknown.append(name)
    if unknown:
        named = ", ".join(repr(name) for name in unknown)
        return {
            "refusal": f"the plan named {named}, which this assistant does not have",
            "finished": True,
            "steps": ["tools"],
        }

    calls = []
    for step in plan:
        name = step["tool"]
        arguments = step.get("arguments")
        if not isinstance(arguments, dict):
            calls.append({
                "tool": name,
                "arguments": arguments,
                "error": "the arguments were not an object",
            })
            continue
        try:
            result = catalogue[name].invoke(arguments)
            calls.append({"tool": name, "arguments": arguments, "result": result})
        except Exception as error:
            calls.append({"tool": name, "arguments": arguments, "error": str(error)})
    return {"tool_calls": calls, "steps": ["tools"]}


def _held_classes(state):
    found = []
    for call in state.get("tool_calls") or []:
        if not isinstance(call, dict):
            continue
        result = call.get("result")
        if not isinstance(result, dict):
            continue
        named = str(result.get("exception_class") or "")
        if named in constants.HELD_EXCEPTION_CLASSES and named not in found:
            found.append(named)
    return found


def approval_gate(state):
    reasons = [f"read as {named}" for named in _held_classes(state)]
    objection = str(state.get("veto") or "").strip()
    if objection:
        reasons.append(objection)
    if not str(state.get("draft") or "").strip():
        reasons.append("nothing was drafted")
    if not reasons:
        return {"held": "", "steps": ["gate"]}
    return {
        "held": "; ".join(reasons),
        "answer": constants.HELD_FOR_A_PERSON_REPLY,
        "steps": ["gate"],
    }


if __name__ == "__main__":
    for question in ("Why is my bill for June three times the usual amount this time?",
                     "There has been no supply in our street since last evening and it is "
                     "getting dangerous.",
                     ""):
        read = triage_the_question(new_assistant_state(question))
        print(f"{question[:52]!r:<56} -> {read}")
