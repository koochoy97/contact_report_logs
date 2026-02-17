"""Entry point: APScheduler cron + API server + manual trigger."""
import asyncio
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.pipeline.extract import run_pipeline


def main():
    # Manual trigger: python3 -m app.main --now
    if "--now" in sys.argv:
        print("[main] Ejecutando pipeline manualmente...")
        asyncio.run(run_pipeline())
        return

    # API only (dev): python3 -m app.main --api
    if "--api" in sys.argv:
        import uvicorn
        from app.api import app
        print("[main] Iniciando API server en http://0.0.0.0:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
        return

    # Production: scheduler + API together
    import uvicorn
    from app.api import app

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(hour=0, minute=0, timezone="America/Lima"),
        id="daily_extraction",
        name="Extracción diaria de contactos Reply.io",
        replace_existing=True,
    )
    scheduler.start()
    print("[main] Scheduler iniciado — cron a las 00:00 America/Lima (05:00 UTC)")
    print("[main] API + Frontend en http://0.0.0.0:8001")

    uvicorn.run(app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main()
