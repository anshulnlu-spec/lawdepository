# main.py - FastAPI app
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import logging

import database
import autonomous_researcher

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Autonomous Researcher Service")

# mount static safely even when directory missing in dev
app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

@app.on_event("startup")
def on_startup():
    # Initialize DB (raises if misconfigured)
    try:
        database.connect_and_init_db()
    except Exception:
        logger.exception("Database initialization failed during startup.")
        # re-raise so container startup is visibly failing with trace
        raise

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
def index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"service": "autonomous-researcher", "status": "running"})

@app.post("/run", tags=["research"])
def run_research(topic: str, db: Session = Depends(database.get_db)):
    try:
        result = autonomous_researcher.run_autonomous_research_cycle(topic, db=db)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.exception("Error running research cycle")
        raise HTTPException(status_code=500, detail=str(e))
