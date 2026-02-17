"""Load raw CSV into staging.contacts_report (no transformations)."""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.db import engine


def load_csv_to_staging(csv_path: Path, client_name: str) -> int:
    """
    Read CSV, add client column, DELETE existing rows for this client,
    then bulk INSERT into staging.contacts_report.

    Returns number of rows loaded.
    """
    df = pd.read_csv(csv_path, dtype=str)

    # Map CSV columns to staging schema
    column_map = {
        "Email": "email",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Account Name": "company",
        "Added On": "adding_date",
        "Sequence": "sequence",
    }

    # Only keep columns that exist in the CSV
    existing_cols = {k: v for k, v in column_map.items() if k in df.columns}
    df = df.rename(columns=existing_cols)
    df = df[[v for v in existing_cols.values()]]

    # Add client column
    df["client"] = client_name

    # Extract domain from email as company
    if "email" in df.columns:
        df["company"] = df["email"].str.split("@").str[1]

    # Parse adding_date if present
    if "adding_date" in df.columns:
        df["adding_date"] = pd.to_datetime(df["adding_date"], errors="coerce")

    # Parse reply_id as numeric
    if "reply_id" in df.columns:
        df["reply_id"] = pd.to_numeric(df["reply_id"], errors="coerce")

    with engine.begin() as conn:
        # Delete existing rows for this client (daily replacement)
        conn.execute(
            text("DELETE FROM staging.contacts_report WHERE client = :client"),
            {"client": client_name},
        )

        # Bulk insert
        df.to_sql(
            "contacts_report",
            conn,
            schema="staging",
            if_exists="append",
            index=False,
        )

    rows = len(df)
    print(f"[load] {client_name}: {rows} filas cargadas a staging")
    return rows
