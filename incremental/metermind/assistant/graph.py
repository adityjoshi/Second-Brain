from langgraph.graph import END, START, StateGraph

from metermind.assistant.agents import (
    critique_draft,
    draft_answer,
    plan_tools,
    write_response,
)
from metermind.assistant.nodes import approval_gate, run_tools, triage_the_question
from metermind.assistant.state import AssistantState

CARRY_ON = "carry on"
ASSISTANT_NODES = (
    ("triage", triage_the_question),
    ("plan", plan_tools),
    ("tools", run_tools),
    ("draft", draft_answer),
    ("critique", critique_draft),
    ("gate", approval_gate),
    ("respond", write_response),
)


def worth_answering(state):
    if state.get("finished") or str(state.get("refusal") or "").strip():
        return END
    return CARRY_ON


def still_going(state):
    if state.get("finished") or str(state.get("refusal") or "").strip():
        return END
    return CARRY_ON


class _AssistantGraph(StateGraph):
    """StateGraph that allows a node to share its name with a channel.

    The plan is both a channel and a node, and so is the draft. This release of
    the graph library refuses that overlap even though the run itself is sound.
    """

    def add_node(self, node, action=None, *, metadata=None, input=None, retry=None,
                 destinations=None):
        name = node if isinstance(node, str) else None
        hidden = self.channels.pop(name) if name in self.channels else None
        try:
            return super().add_node(
                node, action, metadata=metadata, input=input, retry=retry,
                destinations=destinations,
            )
        finally:
            if hidden is not None:
                self.channels[name] = hidden


def build_assistant_graph():
    graph = _AssistantGraph(AssistantState)
    for name, function in ASSISTANT_NODES:
        graph.add_node(name, function)
    graph.add_edge(START, "triage")
    graph.add_conditional_edges("triage", worth_answering, {CARRY_ON: "plan", END: END})
    graph.add_edge("plan", "tools")
    graph.add_conditional_edges("tools", still_going, {CARRY_ON: "draft", END: END})
    graph.add_edge("draft", "critique")
    graph.add_conditional_edges("critique", still_going, {CARRY_ON: "gate", END: END})
    graph.add_conditional_edges("gate", still_going, {CARRY_ON: "respond", END: END})
    graph.add_edge("respond", END)
    return graph


def _edges_in_holding_order(compiled):
    builder = compiled.builder
    rows = []
    for source, target in builder.edges:
        rows.append((source, target, False))
    for source, branches in builder.branches.items():
        for branch in branches.values():
            for label, target in branch.ends.items():
                rows.append((source, target, label == CARRY_ON))
    opening = [row for row in rows if row[0] == START]
    closing = [row for row in rows if row[0] == "respond" and row[1] == END]
    middle = [row for row in rows if row not in opening and row not in closing]
    middle.sort(key=lambda row: (row[0], row[1]))
    return opening + middle + closing


if __name__ == "__main__":
    compiled = build_assistant_graph().compile()
    print("the flow, and where it can leave early:")
    for source, target, only_while_going in _edges_in_holding_order(compiled):
        note = " only when the run is still going" if only_while_going else ""
        print(f"   {source:<13}-> {target:<12}{note}")
    samples = (
        ("an ordinary run", {"finished": False, "refusal": ""}),
        ("a run that has stopped", {"finished": True, "refusal": ""}),
        ("a run that was refused", {"finished": False, "refusal": "nothing was asked"}),
    )
    for label, sample in samples:
        print(
            f"   {label:<25}worth_answering: {worth_answering(sample):<11}"
            f"still_going: {still_going(sample)}"
        )
