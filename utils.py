import requests, hashlib, time
from io import BytesIO
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
import re

cache = {}

def extract_title_date_from_pdf(url):
    now = time.time()
    if url in cache and now - cache[url]["time"] < 7*24*3600:  # 7 day cache
        return cache[url]["title"], cache[url]["date"]

    title, date = None, None
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        pdf_bytes = r.content

        # Try text extraction
        reader = PdfReader(BytesIO(pdf_bytes))
        first_page = reader.pages[0].extract_text() if reader.pages else ""

        text = first_page.strip() if first_page else ""

        # If no text, run OCR
        if not text:
            images = convert_from_bytes(pdf_bytes, first_page=0, last_page=1)
            if images:
                text = pytesseract.image_to_string(images[0])

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            title = lines[0]
            # Try find date in any line
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

def deduplicate(entries):
    seen = set()
    categories = {}
    for e in entries:
        key = (e["title"], e.get("date"), e["link"])
        if key in seen:
            continue
        seen.add(key)
        cat = e.get("category", "Other")
        categories.setdefault(cat, []).append(e)
    return categories
