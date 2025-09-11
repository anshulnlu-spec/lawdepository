# autonomous_researcher.py
import re
import ast
import logging
from typing import List
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HAVE_GENAI = False
try:
    import google.generativeai as genai
    HAVE_GENAI = True
except Exception:
    try:
        import google_ai_generativelanguage as genai
        HAVE_GENAI = True
    except Exception:
        HAVE_GENAI = False

def _get_gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def safe_generate_urls_from_model(prompt: str) -> List[str]:
    key = _get_gemini_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    if not HAVE_GENAI:
        raise RuntimeError("Generative AI library not installed in container")

    try:
        genai.configure(api_key=key)
        model = "gemini-1.5"
        resp = genai.generate(model=model, input=prompt)
        text = ""
        if hasattr(resp, "output"):
            text = getattr(resp, "output")
            if isinstance(text, dict) and "content" in text:
                text = text["content"]
        if not text:
            text = getattr(resp, "text", "") or str(resp)
    except Exception as e:
        logger.exception("Model call failed")
        raise

    m = re.search(r"(\[(?:.|\s)*?\])", text)
    if not m:
        raise ValueError("Model output didn't contain a list literal")
    list_text = m.group(1)

    try:
        parsed = ast.literal_eval(list_text)
    except Exception as e:
        raise ValueError(f"Failed to parse model output as list: {e}")

    urls = [u for u in parsed if isinstance(u, str) and u.startswith(("http://", "https://"))]
    return urls

def simple_extract_document_links_from_page(url: str, max_links: int = 20) -> List[str]:
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
        full = requests.compat.urljoin(url, href)
        lower = full.lower()
        if any(keyword in lower for keyword in [".pdf", "/act", "/law", "/regulation", "/gazette", "/rules"]):
            links.append(full)
        if len(links) >= max_links:
            break
    return list(dict.fromkeys(links))

def find_authoritative_sources(topic: str) -> List[str]:
    prompt = (
        "Return a Python list literal of 5-15 authoritative URLs (strings) "
        f"for the topic: {topic}. Return ONLY the list, e.g. [\"https://...\", \"https://...\"]"
    )
    try:
        urls = safe_generate_urls_from_model(prompt)
        if urls:
            logger.info("Model returned %d candidate urls", len(urls))
            return urls
    except Exception as e:
        logger.warning("Model extraction failed: %s — falling back to heuristics", e)

    seeds = [
        "https://www.google.com/search?q=" + requests.utils.quote(topic + " site:gov"),
        "https://www.bing.com/search?q=" + requests.utils.quote(topic + " site:gov"),
    ]
    for seed in seeds:
        try:
            cands = simple_extract_document_links_from_page(seed, max_links=10)
            if cands:
                return cands
        except Exception:
            continue
    return []

def run_autonomous_research_cycle(topic: str, db=None) -> dict:
    result = {"topic": topic, "sources": [], "snippets": [], "errors": []}
    try:
        urls = find_authoritative_sources(topic)
        result["sources"] = urls
        for u in urls[:10]:
            try:
                r = requests.get(u, timeout=8)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                title = soup.title.string.strip() if soup.title else None
                result["snippets"].append({"url": u, "title": title})
            except Exception as e:
                result["snippets"].append({"url": u, "title": None, "error": str(e)})

        if db is not None:
            try:
                from database import Document
                for s in result["snippets"]:
                    url = s.get("url")
                    if not url:
                        continue
                    existing = db.query(Document).filter(Document.url == url).first()
                    if not existing:
                        doc = Document(url=url, title=s.get("title"), content=None)
                        db.add(doc)
                db.commit()
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass

        return result
    except Exception as e:
        logger.exception("Research cycle failed")
        result["errors"].append(str(e))
        return result

def main(request):
    try:
        data = request.get_json(silent=True) or {}
        topic = data.get("topic") or request.args.get("topic") or "autonomous research"
    except Exception:
        topic = request.args.get("topic") or "autonomous research"

    res = run_autonomous_research_cycle(topic, db=None)
    return (res, 200, {"Content-Type": "application/json"})
