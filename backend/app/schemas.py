from pydantic import BaseModel
from typing import Optional


class LogBody(BaseModel):
    notes: str


class FollowupBody(BaseModel):
    intent: Optional[str] = "move the deal forward"


class OutcomeBody(BaseModel):
    outcome: str
    stage: Optional[str] = None
