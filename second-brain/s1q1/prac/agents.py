import os 
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).resolve().parent / ".env")


def extract_remediation_items(review: str) -> list[str]:
    prompt = (
        "Identify every remediation or follow-up action arising from the review."
        "Each line should open with the marker FIX: followed by the action"
        "The reply should carry one action per line.Preserve any name, system, deadline and urgency in action"
        "Don't include commentary. If there are no actions return no FIX: \n\n"
        f"Incident review: {review}"
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(model=os.getenv("GEMINI_MODEL"),contents=prompt)

    if response.text is None:
        raise ValueError("Model is not generating the answer what to do")

    return [
        line.strip().removeprefix("FIX:").strip()
        for line in response.text.splitlines()
        if line.strip().startswith("FIX:")
    ]


def assign_engineer_and_priority(task: str, responders: list[str]) -> tuple[str, str]:
    prompt = (
        "Select exactly one engineer from the responder list. Copy the exact engineers name from it."
        "Choose the priority as exactly as HIGH,MEDIUM or LOW."
        "Reply exactly like this ENGINEER:<responder name>\nPRIORITY:<HIGH|MEDIUM|LOW>\n\n"
        f"Action: {task}\nResponders:\n" + "\n".join(responders)
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(model=os.getenv("GEMINI_AI_MODEL"),contents=prompt)

    if response is None:
        raise ValueError("eroooorrrr")

    engineer = ""
    priority = ""

    for line in (response.text or "").splitlines():
        line = line.strip()

        if line.startswith("ENGINEER:"):
            engineer = line[len("ENGINEER:"):].strip()
        elif line.startswith("PRIORITY:"):
            priority = line[len("PRIORITY:"):].strip()

    return engineer, priority