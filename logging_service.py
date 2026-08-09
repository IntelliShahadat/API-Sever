"""
Central logging service. Owns the logs/ folder.

One log file per LOGIN SESSION - not per action. A session_id is generated
the moment a user logs in, stored in the browser (localStorage), and
attached to every request that follows - dashboard loads, chat messages,
admin actions - for as long as that user stays logged in. Every layer of
the stack (chat.html, dashboard.html, api.js, the MCP server, the API
server) writes into that SAME file via write_log(), either directly (this
process) or over HTTP through POST /logs (other processes). Logging out
ends the session; the next login gets a brand new session_id and therefore
a brand new file.

 Rotation: an index file (logs/_index.json) tracks session_ids in the order
they were first seen. Once more than MAX_LOG_FILES distinct sessions have
logged something, the oldest file is deleted.
"""
import os
import json
import threading
from datetime import datetime

LOG_DIR = os.getenv("LOG_DIR", "logs")
MAX_LOG_FILES = int(os.getenv("MAX_LOG_FILES", "20"))
INDEX_FILE = os.path.join(LOG_DIR, "_index.json")

_lock = threading.Lock()  # guards index read/modify/write + rotation


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _load_index() -> list[str]:
    if not os.path.exists(INDEX_FILE):
        return []
    try:
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_index(index: list[str]):
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f)


def _log_file_path(session_id: str) -> str:
    # Sanitize - session_id should be a UUID, but never trust client input
    # as a raw file path component.
    safe_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_"))
    return os.path.join(LOG_DIR, f"{safe_id}.log")


def write_log(
    session_id: str,
    source: str,       # "frontend" | "mcp_server" | "api_server"
    script: str,        # e.g. "chat.html", "agent.py"
    method: str,        # e.g. "run_chat", "handleSubmit"
    message: str,
    level: str = "INFO",
) -> None:
    _ensure_log_dir()
    timestamp = datetime.now().strftime("%d-%m-%Y  %H:%M:%S.%f")[:-3] # :-3 if for eleminating total of 6 digit miliseconds value's last three digits
    line = f"[{timestamp}] [{level:<5}] [{source}] {script}::{method} — {message}\n"

    with _lock:
        # Rotation bookkeeping: record this session_id as "seen" (once)
        index = _load_index()
        if session_id not in index:
            index.append(session_id)
            while len(index) > MAX_LOG_FILES:
                oldest_id = index.pop(0)
                oldest_path = _log_file_path(oldest_id)
                if os.path.exists(oldest_path):
                    os.remove(oldest_path)
            _save_index(index)

        # Append the actual log line
        with open(_log_file_path(session_id), "a", encoding="utf-8") as f:
            f.write(line)


def list_log_files() -> list[dict]:
    """Used by an optional admin view - lists current log files, oldest first."""
    _ensure_log_dir()
    index = _load_index()
    results = []
    for exec_id in index:
        path = _log_file_path(exec_id)
        if os.path.exists(path):
            results.append(
                {
                    "session_id": exec_id,
                    "size_bytes": os.path.getsize(path),
                    "modified_at": datetime.fromtimestamp(
                        os.path.getmtime(path), tz=timezone.utc
                    ).isoformat(),
                }
            )
    return results


def read_log_file(session_id: str) -> str | None:
    path = _log_file_path(session_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
