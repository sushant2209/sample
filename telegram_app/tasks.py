# myapp/tasks.py
import asyncio
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime

def fetch_messages():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        client = TelegramClient(StringSession(settings.SESSION_STRING), settings.API_ID, settings.API_HASH)
        client.start(phone=settings.PHONE_NUMBER)
        channel = client.get_entity(settings.CHANNEL_USERNAME)
        messages = client.get_messages(channel, limit=10)
        data = []
        for message in messages:
            timestamp = datetime.fromtimestamp(message.date.timestamp()).strftime('%Y-%m-%d %H:%M:%S')
            text = message.text or ''
            data.append([timestamp, text])
        client.disconnect()
        return data
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        raise

def update_google_sheets(data):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(settings.GOOGLE_SHEETS_CREDS_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(settings.SPREADSHEET_NAME).sheet1
        sheet.clear()
        if data:
            sheet.append_rows(data, value_input_option='RAW')
    except Exception as e:
        print(f"Error updating Google Sheets: {str(e)}")
        raise
