import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import LearningEvent, Assessment, Profile
from services.llm_service import suggest_project

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{user_id}")
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    events = db.query(LearningEvent).filter(LearningEvent.user_id == user_id).all()
    assessments = db.query(Assessment).filter(Assessment.user_id == user_id).all()

    completed = [e for e in events if e.status == "completed"]

    # simple rule-based "behavioral intelligence" — no ML needed for the demo
    last_activity = max((e.timestamp for e in events), default=None)
    days_inactive = (datetime.datetime.utcnow() - last_activity).days if last_activity else None
    nudge = None
    if days_inactive is not None and days_inactive >= 3:
        nudge = f"You've been inactive for {days_inactive} days — pick a quick topic to keep momentum."
    elif not events:
        nudge = "Get started by checking today's tech brief."

    avg_score = round(sum(a.score for a in assessments if a.score is not None) /
                       max(len([a for a in assessments if a.score is not None]), 1), 1)

    return {
        "items_viewed": len(events),
        "items_completed": len(completed),
        "assessments_taken": len(assessments),
        "average_score": avg_score,
        "nudge": nudge,
    }


@router.get("/{user_id}/build-challenge")
def build_challenge(user_id: int, topic: str, db: Session = Depends(get_db)):
    """Turns learning into action — suggests a hands-on project."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    suggestion = suggest_project(topic, profile.current_level, profile.known_skills)
    return {"topic": topic, "project_suggestion": suggestion}
