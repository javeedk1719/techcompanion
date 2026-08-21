from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import TechItem, Profile, LearningEvent
from schemas import TechItemOut, WhyCareOut
from services.ingestion_service import ingest_latest
from services.llm_service import why_care_and_next

router = APIRouter(prefix="/techbrief", tags=["tech brief"])


@router.post("/ingest")
def trigger_ingestion(db: Session = Depends(get_db)):
    """Manually trigger ingestion (in production this would be a scheduled job)."""
    items = ingest_latest(db)
    return {"ingested": len(items)}


@router.get("/latest", response_model=list[TechItemOut])
def latest_items(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(TechItem).order_by(TechItem.created_at.desc()).limit(limit).all()


@router.get("/{user_id}/why-care/{tech_item_id}", response_model=WhyCareOut)
def why_care(user_id: int, tech_item_id: int, db: Session = Depends(get_db)):
    """Personalized 'why should YOU care' — core differentiator vs generic feeds."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    item = db.query(TechItem).filter(TechItem.id == tech_item_id).first()
    if not profile or not item:
        raise HTTPException(404, "Profile or tech item not found")

    profile_dict = {
        "goal": profile.goal, "current_level": profile.current_level,
        "known_skills": profile.known_skills, "interests": profile.interests,
        "weak_topics": profile.weak_topics, "strong_topics": profile.strong_topics,
    }
    result = why_care_and_next(item.title, item.summary, profile_dict)

    # log that the user viewed this — feeds behavior tracking
    db.add(LearningEvent(user_id=user_id, tech_item_id=item.id, status="viewed"))
    db.commit()

    return WhyCareOut(
        tech_item_id=item.id,
        title=item.title,
        why_it_matters=result.get("why_it_matters", ""),
        difficulty_for_you=result.get("difficulty_for_you", ""),
        should_learn_next=result.get("should_learn_next", False),
        reason=result.get("reason", ""),
    )


@router.get("/{user_id}/whats-next", response_model=list[WhyCareOut])
def whats_next(user_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """Ranks recent tech items for this student — the 'what should I learn next' feature."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    profile_dict = {
        "goal": profile.goal, "current_level": profile.current_level,
        "known_skills": profile.known_skills, "interests": profile.interests,
        "weak_topics": profile.weak_topics, "strong_topics": profile.strong_topics,
    }

    items = db.query(TechItem).order_by(TechItem.created_at.desc()).limit(15).all()
    results = []
    for item in items:
        r = why_care_and_next(item.title, item.summary, profile_dict)
        if r.get("should_learn_next"):
            results.append(WhyCareOut(
                tech_item_id=item.id, title=item.title,
                why_it_matters=r.get("why_it_matters", ""),
                difficulty_for_you=r.get("difficulty_for_you", ""),
                should_learn_next=True, reason=r.get("reason", ""),
            ))
        if len(results) >= limit:
            break
    return results
