import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

print("===== 1. CLEAN THE READING BOOK =====")
os.system('python3 -c "from config import constants as c; from metermind.data_access.cleaning_pipeline import clean_reading_book as f; print(f(c.READING_BOOK_TRAIN_PATH, c.CLEAN_READING_BOOK_PATH, c.REJECTED_READING_BOOK_PATH))"')

print("")
print("===== 2. WHY WERE ROWS REJECTED =====")
os.system('python3 -c "import pandas as pd; print(pd.read_csv(\'processed_data/readings_rejected.csv\')[\'rejection_reason\'].value_counts().to_string())"')

print("")
print("===== 3. LOAD CLEAN ROWS INTO THE DATABASE =====")
os.system("python3 -m metermind.data_access.database_loader")

print("")
print("===== 4. SQL REPORTS =====")
os.system("python3 -m metermind.data_access.database_reports")
os.system("cat output/reading_reports.csv")

print("")
print("===== 5. ORM TABLES =====")
os.system("python3 -m metermind.api.orm_models")

print("")
