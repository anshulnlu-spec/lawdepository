import logging
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database
from config import LEGISLATION_TOPICS

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Global Law Depository API")

# Allow all cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Connect to the database when the application starts."""
    database.connect_and_init_db()

@app.get("/api/health")
def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}

@app.get("/api/topics")
def get_topics():
    """Returns the list of legislation topics."""
    return JSONResponse(content=LEGISLATION_TOPICS)

@app.get("/api/documents/{topic}")
def get_documents(topic: str, db: Session = Depends(database.get_db)):
    """Fetches all documents for a specific topic from the database."""
    from urllib.parse import unquote
    decoded_topic = unquote(topic)
    
    try:
        docs_query = db.query(database.Document).filter(database.Document.topic == decoded_topic).all()
        
        categorized_docs = {"India": {}, "United Kingdom": {}, "United States": {}}
        for doc in docs_query:
            country = doc.jurisdiction
            category = doc.category
            if category not in categorized_docs.get(country, {}):
                categorized_docs[country][category] = []
            
            categorized_docs[country][category].append({
                "title": doc.title, "date": doc.publication_date,
                "summary": doc.summary, "url": doc.url,
                "content_type": doc.content_type
            })
        
        logging.info(f"Found {len(docs_query)} documents for topic '{decoded_topic}'.")
        return JSONResponse(content=categorized_docs)
    except Exception as e:
        logging.error(f"Error fetching documents for topic '{topic}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve documents.")
