import os
import sys
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import URL

# --- Basic Setup ---
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
Base = declarative_base()

# --- Global variables to hold the engine and session ---
# We initialize them to None. They will be created when the app starts.
engine = None
SessionLocal = None

# --- Database Model Definition ---
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
    topic = Column(String, index=True)

# --- Connection and Initialization Function ---
def connect_and_init_db():
    """
    Connects to the database, creates the engine and session,
    and initializes tables. This should be called once at application startup.
    """
    global engine, SessionLocal

    # Get database credentials from environment variables
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")  # Cloud SQL connection name
    db_name = os.getenv("DB_NAME")
    cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")

    if not all([db_user, db_password, db_name]):
        logging.critical("FATAL: DB_USER, DB_PASSWORD, and DB_NAME must be set.")
        sys.exit(1)

    # Use Unix socket for Cloud Run, TCP for local
    if cloud_sql_connection_name:
        db_host_socket = f"/cloudsql/{cloud_sql_connection_name}"
        database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=db_user, password=db_password,
            database=db_name, query={"host": db_host_socket}
        )
    else: # Fallback for local development
        db_host_local = db_host or "localhost"
        database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=db_user, password=db_password,
            host=db_host_local, port=5432, database=db_name
        )

    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logging.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logging.info("Database connection and initialization successful.")
    except Exception as e:
        logging.critical(f"FATAL: Could not connect to the database: {e}", exc_info=True)
        raise

# --- Dependency for FastAPI ---
def get_db():
    """Dependency that provides a database session for each request."""
    if SessionLocal is None:
        logging.error("Database session requested before initialization.")
        raise RuntimeError("Database not initialized. Call connect_and_init_db() on startup.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
