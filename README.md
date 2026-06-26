# ZaraBot

ZaraBot watches Zara product pages and sends a Telegram notification when an item moves from out of stock to in stock.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
Copy-Item products.example.txt products.txt
```

Edit `.env` with your Telegram bot token and chat id, then put one Zara product URL per line in `products.txt`.

## Run

```powershell
python -m zarabot --products products.txt
```

Useful options:

```powershell
python -m zarabot --products products.txt --once
python -m zarabot --products products.txt --once --notify-current --headed --browser-channel chrome
python -m zarabot --products products.txt --interval 30 --max-runs 2 --headed --browser-channel chrome
python -m zarabot --products products.txt --interval 120
python -m zarabot --products products.txt --database data/zarabot.sqlite3
```

## GitHub Actions

The repository includes `.github/workflows/zara-stock-check.yml` for scheduled checks.

1. Push this project to GitHub.
2. In the GitHub repository, go to Settings > Secrets and variables > Actions.
3. Add these repository secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Keep `products.txt` committed with the Zara product URLs you want to watch.
5. Open Actions > Zara stock check > Run workflow to test it manually.

The scheduled workflow runs every 5 minutes. It stores `data/zarabot.sqlite3` in the GitHub Actions cache so the next run can detect `out_of_stock` to `in_stock` transitions.

To test the transition notification without waiting for a real restock, run the workflow manually and paste an in-stock product URL into `seed_out_of_stock_url`. The workflow will first mark that URL as `out_of_stock`, then check the page normally. If it is currently in stock, Telegram should receive a stock alert.

## Notes

- The bot notifies only on an `out_of_stock` to `in_stock` transition.
- The first time a product is seen as in stock, no notification is sent. This avoids alerts for products that were already available before the bot started.
- Zara can change its page markup. The detector checks structured data first and then visible page text.
