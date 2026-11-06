import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

os.system('python3 -m uvicorn "metermind.api.application_factory:build_application" --factory --port 8000 --root-path /proxy/8000')


"""
{
  "account_number": "ACC10000123",
  "meter_serial": "MTR-NS-004411",
  "consumer_category": "domestic",
  "billing_period": "2026-06",
  "sanctioned_load_kw": 3,
  "cycle_days": 30,
  "previous_reading": 14208,
  "current_reading": 14675,
  "read_type": "actual",
  "read_date": "2026-07-01"
}
python3 -m metermind.exception_models.champion_model
"""