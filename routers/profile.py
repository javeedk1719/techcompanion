from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Profile
from schemas import UserCreate, UserOut, ProfileUpdate, ProfileOut

router = APIRouter(prefix="/users", tags=["users & profile"])


@router.post("/", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(400, "User with this email already exists")

    user = User(name=payload.name, email=payload.email)
    db.add(user)
    db.flush()  # get user.id before commit

    profile = Profile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}/profile", response_model=ProfileOut)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile


@router.put("/{user_id}/profile", response_model=ProfileOut)
def update_profile(user_id: int, payload: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
