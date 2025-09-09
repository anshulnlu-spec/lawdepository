import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import database
from config import LEGISLATION_TOPICS

# Configure logging to see output in Google Cloud Run logs
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Global Law Depository API")

# Allow all cross-origin requests for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Ensure the database and tables are created on application startup."""
    logging.info("FastAPI startup: Initializing database...")
    try:
        database.init_db()
        logging.info("Database initialization successful.")
    except Exception as e:
        logging.critical(f"FATAL: Database initialization failed: {e}", exc_info=True)
        # If the DB fails to init, the app is not healthy and should not start.
        raise

@app.get("/api/health")
def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}

@app.get("/api/topics")
def get_topics():
    """Returns the list of legislation topics for the frontend navigation."""
    logging.info("API CALL: /api/topics")
    return JSONResponse(content=LEGISLATION_TOPICS)

@app.get("/api/documents/{topic}")
def get_documents(topic: str):
    """Fetches all categorized documents for a specific topic from the database."""
    logging.info(f"API CALL: /api/documents/{topic}")
    try:
        # URL Decode the topic name in case it has spaces like "Companies%20Act"
        from urllib.parse import unquote
        decoded_topic = unquote(topic)

        docs = database.get_documents_by_topic(decoded_topic)
        
        categorized_docs = {
            "India": {}, "United Kingdom": {}, "United States": {}
        }
        for doc in docs:
            country = doc.jurisdiction
            category = doc.category
            if country not in categorized_docs:
                categorized_docs[country] = {}
            if category not in categorized_docs[country]:
                categorized_docs[country][category] = []
            
            categorized_docs[country][category].append({
                "title": doc.title,
                "date": doc.publication_date,
                "summary": doc.summary,
                "url": doc.url,
                "content_type": doc.content_type
            })
        logging.info(f"Found and processed {len(docs)} documents for topic '{decoded_topic}'.")
        return JSONResponse(content=categorized_docs)
    except Exception as e:
        logging.error(f"Error fetching documents for topic '{topic}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve documents.")

# Serve the static frontend files (index.html, style.css, etc.)
# This must be mounted after all API routes.
app.mount("/", StaticFiles(directory="static", html=True), name="static")

