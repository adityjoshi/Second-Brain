"""
final.py — Analysis: can we pass all tests by writing only agents.py?

Verdict
-------
NO. Writing only agents.py is not enough to pass the full suite.

tests.py has 15 tests. Only 3 of them target agents.py. The other 12
require correct implementations of state.py, nodes.py, and graph.py, plus
a working end-to-end pipeline that uses all of them together.


Test map (15 total)
-------------------
state.py   (2)  — schema + add_messages reducer
agents.py  (3)  — extract_repair_tasks, assign_technician_and_urgency, GEMINI_MODEL
nodes.py   (5)  — load_inspection, extract_repairs, assign_technicians, format_summary
graph.py   (2)  — four nodes registered, edges in documented order
e2e        (3)  — full invoke on INS-201 (live Gemini)


Why agents.py alone fails
-------------------------
1. state tests import InspectionState from state.py — agents.py never
   defines that schema.

2. node tests import and call load_inspection / extract_repairs /
   assign_technicians / format_summary from nodes.py. Those nodes call
   the agents, but the tests assert node return shapes (status, work_orders,
   summary text). Agent logic cannot satisfy those assertions by itself.

3. graph tests import build_workflow from graph.py and check node names
   and edge order. That wiring lives only in graph.py.

4. e2e tests invoke the compiled graph. They need:
     state schema → load node → extract agent → assign agent → format node
   Missing any of those layers fails the shared workflow run.

Even a perfect agents.py can pass at most 3/15 tests if the other modules
are empty or wrong.


What each module must provide
-----------------------------
state.py
  InspectionState with messages, inspection_id, property, crew, report,
  work_orders, summary, status. messages must be Annotated[..., add_messages].

agents.py  (the only module the question asked about)
  extract_repair_tasks(report) -> list[str]
    - prompt must contain the report
    - model = os.getenv / environ GEMINI_MODEL
    - parse lines starting with REPAIR:
  assign_technician_and_urgency(task, crew) -> (technician, urgency)
    - prompt must contain the task and every crew name
    - model from GEMINI_MODEL
    - parse TECHNICIAN: and URGENCY: labels

nodes.py
  load_inspection      — input() + JSON lookup; status extracting or completed
  extract_repairs      — call extract agent; empty tech/urgency; status assigning
  assign_technicians   — one agent call per work order; preserve task order
  format_summary       — string with id, property, count, every task/tech/urgency

graph.py
  START → load_inspection → extract_repairs → assign_technicians
        → format_summary → END


Current repo note
-----------------
state.py, nodes.py, graph.py, and agents.py are already implemented in
this workspace. Passing the suite still requires all four modules (and
google-genai installed + valid .env for the three live e2e tests).

One latent bug in nodes.py extract_repairs empty-report branch:
  "messages": f[AIMessage(...)]   # should be a list literal [...]
That path is not covered by the current unit tests (they always pass a
report), so it does not block the suite when INS-201 is used.


Bottom line
-----------
You cannot pass all test cases by writing only agents.py.
You need state.py + agents.py + nodes.py + graph.py (main.py is not
directly tested).
"""


def can_pass_all_tests_with_agents_only() -> bool:
    """Explicit answer for programmatic use."""
    return False


def test_coverage_breakdown() -> dict[str, int]:
    """How many tests each module owns (plus shared e2e)."""
    return {
        "state.py": 2,
        "agents.py": 3,
        "nodes.py": 5,
        "graph.py": 2,
        "end_to_end": 3,
        "total": 15,
        "max_passable_via_agents_only": 3,
    }


if __name__ == "__main__":
    print("Can we pass all tests by writing only agents.py?",
          can_pass_all_tests_with_agents_only())
    print("Coverage:", test_coverage_breakdown())
