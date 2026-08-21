# AI Technology Awareness & Learning Companion — MVP

Core loop: **Profile → Daily Brief → Why Care → What's Next → AI Chat → AI Assessment → Dashboard/Build Challenge**

## Setup

```bash
cd techcompanion
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your ANTHROPIC_API_KEY
```

## Run

```bash
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/docs** — interactive Swagger UI to test every endpoint (great for your Round 2 prototype demo, judges can see it live).

## Demo flow (run in this order)

1. **Create a user** — `POST /users/`
   ```json
   { "name": "Asha", "email": "asha@test.com" }
   ```
2. **Update their profile** — `PUT /users/1/profile`
   ```json
   {
     "goal": "Become a backend developer",
     "current_level": "beginner",
     "interests": ["web development", "AI"],
     "known_skills": ["Python basics"]
   }
   ```
3. **Ingest tech news** — `POST /techbrief/ingest` (pulls from RSS, summarizes + tags via LLM)
4. **See the brief** — `GET /techbrief/latest`
5. **Why should I care** — `GET /techbrief/1/why-care/{tech_item_id}` (personalized to Asha)
6. **What's next** — `GET /techbrief/1/whats-next` (ranked recommendations)
7. **Chat with the tutor** — `POST /chat/`
   ```json
   { "user_id": 1, "topic": "REST APIs", "message": "What is a REST API?" }
   ```
8. **Generate a quiz** — `POST /assessment/generate`
   ```json
   { "user_id": 1, "topic": "REST APIs", "num_questions": 3 }
   ```
9. **Submit answers** — `POST /assessment/submit`
10. **Check dashboard** — `GET /dashboard/1`
11. **Get a build challenge** — `GET /dashboard/1/build-challenge?topic=REST APIs`

## Architecture notes (for your pitch deck)

- **DB**: SQLite for MVP (swap `DATABASE_URL` in `.env` for Postgres in production — code doesn't change).
- **LLM layer**: centralized in `services/llm_service.py` — one file, one model, every AI call goes through it.
- **Personalization**: not a separate "engine" — it's one focused prompt (`why_care_and_next`) that takes profile + tech item and returns a structured decision. Simple, explainable, fast to build.
- **Behavior intelligence**: rule-based (inactivity days, score thresholds) — same user-facing value as ML, a fraction of the build risk for a hackathon.
- **What's NOT built yet** (mention as "roadmap" in your pitch, don't over-promise as done): true dependency graph, gamification, auth/login, scheduled ingestion jobs, frontend UI.

## Next build priorities (in order)

1. A minimal frontend (even Jinja templates) so the demo isn't just Swagger docs.
2. Auth (simple JWT) — skip for Round 2, add before Round 3 if time allows.
3. Scheduled ingestion (cron / APScheduler) instead of manual trigger.
4. Cache `why_care_and_next` results per user+item so `/whats-next` isn't calling the LLM 15x on every request.
