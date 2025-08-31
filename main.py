from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests, time
from io import BytesIO
from PyPDF2 import PdfReader

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = {}
cache_expiry = 24 * 3600
clicks = {}

def extract_title_and_date(url):
    now = time.time()
    if url in cache and now - cache[url]["time"] < cache_expiry:
        return cache[url]["title"], cache[url]["date"]
    title, date = None, None
    try:
        r = requests.get(url, timeout=20, stream=True)
        pdf = PdfReader(BytesIO(r.content))
        first_page = pdf.pages[0].extract_text()
        if first_page:
            lines = [l.strip() for l in first_page.split("\n") if l.strip()]
            if lines:
                title = lines[0]
                if len(lines) > 1 and ("20" in lines[1] or "19" in lines[1]):
                    date = lines[1]
        if not title:
            title = url.split("/")[-1]
    except Exception as e:
        title = url.split("/")[-1]
        date = None
    cache[url] = {"title": title, "date": date, "time": now}
    return title, date

def classify(title):
    t = title.lower()
    if "amendment bill" in t or ("bill" in t and "act" not in t):
        return "Amendment Bills"
    if "ordinance" in t or "amendment act" in t:
        return "Amendment Acts"
    if "act" in t and "amendment" not in t:
        return "Act"
    if "rules" in t:
        return "Rules"
    if "regulation" in t:
        return "Regulations"
    if "notification" in t or "gazette" in t:
        return "Notifications"
    if "report" in t or "committee" in t:
        return "Reports"
    return "Other"

sources = [
    {"link": "https://ibbi.gov.in//uploads/legalframwork/0150ec26cf05f06e66bd82b2ec4f6296.pdf"},
    {"link": "https://www.indiacode.nic.in/bitstream/123456789/16242/1/A2021-26.pdf"},
    {"link": "https://sansad.in/getFile/BillsPDFFiles/Notification/2021-104-gaz.pdf?source=loksabhadocs"},
    {"link": "https://sansad.in/getFile/BillsPDFFiles/Notification/2019-145-gaz.pdf?source=loksabhadocs"},
    {"link": "https://ibbi.gov.in/uploads/resources/BLRCReportVol1_04112015.pdf"},
    {"link": "http://164.100.47.193/lsscommittee/Finance/17_Finance_30.pdf"},
    {"link": "https://ibbi.gov.in//uploads/legalframwork/2016-05-05_cirp_regulations.pdf"},
    {"link": "https://ibbi.gov.in//uploads/legalframwork/2016-12-15_liquidation_regulations.pdf"},
    {"link": "https://egazette.nic.in/WriteReadData/2016/ibc_notification.pdf"}
]

@app.get("/")
def home():
    return {"message": "Law Depository Backend is running 🚀"}

@app.get("/law/ibc")
def get_ibc():
    data = {
        "law": "Insolvency and Bankruptcy Code, 2016",
        "categories": {
            "Act": [], "Amendment Acts": [], "Amendment Bills": [], "Rules": [],
            "Regulations": [], "Notifications": [], "Reports": [], "Other": []
        }
    }
    for s in sources:
        title, date = extract_title_and_date(s["link"])
        cat = classify(title)
        data["categories"][cat].append({
            "title": title,
            "date": date,
            "link": s["link"],
            "clicks": clicks.get(s["link"], 0)
        })
    for cat in data["categories"]:
        data["categories"][cat].sort(key=lambda x: x["clicks"], reverse=True)
    return data

@app.post("/click")
async def register_click(req: Request):
    body = await req.json()
    link = body.get("link")
    if link:
        clicks[link] = clicks.get(link, 0) + 1
    return {"status": "ok", "link": link, "total_clicks": clicks.get(link, 0)}
