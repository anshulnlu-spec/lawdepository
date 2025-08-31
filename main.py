from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import schedule, time, threading

# Import scrapers
from scraper_ibbi import scrape_ibbi
from utils import deduplicate

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache
DATA_CACHE = {"law": "IBC", "categories": {}}

# Function to refresh data
def refresh_data():
    global DATA_CACHE
    all_docs = []
    try:
        all_docs.extend(scrape_ibbi())
    except Exception as e:
        print("Error running scrapers:", e)

    # Deduplicate & categorise
    DATA_CACHE["categories"] = deduplicate(all_docs)
    print("Data refreshed, total docs:", sum(len(v) for v in DATA_CACHE["categories"].values()))

# Background thread to run schedule
def scheduler_thread():
    schedule.every(24).hours.do(refresh_data)
    refresh_data()  # run once at startup
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=scheduler_thread, daemon=True).start()

@app.get("/")
def home():
    return {"message": "Law Depository Backend is running 🚀"}

@app.get("/law/ibc")
def get_ibc():
    return DATA_CACHE
