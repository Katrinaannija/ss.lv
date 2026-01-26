# Riga Apartment Listing Monitor

Automatically monitors [ss.lv](https://www.ss.lv) for new apartment rentals in Riga city centre and sends Telegram notifications.

## Features

- Scrapes ss.lv apartment listings for Riga centre
- Filters by price, size, and specific streets
- Detects new listings only (no duplicate notifications)
- Sends instant Telegram notifications
- Runs automatically via GitHub Actions (every 3 hours)

## Filter Criteria

| Criterion | Value |
|-----------|-------|
| Max price | 500 EUR/month |
| Min size | 30 m² |
| Street numbers | 1-80 (central area) |

### Monitored Streets

- Lāčplēša iela
- Ģertrūdes iela
- Blaumaņa iela
- Dzirnavu iela
- Tērbatas iela
- Baznīcas iela
- Skolas iela
- Krišjāņa Barona iela
- Raiņa bulvāris
- Valdemāra iela
- Antonijas iela
- Elizabetes iela
- Alfreda Kalniņa iela
- Strēlnieku iela
- Merķeļa iela
- Brīvības bulvāris
- Aleksandra Čaka iela
- Stabu iela
- Kungu iela

## Setup

### 1. Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Message [@userinfobot](https://t.me/userinfobot) to get your chat ID
5. Start a conversation with your new bot (send `/start`)

### 2. Configure GitHub Secrets

Go to your repository **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID from userinfobot |

### 3. Enable GitHub Actions

The workflow runs automatically every 3 hours. You can also trigger it manually:

1. Go to **Actions** tab
2. Select "Apartment Monitor"
3. Click "Run workflow"

## Local Development

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run manually

```bash
# Normal run
python -m src.main

# Dry run (no notifications, no state update)
python -m src.main --dry-run

# Scrape more pages
python -m src.main --pages 5

# Test Telegram connection
python -m src.main --test-telegram
```

### Environment variables

```bash
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

## Project Structure

```
├── .github/workflows/
│   └── monitor.yml         # GitHub Actions workflow
├── src/
│   ├── __init__.py
│   ├── scraper.py          # ss.lv scraper
│   ├── filters.py          # Criteria filtering
│   ├── notifier.py         # Telegram notifications
│   └── main.py             # Main orchestration
├── data/
│   └── seen_listings.json  # State file (auto-generated)
├── config.py               # Configuration
├── requirements.txt
└── README.md
```

## Customization

Edit `config.py` to change:

- `MAX_PRICE` - Maximum rent price
- `MIN_SIZE` - Minimum apartment size
- `MAX_STREET_NUMBER` - Filter street numbers (central area)
- `ALLOWED_STREETS` - List of streets to monitor

## How It Works

1. **Scrape** - Fetches listings from ss.lv Riga centre rentals
2. **Filter** - Applies price, size, and location criteria
3. **Compare** - Checks against previously seen listings
4. **Notify** - Sends Telegram messages for new matches
5. **Save** - Updates state file to prevent duplicates

The state file (`data/seen_listings.json`) is committed back to the repository after each run.
