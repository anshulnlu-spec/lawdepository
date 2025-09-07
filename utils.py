import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env file for local development
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # This message will show in logs if the key is missing in Render's environment
    print("WARNING: GEMINI_API_KEY not found in environment. The API calls will fail.")
else:
    # Configure the API key only if it exists
    genai.configure(api_key=GEMINI_API_KEY)

# Use a model that supports multimodal inputs
model = genai.GenerativeModel('gemini-1.5-flash')

def get_cache(law_name):
    """Loads the cache file for a given law."""
    cache_file = f"{law_name}_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}

def save_cache(law_name, cache):
    """Saves data to the cache file."""
    cache_file = f"{law_name}_cache.json"
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

def extract_details_from_pdf(pdf_url, law_name):
    """
    Extracts title, date, and category from a PDF URL using Gemini, with caching.
    """
    # The incorrect check 'if not genai.api_key:' has been removed from here.

    if not GEMINI_API_KEY:
        return "API key not configured", "N/A", "N/A"

    cache = get_cache(law_name)
    if pdf_url in cache:
        print(f"✅ Returning cached data for {pdf_url}")
        return cache[pdf_url]['title'], cache[pdf_url]['date'], cache[pdf_url]['category']

    print(f"⚙️ Processing new URL: {pdf_url}")
    try:
        # 1. Fetch the PDF content
        response = requests.get(pdf_url)
        response.raise_for_status()
        pdf_content = response.content

        # 2. Prepare the prompt for Gemini
        prompt = """
        Analyze the first page of this document and provide the following details in a JSON format:
        1. "title": The official title of the document.
        2. "date": The publication or notification date (format as YYYY-MM-DD).
        3. "category": Classify this document into one of the following: 'Act', 'Rules', 'Regulation', 'Notification', 'Amendment', 'Report', or 'Order'.
        
        Return ONLY the JSON object.
        """

        # 3. Call the Gemini API with the PDF content
        pdf_file = {"mime_type": "application/pdf", "data": pdf_content}
        api_response = model.generate_content([prompt, pdf_file])
        
        # 4. Parse the JSON response
        result_json = json.loads(api_response.text.strip('` \\njson'))
        
        title = result_json.get("title", "Title not found")
        date = result_json.get("date", "Date not found")
        category = result_json.get("category", "Uncategorized")

        # 5. Cache the new result
        cache[pdf_url] = {"title": title, "date": date, "category": category}
        save_cache(law_name, cache)

        return title, date, category

    except Exception as e:
        print(f"Error processing {pdf_url}: {e}")
        return "Error processing document", "N/A", "N/A"
