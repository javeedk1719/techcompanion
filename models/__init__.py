import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Text
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    learning_events = relationship("LearningEvent", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    assessments = relationship("Assessment", back_populates="user")


class Profile(Base):
    """Everything the AI knows about the student — drives all personalization."""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    goal = Column(String, default="")                 # e.g. "Become a backend developer"
    current_level = Column(String, default="beginner")  # beginner / intermediate / advanced
    interests = Column(JSON, default=list)             # ["web dev", "AI"]
    known_skills = Column(JSON, default=list)          # ["Python", "SQL"]
    weak_topics = Column(JSON, default=list)           # updated after assessments
    strong_topics = Column(JSON, default=list)
    available_time_per_day = Column(String, default="1 hour")
    resource_preference = Column(String, default="articles")  # articles/video/hands-on

    user = relationship("User", back_populates="profile")


class TechItem(Base):
    """A single piece of tech news / topic ingested by the system."""
    __tablename__ = "tech_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, default="")
    source = Column(String, default="")
    url = Column(String, default="")
    difficulty = Column(String, default="beginner")     # beginner/intermediate/advanced
    tags = Column(JSON, default=list)                   # ["python", "backend"]
    prerequisites = Column(JSON, default=list)           # simple tag-based, e.g. ["REST APIs"]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class LearningEvent(Base):
    """Tracks a student's interaction with a tech item — powers dashboard + behavior nudges."""
    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tech_item_id = Column(Integer, ForeignKey("tech_items.id"))
    status = Column(String, default="viewed")  # viewed / in_progress / completed / skipped
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="learning_events")
    tech_item = relationship("TechItem")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String, default="")
    role = Column(String)   # "user" or "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String)
    questions = Column(JSON)     # list of {question, options, correct_index}
    answers = Column(JSON, default=list)  # student's submitted answers
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="assessments")
