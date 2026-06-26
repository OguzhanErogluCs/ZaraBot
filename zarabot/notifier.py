from __future__ import annotations

import httpx


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id

    async def send_stock_alert(self, title: str | None, url: str) -> None:
        name = title or "Zara urunu"
        text = f"Stok geldi: {name}\n{url}"
        api_url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                api_url,
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "disable_web_page_preview": False,
                },
            )
            response.raise_for_status()
