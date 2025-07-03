# Italian public transport strikes bot 🇮🇹⚠️

A Telegram bot that monitors Italian strikes from the official RSS feed and sends notifications to a Telegram channel when strikes match your configured criteria.

## Features
- Monitors the official Italian Ministry of Transport strikes RSS feed
- Configurable filtering by sector and region
- Duplicate detection - prevents sending the same strike multiple times
- Multi-language support (Italian/English)

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Save the bot token (format: `123456789:ABCdefGHIjklMNOPqrstUVWxyz`)

### 2. Create a Telegram Channel

1. Create a new Telegram channel
2. Add your bot as an administrator with "Post Messages" permission
3. Get the channel ID:
   - Forward a message from the channel to [@userinfobot](https://t.me/userinfobot)
   - The bot will reply with the channel ID (format: `-1001234567890`)

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:
   ```bash
   BOT_TOKEN=your_actual_bot_token_here
   CHANNEL_ID=your_actual_channel_id_here
   RSS_URL=https://scioperi.mit.gov.it/mit2/public/scioperi/rss
   MAX_STRIKES_TO_STORE=10
   STRIKES_CSV_FILE=strikes_history.csv
   CONFIG_FILE=config.json
   ```

### 5. Configure Strike Filters

Edit `config.json` to define which strikes you want to monitor:

```json
[
  {
    "name": "LOCAL TRANSPORT STRIKE 🚌",
    "sectors": ["Trasporto pubblico locale"],
    "regions": ["Veneto", "Italia"]
  },
  {
    "name": "RAILWAY STRIKE 🚆",
    "sectors": ["Ferroviario"],
    "regions": ["Veneto", "Italia"]
  }
]
```

**Configuration Options:**
- `name`: Display name for the strike type
- `sectors`: Array of sectors to monitor (in Italian)
- `regions`: Array of regions to monitor (in Italian)

Common sectors:
- `"Trasporto pubblico locale"` - Local public transport
- `"Ferroviario"` - Railway
- `"Trasporto aereo"` - Air transport
- `"Trasporto marittimo"` - Maritime transport

Common regions:
- `"Italia"` - All of Italy
- `"Veneto"`, `"Lombardia"`, `"Lazio"`, etc. - Specific regions

### 6. Run the Bot

```bash
python strikes.py
```
