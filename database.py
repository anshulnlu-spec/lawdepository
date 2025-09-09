import os
import sys
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import URL

# Configure basic logging to help with debugging in Cloud Run
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This is the new, cloud-native way to connect.
# It reads the secret variables provided by Cloud Run.
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST") # This will be the socket path e.g. /cloudsql/project:region:instance
db_name = os.getenv("DB_NAME")

# This is a critical check. If any secret is missing, it will log a clear error and exit.
if not all([db_user, db_password, db_host, db_name]):
    logging.critical("DATABASE FATAL ERROR: One or more database environment variables are not set. Exiting.")
    sys.exit(1) # Exit the process immediately if the configuration is incomplete.

# Build the database URL for Cloud SQL (PostgreSQL)
# The drivername 'postgresql+psycopg2' tells SQLAlchemy how to talk to Postgres.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=db_user,
    password=db_password,
    database=db_name,
    query={"host": db_host},
)

# The engine now connects to our Cloud SQL database.
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- The rest of your database model and functions remain the same ---

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

def init_db():
    # This function will now create the table in your Cloud SQL database.
    Base.metadata.create_all(bind=engine)

def add_document(url, title, publication_date, summary, category, jurisdiction, content_type):
    db = SessionLocal()
    try:
        db_doc = Document(
            url=url, title=title, publication_date=publication_date,
            summary=summary, category=category, jurisdiction=jurisdiction,
            content_type=content_type
        )
        db.add(db_doc)
        db.commit()
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

