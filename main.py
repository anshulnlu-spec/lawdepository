from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests, time

app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache and click tracker
cache = {}
cache_expiry = 24 * 3600  # 24 hours
clicks = {}

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

def is_pdf(url):
    now = time.time()
    if url in cache and now - cache[url]["time"] < cache_expiry:
        return cache[url]["ok"]
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        ct = r.headers.get("Content-Type", "").lower()
        ok = "pdf" in ct
    except:
        ok = False
    cache[url] = {"ok": ok, "time": now}
    return ok

# Static seed list of IBC PDFs
sources = [
    {"title": "IBC, 2016 (Bare Act)", "link": "https://ibbi.gov.in//uploads/legalframwork/0150ec26cf05f06e66bd82b2ec4f6296.pdf"},
    {"title": "Application to Adjudicating Authority Rules, 2016", "link": "https://ibbi.gov.in//uploads/legalframwork/0150ec26cf05f06e66bd82b2ec4f6296.pdf"},
    {"title": "CIRP Regulations, 2016", "link": "https://ibbi.gov.in//uploads/legalframwork/2016-05-05_cirp_regulations.pdf"},
    {"title": "MCA Notification – Enforcement of IBC Sections (2016)", "link": "https://egazette.nic.in/WriteReadData/2016/ibc_notification.pdf"},
    {"title": "IBC (Amendment) Act, 2021", "link": "https://www.indiacode.nic.in/bitstream/123456789/16242/1/A2021-26.pdf"},
    {"title": "IBC Amendment Bill, 2021", "link": "https://sansad.in/getFile/BillsPDFFiles/Notification/2021-104-gaz.pdf?source=loksabhadocs"},
    {"title": "IBC Amendment Bill, 2019", "link": "https://sansad.in/getFile/BillsPDFFiles/Notification/2019-145-gaz.pdf?source=loksabhadocs"},
    {"title": "BLRC Committee Report (2015)", "link": "https://ibbi.gov.in/uploads/resources/BLRCReportVol1_04112015.pdf"},
    {"title": "Standing Committee Report on IBC (2021)", "link": "http://164.100.47.193/lsscommittee/Finance/17_Finance_30.pdf"}
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
        if is_pdf(s["link"]):
            cat = classify(s["title"])
            data["categories"][cat].append({
                "title": s["title"],
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
