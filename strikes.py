import pandas as pd
import re, json, asyncio, feedparser, os, hashlib
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()


def parse_feed(feed):
    dates = []
    sectors = []
    relevances = []
    regions = []
    provinces = []

    for entry in feed.entries:
        title = entry.title

        date_match = re.search(r'Data inizio: (\d{2}/\d{2}/\d{4})', title)
        sector_match = re.search(r'Settore: ([^-]+)', title)
        relevance_match = re.search(r'Rilevanza: ([^-]+)', title)
        region_match = re.search(r'Regione: ([^-]+)', title)
        province_match = re.search(r'Provincia: ([^$]+)', title)

        dates.append(date_match.group(1) if date_match else None)
        sectors.append(sector_match.group(1).strip() if sector_match else None)
        relevances.append(relevance_match.group(1).strip() if relevance_match else None)
        regions.append(region_match.group(1).strip() if region_match else None)
        provinces.append(province_match.group(1).strip() if province_match else None)

    strikes_df = pd.DataFrame({
        'Date': dates,
        'Sector': sectors,
        'Relevance': relevances,
        'Region': regions,
        'Province': provinces
    })

    return strikes_df


def fetch(rss_url: str):
    feed = feedparser.parse(rss_url)
    if feed.status != 200:
        raise Exception(f"Failed to fetch RSS feed: {feed.status}")

    return feed


def get_translations():
    translations_file = os.getenv('TRANSLATIONS_FILE', 'translations.json')
    try:
        with open(translations_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading translations: {e}")
        return {"en": {}, "it": {}}

def loc(text, target_lang='en'):
    if target_lang == 'it':
        return text

    translations = get_translations()
    lang_translations = translations.get(target_lang, {})
    return lang_translations.get(text, text)  # Return original if no translation exists

async def filter_and_publish(parsed_feed: pd.DataFrame, bot: Bot, channel_id: str, lang=None):
    if lang is None:
        lang = os.getenv('LANGUAGE', 'en')
    
    config_file = os.getenv('CONFIG_FILE', 'config.json')
    
    with open(config_file, 'r') as file:
        conditions = json.load(file)

    for condition in conditions:
        sectors = condition.get('sectors', [])
        regions = condition.get('regions', [])
        matching = parsed_feed[
            (parsed_feed['Sector'].isin(sectors)) &
            (parsed_feed['Region'].isin(regions))
            ]

        if not matching.empty:
            print(f"Matches found for condition: {condition['name']}")
            print(matching)

            for _, strike in matching.iterrows():
                # Generate unique ID for this strike
                strike_id = generate_strike_id(strike)
                
                if strike_already_sent(strike_id):
                    print(f"Strike {strike_id} already sent, skipping...")
                    continue
                
                strike_name = loc(condition['name'], lang)
                message = (
                    f"<b>⚠️ {strike_name} ⚠️</b>\n\n"
                    f"<b>{loc('Data inizio', lang)}:</b> {strike['Date']} 📅\n"
                    f"<b>{loc('Settore', lang)}:</b> {loc(strike['Sector'], lang)}\n"
                    f"<b>{loc('Regione', lang)}:</b> {loc(strike['Region'], lang)}\n"
                )

                if pd.notna(strike['Province']):
                    message += f"<b>{loc('Provincia', lang)}:</b> {loc(strike['Province'], lang)}\n"

                if pd.notna(strike['Relevance']):
                    message += f"<b>{loc('Rilevanza', lang)}:</b> {loc(strike['Relevance'], lang)}\n"

                try:
                    await bot.send_message(chat_id=channel_id, text=message, parse_mode='HTML')
                    print(f"Message sent for strike {strike_id}")
                    save_strike_to_history(strike, strike_id)
                    
                except TelegramError as e:
                    print(f"Error sending message to Telegram: {e}")

                strike_id = generate_strike_id(strike)
                if not strike_already_sent(strike_id):
                    save_strike_to_history(strike, strike_id)

def generate_strike_id(strike_data):
    strike_string = f"{strike_data['Date']}{strike_data['Sector']}{strike_data['Region']}{strike_data.get('Province', '')}"
    return hashlib.md5(strike_string.encode()).hexdigest()[:12]

def load_strikes_history():
    csv_file = os.getenv('STRIKES_CSV_FILE', 'strikes_history.csv')
    try:
        if os.path.exists(csv_file):
            return pd.read_csv(csv_file)
        else:
            return pd.DataFrame(columns=['strike_id', 'date', 'sector', 'region', 'province', 'sent_at'])
    except Exception as e:
        print(f"Error loading strikes history: {e}")
        return pd.DataFrame(columns=['strike_id', 'date', 'sector', 'region', 'province', 'sent_at'])

def save_strike_to_history(strike_data, strike_id):
    """Save a strike to the history CSV file"""
    csv_file = os.getenv('STRIKES_CSV_FILE', 'strikes_history.csv')
    max_strikes = int(os.getenv('MAX_STRIKES_TO_STORE', '10'))
    
    history_df = load_strikes_history()
    
    new_record = {
        'strike_id': strike_id,
        'date': strike_data['Date'],
        'sector': strike_data['Sector'],
        'region': strike_data['Region'],
        'province': strike_data.get('Province', ''),
        'sent_at': datetime.now().isoformat()
    }
    
    history_df = pd.concat([history_df, pd.DataFrame([new_record])], ignore_index=True)
    
    # Keep only the last N strikes
    if len(history_df) > max_strikes:
        history_df = history_df.tail(max_strikes)
    
    try:
        history_df.to_csv(csv_file, index=False)
    except Exception as e:
        print(f"Error saving strikes history: {e}")

def strike_already_sent(strike_id):
    history_df = load_strikes_history()
    return strike_id in history_df['strike_id'].values

async def main():
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    RSS_URL = os.getenv('RSS_URL', 'https://scioperi.mit.gov.it/mit2/public/scioperi/rss')
    
    if not CHANNEL_ID or not BOT_TOKEN:
        raise ValueError("CHANNEL_ID and BOT_TOKEN must be set in environment variables")

    bot = Bot(token=BOT_TOKEN)
    print(f"Parsing feed {RSS_URL}")
    feed = fetch(RSS_URL)
    parsed_feed = parse_feed(feed)
    await filter_and_publish(parsed_feed, bot, CHANNEL_ID)


if __name__ == "__main__":
    asyncio.run(main())
