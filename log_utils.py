from logging_service import write_log


def log_event(
    session_id: str | None,
    method: str,
    message: str,
    level: str = "INFO",
    script: str = "api_server",
):
    """
    Used inside api_server's own functions. If no session_id was supplied
    by the caller (e.g. a request that didn't include the X-Session-Id
    header), logs go to a shared 'unscoped' bucket rather than being dropped,
    so nothing is silently lost.
    """
    write_log(
        session_id=session_id or "unscoped",
        source="api_server",
        script=script,
        method=method,
        message=message,
        level=level,
    )
