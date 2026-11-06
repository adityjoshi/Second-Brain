import time
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/api/v1/health"

counts = {}
first_429 = None
start = time.time()

for number in range(1, 71):
    try:
        code = urllib.request.urlopen(URL).status
    except urllib.error.HTTPError as error:
        code = error.code
    counts[code] = counts.get(code, 0) + 1
    if code == 429 and first_429 is None:
        first_429 = number
    print(number, code)

print("")
print("Took", round(time.time() - start, 1), "seconds")
print("Results:", counts)
print("First blocked request:", first_429)