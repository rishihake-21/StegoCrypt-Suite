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

def get_logs(count: int = 20) -> list:
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

def get_log_stats() -> dict:
    """Get statistics from all logs."""
    if not os.path.exists(LOG_FILE):
        return {
            "total_operations": 0,
            "files_processed": 0,
            "recent_logs": [],
        }
    
    log_entries = []
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    if line.strip():
                        log_entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    # Optionally log this error to a separate file for debugging
                    continue
    except Exception:
        # Handle file reading errors
        return {
            "total_operations": 0,
            "files_processed": 0,
            "recent_logs": [],
        }

    total_operations = len(log_entries)
    files_processed = sum(1 for log in log_entries if log.get("details", {}).get("filename"))
    
    return {
        "total_operations": total_operations,
        "files_processed": files_processed,
        "recent_logs": log_entries[-20:],
    }

def clear_logs():
    """Clear all logs"""
    try:
        with open(LOG_FILE, 'w') as f:
            f.write("")
        return True
    except Exception:
        return False
