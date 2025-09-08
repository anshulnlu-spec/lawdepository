import os
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import database
import tasks

# Get the project ID from the environment variable set by GCP
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")

app = FastAPI(title="Global Law Depository API")

# Allow all cross-origin requests for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    This function runs when the Cloud Run instance starts.
    It ensures the database and its tables are created.
    """
    print("Application startup: Initializing database...")
    database.init_db()
    print("Database initialized.")

@app.get("/api/health")
def health_check():
    """A simple health check endpoint that Cloud Run can use to verify the instance is live."""
    return {"status": "ok"}

@app.get("/api/documents")
def get_documents():
    """
    The main API endpoint for the frontend. Fetches all categorized documents
    from the database and formats them for display.
    """
    print("API call received for /api/documents")
    try:
        docs = database.get_all_documents()
        
        # Prepare a structured dictionary for the frontend
        categorized_docs = {}
        
        for doc in docs:
            topic = doc.topic
            category = doc.category
            
            if topic not in categorized_docs:
                categorized_docs[topic] = {}
            if category not in categorized_docs[topic]:
                categorized_docs[topic][category] = []
                
            categorized_docs[topic][category].append({
                "title": doc.title,
                "date": doc.publication_date,
                "summary": doc.summary,
                "url": doc.url,
                "content_type": doc.content_type,
                "click_count": doc.click_count
            })
        
        return JSONResponse(content={"topics": categorized_docs})
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to retrieve documents from the database."})

@app.post("/api/track_click")
async def track_click(request: Request):
    """
    API endpoint to track when a user clicks on a document link.
    This data makes the AI researcher smarter over time.
    """
    try:
        data = await request.json()
        doc_url = data.get("url")
        if doc_url:
            database.increment_click_count(doc_url)
            print(f"Tracked click for URL: {doc_url}")
            return {"status": "success"}
        return {"status": "error", "message": "URL not provided"}
    except Exception as e:
        print(f"Error tracking click: {e}")
        return JSONResponse(status_code=400, content={"error": "Invalid request."})

@app.post("/run-tasks")
def run_tasks_endpoint(background_tasks: BackgroundTasks):
    """
    A secure endpoint that Cloud Scheduler can call to trigger the AI researcher.
    It runs the heavy AI task in the background to avoid timeouts.
    """
    print("Received request to run AI researcher job.")
    background_tasks.add_task(tasks.run_update_job)
    return {"message": "AI researcher job has been triggered and is running in the background."}

# This MUST be the last part of the file.
# It serves the frontend files (index.html, style.css, etc.) from the 'static' directory.
app.mount("/", StaticFiles(directory="static", html=True), name="static")

