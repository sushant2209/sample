from django.http import JsonResponse
import asyncio
from datetime import datetime, timedelta
import pytz
from telethon import TelegramClient
from telethon.sessions import StringSession
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
import json

# Async function to fetch messages from a specific Telegram channel
async def fetch_messages(channel_username):
    client = TelegramClient(StringSession(settings.SESSION_STRING), settings.API_ID, settings.API_HASH)
    data = []
    try:
        await client.start(phone=settings.PHONE_NUMBER)
        channel = await client.get_entity(channel_username)
        
        now = datetime.now(pytz.timezone('Asia/Kolkata'))  # Current time in IST
        five_minutes_ago = now - timedelta(minutes=5)
        
        messages = await client.get_messages(channel, limit=25)  # Fetch up to 100 messages
        
        for message in messages:
            message_time = message.date.astimezone(pytz.timezone('Asia/Kolkata'))  # Convert to IST
            if message_time >= five_minutes_ago:
                timestamp = message_time.strftime('%Y-%m-%d %H:%M:%S')
                post_link = f"https://t.me/{channel_username}/{message.id}"  # Generate the post link
                text = message.text or ''
                data.append([timestamp, post_link, text])  # Include time, post link, and message text

    finally:
        await client.disconnect()

    return data

# Async function to update a specific Google Sheet
async def update_google_sheets(data, spreadsheet_name):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(settings.GOOGLE_SHEETS_CREDS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_name).sheet1
    if data:
        sheet.append_rows(data, value_input_option='RAW')

# Django view for fetching messages from the first channel and updating the first Google Sheet
def fetch_and_update_spreadsheet_1(request):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def fetch_and_update():
            messages_1 = await fetch_messages(settings.CHANNEL_USERNAME_1)
            await update_google_sheets(messages_1, settings.SPREADSHEET_NAME_1)
            return len(messages_1)

        # Run the task asynchronously
        message_count_1 = loop.run_until_complete(fetch_and_update())

        loop.close()

        return JsonResponse({"status": "success", "message_count": message_count_1})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

# Django view for fetching messages from the second channel, filtering, and updating the second Google Sheet
def fetch_and_update_spreadsheet_2(request):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def fetch_and_update():
            messages_2 = await fetch_messages(settings.CHANNEL_USERNAME_2)
            filtered_messages_2 = [msg for msg in messages_2 if 'Rank' not in msg[2]]
            await update_google_sheets(filtered_messages_2, settings.SPREADSHEET_NAME_2)
            return len(filtered_messages_2)

        # Run the task asynchronously
        message_count_2 = loop.run_until_complete(fetch_and_update())

        loop.close()

        return JsonResponse({"status": "success", "message_count": message_count_2})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
