import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
FERNET_KEY = os.getenv("FERNET_KEY")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
PROXY_URL = os.getenv("PROXY_URL", "")
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "/tmp/reply_contact_report_extraction"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
