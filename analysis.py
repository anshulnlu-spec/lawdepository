# analysis.py - helpers used by the research flow (web scraping / link extraction)
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

def scrape_links_from_url(url: str, keywords=None, max_links: int = 50):
    keywords = keywords or ["act", "law", "rule", "regulation", "gazette", ".pdf"]
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.debug("Failed to fetch %s: %s", url, e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#"):
            continue
        full = urljoin(url, href)
        lower = full.lower()
        if any(kw in lower for kw in keywords):
            links.append(full)
        if len(links) >= max_links:
            break

    return list(dict.fromkeys(links))
