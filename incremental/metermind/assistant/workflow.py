import sqlite3
from pathlib import Path

from config import constants
from metermind.assistant.graph import build_assistant_graph
from metermind.assistant.state import new_assistant_state
from metermind.core.exceptions import MeterMindError

ASSISTANT_OUTCOME_FIELDS = (
    "thread_id",
    "answer",
    "held",
    "refusal",
    "category",
    "urgency",
    "steps",
    "tools_called",
)


class NoSuchThread(MeterMindError):
    pass


def open_saved_graph(threads_path=constants.ASSISTANT_THREADS_PATH):
    path = Path(threads_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), check_same_thread=False)
    from langgraph.checkpoint.sqlite import SqliteSaver

    compiled = build_assistant_graph().compile(
        checkpointer=SqliteSaver(connection),
        interrupt_before=["respond"],
    )
    compiled.threads_connection = connection
    compiled.threads_path = str(path)
    return compiled


def _config(thread_id):
    return {"configurable": {"thread_id": str(thread_id)}}


def _snapshot(graph, thread_id):
    return graph.get_state(_config(thread_id))


def _outcome(thread_id, values):
    calls = values.get("tool_calls") or []
    names = []
    for call in calls:
        if isinstance(call, dict) and call.get("tool"):
            names.append(call["tool"])
    return {
        "thread_id": thread_id,
        "answer": values.get("answer") or "",
        "held": values.get("held") or "",
        "refusal": values.get("refusal") or "",
        "category": values.get("category") or "",
        "urgency": values.get("urgency") or "",
        "steps": list(values.get("steps") or []),
        "tools_called": names,
    }


def _carry_on_if_not_held(graph, thread_id):
    snapshot = _snapshot(graph, thread_id)
    values = dict(snapshot.values or {})
    waiting = tuple(snapshot.next or ())
    if "respond" in waiting and not str(values.get("held") or "").strip():
        graph.invoke(None, _config(thread_id))
        values = dict(_snapshot(graph, thread_id).values or {})
    return _outcome(thread_id, values)


def _forget_thread(graph, thread_id):
    saver = graph.checkpointer
    if saver is None:
        return
    if not getattr(saver, "is_setup", False):
        saver.setup()
    with saver.cursor() as cursor:
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (str(thread_id),))
        cursor.execute("DELETE FROM writes WHERE thread_id = ?", (str(thread_id),))


def run_assistant(question, thread_id, consumer_category="domestic", billing_period="",
                  graph=None):
    if graph is None:
        graph = open_saved_graph()
    if question is None:
        snapshot = _snapshot(graph, thread_id)
        held = str((snapshot.values or {}).get("held") or "").strip()
        if tuple(snapshot.next or ()) and not held:
            graph.invoke(None, _config(thread_id))
    else:
        _forget_thread(graph, thread_id)
        graph.invoke(
            new_assistant_state(question, consumer_category, billing_period),
            _config(thread_id),
        )
    return _carry_on_if_not_held(graph, thread_id)


def release_held_run(thread_id, graph=None):
    if graph is None:
        graph = open_saved_graph()
    snapshot = _snapshot(graph, thread_id)
    if "respond" not in tuple(snapshot.next or ()):
        raise NoSuchThread(f"thread {thread_id} is not waiting")
    graph.update_state(_config(thread_id), {"held": ""}, as_node="gate")
    graph.invoke(None, _config(thread_id))
    values = dict(_snapshot(graph, thread_id).values or {})
    return _outcome(thread_id, values)


if __name__ == "__main__":
    print(f"threads are kept in : {constants.ASSISTANT_THREADS_PATH}")
    print("a run stops before  : respond, so a held one can be picked up there")
    print(f"a run comes back as : {ASSISTANT_OUTCOME_FIELDS}")
    compiled = open_saved_graph()
    unused = compiled.get_state({"configurable": {"thread_id": "unused"}})
    print(f"an unused thread has: nothing on it and waits at {tuple(unused.next)}")
