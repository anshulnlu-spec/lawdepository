from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///law_depository.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    publication_date = Column(String)
    summary = Column(Text)
    category = Column(String)
    jurisdiction = Column(String)
    content_type = Column(String) # New column

def init_db():
    Base.metadata.create_all(bind=engine)

def add_document(url, title, publication_date, summary, category, jurisdiction, content_type):
    db = SessionLocal()
    try:
        db_doc = Document(
            url=url, title=title, publication_date=publication_date,
            summary=summary, category=category, jurisdiction=jurisdiction,
            content_type=content_type # Add new field
        )
        db.add(db_doc)
        db.commit()
    finally:
        db.close()

def get_all_documents():
    db = SessionLocal()
    try:
        return db.query(Document).order_by(Document.publication_date.desc()).all()
    finally:
        db.close()

def get_new_links(discovered_links):
    db = SessionLocal()
    try:
        existing_urls = {doc.url for doc in db.query(Document.url).all()}
        new_links = [link for link in discovered_links if link['url'] not in existing_urls]
        return new_links
    finally:
        db.close()