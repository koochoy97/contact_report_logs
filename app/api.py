"""FastAPI endpoints for extraction logs + serves frontend static files."""
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.db import engine

app = FastAPI(title="Contact Report Extraction Logs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


@app.get("/api/runs")
def list_runs(
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
):
    """List pipeline runs with summary stats."""
    where_clauses = []
    params = {}

    if date_from:
        where_clauses.append("created_at >= CAST(:date_from AS date)")
        params["date_from"] = date_from
    if date_to:
        where_clauses.append("created_at < CAST(:date_to AS date) + interval '1 day'")
        params["date_to"] = date_to

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT
            run_id,
            MIN(created_at) AS started_at,
            MAX(created_at) AS finished_at,
            COUNT(*) FILTER (WHERE status = 'scraping_done') AS clients_ok,
            COUNT(*) FILTER (WHERE status = 'scraping_failed') AS clients_failed,
            BOOL_OR(status = 'transform_done') AS transform_ok,
            MAX(CASE WHEN status = 'transform_done' THEN rows_count END) AS total_rows
        FROM core.contact_report_extraction_logs
        {where_sql}
        GROUP BY run_id
        ORDER BY MIN(created_at) DESC
    """

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [
        {
            "run_id": str(r[0]),
            "started_at": r[1].isoformat() if r[1] else None,
            "finished_at": r[2].isoformat() if r[2] else None,
            "clients_ok": r[3],
            "clients_failed": r[4],
            "transform_ok": r[5] or False,
            "total_rows": r[6],
        }
        for r in rows
    ]


@app.get("/api/runs/{run_id}/logs")
def get_run_logs(run_id: str):
    """Get all log entries for a specific run."""
    query = """
        SELECT id, run_id, client_id, client, status, rows_count,
               error_message, created_at
        FROM core.contact_report_extraction_logs
        WHERE run_id = :run_id
        ORDER BY created_at ASC, id ASC
    """

    with engine.connect() as conn:
        rows = conn.execute(text(query), {"run_id": run_id}).fetchall()

    return [
        {
            "id": r[0],
            "run_id": str(r[1]),
            "client_id": r[2],
            "client": r[3],
            "status": r[4],
            "rows_count": r[5],
            "error_message": r[6],
            "created_at": r[7].isoformat() if r[7] else None,
        }
        for r in rows
    ]


# Serve frontend static files (production build)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """SPA fallback — serve index.html for any non-API route."""
        return FileResponse(FRONTEND_DIST / "index.html")
