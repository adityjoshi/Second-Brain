import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

print("===== NORMAL READING =====")
os.system('printf "ACC10000123\\n3\\n30\\n14208\\n14675\\n340\\n2\\n" | python3 scripts/day01_bill_from_reading.py')
print("-----")
os.system('printf "ACC10000123\\ndomestic\\n3\\n30\\n14208\\n14675\\n0\\n0\\n" | python3 scripts/day02_bill_pricing.py')

print("")
print("===== FAULTY METER: reading went backwards (500 -> 400) =====")
os.system('printf "ACC10000123\\n3\\n30\\n500\\n400\\n0\\n0\\n" | python3 scripts/day01_bill_from_reading.py')
print("-----")
os.system('printf "ACC10000123\\ndomestic\\n3\\n30\\n500\\n400\\n0\\n0\\n" | python3 scripts/day02_bill_pricing.py')

print("")
print("===== ABOVE PHYSICAL LIMIT: 3000 units, max is 2376 =====")
os.system('printf "ACC10000123\\n3\\n30\\n1000\\n4000\\n0\\n0\\n" | python3 scripts/day01_bill_from_reading.py')
print("-----")
os.system('printf "ACC10000123\\ndomestic\\n3\\n30\\n1000\\n4000\\n0\\n0\\n" | python3 scripts/day02_bill_pricing.py')