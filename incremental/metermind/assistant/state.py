import operator
from typing import Annotated, List, TypedDict

ACCUMULATING_CHANNELS = ("steps", "tool_calls")


class AssistantState(TypedDict):
    question: str
    consumer_category: str
    billing_period: str
    category: str
    urgency: str
    plan: list
    draft: str
    answer: str
    refusal: str
    veto: str
    held: str
    finished: bool
    steps: Annotated[List[str], operator.add]
    tool_calls: Annotated[List[dict], operator.add]


def new_assistant_state(question, consumer_category="domestic", billing_period=""):
    return {
        "question": question,
        "consumer_category": consumer_category,
        "billing_period": billing_period,
        "category": "",
        "urgency": "",
        "plan": [],
        "draft": "",
        "answer": "",
        "refusal": "",
        "veto": "",
        "held": "",
        "finished": False,
        "steps": [],
        "tool_calls": [],
    }


if __name__ == "__main__":
    print(sorted(AssistantState.__annotations__))
    print(new_assistant_state("Why is my bill so high this month?"))
