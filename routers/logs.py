from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional

from logging_service import write_log, list_log_files, read_log_file

router = APIRouter(prefix="/logs", tags=["Logging"])


class LogEntry(BaseModel):
    session_id: str
    source: str          # "frontend" | "mcp_server" | "api_server"
    script: str            # filename, e.g. "chat.html"
    method: str             # function/handler name
    message: str
    level: Optional[str] = "INFO"


@router.post("")
def submit_log(entry: LogEntry):
    """
    Called by:
    - frontend/js/logger.js (fetch, no auth required - logging must never
      fail a user action, even if their token just expired)
    - mcp_server/log_utils.py (httpx, same reasoning)
    The API server's own code calls write_log() directly instead of hitting
    this endpoint over HTTP, to avoid an unnecessary network round trip.
    """
    write_log(
        session_id=entry.session_id,
        source=entry.source,
        script=entry.script,
        method=entry.method,
        message=entry.message,
        level=entry.level or "INFO",
    )
    return {"status": "logged"}


@router.get("")
def list_logs():
    """Lists current log files (oldest first) - handy for the admin panel or manual inspection."""
    return list_log_files()


@router.get("/{session_id}")
def get_log(session_id: str):
    """Returns the full contents of one login session's log file."""
    content = read_log_file(session_id)
    if content is None:
        return {"detail": "No log file found for this session_id"}
    return {"session_id": session_id, "content": content}
