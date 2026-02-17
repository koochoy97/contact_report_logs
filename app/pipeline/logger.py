"""Pipeline logging to core.contact_report_extraction_logs."""
import uuid
from datetime import datetime

from sqlalchemy import text

from app.db import engine


def new_run_id() -> str:
    """Generate a new UUID for a pipeline run."""
    return str(uuid.uuid4())


def log_event(
    run_id: str,
    status: str,
    client_id: int | None = None,
    client: str | None = None,
    rows_count: int | None = None,
    error_message: str | None = None,
):
    """Insert a log row into core.contact_report_extraction_logs."""
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO core.contact_report_extraction_logs
                    (run_id, client_id, client, status, rows_count, error_message)
                VALUES
                    (:run_id, :client_id, :client, :status, :rows_count, :error_message)
            """),
            {
                "run_id": run_id,
                "client_id": client_id,
                "client": client,
                "status": status,
                "rows_count": rows_count,
                "error_message": error_message,
            },
        )
