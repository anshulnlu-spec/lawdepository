from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# In a serverless environment like Cloud Run, the filesystem is temporary.
# We save the database to the /tmp directory, which is a writable in-memory filesystem.
DB_PATH = "/tmp/law_depository.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Document(Base):
    """Defines the structure of the documents table in the database."""
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    publication_date = Column(String)
    summary = Column(Text)
    category = Column(String)
    jurisdiction = Column(String)
    content_type = Column(String)
    topic = Column(String, index=True)      # To categorize by law (e.g., "Companies Act")
    click_count = Column(Integer, default=0) # To track user interaction

def init_db():
    """Creates the database and the documents table if they don't exist."""
    Base.metadata.create_all(bind=engine)

def add_document(url, title, publication_date, summary, category, jurisdiction, content_type, topic, click_count=0):
    """Adds a new, analyzed document to the database."""
    db = SessionLocal()
    try:
        db_doc = Document(
            url=url, title=title, publication_date=publication_date,
            summary=summary, category=category, jurisdiction=jurisdiction,
            content_type=content_type, topic=topic, click_count=click_count
        )
        db.add(db_doc)
        db.commit()
    finally:
        db.close()

def get_all_documents():
    """Retrieves all documents from the database, ordered by date."""
    db = SessionLocal()
    try:
        return db.query(Document).order_by(Document.publication_date.desc()).all()
    finally:
        db.close()

def get_new_links(discovered_links):
    """Filters a list of discovered links, returning only the ones not already in the database."""
    db = SessionLocal()
    try:
        existing_urls = {doc.url for doc in db.query(Document.url).all()}
        new_links = [link for link in discovered_links if link['url'] not in existing_urls]
        return new_links
    finally:
        db.close()

def increment_click_count(doc_url):
    """Increments the click counter for a specific document when a user clicks it."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.url == doc_url).first()
        if doc:
            doc.click_count += 1
            db.commit()
    finally:
        db.close()

def get_popular_topics():
    """Identifies the most clicked-on documents to help the AI researcher prioritize."""
    db = SessionLocal()
    try:
        # Returns the titles of the top 5 most popular documents
        return [doc.title for doc in db.query(Document).order_by(Document.click_count.desc()).limit(5).all()]
    finally:
        db.close()

