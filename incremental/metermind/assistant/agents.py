import json
import re

from config import constants
from metermind.assistant.tools import READING_TOOLS
from metermind.message_intelligence.llm_client import (
    LanguageModelError,
    ask_model_with_retry,
    read_answer,
)

language_model_cache_path = constants.LANGUAGE_MODEL_CACHE_PATH

PLACEHOLDER_PATTERN = re.compile(r"\{([a-z_]+)\}")
PLANNER_KEYS = ("plan", "reason")
RESOLVER_KEYS = ("draft", "reason")
CRITIC_KEYS = ("veto", "reason")
RESPONDER_KEYS = ("reply", "reason")


def _argument_descriptions(tool):
    descriptions = {}
    for name, field in tool.args_schema.model_fields.items():
        descriptions[name] = field.description or ""
    return descriptions


def _catalogue_from_tools():
    catalogue = {}
    for tool in READING_TOOLS:
        catalogue[tool.name] = {
            "does": tool.description,
            "arguments": _argument_descriptions(tool),
        }
    return catalogue


TOOL_CATALOGUE = _catalogue_from_tools()

PLANNER_PROMPT = (
    "You choose which tools to call, and in what order, to answer one question "
    "about a connection of an electricity distribution company.\n"
    "You may name only tools in this catalogue. Naming any tool outside the "
    "catalogue is forbidden.\n"
    "{catalogue}\n"
    "Reply with a JSON object and nothing else, holding plan and reason. "
    "plan is a list of at most {rounds} steps. Each step is an object with tool "
    "and arguments. Use the exact argument names listed against each tool. "
    "Leave a step out rather than guess an argument you cannot fill. "
    "An empty plan is allowed where no tool is needed.\n"
    "Question: {question}\n"
    "What the triage read — category: {category}; urgency: {urgency}.\n"
    "The connection the question is about — consumer category: "
    "{consumer_category}; billing period: {billing_period}.\n"
    'Answer in the form {{"plan": [{{"tool": "<name>", "arguments": {{}}}}], '
    '"reason": "<why these steps>"}}.'
)

RESOLVER_PROMPT = (
    "Draft the reply from what the tools returned, and from nothing else. "
    "Do not work out any figure the tools did not return. "
    "Where the tools did not answer the question, say so plainly rather than "
    "fill the gap.\n"
    "Question: {question}\n"
    "What the tools returned: {tool_calls}\n"
    "Reply with a JSON object and nothing else, holding draft and reason, "
    'in the form {{"draft": "<the draft>", "reason": "<why>"}}.'
)

CRITIC_PROMPT = (
    "You may only object. You may not rewrite the draft and you may not answer "
    "the question itself.\n"
    "Object where the draft carries a figure the tools did not return, a "
    "statement contradicting what they did return, or an accusation against the "
    "consumer that the tools did not establish.\n"
    "Question: {question}\n"
    "What the tools returned: {tool_calls}\n"
    "Draft: {draft}\n"
    "Reply with a JSON object and nothing else, holding veto — true or false — "
    "and reason, in the form "
    '{{"veto": false, "reason": "<why you object, or nothing if you do not>"}}.'
)

RESPONDER_PROMPT = (
    "Write the reply the consumer reads. Confine the reply to what the draft "
    "says, in plain language, without jargon and without any figure the draft "
    "does not carry.\n"
    "Question: {question}\n"
    "Draft: {draft}\n"
    "Reply with a JSON object and nothing else, holding reply and reason, "
    'in the form {{"reply": "<the reply>", "reason": "<why>"}}.'
)


def build_agent_prompt(template, filling):
    names = []
    for name in PLACEHOLDER_PATTERN.findall(template):
        if name not in names:
            names.append(name)
    missing = [name for name in names if name not in filling]
    if missing:
        raise LanguageModelError("nothing was supplied for " + ", ".join(missing))
    # Values can themselves contain braces (a tool result is JSON). Mark the
    # placeholders first so unescaping the template's doubled braces cannot
    # rewrite what was supplied.
    rendered = template
    for name in names:
        rendered = rendered.replace("{" + name + "}", "\x00" + name + "\x00")
    rendered = rendered.replace("{{", "{").replace("}}", "}")
    for name in names:
        rendered = rendered.replace("\x00" + name + "\x00", str(filling[name]))
    return rendered


def _asked(prompt, keys, cache_path):
    where = language_model_cache_path if cache_path is None else cache_path
    return read_answer(ask_model_with_retry(prompt, cache_path=where), keys)


def _plan_is_steps(plan):
    if not isinstance(plan, list):
        return False
    return all(isinstance(step, dict) and "tool" in step and "arguments" in step
               for step in plan)


def plan_tools(state, cache_path=None):
    prompt = build_agent_prompt(PLANNER_PROMPT, {
        "catalogue": json.dumps(TOOL_CATALOGUE, indent=2),
        "rounds": constants.ASSISTANT_TOOL_ROUNDS,
        "question": state.get("question", ""),
        "category": state.get("category", ""),
        "urgency": state.get("urgency", ""),
        "consumer_category": state.get("consumer_category", ""),
        "billing_period": state.get("billing_period", ""),
    })
    answer = _asked(prompt, PLANNER_KEYS, cache_path)
    plan = answer["plan"]
    if not _plan_is_steps(plan):
        raise LanguageModelError(
            f"the plan came back as {plan!r}, not a list of steps"
        )
    return {"plan": plan, "steps": ["plan"]}


def draft_answer(state, cache_path=None):
    prompt = build_agent_prompt(RESOLVER_PROMPT, {
        "question": state.get("question", ""),
        "tool_calls": json.dumps(state.get("tool_calls") or [], indent=2, default=str),
    })
    answer = _asked(prompt, RESOLVER_KEYS, cache_path)
    return {"draft": str(answer["draft"]), "steps": ["draft"]}


def _objected(veto):
    if isinstance(veto, bool):
        return veto
    return str(veto).strip().lower() in {"true", "yes", "1"}


def critique_draft(state, cache_path=None):
    prompt = build_agent_prompt(CRITIC_PROMPT, {
        "question": state.get("question", ""),
        "tool_calls": json.dumps(state.get("tool_calls") or [], indent=2, default=str),
        "draft": state.get("draft", ""),
    })
    answer = _asked(prompt, CRITIC_KEYS, cache_path)
    if _objected(answer["veto"]):
        reason = str(answer.get("reason") or "").strip() or "the draft does not agree with the tools"
        return {"veto": reason, "steps": ["critique"]}
    return {"veto": "", "steps": ["critique"]}


def write_response(state, cache_path=None):
    prompt = build_agent_prompt(RESPONDER_PROMPT, {
        "question": state.get("question", ""),
        "draft": state.get("draft", ""),
    })
    answer = _asked(prompt, RESPONDER_KEYS, cache_path)
    return {"answer": str(answer["reply"]), "finished": True, "steps": ["respond"]}


def _first_sentence(description):
    flat = " ".join(str(description).split())
    stop = flat.find(".")
    if stop < 0:
        return flat
    return flat[: stop + 1]


if __name__ == "__main__":
    agents = (
        ("planner", PLANNER_KEYS, PLANNER_PROMPT),
        ("resolver", RESOLVER_KEYS, RESOLVER_PROMPT),
        ("critic", CRITIC_KEYS, CRITIC_PROMPT),
        ("responder", RESPONDER_KEYS, RESPONDER_PROMPT),
    )
    for name, keys, prompt in agents:
        told = PLACEHOLDER_PATTERN.findall(prompt)
        print(f"{name:<11}answers with {keys!r:<22}and is told {told}")
    print()
    print(f"the planner may name these {len(TOOL_CATALOGUE)} tools and no others, "
          "and is given the argument names each one takes:")
    for name, entry in TOOL_CATALOGUE.items():
        print(f"   {name:<26} {_first_sentence(entry['does'])}")
        print(f"{'':<30}takes {list(entry['arguments'])}")
    print()
    print("the resolver is handed what the tools returned, and nothing else")
    print(build_agent_prompt(RESPONDER_PROMPT, {
        "question": "Why is my bill so high this month?",
        "draft": "The tools returned no figure for this bill.",
    }))
