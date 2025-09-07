from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from utils import extract_details_from_pdf

app = FastAPI()

# --- Middleware for CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def root():
    return {"message": "Law Depository Backend (Gemini) is running 🚀"}

@app.get("/law/{law_name}")
def get_law(law_name: str):
    """
    Processes a law file, extracts details from its PDFs using Gemini,
    and returns the structured data.
    """
    json_file = f"{law_name}.json"
    if not os.path.exists(json_file):
        return {"error": f"Law '{law_name}' not found"}

    with open(json_file, "r") as f:
        data = json.load(f)

    results = []
    pdf_urls = data.get("pdfs", [])
    
    for url in pdf_urls:
        title, date, category = extract_details_from_pdf(url, law_name)
        results.append({
            "title": title,
            "date": date,
            "category": category,
            "url": url
        })
        
    # Sort results by date, newest first
    results.sort(key=lambda x: x.get('date', '0000-00-00'), reverse=True)

    return {"law": law_name, "docs": results}