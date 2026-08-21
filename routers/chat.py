from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Profile, ChatMessage
from schemas import ChatRequest, ChatResponse
from services.llm_service import chat_reply

router = APIRouter(prefix="/chat", tags=["ai chat"])


@router.post("/", response_model=ChatResponse)
def send_message(payload: ChatRequest, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == payload.user_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    profile_dict = {"current_level": profile.current_level, "goal": profile.goal}

    # pull recent history for this user+topic for context
    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == payload.user_id, ChatMessage.topic == payload.topic)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    history = [{"role": h.role, "content": h.content} for h in history_rows]

    reply = chat_reply(payload.topic, profile_dict, history, payload.message)

    # store both turns
    db.add(ChatMessage(user_id=payload.user_id, topic=payload.topic, role="user", content=payload.message))
    db.add(ChatMessage(user_id=payload.user_id, topic=payload.topic, role="assistant", content=reply))
    db.commit()

    return ChatResponse(reply=reply)


@router.get("/{user_id}/{topic}")
def get_history(user_id: int, topic: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id, ChatMessage.topic == topic)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    return [{"role": r.role, "content": r.content, "timestamp": r.timestamp} for r in rows]
