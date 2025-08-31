import os, requests, time, re, json
from io import BytesIO
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

cache_file = "ibc_cache.json"

if os.path.exists(cache_file):
    with open(cache_file, "r") as f:
        cache = json.load(f)
else:
    cache = {}

def save_cache():
    with open(cache_file, "w") as f:
        json.dump(cache, f)

def extract_title_date_from_pdf(url, law_name="ibc"):
    now = time.time()
    if url in cache:
        return cache[url]["title"], cache[url]["date"], cache[url]["category"]

    text = ""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        pdf_bytes = r.content

        reader = PdfReader(BytesIO(pdf_bytes))
        if reader.pages:
            text = reader.pages[0].extract_text() or ""

        if not text.strip():
            images = convert_from_bytes(pdf_bytes, first_page=0, last_page=1)
            if images:
                text = pytesseract.image_to_string(images[0])
    except Exception as e:
        print("⚠️ Error fetching PDF:", e)

    title, date, category = None, None, None
    try:
        prompt = f"""
        You are a legal document metadata extractor.
        From the following PDF text, extract:
        1. Full official title of the legislation/notification/report.
        2. Date (if present).
        3. Category (choose: Act, Amendment Act, Rules, Regulations, Notification, Bill, Report, Treatise).
        Return JSON with keys: title, date, category.

        PDF text:
        {text[:4000]}
        """

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)

        match = re.search(r"\{.*\}", response.text, re.S)
        if match:
            parsed = json.loads(match.group(0))
            title = parsed.get("title")
            date = parsed.get("date")
            category = parsed.get("category")

    except Exception as e:
        print("⚠️ Gemini classification failed:", e)

    if not title:
        title = url.split("/")[-1]

    cache[url] = {"title": title, "date": date, "category": category, "time": now}
    save_cache()
    return title, date, category
