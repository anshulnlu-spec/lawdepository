import os
import json
import requests
import google.generativeai as genai

# Secret Manager is optional and used in GCP; fallback to .env for local dev
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except Exception:
    SECRET_MANAGER_AVAILABLE = False

# Configuration
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
SECRET_ID = os.environ.get("GEMINI_SECRET_NAME", "gemini-api-key")

def get_gemini_key():
    """
    Try to fetch Gemini API key from Secret Manager if possible.
    If that fails, fall back to loading from a local .env (GEMINI_API_KEY).
    If both fail, raise a clear error.
    """
    # Try Secret Manager only if google-cloud-secret-manager is installed and project is set
    if SECRET_MANAGER_AVAILABLE and GCP_PROJECT_ID:
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{GCP_PROJECT_ID}/secrets/{SECRET_ID}/versions/latest"
            response = client.access_secret_version(name=name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            # log and fallback
            print(f"[analysis.get_gemini_key] Secret Manager fetch failed: {e}")

    # fallback to .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    key = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
    if not key:
        raise ValueError("Gemini API key not found in Secret Manager or environment (.env). Set GEMINI_API_KEY or configure Secret Manager.")
    return key

# Configure genai client
API_KEY = get_gemini_key()
genai.configure(api_key=API_KEY)
analysis_model = genai.GenerativeModel('gemini-1.5-flash')

# Optional: lxml for robust HTML parsing
try:
    from lxml import html as lxml_html
    LXML_AVAILABLE = True
except Exception:
    LXML_AVAILABLE = False

def validate_link(url):
    """
    Lightweight HEAD request to validate a link appears to be a document (PDF/HTML/text).
    Returns (is_valid: bool, content_type or None)
    """
    print(f"  -> Validating link: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, timeout=15, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type or 'html' in content_type or 'text' in content_type:
                print(f"  -> Link is valid. Content-Type: {content_type}")
                return True, content_type
            else:
                print(f"  -> Skipping non-document link. Content-Type: {content_type}")
                return False, None
        else:
            print(f"  -> Link returned status code {response.status_code}")
            return False, None
    except requests.RequestException as e:
        print(f"  -> Link validation failed with network error: {e}")
        return False, None

def _extract_text_from_html_bytes(raw_bytes):
    """
    Attempt to extract readable text from raw HTML bytes.
    Uses lxml if available; otherwise falls back to a naive decode & strip.
    """
    try:
        if LXML_AVAILABLE:
            tree = lxml_html.fromstring(raw_bytes)
            return tree.text_content()
        else:
            text = raw_bytes.decode('utf-8', errors='ignore')
            # very naive: strip tags (not ideal, but safe fallback)
            import re
            cleaned = re.sub(r'<[^>]+>', ' ', text)
            return cleaned
    except Exception as e:
        print(f"  -> HTML to text extraction failed: {e}")
        return ""

def analyze_document_content(doc_url, jurisdiction, topic, content_type):
    """
    Fetch document content and ask Gemini to analyze it.
    Returns a dict with at minimum {"is_relevant": bool}.
    """
    print(f"  -> Fetching content for AI analysis: {doc_url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(doc_url, timeout=60, headers=headers)
        response.raise_for_status()

        # Prepare model input: either binary pdf part or plain text extracted
        if content_type and 'pdf' in content_type:
            # send bytes to model if supported by SDK
            try:
                content_part = genai.Part.from_data(data=response.content, mime_type="application/pdf")
            except Exception:
                # If SDK doesn't support Part or fails, try fallback to text extraction (best-effort)
                content_part = _extract_text_from_html_bytes(response.content)
        else:
            # HTML or text: extract text
            content_part = _extract_text_from_html_bytes(response.content)

        prompt = f"""
You are an expert legal analyst. A document from {jurisdiction} has been found related to the topic of "{topic}".
Analyze its content and determine if it is substantively relevant.

If it is relevant, provide a JSON object:
{{"is_relevant": true, "title": "...", "date": "YYYY-MM-DD", "summary": "...", "category": "..."}}

If not relevant, return: {{"is_relevant": false}}

Return ONLY the JSON object.
"""
        # Use the SDK generate_content helper
        api_response = analysis_model.generate_content([prompt, content_part])
        text = getattr(api_response, "text", "") or str(api_response)
        cleaned_text = text.strip().lstrip('```json').rstrip('```').strip()
        try:
            details = json.loads(cleaned_text)
            return details
        except Exception as e:
            print(f"  -> Failed to parse model output as JSON: {e}. Output was: {cleaned_text[:400]}")
            return {"is_relevant": False}
    except Exception as e:
        print(f"  -> Gemini analysis failed: {e}")
        return {"is_relevant": False}
