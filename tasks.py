import os
import json
import google.generativeai as genai
import database
import analysis
from config import LEGISLATION_TOPICS

# This script is designed to be run in a Google Cloud environment.
# The analysis.py file handles fetching the API key securely.

# Initialize the model for link discovery
discovery_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[genai.Tool(google_search=genai.GoogleSearch())]
)

def discover_new_document_links():
    """
    Uses Gemini with Google Search to discover new, relevant document links
    for all topics defined in the config, prioritizing popular topics.
    """
    print("Asking Gemini to discover new documents via Google Search...")
    
    # Get the top 5 most clicked-on document titles to make the search smarter
    popular_docs = database.get_popular_topics()
    
    # Construct a dynamic, intelligent prompt for the AI
    prompt = f"""
    Using Google Search, perform a comprehensive search for recent (published in the last 45 days) and official documents, reports, or legislation related to the following legal topics: {', '.join(LEGISLATION_TOPICS)}.

    For your search, also consider finding updates or related documents for these known popular topics: {', '.join(popular_docs)}.

    Prioritize direct links to PDF files or official government web pages (e.g., URLs ending in .gov, .gov.in, .gov.uk). Avoid news articles, blogs, or commercial websites.

    Return the findings as a JSON array where each object has three keys:
    1. "url": The direct URL to the document.
    2. "jurisdiction": The country of origin ("India", "United Kingdom", or "United States").
    3. "topic": The specific legal topic from the list it relates to (e.g., "Companies Act").

    Ensure the URLs are well-formed. Find up to 20 relevant documents in total.
    """
    
    try:
        response = discovery_model.generate_content(prompt)
        # Clean the response to ensure it's a valid JSON string
        cleaned_text = response.text.strip().lstrip('```json').rstrip('```')
        discovered_links = json.loads(cleaned_text)
        print(f"Discovered {len(discovered_links)} potential new links across all topics.")
        return discovered_links
    except Exception as e:
        print(f"Error during Gemini link discovery: {e}")
        return []

def run_update_job():
    """
    The main task for the scheduled job. It orchestrates the entire
    process of discovering, analyzing, and storing new documents.
    """
    print("Starting the AI document discovery and update job...")
    database.init_db()  # Ensure the database and tables exist
    
    discovered_links = discover_new_document_links()
    
    # Filter out links that are already in our database
    new_links_to_process = database.get_new_links(discovered_links)
    
    if not new_links_to_process:
        print("No new, unique documents found to process. Job finished.")
        return

    print(f"Found {len(new_links_to_process)} new, unique documents to analyze.")
    
    for link_info in new_links_to_process:
        url = link_info['url']
        jurisdiction = link_info['jurisdiction']
        topic = link_info['topic']
        
        print(f"Processing: {url} for topic '{topic}'")
        try:
            # Step 1: Validate the link is real and is a document
            is_valid, content_type = analysis.validate_link(url)
            if not is_valid:
                print(f"  -> Skipping invalid or broken link.")
                continue

            # Step 2: Perform deep analysis on the document content
            details = analysis.analyze_document_content(url, jurisdiction, topic, content_type)
            
            # Step 3: If relevant, add to the database
            if details and details.get("is_relevant"):
                database.add_document(
                    url=url, title=details['title'],
                    publication_date=details['date'], summary=details['summary'],
                    category=details['category'], jurisdiction=jurisdiction,
                    content_type=content_type, topic=topic
                )
                print(f"  -> SUCCESS: Added '{details['title']}' to the database.")
            else:
                print(f"  -> Document was analyzed and found not relevant.")
        except Exception as e:
            print(f"  -> An unexpected error occurred while processing {url}: {e}")
            
    print("\n✅ AI document discovery job completed successfully.")

# This allows the script to be run directly for the initial setup in Cloud Build
if __name__ == "__main__":
    run_update_job()

