import logging
import sys

# Configure logging at the very beginning to capture everything.
# This will print detailed messages to your Google Cloud logs.
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Application starting up...")

try:
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import database
    logging.info("All primary modules imported successfully.")
except Exception as e:
    logging.error(f"CRITICAL FAILURE during initial imports: {e}")
    # If this fails, the container will crash, and this log will be the reason.
    raise

app = FastAPI(title="Global Insolvency Law Depository API")
logging.info("FastAPI app initialized.")

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.info("CORS middleware configured.")

@app.on_event("startup")
def on_startup():
    """Ensure the database and tables are created on application startup."""
    logging.info("Executing FastAPI startup event...")
    try:
        logging.info("Attempting to initialize the database (running create_all)...")
        database.init_db()
        logging.info("Database initialized successfully. Tables should exist.")
    except Exception as e:
        # This is the most likely place for a crash. This log will capture the exact error.
        logging.error(f"CRITICAL FAILURE during database initialization: {e}", exc_info=True)
        # We raise the exception to ensure the startup fails visibly if the DB is not ready.
        raise

@app.get("/api/health")
def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}

@app.get("/api/documents")
def get_documents():
    """Fetches all categorized and validated documents from the database."""
    logging.info("API CALL: /api/documents endpoint hit.")
    try:
        docs = database.get_all_documents()
        logging.info(f"Successfully retrieved {len(docs)} documents from database.")
        categorized_docs = {
            "India": {}, "United Kingdom": {}, "United States": {}
        }
        for doc in docs:
            country = doc.jurisdiction
            category = doc.category
            if category not in categorized_docs.get(country, {}):
                categorized_docs[country][category] = []
            categorized_docs[country][category].append({
                "title": doc.title, "date": doc.publication_date,
                "summary": doc.summary, "url": doc.url, "content_type": doc.content_type
            })
        return JSONResponse(content=categorized_docs)
    except Exception as e:
        logging.error(f"Error processing documents for API response: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Failed to retrieve documents."})

# Serve the static frontend files (index.html, style.css, etc.)
# This must be mounted after all API routes.
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
    logging.info("Static files mounted successfully.")
except Exception as e:
    logging.error(f"CRITICAL FAILURE while mounting static files: {e}", exc_info=True)
    raise

logging.info("Application setup complete. Uvicorn is now starting to serve requests.")

