# database.py - SQLAlchemy engine, session, and model definitions
import os
import logging
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()
SessionLocal = None
engine = None

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    title = Column(String(1024), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def _build_database_url():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    cloud_sql_conn = os.getenv("CLOUD_SQL_CONNECTION_NAME")

    if not db_user or not db_password or not db_name:
        raise RuntimeError("DB_USER, DB_PASSWORD and DB_NAME must be set in environment")

    if cloud_sql_conn:
        return f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host=/cloudsql/{cloud_sql_conn}"
    else:
        return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def connect_and_init_db():
    global SessionLocal, engine
    if engine is not None and SessionLocal is not None:
        return

    database_url = _build_database_url()
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized and tables created/verified.")

def get_db():
    if SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized. Call connect_and_init_db() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
