"""Every figure the question hands the associate, in one place.

What lives here is what the distribution company publishes: the tariff schedule, the plausibility
limits, the identifier formats and the paths files are written to. What an associate has to
derive - a bill, a proration, an exception class, a model's accuracy - is never here, because
producing that value is the work.
"""

DATA_DIRECTORY = "data"

READING_BOOK_TRAIN_PATH = "data/reading_book_train.csv"
READING_BOOK_PREDICT_PATH = "data/reading_book_predict.csv"
CONNECTION_REGISTER_PATH = "data/connection_register.csv"
COMPLAINT_MESSAGES_PATH = "data/complaint_messages.csv"
MESSAGE_THREADS_PATH = "data/message_threads.csv"
TARIFF_ORDERS_DIRECTORY = "data/tariff_orders"
TARIFF_ORDERS_MANIFEST_PATH = "data/tariff_orders_manifest.json"
RETRIEVAL_EVALUATION_SET_PATH = "data/retrieval_evaluation_set.json"

CLEAN_READING_BOOK_PATH = "processed_data/readings_clean.csv"
REJECTED_READING_BOOK_PATH = "processed_data/readings_rejected.csv"
WIDENED_READINGS_PATH = "processed_data/readings_widened.csv"
CLEAN_COMPLAINTS_PATH = "processed_data/complaints_clean.csv"
TARIFF_CHUNKS_PATH = "processed_data/tariff_chunks.json"

READINGS_DATABASE_PATH = "database/metermind.sqlite"
# The service keeps its own store, the one the ORM opens: the loader above rebuilds the
# reporting table from the clean book, and a service whose rows vanish on a reload is not a
# store. ClaimBridge splits the same two apart, and names its second file the same way.
ORM_DATABASE_PATH = "database/metermind_orm.sqlite"
READING_REPORTS_PATH = "output/reading_reports.csv"
EXCEPTION_REPORT_PATH = "output/exception_report.csv"
BASELINE_SCORES_PATH = "output/baseline_scores.json"
CROSS_VALIDATION_PATH = "output/cross_validation.csv"
FEATURE_LIFT_PATH = "output/feature_lift.json"
OPERATING_RULE_PATH = "output/operating_rule.json"
THREAD_SUMMARIES_PATH = "output/thread_summaries.csv"
EXTRACTED_REFERENCES_PATH = "output/extracted_references.csv"
ESCALATIONS_PATH = "output/escalations.csv"
BATCH_FAILURES_PATH = "output/batch_failures.csv"
TARIFF_ANSWERS_PATH = "output/tariff_answers.csv"
FILTERED_ANSWERS_PATH = "output/filtered_answers.csv"
REQUEST_LOG_PATH = "output/logs/requests.log"
AUDIT_TRAIL_PATH = "output/audit_trail.csv"

BASELINE_MODEL_PATH = "artifacts/baseline_exception.joblib"
DECISION_TREE_MODEL_PATH = "artifacts/tree_exception.joblib"
RANDOM_FOREST_MODEL_PATH = "artifacts/forest_exception.joblib"
CHAMPION_MODEL_PATH = "artifacts/champion_exception.joblib"
COMPLAINT_CATEGORY_MODEL_PATH = "artifacts/complaint_category.joblib"
COMPLAINT_URGENCY_MODEL_PATH = "artifacts/complaint_urgency.joblib"
COMPLAINT_SCORES_PATH = "output/complaint_scores.json"
LANGUAGE_MODEL_CACHE_PATH = "artifacts/llm_cache.json"

QUEUE_FILE_PATHS = {"genuine_high_usage": "output/queue_no_action.csv",
                    "estimated_read": "output/queue_meter_reading.csv",
                    "meter_fault": "output/queue_metering.csv",
                    "tamper_suspected": "output/queue_vigilance.csv",
                    "tariff_mismatch": "output/queue_billing.csv"}

# ---------------------------------------------------------------------------------------------
# THE TARIFF SCHEDULE, AS PUBLISHED IN THE ORDER IN FORCE
#
# Each band is (upper limit in units, rate in rupees a unit). A domestic connection is billed
# TELESCOPICALLY - every band charged at its own rate. A commercial connection is billed
# NON-TELESCOPICALLY - the whole consumption charged at the rate of the band it lands in. An
# agricultural connection has one band and one rate.
# ---------------------------------------------------------------------------------------------
CONSUMER_CATEGORIES = ("domestic", "commercial", "agricultural")
# Charged band by band. A category not named here is charged at the single rate of the band
# its whole consumption lands in. An agricultural connection has one band, so both readings
# come out the same.
TELESCOPIC_CATEGORIES = ("domestic", "agricultural")
TARIFF_CODE_BY_CATEGORY = {"domestic": "LT-1", "commercial": "LT-2", "agricultural": "LT-5"}
UNLIMITED_UNITS = 1000000

SLAB_TABLE_INR_BY_CATEGORY = {
    "domestic": ((100, 3.50), (200, 4.90), (400, 6.30), (UNLIMITED_UNITS, 7.10)),
    "commercial": ((200, 7.40), (500, 8.60), (UNLIMITED_UNITS, 9.80)),
    "agricultural": ((UNLIMITED_UNITS, 2.25),),
}
FIXED_CHARGE_INR_PER_KW_BY_CATEGORY = {"domestic": 50.0, "commercial": 145.0}
FIXED_CHARGE_INR_PER_HORSEPOWER = 22.0
HORSEPOWER_PER_KILOWATT = 1.34102
ELECTRICITY_DUTY_PERCENT_BY_CATEGORY = {"domestic": 5.0, "commercial": 9.0, "agricultural": 0.0}

# The rebate is means-tested by consumption: a cycle at or under the qualifying figure earns the
# per-unit rebate on every unit it used, and a cycle one unit above it earns nothing.
SUBSIDY_INR_PER_UNIT_BY_CATEGORY = {"domestic": 1.50, "commercial": 0.0, "agricultural": 2.60}
SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY = {"domestic": 100, "commercial": 0,
                                        "agricultural": UNLIMITED_UNITS}
CURRENCY_DECIMAL_PLACES = 2
# A measured score is published to four places, so what a file says and what a run printed are
# the same number, and so three figures a reader is meant to add up do add up.
MEASUREMENT_DECIMAL_PLACES = 4

# What a meter can do, and what a billing cycle is allowed to look like.
METER_DIGIT_COUNT = 5
METER_ROLLOVER_UNITS = 100000
MINIMUM_CYCLE_DAYS = 26
MAXIMUM_CYCLE_DAYS = 36
HOURS_IN_A_DAY = 24
CAPACITY_ALLOWANCE_FACTOR = 1.10
# Two different questions. A reading a little above the sanctioned load is SUSPICIOUS - the load
# on file is probably wrong, which is what a tariff mismatch is - and the connection is flagged
# for somebody to look at. A reading far above it is CORRUPT: no record of any load explains it,
# so the row is refused outright rather than flagged.
IMPLAUSIBLE_CAPACITY_FACTOR = 2.5
READ_TYPES = ("actual", "estimated", "locked")
SEAL_CHECK_RESULTS = ("intact", "not_checked", "broken", "resealed")
METER_MAKES = ("Secure", "Genus", "L&T", "HPL", "Avon")
DIVISIONS = ("North", "South", "East", "West", "Central")
SUBDIVISIONS_BY_DIVISION = {
    "North": ("N-Sector 7", "N-Sector 12", "N-Mill Road"),
    "South": ("S-Lake View", "S-Textile Park", "S-Old Town"),
    "East": ("E-Station Road", "E-Grain Market", "E-Riverside"),
    "West": ("W-Airport Belt", "W-Industrial Estate", "W-Canal Colony"),
    "Central": ("C-Fort Area", "C-Civil Lines", "C-Bus Depot"),
}

# The five things that can be wrong with a reading, and the ladder a case walks.
EXCEPTION_CLASSES = ("genuine_high_usage", "estimated_read", "meter_fault", "tamper_suspected",
                     "tariff_mismatch")
# The two classes a person must confirm before anything is said to a consumer: a vigilance
# case, and a reclassification that recovers the difference for up to twelve past cycles.
HELD_EXCEPTION_CLASSES = ("tamper_suspected", "tariff_mismatch")
INITIAL_CASE_STATUS = "raised"
INSPECTOR_ROLE = "inspector"
CONSUMER_ROLE = "consumer"
HELD_OUT_SHARE = 0.2

# The nine spellings the field application produced, and the three the platform uses.
CONSUMER_CATEGORY_CORRECTIONS = {"dom": "domestic", "residential": "domestic",
                                 "house": "domestic", "comm": "commercial",
                                 "commerical": "commercial", "shop": "commercial",
                                 "agri": "agricultural", "agriculture": "agricultural",
                                 "farm": "agricultural"}

# What every model in the project is fitted with, so two of them are comparable.
MODEL_SEED = 42
CROSS_VALIDATION_FOLDS = 5
DECISION_TREE_DEPTH_LIMIT = 8
RANDOM_FOREST_TREE_COUNT = 200
RANDOM_FOREST_DEPTH_LIMIT = 14
SUPPORT_VECTOR_REGULARISATION = 0.1
TEXT_MINIMUM_DOCUMENT_COUNT = 3
TEXT_MAXIMUM_FEATURES = 40000
COMPLAINT_CATEGORIES = ("high_bill", "no_supply", "meter_problem", "connection_request",
                        "payment_issue")
COMPLAINT_URGENCIES = ("routine", "priority", "emergency")
SUMMARY_SENTENCE_COUNT = 3

# What the language model is asked for and how the answer is read back.
DEFAULT_LANGUAGE_MODEL = "gemini-3.1-flash-lite"
TONE_READINGS = ("calm", "frustrated", "angry")
TONE_REPLY_KEYS = ("tone", "reason")
ESCALATION_SIGNALS_NEEDED = 2
ESCALATING_URGENCIES = ("emergency",)
ESCALATING_TONES = ("angry",)
COMPLAINT_AGE_ESCALATION_DAYS = 21
ESCALATION_SAMPLE_MESSAGES = 20

# How a tariff order is cut up before anything tries to search it.
CHUNK_CHARACTERS = 900
CHUNK_OVERLAP_CHARACTERS = 150

# The store the pieces are searched in, and the model that decides what near means.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DISTANCE_MEASURE = "cosine"
TARIFF_STORE_DIRECTORY = "database/tariff_store"
TARIFF_STORE_COLLECTION = "tariff_orders"
SEARCH_RESULT_COUNT = 5
STORED_CHUNK_FIELDS = ("order_id", "title", "consumer_category", "effective_from",
                       "effective_to", "section")

# What the assistant may do in one run, and where a held run is kept.
ASSISTANT_TOOL_ROUNDS = 3
ASSISTANT_THREADS_PATH = "database/assistant_threads.sqlite"
MODEL_RETRY_ATTEMPTS = 3
MODEL_RETRY_SECONDS = 2.0
HELD_FOR_A_PERSON_REPLY = ("This has gone to an inspector to look at, and you will hear back "
                           "once they have.")

# What a grounded answer is allowed to say, and what it has to say it with.
GROUNDED_ANSWER_KEYS = ("answer", "citations")
UNANSWERABLE_REPLY = "NOT IN THE ORDER"

ALLOWED_ORIGINS = ("http://localhost:8080", "https://billing.example.in")
REQUESTS_ALLOWED_PER_WINDOW = 60
RATE_LIMIT_WINDOW_SECONDS = 60
TOKEN_SECRET_ENVIRONMENT_NAME = "METERMIND_TOKEN_SECRET"
DEVELOPMENT_SECRET = "metermind-development-signing-secret-not-for-production"
TOKEN_VALID_MINUTES = 30

ACCOUNT_NUMBER_PATTERN = r"^ACC\d{8}$"
METER_SERIAL_PATTERN = r"^MTR-[A-Z]{2}-\d{6}$"
COMPLAINT_REFERENCE_PATTERN = r"^CMP\d{7}$"
BILLING_PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
EMAIL_ADDRESS_PATTERN = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
