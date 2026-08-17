import json
import os
from datetime import datetime

HISTORY_FILE = "search_history.json"

def load_history():
    """Loads search history from local JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_search(query, summary, sources):
    """Saves a new research item to JSON history."""
    history = load_history()
    new_entry = {
        "id": len(history) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "summary": summary,
        "sources": sources
    }
    # Prepend new searches so the latest shows first
    history.insert(0, new_entry)
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)
        
    return history

def clear_history():
    """Wipes search history."""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return []