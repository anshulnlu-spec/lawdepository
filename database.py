import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker, declarative_base

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST") # For local TCP connection (e.g., "localhost")
# The Cloud SQL connection name is the primary indicator of a Cloud Run environment.
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

# Exit immediately if essential secrets are not set
if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    logging.critical("FATAL: DB_USER, DB_PASSWORD, and DB_NAME must be set.")
    sys.exit(1)

# --- URL Construction ---
if CLOUD_SQL_CONNECTION_NAME:
    # We are in a Google Cloud Run environment
    logging.info("Using Cloud SQL Unix socket for database connection.")
    db_socket_path = f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
    
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        query={"host": db_socket_path},
    )
else:
    # We are in a local development environment
    logging.info("Using TCP for local database connection.")
    # Use localhost as a default if DB_HOST is not set
    db_host_local = DB_HOST or "localhost"
    
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=db_host_local,
        port=5432,
        database=DB_NAME,
    )

# --- Engine and Session Setup ---
# pool_pre_ping=True checks connection validity, preventing errors from stale connections.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300 # Recycle connections every 5 minutes
)

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
