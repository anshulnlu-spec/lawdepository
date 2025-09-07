from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import database

app = FastAPI(title="Global Insolvency Law Depository API")

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Ensure the database and tables are created on application startup."""
    database.init_db()

@app.get("/api/health")
def health_check():
    """A simple health check endpoint for Render."""
    return {"status": "ok"}

@app.get("/api/documents")
def get_documents():
    """Fetches all categorized and validated documents from the database."""
    try:
        docs = database.get_all_documents()
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
        print(f"Error fetching documents: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to retrieve documents."})

# Serve the static frontend files (index.html, style.css, etc.)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
