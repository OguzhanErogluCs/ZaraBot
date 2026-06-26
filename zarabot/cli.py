from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from .config import load_settings
from .notifier import TelegramNotifier
from .storage import StateStore
from .watcher import ZaraWatcher


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description="Watch Zara product pages for stock changes.")
    parser.add_argument("--products", default="products.txt", help="Path to a text file with one product URL per line.")
    parser.add_argument("--interval", type=int, help="Polling interval in seconds. Overrides POLL_INTERVAL_SECONDS.")
    parser.add_argument("--database", help="SQLite database path. Overrides DATABASE_PATH.")
    parser.add_argument("--once", action="store_true", help="Check all products once and exit.")
    parser.add_argument("--max-runs", type=int, help="Stop after this many polling cycles. Useful for testing.")
    parser.add_argument("--headed", action="store_true", help="Open a visible browser window instead of headless mode.")
    parser.add_argument("--browser-channel", help="Playwright browser channel, for example chrome or msedge.")
    parser.add_argument("--browser-executable", help="Full path to Chrome or Edge executable.")
    parser.add_argument(
        "--notify-current",
        action="store_true",
        help="Send a notification for products that are currently in stock. Useful for local testing.",
    )
    args = parser.parse_args()
    if args.max_runs is not None and args.max_runs < 1:
        raise SystemExit("--max-runs must be at least 1.")

    settings = load_settings(database_override=args.database, interval_override=args.interval)
    urls = load_product_urls(Path(args.products))
    if not urls:
        raise SystemExit(f"No product URLs found in {args.products}.")

    store = StateStore(settings.database_path)
    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    watcher = ZaraWatcher(store, notifier)

    try:
        asyncio.run(
            watcher.run(
                urls,
                settings.poll_interval_seconds,
                once=args.once,
                max_runs=args.max_runs,
                notify_current=args.notify_current,
                headless=not args.headed,
                browser_channel=args.browser_channel,
                browser_executable=args.browser_executable,
            )
        )
    finally:
        store.close()


def load_product_urls(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Product file not found: {path}")

    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            urls.append(stripped)
    return urls
