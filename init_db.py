# init_db.py
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.db import init_db
from backend.kb_ingest import ingest_from_folder

if __name__ == "__main__":
    init_db()
    ingest_from_folder()
    print("Initialization complete.")
