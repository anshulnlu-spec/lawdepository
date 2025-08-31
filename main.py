from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# ✅ Allow frontend (GitHub Pages) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Law Depository Backend is running 🚀"}

@app.get("/laws")
def get_laws():
    try:
        url = "https://egazette.nic.in/Welcome.aspx"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        laws = []
        for a in soup.find_all("a", href=True)[:10]:
            title = a.text.strip()
            if not title:
                continue
            link = "https://egazette.nic.in/" + a["href"]
            laws.append({"title": title, "link": link})

        if not laws:  # if scraping failed
            raise Exception("No data scraped")

        return {"laws": laws}

    except Exception as e:
        # ✅ fallback demo data so site never breaks
        demo_data = [
            {"title": "Insolvency and Bankruptcy Code, 2016", "link": "https://ibbi.gov.in"},
            {"title": "Companies (Amendment) Act, 2020", "link": "https://mca.gov.in"},
            {"title": "Competition Act, 2002", "link": "https://cci.gov.in"}
        ]
        return {"laws": demo_data, "note": "⚠️ Showing demo data because scraping failed"}
