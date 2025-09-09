import os
import logging
import threading
import time
from typing import Optional

from fastapi import FastAPI, HTTPException

# Try to import your database module if present. If not present, we still start the app.
try:
    import database
except Exception as e:  # ImportError or other errors when importing (keep robust)
    database = None
    logging.getLogger("main").warning("database module import failed: %s", e)

# Optional: import any config module (safe if missing)
try:
    import config
except Exception:
    config = None

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("legal-docs-service")

app = FastAPI(title="Legal Docs Service")

@app.get("/", tags=["root"])
def read_root():
    return {"status": "ok", "service": "legal-docs-service"}

@app.get("/api/health", tags=["health"])
def health() -> dict:
    """
    Health endpoint used for readiness/liveness checks.
    Returns status ok if app process is running.
    Note: it does NOT assert DB connectivity to avoid failing container startup.
    """
    return {"status": "ok"}

def _init_db_if_available(retries: int = 6, delay: int = 10):
    """
    Try to call database.init_db() if present. Retries on Exception.
    Runs in a background daemon thread from the startup handler so container startup is not blocked.
    """
    if database is None:
        logger.info("No database module found; skipping DB initialization.")
        return

    init_fn = getattr(database, "init_db", None)
    if not callable(init_fn):
        logger.info("database.init_db not found or not callable; skipping DB initialization.")
        return

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"DB init attempt {attempt}/{retries}...")
            init_fn()
            logger.info("Database initialized successfully.")
            return
        except Exception as e:
            logger.exception(f"DB init attempt {attempt} failed: {e}")
            if attempt == retries:
                logger.error("All DB init attempts failed — continuing without blocking the app.")
                return
            time.sleep(delay)

@app.on_event("startup")
def on_startup():
    """
    Startup event: spawn background thread to initialize DB (non-blocking).
    This prevents container crashes when DB or secrets are temporarily unavailable.
    """
    logger.info("FastAPI startup event triggered.")
    t = threading.Thread(target=_init_db_if_available, kwargs={"retries": 6, "delay": 10}, daemon=True)
    t.start()

# Example endpoint that uses DB if available (safe-check)
@app.get("/api/items/{item_id}", tags=["items"])
def get_item(item_id: int):
    """
    Example handler that will call database.get_item if available.
    Returns a placeholder if DB helpers are not present.
    """
    if database is not None and hasattr(database, "get_item"):
        try:
            return database.get_item(item_id)
        except Exception as e:
            logger.exception("Error fetching item from database: %s", e)
            raise HTTPException(status_code=500, detail="Database error")
    # Fallback placeholder
    return {"id": item_id, "title": "not found", "message": "Database not configured or item missing"}
