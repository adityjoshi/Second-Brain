import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

from dotenv import find_dotenv, load_dotenv

path = find_dotenv(usecwd=True)
print("working folder :", os.getcwd())
print(".env found at  :", path or "NOT FOUND")

if path:
    names = []
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            names.append(line.split("=")[0].strip())
    print("names in .env  :", names)

load_dotenv(path)
key = os.environ.get("GEMINI_API_KEY", "").strip()
if key:
    print("GEMINI_API_KEY : set,", len(key), "characters")
else:
    print("GEMINI_API_KEY : EMPTY OR MISSING")