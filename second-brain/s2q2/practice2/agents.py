import os 
from google import genai
from dotenv import load_dotenv

load_dotenv()


def extract_repair_tasks(report: str) -> list[str]:
    prompt = (
        "Return one job per line, each line opening with the marker REPAIR: "
        f"Inspection report: {report}"
    )

    client = genai.clinet(api_key=os.getenv("GEMINI_API_KEY"))

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

    client = genai.clinet(api_key=os.getenv("GEMINI_API_KEY"))
    
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