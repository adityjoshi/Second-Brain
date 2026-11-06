import os

# Change these two numbers to run only some weeks. 0 is the one-time setup.
START_WEEK = 0
END_WEEK = 8

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

CLEAN = (
    'python3 -c "from config import constants as c; '
    'from metermind.data_access.cleaning_pipeline import clean_reading_book as f; '
    'print(f(c.READING_BOOK_TRAIN_PATH, c.CLEAN_READING_BOOK_PATH, c.REJECTED_READING_BOOK_PATH))"'
)

STEPS = [
    (0, "python3 -m pip install -q langgraph-checkpoint-sqlite"),

    (1, "python3 -m metermind.core.entities"),
    (1, "python3 -m metermind.core.validators"),
    (1, "python3 -m metermind.core.decorators"),
    (1, "python3 -m metermind.data_access.file_storage"),

    (2, CLEAN),
    (2, "python3 -m metermind.data_access.database_loader"),
    (2, "python3 -m metermind.data_access.database_reports"),
    (2, "python3 -m metermind.api.orm_models"),

    (3, "python3 -m metermind.api.password_hashing"),
    (3, "python3 -m metermind.api.middleware"),
    (3, "python3 -m metermind.api.case_transitions"),
    (3, "python3 -m metermind.api.access_control"),
    (3, "python3 -m metermind.exception_models.feature_pipeline"),
    (3, "python3 -m metermind.exception_models.baseline_model"),

    (4, "python3 -m metermind.exception_models.tree_models"),
    (4, "python3 -m metermind.exception_models.cross_validation"),
    (4, "python3 -m metermind.exception_models.feature_engineering"),
    (4, "python3 -m metermind.exception_models.champion_model"),
    (4, "python3 -m metermind.exception_models.investigation_queues"),

    (5, "python3 -m metermind.exception_models.exception_report"),
    (5, "python3 -m metermind.message_intelligence.attention"),
    (5, "python3 -m metermind.message_intelligence.text_cleaning"),
    (5, "python3 -m metermind.message_intelligence.complaint_classifier"),

    (6, "python3 -m metermind.message_intelligence.thread_summary"),
    (6, "python3 -m metermind.message_intelligence.llm_client"),
    (6, "python3 -m metermind.message_intelligence.reference_extraction"),
    (6, "python3 -m metermind.message_intelligence.escalation"),
    (6, "python3 -m metermind.retrieval.document_loader"),
    (6, "python3 -m metermind.retrieval.chunking"),

    (7, "python3 -m metermind.retrieval.vector_store"),
    (7, "python3 -m metermind.retrieval.grounded_answer"),
    (7, "python3 -m metermind.retrieval.filtered_search"),
    (7, "python3 -m metermind.assistant.tools"),
    (7, "python3 -m metermind.assistant.state"),
    (7, "python3 -m metermind.assistant.nodes"),

    (8, "python3 -m metermind.assistant.agents"),
    (8, "python3 -m metermind.assistant.graph"),
    (8, "python3 -m metermind.assistant.workflow"),
]

results = []

for week, command in STEPS:
    if week < START_WEEK or week > END_WEEK:
        continue
    print("")
    print("=" * 70)
    print("WEEK", week, "->", command[:90])
    print("=" * 70)
    code = os.system(command)
    results.append((week, command, code == 0))

print("")
print("=" * 70)
print("SUMMARY")
print("=" * 70)
for week, command, ok in results:
    print("OK    " if ok else "FAILED", "week", week, command[:70])

failed = [r for r in results if not r[2]]
print("")
print("Steps run:", len(results), "  Failed:", len(failed))
if failed:
    print("The first failure is the one to fix. Later ones may fail because of it.")