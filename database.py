cat > database.py <<'PY'
"""
Robust database helper for Cloud Run / local fallback.
- If DB env vars are present, constructs a Postgres connection string suitable for Cloud SQL UNIX socket usage:
    postgresql+psycopg2://<user>:<password>@/<db>?host=/cloudsql/<INSTANCE_CONNECTION_NAME>
  This is built as a plain string to avoid SQLAlchemy URL.create query-type errors.
- If required env vars are missing, falls back to a local SQLite file (./app.db) so container can start.
- Exposes: engine, SessionLocal, Base, init_db(), get_item()
"""
import os
import logging
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Date, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("database")
logging.basicConfig(level=logging.INFO)

# Read environment variables (may be None)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")  # e.g. project:region:instance

def _build_database_url():
    """
    Build a DB URL string. If required Postgres envs present, return a Postgres URL that uses
    the Cloud SQL unix socket path. Otherwise return a sqlite file URL.
    """
    if DB_USER and DB_PASSWORD and DB_NAME and INSTANCE_CONNECTION_NAME:
        # Use Cloud SQL Unix socket connection via SQLAlchemy URL string
        # Format (works without setting 'host' key which can cause type errors via URL.create):
        # postgresql+psycopg2://<user>:<password>@/<db>?host=/cloudsql/<INSTANCE_CONNECTION_NAME>
        user = DB_USER
        pw = DB_PASSWORD
        db = DB_NAME
        inst = INSTANCE_CONNECTION_NAME
        url = f"postgresql+psycopg2://{user}:{pw}@/{db}?host=/cloudsql/{inst}"
        logger.info("Using Cloud SQL Postgres URL (unix socket).")
        return url
    else:
        # Fallback: SQLite local file (safe for startup and local dev)
        logger.warning("One or more DB env vars missing (DB_USER/DB_PASSWORD/DB_NAME/INSTANCE_CONNECTION_NAME). Falling back to SQLite for startup.")
        sqlite_path = os.getenv("SQLITE_PATH", "./app.db")
        return f"sqlite:///{sqlite_path}"

DATABASE_URL = _build_database_url()

# Create engine, session factory, base
# Use future=True for SQLAlchemy 1.4+ style
engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Example Document model used by endpoints (compatible with earlier expectations)
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=True)
    title = Column(String(1024), nullable=True)
    publication_date = Column(Date, nullable=True)
    summary = Column(Text, nullable=True)
    category = Column(String(256), nullable=True)
    jurisdiction = Column(String(256), nullable=True)
    content_type = Column(String(128), nullable=True)
    topic = Column(String(256), nullable=True)

def init_db():
    """
    Create DB tables if they don't exist. Safe to call multiple times.
    This should be called in a background thread (not to block startup) — main.py already starts it in background.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured.")
    except Exception as e:
        logger.exception("init_db failed: %s", e)
        # Do not exit the process — log and continue so container can start.

def get_item(item_id: int):
    """
    Return a document by id or a safe placeholder.
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == item_id).first()
        if not doc:
            return {"id": item_id, "title": "not found", "message": "Document not found"}
        # Convert SQLAlchemy object to dict
        return {
            "id": doc.id,
            "url": doc.url,
            "title": doc.title,
            "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
            "summary": doc.summary,
            "category": doc.category,
            "jurisdiction": doc.jurisdiction,
            "content_type": doc.content_type,
            "topic": doc.topic,
        }
    finally:
        db.close()

# If you want to keep a fast sanity check during import, log the chosen URL (do NOT raise/exit)
logger.info("DATABASE_URL chosen (hidden for safety). Using scheme: %s", DATABASE_URL.split(":", 1)[0] if DATABASE_URL else "unknown")
PY

# commit & push
git add database.py
git commit -m "fix(database): make DB initialization resilient; fallback to SQLite if secrets missing; provide init_db and get_item"
git push origin main
