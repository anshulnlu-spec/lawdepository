from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Law Depository Backend is running 🚀"}

@app.get("/laws")
def get_laws():
    url = "https://egazette.nic.in/Welcome.aspx"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    laws = []
    # Get latest links (top 10 for demo)
    for a in soup.find_all("a", href=True)[:10]:
        title = a.text.strip()
        if not title:
            continue
        link = "https://egazette.nic.in/" + a["href"]
        laws.append({"title": title, "link": link})

    return {"laws": laws}
