import json
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings

# Define async function to fetch messages from a specific channel
async def fetch_messages(channel_username):
    client = TelegramClient(StringSession(settings.SESSION_STRING), settings.API_ID, settings.API_HASH)
    data = []
    try:
        await client.start(phone=settings.PHONE_NUMBER)
        channel = await client.get_entity(channel_username)

        # Define the time window for the last 5 minutes
        now = datetime.now()  # Current time on the server (which is in IST)
        five_minutes_ago = now - timedelta(minutes=5)

        # Fetch messages (up to 100) to filter
        messages = await client.get_messages(channel, limit=100)

        for message in messages:
            message_time = message.date  # Server time (already in IST)
            if message_time >= five_minutes_ago:
                timestamp = message_time.strftime('%Y-%m-%d %H:%M:%S')
                text = message.text or ''
                data.append([timestamp, text])
    finally:
        await client.disconnect()
    return data

# Define async function to update a specific Google Sheet
async def update_google_sheets(data, spreadsheet_name):
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(settings.GOOGLE_SHEETS_CREDS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_name).sheet1
    sheet.clear()
    if data:
        sheet.append_rows(data, value_input_option='RAW')

# Synchronous view function to handle both channels and sheets
def fetch_and_update(request):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Fetch messages from the first channel and update the first sheet
        messages_1 = loop.run_until_complete(fetch_messages(settings.CHANNEL_USERNAME_1))
        loop.run_until_complete(update_google_sheets(messages_1, settings.SPREADSHEET_NAME_1))

        # Fetch messages from the second channel
        messages_2 = loop.run_until_complete(fetch_messages(settings.CHANNEL_USERNAME_2))

        # Filter out messages containing the keyword 'Rank'
        filtered_messages_2 = [msg for msg in messages_2 if 'Rank' not in msg[1]]

        # Update the second sheet with filtered messages
        loop.run_until_complete(update_google_sheets(filtered_messages_2, settings.SPREADSHEET_NAME_2))

        loop.close()

        return JsonResponse({
            "status": "success", 
            "message_count_1": len(messages_1), 
            "message_count_2": len(filtered_messages_2)
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
