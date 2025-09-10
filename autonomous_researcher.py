import logging
import sys
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import database
import analysis

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RESEARCH_MISSIONS = [
    "Insolvency and Bankruptcy Law in India",
    "The Companies Act in India"
]

def find_authoritative_sources(topic):
    """AI brainstorms sources for a legal topic."""
    logging.info(f"AI is brainstorming sources for: '{topic}'...")
    try:
        # Configure Gemini API
        api_key = analysis.get_gemini_key()
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are a world-class legal researcher. Your task is to identify the best online sources for a legal topic.
        List the top 5 most authoritative, primary source websites for monitoring the topic: "{topic}".
        Focus on official government portals, regulatory bodies, and parliamentary sites. Avoid news articles and blogs.
        Return your answer as a Python list of URLs. For example: ["https://site1.gov.in", "https://site2.org"]
        Return ONLY the Python list.
        """
        response = model.generate_content(prompt)
        url_list_str = response.text.strip().replace("`", "").replace("python", "")
        import ast
        source_urls = ast.literal_eval(url_list_str)
        logging.info(f"AI identified the following sources: {source_urls}")
        return source_urls
    except Exception as e:
        logging.error(f"AI failed to brainstorm sources. Error: {e}")
        return []

def run_autonomous_research_cycle():
    """Main research cycle function."""
    logging.info("--- Starting new AUTONOMOUS AI research cycle ---")
    
    try:
        database.connect_and_init_db()
        db = next(database.get_db())
        
        try:
            existing_urls_query = db.query(database.Document.url).all()
            existing_urls = {url for (url,) in existing_urls_query}
            logging.info(f"Found {len(existing_urls)} documents already in the database.")
            
            for mission_topic in RESEARCH_MISSIONS:
                logging.info(f"--- Starting mission: {mission_topic} ---")
                source_urls = find_authoritative_sources(mission_topic)
                
                if not source_urls:
                    logging.warning("Could not find sources for this mission. Skipping.")
                    continue
                    
                for source_url in source_urls:
                    try:
                        discovered_links = analysis.scrape_links_from_url(source_url)
                        new_links = [link for link in discovered_links if link not in existing_urls]
                        
                        if not new_links:
                            logging.info(f"  No new documents found at {source_url}")
                            continue
                            
                        logging.info(f"  Found {len(new_links)} new documents to analyze from {source_url}...")
                        
                        for link in new_links:
                            try:
                                is_valid, content_type = analysis.validate_link(link)
                                if is_valid:
                                    details = analysis.analyze_document_content(link, "India", mission_topic, content_type)
                                    if details and details.get("is_relevant"):
                                        logging.info(f"      SUCCESS: AI confirmed document is relevant. Title: '{details.get('title')}'")
                                        
                                        db_doc = database.Document(
                                            url=link, 
                                            title=details.get("title", "Title not available"),
                                            publication_date=details.get("date"), 
                                            summary=details.get("summary"),
                                            category=details.get("category", "Uncategorized"), 
                                            jurisdiction="India",
                                            content_type=content_type, 
                                            topic=mission_topic
                                        )
                                        db.add(db_doc)
                                        db.commit()
                                        existing_urls.add(link)
                            except Exception as e:
                                logging.error(f"Error processing link {link}: {e}")
                                continue
                                
                    except Exception as e:
                        logging.error(f"Error processing source {source_url}: {e}")
                        continue
                        
        except Exception as e:
            logging.critical(f"FATAL ERROR during autonomous research cycle: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}", exc_info=True)
        raise
        
    logging.info("--- Autonomous AI research cycle finished ---")

def main(request):
    """
    Cloud Function HTTP entry point.
    Args:
        request: The HTTP request object.
    Returns:
        A response indicating success or failure.
    """
    try:
        run_autonomous_research_cycle()
        return {"status": "completed", "message": "Research cycle finished successfully"}
    except Exception as e:
        logging.error(f"Function execution failed: {e}")
        return {"status": "error", "message": str(e)}, 500

# For local testing
if __name__ == "__main__":
    run_autonomous_research_cycle()
