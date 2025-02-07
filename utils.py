import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def load_json(file):
    """Load JSON data from a file with error handling."""
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            logging.warning(f"⚠️ Error: Corrupt {file}, resetting file.")
            return {}
    return {}

def save_json(file, data):
    """Save JSON data to a file."""
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def ensure_folder(folder):
    """Ensure a directory exists."""
    if not os.path.exists(folder):
        os.makedirs(folder)
