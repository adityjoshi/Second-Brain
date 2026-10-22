
import os 
from pathlib import Path
from dotenv import load_dotenv
from google import genai


load_dotenv(Path(__file__).resolve().parent / ".env")

def extract_repair_tasks(report: str) -> list[str]:

    prompt = (
        "Identify every follow-up job arising from this inspection"
        "Preserve any named location, deadline, and urgency "
        "in each job. Don't invent jobs. Reply with one job per line, each"
        "beginning with REPAIR: followed by the job. Don't include commentary."
        "If there are no jobs,return no REPAIR: lines. \n\n"
        f"Inspection report:\n{report}"
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"),contents=prompt)


    if response.text is None:
        raise ValueError("The extraction model returned no text.")


    return [
        line.strip().removeprefix("REPAIR:").strip()
        for line in response.text.splitlines()
        if line.strip().startswith("REPAIR:")
    ]


def assign_technician_and_urgency(task: str, crew: list[str]) -> tuple[str, str]:

    prompt = (
        "Assign the repair to exactly one technician from the complete crew list."
        "Copy's the technician name exactly as written. Choose the urgency as "
        "HIGH, MEDIUM, or LOW. Reply with exactly two lines:\n"
        "TECHNICIAN:<crew member name>\nURGENCY: <HIGH, MEDIUM, or LOW>\n\n"
        f"REPAIR: {task}\nCrew:\n" + "\n".join(crew)
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"),contents=prompt)

    if response.text is None:
        raise ValueError("This assignment model returned no text.")


    fields = {}

    for line in response.text.splitlines():
        label,seprator, value = line.strip().partition(":")
        if seprator and label in {"TECHNICIAN","URGENCY"}:
            fields["label"] = value.strip()

    if "TECHNICIAN" not in fields or "URGENCY" not in fields:
        raise ValueError("The model reply must include TECHNICIAN: and URGENCY: lines.")

    technician,urgency = fields["TECHNICIAN"], fields["URGENCY"]

    if technician not in crew or urgency not in {"HIGH","MEDIUM","LOW"}:
        raise ValueError("The model returned an invalid technician or urgency.")

    return technician,urgency



