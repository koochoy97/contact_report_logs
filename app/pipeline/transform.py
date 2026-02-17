"""Transform staging.contacts_report → core.contacts_report + refresh materialized view."""
from sqlalchemy import text

from app.db import engine


def transform_staging_to_core() -> int:
    """Delete core data, insert from staging, refresh materialized view."""
    with engine.begin() as conn:
        # 1. Delete existing core data
        conn.execute(text("DELETE FROM core.contacts_report"))

        # 2. Insert from staging to core
        result = conn.execute(text("""
            INSERT INTO core.contacts_report (
                reply_id, email, domain, first_name, last_name,
                company, adding_date, client
            )
            SELECT
                reply_id,
                email,
                split_part(email, '@', 2) AS domain,
                first_name,
                last_name,
                company,
                adding_date,
                client
            FROM staging.contacts_report
        """))
        rows = result.rowcount
        print(f"[transform] {rows} filas insertadas en core.contacts_report")

        # 3. Refresh materialized view
        conn.execute(text("REFRESH MATERIALIZED VIEW core.contacts_report_with_periods_mv"))
        print("[transform] Materialized view refreshed")

    return rows
