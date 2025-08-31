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
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # For demo: just grab all <a> links on homepage
    links = []
    for a in soup.find_all("a", href=True)[:10]:  # only 10 links for now
        links.append({
            "title": a.text.strip(),
            "link": "https://egazette.nic.in/" + a['href']
        })

    return {"laws": links}
