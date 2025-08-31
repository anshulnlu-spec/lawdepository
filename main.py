from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json, os
from utils import extract_title_date_from_pdf

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Law Depository Backend with GPT 🚀"}

@app.get("/law/{law_name}")
def get_law(law_name: str):
    json_file = f"{law_name}.json"
    if not os.path.exists(json_file):
        return {"error": f"{law_name}.json not found"}

    with open(json_file, "r") as f:
        data = json.load(f)

    results = []
    for link in data.get("pdfs", []):
        title, date, category = extract_title_date_from_pdf(link, law_name)
        results.append({
            "title": title,
            "date": date,
            "link": link,
            "category": category or "Other",
            "source": law_name.upper()
        })

    return {"law": law_name.upper(), "documents": results}
