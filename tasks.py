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
# These are initialized to None and will be created when the app starts.
engine = None
SessionLocal = None

# --- Database Model Definition ---
# This class defines the structure of the 'documents' table in your database.
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
    and initializes tables. This is called once at application startup.
    """
    global engine, SessionLocal

    # Get database credentials from environment variables
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    # This variable is set in cloudbuild.yaml and is the key to connecting correctly.
    cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")

    # This check is critical for Cloud Run. Local dev can use DB_HOST.
    if not all([db_user, db_password, db_name]):
        logging.critical("FATAL: DB_USER, DB_PASSWORD, and DB_NAME must be set.")
        sys.exit(1)

    try:
        if cloud_sql_connection_name:
            # We are in a Google Cloud Run environment
            logging.info("Using Cloud SQL Unix socket for database connection.")
            db_socket_path = f"/cloudsql/{cloud_sql_connection_name}"
            
            database_url = URL.create(
                drivername="postgresql+psycopg2",
                username=db_user, password=db_password,
                database=db_name, query={"host": db_socket_path}
            )
        else:
            # We are in a local development environment
            logging.info("Using TCP for local database connection.")
            db_host_local = os.getenv("DB_HOST", "localhost")
            database_url = URL.create(
                drivername="postgresql+psycopg2",
                username=db_user, password=db_password,
                host=db_host_local, port=5432, database=db_name
            )

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
        raise RuntimeError("Database not initialized.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Database Interaction Functions ---
# These functions now accept a database session as an argument.
# This is a best practice for managing database connections efficiently.

def add_document(db, url, title, publication_date, summary, category, jurisdiction, content_type, topic):
    """Adds a new document to the database using the provided session."""
    db_doc = Document(
        url=url, title=title, publication_date=publication_date,
        summary=summary, category=category, jurisdiction=jurisdiction,
        content_type=content_type, topic=topic
    )
    db.add(db_doc)
    db.commit()
    logging.info(f"Successfully committed document: {title}")

def get_documents_by_topic(db, topic: str):
    """Retrieves all documents for a specific topic using the provided session."""
    return db.query(Document).filter(Document.topic == topic).all()

def get_new_links(db, discovered_links):
    """Filters a list of links, returning only those not already in the database."""
    existing_urls_query = db.query(Document.url).all()
    existing_urls = {url for (url,) in existing_urls_query}
    return [link for link in discovered_links if link['url'] not in existing_urls]
