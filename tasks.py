# tasks.py — resilient update job
import os
import json
import google.generativeai as genai
import database
import analysis
from config import LEGISLATION_TOPICS

# Initialize discovery_model (keep as before)
discovery_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[genai.Tool(google_search=genai.GoogleSearch())]
)

def discover_new_document_links():
    # ... (same as before) ...
    print("Asking Gemini to discover new documents via Google Search...")
    try:
        popular_docs = database.get_popular_topics()
    except Exception:
        popular_docs = []
    # rest unchanged...
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
        cleaned_text = response.text.strip().lstrip('```json').rstrip('```')
        discovered_links = json.loads(cleaned_text)
        print(f"Discovered {len(discovered_links)} potential new links across all topics.")
        return discovered_links
    except Exception as e:
        print(f"Error during Gemini link discovery: {e}")
        return []

def run_update_job():
    print("Starting the AI document discovery and update job...")
    # Be tolerant: init_db may fail (e.g., secrets missing). Don't crash the process.
    try:
        database.init_db()
    except Exception as e:
        print(f"Warning: init_db failed (will continue). Error: {e}")

    discovered_links = discover_new_document_links()
    new_links_to_process = database.get_new_links(discovered_links)

    if not new_links_to_process:
        print("No new, unique documents found to process. Job finished.")
        return

    print(f"Found {len(new_links_to_process)} new, unique documents to analyze.")
    for link_info in new_links_to_process:
        url = link_info.get('url')
        jurisdiction = link_info.get('jurisdiction')
        topic = link_info.get('topic')
        print(f"Processing: {url} for topic '{topic}'")
        try:
            is_valid, content_type = analysis.validate_link(url)
            if not is_valid:
                print(f"  -> Skipping invalid or broken link.")
                continue

            details = analysis.analyze_document_content(url, jurisdiction, topic, content_type)

            if details and details.get("is_relevant"):
                # add_document now accepts topic
                try:
                    database.add_document(
                        url=url,
                        title=details.get('title', 'Untitled'),
                        publication_date=details.get('date'),
                        summary=details.get('summary'),
                        category=details.get('category'),
                        jurisdiction=jurisdiction,
                        content_type=content_type,
                        topic=topic
                    )
                    print(f"  -> SUCCESS: Added '{details.get('title')}' to the database.")
                except Exception as e:
                    print(f"  -> DB insert failed for {url}: {e}")
            else:
                print(f"  -> Document was analyzed and found not relevant.")
        except Exception as e:
            print(f"  -> An unexpected error occurred while processing {url}: {e}")

    print("\n✅ AI document discovery job completed successfully.")

if __name__ == "__main__":
    run_update_job()
