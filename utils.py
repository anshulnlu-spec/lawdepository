import requests, time, re
from io import BytesIO
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pytesseract

cache = {}

def extract_title_date_from_pdf(url):
    now = time.time()
    if url in cache and now - cache[url]["time"] < 30*24*3600:
        return cache[url]["title"], cache[url]["date"]

    title, date = None, None
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        pdf_bytes = r.content

        reader = PdfReader(BytesIO(pdf_bytes))
        first_page = reader.pages[0].extract_text() if reader.pages else ""

        text = first_page.strip() if first_page else ""

        if not text:
            images = convert_from_bytes(pdf_bytes, first_page=0, last_page=1)
            if images:
                text = pytesseract.image_to_string(images[0])

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            title = lines[0]
            for l in lines:
                match = re.search(r"(\d{1,2}\s+[A-Za-z]+\s+20\d{2})", l)
                if match:
                    date = match.group(1)
                    break

    except Exception as e:
        print("Error extracting title/date:", e)
        title = url.split("/")[-1]

    cache[url] = {"title": title, "date": date, "time": now}
    return title, date

def categorise_entry(title: str):
    if not title:
        return "Other"
    t = title.lower()
    if "amendment act" in t or "act" in t:
        return "Act"
    if "rule" in t:
        return "Rules"
    if "regulation" in t:
        return "Regulations"
    if "notification" in t:
        return "Notifications"
    if "report" in t or "committee" in t:
        return "Reports"
    if "circular" in t or "guideline" in t:
        return "Circulars & Guidelines"
    if "treatise" in t or "code" in t:
        return "Treatises"
    return "Other"
