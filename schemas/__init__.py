from pydantic import BaseModel
from typing import List, Optional


class UserCreate(BaseModel):
    name: str
    email: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    goal: Optional[str] = None
    current_level: Optional[str] = None
    interests: Optional[List[str]] = None
    known_skills: Optional[List[str]] = None
    available_time_per_day: Optional[str] = None
    resource_preference: Optional[str] = None


class ProfileOut(BaseModel):
    goal: str
    current_level: str
    interests: List[str]
    known_skills: List[str]
    weak_topics: List[str]
    strong_topics: List[str]
    available_time_per_day: str
    resource_preference: str
    class Config:
        from_attributes = True


class TechItemOut(BaseModel):
    id: int
    title: str
    summary: str
    source: str
    url: str
    difficulty: str
    tags: List[str]
    prerequisites: List[str]
    class Config:
        from_attributes = True


class WhyCareOut(BaseModel):
    tech_item_id: int
    title: str
    why_it_matters: str
    difficulty_for_you: str
    should_learn_next: bool
    reason: str


class ChatRequest(BaseModel):
    user_id: int
    topic: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class AssessmentRequest(BaseModel):
    user_id: int
    topic: str
    num_questions: int = 5


class AssessmentSubmit(BaseModel):
    assessment_id: int
    answers: List[int]  # index of chosen option per question
