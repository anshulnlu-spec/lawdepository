from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json, os
from utils import extract_title_date_from_pdf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Law Depository Backend (Gemini) is running 🚀"}

@app.get("/law/{law_name}")
def get_law(law_name: str):
    file = f"{law_name}.json"
    if not os.path.exists(file):
        return {"error": "Law not found"}

    with open(file, "r") as f:
        data = json.load(f)

    results = []
    for url in data.get("pdfs", []):
        title, date, category = extract_title_date_from_pdf(url, law_name)
        results.append({
            "title": title,
            "date": date,
            "category": category,
            "url": url
        })
    return {"law": law_name, "docs": results}
