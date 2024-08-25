# myapp/views.py
import json
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime
from django.http import JsonResponse
from django.conf import settings

# Define async functions
async def fetch_messages():
    client = TelegramClient(StringSession(settings.SESSION_STRING), settings.API_ID, settings.API_HASH)
    data = []
    try:
        await client.start(phone=settings.PHONE_NUMBER)
        channel = await client.get_entity(settings.CHANNEL_USERNAME)
        messages = await client.get_messages(channel, limit=10)
        for message in messages:
            timestamp = datetime.fromtimestamp(message.date.timestamp()).strftime('%Y-%m-%d %H:%M:%S')
            text = message.text or ''
            data.append([timestamp, text])
    finally:
        await client.disconnect()
    return data

async def update_google_sheets(data):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(settings.GOOGLE_SHEETS_CREDS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(settings.SPREADSHEET_NAME).sheet1
    sheet.clear()
    if data:
        sheet.append_rows(data, value_input_option='RAW')

# Synchronous view function
def fetch_and_update(request):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        messages = loop.run_until_complete(fetch_messages())
        loop.run_until_complete(update_google_sheets(messages))
        loop.close()
        return JsonResponse({"status": "success", "message_count": len(messages)})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
