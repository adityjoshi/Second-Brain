import os

import pandas as pd

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

os.system("python3 -m metermind.exception_models.cross_validation")

print("")
print("===== 2. ACCURACY OF EACH MODEL ON EACH OF THE 5 FOLDS =====")
scores = pd.read_csv("output/cross_validation.csv")
table = scores.pivot(index="model", columns="fold", values="accuracy")
print(table.round(4))

print("")
print("===== 3. SUMMARY =====")
summary = pd.DataFrame()
summary["mean"] = table.mean(axis=1)
summary["spread"] = table.max(axis=1) - table.min(axis=1)
summary = summary.sort_values("mean", ascending=False)
print(summary.round(4))

print("")
print("Best model:", summary.index[0])
print("Most stable model:", summary["spread"].idxmin())