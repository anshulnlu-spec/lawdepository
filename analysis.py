import os
import json
import requests
import google.generativeai as genai
from google.cloud import secretmanager

# --- Configuration ---
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
SECRET_ID = "gemini-api-key"

def get_gemini_key():
    """Fetches the Gemini API key from Google Cloud Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT_ID}/secrets/{SECRET_ID}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error fetching secret from Secret Manager: {e}")
        # Fallback for local testing (expects a .env file)
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("API key not found in Secret Manager or .env file.")
        return key

# --- Initialize Gemini Client ---
API_KEY = get_gemini_key()
genai.configure(api_key=API_KEY)
analysis_model = genai.GenerativeModel('gemini-1.5-flash')

def validate_link(url):
    """
    Checks if a link is valid and is a document (PDF/HTML).
    Uses a lightweight HEAD request to avoid downloading the full content.
    """
    print(f"  -> Validating link: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
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

def analyze_document_content(doc_url, jurisdiction, topic, content_type):
    """
    Analyzes a validated document's content using Gemini to extract structured information.
    """
    print(f"  -> Fetching content for AI analysis...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(doc_url, timeout=45, headers=headers)
        response.raise_for_status()

        prompt = f"""
        You are an expert legal analyst. A document from {jurisdiction} has been found related to the topic of "{topic}".
        Analyze its content and determine if it is substantively relevant.

        If it is relevant, provide the following details in a valid JSON format:
        1. "is_relevant": true
        2. "title": The official, full title of the document.
        3. "date": The publication or effective date (format as YYYY-MM-DD). If no specific date is found, use the closest available date.
        4. "summary": A concise, one-sentence summary of the document's main purpose or finding.
        5. "category": Classify the document as one of the following: "Legislation", "Regulation", "Case Law", "Official Notice", "Policy/Report", or "Bill".

        If the document is not relevant to the topic, return a JSON object with only one key: "is_relevant": false.
        
        Return ONLY the JSON object and nothing else.
        """
        
        if 'pdf' in content_type:
            content_part = genai.Part.from_data(data=response.content, mime_type="application/pdf")
        else: # Treat HTML and text as plain text for the model
            # A simple way to get text from HTML for analysis
            from io import BytesIO
            from lxml import html
            tree = html.fromstring(response.content)
            text_content = tree.text_content()
            content_part = text_content
            
        api_response = analysis_model.generate_content([prompt, content_part])
        
        # Clean the response to ensure it's valid JSON
        cleaned_text = api_response.text.strip().lstrip('```json').rstrip('```')
        details = json.loads(cleaned_text)
        return details

    except Exception as e:
        print(f"  -> Gemini analysis failed: {e}")
        return {"is_relevant": False}

