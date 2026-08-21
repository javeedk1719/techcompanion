from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Profile, Assessment
from schemas import AssessmentRequest, AssessmentSubmit
from services.llm_service import generate_assessment

router = APIRouter(prefix="/assessment", tags=["ai assessment"])


@router.post("/generate")
def create_assessment(payload: AssessmentRequest, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == payload.user_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    questions = generate_assessment(payload.topic, profile.current_level, payload.num_questions)

    assessment = Assessment(user_id=payload.user_id, topic=payload.topic, questions=questions)
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # strip correct answers before sending to client
    safe_questions = [
        {"question": q["question"], "options": q["options"]} for q in questions
    ]
    return {"assessment_id": assessment.id, "topic": assessment.topic, "questions": safe_questions}


@router.post("/submit")
def submit_assessment(payload: AssessmentSubmit, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == payload.assessment_id).first()
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    correct = 0
    feedback = []
    for i, q in enumerate(assessment.questions):
        chosen = payload.answers[i] if i < len(payload.answers) else -1
        is_correct = chosen == q["correct_index"]
        if is_correct:
            correct += 1
        feedback.append({
            "question": q["question"],
            "your_answer": q["options"][chosen] if 0 <= chosen < len(q["options"]) else "no answer",
            "correct_answer": q["options"][q["correct_index"]],
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    score = round((correct / len(assessment.questions)) * 100, 1)
    assessment.answers = payload.answers
    assessment.score = score
    db.commit()

    # update profile weak/strong topics based on result
    profile = db.query(Profile).filter(Profile.user_id == assessment.user_id).first()
    if profile:
        if score < 60 and assessment.topic not in profile.weak_topics:
            profile.weak_topics = profile.weak_topics + [assessment.topic]
        elif score >= 80 and assessment.topic not in profile.strong_topics:
            profile.strong_topics = profile.strong_topics + [assessment.topic]
        db.commit()

    return {"score": score, "feedback": feedback}
