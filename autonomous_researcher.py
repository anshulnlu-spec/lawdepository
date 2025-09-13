import logging
import sys
import google.generativeai as genai

# Import your existing project files
import database
import analysis

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- The AI's Mission ---
RESEARCH_MISSIONS = [
    "Insolvency and Bankruptcy Law in India",
    "The Companies Act in India",
    "Real Estate (Regulation and Development) Act, RERA in India"
]
# -------------------------

def find_authoritative_sources(topic):
    """Uses Gemini to brainstorm a list of high-quality source websites."""
    logging.info(f"AI is brainstorming sources for: '{topic}'...")
    try:
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
    """The main function for the autonomous AI researcher."""
    logging.info("--- Starting new AUTONOMOUS AI research cycle ---")
    
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

            for source_url in analysis.scrape_links_from_url(source_url):
                if source_url not in existing_urls:
                    logging.info(f"    -> Analyzing new link: {source_url}")
                    is_valid, content_type = analysis.validate_link(source_url)
                    if is_valid:
                        details = analysis.analyze_document_content(source_url, "India", mission_topic, content_type)
                        
                        if details and details.get("is_relevant"):
                            logging.info(f"      SUCCESS: AI confirmed document is relevant. Title: '{details.get('title')}'")
                            db_doc = database.Document(
                                url=source_url, title=details.get("title", "Title not available"),
                                publication_date=details.get("date"), summary=details.get("summary"),
                                category=details.get("category", "Uncategorized"), jurisdiction="India",
                                content_type=content_type, topic=mission_topic
                            )
                            db.add(db_doc)
                            db.commit()
                            existing_urls.add(source_url)
    except Exception as e:
        logging.critical(f"FATAL ERROR during autonomous research cycle: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        logging.info("--- Autonomous AI research cycle finished ---")

# --- This is the corrected section ---
# This tells the script: "if you are run directly, then start the research cycle."
# It removes the need for a special Cloud Function signal.
if __name__ == "__main__":
    run_autonomous_research_cycle()
