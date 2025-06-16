# app/schemas.py
from pydantic import BaseModel, Field
from typing import List

class HistoricalTask(BaseModel):
    task_id: str = Field(..., example="T0001")
    user_id: str = Field(..., example="U0001")
    success: bool = Field(..., example=True)
    skills_used: List[str] = Field(..., example=["python", "docker"])

class QualifiedUser(BaseModel):
    user_id: str = Field(..., example="U0001")
    match_score: float = Field(..., example=95.5)
    available_capacity: int = Field(..., example=2)

class AssignmentDecision(BaseModel):
    user_id: str = Field(..., example="U0001")
    reason: str = Field(..., example="Best skill match and availability")
    confidence: float = Field(..., example=0.95)
