"""
Logging utilities for StegoCrypt Suite
"""

import logging
import os
import json
from datetime import datetime

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "stegocrypt.log")

# Basic file handler for raw logs
handler = logging.FileHandler(LOG_FILE)
handler.setFormatter(logging.Formatter('%(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def log_operation(operation: str, status: str, details: dict = None):
    """Log an operation in a structured JSON format."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "status": status,
        "details": details or {}
    }
    logger.info(json.dumps(log_entry))

def get_logs(count: int = 15) -> list:
    """Get recent logs in a structured format."""
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        # Parse each line as JSON and return the last `count` entries
        log_entries = []
        for line in lines:
            try:
                log_entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                # Ignore malformed lines
                continue
        
        return log_entries[-count:]
    except FileNotFoundError:
        return []
    except Exception:
        return []

def clear_logs():
    """Clear all logs"""
    try:
        with open(LOG_FILE, 'w') as f:
            f.write("")
        return True
    except Exception:
        return False
