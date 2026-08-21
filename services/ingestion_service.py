"""
Pulls raw tech news from RSS feeds, dedupes, and runs each through the LLM
to produce a clean TechItem. Keep sources small for the demo — 2-3 feeds is plenty.
"""
import feedparser
from sqlalchemy.orm import Session
from models import TechItem
from services.llm_service import summarize_and_tag

FEEDS = [
    "https://hnrss.org/frontpage",          # Hacker News front page
    "https://www.technologyreview.com/feed/",  # MIT Tech Review
]


def ingest_latest(db: Session, limit_per_feed: int = 5) -> list[TechItem]:
    created = []
    for feed_url in FEEDS:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:limit_per_feed]:
            title = entry.get("title", "")
            # skip if we already have this title
            exists = db.query(TechItem).filter(TechItem.title == title).first()
            if exists or not title:
                continue

            content = entry.get("summary", "") or entry.get("description", "")
            try:
                enriched = summarize_and_tag(title, content)
            except Exception:
                # fail-safe: still store the raw item so ingestion doesn't break the demo
                enriched = {"summary": content[:300], "difficulty": "beginner",
                            "tags": [], "prerequisites": []}

            item = TechItem(
                title=title,
                summary=enriched.get("summary", ""),
                source=feed_url,
                url=entry.get("link", ""),
                difficulty=enriched.get("difficulty", "beginner"),
                tags=enriched.get("tags", []),
                prerequisites=enriched.get("prerequisites", []),
            )
            db.add(item)
            created.append(item)

    db.commit()
    return created
