"""Playwright scraper for Reply.io — downloads People (contacts) CSV with cookie support."""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

from app.utils.rate_limit import random_user_agent, random_viewport


async def download_contacts_csv(
    email: str,
    password: str,
    team_id: int,
    download_dir: Path,
    cookies_json: str | None = None,
    headless: bool = True,
    proxy_url: str | None = None,
) -> tuple[Path, str | None, str]:
    """
    Download the People CSV (Basic fields) from a Reply.io workspace.

    Uses cookies when available to skip login (anti-detection).
    Returns: (csv_path, updated_cookies_json or None, login_status)
    login_status: 'login_done' | 'login_skipped'
    """
    download_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        launch_opts = {"headless": headless}
        if proxy_url:
            launch_opts["proxy"] = {"server": proxy_url}

        browser = await p.chromium.launch(**launch_opts)

        # Anti-fingerprinting: random UA + viewport + timezone
        context_opts = {
            "viewport": random_viewport(),
            "user_agent": random_user_agent(),
            "timezone_id": "America/Lima",
            "accept_downloads": True,
        }

        # Load cookies if available
        if cookies_json:
            try:
                storage_state = json.loads(cookies_json)
                context_opts["storage_state"] = storage_state
                print(f"[scraper] Cargando cookies para {email}")
            except (json.JSONDecodeError, TypeError):
                print(f"[scraper] Cookies inválidas para {email}, haciendo login")

        context = await browser.new_context(**context_opts)
        page = await context.new_page()

        # Navigate — cookies should keep us logged in
        await page.goto("https://run.reply.io/", wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(3)

        # Check if we need to login
        needs_login = "oauth" in page.url or "login" in page.url.lower()
        login_status = "login_skipped"
        if needs_login:
            print(f"[scraper] Login requerido para {email}")
            await _do_login(page, email, password)
            login_status = "login_done"

        # Switch workspace
        print(f"[scraper] Cambiando a workspace {team_id}...")
        await page.goto(
            f"https://run.reply.io/Home/SwitchTeam?teamId={team_id}",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await asyncio.sleep(8)

        # Download People CSV
        csv_path = await _download_people_csv(page, download_dir)

        # Save updated cookies
        updated_cookies = None
        try:
            storage = await context.storage_state()
            updated_cookies = json.dumps(storage)
        except Exception as e:
            print(f"[scraper] No se pudieron guardar cookies: {e}")

        await browser.close()
        return csv_path, updated_cookies, login_status


async def _do_login(page, email: str, password: str):
    """Perform email/password login on Reply.io."""
    await page.locator("input:visible").first.fill(email)
    await page.locator('input[type="password"]:visible').fill(password)
    await page.get_by_role("button", name="Sign in").click()
    try:
        await page.wait_for_url("**/run.reply.io/**", timeout=20_000)
    except Exception:
        pass
    await asyncio.sleep(3)


async def _clear_overlays(page):
    """Remove popups, chat widgets, modals, and any overlay that could block clicks."""
    await page.evaluate("""() => {
        // Intercom chat widget
        document.querySelector('#intercom-container')?.remove();
        // Generic overlay/modal selectors
        const selectors = [
            '[class*="intercom"]', '[class*="modal-backdrop"]',
            '[class*="overlay"]', '[class*="popup"]',
            '[id*="intercom"]', '[id*="hubspot"]',
            '[id*="drift"]', '[id*="crisp"]',
            '[class*="banner"]', '[class*="cookie"]',
        ];
        for (const sel of selectors) {
            document.querySelectorAll(sel).forEach(el => {
                if (el.offsetHeight > 0 && getComputedStyle(el).position === 'fixed') {
                    el.remove();
                }
            });
        }
    }""")


async def _download_people_csv(page, download_dir: Path) -> Path:
    """People > All tab > Select All in list > More > Export to CSV > Basic fields."""

    await page.goto(
        "https://run.reply.io/Dashboard/Material#/people/list",
        wait_until="domcontentloaded",
        timeout=30_000,
    )
    await asyncio.sleep(5)

    # Remove overlays that block clicks (Intercom, modals, banners, etc.)
    await _clear_overlays(page)

    # Click "All" tab
    await page.locator('text=/^All\\s*\\(/').first.click(force=True)
    await asyncio.sleep(2)

    # Click the select-control-button dropdown
    await page.locator('[data-test-id="select-control-button"]').click(force=True)
    await asyncio.sleep(1)

    # Click "All in list"
    await page.locator("text=All in list").first.click(force=True)
    await asyncio.sleep(2)

    # Click "More" dropdown
    await page.locator('button:has-text("More"):visible').first.click(force=True)
    await asyncio.sleep(1)

    # Hover "Export to CSV"
    await page.locator("text=Export to CSV").hover(force=True)
    await asyncio.sleep(1)

    # Click "Basic fields" — triggers download
    async with page.expect_download(timeout=60_000) as download_info:
        await page.locator("text=/^Basic fields$/").first.click(force=True)

    download = await download_info.value
    dest = download_dir / "people.csv"
    await download.save_as(str(dest))
    print(f"[scraper] people.csv descargado: {dest.stat().st_size:,} bytes")
    return dest
