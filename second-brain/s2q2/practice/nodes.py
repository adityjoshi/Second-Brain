# import os 
# import json
# from langchain_core.messages import AIMessage
# from state import InspectionState
# from agents import extract_repair_tasks, assign_technician_and_urgency
# from pathlib import Path

# FILE = Path(__file__).resolve().parent / "data" / "inspection_reports.json"


# def load_inspection(state: InspectionState) -> dict:
#     inspection_id = input("Provide the incident id")
#     with FILE.open(encoding="utf-8") as f:
#         inspections = json.load(f)["inspections"]

#     for inspection in inspections:
#         if inspection["inspection_id"] == inspection_id:
#             return {
#                 "inspection_id": inspection_id,
#                 "property": inspection["property"],
#                 "crew": inspection["crew"],
#                 "report": inspection["report"],
#                 "status": "extracting",
#                 "messages": [AIMessage(content=f"load inspection {inspection_id}")]
#             }
#     return {
#                     "inspection_id": inspection_id,
#                     "property": "",
#                     "crew": [],
#                     "report": "",
#                     "status": "completed",
#                     "messages": [AIMessage(content=f"inspection not found for {inspection_id}")]
#                 }

# def extract_repairs(state: InspectionState) -> dict:
#     if not state["report"]:
#         return {
#             "work_orders": [],
#             "status":"completed",
#             "messages": [AIMessage(content=f"no report found")]
#         }
#     tasks = extract_repair_tasks(state["report"])

#     return {
#           "work_orders": [{"task":task,"technician":"","urgency":""} for task in tasks],
#           "status":"assigning",
#           "messages": [AIMessage(content=f"extracted {len(tasks)} tasks")]
#     }


# def assign_technicians(state: InspectionState) -> dict:
#     orders = []

#     for order in state["work_orders"]:
#         # fix: pass this order's task (state has no "task" field)
#         technician, urgency = assign_technician_and_urgency(order["task"],state["crew"])
#         # fix: key must be "technician" (was mistyped "techinican")
#         orders.append({"task":order["task"],"technician":technician,"urgency":urgency})

#     return {
#         "work_orders": orders,
#         "messages": [AIMessage(content=f"Assigned {len(orders)} orders")]
#     }

# def format_summary(state: InspectionState) -> dict:
#     # fix: join crew outside f-string (nested quotes broke the f-string)
#     crew_names = ", ".join(state["crew"])
#     lines = [
#         "PROPERTY REPORT",
#         f"Inspection ID: {state['inspection_id']}",
#         f"Property: {state['property']}",
#         f"Crew List: {crew_names}",
#         "",
#         f"Work Orders ({len(state['work_orders'])})"
#     ]

#     for index, order in enumerate(state["work_orders"],start=1):
#         lines.append(f" {index}. [{order['urgency']}] {order['task']}")
#         lines.append(f"    Technician: {order['technician']}")

#     return {
#         "summary": "\n".join(lines),
#         "status": "completed",
#         "messages": [AIMessage(content=f"Property repair summary completed")]
#     }


import json 
from langchain_core.messages import AIMessage
from agents import assign_technician_and_urgency, extract_repair_tasks
from state import InspectionState

FILE_PATH = "data/inspection_reports.json"

def load_inspection(state: InspectionState) -> dict:
    inspection_id = input("Inspection id")

    with open(FILE_PATH, encoding="utf-8") as f:
        inspections = json.load(f)["inspections"]

    for inspection in inspections:
        if inspection["inspection_id"] == inspection_id:
            return {
                "inspection_id": inspection_id,
                "property": inspection["property"],
                "crew": inspection["crew"],
                "report": inspection["report"],
                "status": "extracting",
                "messages": [AIMessage(content=f"Loaded inspection {inspection_id}.")],
            }
    return {
        "inspection_id": inspection_id,
         "property": "",
         "crew": [],
         "report": "",
         "status": "completed",
         "messages": [AIMessage(content=f"Inspection {inspection_id} was not found.")],       
    }   

def extract_repairs(state: InspectionState) -> dict:
    if not state["report"]:
        return {
            "work_orders": [],
            "status": "completed",
            "messages": [AIMessage(content="No inspection report to process.")],            
        }
    tasks = extract_repair_tasks(state["report"])

    return {
        "work_orders": [{"task":task,"technician": "", "urgency": ""} for task in tasks],
        "status": "assigning",
                "messages": [AIMessage(content=f"Extracted {len(tasks)} work orders.")],
    }


def assign_technicians(state: InspectionState) -> dict:
    orders = []

    for order in state["work_orders"]:
        technician, urgency = assign_technician_and_urgency(order["task"], state["crew"])
        orders.append({"task":order["task"],"technician":technician,"urgency":urgency})

    return {
        "work_orders":orders,
        "messages": [AIMessage(content=f"Assigned {len(orders)} work orders.")],

    }

def format_summary(state: InspectionState) -> dict:
    lines = [
        "PROPERTY REPAIR SUMMARY",
        "",
        f"Inspection ID : {state['inspection_id']}",
        f"Property      : {state['property']}",
        f"Crew          : {', '.join(state['crew'])}",
        "",
        f"Work Orders ({len(state['work_orders'])}):",
    ]

    for index,order in enumerate(state["work_orders"]):
        lines.append(f" {index}. [{order['urgency']}] {order['task']}")
        lines.append(f"    Technician: {order['technician']}")


    return {
        "summary":"\n".join(lines),
        "status":"completed",
        "messages":[AIMessage(content="Property repair summary completed.")],
    }
