import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found.")
genai.configure(api_key=GEMINI_API_KEY)

analysis_model = genai.GenerativeModel('gemini-1.5-flash')

def validate_link(url):
    """
    Checks if a link is valid and returns its content type.
    Uses a HEAD request to avoid downloading the full content.
    """
    print(f"  -> Validating link: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, timeout=15, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            # Check if it is a document type we can process
            if 'pdf' in content_type or 'html' in content_type or 'text' in content_type:
                print(f"  -> Link is valid. Content-Type: {content_type}")
                return True, content_type
    except requests.RequestException as e:
        print(f"  -> Link validation failed: {e}")
    return False, None

def analyze_document_content(doc_url, jurisdiction, content_type):
    """Analyzes a validated document's content to extract structured information."""
    print(f"  -> Fetching content for analysis...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(doc_url, timeout=30, headers=headers)
        response.raise_for_status()

        prompt = f"""
        You are an expert legal analyst. The following document is from {jurisdiction}. Analyze its content and determine if it is substantively relevant to insolvency or bankruptcy law.

        If it is relevant, provide the following details in a JSON format:
        1. "is_relevant": true
        2. "title": The official title of the document.
        3. "date": The publication date (format as YYYY-MM-DD). If no specific date is found, estimate it.
        4. "summary": A concise, one-sentence summary of the document's purpose.
        5. "category": Classify it as "Legislation", "Regulation", "Case Law", "Official Notice", "Policy/Report", or "Bill".

        If not relevant, return JSON with "is_relevant": false. Return ONLY the JSON object.
        """
        
        if 'pdf' in content_type:
            content_part = {"mime_type": "application/pdf", "data": response.content}
        else: # Treat HTML and text as plain text
            content_part = response.text

        api_response = analysis_model.generate_content([prompt, content_part])
        cleaned_text = api_response.text.strip().lstrip('```json').rstrip('```')
        details = json.loads(cleaned_text)
        return details

    except Exception as e:
        print(f"  -> Gemini analysis failed: {e}")
        return {"is_relevant": False}