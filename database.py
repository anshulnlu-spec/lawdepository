# (existing content you already have above — unchanged)
# ... [existing database.py content remains as previously patched] ...

# Add a simple get_item helper used by main.py's example endpoint
def get_item(item_id: int):
    """
    Return a document by primary key id, or a placeholder if not found.
    This helper is intentionally simple to support example endpoints without crashing.
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == item_id).first()
        if not doc:
            # return a fallback dict rather than raising to keep endpoint simple
            return {"id": item_id, "title": "not found", "message": "Document not found"}
        return {
            "id": doc.id,
            "url": doc.url,
            "title": doc.title,
            "publication_date": doc.publication_date,
            "summary": doc.summary,
            "category": doc.category,
            "jurisdiction": doc.jurisdiction,
            "content_type": doc.content_type,
            "topic": doc.topic,
        }
    finally:
        db.close()
