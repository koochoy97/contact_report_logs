"""Orchestrate extraction from core.clientes with parallelism."""
import asyncio
from collections import defaultdict
from datetime import datetime

from sqlalchemy import text

from app.config import DOWNLOAD_DIR, MAX_WORKERS, PROXY_URL
from app.db import engine
from app.scraper.reply_io import download_contacts_csv
from app.pipeline.load import load_csv_to_staging
from app.pipeline.transform import transform_staging_to_core
from app.pipeline.logger import new_run_id, log_event
from app.utils.crypto import decrypt
from app.utils.rate_limit import random_delay, backoff_delay


def _get_active_clients() -> list[dict]:
    """Fetch clients from core.clientes that have credentials and team_id."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, cliente, reply_mail, reply_password, team_id "
            "FROM core.clientes "
            "WHERE reply_mail IS NOT NULL "
            "AND reply_password IS NOT NULL "
            "AND team_id IS NOT NULL "
            "AND status != 'Archived'"
        )).fetchall()

    return [
        {
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "password_encrypted": r[3],
            "team_id": r[4],
        }
        for r in rows
    ]


async def run_pipeline():
    """Full ELT pipeline: extract all accounts → load staging → transform core."""
    run_id = new_run_id()
    log_event(run_id, "pipeline_started")
    print(f"[extract] Pipeline iniciado (run_id={run_id})")

    clients = _get_active_clients()

    if not clients:
        print("[extract] No hay clientes con credenciales y team_id")
        log_event(run_id, "pipeline_completed", rows_count=0)
        return

    # Group clients by email (same login = same browser session)
    accounts = defaultdict(list)
    for client in clients:
        accounts[client["email"]].append(client)

    print(f"[extract] {len(accounts)} cuentas, {len(clients)} clientes")

    semaphore = asyncio.Semaphore(MAX_WORKERS)
    failed_clients = []

    async def process_account(email: str, account_clients: list[dict]):
        async with semaphore:
            password = decrypt(account_clients[0]["password_encrypted"])
            cookies = None

            print(f"[extract] Procesando cuenta: {email} ({len(account_clients)} workspaces)")

            for i, client in enumerate(account_clients):
                cid = client["id"]
                cname = client["name"]

                # Log scraping start
                log_event(run_id, "scraping", client_id=cid, client=cname)

                started_at = datetime.now()
                try:
                    download_dir = DOWNLOAD_DIR / cname.lower().replace(" ", "_")

                    # Log login attempt
                    log_event(run_id, "login_started", client_id=cid, client=cname)

                    csv_path, updated_cookies, login_status = await download_contacts_csv(
                        email=email,
                        password=password,
                        team_id=client["team_id"],
                        download_dir=download_dir,
                        cookies_json=cookies,
                        headless=True,
                        proxy_url=PROXY_URL or None,
                    )

                    # Log login result
                    log_event(run_id, login_status, client_id=cid, client=cname)

                    if updated_cookies:
                        cookies = updated_cookies

                    rows = load_csv_to_staging(csv_path, cname)
                    duration = int((datetime.now() - started_at).total_seconds())
                    print(f"[extract] {cname}: {rows} filas en {duration}s")

                    # Log successful scraping + load
                    log_event(run_id, "scraping_done", client_id=cid, client=cname, rows_count=rows)

                except Exception as e:
                    print(f"[extract] Error en {cname}: {e}")
                    failed_clients.append(client)
                    log_event(run_id, "scraping_failed", client_id=cid, client=cname, error_message=str(e))

                # Delay between workspaces (same account)
                if i < len(account_clients) - 1:
                    await random_delay(30, 60)

    # Launch all accounts in parallel (semaphore limits concurrent browsers)
    await asyncio.gather(*[
        process_account(email, accs)
        for email, accs in accounts.items()
    ])

    # Retry failed
    if failed_clients:
        await _retry_failed(failed_clients, run_id, max_retries=3)

    # Transform: staging → core + refresh materialized view
    try:
        log_event(run_id, "transform_started")
        rows = transform_staging_to_core()
        log_event(run_id, "transform_done", rows_count=rows)
    except Exception as e:
        log_event(run_id, "transform_failed", error_message=str(e))
        print(f"[extract] Error en transform: {e}")

    log_event(run_id, "pipeline_completed")
    print("[extract] Pipeline completado")


async def _retry_failed(failed_clients: list[dict], run_id: str, max_retries: int = 3):
    """Retry clients that failed."""
    print(f"[retry] Reintentando {len(failed_clients)} clientes fallidos...")

    for attempt in range(1, max_retries + 1):
        still_failed = []

        for client in failed_clients:
            cid = client["id"]
            cname = client["name"]
            log_event(run_id, "retry", client_id=cid, client=cname,
                      error_message=f"intento {attempt}")
            try:
                password = decrypt(client["password_encrypted"])
                download_dir = DOWNLOAD_DIR / cname.lower().replace(" ", "_")

                csv_path, _, login_status = await download_contacts_csv(
                    email=client["email"],
                    password=password,
                    team_id=client["team_id"],
                    download_dir=download_dir,
                    headless=True,
                    proxy_url=PROXY_URL or None,
                )

                rows = load_csv_to_staging(csv_path, cname)
                print(f"[retry] {cname} exitoso en intento {attempt}: {rows} filas")
                log_event(run_id, "scraping_done", client_id=cid, client=cname, rows_count=rows)

            except Exception as e:
                still_failed.append(client)
                print(f"[retry] {cname} falló intento {attempt}: {e}")
                log_event(run_id, "scraping_failed", client_id=cid, client=cname,
                          error_message=f"retry {attempt}: {e}")

        failed_clients = still_failed
        if not failed_clients:
            break

        await backoff_delay(attempt)
