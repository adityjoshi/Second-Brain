import os

import pandas as pd

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

book = pd.read_csv("processed_data/readings_clean.csv")

held = book[book["exception_class"].isin(["tamper_suspected", "tariff_mismatch"])]
normal = book[book["exception_class"] == "genuine_high_usage"]

held_row = held.iloc[0]
normal_row = normal.iloc[0]

print("Readings that should be HELD for an inspector:")
print(held[["reading_id", "exception_class", "consumer_category", "billing_period"]].head(6).to_string(index=False))

print("")
print("A reading that should NOT be held:")
print(normal[["reading_id", "exception_class", "consumer_category", "billing_period"]].head(2).to_string(index=False))

print("")
print("===== JSON for the HELD case: POST /api/v1/assistant/questions =====")
print("{")
print('  "question": "Which exception class is reading ' + held_row["reading_id"] + ' in, and how reliable is that?",')
print('  "consumer_category": "' + held_row["consumer_category"] + '",')
print('  "billing_period": "' + held_row["billing_period"] + '",')
print('  "thread_id": "held-test-1"')
print("}")

# print("")
# print("===== JSON for the NORMAL case =====")
# print("{")
# print('  "question": "Which exception class is reading ' + normal_row["reading_id"] + ' in, and how reliable is that?",')
# print('  "consumer_category": "' + normal_row["consumer_category"] + '",')
# print('  "billing_period": "' + normal_row["billing_period"] + '",')
# print('  "thread_id": "normal-test-1"')
# print("}")