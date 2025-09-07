import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import database
import analysis

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment.")
genai.configure(api_key=GEMINI_API_KEY)

# Use a model that supports tool use (Google Search)
discovery_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[genai.Tool(google_search=genai.GoogleSearch())]
)

def discover_new_document_links():
    """Uses Gemini with Google Search to discover new, relevant document links."""
    print("Asking Gemini to discover new documents via Google Search...")
    try:
        prompt = """
        Using Google Search, find up to 15 recent (published in the last 30 days) and official documents, reports, or legislation related to "Insolvency and Bankruptcy law" from India, the United Kingdom, and the United States.

        Prioritize direct links to PDF files or official government web pages (URLs ending in .gov, .gov.in, .gov.uk, etc.). Avoid links to news articles or blogs.
        
        Return the findings as a JSON array where each object has two keys: "url" and "jurisdiction" (e.g., "India", "United Kingdom", "United States"). Ensure the URLs are well-formed.
        """
        response = discovery_model.generate_content(prompt)
        cleaned_text = response.text.strip().lstrip('```json').rstrip('```')
        discovered_links = json.loads(cleaned_text)
        print(f"Discovered {len(discovered_links)} potential new links.")
        return discovered_links
    except Exception as e:
        print(f"Error during Gemini link discovery: {e}")
        return []

def run_update_job():
    """The main task for the Cron Job."""
    print("Starting the AI document discovery and update job...")
    database.init_db()
    
    discovered_links = discover_new_document_links()
    new_links = database.get_new_links(discovered_links)
    
    if not new_links:
        print("No new documents to process. Job finished.")
        return

    print(f"Found {len(new_links)} new documents to analyze.")
    
    for link in new_links:
        print(f"Processing: {link['url']}")
        try:
            is_valid, content_type = analysis.validate_link(link['url'])
            if not is_valid:
                print(f"  -> Skipping invalid or broken link.")
                continue

            details = analysis.analyze_document_content(link['url'], link['jurisdiction'], content_type)
            if details and details.get("is_relevant"):
                database.add_document(
                    url=link['url'], title=details['title'],
                    publication_date=details['date'], summary=details['summary'],
                    category=details['category'], jurisdiction=link['jurisdiction'],
                    content_type=content_type
                )
                print(f"  -> Successfully added '{details['title']}' to the database.")
            else:
                print(f"  -> Document not relevant or analysis failed.")
        except Exception as e:
            print(f"  -> An error occurred processing {link['url']}: {e}")
            
    print("AI document discovery job completed successfully.")

if __name__ == "__main__":
    run_update_job()