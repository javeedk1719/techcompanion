import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import Base, engine
import models  # noqa: F401 - ensures models are registered before create_all
from routers import profile, techbrief, chat, assessment, dashboard

# Create database tables
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

# Include existing API routers
app.include_router(profile.router)
app.include_router(techbrief.router)
app.include_router(chat.router)
app.include_router(assessment.router)
app.include_router(dashboard.router)

# Serve CSS, JS, images, and static assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the main frontend page at the root route
@app.get("/")
def root():
    return FileResponse(os.path.join("static", "index.html"))
