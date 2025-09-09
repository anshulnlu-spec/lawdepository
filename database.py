import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Database configuration
def get_database_url():
    """
    Get database URL based on environment (Cloud Run vs local development)
    """
    
    # Get environment variables
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST")
    
    # Check if we're running in Cloud Run (with Cloud SQL connector)
    cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME", 
                                        "gen-lang-client-0486914658:us-central1:legal-docs-db")
    
    if os.getenv("GOOGLE_CLOUD_PROJECT"):  # Running in Cloud Run
        # Use Unix socket connection for Cloud SQL
        db_socket_dir = "/cloudsql"
        database_url = f"postgresql://{db_user}:{db_password}@/{db_name}?host={db_socket_dir}/{cloud_sql_connection_name}"
        logger.info("Using Cloud SQL Unix socket connection")
    else:
        # Use TCP connection for local development
        if not db_host:
            db_host = "localhost"  # Default for local development
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
        logger.info("Using TCP connection for local development")
    
    logger.info(f"Database URL (without password): postgresql://{db_user}:***@{db_host or 'unix_socket'}:5432/{db_name}")
    return database_url

# Create engine with retry logic
def create_db_engine():
    database_url = get_database_url()
    
    engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=0,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        echo=False  # Set to True for SQL debugging
    )
    
    return engine

# Create engine and session
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables with retry logic"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to initialize database (attempt {attempt + 1}/{max_retries})")
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
            return
        except Exception as e:
            logger.error(f"Database initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                import time
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Database initialization failed after all retries")
                # Don't raise the exception - let the app start without DB for now
                # raise
