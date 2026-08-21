from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
import models  # noqa: F401 - ensures models are registered before create_all
from routers import profile, techbrief, chat, assessment, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Technology Awareness & Learning Companion",
    description="Discover -> Understand -> Personalize -> Learn -> Test -> Build -> Adapt",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(techbrief.router)
app.include_router(chat.router)
app.include_router(assessment.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}
