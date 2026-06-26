from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Sequence

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

from playwright.async_api import Browser, Page, async_playwright

from .detector import ProductSnapshot, StockStatus, detect_stock_status, extract_title
from .notifier import TelegramNotifier
from .storage import StateStore


logger = logging.getLogger(__name__)


class UnknownStockStatusError(RuntimeError):
    pass


class ZaraWatcher:
    def __init__(self, store: StateStore, notifier: TelegramNotifier) -> None:
        self._store = store
        self._notifier = notifier

    async def run(
        self,
        urls: Sequence[str],
        interval_seconds: int,
        once: bool = False,
        max_runs: int | None = None,
        notify_current: bool = False,
        headless: bool = True,
        browser_channel: str | None = None,
        browser_executable: str | None = None,
        fail_on_unknown: bool = False,
    ) -> None:
        async with async_playwright() as playwright:
            launch_options = {
                "headless": headless,
                "args": ["--disable-blink-features=AutomationControlled"],
            }
            if browser_channel:
                launch_options["channel"] = browser_channel
            if browser_executable:
                launch_options["executable_path"] = browser_executable

            browser = await playwright.chromium.launch(**launch_options)
            try:
                run_count = 0
                while True:
                    run_count += 1
                    logger.info("Starting polling cycle %s", run_count)
                    snapshots = await self.check_all(browser, urls, notify_current=notify_current)
                    unknown_urls = [snapshot.url for snapshot in snapshots if snapshot.status == StockStatus.UNKNOWN]
                    if fail_on_unknown and unknown_urls:
                        joined_urls = ", ".join(unknown_urls)
                        raise UnknownStockStatusError(f"Unknown stock status for: {joined_urls}")
                    if once or (max_runs is not None and run_count >= max_runs):
                        logger.info("Stopping after %s polling cycle(s)", run_count)
                        return
                    await asyncio.sleep(interval_seconds)
            finally:
                await browser.close()

    async def check_all(self, browser: Browser, urls: Sequence[str], notify_current: bool = False) -> list[ProductSnapshot]:
        page = await browser.new_page(
            locale="tr-TR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
        )
        snapshots: list[ProductSnapshot] = []
        try:
            for url in urls:
                try:
                    snapshot = await self._fetch_snapshot(page, url)
                    snapshots.append(snapshot)
                    await self._handle_snapshot(snapshot, notify_current=notify_current)
                    logger.info("Checked %s: %s%s", url, snapshot.status.value, f" ({snapshot.title})" if snapshot.title else "")
                except Exception:
                    logger.exception("Could not check %s", url)
        finally:
            await page.close()
        return snapshots

    async def _fetch_snapshot(self, page: Page, url: str) -> ProductSnapshot:
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await self._accept_cookies_if_present(page)
        await page.wait_for_timeout(2_000)
        html = await page.content()
        return ProductSnapshot(
            url=url,
            status=detect_stock_status(html),
            title=extract_title(html),
        )

    async def _handle_snapshot(self, snapshot: ProductSnapshot, notify_current: bool = False) -> None:
        previous = self._store.get(snapshot.url)
        should_notify = (
            snapshot.status == StockStatus.IN_STOCK
            and (
                notify_current
                or (previous is not None and previous.status == StockStatus.OUT_OF_STOCK)
            )
        )

        if snapshot.status != StockStatus.UNKNOWN:
            self._store.upsert(snapshot.url, snapshot.status, snapshot.title)

        if should_notify:
            await self._notifier.send_stock_alert(snapshot.title or previous.title, snapshot.url)
            logger.info("Sent stock alert for %s", snapshot.url)

    async def _accept_cookies_if_present(self, page: Page) -> None:
        cookie_buttons = [
            "button:has-text('Kabul')",
            "button:has-text('Accept')",
            "button:has-text('Tümünü kabul')",
            "button:has-text('Accept all')",
        ]
        for selector in cookie_buttons:
            locator = page.locator(selector).first
            try:
                if await locator.is_visible(timeout=1_000):
                    await locator.click(timeout=2_000)
                    return
            except Exception:
                continue
