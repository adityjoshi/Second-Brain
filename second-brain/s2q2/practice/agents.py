# import os
# from pathlib import Path

# from google import genai
# from dotenv import load_dotenv

# load_dotenv()

# def extract_repair_tasks(report: str) -> list[str]:
#     prompt = (
#         "Return one job per line, each line opening with the marker REPAIR: "
#         f"Inspection Report {report}"
#     )

#     client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#     # fix: env key is GEMINI_MODEL (not GEMINI_MODELS)
#     response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"),contents=prompt)

#     return [
#         line.strip().removeprefix("REPAIR:").strip()
#         # fix: splitlines (not striplines); strip before startswith (bool has no .strip)
#         for line in response.text.splitlines()
#         if line.strip().startswith("REPAIR:")
#     ]



# def assign_technician_and_urgency(task: str, crew: list[str]) -> tuple[str, str]:
#     # fix: join crew outside f-string (backslash inside {} is a SyntaxError on 3.9)
#     crew_list = "\n".join(crew)
#     prompt = (f"""
#         Return exactly two lines.
#         TECHNICIAN: technician name
#         URGENCY: High | Medium | Low
#         Repair task: {task}  # fix: was f{task} (literal "f" before the task)
#         Available crew: {crew_list}
#         """
#     )

#     # fix: use GEMINI_API_KEY to match .env (not GOOGLE_API_KEY)
#     client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#     response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"),contents=prompt)

#     technician = ""
#     urgency = ""
#     for line in (response.text or "").splitlines():
#         # fix: assign strip result so leading spaces don't break label matching
#         line = line.strip()

#         if line.startswith("TECHNICIAN:"):
#             technician = line[len("TECHNICIAN:"):].strip()
#         elif line.startswith("URGENCY:"):
#             urgency = line[len("URGENCY:"):].strip()


#     return technician,urgency


import os 
from google import genai
from dotenv import load_dotenv

load_dotenv()


def extract_repair_tasks(report: str) -> list[str]:
    prompt = (
        "Return one job per line, each line opening with the marker REPAIR: "
        f"Inspection report: {report}"
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"),contents=prompt)

    return [
        line.strip().removeprefix("REPAIR:").strip()
        for line in response.text.splitlines()
        if line.strip().startswith("REPAIR:")
    ]


def assign_technician_and_urgency(task: str, crew: list[str]) -> tuple[str, str]:
    crew_list = "\n".join(crew)
    prompt = (
        f"""
        Return exactly two lines.
        TECHNICIAN: technician name
        URGENCY: High | Medium | Low
        Repair task: {task}  
        Available crew: {crew_list}
        """
        
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"),contents=prompt)

    technician = ""
    urgency = ""

    for line in (response.text or "").splitlines():
        line = line.strip()

        if line.startswith("TECHNICIAN:"):
            technician = line[len("TECHNICIAN:"):].strip()
        elif line.startswith("URGENCY:"):
            urgency = line[len("URGENCY:"):].strip()

    return technician,urgency