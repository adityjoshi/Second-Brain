# MeterMind — Electricity Billing Detection and Consumer Assistant

## Problem statement

MeterMind is an electricity distribution company that bills twenty-five thousand low-tension connections across five divisions. Every billing cycle a meter reader records a reading, and the company prices it by hand against a tariff order that changes each financial year. Its billing clerks apply the slab table, the fixed charge, the electricity duty and the rebate in whatever order each of them learned, and a reading that cannot have happened is argued over rather than refused. Its vigilance team has no way to rank which of five thousand suspect readings deserves an inspection first, and a case wrongly sent to vigilance costs the company a consumer. Its grievance desk opens every complaint itself, and the wording that decides a bill is published across twelve separate tariff orders, several of which have been superseded while the versions they replaced still govern the cycles billed under them.

The company requires a single platform that prices a reading against the schedule in force, serves that domain over an authenticated web service, sorts suspect readings by what a trained model expects of them, reads incoming complaints without a person opening each one, answers a question out of the tariff order that was actually in force in the billing period asked about, and puts a consumer assistant behind one endpoint that can reach every earlier day as a tool and stop for an inspector when it should.

## Objective

Build the MeterMind platform across thirty-eight days, each day extending what the previous days produced.

Begin with the billing domain in plain Python — the units a meter recorded, the telescopic and non-telescopic slab tables, the fixed charge on the sanctioned load, the electricity duty and the means-tested rebate — and grow it into a package with validated entities and a connection hierarchy. Clean the reading book into a modelling dataset, load it into a database, and expose the domain through a FastAPI service protected by token authentication, role rules and a case status ladder.

Train and compare exception classification models on a shared preparation pipeline, choose a champion by cross-validation, derive three columns the book does not carry, choose an operating rule on cost rather than on accuracy, and sort the flagged readings into the five queues a distribution company works.

Turn the complaint corpus into structured fact: clean it, classify category and urgency with a trained model, score sentences by attention to summarise a thread, and send that summary to a language model for a reading no counting can produce. Extract the account numbers and meter serials a consumer quotes, check them against the register, run the corpus in batch, and escalate the complaints a supervisor must see today.

Index the tariff orders into a ChromaDB vector store with the metadata that dates them, answer questions only from retrieved extracts with every citation resolved, and narrow retrieval to the order in force in the billing period asked about. Finally, wrap four earlier days as tools, drive them with a graph of agents that triage, plan, gather, draft, check and answer, hold a run for an inspector where the platform must not answer alone, and expose the whole assistant as an authenticated endpoint on the service built in weeks two and three.

## File structure

The original document has a file-structure section here. No tree or table was included in the text that was converted.

## Dataset description

Every file below is supplied in the `data` folder, is read only, and is never written to by any day.

### Dataset inventory

Schema tables and sample records were not included in the text that was converted. The descriptions below are the prose that was.

#### `reading_book_train.csv`

The reading book with the exception attached, used to train and compare the models of Weeks 3 to 5. The file is deliberately unclean: it carries four categories the company does not bill at all — `temp`, `misc`, `streetlight` and `industial`, read dates in four different shapes and sometimes not at all, identifiers that fail their published format, cycle lengths no cycle may run, and consumption no sanctioned load could draw. Cleaning it is the task of Week 2 Day 1, after which 28,021 rows survive and 1,979 are rejected with the reason each was rejected for.

#### `reading_book_predict.csv`

The readings waiting to be classified, carrying every column of the training book except `exception_class`, which is the column the model exists to supply. Identifiers run from `RDG30000000`. Week 4 Day 5 sorts these into the five investigation queues.

#### `connection_register.csv`

Every connection on the books, one row each, keyed by account number. Week 6 Day 3 checks against it the account numbers and meter serials a consumer quotes in a complaint.

#### `complaint_messages.csv`

One complaint each, as received. The text carries the quoted reply, the greeting, the sign-off and the signature block a real message carries, and removing them is the task of Week 5 Day 4. Both label columns are used by the classifiers of Week 5 Day 5.

#### `message_threads.csv`

600 complaint threads across 2,693 turns, one row per turn, ordered by turn number within each thread. Week 6 Day 1 summarises a whole thread from these turns.

#### `tariff_orders`

Twelve tariff orders as PDF documents, four financial years by three consumer categories, with two mid-year amendments among them. Their windows tile 2024-04-01 to 2027-03-31 without a gap and without an overlap, so exactly one order is in force for any category on any date. Each carries the same twelve sections, among them ENERGY CHARGE, FIXED CHARGE, ELECTRICITY DUTY, SUBSIDY AND REBATE and UNAUTHORISED USE OF ELECTRICITY.

The inventory table was not included in the text that was converted.

#### `tariff_orders_manifest.json`

A list of twelve entries, one per order. Week 6 Day 5 loads only the documents this file names, and Week 7 Day 3 reads `effective_from` and `effective_to` to decide which order was in force in the period asked about.

#### `retrieval_evaluation_set.json`

148 questions, each with the order and the section that answers it. 37 distinct question-and-category pairs are asked across different billing periods, so the same question has different answers depending on the period, and every one of them is answered by at least two different orders. Week 7 Days 2 and 3 are measured against this file.

---

## Week 1

### Week 1 Day 1

**Module:** `scripts/day01_bill_from_reading.py`

A single script with no functions and no classes, written entirely at the top level of the file. It reads one meter reading from the terminal, prices it against the domestic schedule, prints the figures it derived, and ends with a decision followed by every rule the reading breaks.

The pricing order introduced here — the units the meter recorded, the telescopic slab table, the fixed charge on the sanctioned load, the electricity duty, then the rebate — governs the whole platform. It returns as named functions on Week 1 Day 2, moves into `metermind/core/tariff_calculations.py` on Week 1 Day 3, and is what the service of Week 2 answers with.

**Constants from `config/constants.py`:** none are imported. The schedule this day needs is the one `config/constants.py` already holds, in `SLAB_TABLE_INR_BY_CATEGORY`, `FIXED_CHARGE_INR_PER_KW_BY_CATEGORY`, `ELECTRICITY_DUTY_PERCENT_BY_CATEGORY`, `SUBSIDY_INR_PER_UNIT_BY_CATEGORY` and `SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY`, and the file is supplied pre-loaded, so the figures can be read from it. On this day they are written into the script by hand; from Week 1 Day 3 the platform imports them.

**Signature:** none. The day has no functions and no classes; every statement is written at the top level of the file.

**Parameters:** none. The script takes its seven values from standard input.

**Purpose:** prices one domestic meter reading typed at the terminal and reports the figures it derived, the amount payable, and every reason the reading would be refused.

**Requirements:**

- Read seven values from standard input, one to a line, in this order: `account_number`, `sanctioned_load_kw`, `cycle_days`, `previous_reading`, `current_reading`, `arrears_inr` and `late_payment_surcharge_percent`. Settle `account_number` to upper case with surrounding whitespace removed.
- Hold the domestic schedule by hand: four consumption blocks with their own limits and rates, a fixed charge for each kilowatt sanctioned, an electricity duty as a percentage of the energy charge, a rebate for each unit used where consumption qualifies for it, and the consumption at or under which it qualifies.
- Work out the most a connection of this load could physically draw across the cycle, from the sanctioned load, the hours in a day, the days in the cycle and the allowance a meter is given over its sanctioned load. This figure decides both a rollover and a refusal, so it is derived once.
- Report `units_consumed` as the difference between the two readings where the meter went forward. Where the current reading is below the previous one, the meter has either rolled past its last digit and started again or it has gone backwards, and only the first of those is billable: a rollover is credited when the previous reading plus what the connection could draw would have reached the meter's ceiling, and nothing else is.
- Charge the consumption telescopically: every block is charged at its own rate, and only the units falling inside a block are charged at that block's rate. A cycle of four hundred and sixty-seven units is not four hundred and sixty-seven units at the top rate.
- Report `fixed_charge_inr` from the sanctioned load rather than from the units, so a connection that used nothing still carries it.
- Report `electricity_duty_inr` as the published percentage of the energy charge alone, not of the whole bill.
- The rebate is means-tested by consumption. A cycle at or under the qualifying figure earns the per-unit rebate on every unit it used; a cycle one unit above it earns nothing at all.
- Report `current_demand_inr` as the energy charge plus the fixed charge plus the duty, less the rebate, and never below zero.
- Report the surcharge as the published percentage of the arrears, and `amount_payable_inr` as the current demand plus the arrears plus that surcharge.
- Print one labelled line for each of the nine reported figures, in this order: `account_number`, `units_consumed`, `energy_charge_inr`, `fixed_charge_inr`, `electricity_duty_inr`, the rebate, `current_demand_inr`, the surcharge and `amount_payable_inr`. Units are rounded to one decimal place and every rupee figure to two before printing, and each is printed as the number itself — a figure that rounds to `280.0` prints as `280.0`, not as `280.00`.
- Those nine are the figures the day is judged on. Whatever is worked out along the way to them — the units falling in each block, the physical maximum, the count of broken rules — is named as the writer of the script sees fit, and nothing later in the platform reads any of it.
- Refuse the reading when the meter went backwards without a rollover explaining it, when the consumption is above what the sanctioned load could physically draw, or when the billing cycle is outside the length a cycle may run.
- Print a separate line beginning `Rejected:` for every rule broken, each naming the figure it failed against and the limit it failed, so that the line can be read on its own without the reading beside it.
- Print exactly one closing line: `Reading is billable` where nothing is broken, and a line stating the reading is not billable together with how many reasons were found where something is.

**Returns:** nothing. The result of the day is what the script prints.

**Input:** seven values typed at the terminal, one to a line. No data file is read.

| Name | Type | Meaning |
| --- | --- | --- |
| `account_number` | Text | The connection billed, in the shape `ACC10000000` |
| `sanctioned_load_kw` | Float | The load the connection is sanctioned for, in kilowatts |
| `cycle_days` | Integer | Days in the billing cycle |
| `previous_reading` | Float | What the meter showed at the start of the cycle |
| `current_reading` | Float | What the meter shows now |
| `arrears_inr` | Float | What the account already owes, in rupees |
| `late_payment_surcharge_percent` | Float | The surcharge charged on those arrears, as a percentage |

Console input. The script prints no prompt.

```text
ACC10000123
3
30
14208
14675
340
2
```

A domestic connection of 3 kW read over a 30 day cycle, the meter moving from 14208.0 to 14675.0, against arrears of 340.00 rupees carrying a 2 percent surcharge.

```bash
python3 scripts/day01_bill_from_reading.py
```

```text
Account number: ACC10000123
Units consumed: 467.0
Energy charge: 2575.7
Fixed charge: 150.0
Electricity duty: 128.78
Rebate: 0.0
Current demand: 2854.48
Late payment surcharge: 6.8
Amount payable: 3201.28
Reading is billable
```

The transcript above is the format to produce. The test cases read the figures rather than the lines, so a label worded differently or spaced differently is not a failure — but every figure shown must appear, rounded as stated above and printed as the number itself. One line is read for its wording as well: a refusal of a reading that went backwards has to say so in words a reader can act on.

**Generated files:** none.

### Week 1 Day 2

**Module:** `scripts/day02_bill_pricing.py`

The same pricing as Week 1 Day 1, now expressed as six named calculations and one class rather than as a run of top-level statements, and covering all three consumer categories rather than the domestic one alone.

The class holds the reading and prices it. Its method derives its answer from the six calculations rather than repeating the arithmetic, so a change to a calculation reaches the class without being copied into it. All six calculations move into the package on Week 1 Day 3 and the class is replaced by the connection hierarchy on Week 1 Day 4; the names given here are the names those later days keep.

**Constants declared in the script** (none imported from `config/constants.py`):

| Name | Meaning |
| --- | --- |
| `UNLIMITED_UNITS` | Integer. The upper limit written against a block that has no upper limit, so every block can be held in the same shape |
| `SLAB_RATES_INR` | Dictionary. The block table for each consumer category, each block a pair of an upper limit in units and a rate in rupees a unit. Its keys are also the catalogue of categories the company bills |
| `TELESCOPIC_CATEGORIES` | Tuple. The categories charged block by block. A category not named here is charged the other way |
| `FIXED_CHARGE_PER_KW_INR` | Dictionary. The fixed charge for each kilowatt sanctioned, for the categories billed by kilowatt |
| `FIXED_CHARGE_PER_HORSEPOWER_INR` | Float. The fixed charge for each horsepower, for the category billed by horsepower |
| `HORSEPOWER_PER_KILOWATT` | Float. The conversion between the two |
| `ELECTRICITY_DUTY_PERCENT` | Dictionary. The duty each category carries, as a percentage of the energy charge |
| `REBATE_PER_UNIT_INR` | Dictionary. The rebate each category earns for each unit used, where it qualifies |
| `REBATE_QUALIFYING_UNITS` | Dictionary. The consumption at or under which each category qualifies for its rebate |
| `METER_CEILING_UNITS` | Integer. The reading at which a meter rolls past its last digit and starts again |

The same nine figures appear in `config/constants.py` under the names `SLAB_TABLE_INR_BY_CATEGORY`, `FIXED_CHARGE_INR_PER_KW_BY_CATEGORY`, `FIXED_CHARGE_INR_PER_HORSEPOWER`, `HORSEPOWER_PER_KILOWATT`, `ELECTRICITY_DUTY_PERCENT_BY_CATEGORY`, `SUBSIDY_INR_PER_UNIT_BY_CATEGORY`, `SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY`, `METER_ROLLOVER_UNITS` and `UNLIMITED_UNITS`. The platform starts reading them on Week 1 Day 3.

#### `units_consumed(previous_reading, current_reading, physical_maximum_units)`

- `previous_reading` — float. What the meter showed at the start of the cycle.
- `current_reading` — float. What the meter shows now.
- `physical_maximum_units` — float. The most this connection could physically have drawn across the cycle, worked out by the caller.

Returns the units the cycle used, reading a meter that has rolled past its last digit as a rollover rather than as a mistake.

- Where the meter went forward, the units are the difference between the two readings.
- Where the current reading is below the previous one, two different things may have happened and only one of them is billable. Credit a rollover when the previous reading plus what the connection could physically draw would have reached the meter's ceiling, and count the units the meter recorded on both sides of that ceiling.
- Where no rollover explains it, the meter has gone backwards and the cycle used nothing.

Returns a float, the units consumed.

#### `slab_energy_charge(consumer_category, units)`

- `consumer_category` — text. `domestic`, `commercial` or `agricultural`.
- `units` — float. The units the cycle used.

Returns the energy charge for a cycle, under whichever of the two block conventions the category is billed by.

- A telescopic category is charged block by block: only the units falling inside a block are charged at that block's rate, and every block below is charged at its own.
- A non-telescopic category is charged at one rate: the whole consumption is charged at the rate of the block it lands in. One unit past a block boundary therefore reprices the entire cycle, and that is intended.
- Which convention a category is billed by is decided by `TELESCOPIC_CATEGORIES`, never by the category's name written into the arithmetic.
- A category with one block and one rate must come out the same way under either reading.

Returns a float, the energy charge in rupees.

#### `apply_fixed_charge(consumer_category, sanctioned_load_kw)`

- `consumer_category` — text.
- `sanctioned_load_kw` — float.

Returns the fixed charge the connection carries, from its sanctioned load rather than from what it used.

- Two categories are billed for each kilowatt sanctioned, at their own published rate.
- The agricultural category is billed for each horsepower instead, so the sanctioned load is converted before the rate is applied. Billing an agricultural connection by the kilowatt is a different bill, not a rounding difference.
- A connection that used nothing at all still carries this charge.

Returns a float, the fixed charge in rupees.

#### `apply_electricity_duty(consumer_category, energy_charge_inr)`

- `consumer_category` — text.
- `energy_charge_inr` — float. The energy charge already worked out for the cycle.

Returns the electricity duty the cycle carries.

- The duty is the category's published percentage of the energy charge alone. It is not charged on the fixed charge and it is not charged on the whole bill.
- A category whose published duty is zero carries none.

Returns a float, the duty in rupees.

#### `apply_subsidy(consumer_category, units)`

- `consumer_category` — text.
- `units` — float.

Returns the rebate the cycle earns, which is means-tested by consumption rather than tapered.

- A cycle at or under the category's qualifying consumption earns the per-unit rebate on every unit it used.
- A cycle one unit above that figure earns nothing at all. There is no taper and no partial rebate.
- A category whose qualifying consumption is zero never earns one.

Returns a float, the rebate in rupees.

#### `net_bill_amount(consumer_category, units, sanctioned_load_kw)`

- `consumer_category` — text.
- `units` — float.
- `sanctioned_load_kw` — float.

Returns what the cycle costs, assembled from the four calculations above.

- The four charges are obtained by calling the four calculations above, never by repeating their arithmetic here.
- The energy charge, the fixed charge and the duty are added, and the rebate is taken off.
- A bill is never negative. The agricultural category earns a rebate larger than its tariff, so a small agricultural cycle reaches zero and stops there.

Returns a float, the amount in rupees.

#### Class `MeterReading`

One reading, held as an object, able to price itself. Two members: a constructor and one method.

`__init__(self, account_number, consumer_category, sanctioned_load_kw, cycle_days, previous_reading, current_reading)`

Holds one reading's fields as attributes of the object, under the same names the reading book uses. The six values are held as attributes under the names they were given. The same names are used by the file storage of Week 1 Day 3 and by the entities of Week 1 Day 4.

`price(self)` returns what this reading used and what it costs.

- The most this connection could physically draw across the cycle is worked out from its own sanctioned load, the hours in a day, its own cycle length and the allowance a meter is given over its sanctioned load.
- The units and the amount are obtained by calling `units_consumed` and `net_bill_amount`, not by repeating what they do.

Returns a tuple of two floats: the units consumed, and the amount in rupees.

**Main block:** reads eight values from standard input, prices the reading through the class, and prints seven labelled lines. The block runs only when the file is run directly, so importing the module for its calculations prints nothing.

**Input:** eight values, one to a line. The same seven as Week 1 Day 1, with the consumer category second. `account_number` is settled to upper case; `consumer_category` is settled to lower case.

```text
ACC10000123
domestic
3
30
14208
14675
0
0
```

```bash
python3 scripts/day02_bill_pricing.py
```

```text
Account number: ACC10000123
Consumer category: domestic
Units consumed: 467.0
Energy charge: 2575.7
Fixed charge: 150.0
Current demand: 2854.48
Amount payable: 2854.48
```

Run it a second time with a commercial connection of 30 kW whose meter moved from 99500 to 300 over a 30 day cycle, and the rollover is read as a rollover: the cycle used 800 units, not a negative number.

**Generated files:** none.

### Week 1 Day 3

The platform becomes a package. The pricing written twice as loose statements is moved into it once, under names every later week imports, and the first file is written to disk.

#### `metermind/core/exceptions.py`

The error hierarchy the whole platform raises from. Every failure the platform is allowed to have is one of these, so a caller may catch the parent and be certain nothing else escapes.

| Class | Parent | Purpose |
| --- | --- | --- |
| `MeterMindError` | `Exception` | The parent every error in the platform inherits from. Adds nothing. Catching this one catches every error the platform raises deliberately. Nothing in the platform raises a bare built-in exception where one of these would do |
| `UnsupportedCategoryError` | `MeterMindError` | Raised where a consumer category has no published schedule |
| `ReadingStorageError` | `MeterMindError` | Raised where a reading cannot be written or cannot be found. Both stores of Week 3 Day 1 and the service routes of Week 2 Day 4 raise it |
| `InvalidReadingError` | `MeterMindError` | Raised where a reading cannot be true |

#### `metermind/core/tariff_calculations.py`

The pricing of Week 1 Day 2, moved into the package and reading its figures from `config/constants.py` rather than declaring them. Three functions today; the proration pair arrives on Week 1 Day 5 and the whole module is what Week 2, Week 5 Day 1 and the assistant tool of Week 7 Day 4 price with.

Constants: `METER_ROLLOVER_UNITS`, `SLAB_TABLE_INR_BY_CATEGORY`, `FIXED_CHARGE_INR_PER_KW_BY_CATEGORY`, `FIXED_CHARGE_INR_PER_HORSEPOWER`, `HORSEPOWER_PER_KILOWATT`, `ELECTRICITY_DUTY_PERCENT_BY_CATEGORY`, `SUBSIDY_INR_PER_UNIT_BY_CATEGORY`, `SUBSIDY_QUALIFYING_UNITS_BY_CATEGORY`.

Published in this module: `TELESCOPIC_CATEGORIES` — the categories charged block by block. A category not named here is charged the other way.

`calculate_units_consumed(previous_reading, current_reading, physical_maximum_units)` behaves as `units_consumed` of Week 1 Day 2, with the meter ceiling read from `METER_ROLLOVER_UNITS`. Returns a float.

`calculate_slab_energy_charge(consumer_category, units, blocks=None)`

- A category with no published schedule raises `UnsupportedCategoryError` naming the category. It does not return zero and it does not fall back to another category's table.
- A telescopic category is charged block by block; a non-telescopic category is charged at the single rate of the block its whole consumption lands in. Which convention applies is decided by `TELESCOPIC_CATEGORIES`.
- Where a block table is supplied, it is charged against in place of the published one, under the same convention the category is billed by. Week 1 Day 5 supplies a prorated table.

Returns a float, the energy charge in rupees.

`calculate_bill_amount(consumer_category, units, sanctioned_load_kw)`

- The energy charge comes from `calculate_slab_energy_charge`, never from arithmetic repeated here.
- The fixed charge follows the sanctioned load, by horsepower for the agricultural category and by kilowatt for the others.
- The duty is the category's published percentage of the energy charge alone.
- The rebate is means-tested by consumption exactly as on Week 1 Day 2.
- A bill is never negative.
- This is the one function the rest of the platform prices with. Week 2 Day 4, Week 5 Day 1 and the `calculate_bill` tool of Week 7 Day 4 all answer with what it returns.

Returns a float, the amount in rupees.

#### `metermind/data_access/file_storage.py`

The reading book on disk. One class today, gaining a third method on Week 1 Day 5.

`ReadingFileStorage` reads and writes the reading book as CSV under one directory.

`__init__(self, directory)` holds the folder as a path object, so a caller may supply either a string or a path. The folder is not created here. A storage that has only ever been read from must not leave an empty folder behind.

`save_readings_csv(self, file_name, readings)`

- An empty list raises `ReadingStorageError`. A file with a header and no rows is not what the caller asked for.
- The folder is created if it is not there.
- The header is the column names of the first reading, in the order that reading carries them.
- Returns the path written, so a caller need not rebuild it.

`load_readings_csv(self, file_name)`

- A file that is not there raises `ReadingStorageError` naming the path looked for.
- Every reading comes back as a dictionary keyed by the header row. Every value comes back as text, because that is what a CSV holds; converting them is the caller's business.

Returns a list of dictionaries, one per row.

No demonstration is run on this day. `file_storage.py` gets one on Week 1 Day 5, and `tariff_calculations.py` gets one on Week 2 Day 1. What this day produces is checked by its test cases. This day writes only where a caller asks it to.

### Week 1 Day 4

The class of Week 1 Day 2 becomes a hierarchy. One base class holds everything common to a connection, two subclasses override only what their category bills differently, and a factory returns the right one from a record.

**Module:** `metermind/core/entities.py`

Three classes and one factory. Nothing outside this module decides which class to build; callers hand a record to the factory and are given a connection that already knows how it is billed.

Constants: `CONSUMER_CATEGORIES`, `HOURS_IN_A_DAY`, `CAPACITY_ALLOWANCE_FACTOR`, the tariff figures named on Week 1 Day 3, `MINIMUM_CYCLE_DAYS`, `MAXIMUM_CYCLE_DAYS`.

#### `ServiceConnection`

One connection, able to price itself and to state why it would be refused. This is the domestic connection and the base every other category inherits from. Nine members: a constructor and eight methods.

`__init__(...)` holds the six values and settles two derived figures once.

- A category that is not one of `CONSUMER_CATEGORIES` raises `UnsupportedCategoryError` naming the category. An object that cannot be billed must not be built at all.
- `physical_maximum_units` is derived from the sanctioned load, the hours in a day, the cycle length and the capacity allowance.
- `units_consumed` is derived by calling `calculate_units_consumed`. The arithmetic is not repeated in this module.

| Method | What it does |
| --- | --- |
| `applicable_slab_table` | The table from `SLAB_TABLE_INR_BY_CATEGORY`. Every method that needs the table asks this one, so a subclass overrides one method rather than several |
| `energy_charge_inr` | The base class charges telescopically, against whatever `applicable_slab_table` returns |
| `fixed_charge_inr` | Per kilowatt at the category's published rate. A connection that used nothing still carries it |
| `electricity_duty_inr` | The published percentage of `energy_charge_inr()`. A subclass that changes energy therefore changes the duty without touching this method |
| `subsidy_inr` | Means-tested: the whole consumption earns it at or under the qualifying figure, and nothing earns it above |
| `net_bill_inr` | The four methods above, added and subtracted. Never negative |
| `refusal_reasons` | All three rules, every time. A reading breaking two rules reports two reasons |
| `is_billable` | True exactly when `refusal_reasons` is empty. Derived from that method rather than repeating its checks |

The three refusal rules: a meter that went backwards with no rollover explaining it; consumption above what the sanctioned load could physically draw; a billing cycle shorter or longer than a cycle may run. Each reason is a sentence that can be read on its own. These are the sentences the service returns on Week 2 Day 4. The cleaning pipeline of Week 2 Day 1 publishes its own set in `REJECTION_REASONS`.

#### `CommercialConnection(ServiceConnection)`

Inherits everything and overrides `energy_charge_inr` alone. The whole consumption is charged at the single rate of the block it lands in. One unit past a block boundary reprices the entire cycle. The table is whatever `applicable_slab_table` returns.

#### `AgriculturalConnection(ServiceConnection)`

Overrides `fixed_charge_inr` and `subsidy_inr`.

- Fixed charge: the sanctioned load is converted to horsepower and charged at the published rate for each one.
- Subsidy: there is no qualifying consumption to test against. Every unit earns the rebate.

#### `create_service_connection(record)`

`record` is a dictionary keyed by `account_number`, `consumer_category`, `sanctioned_load_kw`, `cycle_days`, `previous_reading` and `current_reading`.

- The category is settled to lower case with surrounding whitespace removed.
- Each of the three categories maps to its own class. A category outside the three raises `UnsupportedCategoryError` naming it.
- The account number is settled to upper case with surrounding whitespace removed.
- Every numeric field is converted to its type whatever the record supplied it as, because a record read back from CSV supplies every field as text.
- No caller outside this module names a connection class.

Returns a `ServiceConnection`, a `CommercialConnection` or an `AgriculturalConnection`.

**Main block:** prices the same cycle under all three categories.

```bash
python3 -m metermind.core.entities
```

```text
domestic      467 units on a 3 kW connection -> Rs. 2854.48
commercial    467 units on a 3 kW connection -> Rs. 4812.66
agricultural  467 units on a 3 kW connection -> Rs. 0.0
an agricultural cycle costs nothing because the rebate of Rs. 2.6 a unit is larger than the tariff of Rs. 2.25 a unit, and a bill is never negative
```

**Generated files:** none.

### Week 1 Day 5

Three modules gain work: two wrappers that guard a call and time it, the identifier checks the whole platform validates with, the proration a mid-cycle tariff change forces, and a loader that turns rows into connection objects.

#### `metermind/core/decorators.py`

Neither decorator changes what the function it wraps returns.

`reject_negative_readings(wrapped_function)`

- Every argument is examined, whether passed by position or by name.
- A negative number raises `InvalidReadingError` naming the wrapped function and the value. The wrapped function is not called.
- A boolean is not a number for this purpose, even though the language counts it as one. A call carrying `False` must not be refused.
- The wrapper carries the wrapped function's name and documentation forward.
- A call carrying nothing negative returns exactly what the wrapped function returned.

`measure_execution_duration(wrapped_function)`

- The elapsed time of the most recent call is published on the wrapper as `last_duration_seconds`.
- `last_duration_seconds` exists and is zero before the wrapper has ever been called.
- The wrapper returns exactly what the wrapped function returned. It must not return the duration, and it must not return a pair.
- The wrapper carries the wrapped function's name and documentation forward.

Main block: wraps a small function, calls it, and prints both what it returned and what the wrapper timed.

#### `metermind/core/validators.py`

Four checks, each answering yes or no. The service of Weeks 2 and 3, the cleaning of Week 2 Day 1 and the reference extraction of Week 6 Day 3 all validate through these.

Constants: `ACCOUNT_NUMBER_PATTERN`, `METER_SERIAL_PATTERN`, `BILLING_PERIOD_PATTERN`, `EMAIL_ADDRESS_PATTERN`.

Shared rules: the value must match the whole of the published pattern, not merely contain something matching it. Surrounding whitespace is disregarded. A value that is not text returns `False` rather than raising.

| Function | Pattern | Extra rule |
| --- | --- | --- |
| `validate_account_number` | `ACCOUNT_NUMBER_PATTERN` | |
| `validate_meter_serial` | `METER_SERIAL_PATTERN` | |
| `validate_billing_period` | `BILLING_PERIOD_PATTERN` | A month outside the twelve is not well formed |
| `validate_email_address` | `EMAIL_ADDRESS_PATTERN` | Settled to lower case before the check |

#### `metermind/core/tariff_calculations.py` — proration

A tariff order may be replaced part way through a billing cycle, and a cycle spanning two orders is billed against both. Week 2 Day 1 adds a third function, which prices a whole book at once.

`calculate_prorated_slab_limits(blocks, day_share)`

- Every block limit is scaled by the share. A block allowing a hundred units over a whole cycle allows fewer over part of one, or a cycle split in two would receive its allowance twice.
- The rates are never scaled.
- The block that has no upper limit keeps the limit standing for that, unscaled. Scaling a stand-in for infinity produces a smaller stand-in for infinity, which is a different table.

Returns a tuple of pairs, in the order supplied.

`calculate_prorated_energy_charge(consumer_category, units, cycle_days, days_on_the_earlier_order, earlier_blocks, later_blocks)`

- The cycle is split by days, and the consumption is apportioned to each part in the same proportion.
- Each part is charged against its own order's table, with that table's limits scaled by `calculate_prorated_slab_limits`.
- The two parts are added.
- A cycle whose two orders carry the same table must come out at exactly what the whole cycle would have cost on that table alone.

Returns a float, the energy charge in rupees.

#### `metermind/data_access/file_storage.py` — `load_connection_objects`

`load_connection_objects(self, file_name)`

- The rows come from `load_readings_csv`, and each is turned into a connection by `create_service_connection`. Neither is reimplemented here.
- A row the factory will not accept — an unsupported category, a missing column, a figure that will not convert — is passed over and the rest of the book is still returned.
- The order of the file is kept.

Returns a list of connection objects.

Main block: loads `data/reading_book_predict.csv` and prints how many connections were built.

```bash
python3 -m metermind.core.validators
python3 -m metermind.core.decorators
python3 -m metermind.data_access.file_storage
```

```text
account number ACC10000123    well formed: True
account number ACC1           well formed: False
billing period 2026-06        well formed: True
billing period 2026-13        well formed: False
add_up([1, 2, 3]) returned 6 and the wrapper timed it at 0.000001 seconds
connections loaded: 5000
```

**Generated files:** none.

---

## Week 2

### Week 2 Day 1

The whole book is priced in one pass rather than a row at a time, and made fit to be priced first: every row that cannot be true is refused, and the reason it was refused is recorded beside it.

#### `calculate_bill_amounts(book)` in `metermind/core/tariff_calculations.py`

`book` is a DataFrame carrying at least `units_consumed`, `sanctioned_load_kw` and `consumer_category`.

- The whole book is priced without looping over its rows.
- Each category is priced under its own convention, telescopic or otherwise, and its own fixed charge basis, kilowatt or horsepower.
- The rebate is means-tested by consumption for each category as elsewhere.
- The net amount is the energy charge plus the fixed charge plus the duty, less the rebate, and never below zero.
- A row must come out at the same figure this book would have produced one reading at a time through `calculate_bill_amount`.

Returns a Series named `net_bill_inr`, one value per reading, carrying the same index the book was handed with.

#### `metermind/data_access/cleaning_pipeline.py`

Everything the models of Weeks 3 to 5 are fitted on comes out of here.

Published names:

- `REJECTION_REASONS` — eight reasons, in the order they are tested: a required field is empty; the read date could not be read; the billing period is not a year and a month; the consumer category has no tariff schedule; the sanctioned load is not above zero; the billing cycle length is outside the permitted range; the current reading is below the previous reading; the consumption could not be drawn by any load on file. A row is never refused for a reason outside this tuple.
- `REQUIRED_FIELDS` — the nine columns a row must carry a value in before any other rule is applied.
- `READ_DATE_FORMATS` — `%Y-%m-%d`, `%d/%m/%Y`, `%d-%b-%Y`, `%d.%m.%Y`.

Constants: `CONSUMER_CATEGORIES`, `MINIMUM_CYCLE_DAYS`, `MAXIMUM_CYCLE_DAYS`, `HOURS_IN_A_DAY`, `IMPLAUSIBLE_CAPACITY_FACTOR`, `METER_ROLLOVER_UNITS`, `READING_BOOK_TRAIN_PATH`, `CLEAN_READING_BOOK_PATH`, `REJECTED_READING_BOOK_PATH`.

`IMPLAUSIBLE_CAPACITY_FACTOR` is a different question from the capacity allowance of Week 1 Day 4: a reading a little above the sanctioned load is flagged for somebody to look at, and a reading far above it is refused outright.

`parse_read_dates(book)` returns the read date of every row as a real date.

- All four published shapes are tried in order until one succeeds. Rows already read are not attempted again.
- A row whose date matches none of the four comes back empty rather than raising.
- The result keeps the book's own row labels.

`first_broken_rule(row)` — `row` carries the parsed read date in `read_on`.

- Rules are applied in the published order, and the first one broken is the answer. A row breaking three rules is reported against one, so the counts across reasons add back to the rows refused.
- A row missing a value in any of `REQUIRED_FIELDS` is refused before any other rule is tried.
- The last two rules rest on the units this connection could have drawn at `IMPLAUSIBLE_CAPACITY_FACTOR` times its sanctioned load. A backwards meter is explained by a rollover only where that figure would have carried it past `METER_ROLLOVER_UNITS`.
- Every reason returned is a member of `REJECTION_REASONS`, unaltered.

Returns that text, or an empty string.

`clean_reading_book(book_path, clean_path, rejected_path)`

- Every numeric column is converted before any rule is tested, and a value that will not convert becomes empty rather than raising.
- Dates go through `parse_read_dates` and each row through `first_broken_rule`.
- No row is lost. The rows written to the two files add back exactly to the rows read.
- The rejected file carries `rejection_reason`; the clean file does not carry that column.
- Both parent folders are created if they are not there.

Returns a dictionary keyed `kept` and `rejected`.

```bash
python3 -m metermind.core.tariff_calculations
python3 -m metermind.data_access.cleaning_pipeline
```

```text
units consumed: 467.0
energy charge : 2575.7
current demand: 2854.48
a cycle split 14 days on the old order and 16 on the new: 2675.33

kept: 28021 rejected: 1979
```

**Generated files:**

- `processed_data/readings_clean.csv` — the 28,021 rows that survive. Every model day from Week 3 Day 5 onwards is fitted on this file.
- `processed_data/readings_rejected.csv` — the 1,979 rows refused, each carrying the published reason.

### Week 2 Day 2

The clean book moves into a database, and the billing office gets three grouped reports.

#### `metermind/data_access/database_loader.py`

`READINGS_TABLE` is the name of the table this module owns. Every statement names the table through this rather than spelling it. The table is what the reporting of this day, the `look_up_reading` tool of Week 7 Day 4 and the assistant of Week 8 all read.

`ReadingDatabase(database_path)`

- The path is held as text.
- The open connection is an attribute named `connection`, because the reporting module runs its own statements against it.
- Rows come back in a form that can be read by column name.

`create_readings_table(self, book)`

- The table is built from the columns the book carries rather than from a column list written into this module.
- `reading_id` is the primary key.
- Any table left from an earlier load is dropped first.
- Every row is loaded, and the load is committed before the method returns.
- Returns how many rows were loaded.

`find_reading_by_identifier(self, reading_identifier)` returns a dictionary, or nothing where the identifier is not stored. Not finding something is an answer. The identifier is bound as a parameter and never assembled into the statement text.

`delete_reading_by_identifier(self, reading_identifier)` raises `ReadingStorageError` naming an identifier nothing is stored against. The removal is committed. Returns how many rows were removed, which is one.

#### `metermind/data_access/database_reports.py`

Three SQL statements, each declared once: `EXCEPTION_RATE_QUERY`, `ESTIMATED_READ_QUERY`, `BILLED_UNITS_QUERY`. Each groups the readings table, counts what the office asks for, and orders the result so the row that matters most is first. Grouping is done in the database, not in Python.

| Function | Groups by | Returns |
| --- | --- | --- |
| `exception_rate_by_category` | Consumer category | How many cycles were flagged and what share need somebody to look. One row per category, none twice |
| `estimated_read_share_by_month` | Billing period, ordered by it | How many cycles were flagged and what share were billed without a meter reader seeing the meter |
| `billed_units_by_division` | Division | How many cycles were flagged and the units billed. The units column is stored as text and must be read as a number before it is summed |

`write_report_files(database, report_path)` runs all three, writes each under a heading in capitals, followed by its column names, its rows, and a blank line, and returns the path written.

```bash
python3 -m metermind.data_access.database_loader
python3 -m metermind.data_access.database_reports
```

```text
stored: 28021
written: output/reading_reports.csv
```

**Generated files:**

- `database/metermind.sqlite`
- `output/reading_reports.csv`

### Week 2 Day 3

The domain becomes a service. One health route, and a request model that refuses a malformed body before any handler sees it.

#### `metermind/api/schemas.py`

`HealthReply`: required `service` and `status`. The route declares this as its response model.

`ReadingSubmission` is the body a caller submits a reading with, and the parent of the screening request of Week 5 Day 1.

| Field | Rule |
| --- | --- |
| `account_number` | Text |
| `meter_serial` | Text |
| `consumer_category` | Text |
| `billing_period` | Text |
| `sanctioned_load_kw` | Float, above zero and not above five hundred |
| `cycle_days` | Integer, between the published minimum and maximum |
| `previous_reading`, `current_reading` | Float, not below zero and below the meter's ceiling |
| `read_type` | Text, defaults to `actual` |

The four numeric bounds are declared on the fields, so a body breaking one is refused with 422 before any handler runs. A field carrying a default is optional; every other field is required.

Validators, each using the Week 1 Day 5 check rather than rewriting the pattern. A malformed value raises with a message stating the shape expected, in words rather than as the pattern. A well-formed value is returned settled.

- `account_number_is_well_formed` — upper case, whitespace removed.
- `meter_serial_is_well_formed` — the same settling.
- `billing_period_is_well_formed` — a month outside the twelve is refused.

#### `metermind/api/application_factory.py`

`API_PREFIX` — the prefix every route is mounted under.

`SERVICE_NAME` — what the service calls itself in its health reply.

`read_health()` returns a `HealthReply` carrying the published service name and a status saying it is up. It takes nothing, reads nothing and needs no token.

`build_application()` builds a new application on every call. Two calls must not share anything. The health route is mounted under `API_PREFIX`, answers `GET`, and declares `HealthReply` as its response model. Every route the platform ever adds is mounted under `API_PREFIX`. The `database_path` parameter arrives on Week 3 Day 2.

```bash
python3 -m uvicorn "metermind.api.application_factory:build_application" --factory --port 8000
curl -s http://127.0.0.1:8000/api/v1/health
```

```json
{"service":"metermind","status":"up"}
```

The interactive documentation is at `http://127.0.0.1:8000/docs`.

**Generated files:** none.

### Week 2 Day 4

The service gains its first two reading routes, and a store to keep readings in. The pricing behind them is Week 1 Day 4's, called rather than repeated.

#### `InMemoryReadingRepository`

`__init__` starts an empty store. Each store counts its own identifiers. Two stores built in one process must not share either.

`add_reading(self, reading)` — the store assigns the identifier. Identifiers are issued in sequence and never reused. What is returned is a copy.

`get_reading(self, reading_identifier)` raises `ReadingStorageError` naming an unknown identifier, and returns a copy.

`list_readings(self)` returns every reading as a copy, in a new list.

Week 2 Day 5 adds `replace_reading` and `remove_reading`. Week 3 Day 1 puts a published interface above this class.

#### `ReadingReply`

`reading_id`, `account_number`, `consumer_category`, `units_consumed`, `energy_charge_inr`, `fixed_charge_inr`, `net_bill_inr`, `is_billable`, `refusal_reasons`.

A refused reading is answered with this same model, carrying its reasons, rather than with an error.

#### `metermind/api/routers/readings.py`

`router` is tagged so the documentation page groups the routes. `reading_repository` is a module-level name so that `build_application` can replace it on Week 3 Day 2 without any route being edited.

`price_reading(stored_reading)` builds the connection with `create_service_connection` and reads every figure off it. No arithmetic is done here. Units are rounded to one decimal place and every rupee figure to two. Both the decision and the reasons are carried.

`POST /readings` — `submit_reading(submitted_reading: ReadingSubmission)`

- Answers 201 on success.
- A body that fails the model is 422 before this handler is entered.
- An unsupported category is 422 carrying the domain's own message, and is not stored.
- A reading the domain accepts but will not bill is stored and answered with its reasons.

`GET /readings/{reading_identifier}` answers 404 carrying the store's own message when the identifier is absent. The reply is built by `price_reading`.

The readings router is mounted under `API_PREFIX`.

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/readings \
  -H "Content-Type: application/json" \
  -d '{"account_number":"ACC10000123","meter_serial":"MTR-NS-004411",
       "consumer_category":"domestic","billing_period":"2026-06","sanctioned_load_kw":3,
       "cycle_days":30,"previous_reading":14208,"current_reading":14675}'
```

```json
{"reading_id":"RDG40000001","account_number":"ACC10000123","consumer_category":"domestic","units_consumed":467.0,"energy_charge_inr":2575.7,"fixed_charge_inr":150.0,"net_bill_inr":2854.48,"is_billable":true,"refusal_reasons":[]}
```

Fetching `RDG00000000` answers 404. The store keeps readings in memory only. Week 3 Day 1 gives the service a store that survives a restart.

### Week 2 Day 5

Two mapped tables and a session factory. The store and the routes complete their four operations.

#### `metermind/api/orm_models.py`

`ORM_DATABASE_PATH` is not the reporting database of Week 2 Day 2. `Base` is the declarative base. A class inheriting from it registers its table, and the factory creates every registered table at once.

`ConnectionRow` maps to `connections`: `account_number` primary key; `consumer_name`, `consumer_category`, `tariff_code`, `sanctioned_load_kw`, `division`, `subdivision` required; `meter_serial` required and unique. The class is not imported by name anywhere else. It does its work by existing.

`ReadingRow` maps to `readings`: `reading_id` primary key; `account_number` required and indexed; `meter_serial`, `consumer_category` required; `billing_period` required and indexed; `sanctioned_load_kw`, `cycle_days`, `previous_reading`, `current_reading` required; `read_type` required, defaulting to `actual`; `case_status` and `is_billable` optional.

`build_session_factory(database_path)` creates both tables, treats existing tables as success, returns its own factory, and keeps two sessions independent. An object read through a session remains usable after that session is closed.

```bash
python3 -m metermind.api.orm_models
```

```text
tables: ['connections', 'readings']
```

#### Repository and routes

`replace_reading(self, reading_identifier, reading)` raises `ReadingStorageError` when the identifier is absent. A replacement does not create. The identifier is kept. What is returned is a copy.

`remove_reading(self, reading_identifier)` raises `ReadingStorageError` when the identifier is absent, so removing the same reading twice fails the second time.

`PUT /readings/{reading_identifier}` answers 404 when the identifier is absent and 422 when the body is unacceptable. The two are told apart. The reply is the replacement priced.

`DELETE /readings/{reading_identifier}` answers 204 with no body. An absent identifier is 404.

```bash
curl -s -X PUT http://127.0.0.1:8000/api/v1/readings/RDG40000001 \
  -H "Content-Type: application/json" \
  -d '{"account_number":"ACC10000123","meter_serial":"MTR-NS-004411",
       "consumer_category":"domestic","billing_period":"2026-06","sanctioned_load_kw":5,
       "cycle_days":30,"previous_reading":14208,"current_reading":14675}'

curl -s -o /dev/null -w "%{http_code}\n" -X DELETE \
  http://127.0.0.1:8000/api/v1/readings/RDG40000001
```

The delete answers 204.

**Generated files:** `database/metermind_orm.sqlite`. A different file from the reporting database, because that loader rebuilds its table from the clean book on every run.

---

## Week 3

### Week 3 Day 1

A published interface goes above the store, and a second store answers it against the database of Week 2 Day 5. The routes are not edited.

`STORED_READING_FIELDS` — the eleven fields a stored reading carries, whichever store is holding it.

`ReadingRepository(abc.ABC)` declares five abstract operations: `add_reading`, `get_reading`, `replace_reading`, `list_readings`, `remove_reading`. A class implementing only some of them cannot be created. The interface holds no state and no logic.

`InMemoryReadingRepository` now declares `ReadingRepository` as its parent. Its behaviour is unchanged.

#### `SqlReadingRepository(ReadingRepository)`

`__init__(self, database_path=READINGS_DATABASE_PATH)` obtains the session factory from `build_session_factory`.

Each operation answers as the in-memory store answers, including the same `ReadingStorageError` message shape. Writes are committed before the method returns. A field the caller supplied that is not one of the stored fields is not written. `list_readings` orders by identifier, so two calls against an unchanged database answer in the same order.

Nothing in the routes changes. The SQL store is not handed to the service until Week 3 Day 2.

```bash
python3 -m pytest tests.py -q -k week3_day1
```

### Week 3 Day 2

The service is wrapped in the layers every request passes through, told which store to keep readings in, and given password hashing.

`choose_reading_repository(database_path)` returns the in-memory store when handed nothing, and the SQL store when handed a database. Which store is chosen is decided here and nowhere else.

`build_application(database_path="")` sets the chosen store on the readings router's module-level name, adds the rate limiter and the request log, and applies the cross-origin policy. The module's main block opens `ORM_DATABASE_PATH`.

#### `metermind/api/middleware.py`

`REQUEST_LOG_FIELDS`: `received_at`, `method`, `path`, `status_code`, `duration_ms`.

`RequestLogMiddleware` creates the log folder in the constructor. `dispatch` times the request around the call, writes one line of the five fields after the answer is known, and returns the answer untouched. One request writes exactly one line, whether it succeeded or failed.

`FixedWindowRateLimiter` takes `allowed` and `window_seconds` with published defaults. Callers are counted separately. The window is fixed, not rolling. A request past the limit is answered 429 and is not passed down.

`add_cross_origin_policy(application)` allows only the published origins, names the four methods the service answers, permits credentials, and returns the application.

#### `metermind/api/password_hashing.py`

`hasher` is built once at module level.

`hash_password(plain_password)` never returns the password. Hashing the same password twice returns two different hashes, because each carries its own salt. Both still verify.

`verify_password(plain_password, hashed_password)` returns `False` for a wrong password and for a stored value that is not a hash at all.

```bash
python3 -m metermind.api.password_hashing
python3 -m metermind.api.middleware
python3 -m metermind.api.application_factory
```

```text
the stored hash begins: $argon2id$v=19$m=65536,t=3,p=4$... and then a salt that differs every time
the right password verifies : True
a different one does not    : False
fields written for every request: ('received_at', 'method', 'path', 'status_code', 'duration_ms')
60 requests are allowed in each 60 second window
origins the browser may call from: ('http://localhost:3000', 'https://billing.example.in')
```

**Generated files:** `output/logs/requests.log`.

### Week 3 Day 3

A case walks a ladder, only an inspector may move it, and every move is written down.

#### `metermind/api/case_transitions.py`

`ALLOWED_TRANSITIONS` maps all six statuses — `raised`, `assigned`, `inspected`, `regularised`, `billed_back`, `closed_no_fault` — to the statuses each may move to. Three map to nothing, and those are the ends of the ladder.

`move_case_status(current_status, wanted_status)`

- A status the platform does not know raises `MeterMindError` naming it.
- A move the ladder does not allow raises `MeterMindError` stating where the case could have gone, or that it is closed where it could have gone nowhere.
- A permitted move returns the status moved to.
- The ladder goes one way, with one published exception: a case that has been inspected may be sent back to be assigned again.

```bash
python3 -m metermind.api.case_transitions
```

```text
raised               -> assigned             assigned
assigned             -> inspected            inspected
raised               -> closed_no_fault      refused: a case at raised may move to assigned, not to closed_no_fault
```

#### `metermind/api/access_control.py`

`AUDIT_TRAIL_FIELDS`: `recorded_at`, `actor`, `role`, `reading_id`, `from_status`, `to_status`.

`bearer_scheme` is declared not to raise on its own, so a missing token reaches the platform's own handling. Declaring it puts an Authorize button and a padlock on every guarded route in the documentation.

`read_signing_secret()` reads `TOKEN_SECRET_ENVIRONMENT_NAME` and uses `DEVELOPMENT_SECRET` where the environment names none. Both signing and reading go through this function.

`issue_token(subject, role)` carries the subject, the role and an expiry `TOKEN_VALID_MINUTES` ahead, computed against a clock that carries its time zone. The token is signed.

`read_token(token)` raises 401 with a message that says the token could not be read and nothing more. Expired, signed elsewhere, altered or absent are all one answer.

`require_inspector(carried=Depends(bearer_scheme))` answers 401 when there is no readable token and 403, naming the required role, when the role is not `INSPECTOR_ROLE`. A route depending on this receives what the token carried.

`record_audit_entry(...)` appends. The header is written only when the file is being created. The time carries its time zone. The six fields are written in the published order.

`CaseStatusRequest`: `wanted_status`, `noted_by`. Who is moving the case is required, not inferred from the token.

`CaseStatusReply`: `reading_id`, `from_status`, `to_status`, `recorded_by`.

`PATCH /readings/{reading_identifier}/status` depends on `require_inspector`.

- 404 when the store does not hold the reading.
- A case that has never been moved stands at `INITIAL_CASE_STATUS`.
- A move the ladder refuses is 409, carrying the ladder's own message. The body was well formed; the state of the case makes it impossible.
- A permitted move is stored, and only then written to the audit trail.
- The entry carries the person from the body and the role from the token.

**Generated files:** `output/audit_trail.csv`, created by the first accepted move.

### Week 3 Day 4

Accounts, sign-in, and a listing that needs a token and comes back a page at a time.

`require_signed_in` admits any readable token, whatever the role. No token, or one that cannot be read, is 401.

`PagedReadings`: `readings` (list of `ReadingReply`), `page`, `page_size`, `total`. `total` counts what the filters matched, not what this page holds.

#### `metermind/api/routers/user_accounts.py`

`accounts` is a module-level mapping keyed by account number. `CONSUMER_ROLE` is the role an account is given where it names none.

`AccountRequest`: `account_number`, `email_address`, `password`, `role` defaulting to the consumer role. Validators settle the account number as on Week 2 Day 3, and the email through `validate_email_address`, returned in lower case.

`AccountReply`: `account_number`, `email_address`, `role`. The password is not a field, in any form.

`LoginRequest`: `account_number`, `password`.

`TokenReply`: `access_token`, `token_type`, `role`.

`POST /accounts` answers 201. An account number already signed up is 409 and the existing account is not overwritten. What is stored is the hash from `hash_password`.

`POST /accounts/login` checks `verify_password`. An unknown account and a wrong password are answered the same way, with 401 and one message. A correct sign-in returns a token from `issue_token` carrying the account's role.

`GET /readings` takes optional `consumer_category` and `read_type`, `page` at least 1, and `page_size` from 1 to 200, and depends on `require_signed_in`.

- The meter reader who submits a reading needs no token; the book of every reading is not public.
- A page size of ten thousand is 422 before the handler runs.
- A filter not given narrows nothing. Two filters given are both applied.
- `total` counts matches before the page is cut out.
- Two consecutive pages hold no reading in common, and together hold every matched reading.
- Every reading on the page is priced by `price_reading`.

The accounts router is mounted under `API_PREFIX`.

```bash
python3 -m metermind.api.access_control
```

```text
issued: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ...
reads back as: {'sub': 'je/1180', 'role': 'inspector', 'exp': 1786648972}
```

Sign-up and login return the account reply and a bearer token. Listing without a token answers 401; with one, 200. Accounts live for as long as the service runs.

### Week 3 Day 5

The first model. One preparation pipeline, a baseline to beat, and the split every later comparison is made on.

#### `metermind/exception_models/feature_pipeline.py`

`MODELLING_NUMBER_COLUMNS` — ten columns. `MODELLING_CATEGORY_COLUMNS` — five columns. `MODELLING_COLUMNS` is the two together, derived rather than listed again. `EXCEPTION_COLUMN` is the column every model learns.

`build_feature_pipeline()` returns an unfitted column transformer.

- Numeric columns have missing values filled and are then rescaled.
- Categoric columns are widened into indicator columns.
- A category never seen while fitting must not raise when it is met later.
- A category too rare to be worth its own column is grouped rather than given one.
- Returned unfitted, as one object, so a saved model prepares its input the same way.

```text
15 columns in, 30 numbers out
```

#### `metermind/exception_models/baseline_model.py`

`EXCEPTION_CLASSES` is taken from `config/constants.py` and published here. Also `HELD_OUT_SHARE`, `MODEL_SEED`, and the clean-book, model and scores paths.

`split_readings(book)` is stratified by exception class and settled by the published seed. A row is on one side or the other and never on both. Only the modelling columns go into the fitting rows; the class column is carried separately. Returns fitting columns, held-out columns, fitting classes, held-out classes.

`train_baseline_model(fitting_columns, fitting_classes)` holds preparation and decision in one object. The steps are named `prepare` and `decide`. The decision step uses the published seed and is given enough iterations to settle. The model learns all five classes.

`score_exception_model(...)` returns `accuracy` and `per_class`. Accuracy alone is not enough: two of the five classes are rare. A class the model never predicted is scored zero rather than raising.

`save_model` writes the whole fitted object, preparation included. `load_model` must reach exactly the same decisions on the same rows.

`predict_exception(model, readings)` hands over only the published modelling columns. Every class returned is one of the five.

```text
accuracy: 0.7991
```

The accuracy moves a little from one machine to another. No test case pins a score.

**Generated files:** `artifacts/baseline_exception.joblib`, `output/baseline_scores.json`.

---

## Week 4

### Week 4 Day 1

Two more families on the same preparation, and whether the model can read the classes that matter most.

`FITTING_ROUNDS_LIMIT` — how many rounds the baseline is given to settle.

`build_baseline_model(class_weight=None)` returns the baseline unfitted. Building and fitting are separate from today, because Week 4 Day 2 must fit each family five times.

`split_readings(book, columns=None)` splits on the published modelling set when no columns are given. Week 4 Day 3 splits on the widened set through this same function.

`train_baseline_model` now builds through `build_baseline_model`.

#### `metermind/exception_models/tree_models.py`

`build_decision_tree_model(class_weight=None)` limits depth to `DECISION_TREE_DEPTH_LIMIT`, uses the shared preparation, and the published seed.

`build_random_forest_model(class_weight=None)` uses `RANDOM_FOREST_TREE_COUNT` trees, each limited to `RANDOM_FOREST_DEPTH_LIMIT`, fitted on one worker so the result does not depend on how many processors the machine has.

`train_decision_tree` and `train_random_forest` build through those functions and then fit.

`compare_class_weighting(...)` fits the forest twice on the same rows, once weighted and once not. Recall is reported class by class, plus the lowest recall across the five classes. Every published class appears, in the published order. Returns `unweighted` and `balanced`, each holding `recall_by_class` and `lowest_recall`.

```text
artifacts/tree_exception.joblib 0.8676
artifacts/forest_exception.joblib 0.884
```

The forest reading the hardest class at least as well as the single tree is what the day is judged on, not the third decimal.

**Generated files:** `artifacts/tree_exception.joblib`, `artifacts/forest_exception.joblib`.

### Week 4 Day 2

A fourth family, and a comparison that does not rest on one lucky split.

`CROSS_VALIDATION_FIELDS`: `model`, `fold`, `accuracy`.

`build_support_vector_model(class_weight=None)` uses the shared preparation, `SUPPORT_VECTOR_REGULARISATION`, and the published seed. This family reports no confidence, only a decision. Week 4 Day 4 cannot consider it for champion.

`every_candidate_model(class_weight=None)` returns all four families unfitted, keyed by the names the written file and the champion use. Each is built by its own builder.

`cross_validate_models(fitting_columns, fitting_classes, folds=None)`

- Folds are stratified.
- Every family is scored over the same folds, settled by the published seed.
- Fitted on one worker.
- Every fold's score is kept, not only the mean.

Returns a dictionary keyed by family name, each holding a list of one score per fold.

`fold_spread(fold_scores)` is the distance between a family's best and worst folds. Never negative.

`write_cross_validation(scored, where)` writes one row per family per fold. Four families over five folds is twenty rows. Folds are numbered from one.

About thirty seconds: twenty fits.

```text
baseline         mean 0.7236  spread 0.0109
decision_tree    mean 0.8602  spread 0.0105
random_forest    mean 0.8924  spread 0.0074
support_vector   mean 0.7943  spread 0.0158
```

What the day is judged on is the ordering of the families and the shape of the table, not the digits.

**Generated files:** `output/cross_validation.csv`.

### Week 4 Day 3

Three columns the reading book does not carry.

`DERIVED_NUMBER_COLUMNS`: `consumption_ratio_to_average`, `load_factor`, `meter_age_years`.

`WIDENED_MODELLING_COLUMNS` is the published modelling columns plus those three.

`modelling_columns(widened=False)` returns the Week 3 Day 5 set when the derived columns are not wanted.

`build_feature_pipeline(widened=False)`, and every model builder, gains `widened=False` in the same position: `build_baseline_model`, `build_decision_tree_model`, `build_random_forest_model`, `build_support_vector_model` and `every_candidate_model` all become `(class_weight=None, widened=False)`.

`DAYS_IN_A_YEAR` includes the leap quarter.

Each of the first three functions returns a copy. The book handed in is not altered.

- `add_consumption_ratio_to_average` — a cycle equal to the connection's own average comes out at exactly one. A connection with no history is treated as ordinary rather than dropped. This is the column that separates `genuine_high_usage` from everything else.
- `add_load_factor` — units used over the units the sanctioned load could draw. A value above one is physically impossible and points at a tariff mismatch. A very low value points at a meter that has stopped.
- `add_meter_age_years` — span from installation to the end of the cycle, in years. A date that cannot be read leaves the age empty rather than raising.

`widen_readings(book)` calls those three. Exactly three columns are added. The result carries `WIDENED_MODELLING_COLUMNS`.

`measure_feature_lift(book)` fits the same family, seed and split twice. Only the column set differs. Reports `narrow`, `widened` and `lift`, rounded to `MEASUREMENT_DECIMAL_PLACES`. The lift is the difference between the two rounded figures.

```text
narrow   0.885
widened  0.9137
lift     0.0287
```

The lift must be positive, and the three figures must agree with one another.

**Generated files:** `processed_data/readings_widened.csv`, `output/feature_lift.json`.

### Week 4 Day 4

Not every mistake costs the same. The platform chooses its model and its thresholds on cost rather than on accuracy.

`COST_MATRIX` — for every true class, the cost of calling it each of the five. The diagonal is zero. The matrix is not symmetric: calling a genuine high-usage cycle a tamper is the most expensive entry.

`TAMPER_FLOORS` and `FAULT_FLOORS` — the confidence floors the search tries.

`MODELS_THAT_REPORT_CONFIDENCE` — the three families that can carry an operating rule.

`choose_champion(fitting_columns, fitting_classes, folds=None)` scores through `cross_validate_models` and considers only the families that report a confidence. Returns the winner's name and every considered family's mean.

`expected_cost(truth, predicted)` charges each pair at the matrix entry and divides by the count. A perfect prediction costs exactly zero. Different lengths are an error.

`predict_with_rule(model, columns, tamper_floor, fault_floor)`

- Reads confidence across all five classes.
- Where the leading class is one of the two guarded ones and its confidence is below that class's floor, the next most likely class is taken. The row is still classified.
- A class with no floor stands whatever its confidence.
- Floors of zero reproduce exactly what the model would have said unaided.

`choose_operating_rule(model, held_out_columns, held_out_classes)` tries every combination of the published floors on the rows kept back. The pair kept is the cheapest, and it is never dearer than taking the model's own answer, because floors of zero are among those tried. Returns `tamper_floor`, `fault_floor` and `expected_cost`.

`save_champion(model, rule, model_path, rule_path)` writes the model and its rule together. Every figure in the written rule is rounded to the published number of places. A champion saved and reloaded with its rule reaches exactly the same decisions.

About forty seconds.

```text
only the families that report a confidence can carry an operating rule, so the support vector
is not considered:
chosen: random_forest {'baseline': 0.7236, 'decision_tree': 0.8602, 'random_forest': 0.8924}
argmax cost: 0.3129
rule: {'tamper_floor': 0.6, 'fault_floor': 0.0, 'expected_cost': 0.3083}
```

The rule's cost is below the unaided cost.

**Generated files:** `artifacts/champion_exception.joblib`, `output/operating_rule.json`. Read by Week 4 Day 5, Week 5 Days 1 and 2, and the `predict_reading_exception` tool of Week 7 Day 4.

### Week 4 Day 5

The five thousand waiting readings are classified and sorted into the five queues, one file each.

`QUEUES` is taken from `QUEUE_FILE_PATHS`. `QUEUE_BY_DECISION` maps each decided class to where its queue is written. There is one queue for every published class and no class without one.

`sort_into_queues(book, decided)` does not alter the book. Every row lands in exactly one queue. The queue is the class it was decided to be. An empty queue is still present. Each queue's rows are renumbered from zero.

`queue_counts` returns one entry per queue, including empty ones.

`write_queue_files` writes five files, each with a header row whether or not it holds readings.

```text
{'genuine_high_usage': 2342, 'estimated_read': 1253, 'meter_fault': 600, 'tamper_suspected': 273, 'tariff_mismatch': 532}
```

The five counts add to 5,000. The counts themselves move with the model.

| File | Class | Who is sent |
| --- | --- | --- |
| `output/queue_no_action.csv` | `genuine_high_usage` | Nobody |
| `output/queue_meter_reading.csv` | `estimated_read` | A reader |
| `output/queue_metering.csv` | `meter_fault` | The metering team |
| `output/queue_vigilance.csv` | `tamper_suspected` | Vigilance. The operating rule guards this queue most closely |
| `output/queue_billing.csv` | `tariff_mismatch` | Billing reviews the sanctioned load |

---

## Week 5

### Week 5 Day 1

The champion goes behind a route. The two spelling problems the raw book carries are settled at the door.

`ReadingSubmission` gains optional `read_date`.

`spelling_is_settled_at_the_door` lower-cases and strips, then corrects a published misspelling from `CONSUMER_CATEGORY_CORRECTIONS`. A value that is neither a category nor a known misspelling is returned unchanged. The domain refuses it.

`date_is_readable` accepts nothing, because the field is optional. All four shapes Week 2 Day 1 reads are accepted, and what is returned is always the one shape the platform uses. Anything else is refused.

`ScreeningRequest(ReadingSubmission)` adds thirteen fields the champion was fitted on and the three derived columns are built from: `units_consumed`, `twelve_month_average_units`, `same_month_last_year_units`, `consecutive_estimated_reads`, `days_since_actual_read`, `neighbourhood_average_units`, `arrears_inr`, `payment_defaults_last_year`, `seal_check_result`, `meter_make`, `division`, `meter_install_date`, `cycle_end_date`.

`ScreeningReply`: `account_number`, `billing_period`, `exception_class`, `confidence`, `goes_to`.

#### `metermind/api/routers/screening.py`

`champion_model_path` and `operating_rule_path` are module-level so a test can point the route at a champion it fitted. `loaded_champion` starts empty and then holds `model` and `rule`.

`load_champion_once()` reads the model once for the life of the service, together with its rule. No champion is 503: nothing is broken, the platform is not ready.

`POST /screening` depends on `require_signed_in`.

- The reading is widened by `widen_readings`.
- The class is decided by `predict_with_rule` under the saved rule.
- The confidence reported is the confidence in the class that was returned.
- The queue is read from `QUEUE_FILE_PATHS`.
- The class is always one of the five.

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/screening \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"account_number":"ACC10000123","meter_serial":"MTR-NS-004411",
       "consumer_category":"domestic","billing_period":"2026-06","sanctioned_load_kw":5,
       "cycle_days":30,"previous_reading":14208,"current_reading":14675,
       "read_type":"actual","read_date":"2026-07-01","units_consumed":467.0,
       "twelve_month_average_units":180.0,"same_month_last_year_units":195.0,
       "consecutive_estimated_reads":0,"days_since_actual_read":30,
       "neighbourhood_average_units":210.0,"arrears_inr":0.0,
       "payment_defaults_last_year":0,"seal_check_result":"intact","meter_make":"Genus",
       "division":"North","meter_install_date":"2024-08-14","cycle_end_date":"2026-06-30"}'
```

```json
{"account_number":"ACC10000123","billing_period":"2026-06","exception_class":"meter_fault","confidence":0.5374,"goes_to":"queue_metering.csv"}
```

The class and the confidence move with the champion. Without a token the route answers 401. Without the champion files it answers 503.

### Week 5 Day 2

The champion is reported class by class, with the confusion behind it.

`EXCEPTION_REPORT_FIELDS`: `exception_class`, `precision`, `recall`, `support`.

`per_class_scores(truth, predicted)` includes all five classes, in the published order. A class never predicted scores zero. Precision asks, of the readings sent to a queue, how many deserved it. Recall asks, of the readings that deserved it, how many were sent. Supports add back to the rows scored.

`confusion_frame(truth, predicted)` is five by five, both axes labelled in the published order. Each row totals the support of that class. The diagonal over the total is the accuracy, and the table and the overall figure must agree.

`write_exception_report(truth, predicted, where)` writes one row per class and a total row that cannot be read as a sixth class. The total support is the sum. Every figure is rounded to four places. Week 7 Day 4 reads precision out of this file.

The demonstration table reads down the rows for what a reading truly was and across the columns for what the champion called it. The counts move with the champion; the table totalling the rows scored does not.

**Generated files:** `output/exception_report.csv`.

### Week 5 Day 3

Attention, written out. Three functions, no library that does it for them. Nothing else in the platform imports them.

`softmax_rows(scores)` — every row adds to exactly one, and no weight is negative. The largest score in each row is taken off before exponentiation. A row of scores in the hundreds must come back finite. Only the last dimension is turned into weights.

`attention_weights(queries, keys)` — square when queries and keys are the same length, each row adding to one. Scores are scaled by the size of a key before they become weights. The weights come from `softmax_rows`.

`scaled_dot_product_attention(queries, keys, values)` — weights from `attention_weights`. The result is shaped by the values, not by the keys.

```text
every row of a softmax adds to one: [1. 1. 1.]
three positions attending over three, four numbers each -> (3, 4)
```

### Week 5 Day 4

A complaint as received carries a quoted reply, a greeting, a sign-off and a signature block. None of that is the complaint.

Six compiled patterns: `QUOTED_REPLY_PATTERN`, `GREETING_PATTERN`, `SIGN_OFF_PATTERN`, `SIGNATURE_PATTERN`, `COMPLAINT_REFERENCE_PATTERN`, `WHITESPACE_PATTERN`.

| Function | What it removes | What it keeps |
| --- | --- | --- |
| `strip_quoted_reply` | Quoted lines, forwarded headers, and the line introducing a quotation, together with what follows | The consumer's own words |
| `strip_greeting_and_sign_off` | A line that is wholly a greeting or a sign-off | A sentence that merely contains one of those words |
| `strip_signature` | A line that is wholly a contact number or a staff identifier | A number quoted inside a sentence |
| `normalise_whitespace` | Line breaks and runs of spaces | One line, single spaces, ends trimmed |

`clean_message` calls those functions, and also removes the complaint reference, because the corpus already carries it in its own column. A value that is not text is turned into text. No message is emptied.

`clean_messages` returns one cleaned message per input, in order. It is declared at module level, because the classifier pipeline of Week 5 Day 5 carries it as its first step, and a nested function cannot be saved and reloaded.

`clean_corpus` adds `clean_text` and keeps the original. No message is lost. Reports `messages` and `shortest`.

```text
{'messages': 5000, 'shortest': 93}
```

**Generated files:** `processed_data/complaints_clean.csv`.

### Week 5 Day 5

Two classifiers: what the complaint is about, and how quickly it must be answered.

`COMPLAINT_CATEGORIES`: `high_bill`, `no_supply`, `meter_problem`, `connection_request`, `payment_issue`.

`COMPLAINT_URGENCIES`: `routine`, `priority`, `emergency`.

`build_text_pipeline()` — cleaning is the first step, calling `clean_messages`. Terms are weighted, unigrams and bigrams are both counted, a term in fewer than `TEXT_MINIMUM_DOCUMENT_COUNT` messages is dropped, and at most `TEXT_MAXIMUM_FEATURES` terms are kept. The decision step uses `MODEL_SEED`. Returned unfitted.

`split_complaints(corpus, label_column)` is stratified on the label being learned, settled by the published seed, and splits the raw message text.

`train_category_classifier` and `train_urgency_classifier` are built through that pipeline and must beat always naming the commonest label.

`classify_message(category_model, urgency_model, message)` is handed raw text. The category is one of the five and the urgency one of the three.

```text
{'category': 0.938, 'urgency': 0.815}
```

**Generated files:** `artifacts/complaint_category.joblib`, `artifacts/complaint_urgency.joblib`, `output/complaint_scores.json`.

---

## Week 6

### Week 6 Day 1

The sentences that carry a thread are found by the attention of Week 5 Day 3, and nothing is invented.

`SENTENCE_END_PATTERN`, `SHORTEST_SENTENCE_CHARACTERS`. `UnreadableThread` adds nothing to `Exception`.

`split_sentences(thread_text)` splits at sentence-ending punctuation followed by a space, drops fragments shorter than the published length, and settles what remains to single spaces. A thread with nothing long enough returns an empty list.

`sentence_matrix(sentences)` is one row per sentence. The vocabulary is the thread's own words, lower case, trailing punctuation removed, in a settled order. Each row counts how often that sentence uses each word.

`score_sentences(sentences)` raises `UnreadableThread` for fewer than two sentences. Scores come from `attention_weights`, with the sentences attending over themselves. One finite score per sentence.

`summarise_thread(thread_text, sentence_count=None)` returns only sentences the thread contains, word for word, in the order the thread said them. A thread with no sentence long enough raises `UnreadableThread`. A thread with no more sentences than are wanted comes back whole.

`write_thread_summaries` gathers the turns of a thread, cleans each with `clean_message`, and joins them. A thread that cannot be summarised still gets a row, carrying why. Reports `threads`, `summarised` and `not summarised`, and the three must add up.

```text
written: {'threads': 600, 'summarised': 600, 'not summarised': 0}
```

**Generated files:** `output/thread_summaries.csv`. Nobody else in the platform reads it. Escalation works from the corpus itself, because it needs each complaint's own age.

### Week 6 Day 2

The first language model. Answers are cached, and a failure is never quiet. Week 8 Day 2 adds the retry. Everything in Weeks 6 to 8 that speaks to a model speaks through `metermind/message_intelligence/llm_client.py`.

`LanguageModelError` is the parent. `ModelNotConfigured(LanguageModelError)` is raised where no key has been configured, and is told apart from the parent because no number of attempts supplies a missing key.

`load_settings()` reads `.env` into the environment first. A missing or empty key raises `ModelNotConfigured` naming the variable and where to put it. The model name comes from the environment, or `DEFAULT_LANGUAGE_MODEL`.

`cache_key(model_name, prompt)` is a SHA-256 digest. The same prompt against the same model gives the same key; any difference in either gives a different key.

`read_cache` returns an empty dictionary when there is no file yet. A file that cannot be read raises `LanguageModelError`.

`write_cache` creates the parent folder. What is written is read back unchanged.

`open_model_client(api_key)` imports the vendor package inside the function.

`ask_model(prompt, cache_path=LANGUAGE_MODEL_CACHE_PATH)`

- A cache hit is returned without a client being opened, and with no key configured.
- A miss asks the model and the answer is cached before it is returned.
- The client is held for as long as the call takes.
- A failed call raises `LanguageModelError`. It is never answered with a default, a guess or an empty string.
- A model that answers with nothing is also an error.

`read_answer(said, wanted_keys)` finds a JSON object inside a fenced block or a sentence. No object, unreadable JSON, or a missing wanted key raises `LanguageModelError`. A missing key is named.

`.env` must carry `GEMINI_API_KEY` from this day onwards.

```text
cache holds: 4 answers
```

The count is whatever the cache is holding, and is zero before anything has been asked.

**Generated files:** `artifacts/llm_cache.json`.

### Week 6 Day 3

Account numbers and meter serials are found in the text and checked against the register. The two kinds of fault are told apart.

Patterns match only a whole reference, not a fragment inside a longer run of characters.

`EXTRACTED_REFERENCE_FIELDS`: `message_id`, `account_numbers`, `meter_serials`, `complaint_references`, `unknown_accounts`, `serials_on_another_account`.

`find_account_numbers`, `find_meter_serials` and `find_complaint_references` each return every match once, in a settled order, or an empty list. A value that is not text is turned into text. All three kinds are found in one message where one message quotes all three.

`check_against_connection_register(accounts, serials, known_accounts, serial_owner)`

- An account the register has never heard of is one fault.
- A serial standing against a different account is the worse fault, reported separately.
- A serial the register does not carry is neither fault.
- A message quoting a serial but no account cannot have a mismatch.

Returns `unknown_accounts` and `serials_on_another_account`.

`extract_and_check` reads the register once. One row per message, whether or not it quoted anything. Several references in one column are joined so the column can be split back apart. Reports `messages` and `faults`.

```text
{'messages': 5000, 'faults': 1116}
```

**Generated files:** `output/extracted_references.csv`.

### Week 6 Day 4

Five thousand messages run in one batch, and escalation is decided on three signals rather than one.

`BATCH_FAILURE_FIELDS`: `message_id`, `reason`.

`MessageFailure(message_id, reason)` holds both as attributes.

`run_batch(messages, handle_one, failures_path=BATCH_FAILURES_PATH)` returns one result per message, in order. A failure is a `MessageFailure`, and the batch carries on. The failures file has a header even when nothing failed.

`TONE_PROMPT` names the three tones and requires a phrase from the complaint as evidence. `ESCALATION_FIELDS`: `message_id`, `age_days`, `urgency`, `tone`, `escalate`, `signals`.

`complaint_age_days(received_date, today=None)` accepts a supplied day so the answer does not change tomorrow.

`decide_escalation(age_days, urgency, tone)` considers waiting too long, an escalating urgency (`emergency`), and an escalating tone (`angry`). Escalation needs `ESCALATION_SIGNALS_NEEDED`, not one signal. The signals that fired are returned beside the decision. Moving any one of the three must be able to change the decision.

`read_tone` asks through `ask_model` and reads through `read_answer`. A tone the platform does not publish raises `LanguageModelError` naming it. No tone is guessed from keywords.

`escalate_one_message` gets age, urgency, tone and the decision from those four functions, and writes the three signals beside the decision.

`write_escalations` runs through `run_batch`. Reports `decided`, `failed` and `escalated`. The first two add back to the complaints handed in.

```text
handled and returned: 240
MSG000002 failed, and the batch carried on: 'units'
what failed is written to: output/batch_failures.csv
{'decided': 20, 'failed': 0, 'escalated': 3}
```

**Generated files:** `output/batch_failures.csv`, `output/escalations.csv`.

### Week 6 Day 5

Tariff orders are cut into pieces that remember which order and which section they came from. Nothing is searched yet.

`UnreadableOrder` adds nothing to `Exception`.

`read_pdf_text(pdf_path)` raises `UnreadableOrder` when the file is missing and when a file yields no text. Every page is read and joined in order.

`read_manifest` returns the manifest as it stands.

`load_tariff_orders` loads only what the manifest names. Each order comes back with its identifier, title, category, the window it was in force, its section headings and its text. An unreadable named document raises rather than being skipped.

`CHUNK_FIELDS`: `chunk_id`, the text, and `STORED_CHUNK_FIELDS`.

`split_into_chunks(text, size=CHUNK_CHARACTERS, overlap=CHUNK_OVERLAP_CHARACTERS)` — no piece longer than the size, consecutive pieces overlap by the amount asked, an overlap not smaller than the size raises `ValueError`, and a whitespace-only piece is dropped.

`chunk_metadata(order, chunk_text, position)` — the identifier carries the order and the position. The order, title, category and window travel with the piece. The section is the order's own heading where the piece contains one, and empty where it does not.

`write_chunks` gives no two pieces the same identifier. A piece with no heading of its own carries the heading of the piece before it. Reports `orders`, `chunks` and `without_a_section`.

```text
12 orders, 56819 characters of text
{'orders': 12, 'chunks': 84, 'without_a_section': 0}
```

**Generated files:** `processed_data/tariff_chunks.json`. Read by Week 7 Day 1.

---

## Week 7

### Week 7 Day 1

The pieces go into a vector store and are searched by meaning.

`STORE_SETTINGS` states the distance measure rather than leaving it to the default. `SEARCH_RESULT_FIELDS` carries the piece, its text, how far away it was, and the published metadata.

`TariffStoreMissing` adds nothing to `Exception`.

`load_embedder` loads `EMBEDDING_MODEL_NAME`. The same model must build the store and search it.

`build_tariff_store` stores one record per piece, declares the distance measure, carries text and metadata, removes a collection left from an earlier build, and writes to disk.

`open_tariff_store` opens a store that has already been built. No store, or no collection of the published name, raises `TariffStoreMissing`.

`search_tariff` returns the nearest pieces first, across every order, including ones that had ceased to have effect. Week 7 Day 3 exists because of that.

The first run downloads the embedding model, about 90 MB.

```text
84 chunks stored
  0.538  FY2026-27-LT5     ENERGY CHARGE
  0.540  FY2024-25-LT5     ENERGY CHARGE
  0.545  FY2025-26-LT5     ENERGY CHARGE
  0.555  FY2025-26-LT1     ENERGY CHARGE
  0.556  FY2024-25-LT1     ENERGY CHARGE
```

Five orders reached for one domestic question, three of them for a category nobody asked about.

**Generated files:** `database/tariff_store`.

### Week 7 Day 2

The model answers from what was retrieved and from nothing else. Every citation must resolve.

`CITATION_PATTERN`, `ANSWER_FIELDS` (`question_id`, `question`, `answer`, `citations`, `chunks_handed_over`, `refused_because`), and `ANSWER_TEMPLATE`. The template tells the model to use only the extracts, to cite every extract it relies on, and to answer with `UNANSWERABLE_REPLY` where the extracts do not answer the question.

`UngroundedAnswer` adds nothing to `Exception`.

`check_citations(answer_text, chunks)` raises `UngroundedAnswer` naming a citation that was not among the extracts. Resolved citations are returned once, in a settled order.

`build_answer_prompt(question, chunks)` raises `UngroundedAnswer` on an empty extract list. Every handed extract appears, with its identifier, order, section and window. No extract appears that was not handed in.

`answer_from_chunks` builds the prompt, asks through `ask_model`, reads through `read_answer` against `GROUNDED_ANSWER_KEYS`, and checks citations both in the answer text and in the citations field. Returns `answer` and `citations`.

`write_answers` searches, then answers. A question that could not be answered still gets a row, carrying why. Reports `questions`, `answered` and `refused`, and the last two add back to the first.

```text
{'questions': 5, 'answered': 5, 'refused': 0}
```

With no key the search still runs and only the answering refuses.

**Generated files:** `output/tariff_answers.csv`.

### Week 7 Day 3

Retrieval is narrowed to the order that was actually in force.

`search_with_filter(collection, question, embedder, conditions, result_count=SEARCH_RESULT_COUNT)` applies the filter in the store, not after the search. Conditions of nothing search everything, which is how `search_tariff` now behaves. `search_tariff` calls this with no conditions, so there is one search in the module.

`FILTERED_ANSWER_FIELDS`: `question_id`, `question`, `consumer_category`, `billing_period`, `order_in_force`, `answer`, `citations`, `refused_because`.

`NoOrderInForce` adds nothing to `Exception`.

`order_in_force(manifest, consumer_category, billing_period)` returns the one order whose window holds the period, for that category. A period no order covers raises `NoOrderInForce`.

`filtered_search` settles the order first and narrows the search to it. No piece comes back from an order that was not in force, and none from another category.

`write_filtered_answers` answers each question from its own order and writes that order into the row. A question that could not be answered still gets a row. Reports the same three counts as Week 7 Day 2.

```text
nearest, any order at all : ['FY2024-25-LT5', 'FY2025-26-AM-LT1', 'FY2025-26-AM-LT5', 'FY2025-26-LT5', 'FY2026-27-LT5']
nearest, domestic 2024-09 : ['FY2024-25-LT1']
asked about 2019-01       : no domestic order was in force in 2019-01; answering from an order that had ceased to have effect would be worse than not answering
five questions, filtered  : {'questions': 5, 'answered': 5, 'refused': 0}
```

The first three lines need no key. With no key the last line reads `{'questions': 5, 'answered': 0, 'refused': 5}`.

**Generated files:** `output/filtered_answers.csv`.

### Week 7 Day 4

Four earlier days are wrapped as tools. Each declares what it takes, refuses a malformed argument before its body runs, and says what it is for.

`ToolError(MeterMindError)` adds nothing.

Module-level paths, so a test can point the tools at what it built: `readings_database_path`, `champion_model_path`, `operating_rule_path`, `exception_report_path`, `tariff_store_directory`.

`READING_TOOLS` is the only list the assistant of Week 8 may call. `opened_resources` keeps the database, champion, rule, report, store and embedder once opened.

| Model | Fields | Validator |
| --- | --- | --- |
| `ReadingRequest` | `reading_identifier` | |
| `BillRequest` | `consumer_category`, `units_consumed` not below zero, `sanctioned_load_kw` above zero | `a_category_that_is_billed` names the three categories |
| `TariffRequest` | `question`, `consumer_category`, `billing_period` matching `BILLING_PERIOD_PATTERN` | `a_category_with_a_schedule` |

Every field carries a description. The planner of Week 8 Day 1 is shown these names and descriptions.

`look_up_reading` fetches from the Week 2 Day 2 database. An unknown identifier raises `ToolError` naming it.

`calculate_bill` calls `calculate_bill_amount` and rounds to `CURRENCY_DECIMAL_PLACES`. It does no arithmetic of its own. Its description says what it does and what it does not: it says nothing about whether the reading behind the units is trustworthy.

`predict_reading_exception` fetches through `look_up_reading`, widens as Week 4 Day 3 widens, classifies under the saved operating rule, and reads precision from the Week 5 Day 2 report.

`search_tariff_order` goes through `filtered_search`. A period no order covers raises `ToolError` rather than falling back to an unfiltered search. Its description warns against answering a tariff question from memory.

```text
look_up_reading            ['reading_identifier']
calculate_bill             ['consumer_category', 'sanctioned_load_kw', 'units_consumed']
predict_reading_exception  ['reading_identifier']
search_tariff_order        ['billing_period', 'consumer_category', 'question']
```

**Generated files:** none.

### Week 7 Day 5

What travels between the nodes, and the first node: triage. The tool runner arrives on Week 8 Day 1 and the approval gate on Week 8 Day 2.

`ACCUMULATING_CHANNELS`: `steps` and `tool_calls`.

`AssistantState` declares `question`, `consumer_category`, `billing_period`, `category`, `urgency`, `plan`, `answer`, `refusal`, `finished`, `steps`, `tool_calls`. Exactly two channels accumulate. Every other channel is replaced by whichever node last wrote it. A node returning an undeclared channel is silently discarded. Each node appends one word to `steps`, the name it is registered under: `triage`, `plan`, `tools`, `draft`, `critique`, `gate`, `respond`. The state is widened twice in Week 8. Nothing declared today is removed.

`new_assistant_state(question, consumer_category="domestic", billing_period="")` sets the question, starts both accumulating channels as empty lists, and starts the run unfinished.

`loaded_classifiers` keeps the two Week 5 Day 5 classifiers once read. `category_model_path` and `urgency_model_path` are module-level so a test can point the node elsewhere.

`triage_the_question(state)`

- An empty or whitespace question is refused with a reason, and the run is finished. It does not raise.
- Category and urgency come from the classifiers. There is no keyword list.
- Missing classifiers raise `ToolError` naming where they were looked for.
- The node returns only the channels it changed, and records that it ran.

```text
['answer', 'billing_period', 'category', 'consumer_category', 'finished', 'plan', 'question', 'refusal', 'steps', 'tool_calls', 'urgency']
{'question': 'Why is my bill so high this month?', 'consumer_category': 'domestic', 'billing_period': '', 'category': '', 'urgency': '', 'plan': '', 'answer': '', 'refusal': '', 'finished': False, 'steps': [], 'tool_calls': []}
'Why is my bill for June three times the usual amount'   -> {'category': 'high_bill', 'urgency': 'routine', 'steps': ['triage']}
'There has been no supply in our street since last ev'   -> {'category': 'no_supply', 'urgency': 'priority', 'steps': ['triage']}
''                                                       -> {'refusal': 'nothing was asked', 'finished': True, 'steps': ['triage']}
```

**Generated files:** none.

---

## Week 8

### Week 8 Day 1

Two agents and the ordinary code between them: one that chooses which tools to call, one that drafts the reply, and a plain node that dispatches what was chosen.

#### `metermind/assistant/agents.py`

`language_model_cache_path` is module-level. `ASSISTANT_TOOL_ROUNDS` is the most steps a plan may hold.

`PLACEHOLDER_PATTERN` finds the placeholders in a template. `PLANNER_KEYS` and `RESOLVER_KEYS` are the keys each reply must carry.

`TOOL_CATALOGUE` is read off `READING_TOOLS`, not written by hand. Each entry has `does` and `arguments`.

`PLANNER_PROMPT` placeholders, and no others: `catalogue`, `rounds`, `question`, `category`, `urgency`, `consumer_category`, `billing_period`. It requires a JSON object holding `plan` — a list of at most `rounds` steps, each with `tool` and `arguments` — and `reason`. It forbids naming a tool outside the catalogue, requires the exact argument names, tells the model to leave a step out rather than guess, and allows an empty plan.

`RESOLVER_PROMPT` placeholders, and no others: `question`, `tool_calls`. It confines the draft to what the tools returned, forbids working out a figure the tools did not return, and requires the model to say plainly where the tools did not answer. The JSON object holds `draft` and `reason`.

`build_agent_prompt(template, filling)` raises `LanguageModelError` naming a placeholder nothing was supplied for. It does not send a half-written prompt. All four agents use this function.

`plan_tools(state, cache_path=None)` gets the plan from the model and from nowhere else. A plan that is not a list of steps raises `LanguageModelError` saying what came back. The node returns only the channels it changed.

`draft_answer(state, cache_path=None)` rests on the tool results. The reply is read against `RESOLVER_KEYS`. The node returns only the channels it changed.

#### `run_tools(state)` in `nodes.py`

- A plan naming a tool that does not exist is refused before anything runs, names what was asked for, and finishes the run.
- Existing tools are called in the order named.
- A tool that fails is recorded with its error and the run carries on.
- Every call is recorded with the tool, the arguments, and either its result or its error.
- Only tools in the published list may be called.

#### State

`plan` is now a list. `draft` is added as text. Every Week 7 Day 5 channel stays. The two accumulating channels are unchanged.

```text
planner    answers with ('plan', 'reason')       and is told ['catalogue', 'rounds', 'question', 'category', 'urgency', 'consumer_category', 'billing_period']
resolver   answers with ('draft', 'reason')      and is told ['question', 'tool_calls']
```

The planner may name these four tools and no others:

| Tool | Takes |
| --- | --- |
| `look_up_reading` | `reading_identifier` |
| `calculate_bill` | `consumer_category`, `sanctioned_load_kw`, `units_consumed` |
| `predict_reading_exception` | `reading_identifier` |
| `search_tariff_order` | `billing_period`, `consumer_category`, `question` |

The resolver is handed what the tools returned, and nothing else. A new state now includes `draft: ''` and `plan: []`.

**Generated files:** none.

### Week 8 Day 2

The last two agents, the gate, the graph, and the retry.

#### `ask_model_with_retry` in `llm_client.py`

`ask_model_with_retry(prompt, cache_path=LANGUAGE_MODEL_CACHE_PATH, attempts=MODEL_RETRY_ATTEMPTS, pause_seconds=MODEL_RETRY_SECONDS, waits=None)`

- Each wait is longer than the one before it.
- `ModelNotConfigured` is re-raised at once and never retried.
- After the last attempt the failure is raised. Nothing is invented.
- Where a list is supplied for the waits, the waits are recorded in it and not taken.
- The call goes through `ask_model`, so the cache is unchanged in behaviour.

#### Critic and responder

`CRITIC_PROMPT` placeholders: `question`, `tool_calls`, `draft`. The critic may only object. It may not rewrite the draft or answer the question. Worth objecting to: a figure the tools did not return, a statement contradicting what they returned, and an accusation the tools did not establish. JSON holds `veto` and `reason`.

`RESPONDER_PROMPT` placeholders: `question`, `draft`. The reply stays inside the draft, in plain language, without a figure the draft does not carry. JSON holds `reply` and `reason`.

`critique_draft` writes no answer and no draft. An objection is carried as the reason the model gave. Where the model does not object, the objection channel is left empty.

`write_response` is handed the question and the draft, not the tool results. This node finishes the run. It is the only node that finishes a run that was answered.

`plan_tools` and `draft_answer` now ask through `ask_model_with_retry`. Nothing else about either changes.

#### `approval_gate(state)`

The gate never reads the draft's wording.

- A run whose tools read the connection as one of `HELD_EXCEPTION_CLASSES` is held. The other three classes do not hold the run.
- A draft the critic objected to is held, carrying the objection.
- A run that drafted nothing is held.
- Where more than one of these tripped, the hold names all of them.
- A held run still tells the consumer `HELD_FOR_A_PERSON_REPLY`. The hold carries the reason for the inspector. The consumer is not shown the reason.
- An ordinary run is held for nothing and passes through.

#### State

`veto` and `held` are added, both text. Earlier channels stay.

#### `metermind/assistant/graph.py`

`CARRY_ON` is the one route that is not the end.

`ASSISTANT_NODES`, in flow order: `triage`, `plan`, `tools`, `draft`, `critique`, `gate`, `respond`.

`worth_answering(state)` returns the end where the run is finished or carries a refusal, and `CARRY_ON` otherwise. It decides on the state, not by re-reading the question.

`still_going(state)` asks the same question of the state, under a separate name, and is wired at three later branches.

`build_assistant_graph()` registers every node in `ASSISTANT_NODES` and nothing else. The flow enters at triage. After triage, tools, critique and the gate, the run may leave for the end. From plan to tools, from draft to critique, and from the responder to the end, it may not. The graph is returned uncompiled.

```text
the flow, and where it can leave early:
   __start__    -> triage
   critique     -> __end__
   critique     -> gate          only when the run is still going
   draft        -> critique
   gate         -> __end__
   gate         -> respond       only when the run is still going
   plan         -> tools
   tools        -> __end__
   tools        -> draft         only when the run is still going
   triage       -> __end__
   triage       -> plan          only when the run is still going
   respond      -> __end__
   an ordinary run          worth_answering: carry on   still_going: carry on
   a run that has stopped   worth_answering: __end__    still_going: __end__
   a run that was refused   worth_answering: __end__    still_going: __end__
```

The edges are listed in the order the graph holds them, which is not the order the flow runs them.

**Generated files:** none.

### Week 8 Day 3

The graph is compiled against a saver, and the assistant sits behind one authenticated door.

#### `metermind/assistant/workflow.py`

`ASSISTANT_OUTCOME_FIELDS`: `thread_id`, `answer`, `held`, `refusal`, `category`, `urgency`, `steps`, `tools_called`.

`NoSuchThread(MeterMindError)` is raised where a thread was never started, or is not waiting.

`open_saved_graph(threads_path=ASSISTANT_THREADS_PATH)` compiles the graph against a saver and stops it before the node that writes the consumer's reply. The run is written to disk. The directory is created if needed. The connection may be used from more than one thread.

`run_assistant(question, thread_id, consumer_category="domestic", billing_period="", graph=None)`

- Two consumers asking at the same time do not read each other's answers.
- A question starts a new run. Nothing in its place carries on the run already on that thread.
- A run that stopped at the gate and was not held is carried on to the end without anybody being asked. Only a run the gate actually held waits for a person.
- The outcome carries exactly the published fields. Tools are reported by name. A channel the run never set comes back empty.

`release_held_run(thread_id, graph=None)` raises `NoSuchThread` for a thread nobody started and for a thread that is not waiting. The hold is cleared and the run continues from where it stopped. It is not started again from the question.

```text
threads are kept in : database/assistant_threads.sqlite
a run stops before  : respond, so a held one can be picked up there
a run comes back as : ('thread_id', 'answer', 'held', 'refusal', 'category', 'urgency', 'steps', 'tools_called')
an unused thread has: nothing on it and waits at ()
```

#### `metermind/api/routers/assistant.py`

`assistant_threads_path` is module-level. `opened_graph` keeps the compiled graph once, for the life of the service.

The field lists of `AssistantQuestion` and `AssistantReply` were blank in the text that was converted. The requirements that were present:

`AssistantQuestion` refuses an empty question before a thread is started. A question sent with no thread is a new run. A question sent with one carries on that thread.

`AssistantReply` carries exactly `ASSISTANT_OUTCOME_FIELDS`.

`POST /assistant/questions` depends on `require_signed_in`. Any signed-in role may ask. A missing thread id starts a new one, returned in the reply. The reply is the outcome of the run, unchanged. A model that cannot be reached answers 503, carrying why. Returns 200, or 401 without a token, 422 when the question is empty, 503 when the model cannot be reached.

`POST /assistant/threads/{thread_id}/release` depends on `require_inspector`. A thread that is not waiting answers 404, carrying why. A model that cannot be reached answers 503, and the run stays on its thread. Returns 200, or 401, 403, 404, or 503.

The assistant router is mounted under `API_PREFIX`.

```bash
python3 -m metermind.assistant.workflow

curl -s -X POST http://127.0.0.1:8000/api/v1/assistant/questions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"Why is reading RDG20000011 billed at that amount?",
       "consumer_category":"domestic","billing_period":"2025-05","thread_id":"thread-one"}'
```

A question the champion reads as a held class comes back with `answer` set to the published held reply, `held` naming the class, and `steps` ending at `gate` with no `respond`. An inspector releasing that thread gets `held` cleared and the answer written. No token is 401. Releasing a thread nobody started is 404.

**Generated files:** `database/assistant_threads.sqlite`.

---

## Closing

### Output

Thirty-seven of the thirty-eight days print something. Week 1 Day 3 is the one that does not, because none of its three modules carries a demonstration. Fifteen of them write no file at all. They deliver library code a later day calls, or a route that answers over the network, and they are validated by their own test cases and by what the main block prints.

Nothing under `data` or `config` is ever written to. Every generated file lands in `processed_data`, `database`, `artifacts` or `output`, all four of which are supplied empty.

Running `tests.py` also writes into `output` and `database`. Test cases that start the real application install the request log of Week 3 Day 2, and the ones that move a case append to the audit trail of Week 3 Day 3.

### Flow diagram

The original document has a flow diagram here. The diagram itself was not included in the text that was converted.

### Files produced, Week 1 to Week 4

The original document has a files-produced section here. The table was not included in the text that was converted. The generated files named inside each day above are the ones the prose lists.

### Expected output of the running service

The thirty-eight days build one service. This is that service running: started, an account created, a token obtained, a reading submitted that cannot have happened, a reading submitted that can, that reading read back and listed, one that is not on file refused, a case moved along the ladder and then refused going backwards, a screening called without a token and then with one, and the assistant asked a question.

Every one of the fourteen calls goes through the middleware of Week 3 Day 2. The four routes written on Week 2 carry no token, and every route added from Week 3 Day 4 on is declared with the guard it needs.

```bash
python3 -m metermind.api.application_factory
```

`GET /api/v1/health` — 200.

```json
{"service":"metermind","status":"up"}
```

`POST /api/v1/accounts` — 201. The password is never echoed back.

```json
{"account_number":"ACC10000123","email_address":"meena@example.in","role":"inspector"}
```

`POST /api/v1/accounts/login` — 200. The token differs on every sign-in.

`POST /api/v1/readings` with the current reading below the previous — 201. The reading is stored and is not billable. Units are 0.0, energy is 0.0, fixed charge is 150.0, net bill is 150.0, and the refusal says the current reading is below the previous reading and the meter cannot have rolled over.

`POST /api/v1/readings` with the same cycle the right way round — 201. Units 467.0, energy 2575.7, fixed charge 150.0, net bill 2854.48, billable, no refusals. Both replies carry the fixed charge, because that charge is on the sanctioned load.

`GET /api/v1/readings/RDG50000002` — 200, the same reply.

`GET /api/v1/readings?page=1&page_size=2` — 200, `total` 2.

`GET /api/v1/readings/RDG99999999` — 404, `there is no reading RDG99999999`.

`PATCH /api/v1/readings/RDG50000002/status` to `assigned` — 200, inspector only. From `raised` to `assigned`, recorded by `je/1180`.

The same case back to `raised` — 409. A case at `assigned` may move to `inspected` or `closed_no_fault`, not to `raised`.

`POST /api/v1/screening` with no token — 401, `the token could not be read`.

`POST /api/v1/screening` with a token — 200. The first call reads the champion off disk; later screenings answer from the model already in memory. The sample class is `genuine_high_usage` at confidence 0.6514, going to `queue_no_action.csv`. The class moves with the champion.

`POST /api/v1/assistant/questions` with no key in `.env` — 503. The detail says `GEMINI_API_KEY` is not set and to put it in `.env`.

With a key, a question such as "Why is my June bill so high?" for a domestic connection in `2026-06` runs all seven nodes. The sample outcome:

```text
category: high_bill
urgency: routine
steps: triage, plan, tools, draft, critique, gate, respond
tools_called: look_up_reading, calculate_bill, search_tariff_order
held: empty
refusal: empty
```

The sample consumer answer says the specific reading is not available, states the domestic fixed charge of Rs. 50.00 per kilowatt, energy charges with a 5% electricity tax, and a discount of Rs. 1.50 per unit at or under 100 units, and points the consumer at the grievance forum. That run is the platform behaving correctly under a question it cannot fully answer: the question named no reading, so `look_up_reading` was handed an invented identifier and failed, `calculate_bill` was handed a sanctioned load of zero and was refused by its schema, and only `search_tariff_order` answered. The resolver said the readings were not available rather than producing a figure.

`RDG20000011` is a domestic cycle of 560.9 units that the champion reads as `genuine_high_usage`: the tools answer, the draft carries real figures, and the gate lets it through. `RDG20000034` is a domestic cycle of 76.7 units that the champion reads as `tamper_suspected`: the answer is the published held reply, `held` names the class, and `steps` ends at `gate`.

`POST /assistant/threads/{thread_id}/release` — 200, inspector only. `held` is cleared and `respond` is on the end of the steps.

`POST /assistant/threads/nobody-started-this/release` — 404, `there is no run on thread nobody-started-this to release`.

The wording of every model-written line differs between runs. The figures, the tools, the class and the steps do not.

### The service's own record

The request log writes `received_at|method|path|status_code|duration_ms`. The audit trail writes one row per accepted case move. Refusals are logged beside successes. Clock readings, durations, the process number and the token differ on every run.

Sample log and audit lines from the original:

```text
1786648785.787|GET|/api/v1/health|200|2.1
1786648786.119|POST|/api/v1/accounts|201|321.3
1786648786.357|POST|/api/v1/accounts/login|200|226.7
1786648786.457|POST|/api/v1/readings|201|32.4
1786648786.475|POST|/api/v1/readings|201|6.2
1786648786.494|GET|/api/v1/readings/RDG50000002|200|7.4
1786648786.512|GET|/api/v1/readings|200|6.2
1786648786.525|GET|/api/v1/readings/RDG99999999|404|2.7
1786648786.542|PATCH|/api/v1/readings/RDG50000002/status|200|8.4
1786648786.555|PATCH|/api/v1/readings/RDG50000002/status|409|3.5
1786648786.568|POST|/api/v1/screening|401|4.0
1786648797.834|POST|/api/v1/screening|200|784.7
1786648797.935|POST|/api/v1/assistant/questions|503|90.8
1786648797.948|POST|/api/v1/assistant/threads/nobody-started-this/release|404|2.3
```

```text
recorded_at,actor,role,reading_id,from_status,to_status
2026-08-13T19:19:46.541715+00:00,je/1180,inspector,RDG50000002,raised,assigned
```

## Implementation steps

1. Move into the project directory. Every command is run from here, and every path is relative to it: `cd Project`.
2. Install the dependencies. The arithmetic libraries are pinned so the printed figures reproduce: `pip install -r requirements.txt`.
3. Fill `.env` at the project root before any module that reaches the model will run. A free-tier key comes from the Google AI Studio console.

```text
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.1-flash-flash
```

4. Run each day's module as it is written. A script is run by its path and a package module with `-m`, always from the project root.

```bash
python3 scripts/day01_bill_from_reading.py
python3 -m metermind.core.entities
```

5. Run the days in order the first time through. Week 4 Day 5 cannot sort queues before Week 4 Day 4 has saved a champion, and Week 7 Day 2 cannot answer before Week 7 Day 1 has built the store. Week 7 Day 1 downloads the embedding model on its first run, roughly ninety megabytes.
6. Serve the platform: `python3 -m metermind.api.application_factory`.
7. The interactive documentation is at `http://127.0.0.1:8000/docs`. Everything added from Week 3 Day 4 on needs the token the login returns.

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"account_number":"ACC10000123","email_address":"meena@example.in",
       "password":"Chennai#2026","role":"inspector"}'

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/accounts/login \
  -H "Content-Type: application/json" \
  -d '{"account_number":"ACC10000123","password":"Chennai#2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://127.0.0.1:8000/api/v1/assistant/questions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"Why is reading RDG20000011 billed at that amount?",
       "consumer_category":"domestic","billing_period":"2025-05"}'
```

8. Run the test cases. Every day adds between three and five, and the whole file is present from the first day. The whole file runs in under a minute, and reaches one hundred and seventy-eight passing on Week 8 Day 3.

```bash
python3 -m pytest tests.py -v
```

## Final output

Zip: `IP3.zip` (3.1 MB).

The project will not be submitted if "Submit Project" is not done at least once.
