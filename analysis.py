import os
import json
import requests
import google.generativeai as genai
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# --- Secret Manager and Configuration ---
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
SECRET_ID = os.environ.get("GEMINI_SECRET_NAME", "gemini-api-key")

def get_gemini_key():
    """Fetches Gemini API key from Secret Manager or environment variables."""
    if SECRET_MANAGER_AVAILABLE and GCP_PROJECT_ID:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{GCP_PROJECT_ID}/secrets/{SECRET_ID}/versions/latest"
            response = client.access_secret_version(name=name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Secret Manager fetch failed: {e}. Falling back to .env.")

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("Gemini API key not found in Secret Manager or environment variables.")
    return key

# Configure genai client
API_KEY = get_gemini_key()
genai.configure(api_key=API_KEY)
analysis_model = genai.GenerativeModel('gemini-1.5-flash')

# --- Web Scraping and Validation ---

def scrape_links_from_url(base_url):
    """Visits a URL and finds all links to documents (PDFs) or other pages."""
    print(f"  Scraping URL: {base_url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(base_url, timeout=20, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            if full_url.lower().endswith(('.pdf', '.html', '.htm')):
                links.add(full_url)
        print(f"  Found {len(links)} potential links on the page.")
        return list(links)
    except requests.RequestException as e:
        print(f"  Could not scrape {base_url}. Reason: {e}")
        return []

def validate_link(url):
    """Validates if a link points to a document (PDF/HTML/text)."""
    print(f"  -> Validating link: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, timeout=15, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if any(doc_type in content_type for doc_type in ['pdf', 'html', 'text']):
                print(f"  -> Link is valid. Content-Type: {content_type}")
                return True, content_type
        print(f"  -> Link returned status code {response.status_code} or unsupported content-type.")
        return False, None
    except requests.RequestException as e:
        print(f"  -> Link validation failed with network error: {e}")
        return False, None

def _extract_text_from_html(html_content):
    """Extracts clean text from HTML content."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return " ".join(soup.stripped_strings)
    except Exception:
        return ""

# --- Gemini AI Analysis ---

def analyze_document_content(doc_url, jurisdiction, topic, content_type):
    """Fetch document content and ask Gemini to analyze it."""
    print(f"  -> Fetching content for AI analysis: {doc_url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(doc_url, timeout=60, headers=headers)
        response.raise_for_status()

        if 'pdf' in content_type:
            content_part = genai.Part.from_data(data=response.content, mime_type="application/pdf")
        else:
            text_content = _extract_text_from_html(response.content)
            content_part = text_content

        prompt = f"""
        You are an expert legal analyst. A document from {jurisdiction} has been found related to the topic of "{topic}".
        Analyze its content and determine if it is substantively relevant.

        If it is relevant, provide a JSON object with a common-sense title, a well-written one-paragraph summary, the publication date (YYYY-MM-DD), and a precise category (e.g., "Committee Report", "Draft Bill", "Enacted Legislation", "Parliamentary Debate", "Case Law").
        Example format:
        {{"is_relevant": true, "title": "...", "summary": "...", "date": "YYYY-MM-DD", "category": "..."}}

        If it is not relevant, return: {{"is_relevant": false}}

        Return ONLY the JSON object.
        """
        api_response = analysis_model.generate_content([prompt, content_part])
        cleaned_text = api_response.text.strip().lstrip('```json').rstrip('```').strip()
        
        details = json.loads(cleaned_text)
        return details
    except Exception as e:
        print(f"  -> Gemini analysis failed: {e}")
        return {"is_relevant": False}
