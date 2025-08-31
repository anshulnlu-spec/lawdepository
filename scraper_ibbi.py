import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import extract_title_date_from_pdf

BASE_URL = "https://ibbi.gov.in"

def scrape_ibbi():
    results = []
    url = f"{BASE_URL}/legal-framework"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # All PDF links on the page
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".pdf"):
                link = urljoin(BASE_URL, href)

                # Only keep IBC-related documents
                text = a.get_text(strip=True)
                if not any(word in text.lower() for word in ["insolvency", "bankruptcy"]):
                    continue

                # Extract title + date from PDF (OCR fallback if scanned)
                title, date = extract_title_date_from_pdf(link)

                # Categorise
                category = "Other"
                if "rule" in text.lower():
                    category = "Rules"
                elif "regulation" in text.lower():
                    category = "Regulations"
                elif "circular" in text.lower() or "guideline" in text.lower():
                    category = "Circulars & Guidelines"

                results.append({
                    "title": title or text,
                    "date": date,
                    "link": link,
                    "source": "IBBI",
                    "category": category
                })
    except Exception as e:
        print("Error scraping IBBI:", e)
    return results
