import logging
import sys
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import database
from config import LEGISLATION_TOPICS

# --- Define absolute paths for serving files ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Global Law Depository API")

# Mount the 'static' folder to serve CSS and JavaScript files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Allow all cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Connect to the database when the application starts."""
    database.connect_and_init_db()

# --- Main Page and API Endpoints ---

@app.get("/")
async def read_index():
    """Serves the frontend's index.html file."""
    return FileResponse(INDEX_PATH)

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
        
        # This structure is what the front-end expects
        categorized_docs = {"India": {}, "United Kingdom": {}, "United States": {}}
        for doc in docs_query:
            country = doc.jurisdiction
            category = doc.category
            if country not in categorized_docs:
                categorized_docs[country] = {}
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
