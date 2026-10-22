import os
from pathlib import Path
import json
from agents import assign_engineer_and_priority, extract_remediation_items
from langchain_core.messages import AIMessage
from state import IncidentState


REVIEW_FILES = Path(__file__).resolve().parent / "data" / "incident_reviews.json"

def load_incident(state: IncidentState) -> dict:
    incident_id = input("enter the id").strip()
    with REVIEW_FILES.open(encoding="utf-8") as f:
        incidents = json.load(f)["incidents"]

    for incident in incidents:
        if incident["incident_id"] == incident_id:
            return{
                "incident_id": incident_id,
                "service": incident["service"],
                "responders": incident["responders"],
                "review": incident["review"],
                "status": "extracting",
                "message": [AIMessage(content=f"Loaded Incident {incident_id}")]
            }

    return {
        "incident_id": incident_id,
        "service": "",
        "responders": [],
        "review": "",
        "status": "completed",
        "message": [AIMessage(content=f" Incident {incident_id} was not found")]
    }


def extract_fixes(state: IncidentState) -> dict:
    if not state["review"]:
        return {
            "tickets":[],
            "status":"completed",
            "message": [AIMessage(content="No review found")]
        }
    tasks = extract_remediation_items(state["review"])
    return {
        "tickets":[{"task":task,"engineer":"","priority":""} for task in tasks],
        "status":"completed",
        "message": [AIMessage(content=f"Extracted {len(tasks)} tickets")]
    }


def assign_engineers(state: IncidentState) -> dict:
    tickets = []

    for ticket in state["tickets"]:
        engineer,priority = assign_engineer_and_priority(state["task"],state["responders"])
        tickets.append({"task":ticket["task"], "engineer":engineer, "priority":priority})
    return {
        "tickets":tickets,
        "message": [AIMessage(content=f"Assigned {len(tickets)} tickets")]
    }

def format_summary(state: IncidentState) -> dict:
    lines = [
        "INCIDENT REMEDIATION SUMMARY",
        "",
        f"Incident ID : {state['incident_id']}",
        f"Service     : {state['service']}",
        f"Responders  : {', '.join(state['responders'])}",
        "",
        f"Tickets ({len(state['tickets'])}):",
    ]
    for index, ticket in enumerate(state["tickets"], start=1):
        lines.append(f"  {index}. [{ticket['priority']}] {ticket['task']}")
        lines.append(f"     Engineer: {ticket['engineer']}")
    return {
        "summary": "\n".join(lines),
        "status": "completed",
        "messages": [AIMessage(content="Incident remediation summary completed.")],
    }