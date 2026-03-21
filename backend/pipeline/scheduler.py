from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from .fetcher import fetch_arxiv_articles
from .generator import generate_course

logger = logging.getLogger(__name__)


def run_pipeline(db_session_factory, domain: str = "machine_learning", max_results: int = 3):
    logger.info(f"Pipeline started for domain: {domain}")
    from models.course import Course

    articles = fetch_arxiv_articles(domain=domain, max_results=max_results)
    logger.info(f"Fetched {len(articles)} articles")

    db = db_session_factory()
    try:
        for article in articles:
            # Skip if already exists by source URL
            existing = db.query(Course).filter(Course.source_url == article.url).first()
            if existing:
                logger.info(f"Skipping already processed: {article.url}")
                continue

            course_data = generate_course(article)
            if not course_data:
                continue

            course = Course(
                title=course_data["title"],
                domain=course_data["domain"],
                source_url=course_data["source_url"],
                source_title=course_data["source_title"],
                summary=course_data["summary"],
                modules=course_data["modules"],
            )
            db.add(course)
            db.commit()
            logger.info(f"Course saved: {course.title}")
    except Exception as e:
        db.rollback()
        logger.error(f"Pipeline error: {e}")
        raise
    finally:
        db.close()


def start_scheduler(db_session_factory):
    scheduler = BackgroundScheduler()

    # Run daily at 8 AM UTC
    scheduler.add_job(
        func=lambda: run_pipeline(db_session_factory),
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_course_generation",
        name="Generate courses daily",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started — courses will generate daily at 08:00 UTC")
    return scheduler
