import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import URL

# ... (logging setup and the rest of your file) ...

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST") # This will be "project:region:instance"
db_name = os.getenv("DB_NAME")

if not all([db_user, db_password, db_host, db_name]):
    logging.critical("DATABASE FATAL ERROR: One or more database environment variables are not set.")
    sys.exit(1)

# Build the database URL for Cloud SQL (PostgreSQL)
# The drivername 'postgresql+psycopg2' tells SQLAlchemy how to talk to Postgres.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=db_user,
    password=db_password,
    database=db_name,
    query={"host": f"/cloudsql/{db_host}"},
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Dependency for Web Frameworks (like FastAPI) ---
def get_db():
    """Dependency to get a database session for a single request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Database Initialization ---
def init_db():
    """Creates all database tables based on the models."""
    try:
        logging.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialization check complete.")
    except Exception as e:
        logging.critical(f"FATAL: Database initialization failed: {e}", exc_info=True)
        # Raising the exception will cause the app to fail its startup,
        # which is desirable so the orchestrator (Cloud Run) can restart it.
        raise


