"""Create schemas and tables for the ELT pipeline."""
from sqlalchemy import text

from app.db import engine
from app.models import Base


def run_migrations():
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS core"))

        # staging.reply_contacts — raw CSV data, truncated daily per client
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS staging.reply_contacts (
                id BIGSERIAL PRIMARY KEY,
                reply_id BIGINT,
                email TEXT,
                first_name TEXT,
                last_name TEXT,
                company TEXT,
                adding_date TIMESTAMP,
                client TEXT,
                sequence TEXT,
                loaded_at TIMESTAMP DEFAULT now()
            )
        """))

        # core.contacts — transformed with domain, deduplicated
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS core.contacts (
                id BIGSERIAL PRIMARY KEY,
                reply_id BIGINT,
                email TEXT,
                first_name TEXT,
                last_name TEXT,
                company TEXT,
                adding_date TIMESTAMP,
                client TEXT,
                domain TEXT,
                sequence TEXT,
                UNIQUE (reply_id, client)
            )
        """))

    # elt_accounts, elt_clients, elt_runs (public schema, via SQLAlchemy ORM)
    Base.metadata.create_all(engine)
    print("[migrate] Tablas creadas exitosamente")


if __name__ == "__main__":
    run_migrations()
