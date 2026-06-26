from __future__ import annotations

import asyncio
import os
from pathlib import Path

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

from playwright.async_api import async_playwright


def load_first_url() -> str:
    for line in Path("products.txt").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    raise SystemExit("products.txt does not contain a product URL.")


async def main() -> None:
    url = load_first_url()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(locale="tr-TR")
        await page.goto(url, wait_until="networkidle", timeout=90_000)
        title = await page.title()
        text = await page.locator("body").inner_text(timeout=10_000)
        print("TITLE:", title)
        print("TEXT_START")
        print(text[:4_000])
        print("TEXT_END")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
