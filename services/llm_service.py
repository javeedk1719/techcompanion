"""
Central place for all LLM calls. Keeping this in one file means:
- easy to swap models/providers later
- easy to demo "here's our AI reasoning layer" in Round 1/2
"""
import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"  # swap for whichever model you have access to


def _call(system: str, user: str, max_tokens: int = 1000) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def _call_json(system: str, user: str, max_tokens: int = 1000) -> dict:
    """Forces the model to return parsable JSON only."""
    system_json = system + "\n\nRespond with ONLY valid JSON. No markdown, no backticks, no preamble."
    raw = _call(system_json, user, max_tokens)
    raw = raw.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def summarize_and_tag(raw_title: str, raw_content: str) -> dict:
    """Used by ingestion pipeline: turns raw scraped content into a clean TechItem."""
    system = (
        "You are a technology news editor for a learning platform. "
        "Given a raw tech news item, produce a clean summary, difficulty level, and tags."
    )
    user = f"""Title: {raw_title}
Content: {raw_content}

Return JSON with keys:
- summary (2-3 sentences, plain language)
- difficulty ("beginner", "intermediate", or "advanced")
- tags (list of 2-5 lowercase tech keywords)
- prerequisites (list of 0-3 prerequisite skills/topics needed to understand this)
"""
    return _call_json(system, user)


def why_care_and_next(tech_title: str, tech_summary: str, profile: dict) -> dict:
    """The core personalization call: 'why should YOU care about this?'"""
    system = (
        "You are an AI learning companion that personalizes technology recommendations "
        "for a specific student based on their profile. Be concise, direct, and specific to them — "
        "never generic."
    )
    user = f"""Student profile:
- Goal: {profile.get('goal')}
- Current level: {profile.get('current_level')}
- Known skills: {profile.get('known_skills')}
- Interests: {profile.get('interests')}
- Weak topics: {profile.get('weak_topics')}
- Strong topics: {profile.get('strong_topics')}

Technology item:
Title: {tech_title}
Summary: {tech_summary}

Return JSON with keys:
- why_it_matters (1-2 sentences, personalized to THIS student's goal, not generic hype)
- difficulty_for_you ("easy", "moderate", or "challenging" — relative to their current level)
- should_learn_next (true/false — is this a good next step for them right now?)
- reason (1 sentence explaining the should_learn_next decision)
"""
    return _call_json(system, user)


def chat_reply(topic: str, profile: dict, history: list, message: str) -> str:
    """Conversational tutor — adapts explanation to student's level."""
    system = (
        f"You are a patient, adaptive AI tutor teaching the topic '{topic}'. "
        f"The student's level is '{profile.get('current_level')}' and their goal is "
        f"'{profile.get('goal')}'. Adjust explanation depth accordingly. Ask a follow-up "
        f"question when useful to check understanding. Keep answers focused and not too long."
    )
    # Build conversation for the API
    messages = []
    for h in history[-10:]:  # last 10 turns for context window control
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    resp = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system,
        messages=messages,
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def generate_assessment(topic: str, level: str, num_questions: int = 5) -> list:
    """Generates MCQ quiz scoped to topic + student level."""
    system = (
        "You are an assessment generator for a learning platform. "
        "Create fair, clear multiple-choice questions."
    )
    user = f"""Create {num_questions} multiple-choice questions on "{topic}" 
suitable for a student at "{level}" level.

Return JSON as a list of objects, each with keys:
- question (string)
- options (list of 4 strings)
- correct_index (integer 0-3)
- explanation (1 sentence on why the answer is correct)
"""
    system_json = system + "\n\nRespond with ONLY valid JSON array. No markdown, no backticks."
    raw = _call(system_json, user, max_tokens=1500)
    raw = raw.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def suggest_project(topic: str, level: str, skills: list) -> str:
    """Turns learning into action — hands-on build challenge."""
    system = "You suggest small, achievable hands-on coding projects to reinforce learning."
    user = f"""Topic: {topic}
Student level: {level}
Known skills: {skills}

Suggest ONE specific, scoped hands-on project (buildable in a few hours) that reinforces this topic. 
2-4 sentences: what to build and why it reinforces the concept."""
    return _call(system, user, max_tokens=300)
