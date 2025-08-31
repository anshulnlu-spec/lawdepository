from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json, os
from utils import extract_title_date_from_pdf, categorise_entry

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://anshulnlu-spec.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)

@app.get("/")
def home():
    return {"message": "Law Depository Registry Backend is running 🚀"}

@app.get("/law/{law_name}")
def get_law(law_name: str):
    json_file = os.path.join(BASE_DIR, f"{law_name}.json")
    if not os.path.exists(json_file):
        return {"error": "Law not found"}

    with open(json_file, "r") as f:
        data = json.load(f)

    results = []
    for link in data.get("pdfs", []):
        title, date = extract_title_date_from_pdf(link)
        entry = {
            "title": title,
            "date": date,
            "link": link,
            "source": law_name.upper()
        }
        entry["category"] = categorise_entry(title)
        results.append(entry)

    categories = {}
    for e in results:
        cat = e.get("category", "Other")
        categories.setdefault(cat, []).append(e)

    return {"law": law_name.upper(), "categories": categories}
