"""Anti-detection utilities: random delays, User-Agent rotation, viewport variation."""
import asyncio
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def random_viewport() -> dict:
    base_w, base_h = 1920, 1080
    return {
        "width": base_w + random.randint(-50, 50),
        "height": base_h + random.randint(-50, 50),
    }


async def random_delay(min_sec: float, max_sec: float):
    delay = random.uniform(min_sec, max_sec)
    print(f"[rate_limit] Esperando {delay:.1f}s...")
    await asyncio.sleep(delay)


async def backoff_delay(attempt: int, base: float = 5.0, max_delay: float = 300.0):
    delay = min(base * (2 ** attempt), max_delay)
    delay += random.uniform(0, delay * 0.2)  # jitter
    print(f"[rate_limit] Backoff intento {attempt}: {delay:.1f}s")
    await asyncio.sleep(delay)
