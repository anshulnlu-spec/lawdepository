# tasks.py - small helper wrappers for scheduled/background tasks
import logging
import database
import autonomous_researcher

logger = logging.getLogger(__name__)

def run_and_store(topic: str):
    database.connect_and_init_db()
    db_gen = database.get_db()
    db = next(db_gen)
    try:
        result = autonomous_researcher.run_autonomous_research_cycle(topic, db=db)
        return result
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
