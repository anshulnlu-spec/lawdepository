# database.py — safe startup-friendly version
import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import URL

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

# Environment (Cloud Run / local .env)
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

def _make_cloudsql_url():
    """
    Construct SQLAlchemy URL only when required env vars are present.
    Returns a sqlalchemy.engine.URL or None if configuration is incomplete.
    """
    if not (db_user and db_password and db_name):
        logger.warning("DB_USER/DB_PASSWORD/DB_NAME not all present — skipping Cloud SQL URL creation.")
        return None

    query = {}
    if db_host:
        query["host"] = str(db_host)

    try:
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=str(db_user),
            password=str(db_password),
            database=str(db_name),
            query=query or None,
        )
        logger.info("Constructed Cloud SQL DATABASE_URL successfully.")
        return url
    except Exception as e:
        logger.exception("Failed to create Cloud SQL URL: %s", e)
        return None

# Primary DATABASE_URL (URL object or string)
DATABASE_URL = _make_cloudsql_url()

# Fallback to SQLite if PostgreSQL config not present
if DATABASE_URL is None:
    fallback_path = os.path.join(os.getcwd(), "local_dev.db")
    sqlite_url = f"sqlite:///{fallback_path}"
    logger.warning("Falling back to SQLite database at %s", fallback_path)
    DATABASE_URL = sqlite_url

# Engine creation (support URL object or string)
url_str = str(DATABASE_URL)
connect_args = {"check_same_thread": False} if url_str.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Models ---
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    publication_date = Column(String)
    summary = Column(Text)
    category = Column(String)
    jurisdiction = Column(String)
    content_type = Column(String)
    topic = Column(String)  # tasks.py passes topic — keep it in model

# --- Helpers / CRUD ---
def init_db():
    """
    Create tables if they don't exist. Safe to call at startup.
    May raise if DB connection fails; callers should handle/log exceptions.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured (create_all completed).")
    except Exception as e:
        logger.exception("Error during init_db: %s", e)
        # Re-raise to let callers decide whether to abort or retry
        raise

def add_document(url, title, publication_date, summary, category, jurisdiction, content_type, topic=None):
    db = SessionLocal()
    try:
        db_doc = Document(
            url=url, title=title, publication_date=publication_date,
            summary=summary, category=category, jurisdiction=jurisdiction,
            content_type=content_type, topic=topic
        )
        db.add(db_doc)
        db.commit()
        logger.info("Added document to DB: %s", title)
    except Exception:
        db.rollback()
        logger.exception("Failed to add document: %s", url)
        raise
    finally:
        db.close()

def get_all_documents():
    db = SessionLocal()
    try:
        return db.query(Document).all()
    finally:
        db.close()

def get_new_links(discovered_links):
    db = SessionLocal()
    try:
        existing_urls_query = db.query(Document.url).all()
        existing_urls = {url for (url,) in existing_urls_query}
        new_links = [link for link in discovered_links if link['url'] not in existing_urls]
        return new_links
    finally:
        db.close()

def get_popular_topics(limit: int = 5):
    """
    Return up to `limit` popular topics (best-effort).
    This is lightweight — used by tasks.py to make prompts smarter.
    """
    db = SessionLocal()
    try:
        rows = db.query(Document.topic).filter(Document.topic.isnot(None)).limit(limit).all()
        return [r[0] for r in rows if r[0]]
    except Exception:
        logger.exception("Failed to fetch popular topics, returning empty list.")
        return []
    finally:
        db.close()
