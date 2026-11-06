import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from config import constants
from metermind.api.access_control import require_inspector, require_signed_in
from metermind.assistant.workflow import (
    ASSISTANT_OUTCOME_FIELDS,
    NoSuchThread,
    open_saved_graph,
    release_held_run,
    run_assistant,
)
from metermind.message_intelligence.llm_client import LanguageModelError

assistant_threads_path = constants.ASSISTANT_THREADS_PATH
opened_graph = {}

router = APIRouter(tags=["assistant"])


class AssistantQuestion(BaseModel):
    question: str
    consumer_category: str = "domestic"
    billing_period: str = ""
    thread_id: Optional[str] = None

    @field_validator("question")
    @classmethod
    def question_is_present(cls, given):
        text = str(given or "").strip()
        if not text:
            raise ValueError("a question is required")
        return text


class AssistantReply(BaseModel):
    thread_id: str
    answer: str
    held: str
    refusal: str
    category: str
    urgency: str
    steps: list
    tools_called: list


def _graph():
    current = opened_graph.get("graph")
    if current is None or getattr(current, "threads_path", None) != str(assistant_threads_path):
        current = open_saved_graph(assistant_threads_path)
        opened_graph["graph"] = current
    return current


def _unavailable(error):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(error),
    ) from error


@router.post("/assistant/questions", response_model=AssistantReply)
def ask_assistant(asked: AssistantQuestion, carried=Depends(require_signed_in)):
    thread_id = (asked.thread_id or "").strip() or str(uuid.uuid4())
    try:
        outcome = run_assistant(
            asked.question,
            thread_id,
            consumer_category=asked.consumer_category,
            billing_period=asked.billing_period,
            graph=_graph(),
        )
    except LanguageModelError as error:
        _unavailable(error)
    return AssistantReply(**{field: outcome[field] for field in ASSISTANT_OUTCOME_FIELDS})


@router.post("/assistant/threads/{thread_id}/release", response_model=AssistantReply)
def release_assistant_thread(thread_id: str, carried=Depends(require_inspector)):
    try:
        outcome = release_held_run(thread_id, graph=_graph())
    except NoSuchThread as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except LanguageModelError as error:
        _unavailable(error)
    return AssistantReply(**{field: outcome[field] for field in ASSISTANT_OUTCOME_FIELDS})
